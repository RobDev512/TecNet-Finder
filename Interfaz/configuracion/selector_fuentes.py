# ============================================================
# Archivo: selector_fuentes.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene el selector especializado de familias tipográficas
# utilizado por Configuración.
#
# Permite buscar fuentes escribiendo cualquier parte del nombre,
# navegar con las flechas, seleccionar mediante Enter y cerrar
# mediante Escape.
#
# El desplegable también comprueba el área disponible de la
# pantalla para decidir si debe abrirse debajo o encima del
# control, evitando quedar oculto detrás de la barra de tareas.
#
# Solamente se muestran fuentes compatibles con el renderizado
# moderno utilizado por Qt.
# ============================================================

from PySide6.QtCore import QPoint, Qt, Signal  # Proporciona coordenadas, opciones de Qt y señales personalizadas.
from PySide6.QtGui import QKeyEvent  # Permite procesar las teclas utilizadas dentro del buscador.
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout  # Proporciona los controles necesarios.
from Motor.catalogo_fuentes import normalizar_fuente, obtener_fuentes_compatibles  # Centraliza el catálogo de fuentes seguras.


class VentanaFuentes(QFrame):  # Representa el popup que contiene buscador y coincidencias.
    fuente_seleccionada = Signal(str)  # Comunica al selector principal la familia elegida.

    def __init__(self, padre=None):
        super().__init__(padre, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)  # Crea una ventana flotante sin barra nativa que se cierra al pulsar fuera.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite conservar esquinas exteriores transparentes.
        self.setObjectName("VentanaFuentes")  # Identifica específicamente este popup.
        self.fuentes: list[str] = []  # Conserva todas las familias aunque la lista visible se encuentre filtrada.

        diseno_exterior = QVBoxLayout(self)  # Reserva una pequeña zona transparente alrededor del marco.
        diseno_exterior.setContentsMargins(2, 2, 2, 2)  # Evita recortar las esquinas redondeadas.
        diseno_exterior.setSpacing(0)  # Mantiene compacto el popup.

        self.marco = QFrame()  # Crea la superficie realmente visible.
        self.marco.setObjectName("MarcoVentanaFuentes")  # Permite estilizar solamente la superficie interior.
        diseno_marco = QVBoxLayout(self.marco)  # Organiza buscador y lista verticalmente.
        diseno_marco.setContentsMargins(7, 7, 7, 7)  # Separa el contenido del contorno.
        diseno_marco.setSpacing(6)  # Mantiene una separación discreta entre controles.

        self.campo_busqueda = QLineEdit()  # Permite localizar una familia escribiendo cualquier fragmento.
        self.campo_busqueda.setObjectName("BusquedaFuente")  # Permite aplicar un estilo exclusivo.
        self.campo_busqueda.setPlaceholderText("Buscar fuente...")  # Explica su función mientras está vacío.
        self.campo_busqueda.setClearButtonEnabled(True)  # Permite limpiar rápidamente una búsqueda.
        self.campo_busqueda.textChanged.connect(self._filtrar)  # Actualiza las coincidencias conforme se escribe.
        self.campo_busqueda.returnPressed.connect(self._seleccionar_actual)  # Confirma mediante Enter la fila marcada.
        self.campo_busqueda.installEventFilter(self)  # Permite procesar Escape y las flechas sin abandonar el buscador.

        self.lista = QListWidget()  # Presenta las fuentes coincidentes.
        self.lista.setObjectName("ListaFuentes")  # Permite estilizar específicamente la lista.
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Evita desplazamiento horizontal innecesario.
        self.lista.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Presenta scrollbar únicamente cuando resulta necesario.
        self.lista.setSpacing(1)  # Mantiene una separación mínima entre fuentes.
        self.lista.itemPressed.connect(self._seleccionar_elemento)  # Procesa inmediatamente una selección mediante mouse.
        self.lista.itemActivated.connect(self._seleccionar_elemento)  # Permite seleccionar también mediante teclado.

        diseno_marco.addWidget(self.campo_busqueda)  # Coloca primero el campo de búsqueda.
        diseno_marco.addWidget(self.lista, 1)  # Entrega el espacio restante a las coincidencias.
        diseno_exterior.addWidget(self.marco)  # Añade la superficie visible al popup.

        self.setStyleSheet("""
            QFrame#MarcoVentanaFuentes { background-color: #181825; border: 1px solid #45475a; border-radius: 10px; }
            QLineEdit#BusquedaFuente { background-color: #11111b; color: #cdd6f4; border: 1px solid #45475a; border-radius: 7px; padding: 7px 10px; selection-background-color: #89b4fa; selection-color: #1e1e2e; }
            QLineEdit#BusquedaFuente:hover { border-color: #585b70; }
            QLineEdit#BusquedaFuente:focus { border-color: #89b4fa; }
            QListWidget#ListaFuentes { background-color: transparent; color: #cdd6f4; border: none; outline: none; padding: 1px; }
            QListWidget#ListaFuentes::item { background-color: transparent; border: none; border-radius: 6px; padding: 7px 9px; }
            QListWidget#ListaFuentes::item:hover { background-color: #313244; color: #ffffff; }
            QListWidget#ListaFuentes::item:selected { background-color: #45475a; color: #ffffff; }
            QScrollBar:vertical { background-color: transparent; width: 10px; margin: 4px 1px; border: none; }
            QScrollBar::handle:vertical { background-color: #45475a; min-height: 28px; border: none; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background-color: #585b70; }
            QScrollBar::handle:vertical:pressed { background-color: #6c7086; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
        """)  # Mantiene el mismo diseño oscuro de Configuración.

    def establecer_fuentes(self, fuentes: list[str] | tuple[str, ...]) -> None:
        self.fuentes = list(fuentes)  # Conserva una copia independiente de todas las familias.
        self._filtrar("")  # Presenta inicialmente la colección completa.

    def mostrar_junto_control(self, control, ancho: int, fuente_actual: str) -> None:
        centro_global = control.mapToGlobal(control.rect().center())  # Obtiene un punto global perteneciente al monitor donde realmente se encuentra el selector.
        pantalla = QApplication.screenAt(centro_global) or QApplication.primaryScreen()  # Utiliza ese monitor y conserva la pantalla principal como respaldo.
        if pantalla is None:  # Comprueba el caso excepcional donde Qt no puede identificar ninguna pantalla.
            return  # Evita mostrar un popup cuya posición no pueda calcularse correctamente.

        area = pantalla.availableGeometry()  # Obtiene exclusivamente el área utilizable y excluye elementos como la barra de tareas.
        origen_global = control.mapToGlobal(QPoint(0, 0))  # Recupera la esquina superior izquierda del selector en coordenadas globales.
        margen = 8  # Reserva una distancia mínima respecto a los bordes de la pantalla.
        separacion = 4  # Mantiene una pequeña distancia respecto al selector que abrió el popup.
        ancho_maximo = max(160, area.width() - (margen * 2))  # Calcula cuánto ancho puede utilizarse sin salir de la pantalla.
        ancho_popup = min(max(260, ancho), ancho_maximo)  # Mantiene un ancho cómodo pero nunca superior al área disponible.
        alto_deseado = min(330, max(120, area.height() - (margen * 2)))  # Limita la altura ideal al espacio real del monitor.
        espacio_abajo = area.bottom() - (origen_global.y() + control.height()) - margen - separacion  # Calcula el espacio útil existente debajo.
        espacio_arriba = origen_global.y() - area.top() - margen - separacion  # Calcula el espacio útil existente encima.

        if espacio_abajo >= alto_deseado:  # Comprueba si el popup completo cabe cómodamente debajo.
            alto_popup = alto_deseado  # Conserva la altura ideal.
            posicion_y = origen_global.y() + control.height() + separacion  # Abre el popup debajo del selector.
        elif espacio_arriba >= alto_deseado:  # Comprueba si existe espacio completo en la dirección contraria.
            alto_popup = alto_deseado  # Conserva igualmente la altura ideal.
            posicion_y = origen_global.y() - alto_popup - separacion  # Abre el popup hacia arriba.
        elif espacio_arriba > espacio_abajo:  # Compara ambos espacios cuando ninguno permite utilizar la altura completa.
            alto_popup = max(120, espacio_arriba)  # Aprovecha el espacio superior disponible.
            posicion_y = origen_global.y() - alto_popup - separacion  # Sitúa el popup encima del selector.
        else:  # Utiliza la zona inferior cuando dispone de más espacio.
            alto_popup = max(120, espacio_abajo)  # Aprovecha el espacio inferior disponible.
            posicion_y = origen_global.y() + control.height() + separacion  # Sitúa el popup debajo del selector.

        alto_popup = min(alto_popup, area.height() - (margen * 2))  # Garantiza que la altura final nunca supere el área útil.
        posicion_y = max(area.top() + margen, min(posicion_y, area.bottom() - alto_popup - margen + 1))  # Corrige cualquier posible desbordamiento vertical.
        posicion_x = max(area.left() + margen, min(origen_global.x(), area.right() - ancho_popup - margen + 1))  # Corrige también cualquier desbordamiento horizontal.

        self.setFixedSize(ancho_popup, alto_popup)  # Aplica las dimensiones calculadas.
        self.move(posicion_x, posicion_y)  # Sitúa el popup completamente dentro del monitor.
        self.show()  # Muestra la ventana flotante.
        self.raise_()  # Garantiza que permanezca encima de Configuración.
        self.campo_busqueda.clear()  # Comienza cada apertura mostrando todas las familias.
        self._seleccionar_por_nombre(fuente_actual)  # Marca la fuente actualmente elegida.
        self.campo_busqueda.setFocus()  # Permite comenzar a buscar inmediatamente.

    def _filtrar(self, texto: str) -> None:
        busqueda = texto.strip().casefold()  # Normaliza el texto para ignorar mayúsculas, minúsculas y espacios exteriores.
        coincidencias = [fuente for fuente in self.fuentes if busqueda in fuente.casefold()]  # Conserva coincidencias parciales en cualquier posición del nombre.
        self.lista.clear()  # Elimina los resultados correspondientes al filtro anterior.
        for fuente in coincidencias:  # Recorre las fuentes compatibles con la búsqueda actual.
            self.lista.addItem(QListWidgetItem(fuente))  # Añade una fila visible por cada coincidencia.
        if self.lista.count() > 0:  # Comprueba si existe al menos un resultado.
            self.lista.setCurrentRow(0)  # Preselecciona la primera coincidencia para facilitar el uso de Enter.

    def _seleccionar_por_nombre(self, nombre: str) -> None:
        for indice in range(self.lista.count()):  # Recorre todos los elementos actualmente visibles.
            elemento = self.lista.item(indice)  # Recupera la fila correspondiente.
            if elemento.text() == nombre:  # Comprueba si representa la familia seleccionada.
                self.lista.setCurrentItem(elemento)  # Marca visualmente la fila.
                self.lista.scrollToItem(elemento)  # Desplaza la lista hasta hacerla visible.
                return  # Finaliza después de localizar la familia actual.

    def _seleccionar_actual(self) -> None:
        elemento = self.lista.currentItem()  # Recupera la coincidencia marcada actualmente.
        if elemento is not None:  # Comprueba que realmente exista una fila seleccionable.
            self._seleccionar_elemento(elemento)  # Confirma la misma ruta utilizada por un clic.

    def _seleccionar_elemento(self, elemento: QListWidgetItem) -> None:
        if elemento is None:  # Protege la operación frente a una selección inexistente.
            return  # No realiza ningún cambio.
        self.fuente_seleccionada.emit(elemento.text())  # Comunica el nombre exacto de la familia elegida.
        self.close()  # Cierra el popup después de entregar la selección.

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.campo_busqueda and isinstance(evento, QKeyEvent):  # Procesa únicamente teclas recibidas dentro del buscador.
            if evento.key() == Qt.Key.Key_Escape:  # Comprueba si se solicitó abandonar la búsqueda.
                self.close()  # Cierra el popup sin modificar la selección.
                return True  # Consume la tecla para evitar otros efectos.
            if evento.key() == Qt.Key.Key_Down and self.lista.count() > 0:  # Comprueba si puede avanzar a otra coincidencia.
                self.lista.setCurrentRow(min(self.lista.currentRow() + 1, self.lista.count() - 1))  # Avanza sin superar la última fila.
                return True  # Consume la tecla.
            if evento.key() == Qt.Key.Key_Up and self.lista.count() > 0:  # Comprueba si puede retroceder dentro de las coincidencias.
                self.lista.setCurrentRow(max(self.lista.currentRow() - 1, 0))  # Retrocede sin superar la primera fila.
                return True  # Consume la tecla.
        return super().eventFilter(objeto, evento)  # Conserva el procesamiento normal para cualquier otro evento.


class SelectorFuentes(QFrame):  # Representa el selector compacto utilizado dentro de las tarjetas de Configuración.
    valor_cambiado = Signal(str)  # Comunica solamente una selección realmente realizada por el usuario.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el marco principal del control.
        self.setObjectName("SelectorFuentes")  # Permite aplicar estilos específicos.
        self.setFixedHeight(38)  # Mantiene la misma altura aproximada de los demás controles.
        self._fuentes = list(obtener_fuentes_compatibles())  # Recupera únicamente familias seguras y escalables.
        self._fuente_actual = normalizar_fuente("Consolas", "Consolas")  # Prepara una selección inicial compatible antes de recibir la preferencia real.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente nombre y flecha.
        diseno.setContentsMargins(0, 0, 0, 0)  # Utiliza toda la superficie disponible.
        diseno.setSpacing(0)  # Une visualmente ambas zonas.

        self.boton_texto = QPushButton("")  # Presenta el nombre de la fuente seleccionada.
        self.boton_texto.setObjectName("TextoSelectorFuente")  # Permite estilizar la parte principal.
        self.boton_texto.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el control es interactivo.
        self.boton_texto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite alcanzarlo mediante teclado.
        self.boton_texto.clicked.connect(self._mostrar_fuentes)  # Abre el buscador desde el área principal.

        self.boton_flecha = QPushButton("⌄")  # Presenta una flecha sencilla en lugar del desplegable nativo.
        self.boton_flecha.setObjectName("FlechaSelectorFuente")  # Permite estilizar la zona derecha.
        self.boton_flecha.setFixedWidth(34)  # Reserva únicamente el ancho necesario.
        self.boton_flecha.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica interacción.
        self.boton_flecha.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Mantiene un solo punto de foco.
        self.boton_flecha.clicked.connect(self._mostrar_fuentes)  # Abre el mismo popup.

        diseno.addWidget(self.boton_texto, 1)  # Entrega el espacio principal al nombre.
        diseno.addWidget(self.boton_flecha)  # Coloca la flecha al extremo derecho.

        self.popup = VentanaFuentes(self.window())  # Crea una única ventana flotante reutilizable.
        self.popup.establecer_fuentes(self._fuentes)  # Entrega únicamente las fuentes compatibles.
        self.popup.fuente_seleccionada.connect(self._seleccionar_fuente)  # Recibe la elección final del usuario.

        self.setStyleSheet("""
            QFrame#SelectorFuentes { background-color: #313244; border: 1px solid #45475a; border-radius: 8px; }
            QPushButton#TextoSelectorFuente { background-color: transparent; color: #cdd6f4; border: none; border-radius: 7px; padding: 5px 10px; text-align: left; }
            QPushButton#TextoSelectorFuente:hover { background-color: #363649; }
            QPushButton#TextoSelectorFuente:focus { color: #ffffff; }
            QPushButton#FlechaSelectorFuente { background-color: transparent; color: #a6adc8; border: none; border-top-right-radius: 7px; border-bottom-right-radius: 7px; padding: 0px; font-family: "Segoe UI Symbol"; font-size: 13pt; }
            QPushButton#FlechaSelectorFuente:hover { background-color: #45475a; color: #ffffff; }
        """)  # Conserva la apariencia coherente con los controles existentes.

        self.establecer_valor(self._fuente_actual)  # Muestra inmediatamente la selección inicial compatible.

    def establecer_valor(self, fuente: str, emitir: bool = False) -> None:
        fuente_segura = normalizar_fuente(fuente, self._fuente_actual or "Consolas")  # Sustituye automáticamente cualquier familia antigua o incompatible.
        cambio = self._fuente_actual != fuente_segura  # Comprueba si la selección realmente cambia.
        self._fuente_actual = fuente_segura  # Conserva únicamente una familia segura.
        self.boton_texto.setText(fuente_segura)  # Presenta su nombre.
        self.boton_texto.setToolTip(fuente_segura)  # Permite consultar nombres largos.
        if emitir and cambio:  # Comprueba si la modificación proviene realmente de una acción del usuario.
            self.valor_cambiado.emit(fuente_segura)  # Comunica la nueva selección al panel.

    def valor_actual(self) -> str:
        return self._fuente_actual  # Permite consultar la familia utilizada actualmente.

    def _mostrar_fuentes(self) -> None:
        if self.popup.isVisible():  # Comprueba si el popup ya se encuentra abierto.
            self.popup.close()  # Permite cerrarlo pulsando nuevamente el selector.
            return  # Evita volver a mostrarlo inmediatamente.
        self.popup.establecer_fuentes(self._fuentes)  # Sincroniza la lista completa antes de cada apertura.
        self.popup.mostrar_junto_control(self, self.width(), self._fuente_actual)  # Calcula automáticamente si debe abrirse arriba o abajo.

    def _seleccionar_fuente(self, fuente: str) -> None:
        self.establecer_valor(fuente, emitir=True)  # Actualiza la selección y comunica solamente un cambio real.