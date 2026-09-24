# ============================================================
# Archivo: prueba_placeholder_editor_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que el ejemplo visual del editor exista en los seis
# idiomas, conserve las palabras reservadas del DSL y se aplique
# con una opacidad reducida.
# ============================================================

import json

from PySide6.QtGui import QPalette

from Interfaz.internacionalizacion.control_placeholder_editor import (
    ControlPlaceholderEditor,
)
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class _EditorFalso:
    COLOR_PLACEHOLDER = "#6c7086"

    def __init__(self):
        self.texto_placeholder = ""
        self._paleta = QPalette()
        self.viewport_actualizado = False

    def setPlaceholderText(self, texto):
        self.texto_placeholder = texto

    def palette(self):
        return QPalette(self._paleta)

    def setPalette(self, paleta):
        self._paleta = QPalette(paleta)

    def viewport(self):
        return self

    def update(self):
        self.viewport_actualizado = True


class _VentanaFalsa:
    def __init__(self):
        self.editor_codigo = _EditorFalso()


def prueba_seis_catalogos_tienen_placeholder_localizado():
    gestor = GestorTraducciones("es")

    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = gestor.ruta_catalogos / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        texto = datos["principal.editor.placeholder_ejemplo"]

        assert texto
        assert "IP " in texto
        assert " MASK " in texto
        assert " HOSTS " in texto
        assert " NAME " in texto


def prueba_placeholder_cambia_con_el_idioma():
    ventana = _VentanaFalsa()
    control = ControlPlaceholderEditor(ventana)

    assert control.establecer_idioma("en")
    assert ventana.editor_codigo.texto_placeholder.startswith("Example:")
    assert ventana.editor_codigo.texto_placeholder.endswith("NAME Office")

    assert control.establecer_idioma("es")
    assert ventana.editor_codigo.texto_placeholder.startswith("Ejemplo:")
    assert ventana.editor_codigo.texto_placeholder.endswith("NAME Oficina")


def prueba_placeholder_se_muestra_con_opacidad_reducida():
    ventana = _VentanaFalsa()
    control = ControlPlaceholderEditor(ventana)

    assert control.establecer_idioma("en")

    color = ventana.editor_codigo._paleta.color(
        QPalette.ColorRole.PlaceholderText
    )
    assert 0.45 <= color.alphaF() <= 0.60
    assert ventana.editor_codigo.viewport_actualizado
