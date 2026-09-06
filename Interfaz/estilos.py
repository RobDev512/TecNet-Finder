# ============================================================
# Archivo: estilos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el estilo visual general de la interfaz
# gráfica de TecNet Finder desarrollada con PySide6.
#
# Centralizar los estilos permite modificar posteriormente la
# apariencia de la aplicación sin mezclar diseño visual con la
# lógica de los demás componentes.
# ============================================================

ESTILO_APLICACION = """  /* Define la hoja de estilos general utilizada por toda la aplicación. */

QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Consolas";
    font-size: 10pt;
}

QFrame#Panel {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
}

QLabel#TituloPrincipal {
    color: #89b4fa;
    font-size: 19pt;
    font-weight: bold;
}

QLabel#SubtituloPrincipal {
    color: #a6adc8;
    font-size: 10pt;
}

QLabel#TituloSeccion {
    color: #89b4fa;
    font-weight: bold;
    font-size: 11pt;
}

QLabel#EstadoNeutral {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px;
}

QLabel#EstadoCorrecto {
    background-color: #181825;
    color: #a6e3a1;
    border: 1px solid #a6e3a1;
    border-radius: 6px;
    padding: 7px;
    font-weight: bold;
}

QLabel#EstadoError {
    background-color: #181825;
    color: #f38ba8;
    border: 1px solid #f38ba8;
    border-radius: 6px;
    padding: 7px;
    font-weight: bold;
}

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 7px;
    padding: 8px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}

QPushButton:pressed {
    background-color: #585b70;
}

QPushButton#BotonPrincipal {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: 1px solid #89b4fa;
}

QPushButton#BotonPrincipal:hover {
    background-color: #b4befe;
}

QPlainTextEdit {
    background-color: #11111b;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 5px;
    selection-background-color: #45475a;
}

QTableWidget {
    background-color: #11111b;
    alternate-background-color: #181825;
    color: #cdd6f4;
    gridline-color: #313244;
    border: 1px solid #313244;
    selection-background-color: #45475a;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    padding: 6px;
    font-weight: bold;
}

QTabWidget::pane {
    border: 1px solid #313244;
    background-color: #181825;
}

QTabBar::tab {
    background-color: #313244;
    color: #cdd6f4;
    padding: 7px 13px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}

QSplitter::handle {
    background-color: #313244;
}

QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #89b4fa;
}
"""