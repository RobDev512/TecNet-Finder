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
#
# Los controles utilizan iconos PNG propios y pueden cambiar
# su imagen de acuerdo con su estado visual.
# ============================================================

from pathlib import Path  # Importa Path para localizar los recursos gráficos mediante rutas relativas.

from PySide6.QtCore import QSize, Qt  # Importa tamaños y opciones utilizadas por los controles de la barra.
from PySide6.QtGui import QIcon  # Importa la clase utilizada para representar iconos PNG.
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget  # Importa los componentes necesarios para construir la barra personalizada.


class BotonIconoEstado(QPushButton):  # Define un botón capaz de cambiar su icono según el estado visual.
    def __init__(self, padre=None):  # Inicializa el botón y prepara sus posibles iconos.
        super().__init__(padre)  # Inicializa el comportamiento estándar de QPushButton.
        self.icono_normal = QIcon()  # Guarda el icono utilizado cuando el botón está en reposo.
        self.icono_hover = QIcon()  # Guarda el icono utilizado cuando el puntero se encuentra encima.
        self.icono_presionado = QIcon()  # Guarda el icono utilizado mientras el botón está presionado.
        self.puntero_encima = False  # Indica si el mouse se encuentra actualmente sobre el botón.
        self.esta_presionado = False  # Indica si el botón se encuentra actualmente presionado.

    def establecer_iconos(
        self,
        ruta_normal: Path,
        ruta_hover: Path | None = None,
        ruta_presionado: Path | None = None,
    ) -> None:  # Configura las imágenes utilizadas por cada estado del botón.
        self.icono_normal = self._cargar_icono(ruta_normal)  # Carga el icono utilizado en el estado normal.
        self.icono_hover = self._cargar_icono(ruta_hover) if ruta_hover is not None else self.icono_normal  # Utiliza una variante hover cuando existe.
        self.icono_presionado = self._cargar_icono(ruta_presionado) if ruta_presionado is not None else self.icono_hover  # Utiliza una variante específica o reutiliza hover.
        self._actualizar_icono()  # Aplica inmediatamente el icono correspondiente al estado actual.

    def _cargar_icono(self, ruta: Path) -> QIcon:  # Convierte un archivo PNG existente en un icono de Qt.
        if ruta.exists():  # Comprueba que el recurso realmente exista.
            return QIcon(str(ruta))  # Devuelve el icono construido desde el archivo recibido.

        return QIcon()  # Devuelve un icono vacío para mantener funcional la interfaz si falta un recurso.

    def _actualizar_icono(self) -> None:  # Selecciona el icono correspondiente al estado actual del botón.
        if self.esta_presionado:  # Comprueba si el usuario mantiene el botón presionado.
            self.setIcon(self.icono_presionado)  # Muestra la variante correspondiente al estado presionado.
        elif self.puntero_encima:  # Comprueba si el mouse permanece sobre el botón.
            self.setIcon(self.icono_hover)  # Muestra la variante utilizada durante hover.
        else:  # Se ejecuta cuando el botón se encuentra completamente en reposo.
            self.setIcon(self.icono_normal)  # Recupera el icono normal.

    def enterEvent(self, evento) -> None:  # Detecta cuando el puntero entra en el área del botón.
        self.puntero_encima = True  # Registra que el control está siendo señalado.
        self._actualizar_icono()  # Actualiza inmediatamente su apariencia.
        super().enterEvent(evento)  # Conserva el comportamiento estándar de Qt.

    def leaveEvent(self, evento) -> None:  # Detecta cuando el puntero abandona el botón.
        self.puntero_encima = False  # Registra que el mouse dejó de señalar el control.
        self.esta_presionado = False  # Evita conservar visualmente el estado presionado.
        self._actualizar_icono()  # Recupera el icono normal.
        super().leaveEvent(evento)  # Conserva el comportamiento estándar de Qt.

    def mousePressEvent(self, evento) -> None:  # Detecta el inicio de una pulsación sobre el botón.
        if evento.button() == Qt.MouseButton.LeftButton:  # Comprueba que se utilizó el botón principal del mouse.
            self.esta_presionado = True  # Registra temporalmente el estado presionado.
            self._actualizar_icono()  # Muestra la variante correspondiente.

        super().mousePressEvent(evento)  # Permite que QPushButton procese normalmente la pulsación.

    def mouseReleaseEvent(self, evento) -> None:  # Detecta cuando el usuario deja de presionar el botón.
        if evento.button() == Qt.MouseButton.LeftButton:  # Comprueba que terminó la pulsación principal.
            self.esta_presionado = False  # Libera el estado visual presionado.
            self._actualizar_icono()  # Recupera hover o normal según la posición del puntero.

        super().mouseReleaseEvent(evento)  # Permite que QPushButton emita normalmente la señal clicked.


class BarraTitulo(QWidget):  # Representa la barra superior personalizada de la ventana principal.
    def __init__(self, ventana, ruta_icono: Path | None = None):  # Recibe la ventana que controlará y opcionalmente la ruta de su logotipo.
        super().__init__(ventana)  # Establece la ventana principal como propietaria de la barra.
        self.ventana = ventana  # Conserva la referencia utilizada por los botones de control.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.

        self.setObjectName("BarraTitulo")  # Permite aplicar estilos específicos desde estilos.py.
        self.setFixedHeight(38)  # Mantiene una altura similar a una barra de título convencional.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente logotipo, nombre y controles.
        diseno.setContentsMargins(10, 0, 0, 0)  # Deja espacio antes del logotipo y elimina margen en los controles.
        diseno.setSpacing(8)  # Define una separación pequeña entre logotipo y nombre.

        self.etiqueta_icono = QLabel()  # Crea el espacio destinado al icono pequeño de la aplicación.
        self.etiqueta_icono.setFixedSize(22, 22)  # Mantiene dimensiones apropiadas para la barra.

        if ruta_icono is not None and ruta_icono.exists():  # Comprueba que el logotipo realmente exista.
            icono = QIcon(str(ruta_icono))  # Carga el icono general utilizando la ruta recibida.
            self.etiqueta_icono.setPixmap(icono.pixmap(18, 18))  # Genera una versión pequeña apropiada para la barra.

        diseno.addWidget(self.etiqueta_icono)  # Coloca el logotipo a la izquierda de la barra.

        self.etiqueta_titulo = QLabel("TecNet Finder")  # Muestra el nombre de la aplicación.
        self.etiqueta_titulo.setObjectName("TituloBarra")  # Aplica el estilo correspondiente al texto.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Mantiene el título correctamente alineado.
        diseno.addWidget(self.etiqueta_titulo)  # Coloca el nombre inmediatamente después del logotipo.
        diseno.addStretch()  # Empuja los controles de ventana hacia el extremo derecho.

        self.boton_minimizar = self._crear_boton("BotonVentana", "Minimizar")  # Crea el control utilizado para minimizar TecNet Finder.
        self.boton_pantalla_completa = self._crear_boton("BotonPantallaCompleta", "Pantalla completa (F11)")  # Crea el control utilizado para pantalla completa.
        self.boton_cerrar = self._crear_boton("BotonCerrar", "Cerrar")  # Crea el botón encargado de finalizar la aplicación.

        self.boton_minimizar.establecer_iconos(  # Configura el icono utilizado para minimizar.
            self.ruta_iconos / "Minimizar.png",
        )

        self.boton_pantalla_completa.establecer_iconos(  # Configura las variantes iniciales del botón de pantalla completa.
            self.ruta_iconos / "Pantalla_completa.png",
            self.ruta_iconos / "Pantalla_completa_hover.png",
        )

        self.boton_cerrar.establecer_iconos(  # Configura las variantes utilizadas por el control de cierre.
            self.ruta_iconos / "Cerrar.png",
            self.ruta_iconos / "Cerrar_activo.png",
            self.ruta_iconos / "Cerrar_activo.png",
        )

        self.boton_minimizar.clicked.connect(self.ventana.minimizar_animado)  # Ejecuta una transición suave antes de minimizar.
        self.boton_pantalla_completa.clicked.connect(self.ventana.alternar_pantalla_completa)  # Alterna entre maximizado y pantalla completa.
        self.boton_cerrar.clicked.connect(self.ventana.close)  # Solicita el cierre para que closeEvent ejecute su animación.

        diseno.addWidget(self.boton_minimizar)  # Coloca minimizar como primer control.
        diseno.addWidget(self.boton_pantalla_completa)  # Coloca pantalla completa inmediatamente después.
        diseno.addWidget(self.boton_cerrar)  # Coloca cerrar en el extremo derecho.

    def _crear_boton(self, nombre_objeto: str, ayuda: str) -> BotonIconoEstado:  # Construye uniformemente cada control gráfico de la barra.
        boton = BotonIconoEstado(self)  # Crea un botón preparado para manejar variantes visuales.
        boton.setObjectName(nombre_objeto)  # Permite aplicar el estilo correspondiente desde estilos.py.
        boton.setFixedSize(46, 38)  # Utiliza dimensiones similares a los controles convencionales de Windows.
        boton.setIconSize(QSize(16, 16))  # Reduce los PNG a un tamaño apropiado para la barra.
        boton.setToolTip(ayuda)  # Muestra una explicación breve al colocar el cursor encima.
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita que los controles interfieran con la navegación mediante Tab.
        return boton  # Devuelve el botón completamente configurado.

    def actualizar_estado_pantalla_completa(self, pantalla_completa: bool) -> None:  # Cambia ayuda e iconos según el estado real de la ventana.
        if pantalla_completa:  # Comprueba si TecNet Finder está ocupando actualmente toda la pantalla.
            self.boton_pantalla_completa.setToolTip("Salir de pantalla completa (F11)")  # Explica la nueva función del control.
            self.boton_pantalla_completa.establecer_iconos(  # Sustituye expandir por las variantes utilizadas para abandonar fullscreen.
                self.ruta_iconos / "Salir_pantalla_completa.png",
                self.ruta_iconos / "Salir_pantalla_completa_hover.png",
            )
        else:  # Se ejecuta cuando TecNet Finder se encuentra maximizado.
            self.boton_pantalla_completa.setToolTip("Pantalla completa (F11)")  # Explica que el control permitirá entrar a fullscreen.
            self.boton_pantalla_completa.establecer_iconos(  # Recupera las variantes utilizadas para entrar a pantalla completa.
                self.ruta_iconos / "Pantalla_completa.png",
                self.ruta_iconos / "Pantalla_completa_hover.png",
            )