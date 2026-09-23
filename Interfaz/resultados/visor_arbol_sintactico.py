# ============================================================
# Archivo: visor_arbol_sintactico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene la representación textual y gráfica de los árboles
# sintácticos producidos por TecNet Finder.
#
# Los valores terminales cortos se representan como círculos.
# Los nodos estructurales y valores largos conservan una forma
# ovalada para mantener legibilidad sin deformar el árbol.
#
# La acción Guardar se mantiene como un botón cuadrado
# superpuesto dentro del área gráfica para no consumir espacio
# vertical ni modificar el tamaño disponible para el árbol.
# ============================================================

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QIcon, QImage, QPainter, QPen
from PySide6.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsView, QLabel, QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget

from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro
from Motor.compilacion.modelos import NodoSintactico


class VistaArbol(QGraphicsView):
    MARGEN_BOTON = 8

    def __init__(self, escena: QGraphicsScene, padre=None):
        super().__init__(escena, padre)
        self.boton_superpuesto: QPushButton | None = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def establecer_boton_superpuesto(self, boton: QPushButton) -> None:
        self.boton_superpuesto = boton
        self._posicionar_boton_superpuesto()
        boton.raise_()

    def _posicionar_boton_superpuesto(self) -> None:
        if self.boton_superpuesto is None:
            return

        x = max(
            self.MARGEN_BOTON,
            self.viewport().width()
            - self.boton_superpuesto.width()
            - self.MARGEN_BOTON,
        )
        self.boton_superpuesto.move(x, self.MARGEN_BOTON)
        self.boton_superpuesto.raise_()

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._posicionar_boton_superpuesto()

    def wheelEvent(self, evento) -> None:
        if evento.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if evento.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            evento.accept()
            return

        super().wheelEvent(evento)


class VisorArbolSintactico(QWidget):
    ANCHO_MINIMO_NODO = 120.0
    ALTO_NODO = 52.0
    DIAMETRO_MINIMO_TERMINAL = 58.0
    UMBRAL_TEXTO_CIRCULAR = 62.0
    RELLENO_CIRCULO = 24.0
    ESPACIO_HORIZONTAL = 28.0
    ESPACIO_VERTICAL = 105.0
    MARGEN_ESCENA = 45.0

    def __init__(self, padre=None):
        super().__init__(padre)
        self.escenas: list[QGraphicsScene] = []
        diseno = QVBoxLayout(self)
        diseno.setContentsMargins(0, 0, 0, 0)

        self.pestanas_vista = QTabWidget()
        diseno.addWidget(self.pestanas_vista)

        self.texto_arbol = QPlainTextEdit()
        self.texto_arbol.setReadOnly(True)
        self.texto_arbol.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.contenedor_grafico = QWidget()
        diseno_grafico = QVBoxLayout(self.contenedor_grafico)
        diseno_grafico.setContentsMargins(6, 6, 6, 6)

        ayuda = QLabel("Arrastra para desplazarte · Ctrl + rueda para acercar o alejar")
        ayuda.setObjectName("SubtituloPrincipal")
        diseno_grafico.addWidget(ayuda)

        self.pestanas_arboles = QTabWidget()
        diseno_grafico.addWidget(self.pestanas_arboles, 1)

        self.pestanas_vista.addTab(self.texto_arbol, "Representación textual")
        self.pestanas_vista.addTab(self.contenedor_grafico, "Árbol gráfico")
        self.limpiar()

    def mostrar_arboles(self, arboles: list[NodoSintactico], arbol_textual: str) -> None:
        self.texto_arbol.setPlainText(
            arbol_textual or "No hay árboles válidos para mostrar."
        )
        self._limpiar_arboles_graficos()

        if not arboles:
            self._mostrar_estado_vacio()
            return

        for indice, arbol in enumerate(arboles, start=1):
            self._agregar_arbol(arbol, indice)

    def limpiar(self) -> None:
        self.texto_arbol.setPlainText("No hay árboles válidos para mostrar.")
        self._limpiar_arboles_graficos()
        self._mostrar_estado_vacio()

    def _limpiar_arboles_graficos(self) -> None:
        while self.pestanas_arboles.count() > 0:
            widget = self.pestanas_arboles.widget(0)
            self.pestanas_arboles.removeTab(0)
            widget.deleteLater()

        self.escenas.clear()

    def _mostrar_estado_vacio(self) -> None:
        contenedor = QWidget()
        diseno = QVBoxLayout(contenedor)
        etiqueta = QLabel("No hay árboles sintácticos válidos para mostrar.")
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diseno.addWidget(etiqueta)
        self.pestanas_arboles.addTab(contenedor, "Sin árbol")

    def _agregar_arbol(self, arbol: NodoSintactico, indice: int) -> None:
        contenedor = QWidget()
        diseno = QVBoxLayout(contenedor)
        diseno.setContentsMargins(4, 4, 4, 4)

        escena = QGraphicsScene(self)
        escena.setBackgroundBrush(QBrush(QColor("#181825")))
        self.escenas.append(escena)

        ancho_total = self._ancho_subarbol(arbol)
        self._dibujar_nodo(
            escena,
            arbol,
            self.MARGEN_ESCENA,
            self.MARGEN_ESCENA,
            True,
        )

        limites = escena.itemsBoundingRect().adjusted(
            -self.MARGEN_ESCENA,
            -self.MARGEN_ESCENA,
            self.MARGEN_ESCENA,
            self.MARGEN_ESCENA,
        )
        escena.setSceneRect(limites)

        vista = VistaArbol(escena)
        vista.setMinimumWidth(
            int(min(ancho_total + self.MARGEN_ESCENA * 2, 900))
        )
        diseno.addWidget(vista, 1)

        nombre = self._nombre_arbol(arbol, indice)
        vista.setProperty("nombre_arbol", nombre)

        boton_guardar = QPushButton(vista.viewport())
        boton_guardar.setObjectName("BotonGuardarArbol")
        boton_guardar.setFixedSize(34, 34)
        boton_guardar.setText("")
        boton_guardar.setToolTip("Guardar este árbol sintáctico como imagen PNG")
        boton_guardar.setIconSize(QSize(18, 18))

        ruta_guardar = ruta_icono_oscuro("Guardar.png")
        if ruta_guardar.exists():
            boton_guardar.setIcon(QIcon(str(ruta_guardar)))

        boton_guardar.clicked.connect(
            lambda _marcado=False, e=escena, n=nombre: self._guardar_png(e, n)
        )
        vista.establecer_boton_superpuesto(boton_guardar)
        self.pestanas_arboles.addTab(contenedor, nombre)

    @staticmethod
    def _texto_nodo(nodo: NodoSintactico) -> str:
        if nodo.etiqueta == "VALOR" and nodo.valor is not None:
            return str(nodo.valor)

        if nodo.valor is not None:
            return f"{nodo.etiqueta}\n{nodo.valor}"

        return nodo.etiqueta

    @classmethod
    def _debe_ser_circular(cls, nodo: NodoSintactico, ancho_texto: float) -> bool:
        return (
            not nodo.hijos
            and nodo.etiqueta == "VALOR"
            and nodo.valor is not None
            and ancho_texto <= cls.UMBRAL_TEXTO_CIRCULAR
        )

    def _medidas_texto(self, nodo: NodoSintactico) -> tuple[float, float]:
        fuente = QFont("Consolas", 9)
        metricas = QFontMetrics(fuente)
        lineas = self._texto_nodo(nodo).splitlines()
        ancho_texto = (
            max(metricas.horizontalAdvance(linea) for linea in lineas)
            if lineas
            else 0
        )
        alto_texto = max(
            metricas.height() * max(len(lineas), 1),
            metricas.height(),
        )
        return float(ancho_texto), float(alto_texto)

    def _dimensiones_nodo(self, nodo: NodoSintactico) -> tuple[float, float]:
        ancho_texto, alto_texto = self._medidas_texto(nodo)

        if self._debe_ser_circular(nodo, ancho_texto):
            diametro = max(
                self.DIAMETRO_MINIMO_TERMINAL,
                ancho_texto + self.RELLENO_CIRCULO,
                alto_texto + self.RELLENO_CIRCULO,
            )
            return float(diametro), float(diametro)

        ancho = max(self.ANCHO_MINIMO_NODO, ancho_texto + 34.0)
        return float(ancho), float(self.ALTO_NODO)

    def _ancho_nodo(self, nodo: NodoSintactico) -> float:
        ancho, _alto = self._dimensiones_nodo(nodo)
        return ancho

    def _ancho_subarbol(self, nodo: NodoSintactico) -> float:
        ancho_propio = self._ancho_nodo(nodo)

        if not nodo.hijos:
            return ancho_propio

        anchos_hijos = [
            self._ancho_subarbol(hijo)
            for hijo in nodo.hijos
        ]
        ancho_hijos = sum(anchos_hijos) + self.ESPACIO_HORIZONTAL * max(
            len(nodo.hijos) - 1,
            0,
        )
        return max(ancho_propio, ancho_hijos)

    def _dibujar_nodo(
        self,
        escena: QGraphicsScene,
        nodo: NodoSintactico,
        izquierda: float,
        superior: float,
        es_raiz: bool = False,
    ) -> float:
        ancho_subarbol = self._ancho_subarbol(nodo)
        centro_x = izquierda + ancho_subarbol / 2.0
        ancho_nodo, alto_nodo = self._dimensiones_nodo(nodo)

        posiciones_hijos = []
        anchos_hijos = [
            self._ancho_subarbol(hijo)
            for hijo in nodo.hijos
        ]
        ancho_grupo_hijos = (
            sum(anchos_hijos)
            + self.ESPACIO_HORIZONTAL * max(len(anchos_hijos) - 1, 0)
        )
        izquierda_hijo = (
            izquierda
            + max((ancho_subarbol - ancho_grupo_hijos) / 2.0, 0.0)
        )  # Centra el conjunto de hijos respecto al espacio reservado por el padre.

        for hijo, ancho_hijo in zip(nodo.hijos, anchos_hijos):
            centro_hijo = izquierda_hijo + ancho_hijo / 2.0
            posiciones_hijos.append((hijo, izquierda_hijo, centro_hijo))
            izquierda_hijo += ancho_hijo + self.ESPACIO_HORIZONTAL

        lapiz_linea = QPen(QColor("#89b4fa"))
        lapiz_linea.setWidthF(2.0)

        for hijo, izquierda_reservada, centro_hijo in posiciones_hijos:
            y_hijo = superior + self.ESPACIO_VERTICAL
            escena.addLine(
                centro_x,
                superior + alto_nodo,
                centro_hijo,
                y_hijo,
                lapiz_linea,
            )
            self._dibujar_nodo(
                escena,
                hijo,
                izquierda_reservada,
                y_hijo,
                False,
            )

        color_fondo = QColor("#45475a") if es_raiz else QColor("#313244")
        lapiz_nodo = QPen(QColor("#89b4fa"))
        lapiz_nodo.setWidthF(2.0)

        elipse = escena.addEllipse(
            centro_x - ancho_nodo / 2.0,
            superior,
            ancho_nodo,
            alto_nodo,
            lapiz_nodo,
            QBrush(color_fondo),
        )
        elipse.setData(
            0,
            "circulo_terminal"
            if abs(ancho_nodo - alto_nodo) < 0.01
            else "ovalo_sintactico",
        )

        fuente = QFont("Consolas", 9)
        fuente.setBold(bool(nodo.hijos or es_raiz))

        texto = escena.addText(self._texto_nodo(nodo), fuente)
        texto.setDefaultTextColor(QColor("#cdd6f4"))
        rectangulo_texto = texto.boundingRect()
        texto.setPos(
            centro_x - rectangulo_texto.width() / 2.0,
            superior + alto_nodo / 2.0 - rectangulo_texto.height() / 2.0 - 2,
        )
        return centro_x

    def _nombre_arbol(self, arbol: NodoSintactico, indice: int) -> str:
        if arbol.etiqueta.startswith("BloqueRed:"):
            nombre = arbol.etiqueta.split(":", 1)[1].strip()
            if nombre:
                return nombre

        return f"Árbol {indice}"

    def _guardar_png(self, escena: QGraphicsScene, nombre: str) -> None:
        ruta, _filtro = QFileDialog.getSaveFileName(
            self,
            "Guardar árbol sintáctico",
            f"Arbol_{nombre}.png",
            "Imagen PNG (*.png)",
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".png"):
            ruta += ".png"

        limites = escena.itemsBoundingRect().adjusted(-30, -30, 30, 30)
        ancho = max(int(limites.width()), 1)
        alto = max(int(limites.height()), 1)

        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        color_fondo = escena.backgroundBrush().color()
        imagen.fill(
            color_fondo if color_fondo.isValid() else QColor("#181825")
        )

        pintor = QPainter(imagen)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pintor.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        escena.render(pintor, QRectF(0, 0, ancho, alto), limites)
        pintor.end()
        imagen.save(ruta, "PNG")
