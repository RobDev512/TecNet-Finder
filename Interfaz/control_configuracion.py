# ============================================================
# Archivo: control_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo conecta la ventana general de configuración con
# TecNet Finder.
#
# Autocompletado y mejora de diagnósticos se sincronizan como
# funciones independientes, mientras que ambas comparten el mismo
# estado real del servicio privado de Ollama.
# ============================================================

from PySide6.QtCore import QObject  # Permite vincular el controlador con el ciclo de vida de la ventana principal.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite compartir la instalación opcional detectada.
from AsistenteIA.gestor_ollama import GestorOllama  # Permite compartir exactamente el mismo servicio administrado por la aplicación.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Permite compartir las preferencias persistentes del usuario.
from Interfaz.ventana_configuracion import VentanaConfiguracion  # Importa la ventana general que contendrá las diferentes categorías.


class ControlConfiguracion(QObject):  # Coordina la configuración sin mezclarla con las fases internas del compilador.
    def __init__(
        self,
        ventana,
        gestor_ollama: GestorOllama,
        componente_ia: GestorComponenteIA,
        preferencias_ia: PreferenciasIA,
        asistencia_disponible_inicial: bool,
    ):
        super().__init__(ventana)  # Vincula automáticamente el controlador con la ventana principal.
        self.ventana = ventana  # Conserva el acceso a la interfaz, editor y panel de diagnósticos.
        self.gestor_ollama = gestor_ollama  # Reutiliza el servicio privado administrado desde principal.py.
        self.componente_ia = componente_ia  # Reutiliza la ubicación instalada detectada al iniciar.
        self.preferencias_ia = preferencias_ia  # Reutiliza las preferencias persistentes.
        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Conserva el último estado confirmado del servicio compartido.

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(self._abrir_configuracion)  # Hace que el engrane abra directamente Configuración.

        autocompletado_inicial = self.asistencia_disponible and preferencias_ia.autocompletado_activado()  # Exige simultáneamente preferencia y servicio operativo.
        diagnosticos_iniciales = self.asistencia_disponible and preferencias_ia.diagnosticos_ia_activados()  # Evalúa independientemente la segunda función.
        self._aplicar_autocompletado(autocompletado_inicial)  # Sincroniza inicialmente el editor con su preferencia efectiva.
        self._aplicar_diagnosticos(diagnosticos_iniciales)  # Sincroniza también la mejora automática de la columna Solución.

    def _abrir_configuracion(self) -> None:
        ventana_configuracion = VentanaConfiguracion(
            gestor_ollama=self.gestor_ollama,
            componente_ia=self.componente_ia,
            preferencias_ia=self.preferencias_ia,
            asistencia_disponible_inicial=self.asistencia_disponible,
            padre=self.ventana,
        )  # Construye Configuración utilizando exactamente los mismos componentes activos de esta ejecución.

        ventana_configuracion.autocompletado_ia_cambiado.connect(self._aplicar_autocompletado)  # Sincroniza únicamente los cambios efectivos del ghost text.
        ventana_configuracion.diagnosticos_ia_cambiados.connect(self._aplicar_diagnosticos)  # Sincroniza independientemente las explicaciones automáticas.
        ventana_configuracion.servicio_ia_cambiado.connect(self._actualizar_servicio)  # Conserva el estado real utilizado cuando Configuración vuelva a abrirse.
        ventana_configuracion.exec()  # Mantiene una única configuración abierta hasta que el usuario decida cerrarla.

    def _actualizar_servicio(self, disponible: bool) -> None:
        self.asistencia_disponible = bool(disponible)  # Conserva exclusivamente la disponibilidad de Ollama sin confundirla con una función concreta.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        control = self.ventana.editor_codigo.control_autocompletado  # Obtiene el controlador ya asociado con el editor.
        control.establecer_habilitado(bool(habilitado))  # Habilita o detiene nuevas generaciones de ghost text.

        if not habilitado:
            return  # No debe programarse ninguna sugerencia nueva después de desactivar exclusivamente esta función.

        actualizar = getattr(self.ventana.editor_codigo, "_actualizar_autocompletado", None)  # Obtiene la operación utilizada para examinar la línea actual.

        if callable(actualizar):
            actualizar()  # Permite utilizar inmediatamente el autocompletado sobre una línea que ya estaba escrita.

    def _aplicar_diagnosticos(self, habilitado: bool) -> None:
        self.ventana.panel_diagnosticos.establecer_ia_habilitada(bool(habilitado))  # Activa la generación automática o restaura inmediatamente las soluciones oficiales.
