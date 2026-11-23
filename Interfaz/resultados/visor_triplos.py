# ============================================================
# Archivo: visor_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Presenta el código intermedio en tres columnas, conserva
# las referencias y permite filtrar las operaciones por cada
# instrucción original sin alterar la numeración de triplos.
# ============================================================

import re  # Permite reconocer logaritmos, redondeos y potencias dentro de las comprobaciones.
from html import escape  # Protege el texto de cada operación antes de presentarlo con formato enriquecido.

from PySide6.QtCore import QEvent, QPoint, QRectF, QSize, Qt  # Proporciona eventos, dimensiones, posiciones y opciones de alineación.
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPalette, QPolygon, QRegion, QTextDocument  # Dibuja expresiones, flechas y contornos redondeados.
from PySide6.QtWidgets import QApplication, QAbstractItemView, QComboBox, QFrame, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QListView, QPushButton, QStyledItemDelegate, QStyle, QStyleOptionViewItem, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget  # Construye el visor integrado con el estilo visual de Qt.

from Motor.configuracion.catalogo_temas import obtener_tema  # Recupera los colores del tema activo sin crear una paleta independiente.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Detecta el tema elegido para redondear los controles de forma coherente.
from Motor.compilacion.modelos import ResultadoCompilacion  # Recupera los triplos y su ejecución desde el resultado general.


def comprobacion_html(texto: str) -> str:
    texto = escape(texto)  # Evita interpretar como HTML cualquier fragmento proveniente del código fuente.
    texto = re.sub(r"\blog2\(", "log<sub>2</sub>(", texto)  # Presenta la base del logaritmo como subíndice.
    texto = re.sub(r"\bceil\(\((\d+)\)\)", r"⌈(\1)⌉", texto)  # Convierte el techo de una referencia en notación matemática.
    texto = re.sub(r"\bceil\((-?\d+(?:\.\d+)?)\)", r"⌈\1⌉", texto)  # Convierte el techo de un número en notación matemática.
    texto = re.sub(r"(?<![\w])([+-]?\d+)\s+\^\s+\((\d+)\)", r"\1<sup>(\2)</sup>", texto)  # Eleva las referencias que se utilizan como exponentes.
    texto = re.sub(r"(?<![\w])([+-]?\d+)\s+\^\s+(\d+)", r"\1<sup>\2</sup>", texto)  # Eleva los exponentes numéricos ya resueltos.
    return texto.replace(" -&gt; ", " → ")  # Conserva el recorrido de sustitución de los resultados intermedios.


class DelegadoComprobacion(QStyledItemDelegate):  # Dibuja únicamente la última columna mediante texto enriquecido.
    def _documento(self, texto: str, fuente, color: str, ancho: int) -> QTextDocument:
        documento = QTextDocument()  # Crea una representación temporal sin mantener widgets por celda.
        documento.setDefaultFont(fuente)  # Utiliza la tipografía configurada para la tabla y el tema activo.
        documento.setDocumentMargin(0)  # Evita márgenes HTML adicionales que dificulten la alineación.
        documento.setHtml(f'<span style="color: {color};">{comprobacion_html(texto)}</span>')  # Aplica color del tema y formato matemático seguro.
        documento.setTextWidth(max(1, ancho))  # Ajusta las líneas al ancho realmente disponible.
        return documento

    def paint(self, pintor, opcion, indice) -> None:
        estilo_opcion = QStyleOptionViewItem(opcion)  # Copia el estado visual de la celda para conservar selección y alternancia de filas.
        self.initStyleOption(estilo_opcion, indice)  # Recupera colores, foco y tipografía reales de Qt.
        estilo_opcion.text = ""  # Evita que Qt dibuje texto plano encima de nuestro formato enriquecido.
        estilo = estilo_opcion.widget.style() if estilo_opcion.widget is not None else QApplication.style()  # Utiliza el estilo vigente de la aplicación.
        pintor.save()  # Aísla las operaciones gráficas de esta celda.
        estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, estilo_opcion, pintor, estilo_opcion.widget)  # Dibuja fondo y selección como cualquier otra celda.
        seleccionado = bool(opcion.state & QStyle.StateFlag.State_Selected)  # Identifica cuándo debe emplearse el contraste de selección.
        rol = QPalette.ColorRole.HighlightedText if seleccionado else QPalette.ColorRole.Text  # Selecciona el color coherente con el tema.
        color = opcion.palette.color(rol).name()  # Obtiene el valor del tema sin establecer colores fijos.
        ancho = max(1, opcion.rect.width() - 16)  # Reserva ocho píxeles a cada lado del contenido.
        documento = self._documento(str(indice.data(Qt.ItemDataRole.DisplayRole) or ""), opcion.font, color, ancho)  # Prepara las expresiones formateadas.
        pintor.translate(opcion.rect.left() + 8, opcion.rect.top() + max(0, (opcion.rect.height() - documento.size().height()) / 2))  # Alinea el contenido verticalmente.
        documento.drawContents(pintor, QRectF(0, 0, ancho, documento.size().height()))  # Dibuja el texto con subíndices y exponentes reales.
        pintor.restore()  # Devuelve al pintor su estado previo.

    def sizeHint(self, opcion, indice) -> QSize:
        ancho = max(250, opcion.rect.width() - 16)  # Evita tamaños inestables antes de que la tabla tenga geometría final.
        documento = self._documento(str(indice.data(Qt.ItemDataRole.DisplayRole) or ""), opcion.font, "#000000", ancho)  # Mide la misma comprobación que se dibujará.
        tamano = super().sizeHint(opcion, indice)  # Conserva el mínimo calculado por Qt para cualquier celda.
        return QSize(max(tamano.width(), 250), max(tamano.height(), int(documento.size().height()) + 14))  # Reserva altura suficiente para varias líneas.


class TablaTriplosRedondeada(QTableWidget):  # Recorta las esquinas reales del encabezado, las celdas y el desplazamiento.
    def _ajustar_mascara(self) -> None:
        if self.width() <= 0 or self.height() <= 0: return  # Espera a tener una geometría válida antes de construir el recorte.
        contorno = QPainterPath()  # Prepara una figura que también limita los widgets hijos de la tabla.
        contorno.addRoundedRect(QRectF(self.rect()), 10, 10)  # Recorta las cuatro esquinas, no solo el borde del marco exterior.
        self.setMask(QRegion(contorno.toFillPolygon().toPolygon()))  # Impide que el encabezado o el viewport tapen las esquinas.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Conserva la distribución nativa de columnas, encabezado y barras de desplazamiento.
        self._ajustar_mascara()  # Recalcula el recorte al cambiar el ancho o la altura del visor.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt termine de construir el viewport y las barras.
        self._ajustar_mascara()  # Garantiza las esquinas redondeadas también en la primera apertura.


class ListaOpcionesTriplos(QListView):  # Identifica la opción bajo el cursor sin alterar la selección confirmada.
    def __init__(self, padre=None):
        super().__init__(padre)  # Conserva el comportamiento del desplegable original.
        self.fila_hover = -1  # Distingue el movimiento del cursor de la selección vigente del combo.
        self.setMouseTracking(True)  # Recibe movimientos incluso sin presionar el botón del mouse.
        self.viewport().setMouseTracking(True)  # Permite detectar el hover sobre las opciones reales.

    def mouseMoveEvent(self, evento) -> None:
        fila = self.indexAt(evento.position().toPoint()).row()  # Determina la opción apuntada sin seleccionarla.
        if fila != self.fila_hover:
            self.fila_hover = fila  # Actualiza únicamente la posición visual del cursor.
            self.viewport().update()  # Redibuja el hover sin modificar el índice confirmado.
        super().mouseMoveEvent(evento)  # Mantiene la navegación y los eventos de Qt.

    def viewportEvent(self, evento) -> bool:
        if evento.type() == QEvent.Type.Leave and self.fila_hover != -1:
            self.fila_hover = -1  # Elimina el resaltado temporal al salir del menú.
            self.viewport().update()  # Restablece el color normal de las opciones.
        return super().viewportEvent(evento)  # Conserva el resto de eventos del listado.


class DelegadoOpcionesTriplos(QStyledItemDelegate):  # Dibuja colores independientes para selección y hover.
    def __init__(self, selector, padre=None):
        super().__init__(padre)  # Reutiliza el mecanismo de delegados de Qt.
        self.selector = selector  # Consulta la opción efectivamente elegida en el QComboBox.
        self.color_normal = QColor('#172a36')  # Mantiene un respaldo hasta aplicar la paleta del tema.
        self.color_seleccion = QColor('#74c7ec')  # Reserva el azul de acento para la opción elegida.
        self.color_hover = QColor('#325a70')  # Utiliza un azul más discreto mientras se desplaza el mouse.
        self.texto_normal = QColor('#ffffff')  # Conserva legibilidad antes del primer cambio de tema.
        self.texto_seleccion = QColor('#101820')  # Permite leer el fondo resaltado.

    def colores_fila(self, fila: int):
        if fila == self.selector.currentIndex():
            return self.color_seleccion, self.texto_seleccion  # La selección permanece resaltada aunque se mueva el cursor.
        if fila == self.selector.vista_opciones.fila_hover:
            return self.color_hover, self.texto_normal  # El hover utiliza otro tono sin confirmar la opción.
        return self.color_normal, self.texto_normal  # Las demás opciones conservan el color del panel.

    def paint(self, pintor, opcion, indice) -> None:
        fondo, texto = self.colores_fila(indice.row())  # Obtiene colores según selección fija o cursor temporal.
        pintor.save()  # Evita que el estado del dibujo afecte a otras opciones.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)  # Suaviza las esquinas del resaltado.
        pintor.setPen(Qt.PenStyle.NoPen)  # No agrega bordes internos a cada opción.
        pintor.setBrush(fondo)  # Distingue el color elegido del color de hover.
        pintor.drawRoundedRect(opcion.rect.adjusted(3, 2, -3, -2), 7, 7)  # Conserva la selección redondeada de mantenimiento.
        pintor.setPen(texto)  # Utiliza contraste según el fondo que se acaba de pintar.
        pintor.setFont(opcion.font)  # Respeta la tipografía elegida por el usuario.
        contenido = opcion.rect.adjusted(17, 0, -10, 0)  # Deja el mismo margen interior que las otras opciones.
        cadena = str(indice.data(Qt.ItemDataRole.DisplayRole) or '')  # Recupera la traducción activa sin abreviar el contenido.
        pintor.drawText(contenido, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, cadena)  # Muestra la opción centrada verticalmente.
        pintor.restore()  # Devuelve a Qt el estado original del pintor.

    def sizeHint(self, opcion, indice) -> QSize:
        tamano = super().sizeHint(opcion, indice)  # Mantiene el ancho mínimo calculado por Qt.
        return QSize(tamano.width(), max(43, tamano.height()))  # Proporciona una altura cómoda al selector sin alterar el modelo.


class SelectorInstruccionTriplos(QComboBox):  # Dibuja la flecha y redondea el menú sin depender del estilo nativo de Windows.
    def __init__(self, padre=None):
        super().__init__(padre)  # Conserva las señales y el modelo habitual de QComboBox.
        self.color_flecha = QColor("#ffffff")  # Establece un respaldo hasta que se aplique el tema configurado.
        self.vista_opciones = ListaOpcionesTriplos()  # Detecta el hover sin cambiar la selección confirmada.
        self.vista_opciones.setObjectName("OpcionesInstruccionTriplo")  # Limita los estilos a esta lista de instrucciones.
        self.vista_opciones.setFrameShape(QFrame.Shape.NoFrame)  # Evita que aparezca un segundo borde cuadrado en el desplegable.
        self.vista_opciones.setSpacing(2)  # Mantiene la separación entre opciones del Centro de mantenimiento.
        self.setView(self.vista_opciones)  # Sustituye la lista nativa por una vista con selección redondeada.
        self.delegado_opciones = DelegadoOpcionesTriplos(self, self.vista_opciones)  # Separa visualmente la selección y el hover.
        self.vista_opciones.setItemDelegate(self.delegado_opciones)  # Aplica los colores de cada estado al menú real.

    def paintEvent(self, evento) -> None:
        super().paintEvent(evento)  # Dibuja primero el control y el texto con el tema vigente.
        pintor = QPainter(self)  # Recupera la zona del botón que Qt deja libre para la flecha.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)  # Suaviza los bordes del pequeño triángulo.
        pintor.setPen(Qt.PenStyle.NoPen)  # Evita dibujar un contorno diferente al color del icono.
        pintor.setBrush(self.color_flecha)  # Utiliza el mismo color del texto del tema activo.
        centro_x = self.width() - 16  # Coloca la flecha a la derecha como en el selector de Registros.
        centro_y = self.height() // 2  # Mantiene el icono centrado al cambiar la altura de la fila.
        pintor.drawPolygon(QPolygon([QPoint(centro_x - 4, centro_y - 2), QPoint(centro_x + 4, centro_y - 2), QPoint(centro_x, centro_y + 3)]))  # Dibuja una flecha descendente legible.
        pintor.end()  # Libera el pintor antes de que Qt termine el evento.

    def showPopup(self) -> None:
        self.vista_opciones.fila_hover = -1  # Evita conservar el resaltado temporal de una apertura anterior.
        super().showPopup()  # Permite que Qt calcule el tamaño real del menú y su desplazamiento.
        ventana = self.view().window()  # Recupera el contenedor emergente, no el cuadro del selector.
        if ventana.width() <= 0 or ventana.height() <= 0: return  # Espera una geometría válida antes de colocarlo.
        posicion = self.mapToGlobal(QPoint(0, self.height() + 4))  # Sitúa el menú debajo del cuadro, con cuatro píxeles de separación.
        pantalla = self.screen()  # Utiliza el monitor donde se encuentra TecNet Finder.
        if pantalla is not None:
            limite = pantalla.availableGeometry()  # Evita que el desplegable se salga del área visible del escritorio.
            if posicion.y() + ventana.height() > limite.bottom() + 1:
                encima = self.mapToGlobal(QPoint(0, -ventana.height() - 4))  # Prepara una alternativa si no cabe abajo.
                posicion.setY(encima.y() if encima.y() >= limite.top() else max(limite.top(), limite.bottom() + 1 - ventana.height()))  # Prioriza mostrar todas las opciones.
            posicion.setX(max(limite.left(), min(posicion.x(), limite.right() + 1 - ventana.width())))  # Conserva visible el borde derecho.
        ventana.move(posicion)  # Corrige la alineación nativa de Qt con la opción seleccionada.
        contorno = QPainterPath()  # Conserva la máscara existente de las cuatro esquinas.
        contorno.addRoundedRect(QRectF(ventana.rect()), 10, 10)  # Suaviza el menú completo.
        ventana.setMask(QRegion(contorno.toFillPolygon().toPolygon()))  # Evita las esquinas cuadradas del popup.


class VisorTriplos(QWidget):  # Reúne el encabezado, la tabla del código intermedio y la acción de copiado.
    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el contenedor independiente de la pestaña principal.
        diseno = QVBoxLayout(self)  # Organiza el encabezado y la tabla verticalmente.
        diseno.setContentsMargins(4, 4, 4, 4)  # Respeta los márgenes compactos de las demás fases.
        diseno.setSpacing(8)  # Mantiene una separación uniforme entre los controles.
        fila_superior = QHBoxLayout()  # Coloca el contador y el botón sin ocupar espacio de la tabla.
        self.contador = QLabel("Triplos: 0")  # Identifica la cantidad actual de operaciones generadas.
        self.selector_instruccion = SelectorInstruccionTriplos()  # Permite filtrar redes y conserva el desplegable redondeado de mantenimiento.
        self.selector_instruccion.setObjectName("SelectorInstruccionTriplo")  # Facilita localizar el control desde las pruebas y los temas.
        self.selector_instruccion.setMinimumWidth(185)  # Mantiene visible la línea seleccionada en ventanas estrechas.
        self.selector_instruccion.setMaximumWidth(285)  # Reserva espacio para mostrar el código fuente completo.
        self.selector_instruccion.setEnabled(False)  # Se habilita al compilar al menos una instrucción válida.
        self.marco_selector = QFrame()  # Emplea el mismo contenedor del filtro por niveles del Centro de mantenimiento.
        self.marco_selector.setObjectName("MarcoSelectorTriplos")  # Identifica el borde exterior sin afectar otros desplegables.
        self.marco_selector.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Hace visibles las esquinas del marco completo.
        diseno_selector = QHBoxLayout(self.marco_selector)  # Encierra el combo sin que su propia superficie cubra el borde.
        diseno_selector.setContentsMargins(1, 1, 1, 1)  # Reproduce exactamente el margen usado en MantenimientoMarcoNivel.
        diseno_selector.addWidget(self.selector_instruccion)  # Mantiene el comportamiento de selección y la flecha nativos.
        self.campo_fuente = QLineEdit()  # Presenta la instrucción original asociada con la selección.
        self.campo_fuente.setObjectName("FuenteInstruccionTriplo")  # Permite adaptar el campo al tema sin afectar el editor principal.
        self.campo_fuente.setReadOnly(True)  # Impide modificar accidentalmente el código desde el resultado.
        self.campo_fuente.setMinimumWidth(170)  # Conserva un área visible para el texto de la instrucción.
        self.campo_fuente.setPlaceholderText("Selecciona una instrucción para ver su código fuente.")  # Explica el uso del filtro.
        self.boton_copiar = QPushButton()  # Emplea el mismo botón cuadrado de copiado que el resto de la interfaz.
        self.boton_copiar.setObjectName("BotonFlotantePanel")  # Reutiliza la apariencia de los controles con iconos del proyecto.
        self.boton_copiar.setFixedSize(32, 32)  # Evita que el texto de la acción cambie el ancho del encabezado.
        self.boton_copiar.setCursor(Qt.CursorShape.PointingHandCursor)  # Identifica visualmente la acción disponible.
        self.boton_copiar.setToolTip("Copiar tabla")  # Explica la acción sin mostrar una etiqueta extensa.
        self.boton_copiar.setAccessibleName("Copiar tabla")  # Conserva el nombre para lectores de pantalla.
        self.boton_copiar.setEnabled(False)  # No permite copiar información inexistente.
        self.boton_copiar.clicked.connect(self.copiar_tabla)  # Copia una representación tabulada al portapapeles.
        fila_superior.addWidget(self.contador)  # Coloca el contador a la izquierda.
        fila_superior.addSpacing(12)  # Separa la cantidad de triplos del selector de instrucciones.
        fila_superior.addWidget(self.marco_selector)  # Integra el selector con el marco redondeado del Centro de mantenimiento.
        fila_superior.addWidget(self.campo_fuente, 1)  # Muestra el código fuente usando el espacio disponible.
        fila_superior.addWidget(self.boton_copiar)  # Coloca la acción de copia a la derecha.
        diseno.addLayout(fila_superior)  # Agrega el encabezado a la sección.

        self.tabla = TablaTriplosRedondeada(0, 3)  # Redondea de verdad el encabezado y las celdas sin cambiar el modelo de tres columnas.
        self.tabla.setObjectName("TablaTriplos")  # Identifica el control para los estilos y las pruebas de interfaz.
        self.tabla.setHorizontalHeaderLabels(["(n)", "(Op, Arg1, Arg2)", "Comprobación"])  # Mantiene las columnas solicitadas.
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide cambiar las operaciones desde la visualización.
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Permite reconocer la comprobación completa de una operación.
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Evita selecciones accidentales entre referencias diferentes.
        self.tabla.setAlternatingRowColors(True)  # Aprovecha los colores alternos definidos por el tema.
        self.tabla.setWordWrap(True)  # Permite representar comprobaciones largas en varias líneas.
        self.tabla.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita recortar expresiones con puntos suspensivos.
        self.tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Conserva columnas legibles en ventanas estrechas.
        self.tabla.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite desplazamiento horizontal suave.
        self.tabla.verticalHeader().setVisible(False)  # Evita duplicar la numeración que ya forma parte de los triplos.
        self.tabla.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Adapta cada fila a su comprobación.
        self.tabla.verticalHeader().setMinimumSectionSize(38)  # Evita filas excesivamente comprimidas.
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Permite definir anchos mínimos y proporciones.
        self.tabla.horizontalHeader().setStretchLastSection(False)  # Evita anchos desproporcionados por la última columna.
        self.tabla.setItemDelegateForColumn(2, DelegadoComprobacion(self.tabla))  # Aplica símbolos matemáticos solo a las comprobaciones.
        self.tabla.horizontalHeader().sectionResized.connect(self._ajustar_altura_filas)  # Recalcula alturas cuando cambie el ancho de cualquier columna.
        self.marco_tabla = QFrame()  # Rodea el visor con esquinas realmente redondeadas, como el Centro de mantenimiento.
        self.marco_tabla.setObjectName("MarcoTablaTriplos")  # Limita el marco al código intermedio sin afectar otras tablas.
        self.marco_tabla.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt pinte el borde y el fondo redondeado.
        diseno_marco = QVBoxLayout(self.marco_tabla)  # Deja una separación entre los encabezados rectangulares y las esquinas.
        diseno_marco.setContentsMargins(7, 7, 7, 7)  # Evita que la tabla cubra las cuatro esquinas del contenedor.
        diseno_marco.setSpacing(0)  # Mantiene la tabla compacta dentro de su marco.
        diseno_marco.addWidget(self.tabla)  # Conserva el desplazamiento y las celdas originales dentro del marco.
        diseno.addWidget(self.marco_tabla, 1)  # Reserva la altura disponible para el visor completo.

        self.triplos_completos = []  # Conserva la secuencia sin filtros para restaurarla cuando sea necesario.
        self.comprobaciones = {}  # Conserva los resultados del intérprete por el índice original de cada triplo.
        self.grupos = []  # Agrupa los triplos por el bloque de red y la línea del código fuente.
        self.lineas_fuente = []  # Conserva las líneas originales sin depender de la posición visual de las filas.
        self.origenes = []  # Conserva la procedencia de las operaciones visibles para actualizar sus ayudas.
        self.operadores = []  # Conserva los operadores para mostrar explicaciones breves al pasar el cursor.
        self.filas_grupo = set()  # Distingue encabezados decorativos de triplos reales para copiar y seleccionar correctamente.
        self.cantidad_visible = 0  # Cuenta operaciones y nunca incluye las filas que separan redes.
        self.ayudas_operadores = {
            "INICIAR_RED": "Establece la red base y la primera dirección disponible.",
            "SOLICITUD": "Relaciona los hosts solicitados con el tamaño de bloque calculado.",
            "ASIGNAR_VLSM": "Reserva la subred desde el cursor actual y calcula su broadcast.",
            "SIGUIENTE_CURSOR": "Avanza a la dirección posterior al broadcast para la siguiente subred.",
        }  # Explica las operaciones de red sin alterar las comprobaciones del intérprete.
        self.formato_origen = "Línea {linea} · Bloque {bloque}"  # Describe dónde se generó cada operación.
        self.formato_host = "HOSTS posición {posicion}"  # Identifica la solicitud original incluso si fue reordenada.
        self.formato_contador = "Triplos: {cantidad}"  # Conserva el conteo general aunque todavía no se haya aplicado el idioma.
        self.texto_todas = "Todas las instrucciones"  # Identifica la vista completa de la secuencia intermedia.
        self.formato_linea = "Línea {linea}"  # Etiqueta la instrucción original dentro del selector.
        self.formato_grupo = "Red: {nombre}    |    IP base: {ip}    |    Línea: {linea}"  # Presenta separadores equivalentes a los de la tabla de tokens.
        self.texto_fuente = "Selecciona una instrucción para ver su código fuente."  # Describe cómo consultar la expresión original.
        self.formato_contador_filtrado = "Triplos: {visibles} de {total}"  # Diferencia las filas visibles del total generado.
        self.mensaje_vacio = "Compila una instrucción válida para visualizar los triplos."  # Conserva el texto inicial configurable por idioma.
        self.mensaje_sin_bloques = "No hay bloques válidos para generar triplos."  # Explica los resultados vacíos sin inventar operaciones.
        self.mensaje_no_disponible = "El código intermedio no está disponible."  # Distingue una ejecución no disponible de una secuencia vacía.
        self.etiqueta_estado = QLabel(self.mensaje_vacio)  # Muestra instrucciones o el motivo de ausencia de resultados.
        self.etiqueta_estado.setWordWrap(True)  # Permite leer el mensaje en ventanas estrechas.
        diseno.addWidget(self.etiqueta_estado)  # Conserva la explicación debajo de la tabla.
        self.selector_instruccion.addItem(self.texto_todas, None)  # Presenta el filtro general aunque todavía no exista una compilación.
        self.selector_instruccion.currentIndexChanged.connect(self._filtrar_instruccion)  # Cambia la vista sin volver a ejecutar el compilador.
        self.tabla.itemSelectionChanged.connect(self._actualizar_fuente)  # Permite consultar la línea original desde cualquier triplo seleccionado.
        self._aplicar_estilos()  # Aplica bordes redondeados sin cambiar los componentes globales de la aplicación.
        self._ajustar_columnas()  # Establece anchos mínimos antes de mostrar resultados.

    def _aplicar_estilos(self) -> None:
        p = obtener_tema(PreferenciasTema().tema())  # Obtiene los colores actuales para respetar los temas claros y oscuros.
        self.marco_selector.setStyleSheet(f"""
            QFrame#MarcoSelectorTriplos {{ background-color: {p["editor"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 8px; }}
            QComboBox#SelectorInstruccionTriplo {{ background: transparent; color: {p["texto"]}; border: none; border-radius: 7px; padding: 7px 30px 7px 9px; }}
            QComboBox#SelectorInstruccionTriplo::drop-down {{ background: transparent; border: none; border-top-right-radius: 7px; border-bottom-right-radius: 7px; width: 25px; }}
            QComboBox#SelectorInstruccionTriplo::down-arrow {{ image: none; width: 0px; height: 0px; }}
            QComboBox#SelectorInstruccionTriplo QAbstractItemView {{ background-color: {p["panel"]}; color: {p["texto"]}; selection-background-color: {p["acento"]}; selection-color: {p["texto_inverso"]}; }}
        """)  # Conserva el marco de Mantenimiento y reserva espacio para dibujar la flecha visible.
        self.selector_instruccion.color_flecha = QColor(p["texto"])  # Sincroniza el icono desplegable con el tema claro u oscuro.
        self.selector_instruccion.vista_opciones.setStyleSheet(f"""
            QListView#OpcionesInstruccionTriplo {{ background-color: {p["panel"]}; color: {p["texto"]}; border: none; border-radius: 9px; outline: none; padding: 7px; }}
            QListView#OpcionesInstruccionTriplo::item {{ background: transparent; color: {p["texto"]}; border: none; border-radius: 7px; padding: 7px 9px; min-height: 22px; }}
            QListView#OpcionesInstruccionTriplo::item:selected {{ background-color: {p["acento"]}; color: {p["texto_inverso"]}; }}
            QListView#OpcionesInstruccionTriplo::item:hover:!selected {{ background-color: {p["superficie_hover"]}; color: {p["texto"]}; }}
        """)  # Aplica directamente al menú su selección azul redondeada en lugar de depender de estilos heredados.
        paleta_opciones = self.selector_instruccion.vista_opciones.palette()  # Recupera el contraste utilizado por Qt para la vista emergente.
        paleta_opciones.setColor(QPalette.ColorRole.Highlight, QColor(p["acento"]))  # Utiliza el mismo acento de las pestañas y controles de mantenimiento.
        paleta_opciones.setColor(QPalette.ColorRole.HighlightedText, QColor(p["texto_inverso"]))  # Mantiene legible la opción seleccionada.
        self.selector_instruccion.vista_opciones.setPalette(paleta_opciones)  # Aplica la selección a la lista real del popup.
        delegado = self.selector_instruccion.delegado_opciones  # Configura también los estados dibujados de manera independiente.
        delegado.color_normal = QColor(p["panel"])  # Conserva el fondo neutro de las opciones disponibles.
        delegado.color_seleccion = QColor(p["acento"])  # Destaca la opción confirmada con el azul fuerte del tema.
        color_base = QColor(p["panel"])  # Mezcla el fondo con el acento para producir un segundo azul más discreto.
        color_acento = QColor(p["acento"])  # Recupera el acento actual sin fijar un tono que falle en temas claros.
        delegado.color_hover = QColor(round(color_base.red() * 0.52 + color_acento.red() * 0.48), round(color_base.green() * 0.52 + color_acento.green() * 0.48), round(color_base.blue() * 0.52 + color_acento.blue() * 0.48))  # Diferencia el hover de la selección para todos los temas.
        delegado.texto_normal = QColor(p["texto"])  # Mantiene legible el texto en el fondo y el hover.
        delegado.texto_seleccion = QColor(p["texto_inverso"])  # Conserva contraste en la opción seleccionada.
        self.selector_instruccion.vista_opciones.viewport().update()  # Redibuja las opciones después de cambiar de tema.
        ventana_opciones = self.selector_instruccion.vista_opciones.window()  # Recupera el contenedor que Qt muestra como popup.
        ventana_opciones.setObjectName("MarcoOpcionesTriplo")  # Evita afectar los demás desplegables de TecNet Finder.
        ventana_opciones.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Permite pintar el fondo redondeado del menú.
        ventana_opciones.setStyleSheet(f"QFrame#MarcoOpcionesTriplo {{ background-color: {p['panel']}; border: 1px solid {p['borde_fuerte']}; border-radius: 10px; }}")  # Replica el marco flotante del filtro de Registros.
        self.selector_instruccion.update()  # Redibuja la flecha si el usuario cambia de tema.
        self.campo_fuente.setStyleSheet(f"""
            QLineEdit#FuenteInstruccionTriplo {{ background-color: {p["superficie"]}; color: {p["texto"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 9px; padding: 6px 10px; }}
            QLineEdit#FuenteInstruccionTriplo:hover {{ border-color: {p["acento"]}; }}
            QLineEdit#FuenteInstruccionTriplo:focus {{ border-color: {p["acento"]}; }}
        """)  # Redondea el campo de código fuente manteniendo su selección de texto.
        self.marco_tabla.setStyleSheet(f"""
            QFrame#MarcoTablaTriplos {{ background-color: {p["editor"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 11px; }}
            QTableWidget#TablaTriplos {{ background-color: {p["editor"]}; alternate-background-color: {p["panel"]}; color: {p["texto"]}; border: none; border-radius: 10px; selection-background-color: {p["superficie_hover"]}; selection-color: {p["texto"]}; }}
            QTableWidget#TablaTriplos::item {{ padding: 4px 7px; }}
            QTableWidget#TablaTriplos::item:selected {{ background-color: {p["superficie_hover"]}; color: {p["texto"]}; }}
        """)  # Replica el marco de Mantenimiento y combina el borde con un recorte real de las esquinas interiores.
        for fila in self.filas_grupo:
            item = self.tabla.item(fila, 0)  # Recupera únicamente los encabezados de red que siguen visibles.
            if item is not None:
                item.setBackground(QBrush(QColor(p["superficie"])))  # Destaca cada grupo sin utilizar colores fijos.
                item.setForeground(QBrush(QColor(p["acento"])))  # Respeta el contraste del acento seleccionado.

    def _insertar_encabezado_grupo(self, grupo: dict) -> None:
        fila = self.tabla.rowCount()  # Inserta un separador antes del primer triplo de cada red.
        self.tabla.insertRow(fila)  # Crea una fila visual que no forma parte del código intermedio.
        self.tabla.setSpan(fila, 0, 1, 3)  # Ocupa las tres columnas sin añadir una cuarta columna al formato.
        titulo = self.formato_grupo.format(nombre=grupo["nombre"], ip=grupo["ip"], linea=grupo["linea"])  # Identifica red, IP base y línea original.
        item = QTableWidgetItem(titulo)  # Conserva el separador en formato seleccionable para copias tabuladas.
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Impide tratar el encabezado como una operación seleccionable.
        fuente = item.font()  # Reutiliza la tipografía del resto de la tabla.
        fuente.setBold(True)  # Distingue el separador sin aumentar demasiado su altura.
        item.setFont(fuente)  # Aplica énfasis a la información de origen de la red.
        item.setToolTip(grupo["fuente"] or titulo)  # Permite consultar la instrucción completa desde el propio encabezado.
        self.tabla.setItem(fila, 0, item)  # Inserta el título en la celda extendida a las demás columnas.
        self.filas_grupo.add(fila)  # Marca la fila para que no se cuente como un triplo.
        self.origenes.append(None)  # Mantiene alineadas las procedencias con todas las filas visuales.
        self.operadores.append("")  # Evita crear ayudas de operador sobre una cabecera de grupo.

    def _ajustar_altura_filas(self, _indice=0, _anterior=0, _nuevo=0) -> None:
        if self.tabla.rowCount():
            self.tabla.resizeRowsToContents()  # Actualiza alturas después de cualquier cambio de ancho.

    def _ajustar_columnas(self) -> None:
        ancho = max(1, self.tabla.viewport().width() - 2)  # Recupera el espacio visible sin desplazar horizontalmente la página.
        minimos = [70, 245, 430]  # Reserva espacio legible para índice, operación y procedimiento.
        if ancho <= sum(minimos):
            anchos = minimos  # Conserva los mínimos y habilita scroll si la ventana es estrecha.
        else:
            resto = ancho - sum(minimos)  # Calcula el espacio adicional disponible.
            anchos = [minimos[0], minimos[1] + int(resto * 0.25), minimos[2] + resto - int(resto * 0.25)]  # Da prioridad visual a las comprobaciones.
        for columna, medida in enumerate(anchos):
            if self.tabla.columnWidth(columna) != medida:
                self.tabla.setColumnWidth(columna, medida)  # Cambia solo las columnas que realmente necesitan reajuste.
        self._ajustar_altura_filas()  # Evita que las líneas se recorten al cambiar el ancho disponible.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Permite primero que Qt redistribuya el espacio del contenedor.
        self._ajustar_columnas()  # Reajusta la tabla al nuevo ancho de la ventana.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Obtiene el área visible después de mostrar la pestaña.
        self._aplicar_estilos()  # Recarga la paleta vigente cuando el usuario regresa a esta pestaña.
        self._ajustar_columnas()  # Corrige la distribución tras la primera visualización.

    def establecer_textos(self, encabezado: str, copiar: str, vacio: str, sin_bloques: str, no_disponible: str, contador: str, origen: str, host: str, ayudas: dict[str, str] | None = None, todas: str | None = None, linea: str | None = None, fuente: str | None = None, contador_filtrado: str | None = None, grupo: str | None = None) -> None:
        self.tabla.setHorizontalHeaderLabels(["(n)", "(Op, Arg1, Arg2)", encabezado])  # Traduce solamente el encabezado de texto y conserva la notación de los triplos.
        self.boton_copiar.setToolTip(copiar)  # Traduce la ayuda del icono sin volver a mostrar texto en el botón.
        self.boton_copiar.setAccessibleName(copiar)  # Conserva la traducción también para lectores de pantalla.
        if ayudas is not None:
            self.ayudas_operadores = ayudas  # Reemplaza los textos de ayuda por los del idioma seleccionado.
        self.mensaje_vacio = vacio  # Conserva el texto de bienvenida del idioma activo.
        self.mensaje_sin_bloques = sin_bloques  # Conserva el mensaje para entradas sin redes válidas.
        self.mensaje_no_disponible = no_disponible  # Conserva el texto para ejecuciones ausentes.
        self.formato_contador = contador  # Conserva la plantilla localizada para la cantidad de operaciones.
        self.formato_origen = origen  # Traduce la línea y el bloque asociados con cada triplo.
        self.formato_host = host  # Traduce la posición original del host solicitado.
        self.texto_todas = todas if todas is not None else self.texto_todas  # Traduce la opción para ver la secuencia completa.
        self.formato_linea = linea if linea is not None else self.formato_linea  # Traduce los números de línea del selector.
        self.texto_fuente = fuente if fuente is not None else self.texto_fuente  # Traduce la indicación de la expresión original.
        self.formato_contador_filtrado = contador_filtrado if contador_filtrado is not None else self.formato_contador_filtrado  # Traduce el conteo parcial.
        self.formato_grupo = grupo if grupo is not None else self.formato_grupo  # Traduce los encabezados de redes en la vista general.
        self.campo_fuente.setPlaceholderText(self.texto_fuente)  # Conserva la ayuda en el idioma actualmente seleccionado.
        seleccion = self.selector_instruccion.currentData()  # Identifica el filtro que estaba seleccionado antes del cambio de idioma.
        self._actualizar_selector(seleccion)  # Traduce las opciones sin perder los resultados ni el filtro.
        self._filtrar_instruccion()  # Reconstruye encabezados traducidos y conserva el filtro sin volver a compilar.
        if self.tabla.rowCount():
            self.etiqueta_estado.hide()  # Mantiene oculta la ayuda cuando ya se muestran triplos.
        else:
            motivo = self.etiqueta_estado.property("motivo_vacio") or "inicial"  # Recupera por qué la tabla está vacía.
            self._mostrar_estado_vacio(motivo)  # Traduce el mensaje correspondiente sin modificar los datos.

    def _mostrar_estado_vacio(self, motivo: str) -> None:
        mensajes = {"inicial": self.mensaje_vacio, "sin_bloques": self.mensaje_sin_bloques, "no_disponible": self.mensaje_no_disponible}  # Relaciona cada estado con su descripción vigente.
        self.etiqueta_estado.setProperty("motivo_vacio", motivo)  # Conserva el motivo para cambios de idioma posteriores.
        self.etiqueta_estado.setText(mensajes.get(motivo, self.mensaje_vacio))  # Presenta la descripción correcta.
        self.etiqueta_estado.show()  # Hace visible la explicación debajo de la tabla.

    def _actualizar_tooltips(self) -> None:
        for fila, origen in enumerate(self.origenes):  # Recorre las operaciones visibles y su procedencia real.
            texto = ""  # Inicializa la ayuda incluso si una operación no tiene información de procedencia.
            if origen is not None:
                texto = self.formato_origen.format(linea=origen.linea_origen, bloque=origen.indice_bloque + 1)  # Señala la línea del DSL y el bloque aceptado.
                if origen.indice_host is not None:
                    texto += " · " + self.formato_host.format(posicion=origen.indice_host + 1)  # Conserva la posición original tras el ordenamiento.
            operador = self.operadores[fila] if fila < len(self.operadores) else ""  # Recupera la acción original del triplo.
            explicacion = self.ayudas_operadores.get(operador, "")  # Consulta la explicación localizada sin alterar el resultado.
            if explicacion:
                texto += ("\n" if texto else "") + explicacion  # Combina origen y propósito en una ayuda breve.
            if fila in self.filas_grupo:
                continue  # Mantiene intacta la ayuda del encabezado y evita confundirlo con un triplo.
            for columna in range(3):
                celda = self.tabla.item(fila, columna)  # Recupera cada columna de la misma operación.
                if celda is not None:
                    celda.setToolTip(texto)  # Aplica la ayuda localizada sin modificar el contenido del triplo.

    def _texto_de_grupo(self, grupo: dict) -> str:
        etiqueta = self.formato_linea.format(linea=grupo["linea"])  # Identifica la línea real del código fuente.
        if grupo["nombre"]:
            return f'{etiqueta} · {grupo["nombre"]}'  # Incluye NAME o IP para distinguir redes sin mostrar toda la expresión.
        return etiqueta  # No inventa un nombre cuando falta información del código original.

    def _crear_grupos(self) -> None:
        self.grupos = []  # Inicia una agrupación nueva para la compilación vigente.
        identificadores = set()  # Evita repetir una línea de origen por cada operación generada.
        for triplo in self.triplos_completos:
            origen = triplo.origen  # Recupera el bloque y la línea de la operación sin analizar de nuevo el DSL.
            if origen is None:
                continue  # Mantiene los triplos sin origen en la vista general.
            clave = f"{origen.indice_bloque}:{origen.linea_origen}"  # Identifica cada bloque de manera estable dentro del selector de Qt.
            if clave in identificadores:
                continue  # Cada instrucción debe aparecer una sola vez en el selector.
            identificadores.add(clave)  # Registra la instrucción antes de procesar sus otros triplos.
            indice_linea = origen.linea_origen - 1  # Convierte la ubicación de origen a un índice de lista.
            fuente = self.lineas_fuente[indice_linea].strip() if 0 <= indice_linea < len(self.lineas_fuente) else ""  # Recupera exactamente la instrucción que produjo los triplos.
            nombre = re.search(r"\bNAME\s+([A-Za-z][A-Za-z0-9_]*)\b", fuente)  # Identifica el nombre opcional sin modificar los tokens.
            direccion = re.search(r"\bIP\s+(\d{1,3}(?:\.\d{1,3}){3})\b", fuente)  # Utiliza la IP si no se declaró NAME.
            identificador = nombre.group(1) if nombre else (direccion.group(1) if direccion else "")  # Evita confundir instrucciones de redes diferentes.
            ip = direccion.group(1) if direccion else str(triplo.argumento1) if triplo.operador == "INICIAR_RED" else ""  # Recupera la IP base aun si el texto fuente no está disponible.
            self.grupos.append({"clave": clave, "linea": origen.linea_origen, "fuente": fuente, "nombre": identificador or ip, "ip": ip})  # Asocia red, IP y línea al separador visual.

    def _actualizar_selector(self, seleccion=None) -> None:
        bloqueado = self.selector_instruccion.blockSignals(True)  # Impide aplicar filtros incompletos mientras se reconstruyen las opciones.
        try:
            self.selector_instruccion.clear()  # Elimina opciones de compilaciones o idiomas anteriores.
            self.selector_instruccion.addItem(self.texto_todas, None)  # Conserva la vista general como primera opción.
            indice_seleccionado = 0  # Restablece la vista completa si el filtro previo ya no existe.
            for posicion, grupo in enumerate(self.grupos, start=1):
                self.selector_instruccion.addItem(self._texto_de_grupo(grupo), grupo["clave"])  # Agrega una opción por instrucción válida.
                self.selector_instruccion.setItemData(posicion, grupo["fuente"], Qt.ItemDataRole.ToolTipRole)  # Permite leer la expresión íntegra al señalarla.
                if grupo["clave"] == seleccion:
                    indice_seleccionado = posicion  # Conserva la selección cuando solo cambia el idioma.
            self.selector_instruccion.setCurrentIndex(indice_seleccionado)  # Recupera la instrucción filtrada o la vista general.
            self.selector_instruccion.setEnabled(bool(self.grupos))  # Desactiva el filtro cuando no existe código intermedio.
        finally:
            self.selector_instruccion.blockSignals(bloqueado)  # Recupera el estado original de las señales de Qt.
        self._actualizar_fuente()  # Sincroniza el código original con la selección vigente.

    def _actualizar_fuente(self) -> None:
        clave = self.selector_instruccion.currentData()  # Identifica la instrucción elegida para mostrar su texto original.
        if clave is None and self.tabla.currentRow() >= 0 and self.tabla.currentRow() < len(self.origenes):
            origen = self.origenes[self.tabla.currentRow()]  # Recupera la línea del triplo seleccionado dentro de la vista general.
            if origen is not None:
                clave = f"{origen.indice_bloque}:{origen.linea_origen}"  # Muestra también la expresión al seleccionar una fila de la tabla.
        if clave is None and len(self.grupos) == 1:
            clave = self.grupos[0]["clave"]  # Muestra directamente el código cuando solo existe una instrucción.
        grupo = next((grupo for grupo in self.grupos if grupo["clave"] == clave), None)  # Busca la línea original sin alterar los triplos.
        fuente = grupo["fuente"] if grupo is not None else ""  # Evita mostrar una expresión que no corresponde al filtro.
        self.campo_fuente.setText(fuente)  # Presenta el código fuente en un campo que también permite seleccionarlo.
        self.campo_fuente.setToolTip(fuente or self.texto_fuente)  # Facilita consultar instrucciones largas sin recortarlas.
        self.campo_fuente.setCursorPosition(0)  # Muestra el inicio de la instrucción incluso si excede el ancho visible.

    def mostrar_resultado(self, resultado: ResultadoCompilacion, texto_fuente: str = "") -> None:
        codigo = resultado.codigo_intermedio  # Recupera la secuencia intermedia de la compilación actual.
        ejecucion = resultado.ejecucion_intermedia  # Recupera los valores y las comprobaciones del intérprete.
        self.triplos_completos = list(codigo.triplos) if codigo is not None and ejecucion is not None else []  # Conserva únicamente operaciones con resultados disponibles.
        self.comprobaciones = dict(ejecucion.comprobaciones) if ejecucion is not None else {}  # Mantiene las comprobaciones asociadas a los índices originales.
        self.lineas_fuente = texto_fuente.splitlines()  # Permite recuperar la expresión escrita usando el número de línea original.
        self._crear_grupos()  # Separa las instrucciones sin cambiar la numeración de triplos.
        self._actualizar_selector()  # Restablece la vista general para cada nueva compilación.
        self._filtrar_instruccion()  # Construye la tabla a partir de los resultados y el filtro actual.
        if codigo is None or ejecucion is None:
            self._mostrar_estado_vacio("no_disponible")  # Distingue una fase ausente de un resultado válido vacío.
        elif not self.triplos_completos:
            self._mostrar_estado_vacio("sin_bloques")  # Informa que no existen redes válidas para generar operaciones.

    def _filtrar_instruccion(self, _indice=0) -> None:
        clave = self.selector_instruccion.currentData()  # Obtiene la línea elegida o None cuando deben verse todas.
        self.tabla.clearSpans()  # Elimina extensiones anteriores antes de reconstruir la tabla filtrada.
        self.tabla.setRowCount(0)  # Descarta solamente la representación anterior, no los triplos almacenados.
        self.origenes = []  # Sincroniza los metadatos con las filas que siguen visibles.
        self.operadores = []  # Conserva las ayudas únicamente para los operadores mostrados.
        self.filas_grupo = set()  # Descarta los separadores de la vista anterior.
        self.cantidad_visible = 0  # Evita contar las filas de título como triplos.
        grupos = {grupo["clave"]: grupo for grupo in self.grupos}  # Relaciona los orígenes con sus encabezados identificables.
        grupo_anterior = None  # Controla el inicio de cada instrucción en la vista completa.
        for triplo in self.triplos_completos:
            origen = triplo.origen  # Consulta la relación de cada operación con su instrucción original.
            if clave is not None and (origen is None or f"{origen.indice_bloque}:{origen.linea_origen}" != clave):
                continue  # Oculta triplos de otros bloques sin renumerar las referencias existentes.
            clave_triplo = f"{origen.indice_bloque}:{origen.linea_origen}" if origen is not None else None  # Reconoce el bloque real de esta operación.
            if clave is None and clave_triplo in grupos and clave_triplo != grupo_anterior:
                self._insertar_encabezado_grupo(grupos[clave_triplo])  # Etiqueta cada red solo en la vista de todas las instrucciones.
            grupo_anterior = clave_triplo  # Permite añadir separadores únicamente cuando cambia el origen.
            argumento2 = triplo.argumento2 if triplo.argumento2 is not None else "—"  # Mantiene el símbolo para operaciones unarias.
            expresion = f"({triplo.operador}, {triplo.argumento1}, {argumento2})"  # Presenta los operandos conservando sus referencias.
            comprobacion = self.comprobaciones.get(triplo.indice, "")  # Busca el desarrollo por índice y no por número de fila.
            fila = self.tabla.rowCount()  # Obtiene la posición visual disponible para insertar el siguiente triplo.
            self.tabla.insertRow(fila)  # Añade una fila exclusivamente para la operación seleccionada.
            self.cantidad_visible += 1  # Cuenta únicamente los triplos verdaderos, sin los encabezados de red.
            self.origenes.append(origen)  # Conserva el origen que se mostrará al pasar el cursor.
            self.operadores.append(triplo.operador)  # Guarda el operador para su explicación contextual.
            for columna, contenido in enumerate((f"({triplo.indice})", expresion, comprobacion)):
                celda = QTableWidgetItem(contenido)  # Mantiene el texto editable para copiarlo, pero no para modificarlo.
                if columna == 0:
                    celda.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra la referencia sin modificar el resto de columnas.
                self.tabla.setItem(fila, columna, celda)  # Inserta el dato con su índice original en la vista filtrada.
        self._actualizar_tooltips()  # Actualiza la línea y las ayudas de cada operación visible.
        self._aplicar_estilos()  # Colorea los nuevos separadores y los controles de acuerdo con el tema actual.
        self._actualizar_controles(self.cantidad_visible)  # Excluye los encabezados del total de operaciones.
        if self.tabla.rowCount():
            self.etiqueta_estado.hide()  # Oculta los avisos de ausencia cuando existen operaciones visibles.
        self._actualizar_fuente()  # Presenta la expresión asociada con el filtro o la fila actual.
        self._ajustar_columnas()  # Mantiene las columnas adaptadas a su contenido al cambiar de red.

    def _actualizar_controles(self, cantidad: int) -> None:
        total = len(self.triplos_completos)  # Identifica la cantidad completa sin depender de la vista actual.
        if self.selector_instruccion.currentData() is None:
            texto = self.formato_contador.format(cantidad=total)  # Muestra el total cuando se consultan todas las instrucciones.
        else:
            texto = self.formato_contador_filtrado.format(visibles=cantidad, total=total)  # Distingue operaciones visibles del total compilado.
        self.contador.setText(texto)  # Sincroniza el contador con el filtro sin volver a analizar el código.
        self.boton_copiar.setEnabled(cantidad > 0)  # Solo permite copiar cuando la tabla contiene operaciones visibles.

    def copiar_tabla(self) -> None:
        if not self.cantidad_visible:
            return  # No modifica el portapapeles cuando no hay operaciones reales.
        cabeceras = [self.tabla.horizontalHeaderItem(columna).text() for columna in range(3)]  # Conserva los encabezados visibles del idioma actual.
        lineas = ["\t".join(cabeceras)]  # Comienza con una fila de títulos apta para documentos y hojas de cálculo.
        for fila in range(self.tabla.rowCount()):
            if fila in self.filas_grupo:
                lineas.append(self.tabla.item(fila, 0).text())  # Conserva la separación entre redes al copiar la vista completa.
                continue  # Impide tratar una cabecera como un triplo.
            lineas.append("\t".join(self.tabla.item(fila, columna).text() for columna in range(3)))  # Copia la operación y la comprobación originales.
        QApplication.clipboard().setText("\n".join(lineas))  # Entrega un resultado completo y editable al portapapeles.

    def limpiar(self) -> None:
        self.tabla.clearSpans()  # Quita también los encabezados extendidos de la compilación anterior.
        self.tabla.setRowCount(0)  # Descarta la presentación anterior al modificar el código fuente.
        self.triplos_completos = []  # Invalida también los datos que se utilizarían para volver a filtrar.
        self.comprobaciones = {}  # Evita conservar resultados de una compilación anterior.
        self.grupos = []  # Descarta los bloques y líneas que dejaron de corresponder al editor.
        self.lineas_fuente = []  # Elimina las expresiones originales obsoletas.
        self.origenes = []  # Descarta las procedencias de las filas visibles.
        self.operadores = []  # Elimina las ayudas de operaciones anteriores.
        self.filas_grupo = set()  # Elimina los encabezados de red que ya no corresponden al código fuente.
        self.cantidad_visible = 0  # Restablece el contador real sin incluir filas decorativas.
        self._actualizar_selector()  # Deshabilita el filtro y elimina las instrucciones anteriores.
        self._actualizar_controles(0)  # Restablece el contador y deshabilita la copia.
        self._mostrar_estado_vacio("inicial")  # Vuelve al mensaje neutral antes de una nueva compilación.
