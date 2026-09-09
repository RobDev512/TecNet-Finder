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
# reutilizable que puede mostrar únicamente los controles
# necesarios según la ventana donde sea utilizada.
#
# Los controles utilizan iconos PNG propios y la barra puede
# delegar el movimiento de ventanas secundarias al sistema
# operativo para mantener un desplazamiento fluido.
# ============================================================

from pathlib import Path  # Permite localizar los recursos gráficos mediante rutas relativas.

from PySide6.QtCore import QSize, Qt  # Importa tamaños, estados y opciones utilizadas por la barra personalizada.
from PySide6.QtGui import QIcon  # Permite representar los iconos utilizados por los botones.
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget  # Importa los componentes necesarios para construir la barra personalizada.


class BotonIconoEstado(QPushButton):  # Define un botón capaz de cambiar su icono según el estado visual.
    def __init__(self, padre=None):
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
    ) -> None:
        self.icono_normal = self._cargar_icono(ruta_normal)  # Carga el icono utilizado en el estado normal.
        self.icono_hover = self._cargar_icono(ruta_hover) if ruta_hover is not None else self.icono_normal  # Utiliza una variante hover cuando existe.
        self.icono_presionado = self._cargar_icono(ruta_presionado) if ruta_presionado is not None else self.icono_hover  # Utiliza una variante específica o reutiliza hover.
        self._actualizar_icono()  # Aplica inmediatamente el icono correspondiente al estado actual.

    def _cargar_icono(self, ruta: Path) -> QIcon:
        if ruta.exists():
            return QIcon(str(ruta))  # Devuelve el icono construido desde el archivo recibido.

        return QIcon()  # Mantiene funcional la interfaz cuando falta un recurso gráfico.

    def _actualizar_icono(self) -> None:
        if self.esta_presionado:
            self.setIcon(self.icono_presionado)  # Muestra la variante correspondiente al estado presionado.
        elif self.puntero_encima:
            self.setIcon(self.icono_hover)  # Muestra la variante utilizada durante hover.
        else:
            self.setIcon(self.icono_normal)  # Recupera el icono normal.

    def enterEvent(self, evento) -> None:
        self.puntero_encima = True  # Registra que el control está siendo señalado.
        self._actualizar_icono()  # Actualiza inmediatamente su apariencia.
        super().enterEvent(evento)  # Conserva el comportamiento estándar de Qt.

    def leaveEvent(self, evento) -> None:
        self.puntero_encima = False  # Registra que el mouse dejó de señalar el control.
        self.esta_presionado = False  # Evita conservar visualmente el estado presionado.
        self._actualizar_icono()  # Recupera el icono normal.
        super().leaveEvent(evento)  # Conserva el comportamiento estándar de Qt.

    def mousePressEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton:
            self.esta_presionado = True  # Registra temporalmente el estado presionado.
            self._actualizar_icono()  # Muestra la variante correspondiente.

        super().mousePressEvent(evento)  # Permite que QPushButton procese normalmente la pulsación.

    def mouseReleaseEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton:
            self.esta_presionado = False  # Libera el estado visual presionado.
            self._actualizar_icono()  # Recupera hover o normal según la posición del puntero.

        super().mouseReleaseEvent(evento)  # Permite que QPushButton emita normalmente la señal clicked.


class BarraTitulo(QWidget):  # Representa la barra superior reutilizable de las ventanas de TecNet Finder.
    def __init__(
        self,
        ventana,
        ruta_icono: Path | None = None,
        titulo: str = "TecNet Finder",
        mostrar_configuracion: bool = True,
        mostrar_minimizar: bool = True,
        mostrar_pantalla_completa: bool = True,
        mostrar_cerrar: bool = True,
        permitir_arrastre: bool = False,
    ):
        super().__init__(ventana)  # Establece la ventana correspondiente como propietaria de la barra.
        self.ventana = ventana  # Conserva la referencia utilizada por los controles y el movimiento de ventanas secundarias.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.
        self.permitir_arrastre = permitir_arrastre  # Determina si la barra puede utilizarse para mover una ventana secundaria.

        self.boton_configuracion = None  # Permite omitir el control en ventanas donde no corresponde.
        self.boton_minimizar = None  # Permite omitir minimizar en diálogos secundarios.
        self.boton_pantalla_completa = None  # Permite omitir fullscreen en ventanas de tamaño fijo.
        self.boton_cerrar = None  # Permite decidir si la ventana debe mostrar una acción de cierre.

        self.setObjectName("BarraTitulo")  # Permite aplicar estilos específicos desde estilos.py.
        self.setFixedHeight(38)  # Mantiene exactamente la misma altura en todas las ventanas.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente logotipo, nombre y controles.
        diseno.setContentsMargins(10, 0, 0, 0)  # Deja espacio antes del logotipo y elimina margen en los controles.
        diseno.setSpacing(8)  # Define una separación pequeña entre logotipo y nombre.

        self.etiqueta_icono = QLabel()  # Crea el espacio destinado al icono pequeño de la aplicación.
        self.etiqueta_icono.setFixedSize(22, 22)  # Mantiene dimensiones apropiadas para la barra.
        self.etiqueta_icono.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite iniciar el movimiento incluso sobre el logotipo.

        if ruta_icono is not None and ruta_icono.exists():
            icono = QIcon(str(ruta_icono))  # Carga el icono general utilizando la ruta recibida.
            self.etiqueta_icono.setPixmap(icono.pixmap(18, 18))  # Genera una versión pequeña apropiada para la barra.

        diseno.addWidget(self.etiqueta_icono)  # Coloca el logotipo a la izquierda de la barra.

        self.etiqueta_titulo = QLabel(titulo)  # Muestra el nombre correspondiente a la ventana actual.
        self.etiqueta_titulo.setObjectName("TituloBarra")  # Aplica el estilo correspondiente al texto.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Mantiene el título correctamente alineado.
        self.etiqueta_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite iniciar el movimiento también sobre el título.
        diseno.addWidget(self.etiqueta_titulo)  # Coloca el nombre inmediatamente después del logotipo.

        diseno.addStretch()  # Empuja los controles hacia el extremo derecho.

        if mostrar_configuracion:
            self.boton_configuracion = self._crear_boton("BotonVentana", "Configuración")  # Crea el acceso directo a la configuración general.
            self.boton_configuracion.setFixedSize(38, 38)  # Mantiene el acceso completamente cuadrado.
            self.boton_configuracion.setIconSize(QSize(18, 18))  # Muestra claramente el engranaje sin dominar la barra.
            self.boton_configuracion.setAccessibleName("Configuración")  # Conserva una descripción accesible del control.
            self.boton_configuracion.establecer_iconos(
                self.ruta_iconos / "Engrane.png",
                self.ruta_iconos / "Engrane_Hover.png",
                self.ruta_iconos / "Engrane_Hover.png",
            )  # Utiliza las variantes normal y hover proporcionadas para Configuración.
            diseno.addWidget(self.boton_configuracion)  # Coloca Configuración antes de los controles de ventana.

        if mostrar_minimizar:
            self.boton_minimizar = self._crear_boton("BotonVentana", "Minimizar")  # Crea el control utilizado para minimizar TecNet Finder.
            self.boton_minimizar.establecer_iconos(
                self.ruta_iconos / "Minimizar.png",
                self.ruta_iconos / "Minimizar_hover.png",
                self.ruta_iconos / "Minimizar_hover.png",
            )  # Utiliza blanco normalmente y azul durante hover o pulsación.
            self.boton_minimizar.clicked.connect(self.ventana.minimizar_animado)  # Ejecuta la transición propia de la ventana principal.
            diseno.addWidget(self.boton_minimizar)  # Coloca minimizar cuando la ventana permite esta acción.

        if mostrar_pantalla_completa:
            self.boton_pantalla_completa = self._crear_boton("BotonPantallaCompleta", "Pantalla completa (F11)")  # Crea el control utilizado para fullscreen.
            self.boton_pantalla_completa.establecer_iconos(
                self.ruta_iconos / "Pantalla_completa.png",
                self.ruta_iconos / "Pantalla_completa_hover.png",
            )  # Configura las variantes iniciales del botón.
            self.boton_pantalla_completa.clicked.connect(self.ventana.alternar_pantalla_completa)  # Alterna los estados permitidos de la ventana principal.
            diseno.addWidget(self.boton_pantalla_completa)  # Coloca fullscreen cuando corresponde.

        if mostrar_cerrar:
            self.boton_cerrar = self._crear_boton("BotonCerrar", "Cerrar")  # Crea el control encargado de cerrar la ventana actual.
            self.boton_cerrar.establecer_iconos(
                self.ruta_iconos / "Cerrar.png",
                self.ruta_iconos / "Cerrar_activo.png",
                self.ruta_iconos / "Cerrar_activo.png",
            )  # Utiliza las variantes ya definidas para el control de cierre.
            self.boton_cerrar.clicked.connect(self.ventana.close)  # Solicita el cierre normal de la ventana propietaria.
            diseno.addWidget(self.boton_cerrar)  # Coloca cerrar en el extremo derecho.

    def _crear_boton(self, nombre_objeto: str, ayuda: str) -> BotonIconoEstado:
        boton = BotonIconoEstado(self)  # Crea un botón preparado para manejar variantes visuales.
        boton.setObjectName(nombre_objeto)  # Permite aplicar el estilo correspondiente desde estilos.py.
        boton.setFixedSize(46, 38)  # Utiliza dimensiones similares a los controles convencionales de Windows.
        boton.setIconSize(QSize(16, 16))  # Mantiene los PNG en un tamaño apropiado para la barra.
        boton.setToolTip(ayuda)  # Muestra una explicación breve al colocar el cursor encima.
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita que los controles interfieran con la navegación mediante Tab.
        return boton  # Devuelve el botón completamente configurado.

    def actualizar_estado_pantalla_completa(self, pantalla_completa: bool) -> None:
        if self.boton_pantalla_completa is None:
            return  # Evita modificar un control que no existe en barras reducidas.

        if pantalla_completa:
            self.boton_pantalla_completa.setToolTip("Salir de pantalla completa (F11)")  # Explica la función actual.
            self.boton_pantalla_completa.establecer_iconos(
                self.ruta_iconos / "Salir_pantalla_completa.png",
                self.ruta_iconos / "Salir_pantalla_completa_hover.png",
            )  # Sustituye expandir por los iconos utilizados para abandonar fullscreen.
        else:
            self.boton_pantalla_completa.setToolTip("Pantalla completa (F11)")  # Explica que el control permitirá entrar a fullscreen.
            self.boton_pantalla_completa.establecer_iconos(
                self.ruta_iconos / "Pantalla_completa.png",
                self.ruta_iconos / "Pantalla_completa_hover.png",
            )  # Recupera las variantes utilizadas para entrar a pantalla completa.

    def mousePressEvent(self, evento) -> None:
        if self.permitir_arrastre and evento.button() == Qt.MouseButton.LeftButton:
            manejador_ventana = self.ventana.windowHandle()  # Obtiene la ventana nativa creada por Qt para delegar el movimiento a Windows.

            if manejador_ventana is not None and manejador_ventana.startSystemMove():
                evento.accept()  # Deja que Windows complete el desplazamiento utilizando su mecanismo nativo de composición.
                return

        super().mousePressEvent(evento)  # Conserva el comportamiento normal cuando la barra no debe mover la ventana.