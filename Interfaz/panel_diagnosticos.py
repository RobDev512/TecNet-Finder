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
# la IA local únicamente cuando el usuario hace doble clic sobre
# la celda Solución y la función se encuentra habilitada.
#
# La tabla Detectados funciona como una vista de consulta sin
# selección visual de celdas. El doble clic sobre un diagnóstico
# permite navegar al fragmento correspondiente en el editor,
# mientras que la columna Solución conserva una interacción
# independiente para solicitar una mejora mediante IA local.
# ============================================================

from PySide6.QtCore import QEvent, QTimer, Qt, Signal  # Importa eventos, temporización, roles, alineaciones, cursores y navegación.
from PySide6.QtGui import QBrush, QColor  # Importa las herramientas utilizadas para colorear filas y estados.
from PySide6.QtWidgets import QApplication, QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QTabWidget  # Importa pestañas, tablas y acceso al intervalo de doble clic.

from AsistenteIA.control_diagnosticos_ia import ControlDiagnosticosIA  # Mejora soluciones en segundo plano sin intervenir en la detección formal.
from AsistenteIA.explicador_diagnosticos import ExplicadorDiagnosticos  # Permite relacionar cada resultado de IA con la identidad exacta del diagnóstico.
from Motor.diagnosticos import Diagnostico, ESTADO_DIAGNOSTICO_DISPONIBLE, obtener_catalogo_diagnosticos, texto_estado_diagnostico  # Importa el modelo y el catálogo centralizado de diagnósticos.


class PanelDiagnosticos(QTabWidget):  # Organiza diagnósticos detectados y catálogo general dentro de dos subpestañas.
    diagnostico_activado = Signal(object)  # Emite el diagnóstico asociado cuando el usuario solicita navegar hacia el código fuente.

    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el contenedor de pestañas.
        self.filas_catalogo: dict[str, int] = {}  # Relaciona cada código con su fila dentro del catálogo.
        self.diagnosticos_actuales: list[Diagnostico] = []  # Conserva la compilación vigente sin modificar sus soluciones oficiales.
        self.ia_habilitada = False  # Impide solicitar explicaciones hasta recibir el estado efectivo desde Configuración.
        self.codigo_catalogo_pendiente: str | None = None  # Retrasa el clic simple sobre Código para distinguirlo correctamente del doble clic.
        self.clave_solucion_pendiente: str | None = None  # Identifica la solución que actualmente espera una respuesta de IA.

        self.tabla_detectados = QTableWidget(0, 6)  # Crea la tabla de diagnósticos correspondientes a la compilación actual.
        self.tabla_catalogo = QTableWidget(0, 6)  # Crea la tabla de referencia con todos los diagnósticos conocidos.
        self.control_diagnosticos_ia = ControlDiagnosticosIA(self)  # Prepara la generación asíncrona de explicaciones.

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
        self.tabla_detectados.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_detectados.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta cada fila según la cantidad de texto mostrada.
        self.tabla_detectados.setMouseTracking(True)  # Permite actualizar el cursor sin necesidad de pulsar.
        self.tabla_detectados.viewport().setMouseTracking(True)  # Activa el seguimiento directamente sobre el área de las celdas.
        self.tabla_detectados.viewport().installEventFilter(self)  # Permite representar Código como un enlace mediante el cursor.

        encabezado = self.tabla_detectados.horizontalHeader()  # Obtiene el encabezado para controlar el ancho de cada columna.

        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Código compacto.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Categoría compacta.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Permite que Mensaje utilice una parte amplia del espacio.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Línea compacta.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Columna compacta.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución comparta el espacio principal.

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
        self.tabla_catalogo.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_catalogo.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta cada ficha según su contenido.

        encabezado = self.tabla_catalogo.horizontalHeader()  # Obtiene el encabezado para administrar sus columnas.

        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Código compacto.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Tipo compacto.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Estado compacto.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene visible el nombre completo.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Permite que Descripción utilice buena parte del espacio.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución sugerida comparta el espacio restante.

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.tabla_detectados.viewport():  # Comprueba que el evento pertenezca al área visible de Detectados.
            if evento.type() == QEvent.Type.MouseMove:
                indice = self.tabla_detectados.indexAt(evento.position().toPoint())  # Obtiene la celda situada debajo del cursor.

                if indice.isValid() and indice.column() == 0:
                    self.tabla_detectados.viewport().setCursor(Qt.CursorShape.PointingHandCursor)  # Representa Código como un enlace interactivo.
                else:
                    self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Mantiene la flecha convencional sobre las demás columnas.

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
            texto += "\n\nHaz doble clic en esta celda para mejorar la solución con IA local."  # Explica la interacción únicamente cuando se encuentra disponible.

        return texto  # Devuelve la ayuda correspondiente al estado actual.

    def _actualizar_ayudas_solucion(self) -> None:
        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            elemento = self.tabla_detectados.item(fila, 5)  # Obtiene la celda Solución correspondiente.

            if elemento is None:
                continue  # Ignora filas que todavía no poseen contenido.

            if elemento.text() == diagnostico.solucion:
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Actualiza únicamente las soluciones oficiales todavía visibles.

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
            self._solicitar_mejora_solucion(fila)  # Utiliza Solución como acceso explícito a la mejora mediante IA.
            return  # Evita navegar al editor cuando la intención fue solicitar una explicación.

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