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
# resaltado de la línea actual, navegación hacia posiciones,
# acciones flotantes para pegar y abrir ejemplos, además de
# diagnósticos visuales mediante ondas y tooltips.
# ============================================================

from pathlib import Path  # Importa Path para localizar los recursos gráficos utilizados por el editor.
from textwrap import fill  # Importa una utilidad para dividir textos largos dentro de los tooltips.

from PySide6.QtCore import QEvent, QPointF, QRect, QSize, Qt, QTimer, Signal  # Importa eventos, geometría, temporización, señales y opciones generales.
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QTextCursor, QTextFormat  # Importa herramientas de dibujo, iconos y manipulación del texto.
from PySide6.QtWidgets import QDialog, QMessageBox, QPlainTextEdit, QPushButton, QTextEdit, QToolTip, QWidget  # Importa el editor base, diálogos, botones, selecciones adicionales y tooltips.

from Interfaz.selector_ejemplos import SelectorEjemplos  # Importa la ventana especializada utilizada para consultar casos válidos e inválidos.
from Motor.diagnosticos import Diagnostico  # Importa el modelo estructurado utilizado para representar errores y advertencias.
from Motor.gestor_ejemplos import GestorEjemplos  # Importa el componente encargado de leer e interpretar los archivos de ejemplos.


class AreaNumerosLinea(QWidget):  # Define el pequeño widget colocado a la izquierda del editor para dibujar números.
    def __init__(self, editor):  # Inicializa el área asociándola con el editor al que pertenece.
        super().__init__(editor)  # Establece el editor como widget padre.
        self.editor = editor  # Conserva una referencia para consultar líneas, tamaño y desplazamiento.

    def sizeHint(self) -> QSize:  # Informa a Qt cuánto espacio horizontal necesita el área de números.
        return QSize(self.editor.ancho_area_numeros_linea(), 0)  # Usa el ancho calculado dinámicamente según la cantidad de líneas.

    def paintEvent(self, evento) -> None:  # Se ejecuta cada vez que Qt necesita volver a dibujar el área.
        self.editor.pintar_numeros_linea(evento)  # Delega el dibujo real al editor principal.


class EditorCodigo(QPlainTextEdit):  # Define el editor especializado utilizado para escribir instrucciones TecNet Finder.
    ejemplos_insertados = Signal()  # Informa a la ventana principal que debe descartar resultados asociados con una entrada anterior.

    AMPLITUD_ONDA = 2.0  # Define qué tan altas serán las curvas de los diagnósticos.
    LONGITUD_ONDA = 5.0  # Define la distancia horizontal ocupada por cada ondulación completa.
    GROSOR_ONDA = 2.0  # Define el grosor visual utilizado para que las ondas resulten claramente visibles.
    DESPLAZAMIENTO_ONDA = 1.5  # Desplaza las ondas hacia abajo respecto a la posición normal del subrayado.

    def __init__(self, padre=None):  # Inicializa el editor y conecta todos sus comportamientos.
        super().__init__(padre)  # Inicializa el QPlainTextEdit original.
        self.diagnosticos: list[Diagnostico] = []  # Conserva los diagnósticos relacionados con la compilación actual.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.
        self.gestor_ejemplos = GestorEjemplos()  # Prepara el lector reutilizable de casos almacenados en Ejemplos.
        self.area_numeros_linea = AreaNumerosLinea(self)  # Crea el área lateral donde se dibujarán los números.
        self.boton_pegar = QPushButton(self)  # Crea el botón de pegado como hijo fijo del editor completo.
        self.boton_ejemplos = QPushButton(self)  # Crea el segundo botón flotante destinado al selector de ejemplos.

        self._configurar_botones_flotantes()  # Prepara ambos controles pequeños mediante los recursos existentes.

        self.blockCountChanged.connect(self.actualizar_ancho_area_numeros_linea)  # Recalcula el margen cuando cambia la cantidad de líneas.
        self.updateRequest.connect(self.actualizar_area_numeros_linea)  # Mantiene sincronizada el área lateral durante desplazamientos.
        self.cursorPositionChanged.connect(self.resaltar_linea_actual)  # Actualiza el fondo de la línea cuando se mueve el cursor.
        self.textChanged.connect(self.limpiar_diagnosticos)  # Elimina diagnósticos antiguos cuando el código se modifica.
        self.verticalScrollBar().rangeChanged.connect(self._posicionar_botones_flotantes)  # Reajusta ambos botones cuando aparece o desaparece la scrollbar.

        self.viewport().installEventFilter(self)  # Permite detectar tooltips y cambios geométricos dentro del área visible.
        self.viewport().setMouseTracking(True)  # Mantiene disponible la posición del mouse sobre el código.

        self.actualizar_ancho_area_numeros_linea()  # Reserva inicialmente el espacio necesario para los números.
        self.resaltar_linea_actual()  # Aplica el resaltado inicial de la línea activa.
        self.setPlaceholderText("IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina")  # Muestra una instrucción de referencia mientras el editor está vacío.

        QTimer.singleShot(0, self._posicionar_botones_flotantes)  # Coloca los controles cuando Qt ya conoce las dimensiones reales del editor.

    def _configurar_botones_flotantes(self) -> None:  # Configura las dos acciones pequeñas superpuestas al área de entrada.
        self._configurar_boton_flotante(self.boton_pegar, "Pegar.png", "Pegar comando desde el portapapeles")  # Prepara el primer control utilizando el icono de pegado.
        self._configurar_boton_flotante(self.boton_ejemplos, "Ejemplos.png", "Abrir selector de ejemplos")  # Prepara el segundo control utilizando el recurso de ejemplos.

        self.boton_pegar.clicked.connect(self._pegar_desde_portapapeles)  # Inserta contenido del sistema mediante el primer botón.
        self.boton_ejemplos.clicked.connect(self._abrir_selector_ejemplos)  # Abre la herramienta heredada mediante el segundo botón.

    def _configurar_boton_flotante(self, boton: QPushButton, nombre_icono: str, ayuda: str) -> None:  # Aplica una configuración uniforme a los controles flotantes.
        boton.setObjectName("BotonFlotanteEditor")  # Permite identificarlos como controles propios del editor.
        boton.setText("")  # Impide mostrar palabras dentro del botón cuadrado.
        boton.setFixedSize(32, 32)  # Mantiene exactamente las mismas dimensiones para ambas acciones.
        boton.setIconSize(QSize(18, 18))  # Reduce los PNG originales a una dimensión apropiada para la interfaz.
        boton.setToolTip(ayuda)  # Explica la acción únicamente cuando el usuario deja el cursor encima.
        boton.setAccessibleName(ayuda)  # Conserva una descripción textual aunque el control no muestre letras.
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Evita retirar permanentemente el foco del área de edición.
        boton.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el elemento puede pulsarse.
        boton.setStyleSheet("padding: 0px;")  # Evita que el padding general reduzca innecesariamente el icono.

        ruta_icono = self.ruta_iconos / nombre_icono  # Construye la ubicación exacta del PNG solicitado.

        if ruta_icono.exists():  # Comprueba que el recurso realmente se encuentre disponible.
            boton.setIcon(QIcon(str(ruta_icono)))  # Coloca la imagen correspondiente dentro del control.

        boton.show()  # Garantiza que el botón se encuentre visible sobre el editor.
        boton.raise_()  # Mantiene el control por encima de los componentes internos de QPlainTextEdit.

    def _posicionar_botones_flotantes(self, *_argumentos) -> None:  # Mantiene ambos controles fijos junto al extremo superior derecho del viewport.
        geometria_viewport = self.viewport().geometry()  # Obtiene la región de texto excluyendo automáticamente la scrollbar.
        margen = 6  # Mantiene una pequeña separación respecto a los bordes internos.
        separacion = 6  # Define el espacio vertical entre Pegar y Ejemplos.
        x = geometria_viewport.right() - self.boton_pegar.width() - margen + 1  # Calcula una única posición horizontal justo antes del límite del área visible.
        y_pegar = geometria_viewport.top() + margen  # Coloca Pegar como primera acción en la esquina superior.
        y_ejemplos = y_pegar + self.boton_pegar.height() + separacion  # Coloca Ejemplos inmediatamente debajo manteniendo el mismo eje vertical.

        self.boton_pegar.move(max(x, 0), max(y_pegar, 0))  # Aplica la posición fija correspondiente al primer control.
        self.boton_ejemplos.move(max(x, 0), max(y_ejemplos, 0))  # Aplica la posición fija correspondiente al segundo control.
        self.boton_pegar.raise_()  # Mantiene Pegar por encima del resto de los hijos del editor.
        self.boton_ejemplos.raise_()  # Mantiene también Ejemplos completamente visible.

    def _pegar_desde_portapapeles(self) -> None:  # Inserta el contenido del portapapeles utilizando el comportamiento convencional de Qt.
        if self.canPaste():  # Comprueba si existe contenido compatible con el editor.
            self.paste()  # Inserta el texto en la posición actual o sustituye cualquier selección existente.

        self.setFocus()  # Devuelve inmediatamente el foco al editor para continuar escribiendo.

    def _abrir_selector_ejemplos(self) -> None:  # Carga los archivos disponibles y abre el selector gráfico de casos.
        ejemplos_validos, ejemplos_invalidos = self.gestor_ejemplos.cargar_ejemplos()  # Recupera ambas categorías mediante el componente independiente de Motor.

        if not ejemplos_validos and not ejemplos_invalidos:  # Comprueba si ninguno de los archivos produjo casos utilizables.
            QMessageBox.warning(self, "Ejemplos", "No se encontraron ejemplos dentro de la carpeta Ejemplos.")  # Informa el problema sin modificar el editor.
            return  # Finaliza porque el selector no tendría contenido que mostrar.

        selector = SelectorEjemplos(ejemplos_validos, ejemplos_invalidos, self.window())  # Crea la ventana modal utilizando la aplicación principal como propietaria.

        if selector.exec() != QDialog.DialogCode.Accepted:  # Comprueba si el usuario cerró o canceló la ventana.
            self.setFocus()  # Devuelve el foco al editor después de abandonar el selector.
            return  # Evita realizar cualquier cambio sobre la entrada.

        texto_ejemplos = selector.obtener_texto_seleccionado()  # Recupera únicamente los comandos correspondientes a las casillas marcadas.

        if not texto_ejemplos:  # Mantiene una última protección frente a una selección vacía.
            self.setFocus()  # Conserva el comportamiento normal del editor.
            return  # Evita sustituir accidentalmente el código por una cadena vacía.

        modo = self._consultar_modo_insercion()  # Determina si debe reemplazarse la entrada actual o agregarse el contenido al final.

        if modo is None:  # Comprueba si el usuario canceló la decisión después de seleccionar los ejemplos.
            self.setFocus()  # Regresa al editor sin realizar ninguna modificación.
            return  # Conserva intacto todo el contenido anterior.

        if modo == "reemplazar":  # Comprueba si se eligió sustituir completamente la entrada.
            self.setPlainText(texto_ejemplos)  # Coloca únicamente los ejemplos seleccionados.
        else:  # Se ejecuta cuando debe conservarse también el código que ya estaba escrito.
            texto_actual = self.toPlainText().rstrip()  # Elimina únicamente saltos sobrantes del final del contenido existente.
            texto_completo = f"{texto_actual}\n{texto_ejemplos}" if texto_actual else texto_ejemplos  # Separa ambas partes mediante un único salto de línea.
            self.setPlainText(texto_completo)  # Actualiza el documento con el contenido combinado.

        cursor = self.textCursor()  # Obtiene el cursor después de actualizar el documento.
        cursor.movePosition(QTextCursor.MoveOperation.End)  # Lleva la posición de escritura al final de los ejemplos insertados.
        self.setTextCursor(cursor)  # Convierte la nueva posición en el cursor visible.
        self.ejemplos_insertados.emit()  # Solicita a la ventana limpiar cualquier resultado correspondiente a una entrada anterior.
        self.setFocus()  # Devuelve el foco para permitir editar o compilar inmediatamente.

    def _consultar_modo_insercion(self) -> str | None:  # Pregunta qué hacer solamente cuando el editor ya contiene código.
        if not self.toPlainText().strip():  # Comprueba si todavía no existe una entrada escrita.
            return "reemplazar"  # Inserta directamente porque no hay información que pueda perderse.

        mensaje = QMessageBox(self)  # Crea una pregunta personalizada con nombres más claros que Sí y No.
        mensaje.setWindowTitle("Insertar ejemplos")  # Identifica la operación que requiere confirmación.
        mensaje.setText("Ya hay texto en la entrada.\n\nElige si deseas reemplazarlo o agregar los ejemplos al final.")  # Explica las dos posibilidades disponibles.

        boton_reemplazar = mensaje.addButton("Reemplazar", QMessageBox.ButtonRole.AcceptRole)  # Crea la acción que descarta la entrada anterior.
        boton_agregar = mensaje.addButton("Agregar al final", QMessageBox.ButtonRole.ActionRole)  # Crea la acción que conserva el código existente.
        boton_cancelar = mensaje.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)  # Permite abandonar la operación sin realizar cambios.

        mensaje.exec()  # Muestra la pregunta y espera una respuesta explícita.
        boton_pulsado = mensaje.clickedButton()  # Obtiene exactamente la acción seleccionada por el usuario.

        if boton_pulsado is boton_reemplazar:  # Comprueba si debe sustituirse todo el contenido.
            return "reemplazar"  # Informa al método anterior que utilice únicamente los ejemplos.

        if boton_pulsado is boton_agregar:  # Comprueba si deben conservarse también las instrucciones actuales.
            return "agregar"  # Informa que los nuevos comandos deben colocarse al final.

        if boton_pulsado is boton_cancelar:  # Comprueba si se pulsó explícitamente la acción de cancelación.
            return None  # Indica que no debe realizarse ningún cambio.

        return None  # Trata cualquier cierre alternativo de la ventana como una cancelación segura.

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

    def resizeEvent(self, evento) -> None:  # Ajusta los elementos auxiliares cuando cambia el tamaño general del editor.
        super().resizeEvent(evento)  # Permite que QPlainTextEdit ejecute primero su comportamiento normal.
        rectangulo = self.contentsRect()  # Obtiene la región interior disponible del editor.
        ancho = self.ancho_area_numeros_linea()  # Calcula el ancho requerido actualmente por los números.
        self.area_numeros_linea.setGeometry(QRect(rectangulo.left(), rectangulo.top(), ancho, rectangulo.height()))  # Coloca el área lateral ocupando toda la altura.
        self._posicionar_botones_flotantes()  # Mantiene ambos controles en la esquina correcta cuando cambia el tamaño.

    def paintEvent(self, evento) -> None:  # Dibuja primero el editor normal y después agrega las ondas de diagnóstico.
        super().paintEvent(evento)  # Permite que Qt dibuje texto, selección, resaltado y demás contenido habitual.
        self._pintar_diagnosticos()  # Dibuja las ondas encima del editor después de que el texto ya está visible.

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
        selecciones = []  # Crea la colección de selecciones visuales utilizadas por el editor.

        if not self.isReadOnly():  # Comprueba que el editor continúe disponible para escribir.
            seleccion = QTextEdit.ExtraSelection()  # Crea una selección independiente de la selección normal del usuario.
            seleccion.format.setBackground(QColor("#181825"))  # Aplica un fondo ligeramente distinto a la línea activa.
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # Extiende el fondo a todo el ancho disponible.
            seleccion.cursor = self.textCursor()  # Utiliza la posición actual del cursor como referencia.
            seleccion.cursor.clearSelection()  # Evita seleccionar caracteres reales.
            selecciones.append(seleccion)  # Agrega la selección de línea a la lista visual.

        self.setExtraSelections(selecciones)  # Aplica únicamente el resaltado de la línea porque las ondas se dibujan manualmente.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:  # Recibe los diagnósticos producidos por la compilación actual.
        self.diagnosticos = list(diagnosticos)  # Conserva una copia independiente de los diagnósticos recibidos.
        self.viewport().update()  # Solicita inmediatamente el redibujado de las ondas sobre el código.

    def limpiar_diagnosticos(self) -> None:  # Elimina las marcas asociadas con una compilación anterior.
        if not self.diagnosticos:  # Comprueba si realmente existen diagnósticos almacenados.
            return  # Evita redibujar innecesariamente cuando no existe ningún diagnóstico.

        self.diagnosticos.clear()  # Elimina todos los diagnósticos asociados actualmente con el código.
        QToolTip.hideText()  # Oculta cualquier tooltip perteneciente a un diagnóstico anterior.
        self.viewport().update()  # Redibuja el editor para retirar todas las ondas antiguas.

    def _pintar_diagnosticos(self) -> None:  # Dibuja ondas personalizadas debajo de todos los fragmentos diagnosticados.
        if not self.diagnosticos:  # Comprueba si existe algún diagnóstico que deba representarse.
            return  # Finaliza inmediatamente cuando el código no presenta marcas visuales.

        pintor = QPainter(self.viewport())  # Crea un pintor directamente sobre el área donde se muestra el código.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza las curvas para evitar líneas dentadas.

        for diagnostico in self.diagnosticos:  # Recorre todos los diagnósticos correspondientes a la última compilación.
            rango = self._rango_diagnostico(diagnostico)  # Convierte la ubicación estructurada en posiciones absolutas del documento.

            if rango is None:  # Comprueba que exista un rango real que pueda mostrarse.
                continue  # Omite solamente los diagnósticos sin posición visual válida.

            inicio, final = rango  # Separa las posiciones absoluta inicial y final.
            cursor_inicio = QTextCursor(self.document())  # Crea un cursor temporal para localizar visualmente el inicio.
            cursor_inicio.setPosition(inicio)  # Coloca el cursor sobre el primer carácter diagnosticado.
            cursor_final = QTextCursor(self.document())  # Crea otro cursor temporal para localizar visualmente el final.
            cursor_final.setPosition(final)  # Coloca el cursor inmediatamente después del último carácter diagnosticado.

            rectangulo_inicio = self.cursorRect(cursor_inicio)  # Obtiene las coordenadas del primer carácter dentro del viewport.
            rectangulo_final = self.cursorRect(cursor_final)  # Obtiene las coordenadas correspondientes al extremo final.

            if rectangulo_inicio.bottom() < 0 or rectangulo_inicio.top() > self.viewport().height():  # Comprueba si el diagnóstico está fuera de la región visible.
                continue  # Evita realizar trabajo de dibujo sobre líneas que el usuario no puede ver.

            inicio_x = float(rectangulo_inicio.left())  # Obtiene la posición horizontal donde debe comenzar la onda.
            final_x = float(rectangulo_final.left())  # Obtiene la posición horizontal donde debe terminar la onda.

            if final_x <= inicio_x:  # Protege el dibujo frente a rangos extremadamente pequeños o posiciones especiales.
                final_x = inicio_x + max(float(self.fontMetrics().horizontalAdvance("M")), 6.0)  # Garantiza una onda mínima claramente visible.

            base_y = float(rectangulo_inicio.bottom()) + self.DESPLAZAMIENTO_ONDA  # Sitúa la onda un poco más abajo de las letras.
            color = self._color_diagnostico(diagnostico)  # Obtiene el color correspondiente al diagnóstico actual.

            lapiz = QPen(color)  # Crea el lápiz utilizado para dibujar la onda actual.
            lapiz.setWidthF(self.GROSOR_ONDA)  # Aumenta el grosor respecto al subrayado estándar de Qt.
            lapiz.setCapStyle(Qt.PenCapStyle.RoundCap)  # Redondea los extremos para conseguir un aspecto más limpio.
            lapiz.setJoinStyle(Qt.PenJoinStyle.RoundJoin)  # Suaviza las uniones entre las curvas consecutivas.
            pintor.setPen(lapiz)  # Activa el lápiz configurado.

            camino = self._crear_camino_ondulado(inicio_x, final_x, base_y)  # Construye la geometría de la onda.
            pintor.drawPath(camino)  # Dibuja finalmente el diagnóstico debajo del fragmento correspondiente.

    def _crear_camino_ondulado(self, inicio_x: float, final_x: float, base_y: float) -> QPainterPath:  # Construye una serie continua de curvas suaves entre dos posiciones horizontales.
        camino = QPainterPath(QPointF(inicio_x, base_y))  # Inicia el camino exactamente debajo del comienzo del diagnóstico.
        x = inicio_x  # Guarda la posición horizontal desde donde se construirá cada ondulación.
        media_onda = self.LONGITUD_ONDA / 2.0  # Divide la longitud completa para construir primero una curva hacia abajo y luego hacia arriba.

        while x < final_x:  # Continúa agregando curvas hasta alcanzar el final del fragmento.
            siguiente = min(x + media_onda, final_x)  # Calcula dónde terminará la primera mitad sin sobrepasar el diagnóstico.
            control_x = x + (siguiente - x) / 2.0  # Calcula el centro horizontal utilizado por la curva.
            camino.quadTo(QPointF(control_x, base_y + self.AMPLITUD_ONDA), QPointF(siguiente, base_y))  # Genera la mitad inferior de la onda.
            x = siguiente  # Continúa desde el extremo alcanzado.

            if x >= final_x:  # Comprueba si ya se llegó exactamente al final del fragmento.
                break  # Evita crear una segunda mitad fuera del rango disponible.

            siguiente = min(x + media_onda, final_x)  # Calcula el final de la segunda mitad.
            control_x = x + (siguiente - x) / 2.0  # Calcula nuevamente el centro horizontal.
            camino.quadTo(QPointF(control_x, base_y - self.AMPLITUD_ONDA), QPointF(siguiente, base_y))  # Genera la mitad superior completando la ondulación.
            x = siguiente  # Avanza hasta continuar con la próxima onda completa.

        return camino  # Devuelve el trazado completo listo para dibujarse.

    def _rango_diagnostico(self, diagnostico: Diagnostico) -> tuple[int, int] | None:  # Convierte la posición estructurada del diagnóstico en posiciones del documento.
        if diagnostico.linea is None:  # Comprueba que el problema tenga una línea asociada.
            return None  # No puede dibujarse un diagnóstico sin una ubicación concreta.

        bloque = self.document().findBlockByNumber(max(diagnostico.linea - 1, 0))  # Localiza la línea convirtiendo la numeración visible a índice interno.

        if not bloque.isValid():  # Comprueba que la línea todavía exista dentro del documento.
            return None  # Omite posiciones que dejaron de ser válidas.

        texto_linea = bloque.text()  # Obtiene únicamente el texto perteneciente a la línea encontrada.

        if not texto_linea:  # Comprueba si la línea está completamente vacía.
            return None  # No existe ningún carácter real sobre el cual dibujar la onda.

        columna = max(diagnostico.columna or 0, 0)  # Normaliza la columna evitando posiciones negativas.
        columna = min(columna, len(texto_linea))  # Impide que la posición sobrepase el final real de la línea.
        final_relativo = min(columna + max(diagnostico.longitud, 1), len(texto_linea))  # Calcula el final respetando la longitud del diagnóstico.

        if final_relativo <= columna:  # Detecta errores ubicados justo después del último carácter, como un token faltante.
            columna = max(len(texto_linea) - 1, 0)  # Utiliza el último carácter visible como referencia.
            final_relativo = len(texto_linea)  # Extiende el subrayado hasta el final real de la línea.

        inicio = bloque.position() + columna  # Convierte la columna relativa en posición absoluta dentro del documento.
        final = bloque.position() + final_relativo  # Convierte también el final relativo.

        return inicio, final  # Devuelve el rango utilizado por la onda y por el tooltip.

    def _color_diagnostico(self, diagnostico: Diagnostico) -> QColor:  # Devuelve el mismo esquema de colores utilizado por el panel de diagnósticos.
        severidad = diagnostico.severidad.lower()  # Normaliza la severidad para aceptar variantes futuras.

        if severidad in ("warning", "advertencia"):  # Comprueba primero si se trata de una advertencia.
            return QColor("#f9e2af")  # Utiliza amarillo para las advertencias.

        if diagnostico.categoria == "Léxico":  # Comprueba si el error pertenece al analizador léxico.
            return QColor("#f38ba8")  # Utiliza rojo para errores léxicos.

        if diagnostico.categoria == "Sintáctico":  # Comprueba si el error pertenece al analizador sintáctico.
            return QColor("#fab387")  # Utiliza naranja para errores sintácticos.

        if diagnostico.categoria == "Semántico":  # Reserva el color utilizado durante la Unidad 1 de LyAII.
            return QColor("#cba6f7")  # Utiliza violeta para futuros errores semánticos.

        return QColor("#f38ba8")  # Utiliza rojo como color de respaldo para otros errores.

    def _diagnosticos_en_posicion(self, posicion: int) -> list[Diagnostico]:  # Busca los diagnósticos cuyo rango contiene la posición indicada.
        encontrados = []  # Crea la colección de diagnósticos relacionados con el carácter señalado.

        for diagnostico in self.diagnosticos:  # Recorre todos los diagnósticos actualmente visibles.
            rango = self._rango_diagnostico(diagnostico)  # Obtiene el mismo rango utilizado para dibujar la onda.

            if rango is None:  # Comprueba que el diagnóstico posea una ubicación representable.
                continue  # Avanza al siguiente cuando no existe ningún rango visual.

            inicio, final = rango  # Separa ambos límites del diagnóstico.

            if inicio <= posicion < final:  # Comprueba si la posición pertenece al fragmento subrayado.
                encontrados.append(diagnostico)  # Conserva el diagnóstico para mostrarlo dentro del tooltip.

        return encontrados  # Devuelve todos los diagnósticos relacionados con la posición indicada.

    def _texto_tooltip(self, diagnosticos: list[Diagnostico]) -> str:  # Construye un tooltip legible incluso cuando coinciden varios diagnósticos.
        bloques = []  # Conserva cada diagnóstico como un bloque textual independiente.

        for diagnostico in diagnosticos:  # Recorre los diagnósticos relacionados con el mismo fragmento.
            mensaje = fill(diagnostico.mensaje, width=72)  # Divide mensajes largos para evitar tooltips excesivamente anchos.
            solucion = fill(diagnostico.solucion, width=72) if diagnostico.solucion else "Sin solución registrada."  # Divide también la recomendación.

            bloques.append(  # Agrega código, categoría, mensaje y solución como una unidad legible.
                f"{diagnostico.codigo} · {diagnostico.categoria}\n"
                f"{mensaje}\n\n"
                f"Solución:\n{solucion}"
            )

        return "\n\n────────────────────────\n\n".join(bloques)  # Separa claramente varios diagnósticos coincidentes.

    def eventFilter(self, objeto, evento):  # Intercepta eventos del área visible para mantener los controles fijos y mostrar información contextual.
        if objeto is self.viewport() and evento.type() == QEvent.Type.Resize:  # Detecta cambios de geometría causados por tamaño o scrollbars.
            QTimer.singleShot(0, self._posicionar_botones_flotantes)  # Recalcula ambas posiciones cuando Qt termina de reajustar sus componentes internos.

        if objeto is self.viewport() and evento.type() == QEvent.Type.ToolTip:  # Comprueba si Qt solicita un tooltip dentro del código fuente.
            cursor = self.cursorForPosition(evento.pos())  # Obtiene la posición textual situada debajo del puntero.
            diagnosticos = self._diagnosticos_en_posicion(cursor.position())  # Busca errores o advertencias relacionados con esa posición.

            if diagnosticos:  # Comprueba si existe al menos un diagnóstico debajo del mouse.
                QToolTip.showText(evento.globalPos(), self._texto_tooltip(diagnosticos), self.viewport())  # Muestra código, mensaje y solución.
            else:  # Se ejecuta cuando el puntero no se encuentra sobre ningún diagnóstico.
                QToolTip.hideText()  # Oculta cualquier información contextual anterior.

            return True  # Indica que el evento de tooltip ya fue procesado.

        return super().eventFilter(objeto, evento)  # Conserva el comportamiento normal para cualquier otro evento.

    def ir_a_posicion(self, linea: int | None, columna: int | None, longitud: int = 1) -> None:  # Coloca el cursor sobre la posición indicada por un diagnóstico.
        if linea is None:  # Comprueba si el diagnóstico carece de una línea concreta.
            return  # Finaliza porque no existe una posición a la cual desplazarse.

        bloque = self.document().findBlockByNumber(max(linea - 1, 0))  # Localiza el bloque correspondiente convirtiendo la línea visible a índice interno.

        if not bloque.isValid():  # Comprueba que la línea solicitada realmente exista dentro del documento.
            return  # Evita modificar el cursor cuando la ubicación no puede encontrarse.

        posicion = bloque.position() + max(columna or 0, 0)  # Calcula la posición absoluta sumando la columna al inicio del bloque.
        cursor = QTextCursor(self.document())  # Crea un cursor independiente asociado al documento actual.
        cursor.setPosition(min(posicion, self.document().characterCount() - 1))  # Coloca el cursor evitando sobrepasar el final del documento.

        if longitud > 0:  # Comprueba si debe seleccionarse temporalmente un fragmento concreto.
            final = min(posicion + longitud, self.document().characterCount() - 1)  # Calcula el final dentro de los límites del documento.
            cursor.setPosition(final, QTextCursor.MoveMode.KeepAnchor)  # Extiende la selección desde la posición inicial hasta el final.

        self.setTextCursor(cursor)  # Convierte el cursor calculado en el cursor visible del editor.
        self.centerCursor()  # Desplaza la vista para mantener visible la línea seleccionada.
        self.setFocus()  # Devuelve el foco al editor para corregir inmediatamente el texto.