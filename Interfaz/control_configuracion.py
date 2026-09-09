# ============================================================
# Archivo: control_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo conecta la ventana general de configuración con
# TecNet Finder.
#
# Abre Configuración directamente desde el botón de engrane de
# la barra personalizada y sincroniza los cambios realizados en
# sus paneles con los componentes activos de la aplicación.
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
        self.ventana = ventana  # Conserva el acceso a la interfaz y a su editor.
        self.gestor_ollama = gestor_ollama  # Reutiliza el servicio privado administrado desde principal.py.
        self.componente_ia = componente_ia  # Reutiliza la ubicación instalada detectada al iniciar.
        self.preferencias_ia = preferencias_ia  # Reutiliza las preferencias persistentes.
        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Conserva el último estado confirmado del asistente.

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(self._abrir_configuracion)  # Hace que el engrane abra directamente Configuración.
        self._aplicar_autocompletado(self.asistencia_disponible)  # Sincroniza inicialmente el editor con el estado real del servicio.

    def _abrir_configuracion(self) -> None:
        ventana_configuracion = VentanaConfiguracion(
            gestor_ollama=self.gestor_ollama,
            componente_ia=self.componente_ia,
            preferencias_ia=self.preferencias_ia,
            asistencia_disponible_inicial=self.asistencia_disponible,
            padre=self.ventana,
        )  # Construye Configuración utilizando exactamente los mismos componentes activos de esta ejecución.

        ventana_configuracion.activacion_ia_cambiada.connect(self._aplicar_autocompletado)  # Sincroniza inmediatamente cualquier modificación de IA.
        ventana_configuracion.exec()  # Mantiene una única configuración abierta hasta que el usuario decida cerrarla.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        self.asistencia_disponible = bool(habilitado)  # Conserva el último estado confirmado sin realizar otra consulta HTTP.
        control = self.ventana.editor_codigo.control_autocompletado  # Obtiene el controlador ya asociado con el editor.
        control.establecer_habilitado(self.asistencia_disponible)  # Habilita o detiene nuevas generaciones.

        if not self.asistencia_disponible:
            return  # No debe programarse ninguna sugerencia nueva después de desactivar la característica.

        actualizar = getattr(self.ventana.editor_codigo, "_actualizar_autocompletado", None)  # Obtiene la operación utilizada para examinar la línea actual.

        if callable(actualizar):
            actualizar()  # Permite utilizar inmediatamente el asistente sobre una línea que ya estaba escrita.