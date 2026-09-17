# ============================================================
# Archivo: aplicador_tema_componentes.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Atiende componentes especiales cuya apariencia no puede
# depender exclusivamente del stylesheet global.
#
# Centraliza:
# - Área de números de línea.
# - Línea activa del editor.
# - Colores de diagnósticos.
# - Filas especiales de tablas.
# - Árbol sintáctico.
# - Iconos dependientes del tema.
# - Tarjetas y superficies especiales de Configuración.
# - Ventana independiente de advertencias.
# - Selector de Media pantalla.
# ============================================================

from types import MethodType  # Permite sustituir proveedores internos de color sin reescribir clases completas.
from PySide6.QtCore import QEvent, QTimer, Qt  # Proporciona eventos, temporización y opciones generales.
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap, QTextFormat  # Proporciona pintura, iconos y formatos.
from PySide6.QtWidgets import QApplication, QFrame, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QLabel, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QTableWidget, QTextEdit, QWidget  # Proporciona componentes especiales y políticas de tamaño para evitar desbordamiento horizontal.
from Interfaz.recursos_tema import resolver_icono_tema  # Resuelve recursos oscuros o claros.
from Motor.catalogo_temas import TEMA_PREDETERMINADO, obtener_tema  # Proporciona la paleta activa.
from Motor.diagnosticos import ESTADO_DIAGNOSTICO_DISPONIBLE, obtener_catalogo_diagnosticos  # Proporciona información formal de diagnósticos.


def color_categoria_tema(paleta: dict, categoria: str) -> QColor:
    categoria_normalizada = str(categoria).casefold()  # Normaliza el texto antes de compararlo.
    if "advertencia" in categoria_normalizada: return QColor(paleta["advertencia"])  # Conserva el significado amarillo o ámbar.
    if "léxico" in categoria_normalizada or "lexico" in categoria_normalizada: return QColor(paleta["error"])  # Conserva rojo para léxico.
    if "sintáctico" in categoria_normalizada or "sintactico" in categoria_normalizada: return QColor(paleta["sintactico"])  # Conserva naranja para sintaxis.
    if "semántico" in categoria_normalizada or "semantico" in categoria_normalizada: return QColor(paleta["semantico"])  # Conserva violeta para semántica.
    return QColor(paleta["texto"])  # Utiliza texto normal para categorías futuras desconocidas.


def color_diagnostico_tema(paleta: dict, diagnostico) -> QColor:
    severidad = str(getattr(diagnostico, "severidad", "")).casefold()  # Recupera la severidad de forma segura.
    if severidad in ("warning", "advertencia"): return QColor(paleta["advertencia"])  # Da prioridad al significado de advertencia.
    return color_categoria_tema(paleta, getattr(diagnostico, "categoria", ""))  # Utiliza después la categoría formal.


class AplicadorTemaComponentes(QWidget):  # Actúa como auxiliar persistente vinculado con la ventana principal.

    def __init__(self, ventana):
        super().__init__(ventana)  # Vincula el ciclo de vida del auxiliar con TecNet Finder.
        self.hide()  # Mantiene el componente completamente invisible.
        self.ventana = ventana  # Conserva acceso a editor y resultados.
        self.tema_id = TEMA_PREDETERMINADO  # Utiliza un tema seguro antes de aplicar preferencias.
        self.paleta = obtener_tema(self.tema_id)  # Conserva la paleta utilizada por dibujos especiales.
        self.editor = self.ventana.editor_codigo  # Recupera el editor una única vez.
        self.editor.area_numeros_linea.installEventFilter(self)  # Sustituye el gutter rígido por uno temático.
        self.editor.cursorPositionChanged.connect(self._actualizar_linea_activa)  # Mantiene actualizado el fondo de la línea activa.
        self.editor.textChanged.connect(self._actualizar_linea_activa)  # Mantiene el resaltado después de modificar código.

        def color_editor_tematico(_editor, diagnostico):
            return color_diagnostico_tema(self.paleta, diagnostico)  # Utiliza los colores semánticos pertenecientes con el tema vigente.

        self.editor._color_diagnostico = MethodType(color_editor_tematico, self.editor)  # Sustituye solamente el proveedor de color del editor.
        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_actualizacion_resultados)  # Recolorea elementos generados al compilar.

    # ========================================================
    # Aplicación general
    # ========================================================

    def aplicar(self, tema_id: str) -> None:
        self.tema_id = tema_id  # Conserva la variante confirmada.
        self.paleta = obtener_tema(tema_id)  # Recupera todos sus colores.
        self._actualizar_linea_activa()  # Sincroniza la línea actual.
        self.editor.area_numeros_linea.update()  # Solicita repintar el gutter.
        self.editor.viewport().update()  # Redibuja código y diagnósticos.
        self._aplicar_resultados()  # Actualiza resultados existentes.
        self._aplicar_diagnosticos()  # Actualiza Detectados y Catálogo.
        self._aplicar_arboles()  # Actualiza escenas sintácticas.
        self._aplicar_iconos_resultados()  # Actualiza recursos gráficos.

        aplicacion = QApplication.instance()  # Recupera ventanas auxiliares existentes.
        if aplicacion is not None:
            for ventana in aplicacion.topLevelWidgets(): self.aplicar_ventana_dinamica(ventana, tema_id)  # Sincroniza cualquier ventana secundaria creada.

    def _programar_actualizacion_resultados(self, *_argumentos) -> None:
        QTimer.singleShot(0, self.reaplicar_resultados)  # Espera a que PanelResultados termine de llenar sus componentes.

    def reaplicar_resultados(self) -> None:
        self._aplicar_resultados()  # Recolorea filas especiales.
        self._aplicar_diagnosticos()  # Recolorea diagnósticos recién generados.
        self._aplicar_arboles()  # Recolorea árboles recién creados.
        self._aplicar_iconos_resultados()  # Reafirma recursos dependientes del tema.

    # ========================================================
    # Filtro de eventos
    # ========================================================

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.editor.area_numeros_linea and evento.type() == QEvent.Type.Paint:
            self._pintar_numeros_linea(evento)  # Sustituye completamente el dibujo rígido original del gutter.
            return True  # Impide que EditorCodigo vuelva a dibujar encima.

        return super().eventFilter(objeto, evento)  # Conserva el resto del comportamiento de Qt.

    # ========================================================
    # Editor
    # ========================================================

    def _pintar_numeros_linea(self, evento) -> None:
        editor = self.editor  # Utiliza un alias local para mantener compacto el procedimiento.
        pintor = QPainter(editor.area_numeros_linea)  # Crea el pintor sobre el gutter.
        pintor.fillRect(evento.rect(), QColor(self.paleta["editor_gutter"]))  # Utiliza el fondo específico del tema.
        pintor.setPen(QColor(self.paleta["texto_deshabilitado"]))  # Utiliza un tono secundario para los números.
        bloque = editor.firstVisibleBlock()  # Recupera la primera línea visible.
        numero_bloque = bloque.blockNumber()  # Obtiene su índice interno.
        superior = int(editor.blockBoundingGeometry(bloque).translated(editor.contentOffset()).top())  # Calcula la posición superior.
        inferior = superior + int(editor.blockBoundingRect(bloque).height())  # Calcula el límite inferior.

        while bloque.isValid() and superior <= evento.rect().bottom():
            if bloque.isVisible() and inferior >= evento.rect().top():
                numero = str(numero_bloque + 1)  # Convierte el índice a numeración humana.
                pintor.drawText(0, superior, editor.area_numeros_linea.width() - 6, editor.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, numero)  # Dibuja el número alineado a la derecha.
            bloque = bloque.next()  # Avanza al siguiente bloque.
            superior = inferior  # Utiliza el final anterior como nuevo comienzo.
            inferior = superior + int(editor.blockBoundingRect(bloque).height())  # Calcula el siguiente límite.
            numero_bloque += 1  # Incrementa la numeración.

        pintor.end()  # Finaliza explícitamente la operación de pintura.

    def _actualizar_linea_activa(self, *_argumentos) -> None:
        selecciones = []  # Prepara la colección esperada por QPlainTextEdit.
        if not self.editor.isReadOnly() and not self.editor.document().isEmpty():
            seleccion = QTextEdit.ExtraSelection()  # Crea una selección solamente visual.
            seleccion.format.setBackground(QColor(self.paleta["editor_linea_activa"]))  # Utiliza el color del tema.
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)  # Extiende el fondo a toda la línea.
            seleccion.cursor = self.editor.textCursor()  # Utiliza el cursor real.
            seleccion.cursor.clearSelection()  # Evita seleccionar caracteres concretos.
            selecciones.append(seleccion)  # Incorpora la línea activa.
        self.editor.setExtraSelections(selecciones)  # Sustituye el resaltado rígido original.

    # ========================================================
    # Resultados
    # ========================================================

    def _aplicar_resultados(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera todas las tablas de resultados.

        for tabla in panel.findChildren(QTableWidget):
            for fila in range(tabla.rowCount()):
                if tabla.columnCount() <= 0 or tabla.columnSpan(fila, 0) < tabla.columnCount(): continue  # Atiende únicamente franjas combinadas.
                item = tabla.item(fila, 0)  # Recupera la celda principal.
                if item is None: continue  # Protege filas incompletas.
                item.setForeground(QBrush(QColor(self.paleta["acento"])))  # Utiliza el acento vigente.
                item.setBackground(QBrush(QColor(self.paleta["superficie"])))  # Utiliza una superficie compatible con el tema.

        tabla_advertencias = getattr(panel, "tabla_advertencias_vlsm", None)  # Recupera la tabla compacta opcional.
        if tabla_advertencias is not None:
            for fila in range(tabla_advertencias.rowCount()):
                for columna in range(tabla_advertencias.columnCount()):
                    item = tabla_advertencias.item(fila, columna)  # Recupera la celda actual.
                    if item is not None: item.setForeground(QBrush(QColor(self.paleta["advertencia"])))  # Adapta el amarillo a cada modo.

        contador = getattr(panel, "contador_advertencias_vlsm", None)  # Recupera el contador compacto.
        if contador is not None: contador.setStyleSheet(f"color: {self.paleta['advertencia']}; font-weight: 700;")  # Evita conservar un color propio del modo oscuro.

    # ========================================================
    # Diagnósticos
    # ========================================================

    def _aplicar_diagnosticos(self) -> None:
        panel = self.ventana.panel_diagnosticos  # Recupera el panel estructurado.
        tabla_detectados = panel.tabla_detectados  # Recupera los diagnósticos actuales.

        for fila, diagnostico in enumerate(panel.diagnosticos_actuales):
            color = color_diagnostico_tema(self.paleta, diagnostico)  # Calcula el color apropiado.
            if fila >= tabla_detectados.rowCount(): break  # Evita acceder fuera de la tabla.
            for columna in range(tabla_detectados.columnCount()):
                item = tabla_detectados.item(fila, columna)  # Recupera cada celda.
                if item is not None: item.setForeground(QBrush(color))  # Mantiene la misma semántica en toda la fila.

        for codigo, informacion in obtener_catalogo_diagnosticos():
            fila = panel.filas_catalogo.get(codigo)  # Recupera la posición del código.
            if fila is None or fila >= panel.tabla_catalogo.rowCount(): continue  # Omite elementos todavía no construidos.
            color_categoria = color_categoria_tema(self.paleta, informacion["categoria"])  # Adapta su categoría.
            color_estado = QColor(self.paleta["exito"] if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE else self.paleta["advertencia"])  # Distingue disponible y reservado.

            for columna in range(panel.tabla_catalogo.columnCount()):
                item = panel.tabla_catalogo.item(fila, columna)  # Recupera la celda.
                if item is not None: item.setForeground(QBrush(color_estado if columna == 2 else color_categoria))  # Utiliza el color de Estado únicamente en su columna.

        tabla_detectados.viewport().update()  # Redibuja también delegados personalizados.
        panel.tabla_catalogo.viewport().update()  # Actualiza el catálogo.

    # ========================================================
    # Árbol sintáctico
    # ========================================================

    def _aplicar_arboles(self) -> None:
        visor = getattr(self.ventana.panel_resultados, "visor_arbol", None)  # Recupera el visor si ya existe.
        if visor is None: return  # Finaliza cuando la sección todavía no fue construida.

        for escena in visor.escenas:
            escena.setBackgroundBrush(QBrush(QColor(self.paleta["editor"])))  # Adapta el fondo de la escena.
            elipses = [item for item in escena.items() if isinstance(item, QGraphicsEllipseItem)]  # Recupera todos los nodos.
            superior_raiz = min((item.sceneBoundingRect().top() for item in elipses), default=None)  # Localiza el primer nivel.

            for item in escena.items():
                if isinstance(item, QGraphicsLineItem):
                    lapiz = item.pen()  # Conserva ancho y demás propiedades.
                    lapiz.setColor(QColor(self.paleta["acento"]))  # Adapta el color de la conexión.
                    item.setPen(lapiz)  # Reasigna el lápiz actualizado.
                elif isinstance(item, QGraphicsEllipseItem):
                    es_raiz = superior_raiz is not None and abs(item.sceneBoundingRect().top() - superior_raiz) < 0.5  # Reconoce la raíz.
                    item.setBrush(QBrush(QColor(self.paleta["superficie_hover"] if es_raiz else self.paleta["superficie"])))  # Diferencia visualmente la raíz.
                    lapiz = item.pen()  # Recupera el contorno existente.
                    lapiz.setColor(QColor(self.paleta["acento"]))  # Utiliza el acento como borde.
                    item.setPen(lapiz)  # Aplica el borde actualizado.
                elif isinstance(item, QGraphicsTextItem):
                    item.setDefaultTextColor(QColor(self.paleta["texto"]))  # Mantiene texto legible sobre cualquier variante.

            escena.update()  # Solicita redibujar toda la representación.

    # ========================================================
    # Iconos de resultados
    # ========================================================

    def _aplicar_iconos_resultados(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera botones y carpeta de recursos.
        relaciones = (
            ("boton_analizar", "Compilar.png"),
            ("boton_exportar_excel", "Exportar_excel.png"),
            ("boton_exportar_reporte", "Exportar_reporte.png"),
            ("boton_limpiar", "Limpiar.png"),
            ("boton_copiar_analisis", "Copiar.png"),
            ("boton_copiar_diagnosticos", "Copiar.png"),
        )  # Relaciona cada botón conocido con su recurso original.

        for atributo, nombre in relaciones:
            boton = getattr(panel, atributo, None)  # Recupera el botón solamente cuando exista.
            if boton is None: continue  # Mantiene compatibilidad con otras versiones.
            ruta = resolver_icono_tema(nombre, self.tema_id)  # Resuelve el icono mediante la ubicación central sin depender de PanelResultados.
            if ruta.exists(): boton.setIcon(QIcon(str(ruta)))  # Sustituye únicamente el gráfico.

        visor = getattr(panel, "visor_arbol", None)  # Recupera el visor gráfico.
        if visor is not None:
            ruta_guardar = resolver_icono_tema("Guardar.png", self.tema_id)  # Obtiene la variante adecuada del icono Guardar mediante el resolvedor central.
            if ruta_guardar.exists():
                for boton in visor.findChildren(QPushButton):
                    if boton.objectName() == "BotonGuardarArbol": boton.setIcon(QIcon(str(ruta_guardar)))  # Actualiza solamente los botones flotantes de guardado del árbol.

    # ========================================================
    # Ventanas dinámicas
    # ========================================================

    def aplicar_ventana_dinamica(self, ventana: QWidget, tema_id: str | None = None) -> None:
        if tema_id is not None:
            self.tema_id = tema_id  # Sincroniza el identificador.
            self.paleta = obtener_tema(tema_id)  # Recupera su paleta.

        nombre = ventana.objectName()  # Identifica el componente especial.
        if nombre == "VentanaConfiguracion": self._aplicar_configuracion(ventana)  # Tematiza Configuración.
        elif nombre == "VentanaAdvertencias": self._aplicar_ventana_advertencias(ventana)  # Tematiza Advertencias.
        elif nombre == "SelectorMediaPantalla": self._aplicar_selector_media_pantalla(ventana)  # Tematiza Snap.

    # ========================================================
    # Configuración
    # ========================================================

    def _aplicar_configuracion(self, ventana) -> None:
        p = self.paleta  # Utiliza un alias corto.

        ventana.setStyleSheet(f"""
            QDialog#VentanaConfiguracion {{
                background-color: transparent;
            }}

            QFrame#TarjetaConfiguracion {{
                background-color: {p["panel"]};
                border: 1px solid {p["borde_fuerte"]};
                border-radius: 8px;
            }}

            QFrame#TarjetaConfiguracion QLabel {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 2px 5px;
            }}

            QListWidget#ListaConfiguracion::item:hover {{
                background-color: {p["superficie"]};
                color: {p["texto"]};
            }}

            QListWidget#ListaConfiguracion::item:selected {{
                background-color: {p["superficie_hover"]};
                color: {p["acento"]};
            }}

            QListWidget#ListaConfiguracion::item:selected:hover {{
                background-color: {p["superficie_hover"]};
                color: {p["acento"]};
            }}

            QScrollBar:vertical {{
                background-color: transparent;
                width: 11px;
                margin: 4px 2px;
                border: none;
            }}

            QScrollBar::handle:vertical {{
                background-color: {p["superficie_hover"]};
                min-height: 34px;
                border: none;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {p["superficie_presionada"]};
            }}

            QScrollBar::handle:vertical:pressed {{
                background-color: {p["acento"]};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                background-color: transparent;
                border: none;
                height: 0px;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background-color: transparent;
                border: none;
            }}
        """)  # Define solamente las particularidades visuales de este diálogo.

        for tarjeta in ventana.findChildren(QFrame, "TarjetaConfiguracion"):
            tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que cada tarjeta pinte realmente su superficie y su contorno.
            tarjeta.setMinimumWidth(0)  # Permite que la tarjeta se contraiga hasta el ancho real del viewport sin crear desplazamiento horizontal.
            tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # Hace que cada tarjeta use el ancho disponible en lugar de imponer el tamaño sugerido por textos largos.
            tarjeta.setStyleSheet(f"""
                QFrame#TarjetaConfiguracion {{
                    background-color: {p["panel"]};
                    border: 1px solid {p["borde_fuerte"]};
                    border-radius: 8px;
                }}
                QFrame#TarjetaConfiguracion QLabel {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                    padding: 2px 5px;
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoCorrecto,
                QFrame#TarjetaConfiguracion QLabel#EstadoAdvertencia,
                QFrame#TarjetaConfiguracion QLabel#EstadoError,
                QFrame#TarjetaConfiguracion QLabel#EstadoNeutral {{
                    border-radius: 6px;
                    padding: 7px 9px;
                    font-weight: bold;
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoCorrecto {{
                    background-color: {p["panel"]};
                    color: {p["exito"]};
                    border: 1px solid {p["exito"]};
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoAdvertencia {{
                    background-color: {p["panel"]};
                    color: {p["advertencia"]};
                    border: 1px solid {p["advertencia"]};
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoError {{
                    background-color: {p["panel"]};
                    color: {p["error"]};
                    border: 1px solid {p["error"]};
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoNeutral {{
                    background-color: {p["panel"]};
                    color: {p["texto"]};
                    border: 1px solid {p["borde_fuerte"]};
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoIACorrecto,
                QFrame#TarjetaConfiguracion QLabel#EstadoIAAdvertencia,
                QFrame#TarjetaConfiguracion QLabel#EstadoIANeutral,
                QFrame#TarjetaConfiguracion QLabel#DetalleIA {{
                    border-radius: 6px;
                    padding: 7px 9px;
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoIACorrecto {{
                    background-color: {p["superficie_suave"]};
                    color: {p["exito"]};
                    border: 1px solid {p["exito"]};
                    font-weight: bold;
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoIAAdvertencia {{
                    background-color: {p["superficie_suave"]};
                    color: {p["advertencia"]};
                    border: 1px solid {p["advertencia"]};
                    font-weight: bold;
                }}
                QFrame#TarjetaConfiguracion QLabel#EstadoIANeutral {{
                    background-color: {p["superficie_suave"]};
                    color: {p["texto_secundario"]};
                    border: 1px solid {p["borde_fuerte"]};
                    font-weight: bold;
                }}
                QFrame#TarjetaConfiguracion QLabel#DetalleIA {{
                    background-color: {p["superficie"]};
                    color: {p["texto"]};
                    border: 1px solid {p["borde"]};
                }}
            """)  # Recupera el borde exterior de cada tarjeta y los recuadros interiores de etiquetas especiales sin tocar la lógica de casillas.

        for etiqueta in ventana.findChildren(QLabel):
            if etiqueta.objectName() not in ("DescripcionConfiguracion", "TextoConfiguracion"): continue  # Atiende solamente explicaciones y textos de opciones capaces de superar el ancho disponible.
            etiqueta.setWordWrap(True)  # Permite que cualquier texto largo continúe en la línea siguiente en lugar de ensanchar el panel completo.
            etiqueta.setMinimumWidth(0)  # Elimina mínimos derivados del sizeHint que podrían forzar un ancho superior al viewport.
            etiqueta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # Aprovecha el ancho disponible y conserva solamente la altura que necesite el texto envuelto.

        marco = getattr(ventana, "marco_ventana", None)  # Recupera el marco exterior.
        if marco is not None: marco.setStyleSheet(f"QFrame#MarcoVentanaConfiguracion {{ background-color: {p['fondo']}; border: 1px solid {p['borde_fuerte']}; border-radius: 14px; }}")  # Conserva un borde visible tanto en claro como en oscuro.

        paneles = getattr(ventana, "paneles", None)  # Recupera el QStackedWidget.
        if paneles is not None: paneles.setStyleSheet(f"QStackedWidget#PanelesConfiguracion {{ background-color: {p['fondo']}; border: none; }}")  # Evita islas pertenecientes a otro tema.

        for marco_administracion in ventana.findChildren(QFrame, "MarcoAdministracionIA"):
            marco_administracion.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Obliga a Qt a dibujar realmente el fondo redondeado.
            marco_administracion.setStyleSheet(f"""
                QFrame#MarcoAdministracionIA {{
                    background-color: {p["superficie"]};
                    border: 1px solid {p["borde"]};
                    border-radius: 8px;
                }}
            """)  # Recupera el recuadro interior que agrupa botones o progreso dentro de Administración de IA.

        for zona_administracion in ventana.findChildren(QStackedWidget, "ZonaAdministracionIA"):
            zona_administracion.setStyleSheet("QStackedWidget#ZonaAdministracionIA { background-color: transparent; border: none; }")  # Evita que la pila cubra el marco redondeado con un rectángulo propio.
            for pagina in zona_administracion.findChildren(QWidget, "PaginaAdministracionIA"):
                pagina.setStyleSheet("QWidget#PaginaAdministracionIA { background-color: transparent; border: none; }")  # Mantiene transparentes las páginas internas.

        for area in ventana.findChildren(QScrollArea):
            if area.objectName() != "AreaDesplazamientoConfiguracion": continue  # Atiende exclusivamente las categorías de Configuración.
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Prohíbe explícitamente desplazamiento lateral porque todas las tarjetas deben adaptarse al viewport.
            area.setWidgetResizable(True)  # Reafirma que el panel interno debe seguir el ancho útil del área desplazable.
            area.setStyleSheet(f"QScrollArea#AreaDesplazamientoConfiguracion {{ background-color: {p['fondo']}; border: none; }} QScrollArea#AreaDesplazamientoConfiguracion > QWidget > QWidget {{ background-color: {p['fondo']}; }}")  # Sincroniza el scroll y su contenido.
            area.viewport().setStyleSheet(f"background-color: {p['fondo']}; border: none;")  # Sincroniza también el viewport interno.

            contenido = area.widget()  # Recupera el panel real.
            if contenido is not None:
                contenido.setMinimumWidth(0)  # Permite al panel comprimirse exactamente hasta el ancho del viewport.
                contenido.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # Evita que un texto largo convierta su sizeHint en un ancho obligatorio.
                contenido.setObjectName("ContenidoSeccionConfiguracion")  # Proporciona un identificador exclusivo.
                contenido.setStyleSheet(f"QWidget#ContenidoSeccionConfiguracion {{ background-color: {p['fondo']}; }}")  # Mantiene el fondo correcto detrás de todas las tarjetas.

        barra = getattr(ventana, "barra_titulo", None)  # Recupera la barra personalizada.
        if barra is not None:
            contenedor = barra.parentWidget()  # Recupera la superficie exterior de la cabecera.
            if contenedor is not None: contenedor.setStyleSheet(f"background-color: {p['panel']}; border: none; border-top-left-radius: 13px; border-top-right-radius: 13px;")  # Adapta la cabecera.

            barra.setStyleSheet("QWidget#BarraTitulo { background-color: transparent; border: none; } QLabel { background-color: transparent; border: none; } QLabel#TituloBarra { background-color: transparent; border: none; }")  # Mantiene limpia la estructura interna.
            ruta_engrane = resolver_icono_tema("Engrane.png", self.tema_id)  # Recupera el engrane apropiado sin consultar directamente la carpeta física.
            if ruta_engrane.exists(): barra.etiqueta_icono.setPixmap(QPixmap(str(ruta_engrane)).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))  # Adapta el icono del título.

            if barra.boton_cerrar is not None:
                barra.boton_cerrar.setStyleSheet("""
                    QPushButton#BotonCerrarConfiguracion { background-color: transparent; border: none; border-top-right-radius: 12px; padding: 0px; }
                    QPushButton#BotonCerrarConfiguracion:hover { background-color: #c42b1c; border: none; border-top-right-radius: 12px; }
                    QPushButton#BotonCerrarConfiguracion:pressed { background-color: #a52016; border: none; border-top-right-radius: 12px; }
                    QPushButton#BotonCerrarConfiguracion:disabled { background-color: transparent; border: none; border-top-right-radius: 12px; }
                """)  # Conserva rojo exclusivamente para la acción destructiva.

        pie = ventana.findChild(QFrame, "PieConfiguracion")  # Recupera el pie.
        if pie is not None: pie.setStyleSheet(f"QFrame#PieConfiguracion {{ background-color: {p['panel']}; border: none; border-top: 1px solid {p['borde_fuerte']}; border-bottom-left-radius: 13px; border-bottom-right-radius: 13px; }}")  # Conserva claramente la separación inferior.

        self._aplicar_casillas_configuracion(ventana)  # Fuerza un estado visual estable mediante :checked sin competir con las señales propias de cada casilla.
        self._aplicar_botones_administracion_ia(ventana)  # Recupera el aspecto real de Instalar y Desinstalar dentro de su página transparente.
        self._aplicar_separadores_un_pixel(ventana)  # Adapta los separadores rígidos.

    def _aplicar_casillas_configuracion(self, ventana: QWidget) -> None:
        p = self.paleta  # Utiliza la misma paleta que el resto de Configuración.
        estilo = f"""
            QPushButton {{ background-color: {p["editor"]}; color: {p["texto"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 6px; padding: 0px; font-family: "Segoe UI Symbol"; font-size: 12pt; font-weight: bold; }}
            QPushButton:hover {{ background-color: {p["superficie_hover"]}; border-color: {p["acento"]}; }}
            QPushButton:checked {{ background-color: {p["acento"]}; color: {p["texto_inverso"]}; border: 1px solid {p["acento"]}; }}
            QPushButton:checked:hover {{ background-color: {p["acento_hover"]}; color: {p["texto_inverso"]}; border-color: {p["acento_hover"]}; }}
            QPushButton:pressed {{ background-color: {p["superficie_presionada"]}; border-color: {p["acento"]}; }}
            QPushButton:disabled {{ background-color: {p["fondo_deshabilitado"]}; color: {p["texto_deshabilitado"]}; border: 1px solid {p["borde_deshabilitado"]}; }}
            QPushButton:checked:disabled {{ background-color: {p["superficie"]}; color: {p["texto_deshabilitado"]}; border: 1px solid {p["borde_deshabilitado"]}; }}
        """  # Define todos los estados mediante pseudoestados de Qt para que la apariencia siempre siga al valor lógico real.
        for boton in ventana.findChildren(QPushButton):
            if not boton.isCheckable() or boton.minimumWidth() != 24 or boton.maximumWidth() != 24 or boton.minimumHeight() != 24 or boton.maximumHeight() != 24: continue  # Limita el tratamiento exclusivamente a las casillas personalizadas de Configuración.
            boton.setStyleSheet(estilo)  # El estilo local tiene prioridad suficiente para conservar fondo azul y contorno en cualquier categoría.
            boton.setText("✓" if boton.isChecked() else "")  # Reafirma la marca sin cambiar ni duplicar la lógica de toggled existente.
            boton.update()  # Solicita el redibujado inmediato.

    def _aplicar_botones_administracion_ia(self, ventana: QWidget) -> None:
        p = self.paleta  # Utiliza un alias compacto de la paleta actual.
        for boton in ventana.findChildren(QPushButton):
            texto = boton.text().strip()  # Identifica únicamente las dos acciones administrativas por su etiqueta estable.
            if texto not in ("Instalar componente", "Desinstalar componente"): continue  # Evita alterar cualquier otro botón de Configuración.
            principal = texto == "Instalar componente"  # Mantiene Instalar como acción primaria y Desinstalar como acción secundaria.
            fondo = p["acento"] if principal else p["superficie"]  # Selecciona el fondo normal apropiado para cada jerarquía.
            color = p["texto_inverso"] if principal else p["texto"]  # Conserva contraste adecuado sobre el fondo normal.
            borde = p["acento"] if principal else p["borde_fuerte"]  # Mantiene un borde visible en ambos botones.
            fondo_hover = p["acento_hover"] if principal else p["superficie_hover"]  # Proporciona respuesta al hover.
            boton.setStyleSheet(f"""
                QPushButton {{ background-color: {fondo}; color: {color}; border: 1px solid {borde}; border-radius: 7px; padding: 8px 14px; font-weight: bold; }}
                QPushButton:hover {{ background-color: {fondo_hover}; border-color: {p["acento"]}; }}
                QPushButton:pressed {{ background-color: {p["superficie_presionada"]}; }}
                QPushButton:disabled {{ background-color: {p["fondo_deshabilitado"]}; color: {p["texto_deshabilitado"]}; border: 1px solid {p["borde_deshabilitado"]}; }}
            """)  # Aplica directamente la geometría visual para que la página transparente no los reduzca a texto flotante.
            boton.setMinimumHeight(34)  # Conserva una altura de botón real aun cuando cambie la tipografía general.

    # ========================================================
    # Advertencias
    # ========================================================

    def _aplicar_ventana_advertencias(self, ventana) -> None:
        p = self.paleta  # Recupera la paleta vigente.
        ruta_advertencia = resolver_icono_tema("Advertencia.png", self.tema_id)  # Recupera automáticamente la variante oscura o clara del icono de advertencia.
        if ruta_advertencia.exists(): ventana.setWindowIcon(QIcon(str(ruta_advertencia)))  # Actualiza también el icono del diálogo.

        marco = getattr(ventana, "marco", None)  # Recupera la superficie visible.
        if marco is not None:
            marco.setStyleSheet(f"""
                QFrame#MarcoVentanaAdvertencias {{
                    background-color: {p["fondo"]};
                    border: 1px solid {p["borde_fuerte"]};
                    border-radius: 14px;
                }}

                QFrame#TarjetaAdvertenciaIndependiente {{
                    background-color: {p["panel"]};
                    border: 1px solid {p["borde_fuerte"]};
                    border-radius: 8px;
                }}

                QFrame#TarjetaAdvertenciaIndependiente:hover {{
                    background-color: {p["superficie_suave"]};
                    border: 1px solid {p["advertencia"]};
                }}

                QFrame#TarjetaAdvertenciaIndependiente QLabel {{
                    background-color: transparent;
                    border: none;
                    border-radius: 0px;
                    padding: 2px 5px;
                }}

                QLabel#CodigoAdvertenciaIndependiente,
                QLabel#UbicacionAdvertenciaIndependiente,
                QLabel#TituloCampoAdvertenciaIndependiente,
                QLabel#TextoAdvertenciaIndependiente {{
                    border-radius: 6px;
                    padding: 6px 10px;
                }}

                QLabel#CodigoAdvertenciaIndependiente {{
                    background-color: {p["superficie"]};
                    color: {p["advertencia"]};
                    border: 1px solid {p["advertencia"]};
                    font-size: 11pt;
                    font-weight: bold;
                }}

                QLabel#UbicacionAdvertenciaIndependiente {{
                    background-color: {p["superficie"]};
                    color: {p["texto_secundario"]};
                    border: 1px solid {p["borde_fuerte"]};
                    font-weight: 600;
                }}

                QLabel#TituloCampoAdvertenciaIndependiente {{
                    background-color: {p["superficie"]};
                    color: {p["texto"]};
                    border: 1px solid {p["borde"]};
                    font-weight: bold;
                }}

                QLabel#TextoAdvertenciaIndependiente {{
                    background-color: {p["superficie_suave"]};
                    color: {p["texto"]};
                    border: 1px solid {p["borde"]};
                }}

                QScrollArea#AreaAdvertenciasIndependientes {{
                    background-color: {p["fondo"]};
                    border: none;
                }}

                QScrollArea#AreaAdvertenciasIndependientes > QWidget > QWidget {{
                    background-color: {p["fondo"]};
                }}
            """)  # Recupera deliberadamente el aspecto de tarjeta con borde que existía originalmente en el modo oscuro.

        for tarjeta in ventana.findChildren(QFrame, "TarjetaAdvertenciaIndependiente"):
            tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que la tarjeta pinte su contorno aunque el área desplazable tenga un stylesheet propio.
            tarjeta.setStyleSheet(f"""
                QFrame#TarjetaAdvertenciaIndependiente {{ background-color: {p["panel"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 8px; }}
                QFrame#TarjetaAdvertenciaIndependiente:hover {{ background-color: {p["superficie_suave"]}; border: 1px solid {p["advertencia"]}; }}
            """)  # Aplica el borde directamente sobre cada tarjeta para que sea visible tanto en oscuro como en claro.

        estilos_labels = {
            "CodigoAdvertenciaIndependiente": (p["superficie"], p["advertencia"], "bold"),  # Conserva el código destacado mediante el color semántico de advertencia.
            "UbicacionAdvertenciaIndependiente": (p["superficie"], p["texto_secundario"], "600"),  # Mantiene la ubicación como información secundaria claramente delimitada.
            "TituloCampoAdvertenciaIndependiente": (p["superficie"], p["texto"], "bold"),  # Presenta Mensaje y Solución como encabezados internos compactos.
            "TextoAdvertenciaIndependiente": (p["superficie_suave"], p["texto"], "normal"),  # Conserva el contenido sobre una superficie ligeramente diferenciada.
        }  # Centraliza los cuatro tratamientos internos para evitar reglas inconsistentes entre temas.
        for nombre, (fondo, color, peso) in estilos_labels.items():
            for etiqueta in ventana.findChildren(QLabel, nombre):
                etiqueta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Fuerza a Qt a recortar el fondo utilizando realmente el radio indicado.
                etiqueta.setStyleSheet(f"QLabel#{nombre} {{ background-color: {fondo}; color: {color}; border: none; border-radius: 7px; padding: 6px 10px; font-weight: {peso}; }}")  # Aplica el fondo redondeado directamente al QLabel para que una regla heredada no vuelva a cuadrarlo.

        area = getattr(ventana, "area_desplazamiento", None)  # Recupera el viewport interno.
        if area is not None: area.viewport().setStyleSheet(f"background-color: {p['fondo']}; border: none;")  # Evita restos de otro tema.

        barra = getattr(ventana, "barra_titulo", None)  # Recupera la cabecera.
        if barra is not None:
            contenedor = barra.parentWidget()  # Recupera la superficie exterior.
            if contenedor is not None: contenedor.setStyleSheet(f"background-color: {p['panel']}; border: none; border-top-left-radius: 13px; border-top-right-radius: 13px;")  # Adapta la cabecera.

            barra.setStyleSheet("QWidget#BarraTitulo { background-color: transparent; border: none; } QLabel { background-color: transparent; border: none; } QLabel#TituloBarra { background-color: transparent; border: none; }")  # Mantiene transparentes sus componentes.
            if ruta_advertencia.exists(): barra.etiqueta_icono.setPixmap(QPixmap(str(ruta_advertencia)).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))  # Adapta el icono pequeño.

            if barra.boton_cerrar is not None:
                barra.boton_cerrar.setStyleSheet("""
                    QPushButton#BotonCerrarAdvertencias { background-color: transparent; border: none; border-top-right-radius: 12px; padding: 0px; }
                    QPushButton#BotonCerrarAdvertencias:hover { background-color: #c42b1c; border: none; border-top-right-radius: 12px; }
                    QPushButton#BotonCerrarAdvertencias:pressed { background-color: #a52016; border: none; border-top-right-radius: 12px; }
                """)  # Conserva el comportamiento rojo de cierre.

        pie = ventana.findChild(QFrame, "PieVentanaAdvertencias")  # Recupera la región inferior.
        if pie is not None: pie.setStyleSheet(f"QFrame#PieVentanaAdvertencias {{ background-color: {p['panel']}; border: none; border-top: 1px solid {p['borde_fuerte']}; border-bottom-left-radius: 13px; border-bottom-right-radius: 13px; }}")  # Conserva una separación visible.

        self._aplicar_separadores_un_pixel(ventana)  # Corrige la línea bajo la barra.

    # ========================================================
    # Selector de Media pantalla
    # ========================================================

    def _aplicar_selector_media_pantalla(self, selector) -> None:
        p = self.paleta  # Recupera la paleta vigente.
        selector.setStyleSheet(f"""
            QFrame#SelectorMediaPantalla {{ background-color: {p["panel"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 12px; }}
            QWidget#ContenedorTarjetasMediaPantalla {{ background-color: transparent; border: none; }}
            QFrame#TarjetaMediaPantalla {{ background-color: {p["fondo"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 10px; }}
            QFrame#TarjetaMediaPantalla:hover {{ background-color: {p["superficie_suave"]}; border: 1px solid {p["acento"]}; }}
            QFrame#TarjetaMediaPantalla[activa="true"] {{ background-color: {p["superficie_suave"]}; border: 1px solid {p["semantico"]}; }}
            QFrame#PrevisualizacionMediaPantalla {{ background-color: {p["editor"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 8px; }}
            QFrame#MitadMediaPantallaActiva {{ background-color: {p["acento"]}; border: none; border-radius: 6px; }}
            QFrame#MitadMediaPantallaInactiva {{ background-color: {p["superficie"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 6px; }}
            QLabel#TituloTarjetaMediaPantalla {{ color: {p["texto"]}; background-color: transparent; border: none; font-weight: 600; }}
            QPushButton#BotonMaximizarDesdeSelector {{ background-color: {p["superficie"]}; color: {p["texto"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 8px; padding: 7px 12px; font-weight: 600; }}
            QPushButton#BotonMaximizarDesdeSelector:hover {{ background-color: {p["superficie_hover"]}; color: {p["texto"]}; border: 1px solid {p["acento"]}; }}
            QPushButton#BotonMaximizarDesdeSelector:pressed {{ background-color: {p["superficie_presionada"]}; border: 1px solid {p["semantico"]}; }}
            QPushButton#BotonMaximizarDesdeSelector:disabled {{ background-color: {p["fondo_deshabilitado"]}; color: {p["texto_deshabilitado"]}; border: 1px solid {p["borde_deshabilitado"]}; }}
        """)  # Mantiene completamente tematizado el selector de Snap.

    def _aplicar_separadores_un_pixel(self, ventana: QWidget) -> None:
        for marco in ventana.findChildren(QFrame):
            if marco.minimumHeight() == 1 and marco.maximumHeight() == 1: marco.setStyleSheet(f"background-color: {self.paleta['borde_fuerte']}; border: none;")  # Adapta exclusivamente líneas divisorias de un píxel.