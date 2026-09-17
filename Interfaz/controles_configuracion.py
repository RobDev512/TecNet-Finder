# ============================================================
# Archivo: controles_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene controles visuales reutilizables para Configuración.
#
# Incluye:
# - Campo numérico sin botones nativos.
# - Selector desplegable personalizado.
# - Popup redondeado y desplazable.
#
# Los desplegables de pocas opciones ajustan exactamente su
# altura al contenido. Las listas extensas continúan utilizando
# desplazamiento y respetan siempre el área útil del monitor.
# ============================================================

from PySide6.QtCore import QPoint, Qt, Signal  # Proporciona posición, opciones visuales y señales.
from PySide6.QtWidgets import QApplication, QAbstractSpinBox, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QVBoxLayout  # Importa los componentes reutilizados.


class CampoNumeroConfiguracion(QSpinBox):  # Representa un campo numérico sin las flechas nativas de Windows.
    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa QSpinBox conservando validación y teclado.
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)  # Elimina completamente los controles arriba y abajo.
        self.setFixedHeight(38)  # Mantiene la misma altura que los selectores personalizados.
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Presenta el número como un campo convencional.
        self.setStyleSheet("""
            QSpinBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 8px; padding: 5px 10px; selection-background-color: #585b70; }
            QSpinBox:hover { border-color: #585b70; }
            QSpinBox:focus { border-color: #89b4fa; }
        """)  # Utiliza la paleta base que posteriormente puede traducir el gestor de apariencia.


class VentanaOpcionesConfiguracion(QFrame):  # Representa el popup utilizado por los selectores generales.
    opcion_seleccionada = Signal(object)  # Comunica al selector el valor real relacionado con la fila elegida.
    MAXIMO_FILAS_SIN_CRECER = 7  # Limita listas grandes sin añadir espacio vacío a selectores pequeños.

    def __init__(self, padre=None):
        super().__init__(padre, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)  # Crea un popup sin barra nativa que se cierra al pulsar fuera.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite conservar esquinas exteriores transparentes.
        self.setObjectName("VentanaOpcionesConfiguracion")  # Identifica la ventana flotante.

        diseno_exterior = QVBoxLayout(self)  # Reserva una pequeña zona transparente alrededor del marco.
        diseno_exterior.setContentsMargins(2, 2, 2, 2)  # Evita recortar las esquinas.
        diseno_exterior.setSpacing(0)  # Mantiene compacto el conjunto.

        self.marco = QFrame()  # Crea la superficie realmente visible.
        self.marco.setObjectName("MarcoOpcionesConfiguracion")  # Permite estilizar exclusivamente el marco.

        diseno_marco = QVBoxLayout(self.marco)  # Organiza la lista dentro del popup.
        diseno_marco.setContentsMargins(5, 5, 5, 5)  # Separa ligeramente las opciones del contorno.
        diseno_marco.setSpacing(0)  # Deja que QListWidget administre el espacio entre filas.

        self.lista = QListWidget()  # Crea la lista desplazable.
        self.lista.setObjectName("ListaOpcionesConfiguracion")  # Permite aplicar su estilo propio.
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Elimina desplazamiento lateral.
        self.lista.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Oculta inicialmente el scrollbar hasta comprobar que realmente sea necesario.
        self.lista.setSpacing(1)  # Mantiene una separación mínima entre opciones.
        self.lista.itemPressed.connect(self._seleccionar_elemento)  # Procesa el clic antes de que Qt cierre automáticamente el popup.
        self.lista.itemActivated.connect(self._seleccionar_elemento)  # Permite confirmar también mediante teclado.

        diseno_marco.addWidget(self.lista)  # Coloca la lista dentro del marco.
        diseno_exterior.addWidget(self.marco)  # Coloca el marco dentro de la región transparente.

        self.setStyleSheet("""
            QFrame#MarcoOpcionesConfiguracion { background-color: #181825; border: 1px solid #45475a; border-radius: 10px; }
            QListWidget#ListaOpcionesConfiguracion { background-color: transparent; color: #cdd6f4; border: none; outline: none; padding: 1px; }
            QListWidget#ListaOpcionesConfiguracion::item { background-color: transparent; border: none; border-radius: 6px; padding: 7px 9px; }
            QListWidget#ListaOpcionesConfiguracion::item:hover { background-color: #313244; color: #ffffff; }
            QListWidget#ListaOpcionesConfiguracion::item:selected { background-color: #45475a; color: #ffffff; }
            QScrollBar:vertical { background-color: transparent; width: 10px; margin: 4px 1px; border: none; }
            QScrollBar::handle:vertical { background-color: #45475a; min-height: 28px; border: none; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background-color: #585b70; }
            QScrollBar::handle:vertical:pressed { background-color: #6c7086; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
        """)  # Conserva la paleta base para permitir que GestorTipografia la transforme con cada tema.

    def limpiar(self) -> None:
        self.lista.clear()  # Elimina todas las filas para reutilizar el mismo popup con otra colección de opciones.
        self.lista.verticalScrollBar().setValue(0)  # Recupera también el inicio de la lista para la siguiente colección.

    def agregar_opcion(self, texto: str, dato) -> None:
        elemento = QListWidgetItem(texto)  # Crea la fila visible.
        elemento.setData(Qt.ItemDataRole.UserRole, dato)  # Guarda independientemente el valor real asociado.
        self.lista.addItem(elemento)  # Incorpora la opción al popup.

    def seleccionar_dato(self, dato) -> None:
        for indice in range(self.lista.count()):  # Recorre todas las opciones visibles.
            elemento = self.lista.item(indice)  # Recupera la fila correspondiente.
            if elemento.data(Qt.ItemDataRole.UserRole) == dato:
                self.lista.setCurrentItem(elemento)  # Marca visualmente la opción seleccionada.
                if self.lista.count() > self.MAXIMO_FILAS_SIN_CRECER: self.lista.scrollToItem(elemento)  # Desplaza únicamente listas extensas que realmente lo necesitan.
                else: self.lista.verticalScrollBar().setValue(0)  # Mantiene visibles todas las opciones de listas pequeñas sin saltos innecesarios.
                return  # Finaliza después de localizar la coincidencia.

    def mostrar_junto_control(self, control, ancho: int) -> None:
        cantidad = self.lista.count()  # Recupera la cantidad de opciones disponibles.
        filas_visibles = min(cantidad, self.MAXIMO_FILAS_SIN_CRECER)  # Determina cuántas filas deben formar parte de la altura máxima.
        alto_respaldo = self.lista.fontMetrics().height() + 16  # Calcula una fila coherente incluso antes de que Qt termine de resolver sizeHintForRow().
        alturas = [max(alto_respaldo, self.lista.sizeHintForRow(indice)) for indice in range(filas_visibles)]  # Recupera la altura real de cada fila visible.
        alto_filas = sum(alturas) + max(0, filas_visibles - 1) * self.lista.spacing()  # Suma exclusivamente contenido real y separaciones existentes.
        alto_deseado = max(48, alto_filas + 18) if cantidad else 48  # Añade solamente los márgenes del marco, evitando zonas vacías arbitrarias.
        alto_deseado = min(270, alto_deseado)  # Conserva el límite histórico para listas extensas.
        self.lista.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff if cantidad <= self.MAXIMO_FILAS_SIN_CRECER else Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra scrollbar únicamente cuando existen más filas que las admitidas sin crecer.
        if cantidad <= self.MAXIMO_FILAS_SIN_CRECER: self.lista.verticalScrollBar().setValue(0)  # Garantiza que una selección previa no deje opciones pequeñas fuera de la vista.

        origen = control.mapToGlobal(QPoint(0, 0))  # Recupera la posición global del selector.
        centro = control.mapToGlobal(control.rect().center())  # Obtiene un punto perteneciente al monitor actual.
        pantalla = QApplication.screenAt(centro) or QApplication.primaryScreen()  # Utiliza ese monitor o la pantalla principal como respaldo.
        if pantalla is None: return  # Evita mostrar el popup en una posición imposible de calcular cuando Qt todavía no conoce una pantalla.

        area = pantalla.availableGeometry()  # Recupera el área útil excluyendo la barra de tareas.
        margen = 8  # Reserva un pequeño espacio respecto a los bordes del monitor.
        separacion = 4  # Mantiene una separación discreta respecto al selector.
        ancho_popup = min(max(120, ancho), max(120, area.width() - margen * 2))  # Evita que el popup exceda horizontalmente la pantalla.
        espacio_abajo = area.bottom() - (origen.y() + control.height()) - margen - separacion  # Calcula el espacio útil inferior.
        espacio_arriba = origen.y() - area.top() - margen - separacion  # Calcula el espacio útil superior.

        if espacio_abajo >= alto_deseado:
            alto_popup = alto_deseado  # Conserva exactamente la altura necesaria cuando toda la lista cabe debajo.
            y = origen.y() + control.height() + separacion  # Abre debajo del selector.
        elif espacio_arriba >= alto_deseado:
            alto_popup = alto_deseado  # Conserva exactamente la altura necesaria cuando toda la lista cabe encima.
            y = origen.y() - alto_deseado - separacion  # Abre hacia arriba.
        elif espacio_arriba > espacio_abajo:
            alto_popup = max(48, espacio_arriba)  # Aprovecha la región superior únicamente cuando la pantalla obliga a reducir el popup.
            y = area.top() + margen  # Coloca el popup dentro del límite superior.
        else:
            alto_popup = max(48, espacio_abajo)  # Aprovecha el espacio inferior disponible cuando la pantalla obliga a reducirlo.
            y = origen.y() + control.height() + separacion  # Mantiene el popup debajo.

        alto_popup = min(alto_popup, area.height() - margen * 2)  # Garantiza que la altura final nunca exceda el monitor.
        x = max(area.left() + margen, min(origen.x(), area.right() - ancho_popup - margen + 1))  # Corrige cualquier desbordamiento horizontal.
        y = max(area.top() + margen, min(y, area.bottom() - alto_popup - margen + 1))  # Corrige cualquier desbordamiento vertical.
        self.setFixedSize(ancho_popup, alto_popup)  # Aplica las dimensiones calculadas.
        self.move(x, y)  # Sitúa completamente el popup dentro de la pantalla.
        self.show()  # Hace visible la ventana flotante.
        self.raise_()  # Garantiza que aparezca encima de Configuración.

    def _seleccionar_elemento(self, elemento: QListWidgetItem) -> None:
        if not self.isVisible(): return  # Evita una segunda emisión causada por itemActivated después de itemPressed.
        dato = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el valor real asociado con la fila.
        self.opcion_seleccionada.emit(dato)  # Comunica el valor antes de cerrar el popup.
        self.close()  # Cierra el desplegable después de entregar correctamente la selección.


class SelectorDesplegableConfiguracion(QFrame):  # Sustituye QComboBox mediante un selector completamente controlado por TecNet Finder.
    valor_cambiado = Signal(object)  # Informa al panel cuando el usuario selecciona realmente otro valor.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa la superficie principal.
        self.setObjectName("SelectorDesplegableConfiguracion")  # Identifica exclusivamente el selector.
        self.setFixedHeight(38)  # Mantiene la misma altura que CampoNumeroConfiguracion.
        self._datos = []  # Conserva las relaciones entre texto visible y valor real.
        self._dato_actual = None  # Conserva la selección actual.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente texto y flecha.
        diseno.setContentsMargins(0, 0, 0, 0)  # Utiliza toda la superficie.
        diseno.setSpacing(0)  # Une visualmente ambas partes.

        self.boton_texto = QPushButton("")  # Presenta el texto de la opción seleccionada.
        self.boton_texto.setObjectName("TextoSelectorConfiguracion")  # Permite estilizar el área principal.
        self.boton_texto.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica interacción.
        self.boton_texto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite alcanzar el selector mediante teclado.
        self.boton_texto.clicked.connect(self._mostrar_opciones)  # Abre o cierra el popup.

        self.boton_flecha = QPushButton("⌄")  # Utiliza una flecha propia en lugar del indicador nativo.
        self.boton_flecha.setObjectName("FlechaSelectorConfiguracion")  # Permite estilizar la zona derecha.
        self.boton_flecha.setFixedWidth(34)  # Reserva solamente el ancho necesario.
        self.boton_flecha.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica interacción.
        self.boton_flecha.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Mantiene un solo punto de foco.
        self.boton_flecha.clicked.connect(self._mostrar_opciones)  # Abre el mismo popup.

        diseno.addWidget(self.boton_texto, 1)  # Entrega la mayor parte del espacio al texto.
        diseno.addWidget(self.boton_flecha)  # Coloca la flecha al extremo derecho.

        self.popup = VentanaOpcionesConfiguracion(self.window())  # Crea una única ventana flotante reutilizable.
        self.popup.opcion_seleccionada.connect(self._seleccionar_valor)  # Recibe el dato antes de que el popup desaparezca.

        self.setStyleSheet("""
            QFrame#SelectorDesplegableConfiguracion { background-color: #313244; border: 1px solid #45475a; border-radius: 8px; }
            QPushButton#TextoSelectorConfiguracion { background-color: transparent; color: #cdd6f4; border: none; border-radius: 7px; padding: 5px 10px; text-align: left; }
            QPushButton#TextoSelectorConfiguracion:hover { background-color: #363649; }
            QPushButton#TextoSelectorConfiguracion:focus { color: #ffffff; }
            QPushButton#FlechaSelectorConfiguracion { background-color: transparent; color: #a6adc8; border: none; border-top-right-radius: 7px; border-bottom-right-radius: 7px; padding: 0px; font-family: "Segoe UI Symbol"; font-size: 13pt; }
            QPushButton#FlechaSelectorConfiguracion:hover { background-color: #45475a; color: #ffffff; }
        """)  # Conserva la paleta base para permitir la traducción dinámica del tema.

    def limpiar_opciones(self) -> None:
        self._datos.clear()  # Elimina todas las relaciones entre texto y valor.
        self._dato_actual = None  # Elimina también la selección actual.
        self.boton_texto.setText("")  # QPushButton no posee clear(), por lo que se elimina su texto mediante setText().
        self.boton_texto.setToolTip("")  # Elimina cualquier ayuda perteneciente a la opción anterior.
        self.popup.limpiar()  # Vacía también las filas del popup reutilizable.

    def agregar_opcion(self, texto: str, dato=None) -> None:
        dato_real = texto if dato is None else dato  # Utiliza el mismo texto como dato cuando no se necesita otro valor.
        self._datos.append((texto, dato_real))  # Conserva internamente la relación.
        self.popup.agregar_opcion(texto, dato_real)  # Registra la misma opción dentro del popup.
        if self._dato_actual is None: self.establecer_valor(dato_real, emitir=False)  # Utiliza la primera opción como selección inicial sin emitir un cambio.

    def establecer_valor(self, dato, emitir: bool = False) -> None:
        for texto, dato_opcion in self._datos:
            if dato_opcion == dato:
                cambio = self._dato_actual != dato_opcion  # Determina si realmente existe una modificación.
                self._dato_actual = dato_opcion  # Actualiza primero el estado interno.
                self.boton_texto.setText(texto)  # Presenta inmediatamente el texto correspondiente.
                self.boton_texto.setToolTip(texto)  # Permite consultar textos extensos.
                self.popup.seleccionar_dato(dato_opcion)  # Mantiene sincronizada la selección del popup.
                if emitir and cambio: self.valor_cambiado.emit(dato_opcion)  # Comunica solamente una selección real del usuario.
                return  # Finaliza una vez localizada la opción.

    def valor_actual(self):
        return self._dato_actual  # Permite consultar el valor actualmente seleccionado.

    def _mostrar_opciones(self) -> None:
        if self.popup.isVisible(): self.popup.close(); return  # Cierra el selector al pulsarlo nuevamente.
        self.popup.mostrar_junto_control(self, self.width())  # Decide automáticamente si el popup debe abrirse arriba o abajo.

    def _seleccionar_valor(self, dato) -> None:
        self.establecer_valor(dato, emitir=True)  # Actualiza el selector y comunica una selección confirmada.
