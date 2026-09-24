# ============================================================
# Archivo: control_placeholder_editor.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Mantiene el ejemplo visual del editor sincronizado con el
# idioma confirmado sin convertirlo en texto real del documento.
#
# El placeholder:
# - conserva IP, MASK, HOSTS y NAME como palabras del DSL;
# - localiza únicamente el prefijo y el identificador de ejemplo;
# - utiliza una opacidad reducida para no competir visualmente
#   con el código escrito por el usuario.
# ============================================================

from PySide6.QtGui import QColor, QPalette

from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class ControlPlaceholderEditor:
    OPACIDAD_PLACEHOLDER = 0.52

    def __init__(self, ventana):
        self.ventana = ventana
        self.gestor = GestorTraducciones("es")

    def establecer_idioma(self, idioma: str) -> bool:
        if not self.gestor.establecer_idioma(idioma):
            return False

        self.aplicar()
        return True

    def aplicar(self) -> None:
        editor = self.ventana.editor_codigo
        editor.setPlaceholderText(
            self.gestor.traducir("principal.editor.placeholder_ejemplo")
        )

        paleta = editor.palette()
        color = QColor(
            getattr(editor, "COLOR_PLACEHOLDER", "#6c7086")
        )
        color.setAlphaF(self.OPACIDAD_PLACEHOLDER)
        paleta.setColor(QPalette.ColorRole.PlaceholderText, color)
        editor.setPalette(paleta)
        editor.viewport().update()
