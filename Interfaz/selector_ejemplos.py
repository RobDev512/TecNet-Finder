# ============================================================
# Archivo: selector_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la ventana utilizada para consultar y
# seleccionar los ejemplos almacenados por TecNet Finder.
#
# Separa las entradas válidas e inválidas, permite seleccionar
# varios casos, consultar una vista previa completa e insertar
# posteriormente los comandos elegidos dentro del editor.
# ============================================================

from PySide6.QtCore import QRectF, QSize, Qt, QTimer  # Importa geometría, tamaños, alineaciones, estados y temporización de la interfaz.
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen  # Importa herramientas para dibujar las casillas personalizadas.
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Importa los componentes necesarios para construir el selector.

from Motor.gestor_ejemplos import EjemploCodigo  # Importa la estructura utilizada para representar cada ejemplo disponible.


class CasillaEjemplo(QCheckBox):  # Representa una casilla claramente visible y adaptada al tema oscuro de TecNet Finder.
    TAMANO_INDICADOR = 20.0  # Define el tamaño del cuadro que representa visualmente el estado de selección.

    def __init__(self, padre=None):  # Inicializa una casilla sin texto y preparada para dibujarse manualmente.
        super().__init__(padre)  # Inicializa el comportamiento convencional de QCheckBox.
        self.setText("")  # Evita mostrar cualquier texto junto al indicador.
        self.setFixedSize(30, 30)  # Reserva un área suficientemente grande para poder pulsarla cómodamente.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica visualmente que la casilla puede activarse.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite utilizar también el teclado para cambiar su estado.

    def sizeHint(self) -> QSize:  # Informa a Qt el tamaño recomendado para colocar la casilla dentro de la tabla.
        return QSize(30, 30)  # Mantiene el control suficientemente grande sin desperdiciar espacio.

    def hitButton(self, posicion) -> bool:  # Define toda el área del control como una zona válida para hacer clic.
        return self.rect().contains(posicion)  # Permite activar la casilla pulsando cualquier punto dentro de sus 30 x 30 píxeles.

    def paintEvent(self, _evento) -> None:  # Dibuja manualmente el indicador para garantizar contraste y centrado.
        pintor = QPainter(self)  # Crea el pintor que trabajará dentro del área de la casilla.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza bordes y líneas del indicador.

        izquierda = (self.width() - self.TAMANO_INDICADOR) / 2.0  # Calcula la posición horizontal necesaria para centrar el cuadro.
        superior = (self.height() - self.TAMANO_INDICADOR) / 2.0  # Calcula la posición vertical necesaria para centrar el cuadro.
        rectangulo = QRectF(izquierda, superior, self.TAMANO_INDICADOR, self.TAMANO_INDICADOR)  # Construye el área exacta del indicador.

        if self.isChecked():  # Comprueba si el ejemplo está actualmente seleccionado.
            fondo = QColor("#89b4fa")  # Utiliza el azul principal para representar claramente el estado activo.
            borde = QColor("#b4befe") if self.underMouse() else QColor("#89b4fa")  # Aclara ligeramente el borde cuando el cursor se encuentra encima.
        else:  # Se ejecuta cuando el ejemplo todavía no se encuentra seleccionado.
            fondo = QColor("#11111b")  # Utiliza el mismo fondo oscuro de las tablas.
            borde = QColor("#b4befe") if self.underMouse() else QColor("#6c7086")  # Mantiene un borde visible incluso cuando la casilla está desactivada.

        lapiz_borde = QPen(borde)  # Crea el lápiz utilizado para delimitar el cuadro.
        lapiz_borde.setWidthF(1.8)  # Hace que el borde sea claramente visible sin resultar demasiado grueso.
        pintor.setPen(lapiz_borde)  # Activa el borde calculado.
        pintor.setBrush(fondo)  # Activa el fondo correspondiente al estado actual.
        pintor.drawRoundedRect(rectangulo, 4.0, 4.0)  # Dibuja el indicador con esquinas ligeramente redondeadas.

        if self.isChecked():  # Comprueba si debe dibujarse la marca interior de selección.
            camino = QPainterPath()  # Crea el recorrido vectorial utilizado para formar la marca.
            camino.moveTo(izquierda + 4.5, superior + 10.5)  # Coloca el comienzo de la primera línea de la marca.
            camino.lineTo(izquierda + 8.5, superior + 14.5)  # Dibuja el tramo corto descendente.
            camino.lineTo(izquierda + 15.5, superior + 6.0)  # Completa la marca mediante el tramo ascendente más largo.

            lapiz_marca = QPen(QColor("#1e1e2e"))  # Utiliza el fondo oscuro para contrastar sobre el azul seleccionado.
            lapiz_marca.setWidthF(2.6)  # Mantiene la marca suficientemente gruesa para distinguirla.
            lapiz_marca.setCapStyle(Qt.PenCapStyle.RoundCap)  # Redondea los extremos de las líneas.
            lapiz_marca.setJoinStyle(Qt.PenJoinStyle.RoundJoin)  # Suaviza la unión central de la marca.
            pintor.setPen(lapiz_marca)  # Activa el lápiz de la marca.
            pintor.setBrush(Qt.BrushStyle.NoBrush)  # Evita utilizar un relleno durante el trazado.
            pintor.drawPath(camino)  # Dibuja finalmente la marca dentro del cuadro.

        if self.hasFocus():  # Comprueba si la casilla fue seleccionada mediante navegación de teclado.
            rectangulo_foco = rectangulo.adjusted(-3.0, -3.0, 3.0, 3.0)  # Construye un marco ligeramente mayor alrededor del indicador.
            lapiz_foco = QPen(QColor("#89b4fa"))  # Utiliza el azul principal para representar el foco.
            lapiz_foco.setStyle(Qt.PenStyle.DotLine)  # Utiliza una línea punteada discreta.
            pintor.setPen(lapiz_foco)  # Activa el lápiz correspondiente.
            pintor.setBrush(Qt.BrushStyle.NoBrush)  # Evita alterar el fondo dibujado anteriormente.
            pintor.drawRoundedRect(rectangulo_foco, 5.0, 5.0)  # Dibuja el marco de navegación por teclado.

    def enterEvent(self, evento) -> None:  # Actualiza el control cuando el cursor entra en su área.
        super().enterEvent(evento)  # Conserva el comportamiento convencional de QCheckBox.
        self.update()  # Solicita un redibujado para mostrar el estado hover.

    def leaveEvent(self, evento) -> None:  # Actualiza el control cuando el cursor abandona su área.
        super().leaveEvent(evento)  # Conserva el comportamiento convencional de QCheckBox.
        self.update()  # Solicita un redibujado para recuperar el borde normal.

    def nextCheckState(self) -> None:  # Cambia el estado y garantiza que la representación personalizada se actualice inmediatamente.
        super().nextCheckState()  # Permite que QCheckBox realice normalmente el cambio entre marcado y desmarcado.
        self.update()  # Redibuja inmediatamente el indicador con su nuevo estado.


class TablaEjemplos(QTableWidget):  # Mantiene las columnas proporcionalmente distribuidas y las filas adaptadas a todo su contenido.
    def __init__(self, filas: int, proporciones: list[float], padre=None):  # Recibe las filas iniciales y el peso relativo de las cuatro columnas.
        super().__init__(filas, 4, padre)  # Inicializa la tabla con las cuatro columnas utilizadas por el selector.
        self.proporciones_columnas = proporciones  # Conserva la distribución que deberá mantenerse al cambiar de tamaño.

    def resizeEvent(self, evento) -> None:  # Redistribuye la tabla cuando cambia el ancho disponible.
        super().resizeEvent(evento)  # Permite que Qt procese primero el cambio general.
        self._distribuir_columnas()  # Recalcula inmediatamente los anchos proporcionales.
        QTimer.singleShot(0, self._ajustar_filas)  # Espera a que cambien las columnas antes de recalcular los saltos de línea.

    def showEvent(self, evento) -> None:  # Ajusta la tabla cuando se muestra por primera vez.
        super().showEvent(evento)  # Permite que Qt complete primero su visualización.
        self._distribuir_columnas()  # Reparte el espacio utilizando el ancho real disponible.
        QTimer.singleShot(0, self._ajustar_filas)  # Recalcula después la altura necesaria para cada ejemplo.

    def _distribuir_columnas(self) -> None:  # Asigna el ancho disponible utilizando las proporciones visuales definidas.
        if len(self.proporciones_columnas) != self.columnCount():  # Comprueba que exista un peso por cada columna.
            return  # Evita realizar una distribución incompleta.

        ancho_disponible = max(self.viewport().width() - 2, 1)  # Obtiene únicamente el espacio donde pueden mostrarse las celdas.
        suma = sum(self.proporciones_columnas)  # Calcula el peso total utilizado como referencia.

        if suma <= 0:  # Comprueba que las proporciones puedan utilizarse correctamente.
            return  # Evita divisiones inválidas.

        anchos: list[int] = []  # Conserva temporalmente los anchos calculados para las primeras columnas.

        for proporcion in self.proporciones_columnas[:-1]:  # Recorre todas las columnas excepto la última.
            ancho = int(ancho_disponible * proporcion / suma)  # Convierte la proporción en píxeles reales.
            anchos.append(ancho)  # Guarda el resultado para aplicarlo posteriormente.

        anchos.append(ancho_disponible - sum(anchos))  # Entrega a la última columna solamente el espacio restante por redondeo.

        for columna, ancho in enumerate(anchos):  # Recorre todos los tamaños finalmente calculados.
            self.setColumnWidth(columna, ancho)  # Aplica el ancho correspondiente a cada columna.

    def _ajustar_filas(self) -> None:  # Recalcula la altura necesaria para mostrar completamente todos los textos.
        self.resizeRowsToContents()  # Permite que cada fila crezca según la cantidad real de líneas que contiene.

        for fila in range(self.rowCount()):  # Recorre todas las filas después del cálculo automático.
            self.setRowHeight(fila, max(self.rowHeight(fila) + 10, 52))  # Agrega espacio interior y garantiza una altura mínima cómoda.


class SelectorEjemplos(QDialog):  # Representa la ventana modal utilizada para elegir ejemplos válidos o inválidos.
    def __init__(self, ejemplos_validos: list[EjemploCodigo], ejemplos_invalidos: list[EjemploCodigo], padre=None):  # Recibe las dos categorías ya interpretadas por Motor.
        super().__init__(padre)  # Inicializa el diálogo utilizando la ventana principal como propietaria.
        self.casillas: list[tuple[CasillaEjemplo, EjemploCodigo]] = []  # Relaciona cada control visual con el ejemplo que representa.
        self.seleccion_final: list[EjemploCodigo] = []  # Conserva los casos aceptados cuando el usuario confirma la inserción.

        self.setWindowTitle("Selector de ejemplos")  # Conserva el nombre utilizado por la herramienta original.
        self.setModal(True)  # Evita interactuar con el editor mientras el selector se encuentra abierto.
        self.resize(1220, 660)  # Proporciona más espacio vertical y horizontal para mostrar correctamente los casos extensos.
        self.setMinimumSize(950, 500)  # Evita dimensiones donde los textos volverían a resultar ilegibles.

        diseno = QVBoxLayout(self)  # Organiza información, pestañas y acciones dentro del diálogo.
        diseno.setContentsMargins(12, 12, 12, 12)  # Mantiene una separación uniforme respecto a los bordes.
        diseno.setSpacing(10)  # Separa visualmente las diferentes regiones del selector.

        informacion = QLabel("Selecciona uno o varios ejemplos y presiona Insertar seleccionados.")  # Explica brevemente la acción principal de la ventana.
        informacion.setObjectName("TituloSeccion")  # Reutiliza el estilo de encabezado existente en TecNet Finder.
        diseno.addWidget(informacion)  # Coloca la instrucción encima de las pestañas.

        aviso = QLabel("Los archivos conservan casos preparados para fases posteriores de LyAII. En este momento el selector únicamente inserta el código; no evalúa todavía las expectativas semánticas, advertencias, optimización o código generado.")  # Evita presentar como implementadas fases correspondientes a unidades posteriores.
        aviso.setObjectName("SubtituloPrincipal")  # Utiliza el estilo secundario del resto de la aplicación.
        aviso.setWordWrap(True)  # Permite adaptar el mensaje cuando la ventana utiliza el ancho mínimo.
        diseno.addWidget(aviso)  # Muestra la aclaración antes de los casos.

        self.pestanas = QTabWidget()  # Crea las pestañas equivalentes a Válidas e Inválidas de la herramienta original.
        diseno.addWidget(self.pestanas, 1)  # Permite que las tablas utilicen la mayor parte de la ventana.

        self._agregar_pestana("Válidas", ejemplos_validos)  # Construye la tabla correspondiente a los casos válidos.
        self._agregar_pestana("Inválidas", ejemplos_invalidos)  # Construye la tabla correspondiente a los casos incorrectos.

        acciones = QHBoxLayout()  # Crea la fila inferior utilizada para selección e inserción.
        acciones.setSpacing(10)  # Mantiene una separación uniforme entre los botones.
        diseno.addLayout(acciones)  # Coloca la barra inmediatamente debajo de las tablas.

        boton_seleccionar = QPushButton("Seleccionar todo")  # Crea la acción utilizada para marcar todos los casos disponibles.
        boton_seleccionar.clicked.connect(lambda: self._establecer_todos(True))  # Marca simultáneamente ambas pestañas.
        acciones.addWidget(boton_seleccionar)  # Coloca la acción en el lado izquierdo.

        boton_quitar = QPushButton("Quitar selección")  # Crea la acción utilizada para limpiar todos los checks.
        boton_quitar.clicked.connect(lambda: self._establecer_todos(False))  # Desmarca simultáneamente ambas categorías.
        acciones.addWidget(boton_quitar)  # Coloca la acción junto al botón de selección completa.

        acciones.addStretch()  # Empuja las acciones finales hacia el extremo derecho.

        boton_cerrar = QPushButton("Cerrar")  # Crea la acción que abandona el selector sin modificar el editor.
        boton_cerrar.clicked.connect(self.reject)  # Cierra el diálogo utilizando el estado rechazado.
        acciones.addWidget(boton_cerrar)  # Coloca Cerrar antes de la acción principal.

        boton_insertar = QPushButton("Insertar seleccionados")  # Crea la acción principal utilizada para devolver los ejemplos elegidos.
        boton_insertar.setObjectName("BotonPrincipal")  # Utiliza el mismo énfasis visual que Compilar.
        boton_insertar.clicked.connect(self._aceptar_seleccion)  # Comprueba la selección antes de aceptar el diálogo.
        acciones.addWidget(boton_insertar)  # Coloca la acción principal en el extremo derecho.

    def _agregar_pestana(self, nombre: str, ejemplos: list[EjemploCodigo]) -> None:  # Construye una pestaña completa para una categoría determinada.
        contenedor = QWidget()  # Crea el widget base donde se mostrará la tabla o el mensaje vacío.
        diseno = QVBoxLayout(contenedor)  # Organiza verticalmente el contenido de la categoría.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene un margen pequeño alrededor de la tabla.

        if not ejemplos:  # Comprueba si el archivo correspondiente no produjo ningún caso.
            mensaje = QLabel("No se encontraron ejemplos para esta categoría.")  # Informa claramente que la pestaña no posee registros.
            mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el mensaje dentro del espacio disponible.
            diseno.addWidget(mensaje, 1)  # Permite que el mensaje ocupe la pestaña completa.
            self.pestanas.addTab(contenedor, nombre)  # Conserva la pestaña aunque el archivo se encuentre vacío.
            return  # Finaliza porque no existe ninguna tabla que construir.

        tabla = TablaEjemplos(len(ejemplos), [0.60, 2.40, 3.15, 3.85])  # Distribuye selección, caso, comando y salida usando todo el ancho disponible.
        tabla.setHorizontalHeaderLabels(["Sel.", "Caso", "Comando", "Salida esperada"])  # Define las cuatro columnas utilizadas por el selector.
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente el contenido de los archivos.
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Facilita identificar visualmente el caso señalado.
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Reserva la selección visual para una única vista previa a la vez.
        tabla.setAlternatingRowColors(True)  # Diferencia ligeramente las filas consecutivas.
        tabla.setWordWrap(True)  # Permite dividir automáticamente los textos largos en varias líneas.
        tabla.setTextElideMode(Qt.TextElideMode.ElideNone)  # Impide sustituir información por puntos suspensivos.
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Evita desplazamiento horizontal porque las columnas ya utilizan el ancho disponible.
        tabla.verticalHeader().setVisible(False)  # Oculta la numeración automática que no aporta información al usuario.

        encabezado = tabla.horizontalHeader()  # Obtiene el encabezado utilizado para controlar los anchos.
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Deja que TablaEjemplos controle proporcionalmente todas las columnas.
        encabezado.setStretchLastSection(False)  # Evita que Salida esperada absorba arbitrariamente el espacio sobrante.
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra todos los títulos de las columnas.
        encabezado.setMinimumHeight(42)  # Da un poco más de presencia visual al encabezado.

        for fila, ejemplo in enumerate(ejemplos):  # Recorre todos los casos manteniendo exactamente el orden del archivo.
            contenedor_casilla = QWidget()  # Crea un pequeño contenedor para poder centrar realmente el QCheckBox.
            contenedor_casilla.setStyleSheet("background: transparent;")  # Evita cubrir el fondo alternado propio de la tabla.
            diseno_casilla = QHBoxLayout(contenedor_casilla)  # Organiza horizontalmente el indicador dentro de la celda.
            diseno_casilla.setContentsMargins(0, 0, 0, 0)  # Elimina márgenes que desplazarían el control.
            diseno_casilla.setSpacing(0)  # Evita cualquier espacio innecesario.
            diseno_casilla.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra la casilla horizontal y verticalmente.

            casilla = CasillaEjemplo()  # Crea el checkbox personalizado claramente visible.
            diseno_casilla.addWidget(casilla)  # Coloca la casilla exactamente en el centro del contenedor.
            tabla.setCellWidget(fila, 0, contenedor_casilla)  # Inserta el control completo dentro de la primera columna.
            self.casillas.append((casilla, ejemplo))  # Conserva la relación para recuperar posteriormente la selección.

            item_titulo = self._crear_item_centrado(ejemplo.titulo)  # Construye la celda del caso mostrando el título completo.
            item_titulo.setToolTip(ejemplo.titulo)  # Conserva también el título íntegro dentro del tooltip.
            tabla.setItem(fila, 1, item_titulo)  # Inserta el nombre dentro de la segunda columna.

            item_comando = self._crear_item_centrado(ejemplo.comando)  # Muestra el comando completo sin recortarlo.
            item_comando.setToolTip(ejemplo.comando)  # Permite consultar igualmente el contenido mediante tooltip.
            tabla.setItem(fila, 2, item_comando)  # Inserta una o varias instrucciones dentro de la tercera columna.

            salida_texto = ejemplo.salida_esperada or "Sin salida esperada registrada."  # Obtiene el resultado esperado o un texto alternativo claro.
            item_salida = self._crear_item_centrado(salida_texto)  # Muestra toda la descripción permitiendo varias líneas.
            item_salida.setToolTip(salida_texto)  # Conserva también el texto completo dentro del tooltip.
            tabla.setItem(fila, 3, item_salida)  # Inserta la descripción en la última columna.

        tabla.cellDoubleClicked.connect(lambda fila, _columna, casos=ejemplos: self._mostrar_vista_previa(casos[fila]))  # Abre una ventana con toda la información al hacer doble clic.
        tabla.resizeRowsToContents()  # Realiza un primer cálculo de las alturas antes de mostrar la pestaña.
        diseno.addWidget(tabla, 1)  # Permite que la tabla utilice toda la pestaña.
        self.pestanas.addTab(contenedor, nombre)  # Agrega finalmente la categoría al selector principal.

    def _crear_item_centrado(self, texto: str) -> QTableWidgetItem:  # Construye una celda textual completamente centrada y preparada para varias líneas.
        item = QTableWidgetItem(texto)  # Crea el elemento utilizando todo el contenido recibido.
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra simultáneamente el texto horizontal y verticalmente.
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)  # Mantiene la celda seleccionable pero no editable.
        return item  # Devuelve el elemento listo para colocarse dentro de cualquier columna textual.

    def _establecer_todos(self, seleccionado: bool) -> None:  # Marca o desmarca todos los ejemplos disponibles.
        for casilla, _ejemplo in self.casillas:  # Recorre todas las casillas reales creadas en ambas categorías.
            casilla.setChecked(seleccionado)  # Aplica directamente el estado solicitado.
            casilla.update()  # Actualiza inmediatamente su representación personalizada.

    def _obtener_seleccionados(self) -> list[EjemploCodigo]:  # Recupera los registros cuyas casillas están marcadas.
        seleccionados: list[EjemploCodigo] = []  # Conserva los ejemplos elegidos respetando el orden original.

        for casilla, ejemplo in self.casillas:  # Recorre cada control junto con el registro que representa.
            if casilla.isChecked():  # Comprueba si el usuario activó la casilla.
                seleccionados.append(ejemplo)  # Conserva el ejemplo completo para insertarlo posteriormente.

        return seleccionados  # Devuelve todos los casos marcados.

    def _aceptar_seleccion(self) -> None:  # Valida que exista al menos un caso antes de cerrar correctamente el selector.
        seleccionados = self._obtener_seleccionados()  # Recupera el estado actual de todas las casillas.

        if not seleccionados:  # Comprueba que el usuario haya elegido alguna entrada.
            QMessageBox.warning(self, "Insertar ejemplos", "Selecciona al menos un ejemplo.")  # Informa el requisito sin cerrar la ventana.
            return  # Mantiene abierto el selector para continuar eligiendo.

        self.seleccion_final = seleccionados  # Conserva definitivamente los ejemplos elegidos.
        self.accept()  # Cierra el diálogo indicando que la selección fue confirmada.

    def obtener_texto_seleccionado(self) -> str:  # Une los comandos elegidos para insertarlos directamente dentro del editor.
        return "\n".join(ejemplo.comando for ejemplo in self.seleccion_final)  # Mantiene juntos los comandos internos y separa distintos casos mediante líneas nuevas.

    def _mostrar_vista_previa(self, ejemplo: EjemploCodigo) -> None:  # Abre una ventana secundaria con el contenido íntegro de un caso.
        vista = QDialog(self)  # Crea un diálogo modal asociado con el selector actual.
        vista.setWindowTitle("Vista previa del ejemplo")  # Conserva el nombre utilizado por la herramienta anterior.
        vista.resize(780, 440)  # Utiliza dimensiones cómodas para comandos y resultados extensos.
        vista.setMinimumSize(620, 360)  # Evita que el contenido se comprima excesivamente.

        diseno = QVBoxLayout(vista)  # Organiza el contenido y el botón de cierre verticalmente.
        diseno.setContentsMargins(10, 10, 10, 10)  # Mantiene una separación uniforme.

        texto = QPlainTextEdit()  # Crea un visor adecuado para preservar saltos de línea del ejemplo.
        texto.setReadOnly(True)  # Evita modificaciones accidentales dentro de la vista previa.
        texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)  # Permite visualizar textos extensos sin desplazamiento horizontal.
        texto.setPlainText(  # Construye la información completa relacionada con el ejemplo.
            f"Tipo: {ejemplo.tipo}\n"
            f"Caso: {ejemplo.titulo}\n\n"
            f"=== COMANDO(S) ===\n"
            f"{ejemplo.comando}\n\n"
            f"=== SALIDA ESPERADA ===\n"
            f"{ejemplo.salida_esperada or 'Sin salida esperada registrada.'}"
        )
        diseno.addWidget(texto, 1)  # Permite que el contenido utilice casi toda la ventana.

        acciones = QHBoxLayout()  # Crea una fila pequeña para cerrar la vista previa.
        acciones.addStretch()  # Empuja la acción hacia la derecha.

        boton_cerrar = QPushButton("Cerrar")  # Crea la única acción necesaria dentro de esta ventana.
        boton_cerrar.clicked.connect(vista.accept)  # Cierra únicamente la vista previa.
        acciones.addWidget(boton_cerrar)  # Coloca el botón al final de la fila.

        diseno.addLayout(acciones)  # Agrega la barra debajo del contenido.
        vista.exec()  # Muestra la vista previa y espera hasta que el usuario la cierre.