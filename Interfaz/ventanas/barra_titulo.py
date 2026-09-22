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
# La ventana principal incluye un selector visual inspirado en
# Snap de Windows. Desde este selector el usuario puede colocar
# TecNet Finder en la mitad izquierda, en la mitad derecha,
# utilizar un modo de ventana fija desplazable o regresar al
# estado maximizado.
#
# Los controles utilizan iconos PNG propios y mantienen el
# comportamiento visual general utilizado por TecNet Finder.
# ============================================================

from pathlib import Path  # Permite localizar los recursos gráficos mediante rutas relativas al proyecto.

from PySide6.QtCore import QPoint, QSize, Qt, Signal  # Proporciona posiciones, tamaños, estados y señales utilizadas por la barra.
from PySide6.QtGui import QIcon  # Permite cargar los iconos utilizados por los controles.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Proporciona los componentes necesarios para barra y selector.

from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona los iconos oscuros utilizados como estado inicial antes de aplicar el tema confirmado.


class BotonIconoEstado(QPushButton):  # Representa un botón capaz de cambiar automáticamente su icono según la interacción.
    def __init__(self, padre=None):  # Inicializa los tres posibles estados gráficos del control.
        super().__init__(padre)  # Inicializa el comportamiento estándar heredado desde QPushButton.
        self.icono_normal = QIcon()  # Conserva el icono utilizado mientras no existe interacción.
        self.icono_hover = QIcon()  # Conserva la variante utilizada cuando el cursor está encima.
        self.icono_presionado = QIcon()  # Conserva la variante utilizada mientras permanece presionado.
        self.puntero_encima = False  # Registra si actualmente el cursor se encuentra sobre el botón.
        self.esta_presionado = False  # Registra si el botón está siendo presionado con el botón izquierdo.

    def establecer_iconos(self, ruta_normal: Path, ruta_hover: Path | None = None, ruta_presionado: Path | None = None) -> None:  # Carga las variantes gráficas utilizadas por cada estado.
        self.icono_normal = self._cargar_icono(ruta_normal)  # Carga el recurso correspondiente con el estado normal.
        self.icono_hover = self._cargar_icono(ruta_hover) if ruta_hover is not None else self.icono_normal  # Utiliza una variante hover o reutiliza el icono normal.
        self.icono_presionado = self._cargar_icono(ruta_presionado) if ruta_presionado is not None else self.icono_hover  # Utiliza una variante presionada o reutiliza hover.
        self._actualizar_icono()  # Representa inmediatamente el icono correspondiente con el estado actual.

    def _cargar_icono(self, ruta: Path) -> QIcon:  # Convierte un recurso existente en QIcon sin provocar errores cuando falta.
        if ruta.exists():  # Comprueba que el archivo solicitado realmente exista.
            return QIcon(str(ruta))  # Devuelve el icono construido desde el recurso.

        return QIcon()  # Mantiene funcional el botón utilizando un icono vacío cuando el archivo falta.

    def _actualizar_icono(self) -> None:  # Selecciona qué variante debe mostrarse según la interacción actual.
        if self.esta_presionado:  # Da prioridad al estado presionado mientras exista una pulsación activa.
            self.setIcon(self.icono_presionado)  # Muestra la variante correspondiente.
        elif self.puntero_encima:  # Comprueba si el cursor está encima cuando el botón ya no está presionado.
            self.setIcon(self.icono_hover)  # Muestra la variante de hover.
        else:  # Atiende el estado convencional sin interacción.
            self.setIcon(self.icono_normal)  # Recupera el recurso normal.

    def enterEvent(self, evento) -> None:  # Actualiza el icono cuando el cursor entra al botón.
        self.puntero_encima = True  # Registra la presencia del cursor.
        self._actualizar_icono()  # Representa inmediatamente la variante hover.
        super().enterEvent(evento)  # Conserva además el comportamiento convencional de Qt.

    def leaveEvent(self, evento) -> None:  # Recupera el estado normal cuando el cursor abandona el botón.
        self.puntero_encima = False  # Registra que el cursor ya no está encima.
        self.esta_presionado = False  # Evita conservar visualmente una pulsación después de abandonar el control.
        self._actualizar_icono()  # Recupera el icono correspondiente con el nuevo estado.
        super().leaveEvent(evento)  # Conserva el procesamiento estándar del evento.

    def mousePressEvent(self, evento) -> None:  # Representa visualmente una pulsación izquierda.
        if evento.button() == Qt.MouseButton.LeftButton:  # Comprueba que se trate de la interacción principal.
            self.esta_presionado = True  # Registra temporalmente el estado presionado.
            self._actualizar_icono()  # Muestra inmediatamente la variante correspondiente.

        super().mousePressEvent(evento)  # Permite que QPushButton continúe procesando normalmente la pulsación.

    def mouseReleaseEvent(self, evento) -> None:  # Libera el estado visual después de soltar el botón izquierdo.
        if evento.button() == Qt.MouseButton.LeftButton:  # Comprueba que la liberación corresponda con la interacción principal.
            self.esta_presionado = False  # Elimina el estado presionado.
            self._actualizar_icono()  # Recupera hover o normal según la posición actual.

        super().mouseReleaseEvent(evento)  # Permite que QPushButton emita normalmente clicked.


class TarjetaMediaPantalla(QFrame):  # Representa visualmente una mitad disponible dentro del selector.
    lado_seleccionado = Signal(str)  # Comunica si el usuario eligió izquierda o derecha.

    def __init__(self, lado: str, titulo: str, padre=None):  # Construye una tarjeta asociada con uno de los dos lados permitidos.
        super().__init__(padre)  # Inicializa el QFrame utilizado como superficie interactiva.
        self.lado = lado  # Conserva qué mitad representa la tarjeta.
        self.activa = False  # Registra si actualmente corresponde con la geometría de TecNet Finder.

        self.setObjectName("TarjetaMediaPantalla")  # Permite aplicar estilos específicos a la tarjeta.
        self.setFixedSize(142, 132)  # Mantiene dimensiones compactas semejantes con una opción de Snap.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que toda la superficie puede pulsarse.
        self.setProperty("activa", False)  # Inicializa la propiedad utilizada por la hoja de estilos.

        diseno_principal = QVBoxLayout(self)  # Organiza verticalmente la previsualización y el título.
        diseno_principal.setContentsMargins(9, 9, 9, 9)  # Mantiene espacio interior uniforme.
        diseno_principal.setSpacing(8)  # Separa discretamente ilustración y texto.

        self.previsualizacion = QFrame(self)  # Crea el pequeño monitor esquemático mostrado dentro de la tarjeta.
        self.previsualizacion.setObjectName("PrevisualizacionMediaPantalla")  # Permite estilizar la previsualización independientemente.
        self.previsualizacion.setFixedHeight(82)  # Reserva la mayor parte de la tarjeta para la representación visual.
        self.previsualizacion.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite que cualquier clic llegue hasta la tarjeta.

        diseno_previsualizacion = QHBoxLayout(self.previsualizacion)  # Divide el pequeño monitor en dos regiones horizontales.
        diseno_previsualizacion.setContentsMargins(7, 7, 7, 7)  # Conserva un borde interno semejante con Snap.
        diseno_previsualizacion.setSpacing(5)  # Mantiene una separación estrecha entre las dos mitades.

        self.mitad_izquierda = QFrame(self.previsualizacion)  # Representa visualmente la mitad izquierda.
        self.mitad_derecha = QFrame(self.previsualizacion)  # Representa visualmente la mitad derecha.
        self.mitad_izquierda.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Mantiene clickeable la tarjeta completa.
        self.mitad_derecha.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Mantiene clickeable la tarjeta completa.

        if self.lado == "izquierda":  # Comprueba qué mitad debe iluminar esta tarjeta.
            self.mitad_izquierda.setObjectName("MitadMediaPantallaActiva")  # Destaca la región que ocuparía TecNet Finder.
            self.mitad_derecha.setObjectName("MitadMediaPantallaInactiva")  # Mantiene neutra la región disponible para otra aplicación.
        else:  # Atiende la alternativa correspondiente con la mitad derecha.
            self.mitad_izquierda.setObjectName("MitadMediaPantallaInactiva")  # Mantiene neutra la primera mitad.
            self.mitad_derecha.setObjectName("MitadMediaPantallaActiva")  # Destaca la región correspondiente con TecNet Finder.

        diseno_previsualizacion.addWidget(self.mitad_izquierda, 1)  # Coloca la mitad izquierda utilizando exactamente la mitad del espacio.
        diseno_previsualizacion.addWidget(self.mitad_derecha, 1)  # Coloca la mitad derecha utilizando el espacio restante.

        self.etiqueta_titulo = QLabel(titulo, self)  # Presenta mediante texto qué lado representa la tarjeta.
        self.etiqueta_titulo.setObjectName("TituloTarjetaMediaPantalla")  # Permite aplicar la apariencia específica del selector.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el título debajo de la previsualización.
        self.etiqueta_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite pulsar la tarjeta incluso directamente sobre el texto.

        diseno_principal.addWidget(self.previsualizacion)  # Coloca primero la representación visual.
        diseno_principal.addWidget(self.etiqueta_titulo)  # Coloca debajo el nombre de la opción.

    def establecer_activa(self, activa: bool) -> None:  # Sincroniza la apariencia con el lado que utiliza actualmente la ventana.
        self.activa = activa  # Conserva internamente el nuevo estado.
        self.setProperty("activa", activa)  # Expone el valor al sistema de estilos de Qt.
        self.style().unpolish(self)  # Retira temporalmente la apariencia calculada anteriormente.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos reconociendo la propiedad actualizada.
        self.update()  # Solicita el redibujado inmediato de la tarjeta.

    def mousePressEvent(self, evento) -> None:  # Comunica la selección al pulsar cualquier punto de la tarjeta.
        if evento.button() == Qt.MouseButton.LeftButton:  # Atiende únicamente la interacción principal.
            self.lado_seleccionado.emit(self.lado)  # Emite exactamente el lado asociado con esta tarjeta.

        super().mousePressEvent(evento)  # Conserva el procesamiento convencional de QFrame.



class TarjetaAccionVentana(QFrame):  # Representa visualmente Modo ventana o Maximizar dentro del selector.
    accion_seleccionada = Signal(str)  # Comunica la acción elegida al selector principal.

    def __init__(self, accion: str, titulo: str, padre=None):  # Construye una tarjeta asociada con una acción de ventana.
        super().__init__(padre)  # Inicializa el QFrame utilizado como superficie interactiva.
        self.accion = accion  # Conserva la acción representada por la tarjeta.
        self.activa = False  # Registra si actualmente esta opción representa el estado real de TecNet Finder.

        self.setObjectName("TarjetaMediaPantalla")  # Reutiliza el mismo lenguaje visual de las demás tarjetas.
        self.setFixedSize(142, 132)  # Mantiene dimensiones homogéneas dentro del selector.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que toda la superficie puede pulsarse.
        self.setProperty("activa", False)  # Inicializa la propiedad utilizada por la hoja de estilos.

        diseno_principal = QVBoxLayout(self)  # Organiza verticalmente previsualización y título.
        diseno_principal.setContentsMargins(9, 9, 9, 9)  # Conserva un margen interior uniforme.
        diseno_principal.setSpacing(8)  # Separa discretamente ilustración y texto.

        self.previsualizacion = QFrame(self)  # Crea el pequeño monitor esquemático mostrado dentro de la tarjeta.
        self.previsualizacion.setObjectName("PrevisualizacionMediaPantalla")  # Reutiliza la apariencia base.
        self.previsualizacion.setFixedHeight(82)  # Reserva la mayor parte de la tarjeta para la representación visual.
        self.previsualizacion.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite que cualquier clic llegue a la tarjeta.

        diseno_previsualizacion = QVBoxLayout(self.previsualizacion)  # Organiza los elementos internos de la vista previa.
        diseno_previsualizacion.setContentsMargins(9, 9, 9, 9)  # Mantiene un margen coherente con las demás vistas.
        diseno_previsualizacion.setSpacing(0)  # No requiere separación adicional dentro del esquema.

        if self.accion == "modo_ventana":  # Representa una ventana centrada y de menor tamaño.
            contenedor = QFrame(self.previsualizacion)  # Crea una superficie transparente para centrar la mini ventana.
            contenedor.setObjectName("ContenedorVistaPreviaAccionVentana")  # Permite retirar bordes automáticamente.
            diseno_contenedor = QHBoxLayout(contenedor)  # Centra horizontalmente la mini ventana.
            diseno_contenedor.setContentsMargins(0, 0, 0, 0)  # Evita márgenes adicionales.
            diseno_contenedor.addStretch()  # Deja espacio a la izquierda.
            self.vista_accion = QFrame(contenedor)  # Crea la mini ventana que simboliza el nuevo modo.
            self.vista_accion.setObjectName("VentanaModoVentanaPreview")  # Permite colorear el rectángulo pequeño.
            self.vista_accion.setFixedSize(36, 38)  # Hace más estrecha la mini ventana para distinguirla claramente del modo maximizado.
            diseno_contenedor.addWidget(self.vista_accion)  # Coloca la mini ventana en el centro.
            diseno_contenedor.addStretch()  # Deja espacio a la derecha.
            diseno_previsualizacion.addStretch()  # Centra verticalmente la mini ventana.
            diseno_previsualizacion.addWidget(contenedor)  # Inserta el esquema.
            diseno_previsualizacion.addStretch()  # Completa el centrado vertical.
        else:  # Atiende la acción Maximizar.
            self.vista_accion = QFrame(self.previsualizacion)  # Crea una representación de una ventana ocupando casi toda el área.
            self.vista_accion.setObjectName("VentanaMaximizadaPreview")  # Permite aplicar un estilo específico.
            diseno_previsualizacion.addWidget(self.vista_accion, 1)  # Llena prácticamente toda la vista previa.

        self.etiqueta_titulo = QLabel(titulo, self)  # Presenta mediante texto la acción representada.
        self.etiqueta_titulo.setObjectName("TituloTarjetaMediaPantalla")  # Reutiliza el estilo tipográfico del selector.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el texto debajo de la previsualización.
        self.etiqueta_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite pulsar la tarjeta incluso directamente sobre el texto.

        diseno_principal.addWidget(self.previsualizacion)  # Coloca primero la representación visual.
        diseno_principal.addWidget(self.etiqueta_titulo)  # Coloca debajo el nombre de la acción.

    def establecer_activa(self, activa: bool) -> None:  # Sincroniza la apariencia con el estado real de la ventana.
        self.activa = activa  # Conserva internamente el nuevo estado.
        self.setProperty("activa", activa)  # Expone el valor al sistema de estilos de Qt.
        self.style().unpolish(self)  # Retira temporalmente la apariencia calculada anteriormente.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos reconociendo la propiedad actualizada.
        self.update()  # Solicita el redibujado inmediato de la tarjeta.

    def mousePressEvent(self, evento) -> None:  # Comunica la acción seleccionada al pulsar cualquier punto de la tarjeta.
        if evento.button() == Qt.MouseButton.LeftButton:  # Atiende únicamente la interacción principal.
            self.accion_seleccionada.emit(self.accion)  # Emite exactamente la acción asociada con esta tarjeta.

        super().mousePressEvent(evento)  # Conserva el procesamiento convencional de QFrame.


class SelectorMediaPantalla(QFrame):  # Representa el popup utilizado para elegir izquierda, derecha, modo ventana o maximizado.
    lado_seleccionado = Signal(str)  # Comunica qué mitad debe utilizar la ventana principal.
    modo_ventana_solicitado = Signal()  # Comunica que se desea utilizar una ventana fija y desplazable.
    maximizar_solicitado = Signal()  # Comunica que se desea recuperar el estado maximizado.

    def __init__(self):  # Construye una única instancia reutilizable del selector.
        super().__init__(None)  # Crea un popup independiente de los layouts de la ventana principal.

        self.setObjectName("SelectorMediaPantalla")  # Identifica únicamente la superficie transparente exterior del popup.
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )  # Conserva el comportamiento de popup, elimina el marco y evita la sombra rectangular nativa que hacía visibles esquinas cuadradas.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # Permite que el popup reciba correctamente los clics.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Deja transparentes los píxeles exteriores sin recortar de forma dentada las esquinas.
        self.setAutoFillBackground(False)  # Evita que Qt vuelva a pintar un rectángulo opaco detrás del panel redondeado.
        self.setFixedSize(320, 300)  # Reserva unos pocos píxeles transparentes alrededor del panel para conservar antialiasing suave.

        diseno_exterior = QVBoxLayout(self)  # Contiene únicamente el panel visual redondeado.
        diseno_exterior.setContentsMargins(3, 3, 3, 3)  # Separa el panel del límite real de la ventana para que sus curvas puedan suavizarse.
        diseno_exterior.setSpacing(0)  # No necesita separación adicional alrededor del panel.

        self.panel_selector = QFrame(self)  # Crea la superficie visible que sustituye al antiguo fondo rectangular del popup.
        self.panel_selector.setObjectName("PanelSelectorMediaPantalla")  # Permite aplicar fondo, borde y radio sin afectar la ventana transparente exterior.
        self.panel_selector.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Obliga a Qt a pintar realmente el fondo redondeado del panel.
        diseno_exterior.addWidget(self.panel_selector)  # Hace que el panel ocupe todo el espacio interior disponible.

        diseno_principal = QVBoxLayout(self.panel_selector)  # Organiza las cuatro tarjetas dentro de la superficie redondeada.
        diseno_principal.setContentsMargins(10, 10, 10, 10)  # Conserva el margen visual existente.
        diseno_principal.setSpacing(10)  # Mantiene separación uniforme entre ambas filas.

        fila_superior = QHBoxLayout()  # Organiza izquierda y derecha.
        fila_superior.setContentsMargins(0, 0, 0, 0)  # Evita márgenes adicionales.
        fila_superior.setSpacing(10)  # Mantiene la separación horizontal.
        self.tarjeta_izquierda = TarjetaMediaPantalla(lado="izquierda", titulo="Izquierda", padre=self.panel_selector)  # Crea la alternativa correspondiente con la mitad izquierda.
        self.tarjeta_derecha = TarjetaMediaPantalla(lado="derecha", titulo="Derecha", padre=self.panel_selector)  # Crea la alternativa correspondiente con la mitad derecha.
        self.tarjeta_izquierda.lado_seleccionado.connect(self._seleccionar_lado)  # Recibe la elección realizada sobre la primera tarjeta.
        self.tarjeta_derecha.lado_seleccionado.connect(self._seleccionar_lado)  # Recibe la elección realizada sobre la segunda tarjeta.
        fila_superior.addWidget(self.tarjeta_izquierda)  # Coloca la tarjeta de la mitad izquierda.
        fila_superior.addWidget(self.tarjeta_derecha)  # Coloca la tarjeta de la mitad derecha.
        diseno_principal.addLayout(fila_superior)  # Inserta la primera fila.

        fila_inferior = QHBoxLayout()  # Organiza Modo ventana y Maximizar.
        fila_inferior.setContentsMargins(0, 0, 0, 0)  # Evita márgenes adicionales.
        fila_inferior.setSpacing(10)  # Mantiene la separación horizontal.
        self.tarjeta_modo_ventana = TarjetaAccionVentana(accion="modo_ventana", titulo="Modo ventana", padre=self.panel_selector)  # Crea la alternativa gráfica correspondiente al nuevo modo.
        self.tarjeta_maximizar = TarjetaAccionVentana(accion="maximizar", titulo="Maximizar", padre=self.panel_selector)  # Crea la alternativa gráfica correspondiente con maximizado.
        self.tarjeta_modo_ventana.accion_seleccionada.connect(self._procesar_accion)  # Procesa la solicitud del nuevo modo.
        self.tarjeta_maximizar.accion_seleccionada.connect(self._procesar_accion)  # Procesa la solicitud de maximizar.
        fila_inferior.addWidget(self.tarjeta_modo_ventana)  # Coloca la tercera tarjeta.
        fila_inferior.addWidget(self.tarjeta_maximizar)  # Coloca la cuarta tarjeta.
        diseno_principal.addLayout(fila_inferior)  # Inserta la segunda fila.

        self.setStyleSheet(
            """
            QFrame#SelectorMediaPantalla {
                background-color: transparent;
                border: none;
            }

            QFrame#PanelSelectorMediaPantalla {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 14px;
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

            QFrame#ContenedorVistaPreviaAccionVentana {
                background-color: transparent;
                border: none;
            }

            QFrame#VentanaModoVentanaPreview {
                background-color: #89b4fa;
                border: none;
                border-radius: 6px;
            }

            QFrame#VentanaMaximizadaPreview {
                background-color: #89b4fa;
                border: none;
                border-radius: 6px;
            }

            QLabel#TituloTarjetaMediaPantalla {
                color: #cdd6f4;
                background-color: transparent;
                border: none;
                font-weight: 600;
            }
            """
        )  # Mantiene una apariencia oscura inicial coherente hasta que el gestor aplique el tema vigente.

    def _seleccionar_lado(self, lado: str) -> None:  # Cierra el popup y comunica la mitad seleccionada.
        self.hide()  # Retira inmediatamente el selector después de la elección.
        self.lado_seleccionado.emit(lado)  # Envía el lado hacia BarraTitulo.

    def _procesar_accion(self, accion: str) -> None:  # Resuelve si debe activar Modo ventana o volver a maximizar.
        self.hide()  # Oculta primero el selector.
        if accion == "modo_ventana":  # Comprueba la acción solicitada.
            self.modo_ventana_solicitado.emit()  # Comunica la nueva modalidad.
        elif accion == "maximizar":  # Atiende la acción de maximizar.
            self.maximizar_solicitado.emit()  # Comunica la solicitud de regresar a maximizado.

    def _solicitar_modo_ventana(self) -> None:  # Conserva compatibilidad con pruebas o llamadas previas.
        self.hide()  # Oculta el selector antes de modificar la geometría.
        self.modo_ventana_solicitado.emit()  # Comunica la acción hacia BarraTitulo.

    def _solicitar_maximizado(self) -> None:  # Conserva compatibilidad con pruebas o llamadas previas.
        self.hide()  # Oculta el selector antes de modificar la geometría.
        self.maximizar_solicitado.emit()  # Comunica la acción hacia BarraTitulo.

    def mostrar(self, boton_origen: QWidget, lado_actual: str, media_pantalla_activa: bool, modo_ventana_activo: bool = False, maximizada: bool = False) -> None:  # Posiciona el popup y representa cuál de sus modos está activo.
        self.tarjeta_izquierda.establecer_activa(media_pantalla_activa and lado_actual == "izquierda")  # Resalta izquierda únicamente cuando corresponde con el estado real.
        self.tarjeta_derecha.establecer_activa(media_pantalla_activa and lado_actual == "derecha")  # Resalta derecha únicamente cuando corresponde con el estado real.
        self.tarjeta_modo_ventana.establecer_activa(modo_ventana_activo)  # Resalta Modo ventana únicamente cuando corresponde con el estado real.
        self.tarjeta_maximizar.establecer_activa(maximizada and not media_pantalla_activa and not modo_ventana_activo)  # Resalta maximizado cuando la ventana se encuentra precisamente en ese estado.

        posicion_boton = boton_origen.mapToGlobal(QPoint(0, boton_origen.height() + 6))  # Calcula inicialmente una posición justo debajo del control de origen.
        pantalla = boton_origen.screen()  # Obtiene el monitor donde se encuentra actualmente la barra.

        if pantalla is None:  # Comprueba si Qt todavía no puede identificar el monitor.
            self.move(posicion_boton)  # Utiliza la posición calculada sin realizar ajustes adicionales.
            self.show()  # Muestra el selector en esa ubicación.
            return  # Finaliza porque no existe geometría disponible para limitarlo.

        area = pantalla.availableGeometry()  # Obtiene el área utilizable excluyendo la barra de tareas.
        posicion_x = posicion_boton.x() + boton_origen.width() - self.width()  # Alinea inicialmente el borde derecho con el botón.
        posicion_y = posicion_boton.y()  # Mantiene inicialmente el selector debajo de la barra.

        if posicion_x < area.left():  # Comprueba si el popup saldría por el borde izquierdo.
            posicion_x = area.left() + 6  # Lo desplaza algunos píxeles hacia el interior del monitor.

        if posicion_x + self.width() > area.right() + 1:  # Comprueba si el popup saldría por el borde derecho.
            posicion_x = area.right() - self.width() + 1  # Corrige la posición para mantenerlo completamente visible.

        if posicion_y + self.height() > area.bottom() + 1:  # Comprueba si no existe suficiente espacio debajo de la barra.
            posicion_y = boton_origen.mapToGlobal(QPoint(0, -self.height() - 6)).y()  # Coloca el selector encima del botón como alternativa.

        self.move(posicion_x, posicion_y)  # Aplica finalmente una posición completamente visible dentro del monitor.
        self.show()  # Hace visible el selector.
        self.raise_()  # Mantiene el popup encima de la ventana principal.


class BarraTitulo(QWidget):  # Representa la barra superior reutilizable de las ventanas de TecNet Finder.
    def __init__(self, ventana, ruta_icono: Path | None = None, titulo: str = "TecNet Finder", mostrar_configuracion: bool = True, mostrar_minimizar: bool = True, mostrar_media_pantalla: bool = False, mostrar_pantalla_completa: bool = True, mostrar_cerrar: bool = True, permitir_arrastre: bool = False):  # Recibe qué controles debe mostrar según la ventana propietaria.
        super().__init__(ventana)  # Establece la ventana correspondiente como propietaria de la barra.
        self.ventana = ventana  # Conserva acceso a las acciones de ventana.
        self.permitir_arrastre = permitir_arrastre  # Determina si la barra puede utilizarse para mover la ventana.

        self.boton_configuracion = None  # Permite omitir Configuración cuando no corresponde.
        self.boton_minimizar = None  # Permite omitir minimizar en ventanas secundarias.
        self.boton_media_pantalla = None  # Permite mostrar el selector únicamente en la ventana principal.
        self.selector_media_pantalla = None  # Conserva una posible instancia del popup de selección.
        self.boton_pantalla_completa = None  # Permite omitir fullscreen en ventanas de tamaño fijo.
        self.boton_cerrar = None  # Permite omitir también la acción de cierre cuando fuera necesario.
        self.media_pantalla_activa = False  # Registra si actualmente la ventana utiliza alguna mitad.
        self.lado_media_pantalla = "izquierda"  # Conserva la última mitad conocida.
        self.modo_ventana_activo = False  # Registra si actualmente se utiliza el tamaño fijo desplazable.

        self.setObjectName("BarraTitulo")  # Permite aplicar los estilos generales preparados en estilos.py.
        self.setFixedHeight(38)  # Mantiene la misma altura visual en todas las ventanas.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente icono, título y controles.
        diseno.setContentsMargins(10, 0, 0, 0)  # Mantiene espacio únicamente antes del logotipo.
        diseno.setSpacing(8)  # Conserva una separación discreta entre icono y título.

        self.etiqueta_icono = QLabel()  # Crea la superficie destinada al logotipo pequeño.
        self.etiqueta_icono.setFixedSize(22, 22)  # Mantiene dimensiones apropiadas para la barra.
        self.etiqueta_icono.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite iniciar un arrastre incluso sobre el logotipo.

        if ruta_icono is not None and ruta_icono.exists():  # Comprueba que la ventana haya proporcionado un icono válido.
            icono = QIcon(str(ruta_icono))  # Carga el recurso recibido.
            self.etiqueta_icono.setPixmap(icono.pixmap(18, 18))  # Genera una versión pequeña adecuada para la barra.

        diseno.addWidget(self.etiqueta_icono)  # Coloca el logotipo a la izquierda.

        self.etiqueta_titulo = QLabel(titulo)  # Crea el texto correspondiente con la ventana actual.
        self.etiqueta_titulo.setObjectName("TituloBarra")  # Aplica la apariencia general del título.
        self.etiqueta_titulo.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Mantiene el texto centrado verticalmente.
        self.etiqueta_titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite arrastrar también desde la zona del título.
        diseno.addWidget(self.etiqueta_titulo)  # Coloca el título después del logotipo.
        diseno.addStretch()  # Empuja todos los controles hacia el extremo derecho.

        if mostrar_configuracion:  # Comprueba si esta ventana necesita acceso directo a Configuración.
            self.boton_configuracion = self._crear_boton("BotonVentana", "Configuración")  # Crea el botón especializado.
            self.boton_configuracion.setFixedSize(38, 38)  # Mantiene el engrane completamente cuadrado.
            self.boton_configuracion.setIconSize(QSize(18, 18))  # Muestra claramente el recurso sin dominar la barra.
            self.boton_configuracion.setAccessibleName("Configuración")  # Conserva una descripción textual accesible.
            self.boton_configuracion.establecer_iconos(ruta_icono_oscuro("Engrane.png"), ruta_icono_oscuro("Engrane_Hover.png"), ruta_icono_oscuro("Engrane_Hover.png"))  # Inicializa Configuración con sus estados oscuros.
            diseno.addWidget(self.boton_configuracion)  # Coloca Configuración antes de los controles de ventana.

        if mostrar_minimizar:  # Comprueba si la ventana puede enviarse a la barra de tareas.
            self.boton_minimizar = self._crear_boton("BotonVentana", "Minimizar")  # Construye el control correspondiente.
            self.boton_minimizar.establecer_iconos(ruta_icono_oscuro("Minimizar.png"), ruta_icono_oscuro("Minimizar_hover.png"), ruta_icono_oscuro("Minimizar_hover.png"))  # Inicializa Minimizar con sus estados gráficos oficiales.
            self.boton_minimizar.clicked.connect(self.ventana.minimizar_animado)  # Ejecuta la transición implementada por VentanaPrincipal.
            diseno.addWidget(self.boton_minimizar)  # Añade el control a la barra.

        if mostrar_media_pantalla:  # Comprueba si esta barra pertenece a la ventana principal.
            self.boton_media_pantalla = self._crear_boton("BotonVentana", "Elegir modo de ventana")  # Crea el acceso al selector visual.
            self.boton_media_pantalla.setAccessibleName("Elegir modo de ventana")  # Proporciona una descripción para accesibilidad.
            self.boton_media_pantalla.establecer_iconos(ruta_icono_oscuro("Pantalla_Dividida.png"), ruta_icono_oscuro("Pantalla_Dividida_hover.png"), ruta_icono_oscuro("Pantalla_Dividida_hover.png"))  # Inicializa el selector con sus variantes gráficas oficiales.
            self.boton_media_pantalla.clicked.connect(self._mostrar_selector_media_pantalla)  # Abre el popup en lugar de modificar inmediatamente la geometría.
            diseno.addWidget(self.boton_media_pantalla)  # Coloca el selector entre minimizar y fullscreen.

            self.selector_media_pantalla = SelectorMediaPantalla()  # Construye una única instancia reutilizable.
            self.selector_media_pantalla.lado_seleccionado.connect(self._seleccionar_lado_media_pantalla)  # Envía la mitad elegida hacia la ventana principal.
            self.selector_media_pantalla.modo_ventana_solicitado.connect(self._modo_ventana_desde_selector)  # Envía la modalidad fija hacia la ventana principal.
            self.selector_media_pantalla.maximizar_solicitado.connect(self._maximizar_desde_selector)  # Envía la acción de regreso al modo maximizado.

        if mostrar_pantalla_completa:  # Comprueba si esta ventana admite fullscreen.
            self.boton_pantalla_completa = self._crear_boton("BotonPantallaCompleta", "Pantalla completa (F11)")  # Crea el control correspondiente.
            self.boton_pantalla_completa.establecer_iconos(ruta_icono_oscuro("Pantalla_completa.png"), ruta_icono_oscuro("Pantalla_completa_hover.png"))  # Inicializa Pantalla completa con sus variantes gráficas oficiales.
            self.boton_pantalla_completa.clicked.connect(self.ventana.alternar_pantalla_completa)  # Delega la transición en la ventana propietaria.
            diseno.addWidget(self.boton_pantalla_completa)  # Añade fullscreen después del selector.

        if mostrar_cerrar:  # Comprueba si la ventana necesita una acción explícita de cierre.
            self.boton_cerrar = self._crear_boton("BotonCerrar", "Cerrar")  # Crea el control correspondiente.
            self.boton_cerrar.establecer_iconos(ruta_icono_oscuro("Cerrar.png"), ruta_icono_oscuro("Cerrar_activo.png"), ruta_icono_oscuro("Cerrar_activo.png"))  # Inicializa Cerrar con su variante destinada al fondo rojo.
            self.boton_cerrar.clicked.connect(self.ventana.close)  # Solicita el cierre convencional de la ventana propietaria.
            diseno.addWidget(self.boton_cerrar)  # Coloca cerrar en el extremo derecho.

    def _crear_boton(self, nombre_objeto: str, ayuda: str) -> BotonIconoEstado:  # Construye un control estándar de la barra con apariencia uniforme.
        boton = BotonIconoEstado(self)  # Crea un botón preparado para variantes normal, hover y presionado.
        boton.setObjectName(nombre_objeto)  # Permite aplicar la regla correspondiente desde estilos.py.
        boton.setFixedSize(46, 38)  # Utiliza dimensiones semejantes con los controles convencionales de Windows.
        boton.setIconSize(QSize(16, 16))  # Mantiene los PNG en un tamaño apropiado.
        boton.setToolTip(ayuda)  # Explica brevemente su función al usuario.
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita interferir con la navegación mediante Tab.
        return boton  # Entrega el botón completamente configurado.

    def _mostrar_selector_media_pantalla(self) -> None:  # Abre el popup reflejando el estado real de TecNet Finder.
        if self.selector_media_pantalla is None or self.boton_media_pantalla is None:  # Comprueba que esta barra realmente tenga la característica.
            return  # Evita utilizar controles inexistentes en ventanas secundarias.

        self.selector_media_pantalla.mostrar(
            boton_origen=self.boton_media_pantalla,
            lado_actual=self.lado_media_pantalla,
            media_pantalla_activa=self.media_pantalla_activa,
            modo_ventana_activo=self.modo_ventana_activo,
            maximizada=self.ventana.isMaximized(),
        )  # Sitúa el popup y representa Izquierda, Derecha, Modo ventana o Maximizar según corresponda.

    def _seleccionar_lado_media_pantalla(self, lado: str) -> None:  # Delega la elección de lado sobre la ventana propietaria.
        if hasattr(self.ventana, "colocar_media_pantalla"):  # Comprueba que la ventana posea la operación requerida.
            self.ventana.colocar_media_pantalla(lado)  # Solicita realmente el Snap sobre el lado elegido.

    def _modo_ventana_desde_selector(self) -> None:  # Delega la nueva modalidad fija hacia la ventana propietaria.
        if hasattr(self.ventana, "activar_modo_ventana"):  # Comprueba que la ventana principal implemente la operación.
            self.ventana.activar_modo_ventana()  # Solicita el tamaño fijo y habilita su desplazamiento.

    def _maximizar_desde_selector(self) -> None:  # Delega la salida de cualquier modo temporal hacia maximizado.
        if hasattr(self.ventana, "maximizar_ventana"):  # Comprueba que la ventana implemente la operación.
            self.ventana.maximizar_ventana()  # Solicita recuperar el modo maximizado.

    def actualizar_estado_media_pantalla(self, media_pantalla: bool, lado: str = "izquierda") -> None:  # Sincroniza el selector y tooltip con la geometría real de la ventana.
        self.media_pantalla_activa = media_pantalla  # Conserva si actualmente existe una mitad activa.
        self.lado_media_pantalla = lado if lado in ("izquierda", "derecha") else "izquierda"  # Acepta exclusivamente los dos lados reconocidos.
        self._actualizar_tooltip_modo_ventana()  # Reconstruye el texto considerando también Modo ventana.

    def actualizar_estado_modo_ventana(self, activo: bool) -> None:  # Sincroniza la nueva modalidad con el selector.
        self.modo_ventana_activo = bool(activo)  # Conserva si actualmente se utiliza el tamaño fijo desplazable.
        self._actualizar_tooltip_modo_ventana()  # Actualiza el acceso principal con el estado combinado.

    def _actualizar_tooltip_modo_ventana(self) -> None:  # Explica desde el mismo botón cuál de los modos de ventana está activo.
        if self.boton_media_pantalla is None:  # Comprueba que esta barra incluya realmente el selector.
            return  # Finaliza en ventanas secundarias.

        if self.modo_ventana_activo:  # Da prioridad al nuevo modo cuando se encuentra activo.
            self.boton_media_pantalla.setToolTip("Modo ventana activo. Haz clic para cambiar de posición o maximizar.")  # Explica las alternativas disponibles.
        elif self.media_pantalla_activa:  # Atiende alguna de las dos mitades.
            nombre_lado = "izquierda" if self.lado_media_pantalla == "izquierda" else "derecha"  # Convierte el estado interno en texto legible.
            self.boton_media_pantalla.setToolTip(f"Media pantalla actual: {nombre_lado}. Haz clic para cambiar de modo.")  # Explica el lado actualmente utilizado.
        else:  # Atiende maximizado o una ventana convencional iniciada desde preferencias.
            self.boton_media_pantalla.setToolTip("Elegir modo de ventana")  # Presenta el selector como acceso a todas sus opciones.

    def actualizar_estado_pantalla_completa(self, pantalla_completa: bool) -> None:  # Cambia tooltip e iconos según entrada o salida de fullscreen.
        if self.boton_pantalla_completa is None:  # Comprueba que esta barra incluya realmente el control.
            return  # Finaliza en ventanas secundarias sin fullscreen.

        if pantalla_completa:  # Representa la acción que permitirá abandonar fullscreen.
            self.boton_pantalla_completa.setToolTip("Salir de pantalla completa (F11)")  # Explica la función actual.
            self.boton_pantalla_completa.establecer_iconos(ruta_icono_oscuro("Salir_pantalla_completa.png"), ruta_icono_oscuro("Salir_pantalla_completa_hover.png"))  # Sustituye los recursos de entrada por los utilizados para abandonar pantalla completa.
        else:  # Representa la acción disponible mientras la ventana no está en fullscreen.
            self.boton_pantalla_completa.setToolTip("Pantalla completa (F11)")  # Explica que el control permitirá entrar al modo.
            self.boton_pantalla_completa.establecer_iconos(ruta_icono_oscuro("Pantalla_completa.png"), ruta_icono_oscuro("Pantalla_completa_hover.png"))  # Recupera los recursos convencionales para entrar a pantalla completa.

    def mousePressEvent(self, evento) -> None:  # Permite mover la ventana mediante el mecanismo nativo del sistema cuando el modo actual lo autoriza.
        if self.permitir_arrastre and evento.button() == Qt.MouseButton.LeftButton:  # Comprueba que el arrastre esté habilitado y se utilice el botón principal.
            manejador_ventana = self.ventana.windowHandle()  # Obtiene la representación nativa administrada por Qt.

            if manejador_ventana is not None and manejador_ventana.startSystemMove():  # Solicita al sistema iniciar el desplazamiento real.
                evento.accept()  # Marca el evento como atendido por la operación nativa.
                return  # Evita procesar adicionalmente la misma pulsación.

        super().mousePressEvent(evento)  # Conserva el comportamiento normal cuando no corresponde iniciar un arrastre.
