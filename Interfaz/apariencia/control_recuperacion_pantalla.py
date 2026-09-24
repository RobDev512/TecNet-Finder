# ============================================================
# Archivo: control_recuperacion_pantalla.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Mantiene sincronizada la numeración lateral del editor con la
# tipografía seleccionada para el código.
#
# Importante:
# Esta versión NO intenta detectar suspensión, reactivación,
# pérdida de foco, cambios de monitor ni cambios de DPI.
# Tampoco mueve, restaura, maximiza ni repinta la ventana.
#
# Se conserva este controlador únicamente para que los números
# de línea utilicen siempre la misma familia y tamaño que el
# texto del editor.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QRect, QTimer
from PySide6.QtGui import QFont


class ControlRecuperacionPantalla(QObject):
    def __init__(self, aplicacion, ventana, gestor_tipografia):
        super().__init__(ventana)

        # Se conservan los parámetros para mantener compatible la creación
        # existente desde principal.py, pero no se conectan eventos globales.
        self.aplicacion = aplicacion
        self.ventana = ventana
        self.gestor_tipografia = gestor_tipografia
        self.editor = ventana.editor_codigo

        # Solo observamos cambios reales de fuente en el editor.
        self.editor.installEventFilter(self)

        QTimer.singleShot(0, self._sincronizar_numeros_linea)

    def _sincronizar_numeros_linea(self) -> None:
        area = getattr(self.editor, "area_numeros_linea", None)

        if area is None:
            return

        # Copia exactamente familia, tamaño, peso y demás propiedades
        # tipográficas del editor hacia el gutter.
        area.setFont(QFont(self.editor.font()))

        # Recalcula el margen izquierdo porque un tamaño de fuente mayor
        # también necesita más anchura para representar los índices.
        self.editor.actualizar_ancho_area_numeros_linea()

        rectangulo = self.editor.contentsRect()
        ancho = self.editor.ancho_area_numeros_linea()

        area.setGeometry(
            QRect(
                rectangulo.left(),
                rectangulo.top(),
                ancho,
                rectangulo.height(),
            )
        )

        area.update()
        self.editor.viewport().update()

    def eventFilter(self, objeto, evento) -> bool:
        if (
            objeto is self.editor
            and evento.type() == QEvent.Type.FontChange
        ):
            QTimer.singleShot(0, self._sincronizar_numeros_linea)

        return super().eventFilter(objeto, evento)
