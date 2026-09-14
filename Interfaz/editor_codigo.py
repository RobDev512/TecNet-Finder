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
# acciones flotantes, diagnósticos visuales y autocompletado
# opcional mediante el asistente local de inteligencia artificial.
# ============================================================

from pathlib import Path  # Importa Path para localizar los recursos gráficos utilizados por el editor.
from textwrap import fill  # Importa una utilidad para dividir textos largos dentro de los tooltips.

from PySide6.QtCore import QEvent, QPointF, QRect, QSize, Qt, QTimer, Signal  # Importa eventos, geometría, temporización, señales y opciones generales.
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap, QTextCursor, QTextFormat  # Importa herramientas de dibujo, iconos, paleta, imágenes y manipulación del texto.
from PySide6.QtWidgets import QDialog, QMessageBox, QPlainTextEdit, QPushButton, QTextEdit, QToolTip, QWidget  # Importa el editor base, diálogos, botones, selecciones adicionales y tooltips.

from AsistenteIA.control_autocompletado import ControlAutocompletado  # Importa el controlador que obtiene sugerencias sin bloquear la interfaz.
from Interfaz.selector_ejemplos import SelectorEjemplos  # Importa la ventana especializada utilizada para consultar casos válidos e inválidos.
from Motor.diagnosticos import Diagnostico  # Importa el modelo estructurado utilizado para representar errores y advertencias.
from Motor.gestor_ejemplos import GestorEjemplos  # Importa el componente encargado de leer e interpretar los archivos de ejemplos.


class AreaNumerosLinea(QWidget):  # Define el pequeño widget colocado a la izquierda del editor para dibujar números.
    def __init__(self, editor):
        super().__init__(editor)  # Establece el editor como widget padre.
        self.editor = editor  # Conserva una referencia para consultar líneas, tamaño y desplazamiento.

    def sizeHint(self) -> QSize:
        return QSize(self.editor.ancho_area_numeros_linea(), 0)  # Usa el ancho calculado dinámicamente según la cantidad de líneas.

    def paintEvent(self, evento) -> None:
        self.editor.pintar_numeros_linea(evento)  # Delega el dibujo real al editor principal.


class EditorCodigo(QPlainTextEdit):  # Define el editor especializado utilizado para escribir instrucciones TecNet Finder.
    ejemplos_insertados = Signal()  # Informa a la ventana principal que debe descartar resultados asociados con una entrada anterior.

    AMPLITUD_ONDA = 2.0  # Define qué tan altas serán las curvas de los diagnósticos.
    LONGITUD_ONDA = 5.0  # Define la distancia horizontal ocupada por cada ondulación completa.
    GROSOR_ONDA = 2.0  # Define el grosor visual utilizado para que las ondas resulten claramente visibles.
    DESPLAZAMIENTO_ONDA = 1.5  # Desplaza las ondas hacia abajo respecto a la posición normal del subrayado.
    COLOR_SUGERENCIA_IA = "#6c7086"  # Mantiene el ghost text discreto respecto al código escrito realmente.
    COLOR_PLACEHOLDER = "#6c7086"  # Mantiene el ejemplo inicial visible pero claramente secundario respecto al código real.
    TAMANO_ICONO_AUTOCOMPLETADO = 14  # Define un tamaño discreto para identificar visualmente una sugerencia producida por IA.
    SEPARACION_ICONO_AUTOCOMPLETADO = 5  # Separa el icono de IA del final del ghost text sin alterar la continuidad de la sugerencia.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el QPlainTextEdit original.
        self.diagnosticos: list[Diagnostico] = []  # Conserva los diagnósticos relacionados con la compilación actual.
        self.sugerencia_ia = ""  # Conserva únicamente la continuación gris que todavía no forma parte del documento.
        self.prefijo_sugerencia_ia = ""  # Identifica el texto exacto que produjo la sugerencia visible.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.
        ruta_icono_autocompletado = self.ruta_iconos / "Autocompletado.png"  # Localiza el recurso reservado para identificar visualmente el ghost text.
        self.icono_autocompletado_ia = QPixmap(str(ruta_icono_autocompletado)) if ruta_icono_autocompletado.exists() else QPixmap()  # Carga el icono solo cuando el recurso se encuentra disponible.
        self.gestor_ejemplos = GestorEjemplos()  # Prepara el lector reutilizable de casos almacenados en Ejemplos.
        self.control_autocompletado = ControlAutocompletado(self)  # Prepara el asistente asíncrono asociado exclusivamente con este editor.
        self.area_numeros_linea = AreaNumerosLinea(self)  # Crea el área lateral donde se dibujarán los números.
        self.boton_pegar = QPushButton(self)  # Crea el botón de pegado como hijo fijo del editor completo.
        self.boton_ejemplos = QPushButton(self)  # Crea el segundo botón flotante destinado al selector de ejemplos.

        self._configurar_botones_flotantes()  # Prepara ambos controles pequeños mediante los recursos existentes.

        self.blockCountChanged.connect(self.actualizar_ancho_area_numeros_linea)  # Recalcula el margen cuando cambia la cantidad de líneas.
        self.updateRequest.connect(self.actualizar_area_numeros_linea)  # Mantiene sincronizada el área lateral durante desplazamientos.
        self.cursorPositionChanged.connect(self.resaltar_linea_actual)  # Actualiza el fondo de la línea cuando se mueve el cursor.
        self.cursorPositionChanged.connect(self._actualizar_autocompletado)  # Invalida sugerencias cuando el cursor deja la posición que las originó.
        self.textChanged.connect(self.limpiar_diagnosticos)  # Elimina diagnósticos antiguos cuando el código se modifica.
        self.textChanged.connect(self.resaltar_linea_actual)  # Retira el resaltado cuando el editor queda vacío para no cubrir el placeholder.
        self.textChanged.connect(self._actualizar_autocompletado)  # Programa una nueva sugerencia cuando cambia realmente el código.
        self.control_autocompletado.sugerencia_lista.connect(self._recibir_sugerencia_ia)  # Recibe únicamente generaciones actuales aprobadas por el predictor.
        self.verticalScrollBar().rangeChanged.connect(self._posicionar_botones_flotantes)  # Reajusta ambos botones cuando aparece o desaparece la scrollbar.

        self.viewport().installEventFilter(self)  # Permite detectar tooltips y cambios geométricos dentro del área visible.
        self.viewport().setMouseTracking(True)  # Mantiene disponible la posición del mouse sobre el código.

        self.actualizar_ancho_area_numeros_linea()  # Reserva inicialmente el espacio necesario para los números.
        self.resaltar_linea_actual()  # Aplica el resaltado inicial únicamente cuando existe código real.
        self.setPlaceholderText("IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina")  # Muestra una instrucción de referencia mientras el editor está vacío.
        paleta = self.palette()  # Obtiene una copia de la paleta actual para modificar únicamente el texto de ejemplo.
        paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(self.COLOR_PLACEHOLDER))  # Define explícitamente el gris utilizado por el placeholder.
        self.setPalette(paleta)  # Aplica la paleta sin cambiar los demás colores administrados por los estilos generales.

        QTimer.singleShot(0, self._posicionar_botones_flotantes)  # Coloca los controles cuando Qt ya conoce las dimensiones reales del editor.

    def _configurar_botones_flotantes(self) -> None:
        self._configurar_boton_flotante(self.boton_pegar, "Pegar.png", "Pegar comando desde el portapapeles")  # Prepara el primer control utilizando el icono de pegado.
        self._configurar_boton_flotante(self.boton_ejemplos, "Ejemplos.png", "Abrir selector de ejemplos")  # Prepara el segundo control utilizando el recurso de ejemplos.

        self.boton_pegar.clicked.connect(self._pegar_desde_portapapeles)  # Inserta contenido del sistema mediante el primer botón.
        self.boton_ejemplos.clicked.connect(self._abrir_selector_ejemplos)  # Abre la herramienta heredada mediante el segundo botón.

    def _configurar_boton_flotante(self, boton: QPushButton, nombre_icono: str, ayuda: str) -> None:
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

        if ruta_icono.exists():
            boton.setIcon(QIcon(str(ruta_icono)))  # Coloca la imagen correspondiente dentro del control.

        boton.show()  # Garantiza que el botón se encuentre visible sobre el editor.
        boton.raise_()  # Mantiene el control por encima de los componentes internos de QPlainTextEdit.

    def _posicionar_botones_flotantes(self, *_argumentos) -> None:
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

    def _pegar_desde_portapapeles(self) -> None:
        if self.canPaste():
            self.paste()  # Inserta el texto en la posición actual o sustituye cualquier selección existente.

        self.setFocus()  # Devuelve inmediatamente el foco al editor para continuar escribiendo.

    def _abrir_selector_ejemplos(self) -> None:
        ejemplos_validos, ejemplos_invalidos = self.gestor_ejemplos.cargar_ejemplos()  # Recupera ambas categorías mediante el componente independiente de Motor.

        if not ejemplos_validos and not ejemplos_invalidos:
            QMessageBox.warning(self, "Ejemplos", "No se encontraron ejemplos dentro de la carpeta Ejemplos.")  # Informa el problema sin modificar el editor.
            return

        selector = SelectorEjemplos(ejemplos_validos, ejemplos_invalidos, self.window())  # Crea la ventana modal utilizando la aplicación principal como propietaria.

        if selector.exec() != QDialog.DialogCode.Accepted:
            self.setFocus()  # Devuelve el foco al editor después de abandonar el selector.
            return

        texto_ejemplos = selector.obtener_texto_seleccionado()  # Recupera únicamente los comandos correspondientes a las casillas marcadas.

        if not texto_ejemplos:
            self.setFocus()  # Conserva el comportamiento normal del editor.
            return

        modo = self._consultar_modo_insercion()  # Determina si debe reemplazarse la entrada actual o agregarse el contenido al final.

        if modo is None:
            self.setFocus()  # Regresa al editor sin realizar ninguna modificación.
            return

        if modo == "reemplazar":
            self.setPlainText(texto_ejemplos)  # Coloca únicamente los ejemplos seleccionados.
        else:
            texto_actual = self.toPlainText().rstrip()  # Elimina únicamente saltos sobrantes del final del contenido existente.
            texto_completo = f"{texto_actual}\n{texto_ejemplos}" if texto_actual else texto_ejemplos  # Separa ambas partes mediante un único salto de línea.
            self.setPlainText(texto_completo)  # Actualiza el documento con el contenido combinado.

        cursor = self.textCursor()  # Obtiene el cursor después de actualizar el documento.
        cursor.movePosition(QTextCursor.MoveOperation.End)  # Lleva la posición de escritura al final de los ejemplos insertados.
        self.setTextCursor(cursor)  # Convierte la nueva posición en el cursor visible.
        self.ejemplos_insertados.emit()  # Solicita a la ventana limpiar cualquier resultado correspondiente a una entrada anterior.
        self.setFocus()  # Devuelve el foco para permitir editar o compilar inmediatamente.

    def _consultar_modo_insercion(self) -> str | None:
        if not self.toPlainText().strip():
            return "reemplazar"  # Inserta directamente porque no hay información que pueda perderse.

        mensaje = QMessageBox(self)  # Crea una pregunta personalizada con nombres más claros que Sí y No.
        mensaje.setWindowTitle("Insertar ejemplos")  # Identifica la operación que requiere confirmación.
        mensaje.setText("Ya hay texto en la entrada.\n\nElige si deseas reemplazarlo o agregar los ejemplos al final.")  # Explica las dos posibilidades disponibles.

        boton_reemplazar = mensaje.addButton("Reemplazar", QMessageBox.ButtonRole.AcceptRole)  # Crea la acción que descarta la entrada anterior.
        boton_agregar = mensaje.addButton("Agregar al final", QMessageBox.ButtonRole.ActionRole)  # Crea la acción que conserva el código existente.
        boton_cancelar = mensaje.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)  # Permite abandonar la operación sin realizar cambios.

        mensaje.exec()  # Muestra la pregunta y espera una respuesta explícita.
        boton_pulsado = mensaje.clickedButton()  # Obtiene exactamente la acción seleccionada por el usuario.

        if boton_pulsado is boton_reemplazar:
            return "reemplazar"

        if boton_pulsado is boton_agregar:
            return "agregar"

        if boton_pulsado is boton_cancelar:
            return None

        return None  # Trata cualquier cierre alternativo de la ventana como una cancelación segura.

    def ancho_area_numeros_linea(self) -> int:
        digitos = len(str(max(1, self.blockCount())))  # Obtiene cuántos dígitos necesita representar el número de línea más grande.
        return 12 + self.fontMetrics().horizontalAdvance("9") * digitos  # Combina el ancho de los dígitos con un pequeño margen adicional.

    def actualizar_ancho_area_numeros_linea(self, _cantidad=0) -> None:
        self.setViewportMargins(self.ancho_area_numeros_linea(), 0, 0, 0)  # Evita que el texto del editor se dibuje debajo de los números.

    def actualizar_area_numeros_linea(self, rectangulo, desplazamiento: int) -> None:
        if desplazamiento:
            self.area_numeros_linea.scroll(0, desplazamiento)  # Desplaza los números la misma cantidad que el contenido.
        else:
            self.area_numeros_linea.update(0, rectangulo.y(), self.area_numeros_linea.width(), rectangulo.height())  # Redibuja solamente la zona afectada.

        if rectangulo.contains(self.viewport().rect()):
            self.actualizar_ancho_area_numeros_linea()  # Recalcula el ancho por si cambió la cantidad total de líneas.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Permite que QPlainTextEdit ejecute primero su comportamiento normal.
        rectangulo = self.contentsRect()  # Obtiene la región interior disponible del editor.
        ancho = self.ancho_area_numeros_linea()  # Calcula el ancho requerido actualmente por los números.
        self.area_numeros_linea.setGeometry(QRect(rectangulo.left(), rectangulo.top(), ancho, rectangulo.height()))  # Coloca el área lateral ocupando toda la altura.
        self._posicionar_botones_flotantes()  # Mantiene ambos controles en la esquina correcta cuando cambia el tamaño.

    def paintEvent(self, evento) -> None:
        super().paintEvent(evento)  # Permite que Qt dibuje texto, selección, resaltado y demás contenido habitual.
        self._pintar_sugerencia_ia()  # Dibuja la continuación virtual sin incorporarla todavía al documento.
        self._pintar_diagnosticos()  # Dibuja las ondas encima del editor después de que el texto ya está visible.

    def keyPressEvent(self, evento) -> None:
        if self.sugerencia_ia and evento.key() == Qt.Key.Key_Tab and evento.modifiers() == Qt.KeyboardModifier.NoModifier:
            prefijo_actual = self._obtener_prefijo_linea_cursor()  # Comprueba nuevamente que el usuario siga exactamente donde nació la sugerencia.

            if prefijo_actual == self.prefijo_sugerencia_ia:
                sugerencia = self.sugerencia_ia  # Conserva la continuación antes de retirar su representación virtual.
                self._ocultar_sugerencia_ia()  # Retira el texto gris antes de convertirlo en texto real.
                self.control_autocompletado.cancelar()  # Invalida cualquier generación anterior relacionada con el mismo prefijo.

                cursor = self.textCursor()  # Obtiene la posición exacta donde debe aceptarse el ghost text.
                cursor.insertText(sugerencia)  # Convierte la continuación validada en código real del documento.
                self.setTextCursor(cursor)  # Mantiene el cursor inmediatamente después del texto insertado.

                self.control_autocompletado.cancelar()  # Cancela la solicitud que textChanged pudiera haber programado para la línea ya completada.
                return

        if self.sugerencia_ia and evento.key() == Qt.Key.Key_Escape:
            self.control_autocompletado.cancelar()  # Impide que reaparezca una respuesta correspondiente al mismo texto.
            self._ocultar_sugerencia_ia()  # Retira únicamente la propuesta sin modificar ningún carácter real.
            return

        super().keyPressEvent(evento)  # Conserva el comportamiento tradicional para cualquier otra tecla.

    def pintar_numeros_linea(self, evento) -> None:
        pintor = QPainter(self.area_numeros_linea)  # Crea el objeto encargado de dibujar dentro del área lateral.
        pintor.fillRect(evento.rect(), QColor("#181825"))  # Pinta el fondo del área con el tono oscuro de la interfaz.
        bloque = self.firstVisibleBlock()  # Obtiene el primer bloque de texto que actualmente puede verse.
        numero_bloque = bloque.blockNumber()  # Obtiene el índice interno de la primera línea visible.
        superior = int(self.blockBoundingGeometry(bloque).translated(self.contentOffset()).top())  # Calcula la posición vertical inicial del bloque.
        inferior = superior + int(self.blockBoundingRect(bloque).height())  # Calcula dónde termina verticalmente el mismo bloque.
        pintor.setPen(QColor("#6c7086"))  # Selecciona el color utilizado para dibujar los números de línea.

        while bloque.isValid() and superior <= evento.rect().bottom():
            if bloque.isVisible() and inferior >= evento.rect().top():
                numero = str(numero_bloque + 1)  # Convierte el índice interno empezado en cero al número visible empezado en uno.
                pintor.drawText(0, superior, self.area_numeros_linea.width() - 6, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, numero)  # Dibuja el número alineado a la derecha.

            bloque = bloque.next()  # Avanza al siguiente bloque de texto del documento.
            superior = inferior  # Usa el final anterior como comienzo vertical del siguiente bloque.
            inferior = superior + int(self.blockBoundingRect(bloque).height())  # Calcula el final vertical del nuevo bloque.
            numero_bloque += 1  # Avanza también el número lógico de línea.

    def resaltar_linea_actual(self) -> None:
        selecciones = []  # Crea la colección de selecciones visuales utilizadas por el editor.

        if not self.isReadOnly() and not self.document().isEmpty():
            seleccion = QTextEdit.ExtraSelection()  # Crea el resaltado únicamente cuando existe código real para no ocultar el placeholder.
            seleccion.format.setBackground(QColor("#181825"))  # Aplica un fondo ligeramente distinto a la línea activa.
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # Extiende el fondo a todo el ancho disponible.
            seleccion.cursor = self.textCursor()  # Utiliza la posición actual del cursor como referencia.
            seleccion.cursor.clearSelection()  # Evita seleccionar caracteres reales.
            selecciones.append(seleccion)  # Agrega la selección de línea a la lista visual.

        self.setExtraSelections(selecciones)  # Aplica únicamente el resaltado de la línea porque las ondas se dibujan manualmente.

    def _actualizar_autocompletado(self) -> None:
        self._ocultar_sugerencia_ia()  # Una propuesta anterior deja de ser válida en cuanto cambia texto o posición.
        prefijo = self._obtener_prefijo_linea_cursor()  # Recupera únicamente la línea que puede completarse de forma segura.

        if prefijo is None:
            self.control_autocompletado.cancelar()  # Invalida cualquier generación cuando el cursor ya no cumple las condiciones.
            return

        self.control_autocompletado.programar(prefijo)  # Reinicia el debounce utilizando exactamente el contenido más reciente.

    def _obtener_prefijo_linea_cursor(self) -> str | None:
        cursor = self.textCursor()  # Obtiene el cursor real sin modificar su posición.

        if cursor.hasSelection():
            return None  # Evita sugerencias mientras el usuario está seleccionando texto existente.

        bloque = cursor.block()  # Obtiene exclusivamente la línea donde se encuentra el cursor.

        if not bloque.isValid():
            return None  # Protege el autocompletado frente a posiciones transitorias durante cambios del documento.

        posicion_relativa = cursor.position() - bloque.position()  # Calcula la columna actual dentro de la línea.

        if posicion_relativa != len(bloque.text()):
            return None  # Solo permite ghost text cuando el cursor está exactamente al final de la línea.

        prefijo = bloque.text()  # Conserva el contenido completo porque el cursor ya se encuentra después del último carácter.

        if not prefijo.strip():
            return None  # No consulta la IA sobre líneas vacías.

        return prefijo  # Entrega al predictor únicamente la instrucción actualmente activa.

    def _recibir_sugerencia_ia(self, prefijo: str, sugerencia: str) -> None:
        prefijo_actual = self._obtener_prefijo_linea_cursor()  # Comprueba nuevamente el documento porque la generación ocurrió en otro hilo.

        if prefijo_actual != prefijo:
            return  # Descarta visualmente cualquier resultado que ya no corresponda con el cursor y texto actuales.

        self.prefijo_sugerencia_ia = prefijo  # Registra la relación necesaria para aceptar posteriormente con Tab.
        self.sugerencia_ia = sugerencia  # Conserva la continuación sin insertarla en el QTextDocument.
        self.viewport().update()  # Solicita un repintado inmediato para que aparezca el ghost text.

    def _ocultar_sugerencia_ia(self) -> None:
        if not self.sugerencia_ia and not self.prefijo_sugerencia_ia:
            return  # Evita repintados innecesarios cuando no existe ninguna propuesta visible.

        self.sugerencia_ia = ""  # Elimina solamente la representación virtual.
        self.prefijo_sugerencia_ia = ""  # Elimina también el vínculo con el prefijo que la produjo.
        self.viewport().update()  # Retira el texto gris de la vista.

    def _pintar_sugerencia_ia(self) -> None:
        if not self.sugerencia_ia:
            return  # Finaliza inmediatamente cuando no existe una continuación aprobada.

        prefijo_actual = self._obtener_prefijo_linea_cursor()  # Comprueba que todavía pueda dibujarse en la posición original.

        if prefijo_actual != self.prefijo_sugerencia_ia:
            return  # Impide representar una propuesta sobre texto que cambió después de recibirla.

        cursor = self.textCursor()  # Usa el cursor actual como punto donde comenzará el ghost text.
        rectangulo = self.cursorRect(cursor)  # Convierte la posición textual en coordenadas del viewport.
        base_y = float(rectangulo.top() + self.fontMetrics().ascent())  # Alinea verticalmente la sugerencia con el texto real de la línea.

        pintor = QPainter(self.viewport())  # Dibuja directamente sobre la vista sin alterar el contenido del documento.
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)  # Suaviza el pequeño icono utilizado para identificar visualmente el autocompletado.
        pintor.setPen(QColor(self.COLOR_SUGERENCIA_IA))  # Aplica un color secundario claramente distinto al código confirmado.
        pintor.setFont(self.font())  # Mantiene exactamente la misma tipografía utilizada por el editor.
        pintor.setOpacity(0.72)  # Reduce la intensidad para dejar claro que el contenido aún no ha sido aceptado.
        texto_x = float(rectangulo.left())  # Conserva el comienzo exacto de la continuación para que el ghost text siga unido al código escrito.
        pintor.drawText(QPointF(texto_x, base_y), self.sugerencia_ia)  # Dibuja la continuación inmediatamente después del cursor.
        if not self.icono_autocompletado_ia.isNull():  # Comprueba que el recurso visual de IA se haya cargado correctamente.
            ancho_sugerencia = float(self.fontMetrics().horizontalAdvance(self.sugerencia_ia))  # Calcula dónde termina visualmente el ghost text.
            icono_x = int(texto_x + ancho_sugerencia + self.SEPARACION_ICONO_AUTOCOMPLETADO)  # Coloca el icono después de la sugerencia sin interrumpirla.
            icono_y = int(rectangulo.top() + max(0, (self.fontMetrics().height() - self.TAMANO_ICONO_AUTOCOMPLETADO) / 2))  # Centra verticalmente el icono respecto a la línea.
            pintor.setOpacity(0.88)  # Hace el indicador un poco más visible que el texto virtual sin convertirlo en protagonista.
            pintor.drawPixmap(icono_x, icono_y, self.TAMANO_ICONO_AUTOCOMPLETADO, self.TAMANO_ICONO_AUTOCOMPLETADO, self.icono_autocompletado_ia)  # Identifica la sugerencia como contenido producido por el asistente local.
        pintor.end()  # Libera explícitamente el pintor antes de continuar con otros elementos visuales.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:
        self.diagnosticos = list(diagnosticos)  # Conserva una copia independiente de los diagnósticos recibidos.
        self.viewport().update()  # Solicita inmediatamente el redibujado de las ondas sobre el código.

    def limpiar_diagnosticos(self) -> None:
        if not self.diagnosticos:
            return  # Evita redibujar innecesariamente cuando no existe ningún diagnóstico.

        self.diagnosticos.clear()  # Elimina todos los diagnósticos asociados actualmente con el código.
        QToolTip.hideText()  # Oculta cualquier tooltip perteneciente a un diagnóstico anterior.
        self.viewport().update()  # Redibuja el editor para retirar todas las ondas antiguas.

    def _pintar_diagnosticos(self) -> None:
        if not self.diagnosticos:
            return  # Finaliza inmediatamente cuando el código no presenta marcas visuales.

        pintor = QPainter(self.viewport())  # Crea un pintor directamente sobre el área donde se muestra el código.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza las curvas para evitar líneas dentadas.

        for diagnostico in self.diagnosticos:
            rango = self._rango_diagnostico(diagnostico)  # Convierte la ubicación estructurada en posiciones absolutas del documento.

            if rango is None:
                continue

            inicio, final = rango  # Separa las posiciones absoluta inicial y final.
            cursor_inicio = QTextCursor(self.document())  # Crea un cursor temporal para localizar visualmente el inicio.
            cursor_inicio.setPosition(inicio)  # Coloca el cursor sobre el primer carácter diagnosticado.
            cursor_final = QTextCursor(self.document())  # Crea otro cursor temporal para localizar visualmente el final.
            cursor_final.setPosition(final)  # Coloca el cursor inmediatamente después del último carácter diagnosticado.

            rectangulo_inicio = self.cursorRect(cursor_inicio)  # Obtiene las coordenadas del primer carácter dentro del viewport.
            rectangulo_final = self.cursorRect(cursor_final)  # Obtiene las coordenadas correspondientes al extremo final.

            if rectangulo_inicio.bottom() < 0 or rectangulo_inicio.top() > self.viewport().height():
                continue  # Evita realizar trabajo de dibujo sobre líneas que el usuario no puede ver.

            inicio_x = float(rectangulo_inicio.left())  # Obtiene la posición horizontal donde debe comenzar la onda.
            final_x = float(rectangulo_final.left())  # Obtiene la posición horizontal donde debe terminar la onda.

            if final_x <= inicio_x:
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

    def _crear_camino_ondulado(self, inicio_x: float, final_x: float, base_y: float) -> QPainterPath:
        camino = QPainterPath(QPointF(inicio_x, base_y))  # Inicia el camino exactamente debajo del comienzo del diagnóstico.
        x = inicio_x  # Guarda la posición horizontal desde donde se construirá cada ondulación.
        media_onda = self.LONGITUD_ONDA / 2.0  # Divide la longitud completa para construir primero una curva hacia abajo y luego hacia arriba.

        while x < final_x:
            siguiente = min(x + media_onda, final_x)  # Calcula dónde terminará la primera mitad sin sobrepasar el diagnóstico.
            control_x = x + (siguiente - x) / 2.0  # Calcula el centro horizontal utilizado por la curva.
            camino.quadTo(QPointF(control_x, base_y + self.AMPLITUD_ONDA), QPointF(siguiente, base_y))  # Genera la mitad inferior de la onda.
            x = siguiente  # Continúa desde el extremo alcanzado.

            if x >= final_x:
                break

            siguiente = min(x + media_onda, final_x)  # Calcula el final de la segunda mitad.
            control_x = x + (siguiente - x) / 2.0  # Calcula nuevamente el centro horizontal.
            camino.quadTo(QPointF(control_x, base_y - self.AMPLITUD_ONDA), QPointF(siguiente, base_y))  # Genera la mitad superior completando la ondulación.
            x = siguiente  # Avanza hasta continuar con la próxima onda completa.

        return camino  # Devuelve el trazado completo listo para dibujarse.

    def _rango_diagnostico(self, diagnostico: Diagnostico) -> tuple[int, int] | None:
        if diagnostico.linea is None:
            return None  # No puede dibujarse un diagnóstico sin una ubicación concreta.

        bloque = self.document().findBlockByNumber(max(diagnostico.linea - 1, 0))  # Localiza la línea convirtiendo la numeración visible a índice interno.

        if not bloque.isValid():
            return None

        texto_linea = bloque.text()  # Obtiene únicamente el texto perteneciente a la línea encontrada.

        if not texto_linea:
            return None

        columna = max(diagnostico.columna or 0, 0)  # Normaliza la columna evitando posiciones negativas.
        columna = min(columna, len(texto_linea))  # Impide que la posición sobrepase el final real de la línea.
        final_relativo = min(columna + max(diagnostico.longitud, 1), len(texto_linea))  # Calcula el final respetando la longitud del diagnóstico.

        if final_relativo <= columna:
            columna = max(len(texto_linea) - 1, 0)  # Utiliza el último carácter visible como referencia.
            final_relativo = len(texto_linea)  # Extiende el subrayado hasta el final real de la línea.

        inicio = bloque.position() + columna  # Convierte la columna relativa en posición absoluta dentro del documento.
        final = bloque.position() + final_relativo  # Convierte también el final relativo.

        return inicio, final  # Devuelve el rango utilizado por la onda y por el tooltip.

    def _color_diagnostico(self, diagnostico: Diagnostico) -> QColor:
        severidad = diagnostico.severidad.lower()  # Normaliza la severidad para aceptar variantes futuras.

        if severidad in ("warning", "advertencia"):
            return QColor("#f9e2af")  # Utiliza amarillo para las advertencias.

        if diagnostico.categoria == "Léxico":
            return QColor("#f38ba8")  # Utiliza rojo para errores léxicos.

        if diagnostico.categoria == "Sintáctico":
            return QColor("#fab387")  # Utiliza naranja para errores sintácticos.

        if diagnostico.categoria == "Semántico":
            return QColor("#cba6f7")  # Utiliza violeta para futuros errores semánticos.

        return QColor("#f38ba8")  # Utiliza rojo como color de respaldo para otros errores.

    def _diagnosticos_en_posicion(self, posicion: int) -> list[Diagnostico]:
        encontrados = []  # Crea la colección de diagnósticos relacionados con el carácter señalado.

        for diagnostico in self.diagnosticos:
            rango = self._rango_diagnostico(diagnostico)  # Obtiene el mismo rango utilizado para dibujar la onda.

            if rango is None:
                continue

            inicio, final = rango  # Separa ambos límites del diagnóstico.

            if inicio <= posicion < final:
                encontrados.append(diagnostico)  # Conserva el diagnóstico para mostrarlo dentro del tooltip.

        return encontrados  # Devuelve todos los diagnósticos relacionados con la posición indicada.

    def _texto_tooltip(self, diagnosticos: list[Diagnostico]) -> str:
        bloques = []  # Conserva cada diagnóstico como un bloque textual independiente.

        for diagnostico in diagnosticos:
            mensaje = fill(diagnostico.mensaje, width=72)  # Divide mensajes largos para evitar tooltips excesivamente anchos.
            solucion = fill(diagnostico.solucion, width=72) if diagnostico.solucion else "Sin solución registrada."  # Divide también la recomendación.

            bloques.append(
                f"{diagnostico.codigo} · {diagnostico.categoria}\n"
                f"{mensaje}\n\n"
                f"Solución:\n{solucion}"
            )

        return "\n\n────────────────────────\n\n".join(bloques)  # Separa claramente varios diagnósticos coincidentes.

    def eventFilter(self, objeto, evento):
        if objeto is self.viewport() and evento.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._posicionar_botones_flotantes)  # Recalcula ambas posiciones cuando Qt termina de reajustar sus componentes internos.

        if objeto is self.viewport() and evento.type() == QEvent.Type.ToolTip:
            cursor = self.cursorForPosition(evento.pos())  # Obtiene la posición textual situada debajo del puntero.
            diagnosticos = self._diagnosticos_en_posicion(cursor.position())  # Busca errores o advertencias relacionados con esa posición.

            if diagnosticos:
                QToolTip.showText(evento.globalPos(), self._texto_tooltip(diagnosticos), self.viewport())  # Muestra código, mensaje y solución.
            else:
                QToolTip.hideText()  # Oculta cualquier información contextual anterior.

            return True

        return super().eventFilter(objeto, evento)  # Conserva el comportamiento normal para cualquier otro evento.

    def ir_a_posicion(self, linea: int | None, columna: int | None, longitud: int = 1) -> None:
        if linea is None:
            return

        bloque = self.document().findBlockByNumber(max(linea - 1, 0))  # Localiza el bloque correspondiente convirtiendo la línea visible a índice interno.

        if not bloque.isValid():
            return

        posicion = bloque.position() + max(columna or 0, 0)  # Calcula la posición absoluta sumando la columna al inicio del bloque.
        cursor = QTextCursor(self.document())  # Crea un cursor independiente asociado al documento actual.
        cursor.setPosition(min(posicion, self.document().characterCount() - 1))  # Coloca el cursor evitando sobrepasar el final del documento.

        if longitud > 0:
            final = min(posicion + longitud, self.document().characterCount() - 1)  # Calcula el final dentro de los límites del documento.
            cursor.setPosition(final, QTextCursor.MoveMode.KeepAnchor)  # Extiende la selección desde la posición inicial hasta el final.

        self.setTextCursor(cursor)  # Convierte el cursor calculado en el cursor visible del editor.
        self.centerCursor()  # Desplaza la vista para mantener visible la línea seleccionada.
        self.setFocus()  # Devuelve el foco al editor para corregir inmediatamente el texto.