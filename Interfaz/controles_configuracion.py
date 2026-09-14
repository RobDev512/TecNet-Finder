# ============================================================
# Archivo: controles_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene controles visuales reutilizables para Configuración.
#
# Incluye:
# - Campo numérico sin botones nativos arriba/abajo.
# - Selector desplegable propio de TecNet Finder.
# - Popup redondeado y desplazable para listas de opciones.
#
# La selección del popup se procesa desde la presión del elemento
# para asegurar que el valor llegue al panel antes de que Qt cierre
# automáticamente una ventana con comportamiento Popup.
# ============================================================

from PySide6.QtCore import QPoint, Qt, Signal  # Proporciona posición, opciones visuales y señales para los controles personalizados.
from PySide6.QtWidgets import QAbstractSpinBox, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QVBoxLayout  # Importa los componentes base reutilizados.


class CampoNumeroConfiguracion(QSpinBox):  # Representa un campo numérico limpio sin los botones nativos de Windows.
    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa QSpinBox para conservar validación, teclado y límites numéricos.
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)  # Elimina completamente las flechas nativas arriba y abajo.
        self.setFixedHeight(38)  # Mantiene la misma altura que los selectores personalizados.
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Presenta el número como un campo de texto convencional.
        self.setStyleSheet("""
            QSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px 10px;
                selection-background-color: #585b70;
            }
            QSpinBox:hover { border-color: #585b70; }
            QSpinBox:focus { border-color: #89b4fa; }
        """)  # Mantiene el campo dentro de la misma estética oscura de TecNet Finder.


class VentanaOpcionesConfiguracion(QFrame):  # Representa el panel flotante utilizado por los desplegables personalizados.
    opcion_seleccionada = Signal(object)  # Comunica al selector el dato real relacionado con la opción elegida.

    def __init__(self, padre=None):
        super().__init__(padre, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)  # Crea un popup sin barra nativa que se cierra al pulsar fuera.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite que las esquinas exteriores realmente sean transparentes.
        self.setObjectName("VentanaOpcionesConfiguracion")  # Identifica esta ventana flotante dentro de sus estilos.

        diseno_exterior = QVBoxLayout(self)  # Reserva una zona mínima alrededor del marco visible.
        diseno_exterior.setContentsMargins(2, 2, 2, 2)  # Evita que el borde redondeado quede recortado.
        diseno_exterior.setSpacing(0)  # Mantiene el popup compacto.

        self.marco = QFrame()  # Crea la superficie visible del desplegable.
        self.marco.setObjectName("MarcoOpcionesConfiguracion")  # Permite aplicar fondo y esquinas exclusivamente al panel.
        diseno_marco = QVBoxLayout(self.marco)  # Organiza la lista dentro del marco.
        diseno_marco.setContentsMargins(5, 5, 5, 5)  # Separa las opciones ligeramente del contorno.
        diseno_marco.setSpacing(0)  # Deja que la lista administre internamente sus filas.

        self.lista = QListWidget()  # Crea la lista desplazable utilizada por fuentes y otras selecciones.
        self.lista.setObjectName("ListaOpcionesConfiguracion")  # Permite aplicar el estilo propio de la lista.
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Elimina cualquier desplazamiento horizontal.
        self.lista.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Presenta scrollbar solamente cuando la lista lo necesita.
        self.lista.setSpacing(1)  # Mantiene una separación mínima entre opciones.
        self.lista.itemPressed.connect(self._seleccionar_elemento)  # Procesa el clic desde la presión para evitar perderlo cuando Qt cierre el Popup.
        self.lista.itemActivated.connect(self._seleccionar_elemento)  # Permite confirmar también mediante Enter o activación de teclado.

        diseno_marco.addWidget(self.lista)  # Coloca la lista dentro del marco redondeado.
        diseno_exterior.addWidget(self.marco)  # Coloca el marco dentro de la pequeña región transparente.

        self.setStyleSheet("""
            QFrame#MarcoOpcionesConfiguracion {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 10px;
            }

            QListWidget#ListaOpcionesConfiguracion {
                background-color: transparent;
                color: #cdd6f4;
                border: none;
                outline: none;
                padding: 1px;
            }

            QListWidget#ListaOpcionesConfiguracion::item {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 7px 9px;
            }

            QListWidget#ListaOpcionesConfiguracion::item:hover {
                background-color: #313244;
                color: #ffffff;
            }

            QListWidget#ListaOpcionesConfiguracion::item:selected {
                background-color: #45475a;
                color: #ffffff;
            }

            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                margin: 4px 1px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background-color: #45475a;
                min-height: 28px;
                border: none;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover { background-color: #585b70; }
            QScrollBar::handle:vertical:pressed { background-color: #6c7086; }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: transparent;
                border: none;
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
                border: none;
            }
        """)  # Mantiene popup, selección y scrollbar completamente coherentes con el resto de Configuración.

    def limpiar(self) -> None:
        self.lista.clear()  # Elimina todas las opciones para poder reutilizar el mismo control.

    def agregar_opcion(self, texto: str, dato) -> None:
        elemento = QListWidgetItem(texto)  # Crea la fila que verá el usuario.
        elemento.setData(Qt.ItemDataRole.UserRole, dato)  # Guarda separadamente el valor real asociado con la fila.
        self.lista.addItem(elemento)  # Incorpora la opción al popup.

    def seleccionar_dato(self, dato) -> None:
        for indice in range(self.lista.count()):  # Recorre las opciones actualmente disponibles.
            elemento = self.lista.item(indice)  # Recupera el elemento correspondiente con la posición actual.
            if elemento.data(Qt.ItemDataRole.UserRole) == dato:  # Comprueba si corresponde con el dato solicitado.
                self.lista.setCurrentItem(elemento)  # Marca visualmente la misma selección dentro del popup.
                return  # Finaliza una vez localizada la coincidencia.

    def mostrar_debajo(self, control, ancho: int) -> None:
        cantidad = self.lista.count()  # Obtiene la cantidad de opciones disponibles.
        alto_fila = self.lista.sizeHintForRow(0) if cantidad else 34  # Obtiene la altura real de una opción o utiliza un respaldo seguro.
        alto = min(270, max(48, alto_fila * min(cantidad, 7) + 14))  # Limita la altura para que listas extensas utilicen scrollbar.
        posicion = control.mapToGlobal(QPoint(0, control.height() + 4))  # Calcula una posición inmediatamente debajo del selector.
        self.setFixedSize(ancho, alto)  # Mantiene el mismo ancho del selector y una altura controlada.
        self.move(posicion)  # Coloca el panel en la posición calculada.
        self.show()  # Hace visible el popup.
        self.raise_()  # Garantiza que aparezca encima de Configuración.

    def _seleccionar_elemento(self, elemento: QListWidgetItem) -> None:
        if not self.isVisible():  # Evita procesar nuevamente una activación emitida después de que itemPressed ya cerró el popup.
            return  # Impide una segunda emisión accidental del mismo valor.
        dato = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el valor real relacionado con la opción.
        self.opcion_seleccionada.emit(dato)  # Envía el dato al selector antes de cerrar la ventana Popup.
        self.close()  # Cierra el desplegable solamente después de haber comunicado correctamente la selección.


class SelectorDesplegableConfiguracion(QFrame):  # Sustituye QComboBox mediante un selector completamente controlado por TecNet Finder.
    valor_cambiado = Signal(object)  # Informa al panel cuando el usuario selecciona realmente un valor diferente.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el marco utilizado como superficie del selector.
        self.setObjectName("SelectorDesplegableConfiguracion")  # Permite identificar exclusivamente este componente.
        self.setFixedHeight(38)  # Mantiene la misma altura que el campo numérico.
        self._datos = []  # Conserva las relaciones entre texto visible y valor real.
        self._dato_actual = None  # Conserva el valor seleccionado actualmente.

        diseno = QHBoxLayout(self)  # Organiza horizontalmente texto y flecha.
        diseno.setContentsMargins(0, 0, 0, 0)  # Hace que ambos controles ocupen toda la superficie.
        diseno.setSpacing(0)  # Elimina separaciones visuales entre texto y flecha.

        self.boton_texto = QPushButton("")  # Presenta el texto de la opción seleccionada.
        self.boton_texto.setObjectName("TextoSelectorConfiguracion")  # Permite estilizar el área principal.
        self.boton_texto.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que todo el campo puede abrirse.
        self.boton_texto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite seleccionar el control mediante teclado.
        self.boton_texto.clicked.connect(self._mostrar_opciones)  # Abre o cierra el popup al pulsar el texto.

        self.boton_flecha = QPushButton("⌄")  # Utiliza una flecha sencilla en lugar del indicador nativo de Windows.
        self.boton_flecha.setObjectName("FlechaSelectorConfiguracion")  # Permite aplicar un hover independiente.
        self.boton_flecha.setFixedWidth(34)  # Reserva únicamente el espacio necesario para la flecha.
        self.boton_flecha.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que la flecha también es interactiva.
        self.boton_flecha.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Mantiene un solo punto de foco para todo el selector.
        self.boton_flecha.clicked.connect(self._mostrar_opciones)  # Abre exactamente el mismo popup desde la flecha.

        diseno.addWidget(self.boton_texto, 1)  # Entrega al texto todo el espacio horizontal disponible.
        diseno.addWidget(self.boton_flecha)  # Coloca la flecha en el extremo derecho.

        self.popup = VentanaOpcionesConfiguracion(self.window())  # Crea el panel flotante reutilizado por este selector.
        self.popup.opcion_seleccionada.connect(self._seleccionar_valor)  # Recibe el dato antes de que el Popup desaparezca.

        self.setStyleSheet("""
            QFrame#SelectorDesplegableConfiguracion {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
            }

            QPushButton#TextoSelectorConfiguracion {
                background-color: transparent;
                color: #cdd6f4;
                border: none;
                border-radius: 7px;
                padding: 5px 10px;
                text-align: left;
            }

            QPushButton#TextoSelectorConfiguracion:hover {
                background-color: #363649;
            }

            QPushButton#TextoSelectorConfiguracion:focus {
                color: #ffffff;
            }

            QPushButton#FlechaSelectorConfiguracion {
                background-color: transparent;
                color: #a6adc8;
                border: none;
                border-top-right-radius: 7px;
                border-bottom-right-radius: 7px;
                padding: 0px;
                font-family: "Segoe UI Symbol";
                font-size: 13pt;
            }

            QPushButton#FlechaSelectorConfiguracion:hover {
                background-color: #45475a;
                color: #ffffff;
            }
        """)  # Mantiene el selector limpio, redondeado y separado de la apariencia nativa de QComboBox.

    def agregar_opcion(self, texto: str, dato=None) -> None:
        dato_real = texto if dato is None else dato  # Utiliza el mismo texto como dato cuando no se necesita otro valor.
        self._datos.append((texto, dato_real))  # Conserva internamente la relación entre presentación y dato.
        self.popup.agregar_opcion(texto, dato_real)  # Registra la misma opción dentro del popup.
        if self._dato_actual is None:  # Comprueba si todavía no se había seleccionado ningún elemento.
            self.establecer_valor(dato_real, emitir=False)  # Utiliza la primera opción como selección inicial sin generar un cambio.

    def establecer_valor(self, dato, emitir: bool = False) -> None:
        for texto, dato_opcion in self._datos:  # Recorre las opciones disponibles hasta localizar el dato.
            if dato_opcion == dato:  # Comprueba si corresponde con el valor solicitado.
                cambio = self._dato_actual != dato_opcion  # Determina si el usuario realmente eligió algo diferente.
                self._dato_actual = dato_opcion  # Actualiza primero el estado interno del selector.
                self.boton_texto.setText(texto)  # Presenta inmediatamente el texto correspondiente.
                self.popup.seleccionar_dato(dato_opcion)  # Mantiene sincronizada la selección visual del popup.
                if emitir and cambio:  # Comprueba que sea una selección del usuario y un valor realmente nuevo.
                    self.valor_cambiado.emit(dato_opcion)  # Informa el cambio para que la preferencia temporal pueda actualizarse.
                return  # Finaliza cuando encuentra la opción.

    def valor_actual(self):
        return self._dato_actual  # Permite consultar el valor actualmente seleccionado.

    def _mostrar_opciones(self) -> None:
        if self.popup.isVisible():  # Comprueba si el usuario pulsó nuevamente un selector ya abierto.
            self.popup.close()  # Cierra el panel en lugar de crear otro.
            return  # Evita volver a mostrarlo.
        self.popup.mostrar_debajo(self, self.width())  # Abre el panel inmediatamente debajo utilizando el mismo ancho.

    def _seleccionar_valor(self, dato) -> None:
        self.establecer_valor(dato, emitir=True)  # Actualiza el selector y emite el cambio después de recibir la selección del popup.