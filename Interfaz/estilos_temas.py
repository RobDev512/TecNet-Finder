# ============================================================
# Archivo: estilos_temas.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Construye la apariencia dinámica correspondiente con el tema
# seleccionado por el usuario.
#
# estilos.py continúa conservando la estructura visual:
# - Márgenes.
# - Padding.
# - Radios.
# - Tamaños.
# - Geometría.
#
# Este archivo sobrescribe después los colores que dependen de
# la variante seleccionada sin duplicar toda la hoja principal.
# ============================================================

from Interfaz.estilos import ESTILO_APLICACION  # Recupera la estructura visual base de TecNet Finder.
from Motor.catalogo_temas import obtener_tema  # Recupera la paleta previamente validada.


def construir_estilo_aplicacion(tema_id: str, familia_interfaz: str, tamano_interfaz: int, familia_editor: str, tamano_editor: int) -> str:
    p = obtener_tema(tema_id)  # Recupera una copia de la paleta solicitada.
    familia_interfaz = _escapar_fuente(familia_interfaz)  # Protege la familia general antes de insertarla dentro de QSS.
    familia_editor = _escapar_fuente(familia_editor)  # Protege igualmente la familia independiente del editor.

    estilo_tema = f"""
/* ===========================================================
   Tema dinámico de TecNet Finder
   =========================================================== */

QWidget {{
    background-color: {p["fondo"]};
    color: {p["texto"]};
    font-family: "{familia_interfaz}";
    font-size: {tamano_interfaz}pt;
}}

QMainWindow, QDialog, QWidget#VentanaCentral, QWidget#ContenidoPrincipal {{
    background-color: {p["fondo"]};
    color: {p["texto"]};
}}

QWidget#BarraTitulo, QMenuBar#MenuPrincipal {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border-bottom-color: {p["borde"]};
}}

QLabel#TituloBarra {{
    background-color: transparent;
    color: {p["texto"]};
}}

QMenu {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QMenuBar#MenuPrincipal::item:selected, QMenu::item:selected {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
}}

QFrame#Panel, QFrame#PanelAsistenciaIA, QFrame#TarjetaConfiguracion {{
    background-color: {p["panel"]};
    border-color: {p["borde"]};
}}

QFrame#PieConfiguracion {{
    background-color: {p["panel"]};
    border-top-color: {p["borde"]};
}}

QLabel#TituloPrincipal, QLabel#TituloSeccion, QLabel#TituloResumen, QLabel#TituloDialogoIA, QLabel#TituloConfiguracion {{
    color: {p["acento"]};
}}

QLabel#SubtituloPrincipal, QLabel#DescripcionDialogoIA, QLabel#EstadoIANeutral, QLabel#TituloTarjeta, QLabel#DescripcionConfiguracion {{
    color: {p["texto_secundario"]};
}}

QLabel#SubtituloConfiguracion, QLabel#TextoConfiguracion, QLabel#TituloVentanaConfiguracion {{
    color: {p["texto"]};
}}

QFrame#TarjetaTokens {{
    background-color: {p["panel"]};
    border-color: {p["acento"]};
}}

QFrame#TarjetaBloques {{
    background-color: {p["panel"]};
    border-color: {p["exito"]};
}}

QFrame#TarjetaSubredes {{
    background-color: {p["panel"]};
    border-color: {p["subred"]};
}}

QFrame#TarjetaLexicos {{
    background-color: {p["panel"]};
    border-color: {p["error"]};
}}

QFrame#TarjetaSintacticos {{
    background-color: {p["panel"]};
    border-color: {p["sintactico"]};
}}

QFrame#TarjetaAdvertencias {{
    background-color: {p["panel"]};
    border-color: {p["advertencia"]};
}}

QLabel#ValorTokens {{ color: {p["acento"]}; }}
QLabel#ValorBloques, QLabel#EstadoIACorrecto {{ color: {p["exito"]}; }}
QLabel#ValorSubredes {{ color: {p["subred"]}; }}
QLabel#ValorLexicos {{ color: {p["error"]}; }}
QLabel#ValorSintacticos {{ color: {p["sintactico"]}; }}
QLabel#ValorAdvertencias, QLabel#EstadoIAAdvertencia {{ color: {p["advertencia"]}; }}

QLabel#EstadoNeutral {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QLabel#EstadoCorrecto {{
    background-color: {p["panel"]};
    color: {p["exito"]};
    border-color: {p["exito"]};
}}

QLabel#EstadoAdvertencia {{
    background-color: {p["panel"]};
    color: {p["advertencia"]};
    border-color: {p["advertencia"]};
}}

QLabel#EstadoError {{
    background-color: {p["panel"]};
    color: {p["error"]};
    border-color: {p["error"]};
}}

QPushButton {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QPushButton:hover {{
    background-color: {p["superficie_hover"]};
    border-color: {p["acento"]};
}}

QPushButton:pressed {{
    background-color: {p["superficie_presionada"]};
}}

QPushButton:disabled {{
    background-color: {p["fondo_deshabilitado"]};
    color: {p["texto_deshabilitado"]};
    border-color: {p["borde_deshabilitado"]};
}}

QPushButton#BotonPrincipal {{
    background-color: {p["acento"]};
    color: {p["texto_inverso"]};
    border-color: {p["acento"]};
}}

QPushButton#BotonPrincipal:hover {{
    background-color: {p["acento_hover"]};
    color: {p["texto_inverso"]};
    border-color: {p["acento_hover"]};
}}

QPushButton#BotonFlotantePanel {{
    background-color: {p["superficie_hover"]};
    color: {p["texto"]};
    border-color: {p["superficie_presionada"]};
}}

QPushButton#BotonFlotantePanel:hover {{
    background-color: {p["superficie_presionada"]};
    border-color: {p["acento"]};
}}

QPushButton#BotonFlotantePanel:disabled {{
    background-color: {p["fondo_deshabilitado"]};
    color: {p["texto_deshabilitado"]};
    border-color: {p["borde_deshabilitado"]};
}}

QCheckBox {{
    color: {p["texto"]};
}}

QCheckBox::indicator:unchecked {{
    background-color: {p["editor"]};
    border-color: {p["borde_fuerte"]};
}}

QCheckBox::indicator:checked {{
    background-color: {p["acento"]};
    border-color: {p["acento"]};
}}

QCheckBox:disabled {{
    color: {p["texto_deshabilitado"]};
}}

QPlainTextEdit, QTextEdit {{
    background-color: {p["editor"]};
    color: {p["texto"]};
    border-color: {p["borde"]};
    selection-background-color: {p["acento"]};
    selection-color: {p["texto_inverso"]};
}}

QPlainTextEdit#EditorCodigo {{
    font-family: "{familia_editor}";
    font-size: {tamano_editor}pt;
}}

QLineEdit, QSpinBox {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
    selection-background-color: {p["acento"]};
    selection-color: {p["texto_inverso"]};
}}

QLineEdit:hover, QSpinBox:hover {{
    border-color: {p["superficie_presionada"]};
}}

QLineEdit:focus, QSpinBox:focus {{
    border-color: {p["acento"]};
}}

QTableWidget {{
    background-color: {p["editor"]};
    alternate-background-color: {p["panel"]};
    color: {p["texto"]};
    gridline-color: {p["borde"]};
    border-color: {p["borde"]};
    selection-background-color: {p["superficie_hover"]};
    selection-color: {p["texto"]};
}}

QHeaderView::section {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QTabWidget::pane {{
    background-color: {p["panel"]};
    border-color: {p["borde"]};
}}

QTabBar {{
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
    border-bottom-color: {p["superficie"]};
}}

QTabBar::tab:hover {{
    background-color: {p["superficie_hover"]};
    border-color: {p["superficie_presionada"]};
    border-bottom-color: {p["superficie"]};
}}

QTabBar::tab:selected {{
    background-color: {p["acento"]};
    color: {p["texto_inverso"]};
    border-color: {p["acento"]};
    border-bottom-color: {p["panel"]};
}}

QToolTip {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border-color: {p["acento"]};
}}

QListWidget {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border-color: {p["borde"]};
}}

QListWidget::item:hover {{
    background-color: {p["superficie"]};
}}

QListWidget::item:selected {{
    background-color: {p["superficie_hover"]};
    color: {p["texto"]};
}}

QListWidget#ListaConfiguracion {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border-right-color: {p["borde"]};
}}

QListWidget#ListaConfiguracion::item:selected {{
    background-color: {p["superficie_hover"]};
    color: {p["acento"]};
}}

QStackedWidget#PanelesConfiguracion, QStackedWidget#ZonaAdministracionIA, QWidget#PaginaAdministracionIA {{
    background-color: {p["fondo"]};
}}

QScrollArea, QAbstractScrollArea {{
    color: {p["texto"]};
    border-color: {p["borde"]};
}}

QScrollBar:vertical {{
    background-color: transparent;
}}

QScrollBar::handle:vertical {{
    background-color: {p["superficie_hover"]};
}}

QScrollBar::handle:vertical:hover {{
    background-color: {p["superficie_presionada"]};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {p["acento"]};
}}

QScrollBar:horizontal {{
    background-color: transparent;
}}

QScrollBar::handle:horizontal {{
    background-color: {p["superficie_hover"]};
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {p["superficie_presionada"]};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {p["acento"]};
}}

QPushButton#CasillaIA {{
    background-color: {p["editor"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QPushButton#CasillaIA:hover {{
    background-color: {p["panel"]};
    border-color: {p["acento"]};
}}

QProgressBar {{
    background-color: {p["editor"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QProgressBar::chunk {{
    background-color: {p["acento"]};
}}
"""  # Sobrescribe únicamente propiedades cromáticas y tipográficas que dependen del tema.

    return ESTILO_APLICACION + estilo_tema  # Coloca las reglas dinámicas después del estilo base para que tengan prioridad.


def _escapar_fuente(familia: str) -> str:
    return str(familia).replace("\\", "\\\\").replace('"', '\\"')  # Protege caracteres capaces de romper una cadena QSS.