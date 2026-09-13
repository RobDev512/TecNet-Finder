# ============================================================
# Archivo: barra_titulo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la barra de título personalizada de
# TecNet Finder.
#
# Sustituye visualmente la barra estándar de Windows por una
# barra propia reutilizable que muestra únicamente los controles
# necesarios según la ventana donde sea utilizada.
#
# La ventana principal incluye un botón de Media pantalla que
# abre un selector visual inspirado en Snap de Windows. Desde
# este selector el usuario puede colocar TecNet Finder en la
# mitad izquierda, en la mitad derecha o regresar al modo de
# ventana maximizada.
#
# Los controles utilizan iconos PNG propios y mantienen el
# comportamiento visual general utilizado por TecNet Finder.
# ============================================================

from pathlib import Path  # Permite localizar los recursos gráficos mediante rutas relativas al proyecto.

from PySide6.QtCore import QPoint, QSize, Qt, Signal  # Importa posiciones, tamaños, estados, banderas y señales utilizadas por la barra.
from PySide6.QtGui import QIcon  # Permite representar los iconos utilizados por los botones.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Importa los componentes necesarios para construir la barra y el selector visual.


class BotonIconoEstado(QPushButton):  # Define un botón capaz de cambiar su icono según el estado visual.
    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el comportamiento estándar proporcionado por QPushButton.
        self.icono_normal = QIcon()  # Guarda el icono utilizado cuando el botón está en reposo.
        self.icono_hover = QIcon()  # Guarda el icono utilizado cuando el puntero se encuentra encima.
        self.icono_presionado = QIcon()  # Guarda el icono utilizado mientras el botón permanece presionado.
        self.puntero_encima = False  # Indica si el mouse se encuentra actualmente sobre el botón.
        self.esta_presionado = False  # Indica si el botón se encuentra actualmente presionado.

    def establecer_iconos(
        self,
        ruta_normal: Path,
        ruta_hover: Path | None = None,
        ruta_presionado: Path | None = None,
    ) -> None:
        self.icono_normal = self._cargar_icono(ruta_normal)  # Carga el icono utilizado en el estado normal.
        self.icono_hover = self._cargar_icono(ruta_hover) if ruta_hover is not None else self.icono_normal  # Utiliza una variante hover cuando fue proporcionada.
        self.icono_presionado = self._cargar_icono(ruta_presionado) if ruta_presionado is not None else self.icono_hover  # Utiliza una variante específica o reutiliza el icono hover.
        self._actualizar_icono()  # Aplica inmediatamente el icono correspondiente con el estado actual.

    def _cargar_icono(self, ruta: Path) -> QIcon:
        if ruta.exists():
            return QIcon(str(ruta))  # Devuelve un icono construido a partir del archivo recibido.

        return QIcon()  # Mantiene funcional la interfaz incluso si algún recurso gráfico estuviera ausente.

    def _actualizar_icono(self) -> None:
        if self.esta_presionado:
            self.setIcon(self.icono_presionado)  # Muestra la variante correspondiente con una pulsación activa.
        elif self.puntero_encima:
            self.setIcon(self.icono_hover)  # Muestra la variante utilizada mientras el puntero está encima.
        else:
            self.setIcon(self.icono_normal)  # Recupera el icono normal cuando no existe interacción.

    def enterEvent(self, evento) -> None:
        self.puntero_encima = True  # Registra que el control comenzó a ser señalado.
        self._actualizar_icono()  # Actualiza inmediatamente su apariencia.
        super().enterEvent(evento)  # Conserva también el comportamiento estándar de Qt.

    def leaveEvent(self, evento) -> None:
        self.puntero_encima = False  # Registra que el mouse dejó de señalar el control.
        self.esta_presionado = False  # Evita conservar visualmente un estado presionado fuera del botón.
        self._actualizar_icono()  # Recupera la apariencia correspondiente.
        super().leaveEvent(evento)  # Conserva el comportamiento estándar de Qt.

    def mousePressEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton:
            self.esta_presionado = True  # Registra temporalmente que el botón está siendo presionado.
            self._actualizar_icono()  # Muestra inmediatamente la variante correspondiente.

        super().mousePressEvent(evento)  # Permite que QPushButton procese normalmente la pulsación.

    def mouseReleaseEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton:
            self.esta_presionado = False  # Libera el estado visual presionado.
            self._actualizar_icono()  # Recupera hover o normal según la posición actual del puntero.

        super().mouseReleaseEvent(evento)  # Permite que QPushButton emita normalmente la señal clicked.


class TarjetaMediaPantalla(QFrame):  # Representa una de las dos alternativas visuales del selector de Media pantalla.
    lado_seleccionado = Signal(str)  # Comunica si el usuario eligió la mitad izquierda o derecha.

    def __init__(self, lado: str, titulo: str, padre=None):
        super().__init__(padre)  # Inicializa el contenedor visual de la tarjeta.
        self.lado = lado  # Conserva el lado que representa esta tarjeta.
        self.activa = False  # Indica si esta tarjeta corresponde con la posición actualmente utilizada.

        self.setObjectName("TarjetaMediaPantalla")  # Permite aplicar estilos específicos a la tarjeta.
        self.setFixedSize(142, 132)  # Mantiene dimensiones compactas semejantes con una opción de Snap de Windows.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica visualmente que toda la tarjeta puede pulsarse.
        self.setProperty("activa", False)  # Inicializa la propiedad utilizada para resaltar la opción activa.

        diseno_principal = QVBoxLayout(self)  # Organiza la previsualización y el nombre de la posición.
        diseno_principal.setContentsMargins(9, 9, 9, 9)  # Mantiene espacio interior suficiente alrededor de la previsualización.
        diseno_principal.setSpacing(8)  # Separa discretamente la ilustración del texto.

        self.previsualizacion = QFrame(self)  # Crea el pequeño monitor esquemático utilizado para representar la división.
        self.previsualizacion.setObjectName("PrevisualizacionMediaPantalla")  # Permite aplicar su fondo y borde independientemente.
        self.previsualizacion.setFixedHeight(82)  # Reserva la mayor parte de la tarjeta para la representación visual.
        self.previsualizacion.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Hace que los clics sobre la previsualización lleguen a la tarjeta completa.

        diseno_previsualizacion = QHBoxLayout(self.previsualizacion)  # Divide visualmente el pequeño monitor en dos mitades.
        diseno_previsualizacion.setContentsMargins(7, 7, 7, 7)  # Mantiene un borde interno semejante con los layouts de Windows.
        diseno_previsualizacion.setSpacing(5)  # Deja una separación estrecha entre ambas zonas.

        self.mitad_izquierda = QFrame(self.previsualizacion)  # Representa la mitad izquierda del monitor.
        self.mitad_derecha = QFrame(self.previsualizacion)  # Representa la mitad derecha del monitor.

        self.mitad_izquierda.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite seleccionar la tarjeta aunque se pulse directamente sobre esta mitad.
        self.mitad_derecha.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite seleccionar la tarjeta aunque se pulse directamente sobre esta mitad.

        if self.lado == "izquierda":
            self.mitad_izquierda.setObjectName("MitadMediaPantallaActiva")  # Ilumina la mitad que TecNet Finder ocupará al elegir esta opción.
            self.mitad_derecha.setObjectName("MitadMediaPantallaInactiva")  # Mantiene neutra la mitad reservada para otra aplicación.
        else:
            self.mitad_izquierda.setObjectName("MitadMediaPantallaInactiva")  # Mantiene neutra la mitad reservada para otra aplicación.
            self.mitad_derecha.setObjectName("MitadMediaPantallaActiva")  # Ilumina la mitad que TecNet Finder ocupará al elegir esta opción.

        diseno_previsualizacion.addWidget(self.mitad_izquierda, 1)  # Coloca la mitad izquierda ocupando exactamente la mitad del pequeño monitor.
        diseno_previsualizacion.addWidget(self.mitad_derecha, 1)  # Coloca la mitad derecha ocupando exactamente la otra mitad.

        self.etiqueta_titulo = QLabel(titulo, self)  # Muestra el nombre textual de la alternativa.
        self.etiqueta_titulo.setObjectName("TituloTarjetaMediaPantalla")  # Permite aplicar un estilo específico al texto.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el nombre debajo de la representación.
        self.etiqueta_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite seleccionar la tarjeta incluso al pulsar directamente sobre el texto.

        diseno_principal.addWidget(self.previsualizacion)  # Coloca primero la ilustración visual.
        diseno_principal.addWidget(self.etiqueta_titulo)  # Coloca debajo el nombre del lado correspondiente.

    def establecer_activa(self, activa: bool) -> None:
        self.activa = activa  # Conserva el nuevo estado de selección de esta tarjeta.
        self.setProperty("activa", activa)  # Expone el estado al sistema de estilos de Qt.
        self.style().unpolish(self)  # Retira temporalmente el estilo anterior para reconocer la nueva propiedad.
        self.style().polish(self)  # Aplica nuevamente el estilo correspondiente con el estado actualizado.
        self.update()  # Solicita el redibujado inmediato de la tarjeta.

    def mousePressEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton:
            self.lado_seleccionado.emit(self.lado)  # Comunica inmediatamente qué mitad fue elegida.

        super().mousePressEvent(evento)  # Conserva el procesamiento normal de eventos de QFrame.


class SelectorMediaPantalla(QFrame):  # Define el popup visual que ofrece izquierda, derecha y maximizado.
    lado_seleccionado = Signal(str)  # Comunica a la barra qué mitad debe solicitar a la ventana principal.
    maximizar_solicitado = Signal()  # Comunica que el usuario desea regresar al modo de ventana maximizada.

    def __init__(self):
        super().__init__(None)  # Crea un popup independiente que puede mostrarse encima de la ventana principal.

        self.setObjectName("SelectorMediaPantalla")  # Permite aplicar el estilo exterior específico del selector.
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )  # Hace que el selector se cierre al pulsar fuera y evita añadir una barra de título propia.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # Permite que el popup reciba correctamente los clics de selección.
        self.setFixedSize(316, 204)  # Reserva espacio para las dos tarjetas y la acción inferior de maximizar.

        diseno_principal = QVBoxLayout(self)  # Organiza primero las tarjetas y debajo la acción de maximizado.
        diseno_principal.setContentsMargins(10, 10, 10, 10)  # Mantiene un borde interior compacto alrededor de todo el selector.
        diseno_principal.setSpacing(10)  # Separa visualmente las tarjetas del botón inferior.

        contenedor_tarjetas = QWidget(self)  # Crea una fila independiente para mantener ambas alternativas lado a lado.
        contenedor_tarjetas.setObjectName("ContenedorTarjetasMediaPantalla")  # Permite mantener transparente esta zona.
        contenedor_tarjetas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)  # Permite que las tarjetas continúen recibiendo interacción.

        diseno_tarjetas = QHBoxLayout(contenedor_tarjetas)  # Organiza las dos opciones horizontalmente.
        diseno_tarjetas.setContentsMargins(0, 0, 0, 0)  # Evita agregar márgenes duplicados dentro del popup.
        diseno_tarjetas.setSpacing(10)  # Mantiene una separación uniforme entre ambas tarjetas.

        self.tarjeta_izquierda = TarjetaMediaPantalla(
            lado="izquierda",
            titulo="Izquierda",
            padre=contenedor_tarjetas,
        )  # Crea la alternativa que coloca TecNet Finder sobre la mitad izquierda.

        self.tarjeta_derecha = TarjetaMediaPantalla(
            lado="derecha",
            titulo="Derecha",
            padre=contenedor_tarjetas,
        )  # Crea la alternativa que coloca TecNet Finder sobre la mitad derecha.

        self.tarjeta_izquierda.lado_seleccionado.connect(self._seleccionar_lado)  # Atiende la elección de la primera tarjeta.
        self.tarjeta_derecha.lado_seleccionado.connect(self._seleccionar_lado)  # Atiende la elección de la segunda tarjeta.

        diseno_tarjetas.addWidget(self.tarjeta_izquierda)  # Coloca la vista de izquierda como primera opción.
        diseno_tarjetas.addWidget(self.tarjeta_derecha)  # Coloca la vista de derecha inmediatamente después.

        self.boton_maximizar = QPushButton("Maximizar ventana", self)  # Crea una acción explícita para abandonar Media pantalla.
        self.boton_maximizar.setObjectName("BotonMaximizarDesdeSelector")  # Permite aplicar un estilo propio dentro del popup.
        self.boton_maximizar.setFixedHeight(40)  # Mantiene una altura cómoda sin hacer crecer demasiado el selector.
        self.boton_maximizar.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el área inferior es completamente interactiva.
        self.boton_maximizar.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita introducir una parada innecesaria durante navegación mediante Tab.
        self.boton_maximizar.clicked.connect(self._solicitar_maximizado)  # Cierra el selector y comunica la acción hacia la ventana principal.

        diseno_principal.addWidget(contenedor_tarjetas)  # Coloca primero las dos opciones de Media pantalla.
        diseno_principal.addWidget(self.boton_maximizar)  # Coloca debajo la salida hacia el modo maximizado.

        self.setStyleSheet(
            """
            QFrame#SelectorMediaPantalla {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 12px;
            }

            QWidget#ContenedorTarjetasMediaPantalla {
                background-color: transparent;
                border: none;
            }

            QFrame#TarjetaMediaPantalla {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 10px;
            }

            QFrame#TarjetaMediaPantalla:hover {
                background-color: #242438;
                border: 1px solid #89b4fa;
            }

            QFrame#TarjetaMediaPantalla[activa="true"] {
                background-color: #242438;
                border: 1px solid #cba6f7;
            }

            QFrame#PrevisualizacionMediaPantalla {
                background-color: #11111b;
                border: 1px solid #45475a;
                border-radius: 8px;
            }

            QFrame#MitadMediaPantallaActiva {
                background-color: #89b4fa;
                border: none;
                border-radius: 6px;
            }

            QFrame#MitadMediaPantallaInactiva {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
            }

            QLabel#TituloTarjetaMediaPantalla {
                color: #cdd6f4;
                background-color: transparent;
                border: none;
                font-weight: 600;
            }

            QPushButton#BotonMaximizarDesdeSelector {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 7px 12px;
                font-weight: 600;
            }

            QPushButton#BotonMaximizarDesdeSelector:hover {
                background-color: #45475a;
                color: #ffffff;
                border: 1px solid #89b4fa;
            }

            QPushButton#BotonMaximizarDesdeSelector:pressed {
                background-color: #585b70;
                border: 1px solid #cba6f7;
            }
            """
        )  # Aplica una apariencia coherente con el tema oscuro utilizado por TecNet Finder.

    def _seleccionar_lado(self, lado: str) -> None:
        self.hide()  # Oculta inmediatamente el popup después de elegir una posición.
        self.lado_seleccionado.emit(lado)  # Comunica a la barra qué lado debe utilizar la ventana principal.

    def _solicitar_maximizado(self) -> None:
        self.hide()  # Oculta el selector antes de modificar la geometría de la ventana principal.
        self.maximizar_solicitado.emit()  # Comunica que TecNet Finder debe regresar al modo maximizado.

    def mostrar(
        self,
        boton_origen: QWidget,
        lado_actual: str,
        media_pantalla_activa: bool,
    ) -> None:
        self.tarjeta_izquierda.establecer_activa(
            media_pantalla_activa and lado_actual == "izquierda"
        )  # Resalta la tarjeta izquierda únicamente cuando representa el estado actual.
        self.tarjeta_derecha.establecer_activa(
            media_pantalla_activa and lado_actual == "derecha"
        )  # Resalta la tarjeta derecha únicamente cuando representa el estado actual.

        self.boton_maximizar.setEnabled(
            media_pantalla_activa
        )  # Activa la salida a maximizado únicamente cuando TecNet Finder realmente está en Media pantalla.

        posicion_boton = boton_origen.mapToGlobal(
            QPoint(0, boton_origen.height() + 6)
        )  # Calcula una posición inicial ligeramente debajo del botón de Media pantalla.

        pantalla = boton_origen.screen()  # Obtiene el monitor donde se encuentra actualmente la barra principal.

        if pantalla is None:
            self.move(posicion_boton)  # Utiliza directamente la posición inicial cuando Qt no conoce todavía el monitor.
            self.show()  # Muestra el selector utilizando la posición calculada.
            return

        area = pantalla.availableGeometry()  # Obtiene el área utilizable del monitor excluyendo la barra de tareas.
        posicion_x = posicion_boton.x() + boton_origen.width() - self.width()  # Alinea inicialmente el borde derecho del popup con el borde derecho del botón.
        posicion_y = posicion_boton.y()  # Coloca inicialmente el selector debajo de la barra.

        if posicion_x < area.left():
            posicion_x = area.left() + 6  # Impide que el selector salga por el borde izquierdo del monitor.

        if posicion_x + self.width() > area.right() + 1:
            posicion_x = area.right() - self.width() + 1  # Impide que el selector salga por el borde derecho del monitor.

        if posicion_y + self.height() > area.bottom() + 1:
            posicion_y = boton_origen.mapToGlobal(
                QPoint(0, -self.height() - 6)
            ).y()  # Muestra el selector encima del botón cuando no existe espacio suficiente debajo.

        self.move(posicion_x, posicion_y)  # Coloca finalmente el popup dentro del monitor actual.
        self.show()  # Hace visible el selector con las tres alternativas.
        self.raise_()  # Garantiza que el popup quede encima de la ventana principal.


class BarraTitulo(QWidget):  # Representa la barra superior reutilizable de las ventanas de TecNet Finder.
    def __init__(
        self,
        ventana,
        ruta_icono: Path | None = None,
        titulo: str = "TecNet Finder",
        mostrar_configuracion: bool = True,
        mostrar_minimizar: bool = True,
        mostrar_media_pantalla: bool = False,
        mostrar_pantalla_completa: bool = True,
        mostrar_cerrar: bool = True,
        permitir_arrastre: bool = False,
    ):
        super().__init__(ventana)  # Establece la ventana correspondiente como propietaria de la barra.
        self.ventana = ventana  # Conserva la referencia utilizada por los controles y el movimiento de ventanas secundarias.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.
        self.permitir_arrastre = permitir_arrastre  # Determina si la barra puede utilizarse para mover una ventana secundaria.

        self.boton_configuracion = None  # Permite omitir el acceso de Configuración en ventanas donde no corresponde.
        self.boton_minimizar = None  # Permite omitir minimizar en diálogos secundarios.
        self.boton_media_pantalla = None  # Permite mostrar el selector de Snap únicamente en la ventana principal.
        self.selector_media_pantalla = None  # Conserva el popup visual utilizado para elegir izquierda, derecha o maximizado.
        self.boton_pantalla_completa = None  # Permite omitir fullscreen en ventanas de tamaño fijo.
        self.boton_cerrar = None  # Permite decidir si la ventana debe mostrar una acción de cierre.
        self.media_pantalla_activa = False  # Conserva el estado actual para resaltarlo cuando se abra el selector.
        self.lado_media_pantalla = "izquierda"  # Conserva el último lado conocido para representarlo dentro del selector.

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

        self.etiqueta_titulo = QLabel(titulo)  # Muestra el nombre correspondiente con la ventana actual.
        self.etiqueta_titulo.setObjectName("TituloBarra")  # Aplica el estilo correspondiente con el texto.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Mantiene el título correctamente alineado.
        self.etiqueta_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite iniciar el movimiento también sobre el título.
        diseno.addWidget(self.etiqueta_titulo)  # Coloca el nombre inmediatamente después del logotipo.

        diseno.addStretch()  # Empuja todos los controles hacia el extremo derecho.

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

        if mostrar_media_pantalla:
            self.boton_media_pantalla = self._crear_boton("BotonVentana", "Elegir media pantalla")  # Crea el botón encargado exclusivamente de abrir el selector visual.
            self.boton_media_pantalla.setAccessibleName("Elegir media pantalla")  # Conserva una descripción accesible del control.
            self.boton_media_pantalla.establecer_iconos(
                self.ruta_iconos / "Pantalla_Dividida.png",
                self.ruta_iconos / "Pantalla_Dividida_hover.png",
                self.ruta_iconos / "Pantalla_Dividida_hover.png",
            )  # Utiliza exactamente los recursos preparados para la vista dividida.
            self.boton_media_pantalla.clicked.connect(self._mostrar_selector_media_pantalla)  # Abre izquierda, derecha y maximizado en lugar de ejecutar Snap inmediatamente.
            diseno.addWidget(self.boton_media_pantalla)  # Coloca el selector entre minimizar y fullscreen.

            self.selector_media_pantalla = SelectorMediaPantalla()  # Construye una única instancia reutilizable del popup visual.
            self.selector_media_pantalla.lado_seleccionado.connect(self._seleccionar_lado_media_pantalla)  # Envía la elección de mitad hacia la ventana principal.
            self.selector_media_pantalla.maximizar_solicitado.connect(self._maximizar_desde_selector)  # Envía la opción inferior de regreso al modo maximizado.

        if mostrar_pantalla_completa:
            self.boton_pantalla_completa = self._crear_boton("BotonPantallaCompleta", "Pantalla completa (F11)")  # Crea el control utilizado para fullscreen.
            self.boton_pantalla_completa.establecer_iconos(
                self.ruta_iconos / "Pantalla_completa.png",
                self.ruta_iconos / "Pantalla_completa_hover.png",
            )  # Configura las variantes iniciales del botón.
            self.boton_pantalla_completa.clicked.connect(self.ventana.alternar_pantalla_completa)  # Alterna el modo fullscreen independientemente del selector de Snap.
            diseno.addWidget(self.boton_pantalla_completa)  # Coloca fullscreen después del control de Media pantalla.

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
        boton.setFixedSize(46, 38)  # Utiliza dimensiones similares con los controles convencionales de Windows.
        boton.setIconSize(QSize(16, 16))  # Mantiene los PNG en un tamaño apropiado para la barra.
        boton.setToolTip(ayuda)  # Muestra una explicación breve al colocar el cursor encima.
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita que los controles interfieran con la navegación mediante Tab.
        return boton  # Devuelve el botón completamente configurado.

    def _mostrar_selector_media_pantalla(self) -> None:
        if self.selector_media_pantalla is None or self.boton_media_pantalla is None:
            return  # Evita intentar abrir un selector inexistente en ventanas secundarias.

        self.selector_media_pantalla.mostrar(
            boton_origen=self.boton_media_pantalla,
            lado_actual=self.lado_media_pantalla,
            media_pantalla_activa=self.media_pantalla_activa,
        )  # Muestra el popup debajo del botón y refleja dentro de él el estado real de la ventana.

    def _seleccionar_lado_media_pantalla(self, lado: str) -> None:
        if hasattr(self.ventana, "colocar_media_pantalla"):
            self.ventana.colocar_media_pantalla(lado)  # Delega la ejecución real de Snap a la ventana principal.

    def _maximizar_desde_selector(self) -> None:
        if hasattr(self.ventana, "maximizar_ventana"):
            self.ventana.maximizar_ventana()  # Delega a la ventana principal la salida ordenada desde Media pantalla.

    def actualizar_estado_media_pantalla(
        self,
        media_pantalla: bool,
        lado: str = "izquierda",
    ) -> None:
        self.media_pantalla_activa = media_pantalla  # Conserva si actualmente se utiliza alguna de las dos mitades.
        self.lado_media_pantalla = lado if lado in ("izquierda", "derecha") else "izquierda"  # Conserva únicamente posiciones reconocidas por el selector.

        if self.boton_media_pantalla is None:
            return  # Evita modificar un botón ausente en ventanas secundarias.

        if media_pantalla:
            nombre_lado = "izquierda" if self.lado_media_pantalla == "izquierda" else "derecha"  # Convierte el estado interno en una descripción legible.
            self.boton_media_pantalla.setToolTip(
                f"Media pantalla actual: {nombre_lado}. Haz clic para cambiar de lado o maximizar."
            )  # Explica que el selector permite cambiar de mitad o recuperar maximizado.
        else:
            self.boton_media_pantalla.setToolTip(
                "Elegir media pantalla"
            )  # Recupera el mensaje general mientras la ventana se encuentra maximizada.

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