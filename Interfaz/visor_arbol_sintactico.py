# ============================================================
# Archivo: visor_arbol_sintactico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la representación visual de los árboles
# sintácticos producidos por el analizador de TecNet Finder.
#
# Permite consultar cada árbol mediante una representación
# textual y una vista gráfica desplazable. También permite
# guardar individualmente cada árbol gráfico como imagen PNG.
# ============================================================

from PySide6.QtCore import QRectF, Qt  # Importa geometría y opciones necesarias para organizar la escena gráfica.
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QImage, QPainter, QPen  # Importa herramientas de dibujo, fuentes e imágenes.
from PySide6.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget  # Importa componentes utilizados por el visor.

from Motor.modelos import NodoSintactico  # Importa la estructura generada directamente por el analizador sintáctico.


class VistaArbol(QGraphicsView):  # Define una vista desplazable dedicada a mostrar un único árbol sintáctico.
    def __init__(self, escena: QGraphicsScene, padre=None):  # Inicializa la vista utilizando la escena gráfica recibida.
        super().__init__(escena, padre)  # Asocia inmediatamente la escena con el visor.
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza líneas, elipses y textos del árbol.
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # Permite desplazarse arrastrando cuando el árbol supera el tamaño visible.
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)  # Mantiene el punto señalado por el mouse durante el zoom.
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)  # Mantiene centrada la escena cuando cambia el tamaño del visor.

    def wheelEvent(self, evento) -> None:  # Permite usar Ctrl más la rueda para acercar o alejar el árbol.
        if evento.modifiers() & Qt.KeyboardModifier.ControlModifier:  # Comprueba si el usuario mantiene presionada la tecla Ctrl.
            factor = 1.15 if evento.angleDelta().y() > 0 else 1 / 1.15  # Selecciona acercamiento o alejamiento según el sentido de la rueda.
            self.scale(factor, factor)  # Aplica el cambio de escala conservando la escena original.
            evento.accept()  # Marca el evento como procesado por el visor.
            return  # Evita utilizar también el desplazamiento vertical normal.

        super().wheelEvent(evento)  # Conserva el desplazamiento convencional cuando Ctrl no está presionado.


class VisorArbolSintactico(QWidget):  # Organiza la representación textual y gráfica de los árboles sintácticos.
    ANCHO_MINIMO_NODO = 120.0  # Define un ancho mínimo para evitar nodos excesivamente pequeños.
    ALTO_NODO = 52.0  # Define la altura uniforme utilizada por cada nodo gráfico.
    ESPACIO_HORIZONTAL = 28.0  # Define la separación mínima entre subárboles hermanos.
    ESPACIO_VERTICAL = 105.0  # Define la distancia vertical entre niveles consecutivos.
    MARGEN_ESCENA = 45.0  # Reserva espacio alrededor del árbol para evitar que quede pegado a los bordes.

    def __init__(self, padre=None):  # Inicializa las dos formas de visualizar la información sintáctica.
        super().__init__(padre)  # Inicializa el QWidget utilizado como contenedor general.
        self.escenas: list[QGraphicsScene] = []  # Conserva las escenas actuales para poder exportarlas posteriormente.

        diseno = QVBoxLayout(self)  # Organiza el conjunto interno de pestañas dentro del visor.
        diseno.setContentsMargins(0, 0, 0, 0)  # Permite aprovechar completamente el espacio disponible.

        self.pestanas_vista = QTabWidget()  # Separa la representación textual de la representación gráfica.
        diseno.addWidget(self.pestanas_vista)  # Coloca las vistas ocupando todo el contenedor.

        self.texto_arbol = QPlainTextEdit()  # Crea el área donde se mostrará la representación mediante ramas de texto.
        self.texto_arbol.setReadOnly(True)  # Evita que el usuario modifique accidentalmente el árbol generado.
        self.texto_arbol.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # Conserva correctamente los conectores y sangrías del árbol.

        self.contenedor_grafico = QWidget()  # Crea el contenedor destinado a los árboles visuales.
        diseno_grafico = QVBoxLayout(self.contenedor_grafico)  # Organiza ayuda y pestañas de árboles verticalmente.
        diseno_grafico.setContentsMargins(6, 6, 6, 6)  # Mantiene una separación discreta alrededor de la vista.

        ayuda = QLabel("Arrastra para desplazarte · Ctrl + rueda para acercar o alejar")  # Informa brevemente los controles disponibles.
        ayuda.setObjectName("SubtituloPrincipal")  # Reutiliza el estilo secundario de la interfaz.
        diseno_grafico.addWidget(ayuda)  # Coloca la ayuda inmediatamente encima de los árboles.

        self.pestanas_arboles = QTabWidget()  # Permite mostrar independientemente cada bloque sintácticamente válido.
        diseno_grafico.addWidget(self.pestanas_arboles, 1)  # Permite que las vistas gráficas ocupen la mayor parte del espacio.

        self.pestanas_vista.addTab(self.texto_arbol, "Representación textual")  # Agrega la forma textual ya existente en el proyecto.
        self.pestanas_vista.addTab(self.contenedor_grafico, "Árbol gráfico")  # Agrega la nueva representación visual recuperada.

        self.limpiar()  # Inicializa ambos formatos en estado vacío.

    def mostrar_arboles(self, arboles: list[NodoSintactico], arbol_textual: str) -> None:  # Sustituye las vistas existentes por los árboles de la compilación actual.
        self.texto_arbol.setPlainText(arbol_textual or "No hay árboles válidos para mostrar.")  # Actualiza inmediatamente la representación textual.
        self._limpiar_arboles_graficos()  # Elimina pestañas correspondientes a una compilación anterior.

        if not arboles:  # Comprueba si el parser no produjo ningún árbol válido.
            self._mostrar_estado_vacio()  # Muestra un mensaje claro en lugar de dejar la vista gráfica vacía.
            return  # Finaliza porque no existen nodos que puedan dibujarse.

        for indice, arbol in enumerate(arboles, start=1):  # Recorre un árbol por cada instrucción sintácticamente válida.
            self._agregar_arbol(arbol, indice)  # Construye una pestaña gráfica independiente para el árbol actual.

    def limpiar(self) -> None:  # Restaura las vistas sintácticas a su estado inicial.
        self.texto_arbol.setPlainText("No hay árboles válidos para mostrar.")  # Recupera el mensaje neutral de la representación textual.
        self._limpiar_arboles_graficos()  # Elimina cualquier escena gráfica perteneciente al análisis anterior.
        self._mostrar_estado_vacio()  # Recupera también el mensaje neutral en la representación gráfica.

    def _limpiar_arboles_graficos(self) -> None:  # Elimina todas las pestañas y escenas gráficas existentes.
        while self.pestanas_arboles.count() > 0:  # Continúa mientras todavía exista alguna pestaña del análisis anterior.
            widget = self.pestanas_arboles.widget(0)  # Obtiene el primer contenedor gráfico existente.
            self.pestanas_arboles.removeTab(0)  # Retira la pestaña del conjunto visible.
            widget.deleteLater()  # Solicita a Qt destruir correctamente el contenedor retirado.

        self.escenas.clear()  # Descarta las referencias a las escenas que dejaron de utilizarse.

    def _mostrar_estado_vacio(self) -> None:  # Crea una pestaña neutral cuando todavía no existe ningún árbol.
        contenedor = QWidget()  # Crea un contenedor simple para mostrar el mensaje inicial.
        diseno = QVBoxLayout(contenedor)  # Organiza el mensaje dentro de la pestaña.
        etiqueta = QLabel("No hay árboles sintácticos válidos para mostrar.")  # Explica por qué no aparece ninguna estructura gráfica.
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el mensaje dentro del espacio disponible.
        diseno.addWidget(etiqueta)  # Coloca el mensaje ocupando la pestaña.
        self.pestanas_arboles.addTab(contenedor, "Sin árbol")  # Agrega una única pestaña neutral.

    def _agregar_arbol(self, arbol: NodoSintactico, indice: int) -> None:  # Construye la pestaña completa correspondiente a un árbol sintáctico.
        contenedor = QWidget()  # Crea el contenedor particular del árbol actual.
        diseno = QVBoxLayout(contenedor)  # Organiza botones y vista gráfica verticalmente.
        diseno.setContentsMargins(4, 4, 4, 4)  # Mantiene un margen pequeño alrededor del árbol.

        acciones = QHBoxLayout()  # Crea una fila dedicada a las acciones disponibles sobre el árbol.
        acciones.addStretch()  # Empuja el botón de guardado hacia el extremo derecho.

        boton_guardar = QPushButton("💾 Guardar PNG")  # Crea la acción que permite exportar el árbol actual como imagen.
        boton_guardar.setToolTip("Guardar este árbol sintáctico como imagen PNG")  # Explica brevemente la finalidad del botón.
        acciones.addWidget(boton_guardar)  # Coloca el botón dentro de la zona superior.
        diseno.addLayout(acciones)  # Agrega las acciones antes de la escena gráfica.

        escena = QGraphicsScene(self)  # Crea una escena independiente para el árbol actual.
        escena.setBackgroundBrush(QBrush(QColor("#181825")))  # Utiliza el mismo fondo oscuro del resto de TecNet Finder.
        self.escenas.append(escena)  # Conserva la escena para poder exportarla posteriormente.

        ancho_total = self._ancho_subarbol(arbol)  # Calcula cuánto espacio horizontal necesita toda la estructura.
        self._dibujar_nodo(escena, arbol, self.MARGEN_ESCENA, self.MARGEN_ESCENA, True)  # Dibuja recursivamente el árbol desde la esquina superior.

        limites = escena.itemsBoundingRect().adjusted(-self.MARGEN_ESCENA, -self.MARGEN_ESCENA, self.MARGEN_ESCENA, self.MARGEN_ESCENA)  # Amplía los límites reales para dejar margen.
        escena.setSceneRect(limites)  # Define la región completa que podrá recorrerse mediante scroll.

        vista = VistaArbol(escena)  # Crea el componente interactivo que mostrará la escena construida.
        vista.setMinimumWidth(int(min(ancho_total + self.MARGEN_ESCENA * 2, 900)))  # Conserva una anchura razonable sin forzar el tamaño de la ventana.
        diseno.addWidget(vista, 1)  # Permite que el árbol ocupe todo el espacio restante.

        nombre = self._nombre_arbol(arbol, indice)  # Obtiene una etiqueta legible para identificar la pestaña.
        boton_guardar.clicked.connect(lambda _marcado=False, e=escena, n=nombre: self._guardar_png(e, n))  # Asocia el botón con la escena exacta correspondiente.
        self.pestanas_arboles.addTab(contenedor, nombre)  # Agrega finalmente el árbol al conjunto de pestañas.

    def _texto_nodo(self, nodo: NodoSintactico) -> str:  # Construye el texto que aparecerá dentro de cada nodo gráfico.
        if nodo.valor is not None:  # Comprueba si el nodo representa además un valor terminal concreto.
            return f"{nodo.etiqueta}\n{nodo.valor}"  # Muestra tipo de nodo y valor en líneas separadas.

        return nodo.etiqueta  # Utiliza únicamente la etiqueta para nodos estructurales.

    def _ancho_nodo(self, nodo: NodoSintactico) -> float:  # Calcula cuánto ancho necesita la elipse según el texto que contiene.
        fuente = QFont("Consolas", 9)  # Utiliza una fuente monoespaciada adecuada para elementos del compilador.
        metricas = QFontMetrics(fuente)  # Obtiene las medidas reales de la fuente utilizada.
        lineas = self._texto_nodo(nodo).splitlines()  # Separa etiqueta y valor cuando ocupan más de una línea.
        ancho_texto = max(metricas.horizontalAdvance(linea) for linea in lineas) if lineas else 0  # Obtiene la línea visible más ancha.
        return max(self.ANCHO_MINIMO_NODO, float(ancho_texto + 34))  # Agrega espacio interior y conserva el mínimo establecido.

    def _ancho_subarbol(self, nodo: NodoSintactico) -> float:  # Calcula recursivamente cuánto ancho debe reservarse para cada rama.
        ancho_propio = self._ancho_nodo(nodo)  # Calcula primero el espacio requerido por el nodo actual.

        if not nodo.hijos:  # Comprueba si el nodo es una hoja del árbol.
            return ancho_propio  # Una hoja solamente necesita el ancho de su propia representación.

        anchos_hijos = [self._ancho_subarbol(hijo) for hijo in nodo.hijos]  # Calcula independientemente el ancho de todos los descendientes inmediatos.
        ancho_hijos = sum(anchos_hijos) + self.ESPACIO_HORIZONTAL * max(len(nodo.hijos) - 1, 0)  # Agrega los espacios necesarios entre ramas hermanas.

        return max(ancho_propio, ancho_hijos)  # Garantiza que tanto padre como descendientes quepan dentro del espacio reservado.

    def _dibujar_nodo(self, escena: QGraphicsScene, nodo: NodoSintactico, izquierda: float, superior: float, es_raiz: bool = False) -> float:  # Dibuja recursivamente un nodo y todos sus descendientes.
        ancho_subarbol = self._ancho_subarbol(nodo)  # Obtiene el espacio reservado para toda la rama actual.
        centro_x = izquierda + ancho_subarbol / 2.0  # Calcula el centro horizontal donde se colocará el nodo padre.
        ancho_nodo = self._ancho_nodo(nodo)  # Obtiene el ancho concreto de la elipse actual.

        posiciones_hijos = []  # Conserva temporalmente los centros de los hijos para dibujar sus conexiones.
        izquierda_hijo = izquierda  # Comienza a distribuir descendientes desde el borde izquierdo de la rama.

        for hijo in nodo.hijos:  # Recorre todos los descendientes directos del nodo actual.
            ancho_hijo = self._ancho_subarbol(hijo)  # Calcula cuánto espacio reservar al descendiente actual.
            centro_hijo = izquierda_hijo + ancho_hijo / 2.0  # Obtiene anticipadamente el centro horizontal del hijo.
            posiciones_hijos.append((hijo, izquierda_hijo, centro_hijo))  # Guarda la información necesaria para conexión y recursividad.
            izquierda_hijo += ancho_hijo + self.ESPACIO_HORIZONTAL  # Avanza al espacio reservado para el siguiente descendiente.

        lapiz_linea = QPen(QColor("#89b4fa"))  # Utiliza azul para las relaciones jerárquicas entre nodos.
        lapiz_linea.setWidthF(2.0)  # Aumenta ligeramente el grosor para mantener las conexiones visibles.

        for hijo, izquierda_reservada, centro_hijo in posiciones_hijos:  # Dibuja primero las conexiones para que los nodos aparezcan encima.
            y_hijo = superior + self.ESPACIO_VERTICAL  # Calcula la altura correspondiente al siguiente nivel del árbol.
            escena.addLine(centro_x, superior + self.ALTO_NODO, centro_hijo, y_hijo, lapiz_linea)  # Conecta el borde inferior del padre con el superior del hijo.
            self._dibujar_nodo(escena, hijo, izquierda_reservada, y_hijo, False)  # Continúa recursivamente con el descendiente actual.

        color_fondo = QColor("#45475a") if es_raiz else QColor("#313244")  # Diferencia visualmente la raíz del resto de nodos.
        color_borde = QColor("#89b4fa")  # Conserva el azul principal como contorno uniforme.
        lapiz_nodo = QPen(color_borde)  # Crea el borde utilizado por la elipse.
        lapiz_nodo.setWidthF(2.0)  # Hace el contorno suficientemente visible sobre el fondo oscuro.

        escena.addEllipse(centro_x - ancho_nodo / 2.0, superior, ancho_nodo, self.ALTO_NODO, lapiz_nodo, QBrush(color_fondo))  # Dibuja la elipse correspondiente al nodo actual.

        fuente = QFont("Consolas", 9)  # Utiliza la misma fuente empleada para calcular dimensiones.
        fuente.setBold(bool(nodo.hijos or es_raiz))  # Destaca nodos estructurales y raíz frente a hojas simples.
        texto = escena.addText(self._texto_nodo(nodo), fuente)  # Crea el contenido textual colocado encima de la elipse.
        texto.setDefaultTextColor(QColor("#cdd6f4"))  # Utiliza el color principal de texto de la interfaz.

        rectangulo_texto = texto.boundingRect()  # Obtiene el tamaño real ocupado por la etiqueta renderizada.
        texto.setPos(centro_x - rectangulo_texto.width() / 2.0, superior + self.ALTO_NODO / 2.0 - rectangulo_texto.height() / 2.0 - 2)  # Centra el contenido dentro de la elipse.

        return centro_x  # Devuelve el centro calculado por si una llamada superior necesita utilizarlo.

    def _nombre_arbol(self, arbol: NodoSintactico, indice: int) -> str:  # Obtiene un nombre corto para identificar visualmente cada árbol.
        if arbol.etiqueta.startswith("BloqueRed:"):  # Comprueba si el parser incluyó un nombre de red dentro de la raíz.
            nombre = arbol.etiqueta.split(":", 1)[1].strip()  # Extrae únicamente el identificador situado después de los dos puntos.

            if nombre:  # Comprueba que realmente exista algún texto utilizable.
                return nombre  # Utiliza directamente el nombre de la red como pestaña.

        return f"Árbol {indice}"  # Usa una numeración estable cuando la raíz no incluye un nombre explícito.

    def _guardar_png(self, escena: QGraphicsScene, nombre: str) -> None:  # Exporta una escena completa sin depender de la región actualmente visible.
        ruta, _filtro = QFileDialog.getSaveFileName(self, "Guardar árbol sintáctico", f"Arbol_{nombre}.png", "Imagen PNG (*.png)")  # Solicita al usuario la ubicación final del archivo.

        if not ruta:  # Comprueba si el usuario canceló el cuadro de guardado.
            return  # Finaliza sin crear ningún archivo.

        if not ruta.lower().endswith(".png"):  # Comprueba que la extensión haya sido incluida manualmente.
            ruta += ".png"  # Agrega PNG para mantener el formato esperado.

        limites = escena.itemsBoundingRect().adjusted(-30, -30, 30, 30)  # Incluye un pequeño margen exterior alrededor del árbol completo.
        ancho = max(int(limites.width()), 1)  # Calcula el ancho de imagen evitando dimensiones nulas.
        alto = max(int(limites.height()), 1)  # Calcula la altura de imagen evitando dimensiones nulas.

        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)  # Crea una imagen capaz de contener toda la escena.
        imagen.fill(QColor("#181825"))  # Utiliza el mismo fondo oscuro de la representación gráfica.

        pintor = QPainter(imagen)  # Crea el pintor utilizado para copiar la escena dentro de la imagen.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Mantiene curvas y líneas suaves también en el archivo exportado.
        escena.render(pintor, QRectF(0, 0, ancho, alto), limites)  # Renderiza la escena completa independientemente del zoom actual.
        pintor.end()  # Finaliza explícitamente el pintado antes de escribir el archivo.

        imagen.save(ruta, "PNG")  # Guarda finalmente la representación gráfica utilizando el formato PNG.