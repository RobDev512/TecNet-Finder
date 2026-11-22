# ============================================================
# Archivo: visor_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Presenta el código intermedio en tres columnas, conserva
# las referencias originales y muestra las comprobaciones
# de cada triplo con símbolos matemáticos legibles.
# ============================================================

import re  # Permite reconocer logaritmos, redondeos y potencias dentro de las comprobaciones.
from html import escape  # Protege el texto de cada operación antes de presentarlo con formato enriquecido.

from PySide6.QtCore import QRectF, QSize, Qt  # Proporciona dimensiones, posiciones y opciones de alineación.
from PySide6.QtGui import QPalette, QTextDocument  # Permite dibujar expresiones con subíndices y exponentes reales.
from PySide6.QtWidgets import QApplication, QAbstractItemView, QHeaderView, QHBoxLayout, QLabel, QPushButton, QStyledItemDelegate, QStyle, QStyleOptionViewItem, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget  # Construye el visor integrado con el estilo visual de Qt.

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


class VisorTriplos(QWidget):  # Reúne el encabezado, la tabla del código intermedio y la acción de copiado.
    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el contenedor independiente de la pestaña principal.
        diseno = QVBoxLayout(self)  # Organiza el encabezado y la tabla verticalmente.
        diseno.setContentsMargins(4, 4, 4, 4)  # Respeta los márgenes compactos de las demás fases.
        diseno.setSpacing(8)  # Mantiene una separación uniforme entre los controles.
        fila_superior = QHBoxLayout()  # Coloca el contador y el botón sin ocupar espacio de la tabla.
        self.contador = QLabel("Triplos: 0")  # Identifica la cantidad actual de operaciones generadas.
        self.boton_copiar = QPushButton()  # Emplea el mismo botón cuadrado de copiado que el resto de la interfaz.
        self.boton_copiar.setObjectName("BotonFlotantePanel")  # Reutiliza la apariencia de los controles con iconos del proyecto.
        self.boton_copiar.setFixedSize(32, 32)  # Evita que el texto de la acción cambie el ancho del encabezado.
        self.boton_copiar.setCursor(Qt.CursorShape.PointingHandCursor)  # Identifica visualmente la acción disponible.
        self.boton_copiar.setToolTip("Copiar tabla")  # Explica la acción sin mostrar una etiqueta extensa.
        self.boton_copiar.setAccessibleName("Copiar tabla")  # Conserva el nombre para lectores de pantalla.
        self.boton_copiar.setEnabled(False)  # No permite copiar información inexistente.
        self.boton_copiar.clicked.connect(self.copiar_tabla)  # Copia una representación tabulada al portapapeles.
        fila_superior.addWidget(self.contador)  # Coloca el contador a la izquierda.
        fila_superior.addStretch(1)  # Separa visualmente el contador de las acciones.
        fila_superior.addWidget(self.boton_copiar)  # Coloca el botón a la derecha.
        diseno.addLayout(fila_superior)  # Agrega el encabezado a la sección.

        self.tabla = QTableWidget(0, 3)  # Crea una fila por triplo y tres columnas según el formato acordado.
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
        diseno.addWidget(self.tabla, 1)  # Utiliza el resto del espacio disponible para el código intermedio.

        self.origenes = []  # Conserva la procedencia de las operaciones para actualizar sus ayudas al cambiar de idioma.
        self.operadores = []  # Conserva los operadores para mostrar explicaciones breves al pasar el cursor.
        self.ayudas_operadores = {
            "INICIAR_RED": "Establece la red base y la primera dirección disponible.",
            "SOLICITUD": "Relaciona los hosts solicitados con el tamaño de bloque calculado.",
            "ASIGNAR_VLSM": "Reserva la subred desde el cursor actual y calcula su broadcast.",
            "SIGUIENTE_CURSOR": "Avanza a la dirección posterior al broadcast para la siguiente subred.",
        }  # Explica las operaciones de red sin alterar las comprobaciones del intérprete.
        self.formato_origen = "Línea {linea} · Bloque {bloque}"  # Describe dónde se generó cada operación.
        self.formato_host = "HOSTS posición {posicion}"  # Identifica la solicitud original incluso si fue reordenada.
        self.mensaje_vacio = "Compila una instrucción válida para visualizar los triplos."  # Conserva el texto inicial configurable por idioma.
        self.mensaje_sin_bloques = "No hay bloques válidos para generar triplos."  # Explica los resultados vacíos sin inventar operaciones.
        self.mensaje_no_disponible = "El código intermedio no está disponible."  # Distingue una ejecución no disponible de una secuencia vacía.
        self.etiqueta_estado = QLabel(self.mensaje_vacio)  # Muestra instrucciones o el motivo de ausencia de resultados.
        self.etiqueta_estado.setWordWrap(True)  # Permite leer el mensaje en ventanas estrechas.
        diseno.addWidget(self.etiqueta_estado)  # Conserva la explicación debajo de la tabla.
        self._ajustar_columnas()  # Establece anchos mínimos antes de mostrar resultados.

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
        self._ajustar_columnas()  # Corrige la distribución tras la primera visualización.

    def establecer_textos(self, encabezado: str, copiar: str, vacio: str, sin_bloques: str, no_disponible: str, contador: str, origen: str, host: str, ayudas: dict[str, str] | None = None) -> None:
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
        self._actualizar_tooltips()  # Actualiza las ayudas de filas existentes sin volver a ejecutar el compilador.
        self.contador.setText(self.formato_contador.format(cantidad=self.tabla.rowCount()))  # Actualiza el contador sin perder los resultados.
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
            for columna in range(3):
                celda = self.tabla.item(fila, columna)  # Recupera cada columna de la misma operación.
                if celda is not None:
                    celda.setToolTip(texto)  # Aplica la ayuda localizada sin modificar el contenido del triplo.

    def mostrar_resultado(self, resultado: ResultadoCompilacion) -> None:
        self.tabla.setRowCount(0)  # Descarta las operaciones de la compilación anterior.
        self.origenes = []  # Evita mezclar procedencias de compilaciones anteriores.
        self.operadores = []  # Evita mezclar ayudas de operaciones de compilaciones distintas.
        codigo = resultado.codigo_intermedio  # Recupera la secuencia generada por el compilador.
        ejecucion = resultado.ejecucion_intermedia  # Recupera las comprobaciones obtenidas al interpretar la secuencia.
        if codigo is None or ejecucion is None:
            self._actualizar_controles(0)  # Deshabilita copiar resultados que no están disponibles.
            self._mostrar_estado_vacio("no_disponible")  # Informa que la fase no produjo resultados.
            return
        for fila, triplo in enumerate(codigo.triplos):
            argumento2 = triplo.argumento2 if triplo.argumento2 is not None else "—"  # Conserva el símbolo utilizado por el modelo para los operadores unarios.
            expresion = f"({triplo.operador}, {triplo.argumento1}, {argumento2})"  # Construye la operación sin duplicar su índice.
            comprobacion = ejecucion.comprobaciones.get(triplo.indice, "")  # Relaciona la explicación con el índice original y no con su fila.
            self.tabla.insertRow(fila)  # Reserva una fila para la operación actual.
            self.origenes.append(triplo.origen)  # Conserva los metadatos para traducir sus ayudas posteriormente.
            self.operadores.append(triplo.operador)  # Conserva la operación necesaria para mostrar su propósito.
            for columna, contenido in enumerate((f"({triplo.indice})", expresion, comprobacion)):
                celda = QTableWidgetItem(contenido)  # Guarda el texto original, independiente de su representación HTML.
                if columna == 0:
                    celda.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra únicamente la referencia numérica.
                self.tabla.setItem(fila, columna, celda)  # Inserta el dato sin alterar la estructura del triplo.
        self._actualizar_tooltips()  # Aplica las ayudas de procedencia en el idioma seleccionado.
        self._actualizar_controles(len(codigo.triplos))  # Sincroniza contador, selección y botón de copia.
        if codigo.triplos:
            self.etiqueta_estado.hide()  # Dedica toda la superficie a los resultados disponibles.
        else:
            self._mostrar_estado_vacio("sin_bloques")  # Explica por qué no hay operaciones cuando fallaron los bloques.
        self._ajustar_columnas()  # Recalcula alturas para las comprobaciones generadas.

    def _actualizar_controles(self, cantidad: int) -> None:
        formato = getattr(self, "formato_contador", "Triplos: {cantidad}")  # Utiliza el idioma actual o el formato español inicial.
        self.contador.setText(formato.format(cantidad=cantidad))  # Muestra el número real de operaciones generadas.
        self.boton_copiar.setEnabled(cantidad > 0)  # Solo permite copiar cuando existen triplos.

    def copiar_tabla(self) -> None:
        if not self.tabla.rowCount():
            return  # No modifica el portapapeles cuando la tabla está vacía.
        cabeceras = [self.tabla.horizontalHeaderItem(columna).text() for columna in range(3)]  # Conserva los encabezados visibles del idioma actual.
        lineas = ["\t".join(cabeceras)]  # Comienza con una fila de títulos apta para documentos y hojas de cálculo.
        for fila in range(self.tabla.rowCount()):
            lineas.append("\t".join(self.tabla.item(fila, columna).text() for columna in range(3)))  # Copia la operación y la comprobación originales.
        QApplication.clipboard().setText("\n".join(lineas))  # Entrega un resultado completo y editable al portapapeles.

    def limpiar(self) -> None:
        self.tabla.setRowCount(0)  # Descarta todos los triplos de la compilación anterior.
        self.origenes = []  # Descarta los metadatos que ya no corresponden al código editado.
        self.operadores = []  # Elimina las ayudas asociadas con operaciones anteriores.
        self._actualizar_controles(0)  # Restablece el contador y deshabilita la copia.
        self._mostrar_estado_vacio("inicial")  # Vuelve al mensaje neutral antes de una nueva compilación.
