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
#
# Las tablas utilizan anchos mínimos legibles y distribución
# proporcional. Cuando el espacio disponible no permite mostrar
# todas las columnas correctamente, se habilita desplazamiento
# horizontal en lugar de comprimir excesivamente el contenido.
#
# Cuando una compilación genera VLSM y únicamente presenta
# advertencias, puede mostrar debajo un panel compacto con esos
# diagnósticos sin ocultar la Tabla VLSM.
#
# Navegación automática y advertencias compactas pueden
# habilitarse o deshabilitarse desde Configuración sin modificar
# el resultado formal producido por el compilador.
# ============================================================

from collections import Counter  # Permite contar cuántas veces aparece cada palabra reservada.


from PySide6.QtCore import QEvent, QSize, QTimer, Qt  # Aporta eventos, tamaños, temporización y opciones generales utilizadas por la interfaz.
from PySide6.QtGui import QBrush, QColor, QIcon, QPixmap  # Aporta colores, iconos e imágenes utilizados en los resultados.
from PySide6.QtWidgets import QApplication, QAbstractItemView, QFileDialog, QFrame, QGridLayout, QHeaderView, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Aporta los widgets utilizados por el panel.

from Interfaz.apariencia.recursos_tema import ruta_icono_comun, ruta_icono_oscuro  # Proporciona recursos iniciales y semánticos mediante la estructura centralizada.
from Interfaz.resultados.visor_arbol_sintactico import VisorArbolSintactico  # Muestra textual y gráficamente los árboles sintácticos.
from Motor.exportacion.exportador_resultados import exportar_reporte_txt, exportar_vlsm_excel  # Guarda resultados en archivos externos.
from Motor.compilacion.modelos import ResultadoCompilacion, Token  # Define los modelos utilizados para mostrar el análisis.


class TablaResultados(QTableWidget):  # Mantiene columnas proporcionales sin permitir que se compriman por debajo de un ancho legible.
    def __init__(
        self,
        filas: int,
        columnas: int,
        proporciones: list[float],
        anchos_minimos: list[int] | None = None,
        padre=None,
    ):
        super().__init__(filas, columnas, padre)  # Inicializa la tabla estándar.
        self.proporciones_columnas = proporciones  # Conserva el peso relativo utilizado cuando existe espacio adicional.
        self.anchos_minimos_columnas = anchos_minimos or [80] * columnas  # Define un ancho mínimo seguro cuando no se proporcionó una configuración específica.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra desplazamiento horizontal solamente cuando los mínimos ya no caben.
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite desplazar horizontalmente la tabla de forma suave.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Permite que Qt procese primero el cambio de tamaño.
        self._distribuir_columnas()  # Recalcula las columnas después de conocer el nuevo espacio disponible.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite completar la primera visualización.
        self._distribuir_columnas()  # Ajusta las columnas utilizando el ancho real de la tabla.

    def _distribuir_columnas(self) -> None:
        if len(self.proporciones_columnas) != self.columnCount():
            return  # Comprueba que exista una proporción para cada columna.

        if len(self.anchos_minimos_columnas) != self.columnCount():
            return  # Comprueba que exista también un ancho mínimo por columna.

        ancho_disponible = max(self.viewport().width() - 2, 1)  # Utiliza únicamente el espacio visible de la tabla.
        ancho_minimo_total = sum(self.anchos_minimos_columnas)  # Calcula cuánto espacio requiere la tabla para permanecer legible.

        if ancho_disponible <= ancho_minimo_total:
            anchos = list(self.anchos_minimos_columnas)  # Conserva los mínimos cuando la ventana no ofrece suficiente espacio.
        else:
            espacio_adicional = ancho_disponible - ancho_minimo_total  # Calcula únicamente los píxeles sobrantes después de respetar todos los mínimos.
            suma_proporciones = sum(self.proporciones_columnas)  # Calcula el peso total utilizado para repartir el espacio adicional.

            if suma_proporciones <= 0:
                return  # Evita una distribución matemáticamente inválida.

            anchos = []  # Conserva los anchos definitivos antes de aplicarlos.

            for minimo, proporcion in zip(
                self.anchos_minimos_columnas[:-1],
                self.proporciones_columnas[:-1],
            ):
                adicional = int(
                    espacio_adicional * proporcion / suma_proporciones
                )  # Reparte proporcionalmente una parte del espacio que sobra.
                anchos.append(minimo + adicional)  # Mantiene el mínimo y agrega solamente la expansión disponible.

            ancho_ultima = ancho_disponible - sum(anchos)  # Entrega a la última columna los píxeles restantes para evitar huecos por redondeo.
            ancho_ultima = max(
                ancho_ultima,
                self.anchos_minimos_columnas[-1],
            )  # Garantiza que la última columna tampoco pueda comprimirse por debajo de su mínimo.
            anchos.append(ancho_ultima)  # Completa la distribución definitiva.

        for columna, ancho in enumerate(anchos):
            self.setColumnWidth(columna, ancho)  # Aplica cada ancho respetando los límites calculados.


class PanelResultados(QTabWidget):  # Organiza el área central de resultados de TecNet Finder.
    def __init__(self, editor_codigo, panel_diagnosticos, accion_analizar, accion_limpiar, padre=None):
        super().__init__(padre)  # Inicializa el contenedor principal de pestañas.
        self.editor_codigo = editor_codigo  # Conserva el editor especializado de TecNet Finder.
        self.panel_diagnosticos = panel_diagnosticos  # Conserva la vista estructurada de errores y advertencias.
        self.accion_analizar = accion_analizar  # Conserva la acción que ejecuta el flujo de compilación.
        self.accion_limpiar = accion_limpiar  # Conserva la acción que restaura la interfaz.
        self.tarjetas_resumen = {}  # Almacena las etiquetas numéricas del resumen visual.

        self.resultado_actual: ResultadoCompilacion | None = None  # Conserva la última compilación disponible.
        self.codigo_fuente_resultado = ""  # Conserva la entrada exacta asociada con la última compilación.
        self.botones_flotantes: dict[QWidget, tuple[QPushButton, str]] = {}  # Relaciona cada superficie fija con su acción flotante.
        self.superficie_diagnosticos: QWidget | None = None  # Conserva el contenedor exterior utilizado por el botón fijo de diagnósticos.
        self.advertencias_compactas_actuales = []  # Conserva únicamente las advertencias visibles debajo de la Tabla VLSM.
        self.navegacion_automatica = True  # Mantiene por defecto el cambio automático hacia la salida más relevante.
        self.advertencias_compactas_habilitadas = True  # Mantiene por defecto la vista resumida de advertencias debajo de VLSM.

        self._construir_entrada_salida()  # Crea la zona principal de entrada y salidas.
        self._construir_tablas()  # Crea las tablas de tokens y palabras reservadas.
        self._construir_sintaxis()  # Crea producciones, derivación y árboles.
        self._construir_fases_posteriores()  # Reserva las fases correspondientes a futuras unidades.
        self.editor_codigo.textChanged.connect(self._invalidar_resultado_exportable)  # Invalida resultados cuando cambia la entrada.

        self.addTab(self.tab_entrada_salida, "Entrada / Salida")  # Agrega la zona principal de trabajo.
        self.addTab(self.tab_tablas, "Tablas")  # Agrega las tablas internas del análisis.
        self.addTab(self.tab_sintaxis, "Sintaxis")  # Agrega los resultados sintácticos.
        self.addTab(self.tab_fases_posteriores, "Fases posteriores")  # Agrega las etapas todavía no implementadas.

    def establecer_navegacion_automatica(self, habilitada: bool) -> None:
        self.navegacion_automatica = bool(habilitada)  # Conserva la decisión utilizada durante las compilaciones posteriores.

    def establecer_advertencias_compactas(self, habilitadas: bool) -> None:
        self.advertencias_compactas_habilitadas = bool(habilitadas)  # Conserva la decisión utilizada para la sección inferior de VLSM.

        if not self.advertencias_compactas_habilitadas:
            self.panel_advertencias_vlsm.hide()  # Oculta inmediatamente la sección cuando el usuario desactiva la preferencia.
            return  # Mantiene intactos los diagnósticos formales y la pestaña completa de Errores / Advertencias.

        if self.resultado_actual is not None:
            self._mostrar_advertencias_compactas(
                self.resultado_actual
            )  # Recupera inmediatamente el panel cuando existe una compilación vigente que contiene advertencias.

    def _aplicar_icono(self, boton: QPushButton, nombre_archivo: str, tamano: int = 18) -> None:
        boton.setProperty("recurso_tema", nombre_archivo)  # Declara el nombre lógico para permitir que el gestor actualice posteriormente el icono según el tema.
        ruta = ruta_icono_oscuro(nombre_archivo)  # Recupera el recurso inicial desde la categoría oscura antes de aplicar el tema activo.

        if ruta.exists():
            boton.setIcon(QIcon(str(ruta)))  # Utiliza el PNG existente como icono del botón.
            boton.setIconSize(QSize(tamano, tamano))  # Adapta el recurso al tamaño requerido.

    def _configurar_boton_flotante_panel(
        self,
        boton: QPushButton,
        objetivo: QWidget,
        tooltip: str,
        modo: str,
    ) -> None:
        boton.setText("")  # Conserva únicamente el icono gráfico.
        boton.setToolTip(tooltip)  # Explica la acción al mantener el cursor encima.
        boton.setObjectName("BotonFlotantePanel")  # Utiliza el estilo visual preparado para estas acciones.
        boton.setCursor(Qt.CursorShape.PointingHandCursor)  # Muestra la manita convencional de una acción clickeable.

        if modo == "diagnosticos":
            boton.setFixedSize(26, 26)  # Mantiene una acción compacta dentro de la franja de diagnósticos.
            boton.setIconSize(QSize(15, 15))  # Reduce proporcionalmente el recurso gráfico.
        else:
            boton.setFixedSize(32, 32)  # Mantiene el tamaño normal del botón de análisis.
            boton.setIconSize(QSize(18, 18))  # Conserva un icono legible dentro de la acción.

        boton.setParent(objetivo)  # Mantiene el botón dentro de una superficie fija que no participa en el scroll.
        boton.hide()  # Elimina visualmente la acción mientras todavía no exista nada que copiar.
        boton.raise_()  # Mantiene el botón en la capa superior de su contenedor.

        self.botones_flotantes[objetivo] = (boton, modo)  # Registra la relación utilizada para reposicionarlo.
        objetivo.installEventFilter(self)  # Detecta cambios de tamaño y visualización del widget padre.

        if modo == "analisis" and isinstance(objetivo, QPlainTextEdit):
            objetivo.viewport().installEventFilter(self)  # Detecta cambios de geometría del área útil producidos por scrollbars.
            objetivo.verticalScrollBar().rangeChanged.connect(
                lambda _minimo, _maximo, panel=objetivo: self._reubicar_boton_flotante(panel)
            )  # Recalcula la posición cuando aparece o desaparece la barra vertical.
            objetivo.horizontalScrollBar().rangeChanged.connect(
                lambda _minimo, _maximo, panel=objetivo: self._reubicar_boton_flotante(panel)
            )  # Recalcula la posición cuando aparece o desaparece la barra horizontal.

        if modo == "diagnosticos":
            self.panel_diagnosticos.installEventFilter(self)  # Detecta cambios de geometría del panel usado como referencia visual.
            self.panel_diagnosticos.tabBar().installEventFilter(self)  # Detecta cambios en la barra de Detectados y Catálogo.

    def _establecer_visibilidad_boton_flotante(self, objetivo: QWidget, visible: bool) -> None:
        configuracion = self.botones_flotantes.get(objetivo)  # Recupera la acción relacionada con la superficie.

        if configuracion is None:
            return  # Finaliza cuando la superficie no posee una acción flotante registrada.

        boton, _modo = configuracion  # Obtiene el botón flotante registrado.
        boton.setVisible(visible)  # Muestra u oculta por completo la acción según corresponda.

        if visible:
            self._reubicar_boton_flotante(objetivo)  # Calcula su posición antes de mostrarla definitivamente.
            boton.raise_()  # Garantiza que se mantenga en la capa superior.

    def eventFilter(self, objeto, evento) -> bool:
        if objeto in self.botones_flotantes:
            if evento.type() in (
                QEvent.Type.Resize,
                QEvent.Type.Show,
                QEvent.Type.LayoutRequest,
            ):
                self._reubicar_boton_flotante(objeto)  # Mantiene anclado el botón cuando cambia su widget padre.

        if hasattr(self, "texto_analisis") and objeto is self.texto_analisis.viewport():
            if evento.type() in (
                QEvent.Type.Resize,
                QEvent.Type.Show,
            ):
                self._reubicar_boton_flotante(self.texto_analisis)  # Actualiza la posición al cambiar el área útil del visor.

        if objeto is self.panel_diagnosticos or objeto is self.panel_diagnosticos.tabBar():
            if evento.type() in (
                QEvent.Type.Resize,
                QEvent.Type.Show,
                QEvent.Type.Move,
                QEvent.Type.LayoutRequest,
            ):
                if self.superficie_diagnosticos is not None:
                    self._reubicar_boton_flotante(self.superficie_diagnosticos)  # Mantiene la acción alineada con la barra aunque el panel cambie de geometría.

        return super().eventFilter(objeto, evento)  # Permite que Qt siga procesando normalmente el evento.

    def _reubicar_boton_flotante(self, objetivo: QWidget) -> None:
        configuracion = self.botones_flotantes.get(objetivo)  # Recupera botón y modo relacionados con el panel.

        if configuracion is None:
            return  # Finaliza cuando el panel no posee una acción registrada.

        boton, modo = configuracion  # Separa la acción y su estrategia de ubicación.

        if not boton.isVisible():
            return  # Evita calcular posiciones para controles actualmente ocultos.

        if modo == "analisis" and isinstance(objetivo, QPlainTextEdit):
            geometria_viewport = objetivo.viewport().geometry()  # Obtiene la superficie visible real excluyendo scrollbars y bordes.
            posicion_x = geometria_viewport.x() + geometria_viewport.width() - boton.width() - 8  # Ancla el botón al extremo derecho del área útil.
            posicion_y = geometria_viewport.y() + 4  # Mantiene la acción apenas separada del borde superior.
        elif modo == "diagnosticos":
            geometria_panel = self.panel_diagnosticos.geometry()  # Obtiene la posición del panel respecto al contenedor exterior.
            alto_barra = self.panel_diagnosticos.tabBar().height()  # Obtiene la altura real de Detectados y Catálogo.
            posicion_x = geometria_panel.x() + geometria_panel.width() - boton.width() - 3  # Alinea la acción con el extremo derecho del panel.
            posicion_y = geometria_panel.y() + (alto_barra - boton.height()) // 2 - 2  # Sube el botón sobre la franja sin quedar limitado por el borde del panel.
        else:
            posicion_x = max(4, objetivo.width() - boton.width() - 8)  # Proporciona una ubicación convencional como respaldo.
            posicion_y = 8  # Mantiene una distancia pequeña desde la parte superior.

        boton.move(posicion_x, posicion_y)  # Mueve únicamente el botón fijo, nunca el contenido desplazable.
        boton.raise_()  # Garantiza que permanezca en la capa visual superior.

    def _construir_entrada_salida(self) -> None:
        self.tab_entrada_salida = QWidget()  # Crea el contenedor de la primera pestaña principal.
        diseno = QVBoxLayout(self.tab_entrada_salida)  # Organiza entrada, acciones y salidas.
        diseno.setContentsMargins(8, 8, 8, 8)  # Mantiene un margen discreto alrededor del contenido.
        diseno.setSpacing(8)  # Define una separación uniforme.

        panel_entrada = QFrame()  # Crea un bloque visual independiente para el editor.
        panel_entrada.setObjectName("Panel")  # Aplica el estilo general de los paneles.
        diseno_entrada = QVBoxLayout(panel_entrada)  # Organiza el contenido del bloque de entrada.

        titulo = QLabel("Entrada")  # Identifica el área destinada al código fuente.
        titulo.setObjectName("TituloSeccion")  # Aplica el estilo reservado para títulos internos.
        diseno_entrada.addWidget(titulo)  # Coloca el título encima del editor.
        diseno_entrada.addWidget(self.editor_codigo, 1)  # Permite que el editor utilice la mayor parte del panel.

        botones = QHBoxLayout()  # Crea la fila de acciones principales.

        self.boton_analizar = QPushButton("Compilar")  # Crea la acción principal del flujo.
        self.boton_analizar.setObjectName("BotonPrincipal")  # Destaca visualmente la compilación.
        self.boton_analizar.setShortcut("Ctrl+Return")  # Permite ejecutar rápidamente desde teclado.
        self._aplicar_icono(self.boton_analizar, "Compilar.png")  # Coloca el icono oficial de compilación.
        self.boton_analizar.clicked.connect(self.accion_analizar)  # Ejecuta el flujo al pulsar el botón.

        self.boton_exportar_excel = QPushButton("Exportar Excel")  # Crea la exportación de la tabla VLSM.
        self.boton_exportar_excel.setToolTip("Guardar las subredes VLSM en un archivo de Excel")  # Describe su finalidad.
        self.boton_exportar_excel.setEnabled(False)  # Impide utilizarla antes de generar subredes.
        self._aplicar_icono(self.boton_exportar_excel, "Exportar_excel.png")  # Coloca el recurso correspondiente.
        self.boton_exportar_excel.clicked.connect(self._exportar_excel)  # Abre la exportación al activarse.

        self.boton_exportar_reporte = QPushButton("Exportar reporte")  # Crea la exportación del reporte textual.
        self.boton_exportar_reporte.setToolTip("Guardar el análisis actual en un archivo TXT")  # Describe la acción.
        self.boton_exportar_reporte.setEnabled(False)  # Impide utilizarla antes de una compilación.
        self._aplicar_icono(self.boton_exportar_reporte, "Exportar_reporte.png")  # Coloca el icono correspondiente.
        self.boton_exportar_reporte.clicked.connect(self._exportar_reporte)  # Ejecuta la exportación textual.

        self.boton_limpiar = QPushButton("Limpiar")  # Crea la acción que restaura la aplicación.
        self._aplicar_icono(self.boton_limpiar, "Limpiar.png")  # Coloca el recurso correspondiente.
        self.boton_limpiar.clicked.connect(self.accion_limpiar)  # Ejecuta la limpieza solicitada por la ventana.

        botones.addWidget(self.boton_analizar)  # Agrega la compilación al grupo de acciones.
        botones.addWidget(self.boton_exportar_excel)  # Agrega la exportación de Excel.
        botones.addWidget(self.boton_exportar_reporte)  # Agrega la exportación textual.
        botones.addWidget(self.boton_limpiar)  # Agrega la restauración de la interfaz.
        botones.addStretch()  # Mantiene todas las acciones alineadas a la izquierda.
        diseno_entrada.addLayout(botones)  # Coloca las acciones debajo del editor.

        diseno.addWidget(panel_entrada, 2)  # Reserva una porción moderada del espacio para la entrada.

        self.pestanas_salida = QTabWidget()  # Crea las subpestañas que contienen los diferentes resultados.
        self.tab_resumen = self._crear_resumen()  # Construye la vista rápida del análisis.
        self.tab_analisis = self._crear_tab_analisis()  # Construye la salida léxica y sintáctica.
        self.tab_vlsm = self._crear_tab_vlsm()  # Construye la tabla VLSM junto con su panel compacto opcional de advertencias.
        self.tab_errores = self._crear_tab_errores()  # Construye la vista completa de errores y advertencias.

        self.pestanas_salida.addTab(self.tab_resumen, "Resumen")  # Agrega el resumen.
        self.pestanas_salida.addTab(self.tab_analisis, "Análisis léxico-sintáctico")  # Agrega la salida técnica.
        self.pestanas_salida.addTab(self.tab_vlsm, "Tabla VLSM")  # Agrega los resultados de subneteo.
        self.pestanas_salida.addTab(self.tab_errores, "Errores / Advertencias")  # Agrega los diagnósticos completos.

        diseno.addWidget(self.pestanas_salida, 3)  # Permite que las salidas utilicen ligeramente más espacio que la entrada.

    def _crear_tab_vlsm(self) -> QWidget:
        contenedor = QWidget()  # Crea la superficie completa utilizada por la vista de VLSM.
        diseno = QVBoxLayout(contenedor)  # Permite que el splitter utilice toda la pestaña.
        diseno.setContentsMargins(4, 4, 4, 4)  # Mantiene el margen compacto utilizado por las demás salidas.
        diseno.setSpacing(0)  # Deja que el divisor visual sea quien separe ambos bloques.

        self.divisor_vlsm = QSplitter(Qt.Orientation.Vertical, contenedor)  # Permite repartir manualmente espacio entre VLSM y advertencias.
        self.divisor_vlsm.setChildrenCollapsible(False)  # Evita que el usuario colapse accidentalmente la tabla principal hasta desaparecer.
        self.divisor_vlsm.setHandleWidth(5)  # Mantiene un divisor suficientemente visible sin ocupar demasiado espacio.

        self.tabla_vlsm = TablaResultados(
            0,
            9,
            [1.15, 1.35, 1.35, 1.45, 0.55, 1.25, 1.15, 1.15, 1.15],
            [120, 145, 145, 160, 70, 150, 145, 145, 145],
        )  # Mantiene cada dato VLSM legible y habilita scroll cuando las nueve columnas no caben.
        self.tabla_vlsm.setHorizontalHeaderLabels(
            [
                "Red",
                "Hosts solicitados",
                "Hosts disponibles",
                "Dirección de red",
                "CIDR",
                "Máscara",
                "Primera IP",
                "Última IP",
                "Broadcast",
            ]
        )  # Define las columnas visibles.
        self._configurar_tabla(self.tabla_vlsm)  # Aplica el comportamiento visual común.

        self.panel_advertencias_vlsm = QFrame()  # Crea la sección inferior destinada únicamente a advertencias no bloqueantes.
        self.panel_advertencias_vlsm.setObjectName("Panel")  # Reutiliza el estilo general de paneles de TecNet Finder.
        self.panel_advertencias_vlsm.setMinimumHeight(150)  # Evita que el divisor comprima el panel hasta ocultar el contenido de las advertencias.

        diseno_advertencias = QVBoxLayout(self.panel_advertencias_vlsm)  # Organiza encabezado y tabla compacta.
        diseno_advertencias.setContentsMargins(8, 6, 8, 8)  # Mantiene el panel compacto sin pegar su contenido a los bordes.
        diseno_advertencias.setSpacing(5)  # Separa discretamente el título de la tabla.

        fila_titulo_advertencias = QHBoxLayout()  # Permite mostrar el título y la cantidad de advertencias sobre una misma línea.
        fila_titulo_advertencias.setContentsMargins(0, 0, 0, 0)  # Evita agregar márgenes adicionales.

        self.titulo_advertencias_vlsm = QLabel("Advertencias")  # Identifica claramente que la información no corresponde con errores bloqueantes.
        self.titulo_advertencias_vlsm.setObjectName("TituloSeccion")  # Mantiene el mismo formato de los títulos internos.
        fila_titulo_advertencias.addWidget(self.titulo_advertencias_vlsm)  # Coloca el nombre de la sección a la izquierda.

        self.contador_advertencias_vlsm = QLabel("0")  # Muestra cuántas advertencias acompañan actualmente al resultado.
        self.contador_advertencias_vlsm.setStyleSheet(
            "color: #f9e2af; font-weight: 700;"
        )  # Utiliza el amarillo definido para advertencias semánticas y generales.
        fila_titulo_advertencias.addWidget(self.contador_advertencias_vlsm)  # Coloca el contador inmediatamente después del título.
        fila_titulo_advertencias.addStretch()  # Mantiene ambos textos alineados hacia la izquierda.

        self.tabla_advertencias_vlsm = TablaResultados(
            0,
            3,
            [0.35, 1.40, 1.75],
            [90, 300, 360],
        )  # Conserva Código compacto y reserva el espacio principal para Mensaje y Solución.
        self.tabla_advertencias_vlsm.setHorizontalHeaderLabels(
            [
                "Código",
                "Mensaje",
                "Solución",
            ]
        )  # Define una vista resumida sin repetir categoría, línea y columna.
        self.tabla_advertencias_vlsm.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide editar la información mostrada.
        self.tabla_advertencias_vlsm.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Permite identificar visualmente una advertencia completa.
        self.tabla_advertencias_vlsm.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Limita la interacción a una advertencia por vez.
        self.tabla_advertencias_vlsm.setAlternatingRowColors(True)  # Facilita distinguir advertencias consecutivas.
        self.tabla_advertencias_vlsm.setWordWrap(True)  # Permite que Mensaje y Solución ocupen varias líneas en lugar de quedar recortados horizontalmente.
        self.tabla_advertencias_vlsm.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar texto mediante puntos suspensivos.
        self.tabla_advertencias_vlsm.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Permite explorar columnas cuando los mínimos no caben en media pantalla.
        self.tabla_advertencias_vlsm.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Mantiene suave el desplazamiento horizontal.
        self.tabla_advertencias_vlsm.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Mantiene accesibles varias advertencias cuando el panel alcanza su altura práctica.
        self.tabla_advertencias_vlsm.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite recorrer cómodamente filas altas producidas por textos extensos.
        self.tabla_advertencias_vlsm.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_advertencias_vlsm.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )  # Hace crecer automáticamente cada fila según las líneas necesarias para Mensaje y Solución.
        self.tabla_advertencias_vlsm.verticalHeader().setMinimumSectionSize(38)  # Conserva una altura mínima cómoda aun cuando una advertencia sea corta.

        encabezado_advertencias = self.tabla_advertencias_vlsm.horizontalHeader()  # Obtiene el encabezado de la tabla compacta.
        encabezado_advertencias.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Deja la distribución bajo control de TablaResultados.
        encabezado_advertencias.setStretchLastSection(False)  # Evita deformar la última columna únicamente para rellenar espacio.
        encabezado_advertencias.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra los tres encabezados.
        encabezado_advertencias.setMinimumSectionSize(50)  # Conserva un mínimo interno seguro.

        self.tabla_advertencias_vlsm.cellDoubleClicked.connect(
            self._activar_advertencia_compacta
        )  # Permite saltar al código fuente mediante doble clic sobre una advertencia.

        diseno_advertencias.addLayout(fila_titulo_advertencias)  # Coloca primero el encabezado compacto.
        diseno_advertencias.addWidget(self.tabla_advertencias_vlsm, 1)  # Entrega el resto del panel a la tabla de advertencias.

        self.divisor_vlsm.addWidget(self.tabla_vlsm)  # Coloca VLSM como sección principal superior.
        self.divisor_vlsm.addWidget(self.panel_advertencias_vlsm)  # Coloca las advertencias como sección secundaria inferior.
        self.divisor_vlsm.setStretchFactor(0, 4)  # Da prioridad espacial a los resultados VLSM.
        self.divisor_vlsm.setStretchFactor(1, 1)  # Reserva una porción menor para las advertencias.
        self.panel_advertencias_vlsm.hide()  # Mantiene toda la superficie disponible para VLSM mientras no existan advertencias.

        diseno.addWidget(self.divisor_vlsm, 1)  # Hace que ambas secciones utilicen toda la superficie disponible.

        return contenedor  # Devuelve la pestaña VLSM completamente construida.

    def _crear_tab_analisis(self) -> QWidget:
        contenedor = QWidget()  # Crea la subpestaña completa.
        diseno = QVBoxLayout(contenedor)  # Organiza únicamente la salida textual.
        diseno.setContentsMargins(4, 4, 4, 4)  # Mantiene el margen normal sin reservar espacio para acciones.

        self.texto_analisis = self._crear_salida_textual()  # Crea el visor de análisis.
        diseno.addWidget(self.texto_analisis, 1)  # Permite que utilice toda la superficie disponible.

        self.boton_copiar_analisis = QPushButton()  # Crea una acción independiente del contenido desplazable.
        self.boton_copiar_analisis.setEnabled(False)  # La mantiene inactiva hasta producir resultados.
        self._aplicar_icono(self.boton_copiar_analisis, "Copiar.png")  # Utiliza el recurso gráfico de copiado.

        self._configurar_boton_flotante_panel(
            self.boton_copiar_analisis,
            self.texto_analisis,
            "Copiar análisis",
            "analisis",
        )  # Hace que el botón pertenezca al QPlainTextEdit fijo y no al viewport desplazable.

        self.boton_copiar_analisis.clicked.connect(self._copiar_analisis)  # Copia el contenido actual al portapapeles.

        return contenedor  # Devuelve la vista técnica construida.

    def _crear_tab_errores(self) -> QWidget:
        contenedor = QWidget()  # Crea la superficie exterior que actuará como capa fija para la acción de copiado.
        self.superficie_diagnosticos = contenedor  # Conserva la superficie para mostrar, ocultar y reposicionar la acción.

        diseno = QVBoxLayout(contenedor)  # Organiza únicamente el panel estructurado de diagnósticos.
        diseno.setContentsMargins(4, 4, 4, 4)  # Mantiene el margen convencional alrededor del panel.

        diseno.addWidget(self.panel_diagnosticos, 1)  # Permite que Detectados y Catálogo utilicen todo el espacio disponible.

        self.boton_copiar_diagnosticos = QPushButton()  # Crea una acción independiente del panel interno desplazable.
        self.boton_copiar_diagnosticos.setEnabled(False)  # La mantiene inactiva hasta que existan diagnósticos.
        self._aplicar_icono(self.boton_copiar_diagnosticos, "Copiar.png")  # Utiliza el recurso oficial de copiado.

        self._configurar_boton_flotante_panel(
            self.boton_copiar_diagnosticos,
            contenedor,
            "Copiar diagnósticos",
            "diagnosticos",
        )  # Coloca la acción en una capa exterior que puede sobresalir por encima del panel sin recortarse.

        self.boton_copiar_diagnosticos.clicked.connect(self._copiar_diagnosticos)  # Copia el registro estructurado.

        return contenedor  # Devuelve la pestaña completa de diagnósticos.

    def _crear_resumen(self) -> QWidget:
        contenedor = QWidget()  # Crea el widget base del resumen.
        diseno = QVBoxLayout(contenedor)  # Organiza encabezado, estado y tarjetas.
        diseno.setContentsMargins(12, 12, 12, 12)  # Mantiene un margen uniforme.
        diseno.setSpacing(10)  # Separa adecuadamente las secciones.

        titulo = QLabel("Resumen del análisis")  # Crea el encabezado principal.
        titulo.setObjectName("TituloResumen")  # Aplica el estilo correspondiente.
        diseno.addWidget(titulo)  # Coloca el encabezado en la parte superior.

        self.estado_resumen = QLabel("Sin análisis ejecutado.")  # Muestra inicialmente un estado neutral.
        self.estado_resumen.setObjectName("EstadoNeutral")  # Aplica el estilo inicial.
        diseno.addWidget(self.estado_resumen)  # Coloca el estado debajo del título.

        cuadricula = QGridLayout()  # Organiza seis tarjetas de información.
        cuadricula.setHorizontalSpacing(10)  # Define la separación horizontal.
        cuadricula.setVerticalSpacing(10)  # Define la separación vertical.

        datos_tarjetas = [
            ("tokens", "Tokens reconocidos", "TarjetaTokens", "ValorTokens"),
            ("bloques", "Bloques sintácticos", "TarjetaBloques", "ValorBloques"),
            ("subredes", "Subredes generadas", "TarjetaSubredes", "ValorSubredes"),
            ("errores_lexicos", "Errores léxicos", "TarjetaLexicos", "ValorLexicos"),
            ("errores_sintacticos", "Errores sintácticos", "TarjetaSintacticos", "ValorSintacticos"),
            ("advertencias", "Advertencias", "TarjetaAdvertencias", "ValorAdvertencias"),
        ]  # Define las seis métricas correspondientes al alcance actual.

        posiciones = {
            "tokens": (0, 0, 1, 2),
            "bloques": (0, 2, 1, 2),
            "subredes": (0, 4, 1, 2),
            "errores_lexicos": (1, 0, 1, 2),
            "errores_sintacticos": (1, 2, 1, 2),
            "advertencias": (1, 4, 1, 2),
        }  # Distribuye las tarjetas en dos filas equilibradas.

        for clave, texto, nombre_tarjeta, nombre_valor in datos_tarjetas:
            tarjeta = QFrame()  # Crea el contenedor visual de la métrica.
            tarjeta.setObjectName(nombre_tarjeta)  # Permite asignarle un borde específico.
            diseno_tarjeta = QVBoxLayout(tarjeta)  # Organiza título y valor.
            diseno_tarjeta.setContentsMargins(12, 10, 12, 10)  # Mantiene espacio interior.

            titulo_tarjeta = QLabel(texto)  # Muestra el nombre de la métrica.
            titulo_tarjeta.setObjectName("TituloTarjeta")  # Aplica el formato general de títulos.
            titulo_tarjeta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el texto.

            valor_tarjeta = QLabel("0")  # Inicializa el valor en cero.
            valor_tarjeta.setObjectName(nombre_valor)  # Permite colorear individualmente la métrica.
            valor_tarjeta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el contador.

            diseno_tarjeta.addWidget(titulo_tarjeta)  # Coloca el nombre arriba.
            diseno_tarjeta.addWidget(valor_tarjeta, 1)  # Permite que el valor utilice el espacio sobrante.
            self.tarjetas_resumen[clave] = valor_tarjeta  # Conserva la referencia necesaria para actualizarlo.

            fila, columna, filas_ocupadas, columnas_ocupadas = posiciones[clave]  # Recupera la ubicación asignada.
            cuadricula.addWidget(tarjeta, fila, columna, filas_ocupadas, columnas_ocupadas)  # Inserta la tarjeta.

        for columna in range(6):
            cuadricula.setColumnStretch(columna, 1)  # Distribuye uniformemente todo el ancho disponible.

        cuadricula.setRowStretch(0, 1)  # Permite expandir la primera fila.
        cuadricula.setRowStretch(1, 1)  # Permite expandir la segunda fila.
        diseno.addLayout(cuadricula, 1)  # Entrega todo el espacio restante a las tarjetas.

        return contenedor  # Devuelve la vista de resumen terminada.

    def _construir_tablas(self) -> None:
        self.tab_tablas = QWidget()  # Crea el contenedor principal.
        diseno = QVBoxLayout(self.tab_tablas)  # Organiza sus subpestañas.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene un margen reducido.

        pestanas = QTabWidget()  # Crea las vistas de tokens y reservadas.
        diseno.addWidget(pestanas)  # Permite que utilicen toda la superficie.

        self.tabla_tokens = TablaResultados(
            0,
            4,
            [1.25, 1.90, 0.70, 0.80],
            [110, 190, 75, 85],
        )  # Mantiene legibles Tipo, Valor y posiciones incluso cuando la ventana está dividida.
        self.tabla_tokens.setHorizontalHeaderLabels(["Tipo", "Valor", "Línea", "Posición"])  # Define las columnas visibles.
        self._configurar_tabla(self.tabla_tokens)  # Aplica la configuración común.

        self.tabla_reservadas = TablaResultados(
            0,
            2,
            [1.50, 0.85],
            [190, 100],
        )  # Conserva anchos mínimos apropiados para las palabras reservadas y sus cantidades.
        self.tabla_reservadas.setHorizontalHeaderLabels(["Palabra reservada", "Cantidad"])  # Define sus columnas.
        self._configurar_tabla(self.tabla_reservadas)  # Aplica la configuración común.

        pestanas.addTab(self.tabla_tokens, "Tabla de tokens")  # Agrega los tokens.
        pestanas.addTab(self.tabla_reservadas, "Tabla de palabras reservadas")  # Agrega el conteo global.

    def _construir_sintaxis(self) -> None:
        self.tab_sintaxis = QWidget()  # Crea la sección principal de sintaxis.
        diseno = QVBoxLayout(self.tab_sintaxis)  # Organiza sus vistas.
        diseno.setContentsMargins(6, 6, 6, 6)  # Reduce el margen exterior.

        pestanas = QTabWidget()  # Crea las tres vistas sintácticas.
        diseno.addWidget(pestanas)  # Permite que ocupen todo el espacio.

        self.texto_producciones = self._crear_salida_textual()  # Crea el visor de producciones.
        self.texto_derivacion = self._crear_salida_textual()  # Crea el visor de derivación.
        self.visor_arbol = VisorArbolSintactico()  # Crea el visor textual y gráfico del árbol.

        pestanas.addTab(self.texto_producciones, "Producciones usadas")  # Agrega las producciones.
        pestanas.addTab(self.texto_derivacion, "Derivación")  # Agrega la derivación.
        pestanas.addTab(self.visor_arbol, "Árboles")  # Agrega los árboles.

    def _construir_fases_posteriores(self) -> None:
        self.tab_fases_posteriores = QWidget()  # Crea el contenedor de las etapas futuras.
        diseno = QVBoxLayout(self.tab_fases_posteriores)  # Organiza las futuras fases.
        diseno.setContentsMargins(6, 6, 6, 6)  # Mantiene el mismo margen que las demás secciones.

        pestanas = QTabWidget()  # Crea una pestaña por cada fase futura.
        diseno.addWidget(pestanas)  # Permite que utilicen todo el espacio.

        codigo_intermedio = self._crear_salida_textual()  # Reserva el espacio de la Unidad 2.
        optimizacion = self._crear_salida_textual()  # Reserva el espacio de la Unidad 3.
        codigo_objeto = self._crear_salida_textual()  # Reserva el espacio de la Unidad 4.

        codigo_intermedio.setPlainText("Esta fase se implementará durante la Unidad 2 de Lenguajes y Autómatas II.")  # Mantiene clara su condición futura.
        optimizacion.setPlainText("Esta fase se implementará durante la Unidad 3 de Lenguajes y Autómatas II.")  # Mantiene clara su condición futura.
        codigo_objeto.setPlainText("Esta fase se implementará durante la Unidad 4 de Lenguajes y Autómatas II.")  # Mantiene clara su condición futura.

        pestanas.addTab(codigo_intermedio, "Código intermedio")  # Agrega la fase de la Unidad 2.
        pestanas.addTab(optimizacion, "Optimización")  # Agrega la fase de la Unidad 3.
        pestanas.addTab(codigo_objeto, "Código objeto")  # Agrega la fase de la Unidad 4.

    def _crear_salida_textual(self) -> QPlainTextEdit:
        salida = QPlainTextEdit()  # Crea un visor adecuado para información técnica extensa.
        salida.setReadOnly(True)  # Impide alterar las salidas generadas.
        salida.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # Conserva alineación y estructura de los resultados.
        return salida  # Devuelve el visor listo para utilizarse.

    def _configurar_tabla(self, tabla: QTableWidget) -> None:
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar los resultados.
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Selecciona filas completas.
        tabla.setAlternatingRowColors(True)  # Facilita distinguir filas consecutivas.
        tabla.setWordWrap(False)  # Mantiene uniforme la altura de las filas.
        tabla.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar datos mediante puntos suspensivos.
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra scroll únicamente cuando los anchos mínimos requieren más espacio.
        tabla.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite desplazamiento horizontal continuo.
        tabla.verticalHeader().setVisible(False)  # Oculta el encabezado numérico automático.
        tabla.verticalHeader().setDefaultSectionSize(36)  # Mantiene una altura uniforme.

        encabezado = tabla.horizontalHeader()  # Obtiene el encabezado horizontal.
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)  # Permite que la clase responsiva controle manualmente cada ancho.
        encabezado.setStretchLastSection(False)  # Evita que la última columna absorba arbitrariamente el espacio restante.
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra todos los títulos.
        encabezado.setMinimumSectionSize(50)  # Evita que Qt reduzca internamente una sección hasta volverla ilegible.

    def _crear_item_centrado(self, valor: str) -> QTableWidgetItem:
        item = QTableWidgetItem(valor)  # Crea la celda utilizando el valor recibido.
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra el contenido en ambas direcciones.
        return item  # Devuelve la celda lista para insertarse.

    def _insertar_fila_grupo(self, tabla: QTableWidget, texto: str) -> int:
        fila = tabla.rowCount()  # Obtiene la siguiente posición disponible.
        tabla.insertRow(fila)  # Reserva una fila completa.
        tabla.setSpan(fila, 0, 1, tabla.columnCount())  # Une todas las columnas para formar un encabezado de grupo.

        item = QTableWidgetItem(texto)  # Crea el identificador visual.
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Evita tratar la franja como un dato seleccionable.
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)  # Mantiene el título alineado a la izquierda.
        item.setForeground(QBrush(QColor("#89b4fa")))  # Utiliza azul para identificar la agrupación.
        item.setBackground(QBrush(QColor("#313244")))  # Diferencia la franja de las filas normales.

        fuente = item.font()  # Obtiene la fuente heredada.
        fuente.setBold(True)  # Destaca el identificador.
        item.setFont(fuente)  # Aplica la modificación.

        tabla.setItem(fila, 0, item)  # Inserta la franja en la tabla.
        tabla.setRowHeight(fila, 32)  # Mantiene una altura compacta para el encabezado.

        return fila  # Devuelve la posición de la franja creada.

    def mostrar_resultado(self, resultado: ResultadoCompilacion) -> None:
        self.resultado_actual = resultado  # Conserva la compilación actual.
        self.codigo_fuente_resultado = self.editor_codigo.toPlainText()  # Conserva la entrada que produjo los resultados.
        self.boton_exportar_excel.setEnabled(bool(resultado.subredes_vlsm))  # Habilita Excel únicamente cuando existen subredes.
        self.boton_exportar_reporte.setEnabled(True)  # Habilita el reporte después de cualquier compilación.
        self.boton_copiar_analisis.setEnabled(True)  # Habilita la copia del análisis generado.
        self.boton_copiar_diagnosticos.setEnabled(bool(resultado.diagnosticos))  # Habilita la copia cuando existen diagnósticos.

        self._mostrar_resumen(resultado)  # Actualiza las tarjetas generales.
        self._mostrar_analisis(resultado)  # Actualiza el reporte léxico-sintáctico.
        self._mostrar_vlsm(resultado)  # Actualiza las subredes VLSM.
        self._mostrar_tokens(resultado)  # Actualiza los tokens.
        self._mostrar_reservadas(resultado)  # Actualiza el conteo de palabras reservadas.
        self._mostrar_advertencias_compactas(resultado)  # Actualiza u oculta la sección inferior según la preferencia actual.

        sintactico = resultado.resultado_sintactico  # Obtiene una referencia corta al resultado del parser.
        self.texto_producciones.setPlainText(sintactico.producciones_usadas)  # Muestra las producciones utilizadas.
        self.texto_derivacion.setPlainText(sintactico.derivacion)  # Muestra la derivación.
        self.visor_arbol.mostrar_arboles(sintactico.arboles, sintactico.arbol_textual)  # Actualiza ambos tipos de árbol.

        self._establecer_visibilidad_boton_flotante(
            self.texto_analisis,
            bool(self.texto_analisis.toPlainText()),
        )  # Muestra Copiar análisis únicamente cuando existe información válida.

        if self.superficie_diagnosticos is not None:
            self._establecer_visibilidad_boton_flotante(
                self.superficie_diagnosticos,
                bool(resultado.diagnosticos),
            )  # Muestra Copiar diagnósticos únicamente cuando existen problemas o advertencias.

        if not self.navegacion_automatica:
            return  # Conserva exactamente la pestaña actual cuando el usuario desactivó la navegación automática.

        cantidad_advertencias = sum(
            1
            for diagnostico in resultado.diagnosticos
            if diagnostico.severidad in ("warning", "advertencia")
        )  # Cuenta las advertencias independientemente de si la vista compacta se encuentra visible.

        self.setCurrentWidget(self.tab_entrada_salida)  # Regresa a la zona principal únicamente cuando la navegación automática está habilitada.

        if resultado.tiene_errores:
            self.pestanas_salida.setCurrentWidget(self.tab_errores)  # Da prioridad absoluta a la corrección de errores bloqueantes.
            self.panel_diagnosticos.setCurrentIndex(0)  # Garantiza que Detectados quede visible dentro de la pestaña completa.
        elif resultado.subredes_vlsm:
            self.pestanas_salida.setCurrentWidget(self.tab_vlsm)  # Mantiene Tabla VLSM como salida principal aunque existan advertencias.
        elif cantidad_advertencias > 0:
            self.pestanas_salida.setCurrentWidget(self.tab_errores)  # Muestra la vista completa cuando existen advertencias pero no se produjo VLSM.
            self.panel_diagnosticos.setCurrentIndex(0)  # Garantiza que Detectados quede visible.
        else:
            self.pestanas_salida.setCurrentWidget(self.tab_resumen)  # Utiliza el resumen cuando no existen subredes ni diagnósticos relevantes.

    def _mostrar_advertencias_compactas(self, resultado: ResultadoCompilacion) -> None:
        advertencias = [
            diagnostico
            for diagnostico in resultado.diagnosticos
            if diagnostico.severidad in ("warning", "advertencia")
        ]  # Conserva únicamente diagnósticos no bloqueantes.

        self.advertencias_compactas_actuales = list(advertencias)  # Mantiene la misma secuencia utilizada visualmente para navegación.
        self.tabla_advertencias_vlsm.setRowCount(0)  # Elimina advertencias pertenecientes a la compilación anterior.
        self.contador_advertencias_vlsm.setText(str(len(advertencias)))  # Actualiza el contador visible junto al título.

        if (
            not self.advertencias_compactas_habilitadas
            or not advertencias
            or not resultado.subredes_vlsm
        ):
            self.panel_advertencias_vlsm.hide()  # Entrega nuevamente toda la superficie a VLSM cuando la vista compacta no corresponde.
            return  # Conserva los diagnósticos completos disponibles en Errores / Advertencias.

        for diagnostico in advertencias:
            fila = self.tabla_advertencias_vlsm.rowCount()  # Obtiene la siguiente posición libre.
            self.tabla_advertencias_vlsm.insertRow(fila)  # Reserva una fila compacta para la advertencia.

            valores = [
                diagnostico.codigo,
                diagnostico.mensaje,
                diagnostico.solucion,
            ]  # Conserva únicamente la información esencial para la vista resumida.

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(valor)  # Construye la celda correspondiente.
                item.setForeground(QBrush(QColor("#f9e2af")))  # Utiliza el color oficial reservado para advertencias.
                item.setToolTip(valor)  # Permite consultar el texto completo incluso cuando la ventana sea pequeña.

                if columna == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Mantiene el código centrado y fácil de reconocer.
                    fuente = item.font()  # Obtiene la fuente heredada de la tabla.
                    fuente.setBold(True)  # Refuerza visualmente el identificador.
                    item.setFont(fuente)  # Aplica el énfasis al código.
                else:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                    )  # Coloca Mensaje y Solución desde la esquina superior izquierda para facilitar la lectura de varias líneas.

                self.tabla_advertencias_vlsm.setItem(fila, columna, item)  # Inserta la celda terminada.

        self.panel_advertencias_vlsm.show()  # Hace visible el bloque únicamente después de cargar advertencias válidas.

        QTimer.singleShot(
            0,
            self._ajustar_panel_advertencias_vlsm,
        )  # Espera a que Qt calcule el ancho real antes de ajustar filas y reparto vertical.

    def _ajustar_panel_advertencias_vlsm(self) -> None:
        if not self.panel_advertencias_vlsm.isVisible():
            return  # Evita recalcular una sección que dejó de estar visible.

        self.tabla_advertencias_vlsm._distribuir_columnas()  # Calcula primero los anchos definitivos para que el ajuste de línea utilice el espacio real.
        self.tabla_advertencias_vlsm.resizeRowsToContents()  # Hace crecer cada advertencia según las líneas necesarias para Mensaje y Solución.

        alto_filas = sum(
            self.tabla_advertencias_vlsm.rowHeight(fila)
            for fila in range(self.tabla_advertencias_vlsm.rowCount())
        )  # Calcula la altura real necesaria para las advertencias visibles.

        alto_encabezado_tabla = self.tabla_advertencias_vlsm.horizontalHeader().height()  # Incluye la fila que muestra Código, Mensaje y Solución.
        alto_titulo = self.titulo_advertencias_vlsm.sizeHint().height()  # Conserva espacio suficiente para el encabezado Advertencias.
        alto_margenes = 42  # Reserva espacio para márgenes, separación y bordes del panel.

        alto_necesario = (
            alto_filas
            + alto_encabezado_tabla
            + alto_titulo
            + alto_margenes
        )  # Calcula cuánto espacio permitiría mostrar el contenido sin recortes.

        alto_panel = max(
            165,
            min(alto_necesario, 280),
        )  # Mantiene el panel legible pero evita que varias advertencias consuman excesivamente la vista VLSM.

        alto_total = max(
            self.divisor_vlsm.height(),
            alto_panel + 180,
        )  # Conserva siempre una porción suficiente para la tabla VLSM superior.

        alto_vlsm = max(
            180,
            alto_total - alto_panel,
        )  # Da prioridad a VLSM aunque las advertencias necesiten varias líneas.

        self.divisor_vlsm.setSizes(
            [alto_vlsm, alto_panel]
        )  # Aplica un reparto inicial adaptado al contenido real; posteriormente el usuario puede mover el divisor.

    def _activar_advertencia_compacta(self, fila: int, _columna: int) -> None:
        if fila < 0 or fila >= len(self.advertencias_compactas_actuales):
            return  # Impide navegar cuando la fila dejó de pertenecer a la compilación vigente.

        diagnostico = self.advertencias_compactas_actuales[fila]  # Recupera el diagnóstico original asociado con la fila compacta.

        if diagnostico.linea is None:
            return  # Conserva la vista actual cuando la advertencia no posee una ubicación concreta.

        self.editor_codigo.ir_a_posicion(
            diagnostico.linea,
            diagnostico.columna,
            diagnostico.longitud,
        )  # Lleva directamente al fragmento relacionado con la advertencia.

    def _mostrar_resumen(self, resultado: ResultadoCompilacion) -> None:
        diagnosticos = resultado.diagnosticos  # Obtiene los diagnósticos combinados.
        errores_lexicos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Léxico" and diagnostico.severidad == "error")  # Cuenta errores léxicos.
        errores_sintacticos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Sintáctico" and diagnostico.severidad == "error")  # Cuenta errores sintácticos.
        cantidad_errores = sum(1 for diagnostico in diagnosticos if diagnostico.severidad == "error")  # Cuenta todos los errores actuales.
        cantidad_advertencias = sum(1 for diagnostico in diagnosticos if diagnostico.severidad in ("warning", "advertencia"))  # Cuenta todas las advertencias.

        self.tarjetas_resumen["tokens"].setText(str(len(resultado.resultado_lexico.tokens)))  # Actualiza los tokens reconocidos.
        self.tarjetas_resumen["bloques"].setText(str(len(resultado.bloques_validos)))  # Actualiza los bloques válidos.
        self.tarjetas_resumen["subredes"].setText(str(len(resultado.subredes_vlsm)))  # Actualiza las subredes.
        self.tarjetas_resumen["errores_lexicos"].setText(str(errores_lexicos))  # Actualiza los errores léxicos.
        self.tarjetas_resumen["errores_sintacticos"].setText(str(errores_sintacticos))  # Actualiza los errores sintácticos.
        self.tarjetas_resumen["advertencias"].setText(str(cantidad_advertencias))  # Actualiza las advertencias.

        if cantidad_errores > 0:
            self.estado_resumen.setObjectName("EstadoError")  # Mantiene rojo como prioridad cuando existen errores.
            self.estado_resumen.setText(
                f"Análisis terminado con errores | "
                f"Errores: {cantidad_errores} | "
                f"Advertencias: {cantidad_advertencias} | "
                f"Subredes generadas: {len(resultado.subredes_vlsm)}"
            )  # Resume la compilación cuando existen errores.
        elif cantidad_advertencias > 0:
            self.estado_resumen.setObjectName("EstadoAdvertencia")  # Utiliza amarillo cuando solo existen recomendaciones.
            self.estado_resumen.setText(
                f"Análisis completo con advertencias | "
                f"Advertencias: {cantidad_advertencias} | "
                f"Subredes generadas: {len(resultado.subredes_vlsm)}"
            )  # Resume la compilación válida acompañada por advertencias.
        else:
            self.estado_resumen.setObjectName("EstadoCorrecto")  # Utiliza verde para compilaciones completamente limpias.
            self.estado_resumen.setText(
                f"Análisis completo | "
                f"Bloques válidos: {len(resultado.bloques_validos)} | "
                f"Subredes generadas: {len(resultado.subredes_vlsm)}"
            )  # Resume una compilación completamente limpia.

        self.estado_resumen.style().unpolish(self.estado_resumen)  # Retira temporalmente el estilo anterior.
        self.estado_resumen.style().polish(self.estado_resumen)  # Aplica el estilo correspondiente al nuevo estado.
        self.estado_resumen.update()  # Redibuja inmediatamente la etiqueta.

    def _mostrar_analisis(self, resultado: ResultadoCompilacion) -> None:
        lineas = ["=== ANÁLISIS LÉXICO ===", ""]  # Inicia la salida técnica del lexer.

        if resultado.resultado_lexico.tokens:
            for token in resultado.resultado_lexico.tokens:
                lineas.append(
                    f"Token: {token.tipo:<12} Valor: {token.valor:<18} "
                    f"(Línea {token.linea}, Posición {token.columna})"
                )  # Conserva tipo, valor y ubicación.
        else:
            lineas.append("No se reconocieron tokens.")  # Informa que el lexer no produjo elementos.

        lineas.extend(["", "=== ANÁLISIS SINTÁCTICO ===", ""])  # Separa claramente ambas fases.

        if resultado.bloques_validos:
            for indice, bloque in enumerate(resultado.bloques_validos, start=1):
                nombre = bloque.nombre or "Sin nombre"  # Utiliza una etiqueta comprensible cuando NAME no existe.
                lineas.append(f"Red #{indice}:")  # Identifica cada bloque válido.
                lineas.append(f"  IP: {bloque.direccion_ip}")  # Muestra la IP reconocida.
                lineas.append(f"  Máscara: {bloque.mascara_subred}")  # Muestra la máscara.
                lineas.append(f"  Hosts requeridos: {bloque.cantidades_hosts}")  # Muestra la lista de hosts.
                lineas.append(f"  Nombre: {nombre}")  # Muestra el nombre opcional.
                lineas.append("")  # Separa visualmente cada bloque.
        else:
            lineas.append("No se encontraron bloques sintácticamente válidos.")  # Informa que ninguna instrucción cumplió la gramática.

        cantidad_errores = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad == "error")  # Cuenta errores actuales.
        cantidad_advertencias = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia"))  # Cuenta recomendaciones.

        lineas.append("=== RESUMEN ===")  # Agrega la síntesis final.
        lineas.append(f"Tokens reconocidos: {len(resultado.resultado_lexico.tokens)}")  # Resume tokens.
        lineas.append(f"Bloques sintácticamente válidos: {len(resultado.bloques_validos)}")  # Resume bloques.
        lineas.append(f"Subredes generadas: {len(resultado.subredes_vlsm)}")  # Resume VLSM.
        lineas.append(f"Errores encontrados: {cantidad_errores}")  # Resume errores.
        lineas.append(f"Advertencias encontradas: {cantidad_advertencias}")  # Resume advertencias.
        lineas.append(f"Diagnósticos totales: {len(resultado.diagnosticos)}")  # Conserva el total general.

        self.texto_analisis.setPlainText("\n".join(lineas))  # Muestra el reporte completo.

    def _mostrar_tokens(self, resultado: ResultadoCompilacion) -> None:
        self.tabla_tokens.clearSpans()  # Elimina agrupaciones anteriores.
        self.tabla_tokens.setRowCount(0)  # Vacía la tabla.

        grupos = self._agrupar_tokens_por_red(resultado)  # Divide los tokens por instrucciones.

        for titulo_grupo, tokens in grupos:
            self._insertar_fila_grupo(self.tabla_tokens, titulo_grupo)  # Inserta un encabezado para cada instrucción.

            for token in tokens:
                fila = self.tabla_tokens.rowCount()  # Obtiene la siguiente fila disponible.
                self.tabla_tokens.insertRow(fila)  # Reserva una fila para el token.

                valores = [token.tipo, token.valor, str(token.linea), str(token.columna)]  # Prepara los datos visibles.

                for columna, valor in enumerate(valores):
                    self.tabla_tokens.setItem(fila, columna, self._crear_item_centrado(valor))  # Inserta cada campo centrado.

    def _agrupar_tokens_por_red(self, resultado: ResultadoCompilacion) -> list[tuple[str, list[Token]]]:
        tokens = resultado.resultado_lexico.tokens  # Obtiene la secuencia completa del lexer.

        if not tokens:
            return []  # Evita construir grupos cuando el lexer no reconoció elementos.

        grupos_tokens: list[list[Token]] = []  # Conserva las secuencias asociadas con cada instrucción.
        grupo_actual: list[Token] = []  # Acumula la instrucción recorrida actualmente.

        for token in tokens:
            if token.tipo == "IP" and grupo_actual:
                grupos_tokens.append(grupo_actual)  # Finaliza el grupo anterior al encontrar otro comienzo de instrucción.
                grupo_actual = []  # Prepara una nueva colección para la instrucción siguiente.

            grupo_actual.append(token)  # Agrega el token al grupo activo.

        if grupo_actual:
            grupos_tokens.append(grupo_actual)  # Conserva también el último grupo.

        bloques_por_linea = {bloque.linea_origen: bloque for bloque in resultado.bloques_validos}  # Relaciona bloques válidos con sus líneas iniciales.
        grupos: list[tuple[str, list[Token]]] = []  # Construye la estructura definitiva.

        for grupo in grupos_tokens:
            primer_token = grupo[0]  # Obtiene el elemento inicial de la instrucción.
            linea = primer_token.linea  # Conserva su línea de origen.
            bloque = bloques_por_linea.get(linea)  # Busca un bloque sintáctico válido relacionado.

            if bloque is not None:
                nombre = bloque.nombre or bloque.direccion_ip  # Prioriza NAME y utiliza la IP como respaldo.
                titulo = f"Red: {nombre}    |    IP base: {bloque.direccion_ip}    |    Línea: {linea}"  # Construye el encabezado de una red válida.
            elif primer_token.tipo == "IP":
                direccion = next((token.valor for token in grupo if token.tipo == "IP_ADDRESS"), "No identificada")  # Intenta recuperar la dirección aun con errores posteriores.
                nombre = self._buscar_nombre_en_tokens(grupo)  # Intenta recuperar también NAME.
                identificador = nombre or direccion  # Construye el mejor identificador disponible.
                titulo = f"Red: {identificador}    |    IP base: {direccion}    |    Línea: {linea}"  # Construye un encabezado parcial para una instrucción con problemas.
            else:
                titulo = f"Tokens sin red asociada    |    Línea: {linea}"  # Identifica contenido anterior a una instrucción IP válida.

            grupos.append((titulo, grupo))  # Agrega la agrupación terminada.

        return grupos  # Devuelve todas las instrucciones agrupadas.

    def _buscar_nombre_en_tokens(self, tokens: list[Token]) -> str | None:
        for indice, token in enumerate(tokens[:-1]):
            siguiente = tokens[indice + 1]  # Obtiene el token inmediatamente posterior.

            if token.tipo == "NAME" and siguiente.tipo == "IDENTIFIER":
                return siguiente.valor  # Recupera el nombre cuando la pareja fue tokenizada correctamente.

        return None  # Indica que la instrucción no contiene un nombre recuperable.

    def _mostrar_reservadas(self, resultado: ResultadoCompilacion) -> None:
        reservadas = ["IP", "MASK", "HOSTS", "NAME"]  # Define las palabras reservadas del lenguaje actual.
        contador = Counter(token.tipo for token in resultado.resultado_lexico.tokens if token.tipo in reservadas)  # Cuenta sus apariciones.
        self.tabla_reservadas.clearSpans()  # Elimina cualquier combinación previa.
        self.tabla_reservadas.setRowCount(len(reservadas))  # Reserva una fila para cada palabra.

        for fila, palabra in enumerate(reservadas):
            self.tabla_reservadas.setItem(fila, 0, self._crear_item_centrado(palabra))  # Coloca la palabra.
            self.tabla_reservadas.setItem(fila, 1, self._crear_item_centrado(str(contador.get(palabra, 0))))  # Coloca su cantidad.

    def _mostrar_vlsm(self, resultado: ResultadoCompilacion) -> None:
        self.tabla_vlsm.clearSpans()  # Elimina agrupaciones de la compilación anterior.
        self.tabla_vlsm.setRowCount(0)  # Vacía todos los resultados.

        grupo_anterior: tuple[str, str] | None = None  # Conserva la red original de la última subred mostrada.

        for subred in resultado.subredes_vlsm:
            grupo_actual = (subred.nombre_red, subred.ip_base)  # Identifica la red de origen.

            if grupo_actual != grupo_anterior:
                titulo_grupo = f"Red: {subred.nombre_red}    |    IP base: {subred.ip_base}"  # Crea el encabezado visual.
                self._insertar_fila_grupo(self.tabla_vlsm, titulo_grupo)  # Separa la nueva red del grupo anterior.
                grupo_anterior = grupo_actual  # Recuerda qué red se está mostrando actualmente.

            fila = self.tabla_vlsm.rowCount()  # Obtiene la siguiente posición libre.
            self.tabla_vlsm.insertRow(fila)  # Reserva una fila para la subred.

            valores = [
                subred.nombre_red,
                str(subred.hosts_solicitados),
                str(subred.hosts_disponibles),
                subred.direccion_de_red,
                subred.nueva_mascara,
                subred.mascara_decimal,
                subred.primera_ip_utilizable,
                subred.ultima_ip_utilizable,
                subred.direccion_de_broadcast,
            ]  # Prepara todos los campos VLSM visibles.

            for columna, valor in enumerate(valores):
                self.tabla_vlsm.setItem(fila, columna, self._crear_item_centrado(valor))  # Inserta cada valor centrado.

    def _copiar_analisis(self) -> None:
        texto = self.texto_analisis.toPlainText()  # Obtiene exactamente el reporte mostrado.

        if not texto:
            return  # Evita modificar el portapapeles cuando no existe información.

        QApplication.clipboard().setText(texto)  # Envía el análisis al portapapeles del sistema.

    def _copiar_diagnosticos(self) -> None:
        if self.resultado_actual is None or not self.resultado_actual.diagnosticos:
            return  # Evita copiar cuando no existe una compilación vigente con diagnósticos.

        lineas = []  # Acumula la representación textual estructurada de los diagnósticos.

        for indice, diagnostico in enumerate(self.resultado_actual.diagnosticos, start=1):
            ubicacion = self._formatear_ubicacion(diagnostico.linea, diagnostico.columna)  # Construye una ubicación legible.
            lineas.append(f"{indice}. [{diagnostico.codigo}] {diagnostico.categoria} - {diagnostico.severidad}")  # Identifica el diagnóstico.
            lineas.append(f"   Ubicación: {ubicacion}")  # Registra su posición de origen.
            lineas.append(f"   Mensaje: {diagnostico.mensaje}")  # Incluye el mensaje oficial.

            if diagnostico.fragmento:
                lineas.append(f"   Fragmento: {diagnostico.fragmento}")  # Incluye el texto problemático cuando está disponible.

            if diagnostico.solucion:
                lineas.append(f"   Solución: {diagnostico.solucion}")  # Incluye la recomendación registrada.

            lineas.append("")  # Separa visualmente cada diagnóstico.

        QApplication.clipboard().setText("\n".join(lineas).rstrip())  # Copia todo el registro eliminando el salto sobrante final.

    def _formatear_ubicacion(self, linea: int | None, columna: int | None) -> str:
        if linea is None:
            return "Sin ubicación específica"  # Explica que el diagnóstico afecta globalmente la entrada.

        if columna is None:
            return f"Línea {linea}"  # Muestra únicamente la línea cuando no existe posición de columna.

        return f"Línea {linea}, columna {columna}"  # Devuelve la ubicación completa cuando ambos datos están disponibles.

    def _exportar_excel(self) -> None:
        if self.resultado_actual is None or not self.resultado_actual.subredes_vlsm:
            self._mostrar_mensaje("Exportar Excel", "No hay subredes VLSM disponibles para exportar.", "Advertencia.png")  # Informa que todavía no existe información exportable.
            return

        ruta, _filtro = QFileDialog.getSaveFileName(
            self,
            "Exportar tabla VLSM",
            "TecNetFinder_VLSM.xlsx",
            "Libro de Excel (*.xlsx)",
        )  # Solicita la ubicación del libro mediante el diálogo nativo.

        if not ruta:
            return  # Finaliza cuando el usuario cancela el diálogo.

        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"  # Conserva siempre la extensión correspondiente.

        try:
            ruta_guardada = exportar_vlsm_excel(self.resultado_actual, ruta)  # Delega la escritura al módulo de exportación.
        except Exception as error:
            self._mostrar_mensaje("Error al exportar", f"No se pudo guardar el archivo de Excel.\n\n{error}", "Error.png")  # Informa cualquier error de escritura.
            return

        self._mostrar_mensaje("Exportación completada", f"La tabla VLSM se guardó correctamente en:\n{ruta_guardada}", "Correcto.png")  # Confirma la ubicación final.

    def _exportar_reporte(self) -> None:
        if self.resultado_actual is None:
            self._mostrar_mensaje("Exportar reporte", "Primero ejecuta una compilación para generar el reporte.", "Advertencia.png")  # Informa que no existe una compilación vigente.
            return

        ruta, _filtro = QFileDialog.getSaveFileName(
            self,
            "Exportar reporte de análisis",
            "TecNetFinder_Reporte.txt",
            "Archivo de texto (*.txt)",
        )  # Solicita la ubicación del reporte mediante el diálogo nativo.

        if not ruta:
            return  # Finaliza cuando el usuario cancela el diálogo.

        if not ruta.lower().endswith(".txt"):
            ruta += ".txt"  # Conserva siempre la extensión textual esperada.

        codigo_fuente = self.codigo_fuente_resultado  # Recupera exactamente la entrada asociada con los resultados.

        try:
            ruta_guardada = exportar_reporte_txt(codigo_fuente, self.resultado_actual, ruta)  # Delega la construcción del reporte.
        except Exception as error:
            self._mostrar_mensaje("Error al exportar", f"No se pudo guardar el reporte TXT.\n\n{error}", "Error.png")  # Informa cualquier error de escritura.
            return

        self._mostrar_mensaje("Exportación completada", f"El reporte se guardó correctamente en:\n{ruta_guardada}", "Correcto.png")  # Confirma la ubicación final.

    def _mostrar_mensaje(self, titulo: str, texto: str, nombre_icono: str) -> None:
        mensaje = QMessageBox(self)  # Crea un cuadro modal asociado con TecNet Finder.
        mensaje.setWindowTitle(titulo)  # Define el título del cuadro.
        mensaje.setText(texto)  # Coloca el mensaje principal.
        mensaje.setStandardButtons(QMessageBox.StandardButton.Ok)  # Utiliza únicamente una acción convencional de cierre.

        ruta_icono = ruta_icono_comun(nombre_icono)  # Recupera el icono semántico compartido por todos los temas.

        if ruta_icono.exists():
            pixmap = QPixmap(str(ruta_icono))  # Carga el PNG original.

            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    44,
                    44,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )  # Ajusta suavemente el recurso.
                mensaje.setIconPixmap(pixmap)  # Sustituye el icono estándar de Qt.

        mensaje.exec()  # Muestra el cuadro hasta que el usuario lo cierre.

    def _invalidar_resultado_exportable(self) -> None:
        if self.resultado_actual is None:
            return  # Evita trabajo adicional cuando no existe una compilación vigente.

        self.resultado_actual = None  # Descarta la compilación que dejó de corresponder con la entrada.
        self.codigo_fuente_resultado = ""  # Descarta también su copia del código fuente.
        self.boton_exportar_excel.setEnabled(False)  # Impide exportar resultados obsoletos.
        self.boton_exportar_reporte.setEnabled(False)  # Impide generar reportes obsoletos.
        self.boton_copiar_analisis.setEnabled(False)  # Impide copiar como vigente un análisis anterior.
        self.boton_copiar_diagnosticos.setEnabled(False)  # Impide copiar como vigentes diagnósticos anteriores.

        self.advertencias_compactas_actuales.clear()  # Elimina la relación entre filas compactas y diagnósticos anteriores.
        self.tabla_advertencias_vlsm.setRowCount(0)  # Vacía la representación resumida anterior.
        self.contador_advertencias_vlsm.setText("0")  # Recupera el contador inicial.
        self.panel_advertencias_vlsm.hide()  # Devuelve toda la superficie visual a la tabla VLSM.

        self._establecer_visibilidad_boton_flotante(
            self.texto_analisis,
            False,
        )  # Oculta la acción de análisis cuando deja de existir un resultado vigente.

        if self.superficie_diagnosticos is not None:
            self._establecer_visibilidad_boton_flotante(
                self.superficie_diagnosticos,
                False,
            )  # Oculta la acción de diagnósticos cuando deja de existir un resultado vigente.

    def limpiar(self) -> None:
        self.resultado_actual = None  # Descarta la compilación anterior.
        self.codigo_fuente_resultado = ""  # Descarta el código relacionado con esa compilación.
        self.boton_exportar_excel.setEnabled(False)  # Desactiva la exportación VLSM.
        self.boton_exportar_reporte.setEnabled(False)  # Desactiva el reporte textual.
        self.boton_copiar_analisis.setEnabled(False)  # Desactiva el copiado del análisis.
        self.boton_copiar_diagnosticos.setEnabled(False)  # Desactiva el copiado de diagnósticos.

        self._establecer_visibilidad_boton_flotante(
            self.texto_analisis,
            False,
        )  # Oculta por completo Copiar análisis.

        if self.superficie_diagnosticos is not None:
            self._establecer_visibilidad_boton_flotante(
                self.superficie_diagnosticos,
                False,
            )  # Oculta por completo Copiar diagnósticos.

        self.texto_analisis.clear()  # Elimina el reporte técnico anterior.

        self.tabla_vlsm.clearSpans()  # Elimina encabezados VLSM combinados.
        self.tabla_vlsm.setRowCount(0)  # Elimina todas las subredes.

        self.advertencias_compactas_actuales.clear()  # Elimina cualquier advertencia relacionada con la compilación anterior.
        self.tabla_advertencias_vlsm.setRowCount(0)  # Vacía la tabla compacta inferior.
        self.contador_advertencias_vlsm.setText("0")  # Recupera el contador inicial.
        self.panel_advertencias_vlsm.hide()  # Devuelve toda la altura disponible a la Tabla VLSM.

        self.tabla_tokens.clearSpans()  # Elimina agrupaciones de tokens.
        self.tabla_tokens.setRowCount(0)  # Elimina todos los tokens.

        self.tabla_reservadas.clearSpans()  # Recupera una estructura convencional.
        self.tabla_reservadas.setRowCount(0)  # Elimina el conteo anterior.

        self.texto_producciones.clear()  # Elimina las producciones anteriores.
        self.texto_derivacion.clear()  # Elimina la derivación anterior.
        self.visor_arbol.limpiar()  # Elimina los árboles anteriores.

        for etiqueta in self.tarjetas_resumen.values():
            etiqueta.setText("0")  # Devuelve todas las métricas del resumen a cero.

        self.estado_resumen.setObjectName("EstadoNeutral")  # Recupera el estilo previo a la compilación.
        self.estado_resumen.setText("Sin análisis ejecutado.")  # Recupera el mensaje inicial.
        self.estado_resumen.style().unpolish(self.estado_resumen)  # Retira temporalmente el estilo anterior.
        self.estado_resumen.style().polish(self.estado_resumen)  # Aplica nuevamente el estilo neutral.

        self.setCurrentWidget(self.tab_entrada_salida)  # Regresa a la sección inicial.
        self.pestanas_salida.setCurrentWidget(self.tab_resumen)  # Muestra nuevamente el resumen vacío.