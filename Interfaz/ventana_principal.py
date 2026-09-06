# ============================================================
# Archivo: ventana_principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la ventana principal de TecNet Finder.
#
# Su responsabilidad es construir y conectar los componentes
# visuales de la aplicación. No implementa las fases internas
# del compilador, ya que estas son coordinadas por Motor.
#
# La interfaz utiliza PySide6 y conserva la identidad visual
# utilizada durante la migración realizada en LyA I.
# ============================================================

from pathlib import Path  # Importa Path para localizar los recursos del proyecto sin depender de una ruta absoluta.

from PySide6.QtCore import Qt  # Importa las orientaciones y banderas utilizadas por los widgets.
from PySide6.QtGui import QIcon, QPixmap  # Importa las clases necesarias para mostrar el logotipo y el icono de la ventana.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget  # Importa los componentes utilizados para construir la ventana.

from Interfaz.editor_codigo import EditorCodigo  # Importa el editor especializado con números de línea y navegación.
from Interfaz.panel_diagnosticos import PanelDiagnosticos  # Importa la tabla donde se mostrarán los errores encontrados.
from Interfaz.panel_resultados import PanelResultados  # Importa las pestañas utilizadas para presentar los resultados.
from Interfaz.resaltador_sintaxis import ResaltadorSintaxis  # Importa el resaltador visual del lenguaje TecNet Finder.
from Motor.flujo_compilacion import FlujoCompilacion  # Importa el coordinador que conecta léxico, sintáctico y VLSM.


class VentanaPrincipal(QMainWindow):  # Define la ventana principal que contiene todos los componentes de TecNet Finder.
    def __init__(self):  # Inicializa la ventana y prepara el flujo utilizado para analizar el código.
        super().__init__()  # Inicializa el comportamiento estándar de QMainWindow.
        self.flujo = FlujoCompilacion()  # Crea el coordinador encargado de ejecutar las fases disponibles.
        self.ultimo_resultado = None  # Reserva una referencia para conservar el resultado del análisis más reciente.
        self.setWindowTitle("TecNet Finder")  # Establece el título mostrado por el sistema operativo.
        self.resize(1280, 820)  # Define un tamaño inicial cómodo para editor, resultados y diagnósticos.
        self.setMinimumSize(1000, 650)  # Impide reducir la ventana hasta un tamaño poco usable.
        self._cargar_icono()  # Intenta utilizar el logotipo existente como icono de la aplicación.
        self._construir_interfaz()  # Crea todos los elementos visuales de la ventana.

    def _ruta_recurso(self, nombre_archivo: str) -> Path:  # Construye una ruta independiente del directorio desde donde se ejecute Python.
        raiz_proyecto = Path(__file__).resolve().parent.parent  # Obtiene la carpeta raíz partiendo de la ubicación del archivo actual.
        return raiz_proyecto / "Recursos" / nombre_archivo  # Devuelve la ruta del recurso solicitado dentro de Recursos.

    def _cargar_icono(self) -> None:  # Coloca el icono del proyecto en la barra de título cuando el archivo está disponible.
        ruta_icono = self._ruta_recurso("LogoTNF.ico")  # Obtiene la ubicación esperada del archivo ICO.

        if ruta_icono.exists():  # Comprueba que el recurso realmente exista antes de utilizarlo.
            self.setWindowIcon(QIcon(str(ruta_icono)))  # Establece el icono de la ventana utilizando el archivo encontrado.

    def _construir_interfaz(self) -> None:  # Construye el contenido completo de la ventana principal.
        central = QWidget()  # Crea el widget que funcionará como contenido central de QMainWindow.
        self.setCentralWidget(central)  # Asigna el widget recién creado como zona principal.
        diseno = QVBoxLayout(central)  # Crea una distribución vertical para encabezado, estado y contenido.
        diseno.setContentsMargins(14, 12, 14, 14)  # Deja un margen uniforme alrededor de toda la interfaz.
        diseno.setSpacing(10)  # Define la separación entre los principales elementos de la ventana.

        self._construir_encabezado(diseno)  # Agrega el logotipo y el título del proyecto.
        self.etiqueta_estado = QLabel("Sin análisis ejecutado.")  # Crea la barra textual que mostrará el estado del análisis.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Aplica inicialmente el estilo correspondiente al estado neutro.
        diseno.addWidget(self.etiqueta_estado)  # Coloca la barra de estado debajo del encabezado.

        divisor = QSplitter(Qt.Orientation.Vertical)  # Crea un divisor vertical para permitir redimensionar editor, resultados y diagnósticos.
        diseno.addWidget(divisor, 1)  # Agrega el divisor utilizando todo el espacio restante de la ventana.

        panel_editor = self._crear_panel_editor()  # Construye el panel superior donde se escribirá el código.
        self.panel_resultados = PanelResultados()  # Crea las pestañas que mostrarán tokens, VLSM y sintaxis.
        self.panel_diagnosticos = PanelDiagnosticos()  # Crea la tabla inferior destinada a errores y advertencias.

        divisor.addWidget(panel_editor)  # Coloca el editor como primera sección del divisor.
        divisor.addWidget(self.panel_resultados)  # Coloca los resultados como segunda sección.
        divisor.addWidget(self.panel_diagnosticos)  # Coloca los diagnósticos como tercera sección.
        divisor.setSizes([230, 420, 170])  # Define una proporción inicial razonable entre las tres zonas.

        self.panel_diagnosticos.diagnostico_activado.connect(self._ir_a_diagnostico)  # Conecta el doble clic sobre un error con la navegación dentro del editor.

    def _construir_encabezado(self, diseno_principal: QVBoxLayout) -> None:  # Construye la sección superior con logotipo, nombre y descripción.
        encabezado = QHBoxLayout()  # Crea una distribución horizontal para imagen y textos.
        encabezado.setSpacing(12)  # Define la separación visual entre logotipo y título.
        ruta_logo = self._ruta_recurso("LogoTNF.png")  # Obtiene la ruta del logotipo PNG guardado en Recursos.

        if ruta_logo.exists():  # Comprueba si el archivo de imagen se encuentra disponible.
            etiqueta_logo = QLabel()  # Crea el widget que contendrá la imagen.
            imagen = QPixmap(str(ruta_logo)).scaled(58, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Ajusta el logotipo conservando su proporción.
            etiqueta_logo.setPixmap(imagen)  # Coloca la imagen escalada dentro de la etiqueta.
            encabezado.addWidget(etiqueta_logo)  # Agrega el logotipo al lado izquierdo del encabezado.

        caja_titulos = QVBoxLayout()  # Crea una distribución vertical para nombre y descripción.
        titulo = QLabel("TecNet Finder")  # Crea el nombre principal del proyecto.
        titulo.setObjectName("TituloPrincipal")  # Aplica el estilo especial definido para el título.
        subtitulo = QLabel("Compilador para análisis de instrucciones VLSM")  # Crea una descripción breve del propósito actual.
        subtitulo.setObjectName("SubtituloPrincipal")  # Aplica el estilo secundario correspondiente.
        caja_titulos.addWidget(titulo)  # Coloca el título en la primera línea.
        caja_titulos.addWidget(subtitulo)  # Coloca el subtítulo inmediatamente debajo.
        encabezado.addLayout(caja_titulos)  # Agrega ambos textos a la distribución horizontal.
        encabezado.addStretch()  # Empuja el encabezado hacia la izquierda y deja libre el espacio restante.
        diseno_principal.addLayout(encabezado)  # Coloca finalmente el encabezado dentro de la ventana.

    def _crear_panel_editor(self) -> QFrame:  # Construye el panel que contiene el editor y sus botones principales.
        panel = QFrame()  # Crea un contenedor visual independiente para la entrada.
        panel.setObjectName("Panel")  # Aplica el estilo definido para paneles generales.
        diseno = QVBoxLayout(panel)  # Organiza verticalmente título, editor y botones.
        titulo = QLabel("Código fuente")  # Crea el título que identifica el área de entrada.
        titulo.setObjectName("TituloSeccion")  # Aplica el estilo destinado a títulos de sección.
        diseno.addWidget(titulo)  # Coloca el título encima del editor.

        self.editor_codigo = EditorCodigo()  # Crea el editor especializado para instrucciones TecNet Finder.
        self.resaltador_sintaxis = ResaltadorSintaxis(self.editor_codigo.document())  # Conecta el resaltado visual con el documento del editor.
        diseno.addWidget(self.editor_codigo, 1)  # Agrega el editor utilizando todo el espacio vertical disponible del panel.

        botones = QHBoxLayout()  # Crea una fila para las principales acciones del editor.
        boton_analizar = QPushButton("▶ Analizar")  # Crea el botón encargado de ejecutar el flujo de compilación.
        boton_analizar.setObjectName("BotonPrincipal")  # Aplica el estilo visual destacado de acción principal.
        boton_analizar.setShortcut("Ctrl+Return")  # Permite ejecutar el análisis rápidamente utilizando el teclado.
        boton_analizar.clicked.connect(self._analizar_codigo)  # Conecta el clic con el método que ejecutará el flujo completo.

        boton_limpiar = QPushButton("Limpiar")  # Crea el botón utilizado para borrar entrada y resultados actuales.
        boton_limpiar.clicked.connect(self._limpiar_todo)  # Conecta el botón con el método encargado de restaurar la interfaz.

        botones.addWidget(boton_analizar)  # Coloca primero la acción principal de análisis.
        botones.addWidget(boton_limpiar)  # Coloca después la acción secundaria de limpieza.
        botones.addStretch()  # Mantiene ambos botones alineados hacia el lado izquierdo.
        diseno.addLayout(botones)  # Agrega la fila de acciones debajo del editor.

        return panel  # Devuelve el panel completamente construido para insertarlo en el divisor principal.

    def _analizar_codigo(self) -> None:  # Obtiene la entrada del editor y ejecuta el flujo actual de TecNet Finder.
        codigo_fuente = self.editor_codigo.toPlainText()  # Recupera exactamente el texto escrito por el usuario.

        if not codigo_fuente.strip():  # Comprueba que exista al menos algún contenido distinto de espacios.
            QMessageBox.warning(self, "Entrada vacía", "Introduce una instrucción de TecNet Finder antes de analizar.")  # Informa que no existe código para procesar.
            return  # Finaliza sin ejecutar ninguna fase del compilador.

        try:  # Protege la interfaz ante una excepción interna inesperada del motor.
            resultado = self.flujo.analizar(codigo_fuente)  # Ejecuta léxico, sintáctico y VLSM mediante el coordinador central.
        except Exception as error:  # Captura cualquier problema no convertido todavía en un diagnóstico estructurado.
            QMessageBox.critical(self, "Error interno", f"No se pudo completar el análisis:\n{error}")  # Muestra temporalmente el problema sin cerrar la aplicación.
            return  # Finaliza el análisis actual para mantener utilizable la ventana.

        self.ultimo_resultado = resultado  # Conserva el resultado completo por si otras funciones necesitan utilizarlo posteriormente.
        self.panel_resultados.mostrar_resultado(resultado)  # Actualiza todas las pestañas de resultados.
        self.panel_diagnosticos.mostrar_diagnosticos(resultado.diagnosticos)  # Actualiza la tabla con los diagnósticos combinados del flujo.
        self._actualizar_estado(resultado)  # Actualiza la barra superior según el resultado general obtenido.

    def _actualizar_estado(self, resultado) -> None:  # Cambia el mensaje y estilo de estado según la cantidad de errores y subredes generadas.
        cantidad_errores = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad == "error")  # Cuenta los diagnósticos actualmente clasificados como error.
        cantidad_subredes = len(resultado.subredes_vlsm)  # Obtiene cuántas subredes consiguió producir el flujo.

        if cantidad_errores > 0:  # Comprueba si alguna fase produjo al menos un error.
            self.etiqueta_estado.setObjectName("EstadoError")  # Cambia el estilo a la apariencia correspondiente a un análisis con errores.
            self.etiqueta_estado.setText(f"Análisis terminado con errores: {cantidad_errores} error(es) | Subredes generadas: {cantidad_subredes}")  # Resume el resultado del análisis.
        else:  # Se ejecuta cuando no existen errores léxicos ni sintácticos.
            self.etiqueta_estado.setObjectName("EstadoCorrecto")  # Cambia el estilo para indicar que la entrada fue procesada correctamente.
            self.etiqueta_estado.setText(f"Análisis completo | Bloques válidos: {len(resultado.bloques_validos)} | Subredes generadas: {cantidad_subredes}")  # Resume los principales resultados obtenidos.

        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira temporalmente el estilo anterior para que Qt detecte el nuevo objectName.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente la hoja de estilos utilizando el nuevo estado.
        self.etiqueta_estado.update()  # Solicita el redibujado inmediato de la etiqueta.

    def _ir_a_diagnostico(self, diagnostico) -> None:  # Desplaza el editor hacia el fragmento asociado con el diagnóstico seleccionado.
        self.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Utiliza la ubicación estructurada almacenada por el compilador.

    def _limpiar_todo(self) -> None:  # Restaura la entrada y todas las salidas mostradas por la interfaz.
        self.editor_codigo.clear()  # Elimina completamente el código fuente escrito en el editor.
        self.panel_resultados.limpiar()  # Elimina tablas y resultados sintácticos mostrados.
        self.panel_diagnosticos.limpiar()  # Elimina todos los diagnósticos del análisis anterior.
        self.ultimo_resultado = None  # Descarta la referencia al resultado global anterior.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Recupera el estilo correspondiente al estado inicial.
        self.etiqueta_estado.setText("Sin análisis ejecutado.")  # Recupera también el mensaje inicial de la aplicación.
        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira el estilo anterior para actualizar correctamente el objectName.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente la hoja de estilos con el estado neutral.
        self.etiqueta_estado.update()  # Fuerza el redibujado de la barra de estado.
        self.editor_codigo.setFocus()  # Devuelve el cursor al editor para permitir escribir una nueva entrada inmediatamente.