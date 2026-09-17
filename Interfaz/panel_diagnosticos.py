# ============================================================
# Archivo: panel_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el panel encargado de mostrar los
# diagnósticos detectados y el catálogo general de códigos.
#
# Las soluciones oficiales permanecen intactas internamente y
# pueden sustituirse visualmente por explicaciones generadas por
# la IA local cuando el usuario pulsa el icono ubicado al inicio
# de la celda Solución y la función se encuentra habilitada.
#
# La tabla Detectados funciona como una vista de consulta sin
# selección visual de celdas. El doble clic sobre un diagnóstico
# permite navegar al fragmento correspondiente en el editor,
# mientras que la columna Solución conserva un icono interactivo
# independiente para solicitar una mejora mediante IA local.
#
# Detectados y Catálogo utilizan columnas responsivas. Cada
# columna conserva un ancho mínimo legible y, cuando no existe
# espacio suficiente, se habilita desplazamiento horizontal en
# lugar de comprimir excesivamente mensajes y soluciones.
# ============================================================



from PySide6.QtCore import QEvent, QRect, QSize, QTimer, Qt, Signal  # Importa eventos, geometría, tamaños, temporización, roles, alineaciones, cursores y navegación.
from PySide6.QtGui import QBrush, QColor, QFontMetrics, QIcon, QPalette  # Importa las herramientas utilizadas para colorear, medir texto y representar el icono de IA.
from PySide6.QtWidgets import QApplication, QAbstractItemView, QHeaderView, QStyle, QStyleOptionViewItem, QStyledItemDelegate, QTableWidget, QTableWidgetItem, QTabWidget  # Importa tablas, estilos y el delegado especializado de la columna Solución.

from AsistenteIA.control_diagnosticos_ia import ControlDiagnosticosIA  # Mejora soluciones en segundo plano sin intervenir en la detección formal.
from AsistenteIA.explicador_diagnosticos import ExplicadorDiagnosticos  # Permite relacionar cada resultado de IA con la identidad exacta del diagnóstico.
from Interfaz.recursos_tema import ruta_icono_oscuro  # Proporciona el indicador gráfico inicial utilizado por las soluciones asistidas mediante IA.
from Motor.diagnosticos import Diagnostico, ESTADO_DIAGNOSTICO_DISPONIBLE, obtener_catalogo_diagnosticos, texto_estado_diagnostico  # Importa el modelo y el catálogo centralizado de diagnósticos.


class TablaDiagnosticosResponsiva(QTableWidget):  # Conserva columnas legibles y habilita scroll horizontal cuando la ventana no ofrece espacio suficiente.
    def __init__(
        self,
        filas: int,
        columnas: int,
        anchos_minimos: list[int],
        pesos_expansion: list[float],
        padre=None,
    ):
        super().__init__(filas, columnas, padre)  # Inicializa la tabla convencional utilizada como base.
        self.anchos_minimos_columnas = anchos_minimos  # Conserva el espacio mínimo permitido para cada columna.
        self.pesos_expansion_columnas = pesos_expansion  # Define qué columnas deben aprovechar principalmente el espacio sobrante.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra desplazamiento solo cuando los mínimos ya no caben.
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite recorrer horizontalmente el contenido de forma continua.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Permite que Qt procese primero la nueva geometría.
        self._distribuir_columnas()  # Recalcula los anchos después de conocer el nuevo espacio visible.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt muestre primero la tabla.
        self._distribuir_columnas()  # Realiza la primera distribución utilizando su ancho real.

    def _distribuir_columnas(self) -> None:
        if len(self.anchos_minimos_columnas) != self.columnCount():  # Comprueba que cada columna posea un ancho mínimo.
            return

        if len(self.pesos_expansion_columnas) != self.columnCount():  # Comprueba que cada columna posea también un peso de expansión.
            return

        ancho_disponible = max(self.viewport().width() - 2, 1)  # Obtiene únicamente el espacio visible destinado a las columnas.
        ancho_minimo_total = sum(self.anchos_minimos_columnas)  # Calcula cuánto espacio necesitan las columnas para seguir siendo legibles.

        if ancho_disponible <= ancho_minimo_total:
            anchos = list(self.anchos_minimos_columnas)  # Conserva los mínimos y deja que Qt habilite el scroll horizontal.
        else:
            espacio_adicional = ancho_disponible - ancho_minimo_total  # Obtiene los píxeles que pueden utilizarse para expandir las columnas.
            suma_pesos = sum(self.pesos_expansion_columnas)  # Calcula el peso total de expansión.

            if suma_pesos <= 0:
                anchos = list(self.anchos_minimos_columnas)  # Mantiene únicamente los mínimos cuando ninguna columna fue marcada para expansión.
            else:
                anchos = []  # Acumula los anchos definitivos antes de aplicarlos.

                for minimo, peso in zip(
                    self.anchos_minimos_columnas[:-1],
                    self.pesos_expansion_columnas[:-1],
                ):
                    adicional = int(
                        espacio_adicional * peso / suma_pesos
                    )  # Reparte únicamente el espacio sobrante según la importancia visual de cada columna.
                    anchos.append(minimo + adicional)  # Conserva siempre el mínimo y agrega la expansión calculada.

                ancho_ultima = (
                    ancho_disponible - sum(anchos)
                )  # Entrega a la última columna los píxeles restantes producidos por redondeos.
                ancho_ultima = max(
                    ancho_ultima,
                    self.anchos_minimos_columnas[-1],
                )  # Impide que la última columna termine por debajo de su mínimo.
                anchos.append(ancho_ultima)  # Completa la distribución definitiva.

        for columna, ancho in enumerate(anchos):
            self.setColumnWidth(columna, ancho)  # Aplica los anchos calculados a la tabla real.


class DelegadoSolucionIA(QStyledItemDelegate):  # Dibuja el icono de IA arriba de la solución y convierte únicamente ese símbolo en una acción de clic simple.
    TAMANO_ICONO = 16  # Mantiene el indicador suficientemente visible sin competir con el contenido textual de la solución.
    TAMANO_ZONA_CLIC = 24  # Amplía ligeramente el área interactiva para que el icono resulte cómodo de pulsar.
    MARGEN = 5  # Separa el contenido de los bordes de la celda.
    SEPARACION = 5  # Mantiene distancia entre el icono y el texto de la solución.

    def __init__(self, panel, padre=None):
        super().__init__(padre)  # Vincula el delegado con la tabla sin alterar el modelo que conserva cada diagnóstico.
        self.panel = panel  # Permite consultar el estado efectivo de IA y solicitar la mejora de la fila pulsada.

    def rectangulo_interaccion_icono(self, rectangulo_celda: QRect) -> QRect:
        return QRect(rectangulo_celda.left() + self.MARGEN, rectangulo_celda.top() + self.MARGEN, self.TAMANO_ZONA_CLIC, self.TAMANO_ZONA_CLIC)  # Reserva la zona clickeable en la esquina superior izquierda de Solución.

    def _rectangulo_dibujo_icono(self, rectangulo_celda: QRect) -> QRect:
        zona = self.rectangulo_interaccion_icono(rectangulo_celda)  # Parte de la zona cómoda utilizada para recibir el clic.
        desplazamiento = (self.TAMANO_ZONA_CLIC - self.TAMANO_ICONO) // 2  # Calcula el centrado del PNG dentro del área interactiva mayor.
        return QRect(zona.left() + desplazamiento, zona.top() + desplazamiento, self.TAMANO_ICONO, self.TAMANO_ICONO)  # Sitúa el símbolo pequeño en la parte superior sin centrarlo verticalmente en toda la fila.

    def _mostrar_icono(self) -> bool:
        return self.panel.ia_habilitada and not self.panel.icono_asistente_ia.isNull()  # Solo reserva espacio cuando la función realmente puede utilizarse.

    def paint(self, pintor, opcion, indice) -> None:
        opcion_base = QStyleOptionViewItem(opcion)  # Copia el estilo recibido para conservar fondo, bordes y estados estándar de la tabla.
        self.initStyleOption(opcion_base, indice)  # Completa la copia con los datos reales de la celda actual.
        texto = opcion_base.text  # Conserva la solución antes de impedir que Qt la dibuje automáticamente.
        opcion_base.text = ""  # Evita duplicar el texto porque será representado manualmente con alineación superior.
        opcion_base.icon = QIcon()  # Evita que un icono heredado vuelva a aparecer centrado verticalmente.
        estilo = opcion.widget.style() if opcion.widget is not None else QApplication.style()  # Reutiliza exactamente el estilo vigente de TecNet Finder.
        estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, opcion_base, pintor, opcion.widget)  # Dibuja primero el fondo normal de la celda.

        margen_izquierdo = self.MARGEN  # Usa el margen normal cuando la IA no está disponible.
        if self._mostrar_icono():
            rectangulo_icono = self._rectangulo_dibujo_icono(opcion.rect)  # Calcula la posición superior del indicador.
            self.panel.icono_asistente_ia.paint(pintor, rectangulo_icono, Qt.AlignmentFlag.AlignCenter, QIcon.Mode.Normal, QIcon.State.Off)  # Dibuja el recurso sin modificar el contenido del item.
            margen_izquierdo += self.TAMANO_ZONA_CLIC + self.SEPARACION  # Reserva espacio lateral para impedir que el texto pase debajo del icono.

        rectangulo_texto = opcion.rect.adjusted(margen_izquierdo, self.MARGEN, -self.MARGEN, -self.MARGEN)  # Sitúa la solución desde la parte superior respetando el indicador cuando existe.
        color = indice.data(Qt.ItemDataRole.ForegroundRole)  # Recupera el mismo color asignado al diagnóstico por categoría o severidad.
        pintor.save()  # Conserva el estado utilizado por la tabla antes de personalizar texto y tipografía.
        pintor.setFont(opcion.font)  # Mantiene la fuente general utilizada por la interfaz.
        if isinstance(color, QBrush):
            pintor.setPen(color.color())  # Respeta exactamente el color del diagnóstico almacenado en el item.
        else:
            pintor.setPen(opcion.palette.color(QPalette.ColorRole.Text))  # Utiliza el color normal como respaldo cuando no existe un pincel específico.
        banderas_texto = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) | int(Qt.TextFlag.TextWordWrap)  # Combina alineación superior y ajuste de línea mediante el formato esperado por QPainter.
        pintor.drawText(rectangulo_texto, banderas_texto, texto)  # Dibuja la solución arriba y permite que continúe en varias líneas.
        pintor.restore()  # Devuelve el pintor al estado esperado por las demás celdas.

    def sizeHint(self, opcion, indice) -> QSize:
        ancho_celda = self.parent().columnWidth(indice.column()) if isinstance(self.parent(), QTableWidget) else max(opcion.rect.width(), 360)  # Usa el ancho real de Solución para calcular correctamente el ajuste de línea.
        espacio_icono = self.TAMANO_ZONA_CLIC + self.SEPARACION if self._mostrar_icono() else 0  # Descuenta únicamente el espacio utilizado por el botón visual cuando está disponible.
        ancho_texto = max(ancho_celda - (self.MARGEN * 2) - espacio_icono, 80)  # Garantiza una región mínima legible incluso durante redimensionamientos extremos.
        metricas = QFontMetrics(opcion.font)  # Mide la solución utilizando la misma tipografía visible.
        banderas_texto = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) | int(Qt.TextFlag.TextWordWrap)  # Reutiliza las mismas reglas visuales empleadas durante el dibujo real.
        rectangulo = metricas.boundingRect(QRect(0, 0, ancho_texto, 10000), banderas_texto, str(indice.data(Qt.ItemDataRole.DisplayRole) or ""))  # Calcula la altura necesaria para mostrar el texto completo.
        alto_icono = self.TAMANO_ZONA_CLIC + (self.MARGEN * 2) if self._mostrar_icono() else 0  # Conserva una altura suficiente para el indicador superior.
        return QSize(ancho_celda, max(rectangulo.height() + (self.MARGEN * 2), alto_icono))  # Entrega a la tabla la mayor altura requerida por texto o icono.

    def editorEvent(self, evento, modelo, opcion, indice) -> bool:
        if self._mostrar_icono() and evento.type() == QEvent.Type.MouseButtonRelease and evento.button() == Qt.MouseButton.LeftButton and self.rectangulo_interaccion_icono(opcion.rect).contains(evento.position().toPoint()):
            self.panel._solicitar_mejora_solucion(indice.row())  # Ejecuta la mejora únicamente cuando el clic simple ocurrió realmente sobre el icono.
            return True  # Consume el clic para impedir que la tabla interprete la misma acción como otra navegación.
        return super().editorEvent(evento, modelo, opcion, indice)  # Conserva el comportamiento habitual cuando la interacción ocurre fuera del indicador.


class PanelDiagnosticos(QTabWidget):  # Organiza diagnósticos detectados y catálogo general dentro de dos subpestañas.
    diagnostico_activado = Signal(object)  # Emite el diagnóstico asociado cuando el usuario solicita navegar hacia el código fuente.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el contenedor de pestañas.
        self.filas_catalogo: dict[str, int] = {}  # Relaciona cada código con su fila dentro del catálogo.
        self.diagnosticos_actuales: list[Diagnostico] = []  # Conserva la compilación vigente sin modificar sus soluciones oficiales.
        self.ia_habilitada = False  # Impide solicitar explicaciones hasta recibir el estado efectivo desde Configuración.
        self.codigo_catalogo_pendiente: str | None = None  # Retrasa el clic simple sobre Código para distinguirlo correctamente del doble clic.
        self.clave_solucion_pendiente: str | None = None  # Identifica la solución que actualmente espera una respuesta de IA.
        ruta_icono_ia = ruta_icono_oscuro("Asistente_ia.png")  # Localiza el recurso inicial de IA mediante la estructura centralizada de iconos.
        self.icono_asistente_ia = QIcon(str(ruta_icono_ia)) if ruta_icono_ia.exists() else QIcon()  # Conserva un icono vacío cuando el recurso no se encuentra disponible.

        self.tabla_detectados = TablaDiagnosticosResponsiva(
            0,
            6,
            [90, 110, 320, 70, 80, 360],
            [0.10, 0.10, 1.00, 0.05, 0.05, 1.15],
        )  # Mantiene compactas las columnas técnicas y reserva buen espacio para Mensaje y Solución.
        self.tabla_catalogo = TablaDiagnosticosResponsiva(
            0,
            6,
            [90, 100, 110, 220, 340, 380],
            [0.05, 0.05, 0.05, 0.35, 1.00, 1.10],
        )  # Evita que Descripción y Solución sugerida se conviertan en columnas excesivamente estrechas.
        self.control_diagnosticos_ia = ControlDiagnosticosIA(self)  # Prepara la generación asíncrona de explicaciones.
        self.delegado_solucion_ia = DelegadoSolucionIA(self, self.tabla_detectados)  # Administra dibujo superior y clic simple del icono exclusivamente dentro de Solución.
        self.tabla_detectados.setItemDelegateForColumn(5, self.delegado_solucion_ia)  # Sustituye únicamente la representación de la columna Solución sin modificar las demás celdas.

        self.temporizador_catalogo = QTimer(self)  # Permite diferenciar un clic simple de un doble clic sobre Código.
        self.temporizador_catalogo.setSingleShot(True)  # Ejecuta como máximo una apertura de catálogo por interacción.

        aplicacion = QApplication.instance()  # Consulta el intervalo de doble clic utilizado actualmente por el sistema.
        intervalo_doble_clic = aplicacion.doubleClickInterval() if aplicacion is not None else 250  # Utiliza un valor seguro durante pruebas aisladas.
        self.temporizador_catalogo.setInterval(max(150, intervalo_doble_clic))  # Espera el tiempo suficiente antes de interpretar un clic como simple.
        self.temporizador_catalogo.timeout.connect(self._abrir_codigo_catalogo_pendiente)  # Abre la ficha únicamente cuando no apareció un segundo clic.

        self._configurar_tabla_detectados()  # Prepara la vista de diagnósticos actuales.
        self._configurar_tabla_catalogo()  # Prepara la referencia general de códigos.
        self._cargar_catalogo()  # Carga los diagnósticos conocidos desde Motor.

        self.addTab(self.tabla_detectados, "Detectados")  # Coloca primero la vista correspondiente al análisis actual.
        self.addTab(self.tabla_catalogo, "Catálogo")  # Coloca después la referencia completa.

        self.tabla_detectados.cellClicked.connect(self._procesar_clic_detectado)  # Atiende únicamente la función especial del clic simple sobre Código.
        self.tabla_detectados.cellDoubleClicked.connect(self._activar_diagnostico)  # Gestiona navegación al editor o mejora mediante IA.
        self.control_diagnosticos_ia.soluciones_listas.connect(self._aplicar_soluciones_ia)  # Aplica solamente respuestas válidas de la compilación vigente.

    def _configurar_tabla_detectados(self) -> None:
        self.tabla_detectados.setHorizontalHeaderLabels(
            [
                "Código",
                "Categoría",
                "Mensaje",
                "Línea",
                "Columna",
                "Solución",
            ]
        )  # Define las columnas visibles de cada diagnóstico.

        self.tabla_detectados.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente cualquier diagnóstico.
        self.tabla_detectados.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)  # Convierte la tabla en una vista de consulta sin fondos de selección.
        self.tabla_detectados.setAlternatingRowColors(True)  # Facilita distinguir visualmente diagnósticos consecutivos.
        self.tabla_detectados.setWordWrap(True)  # Permite mostrar mensajes y soluciones extensos en varias líneas.
        self.tabla_detectados.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar contenido mediante puntos suspensivos.
        self.tabla_detectados.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Habilita scroll solamente cuando los mínimos no caben.
        self.tabla_detectados.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite recorrer suavemente las columnas.
        self.tabla_detectados.setIconSize(QSize(16, 16))  # Mantiene discreto el indicador visual de las funciones de IA dentro de Solución.
        self.tabla_detectados.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_detectados.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta cada fila según la cantidad de texto mostrada.
        self.tabla_detectados.setMouseTracking(True)  # Permite actualizar el cursor sin necesidad de pulsar.
        self.tabla_detectados.viewport().setMouseTracking(True)  # Activa el seguimiento directamente sobre el área de las celdas.
        self.tabla_detectados.viewport().installEventFilter(self)  # Permite representar Código como un enlace mediante el cursor.

        encabezado = self.tabla_detectados.horizontalHeader()  # Obtiene el encabezado para controlar el ancho de cada columna.
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Deja que la tabla responsiva administre todos los anchos.
        encabezado.setStretchLastSection(False)  # Evita que Solución absorba arbitrariamente el espacio restante.
        encabezado.setMinimumSectionSize(50)  # Impide que Qt reduzca internamente alguna columna hasta volverla ilegible.
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Mantiene los encabezados técnicos centrados.

    def _configurar_tabla_catalogo(self) -> None:
        self.tabla_catalogo.setHorizontalHeaderLabels(
            [
                "Código",
                "Tipo",
                "Estado",
                "Nombre",
                "Descripción",
                "Solución sugerida",
            ]
        )  # Define las columnas utilizadas por el catálogo general.

        self.tabla_catalogo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Mantiene el catálogo como contenido de solo lectura.
        self.tabla_catalogo.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Conserva la selección completa de fichas dentro del Catálogo.
        self.tabla_catalogo.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite consultar una sola ficha a la vez.
        self.tabla_catalogo.setAlternatingRowColors(True)  # Facilita distinguir los diagnósticos consecutivos.
        self.tabla_catalogo.setWordWrap(True)  # Permite mostrar completamente descripciones y soluciones.
        self.tabla_catalogo.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita recortar información.
        self.tabla_catalogo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra scroll cuando el catálogo necesita más espacio que el disponible.
        self.tabla_catalogo.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite explorar horizontalmente el catálogo de forma cómoda.
        self.tabla_catalogo.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_catalogo.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta cada ficha según su contenido.

        encabezado = self.tabla_catalogo.horizontalHeader()  # Obtiene el encabezado para administrar sus columnas.
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Deja todos los anchos bajo control de la tabla responsiva.
        encabezado.setStretchLastSection(False)  # Evita deformar Solución sugerida únicamente para rellenar espacio.
        encabezado.setMinimumSectionSize(50)  # Conserva un límite interno seguro para todas las secciones.
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Mantiene los títulos del catálogo centrados.

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.tabla_detectados.viewport():  # Comprueba que el evento pertenezca al área visible de Detectados.
            if evento.type() == QEvent.Type.MouseMove:
                indice = self.tabla_detectados.indexAt(evento.position().toPoint())  # Obtiene la celda situada debajo del cursor.

                sobre_codigo = indice.isValid() and indice.column() == 0  # Conserva la manita sobre Código porque continúa funcionando como enlace al catálogo.
                sobre_icono_ia = False  # Considera inicialmente que el puntero no se encuentra sobre la acción inteligente.
                if indice.isValid() and indice.column() == 5 and self.ia_habilitada:
                    rectangulo_celda = self.tabla_detectados.visualRect(indice)  # Obtiene la geometría real de la celda Solución actualmente visible.
                    sobre_icono_ia = self.delegado_solucion_ia.rectangulo_interaccion_icono(rectangulo_celda).contains(evento.position().toPoint())  # Activa la manita únicamente dentro del pequeño icono superior.
                self.tabla_detectados.viewport().setCursor(Qt.CursorShape.PointingHandCursor if sobre_codigo or sobre_icono_ia else Qt.CursorShape.ArrowCursor)  # Evita sugerir que toda la celda Solución es clickeable.

            elif evento.type() == QEvent.Type.Leave:
                self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Evita conservar la manita después de abandonar la tabla.

        return super().eventFilter(objeto, evento)  # Permite que Qt procese normalmente el resto de eventos.

    def establecer_ia_habilitada(self, habilitada: bool) -> None:
        nuevo_estado = bool(habilitada)  # Normaliza el valor recibido desde Configuración.

        if self.ia_habilitada == nuevo_estado:
            return  # Evita trabajo adicional cuando el estado efectivo no cambió.

        self.ia_habilitada = nuevo_estado  # Conserva la disponibilidad utilizada por futuras interacciones.
        self.control_diagnosticos_ia.establecer_habilitado(self.ia_habilitada)  # Sincroniza la capa asíncrona con Configuración.
        self._actualizar_ayudas_solucion()  # Actualiza los tooltips correspondientes a las soluciones oficiales.

        if not self.ia_habilitada:
            self.control_diagnosticos_ia.cancelar()  # Invalida cualquier generación iniciada antes de desactivar la función.
            self._restaurar_soluciones_oficiales()  # Recupera inmediatamente las soluciones deterministas.

    def _color_categoria(self, categoria: str) -> QColor:
        if categoria == "Advertencia":
            return QColor("#f9e2af")  # Utiliza amarillo para advertencias.

        if categoria == "Léxico":
            return QColor("#f38ba8")  # Utiliza rojo rosado para diagnósticos léxicos.

        if categoria == "Sintáctico":
            return QColor("#fab387")  # Utiliza naranja para diagnósticos sintácticos.

        if categoria == "Semántico":
            return QColor("#cba6f7")  # Utiliza violeta para diagnósticos semánticos.

        return QColor("#cdd6f4")  # Utiliza el color general para diagnósticos de otras categorías.

    def _color_diagnostico(self, diagnostico: Diagnostico) -> QColor:
        if diagnostico.severidad in ("warning", "advertencia"):
            return QColor("#f9e2af")  # Da prioridad visual al amarillo cuando se trata de una advertencia.

        return self._color_categoria(diagnostico.categoria)  # Utiliza el color asociado con la categoría del error.

    def _color_estado_catalogo(self, estado: str) -> QColor:
        if estado == ESTADO_DIAGNOSTICO_DISPONIBLE:
            return QColor("#a6e3a1")  # Utiliza verde para diagnósticos implementados actualmente.

        return QColor("#f9e2af")  # Utiliza amarillo para diagnósticos reservados para fases futuras.

    def _cargar_catalogo(self) -> None:
        self.tabla_catalogo.setRowCount(0)  # Elimina cualquier contenido anterior.
        self.filas_catalogo.clear()  # Reinicia las posiciones conocidas de cada código.

        for codigo, informacion in obtener_catalogo_diagnosticos():
            fila = self.tabla_catalogo.rowCount()  # Obtiene la siguiente posición libre.
            self.tabla_catalogo.insertRow(fila)  # Crea la fila correspondiente al diagnóstico.
            self.filas_catalogo[codigo] = fila  # Conserva su posición para posteriores accesos directos.

            valores = [
                codigo,
                informacion["categoria"],
                texto_estado_diagnostico(codigo),
                informacion["nombre"],
                informacion["descripcion"],
                informacion["solucion"],
            ]

            color_categoria = self._color_categoria(informacion["categoria"])  # Obtiene el color correspondiente al tipo de diagnóstico.
            color_estado = self._color_estado_catalogo(informacion["estado"])  # Obtiene el color correspondiente a su disponibilidad.

            for columna, valor in enumerate(valores):
                elemento = QTableWidgetItem(valor)  # Construye la celda con el texto correspondiente.
                elemento.setForeground(QBrush(color_estado if columna == 2 else color_categoria))  # Colorea Estado por disponibilidad y el resto por categoría.
                elemento.setToolTip(valor)  # Conserva el contenido completo disponible como ayuda contextual.

                if columna in (0, 1, 2, 3):
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra los campos compactos.
                else:
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Mantiene textos extensos alineados a la izquierda y centrados verticalmente.

                if columna == 0:
                    elemento.setData(Qt.ItemDataRole.UserRole, codigo)  # Conserva el identificador del diagnóstico dentro de su primera celda.

                self.tabla_catalogo.setItem(fila, columna, elemento)  # Inserta finalmente la celda construida.

        self.tabla_catalogo.resizeRowsToContents()  # Adapta las alturas al contenido completo.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:
        self.control_diagnosticos_ia.cancelar()  # Invalida cualquier mejora correspondiente a una compilación anterior.
        self.clave_solucion_pendiente = None  # Elimina relaciones con solicitudes anteriores.
        self.diagnosticos_actuales = list(diagnosticos)  # Conserva los diagnósticos oficiales de la compilación vigente.
        self.tabla_detectados.setRowCount(0)  # Elimina las filas pertenecientes al análisis anterior.

        for diagnostico in self.diagnosticos_actuales:
            fila = self.tabla_detectados.rowCount()  # Obtiene la siguiente posición disponible.
            self.tabla_detectados.insertRow(fila)  # Crea una nueva fila.
            color = self._color_diagnostico(diagnostico)  # Obtiene el color correspondiente al diagnóstico.

            valores = [
                diagnostico.codigo,
                diagnostico.categoria,
                diagnostico.mensaje,
                "" if diagnostico.linea is None else str(diagnostico.linea),
                "" if diagnostico.columna is None else str(diagnostico.columna),
                diagnostico.solucion,
            ]

            for columna, valor in enumerate(valores):
                elemento = QTableWidgetItem(valor)  # Construye cada celda de la fila.
                elemento.setForeground(QBrush(color))  # Aplica el color propio del diagnóstico.
                elemento.setToolTip(valor)  # Conserva el contenido completo como tooltip.

                if columna in (0, 1, 3, 4):
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra Código, Categoría, Línea y Columna.
                else:
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Centra verticalmente Mensaje y Solución.

                if columna == 0:
                    elemento.setData(Qt.ItemDataRole.UserRole, diagnostico)  # Conserva el objeto completo para posteriores interacciones.
                    fuente_codigo = elemento.font()  # Obtiene la tipografía actualmente aplicada.
                    fuente_codigo.setUnderline(True)  # Subraya Código para representarlo como un enlace.
                    fuente_codigo.setBold(True)  # Refuerza ligeramente el identificador.
                    elemento.setFont(fuente_codigo)  # Aplica la apariencia interactiva.
                    elemento.setToolTip(
                        f"{diagnostico.codigo}\n\n"
                        "Clic: abrir este código en el catálogo.\n"
                        "Doble clic: ir al fragmento correspondiente en el código fuente."
                    )  # Explica las dos interacciones disponibles sobre Código.

                if columna == 5:
                    elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Explica la posibilidad de utilizar IA cuando corresponde.

                self.tabla_detectados.setItem(fila, columna, elemento)  # Inserta finalmente la celda en la tabla.

        self.tabla_detectados.resizeRowsToContents()  # Ajusta todas las filas según el contenido completo.

    def limpiar(self) -> None:
        self.control_diagnosticos_ia.cancelar()  # Invalida cualquier respuesta todavía pendiente.
        self.diagnosticos_actuales.clear()  # Elimina la relación con los diagnósticos anteriores.
        self.temporizador_catalogo.stop()  # Cancela cualquier apertura de catálogo todavía pendiente.
        self.codigo_catalogo_pendiente = None  # Elimina el código asociado con el clic anterior.
        self.clave_solucion_pendiente = None  # Elimina cualquier solicitud de mejora pendiente.
        self.tabla_detectados.setRowCount(0)  # Vacía la vista de diagnósticos actuales.
        self.tabla_catalogo.clearSelection()  # Elimina cualquier ficha previamente seleccionada.
        self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Recupera la flecha convencional.
        self.setCurrentWidget(self.tabla_detectados)  # Regresa a la vista principal del panel.

    def _aplicar_soluciones_ia(self, soluciones: dict) -> None:
        clave_pendiente = self.clave_solucion_pendiente  # Recupera la identidad solicitada mediante doble clic.
        self.clave_solucion_pendiente = None  # Libera la interacción antes de modificar la tabla.

        if not self.ia_habilitada or not clave_pendiente:
            return  # Descarta respuestas obsoletas o generadas después de desactivar la función.

        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            clave = ExplicadorDiagnosticos.clave_diagnostico(diagnostico)  # Obtiene la identidad utilizada por la caché.

            if clave != clave_pendiente:
                continue  # Mantiene intactas las demás filas.

            elemento = self.tabla_detectados.item(fila, 5)  # Recupera la celda Solución correspondiente.

            if elemento is None:
                return  # Finaliza si la tabla cambió durante la generación.

            solucion_ia = soluciones.get(clave_pendiente) if isinstance(soluciones, dict) else None  # Busca la respuesta asociada con la solicitud.
            elemento.setForeground(QBrush(self._color_diagnostico(diagnostico)))  # Recupera el color normal de la fila.

            if not isinstance(solucion_ia, str) or not solucion_ia.strip():
                elemento.setText(diagnostico.solucion)  # Recupera la solución oficial cuando la IA no produjo un resultado válido.
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Permite intentar nuevamente la mejora.
                self.tabla_detectados.resizeRowsToContents()  # Recupera la altura necesaria para la solución original.
                return

            elemento.setText(solucion_ia)  # Sustituye solamente la representación visual de la solución.
            elemento.setToolTip(
                "Solución mejorada con IA local.\n"
                "La solución oficial permanece intacta internamente.\n\n"
                f"Solución oficial:\n{diagnostico.solucion}"
            )  # Conserva accesible la recomendación oficial aunque visualmente se muestre la variante de IA.
            self.tabla_detectados.resizeRowsToContents()  # Ajusta la altura al contenido generado.
            return

    def _solicitar_mejora_solucion(self, fila: int) -> None:
        if not self.ia_habilitada:
            return  # Impide solicitar mejoras cuando la opción correspondiente está desactivada.

        if fila < 0 or fila >= len(self.diagnosticos_actuales):
            return  # Evita acceder a una fila que ya no pertenece a la compilación vigente.

        diagnostico = self.diagnosticos_actuales[fila]  # Obtiene el diagnóstico oficial asociado con la fila.
        clave = ExplicadorDiagnosticos.clave_diagnostico(diagnostico)  # Calcula la identidad utilizada por la capa de IA.

        if self.clave_solucion_pendiente == clave:
            return  # Evita repetir una solicitud que todavía se encuentra ejecutándose.

        self._restaurar_solucion_pendiente()  # Recupera cualquier solución anterior que permaneciera esperando una respuesta.
        self.clave_solucion_pendiente = clave  # Identifica qué celda podrá aceptar el resultado generado.

        elemento = self.tabla_detectados.item(fila, 5)  # Recupera la representación visual de Solución.

        if elemento is None:
            self.clave_solucion_pendiente = None  # Descarta la solicitud si la celda dejó de existir.
            return

        elemento.setText("Mejorando solución con IA...")  # Informa que la petición fue iniciada explícitamente.
        elemento.setToolTip("La IA local está preparando una versión más clara de esta solución.")  # Explica temporalmente el estado actual.
        self.tabla_detectados.resizeRowsToContents()  # Ajusta la fila al texto de espera.
        self.control_diagnosticos_ia.procesar([diagnostico])  # Envía únicamente el diagnóstico solicitado.

    def _restaurar_solucion_pendiente(self) -> None:
        clave_pendiente = self.clave_solucion_pendiente  # Conserva la identidad de la solicitud anterior.

        if not clave_pendiente:
            return  # Evita recorrer la tabla cuando no existe ninguna generación pendiente.

        self.control_diagnosticos_ia.cancelar()  # Hace obsoleta cualquier respuesta que todavía pudiera llegar.
        self.clave_solucion_pendiente = None  # Libera inmediatamente el estado pendiente.

        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            if ExplicadorDiagnosticos.clave_diagnostico(diagnostico) != clave_pendiente:
                continue  # Busca únicamente el diagnóstico relacionado con la solicitud cancelada.

            elemento = self.tabla_detectados.item(fila, 5)  # Recupera su celda Solución.

            if elemento is not None:
                elemento.setText(diagnostico.solucion)  # Recupera la recomendación oficial.
                elemento.setForeground(QBrush(self._color_diagnostico(diagnostico)))  # Recupera el color normal.
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Recupera la ayuda contextual original.

            break  # Finaliza porque cada clave pertenece a una sola fila.

        self.tabla_detectados.resizeRowsToContents()  # Recupera la altura apropiada de la fila.

    def _texto_ayuda_solucion(self, diagnostico: Diagnostico) -> str:
        texto = f"Solución oficial de TecNet Finder:\n{diagnostico.solucion}"  # Identifica siempre el origen determinista de la recomendación.

        if self.ia_habilitada:
            texto += "\n\nHaz clic en el icono de IA situado arriba a la izquierda para mejorar esta solución."  # Explica la nueva interacción sin convertir toda la celda en un botón.

        return texto  # Devuelve la ayuda correspondiente al estado actual.

    def _actualizar_ayudas_solucion(self) -> None:
        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            elemento = self.tabla_detectados.item(fila, 5)  # Obtiene la celda Solución correspondiente.

            if elemento is None:
                continue  # Ignora filas que todavía no poseen contenido.

            if elemento.text() == diagnostico.solucion:
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Actualiza únicamente las soluciones oficiales todavía visibles.

        self.tabla_detectados.resizeRowsToContents()  # Recalcula las alturas porque activar el icono reduce ligeramente el ancho disponible para el texto.
        self.tabla_detectados.viewport().update()  # Redibuja inmediatamente la columna para mostrar u ocultar el indicador superior.

    def _restaurar_soluciones_oficiales(self) -> None:
        self.clave_solucion_pendiente = None  # Invalida cualquier relación con una generación anterior.

        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            elemento = self.tabla_detectados.item(fila, 5)  # Recupera la celda que pudo mostrar contenido de IA.

            if elemento is None:
                continue  # Ignora filas que dejaron de existir.

            elemento.setText(diagnostico.solucion)  # Recupera exactamente la recomendación oficial.
            elemento.setForeground(QBrush(self._color_diagnostico(diagnostico)))  # Recupera el color correspondiente a la fila.
            elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Recupera la ayuda adecuada al nuevo estado.

        self.tabla_detectados.resizeRowsToContents()  # Ajusta nuevamente las alturas.

    def _procesar_clic_detectado(self, fila: int, columna: int) -> None:
        if columna != 0:
            self.temporizador_catalogo.stop()  # Cancela cualquier apertura anterior cuando la interacción ocurre fuera de Código.
            self.codigo_catalogo_pendiente = None  # Elimina la ficha pendiente.
            return  # Los demás clics simples no producen ninguna acción.

        elemento = self.tabla_detectados.item(fila, 0)  # Recupera Código, donde se conserva el diagnóstico completo.

        if elemento is None:
            return  # Finaliza cuando la fila no posee información.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el objeto estructurado asociado con la fila.

        if diagnostico is None:
            return  # Evita continuar con una fila incompleta.

        self.codigo_catalogo_pendiente = diagnostico.codigo  # Conserva temporalmente qué ficha deberá abrirse.
        self.temporizador_catalogo.start()  # Espera para comprobar si llegará un segundo clic.

    def _abrir_codigo_catalogo_pendiente(self) -> None:
        codigo = self.codigo_catalogo_pendiente  # Recupera la intención asociada con el clic simple.
        self.codigo_catalogo_pendiente = None  # Limpia el estado antes de cambiar la pestaña.

        if not codigo:
            return  # Evita actuar cuando el doble clic canceló previamente la operación.

        self._seleccionar_codigo_catalogo(codigo, cambiar_pestana=True)  # Abre finalmente la ficha correspondiente.

    def _seleccionar_codigo_catalogo(self, codigo: str, cambiar_pestana: bool) -> None:
        fila_catalogo = self.filas_catalogo.get(codigo)  # Localiza rápidamente la ficha correspondiente.

        if fila_catalogo is None:
            return  # Mantiene el panel intacto ante códigos desconocidos.

        self.tabla_catalogo.selectRow(fila_catalogo)  # Selecciona la ficha completa dentro de la vista Catálogo.
        elemento_catalogo = self.tabla_catalogo.item(fila_catalogo, 0)  # Recupera su primera celda para poder centrarla.

        if elemento_catalogo is not None:
            self.tabla_catalogo.scrollToItem(
                elemento_catalogo,
                QAbstractItemView.ScrollHint.PositionAtCenter,
            )  # Desplaza la tabla hasta que la ficha quede visible en una posición cómoda.

        if cambiar_pestana:
            self.setCurrentWidget(self.tabla_catalogo)  # Cambia de Detectados a Catálogo cuando la interacción fue un clic simple sobre Código.

    def _activar_diagnostico(self, fila: int, columna: int) -> None:
        self.temporizador_catalogo.stop()  # Cancela cualquier apertura del catálogo todavía pendiente.
        self.codigo_catalogo_pendiente = None  # Confirma que la interacción actual corresponde con un doble clic.

        if columna == 5 and self.ia_habilitada:
            return  # Reserva Solución para el icono de clic simple y evita que un doble clic accidental navegue al editor.

        elemento = self.tabla_detectados.item(fila, 0)  # Recupera Código, donde se conserva el diagnóstico completo.

        if elemento is None:
            return  # Finaliza si la fila dejó de existir.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el objeto estructurado correspondiente.

        if diagnostico is None:
            return  # Evita navegar cuando no existe información asociada.

        QTimer.singleShot(
            0,
            lambda diagnostico=diagnostico: self.diagnostico_activado.emit(diagnostico),
        )  # Devuelve el foco al editor después de que Qt termine de procesar completamente el doble clic.