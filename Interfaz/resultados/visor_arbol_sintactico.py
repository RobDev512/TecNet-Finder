# ============================================================
# Archivo: visor_arbol_sintactico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene la representación textual y gráfica de los árboles
# sintácticos producidos por TecNet Finder.
#
# La acción Guardar PNG se mantiene como un botón cuadrado
# superpuesto dentro del área gráfica para no consumir espacio
# vertical ni modificar el tamaño disponible para el árbol.
# ============================================================

from PySide6.QtCore import QRectF, QSize, Qt  # Proporciona geometría, tamaños y opciones generales de Qt.
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QIcon, QImage, QPainter, QPen  # Proporciona herramientas de dibujo, fuentes e imágenes.
from PySide6.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsView, QLabel, QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget  # Proporciona los controles utilizados por el visor.
from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona el recurso inicial utilizado por la acción Guardar PNG.
from Motor.compilacion.modelos import NodoSintactico  # Define la estructura recibida directamente desde el analizador sintáctico.


class VistaArbol(QGraphicsView):  # Representa una vista desplazable e interactiva para un único árbol sintáctico.
    MARGEN_BOTON = 8  # Mantiene el botón flotante separado de los bordes del viewport.

    def __init__(self, escena: QGraphicsScene, padre=None):
        super().__init__(escena, padre)  # Asocia inmediatamente la escena con el visor.
        self.boton_superpuesto: QPushButton | None = None  # Reserva una posible acción flotante sin ocupar espacio en el layout.
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza líneas, elipses y textos.
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # Permite desplazarse arrastrando el árbol.
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)  # Mantiene el punto del cursor durante zoom.
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)  # Mantiene centrada la escena al redimensionar.

    def establecer_boton_superpuesto(self, boton: QPushButton) -> None:
        self.boton_superpuesto = boton  # Conserva la acción para poder recolocarla automáticamente.
        self._posicionar_boton_superpuesto()  # Coloca el botón inmediatamente en la esquina superior derecha.
        boton.raise_()  # Garantiza que permanezca encima del contenido de la vista.

    def _posicionar_boton_superpuesto(self) -> None:
        if self.boton_superpuesto is None: return  # Finaliza cuando la vista no posee ninguna acción flotante.
        x = max(self.MARGEN_BOTON, self.viewport().width() - self.boton_superpuesto.width() - self.MARGEN_BOTON)  # Calcula la posición derecha dentro del viewport.
        self.boton_superpuesto.move(x, self.MARGEN_BOTON)  # Mantiene el botón dentro del árbol y separado del borde superior.
        self.boton_superpuesto.raise_()  # Reafirma su posición visual encima de la escena.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Permite primero que QGraphicsView actualice correctamente su viewport.
        self._posicionar_boton_superpuesto()  # Reancla después la acción a la esquina superior derecha.

    def wheelEvent(self, evento) -> None:
        if evento.modifiers() & Qt.KeyboardModifier.ControlModifier:  # Comprueba si el usuario mantiene Ctrl.
            factor = 1.15 if evento.angleDelta().y() > 0 else 1 / 1.15  # Selecciona acercamiento o alejamiento.
            self.scale(factor, factor)  # Aplica el cambio de escala sin modificar la escena original.
            evento.accept()  # Marca el evento como atendido.
            return  # Evita desplazar también verticalmente la vista.
        super().wheelEvent(evento)  # Conserva el desplazamiento convencional cuando Ctrl no está presionado.


class VisorArbolSintactico(QWidget):  # Organiza la representación textual y gráfica de todos los árboles válidos.
    ANCHO_MINIMO_NODO = 120.0  # Evita nodos demasiado estrechos.
    ALTO_NODO = 52.0  # Mantiene una altura uniforme.
    ESPACIO_HORIZONTAL = 28.0  # Separa ramas hermanas.
    ESPACIO_VERTICAL = 105.0  # Separa niveles consecutivos.
    MARGEN_ESCENA = 45.0  # Reserva espacio alrededor de la estructura completa.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el contenedor general.
        self.escenas: list[QGraphicsScene] = []  # Conserva las escenas actuales para exportación y tematización.
        diseno = QVBoxLayout(self)  # Organiza el visor completo verticalmente.
        diseno.setContentsMargins(0, 0, 0, 0)  # Aprovecha toda la superficie disponible.
        self.pestanas_vista = QTabWidget()  # Separa representación textual y gráfica.
        diseno.addWidget(self.pestanas_vista)  # Ocupa todo el contenedor principal.
        self.texto_arbol = QPlainTextEdit()  # Crea la representación textual de ramas.
        self.texto_arbol.setReadOnly(True)  # Evita modificaciones accidentales.
        self.texto_arbol.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # Conserva conectores y sangrías.
        self.contenedor_grafico = QWidget()  # Aloja ayuda y pestañas de árboles gráficos.
        diseno_grafico = QVBoxLayout(self.contenedor_grafico)  # Organiza la vista gráfica.
        diseno_grafico.setContentsMargins(6, 6, 6, 6)  # Mantiene una separación discreta.
        ayuda = QLabel("Arrastra para desplazarte · Ctrl + rueda para acercar o alejar")  # Explica los controles disponibles.
        ayuda.setObjectName("SubtituloPrincipal")  # Reutiliza la jerarquía secundaria de TecNet Finder.
        diseno_grafico.addWidget(ayuda)  # Coloca la ayuda encima de las pestañas.
        self.pestanas_arboles = QTabWidget()  # Permite mostrar un árbol por bloque válido.
        diseno_grafico.addWidget(self.pestanas_arboles, 1)  # Entrega la mayor parte del espacio a los árboles.
        self.pestanas_vista.addTab(self.texto_arbol, "Representación textual")  # Añade la vista textual.
        self.pestanas_vista.addTab(self.contenedor_grafico, "Árbol gráfico")  # Añade la vista gráfica.
        self.limpiar()  # Inicializa ambos formatos sin contenido válido.

    def mostrar_arboles(self, arboles: list[NodoSintactico], arbol_textual: str) -> None:
        self.texto_arbol.setPlainText(arbol_textual or "No hay árboles válidos para mostrar.")  # Actualiza la representación textual.
        self._limpiar_arboles_graficos()  # Elimina la compilación gráfica anterior.
        if not arboles: self._mostrar_estado_vacio(); return  # Presenta un estado neutral cuando el parser no produjo árboles válidos.
        for indice, arbol in enumerate(arboles, start=1): self._agregar_arbol(arbol, indice)  # Construye una pestaña por cada bloque válido.

    def limpiar(self) -> None:
        self.texto_arbol.setPlainText("No hay árboles válidos para mostrar.")  # Recupera el mensaje neutral de la vista textual.
        self._limpiar_arboles_graficos()  # Elimina cualquier escena gráfica previa.
        self._mostrar_estado_vacio()  # Recupera también el estado neutral gráfico.

    def _limpiar_arboles_graficos(self) -> None:
        while self.pestanas_arboles.count() > 0:  # Continúa mientras todavía exista una pestaña anterior.
            widget = self.pestanas_arboles.widget(0)  # Recupera el primer contenedor existente.
            self.pestanas_arboles.removeTab(0)  # Lo retira de las pestañas visibles.
            widget.deleteLater()  # Solicita su destrucción segura.
        self.escenas.clear()  # Descarta las referencias a escenas que ya no se utilizan.

    def _mostrar_estado_vacio(self) -> None:
        contenedor = QWidget()  # Crea una superficie simple para el mensaje neutral.
        diseno = QVBoxLayout(contenedor)  # Organiza el contenido del estado vacío.
        etiqueta = QLabel("No hay árboles sintácticos válidos para mostrar.")  # Explica por qué no existe representación gráfica.
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el mensaje en el área disponible.
        diseno.addWidget(etiqueta)  # Coloca la explicación dentro del contenedor.
        self.pestanas_arboles.addTab(contenedor, "Sin árbol")  # Añade una única pestaña neutral.

    def _agregar_arbol(self, arbol: NodoSintactico, indice: int) -> None:
        contenedor = QWidget()  # Crea el contenedor particular del árbol actual.
        diseno = QVBoxLayout(contenedor)  # Organiza únicamente la vista gráfica, sin una fila extra de acciones.
        diseno.setContentsMargins(4, 4, 4, 4)  # Mantiene un margen mínimo alrededor del visor.
        escena = QGraphicsScene(self)  # Crea una escena independiente para este árbol.
        escena.setBackgroundBrush(QBrush(QColor("#181825")))  # Conserva un fondo seguro antes de que el gestor aplique el tema actual.
        self.escenas.append(escena)  # Conserva la escena para exportación y tematización posterior.
        ancho_total = self._ancho_subarbol(arbol)  # Calcula el espacio horizontal necesario.
        self._dibujar_nodo(escena, arbol, self.MARGEN_ESCENA, self.MARGEN_ESCENA, True)  # Dibuja recursivamente toda la estructura.
        limites = escena.itemsBoundingRect().adjusted(-self.MARGEN_ESCENA, -self.MARGEN_ESCENA, self.MARGEN_ESCENA, self.MARGEN_ESCENA)  # Añade margen exterior.
        escena.setSceneRect(limites)  # Define la región completa desplazable.
        vista = VistaArbol(escena)  # Crea el componente interactivo que mostrará la escena.
        vista.setMinimumWidth(int(min(ancho_total + self.MARGEN_ESCENA * 2, 900)))  # Conserva una anchura razonable.
        diseno.addWidget(vista, 1)  # Entrega toda la superficie restante al árbol.
        nombre = self._nombre_arbol(arbol, indice)  # Obtiene una etiqueta legible para la pestaña.
        boton_guardar = QPushButton(vista.viewport())  # Crea la acción directamente sobre el viewport para no consumir espacio del layout.
        boton_guardar.setObjectName("BotonGuardarArbol")  # Permite tematizar exclusivamente este botón flotante.
        boton_guardar.setFixedSize(34, 34)  # Mantiene el formato cuadrado solicitado.
        boton_guardar.setText("")  # Muestra únicamente el icono, sin la etiqueta Guardar PNG.
        boton_guardar.setToolTip("Guardar este árbol sintáctico como imagen PNG")  # Conserva la explicación mediante hover.
        boton_guardar.setIconSize(QSize(18, 18))  # Mantiene el recurso proporcionado dentro de una escala compacta.
        ruta_guardar = ruta_icono_oscuro("Guardar.png")  # Recupera la variante inicial de Guardar antes de que el gestor sincronice el tema actual.
        if ruta_guardar.exists(): boton_guardar.setIcon(QIcon(str(ruta_guardar)))  # Coloca el icono disponible.
        boton_guardar.clicked.connect(lambda _marcado=False, e=escena, n=nombre: self._guardar_png(e, n))  # Asocia la acción con esta escena exacta.
        vista.establecer_boton_superpuesto(boton_guardar)  # Ancla el botón a la esquina superior derecha del área gráfica.
        self.pestanas_arboles.addTab(contenedor, nombre)  # Añade finalmente la pestaña correspondiente con el árbol actual.

    def _texto_nodo(self, nodo: NodoSintactico) -> str:
        if nodo.valor is not None: return f"{nodo.etiqueta}\n{nodo.valor}"  # Muestra etiqueta y valor terminal en líneas separadas.
        return nodo.etiqueta  # Utiliza únicamente la etiqueta para nodos estructurales.

    def _ancho_nodo(self, nodo: NodoSintactico) -> float:
        fuente = QFont("Consolas", 9)  # Utiliza una fuente monoespaciada para nodos del compilador.
        metricas = QFontMetrics(fuente)  # Obtiene medidas reales de la fuente.
        lineas = self._texto_nodo(nodo).splitlines()  # Separa las líneas visibles del nodo.
        ancho_texto = max(metricas.horizontalAdvance(linea) for linea in lineas) if lineas else 0  # Localiza la línea más ancha.
        return max(self.ANCHO_MINIMO_NODO, float(ancho_texto + 34))  # Añade espacio interior y respeta el mínimo.

    def _ancho_subarbol(self, nodo: NodoSintactico) -> float:
        ancho_propio = self._ancho_nodo(nodo)  # Calcula primero el espacio propio del nodo.
        if not nodo.hijos: return ancho_propio  # Una hoja no necesita reservar espacio adicional.
        anchos_hijos = [self._ancho_subarbol(hijo) for hijo in nodo.hijos]  # Calcula recursivamente cada rama hija.
        ancho_hijos = sum(anchos_hijos) + self.ESPACIO_HORIZONTAL * max(len(nodo.hijos) - 1, 0)  # Añade separación entre hermanos.
        return max(ancho_propio, ancho_hijos)  # Garantiza espacio suficiente para padre y descendientes.

    def _dibujar_nodo(self, escena: QGraphicsScene, nodo: NodoSintactico, izquierda: float, superior: float, es_raiz: bool = False) -> float:
        ancho_subarbol = self._ancho_subarbol(nodo)  # Obtiene el espacio reservado para toda la rama.
        centro_x = izquierda + ancho_subarbol / 2.0  # Calcula el centro horizontal del nodo actual.
        ancho_nodo = self._ancho_nodo(nodo)  # Obtiene el ancho concreto de su elipse.
        posiciones_hijos = []  # Conserva temporalmente las posiciones de los descendientes.
        izquierda_hijo = izquierda  # Comienza a distribuir hijos desde el borde izquierdo.
        for hijo in nodo.hijos:  # Recorre todos los descendientes inmediatos.
            ancho_hijo = self._ancho_subarbol(hijo)  # Calcula cuánto espacio requiere la rama hija.
            centro_hijo = izquierda_hijo + ancho_hijo / 2.0  # Calcula su centro horizontal anticipadamente.
            posiciones_hijos.append((hijo, izquierda_hijo, centro_hijo))  # Conserva información para conexión y recursividad.
            izquierda_hijo += ancho_hijo + self.ESPACIO_HORIZONTAL  # Avanza al espacio reservado para el siguiente hijo.
        lapiz_linea = QPen(QColor("#89b4fa"))  # Utiliza el azul histórico como valor inicial de las conexiones.
        lapiz_linea.setWidthF(2.0)  # Mantiene relaciones suficientemente visibles.
        for hijo, izquierda_reservada, centro_hijo in posiciones_hijos:  # Dibuja conexiones antes de los nodos.
            y_hijo = superior + self.ESPACIO_VERTICAL  # Calcula la altura del siguiente nivel.
            escena.addLine(centro_x, superior + self.ALTO_NODO, centro_hijo, y_hijo, lapiz_linea)  # Conecta padre e hijo.
            self._dibujar_nodo(escena, hijo, izquierda_reservada, y_hijo, False)  # Continúa recursivamente con el descendiente.
        color_fondo = QColor("#45475a") if es_raiz else QColor("#313244")  # Diferencia inicialmente la raíz del resto.
        lapiz_nodo = QPen(QColor("#89b4fa"))  # Utiliza el azul histórico como contorno inicial.
        lapiz_nodo.setWidthF(2.0)  # Mantiene un borde claramente visible.
        escena.addEllipse(centro_x - ancho_nodo / 2.0, superior, ancho_nodo, self.ALTO_NODO, lapiz_nodo, QBrush(color_fondo))  # Dibuja el nodo actual.
        fuente = QFont("Consolas", 9)  # Utiliza la misma fuente empleada para medir el nodo.
        fuente.setBold(bool(nodo.hijos or es_raiz))  # Destaca raíz y nodos estructurales.
        texto = escena.addText(self._texto_nodo(nodo), fuente)  # Crea la etiqueta visible del nodo.
        texto.setDefaultTextColor(QColor("#cdd6f4"))  # Utiliza el texto histórico antes de la tematización dinámica.
        rectangulo_texto = texto.boundingRect()  # Obtiene sus dimensiones reales.
        texto.setPos(centro_x - rectangulo_texto.width() / 2.0, superior + self.ALTO_NODO / 2.0 - rectangulo_texto.height() / 2.0 - 2)  # Centra la etiqueta dentro de la elipse.
        return centro_x  # Devuelve el centro calculado para posibles llamadas superiores.

    def _nombre_arbol(self, arbol: NodoSintactico, indice: int) -> str:
        if arbol.etiqueta.startswith("BloqueRed:"):  # Comprueba si la raíz incluye un nombre de red.
            nombre = arbol.etiqueta.split(":", 1)[1].strip()  # Extrae el identificador situado después de los dos puntos.
            if nombre: return nombre  # Utiliza directamente el nombre cuando existe.
        return f"Árbol {indice}"  # Utiliza una numeración estable cuando no existe nombre explícito.

    def _guardar_png(self, escena: QGraphicsScene, nombre: str) -> None:
        ruta, _filtro = QFileDialog.getSaveFileName(self, "Guardar árbol sintáctico", f"Arbol_{nombre}.png", "Imagen PNG (*.png)")  # Solicita la ubicación final de la imagen.
        if not ruta: return  # Finaliza cuando el usuario cancela el cuadro de guardado.
        if not ruta.lower().endswith(".png"): ruta += ".png"  # Garantiza la extensión esperada.
        limites = escena.itemsBoundingRect().adjusted(-30, -30, 30, 30)  # Incluye un pequeño margen alrededor del árbol completo.
        ancho, alto = max(int(limites.width()), 1), max(int(limites.height()), 1)  # Evita dimensiones nulas.
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)  # Crea una imagen capaz de contener la escena completa.
        color_fondo = escena.backgroundBrush().color()  # Recupera el fondo real del tema vigente en lugar de forzar siempre el modo oscuro.
        imagen.fill(color_fondo if color_fondo.isValid() else QColor("#181825"))  # Conserva un respaldo seguro si la brocha no posee color válido.
        pintor = QPainter(imagen)  # Crea el pintor utilizado para copiar la escena.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Mantiene curvas y líneas suaves también en el PNG.
        escena.render(pintor, QRectF(0, 0, ancho, alto), limites)  # Renderiza la escena completa independientemente del zoom actual.
        pintor.end()  # Finaliza explícitamente el pintado antes de escribir el archivo.
        imagen.save(ruta, "PNG")  # Guarda finalmente la representación utilizando formato PNG.
