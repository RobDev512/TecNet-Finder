# ============================================================
# Archivo: controles_edicion_local.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Integra el menú contextual traducido y un completador local
# de palabras reservadas y plantillas del DSL. No consulta IA,
# no interfiere con la compilación y sigue los temas existentes.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QPoint, QRectF, Qt, QTimer  # Gestiona eventos, geometría y posicionamiento diferido.
from PySide6.QtGui import QPainterPath, QRegion, QStandardItem, QStandardItemModel, QTextCursor  # Permite recortar esquinas y editar fragmentos.
from PySide6.QtWidgets import QApplication, QCompleter, QMenu  # Proporciona listas, menús y geometría de pantalla.
from Motor.compilacion.sugerencias_codigo_local import ETIQUETA_PLANTILLA, obtener_sugerencias_codigo  # Identifica la plantilla sin alterar el motor determinista.
from Motor.configuracion.catalogo_temas import obtener_tema  # Recupera los diez temas visuales.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Consulta el idioma confirmado.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Consulta el tema confirmado.


TEXTOS_MENU = {  # Mantiene las traducciones de las acciones nativas en los seis idiomas ya admitidos.
    "es": ("Deshacer", "Rehacer", "Cortar", "Copiar", "Pegar", "Eliminar", "Seleccionar todo"),
    "en": ("Undo", "Redo", "Cut", "Copy", "Paste", "Delete", "Select All"),
    "pt": ("Desfazer", "Refazer", "Recortar", "Copiar", "Colar", "Excluir", "Selecionar tudo"),
    "fr": ("Annuler", "Rétablir", "Couper", "Copier", "Coller", "Supprimer", "Tout sélectionner"),
    "de": ("Rückgängig", "Wiederholen", "Ausschneiden", "Kopieren", "Einfügen", "Löschen", "Alles auswählen"),
    "la": ("Revocare", "Repetere", "Excidere", "Exscribere", "Inserere", "Delere", "Omnia seligere"),
}  # Conserva el orden habitual del menú de QPlainTextEdit sin modificar los atajos.


# ============================================================
# Menú contextual traducido y adaptado al tema
# ============================================================

class FiltroEsquinasMenu(QObject):  # Recorta realmente la ventana del menú y elimina el fondo cuadrado de sus vértices.
    def eventFilter(self, objeto, evento):
        if evento.type() in (QEvent.Type.Show, QEvent.Type.Resize):
            QTimer.singleShot(0, self.actualizar_mascara)  # Espera la geometría definitiva antes del recorte.
        return super().eventFilter(objeto, evento)

    def actualizar_mascara(self) -> None:
        menu = self.parent()  # Recupera el menú sin mantener referencias externas.
        if menu is None or menu.width() < 2 or menu.height() < 2: return  # Evita aplicar una región vacía.
        camino = QPainterPath()  # Dibuja la silueta de cuatro esquinas redondeadas.
        camino.addRoundedRect(QRectF(menu.rect()).adjusted(0, 0, -1, -1), 11, 11)  # Usa el mismo radio declarado en la hoja de estilos.
        menu.setMask(QRegion(camino.toFillPolygon().toPolygon()))  # Oculta incluso las esquinas del fondo de la ventana nativa.


def mostrar_menu_contextual_editor(editor, evento) -> None:  # Reutiliza las acciones nativas sin perder sus iconos ni atajos.
    menu = editor.createStandardContextMenu()  # Recupera Undo, Redo, Cut, Copy, Paste, Delete y Select All originales.
    idioma = PreferenciasAplicacion().idioma_interfaz()  # Consulta el idioma más reciente, también después de cambiarlo en Configuración.
    traducciones = TEXTOS_MENU.get(idioma, TEXTOS_MENU["es"])  # Mantiene español como respaldo seguro.
    originales = ("undo", "redo", "cut", "copy", "paste", "delete", "select all")  # Normaliza exclusivamente las siete acciones tradicionales.
    equivalencias = dict(zip(originales, traducciones))  # Relaciona el comando original con su etiqueta traducida.

    for accion in menu.actions():  # Conserva separadores, estados habilitados y acciones de Qt sin reimplementarlos.
        texto = accion.text()  # Recupera el texto actual, que puede incluir un atajo después de tabulación.
        nombre, separador, atajo = texto.partition("\t")  # Preserva Ctrl+Z, Ctrl+Y y los demás atajos visibles.
        clave = nombre.replace("&", "").replace("…", "").replace("...", "").strip().casefold()  # Retira marcas de acceso y puntuación.
        if clave in equivalencias: accion.setText(equivalencias[clave] + (separador + atajo if separador else ""))  # Traduce solo acciones conocidas.

    p = obtener_tema(PreferenciasTema().tema())  # Obtiene colores de la variante actual, tanto clara como oscura.
    menu.setObjectName("MenuContextualEditor")  # Reserva un identificador exclusivo para los estilos.
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite que el redondeo no deje esquinas cuadradas.
    menu.setStyleSheet(f"""
        QMenu#MenuContextualEditor {{ background-color: {p['panel']}; color: {p['texto']}; border: 1px solid {p['borde_fuerte']}; border-radius: 11px; padding: 6px; }}
        QMenu#MenuContextualEditor::item {{ background: transparent; border: 0px; border-radius: 6px; padding: 7px 28px 7px 30px; margin: 2px 3px; min-width: 170px; }}
        QMenu#MenuContextualEditor::item:selected {{ background-color: {p['superficie_hover']}; color: {p['texto']}; }}
        QMenu#MenuContextualEditor::item:disabled {{ color: {p['texto_deshabilitado']}; }}
        QMenu#MenuContextualEditor::separator {{ height: 1px; background: {p['borde']}; margin: 5px 12px; }}
    """)  # Pinta estados normales, hover y deshabilitados sin modificar los atajos del teclado.
    filtro = FiltroEsquinasMenu(menu)  # Conserva la máscara mientras exista el menú desplegado.
    menu.installEventFilter(filtro)  # Actualiza el recorte cuando Qt termina de calcular el tamaño.
    menu.exec(evento.globalPos())  # Presenta el menú justo donde el usuario hizo clic derecho.
    menu.deleteLater()  # Libera las acciones cuando el menú termina.


# ============================================================
# Completador de código local (independiente de IA)
# ============================================================

class ControlCompletadoLocal(QObject):  # Administra sugerencias emergentes sin modificar las preferencias de IA.
    def __init__(self, editor):
        super().__init__(editor)  # Mantiene el ciclo de vida ligado al editor.
        self.editor = editor  # Conserva el área de texto real.
        self.opciones = {}  # Relaciona cada etiqueta visible con su fragmento de inserción.
        self.prefijo = ""  # Conserva el texto exacto que sustituirá una opción elegida.
        self.insertando = False  # Evita que una inserción programática abra otra lista inmediatamente.
        self.modelo = QStandardItemModel(self)  # Conserva etiquetas y ayuda contextual para cada sugerencia.
        self.completador = QCompleter(self.modelo, self)  # Utiliza el componente estándar de Qt para sugerencias de código.
        self.completador.setWidget(editor)  # Vincula teclado, posición y foco con QPlainTextEdit.
        self.completador.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)  # Muestra una lista como VS Code, sin escribir automáticamente.
        self.completador.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Encuentra IP aunque se escriba ip.
        self.completador.setFilterMode(Qt.MatchFlag.MatchStartsWith)  # Filtra desde el principio de cada token.
        self.completador.setMaxVisibleItems(7)  # Evita ventanas excesivamente altas.
        self.completador.activated[str].connect(self._insertar_etiqueta)  # Permite aceptar una opción también con un clic.
        self.completador.popup().setObjectName("ListaCompletadoLocal")  # Identifica visualmente el desplegable.
        self.completador.popup().setMouseTracking(True)  # Facilita el resaltado de la opción bajo el puntero.
        self.completador.popup().installEventFilter(self)  # Captura Esc aunque el foco del teclado esté en la lista.

    def eventFilter(self, objeto, evento):  # Permite cerrar la lista aun cuando QCompleter consume las teclas.
        if objeto is self.completador.popup() and evento.type() == QEvent.Type.KeyPress and evento.key() == Qt.Key.Key_Escape:
            self._cerrar_y_reactivar_ia()  # Devuelve el control al autocompletador con IA.
            return True  # Evita que Qt procese un segundo Escape sobre el editor.
        return super().eventFilter(objeto, evento)

    def visible(self) -> bool:
        return self.completador.popup().isVisible()  # Permite priorizar el completador frente al ghost text de IA.

    def ocultar(self) -> None:
        if self.visible(): self.completador.popup().hide()  # Retira solamente la lista, sin editar contenido.

    def _cerrar_y_reactivar_ia(self) -> None:
        self.ocultar()  # Retira la lista local sin modificar lo escrito.
        self.editor.setFocus()  # Recupera el teclado en el área de entrada.
        QTimer.singleShot(0, self.editor._actualizar_autocompletado)  # Vuelve a solicitar el ghost text si la IA está habilitada.

    def procesar_tecla(self, evento) -> bool:  # Decide si el teclado pertenece temporalmente a la lista emergente.
        tecla = evento.key()  # Recupera el código de la pulsación.
        if tecla == Qt.Key.Key_Space and evento.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.mostrar(manual=True)  # Ctrl+Espacio abre sugerencias sin requerir un carácter nuevo.
            return True  # Evita introducir espacios al ejecutar el atajo.

        if not self.visible(): return False  # Mantiene todas las teclas originales cuando no hay sugerencias abiertas.
        if tecla == Qt.Key.Key_Escape:
            self._cerrar_y_reactivar_ia()  # Escape libera inmediatamente la interfaz para el ghost text de IA.
            return True
        if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab) and evento.modifiers() == Qt.KeyboardModifier.NoModifier:
            indice = self.completador.popup().currentIndex()  # Recupera la opción enfocada por teclado o ratón.
            if not indice.isValid(): indice = self.completador.completionModel().index(0, 0)  # Usa la primera si todavía no hay selección.
            if indice.isValid(): self._insertar_etiqueta(str(indice.data(Qt.ItemDataRole.DisplayRole)))  # Inserta únicamente al confirmar.
            else: self.ocultar()  # No bloquea indefinidamente una lista vacía.
            return True
        if tecla in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            lista = self.completador.popup()  # Navega sin desplazar el contenido del editor.
            actual = lista.currentIndex().row()
            cantidad = self.completador.completionModel().rowCount()
            if cantidad:
                siguiente = (actual + (-1 if tecla == Qt.Key.Key_Up else 1)) % cantidad
                lista.setCurrentIndex(self.completador.completionModel().index(siguiente, 0))  # Resalta la sugerencia seleccionada.
            return True
        return False  # Permite escribir y recalcular las coincidencias normalmente.

    def actualizar_despues_de_tecla(self, evento) -> None:  # Recalcula solo tras una edición realizada mediante teclado.
        if self.insertando: return  # Evita eventos producidos por un reemplazo controlado.
        texto = evento.text()  # Recupera el carácter realmente escrito.
        modificadores = evento.modifiers()  # Distingue escritura normal de atajos como Ctrl+V.
        cambio = bool(texto and texto.isprintable() and not (modificadores & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier)))
        if cambio or evento.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete): self.mostrar(manual=False)  # Actualiza solo prefijos reservados y oculta el resto.
        elif evento.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End): self.ocultar()  # Retira propuestas si el cursor se desplaza.

    def mostrar(self, *, manual: bool) -> None:
        cursor = self.editor.textCursor()  # Consulta la posición exacta donde se está escribiendo.
        if cursor.hasSelection(): self.ocultar(); return  # Evita sobrescribir selecciones ajenas al completador.
        bloque = cursor.block()  # Limita las sugerencias a la instrucción actual.
        columna = cursor.position() - bloque.position()  # Obtiene la posición relativa sin modificar el documento.
        resto = bloque.text()[columna:]  # Comprueba si existe una palabra posterior que no debería sobrescribirse.
        if resto and not resto.isspace(): self.ocultar(); return  # Mantiene los caracteres de la derecha intactos.
        prefijo, opciones = obtener_sugerencias_codigo(bloque.text()[:columna], manual=manual)  # Consulta exclusivamente la gramática reconocida.
        if not opciones: self.ocultar(); return  # No ofrece palabras fuera de contexto.
        self.prefijo = prefijo  # Conserva la longitud que será reemplazada al aceptar.
        self.opciones = {opcion.etiqueta: opcion for opcion in opciones}  # Construye un mapa exacto, sin desambiguaciones por posición.
        self.modelo.clear()  # Evita conservar entradas antiguas después de cambiar de contexto.
        for opcion in opciones:
            item = QStandardItem(opcion.etiqueta)  # Coloca el nombre del token o plantilla.
            item.setEditable(False)  # Impide editar los textos internos de la lista.
            item.setData(opcion.descripcion, Qt.ItemDataRole.ToolTipRole)  # Proporciona ayuda contextual al pasar el ratón.
            self.modelo.appendRow(item)  # Añade la opción manteniendo el orden de prioridad.
        self.completador.setCompletionPrefix(prefijo)  # Reafirma el filtro de coincidencia sobre el modelo nuevo.
        if not self.completador.completionModel().rowCount(): self.ocultar(); return  # Mantiene la lista cerrada ante un filtro vacío.

        p = obtener_tema(PreferenciasTema().tema())  # Colorea la lista con la variante realmente seleccionada.
        self.completador.popup().setStyleSheet(f"""
            QListView#ListaCompletadoLocal {{ background-color: {p['panel']}; color: {p['texto']}; border: 1px solid {p['borde_fuerte']}; border-radius: 9px; padding: 5px; outline: 0; }}
            QListView#ListaCompletadoLocal::item {{ min-height: 25px; border-radius: 5px; padding: 4px 9px; }}
            QListView#ListaCompletadoLocal::item:hover {{ background-color: {p['superficie_hover']}; color: {p['texto']}; }}
            QListView#ListaCompletadoLocal::item:selected {{ background-color: {p['acento']}; color: {p['texto_inverso']}; }}
        """)  # Mantiene hover, selección y contraste para los diez temas disponibles.
        self.editor._ocultar_sugerencia_ia()  # Oculta el ghost text mientras se selecciona una sugerencia local.
        self.editor.control_autocompletado.cancelar()  # Evita competir con predicciones de IA todavía pendientes.
        rectangulo = self.editor.cursorRect()  # Recupera la posición de la línea activa en el viewport.
        self.ancho_desplegable = self._calcular_ancho_desplegable()  # Ajusta el ancho al texto visible, no al ancho libre del editor.
        rectangulo.setWidth(self.ancho_desplegable)  # Proporciona a Qt el ancho preciso del desplegable.
        self.completador.complete(rectangulo)  # Crea el desplegable manteniendo sus interacciones nativas.
        self._ajustar_altura_desplegable()  # Muestra todas las opciones pequeñas sin una barra de desplazamiento innecesaria.
        self._posicionar_bajo_linea()  # Reubica la lista sin cubrir ni un píxel del texto que se está escribiendo.
        QTimer.singleShot(0, self._posicionar_bajo_linea)  # Corrige ajustes posteriores de geometría realizados por Qt.
        primero = self.completador.completionModel().index(0, 0)  # Selecciona la primera coincidencia disponible.
        if primero.isValid(): self.completador.popup().setCurrentIndex(primero)  # Facilita aceptar con Enter inmediatamente.

    def _calcular_ancho_desplegable(self) -> int:  # Adapta el cuadro al contenido real de las coincidencias filtradas.
        lista = self.completador.popup()  # Usa las métricas de la misma fuente que muestra las sugerencias.
        modelo = self.completador.completionModel()  # Mide solamente las opciones que coinciden con el prefijo actual.
        ancho_texto = max((lista.fontMetrics().horizontalAdvance(str(modelo.index(fila, 0).data(Qt.ItemDataRole.DisplayRole) or "")) for fila in range(modelo.rowCount())), default=0)  # Encuentra la etiqueta visible más larga.
        ancho_scroll = lista.verticalScrollBar().sizeHint().width() + 6 if modelo.rowCount() > self.completador.maxVisibleItems() else 0  # Reserva espacio si aparece la barra vertical.
        ancho_ideal = max(100, ancho_texto + 48 + ancho_scroll)  # Incluye márgenes, padding y bordes para no cortar letras.
        if ETIQUETA_PLANTILLA in self.opciones:  # Únicamente la plantilla larga puede superar el ancho del editor.
            pantalla = QApplication.screenAt(self.editor.mapToGlobal(self.editor.rect().center())) or QApplication.primaryScreen()  # Recupera el monitor donde está el editor.
            limite = pantalla.availableGeometry().width() - 16 if pantalla is not None else self.editor.viewport().width() - 16  # Evita salir de la pantalla.
            return min(max(100, ancho_texto + 88 + lista.verticalScrollBar().sizeHint().width()), max(100, limite))  # Muestra el nombre completo, incluyendo Nombre, con margen adicional.
        return min(ancho_ideal, max(100, self.editor.viewport().width() - 16))  # Conserva el ancho compacto de las palabras reservadas.

    def _ajustar_altura_desplegable(self) -> None:  # Ajusta el alto al número real de opciones y evita scroll innecesario.
        lista = self.completador.popup()  # Recupera la lista utilizada por QCompleter.
        modelo = self.completador.completionModel()  # Consulta solamente las coincidencias que se muestran.
        cantidad = modelo.rowCount()  # Determina el número de sugerencias visibles.
        if not cantidad: return  # No modifica una lista que no contiene opciones.
        maximo = self.completador.maxVisibleItems()  # Mantiene el límite actual de filas mostrado por el completador.
        filas = min(cantidad, maximo)  # Reduce la altura cuando solo hay una o dos sugerencias.
        politica = Qt.ScrollBarPolicy.ScrollBarAlwaysOff if cantidad <= maximo else Qt.ScrollBarPolicy.ScrollBarAsNeeded  # Solo necesita barra cuando realmente se supera el máximo.
        lista.setVerticalScrollBarPolicy(politica)  # QCompleter no debe mostrar una barra para dos filas.
        lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # El ancho ya se adapta al texto disponible.
        altura_filas = sum(max(34, lista.sizeHintForRow(indice)) for indice in range(filas))  # Reserva la altura real de cada opción, incluida su selección.
        altura = altura_filas + 2 * lista.frameWidth() + 16  # Incluye el padding y los bordes del cuadro redondeado.
        if lista.height() != altura: lista.setFixedHeight(altura)  # Mantiene todas las sugerencias visibles sin recortarlas.

    def _posicionar_bajo_linea(self) -> None:  # Ancla el menú bajo la línea completa, no encima de sus caracteres.
        lista = self.completador.popup()  # Recupera la lista emergente ya creada por Qt.
        if not lista.isVisible(): return  # Omite ajustes cuando el usuario cerró las sugerencias.
        self._ajustar_altura_desplegable()  # Reafirma la altura después de los ajustes geométricos diferidos de Qt.
        ancho = getattr(self, "ancho_desplegable", lista.width())  # Conserva el ancho calculado durante el filtrado actual.
        if lista.width() != ancho: lista.resize(ancho, lista.height())  # Impide que Qt vuelva a estirar el cuadro al reposicionarlo.
        rectangulo = self.editor.cursorRect()  # Obtiene altura y origen de la línea que contiene el cursor.
        origen = self.editor.viewport().mapToGlobal(QPoint(rectangulo.left(), rectangulo.bottom() + 2))  # Ubica la lista pegada al borde inferior de la línea, sin taparla.
        pantalla = QApplication.screenAt(origen) or QApplication.primaryScreen()  # Identifica el monitor utilizado actualmente.
        if pantalla is None: lista.move(origen); return  # Conserva la posición calculada si no se conoce la pantalla.
        area = pantalla.availableGeometry()  # Respeta la barra de tareas y los extremos del monitor.
        x = max(area.left() + 4, min(origen.x(), area.right() - lista.width() - 4))  # Impide que la lista salga por la derecha.
        if origen.y() + lista.height() <= area.bottom() - 4: y = origen.y()  # Prefiere siempre abrir por debajo.
        else:
            superior = self.editor.viewport().mapToGlobal(QPoint(rectangulo.left(), rectangulo.top() - 6)).y()  # Calcula el espacio superior.
            y = max(area.top() + 4, superior - lista.height())  # Solo invierte el menú cuando no cabe bajo la línea.
        lista.move(QPoint(x, y))  # Evita la superposición observada sin desplazar el cursor real.

    def _insertar_etiqueta(self, etiqueta: str) -> None:  # Sustituye solo el fragmento aceptado y conserva el historial de deshacer.
        opcion = self.opciones.get(etiqueta)  # Comprueba que la opción pertenezca realmente a la lista actual.
        if opcion is None: self.ocultar(); return  # Descarta selecciones que quedaron obsoletas.
        self.insertando = True  # Protege señales simultáneas de cursor y documento.
        self.ocultar()  # Cierra la lista antes de modificar el contenido.
        self.editor._ocultar_sugerencia_ia()  # Retira cualquier continuación virtual anterior.
        self.editor.control_autocompletado.cancelar()  # Invalida predicciones relacionadas con el fragmento sustituido.
        cursor = self.editor.textCursor()  # Obtiene la posición final del prefijo elegido.
        cursor.beginEditBlock()  # Agrupa la sustitución en una única operación deshacer.
        if self.prefijo:
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(self.prefijo))  # Selecciona solamente el prefijo, no el contenido anterior.
        cursor.insertText(opcion.insercion)  # Inserta exclusivamente el texto definido por el motor determinista.
        if opcion.seleccionar_desde >= 0:
            inicio = cursor.position() - len(opcion.insercion) + opcion.seleccionar_desde  # Sitúa el primer campo editable de la plantilla.
            cursor.setPosition(inicio)  # Mueve el inicio de selección al campo previsto.
            cursor.setPosition(inicio + opcion.seleccionar_longitud, QTextCursor.MoveMode.KeepAnchor)  # Selecciona la dirección IPv4 de ejemplo.
        cursor.endEditBlock()  # Completa el cambio reversible.
        self.editor.setTextCursor(cursor)  # Mantiene el cursor en la posición de edición resultante.
        self.editor.setFocus()  # Devuelve el teclado al editor después de elegir con el ratón.
        self.editor.control_autocompletado.cancelar()  # Descarta generaciones que pudieran programarse durante la sustitución.
        self.insertando = False  # Permite mostrar nuevas sugerencias durante la próxima escritura.
