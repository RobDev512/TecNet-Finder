# ============================================================
# Archivo: prueba_recuperacion_pantalla.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba únicamente la sincronización tipográfica del gutter.
# No existen ya pruebas de suspensión/DPI porque TecNet Finder
# dejó de modificar automáticamente el estado de la ventana.
# ============================================================

from PySide6.QtCore import QRect
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QWidget

from Interfaz.apariencia.control_recuperacion_pantalla import (
    ControlRecuperacionPantalla,
)


def _app():
    return QApplication.instance() or QApplication([])


class _ViewportFalso:
    def __init__(self):
        self.actualizado = False

    def update(self):
        self.actualizado = True


class _AreaFalsa(QWidget):
    pass


class _EditorFalso(QWidget):
    def __init__(self):
        super().__init__()
        self.area_numeros_linea = _AreaFalsa(self)
        self._viewport = _ViewportFalso()
        self.ancho_actualizado = False

    def actualizar_ancho_area_numeros_linea(self, _cantidad=0):
        self.ancho_actualizado = True

    def ancho_area_numeros_linea(self):
        return 42

    def contentsRect(self):
        return QRect(0, 0, 500, 300)

    def viewport(self):
        return self._viewport


class _VentanaFalsa(QWidget):
    def __init__(self):
        super().__init__()
        self.editor_codigo = _EditorFalso()


class _GestorTipografiaFalso:
    pass


def _crear_control():
    aplicacion = _app()
    ventana = _VentanaFalsa()

    control = ControlRecuperacionPantalla(
        aplicacion=aplicacion,
        ventana=ventana,
        gestor_tipografia=_GestorTipografiaFalso(),
    )

    return control, ventana.editor_codigo


def prueba_numeros_linea_usan_misma_fuente_que_editor():
    control, editor = _crear_control()

    fuente = QFont("Consolas")
    fuente.setPointSize(18)
    editor.setFont(fuente)

    control._sincronizar_numeros_linea()

    assert (
        editor.area_numeros_linea.font().family()
        == editor.font().family()
    )
    assert (
        editor.area_numeros_linea.font().pointSize()
        == editor.font().pointSize()
    )


def prueba_sincronizacion_recalcula_ancho_y_geometria():
    control, editor = _crear_control()

    control._sincronizar_numeros_linea()

    assert editor.ancho_actualizado
    assert editor.area_numeros_linea.width() == 42
    assert editor.area_numeros_linea.height() == 300
    assert editor.viewport().actualizado


def prueba_control_no_tiene_recuperacion_automatica_de_suspension():
    metodos_prohibidos = (
        "_al_cambiar_estado_aplicacion",
        "_programar_recuperacion",
        "_recrear_superficie_ventana",
        "_recrear_superficie_si_sigue_vigente",
        "_refrescar_superficie_nativa_windows",
    )

    for nombre in metodos_prohibidos:
        assert not hasattr(ControlRecuperacionPantalla, nombre)
