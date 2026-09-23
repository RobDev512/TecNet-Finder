# ============================================================
# Archivo: control_configuracion_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Extiende ControlConfiguracion para sincronizar el idioma
# confirmado con la ventana principal y con la ventana
# independiente de diagnósticos.
#
# No altera el comportamiento Aplicar / Aceptar / Cancelar:
# - Cancelar no cambia la ventana principal.
# - Aplicar actualiza la ventana principal al terminar de guardar.
# - Aceptar actualiza la ventana principal antes de continuar.
# ============================================================

from PySide6.QtCore import QTimer  # Permite esperar a que Configuración termine de persistir antes de releer el idioma.

from Interfaz.configuracion.control_configuracion import ControlConfiguracion
from Interfaz.internacionalizacion.control_dialogos_secundarios import ControlDialogosSecundarios
from Interfaz.internacionalizacion.control_idioma_interfaz import ControlIdiomaInterfaz


class ControlConfiguracionIdioma(ControlConfiguracion):
    def __init__(self, *argumentos, **palabras_clave):
        super().__init__(*argumentos, **palabras_clave)  # Conserva íntegro el controlador estable.
        self.control_idioma_interfaz = ControlIdiomaInterfaz(self.ventana)  # Añade la capa visual principal de internacionalización.
        self.control_dialogos_secundarios = ControlDialogosSecundarios(
            self.ventana,
            self.preferencias_aplicacion,
        )  # Sustituye únicamente las interacciones secundarias que todavía conservaban textos fijos en español.
        self._aplicar_idioma_principal()  # Recupera el idioma confirmado desde el propio arranque.

        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_reaplicacion_idioma)  # Retraduce resultados dinámicos después de compilar.
        self.ventana.panel_resultados.boton_limpiar.clicked.connect(self._programar_reaplicacion_idioma)  # Recupera el mensaje neutral después de limpiar.
        self.ventana.editor_codigo.ejemplos_insertados.connect(self._programar_reaplicacion_idioma)  # Mantiene neutral el estado después de insertar ejemplos.

    def _crear_ventana_configuracion(self):
        ventana = super()._crear_ventana_configuracion()  # Conserva toda la preparación, tema y conexiones existentes.
        ventana.boton_aplicar.clicked.connect(self._programar_reaplicacion_idioma)  # Lee la preferencia ya confirmada después de Aplicar.
        ventana.accepted.connect(self._programar_reaplicacion_idioma)  # Sincroniza también cuando Aceptar confirma y cierra.
        return ventana

    def _crear_ventana_advertencias(self, diagnosticos: list) -> None:
        super()._crear_ventana_advertencias(diagnosticos)  # Conserva modalidad, señales, tema, referencia y presentación existentes.
        if self.ventana_advertencias is not None and hasattr(self, "control_idioma_interfaz"):
            self.control_idioma_interfaz.aplicar_ventana_diagnosticos(self.ventana_advertencias)  # Traduce antes de que Qt procese el siguiente ciclo de dibujo.

    def _actualizar_boton_reabrir_advertencias(self, resultado=None) -> None:
        super()._actualizar_boton_reabrir_advertencias(resultado)  # Conserva disponibilidad, visibilidad y posición oficiales.
        if not hasattr(self, "control_idioma_interfaz"):
            return  # Durante el constructor base el traductor todavía no existe.
        diagnosticos = self._obtener_diagnosticos_reabribles(resultado)
        self.control_idioma_interfaz.aplicar_boton_reabrir_diagnosticos(
            self.boton_reabrir_advertencias,
            diagnosticos,
        )  # Impide que cambios de pestaña vuelvan a dejar el tooltip en español.

    def _programar_reaplicacion_idioma(self, *_argumentos) -> None:
        QTimer.singleShot(0, self._aplicar_idioma_principal)  # Espera a que la acción original haya terminado de modificar estado o preferencias.

    def _aplicar_idioma_principal(self) -> None:
        idioma = self.preferencias_aplicacion.idioma_interfaz()  # Recupera una sola vez la preferencia confirmada.
        self.control_idioma_interfaz.aplicar(idioma)  # Actualiza la ventana principal con el idioma real.
        self.control_dialogos_secundarios.establecer_idioma(idioma)  # Mantiene sincronizados los diálogos que se abrirán posteriormente.

        if self.ventana_advertencias is not None:
            self.control_idioma_interfaz.aplicar_ventana_diagnosticos(self.ventana_advertencias)  # Actualiza una ventana independiente que ya estuviera abierta.

        self._actualizar_boton_reabrir_advertencias()  # Mantiene también sincronizada la ayuda del acceso flotante.
