# ============================================================
# Archivo: barra_titulo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la barra de título personalizada de
# TecNet Finder.
#
# Sustituye la barra estándar de Windows por una barra propia
# que conserva las acciones de minimizar y cerrar, además de
# incorporar un botón exclusivo para entrar o salir del modo
# de pantalla completa.
# ============================================================

from pathlib import Path  # Importa Path para trabajar con la ruta del icono de la aplicación.

from PySide6.QtCore import Qt  # Importa opciones de alineación y comportamiento de widgets.
from PySide6.QtGui import QIcon  # Importa la clase utilizada para cargar el icono de TecNet Finder.
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget  # Importa los componentes necesarios para construir la barra personalizada.


class BarraTitulo(QWidget):  # Representa la barra superior personalizada de la ventana principal.
    def __init__(self, ventana, ruta_icono: Path | None = None):  # Recibe la ventana que controlará y opcionalmente la ruta de su icono.
        super().__init__(ventana)  # Establece la ventana principal como propietaria de la barra.
        self.ventana = ventana  # Conserva la referencia utilizada por los botones de control.
        self.setObjectName("BarraTitulo")  # Permite aplicar estilos específicos desde estilos.py.
        self.setFixedHeight(38)  # Mantiene una altura similar a una barra de título convencional.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente icono, nombre y controles.
        diseno.setContentsMargins(10, 0, 0, 0)  # Deja espacio antes del icono y elimina margen en los controles.
        diseno.setSpacing(8)  # Define una separación pequeña entre icono y nombre.

        self.etiqueta_icono = QLabel()  # Crea el espacio destinado al icono pequeño de la aplicación.
        self.etiqueta_icono.setFixedSize(22, 22)  # Mantiene el icono con dimensiones propias de una barra de título.

        if ruta_icono is not None and ruta_icono.exists():  # Comprueba que exista el archivo antes de intentar mostrarlo.
            icono = QIcon(str(ruta_icono))  # Carga el icono utilizando la ruta recibida.
            self.etiqueta_icono.setPixmap(icono.pixmap(18, 18))  # Genera una versión pequeña adecuada para la barra.

        diseno.addWidget(self.etiqueta_icono)  # Coloca el icono a la izquierda de la barra.

        self.etiqueta_titulo = QLabel("TecNet Finder")  # Muestra el nombre de la aplicación como lo haría una barra convencional.
        self.etiqueta_titulo.setObjectName("TituloBarra")  # Aplica el estilo correspondiente al texto de la barra.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Mantiene el texto alineado verticalmente.
        diseno.addWidget(self.etiqueta_titulo)  # Coloca el nombre inmediatamente después del icono.
        diseno.addStretch()  # Empuja los controles de ventana hacia el extremo derecho.

        self.boton_minimizar = self._crear_boton("─", "BotonVentana", "Minimizar")  # Crea el control utilizado para minimizar TecNet Finder.
        self.boton_pantalla_completa = self._crear_boton("⛶", "BotonPantallaCompleta", "Pantalla completa (F11)")  # Crea el control exclusivo para fullscreen.
        self.boton_cerrar = self._crear_boton("✕", "BotonCerrar", "Cerrar")  # Crea el botón encargado de finalizar la aplicación.

        self.boton_minimizar.clicked.connect(self.ventana.minimizar_animado)  # Ejecuta una transición suave antes de minimizar la aplicación.
        self.boton_pantalla_completa.clicked.connect(self.ventana.alternar_pantalla_completa)  # Alterna suavemente entre maximizado y pantalla completa.
        self.boton_cerrar.clicked.connect(self.ventana.close)  # Solicita el cierre; closeEvent se encargará de animarlo.

        diseno.addWidget(self.boton_minimizar)  # Coloca minimizar como primer control.
        diseno.addWidget(self.boton_pantalla_completa)  # Coloca fullscreen inmediatamente después.
        diseno.addWidget(self.boton_cerrar)  # Coloca cerrar en el extremo derecho.

    def _crear_boton(self, texto: str, nombre_objeto: str, ayuda: str) -> QPushButton:  # Construye de forma uniforme cada control de la barra.
        boton = QPushButton(texto)  # Crea el botón utilizando el símbolo recibido.
        boton.setObjectName(nombre_objeto)  # Permite aplicar un estilo distinto según el tipo de control.
        boton.setFixedSize(46, 38)  # Utiliza dimensiones similares a los botones de una barra de Windows.
        boton.setToolTip(ayuda)  # Muestra una explicación breve al colocar el cursor encima.
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita que los controles roben el foco al editor mediante Tab.
        return boton  # Devuelve el botón completamente configurado.

    def actualizar_estado_pantalla_completa(self, pantalla_completa: bool) -> None:  # Actualiza la ayuda del botón según el estado actual.
        if pantalla_completa:  # Comprueba si TecNet Finder está ocupando actualmente toda la pantalla.
            self.boton_pantalla_completa.setToolTip("Salir de pantalla completa (F11)")  # Indica que una nueva pulsación regresará al modo maximizado.
        else:  # Se ejecuta cuando la aplicación se encuentra maximizada.
            self.boton_pantalla_completa.setToolTip("Pantalla completa (F11)")  # Indica que el botón permite entrar a fullscreen.