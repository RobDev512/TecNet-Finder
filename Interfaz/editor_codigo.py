# ============================================================
# Archivo: editor_codigo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el editor especializado donde se escribe
# el código fuente de TecNet Finder.
#
# Extiende QPlainTextEdit para agregar números de línea,
# resaltado de la línea actual y navegación hacia posiciones
# específicas del documento.
#
# Posteriormente este mismo componente incorporará subrayados
# ondulados para errores y advertencias.
# ============================================================

from PySide6.QtCore import QRect, QSize, Qt  # Importa estructuras utilizadas para tamaño, geometría y alineación.
from PySide6.QtGui import QColor, QPainter, QTextCursor, QTextFormat  # Importa herramientas de dibujo y manipulación del cursor.
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget  # Importa el editor base y widgets necesarios para el área de números.


class AreaNumerosLinea(QWidget):  # Define el pequeño widget colocado a la izquierda del editor para dibujar números.
    def __init__(self, editor):  # Inicializa el área asociándola con el editor al que pertenece.
        super().__init__(editor)  # Establece el editor como widget padre.
        self.editor = editor  # Conserva una referencia para consultar líneas, tamaño y desplazamiento.

    def sizeHint(self) -> QSize:  # Informa a Qt cuánto espacio horizontal necesita el área de números.
        return QSize(self.editor.ancho_area_numeros_linea(), 0)  # Usa el ancho calculado dinámicamente según la cantidad de líneas.

    def paintEvent(self, evento) -> None:  # Se ejecuta cada vez que Qt necesita volver a dibujar el área.
        self.editor.pintar_numeros_linea(evento)  # Delega el dibujo real al editor principal.


class EditorCodigo(QPlainTextEdit):  # Define el editor especializado utilizado para escribir instrucciones TecNet Finder.
    def __init__(self, padre=None):  # Inicializa el editor y conecta los eventos necesarios para los números de línea.
        super().__init__(padre)  # Inicializa el QPlainTextEdit original.
        self.area_numeros_linea = AreaNumerosLinea(self)  # Crea el área lateral donde se dibujarán los números.
        self.blockCountChanged.connect(self.actualizar_ancho_area_numeros_linea)  # Recalcula el margen cuando cambia la cantidad de líneas.
        self.updateRequest.connect(self.actualizar_area_numeros_linea)  # Mantiene sincronizado el área lateral durante desplazamientos y cambios.
        self.cursorPositionChanged.connect(self.resaltar_linea_actual)  # Actualiza el fondo de la línea donde se encuentra el cursor.
        self.actualizar_ancho_area_numeros_linea()  # Reserva inicialmente el espacio necesario para los números.
        self.resaltar_linea_actual()  # Aplica el resaltado inicial de la línea activa.
        self.setPlaceholderText("Ejemplo:IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina")  # Muestra una instrucción de referencia mientras el editor está vacío.

    def ancho_area_numeros_linea(self) -> int:  # Calcula dinámicamente cuánto ancho requieren los números de línea.
        digitos = len(str(max(1, self.blockCount())))  # Obtiene cuántos dígitos necesita representar el número de línea más grande.
        return 12 + self.fontMetrics().horizontalAdvance("9") * digitos  # Combina el ancho de los dígitos con un pequeño margen adicional.

    def actualizar_ancho_area_numeros_linea(self, _cantidad=0) -> None:  # Actualiza el margen izquierdo reservado para el área de números.
        self.setViewportMargins(self.ancho_area_numeros_linea(), 0, 0, 0)  # Evita que el texto del editor se dibuje debajo de los números.

    def actualizar_area_numeros_linea(self, rectangulo, desplazamiento: int) -> None:  # Mantiene el área lateral sincronizada cuando cambia la vista.
        if desplazamiento:  # Comprueba si el editor se desplazó verticalmente.
            self.area_numeros_linea.scroll(0, desplazamiento)  # Desplaza los números la misma cantidad que el contenido.
        else:  # Se ejecuta cuando se modificó una región sin desplazamiento vertical.
            self.area_numeros_linea.update(0, rectangulo.y(), self.area_numeros_linea.width(), rectangulo.height())  # Redibuja solamente la zona afectada.

        if rectangulo.contains(self.viewport().rect()):  # Comprueba si el cambio afecta toda el área visible.
            self.actualizar_ancho_area_numeros_linea()  # Recalcula el ancho por si cambió la cantidad total de líneas.

    def resizeEvent(self, evento) -> None:  # Ajusta el área de números cuando cambia el tamaño general del editor.
        super().resizeEvent(evento)  # Permite que QPlainTextEdit ejecute primero su comportamiento normal.
        rectangulo = self.contentsRect()  # Obtiene la región interior disponible del editor.
        ancho = self.ancho_area_numeros_linea()  # Calcula el ancho requerido actualmente por los números.
        self.area_numeros_linea.setGeometry(QRect(rectangulo.left(), rectangulo.top(), ancho, rectangulo.height()))  # Coloca el área lateral ocupando toda la altura del editor.

    def pintar_numeros_linea(self, evento) -> None:  # Dibuja únicamente los números correspondientes a las líneas visibles.
        pintor = QPainter(self.area_numeros_linea)  # Crea el objeto encargado de dibujar dentro del área lateral.
        pintor.fillRect(evento.rect(), QColor("#181825"))  # Pinta el fondo del área con el tono oscuro de la interfaz.
        bloque = self.firstVisibleBlock()  # Obtiene el primer bloque de texto que actualmente puede verse.
        numero_bloque = bloque.blockNumber()  # Obtiene el índice interno de la primera línea visible.
        superior = int(self.blockBoundingGeometry(bloque).translated(self.contentOffset()).top())  # Calcula la posición vertical inicial del bloque.
        inferior = superior + int(self.blockBoundingRect(bloque).height())  # Calcula dónde termina verticalmente el mismo bloque.
        pintor.setPen(QColor("#6c7086"))  # Selecciona el color utilizado para dibujar los números de línea.

        while bloque.isValid() and superior <= evento.rect().bottom():  # Recorre solamente los bloques que pueden aparecer dentro de la zona visible.
            if bloque.isVisible() and inferior >= evento.rect().top():  # Comprueba que el bloque realmente intersecte el área que debe redibujarse.
                numero = str(numero_bloque + 1)  # Convierte el índice interno empezado en cero al número visible empezado en uno.
                pintor.drawText(0, superior, self.area_numeros_linea.width() - 6, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, numero)  # Dibuja el número alineado a la derecha.

            bloque = bloque.next()  # Avanza al siguiente bloque de texto del documento.
            superior = inferior  # Usa el final anterior como comienzo vertical del siguiente bloque.
            inferior = superior + int(self.blockBoundingRect(bloque).height())  # Calcula el final vertical del nuevo bloque.
            numero_bloque += 1  # Avanza también el número lógico de línea.

    def resaltar_linea_actual(self) -> None:  # Coloca un fondo discreto sobre la línea donde actualmente se encuentra el cursor.
        selecciones = []  # Crea la lista de selecciones adicionales que se aplicará al editor.

        if not self.isReadOnly():  # Evita aplicar el resaltado cuando el editor se encuentre configurado como solo lectura.
            seleccion = QTextEdit.ExtraSelection()  # Crea una selección visual independiente de la selección normal del usuario.
            seleccion.format.setBackground(QColor("#181825"))  # Aplica un fondo ligeramente distinto a la línea activa.
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # Extiende el fondo a todo el ancho disponible.
            seleccion.cursor = self.textCursor()  # Utiliza la posición actual del cursor como referencia.
            seleccion.cursor.clearSelection()  # Evita seleccionar caracteres reales del documento.
            selecciones.append(seleccion)  # Agrega la selección de línea a la lista que será mostrada.

        self.setExtraSelections(selecciones)  # Aplica las selecciones visuales adicionales al editor.

    def ir_a_posicion(self, linea: int | None, columna: int | None, longitud: int = 1) -> None:  # Coloca el cursor sobre la posición indicada por un diagnóstico.
        if linea is None:  # Comprueba si el diagnóstico carece de una línea concreta.
            return  # Finaliza porque no existe una posición a la cual desplazarse.

        bloque = self.document().findBlockByNumber(max(linea - 1, 0))  # Localiza el bloque correspondiente convirtiendo la línea visible a índice interno.

        if not bloque.isValid():  # Comprueba que la línea solicitada realmente exista dentro del documento.
            return  # Evita modificar el cursor cuando la ubicación no puede encontrarse.

        posicion = bloque.position() + max(columna or 0, 0)  # Calcula la posición absoluta sumando la columna al inicio del bloque.
        cursor = QTextCursor(self.document())  # Crea un cursor independiente asociado al documento actual.
        cursor.setPosition(min(posicion, self.document().characterCount() - 1))  # Coloca el cursor evitando sobrepasar el final del documento.

        if longitud > 0:  # Comprueba si debe resaltarse temporalmente un fragmento concreto.
            final = min(posicion + longitud, self.document().characterCount() - 1)  # Calcula el final de la selección dentro de los límites del documento.
            cursor.setPosition(final, QTextCursor.MoveMode.KeepAnchor)  # Extiende la selección desde la posición inicial hasta el final calculado.

        self.setTextCursor(cursor)  # Convierte el cursor calculado en el cursor visible del editor.
        self.centerCursor()  # Desplaza la vista para mantener visible la línea seleccionada.
        self.setFocus()  # Devuelve el foco al editor para que el usuario pueda corregir inmediatamente el texto.