# ============================================================
# Archivo: control_exportacion_arbol.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Sustituye la exportación básica del árbol sintáctico por una
# elección entre:
# - PNG HD: raster a 3x y 300 DPI.
# - SVG: representación vectorial sin pérdida al ampliar.
#
# El controlador no altera la escena ni el árbol formal. Solo
# renderiza la representación gráfica que ya está en pantalla.
# ============================================================

from pathlib import Path

from PySide6.QtCore import QRect, QRectF, QSize
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QFileDialog

from Interfaz.resultados.visor_arbol_sintactico import VistaArbol
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class ControlExportacionArbol:
    ESCALA_PNG_HD = 3.0
    DPI_PNG_HD = 300
    MARGEN_EXPORTACION = 30.0

    FILTRO_PNG = "PNG HD (*.png)"
    FILTRO_SVG = "SVG (*.svg)"

    def __init__(self, ventana):
        self.ventana = ventana
        self.gestor = GestorTraducciones("es")

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)

    def establecer_idioma(self, idioma: str) -> bool:
        if not self.gestor.establecer_idioma(idioma):
            return False

        self.preparar_vistas()
        return True

    def preparar_vistas(self) -> None:
        visor = self.ventana.panel_resultados.visor_arbol

        for vista in visor.findChildren(VistaArbol):
            self._preparar_vista(vista)

    def _preparar_vista(self, vista: VistaArbol) -> None:
        boton = vista.boton_superpuesto
        if boton is None:
            return

        texto_ayuda = (
            f"{self._t('dialogos.arbol.guardar_titulo')} · PNG HD / SVG"
        )
        boton.setToolTip(texto_ayuda)
        boton.setAccessibleName(texto_ayuda)

        if boton.property("exportacion_arbol_hd_svg"):
            return

        try:
            boton.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass

        boton.clicked.connect(
            lambda _marcado=False, v=vista: self._seleccionar_exportacion(v)
        )
        boton.setProperty("exportacion_arbol_hd_svg", True)

    def _seleccionar_exportacion(self, vista: VistaArbol) -> None:
        try:
            escena = vista.scene()
        except RuntimeError:
            return

        if escena is None:
            return

        nombre = str(vista.property("nombre_arbol") or "1")
        nombre_base = self._nombre_base_traducido(nombre)

        ruta, filtro = QFileDialog.getSaveFileName(
            self.ventana,
            self._t("dialogos.arbol.guardar_titulo"),
            f"{nombre_base}.png",
            f"{self.FILTRO_PNG};;{self.FILTRO_SVG}",
            self.FILTRO_PNG,
        )

        if not ruta:
            return

        formato = self._formato_seleccionado(ruta, filtro)
        ruta_final = self._asegurar_extension(ruta, formato)

        if formato == "svg":
            self._exportar_svg(escena, ruta_final)
        else:
            self._exportar_png_hd(escena, ruta_final)

    def _nombre_base_traducido(self, nombre: str) -> str:
        nombre_catalogo = self._t(
            "dialogos.arbol.nombre_archivo",
            nombre=nombre,
        )
        ruta = Path(nombre_catalogo)

        if ruta.suffix.lower() in (".png", ".svg"):
            return ruta.stem

        return ruta.name

    @classmethod
    def _formato_seleccionado(cls, ruta: str, filtro: str) -> str:
        extension = Path(ruta).suffix.lower()

        if extension == ".svg":
            return "svg"
        if extension == ".png":
            return "png"

        return "svg" if filtro == cls.FILTRO_SVG else "png"

    @staticmethod
    def _asegurar_extension(ruta: str, formato: str) -> str:
        extension = f".{formato}"
        ruta_path = Path(ruta)

        if ruta_path.suffix.lower() == extension:
            return str(ruta_path)

        if ruta_path.suffix.lower() in (".png", ".svg"):
            ruta_path = ruta_path.with_suffix(extension)
        else:
            ruta_path = Path(f"{ruta}{extension}")

        return str(ruta_path)

    def _limites_exportacion(self, escena) -> QRectF:
        return escena.itemsBoundingRect().adjusted(
            -self.MARGEN_EXPORTACION,
            -self.MARGEN_EXPORTACION,
            self.MARGEN_EXPORTACION,
            self.MARGEN_EXPORTACION,
        )

    @staticmethod
    def _color_fondo(escena) -> QColor:
        color = escena.backgroundBrush().color()
        return color if color.isValid() else QColor("#181825")

    @staticmethod
    def _configurar_pintor(pintor: QPainter) -> None:
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pintor.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    def _exportar_png_hd(self, escena, ruta: str) -> bool:
        limites = self._limites_exportacion(escena)
        escala = self.ESCALA_PNG_HD
        ancho = max(int(round(limites.width() * escala)), 1)
        alto = max(int(round(limites.height() * escala)), 1)

        imagen = QImage(
            ancho,
            alto,
            QImage.Format.Format_ARGB32,
        )
        imagen.fill(self._color_fondo(escena))

        puntos_por_metro = int(round(self.DPI_PNG_HD / 0.0254))
        imagen.setDotsPerMeterX(puntos_por_metro)
        imagen.setDotsPerMeterY(puntos_por_metro)

        pintor = QPainter(imagen)
        self._configurar_pintor(pintor)
        escena.render(
            pintor,
            QRectF(0, 0, ancho, alto),
            limites,
        )
        pintor.end()

        return imagen.save(ruta, "PNG")

    def _exportar_svg(self, escena, ruta: str) -> None:
        limites = self._limites_exportacion(escena)
        ancho = max(int(round(limites.width())), 1)
        alto = max(int(round(limites.height())), 1)

        generador = QSvgGenerator()
        generador.setFileName(ruta)
        generador.setSize(QSize(ancho, alto))
        generador.setViewBox(QRect(0, 0, ancho, alto))
        generador.setResolution(96)
        generador.setTitle("TecNet Finder - Syntax Tree")
        generador.setDescription(
            "Vector export generated by TecNet Finder."
        )

        pintor = QPainter(generador)
        self._configurar_pintor(pintor)
        pintor.fillRect(
            QRectF(0, 0, ancho, alto),
            self._color_fondo(escena),
        )
        escena.render(
            pintor,
            QRectF(0, 0, ancho, alto),
            limites,
        )
        pintor.end()
