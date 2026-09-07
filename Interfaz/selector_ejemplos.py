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
# varios casos, probarlos automáticamente, consultar una vista
# previa e insertar posteriormente los comandos elegidos.
# ============================================================

from pathlib import Path  # Importa Path para localizar los recursos gráficos utilizados por las acciones del selector.

from PySide6.QtCore import QRectF, QSize, Qt, QTimer  # Importa geometría, tamaños, alineaciones, estados y temporización de la interfaz.
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen  # Importa herramientas para dibujar casillas y cargar iconos.
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Importa los componentes necesarios para construir el selector.

from Interfaz.reporte_pruebas_ejemplos import VentanaReportePruebas  # Importa la ventana encargada de mostrar los resultados automáticos.
from Motor.gestor_ejemplos import EjemploCodigo  # Importa la estructura utilizada para representar cada ejemplo disponible.
from Motor.pruebas_ejemplos import EjecutorPruebasEjemplos  # Importa el ejecutor independiente que utiliza el flujo real del compilador.


class CasillaEjemplo(QCheckBox):  # Representa una casilla claramente visible y adaptada al tema oscuro de TecNet Finder.
    TAMANO_INDICADOR = 20.0  # Define el tamaño del cuadro que representa visualmente el estado de selección.

    def __init__(self, padre=None):
        super().__init__(padre)
        self.setText("")
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(30, 30)

    def hitButton(self, posicion) -> bool:
        return self.rect().contains(posicion)

    def paintEvent(self, _evento) -> None:
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        izquierda = (self.width() - self.TAMANO_INDICADOR) / 2.0
        superior = (self.height() - self.TAMANO_INDICADOR) / 2.0
        rectangulo = QRectF(izquierda, superior, self.TAMANO_INDICADOR, self.TAMANO_INDICADOR)

        if self.isChecked():
            fondo = QColor("#89b4fa")
            borde = QColor("#b4befe") if self.underMouse() else QColor("#89b4fa")
        else:
            fondo = QColor("#11111b")
            borde = QColor("#b4befe") if self.underMouse() else QColor("#6c7086")

        lapiz_borde = QPen(borde)
        lapiz_borde.setWidthF(1.8)
        pintor.setPen(lapiz_borde)
        pintor.setBrush(fondo)
        pintor.drawRoundedRect(rectangulo, 4.0, 4.0)

        if self.isChecked():
            camino = QPainterPath()
            camino.moveTo(izquierda + 4.5, superior + 10.5)
            camino.lineTo(izquierda + 8.5, superior + 14.5)
            camino.lineTo(izquierda + 15.5, superior + 6.0)

            lapiz_marca = QPen(QColor("#1e1e2e"))
            lapiz_marca.setWidthF(2.6)
            lapiz_marca.setCapStyle(Qt.PenCapStyle.RoundCap)
            lapiz_marca.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pintor.setPen(lapiz_marca)
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawPath(camino)

        if self.hasFocus():
            rectangulo_foco = rectangulo.adjusted(-3.0, -3.0, 3.0, 3.0)
            lapiz_foco = QPen(QColor("#89b4fa"))
            lapiz_foco.setStyle(Qt.PenStyle.DotLine)
            pintor.setPen(lapiz_foco)
            pintor.setBrush(Qt.BrushStyle.NoBrush)
            pintor.drawRoundedRect(rectangulo_foco, 5.0, 5.0)

    def enterEvent(self, evento) -> None:
        super().enterEvent(evento)
        self.update()

    def leaveEvent(self, evento) -> None:
        super().leaveEvent(evento)
        self.update()

    def nextCheckState(self) -> None:
        super().nextCheckState()
        self.update()


class TablaEjemplos(QTableWidget):  # Mantiene las columnas proporcionalmente distribuidas y las filas adaptadas a todo su contenido.
    def __init__(self, filas: int, proporciones: list[float], padre=None):
        super().__init__(filas, 4, padre)
        self.proporciones_columnas = proporciones

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._distribuir_columnas()
        QTimer.singleShot(0, self._ajustar_filas)

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._distribuir_columnas()
        QTimer.singleShot(0, self._ajustar_filas)

    def _distribuir_columnas(self) -> None:
        if len(self.proporciones_columnas) != self.columnCount():
            return

        ancho_disponible = max(self.viewport().width() - 2, 1)
        suma = sum(self.proporciones_columnas)

        if suma <= 0:
            return

        anchos: list[int] = []

        for proporcion in self.proporciones_columnas[:-1]:
            anchos.append(int(ancho_disponible * proporcion / suma))

        anchos.append(ancho_disponible - sum(anchos))

        for columna, ancho in enumerate(anchos):
            self.setColumnWidth(columna, ancho)

    def _ajustar_filas(self) -> None:
        self.resizeRowsToContents()

        for fila in range(self.rowCount()):
            self.setRowHeight(fila, max(self.rowHeight(fila) + 10, 52))


class SelectorEjemplos(QDialog):
    def __init__(self, ejemplos_validos: list[EjemploCodigo], ejemplos_invalidos: list[EjemploCodigo], padre=None):
        super().__init__(padre)
        self.ejemplos_validos = list(ejemplos_validos)
        self.ejemplos_invalidos = list(ejemplos_invalidos)
        self.casillas: list[tuple[CasillaEjemplo, EjemploCodigo]] = []
        self.seleccion_final: list[EjemploCodigo] = []
        self.ejecutor_pruebas = EjecutorPruebasEjemplos()
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"

        self.setWindowTitle("Selector de ejemplos")
        self.setModal(True)
        self.resize(1220, 660)
        self.setMinimumSize(950, 500)

        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(12, 12, 12, 12)
        diseno.setSpacing(10)

        informacion = QLabel("Selecciona uno o varios ejemplos para insertarlos o probarlos automáticamente.")
        informacion.setObjectName("TituloSeccion")
        diseno.addWidget(informacion)

        aviso = QLabel(
            "Las pruebas automáticas evalúan análisis léxico, sintáctico y las "
            "advertencias no semánticas ya recuperadas. Los códigos SEM y ADV-005 "
            "permanecen pendientes hasta comenzar las fases correspondientes."
        )
        aviso.setObjectName("SubtituloPrincipal")
        aviso.setWordWrap(True)
        diseno.addWidget(aviso)

        self.pestanas = QTabWidget()
        diseno.addWidget(self.pestanas, 1)

        self._agregar_pestana("Válidas", self.ejemplos_validos)
        self._agregar_pestana("Inválidas", self.ejemplos_invalidos)

        acciones = QHBoxLayout()
        acciones.setSpacing(10)
        diseno.addLayout(acciones)

        boton_seleccionar = QPushButton("Seleccionar todo")
        boton_seleccionar.clicked.connect(lambda: self._establecer_todos(True))
        acciones.addWidget(boton_seleccionar)

        boton_quitar = QPushButton("Quitar selección")
        boton_quitar.clicked.connect(lambda: self._establecer_todos(False))
        acciones.addWidget(boton_quitar)

        boton_probar_seleccionados = QPushButton("Probar seleccionados")
        boton_probar_seleccionados.setToolTip("Ejecutar únicamente los ejemplos marcados")
        self._aplicar_icono(boton_probar_seleccionados, "Pruebas.png")
        boton_probar_seleccionados.clicked.connect(self._probar_seleccionados)
        acciones.addWidget(boton_probar_seleccionados)

        boton_probar_todos = QPushButton("Probar todos")
        boton_probar_todos.setToolTip("Ejecutar todos los ejemplos disponibles")
        self._aplicar_icono(boton_probar_todos, "Pruebas.png")
        boton_probar_todos.clicked.connect(self._probar_todos)
        acciones.addWidget(boton_probar_todos)

        acciones.addStretch()

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(self.reject)
        acciones.addWidget(boton_cerrar)

        boton_insertar = QPushButton("Insertar seleccionados")
        boton_insertar.setObjectName("BotonPrincipal")
        boton_insertar.clicked.connect(self._aceptar_seleccion)
        acciones.addWidget(boton_insertar)

    def _aplicar_icono(self, boton: QPushButton, nombre_archivo: str) -> None:
        ruta = self.ruta_iconos / nombre_archivo

        if not ruta.exists():
            return

        boton.setIcon(QIcon(str(ruta)))
        boton.setIconSize(QSize(18, 18))

    def _agregar_pestana(self, nombre: str, ejemplos: list[EjemploCodigo]) -> None:
        contenedor = QWidget()
        diseno = QVBoxLayout(contenedor)
        diseno.setContentsMargins(6, 6, 6, 6)

        if not ejemplos:
            mensaje = QLabel("No se encontraron ejemplos para esta categoría.")
            mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
            diseno.addWidget(mensaje, 1)
            self.pestanas.addTab(contenedor, nombre)
            return

        tabla = TablaEjemplos(len(ejemplos), [0.60, 2.40, 3.15, 3.85])
        tabla.setHorizontalHeaderLabels(["Sel.", "Caso", "Comando", "Salida esperada"])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.setWordWrap(True)
        tabla.setTextElideMode(Qt.TextElideMode.ElideNone)
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tabla.verticalHeader().setVisible(False)

        encabezado = tabla.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        encabezado.setStretchLastSection(False)
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        encabezado.setMinimumHeight(42)

        for fila, ejemplo in enumerate(ejemplos):
            contenedor_casilla = QWidget()
            contenedor_casilla.setStyleSheet("background: transparent;")
            diseno_casilla = QHBoxLayout(contenedor_casilla)
            diseno_casilla.setContentsMargins(0, 0, 0, 0)
            diseno_casilla.setSpacing(0)
            diseno_casilla.setAlignment(Qt.AlignmentFlag.AlignCenter)

            casilla = CasillaEjemplo()
            diseno_casilla.addWidget(casilla)
            tabla.setCellWidget(fila, 0, contenedor_casilla)
            self.casillas.append((casilla, ejemplo))

            item_titulo = self._crear_item_centrado(ejemplo.titulo)
            item_titulo.setToolTip(ejemplo.titulo)
            tabla.setItem(fila, 1, item_titulo)

            item_comando = self._crear_item_centrado(ejemplo.comando)
            item_comando.setToolTip(ejemplo.comando)
            tabla.setItem(fila, 2, item_comando)

            salida_texto = ejemplo.salida_esperada or "Sin salida esperada registrada."
            item_salida = self._crear_item_centrado(salida_texto)
            item_salida.setToolTip(salida_texto)
            tabla.setItem(fila, 3, item_salida)

        tabla.cellDoubleClicked.connect(
            lambda fila, _columna, casos=ejemplos: self._mostrar_vista_previa(casos[fila])
        )
        tabla.resizeRowsToContents()
        diseno.addWidget(tabla, 1)
        self.pestanas.addTab(contenedor, nombre)

    def _crear_item_centrado(self, texto: str) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def _establecer_todos(self, seleccionado: bool) -> None:
        for casilla, _ejemplo in self.casillas:
            casilla.setChecked(seleccionado)
            casilla.update()

    def _obtener_seleccionados(self) -> list[EjemploCodigo]:
        seleccionados: list[EjemploCodigo] = []

        for casilla, ejemplo in self.casillas:
            if casilla.isChecked():
                seleccionados.append(ejemplo)

        return seleccionados

    def _probar_seleccionados(self) -> None:
        seleccionados = self._obtener_seleccionados()

        if not seleccionados:
            QMessageBox.warning(self, "Pruebas automáticas", "Selecciona al menos un ejemplo para probar.")
            return

        self._ejecutar_pruebas(seleccionados)

    def _probar_todos(self) -> None:
        ejemplos = [*self.ejemplos_validos, *self.ejemplos_invalidos]

        if not ejemplos:
            QMessageBox.warning(self, "Pruebas automáticas", "No hay ejemplos disponibles para probar.")
            return

        self._ejecutar_pruebas(ejemplos)

    def _ejecutar_pruebas(self, ejemplos: list[EjemploCodigo]) -> None:
        resumen = self.ejecutor_pruebas.ejecutar(ejemplos)
        ventana_reporte = VentanaReportePruebas(resumen, self)
        ventana_reporte.exec()

    def _aceptar_seleccion(self) -> None:
        seleccionados = self._obtener_seleccionados()

        if not seleccionados:
            QMessageBox.warning(self, "Insertar ejemplos", "Selecciona al menos un ejemplo.")
            return

        self.seleccion_final = seleccionados
        self.accept()

    def obtener_texto_seleccionado(self) -> str:
        return "\n".join(ejemplo.comando for ejemplo in self.seleccion_final)

    def _mostrar_vista_previa(self, ejemplo: EjemploCodigo) -> None:
        vista = QDialog(self)
        vista.setWindowTitle("Vista previa del ejemplo")
        vista.resize(780, 440)
        vista.setMinimumSize(620, 360)

        diseno = QVBoxLayout(vista)
        diseno.setContentsMargins(10, 10, 10, 10)

        texto = QPlainTextEdit()
        texto.setReadOnly(True)
        texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        texto.setPlainText(
            f"Tipo: {ejemplo.tipo}\n"
            f"Caso: {ejemplo.titulo}\n\n"
            f"=== COMANDO(S) ===\n"
            f"{ejemplo.comando}\n\n"
            f"=== SALIDA ESPERADA ===\n"
            f"{ejemplo.salida_esperada or 'Sin salida esperada registrada.'}"
        )
        diseno.addWidget(texto, 1)

        acciones = QHBoxLayout()
        acciones.addStretch()

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(vista.accept)
        acciones.addWidget(boton_cerrar)

        diseno.addLayout(acciones)
        vista.exec()