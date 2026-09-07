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
# apariencia sin mezclar diseño visual con la lógica de los
# componentes de la aplicación.
# ============================================================

ESTILO_APLICACION = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Consolas";
    font-size: 10pt;
}

QWidget#VentanaCentral {
    background-color: #1e1e2e;
}

QWidget#ContenidoPrincipal {
    background-color: #1e1e2e;
}

QWidget#BarraTitulo {
    background-color: #181825;
    border-bottom: 1px solid #313244;
}

QLabel#TituloBarra {
    background-color: transparent;
    color: #cdd6f4;
    font-family: "Segoe UI";
    font-size: 9pt;
}

QPushButton#BotonVentana,
QPushButton#BotonPantallaCompleta,
QPushButton#BotonCerrar {
    background-color: transparent;
    color: #cdd6f4;
    border: none;
    border-radius: 0px;
    padding: 0px;
    font-family: "Segoe UI Symbol";
    font-size: 12pt;
    font-weight: normal;
}

QPushButton#BotonVentana:hover {
    background-color: #313244;
}

QPushButton#BotonPantallaCompleta:hover {
    background-color: #45475a;
    color: #89b4fa;
}

QPushButton#BotonCerrar:hover {
    background-color: #c42b1c;
    color: white;
}

QPushButton#BotonVentana:pressed,
QPushButton#BotonPantallaCompleta:pressed {
    background-color: #585b70;
}

QPushButton#BotonCerrar:pressed {
    background-color: #a52016;
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

QLabel#TituloResumen {
    color: #89b4fa;
    font-size: 14pt;
    font-weight: bold;
}

QLabel#TituloTarjeta {
    background-color: transparent;
    color: #a6adc8;
    font-size: 9pt;
    font-weight: bold;
}

QFrame#TarjetaTokens,
QFrame#TarjetaBloques,
QFrame#TarjetaSubredes,
QFrame#TarjetaLexicos,
QFrame#TarjetaSintacticos {
    background-color: #181825;
    border-radius: 8px;
}

QFrame#TarjetaTokens {
    border: 1px solid #89b4fa;
}

QFrame#TarjetaBloques {
    border: 1px solid #a6e3a1;
}

QFrame#TarjetaSubredes {
    border: 1px solid #94e2d5;
}

QFrame#TarjetaLexicos {
    border: 1px solid #f38ba8;
}

QFrame#TarjetaSintacticos {
    border: 1px solid #fab387;
}

QLabel#ValorTokens,
QLabel#ValorBloques,
QLabel#ValorSubredes,
QLabel#ValorLexicos,
QLabel#ValorSintacticos {
    background-color: transparent;
    font-size: 22pt;
    font-weight: bold;
}

QLabel#ValorTokens {
    color: #89b4fa;
}

QLabel#ValorBloques {
    color: #a6e3a1;
}

QLabel#ValorSubredes {
    color: #94e2d5;
}

QLabel#ValorLexicos {
    color: #f38ba8;
}

QLabel#ValorSintacticos {
    color: #fab387;
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

QTabBar::tab:hover {
    background-color: #45475a;
}

QTabBar::tab:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}

QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #89b4fa;
}
"""