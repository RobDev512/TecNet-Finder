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

from PySide6.QtCore import QSize, Qt  # Importa tamaños y opciones de alineación utilizadas por los componentes.
from PySide6.QtGui import QIcon  # Importa la clase utilizada para cargar iconos PNG.
from PySide6.QtWidgets import QAbstractItemView, QFrame, QGridLayout, QHeaderView, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Importa los componentes utilizados para organizar resultados y pestañas.

from Interfaz.visor_arbol_sintactico import VisorArbolSintactico  # Importa el visor encargado de representar textual y gráficamente los árboles sintácticos.
from Motor.modelos import ResultadoCompilacion  # Importa el resultado global producido por el flujo actual.


class PanelResultados(QTabWidget):  # Organiza el área central de TecNet Finder utilizando la distribución general del proyecto original.
    def __init__(self, editor_codigo, panel_diagnosticos, accion_analizar, accion_limpiar, padre=None):  # Recibe los componentes externos necesarios para construir Entrada / Salida.
        super().__init__(padre)  # Inicializa el contenedor principal de pestañas.
        self.editor_codigo = editor_codigo  # Conserva el editor especializado creado por la ventana principal.
        self.panel_diagnosticos = panel_diagnosticos  # Conserva la tabla estructurada de errores y advertencias.
        self.accion_analizar = accion_analizar  # Conserva la función que ejecutará el flujo de compilación.
        self.accion_limpiar = accion_limpiar  # Conserva la función que restaurará la interfaz.
        self.tarjetas_resumen = {}  # Guarda las etiquetas numéricas utilizadas por el resumen visual.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de iconos.

        self._construir_entrada_salida()  # Crea la primera pestaña con editor y salidas principales.
        self._construir_tablas()  # Crea las tablas internas de tokens y palabras reservadas.
        self._construir_sintaxis()  # Crea las vistas de producciones, derivación y árbol.
        self._construir_fases_posteriores()  # Reserva visualmente las fases que se desarrollarán en unidades posteriores.

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

        boton_analizar = QPushButton("Compilar")  # Crea la acción principal utilizando únicamente texto e icono gráfico.
        boton_analizar.setObjectName("BotonPrincipal")  # Destaca visualmente la acción principal.
        boton_analizar.setShortcut("Ctrl+Return")  # Permite compilar rápidamente desde el teclado.
        self._aplicar_icono(boton_analizar, "Compilar.png")  # Coloca el icono correspondiente al botón principal.
        boton_analizar.clicked.connect(self.accion_analizar)  # Ejecuta el flujo cuando el usuario pulsa el botón.

        boton_limpiar = QPushButton("Limpiar")  # Crea la acción encargada de restaurar entrada y resultados.
        self._aplicar_icono(boton_limpiar, "Limpiar.png")  # Coloca el icono correspondiente a la acción de limpieza.
        boton_limpiar.clicked.connect(self.accion_limpiar)  # Conecta el botón con la función proporcionada por la ventana.

        botones.addWidget(boton_analizar)  # Coloca primero la acción principal.
        botones.addWidget(boton_limpiar)  # Coloca la acción de limpieza a continuación.
        botones.addStretch()  # Mantiene los botones alineados hacia la izquierda.
        diseno_entrada.addLayout(botones)  # Coloca las acciones debajo del editor.

        diseno.addWidget(panel_entrada, 2)  # Reserva una porción moderada del espacio vertical para la entrada.

        self.pestanas_salida = QTabWidget()  # Crea las subpestañas de salida utilizadas en la versión anterior.
        self.tab_resumen = self._crear_resumen()  # Construye el resumen general de la compilación.
        self.tab_analisis = self._crear_salida_textual()  # Crea el visor del análisis léxico-sintáctico.
        self.tab_vlsm = QWidget()  # Crea el contenedor destinado a la tabla VLSM.
        self.tab_errores = QWidget()  # Crea el contenedor destinado a los diagnósticos.

        self.tabla_vlsm = QTableWidget(0, 9)  # Crea la tabla principal donde se mostrarán las subredes calculadas.
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

        diseno.addLayout(cuadricula, 1)  # Hace que las tarjetas utilicen todo el espacio sobrante en lugar de dejarlo vacío.

        return contenedor  # Devuelve la vista de resumen completamente construida.

    def _construir_tablas(self) -> None:  # Construye la pestaña principal destinada a las tablas internas.
        self.tab_tablas = QWidget()  # Crea el contenedor principal de tablas.
        diseno = QVBoxLayout(self.tab_tablas)  # Organiza un notebook secundario dentro de la pestaña.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene un margen reducido.

        pestanas = QTabWidget()  # Crea las subpestañas Tabla de tokens y Palabras reservadas.
        diseno.addWidget(pestanas)  # Permite que las subpestañas utilicen toda el área.

        self.tabla_tokens = QTableWidget(0, 4)  # Crea la tabla donde se mostrará cada token reconocido.
        self.tabla_tokens.setHorizontalHeaderLabels(["Tipo", "Valor", "Línea", "Posición"])  # Define las columnas visibles.
        self._configurar_tabla(self.tabla_tokens)  # Aplica la configuración común.

        self.tabla_reservadas = QTableWidget(0, 2)  # Crea la tabla que resume las palabras reservadas encontradas.
        self.tabla_reservadas.setHorizontalHeaderLabels(["Palabra reservada", "Cantidad"])  # Define las dos columnas del resumen.
        self._configurar_tabla(self.tabla_reservadas)  # Aplica el mismo comportamiento visual.

        pestanas.addTab(self.tabla_tokens, "Tabla de tokens")  # Agrega la tabla léxica principal.
        pestanas.addTab(self.tabla_reservadas, "Tabla de palabras reservadas")  # Agrega el conteo de palabras clave.

    def _construir_sintaxis(self) -> None:  # Construye la pestaña destinada exclusivamente a los resultados sintácticos.
        self.tab_sintaxis = QWidget()  # Crea el contenedor principal de la sección.
        diseno = QVBoxLayout(self.tab_sintaxis)  # Organiza un conjunto interno de pestañas.
        diseno.setContentsMargins(6, 6, 6, 6)  # Reduce el margen alrededor del contenido.

        pestanas = QTabWidget()  # Crea las tres vistas principales del análisis sintáctico.
        diseno.addWidget(pestanas)  # Permite que el notebook ocupe toda la pestaña.

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

    def _configurar_tabla(self, tabla: QTableWidget) -> None:  # Aplica una configuración uniforme a las tablas de resultados.
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide editar los datos mostrados.
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Hace que cada selección abarque toda una fila.
        tabla.setAlternatingRowColors(True)  # Facilita distinguir visualmente filas consecutivas.
        tabla.verticalHeader().setVisible(False)  # Oculta el encabezado numérico generado automáticamente.
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Adapta las columnas al tamaño de su contenido.
        tabla.horizontalHeader().setStretchLastSection(True)  # Permite que la última columna utilice cualquier espacio sobrante.

    def mostrar_resultado(self, resultado: ResultadoCompilacion) -> None:  # Actualiza simultáneamente todas las vistas utilizando una compilación nueva.
        self._mostrar_resumen(resultado)  # Actualiza los contadores generales.
        self._mostrar_analisis(resultado)  # Genera el reporte técnico léxico-sintáctico.
        self._mostrar_vlsm(resultado)  # Actualiza la tabla principal de subredes.
        self._mostrar_tokens(resultado)  # Actualiza la tabla interna de tokens.
        self._mostrar_reservadas(resultado)  # Actualiza el conteo de palabras reservadas.

        sintactico = resultado.resultado_sintactico  # Obtiene una referencia corta al resultado generado por el parser.
        self.texto_producciones.setPlainText(sintactico.producciones_usadas)  # Muestra las reglas gramaticales realmente aplicadas.
        self.texto_derivacion.setPlainText(sintactico.derivacion)  # Muestra la derivación generada.
        self.visor_arbol.mostrar_arboles(sintactico.arboles, sintactico.arbol_textual)  # Actualiza conjuntamente la representación textual y los árboles gráficos.

        self.setCurrentWidget(self.tab_entrada_salida)  # Regresa a Entrada / Salida después de cada compilación como hacía la versión anterior.

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

    def _mostrar_tokens(self, resultado: ResultadoCompilacion) -> None:  # Llena la tabla de tokens utilizando el resultado léxico.
        tokens = resultado.resultado_lexico.tokens  # Obtiene todos los tokens reconocidos.
        self.tabla_tokens.setRowCount(len(tokens))  # Reserva una fila para cada token.

        for fila, token in enumerate(tokens):  # Recorre los tokens en el mismo orden del código fuente.
            valores = [token.tipo, token.valor, str(token.linea), str(token.columna)]  # Prepara los cuatro valores visibles.

            for columna, valor in enumerate(valores):  # Recorre cada columna del token actual.
                self.tabla_tokens.setItem(fila, columna, QTableWidgetItem(valor))  # Inserta el valor dentro de su celda.

    def _mostrar_reservadas(self, resultado: ResultadoCompilacion) -> None:  # Cuenta las palabras reservadas encontradas por el lexer.
        reservadas = ["IP", "MASK", "HOSTS", "NAME"]  # Define las palabras principales del lenguaje actual.
        contador = Counter(token.tipo for token in resultado.resultado_lexico.tokens if token.tipo in reservadas)  # Cuenta cuántas veces apareció cada palabra.
        self.tabla_reservadas.setRowCount(len(reservadas))  # Reserva una fila fija para cada palabra reservada.

        for fila, palabra in enumerate(reservadas):  # Recorre las cuatro palabras aunque alguna no aparezca.
            self.tabla_reservadas.setItem(fila, 0, QTableWidgetItem(palabra))  # Coloca la palabra reservada en la primera columna.
            self.tabla_reservadas.setItem(fila, 1, QTableWidgetItem(str(contador.get(palabra, 0))))  # Coloca su cantidad en la segunda columna.

    def _mostrar_vlsm(self, resultado: ResultadoCompilacion) -> None:  # Llena la tabla principal con todas las subredes generadas.
        subredes = resultado.subredes_vlsm  # Obtiene los resultados calculados por Redes.
        self.tabla_vlsm.setRowCount(len(subredes))  # Reserva exactamente una fila para cada subred.

        for fila, subred in enumerate(subredes):  # Recorre las subredes en el orden determinado por el cálculo VLSM.
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
                self.tabla_vlsm.setItem(fila, columna, QTableWidgetItem(valor))  # Inserta el valor correspondiente.

    def limpiar(self) -> None:  # Restaura las salidas de las fases actuales sin modificar las pestañas futuras.
        self.tab_analisis.clear()  # Elimina el reporte léxico-sintáctico anterior.
        self.tabla_vlsm.setRowCount(0)  # Elimina todas las subredes mostradas.
        self.tabla_tokens.setRowCount(0)  # Elimina todos los tokens de la tabla interna.
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