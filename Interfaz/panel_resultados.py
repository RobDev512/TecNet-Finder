# ============================================================
# Archivo: panel_resultados.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el conjunto de pestañas utilizadas para
# presentar los resultados generados por TecNet Finder.
#
# Actualmente muestra tokens, tabla VLSM, árbol sintáctico,
# producciones utilizadas y derivación.
#
# Las fases posteriores de LyA II podrán agregar nuevas pestañas
# sin modificar el editor ni el motor de compilación.
# ============================================================

from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QPlainTextEdit, QTableWidget, QTableWidgetItem, QTabWidget  # Importa los widgets utilizados para representar los resultados.
from Motor.modelos import ResultadoCompilacion  # Importa el modelo global producido por el flujo de compilación.


class PanelResultados(QTabWidget):  # Define el conjunto de pestañas donde se presentan los diferentes resultados del análisis.
    def __init__(self, padre=None):  # Inicializa todas las tablas y áreas de texto que forman el panel.
        super().__init__(padre)  # Inicializa el QTabWidget utilizado como contenedor principal.

        self.tabla_tokens = QTableWidget(0, 4)  # Crea la tabla destinada a los tokens reconocidos por el lexer.
        self.tabla_tokens.setHorizontalHeaderLabels(["Tipo", "Valor", "Línea", "Columna"])  # Define las columnas de la tabla léxica.
        self._configurar_tabla(self.tabla_tokens)  # Aplica el comportamiento visual común a la tabla de tokens.

        self.tabla_vlsm = QTableWidget(0, 9)  # Crea la tabla destinada a las subredes calculadas.
        self.tabla_vlsm.setHorizontalHeaderLabels(["Red", "Hosts solicitados", "Hosts disponibles", "Dirección de red", "CIDR", "Máscara", "Primera IP", "Última IP", "Broadcast"])  # Define los encabezados correspondientes al cálculo VLSM.
        self._configurar_tabla(self.tabla_vlsm)  # Aplica el comportamiento común a la tabla VLSM.

        self.texto_arbol = self._crear_salida_textual()  # Crea el visor de solo lectura destinado al árbol sintáctico textual.
        self.texto_producciones = self._crear_salida_textual()  # Crea el visor destinado a gramática y producciones utilizadas.
        self.texto_derivacion = self._crear_salida_textual()  # Crea el visor destinado a la derivación sintáctica.

        self.addTab(self.tabla_tokens, "Tokens")  # Agrega la tabla léxica como primera pestaña.
        self.addTab(self.tabla_vlsm, "Tabla VLSM")  # Agrega la tabla de subredes calculadas.
        self.addTab(self.texto_arbol, "Árbol sintáctico")  # Agrega la representación textual del árbol.
        self.addTab(self.texto_producciones, "Producciones")  # Agrega la gramática y las reglas utilizadas.
        self.addTab(self.texto_derivacion, "Derivación")  # Agrega las sustituciones realizadas desde la gramática.

    def _configurar_tabla(self, tabla: QTableWidget) -> None:  # Aplica una configuración visual común a todas las tablas del panel.
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide que los resultados puedan modificarse manualmente.
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Selecciona filas completas en vez de celdas individuales.
        tabla.setAlternatingRowColors(True)  # Alterna el fondo de las filas para facilitar la lectura.
        tabla.verticalHeader().setVisible(False)  # Oculta el encabezado vertical generado automáticamente por Qt.
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta inicialmente cada columna según su contenido.
        tabla.horizontalHeader().setStretchLastSection(True)  # Permite que la última columna utilice el espacio horizontal restante.

    def _crear_salida_textual(self) -> QPlainTextEdit:  # Construye un área de texto configurada exclusivamente para mostrar resultados.
        salida = QPlainTextEdit()  # Crea un editor de texto plano adecuado para información técnica.
        salida.setReadOnly(True)  # Impide modificar el resultado generado por el compilador.
        salida.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # Evita partir artificialmente árboles, tablas o derivaciones largas.
        return salida  # Devuelve el visor listo para utilizarse dentro de una pestaña.

    def mostrar_resultado(self, resultado: ResultadoCompilacion) -> None:  # Actualiza todas las pestañas utilizando un nuevo resultado global.
        self._mostrar_tokens(resultado)  # Llena la tabla con la salida producida por el lexer.
        self._mostrar_vlsm(resultado)  # Llena la tabla con las subredes calculadas.
        sintactico = resultado.resultado_sintactico  # Obtiene una referencia corta al resultado producido por el parser.
        self.texto_arbol.setPlainText(sintactico.arbol_textual)  # Muestra la representación textual del árbol sintáctico.
        self.texto_producciones.setPlainText(sintactico.producciones_usadas)  # Muestra la gramática y las producciones realmente utilizadas.
        self.texto_derivacion.setPlainText(sintactico.derivacion)  # Muestra la derivación correspondiente a los bloques válidos.

    def _mostrar_tokens(self, resultado: ResultadoCompilacion) -> None:  # Llena la tabla de tokens utilizando el resultado léxico.
        tokens = resultado.resultado_lexico.tokens  # Obtiene la lista completa de tokens reconocidos.
        self.tabla_tokens.setRowCount(len(tokens))  # Reserva exactamente una fila para cada token.

        for fila, token in enumerate(tokens):  # Recorre los tokens conservando el orden original del código fuente.
            valores = [token.tipo, token.valor, str(token.linea), str(token.columna)]  # Convierte los datos del token en valores visibles.

            for columna, valor in enumerate(valores):  # Recorre cada columna correspondiente al token actual.
                self.tabla_tokens.setItem(fila, columna, QTableWidgetItem(valor))  # Coloca el valor dentro de la celda correspondiente.

    def _mostrar_vlsm(self, resultado: ResultadoCompilacion) -> None:  # Llena la tabla utilizando todas las subredes calculadas por el flujo.
        subredes = resultado.subredes_vlsm  # Obtiene la lista completa de resultados VLSM.
        self.tabla_vlsm.setRowCount(len(subredes))  # Reserva una fila para cada subred generada.

        for fila, subred in enumerate(subredes):  # Recorre las subredes respetando el orden calculado por VLSM.
            valores = [  # Prepara todos los datos visibles correspondientes a la subred actual.
                subred.nombre_red,  # Muestra el nombre de la red o su IP base cuando NAME no existe.
                str(subred.hosts_solicitados),  # Muestra la cantidad originalmente solicitada.
                str(subred.hosts_disponibles),  # Muestra cuántas direcciones utilizables proporciona el bloque.
                subred.direccion_de_red,  # Muestra la dirección de red calculada.
                subred.nueva_mascara,  # Muestra el nuevo prefijo CIDR.
                subred.mascara_decimal,  # Muestra la máscara decimal equivalente.
                subred.primera_ip_utilizable,  # Muestra la primera IP asignable.
                subred.ultima_ip_utilizable,  # Muestra la última IP asignable.
                subred.direccion_de_broadcast,  # Muestra la dirección de broadcast.
            ]

            for columna, valor in enumerate(valores):  # Recorre cada dato visible de la subred.
                self.tabla_vlsm.setItem(fila, columna, QTableWidgetItem(valor))  # Inserta el dato dentro de la celda correspondiente.

    def limpiar(self) -> None:  # Elimina todos los resultados mostrados por un análisis anterior.
        self.tabla_tokens.setRowCount(0)  # Vacía completamente la tabla de tokens.
        self.tabla_vlsm.setRowCount(0)  # Vacía completamente la tabla VLSM.
        self.texto_arbol.clear()  # Elimina la representación anterior del árbol.
        self.texto_producciones.clear()  # Elimina las producciones mostradas anteriormente.
        self.texto_derivacion.clear()  # Elimina la derivación correspondiente al análisis anterior.