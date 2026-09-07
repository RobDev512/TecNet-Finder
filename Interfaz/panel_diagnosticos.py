# ============================================================
# Archivo: panel_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el panel encargado de mostrar de forma
# estructurada los errores y advertencias encontrados durante
# las diferentes fases de TecNet Finder.
#
# Cada fila conserva además el objeto Diagnostico original para
# permitir navegar desde la tabla hasta el código fuente.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Importa roles de datos, alineación y la señal utilizada por los diagnósticos.
from PySide6.QtGui import QBrush, QColor  # Importa las herramientas utilizadas para colorear cada tipo de diagnóstico.
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem  # Importa los componentes utilizados por la tabla.

from Motor.diagnosticos import Diagnostico  # Importa el modelo estructurado utilizado por las fases del compilador.


class PanelDiagnosticos(QTableWidget):  # Define la tabla especializada donde se muestran errores y advertencias.
    diagnostico_activado = Signal(object)  # Emite el diagnóstico asociado cuando el usuario hace doble clic sobre una fila.

    def __init__(self, padre=None):  # Inicializa la tabla y configura su comportamiento general.
        super().__init__(0, 6, padre)  # Crea inicialmente una tabla vacía con seis columnas.
        self.setHorizontalHeaderLabels(["Código", "Categoría", "Mensaje", "Línea", "Columna", "Solución"])  # Define los encabezados visibles.
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente los diagnósticos.
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Selecciona la fila completa al pulsar cualquier celda.
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite seleccionar únicamente un diagnóstico a la vez.
        self.setAlternatingRowColors(True)  # Conserva una ligera diferencia visual entre filas consecutivas.
        self.setWordWrap(True)  # Permite que Mensaje y Solución ocupen varias líneas en lugar de recortarse.
        self.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita reemplazar el final del texto mediante puntos suspensivos.
        self.verticalHeader().setVisible(False)  # Oculta los números automáticos de fila.
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta automáticamente la altura de cada fila al contenido completo.

        encabezado = self.horizontalHeader()  # Obtiene el encabezado horizontal para configurar cada columna.
        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Código con el ancho mínimo necesario.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Categoría con el ancho mínimo necesario.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Permite que Mensaje utilice una parte amplia del espacio restante.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta Línea únicamente a su contenido.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta Columna únicamente a su contenido.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución comparta el espacio restante con Mensaje.

        self.cellDoubleClicked.connect(self._activar_diagnostico)  # Conecta el doble clic con la navegación hacia el código fuente.

    def _color_diagnostico(self, diagnostico: Diagnostico) -> QColor:  # Selecciona el color correspondiente a la categoría o severidad recibida.
        if diagnostico.severidad in ("warning", "advertencia"):  # Da prioridad al amarillo para cualquier variante utilizada por las advertencias.
            return QColor("#f9e2af")  # Utiliza amarillo para todas las advertencias no bloqueantes.

        if diagnostico.categoria == "Léxico":  # Comprueba si el diagnóstico pertenece al analizador léxico.
            return QColor("#f38ba8")  # Utiliza rojo rosado para los errores léxicos.

        if diagnostico.categoria == "Sintáctico":  # Comprueba si el diagnóstico pertenece al parser.
            return QColor("#fab387")  # Utiliza naranja para los errores sintácticos.

        if diagnostico.categoria == "Semántico":  # Reserva desde ahora el color correspondiente al análisis semántico.
            return QColor("#cba6f7")  # Utiliza violeta para los futuros errores semánticos.

        return QColor("#cdd6f4")  # Utiliza el color general del texto para diagnósticos no clasificados.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:  # Sustituye las filas existentes por los diagnósticos de la compilación actual.
        self.setRowCount(0)  # Elimina todos los diagnósticos pertenecientes al análisis anterior.

        for diagnostico in diagnosticos:  # Recorre cada diagnóstico estructurado producido por el flujo.
            fila = self.rowCount()  # Obtiene la posición donde se agregará el nuevo diagnóstico.
            self.insertRow(fila)  # Inserta una nueva fila al final de la tabla.
            color = self._color_diagnostico(diagnostico)  # Obtiene el color correspondiente al tipo de diagnóstico.

            valores = [  # Prepara todos los valores visibles de la fila actual.
                diagnostico.codigo,
                diagnostico.categoria,
                diagnostico.mensaje,
                "" if diagnostico.linea is None else str(diagnostico.linea),
                "" if diagnostico.columna is None else str(diagnostico.columna),
                diagnostico.solucion,
            ]

            for columna, valor in enumerate(valores):  # Recorre cada columna correspondiente al diagnóstico actual.
                elemento = QTableWidgetItem(valor)  # Crea una celda utilizando el valor correspondiente.
                elemento.setForeground(QBrush(color))  # Aplica el color correspondiente a toda la información del diagnóstico.
                elemento.setToolTip(valor)  # Conserva también el tooltip como forma adicional de consultar el contenido.

                if columna in (0, 1, 3, 4):  # Comprueba si la celda contiene datos cortos de identificación o ubicación.
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra Código, Categoría, Línea y Columna.
                else:  # Se ejecuta para Mensaje y Solución.
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Mantiene los textos largos alineados desde arriba.

                if columna == 0:  # Utiliza la primera celda para conservar el objeto Diagnostico completo.
                    elemento.setData(Qt.ItemDataRole.UserRole, diagnostico)  # Guarda internamente el objeto utilizado para navegación.

                self.setItem(fila, columna, elemento)  # Inserta finalmente la celda en su posición correspondiente.

        self.resizeRowsToContents()  # Recalcula las alturas después de insertar todo el texto para mostrarlo completo.

    def limpiar(self) -> None:  # Elimina todos los diagnósticos mostrados actualmente.
        self.setRowCount(0)  # Deja nuevamente la tabla sin filas.

    def _activar_diagnostico(self, fila: int, _columna: int) -> None:  # Recupera el diagnóstico asociado con una fila seleccionada.
        elemento = self.item(fila, 0)  # Obtiene la primera celda porque allí se conserva el objeto completo.

        if elemento is None:  # Comprueba que la fila realmente posea contenido.
            return  # Finaliza si no existe información asociada.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el objeto Diagnostico almacenado internamente.

        if diagnostico is not None:  # Comprueba que se haya recuperado correctamente el diagnóstico.
            self.diagnostico_activado.emit(diagnostico)  # Notifica a la ventana para navegar hacia la posición del problema.