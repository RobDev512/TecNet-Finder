# ============================================================
# Archivo: selector_niveles_registros.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Reutiliza el selector aprobado del visor de triplos en el
# Centro de mantenimiento. Comparte el dibujo de la flecha,
# la lista desplegable, la selección y el hover sin duplicarlos.
# ============================================================

from PySide6.QtCore import Qt  # Permite mantener el comportamiento original de las opciones.
from PySide6.QtGui import QColor, QPalette  # Permite adoptar los colores de cada tema.

from Interfaz.resultados.visor_triplos import SelectorInstruccionTriplos  # Reutiliza exactamente el control visual probado en el visor.


class SelectorNivelesRegistros(SelectorInstruccionTriplos):  # Comparte el comportamiento y los dibujos originales del selector de triplos.

    def aplicar_tema(self, colores: dict) -> None:  # Sincroniza el mismo control con la paleta del Centro de mantenimiento.
        self.setStyleSheet(f"""
            QComboBox#MantenimientoNivel {{ background: transparent; color: {colores["texto"]}; border: none; border-radius: 7px; padding: 7px 30px 7px 9px; }}
            QComboBox#MantenimientoNivel::drop-down {{ background: transparent; border: none; border-top-right-radius: 7px; border-bottom-right-radius: 7px; width: 25px; }}
            QComboBox#MantenimientoNivel::down-arrow {{ image: none; width: 0px; height: 0px; }}
            QComboBox#MantenimientoNivel QAbstractItemView {{ background-color: {colores["panel"]}; color: {colores["texto"]}; selection-background-color: {colores["acento"]}; selection-color: {colores["texto_inverso"]}; }}
        """)  # Replica la estructura de estilos del selector de triplos y respeta el marco que ya existe en mantenimiento.
        self.color_flecha = QColor(colores["texto"])  # Sincroniza el triángulo heredado sin volver a dibujarlo.
        self.vista_opciones.setStyleSheet(f"""
            QListView#OpcionesInstruccionTriplo {{ background-color: {colores["panel"]}; color: {colores["texto"]}; border: none; border-radius: 9px; outline: none; padding: 7px; }}
            QListView#OpcionesInstruccionTriplo::item {{ background: transparent; color: {colores["texto"]}; border: none; border-radius: 7px; padding: 7px 9px; min-height: 22px; }}
            QListView#OpcionesInstruccionTriplo::item:selected {{ background-color: {colores["acento"]}; color: {colores["texto_inverso"]}; }}
            QListView#OpcionesInstruccionTriplo::item:hover:!selected {{ background-color: {colores["superficie_hover"]}; color: {colores["texto"]}; }}
        """)  # Utiliza el mismo estilo de lista, altura y estados seleccionado/hover que la pestaña de triplos.
        paleta = self.vista_opciones.palette()  # Obtiene la paleta del menú emergente real.
        paleta.setColor(QPalette.ColorRole.Highlight, QColor(colores["acento"]))  # Define el color de la opción confirmada.
        paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(colores["texto_inverso"]))  # Garantiza el contraste sobre el acento.
        self.vista_opciones.setPalette(paleta)  # Aplica la misma selección del visor de triplos.
        delegado = self.delegado_opciones  # Recupera el mismo delegado que dibuja las opciones del visor.
        delegado.color_normal = QColor(colores["panel"])  # Conserva el fondo de la lista para las opciones normales.
        delegado.color_seleccion = QColor(colores["acento"])  # Resalta la selección fija en azul.
        base = QColor(colores["panel"])  # Obtiene el color base del tema para el hover.
        acento = QColor(colores["acento"])  # Obtiene el color de acento actual.
        delegado.color_hover = QColor(round(base.red() * 0.52 + acento.red() * 0.48), round(base.green() * 0.52 + acento.green() * 0.48), round(base.blue() * 0.52 + acento.blue() * 0.48))  # Mantiene el mismo azul tenue del visor.
        delegado.texto_normal = QColor(colores["texto"])  # Conserva el texto legible en el fondo y al pasar el mouse.
        delegado.texto_seleccion = QColor(colores["texto_inverso"])  # Contrasta el texto de la selección activa.
        self.vista_opciones.viewport().update()  # Solicita repintar el listado con los colores nuevos.
        ventana = self.vista_opciones.window()  # Recupera el contenedor flotante del mismo QComboBox.
        ventana.setObjectName("MarcoOpcionesTriplo")  # Usa el mismo selector CSS que la versión visual aprobada.
        ventana.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Habilita el fondo redondeado del popup.
        ventana.setStyleSheet(f"QFrame#MarcoOpcionesTriplo {{ background-color: {colores['panel']}; border: 1px solid {colores['borde_fuerte']}; border-radius: 10px; }}")  # Reproduce exactamente el borde flotante del visor.
        self.update()  # Redibuja la flecha nativa heredada al cambiar de tema.
