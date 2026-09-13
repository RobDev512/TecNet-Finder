# ============================================================
# Archivo: control_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo conecta la ventana general de configuración con
# TecNet Finder.
#
# Integra preferencias generales de ventana y resultados junto
# con las funciones independientes de inteligencia artificial.
#
# Las preferencias generales se aplican durante el inicio y los
# cambios realizados desde Configuración se reflejan de forma
# inmediata sobre la ventana principal y el panel de resultados.
# ============================================================

from PySide6.QtCore import QObject  # Permite vincular el controlador con el ciclo de vida de la ventana principal.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite compartir la instalación opcional detectada.
from AsistenteIA.gestor_ollama import GestorOllama  # Permite compartir exactamente el mismo servicio administrado por la aplicación.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Permite compartir las preferencias persistentes de inteligencia artificial.
from Interfaz.ventana_configuracion import VentanaConfiguracion  # Importa la ventana general que contiene las diferentes categorías.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias generales de ventana y resultados.


class ControlConfiguracion(QObject):  # Coordina Configuración sin mezclarla con las fases internas del compilador.
    def __init__(
        self,
        ventana,
        gestor_ollama: GestorOllama,
        componente_ia: GestorComponenteIA,
        preferencias_ia: PreferenciasIA,
        asistencia_disponible_inicial: bool,
        preferencias_aplicacion: PreferenciasAplicacion | None = None,
    ):
        super().__init__(ventana)  # Vincula automáticamente el controlador con la ventana principal.
        self.ventana = ventana  # Conserva el acceso a la ventana, editor y paneles.
        self.gestor_ollama = gestor_ollama  # Reutiliza el servicio privado administrado desde principal.py.
        self.componente_ia = componente_ia  # Reutiliza la ubicación instalada detectada al iniciar.
        self.preferencias_ia = preferencias_ia  # Reutiliza las preferencias específicas del asistente local.
        self.preferencias_aplicacion = preferencias_aplicacion or PreferenciasAplicacion()  # Utiliza la instancia recibida o crea una compatible cuando principal.py todavía no la proporciona.
        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Conserva el último estado confirmado del servicio compartido.

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(
            self._abrir_configuracion
        )  # Hace que el engrane abra directamente la ventana general de Configuración.

        autocompletado_inicial = (
            self.asistencia_disponible
            and self.preferencias_ia.autocompletado_activado()
        )  # Exige simultáneamente preferencia y servicio operativo para ghost text.

        diagnosticos_iniciales = (
            self.asistencia_disponible
            and self.preferencias_ia.diagnosticos_ia_activados()
        )  # Evalúa independientemente la mejora de soluciones mediante IA.

        self._aplicar_autocompletado(autocompletado_inicial)  # Sincroniza inicialmente el editor.
        self._aplicar_diagnosticos(diagnosticos_iniciales)  # Sincroniza inicialmente el panel de diagnósticos.
        self._aplicar_preferencias_aplicacion()  # Sincroniza también ventana, navegación y advertencias persistentes.

    def _abrir_configuracion(self) -> None:
        ventana_configuracion = VentanaConfiguracion(
            gestor_ollama=self.gestor_ollama,
            componente_ia=self.componente_ia,
            preferencias_ia=self.preferencias_ia,
            preferencias_aplicacion=self.preferencias_aplicacion,
            asistencia_disponible_inicial=self.asistencia_disponible,
            padre=self.ventana,
        )  # Construye Configuración utilizando exactamente los mismos componentes y preferencias de esta ejecución.

        ventana_configuracion.lado_media_pantalla_cambiado.connect(
            self._aplicar_lado_media_pantalla
        )  # Actualiza la mitad predeterminada sin reiniciar TecNet Finder.

        ventana_configuracion.navegacion_automatica_cambiada.connect(
            self._aplicar_navegacion_automatica
        )  # Actualiza inmediatamente el comportamiento posterior a la compilación.

        ventana_configuracion.advertencias_vlsm_cambiadas.connect(
            self._aplicar_visibilidad_advertencias_vlsm
        )  # Actualiza inmediatamente la presentación compacta de advertencias.

        ventana_configuracion.autocompletado_ia_cambiado.connect(
            self._aplicar_autocompletado
        )  # Sincroniza únicamente los cambios efectivos del ghost text.

        ventana_configuracion.diagnosticos_ia_cambiados.connect(
            self._aplicar_diagnosticos
        )  # Sincroniza independientemente las explicaciones mediante IA.

        ventana_configuracion.servicio_ia_cambiado.connect(
            self._actualizar_servicio
        )  # Conserva el estado real utilizado cuando Configuración vuelva a abrirse.

        ventana_configuracion.exec()  # Mantiene una única Configuración abierta hasta que el usuario decida cerrarla.

    def _aplicar_preferencias_aplicacion(self) -> None:
        self._aplicar_lado_media_pantalla(
            self.preferencias_aplicacion.lado_media_pantalla()
        )  # Recupera la mitad preferida durante el inicio.

        self._aplicar_navegacion_automatica(
            self.preferencias_aplicacion.navegacion_automatica_activada()
        )  # Recupera el comportamiento de navegación persistido.

        self._aplicar_visibilidad_advertencias_vlsm(
            self.preferencias_aplicacion.advertencias_vlsm_visibles()
        )  # Recupera la preferencia correspondiente con el panel compacto.

    def _aplicar_lado_media_pantalla(self, lado: str) -> None:
        if lado not in (
            PreferenciasAplicacion.LADO_IZQUIERDO,
            PreferenciasAplicacion.LADO_DERECHO,
        ):
            return  # Ignora posiciones distintas de las dos mitades admitidas.

        self.ventana.lado_media_pantalla = lado  # Conserva la mitad que deberá proponerse la próxima vez que se utilice Media pantalla.

        if hasattr(self.ventana, "barra_titulo"):
            self.ventana.barra_titulo.actualizar_estado_media_pantalla(
                bool(getattr(self.ventana, "en_media_pantalla", False)),
                lado,
            )  # Mantiene sincronizado el selector visual con la nueva preferencia.

    def _aplicar_navegacion_automatica(self, activada: bool) -> None:
        panel = self.ventana.panel_resultados  # Obtiene la superficie responsable de decidir qué resultado mostrar después de compilar.
        valor = bool(activada)  # Normaliza el estado recibido desde Configuración.

        metodo = getattr(
            panel,
            "establecer_navegacion_automatica",
            None,
        )  # Busca primero la operación pública preparada para esta preferencia.

        if callable(metodo):
            metodo(valor)  # Utiliza la API pública cuando se encuentra disponible.
            return

        panel.navegacion_automatica = valor  # Mantiene compatibilidad con implementaciones que consultan directamente este atributo.
        panel.navegacion_automatica_resultados = valor  # Mantiene compatibilidad con el nombre utilizado durante versiones intermedias del bloque.

    def _aplicar_visibilidad_advertencias_vlsm(self, visibles: bool) -> None:
        panel = self.ventana.panel_resultados  # Obtiene la superficie responsable del panel compacto de advertencias.
        valor = bool(visibles)  # Normaliza el estado recibido.

        metodo = getattr(
            panel,
            "establecer_advertencias_vlsm_visibles",
            None,
        )  # Busca primero la operación pública correspondiente con esta preferencia.

        if callable(metodo):
            metodo(valor)  # Utiliza la API pública cuando la versión actual del panel ya la ofrece.
            return

        metodo_alternativo = getattr(
            panel,
            "establecer_mostrar_advertencias_vlsm",
            None,
        )  # Reconoce también el nombre utilizado durante una versión intermedia del desarrollo.

        if callable(metodo_alternativo):
            metodo_alternativo(valor)  # Aplica la preferencia mediante la operación alternativa conocida.
            return

        panel.mostrar_advertencias_vlsm = valor  # Mantiene compatibilidad con implementaciones que consultan directamente este atributo.
        panel.mostrar_advertencias_bajo_vlsm = valor  # Conserva también el nombre empleado durante el diseño inicial.

    def _actualizar_servicio(self, disponible: bool) -> None:
        self.asistencia_disponible = bool(disponible)  # Conserva exclusivamente la disponibilidad de Ollama sin confundirla con una función concreta.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        control = self.ventana.editor_codigo.control_autocompletado  # Obtiene el controlador ya asociado con el editor.
        control.establecer_habilitado(bool(habilitado))  # Habilita o detiene nuevas generaciones de ghost text.

        if not habilitado:
            return  # No debe programarse ninguna sugerencia nueva después de desactivar esta función.

        actualizar = getattr(
            self.ventana.editor_codigo,
            "_actualizar_autocompletado",
            None,
        )  # Obtiene la operación utilizada para examinar la línea actual.

        if callable(actualizar):
            actualizar()  # Permite utilizar inmediatamente el autocompletado sobre una línea que ya estaba escrita.

    def _aplicar_diagnosticos(self, habilitado: bool) -> None:
        self.ventana.panel_diagnosticos.establecer_ia_habilitada(
            bool(habilitado)
        )  # Activa la mejora mediante IA o restaura inmediatamente las soluciones oficiales.