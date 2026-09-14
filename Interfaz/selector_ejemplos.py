# ============================================================
# Archivo: selector_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la ventana utilizada para consultar y
# seleccionar los ejemplos almacenados por TecNet Finder.
#
# Separa entradas válidas e inválidas, permite marcar varios
# casos, ejecutarlos automáticamente, consultar una vista previa
# e insertar posteriormente los comandos elegidos en el editor.
#
# Las pruebas utilizan el mismo FlujoCompilacion que la
# aplicación, por lo que comprueban las fases y advertencias
# disponibles actualmente.
# ============================================================

from pathlib import Path  # Permite localizar los recursos gráficos utilizados por las acciones del selector.

from PySide6.QtCore import QRectF, QSize, Qt, QTimer  # Proporciona geometría, tamaños, estados, alineaciones y temporización de la interfaz.
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen  # Proporciona herramientas para dibujar la casilla personalizada y cargar iconos.
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Proporciona los controles necesarios para construir el selector.

from Interfaz.reporte_pruebas_ejemplos import VentanaReportePruebas  # Proporciona la ventana encargada de presentar los resultados automáticos.
from Motor.gestor_ejemplos import EjemploCodigo  # Proporciona la estructura utilizada para representar cada caso disponible.
from Motor.pruebas_ejemplos import EjecutorPruebasEjemplos  # Ejecuta los ejemplos mediante el mismo flujo real del compilador.


class CasillaEjemplo(QCheckBox):  # Representa una casilla personalizada claramente visible dentro de las tablas del tema oscuro.
    TAMANO_INDICADOR = 20.0  # Define el tamaño del cuadro visual utilizado para representar la selección.

    def __init__(self, padre=None):  # Inicializa una casilla sin texto preparada exclusivamente para la columna Sel.
        super().__init__(padre)  # Inicializa el comportamiento estándar heredado desde QCheckBox.
        self.setText("")  # Elimina cualquier texto porque la propia tabla ya identifica el significado de la columna.
        self.setFixedSize(30, 30)  # Reserva suficiente espacio alrededor del indicador personalizado.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que toda la superficie puede pulsarse.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite también seleccionar la casilla utilizando navegación por teclado.

    def sizeHint(self) -> QSize:  # Informa a Qt el tamaño ideal que debe reservar para esta casilla.
        return QSize(30, 30)  # Mantiene el mismo tamaño utilizado explícitamente por el control.

    def hitButton(self, posicion) -> bool:  # Amplía la zona pulsable a toda la superficie de la casilla.
        return self.rect().contains(posicion)  # Considera válido cualquier clic situado dentro de sus límites.

    def paintEvent(self, _evento) -> None:  # Dibuja manualmente cuadro, marca y estado de foco utilizando los colores de TecNet Finder.
        pintor = QPainter(self)  # Crea el pintor encargado de dibujar directamente sobre la casilla.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza bordes y trazos para obtener una representación limpia.

        izquierda = (self.width() - self.TAMANO_INDICADOR) / 2.0  # Calcula la posición horizontal que centra el indicador.
        superior = (self.height() - self.TAMANO_INDICADOR) / 2.0  # Calcula la posición vertical que centra el indicador.
        rectangulo = QRectF(izquierda, superior, self.TAMANO_INDICADOR, self.TAMANO_INDICADOR)  # Define la superficie exacta del cuadro visible.

        if self.isChecked():  # Comprueba si el ejemplo se encuentra actualmente seleccionado.
            fondo = QColor("#89b4fa")  # Utiliza azul como fondo para distinguir claramente una selección activa.
            borde = QColor("#b4befe") if self.underMouse() else QColor("#89b4fa")  # Aclara ligeramente el borde cuando el cursor está encima.
        else:  # Atiende la representación correspondiente con un ejemplo todavía no seleccionado.
            fondo = QColor("#11111b")  # Utiliza el mismo fondo oscuro de otros controles de TecNet Finder.
            borde = QColor("#b4befe") if self.underMouse() else QColor("#6c7086")  # Resalta el borde al pasar el cursor sin marcar la casilla.

        lapiz_borde = QPen(borde)  # Crea el trazo utilizado para dibujar el contorno del indicador.
        lapiz_borde.setWidthF(1.8)  # Mantiene un grosor visible sin hacerlo excesivo.
        pintor.setPen(lapiz_borde)  # Aplica el borde seleccionado al pintor.
        pintor.setBrush(fondo)  # Aplica el fondo correspondiente con el estado actual.
        pintor.drawRoundedRect(rectangulo, 4.0, 4.0)  # Dibuja el cuadro principal utilizando esquinas ligeramente redondeadas.

        if self.isChecked():  # Comprueba si además debe mostrarse la marca de verificación.
            camino = QPainterPath()  # Crea la ruta gráfica que formará la marca.
            camino.moveTo(izquierda + 4.5, superior + 10.5)  # Sitúa el primer punto del trazo.
            camino.lineTo(izquierda + 8.5, superior + 14.5)  # Dibuja la sección descendente de la marca.
            camino.lineTo(izquierda + 15.5, superior + 6.0)  # Completa la sección ascendente del símbolo.

            lapiz_marca = QPen(QColor("#1e1e2e"))  # Utiliza un tono oscuro para contrastar con el fondo azul.
            lapiz_marca.setWidthF(2.6)  # Da suficiente grosor a la marca para mantenerla visible.
            lapiz_marca.setCapStyle(Qt.PenCapStyle.RoundCap)  # Redondea los extremos del trazo.
            lapiz_marca.setJoinStyle(Qt.PenJoinStyle.RoundJoin)  # Suaviza la unión entre ambos segmentos.
            pintor.setPen(lapiz_marca)  # Aplica el lápiz preparado.
            pintor.setBrush(Qt.BrushStyle.NoBrush)  # Evita rellenar el interior de la ruta.
            pintor.drawPath(camino)  # Dibuja finalmente la marca de selección.

        if self.hasFocus():  # Comprueba si la navegación por teclado dejó el foco sobre esta casilla.
            rectangulo_foco = rectangulo.adjusted(-3.0, -3.0, 3.0, 3.0)  # Amplía ligeramente la zona alrededor del indicador.
            lapiz_foco = QPen(QColor("#89b4fa"))  # Utiliza el color principal para representar el foco.
            lapiz_foco.setStyle(Qt.PenStyle.DotLine)  # Diferencia el foco mediante una línea punteada.
            pintor.setPen(lapiz_foco)  # Aplica el trazo preparado.
            pintor.setBrush(Qt.BrushStyle.NoBrush)  # Evita rellenar el rectángulo exterior.
            pintor.drawRoundedRect(rectangulo_foco, 5.0, 5.0)  # Dibuja el indicador adicional alrededor de la casilla.

    def enterEvent(self, evento) -> None:  # Atiende la entrada del cursor para actualizar inmediatamente el borde de hover.
        super().enterEvent(evento)  # Conserva el comportamiento estándar de QCheckBox.
        self.update()  # Solicita redibujar la casilla utilizando ahora el color correspondiente con hover.

    def leaveEvent(self, evento) -> None:  # Atiende la salida del cursor para recuperar el borde normal.
        super().leaveEvent(evento)  # Conserva el comportamiento estándar del control.
        self.update()  # Solicita nuevamente su representación sin el resaltado de hover.

    def nextCheckState(self) -> None:  # Atiende cualquier cambio de selección realizado mediante clic o teclado.
        super().nextCheckState()  # Deja que QCheckBox modifique primero su estado lógico.
        self.update()  # Redibuja inmediatamente cuadro y marca utilizando el nuevo valor.


class TablaEjemplos(QTableWidget):  # Mantiene columnas proporcionales y filas suficientemente altas para mostrar todo el contenido.
    def __init__(self, filas: int, proporciones: list[float], padre=None):  # Recibe la cantidad inicial de filas y la proporción destinada a cada columna.
        super().__init__(filas, 4, padre)  # Inicializa siempre las cuatro columnas Sel., Caso, Comando y Salida esperada.
        self.proporciones_columnas = proporciones  # Conserva las proporciones utilizadas cada vez que cambia el tamaño disponible.

    def resizeEvent(self, evento) -> None:  # Redistribuye automáticamente columnas y filas después de redimensionar la tabla.
        super().resizeEvent(evento)  # Permite primero que Qt aplique normalmente el nuevo tamaño.
        self._distribuir_columnas()  # Recalcula el ancho de las cuatro columnas utilizando el nuevo espacio.
        QTimer.singleShot(0, self._ajustar_filas)  # Ajusta las alturas después de que Qt termine su ciclo actual de diseño.

    def showEvent(self, evento) -> None:  # Prepara la distribución correcta la primera vez que la tabla aparece en pantalla.
        super().showEvent(evento)  # Conserva el evento estándar de visualización.
        self._distribuir_columnas()  # Calcula los anchos utilizando el viewport ya disponible.
        QTimer.singleShot(0, self._ajustar_filas)  # Espera al siguiente ciclo para medir correctamente el contenido visible.

    def _distribuir_columnas(self) -> None:  # Convierte las proporciones definidas en anchos reales según el espacio disponible.
        if len(self.proporciones_columnas) != self.columnCount():  # Comprueba que exista exactamente una proporción para cada columna.
            return  # Evita distribuir incorrectamente una configuración incompleta.

        ancho_disponible = max(self.viewport().width() - 2, 1)  # Obtiene el ancho interior evitando cualquier valor nulo o negativo.
        suma = sum(self.proporciones_columnas)  # Calcula la suma que servirá como base para normalizar las proporciones.

        if suma <= 0:  # Comprueba defensivamente que exista una distribución matemáticamente válida.
            return  # Conserva los anchos actuales cuando las proporciones no pueden utilizarse.

        anchos: list[int] = []  # Reunirá los anchos enteros calculados para cada columna excepto la última.

        for proporcion in self.proporciones_columnas[:-1]:  # Recorre todas las proporciones excepto la última para evitar errores de redondeo acumulados.
            anchos.append(int(ancho_disponible * proporcion / suma))  # Convierte la proporción actual en píxeles disponibles.

        anchos.append(ancho_disponible - sum(anchos))  # Entrega a la última columna exactamente el espacio restante.

        for columna, ancho in enumerate(anchos):  # Recorre cada ancho calculado junto con el índice correspondiente.
            self.setColumnWidth(columna, ancho)  # Aplica físicamente la medida a la tabla.

    def _ajustar_filas(self) -> None:  # Ajusta las alturas para que comandos y salidas largas sigan siendo legibles.
        self.resizeRowsToContents()  # Solicita primero a Qt medir automáticamente el contenido de cada fila.

        for fila in range(self.rowCount()):  # Recorre todas las filas después de la medición automática.
            self.setRowHeight(fila, max(self.rowHeight(fila) + 10, 52))  # Añade espacio interior y conserva un mínimo cómodo de 52 píxeles.


class SelectorEjemplos(QDialog):  # Permite consultar, probar e insertar uno o varios ejemplos disponibles.
    def __init__(self, ejemplos_validos: list[EjemploCodigo], ejemplos_invalidos: list[EjemploCodigo], padre=None):  # Recibe por separado ambas categorías cargadas por GestorEjemplos.
        super().__init__(padre)  # Inicializa el diálogo utilizando la ventana principal como propietario.
        self.ejemplos_validos = list(ejemplos_validos)  # Conserva una copia independiente de los casos válidos disponibles.
        self.ejemplos_invalidos = list(ejemplos_invalidos)  # Conserva igualmente una copia de los casos inválidos.
        self.casillas: list[tuple[CasillaEjemplo, EjemploCodigo]] = []  # Relaciona cada control visual con el ejemplo que representa.
        self.seleccion_final: list[EjemploCodigo] = []  # Mantendrá únicamente los casos confirmados mediante Insertar seleccionados.
        self.ejecutor_pruebas = EjecutorPruebasEjemplos()  # Prepara el evaluador que utiliza FlujoCompilacion para probar ejemplos.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.

        self.setWindowTitle("Selector de ejemplos")  # Identifica la finalidad del diálogo.
        self.setModal(True)  # Impide editar simultáneamente la ventana principal mientras se seleccionan casos.
        self.resize(1220, 660)  # Proporciona suficiente espacio inicial para cuatro columnas.
        self.setMinimumSize(950, 500)  # Evita tamaños donde comandos y salidas resulten difíciles de consultar.

        diseno = QVBoxLayout(self)  # Organiza información, pestañas y acciones verticalmente.
        diseno.setContentsMargins(12, 12, 12, 12)  # Mantiene márgenes uniformes alrededor del selector.
        diseno.setSpacing(10)  # Conserva una separación consistente entre secciones.

        informacion = QLabel("Selecciona uno o varios ejemplos para insertarlos o probarlos automáticamente.")  # Explica brevemente las dos funciones principales del selector.
        informacion.setObjectName("TituloSeccion")  # Reutiliza el estilo azul de los encabezados.
        diseno.addWidget(informacion)  # Coloca la explicación en la parte superior.

        aviso = QLabel(
            "Las pruebas automáticas utilizan las fases actualmente disponibles del compilador: "
            "análisis léxico, sintáctico y semántico, además de advertencias y cálculo VLSM. "
            "Cada ejemplo se compara con los códigos declarados como esperados."
        )  # Mantiene el aviso sincronizado con el estado actual de Unidad 1.
        aviso.setObjectName("SubtituloPrincipal")  # Utiliza el estilo secundario de información.
        aviso.setWordWrap(True)  # Permite adaptar el texto a la anchura disponible.
        diseno.addWidget(aviso)  # Coloca la aclaración antes de las pestañas.

        self.pestanas = QTabWidget()  # Crea el contenedor que separa entradas válidas e inválidas.
        diseno.addWidget(self.pestanas, 1)  # Permite que las tablas utilicen la mayor parte del espacio.

        self._agregar_pestana("Válidas", self.ejemplos_validos)  # Construye la pestaña con los ejemplos que deberían compilar correctamente.
        self._agregar_pestana("Inválidas", self.ejemplos_invalidos)  # Construye la pestaña con casos diseñados para producir diagnósticos.

        acciones = QHBoxLayout()  # Crea la barra inferior de acciones.
        acciones.setSpacing(10)  # Mantiene una separación uniforme entre botones.
        diseno.addLayout(acciones)  # Incorpora la barra al diseño principal.

        boton_seleccionar = QPushButton("Seleccionar todo")  # Crea la acción que marca simultáneamente todos los casos.
        boton_seleccionar.clicked.connect(lambda: self._establecer_todos(True))  # Conecta la acción con el estado seleccionado.
        acciones.addWidget(boton_seleccionar)  # Coloca el botón al comienzo de la barra.

        boton_quitar = QPushButton("Quitar selección")  # Crea la acción contraria para limpiar todas las casillas.
        boton_quitar.clicked.connect(lambda: self._establecer_todos(False))  # Conecta la acción con el estado desmarcado.
        acciones.addWidget(boton_quitar)  # Coloca la acción inmediatamente después.

        boton_probar_seleccionados = QPushButton("Probar seleccionados")  # Ejecuta solamente los ejemplos que se encuentran marcados.
        boton_probar_seleccionados.setToolTip("Ejecutar únicamente los ejemplos marcados")  # Explica el alcance de la acción.
        self._aplicar_icono(boton_probar_seleccionados, "Pruebas.png")  # Reutiliza el icono preparado para las pruebas automáticas.
        boton_probar_seleccionados.clicked.connect(self._probar_seleccionados)  # Conecta la acción con el evaluador.
        acciones.addWidget(boton_probar_seleccionados)  # Añade el botón a la barra inferior.

        boton_probar_todos = QPushButton("Probar todos")  # Ejecuta conjuntamente todos los ejemplos válidos e inválidos.
        boton_probar_todos.setToolTip("Ejecutar todos los ejemplos disponibles")  # Aclara que la selección actual no afecta esta acción.
        self._aplicar_icono(boton_probar_todos, "Pruebas.png")  # Utiliza el mismo icono de pruebas automáticas.
        boton_probar_todos.clicked.connect(self._probar_todos)  # Conecta el botón con la ejecución global.
        acciones.addWidget(boton_probar_todos)  # Añade la acción a la barra.

        acciones.addStretch()  # Separa las operaciones de selección de los botones de cierre e inserción.

        boton_cerrar = QPushButton("Cerrar")  # Cierra el selector sin insertar ningún ejemplo.
        boton_cerrar.clicked.connect(self.reject)  # Finaliza el diálogo mediante rechazo.
        acciones.addWidget(boton_cerrar)  # Coloca el cierre antes de la acción principal.

        boton_insertar = QPushButton("Insertar seleccionados")  # Confirma las casillas y entrega sus comandos al editor.
        boton_insertar.setObjectName("BotonPrincipal")  # Destaca visualmente la acción principal del selector.
        boton_insertar.clicked.connect(self._aceptar_seleccion)  # Comprueba la selección antes de aceptar el diálogo.
        acciones.addWidget(boton_insertar)  # Coloca la acción principal en el extremo derecho.

    def _aplicar_icono(self, boton: QPushButton, nombre_archivo: str) -> None:  # Aplica un recurso PNG cuando se encuentra disponible.
        ruta = self.ruta_iconos / nombre_archivo  # Construye la ruta completa del icono solicitado.

        if not ruta.exists():  # Comprueba si el recurso está realmente presente.
            return  # Mantiene el botón funcional aunque el archivo gráfico falte.

        boton.setIcon(QIcon(str(ruta)))  # Carga el icono encontrado.
        boton.setIconSize(QSize(18, 18))  # Mantiene un tamaño coherente con otras acciones del programa.

    def _agregar_pestana(self, nombre: str, ejemplos: list[EjemploCodigo]) -> None:  # Construye una tabla completa para una categoría determinada.
        contenedor = QWidget()  # Crea el widget que actuará como contenido de la pestaña.
        diseno = QVBoxLayout(contenedor)  # Organiza verticalmente la tabla o el estado vacío.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene una pequeña separación respecto a los bordes.

        if not ejemplos:  # Comprueba si la categoría actual no contiene ningún caso.
            mensaje = QLabel("No se encontraron ejemplos para esta categoría.")  # Explica por qué la tabla no aparece.
            mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el mensaje dentro del espacio disponible.
            diseno.addWidget(mensaje, 1)  # Permite que el texto utilice toda la pestaña.
            self.pestanas.addTab(contenedor, nombre)  # Agrega igualmente la categoría para conservar la estructura de navegación.
            return  # Finaliza porque no existen filas que construir.

        tabla = TablaEjemplos(len(ejemplos), [0.60, 2.40, 3.15, 3.85])  # Crea una fila por ejemplo y asigna proporciones a las cuatro columnas.
        tabla.setHorizontalHeaderLabels(["Sel.", "Caso", "Comando", "Salida esperada"])  # Identifica claramente el contenido de cada columna.
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente los ejemplos desde la tabla.
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Hace que una selección visual abarque la fila completa.
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Mantiene una sola fila enfocada aunque las casillas permitan marcar varias.
        tabla.setAlternatingRowColors(True)  # Facilita seguir visualmente tablas extensas.
        tabla.setWordWrap(True)  # Permite mostrar comandos y salidas largas en varias líneas.
        tabla.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita sustituir contenido por puntos suspensivos.
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Obliga a distribuir las columnas dentro del ancho disponible.
        tabla.verticalHeader().setVisible(False)  # Oculta los números internos de filas porque cada caso ya posee título.

        encabezado = tabla.horizontalHeader()  # Recupera el encabezado para ajustar su comportamiento.
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Deja la distribución real bajo control de TablaEjemplos.
        encabezado.setStretchLastSection(False)  # Evita que Qt modifique automáticamente la última proporción.
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra visualmente los nombres de las columnas.
        encabezado.setMinimumHeight(42)  # Mantiene una altura suficientemente cómoda para el encabezado.

        for fila, ejemplo in enumerate(ejemplos):  # Recorre cada caso conservando el índice utilizado dentro de la tabla.
            contenedor_casilla = QWidget()  # Crea un pequeño contenedor para centrar correctamente la casilla.
            contenedor_casilla.setStyleSheet("background: transparent;")  # Evita cubrir el color alternado de la fila.
            diseno_casilla = QHBoxLayout(contenedor_casilla)  # Permite centrar horizontalmente el control personalizado.
            diseno_casilla.setContentsMargins(0, 0, 0, 0)  # Elimina márgenes que desplazarían el indicador.
            diseno_casilla.setSpacing(0)  # Evita espacio innecesario dentro de una columna tan estrecha.
            diseno_casilla.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Sitúa la casilla exactamente en el centro de la celda.

            casilla = CasillaEjemplo()  # Crea la casilla correspondiente con el ejemplo actual.
            diseno_casilla.addWidget(casilla)  # Coloca el control dentro del contenedor centrado.
            tabla.setCellWidget(fila, 0, contenedor_casilla)  # Inserta el contenedor completo dentro de la primera columna.
            self.casillas.append((casilla, ejemplo))  # Conserva la relación necesaria para recuperar posteriormente los casos marcados.

            item_titulo = self._crear_item_centrado(ejemplo.titulo)  # Construye la celda que identifica el caso.
            item_titulo.setToolTip(ejemplo.titulo)  # Permite consultar el título completo aunque el ancho disponible sea reducido.
            tabla.setItem(fila, 1, item_titulo)  # Inserta el título dentro de su columna.

            item_comando = self._crear_item_centrado(ejemplo.comando)  # Construye la celda que muestra exactamente la entrada del compilador.
            item_comando.setToolTip(ejemplo.comando)  # Conserva una vista rápida del comando completo.
            tabla.setItem(fila, 2, item_comando)  # Inserta el contenido fuente correspondiente.

            salida_texto = ejemplo.salida_esperada or "Sin salida esperada registrada."  # Utiliza una explicación neutral cuando el archivo no declaró resultado.
            item_salida = self._crear_item_centrado(salida_texto)  # Construye la celda correspondiente con la expectativa.
            item_salida.setToolTip(salida_texto)  # Permite consultar todo el texto mediante tooltip.
            tabla.setItem(fila, 3, item_salida)  # Inserta la salida esperada dentro de la última columna.

        tabla.cellDoubleClicked.connect(lambda fila, _columna, casos=ejemplos: self._mostrar_vista_previa(casos[fila]))  # Abre el detalle completo del ejemplo asociado con la fila pulsada.
        tabla.resizeRowsToContents()  # Realiza un primer ajuste antes de mostrar la tabla.
        diseno.addWidget(tabla, 1)  # Permite que la tabla ocupe todo el espacio restante de la pestaña.
        self.pestanas.addTab(contenedor, nombre)  # Incorpora finalmente la categoría al conjunto visible.

    def _crear_item_centrado(self, texto: str) -> QTableWidgetItem:  # Construye una celda no editable con alineación central.
        item = QTableWidgetItem(texto)  # Crea el elemento utilizando el contenido recibido.
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra tanto horizontal como verticalmente su texto.
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)  # Permite seleccionar la celda pero nunca modificarla.
        return item  # Devuelve el elemento preparado para insertarlo dentro de la tabla.

    def _establecer_todos(self, seleccionado: bool) -> None:  # Marca o desmarca simultáneamente todos los ejemplos disponibles.
        for casilla, _ejemplo in self.casillas:  # Recorre cada control independientemente de su pestaña.
            casilla.setChecked(seleccionado)  # Actualiza el estado lógico solicitado.
            casilla.update()  # Fuerza el redibujado inmediato de la representación personalizada.

    def _obtener_seleccionados(self) -> list[EjemploCodigo]:  # Recupera los objetos correspondientes únicamente con las casillas actualmente activas.
        seleccionados: list[EjemploCodigo] = []  # Prepara la colección que será devuelta respetando el orden original.

        for casilla, ejemplo in self.casillas:  # Recorre todas las asociaciones creadas al construir las pestañas.
            if casilla.isChecked():  # Comprueba si el usuario marcó el caso actual.
                seleccionados.append(ejemplo)  # Conserva el ejemplo asociado sin modificar su contenido.

        return seleccionados  # Devuelve la selección completa en el mismo orden visual de las tablas.

    def _probar_seleccionados(self) -> None:  # Ejecuta únicamente los casos que el usuario marcó manualmente.
        seleccionados = self._obtener_seleccionados()  # Recupera la selección actual de ambas pestañas.

        if not seleccionados:  # Comprueba si se pulsó Probar seleccionados sin marcar ningún caso.
            QMessageBox.warning(self, "Pruebas automáticas", "Selecciona al menos un ejemplo para probar.")  # Informa claramente el requisito antes de continuar.
            return  # Evita abrir un reporte vacío.

        self._ejecutar_pruebas(seleccionados)  # Envía exactamente la selección actual al evaluador automático.

    def _probar_todos(self) -> None:  # Ejecuta todos los ejemplos disponibles independientemente de las casillas.
        ejemplos = [*self.ejemplos_validos, *self.ejemplos_invalidos]  # Une ambas categorías respetando primero válidos y después inválidos.

        if not ejemplos:  # Comprueba defensivamente que realmente exista al menos algún caso cargado.
            QMessageBox.warning(self, "Pruebas automáticas", "No hay ejemplos disponibles para probar.")  # Explica por qué no puede realizarse la operación.
            return  # Evita abrir una ventana de reporte sin resultados.

        self._ejecutar_pruebas(ejemplos)  # Envía toda la colección al evaluador.

    def _ejecutar_pruebas(self, ejemplos: list[EjemploCodigo]) -> None:  # Ejecuta los casos recibidos y muestra sus resultados en una ventana independiente.
        resumen = self.ejecutor_pruebas.ejecutar(ejemplos)  # Procesa cada ejemplo utilizando el flujo real de TecNet Finder.
        ventana_reporte = VentanaReportePruebas(resumen, self)  # Construye la ventana utilizando el resumen ya terminado.
        ventana_reporte.exec()  # Mantiene abierto el reporte hasta que el usuario lo cierre.

    def _aceptar_seleccion(self) -> None:  # Confirma los ejemplos que posteriormente serán insertados dentro del editor.
        seleccionados = self._obtener_seleccionados()  # Recupera las casillas activadas en el momento de pulsar Insertar seleccionados.

        if not seleccionados:  # Comprueba que exista al menos un caso que pueda insertarse.
            QMessageBox.warning(self, "Insertar ejemplos", "Selecciona al menos un ejemplo.")  # Informa el requisito sin cerrar el selector.
            return  # Mantiene la ventana abierta para que el usuario pueda marcar casos.

        self.seleccion_final = seleccionados  # Conserva únicamente la selección confirmada.
        self.accept()  # Cierra el diálogo indicando que existe información válida para insertar.

    def obtener_texto_seleccionado(self) -> str:  # Convierte la selección confirmada en el bloque que recibirá posteriormente el editor.
        return "\n".join(ejemplo.comando for ejemplo in self.seleccion_final)  # Une cada comando mediante saltos de línea conservando el orden elegido.

    def _mostrar_vista_previa(self, ejemplo: EjemploCodigo) -> None:  # Abre el detalle completo del ejemplo seleccionado mediante doble clic.
        vista = QDialog(self)  # Crea una ventana secundaria propiedad del selector.
        vista.setWindowTitle("Vista previa del ejemplo")  # Identifica claramente la finalidad de la ventana.
        vista.resize(780, 440)  # Proporciona suficiente espacio para comandos con varias instrucciones.
        vista.setMinimumSize(620, 360)  # Evita dimensiones demasiado reducidas para leer cómodamente.

        diseno = QVBoxLayout(vista)  # Organiza el contenido y las acciones verticalmente.
        diseno.setContentsMargins(10, 10, 10, 10)  # Mantiene separación uniforme respecto a todos los bordes.

        texto = QPlainTextEdit()  # Crea un visor adecuado para conservar saltos y estructura del ejemplo.
        texto.setReadOnly(True)  # Impide modificar el caso desde esta vista previa.
        texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)  # Adapta líneas largas a la anchura de la ventana.
        texto.setPlainText(
            f"Tipo: {ejemplo.tipo}\n"
            f"Caso: {ejemplo.titulo}\n\n"
            f"=== COMANDO(S) ===\n"
            f"{ejemplo.comando}\n\n"
            f"=== SALIDA ESPERADA ===\n"
            f"{ejemplo.salida_esperada or 'Sin salida esperada registrada.'}"
        )  # Construye una vista legible con metadatos, entrada y expectativa.
        diseno.addWidget(texto, 1)  # Permite que el visor utilice casi todo el espacio disponible.

        acciones = QHBoxLayout()  # Crea una barra inferior para cerrar la vista previa.
        acciones.addStretch()  # Empuja el botón hacia el extremo derecho.

        boton_cerrar = QPushButton("Cerrar")  # Crea la única acción requerida dentro de esta ventana.
        boton_cerrar.clicked.connect(vista.accept)  # Cierra la vista previa sin afectar la selección del diálogo principal.
        acciones.addWidget(boton_cerrar)  # Coloca el botón en la barra inferior.

        diseno.addLayout(acciones)  # Incorpora la barra de acciones debajo del visor.
        vista.exec()  # Mantiene abierta la vista previa hasta que el usuario decida cerrarla.