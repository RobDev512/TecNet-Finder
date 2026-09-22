# ============================================================
# Archivo: control_configuracion_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Extiende ControlConfiguracion para sincronizar el idioma
# confirmado con la ventana principal.
#
# No altera el comportamiento Aplicar / Aceptar / Cancelar:
# - Cancelar no cambia la ventana principal.
# - Aplicar actualiza la ventana principal al terminar de guardar.
# - Aceptar actualiza la ventana principal antes de continuar.
# ============================================================

from PySide6.QtCore import QTimer  # Permite esperar a que Configuración termine de persistir antes de releer el idioma.

from Interfaz.configuracion.control_configuracion import ControlConfiguracion
from Interfaz.internacionalizacion.control_idioma_interfaz import ControlIdiomaInterfaz


class ControlConfiguracionIdioma(ControlConfiguracion):
    def __init__(self, *argumentos, **palabras_clave):
        super().__init__(*argumentos, **palabras_clave)  # Conserva íntegro el controlador estable.
        self.control_idioma_interfaz = ControlIdiomaInterfaz(self.ventana)  # Añade únicamente la capa visual de internacionalización.
        self._aplicar_idioma_principal()  # Recupera el idioma confirmado desde el propio arranque.

        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_reaplicacion_idioma)  # Retraduce el estado generado después de compilar.
        self.ventana.panel_resultados.boton_limpiar.clicked.connect(self._programar_reaplicacion_idioma)  # Recupera el mensaje neutral después de limpiar.
        self.ventana.editor_codigo.ejemplos_insertados.connect(self._programar_reaplicacion_idioma)  # Mantiene neutral el estado después de insertar ejemplos.

    def _crear_ventana_configuracion(self):
        ventana = super()._crear_ventana_configuracion()  # Conserva toda la preparación, tema y conexiones existentes.
        ventana.boton_aplicar.clicked.connect(self._programar_reaplicacion_idioma)  # Lee la preferencia ya confirmada después de Aplicar.
        ventana.accepted.connect(self._programar_reaplicacion_idioma)  # Sincroniza también cuando Aceptar confirma y cierra.
        return ventana

    def _programar_reaplicacion_idioma(self, *_argumentos) -> None:
        QTimer.singleShot(0, self._aplicar_idioma_principal)  # Espera a que la acción original haya terminado de modificar estado o preferencias.

    def _aplicar_idioma_principal(self) -> None:
        self.control_idioma_interfaz.aplicar(self.preferencias_aplicacion.idioma_interfaz())  # Utiliza siempre el idioma real, nunca la copia temporal.
