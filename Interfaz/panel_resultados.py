# ============================================================
# Archivo: panel_resultados.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo organiza el área principal de trabajo de
# TecNet Finder mediante pestañas.
#
# Su distribución recupera el acomodo general utilizado en la
# versión de LyA I: Entrada / Salida, Tablas, Sintaxis y Fases
# posteriores.
#
# También actualiza los diferentes resultados generados por el
# flujo de compilación sin implementar ninguna fase interna.
# ============================================================

from collections import Counter  # Importa Counter para calcular cuántas veces aparece cada palabra reservada.
from pathlib import Path  # Importa Path para localizar los iconos utilizados por los botones.

from PySide6.QtCore import QSize, Qt  # Importa tamaños, alineaciones y opciones generales utilizadas por la interfaz.
from PySide6.QtGui import QBrush, QColor, QIcon, QPixmap  # Importa herramientas utilizadas por iconos, imágenes y filas visuales.
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QFrame, QGridLayout, QHeaderView, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Importa los componentes utilizados para organizar resultados, diálogos y pestañas.

from Interfaz.visor_arbol_sintactico import VisorArbolSintactico  # Importa el visor encargado de representar textual y gráficamente los árboles sintácticos.
from Motor.exportador_resultados import exportar_reporte_txt, exportar_vlsm_excel  # Importa las funciones encargadas de guardar los resultados actuales.
from Motor.modelos import ResultadoCompilacion, Token  # Importa los resultados globales y los tokens utilizados para organizar visualmente las tablas.


class TablaResultados(QTableWidget):  # Extiende QTableWidget para mantener una distribución proporcional de columnas.
    def __init__(self, filas: int, columnas: int, proporciones: list[float], padre=None):  # Recibe la cantidad de filas, columnas y proporciones visuales.
        super().__init__(filas, columnas, padre)  # Inicializa la tabla estándar con las dimensiones solicitadas.
        self.proporciones_columnas = proporciones  # Conserva el peso relativo que debe ocupar cada columna.

    def resizeEvent(self, evento) -> None:  # Detecta cambios de tamaño para redistribuir las columnas automáticamente.
        super().resizeEvent(evento)  # Permite que Qt procese primero el cambio de dimensiones.
        self._distribuir_columnas()  # Recalcula los anchos utilizando el nuevo espacio disponible.

    def showEvent(self, evento) -> None:  # Detecta la primera vez que la tabla se hace visible.
        super().showEvent(evento)  # Permite que Qt complete la visualización normal del widget.
        self._distribuir_columnas()  # Ajusta las columnas cuando ya se conoce el ancho real de la tabla.

    def _distribuir_columnas(self) -> None:  # Reparte el ancho disponible de acuerdo con las proporciones definidas.
        if len(self.proporciones_columnas) != self.columnCount():  # Comprueba que exista una proporción por cada columna real.
            return  # Evita intentar distribuir una configuración incompleta.

        ancho_disponible = max(self.viewport().width() - 2, 1)  # Obtiene únicamente el espacio visible reservado para las columnas.
        suma_proporciones = sum(self.proporciones_columnas)  # Calcula el peso total utilizado como referencia.

        if suma_proporciones <= 0:  # Comprueba que la configuración recibida pueda utilizarse matemáticamente.
            return  # Evita una división inválida si todas las proporciones fueran cero.

        anchos = []  # Conserva los anchos calculados para poder ajustar exactamente la última columna.

        for proporcion in self.proporciones_columnas[:-1]:  # Calcula primero todas las columnas excepto la última.
            ancho = int(ancho_disponible * proporcion / suma_proporciones)  # Convierte el peso relativo en píxeles reales.
            anchos.append(ancho)  # Guarda el resultado correspondiente a la columna actual.

        ancho_final = ancho_disponible - sum(anchos)  # Entrega a la última columna únicamente los píxeles restantes por redondeo.
        anchos.append(ancho_final)  # Completa la distribución conservando exactamente el ancho disponible.

        for columna, ancho in enumerate(anchos):  # Recorre las dimensiones calculadas.
            self.setColumnWidth(columna, ancho)  # Aplica el ancho proporcional a cada columna.


class PanelResultados(QTabWidget):  # Organiza el área central de TecNet Finder utilizando la distribución general del proyecto original.
    def __init__(self, editor_codigo, panel_diagnosticos, accion_analizar, accion_limpiar, padre=None):  # Recibe los componentes externos necesarios para construir Entrada / Salida.
        super().__init__(padre)  # Inicializa el contenedor principal de pestañas.
        self.editor_codigo = editor_codigo  # Conserva el editor especializado creado por la ventana principal.
        self.panel_diagnosticos = panel_diagnosticos  # Conserva la tabla estructurada de errores y advertencias.
        self.accion_analizar = accion_analizar  # Conserva la función que ejecutará el flujo de compilación.
        self.accion_limpiar = accion_limpiar  # Conserva la función que restaurará la interfaz.
        self.tarjetas_resumen = {}  # Guarda las etiquetas numéricas utilizadas por el resumen visual.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.
        self.resultado_actual: ResultadoCompilacion | None = None  # Conserva la última compilación para permitir exportarla sin recalcularla.
        self.codigo_fuente_resultado = ""  # Conserva exactamente la entrada asociada con la última compilación mostrada.

        self._construir_entrada_salida()  # Crea la primera pestaña con editor y salidas principales.
        self._construir_tablas()  # Crea las tablas internas de tokens y palabras reservadas.
        self._construir_sintaxis()  # Crea las vistas de producciones, derivación y árbol.
        self._construir_fases_posteriores()  # Reserva visualmente las fases que se desarrollarán en unidades posteriores.
        self.editor_codigo.textChanged.connect(self._invalidar_resultado_exportable)  # Evita exportar resultados antiguos después de modificar la entrada.

        self.addTab(self.tab_entrada_salida, "Entrada / Salida")  # Agrega la zona principal de trabajo.
        self.addTab(self.tab_tablas, "Tablas")  # Agrega las tablas internas del análisis.
        self.addTab(self.tab_sintaxis, "Sintaxis")  # Agrega la información producida por el parser.
        self.addTab(self.tab_fases_posteriores, "Fases posteriores")  # Agrega el espacio reservado para las siguientes unidades.

    def _aplicar_icono(self, boton: QPushButton, nombre_archivo: str, tamano: int = 18) -> None:  # Coloca un icono PNG sobre un botón cuando el recurso existe.
        ruta = self.ruta_iconos / nombre_archivo  # Construye la ubicación exacta del archivo solicitado.

        if ruta.exists():  # Comprueba que el PNG haya sido colocado correctamente.
            boton.setIcon(QIcon(str(ruta)))  # Carga el recurso y lo asigna al botón recibido.
            boton.setIconSize(QSize(tamano, tamano))  # Reduce la imagen original al tamaño requerido por la interfaz.

    def _construir_entrada_salida(self) -> None:  # Construye el equivalente a la pestaña principal Entrada / Salida de la versión anterior.
        self.tab_entrada_salida = QWidget()  # Crea el contenedor de la primera pestaña principal.
        diseno = QVBoxLayout(self.tab_entrada_salida)  # Organiza verticalmente entrada, botones y salidas.
        diseno.setContentsMargins(8, 8, 8, 8)  # Mantiene un margen discreto alrededor del contenido.
        diseno.setSpacing(8)  # Define una separación uniforme entre las zonas.

        panel_entrada = QFrame()  # Crea un bloque visual independiente para el editor.
        panel_entrada.setObjectName("Panel")  # Aplica el estilo general utilizado por los paneles.
        diseno_entrada = QVBoxLayout(panel_entrada)  # Organiza título, editor y acciones verticalmente.

        titulo = QLabel("Entrada")  # Identifica el área donde se escribe el código fuente.
        titulo.setObjectName("TituloSeccion")  # Utiliza el estilo definido para títulos internos.
        diseno_entrada.addWidget(titulo)  # Coloca el título encima del editor.
        diseno_entrada.addWidget(self.editor_codigo, 1)  # Inserta el editor ocupando la mayor parte del panel.

        botones = QHBoxLayout()  # Crea una fila para las acciones principales.

        self.boton_analizar = QPushButton("Compilar")  # Crea la acción principal utilizando únicamente texto e icono gráfico.
        self.boton_analizar.setObjectName("BotonPrincipal")  # Destaca visualmente la acción principal.
        self.boton_analizar.setShortcut("Ctrl+Return")  # Permite compilar rápidamente desde el teclado.
        self._aplicar_icono(self.boton_analizar, "Compilar.png")  # Coloca el icono correspondiente al botón principal.
        self.boton_analizar.clicked.connect(self.accion_analizar)  # Ejecuta el flujo cuando el usuario pulsa el botón.

        self.boton_exportar_excel = QPushButton("Exportar Excel")  # Crea la acción destinada a conservar la tabla VLSM en un libro externo.
        self.boton_exportar_excel.setToolTip("Guardar las subredes VLSM en un archivo de Excel")  # Explica la finalidad del botón.
        self.boton_exportar_excel.setEnabled(False)  # Impide exportar antes de que exista alguna subred calculada.
        self._aplicar_icono(self.boton_exportar_excel, "Exportar_excel.png")  # Coloca el icono preparado para la exportación de Excel.
        self.boton_exportar_excel.clicked.connect(self._exportar_excel)  # Abre el diálogo de guardado cuando la acción se encuentra disponible.

        self.boton_exportar_reporte = QPushButton("Exportar reporte")  # Crea la acción destinada a guardar el análisis completo en texto.
        self.boton_exportar_reporte.setToolTip("Guardar el análisis actual en un archivo TXT")  # Explica la finalidad del reporte externo.
        self.boton_exportar_reporte.setEnabled(False)  # Impide exportar un reporte antes de ejecutar al menos una compilación.
        self._aplicar_icono(self.boton_exportar_reporte, "Exportar_reporte.png")  # Coloca el icono preparado para el reporte.
        self.boton_exportar_reporte.clicked.connect(self._exportar_reporte)  # Abre el diálogo correspondiente al archivo TXT.

        self.boton_limpiar = QPushButton("Limpiar")  # Crea la acción encargada de restaurar entrada y resultados.
        self._aplicar_icono(self.boton_limpiar, "Limpiar.png")  # Coloca el icono correspondiente a la acción de limpieza.
        self.boton_limpiar.clicked.connect(self.accion_limpiar)  # Conecta el botón con la función proporcionada por la ventana.

        botones.addWidget(self.boton_analizar)  # Coloca primero la acción principal.
        botones.addWidget(self.boton_exportar_excel)  # Coloca la exportación VLSM después de compilar.
        botones.addWidget(self.boton_exportar_reporte)  # Coloca el reporte completo junto a la exportación de Excel.
        botones.addWidget(self.boton_limpiar)  # Coloca la acción de limpieza al final del grupo.
        botones.addStretch()  # Mantiene los botones alineados hacia la izquierda.
        diseno_entrada.addLayout(botones)  # Coloca las acciones debajo del editor.

        diseno.addWidget(panel_entrada, 2)  # Reserva una porción moderada del espacio vertical para la entrada.

        self.pestanas_salida = QTabWidget()  # Crea las subpestañas de salida utilizadas en la versión anterior.
        self.tab_resumen = self._crear_resumen()  # Construye el resumen general de la compilación.
        self.tab_analisis = self._crear_salida_textual()  # Crea el visor del análisis léxico-sintáctico.
        self.tab_vlsm = QWidget()  # Crea el contenedor destinado a la tabla VLSM.
        self.tab_errores = QWidget()  # Crea el contenedor destinado a los diagnósticos.

        self.tabla_vlsm = TablaResultados(0, 9, [1.15, 1.35, 1.35, 1.45, 0.55, 1.25, 1.15, 1.15, 1.15])  # Crea la tabla VLSM utilizando anchos proporcionales equilibrados.
        self.tabla_vlsm.setHorizontalHeaderLabels(["Red", "Hosts solicitados", "Hosts disponibles", "Dirección de red", "CIDR", "Máscara", "Primera IP", "Última IP", "Broadcast"])  # Define las columnas de la salida VLSM.
        self._configurar_tabla(self.tabla_vlsm)  # Aplica la configuración común de las tablas.

        diseno_vlsm = QVBoxLayout(self.tab_vlsm)  # Organiza la tabla dentro de su subpestaña.
        diseno_vlsm.setContentsMargins(4, 4, 4, 4)  # Reduce el espacio desperdiciado alrededor de la tabla.
        diseno_vlsm.addWidget(self.tabla_vlsm)  # Coloca la tabla ocupando todo el espacio disponible.

        diseno_errores = QVBoxLayout(self.tab_errores)  # Organiza la tabla de diagnósticos dentro de su subpestaña.
        diseno_errores.setContentsMargins(4, 4, 4, 4)  # Mantiene un margen pequeño alrededor del registro.
        diseno_errores.addWidget(self.panel_diagnosticos)  # Inserta el panel estructurado de errores y advertencias.

        self.pestanas_salida.addTab(self.tab_resumen, "Resumen")  # Agrega la vista rápida del estado actual.
        self.pestanas_salida.addTab(self.tab_analisis, "Análisis léxico-sintáctico")  # Agrega la salida técnica de las dos primeras fases.
        self.pestanas_salida.addTab(self.tab_vlsm, "Tabla VLSM")  # Agrega las subredes calculadas.
        self.pestanas_salida.addTab(self.tab_errores, "Errores / Advertencias")  # Agrega los diagnósticos estructurados.

        diseno.addWidget(self.pestanas_salida, 3)  # Permite que las salidas utilicen ligeramente más espacio que la entrada.

    def _crear_resumen(self) -> QWidget:  # Construye una vista visual con los principales contadores del análisis.
        contenedor = QWidget()  # Crea el widget base utilizado por la pestaña Resumen.
        diseno = QVBoxLayout(contenedor)  # Organiza verticalmente encabezado, estado y tarjetas.
        diseno.setContentsMargins(12, 12, 12, 12)  # Mantiene un margen uniforme alrededor del resumen.
        diseno.setSpacing(10)  # Separa adecuadamente sus diferentes secciones.

        titulo = QLabel("Resumen del análisis")  # Crea el encabezado principal de la vista.
        titulo.setObjectName("TituloResumen")  # Aplica el estilo definido para títulos de resumen.
        diseno.addWidget(titulo)  # Coloca el encabezado en la parte superior.

        self.estado_resumen = QLabel("Sin análisis ejecutado.")  # Muestra el estado textual de la compilación actual.
        self.estado_resumen.setObjectName("EstadoNeutral")  # Utiliza inicialmente el estilo correspondiente a ausencia de análisis.
        diseno.addWidget(self.estado_resumen)  # Coloca el estado inmediatamente debajo del título.

        cuadricula = QGridLayout()  # Crea una cuadrícula flexible que utilizará todo el espacio restante.
        cuadricula.setHorizontalSpacing(10)  # Define la separación horizontal entre tarjetas.
        cuadricula.setVerticalSpacing(10)  # Define la separación vertical entre ambas filas.

        datos_tarjetas = [  # Define cada contador junto con los nombres usados para aplicar su color.
            ("tokens", "Tokens reconocidos", "TarjetaTokens", "ValorTokens"),
            ("bloques", "Bloques sintácticos", "TarjetaBloques", "ValorBloques"),
            ("subredes", "Subredes generadas", "TarjetaSubredes", "ValorSubredes"),
            ("errores_lexicos", "Errores léxicos", "TarjetaLexicos", "ValorLexicos"),
            ("errores_sintacticos", "Errores sintácticos", "TarjetaSintacticos", "ValorSintacticos"),
        ]

        posiciones = {  # Distribuye las tarjetas usando seis columnas para mantener ambas filas equilibradas.
            "tokens": (0, 0, 1, 2),
            "bloques": (0, 2, 1, 2),
            "subredes": (0, 4, 1, 2),
            "errores_lexicos": (1, 0, 1, 3),
            "errores_sintacticos": (1, 3, 1, 3),
        }

        for clave, texto, nombre_tarjeta, nombre_valor in datos_tarjetas:  # Construye las cinco tarjetas del resumen actual.
            tarjeta = QFrame()  # Crea el contenedor visual de la tarjeta.
            tarjeta.setObjectName(nombre_tarjeta)  # Asigna un identificador propio para colorear su borde.
            diseno_tarjeta = QVBoxLayout(tarjeta)  # Organiza verticalmente título y valor.
            diseno_tarjeta.setContentsMargins(12, 10, 12, 10)  # Mantiene espacio interior alrededor del contenido.

            titulo_tarjeta = QLabel(texto)  # Muestra el concepto representado por la tarjeta.
            titulo_tarjeta.setObjectName("TituloTarjeta")  # Aplica el formato común de los nombres.
            titulo_tarjeta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el título horizontalmente.

            valor_tarjeta = QLabel("0")  # Inicializa el contador de la tarjeta en cero.
            valor_tarjeta.setObjectName(nombre_valor)  # Asigna un identificador que determina su color.
            valor_tarjeta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el número dentro de la tarjeta.

            diseno_tarjeta.addWidget(titulo_tarjeta)  # Coloca el título en la parte superior de la tarjeta.
            diseno_tarjeta.addWidget(valor_tarjeta, 1)  # Permite que el valor utilice el espacio vertical sobrante.
            self.tarjetas_resumen[clave] = valor_tarjeta  # Conserva la referencia utilizada para actualizar el contador.

            fila, columna, filas_ocupadas, columnas_ocupadas = posiciones[clave]  # Obtiene la posición y tamaño asignados a esta tarjeta.
            cuadricula.addWidget(tarjeta, fila, columna, filas_ocupadas, columnas_ocupadas)  # Inserta la tarjeta en la cuadrícula equilibrada.

        for columna in range(6):  # Recorre las seis columnas virtuales utilizadas por la cuadrícula.
            cuadricula.setColumnStretch(columna, 1)  # Distribuye uniformemente todo el ancho disponible.

        cuadricula.setRowStretch(0, 1)  # Permite que la primera fila aumente verticalmente.
        cuadricula.setRowStretch(1, 1)  # Permite que la segunda fila ocupe el resto del alto.

        diseno.addLayout(cuadricula, 1)  # Hace que las tarjetas utilicen todo el espacio sobrante.

        return contenedor  # Devuelve la vista de resumen completamente construida.

    def _construir_tablas(self) -> None:  # Construye la pestaña principal destinada a las tablas internas.
        self.tab_tablas = QWidget()  # Crea el contenedor principal de tablas.
        diseno = QVBoxLayout(self.tab_tablas)  # Organiza un conjunto secundario de pestañas.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene un margen reducido.

        pestanas = QTabWidget()  # Crea las subpestañas Tabla de tokens y Palabras reservadas.
        diseno.addWidget(pestanas)  # Permite que las subpestañas utilicen toda el área.

        self.tabla_tokens = TablaResultados(0, 4, [1.25, 1.90, 0.70, 0.80])  # Crea una tabla donde Tipo y Valor reciben mayor espacio que Línea y Posición.
        self.tabla_tokens.setHorizontalHeaderLabels(["Tipo", "Valor", "Línea", "Posición"])  # Define las columnas visibles.
        self._configurar_tabla(self.tabla_tokens)  # Aplica la configuración visual común.

        self.tabla_reservadas = TablaResultados(0, 2, [1.50, 0.85])  # Distribuye la tabla global dando mayor espacio al nombre de la palabra.
        self.tabla_reservadas.setHorizontalHeaderLabels(["Palabra reservada", "Cantidad"])  # Define las dos columnas del resumen.
        self._configurar_tabla(self.tabla_reservadas)  # Aplica el mismo comportamiento visual.

        pestanas.addTab(self.tabla_tokens, "Tabla de tokens")  # Agrega la tabla léxica principal.
        pestanas.addTab(self.tabla_reservadas, "Tabla de palabras reservadas")  # Agrega el conteo de palabras clave.

    def _construir_sintaxis(self) -> None:  # Construye la pestaña destinada exclusivamente a los resultados sintácticos.
        self.tab_sintaxis = QWidget()  # Crea el contenedor principal de la sección.
        diseno = QVBoxLayout(self.tab_sintaxis)  # Organiza un conjunto interno de pestañas.
        diseno.setContentsMargins(6, 6, 6, 6)  # Reduce el margen alrededor del contenido.

        pestanas = QTabWidget()  # Crea las tres vistas principales del análisis sintáctico.
        diseno.addWidget(pestanas)  # Permite que el conjunto ocupe toda la pestaña.

        self.texto_producciones = self._crear_salida_textual()  # Crea el visor destinado a gramática y producciones utilizadas.
        self.texto_derivacion = self._crear_salida_textual()  # Crea el visor de la derivación correspondiente a la entrada.
        self.visor_arbol = VisorArbolSintactico()  # Crea el visor capaz de mostrar tanto árboles textuales como gráficos.

        pestanas.addTab(self.texto_producciones, "Producciones usadas")  # Agrega la gramática y las producciones aplicadas.
        pestanas.addTab(self.texto_derivacion, "Derivación")  # Agrega la derivación correspondiente a los bloques válidos.
        pestanas.addTab(self.visor_arbol, "Árboles")  # Agrega las representaciones textual y gráfica de los árboles sintácticos.

    def _construir_fases_posteriores(self) -> None:  # Construye espacios visibles para las unidades que todavía no deben implementarse.
        self.tab_fases_posteriores = QWidget()  # Crea el contenedor de las etapas futuras.
        diseno = QVBoxLayout(self.tab_fases_posteriores)  # Organiza las subpestañas correspondientes.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene el mismo margen que las demás secciones.

        pestanas = QTabWidget()  # Crea una pestaña independiente para cada fase futura.
        diseno.addWidget(pestanas)  # Expande las fases futuras sobre todo el espacio disponible.

        codigo_intermedio = self._crear_salida_textual()  # Crea el espacio reservado para la Unidad 2.
        optimizacion = self._crear_salida_textual()  # Crea el espacio reservado para la Unidad 3.
        codigo_objeto = self._crear_salida_textual()  # Crea el espacio reservado para la Unidad 4.

        codigo_intermedio.setPlainText("Esta fase se implementará durante la Unidad 2 de Lenguajes y Autómatas II.")  # Explica claramente que todavía no existe código intermedio.
        optimizacion.setPlainText("Esta fase se implementará durante la Unidad 3 de Lenguajes y Autómatas II.")  # Evita presentar optimización como una función ya terminada.
        codigo_objeto.setPlainText("Esta fase se implementará durante la Unidad 4 de Lenguajes y Autómatas II.")  # Reserva honestamente la generación de código objeto.

        pestanas.addTab(codigo_intermedio, "Código intermedio")  # Muestra la fase futura correspondiente a la Unidad 2.
        pestanas.addTab(optimizacion, "Optimización")  # Muestra la fase futura correspondiente a la Unidad 3.
        pestanas.addTab(codigo_objeto, "Código objeto")  # Muestra la fase futura correspondiente a la Unidad 4.

    def _crear_salida_textual(self) -> QPlainTextEdit:  # Crea un área uniforme para mostrar información técnica de solo lectura.
        salida = QPlainTextEdit()  # Crea un editor de texto plano adecuado para resultados extensos.
        salida.setReadOnly(True)  # Evita que el usuario modifique accidentalmente las salidas generadas.
        salida.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # Conserva alineación en árboles, gramáticas y análisis.
        return salida  # Devuelve el visor preparado.

    def _configurar_tabla(self, tabla: QTableWidget) -> None:  # Aplica una configuración uniforme a todas las tablas principales.
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide editar los datos mostrados.
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Hace que cada selección abarque toda una fila.
        tabla.setAlternatingRowColors(True)  # Facilita distinguir visualmente filas consecutivas.
        tabla.setWordWrap(False)  # Evita que el contenido cambie inesperadamente la altura de las filas.
        tabla.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita sustituir los datos por puntos suspensivos.
        tabla.verticalHeader().setVisible(False)  # Oculta el encabezado numérico generado automáticamente.
        tabla.verticalHeader().setDefaultSectionSize(36)  # Mantiene una altura uniforme para todas las filas normales.

        encabezado = tabla.horizontalHeader()  # Obtiene el encabezado horizontal para configurar su comportamiento.
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Permite que la distribución proporcional controle completamente los anchos.
        encabezado.setStretchLastSection(False)  # Evita que la última columna absorba todo el espacio sobrante.
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra los títulos de todas las columnas.

    def _crear_item_centrado(self, valor: str) -> QTableWidgetItem:  # Construye una celda normal con alineación uniforme.
        item = QTableWidgetItem(valor)  # Crea la celda utilizando el texto recibido.
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra simultáneamente el contenido horizontal y verticalmente.
        return item  # Devuelve la celda lista para insertarse en cualquier tabla.

    def _insertar_fila_grupo(self, tabla: QTableWidget, texto: str) -> int:  # Inserta una fila visual que identifica el comienzo de una red.
        fila = tabla.rowCount()  # Obtiene la siguiente posición libre de la tabla.
        tabla.insertRow(fila)  # Reserva una fila completa para el encabezado del grupo.
        tabla.setSpan(fila, 0, 1, tabla.columnCount())  # Une todas las columnas para formar una sola franja visual.

        item = QTableWidgetItem(texto)  # Crea el texto identificador de la red.
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Evita que la fila de agrupación se comporte como un dato seleccionable.
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Centra verticalmente y mantiene el título alineado a la izquierda.
        item.setForeground(QBrush(QColor("#89b4fa")))  # Utiliza el azul principal para distinguir la información de agrupación.
        item.setBackground(QBrush(QColor("#313244")))  # Utiliza un fondo ligeramente más claro que las filas normales.

        fuente = item.font()  # Obtiene la fuente heredada por la celda.
        fuente.setBold(True)  # Resalta el identificador de red mediante negrita.
        item.setFont(fuente)  # Aplica la modificación al encabezado visual.

        tabla.setItem(fila, 0, item)  # Coloca el encabezado dentro de la primera celda combinada.
        tabla.setRowHeight(fila, 32)  # Reserva una altura ligeramente menor que las filas de datos para formar una franja clara.

        return fila  # Devuelve la fila creada por si posteriormente fuera necesario consultarla.

    def mostrar_resultado(self, resultado: ResultadoCompilacion) -> None:  # Actualiza simultáneamente todas las vistas utilizando una compilación nueva.
        self.resultado_actual = resultado  # Conserva la compilación que podrá exportarse posteriormente sin volver a ejecutar el flujo.
        self.codigo_fuente_resultado = self.editor_codigo.toPlainText()  # Guarda el código exacto que produjo los resultados actualmente visibles.
        self.boton_exportar_excel.setEnabled(bool(resultado.subredes_vlsm))  # Habilita Excel únicamente cuando existen subredes válidas.
        self.boton_exportar_reporte.setEnabled(True)  # Permite guardar un reporte incluso cuando la compilación contiene errores.

        self._mostrar_resumen(resultado)  # Actualiza los contadores generales.
        self._mostrar_analisis(resultado)  # Genera el reporte técnico léxico-sintáctico.
        self._mostrar_vlsm(resultado)  # Actualiza la tabla principal de subredes.
        self._mostrar_tokens(resultado)  # Actualiza la tabla interna de tokens.
        self._mostrar_reservadas(resultado)  # Actualiza el conteo de palabras reservadas.

        sintactico = resultado.resultado_sintactico  # Obtiene una referencia corta al resultado generado por el parser.
        self.texto_producciones.setPlainText(sintactico.producciones_usadas)  # Muestra las reglas gramaticales realmente aplicadas.
        self.texto_derivacion.setPlainText(sintactico.derivacion)  # Muestra la derivación generada.
        self.visor_arbol.mostrar_arboles(sintactico.arboles, sintactico.arbol_textual)  # Actualiza conjuntamente la representación textual y los árboles gráficos.

        self.setCurrentWidget(self.tab_entrada_salida)  # Regresa a Entrada / Salida después de cada compilación.

        if resultado.tiene_errores:  # Comprueba si alguna de las fases actuales produjo errores.
            self.pestanas_salida.setCurrentWidget(self.tab_errores)  # Lleva al usuario directamente a los diagnósticos.
        elif resultado.subredes_vlsm:  # Comprueba si el análisis terminó correctamente y produjo subredes.
            self.pestanas_salida.setCurrentWidget(self.tab_vlsm)  # Muestra automáticamente la tabla VLSM cuando todo salió bien.
        else:  # Se ejecuta cuando no existen errores pero tampoco hay una tabla que mostrar.
            self.pestanas_salida.setCurrentWidget(self.tab_resumen)  # Regresa al resumen como vista neutral.

    def _mostrar_resumen(self, resultado: ResultadoCompilacion) -> None:  # Actualiza las tarjetas y el estado general de la compilación.
        diagnosticos = resultado.diagnosticos  # Obtiene todos los diagnósticos combinados del flujo.
        errores_lexicos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Léxico" and diagnostico.severidad == "error")  # Cuenta únicamente errores producidos por el lexer.
        errores_sintacticos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Sintáctico" and diagnostico.severidad == "error")  # Cuenta únicamente errores producidos por el parser.

        self.tarjetas_resumen["tokens"].setText(str(len(resultado.resultado_lexico.tokens)))  # Actualiza la cantidad total de tokens reconocidos.
        self.tarjetas_resumen["bloques"].setText(str(len(resultado.bloques_validos)))  # Actualiza la cantidad de bloques sintácticamente aceptados.
        self.tarjetas_resumen["subredes"].setText(str(len(resultado.subredes_vlsm)))  # Actualiza la cantidad de subredes generadas.
        self.tarjetas_resumen["errores_lexicos"].setText(str(errores_lexicos))  # Actualiza el contador léxico.
        self.tarjetas_resumen["errores_sintacticos"].setText(str(errores_sintacticos))  # Actualiza el contador sintáctico.

        if resultado.tiene_errores:  # Comprueba si existe al menos un error en el resultado global.
            self.estado_resumen.setObjectName("EstadoError")  # Cambia el estilo del mensaje al estado de error.
            self.estado_resumen.setText(f"Análisis terminado con errores | Errores: {errores_lexicos + errores_sintacticos} | Subredes generadas: {len(resultado.subredes_vlsm)}")  # Resume el resultado de la ejecución.
        else:  # Se ejecuta cuando ninguna fase actual produjo errores.
            self.estado_resumen.setObjectName("EstadoCorrecto")  # Aplica el estilo positivo.
            self.estado_resumen.setText(f"Análisis completo | Bloques válidos: {len(resultado.bloques_validos)} | Subredes generadas: {len(resultado.subredes_vlsm)}")  # Muestra los principales datos del análisis correcto.

        self.estado_resumen.style().unpolish(self.estado_resumen)  # Elimina temporalmente el estilo anterior del mensaje.
        self.estado_resumen.style().polish(self.estado_resumen)  # Aplica nuevamente la hoja de estilos con el nuevo estado.
        self.estado_resumen.update()  # Solicita el redibujado del mensaje.

    def _mostrar_analisis(self, resultado: ResultadoCompilacion) -> None:  # Construye una salida textual compacta de las fases léxica y sintáctica.
        lineas = ["=== ANÁLISIS LÉXICO ===", ""]  # Inicia el reporte con el encabezado correspondiente al lexer.

        if resultado.resultado_lexico.tokens:  # Comprueba si fue reconocido al menos un token.
            for token in resultado.resultado_lexico.tokens:  # Recorre los tokens manteniendo el orden original.
                lineas.append(f"Token: {token.tipo:<12} Valor: {token.valor:<18} (Línea {token.linea}, Posición {token.columna})")  # Muestra tipo, valor y ubicación.
        else:  # Se ejecuta cuando el lexer no consiguió producir ningún token.
            lineas.append("No se reconocieron tokens.")  # Informa claramente que la fase léxica quedó vacía.

        lineas.extend(["", "=== ANÁLISIS SINTÁCTICO ===", ""])  # Separa la segunda fase dentro del mismo reporte.

        if resultado.bloques_validos:  # Comprueba si el parser consiguió aceptar instrucciones completas.
            for indice, bloque in enumerate(resultado.bloques_validos, start=1):  # Recorre cada bloque válido.
                nombre = bloque.nombre or "Sin nombre"  # Utiliza una etiqueta legible cuando NAME no fue especificado.
                lineas.append(f"Red #{indice}:")  # Identifica el número del bloque.
                lineas.append(f"  IP: {bloque.direccion_ip}")  # Muestra la dirección base reconocida.
                lineas.append(f"  Máscara: {bloque.mascara_subred}")  # Muestra la máscara escrita.
                lineas.append(f"  Hosts requeridos: {bloque.cantidades_hosts}")  # Muestra la lista de solicitudes.
                lineas.append(f"  Nombre: {nombre}")  # Muestra el identificador opcional.
                lineas.append("")  # Separa visualmente bloques consecutivos.
        else:  # Se ejecuta cuando ninguna instrucción consiguió cumplir completamente la gramática.
            lineas.append("No se encontraron bloques sintácticamente válidos.")  # Informa el resultado sin inventar etapas posteriores.

        lineas.append("=== RESUMEN ===")  # Agrega una síntesis al final del reporte.
        lineas.append(f"Tokens reconocidos: {len(resultado.resultado_lexico.tokens)}")  # Informa la cantidad de tokens.
        lineas.append(f"Bloques sintácticamente válidos: {len(resultado.bloques_validos)}")  # Informa la cantidad de instrucciones aceptadas.
        lineas.append(f"Subredes generadas: {len(resultado.subredes_vlsm)}")  # Informa la cantidad de resultados VLSM.
        lineas.append(f"Diagnósticos encontrados: {len(resultado.diagnosticos)}")  # Informa la cantidad total de problemas detectados.

        self.tab_analisis.setPlainText("\n".join(lineas))  # Muestra el reporte completo dentro de la subpestaña correspondiente.

    def _mostrar_tokens(self, resultado: ResultadoCompilacion) -> None:  # Llena la tabla de tokens separando visualmente cada instrucción de red.
        self.tabla_tokens.clearSpans()  # Elimina combinaciones de celdas creadas durante una compilación anterior.
        self.tabla_tokens.setRowCount(0)  # Elimina todas las filas anteriores antes de reconstruir la tabla.

        grupos = self._agrupar_tokens_por_red(resultado)  # Separa la secuencia léxica según cada aparición inicial de IP.

        for titulo_grupo, tokens in grupos:  # Recorre cada conjunto de tokens asociado con una red.
            self._insertar_fila_grupo(self.tabla_tokens, titulo_grupo)  # Inserta una franja visual antes de los tokens de esa red.

            for token in tokens:  # Recorre los tokens del bloque actual conservando su orden original.
                fila = self.tabla_tokens.rowCount()  # Obtiene la siguiente fila libre de la tabla.
                self.tabla_tokens.insertRow(fila)  # Reserva una fila normal para el token.

                valores = [token.tipo, token.valor, str(token.linea), str(token.columna)]  # Prepara los cuatro valores visibles.

                for columna, valor in enumerate(valores):  # Recorre cada columna del token actual.
                    self.tabla_tokens.setItem(fila, columna, self._crear_item_centrado(valor))  # Inserta el dato centrado en ambas direcciones.

    def _agrupar_tokens_por_red(self, resultado: ResultadoCompilacion) -> list[tuple[str, list[Token]]]:  # Divide visualmente los tokens utilizando IP como inicio de cada instrucción.
        tokens = resultado.resultado_lexico.tokens  # Obtiene la secuencia completa producida por el lexer.

        if not tokens:  # Comprueba si la fase léxica no produjo ningún elemento.
            return []  # Devuelve una lista vacía porque no existe nada que agrupar.

        grupos_tokens: list[list[Token]] = []  # Conserva las secuencias correspondientes a cada instrucción.
        grupo_actual: list[Token] = []  # Acumula los tokens de la red que se está recorriendo.

        for token in tokens:  # Recorre todos los elementos en el mismo orden del código fuente.
            if token.tipo == "IP" and grupo_actual:  # Detecta el comienzo de otra instrucción después de un grupo existente.
                grupos_tokens.append(grupo_actual)  # Conserva la red que acaba de finalizar.
                grupo_actual = []  # Prepara un nuevo conjunto para la siguiente instrucción.

            grupo_actual.append(token)  # Agrega el token actual a la instrucción activa.

        if grupo_actual:  # Comprueba si quedaron tokens pendientes después de terminar el recorrido.
            grupos_tokens.append(grupo_actual)  # Conserva también la última instrucción encontrada.

        bloques_por_linea = {bloque.linea_origen: bloque for bloque in resultado.bloques_validos}  # Relaciona cada línea inicial con su bloque sintácticamente válido.
        grupos: list[tuple[str, list[Token]]] = []  # Construye la estructura final con título y tokens de cada red.

        for grupo in grupos_tokens:  # Recorre las secuencias obtenidas a partir de las palabras IP.
            primer_token = grupo[0]  # Obtiene el primer elemento para conocer la línea de origen aproximada.
            linea = primer_token.linea  # Conserva la línea utilizada para identificar el grupo.
            bloque = bloques_por_linea.get(linea)  # Busca un bloque sintáctico válido que comience en esa misma línea.

            if bloque is not None:  # Comprueba si la instrucción fue aceptada completamente por el parser.
                nombre = bloque.nombre or bloque.direccion_ip  # Utiliza NAME cuando existe y la dirección IP como respaldo.
                titulo = f"Red: {nombre}    |    IP base: {bloque.direccion_ip}    |    Línea: {linea}"  # Construye el encabezado más preciso disponible.
            elif primer_token.tipo == "IP":  # Comprueba si existe una instrucción iniciada con IP aunque haya producido errores sintácticos.
                direccion = next((token.valor for token in grupo if token.tipo == "IP_ADDRESS"), "No identificada")  # Intenta recuperar la dirección reconocida por el lexer.
                nombre = self._buscar_nombre_en_tokens(grupo)  # Intenta recuperar también NAME cuando fue tokenizado correctamente.
                identificador = nombre or direccion  # Utiliza el nombre disponible y conserva la IP como alternativa.
                titulo = f"Red: {identificador}    |    IP base: {direccion}    |    Línea: {linea}"  # Mantiene visible la agrupación incluso para una instrucción inválida.
            else:  # Se ejecuta cuando existieron tokens antes de la primera palabra reservada IP.
                titulo = f"Tokens sin red asociada    |    Línea: {linea}"  # Identifica claramente contenido que no pertenece a una instrucción iniciada correctamente.

            grupos.append((titulo, grupo))  # Conserva el encabezado y la secuencia correspondientes.

        return grupos  # Devuelve todas las redes listas para mostrarse en la tabla.

    def _buscar_nombre_en_tokens(self, tokens: list[Token]) -> str | None:  # Busca un identificador colocado correctamente después de NAME dentro de una secuencia.
        for indice, token in enumerate(tokens[:-1]):  # Recorre todos los elementos que todavía poseen un token posterior.
            siguiente = tokens[indice + 1]  # Obtiene el elemento inmediatamente posterior al actual.

            if token.tipo == "NAME" and siguiente.tipo == "IDENTIFIER":  # Comprueba la pareja utilizada por el nombre opcional.
                return siguiente.valor  # Devuelve el identificador reconocido por el lexer.

        return None  # Indica que la instrucción no contiene un nombre recuperable.

    def _mostrar_reservadas(self, resultado: ResultadoCompilacion) -> None:  # Cuenta las palabras reservadas encontradas por el lexer.
        reservadas = ["IP", "MASK", "HOSTS", "NAME"]  # Define las palabras principales del lenguaje actual.
        contador = Counter(token.tipo for token in resultado.resultado_lexico.tokens if token.tipo in reservadas)  # Cuenta cuántas veces apareció cada palabra.
        self.tabla_reservadas.clearSpans()  # Garantiza que la tabla global no conserve combinaciones de celdas accidentales.
        self.tabla_reservadas.setRowCount(len(reservadas))  # Reserva una fila fija para cada palabra reservada.

        for fila, palabra in enumerate(reservadas):  # Recorre las cuatro palabras aunque alguna no aparezca.
            self.tabla_reservadas.setItem(fila, 0, self._crear_item_centrado(palabra))  # Coloca la palabra reservada centrada.
            self.tabla_reservadas.setItem(fila, 1, self._crear_item_centrado(str(contador.get(palabra, 0))))  # Coloca su cantidad con la misma alineación.

    def _mostrar_vlsm(self, resultado: ResultadoCompilacion) -> None:  # Llena la tabla VLSM separando visualmente las subredes según su red de origen.
        self.tabla_vlsm.clearSpans()  # Elimina combinaciones de columnas pertenecientes a la compilación anterior.
        self.tabla_vlsm.setRowCount(0)  # Vacía completamente las filas para reconstruir grupos y resultados.

        grupo_anterior: tuple[str, str] | None = None  # Conserva nombre e IP base de la última red insertada.

        for subred in resultado.subredes_vlsm:  # Recorre las subredes en el orden determinado por el cálculo VLSM.
            grupo_actual = (subred.nombre_red, subred.ip_base)  # Identifica el bloque original al que pertenece el resultado.

            if grupo_actual != grupo_anterior:  # Comprueba si comienza una red diferente a la anterior.
                titulo_grupo = f"Red: {subred.nombre_red}    |    IP base: {subred.ip_base}"  # Construye la franja visual que separará ambos bloques.
                self._insertar_fila_grupo(self.tabla_vlsm, titulo_grupo)  # Inserta el identificador ocupando el ancho completo de la tabla.
                grupo_anterior = grupo_actual  # Conserva el nuevo bloque como referencia para las siguientes subredes.

            fila = self.tabla_vlsm.rowCount()  # Obtiene la siguiente posición disponible después del encabezado de red.
            self.tabla_vlsm.insertRow(fila)  # Reserva una fila normal para la subred actual.

            valores = [  # Prepara todos los campos visibles de la subred actual.
                subred.nombre_red,
                str(subred.hosts_solicitados),
                str(subred.hosts_disponibles),
                subred.direccion_de_red,
                subred.nueva_mascara,
                subred.mascara_decimal,
                subred.primera_ip_utilizable,
                subred.ultima_ip_utilizable,
                subred.direccion_de_broadcast,
            ]

            for columna, valor in enumerate(valores):  # Recorre cada columna de la subred.
                self.tabla_vlsm.setItem(fila, columna, self._crear_item_centrado(valor))  # Inserta el dato centrado horizontal y verticalmente.

    def _exportar_excel(self) -> None:  # Solicita una ubicación y exporta las subredes VLSM de la compilación actual.
        if self.resultado_actual is None or not self.resultado_actual.subredes_vlsm:  # Comprueba nuevamente que existan resultados aunque el botón normalmente esté deshabilitado.
            self._mostrar_mensaje("Exportar Excel", "No hay subredes VLSM disponibles para exportar.", "Advertencia.png")  # Informa que todavía no existe una tabla válida.
            return  # Evita abrir un cuadro de guardado sin información exportable.

        ruta, _filtro = QFileDialog.getSaveFileName(  # Abre el diálogo nativo para seleccionar la ubicación del libro.
            self,
            "Exportar tabla VLSM",
            "TecNetFinder_VLSM.xlsx",
            "Libro de Excel (*.xlsx)",
        )

        if not ruta:  # Comprueba si el usuario canceló la operación.
            return  # Finaliza sin modificar ningún archivo.

        if not ruta.lower().endswith(".xlsx"):  # Comprueba que el nombre final conserve la extensión correspondiente.
            ruta += ".xlsx"  # Agrega la extensión cuando el usuario la omitió.

        try:  # Protege la interfaz frente a problemas de permisos, rutas o escritura del archivo.
            ruta_guardada = exportar_vlsm_excel(self.resultado_actual, ruta)  # Delega la creación real del libro al módulo independiente de exportación.
        except Exception as error:  # Captura cualquier problema de escritura para comunicarlo sin cerrar la aplicación.
            self._mostrar_mensaje("Error al exportar", f"No se pudo guardar el archivo de Excel.\n\n{error}", "Error.png")  # Muestra el problema recibido desde la operación.
            return  # Finaliza únicamente la exportación que produjo el error.

        self._mostrar_mensaje("Exportación completada", f"La tabla VLSM se guardó correctamente en:\n{ruta_guardada}", "Correcto.png")  # Confirma la ubicación final del libro.

    def _exportar_reporte(self) -> None:  # Solicita una ubicación y guarda un reporte TXT de la última compilación.
        if self.resultado_actual is None:  # Comprueba que exista una ejecución previa del flujo.
            self._mostrar_mensaje("Exportar reporte", "Primero ejecuta una compilación para generar el reporte.", "Advertencia.png")  # Informa por qué todavía no puede exportarse.
            return  # Evita abrir el cuadro de guardado sin información disponible.

        ruta, _filtro = QFileDialog.getSaveFileName(  # Abre el diálogo nativo destinado al reporte textual.
            self,
            "Exportar reporte de análisis",
            "TecNetFinder_Reporte.txt",
            "Archivo de texto (*.txt)",
        )

        if not ruta:  # Comprueba si el usuario canceló la operación.
            return  # Finaliza sin crear ningún archivo.

        if not ruta.lower().endswith(".txt"):  # Comprueba que el archivo conserve la extensión textual esperada.
            ruta += ".txt"  # Agrega TXT cuando el usuario escribió únicamente el nombre.

        codigo_fuente = self.codigo_fuente_resultado  # Recupera exactamente la entrada que produjo la compilación almacenada.

        try:  # Protege la interfaz frente a problemas de escritura en la ubicación seleccionada.
            ruta_guardada = exportar_reporte_txt(codigo_fuente, self.resultado_actual, ruta)  # Delega la construcción y escritura del reporte al módulo independiente.
        except Exception as error:  # Captura cualquier problema para mantener abierta la aplicación.
            self._mostrar_mensaje("Error al exportar", f"No se pudo guardar el reporte TXT.\n\n{error}", "Error.png")  # Explica que la operación no pudo completarse.
            return  # Finaliza únicamente la exportación fallida.

        self._mostrar_mensaje("Exportación completada", f"El reporte se guardó correctamente en:\n{ruta_guardada}", "Correcto.png")  # Confirma que el TXT quedó escrito.

    def _mostrar_mensaje(self, titulo: str, texto: str, nombre_icono: str) -> None:  # Muestra mensajes de exportación utilizando los iconos propios de TecNet Finder.
        mensaje = QMessageBox(self)  # Crea un cuadro modal asociado con la ventana del panel.
        mensaje.setWindowTitle(titulo)  # Define el título visible en la barra del cuadro.
        mensaje.setText(texto)  # Coloca el contenido principal comunicado al usuario.
        mensaje.setStandardButtons(QMessageBox.StandardButton.Ok)  # Utiliza únicamente un botón convencional para cerrar el mensaje.

        ruta_icono = self.ruta_iconos / nombre_icono  # Construye la ubicación del icono correspondiente al tipo de mensaje.

        if ruta_icono.exists():  # Comprueba que el recurso gráfico esté disponible.
            pixmap = QPixmap(str(ruta_icono))  # Carga la imagen PNG original.

            if not pixmap.isNull():  # Comprueba que Qt haya podido interpretar correctamente el archivo.
                pixmap = pixmap.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Reduce suavemente el recurso al tamaño del mensaje.
                mensaje.setIconPixmap(pixmap)  # Sustituye el icono estándar por el recurso propio de TecNet Finder.

        mensaje.exec()  # Muestra el cuadro y espera hasta que el usuario lo cierre.

    def _invalidar_resultado_exportable(self) -> None:  # Descarta la compilación guardada cuando el usuario modifica el código fuente.
        if self.resultado_actual is None:  # Comprueba si realmente existe un resultado que pueda quedar desactualizado.
            return  # Evita trabajo innecesario cuando todavía no se ha compilado o ya se limpió el panel.

        self.resultado_actual = None  # Elimina la referencia a resultados que ya no corresponden con el contenido actual del editor.
        self.codigo_fuente_resultado = ""  # Elimina también la copia de la entrada anteriormente analizada.
        self.boton_exportar_excel.setEnabled(False)  # Impide exportar una tabla asociada con código que ya fue modificado.
        self.boton_exportar_reporte.setEnabled(False)  # Impide generar un reporte mezclando código nuevo con resultados antiguos.

    def limpiar(self) -> None:  # Restaura las salidas de las fases actuales sin modificar las pestañas futuras.
        self.resultado_actual = None  # Descarta la compilación anterior para impedir exportar información que ya no está visible.
        self.codigo_fuente_resultado = ""  # Elimina la entrada asociada con los resultados anteriores.
        self.boton_exportar_excel.setEnabled(False)  # Desactiva Excel hasta que vuelva a existir una tabla VLSM.
        self.boton_exportar_reporte.setEnabled(False)  # Desactiva el reporte hasta que se ejecute una nueva compilación.

        self.tab_analisis.clear()  # Elimina el reporte léxico-sintáctico anterior.

        self.tabla_vlsm.clearSpans()  # Elimina los encabezados combinados correspondientes a redes anteriores.
        self.tabla_vlsm.setRowCount(0)  # Elimina todas las filas de la tabla VLSM.

        self.tabla_tokens.clearSpans()  # Elimina las filas de agrupación creadas para los tokens.
        self.tabla_tokens.setRowCount(0)  # Elimina todos los tokens de la tabla interna.

        self.tabla_reservadas.clearSpans()  # Garantiza que la tabla global conserve su estructura convencional.
        self.tabla_reservadas.setRowCount(0)  # Elimina el conteo anterior de palabras reservadas.

        self.texto_producciones.clear()  # Elimina las producciones sintácticas anteriores.
        self.texto_derivacion.clear()  # Elimina la derivación anterior.
        self.visor_arbol.limpiar()  # Elimina las representaciones textual y gráfica pertenecientes al análisis anterior.

        for etiqueta in self.tarjetas_resumen.values():  # Recorre todos los contadores del resumen.
            etiqueta.setText("0")  # Devuelve cada contador a su valor inicial.

        self.estado_resumen.setObjectName("EstadoNeutral")  # Recupera el estilo neutral del resumen.
        self.estado_resumen.setText("Sin análisis ejecutado.")  # Recupera el mensaje mostrado al iniciar.
        self.estado_resumen.style().unpolish(self.estado_resumen)  # Elimina el estilo anterior.
        self.estado_resumen.style().polish(self.estado_resumen)  # Aplica nuevamente el estilo neutral.
        self.setCurrentWidget(self.tab_entrada_salida)  # Regresa visualmente a la pestaña inicial.
        self.pestanas_salida.setCurrentWidget(self.tab_resumen)  # Muestra nuevamente el resumen vacío.