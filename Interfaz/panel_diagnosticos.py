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
# permitir posteriormente navegar desde la tabla hasta el código.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Importa roles de datos y la señal utilizada para comunicar la selección de un diagnóstico.
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem  # Importa las clases necesarias para construir la tabla.
from Motor.diagnosticos import Diagnostico  # Importa el modelo estructurado utilizado por todas las fases del proyecto.


class PanelDiagnosticos(QTableWidget):  # Define la tabla especializada que mostrará todos los diagnósticos encontrados.
    diagnostico_activado = Signal(object)  # Emite el objeto Diagnostico asociado cuando el usuario hace doble clic sobre una fila.

    def __init__(self, padre=None):  # Inicializa la tabla y configura sus columnas y comportamiento.
        super().__init__(0, 6, padre)  # Crea inicialmente una tabla vacía con seis columnas.
        self.setHorizontalHeaderLabels(["Código", "Categoría", "Mensaje", "Línea", "Columna", "Solución"])  # Define los encabezados visibles.
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente los diagnósticos desde la tabla.
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Hace que al seleccionar una celda se seleccione toda su fila.
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite seleccionar solamente un diagnóstico a la vez.
        self.setAlternatingRowColors(True)  # Alterna discretamente el fondo de las filas para facilitar su lectura.
        self.verticalHeader().setVisible(False)  # Oculta los números de fila propios de QTableWidget.
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta automáticamente el ancho de la columna Código.
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta automáticamente el ancho de Categoría.
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Permite que Mensaje utilice la mayor parte del espacio disponible.
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta Línea al ancho de su contenido.
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Ajusta Columna al ancho de su contenido.
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución utilice el espacio restante.
        self.cellDoubleClicked.connect(self._activar_diagnostico)  # Conecta el doble clic con la emisión del diagnóstico correspondiente.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:  # Reemplaza el contenido de la tabla con los diagnósticos recibidos.
        self.setRowCount(0)  # Elimina todas las filas pertenecientes al análisis anterior.

        for diagnostico in diagnosticos:  # Recorre cada diagnóstico estructurado generado por el flujo.
            fila = self.rowCount()  # Obtiene el índice donde se agregará el nuevo diagnóstico.
            self.insertRow(fila)  # Inserta una fila vacía al final de la tabla.
            valores = [  # Prepara los valores visibles correspondientes al diagnóstico actual.
                diagnostico.codigo,  # Muestra el código único del diagnóstico.
                diagnostico.categoria,  # Muestra la fase o categoría donde se produjo.
                diagnostico.mensaje,  # Muestra la explicación específica del problema.
                "" if diagnostico.linea is None else str(diagnostico.linea),  # Muestra la línea cuando existe una ubicación concreta.
                "" if diagnostico.columna is None else str(diagnostico.columna),  # Muestra la columna cuando existe una ubicación concreta.
                diagnostico.solucion,  # Muestra la recomendación registrada en el catálogo.
            ]

            for columna, valor in enumerate(valores):  # Recorre cada columna visible de la nueva fila.
                elemento = QTableWidgetItem(valor)  # Crea la celda con el texto correspondiente.
                elemento.setToolTip(valor)  # Permite leer textos largos al mantener el cursor sobre la celda.

                if columna == 0:  # Utiliza la primera celda como lugar donde conservar el objeto completo.
                    elemento.setData(Qt.ItemDataRole.UserRole, diagnostico)  # Guarda internamente el Diagnostico sin mostrarlo como texto.

                self.setItem(fila, columna, elemento)  # Coloca la celda terminada dentro de su posición correspondiente.

    def limpiar(self) -> None:  # Elimina todos los diagnósticos mostrados actualmente.
        self.setRowCount(0)  # Deja la tabla nuevamente sin filas.

    def _activar_diagnostico(self, fila: int, _columna: int) -> None:  # Recupera el diagnóstico asociado con la fila seleccionada.
        elemento = self.item(fila, 0)  # Obtiene la primera celda porque allí se almacenó el objeto Diagnostico.

        if elemento is None:  # Comprueba que la fila realmente contenga una celda válida.
            return  # Finaliza si no existe información asociada.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el objeto estructurado guardado dentro de la celda.

        if diagnostico is not None:  # Comprueba que realmente se haya recuperado un diagnóstico.
            self.diagnostico_activado.emit(diagnostico)  # Notifica a la ventana principal para que pueda navegar hasta el código.