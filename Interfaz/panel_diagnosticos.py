# ============================================================
# Archivo: panel_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el panel encargado de mostrar los
# diagnósticos detectados y el catálogo general de códigos.
#
# Los códigos detectados funcionan como enlaces hacia su ficha
# del catálogo, mientras que el doble clic sobre un diagnóstico
# conserva la navegación hacia su posición en el código fuente.
# ============================================================

from PySide6.QtCore import QEvent, Qt, Signal  # Importa eventos, roles, alineaciones, cursores y la señal utilizada para navegar hacia diagnósticos.
from PySide6.QtGui import QBrush, QColor  # Importa las herramientas utilizadas para colorear filas y estados.
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QTabWidget  # Importa pestañas y tablas utilizadas por el panel.

from Motor.diagnosticos import Diagnostico, ESTADO_DIAGNOSTICO_DISPONIBLE, obtener_catalogo_diagnosticos, texto_estado_diagnostico  # Importa el modelo y el catálogo centralizado de diagnósticos.


class PanelDiagnosticos(QTabWidget):  # Organiza diagnósticos detectados y catálogo general dentro de dos subpestañas.
    diagnostico_activado = Signal(object)  # Emite el diagnóstico asociado cuando el usuario solicita navegar hacia el código fuente.

    def __init__(self, padre=None):  # Inicializa las dos tablas manteniendo la misma interfaz pública utilizada por la ventana principal.
        super().__init__(padre)  # Inicializa el contenedor de pestañas.
        self.filas_catalogo: dict[str, int] = {}  # Relaciona cada código con su fila para localizar inmediatamente su ficha.
        self.tabla_detectados = QTableWidget(0, 6)  # Crea la tabla destinada únicamente a los diagnósticos obtenidos en la compilación actual.
        self.tabla_catalogo = QTableWidget(0, 6)  # Crea la tabla fija destinada a mostrar todos los códigos conocidos.

        self._configurar_tabla_detectados()  # Prepara columnas, selección y comportamiento interactivo de la primera vista.
        self._configurar_tabla_catalogo()  # Prepara la tabla utilizada como referencia general.
        self._cargar_catalogo()  # Llena la segunda vista utilizando exclusivamente los datos registrados en Motor.

        self.addTab(self.tabla_detectados, "Detectados")  # Mantiene primero la vista utilizada durante una compilación normal.
        self.addTab(self.tabla_catalogo, "Catálogo")  # Agrega la referencia completa como segunda subpestaña.

        self.tabla_detectados.cellClicked.connect(self._procesar_clic_detectado)  # Permite abrir el catálogo directamente al pulsar el código de un diagnóstico.
        self.tabla_detectados.cellDoubleClicked.connect(self._activar_diagnostico)  # Conserva el doble clic para navegar desde la fila hasta el editor.
        self.tabla_detectados.itemSelectionChanged.connect(self._sincronizar_catalogo_desde_detectados)  # Mantiene preparada en segundo plano la ficha correspondiente al diagnóstico seleccionado.

    def _configurar_tabla_detectados(self) -> None:  # Configura la tabla que muestra únicamente los diagnósticos de la compilación actual.
        self.tabla_detectados.setHorizontalHeaderLabels(
            [
                "Código",
                "Categoría",
                "Mensaje",
                "Línea",
                "Columna",
                "Solución",
            ]
        )

        self.tabla_detectados.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente los diagnósticos.
        self.tabla_detectados.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Selecciona la fila completa al pulsar cualquiera de sus celdas.
        self.tabla_detectados.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite trabajar solamente con un diagnóstico a la vez.
        self.tabla_detectados.setAlternatingRowColors(True)  # Facilita distinguir visualmente filas consecutivas.
        self.tabla_detectados.setWordWrap(True)  # Permite que los mensajes y soluciones extensos utilicen varias líneas.
        self.tabla_detectados.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar información mediante puntos suspensivos.
        self.tabla_detectados.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_detectados.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta la altura según el contenido real.
        self.tabla_detectados.setMouseTracking(True)  # Permite conocer la celda situada debajo del cursor aunque no exista ningún clic.
        self.tabla_detectados.viewport().setMouseTracking(True)  # Activa el seguimiento directamente sobre el área donde se dibujan las celdas.
        self.tabla_detectados.viewport().installEventFilter(self)  # Permite cambiar el cursor solamente cuando se encuentra sobre la columna Código.

        encabezado = self.tabla_detectados.horizontalHeader()  # Obtiene el encabezado para configurar individualmente sus columnas.

        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Reserva únicamente el espacio necesario para Código.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Reserva únicamente el espacio necesario para Categoría.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Permite que Mensaje utilice una parte amplia del espacio restante.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Línea compacta.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Columna compacta.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución comparta el espacio principal.

    def _configurar_tabla_catalogo(self) -> None:  # Configura la tabla de referencia utilizada para consultar todos los códigos conocidos.
        self.tabla_catalogo.setHorizontalHeaderLabels(
            [
                "Código",
                "Tipo",
                "Estado",
                "Nombre",
                "Descripción",
                "Solución sugerida",
            ]
        )

        self.tabla_catalogo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide alterar visualmente la información central del catálogo.
        self.tabla_catalogo.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Mantiene seleccionada la ficha completa del código.
        self.tabla_catalogo.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite consultar una sola entrada a la vez.
        self.tabla_catalogo.setAlternatingRowColors(True)  # Facilita la lectura de códigos consecutivos.
        self.tabla_catalogo.setWordWrap(True)  # Permite mostrar completamente descripciones y soluciones extensas.
        self.tabla_catalogo.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar información del catálogo.
        self.tabla_catalogo.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_catalogo.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Adapta la altura de cada ficha al texto completo.

        encabezado = self.tabla_catalogo.horizontalHeader()  # Obtiene el encabezado de la referencia general.

        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Código compacto.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Tipo compacto.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Reserva solamente el ancho requerido por el Estado.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene visible el nombre completo del diagnóstico.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Permite que Descripción utilice buena parte del espacio disponible.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución sugerida comparta el espacio restante.

    def eventFilter(self, objeto, evento) -> bool:  # Cambia dinámicamente el cursor únicamente al pasar sobre un código clickeable.
        if objeto is self.tabla_detectados.viewport():  # Comprueba que el evento pertenezca al área de celdas de la tabla Detectados.
            if evento.type() == QEvent.Type.MouseMove:  # Atiende cada movimiento del mouse dentro de la tabla.
                indice = self.tabla_detectados.indexAt(evento.position().toPoint())  # Obtiene la fila y columna exactas situadas debajo del cursor.

                if indice.isValid() and indice.column() == 0:  # Comprueba que exista una celda y que corresponda específicamente a Código.
                    self.tabla_detectados.viewport().setCursor(Qt.CursorShape.PointingHandCursor)  # Muestra la manita convencional utilizada por enlaces.
                else:  # Se ejecuta sobre Categoría, Mensaje, Línea, Columna, Solución o espacio vacío.
                    self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Recupera la flecha convencional de Windows.

            elif evento.type() == QEvent.Type.Leave:  # Detecta cuando el mouse abandona completamente el área visible de la tabla.
                self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Garantiza que la manita no permanezca activa fuera de los enlaces.

        return super().eventFilter(objeto, evento)  # Permite que Qt continúe procesando normalmente selección, clics y desplazamiento.

    def _color_categoria(self, categoria: str) -> QColor:  # Devuelve el color utilizado por cada familia de diagnósticos.
        if categoria == "Advertencia":  # Comprueba si se trata de una recomendación no bloqueante.
            return QColor("#f9e2af")  # Utiliza amarillo para advertencias.

        if categoria == "Léxico":  # Comprueba si el código pertenece al lexer.
            return QColor("#f38ba8")  # Utiliza rojo rosado para diagnósticos léxicos.

        if categoria == "Sintáctico":  # Comprueba si el código pertenece al parser.
            return QColor("#fab387")  # Utiliza naranja para diagnósticos sintácticos.

        if categoria == "Semántico":  # Comprueba si el código pertenece al futuro análisis semántico.
            return QColor("#cba6f7")  # Utiliza violeta para diagnósticos semánticos.

        return QColor("#cdd6f4")  # Utiliza el color general para diagnósticos no pertenecientes a las categorías anteriores.

    def _color_diagnostico(self, diagnostico: Diagnostico) -> QColor:  # Conserva la prioridad visual amarilla para cualquier advertencia detectada.
        if diagnostico.severidad in ("warning", "advertencia"):  # Reconoce las dos denominaciones utilizadas históricamente para advertencias.
            return QColor("#f9e2af")  # Fuerza el amarillo independientemente de la categoría almacenada.

        return self._color_categoria(diagnostico.categoria)  # Utiliza el color general correspondiente al resto de diagnósticos.

    def _color_estado_catalogo(self, estado: str) -> QColor:  # Diferencia visualmente funcionalidades actuales de las todavía pendientes.
        if estado == ESTADO_DIAGNOSTICO_DISPONIBLE:  # Comprueba si el código ya pertenece al comportamiento actual.
            return QColor("#a6e3a1")  # Utiliza verde para los diagnósticos disponibles.

        return QColor("#f9e2af")  # Utiliza amarillo para las características que todavía deben implementarse.

    def _cargar_catalogo(self) -> None:  # Construye todas las filas directamente desde la fuente central de Motor.
        self.tabla_catalogo.setRowCount(0)  # Elimina cualquier contenido previo antes de reconstruir la referencia.
        self.filas_catalogo.clear()  # Reinicia también las posiciones utilizadas para localizar códigos rápidamente.

        for codigo, informacion in obtener_catalogo_diagnosticos():  # Recorre todos los códigos conservando el orden definido por Motor.
            fila = self.tabla_catalogo.rowCount()  # Obtiene la nueva posición dentro de la tabla.
            self.tabla_catalogo.insertRow(fila)  # Crea una fila independiente para la ficha.
            self.filas_catalogo[codigo] = fila  # Registra dónde quedó ubicado el código actual.

            valores = [
                codigo,
                informacion["categoria"],
                texto_estado_diagnostico(codigo),
                informacion["nombre"],
                informacion["descripcion"],
                informacion["solucion"],
            ]

            color_categoria = self._color_categoria(informacion["categoria"])  # Obtiene el color correspondiente al tipo de diagnóstico.
            color_estado = self._color_estado_catalogo(informacion["estado"])  # Obtiene verde o amarillo según su disponibilidad.

            for columna, valor in enumerate(valores):  # Construye todas las celdas pertenecientes a la ficha actual.
                elemento = QTableWidgetItem(valor)  # Crea la celda utilizando exactamente la información registrada.
                elemento.setForeground(QBrush(color_estado if columna == 2 else color_categoria))  # Colorea únicamente Estado según disponibilidad y conserva el tipo para las demás columnas.
                elemento.setToolTip(valor)  # Permite consultar también el contenido completo al dejar el cursor encima.

                if columna in (0, 1, 2, 3):  # Comprueba si la información es corta y apropiada para centrarse.
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra código, tipo, estado y nombre.
                else:  # Se ejecuta para los campos descriptivos extensos.
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Mantiene descripción y solución alineadas desde arriba.

                if columna == 0:  # Utiliza Código como identificador interno de la ficha.
                    elemento.setData(Qt.ItemDataRole.UserRole, codigo)  # Conserva el código para futuras interacciones.

                self.tabla_catalogo.setItem(fila, columna, elemento)  # Inserta finalmente la celda en la tabla.

        self.tabla_catalogo.resizeRowsToContents()  # Ajusta todas las alturas después de cargar las descripciones completas.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:  # Sustituye únicamente la tabla de resultados actuales sin modificar el catálogo.
        self.tabla_detectados.setRowCount(0)  # Elimina los diagnósticos correspondientes a la compilación anterior.

        for diagnostico in diagnosticos:  # Recorre todos los problemas y advertencias producidos por el flujo actual.
            fila = self.tabla_detectados.rowCount()  # Obtiene la siguiente posición libre.
            self.tabla_detectados.insertRow(fila)  # Inserta una nueva fila para el diagnóstico.
            color = self._color_diagnostico(diagnostico)  # Obtiene el color correspondiente a su categoría o severidad.

            valores = [
                diagnostico.codigo,
                diagnostico.categoria,
                diagnostico.mensaje,
                "" if diagnostico.linea is None else str(diagnostico.linea),
                "" if diagnostico.columna is None else str(diagnostico.columna),
                diagnostico.solucion,
            ]

            for columna, valor in enumerate(valores):  # Construye las seis celdas utilizadas por cada diagnóstico detectado.
                elemento = QTableWidgetItem(valor)  # Crea la celda con la información correspondiente.
                elemento.setForeground(QBrush(color))  # Aplica el color propio del diagnóstico a toda la fila.
                elemento.setToolTip(valor)  # Mantiene el texto completo disponible mediante tooltip.

                if columna in (0, 1, 3, 4):  # Comprueba si se trata de información corta.
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra código, categoría y ubicación.
                else:  # Se ejecuta para Mensaje y Solución.
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Mantiene los textos largos alineados desde arriba.

                if columna == 0:  # Convierte visual y funcionalmente la columna Código en un acceso directo al catálogo.
                    elemento.setData(Qt.ItemDataRole.UserRole, diagnostico)  # Conserva el objeto completo para navegación y sincronización.
                    fuente_codigo = elemento.font()  # Obtiene una copia de la fuente utilizada por la celda.
                    fuente_codigo.setUnderline(True)  # Subraya el código para comunicar visualmente que puede pulsarse.
                    fuente_codigo.setBold(True)  # Refuerza ligeramente el identificador para distinguirlo del resto de la fila.
                    elemento.setFont(fuente_codigo)  # Aplica el formato visual similar al de un enlace.
                    elemento.setToolTip(
                        f"{diagnostico.codigo}\n\n"
                        "Haz clic para abrir este código en el catálogo.\n"
                        "Haz doble clic sobre otra celda de la fila para ir al código fuente."
                    )

                self.tabla_detectados.setItem(fila, columna, elemento)  # Inserta finalmente la celda en su posición correspondiente.

        self.tabla_detectados.resizeRowsToContents()  # Recalcula la altura necesaria después de insertar todos los textos.

    def limpiar(self) -> None:  # Elimina únicamente los resultados de la compilación y mantiene disponible la referencia fija.
        self.tabla_detectados.setRowCount(0)  # Borra únicamente los diagnósticos producidos por la compilación anterior.
        self.tabla_catalogo.clearSelection()  # Elimina cualquier ficha preseleccionada del catálogo.
        self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Restaura también el cursor convencional al limpiar los diagnósticos.
        self.setCurrentWidget(self.tabla_detectados)  # Regresa a Detectados para dejar el panel en su estado principal.

    def _procesar_clic_detectado(self, fila: int, columna: int) -> None:  # Abre inmediatamente la ficha del catálogo cuando el usuario pulsa el código.
        if columna != 0:  # Comprueba que el clic haya ocurrido específicamente sobre la columna Código.
            return  # Mantiene el comportamiento normal de selección en las demás columnas.

        elemento = self.tabla_detectados.item(fila, 0)  # Recupera la celda donde se conserva el diagnóstico completo.

        if elemento is None:  # Comprueba que la fila posea realmente un elemento válido.
            return  # Finaliza si no existe información asociada.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el objeto estructurado almacenado dentro del código.

        if diagnostico is None:  # Comprueba que el objeto pueda utilizarse.
            return  # Evita continuar con una fila incompleta.

        self._seleccionar_codigo_catalogo(
            diagnostico.codigo,
            cambiar_pestana=True,
        )  # Localiza la ficha y abre inmediatamente la pestaña Catálogo.

    def _sincronizar_catalogo_desde_detectados(self) -> None:  # Mantiene preparada la ficha correspondiente aunque todavía no se cambie de pestaña.
        filas = self.tabla_detectados.selectionModel().selectedRows()  # Recupera la fila completa seleccionada actualmente.

        if not filas:  # Comprueba que exista realmente una selección.
            return  # Evita intentar sincronizar cuando la tabla está vacía.

        fila_detectada = filas[0].row()  # Obtiene la posición del diagnóstico seleccionado.
        elemento = self.tabla_detectados.item(fila_detectada, 0)  # Recupera la celda que conserva el objeto completo.

        if elemento is None:  # Comprueba que la fila contenga información.
            return  # Finaliza si la selección todavía no posee una celda válida.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el diagnóstico estructurado.

        if diagnostico is None:  # Comprueba que exista un objeto asociado.
            return  # Evita intentar localizar un código inexistente.

        self._seleccionar_codigo_catalogo(
            diagnostico.codigo,
            cambiar_pestana=False,
        )  # Preselecciona silenciosamente su ficha sin apartar al usuario de Detectados.

    def _seleccionar_codigo_catalogo(self, codigo: str, cambiar_pestana: bool) -> None:  # Localiza, selecciona y centra una ficha concreta dentro del catálogo.
        fila_catalogo = self.filas_catalogo.get(codigo)  # Busca la posición registrada para el código recibido.

        if fila_catalogo is None:  # Comprueba que el diagnóstico forme parte del catálogo actual.
            return  # Mantiene el panel sin cambios si se tratara de un código desconocido.

        self.tabla_catalogo.selectRow(fila_catalogo)  # Selecciona visualmente la ficha completa correspondiente al código.

        elemento_catalogo = self.tabla_catalogo.item(fila_catalogo, 0)  # Recupera la primera celda para poder desplazar la vista hasta ella.

        if elemento_catalogo is not None:  # Comprueba que la fila haya sido cargada correctamente.
            self.tabla_catalogo.scrollToItem(
                elemento_catalogo,
                QAbstractItemView.ScrollHint.PositionAtCenter,
            )  # Centra la ficha dentro del espacio visible aunque se encuentre lejos en la tabla.

        if cambiar_pestana:  # Comprueba si la acción provino directamente de un clic sobre Código.
            self.setCurrentWidget(self.tabla_catalogo)  # Cambia automáticamente de Detectados a Catálogo mostrando la ficha encontrada.

    def _activar_diagnostico(self, fila: int, columna: int) -> None:  # Conserva el doble clic para navegar desde un diagnóstico hasta el código fuente.
        if columna == 0:  # Evita competir con la función de enlace reservada para la columna Código.
            return  # El código se utiliza exclusivamente para abrir su ficha del catálogo.

        elemento = self.tabla_detectados.item(fila, 0)  # Recupera el objeto completo desde la primera columna de la misma fila.

        if elemento is None:  # Comprueba que exista realmente información asociada.
            return  # Finaliza si la fila estuviera incompleta.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el diagnóstico estructurado almacenado internamente.

        if diagnostico is not None:  # Comprueba que el objeto pueda utilizarse para navegación.
            self.diagnostico_activado.emit(diagnostico)  # Solicita a la ventana principal que seleccione la posición correspondiente en el editor.