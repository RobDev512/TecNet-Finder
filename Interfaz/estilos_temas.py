# ============================================================
# Archivo: estilos_temas.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Construye la apariencia dinámica correspondiente con el tema
# seleccionado por el usuario.
#
# estilos.py conserva estructura, tamaños, radios y geometría.
# Este archivo sobrescribe todos los colores variables.
#
# Las reglas específicas de los botones de ventana también se
# redefinen aquí para impedir que sus estilos oscuros originales
# tengan prioridad dentro de los temas claros.
# ============================================================

from Interfaz.estilos import ESTILO_APLICACION  # Recupera la estructura visual base de TecNet Finder.
from Motor.catalogo_temas import obtener_tema  # Recupera la paleta previamente validada.


def construir_estilo_aplicacion(tema_id: str, familia_interfaz: str, tamano_interfaz: int, familia_editor: str, tamano_editor: int) -> str:
    p = obtener_tema(tema_id)  # Recupera una copia segura de la paleta solicitada.
    familia_interfaz = _escapar_fuente(familia_interfaz)  # Protege el nombre de la fuente antes de insertarlo en QSS.
    familia_editor = _escapar_fuente(familia_editor)  # Protege igualmente la fuente independiente del editor.

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

/* ===========================================================
   Controles de la barra superior
   =========================================================== */

QPushButton#BotonVentana,
QPushButton#BotonPantallaCompleta,
QPushButton#BotonCerrar {{
    background-color: transparent;
    border: none;
    border-radius: 0px;
    padding: 0px;
}}

QPushButton#BotonVentana:hover {{
    background-color: {p["superficie"]};
    border: none;
}}

QPushButton#BotonPantallaCompleta:hover {{
    background-color: {p["superficie_hover"]};
    border: none;
}}

QPushButton#BotonVentana:pressed,
QPushButton#BotonPantallaCompleta:pressed {{
    background-color: {p["superficie_presionada"]};
    border: none;
}}

QPushButton#BotonCerrar:hover {{
    background-color: #c42b1c;
    border: none;
}}

QPushButton#BotonCerrar:pressed {{
    background-color: #a52016;
    border: none;
}}

/* ===========================================================
   Menús
   =========================================================== */

QMenu {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QMenuBar#MenuPrincipal::item:selected, QMenu::item:selected {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
}}

/* ===========================================================
   Paneles y Configuración
   =========================================================== */

QFrame#Panel, QFrame#PanelAsistenciaIA {{
    background-color: {p["panel"]};
    border-color: {p["borde"]};
}}

QFrame#TarjetaConfiguracion {{
    background-color: {p["panel"]};
    border: 1px solid {p["borde_fuerte"]};
    border-radius: 8px;
}}

QFrame#PieConfiguracion {{
    background-color: {p["panel"]};
    border-top-color: {p["borde"]};
}}

QLabel#TituloPrincipal,
QLabel#TituloSeccion,
QLabel#TituloResumen,
QLabel#TituloDialogoIA,
QLabel#TituloConfiguracion {{
    color: {p["acento"]};
}}

QLabel#SubtituloPrincipal,
QLabel#DescripcionDialogoIA,
QLabel#EstadoIANeutral,
QLabel#TituloTarjeta,
QLabel#DescripcionConfiguracion {{
    color: {p["texto_secundario"]};
}}

QLabel#SubtituloConfiguracion,
QLabel#TextoConfiguracion,
QLabel#TituloVentanaConfiguracion {{
    color: {p["texto"]};
}}

/* ===========================================================
   Tarjetas de resumen
   =========================================================== */

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

QLabel#ValorTokens {{
    color: {p["acento"]};
}}

QLabel#ValorBloques,
QLabel#EstadoIACorrecto {{
    color: {p["exito"]};
}}

QLabel#ValorSubredes {{
    color: {p["subred"]};
}}

QLabel#ValorLexicos {{
    color: {p["error"]};
}}

QLabel#ValorSintacticos {{
    color: {p["sintactico"]};
}}

QLabel#ValorAdvertencias,
QLabel#EstadoIAAdvertencia {{
    color: {p["advertencia"]};
}}

/* ===========================================================
   Estados
   =========================================================== */

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

/* ===========================================================
   Botones generales
   =========================================================== */

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
    border: 1px solid {p["acento"]};
}}

QPushButton#BotonPrincipal:hover {{
    background-color: {p["acento_hover"]};
    color: {p["texto_inverso"]};
    border: 1px solid {p["acento_hover"]};
}}

/* ===========================================================
   Botones flotantes
   =========================================================== */

QPushButton#BotonFlotantePanel {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border: 1px solid {p["borde"]};
}}

QPushButton#BotonFlotantePanel:hover {{
    background-color: {p["superficie"]};
    border-color: {p["acento"]};
}}

QPushButton#BotonFlotantePanel:pressed {{
    background-color: {p["superficie_hover"]};
    border-color: {p["acento"]};
}}

QPushButton#BotonFlotantePanel:disabled {{
    background-color: {p["panel"]};
    color: {p["texto_deshabilitado"]};
    border-color: {p["borde"]};
}}

/* ===========================================================
   Casillas
   =========================================================== */

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

/* ===========================================================
   Editores y campos
   =========================================================== */

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

/* ===========================================================
   Tablas
   =========================================================== */

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

/* ===========================================================
   Pestañas
   =========================================================== */

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

/* ===========================================================
   Tooltips y listas
   =========================================================== */

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

QListWidget#ListaConfiguracion::item:hover {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
}}

QListWidget#ListaConfiguracion::item:selected,
QListWidget#ListaConfiguracion::item:selected:hover {{
    background-color: {p["superficie_hover"]};
    color: {p["acento"]};
}}

/* ===========================================================
   Configuración
   =========================================================== */

QStackedWidget#PanelesConfiguracion,
QStackedWidget#ZonaAdministracionIA,
QWidget#PaginaAdministracionIA {{
    background-color: {p["fondo"]};
}}

QScrollArea#AreaDesplazamientoConfiguracion,
QScrollArea#AreaDesplazamientoConfiguracion > QWidget > QWidget {{
    background-color: {p["fondo"]};
    border: none;
}}

QScrollArea, QAbstractScrollArea {{
    color: {p["texto"]};
    border-color: {p["borde"]};
}}

/* ===========================================================
   Scrollbars
   =========================================================== */

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

/* ===========================================================
   Controles especiales
   =========================================================== */

QPushButton#CasillaIA {{
    background-color: {p["editor"]};
    color: {p["texto"]};
    border: 1px solid {p["borde_fuerte"]};
    border-radius: 4px;
    padding: 0px;
}}

QPushButton#CasillaIA:hover {{
    background-color: {p["panel"]};
    color: {p["texto"]};
    border: 1px solid {p["acento"]};
}}

QPushButton#CasillaIA:disabled {{
    background-color: {p["fondo_deshabilitado"]};
    color: {p["texto_deshabilitado"]};
    border: 1px solid {p["borde_deshabilitado"]};
}}

QPushButton#BotonPrincipal:disabled {{
    background-color: {p["superficie"]};
    color: {p["texto_deshabilitado"]};
    border: 1px solid {p["borde_deshabilitado"]};
}}

QProgressBar {{
    background-color: {p["editor"]};
    color: {p["texto"]};
    border-color: {p["borde_fuerte"]};
}}

QProgressBar::chunk {{
    background-color: {p["acento"]};
}}

/* ===========================================================
   Árbol sintáctico
   =========================================================== */

QPushButton#BotonGuardarArbol {{
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border: 1px solid {p["borde_fuerte"]};
    border-radius: 7px;
    padding: 0px;
}}

QPushButton#BotonGuardarArbol:hover {{
    background-color: {p["superficie_hover"]};
    border-color: {p["acento"]};
}}

QPushButton#BotonGuardarArbol:pressed {{
    background-color: {p["superficie_presionada"]};
    border-color: {p["acento"]};
}}

/* ===========================================================
   Cuadros de confirmación
   =========================================================== */

QMessageBox {{
    background-color: {p["fondo"]};
    color: {p["texto"]};
}}

QMessageBox QLabel {{
    background-color: transparent;
    color: {p["texto"]};
}}

QMessageBox QPushButton {{
    min-width: 78px;
    min-height: 30px;
    background-color: {p["superficie"]};
    color: {p["texto"]};
    border: 1px solid {p["borde_fuerte"]};
    border-radius: 7px;
    padding: 6px 12px;
    font-weight: bold;
}}

QMessageBox QPushButton:hover {{
    background-color: {p["superficie_hover"]};
    border-color: {p["acento"]};
}}

QMessageBox QPushButton:pressed {{
    background-color: {p["superficie_presionada"]};
}}
"""  # Las reglas dinámicas se añaden después del estilo estructural original.

    return ESTILO_APLICACION + estilo_tema  # Da prioridad a la paleta dinámica sin duplicar la estructura completa.


def _escapar_fuente(familia: str) -> str:
    return str(familia).replace("\\", "\\\\").replace('"', '\\"')  # Protege caracteres capaces de romper una cadena QSS.