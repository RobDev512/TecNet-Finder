# ============================================================
# Archivo: control_configuracion_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Extiende ControlConfiguracion para sincronizar el idioma
# confirmado con la ventana principal, Configuración, diálogos
# secundarios, árboles y la ventana independiente de
# diagnósticos.
#
# También evita mostrar el acceso flotante de diagnósticos
# mientras el editor se encuentra ampliado.
# ============================================================

from PySide6.QtCore import QTimer

from Interfaz.configuracion.control_configuracion import ControlConfiguracion
from Interfaz.internacionalizacion.control_barrida_final import ControlBarridaFinal
from Interfaz.internacionalizacion.control_cierre_interfaz import ControlCierreInterfaz
from Interfaz.internacionalizacion.control_dialogos_secundarios import ControlDialogosSecundarios
from Interfaz.internacionalizacion.control_exportacion_arbol import ControlExportacionArbol
from Interfaz.internacionalizacion.control_idioma_interfaz import ControlIdiomaInterfaz
from Interfaz.internacionalizacion.control_placeholder_editor import ControlPlaceholderEditor


class ControlConfiguracionIdioma(ControlConfiguracion):
    def __init__(self, *argumentos, **palabras_clave):
        super().__init__(*argumentos, **palabras_clave)

        self.control_idioma_interfaz = ControlIdiomaInterfaz(self.ventana)
        self.control_placeholder_editor = ControlPlaceholderEditor(self.ventana)
        self.control_dialogos_secundarios = ControlDialogosSecundarios(
            self.ventana,
            self.preferencias_aplicacion,
        )
        self.control_cierre_interfaz = ControlCierreInterfaz(self.ventana)
        self.control_barrida_final = ControlBarridaFinal(self.ventana)
        self.control_exportacion_arbol = ControlExportacionArbol(self.ventana)

        self._aplicar_idioma_principal()

        if self.ventana_configuracion_preparada is not None:
            self.control_cierre_interfaz.preparar_configuracion(
                self.ventana_configuracion_preparada
            )
            self.control_barrida_final.preparar_configuracion(
                self.ventana_configuracion_preparada
            )

        self.ventana.panel_resultados.boton_analizar.clicked.connect(
            self._programar_reaplicacion_idioma
        )
        self.ventana.panel_resultados.boton_limpiar.clicked.connect(
            self._programar_reaplicacion_idioma
        )
        self.ventana.editor_codigo.ejemplos_insertados.connect(
            self._programar_reaplicacion_idioma
        )
        self.ventana.editor_codigo.boton_ampliar.clicked.connect(
            self._programar_actualizacion_boton_diagnosticos
        )

    def _crear_ventana_configuracion(self):
        ventana = super()._crear_ventana_configuracion()

        if hasattr(self, "control_cierre_interfaz"):
            idioma = self.preferencias_aplicacion.idioma_interfaz()
            self.control_cierre_interfaz.establecer_idioma(idioma)
            self.control_barrida_final.establecer_idioma(idioma)
            self.control_cierre_interfaz.preparar_configuracion(ventana)
            self.control_barrida_final.preparar_configuracion(ventana)

        ventana.boton_aplicar.clicked.connect(
            self._programar_reaplicacion_idioma
        )
        ventana.boton_aplicar.clicked.connect(
            lambda _marcado=False, v=ventana: self._programar_reaplicacion_configuracion(v)
        )
        ventana.accepted.connect(self._programar_reaplicacion_idioma)
        return ventana

    def _crear_ventana_advertencias(self, diagnosticos: list) -> None:
        super()._crear_ventana_advertencias(diagnosticos)

        if self.ventana_advertencias is not None and hasattr(
            self,
            "control_idioma_interfaz",
        ):
            self.control_idioma_interfaz.aplicar_ventana_diagnosticos(
                self.ventana_advertencias
            )

    def _actualizar_boton_reabrir_advertencias(self, resultado=None) -> None:
        super()._actualizar_boton_reabrir_advertencias(resultado)

        if self.boton_reabrir_advertencias is None:
            return

        if self.ventana.editor_ampliado:
            self.boton_reabrir_advertencias.setVisible(False)
            self.boton_reabrir_advertencias.setEnabled(False)
            return

        if not hasattr(self, "control_idioma_interfaz"):
            return

        diagnosticos = self._obtener_diagnosticos_reabribles(resultado)
        self.control_idioma_interfaz.aplicar_boton_reabrir_diagnosticos(
            self.boton_reabrir_advertencias,
            diagnosticos,
        )

    def _programar_actualizacion_boton_diagnosticos(self, *_argumentos) -> None:
        QTimer.singleShot(
            0,
            self._actualizar_boton_reabrir_advertencias,
        )

    def _programar_reaplicacion_configuracion(self, ventana) -> None:
        QTimer.singleShot(
            0,
            lambda v=ventana: self._reaplicar_configuracion(v),
        )

    def _reaplicar_configuracion(self, ventana) -> None:
        if ventana is None or not hasattr(self, "control_cierre_interfaz"):
            return

        idioma = self.preferencias_aplicacion.idioma_interfaz()
        self.control_cierre_interfaz.establecer_idioma(idioma)
        self.control_barrida_final.establecer_idioma(idioma)
        self.control_cierre_interfaz.preparar_configuracion(ventana)
        self.control_barrida_final.aplicar_configuracion(ventana)

    def _programar_reaplicacion_idioma(self, *_argumentos) -> None:
        QTimer.singleShot(0, self._aplicar_idioma_principal)

    def _aplicar_idioma_principal(self) -> None:
        idioma = self.preferencias_aplicacion.idioma_interfaz()
        self.control_idioma_interfaz.aplicar(idioma)
        self.control_placeholder_editor.establecer_idioma(idioma)
        self.control_dialogos_secundarios.establecer_idioma(idioma)
        self.control_cierre_interfaz.establecer_idioma(idioma)
        self.control_barrida_final.establecer_idioma(idioma)

        # El cierre prepara y reancla primero cada VistaArbol.
        # Después se sustituye exclusivamente la acción Guardar para
        # ofrecer PNG HD, SVG y PDF sin alterar la escena ni el compilador.
        self.control_exportacion_arbol.establecer_idioma(idioma)

        if self.ventana_advertencias is not None:
            self.control_idioma_interfaz.aplicar_ventana_diagnosticos(
                self.ventana_advertencias
            )

        self._actualizar_boton_reabrir_advertencias()
