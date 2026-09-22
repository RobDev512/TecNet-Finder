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
# La ventana conserva una barra de título personalizada, pero
# restaura en Windows las capacidades nativas necesarias para
# Snap, maximización, minimización y composición del escritorio.
#
# El selector de ventana permite utilizar Media pantalla a la
# izquierda o derecha, una ventana fija libremente desplazable
# y el modo maximizado. Pantalla completa continúa disponible
# mediante el botón correspondiente y F11.
# ============================================================

import ctypes  # Permite utilizar las funciones Win32 necesarias para Snap y entrada de teclado.
from ctypes import wintypes  # Proporciona tipos compatibles con las estructuras y funciones nativas de Windows.
import sys  # Permite limitar las operaciones Win32 exclusivamente al sistema correspondiente.
from pathlib import Path  # Permite localizar los recursos del proyecto sin utilizar rutas absolutas.

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QTimer, Qt  # Proporciona eventos, animaciones, temporización y estados de ventana.
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut  # Proporciona iconos, imágenes y atajos de teclado.
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget  # Proporciona los componentes principales de la interfaz.

from Interfaz.apariencia.recursos_tema import ruta_marca  # Centraliza el acceso al logotipo oficial y demás recursos de identidad visual.
from Interfaz.editor.editor_codigo import EditorCodigo  # Proporciona el editor especializado del lenguaje.
from Interfaz.editor.resaltador_sintaxis import ResaltadorSintaxis  # Proporciona únicamente el coloreado visual del código.
from Interfaz.resultados.panel_diagnosticos import PanelDiagnosticos  # Proporciona la vista estructurada de errores y advertencias.
from Interfaz.resultados.panel_resultados import PanelResultados  # Proporciona las pestañas y tablas donde se presentan los resultados.
from Interfaz.ventanas.barra_titulo import BarraTitulo  # Proporciona la barra personalizada utilizada por la ventana principal.
from Motor.compilacion.flujo_compilacion import FlujoCompilacion  # Coordina las fases formales actualmente disponibles.


GWL_STYLE = -16  # Identifica el conjunto de estilos principales asociado con una ventana Win32.
WS_SYSMENU = 0x00080000  # Recupera capacidades estándar relacionadas con la administración del sistema.
WS_THICKFRAME = 0x00040000  # Permite redimensionamiento y participación correcta dentro de Snap.
WS_MINIMIZEBOX = 0x00020000  # Informa a Windows que la ventana admite minimización.
WS_MAXIMIZEBOX = 0x00010000  # Informa que también admite maximización y layouts de ajuste.

SWP_NOSIZE = 0x0001  # Impide modificar el tamaño mientras solamente se actualiza el marco nativo.
SWP_NOMOVE = 0x0002  # Impide modificar la posición durante esa actualización.
SWP_NOZORDER = 0x0004  # Conserva el orden actual de la ventana respecto a las demás.
SWP_NOACTIVATE = 0x0010  # Evita solicitar foco exclusivamente por actualizar estilos.
SWP_FRAMECHANGED = 0x0020  # Solicita a Windows recalcular el marco después de modificar sus capacidades.

VK_LWIN = 0x5B  # Representa la tecla Windows izquierda utilizada para solicitar Snap.
VK_LEFT = 0x25  # Representa la flecha izquierda.
VK_RIGHT = 0x27  # Representa la flecha derecha.
KEYEVENTF_KEYUP = 0x0002  # Identifica la liberación de una tecla dentro de SendInput.
INPUT_KEYBOARD = 1  # Identifica la estructura enviada como una entrada de teclado.
DWMWA_WINDOW_CORNER_PREFERENCE = 33  # Permite solicitar esquinas redondeadas a DWM en Windows 11.
DWMWCP_ROUND = 2  # Solicita el redondeado estándar del sistema.

ANCHO_MAXIMO_QT = 16777215  # Representa el máximo convencional de Qt cuando no debe existir una restricción superior.
ANCHO_MODO_VENTANA = 1280  # Define el ancho preferido del nuevo modo de ventana fija.
ALTO_MODO_VENTANA = 760  # Define la altura preferida del nuevo modo de ventana fija.
MARGEN_MODO_VENTANA = 32  # Reserva un pequeño espacio alrededor de la ventana cuando el monitor lo permite.


class EntradaTecladoWindows(ctypes.Structure):  # Representa un evento individual de teclado compatible con SendInput.
    _fields_ = [
        ("wVk", wintypes.WORD),  # Conserva el código virtual de la tecla.
        ("wScan", wintypes.WORD),  # Reserva un código de escaneo cuando fuera necesario.
        ("dwFlags", wintypes.DWORD),  # Conserva banderas como KEYEVENTF_KEYUP.
        ("time", wintypes.DWORD),  # Permite que Windows gestione automáticamente la marca temporal.
        ("dwExtraInfo", wintypes.WPARAM),  # Reserva información adicional asociada con la entrada.
    ]


class UnionEntradaWindows(ctypes.Union):  # Representa la sección variable de una estructura INPUT.
    _fields_ = [("ki", EntradaTecladoWindows)]  # Utiliza exclusivamente la variante correspondiente con teclado.


class EntradaWindows(ctypes.Structure):  # Representa una entrada completa compatible con SendInput.
    _anonymous_ = ("contenido",)  # Permite acceder directamente mediante entrada.ki.
    _fields_ = [
        ("tipo", wintypes.DWORD),  # Identifica qué clase de entrada representa la estructura.
        ("contenido", UnionEntradaWindows),  # Conserva los datos específicos del teclado.
    ]


class VentanaPrincipal(QMainWindow):  # Construye TecNet Finder y administra sus diferentes estados de ventana.
    def __init__(self):  # Inicializa componentes, estado interno y comportamiento principal.
        super().__init__()  # Inicializa la implementación base proporcionada por QMainWindow.
        self.flujo = FlujoCompilacion()  # Crea el coordinador encargado de ejecutar las fases formales.
        self.ultimo_resultado = None  # Conserva posteriormente la compilación más reciente.

        self.en_pantalla_completa = False  # Registra si actualmente se utiliza fullscreen.
        self.en_media_pantalla = False  # Registra si actualmente se utiliza una de las dos mitades.
        self.en_modo_ventana = False  # Registra si se utiliza el tamaño fijo libremente desplazable.
        self.lado_media_pantalla = "izquierda"  # Conserva la última mitad seleccionada.
        self.modo_antes_pantalla_completa = "maximizado"  # Recuerda qué modo debe recuperarse después de abandonar fullscreen.
        self.geometria_modo_ventana = None  # Conserva posición y tamaño al entrar temporalmente a pantalla completa.
        self.editor_ampliado = False  # Registra si el editor ocupa actualmente todo el espacio útil de TecNet Finder.

        self.transicion_ventana_activa = False  # Evita ejecutar varias transiciones simultáneamente.
        self.animacion_opacidad = None  # Conserva una referencia para impedir que Python destruya una animación todavía activa.
        self.cierre_autorizado = False  # Distingue la primera solicitud animada del cierre definitivo.
        self.integracion_snap_configurada = False  # Registra si las capacidades Win32 necesarias ya fueron aplicadas.
        self.conexion_cambio_pantalla_configurada = False  # Evita conectar varias veces screenChanged.

        self.setWindowTitle("TecNet Finder")  # Mantiene el nombre visible en Windows y barra de tareas.
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)  # Mantiene nuestra barra personalizada sin perder una ventana principal convencional.
        self.setMinimumHeight(560)  # Evita reducir la aplicación hasta una altura poco funcional.

        self._cargar_icono()  # Carga el recurso oficial de la aplicación.
        self._construir_interfaz()  # Construye todos los componentes visuales.
        self._configurar_atajos()  # Activa F11 y Escape para pantalla completa.

    def _ruta_recurso(self, nombre_archivo: str) -> Path:
        return ruta_marca(nombre_archivo)  # Recupera los recursos de identidad visual desde la carpeta Marca centralizada.

    def _cargar_icono(self) -> None:  # Carga el ICO oficial cuando está disponible.
        ruta_icono = self._ruta_recurso("LogoTNF.ico")  # Obtiene la ubicación del recurso principal.

        if ruta_icono.exists():  # Comprueba que el archivo exista.
            self.setWindowIcon(QIcon(str(ruta_icono)))  # Lo utiliza como icono general de la ventana.

    def _construir_interfaz(self) -> None:  # Construye barra, encabezado, editor, diagnósticos y resultados.
        central = QWidget()  # Crea el widget raíz que ocupará toda la ventana.
        central.setObjectName("VentanaCentral")  # Permite aplicar el fondo general desde estilos.py.
        self.setCentralWidget(central)  # Asigna el contenedor como contenido central.

        diseno_general = QVBoxLayout(central)  # Organiza verticalmente barra y contenido.
        diseno_general.setContentsMargins(0, 0, 0, 0)  # Permite que la barra llegue exactamente hasta los bordes.
        diseno_general.setSpacing(0)  # Evita separación entre barra y zona principal.

        self.barra_titulo = BarraTitulo(self, self._ruta_recurso("LogoTNF.ico"), mostrar_media_pantalla=True)  # Construye la barra habilitando el selector de modos de ventana.
        diseno_general.addWidget(self.barra_titulo)  # Mantiene la barra permanentemente en la zona superior.

        contenido = QWidget()  # Crea el contenedor del área de trabajo.
        contenido.setObjectName("ContenidoPrincipal")  # Permite diferenciar su apariencia respecto con la barra.
        self.diseno_contenido = QVBoxLayout(contenido)  # Organiza encabezado, estado y pestañas y permite ajustar sus márgenes en modo ampliado.
        self.diseno_contenido.setContentsMargins(14, 10, 14, 14)  # Conserva el espacio visual utilizado por la interfaz.
        self.diseno_contenido.setSpacing(9)  # Mantiene una separación uniforme entre secciones.

        self._construir_encabezado(self.diseno_contenido)  # Agrega logotipo, nombre y descripción.

        self.etiqueta_estado = QLabel("Sin análisis ejecutado.")  # Crea la barra informativa situada antes de los resultados.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Aplica inicialmente la apariencia neutral.
        self.diseno_contenido.addWidget(self.etiqueta_estado)  # Coloca el estado encima de las pestañas.

        self.editor_codigo = EditorCodigo()  # Crea el editor especializado.
        self.resaltador_sintaxis = ResaltadorSintaxis(self.editor_codigo.document())  # Vincula el resaltador visual con el documento del editor.
        self.panel_diagnosticos = PanelDiagnosticos()  # Crea la tabla estructurada de diagnósticos.
        self.panel_resultados = PanelResultados(editor_codigo=self.editor_codigo, panel_diagnosticos=self.panel_diagnosticos, accion_analizar=self._analizar_codigo, accion_limpiar=self._limpiar_todo)  # Construye el área completa de resultados.

        self.diseno_contenido.addWidget(self.panel_resultados, 1)  # Permite que las pestañas utilicen todo el espacio restante.
        diseno_general.addWidget(contenido, 1)  # Coloca la zona principal debajo de la barra.

        self.panel_diagnosticos.diagnostico_activado.connect(self._ir_a_diagnostico)  # Permite navegar desde una fila detectada hasta el fragmento correspondiente.
        self.editor_codigo.ejemplos_insertados.connect(self._limpiar_resultados_conservando_entrada)  # Descarta resultados obsoletos después de insertar ejemplos.
        self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Inicializa el selector sin ninguna mitad activa.
        self.barra_titulo.actualizar_estado_modo_ventana(False)  # Inicializa también el nuevo modo como inactivo.
        self._configurar_boton_ampliar_editor()  # Sustituye la acción redundante de Pegar por un modo de edición ampliado.

    def _construir_encabezado(self, diseno_principal: QVBoxLayout) -> None:  # Construye el logotipo y textos superiores.
        encabezado = QHBoxLayout()  # Organiza horizontalmente imagen y títulos.
        encabezado.setSpacing(12)  # Mantiene una separación cómoda.
        ruta_logo = self._ruta_recurso("LogoTNF.png")  # Obtiene la imagen de mayor resolución.
        self.etiqueta_logo_principal = None  # Mantiene una referencia segura incluso cuando el recurso no existe.

        if ruta_logo.exists():  # Comprueba que el PNG esté disponible.
            self.etiqueta_logo_principal = QLabel()  # Crea un contenedor persistente para poder ocultarlo durante el modo de editor ampliado.
            imagen = QPixmap(str(ruta_logo)).scaled(58, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Reduce el logotipo conservando proporción y suavizado.
            self.etiqueta_logo_principal.setPixmap(imagen)  # Coloca la imagen procesada.
            encabezado.addWidget(self.etiqueta_logo_principal)  # Añade el logotipo al extremo izquierdo.

        caja_titulos = QVBoxLayout()  # Crea una columna para nombre y descripción.
        self.titulo_principal = QLabel("TecNet Finder")  # Presenta el nombre principal y permite ocultarlo temporalmente.
        self.titulo_principal.setObjectName("TituloPrincipal")  # Utiliza el estilo reservado para el título grande.
        self.subtitulo_principal = QLabel("Compilador para análisis de instrucciones VLSM")  # Presenta una descripción breve del proyecto.
        self.subtitulo_principal.setObjectName("SubtituloPrincipal")  # Utiliza el estilo secundario.

        caja_titulos.addWidget(self.titulo_principal)  # Coloca primero el nombre.
        caja_titulos.addWidget(self.subtitulo_principal)  # Coloca la descripción debajo.
        encabezado.addLayout(caja_titulos)  # Agrega ambos textos junto al logotipo.
        encabezado.addStretch()  # Mantiene todo el conjunto alineado hacia la izquierda.
        diseno_principal.addLayout(encabezado)  # Inserta el encabezado dentro del contenido.

    def _configurar_boton_ampliar_editor(self) -> None:  # Reutiliza el antiguo botón Pegar como control para ampliar y restaurar el editor.
        boton = self.editor_codigo.boton_pegar  # Conserva el atributo histórico para no romper Configuración ni el gestor de temas.
        try:
            boton.clicked.disconnect()  # Retira la acción de pegado porque el menú contextual ya cubre esa necesidad.
        except (RuntimeError, TypeError):
            pass  # Mantiene el inicio seguro aunque Qt no encuentre una conexión previa.

        boton.setToolTip("Ampliar editor")  # Explica la nueva función disponible.
        boton.setAccessibleName("Ampliar editor")  # Actualiza también la descripción accesible.
        boton.setProperty("recurso_tema", "Pantalla_completa.png")  # Declara el icono de ampliación para el tema activo.
        boton.clicked.connect(self.alternar_editor_ampliado)  # Permite entrar y salir del modo con el mismo control.

    def alternar_editor_ampliado(self) -> None:  # Alterna entre la distribución completa de TecNet Finder y un editor de enfoque.
        self._establecer_editor_ampliado(not self.editor_ampliado)  # Invierte exactamente el estado actual.

    def _establecer_editor_ampliado(self, ampliar: bool) -> None:  # Hace que el editor ocupe prácticamente todo el espacio útil de la aplicación.
        ampliar = bool(ampliar)  # Normaliza el valor recibido.
        if ampliar == self.editor_ampliado:
            return  # Evita repetir cambios de distribución innecesarios.

        self.editor_ampliado = ampliar  # Conserva inmediatamente el nuevo estado.
        panel = self.panel_resultados  # Utiliza un alias corto para los elementos que serán ocultados.
        panel.setCurrentWidget(panel.tab_entrada_salida)  # Garantiza que el editor pertenezca a la pestaña visible antes de ocultar la navegación.

        if self.etiqueta_logo_principal is not None:
            self.etiqueta_logo_principal.setVisible(not ampliar)  # Oculta únicamente el logotipo grande, no el de la barra de título.

        self.titulo_principal.setVisible(not ampliar)  # Libera el espacio ocupado por el nombre principal.
        self.subtitulo_principal.setVisible(not ampliar)  # Libera también el espacio ocupado por la descripción.
        self.etiqueta_estado.setVisible(not ampliar)  # Oculta temporalmente el resumen general mientras se escribe.
        panel.tabBar().setVisible(not ampliar)  # Oculta Entrada / Salida, Tablas, Sintaxis y Fases posteriores durante el enfoque.
        panel.pestanas_salida.setVisible(not ampliar)  # Oculta Resumen, Análisis, Tabla VLSM y Diagnósticos para entregar todo el alto al editor.

        for boton in (
            panel.boton_analizar,
            panel.boton_exportar_excel,
            panel.boton_exportar_reporte,
            panel.boton_limpiar,
        ):
            boton.setVisible(not ampliar)  # Oculta la fila de acciones; Compilar continúa disponible mediante Ctrl+Enter.

        panel_entrada = self.editor_codigo.parentWidget()  # Recupera el panel que contiene directamente título, editor y acciones.
        if panel_entrada is not None:
            for etiqueta in panel_entrada.findChildren(QLabel, "TituloSeccion"):
                etiqueta.setVisible(not ampliar)  # Oculta únicamente el título Entrada dentro de ese panel.

        diseno_entrada_salida = panel.tab_entrada_salida.layout()  # Recupera la distribución vertical de la primera pestaña.
        if diseno_entrada_salida is not None:
            diseno_entrada_salida.setContentsMargins(2, 2, 2, 2) if ampliar else diseno_entrada_salida.setContentsMargins(8, 8, 8, 8)  # Reduce el borde exterior únicamente durante el enfoque.
            diseno_entrada_salida.setSpacing(2 if ampliar else 8)  # Recupera la separación original al restaurar.

        self.diseno_contenido.setContentsMargins(4, 4, 4, 4) if ampliar else self.diseno_contenido.setContentsMargins(14, 10, 14, 14)  # Aprovecha casi todo el área disponible sin tocar la barra superior.
        self.diseno_contenido.setSpacing(2 if ampliar else 9)  # Reduce espacios vacíos durante la edición ampliada.

        boton_ampliar = self.editor_codigo.boton_pegar  # Recupera el mismo control flotante reutilizado.
        nombre_icono = "Salir_pantalla_completa.png" if ampliar else "Pantalla_completa.png"  # Representa visualmente la acción siguiente.
        ayuda = "Restaurar vista" if ampliar else "Ampliar editor"  # Explica qué ocurrirá al pulsar nuevamente.
        boton_ampliar.setProperty("recurso_tema", nombre_icono)  # Permite que el gestor seleccione la variante clara u oscura.
        boton_ampliar.setToolTip(ayuda)  # Actualiza el tooltip.
        boton_ampliar.setAccessibleName(ayuda)  # Mantiene sincronizada la accesibilidad.

        control = getattr(self, "control_configuracion", None)  # Recupera Configuración solamente cuando el inicio ya terminó.
        gestor = getattr(control, "gestor_tipografia", None) if control is not None else None  # Recupera el gestor de tema sin acoplar el editor directamente.

        if gestor is not None:
            gestor.aplicar()  # Reaplica los recursos declarados para mostrar inmediatamente el icono correcto del tema.

        QTimer.singleShot(0, self.editor_codigo._posicionar_botones_flotantes)  # Reubica Ampliar y Ejemplos después de cambiar la geometría.
        QTimer.singleShot(0, self.editor_codigo.setFocus)  # Devuelve el cursor al área de escritura después de completar la distribución.

    def _configurar_atajos(self) -> None:  # Configura los atajos utilizados para entrar y salir de fullscreen.
        self.atajo_pantalla_completa = QShortcut(QKeySequence("F11"), self)  # Crea el atajo convencional F11.
        self.atajo_pantalla_completa.activated.connect(self.alternar_pantalla_completa)  # Hace que F11 alterne el estado.
        self.atajo_salir_pantalla_completa = QShortcut(QKeySequence("Escape"), self)  # Crea Escape como salida adicional.
        self.atajo_salir_pantalla_completa.activated.connect(self.salir_pantalla_completa)  # Solo abandona fullscreen cuando se encuentra activo.

    def showEvent(self, evento) -> None:  # Completa la integración de ventana después de hacerse visible.
        super().showEvent(evento)  # Permite que Qt cree primero todos sus componentes.
        QTimer.singleShot(0, self._configurar_ventana_para_pantalla_actual)  # Espera a que exista HWND y geometría definitiva antes de configurar Snap.

    def resizeEvent(self, evento) -> None:  # Detecta cambios de tamaño realizados por Qt o Windows.
        super().resizeEvent(evento)  # Permite primero que Qt actualice sus componentes.

        if self.isVisible() and not self.en_pantalla_completa:  # Ignora cambios internos durante fullscreen o antes de mostrar la ventana.
            QTimer.singleShot(120, self._sincronizar_estado_media_pantalla)  # Espera a que Windows termine cualquier animación o cambio de geometría.

    def moveEvent(self, evento) -> None:  # Detecta desplazamientos que podrían pertenecer a Snap o al nuevo Modo ventana.
        super().moveEvent(evento)  # Conserva el comportamiento convencional de movimiento.

        if self.en_modo_ventana and not self.en_pantalla_completa:  # Comprueba si el movimiento pertenece a la ventana fija desplazable.
            self.geometria_modo_ventana = self.geometry()  # Conserva su última posición para recuperar correctamente fullscreen.

        if self.isVisible() and not self.en_pantalla_completa:  # Evalúa solamente una ventana visible y no fullscreen.
            QTimer.singleShot(120, self._sincronizar_estado_media_pantalla)  # Sincroniza el modo después de que Windows termine el movimiento.

    def _configurar_ventana_para_pantalla_actual(self) -> None:  # Prepara dimensiones, seguimiento de monitor e integración nativa.
        self._actualizar_limites_ancho_pantalla()  # Configura los límites según el modo actual.
        self._conectar_cambio_pantalla()  # Escucha futuros movimientos entre monitores.
        self._habilitar_integracion_snap_windows()  # Ajusta las capacidades Win32 requeridas por el modo actual.
        self._habilitar_esquinas_redondeadas_windows()  # Solicita también las esquinas curvas del sistema cuando sea posible.

    def _conectar_cambio_pantalla(self) -> None:  # Conecta una sola vez screenChanged sobre el manejador nativo.
        if self.conexion_cambio_pantalla_configurada:  # Comprueba si la conexión ya fue realizada anteriormente.
            return  # Evita duplicar la misma señal.

        manejador = self.windowHandle()  # Obtiene la representación nativa administrada por Qt.

        if manejador is None:  # Comprueba si Qt todavía no creó el manejador.
            return  # Espera una ejecución posterior de esta misma configuración.

        manejador.screenChanged.connect(self._al_cambiar_pantalla)  # Solicita recalcular límites al mover la ventana hacia otro monitor.
        self.conexion_cambio_pantalla_configurada = True  # Registra que la conexión quedó preparada.

    def _al_cambiar_pantalla(self, pantalla) -> None:  # Adapta TecNet Finder cuando cambia físicamente de monitor.
        self._actualizar_limites_ancho_pantalla(pantalla)  # Calcula inmediatamente dimensiones utilizando la nueva pantalla.

        if self.en_modo_ventana and not self.en_pantalla_completa:  # Comprueba si el nuevo monitor requiere reducir el tamaño fijo.
            QTimer.singleShot(0, lambda: self._asegurar_modo_ventana_visible(pantalla))  # Mantiene la ventana completamente visible sin recentrarla innecesariamente.

        QTimer.singleShot(0, self._habilitar_integracion_snap_windows)  # Refresca además las capacidades nativas.

    def _obtener_ancho_mitad_pantalla(self, pantalla=None) -> int:  # Calcula exactamente la mitad horizontal del monitor objetivo.
        pantalla_objetivo = pantalla or self.screen() or QApplication.primaryScreen()  # Prioriza el monitor recibido y utiliza el principal como respaldo.

        if pantalla_objetivo is None:  # Comprueba si Qt todavía no reconoce ninguna pantalla.
            return max(self.width(), 1)  # Conserva un ancho seguro basado en la ventana actual.

        area = pantalla_objetivo.availableGeometry()  # Obtiene el escritorio disponible excluyendo barra de tareas.
        return max(area.width() // 2, 1)  # Devuelve exactamente la mitad lógica disponible.

    def _obtener_tamano_modo_ventana(self, pantalla=None) -> tuple[int, int]:  # Calcula el tamaño fijo respetando monitores pequeños.
        pantalla_objetivo = pantalla or self.screen() or QApplication.primaryScreen()  # Utiliza primero el monitor donde se encuentra TecNet Finder.

        if pantalla_objetivo is None:  # Comprueba si Qt aún no puede proporcionar geometría.
            return ANCHO_MODO_VENTANA, ALTO_MODO_VENTANA  # Utiliza los valores preferidos como respaldo.

        area = pantalla_objetivo.availableGeometry()  # Obtiene solamente la zona utilizable del monitor.
        ancho_disponible = max(area.width() - MARGEN_MODO_VENTANA, 1)  # Reserva espacio lateral siempre que sea posible.
        alto_disponible = max(area.height() - MARGEN_MODO_VENTANA, 1)  # Reserva también un pequeño margen vertical.
        ancho_minimo = min(max(area.width() // 2, 1), area.width())  # Conserva aproximadamente media pantalla como mínimo funcional.
        alto_minimo = min(560, area.height())  # Conserva la altura mínima histórica mientras el monitor lo permita.

        ancho = min(ANCHO_MODO_VENTANA, ancho_disponible)  # Utiliza 1280 px cuando existe suficiente espacio.
        alto = min(ALTO_MODO_VENTANA, alto_disponible)  # Utiliza 760 px cuando existe suficiente altura.
        ancho = min(max(ancho, ancho_minimo), area.width())  # Garantiza legibilidad sin superar el monitor.
        alto = min(max(alto, alto_minimo), area.height())  # Garantiza también una altura funcional.

        return ancho, alto  # Entrega las dimensiones exactas que permanecerán bloqueadas.

    def _actualizar_limites_ancho_pantalla(self, pantalla=None) -> None:  # Aplica límites diferentes para Media pantalla, Modo ventana y los estados libres.
        pantalla_objetivo = pantalla or self.screen() or QApplication.primaryScreen()  # Recupera el monitor utilizado como referencia.

        self.setMinimumSize(0, 0)  # Libera primero cualquier restricción perteneciente al modo anterior.
        self.setMaximumSize(ANCHO_MAXIMO_QT, ANCHO_MAXIMO_QT)  # Elimina temporalmente máximos anteriores.

        if self.en_modo_ventana and not self.en_pantalla_completa:  # Comprueba si corresponde bloquear ambas dimensiones.
            ancho, alto = self._obtener_tamano_modo_ventana(pantalla_objetivo)  # Calcula un tamaño compatible con el monitor.
            self.setFixedSize(ancho, alto)  # Impide redimensionar el modo ventana tanto desde Qt como desde los bordes.
            return  # No aplica los límites convencionales mientras este modo esté activo.

        ancho_mitad = self._obtener_ancho_mitad_pantalla(pantalla_objetivo)  # Calcula una sola vez el 50 % correspondiente con el monitor.

        if self.en_media_pantalla and not self.en_pantalla_completa:  # Comprueba si debe conservarse exactamente el ancho dividido.
            self.setMinimumWidth(ancho_mitad)  # Impide reducir la ventana por debajo del 50 %.
            self.setMaximumWidth(ancho_mitad)  # Impide ampliarla por encima del 50 %.
        else:  # Atiende maximizado, normal o pantalla completa.
            self.setMinimumWidth(ancho_mitad)  # Conserva media pantalla como mínimo permitido.
            self.setMaximumWidth(ANCHO_MAXIMO_QT)  # Elimina cualquier restricción superior.

        if pantalla_objetivo is not None:  # Comprueba que exista información geométrica confiable.
            alto_minimo = min(560, pantalla_objetivo.availableGeometry().height())  # Mantiene una altura cómoda sin superar pantallas pequeñas.
            self.setMinimumHeight(alto_minimo)  # Aplica el límite vertical calculado.

    def _aplicar_geometria_modo_ventana(self, centrar: bool = True, geometria_preferida=None) -> None:  # Coloca la ventana fija dentro del monitor actual.
        pantalla = self.screen() or QApplication.primaryScreen()  # Utiliza el monitor actual y recurre al principal como respaldo.

        if pantalla is None:  # Comprueba que exista geometría de pantalla.
            ancho, alto = self._obtener_tamano_modo_ventana()  # Recupera el tamaño de respaldo.
            self.resize(ancho, alto)  # Aplica únicamente las dimensiones cuando no puede calcularse una posición.
            return  # Finaliza sin intentar centrar.

        area = pantalla.availableGeometry()  # Obtiene el espacio utilizable.
        ancho, alto = self._obtener_tamano_modo_ventana(pantalla)  # Calcula el tamaño fijo apropiado para este monitor.

        if not centrar and geometria_preferida is not None:  # Comprueba si debe recuperar una posición anterior.
            posicion_x = geometria_preferida.x()  # Parte de la posición horizontal almacenada.
            posicion_y = geometria_preferida.y()  # Parte de la posición vertical almacenada.
        else:  # Atiende la primera entrada al modo.
            posicion_x = area.left() + max(0, (area.width() - ancho) // 2)  # Centra horizontalmente.
            posicion_y = area.top() + max(0, (area.height() - alto) // 2)  # Centra verticalmente.

        maximo_x = area.right() - ancho + 1  # Calcula la última posición horizontal que mantiene visible la ventana completa.
        maximo_y = area.bottom() - alto + 1  # Calcula la última posición vertical válida.
        posicion_x = max(area.left(), min(posicion_x, maximo_x))  # Impide recuperar una posición fuera del monitor.
        posicion_y = max(area.top(), min(posicion_y, maximo_y))  # Impide también salir verticalmente.

        self.setGeometry(posicion_x, posicion_y, ancho, alto)  # Aplica posición y tamaño en una sola operación.
        self.geometria_modo_ventana = self.geometry()  # Conserva la geometría final ya ajustada.

    def _asegurar_modo_ventana_visible(self, pantalla=None) -> None:  # Reubica mínimamente la ventana cuando cambia de monitor.
        if not self.en_modo_ventana or self.en_pantalla_completa:  # Comprueba que la tarea siga perteneciendo al modo fijo.
            return  # Cancela una ejecución programada que ya quedó obsoleta.

        pantalla_objetivo = pantalla or self.screen() or QApplication.primaryScreen()  # Recupera el monitor actual.

        if pantalla_objetivo is None:  # Comprueba que Qt tenga geometría disponible.
            return  # Mantiene la posición actual cuando no puede validarse.

        area = pantalla_objetivo.availableGeometry()  # Obtiene el área útil del monitor.
        ancho, alto = self._obtener_tamano_modo_ventana(pantalla_objetivo)  # Recupera las dimensiones ya fijadas.
        geometria = self.geometry()  # Conserva la posición actual como primera opción.
        maximo_x = area.right() - ancho + 1  # Calcula el último origen horizontal válido.
        maximo_y = area.bottom() - alto + 1  # Calcula el último origen vertical válido.
        posicion_x = max(area.left(), min(geometria.x(), maximo_x))  # Corrige solamente si queda fuera del monitor.
        posicion_y = max(area.top(), min(geometria.y(), maximo_y))  # Corrige solamente si queda fuera verticalmente.

        self.setGeometry(posicion_x, posicion_y, ancho, alto)  # Mantiene la posición elegida por el usuario siempre que siga siendo válida.
        self.geometria_modo_ventana = self.geometry()  # Actualiza la geometría persistida temporalmente.

    def _habilitar_integracion_snap_windows(self) -> bool:  # Ajusta las capacidades Win32 según el modo actual.
        if sys.platform != "win32":  # Comprueba que se esté ejecutando realmente sobre Windows.
            return False  # Mantiene el programa funcional sin intentar utilizar APIs inexistentes.

        try:  # Protege la aplicación ante cualquier fallo en la integración nativa.
            identificador_ventana = int(self.winId())  # Recupera el HWND correspondiente con TecNet Finder.
            usuario32 = ctypes.windll.user32  # Obtiene la biblioteca de administración de ventanas.

            usuario32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]  # Declara los argumentos de la consulta de estilos.
            usuario32.GetWindowLongW.restype = ctypes.c_long  # Declara el tipo devuelto por Windows.
            usuario32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]  # Declara los argumentos utilizados para modificar estilos.
            usuario32.SetWindowLongW.restype = ctypes.c_long  # Declara también el tipo devuelto por la modificación.

            estilo_actual = usuario32.GetWindowLongW(identificador_ventana, GWL_STYLE)  # Recupera las capacidades actuales asignadas por Qt.
            estilo_actualizado = estilo_actual | WS_SYSMENU | WS_MINIMIZEBOX  # Conserva siempre las capacidades básicas de sistema y minimización.

            if self.en_modo_ventana and not self.en_pantalla_completa:  # Comprueba si el tamaño debe permanecer completamente fijo.
                estilo_actualizado &= ~(WS_THICKFRAME | WS_MAXIMIZEBOX)  # Retira redimensionamiento nativo y maximización directa desde el marco.
            else:  # Atiende Media pantalla, maximizado, normal y fullscreen.
                estilo_actualizado |= WS_THICKFRAME | WS_MAXIMIZEBOX  # Recupera todas las capacidades necesarias para Snap.

            if estilo_actualizado != estilo_actual:  # Comprueba si realmente hace falta modificar el HWND.
                usuario32.SetWindowLongW(identificador_ventana, GWL_STYLE, estilo_actualizado)  # Aplica las capacidades correspondientes con el modo.
                usuario32.SetWindowPos(identificador_ventana, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED)  # Solicita recalcular el marco sin cambiar geometría ni foco.

            self.integracion_snap_configurada = True  # Registra que la integración pudo aplicarse.
            return True  # Confirma al llamador que el marco nativo quedó sincronizado.
        except (AttributeError, OSError, TypeError, ValueError):  # Atiende fallos de Win32 sin cerrar la aplicación.
            self.integracion_snap_configurada = False  # Conserva un estado interno seguro.
            return False  # Permite continuar utilizando la lógica Qt.

    def _habilitar_esquinas_redondeadas_windows(self) -> bool:  # Solicita a Windows 11 que redondee las esquinas de la ventana principal.
        if sys.platform != "win32":  # Comprueba que la API requerida exista.
            return False  # En otros sistemas simplemente se omite la preferencia.

        try:  # Protege la aplicación ante equipos sin DWM o sistemas anteriores.
            identificador_ventana = int(self.winId())  # Recupera el HWND correspondiente con TecNet Finder.
            dwmapi = ctypes.windll.dwmapi  # Obtiene la biblioteca Desktop Window Manager.
            preferencia = ctypes.c_int(DWMWCP_ROUND)  # Solicita el redondeado estándar del sistema.
            resultado = dwmapi.DwmSetWindowAttribute(identificador_ventana, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(preferencia), ctypes.sizeof(preferencia))  # Aplica la preferencia sobre la ventana actual.
            return resultado == 0  # Confirma si Windows aceptó la solicitud.
        except (AttributeError, OSError, TypeError, ValueError):  # Atiende sistemas sin soporte o cualquier fallo nativo.
            return False  # Mantiene funcional la aplicación aunque el redondeado no pueda aplicarse.

    def _crear_entrada_teclado(self, tecla: int, liberar: bool = False) -> EntradaWindows:  # Construye un evento compatible con SendInput.
        banderas = KEYEVENTF_KEYUP if liberar else 0  # Decide entre pulsación y liberación.
        return EntradaWindows(tipo=INPUT_KEYBOARD, ki=EntradaTecladoWindows(wVk=tecla, wScan=0, dwFlags=banderas, time=0, dwExtraInfo=0))  # Devuelve la estructura completamente preparada.

    def _enviar_atajo_snap(self, lado: str) -> bool:  # Solicita Win+Izquierda o Win+Derecha mediante SendInput.
        if sys.platform != "win32":  # Comprueba que la API requerida exista.
            return False  # Obliga a utilizar el respaldo geométrico en otros sistemas.

        tecla_direccion = VK_RIGHT if lado == "derecha" else VK_LEFT  # Selecciona la flecha correspondiente con el lado solicitado.

        try:  # Protege el flujo ante errores de activación o SendInput.
            self._habilitar_integracion_snap_windows()  # Confirma nuevamente que el HWND admita Snap.
            identificador_ventana = int(self.winId())  # Obtiene la ventana que debe recibir el atajo.
            usuario32 = ctypes.windll.user32  # Obtiene las funciones de entrada y activación.

            usuario32.SetForegroundWindow(identificador_ventana)  # Solicita que TecNet Finder sea la ventana activa.
            self.raise_()  # Refuerza mediante Qt que permanezca encima.
            self.activateWindow()  # Solicita además el foco convencional.
            QApplication.processEvents()  # Procesa la activación antes de enviar las teclas.

            entradas = (EntradaWindows * 4)(
                self._crear_entrada_teclado(VK_LWIN),
                self._crear_entrada_teclado(tecla_direccion),
                self._crear_entrada_teclado(tecla_direccion, liberar=True),
                self._crear_entrada_teclado(VK_LWIN, liberar=True),
            )  # Construye la secuencia completa de pulsación y liberación.
            entradas_enviadas = usuario32.SendInput(len(entradas), ctypes.byref(entradas), ctypes.sizeof(EntradaWindows))  # Envía los cuatro eventos mediante la API moderna.
            return entradas_enviadas == len(entradas)  # Confirma que Windows haya aceptado toda la secuencia.
        except (AttributeError, OSError, TypeError, ValueError):  # Atiende cualquier fallo nativo.
            return False  # Permite recurrir al posicionamiento manual.

    def _animar_opacidad(self, inicio: float, fin: float, duracion: int, al_terminar=None) -> None:  # Ejecuta una transición reutilizable sobre la opacidad general.
        if self.animacion_opacidad is not None:  # Comprueba si otra animación todavía conserva una referencia.
            self.animacion_opacidad.stop()  # Detiene la anterior para evitar dos controles simultáneos.

        self.setWindowOpacity(inicio)  # Coloca inmediatamente la opacidad inicial.
        self.animacion_opacidad = QPropertyAnimation(self, b"windowOpacity", self)  # Crea una animación asociada con esta ventana.
        self.animacion_opacidad.setDuration(duracion)  # Define la duración solicitada.
        self.animacion_opacidad.setStartValue(inicio)  # Define el punto inicial.
        self.animacion_opacidad.setEndValue(fin)  # Define el valor final.
        self.animacion_opacidad.setEasingCurve(QEasingCurve.Type.InOutCubic)  # Utiliza aceleración y desaceleración progresivas.

        if al_terminar is not None:  # Comprueba si el llamador proporcionó una acción final.
            self.animacion_opacidad.finished.connect(al_terminar)  # La ejecuta únicamente después de finalizar la transición.

        self.animacion_opacidad.start()  # Inicia la animación configurada.

    def minimizar_animado(self) -> None:  # Atenúa brevemente TecNet Finder antes de enviarlo a la barra de tareas.
        if self.transicion_ventana_activa:  # Comprueba si ya existe otro cambio de ventana en curso.
            return  # Ignora clics adicionales hasta que termine.

        self.transicion_ventana_activa = True  # Bloquea temporalmente otras transiciones.

        def finalizar_minimizado() -> None:  # Completa la minimización después de terminar la animación.
            self.showMinimized()  # Envía finalmente la ventana a la barra de tareas.
            self.setWindowOpacity(1.0)  # Prepara la opacidad normal para su próxima restauración.
            self.transicion_ventana_activa = False  # Permite nuevamente utilizar los controles.

        self._animar_opacidad(1.0, 0.35, 130, finalizar_minimizado)  # Ejecuta la transición breve antes de minimizar.

    def preparar_modo_ventana_inicial(self, pantalla=None) -> None:  # Prepara Modo ventana durante el arranque sin ejecutar una animación innecesaria.
        self.en_pantalla_completa = False  # Garantiza que el inicio no herede fullscreen.
        self.en_media_pantalla = False  # Garantiza que Media pantalla siga siendo temporal.
        self.en_modo_ventana = True  # Registra correctamente el estado recuperable antes de mostrar la ventana.
        self.barra_titulo.permitir_arrastre = True  # Habilita el movimiento desde la primera aparición de la aplicación.

        pantalla_objetivo = pantalla or self.screen() or QApplication.primaryScreen()  # Utiliza el monitor proporcionado por principal.py cuando está disponible.
        self._actualizar_limites_ancho_pantalla(pantalla_objetivo)  # Fija ancho y alto desde el propio inicio.

        if pantalla_objetivo is not None:
            area = pantalla_objetivo.availableGeometry()  # Obtiene la zona disponible del monitor.
            ancho, alto = self._obtener_tamano_modo_ventana(pantalla_objetivo)  # Calcula las dimensiones compatibles.
            posicion_x = area.left() + max(0, (area.width() - ancho) // 2)  # Centra horizontalmente.
            posicion_y = area.top() + max(0, (area.height() - alto) // 2)  # Centra verticalmente.
            self.setGeometry(posicion_x, posicion_y, ancho, alto)  # Aplica tamaño y posición antes del primer fotograma.
            self.geometria_modo_ventana = self.geometry()  # Conserva la geometría inicial para futuras restauraciones.

        self.barra_titulo.actualizar_estado_pantalla_completa(False)  # Mantiene fullscreen desactivado.
        self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Mantiene las mitades desactivadas.
        self.barra_titulo.actualizar_estado_modo_ventana(True)  # Sincroniza el selector desde el primer inicio.

    def activar_modo_ventana(self) -> None:  # Cambia TecNet Finder a una ventana de tamaño fijo que puede desplazarse libremente.
        if self.en_modo_ventana and not self.en_pantalla_completa and not self.en_media_pantalla:  # Comprueba si ya se encuentra exactamente en este modo.
            return  # Evita repetir una transición innecesaria.

        if self.transicion_ventana_activa:  # Comprueba si otra transición todavía está activa.
            return  # Impide superponer animaciones y geometrías.

        self.transicion_ventana_activa = True  # Bloquea temporalmente los demás controles de ventana.

        def aplicar_estado() -> None:  # Aplica el nuevo modo después de atenuar brevemente la interfaz.
            self.en_pantalla_completa = False  # Abandona cualquier fullscreen anterior.
            self.en_media_pantalla = False  # Abandona cualquier mitad activa.
            self.en_modo_ventana = True  # Registra la nueva modalidad.

            self.showNormal()  # Convierte la ventana en una superficie convencional que puede moverse.
            self._actualizar_limites_ancho_pantalla()  # Bloquea ancho y alto al tamaño calculado.
            self._habilitar_integracion_snap_windows()  # Retira también el redimensionamiento desde el marco nativo.
            QApplication.processEvents()  # Permite a Qt completar showNormal antes de fijar la posición final.
            self._aplicar_geometria_modo_ventana(centrar=True)  # Centra la primera entrada al modo.

            self.barra_titulo.permitir_arrastre = True  # Habilita movimiento mediante la barra personalizada.
            self.barra_titulo.actualizar_estado_pantalla_completa(False)  # Mantiene sincronizado fullscreen.
            self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Desactiva las tarjetas de mitad.
            self.barra_titulo.actualizar_estado_modo_ventana(True)  # Marca el nuevo estado dentro del selector.

            self.setWindowOpacity(0.72)  # Prepara una aparición suave desde la nueva geometría.

            def finalizar_transicion() -> None:  # Libera la interfaz cuando termina la aparición.
                self.setWindowOpacity(1.0)  # Garantiza opacidad completa.
                self.transicion_ventana_activa = False  # Permite nuevas acciones.

            self._animar_opacidad(0.72, 1.0, 170, finalizar_transicion)  # Completa suavemente la entrada.

        self._animar_opacidad(1.0, 0.72, 95, aplicar_estado)  # Atenúa primero la ventana antes de cambiar su geometría.

    def alternar_media_pantalla(self) -> None:  # Alterna entre media pantalla y maximizado utilizando el último lado seleccionado.
        if self.en_media_pantalla:  # Comprueba si actualmente ya está activo el modo dividido.
            self._cambiar_media_pantalla(False)  # Recupera el modo maximizado.
        else:  # Atiende maximizado o Modo ventana.
            self._cambiar_media_pantalla(True, self.lado_media_pantalla)  # Utiliza el último lado conocido.

    def colocar_media_pantalla(self, lado: str) -> None:  # Coloca directamente TecNet Finder en izquierda o derecha.
        if lado not in ("izquierda", "derecha"):  # Comprueba que solamente se reciban posiciones válidas.
            return  # Ignora cualquier valor desconocido.

        self._cambiar_media_pantalla(True, lado)  # Ejecuta la transición común utilizando la mitad solicitada.

    def maximizar_ventana(self) -> None:  # Recupera el modo maximizado desde Media pantalla o Modo ventana.
        self._cambiar_media_pantalla(False)  # Reutiliza una única transición para abandonar los modos temporales.

    def _cambiar_media_pantalla(self, activar: bool, lado: str | None = None) -> None:  # Administra la transición entre maximizado y una mitad fija.
        lado_objetivo = lado if lado in ("izquierda", "derecha") else self.lado_media_pantalla  # Utiliza el lado recibido o conserva el anterior.

        if activar and self.en_media_pantalla and not self.en_pantalla_completa and not self.en_modo_ventana and lado_objetivo == self.lado_media_pantalla and self._geometria_corresponde_media_pantalla(lado_objetivo):  # Comprueba si ya se encuentra exactamente en el estado solicitado.
            return  # Evita repetir una transición innecesaria.

        if not activar and self.isMaximized() and not self.en_media_pantalla and not self.en_pantalla_completa and not self.en_modo_ventana:  # Comprueba si maximizado ya representa realmente el estado actual.
            return  # Evita solicitarlo nuevamente.

        if self.transicion_ventana_activa:  # Comprueba si otro cambio todavía continúa ejecutándose.
            return  # Impide superponer animaciones y geometrías.

        self.transicion_ventana_activa = True  # Bloquea temporalmente los demás controles.

        if activar:  # Comprueba si se está entrando al modo dividido.
            self.lado_media_pantalla = lado_objetivo  # Conserva inmediatamente la mitad elegida.

        def aplicar_estado() -> None:  # Aplica la geometría después de la primera atenuación.
            self.en_pantalla_completa = False  # Abandona fullscreen si la solicitud procede desde ese modo.
            self.en_modo_ventana = False  # Media pantalla y maximizado abandonan siempre el tamaño fijo desplazable.
            self.barra_titulo.permitir_arrastre = False  # Restringe el movimiento manual a Modo ventana.

            if activar:  # Atiende el ingreso a Media pantalla.
                self.en_media_pantalla = True  # Registra el nuevo modo.
                self.showNormal()  # Sale de maximizado o fullscreen antes de solicitar Snap.
                self._actualizar_limites_ancho_pantalla()  # Fija simultáneamente mínimo y máximo en 50 %.
                self._habilitar_integracion_snap_windows()  # Recupera capacidades nativas después del cambio.
                self.barra_titulo.actualizar_estado_pantalla_completa(False)  # Sincroniza visualmente fullscreen.
                self.barra_titulo.actualizar_estado_media_pantalla(True, self.lado_media_pantalla)  # Sincroniza el selector con el lado elegido.
                self.barra_titulo.actualizar_estado_modo_ventana(False)  # Desactiva explícitamente la nueva modalidad.
                QApplication.processEvents()  # Permite completar la restauración antes de solicitar Snap.
                QTimer.singleShot(80, self._activar_snap_media_pantalla)  # Solicita Snap después de que Windows reconozca una ventana normal.
            else:  # Atiende la salida de cualquier modo temporal hacia maximizado.
                self.en_media_pantalla = False  # Registra que deja de utilizarse una mitad.
                self._actualizar_limites_ancho_pantalla()  # Libera las dimensiones fijas.
                self._habilitar_integracion_snap_windows()  # Recupera redimensionamiento y maximización nativa.
                self.showMaximized()  # Recupera el tamaño principal.
                self.barra_titulo.actualizar_estado_pantalla_completa(False)  # Mantiene fullscreen preparado para una futura entrada.
                self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Informa que ninguna mitad está activa.
                self.barra_titulo.actualizar_estado_modo_ventana(False)  # Informa que Modo ventana tampoco está activo.

            self.setWindowOpacity(0.72)  # Prepara una aparición progresiva desde la nueva geometría.

            def finalizar_transicion() -> None:  # Libera el estado después de completar la aparición.
                self.setWindowOpacity(1.0)  # Garantiza que la ventana termine completamente visible.
                self.transicion_ventana_activa = False  # Permite nuevas acciones de ventana.

            self._animar_opacidad(0.72, 1.0, 170, finalizar_transicion)  # Hace aparecer progresivamente el nuevo estado.

        self._animar_opacidad(1.0, 0.72, 95, aplicar_estado)  # Atenúa ligeramente TecNet Finder antes de cambiar su geometría.

    def _activar_snap_media_pantalla(self) -> None:  # Solicita Snap nativo y utiliza geometría manual únicamente como respaldo.
        if not self.en_media_pantalla or self.en_pantalla_completa or self.en_modo_ventana:  # Comprueba que la solicitud todavía siga vigente.
            return  # Cancela tareas programadas pertenecientes a un estado anterior.

        self._actualizar_limites_ancho_pantalla()  # Confirma que el ancho continúe fijado al 50 %.
        snap_solicitado = self._enviar_atajo_snap(self.lado_media_pantalla)  # Envía Win+Izquierda o Win+Derecha.

        if snap_solicitado:  # Comprueba si Windows recibió correctamente la secuencia.
            QTimer.singleShot(450, self._verificar_snap_media_pantalla)  # Espera a que termine la animación nativa para comprobar la geometría.
        else:  # Atiende un equipo donde SendInput no pudo utilizarse.
            self._aplicar_geometria_media_pantalla()  # Utiliza inmediatamente el respaldo geométrico.

    def _verificar_snap_media_pantalla(self) -> None:  # Comprueba que Windows realmente haya aplicado la mitad solicitada.
        if not self.en_media_pantalla or self.en_pantalla_completa or self.en_modo_ventana:  # Comprueba que el usuario no haya cambiado nuevamente de modo.
            return  # Evita modificar una ventana cuyo estado ya cambió.

        self._actualizar_limites_ancho_pantalla()  # Refuerza el ancho fijo después de formarse el grupo Snap.

        if self._geometria_corresponde_media_pantalla(self.lado_media_pantalla):  # Comprueba si Windows consiguió la posición esperada.
            self.barra_titulo.actualizar_estado_media_pantalla(True, self.lado_media_pantalla)  # Mantiene sincronizado el selector.
            return  # Conserva la geometría administrada correctamente por Windows.

        self._aplicar_geometria_media_pantalla()  # Utiliza el respaldo solamente cuando Snap no produjo el resultado esperado.

    def _aplicar_geometria_media_pantalla(self) -> None:  # Coloca manualmente la ventana sobre exactamente la mitad del monitor.
        pantalla = self.screen() or QApplication.primaryScreen()  # Utiliza el monitor actual y recurre al principal como respaldo.

        if pantalla is None:  # Comprueba que Qt conozca al menos una pantalla.
            return  # Evita modificar la geometría sin información válida.

        area = pantalla.availableGeometry()  # Obtiene la región utilizable excluyendo la barra de tareas.
        ancho_objetivo = area.width() // 2  # Calcula exactamente el 50 % horizontal.

        if self.lado_media_pantalla == "derecha":  # Comprueba cuál de las dos posiciones fue elegida.
            posicion_x = area.left() + area.width() - ancho_objetivo  # Calcula el comienzo exacto de la mitad derecha.
        else:  # Atiende la mitad izquierda.
            posicion_x = area.left()  # Utiliza directamente el borde izquierdo.

        self._actualizar_limites_ancho_pantalla(pantalla)  # Fija primero el mismo ancho como mínimo y máximo.
        self.setGeometry(posicion_x, area.top(), ancho_objetivo, area.height())  # Ocupa exactamente la mitad elegida y toda la altura disponible.

    def _detectar_lado_media_pantalla(self) -> str | None:  # Deduce izquierda o derecha a partir de la geometría real administrada por Windows.
        pantalla = self.screen() or QApplication.primaryScreen()  # Obtiene el monitor donde se encuentra actualmente la ventana.

        if pantalla is None:  # Comprueba que exista información de pantalla.
            return None  # Indica que todavía no puede determinarse el estado.

        area = pantalla.availableGeometry()  # Obtiene el área disponible.
        geometria_actual = self.frameGeometry()  # Obtiene la geometría real de TecNet Finder.
        ancho_esperado = area.width() // 2  # Calcula el ancho correspondiente con una mitad.
        posicion_derecha = area.left() + area.width() - ancho_esperado  # Calcula dónde comienza la mitad derecha.
        tolerancia = 32  # Admite pequeñas diferencias de escalado, bordes invisibles y animaciones.

        ancho_correcto = abs(geometria_actual.width() - ancho_esperado) <= tolerancia  # Comprueba que la ventana mida aproximadamente el 50 %.
        altura_correcta = abs(geometria_actual.height() - area.height()) <= tolerancia  # Comprueba que ocupe aproximadamente toda la altura.

        if not ancho_correcto or not altura_correcta:  # Descarta geometrías que no representan Media pantalla.
            return None  # Informa que no se detectó ningún lado válido.

        if abs(geometria_actual.left() - area.left()) <= tolerancia:  # Comprueba si la ventana está alineada al borde izquierdo.
            return "izquierda"  # Identifica la primera mitad.

        if abs(geometria_actual.left() - posicion_derecha) <= tolerancia:  # Comprueba si está alineada al comienzo de la mitad derecha.
            return "derecha"  # Identifica la segunda mitad.

        return None  # Descarta ventanas de media anchura situadas en otra posición.

    def _geometria_corresponde_media_pantalla(self, lado: str | None = None) -> bool:  # Comprueba si la geometría real coincide con cualquiera o con una mitad específica.
        lado_detectado = self._detectar_lado_media_pantalla()  # Obtiene el lado deducido desde Windows.

        if lado is None:  # Comprueba si el llamador acepta cualquiera de las dos posiciones.
            return lado_detectado is not None  # Considera válida cualquier mitad reconocida.

        return lado_detectado == lado  # Exige coincidencia exacta cuando se solicitó una posición concreta.

    def _sincronizar_estado_media_pantalla(self) -> None:  # Sincroniza el estado interno con cambios realizados directamente mediante Windows.
        if self.en_pantalla_completa or self.isMinimized():  # Evita interpretar fullscreen o minimizado como una geometría convencional.
            return  # Finaliza sin modificar el estado.

        if self.en_modo_ventana:  # Da prioridad al tamaño fijo desplazable antes de intentar reconocer Snap.
            self._actualizar_limites_ancho_pantalla()  # Reafirma sus dimensiones si algún evento externo intentó alterarlas.
            self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Impide mostrar una mitad activa.
            self.barra_titulo.actualizar_estado_modo_ventana(True)  # Mantiene sincronizada la nueva modalidad.
            return  # Nunca interpreta su geometría como Media pantalla.

        if self.en_media_pantalla:  # Comprueba si el usuario seleccionó explícitamente este modo desde TecNet Finder.
            self._actualizar_limites_ancho_pantalla()  # Mantiene bloqueado el ancho en 50 %.

            if not self._geometria_corresponde_media_pantalla(self.lado_media_pantalla):  # Comprueba si una acción externa alteró la posición.
                QTimer.singleShot(0, self._aplicar_geometria_media_pantalla)  # Recupera inmediatamente la mitad solicitada.

            return  # Conserva el modo explícito.

        if self.isMaximized():  # Comprueba si Windows mantiene una maximización convencional.
            self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Mantiene el selector preparado pero sin lado activo.
            self.barra_titulo.actualizar_estado_modo_ventana(False)  # Mantiene desactivado Modo ventana.
            return  # No necesita ninguna sincronización adicional.

        lado_detectado = self._detectar_lado_media_pantalla()  # Intenta reconocer un Snap iniciado directamente mediante Windows.

        if lado_detectado is not None:  # Comprueba si la geometría corresponde realmente con alguna mitad.
            self.en_media_pantalla = True  # Registra el modo detectado.
            self.en_modo_ventana = False  # Garantiza exclusividad entre ambas modalidades.
            self.lado_media_pantalla = lado_detectado  # Conserva el lado administrado por Windows.
            self.barra_titulo.permitir_arrastre = False  # Mantiene el arrastre especial reservado al Modo ventana.
            self._actualizar_limites_ancho_pantalla()  # Convierte esa geometría en el modo fijo de TecNet Finder.
            self.barra_titulo.actualizar_estado_media_pantalla(True, self.lado_media_pantalla)  # Sincroniza visualmente el selector.
            self.barra_titulo.actualizar_estado_modo_ventana(False)  # Mantiene desactivado el nuevo modo.

    def alternar_pantalla_completa(self) -> None:  # Alterna fullscreen desde F11 o el botón correspondiente.
        self._cambiar_pantalla_completa(not self.en_pantalla_completa)  # Solicita exactamente el estado contrario al actual.

    def entrar_pantalla_completa(self) -> None:  # Solicita explícitamente entrar a fullscreen.
        self._cambiar_pantalla_completa(True)  # Delega toda la transición a la implementación común.

    def salir_pantalla_completa(self) -> None:  # Sale de fullscreen solamente cuando realmente está activo.
        if self.en_pantalla_completa:  # Comprueba el estado actual.
            self._cambiar_pantalla_completa(False)  # Solicita recuperar el modo anterior.

    def _cambiar_pantalla_completa(self, activar: bool) -> None:  # Administra entrada y salida de fullscreen conservando el modo anterior.
        if activar == self.en_pantalla_completa:  # Comprueba si ya se encuentra en el estado solicitado.
            return  # Evita repetir una transición innecesaria.

        if self.transicion_ventana_activa:  # Comprueba si existe otra transición todavía activa.
            return  # Ignora la nueva solicitud para evitar conflictos.

        self.transicion_ventana_activa = True  # Bloquea temporalmente otros cambios.

        def aplicar_estado() -> None:  # Aplica el modo solicitado después de atenuar la ventana.
            if activar:  # Atiende el ingreso a pantalla completa.
                if self.en_media_pantalla:  # Comprueba si fullscreen parte desde una mitad.
                    self.modo_antes_pantalla_completa = "media"  # Recuerda restaurar exactamente ese modo.
                elif self.en_modo_ventana:  # Comprueba si parte desde el nuevo tamaño fijo.
                    self.modo_antes_pantalla_completa = "ventana"  # Recuerda recuperar la ventana libremente desplazable.
                    self.geometria_modo_ventana = self.geometry()  # Conserva dónde estaba situada antes de fullscreen.
                else:  # Atiende maximizado o la ventana normal histórica.
                    self.modo_antes_pantalla_completa = "maximizado"  # Mantiene el comportamiento existente.

                self.en_media_pantalla = False  # Suspende temporalmente Media pantalla.
                self.en_modo_ventana = False  # Suspende temporalmente Modo ventana.
                self.barra_titulo.permitir_arrastre = False  # Evita movimiento manual durante fullscreen.
                self.en_pantalla_completa = True  # Registra fullscreen como estado actual.
                self._actualizar_limites_ancho_pantalla()  # Elimina cualquier máximo perteneciente a modos anteriores.
                self._habilitar_integracion_snap_windows()  # Recupera capacidades convencionales antes del cambio.
                self.showFullScreen()  # Ocupa completamente el monitor actual.
            else:  # Atiende la salida de fullscreen.
                self.en_pantalla_completa = False  # Registra primero el nuevo estado.

                if self.modo_antes_pantalla_completa == "media":  # Comprueba si anteriormente se utilizaba una mitad.
                    self.en_media_pantalla = True  # Recupera el modo fijo.
                    self.en_modo_ventana = False  # Mantiene inactivo Modo ventana.
                    self.barra_titulo.permitir_arrastre = False  # Conserva Snap como responsable de la posición.
                    self.showNormal()  # Vuelve temporalmente a una ventana administrable por Snap.
                    self._actualizar_limites_ancho_pantalla()  # Fija nuevamente el ancho de 50 %.
                    self._habilitar_integracion_snap_windows()  # Recupera capacidades nativas.
                    QApplication.processEvents()  # Completa la restauración antes de solicitar Snap.
                    QTimer.singleShot(100, self._restaurar_snap_media_pantalla)  # Devuelve TecNet Finder al mismo lado.
                elif self.modo_antes_pantalla_completa == "ventana":  # Comprueba si debe recuperar el tamaño fijo desplazable.
                    self.en_media_pantalla = False  # Mantiene desactivado Snap.
                    self.en_modo_ventana = True  # Recupera la nueva modalidad.
                    self.showNormal()  # Vuelve a una ventana convencional antes de restaurar la geometría.
                    self._actualizar_limites_ancho_pantalla()  # Reaplica ancho y alto fijos.
                    self._habilitar_integracion_snap_windows()  # Retira redimensionamiento nativo.
                    QApplication.processEvents()  # Garantiza que showNormal haya finalizado.
                    self._aplicar_geometria_modo_ventana(centrar=False, geometria_preferida=self.geometria_modo_ventana)  # Recupera la posición anterior siempre que siga visible.
                    self.barra_titulo.permitir_arrastre = True  # Habilita nuevamente el movimiento desde la barra.
                else:  # Atiende un fullscreen iniciado desde maximizado.
                    self.en_media_pantalla = False  # Mantiene desactivado el modo dividido.
                    self.en_modo_ventana = False  # Mantiene desactivado el tamaño fijo.
                    self.barra_titulo.permitir_arrastre = False  # Maximizado no debe moverse mediante nuestra barra.
                    self._actualizar_limites_ancho_pantalla()  # Libera nuevamente el ancho máximo.
                    self._habilitar_integracion_snap_windows()  # Mantiene activas las capacidades nativas.
                    self.showMaximized()  # Recupera la ventana principal convencional.

            self.barra_titulo.actualizar_estado_pantalla_completa(activar)  # Sincroniza icono y tooltip del botón.
            self.barra_titulo.actualizar_estado_media_pantalla(self.en_media_pantalla, self.lado_media_pantalla)  # Sincroniza también el selector de mitad.
            self.barra_titulo.actualizar_estado_modo_ventana(self.en_modo_ventana)  # Sincroniza la nueva modalidad.
            self.setWindowOpacity(0.72)  # Prepara la aparición después del cambio.

            def finalizar_transicion() -> None:  # Completa la animación de entrada.
                self.setWindowOpacity(1.0)  # Garantiza opacidad completa.
                self.transicion_ventana_activa = False  # Libera nuevamente los controles.

            self._animar_opacidad(0.72, 1.0, 170, finalizar_transicion)  # Hace aparecer progresivamente el nuevo modo.

        self._animar_opacidad(1.0, 0.72, 95, aplicar_estado)  # Atenúa la ventana antes de modificar su geometría.

    def _restaurar_snap_media_pantalla(self) -> None:  # Recupera el mismo lado después de salir de fullscreen o restaurar la ventana.
        if not self.en_media_pantalla or self.en_pantalla_completa or self.en_modo_ventana:  # Comprueba que Media pantalla siga siendo el estado solicitado.
            return  # Cancela tareas obsoletas.

        self._actualizar_limites_ancho_pantalla()  # Recupera exactamente el ancho fijo.
        self._habilitar_integracion_snap_windows()  # Confirma nuevamente las capacidades nativas.

        if self._geometria_corresponde_media_pantalla(self.lado_media_pantalla):  # Comprueba si Windows ya recuperó la posición correcta.
            return  # Mantiene esa geometría sin realizar otra operación.

        self._activar_snap_media_pantalla()  # Solicita nuevamente el acoplamiento cuando hace falta.

    def changeEvent(self, evento) -> None:  # Atiende cambios de estado como minimizar, restaurar o maximizar.
        super().changeEvent(evento)  # Permite que Qt procese primero el cambio.

        if evento.type() != QEvent.Type.WindowStateChange:  # Comprueba que se trate realmente del estado de la ventana.
            return  # Ignora cualquier otro tipo de cambio.

        estado = self.windowState()  # Obtiene el nuevo estado.
        estado_anterior = evento.oldState()  # Recupera el estado existente antes de esta transición.

        if estado_anterior & Qt.WindowState.WindowMinimized and not estado & Qt.WindowState.WindowMinimized:  # Comprueba si la ventana acaba de salir de minimizado.
            QTimer.singleShot(0, self._restaurar_animado)  # Recupera el modo que existía antes de minimizar.
            return  # Evita ejecutar también las demás comprobaciones.

        if estado & Qt.WindowState.WindowMinimized:  # Comprueba si precisamente se está entrando a minimizado.
            return  # Permite que Windows complete normalmente la operación.

        if self.en_pantalla_completa:  # Comprueba si fullscreen fue solicitado explícitamente.
            return  # Evita interpretar sus cambios internos como Snap.

        if estado & Qt.WindowState.WindowMaximized:  # Comprueba si Windows dejó la aplicación maximizada.
            self.en_media_pantalla = False  # Abandona cualquier estado dividido anterior.
            self.en_modo_ventana = False  # Abandona también el tamaño fijo.
            self.barra_titulo.permitir_arrastre = False  # Maximizado no debe moverse con nuestra barra.
            self._actualizar_limites_ancho_pantalla()  # Libera nuevamente el límite superior.
            self._habilitar_integracion_snap_windows()  # Recupera las capacidades nativas completas.
            self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Sincroniza el selector.
            self.barra_titulo.actualizar_estado_modo_ventana(False)  # Mantiene desactivada la nueva modalidad.
            QTimer.singleShot(0, self._configurar_ventana_para_pantalla_actual)  # Recupera límites e integración Win32.
            return  # Finaliza porque el nuevo estado ya quedó procesado.

        QTimer.singleShot(120, self._sincronizar_estado_media_pantalla)  # Permite reconocer un Snap administrado directamente por Windows.

    def _restaurar_animado(self) -> None:  # Recupera el modo previo después de salir de minimizado.
        if self.en_pantalla_completa:  # Comprueba si se minimizó desde fullscreen.
            self._actualizar_limites_ancho_pantalla()  # Garantiza que no exista un máximo temporal.
            self.showFullScreen()  # Recupera pantalla completa.
        elif self.en_modo_ventana:  # Comprueba si se minimizó desde la ventana fija.
            self.showNormal()  # Recupera una ventana convencional.
            self._actualizar_limites_ancho_pantalla()  # Reaplica exactamente su tamaño fijo.
            self._habilitar_integracion_snap_windows()  # Conserva bloqueado el redimensionamiento nativo.
            self.barra_titulo.permitir_arrastre = True  # Mantiene disponible el movimiento desde la barra.
            self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Mantiene las mitades inactivas.
            self.barra_titulo.actualizar_estado_modo_ventana(True)  # Conserva sincronizado el selector.
        elif self.en_media_pantalla:  # Comprueba si se minimizó desde una mitad.
            self.showNormal()  # Recupera primero una ventana compatible con Snap.
            self._actualizar_limites_ancho_pantalla()  # Fija nuevamente el ancho.
            self._habilitar_integracion_snap_windows()  # Recupera las capacidades nativas.
            self.barra_titulo.permitir_arrastre = False  # Conserva la posición administrada por Snap.
            self.barra_titulo.actualizar_estado_modo_ventana(False)  # Mantiene desactivada la nueva modalidad.
            QTimer.singleShot(120, self._restaurar_snap_media_pantalla)  # Regresa al mismo lado cuando sea necesario.
        else:  # Atiende el modo principal maximizado.
            self._actualizar_limites_ancho_pantalla()  # Conserva únicamente el mínimo.
            self._habilitar_integracion_snap_windows()  # Mantiene disponibles las capacidades de Snap.
            self.barra_titulo.permitir_arrastre = False  # Maximizado permanece inmóvil desde la barra personalizada.
            self.barra_titulo.actualizar_estado_modo_ventana(False)  # Mantiene desactivada la nueva modalidad.
            self.showMaximized()  # Recupera maximizado.

        self.setWindowOpacity(0.55)  # Comienza la restauración parcialmente transparente.

        def finalizar_restauracion() -> None:  # Completa la aparición después de restaurar.
            self.setWindowOpacity(1.0)  # Garantiza visibilidad completa.
            self.transicion_ventana_activa = False  # Libera nuevamente los controles.

        self._animar_opacidad(0.55, 1.0, 180, finalizar_restauracion)  # Ejecuta la transición de restauración.

    def activar_desde_instancia_secundaria(self) -> None:  # Recupera y lleva al frente la instancia ya abierta de TecNet Finder.
        if self.isMinimized():  # Comprueba si la instancia existente está actualmente en la barra de tareas.
            if self.en_modo_ventana:  # Recupera específicamente la ventana fija.
                self.showNormal()  # Restaura el estado convencional.
                self._actualizar_limites_ancho_pantalla()  # Reaplica el tamaño bloqueado.
                self._habilitar_integracion_snap_windows()  # Conserva deshabilitado el redimensionamiento nativo.
                self.barra_titulo.permitir_arrastre = True  # Permite seguir moviéndola desde la barra.
                self.barra_titulo.actualizar_estado_media_pantalla(False, self.lado_media_pantalla)  # Mantiene Snap inactivo.
                self.barra_titulo.actualizar_estado_modo_ventana(True)  # Mantiene el selector sincronizado.
            elif self.en_media_pantalla:  # Recupera específicamente una ventana que estaba dividida.
                self.showNormal()  # Permite nuevamente administrarla mediante Snap.
                self._actualizar_limites_ancho_pantalla()  # Recupera el ancho correspondiente al monitor actual.
                self._habilitar_integracion_snap_windows()  # Confirma las capacidades nativas.
                self.barra_titulo.permitir_arrastre = False  # Conserva el control mediante Snap.
                QTimer.singleShot(120, self._restaurar_snap_media_pantalla)  # Devuelve la ventana a la misma mitad.
            elif self.en_pantalla_completa:  # Recupera una instancia minimizada desde fullscreen.
                self._actualizar_limites_ancho_pantalla()  # Elimina cualquier máximo temporal.
                self.showFullScreen()  # Recupera pantalla completa.
            else:  # Atiende el estado principal maximizado.
                self._actualizar_limites_ancho_pantalla()  # Libera cualquier límite superior previo.
                self._habilitar_integracion_snap_windows()  # Conserva compatibilidad con Snap.
                self.barra_titulo.permitir_arrastre = False  # Maximizado no utiliza arrastre propio.
                self.showMaximized()  # Recupera maximizado.
        else:  # Atiende una instancia que simplemente quedó detrás de otras ventanas.
            self.show()  # Garantiza que permanezca visible.

        self.setWindowOpacity(1.0)  # Evita conservar una transición parcial cuando llegó la solicitud.
        self.raise_()  # Coloca la instancia existente por encima de otras ventanas.
        self.activateWindow()  # Solicita el foco de entrada.

        manejador = self.windowHandle()  # Obtiene la representación nativa cuando se encuentra disponible.

        if manejador is not None:  # Comprueba que Qt ya haya creado el manejador.
            manejador.requestActivate()  # Solicita adicionalmente la activación desde la capa nativa.

    def _analizar_codigo(self) -> None:  # Ejecuta FlujoCompilacion sobre exactamente el contenido actual del editor.
        codigo_fuente = self.editor_codigo.toPlainText()  # Recupera el texto completo escrito por el usuario.

        if not codigo_fuente.strip():  # Comprueba que exista al menos una instrucción o fragmento.
            QMessageBox.warning(self, "Entrada vacía", "Introduce una instrucción de TecNet Finder antes de compilar.")  # Informa el requisito sin ejecutar ninguna fase.
            return  # Mantiene intacto el estado actual.

        try:  # Protege la interfaz frente a fallos inesperados fuera de los diagnósticos normales.
            resultado = self.flujo.analizar(codigo_fuente)  # Ejecuta las fases disponibles mediante Motor.
        except Exception as error:  # Atiende una excepción interna que no pudo expresarse como diagnóstico formal.
            self._limpiar_resultados_conservando_entrada()  # Elimina resultados anteriores para impedir mostrar información obsoleta.
            self._mostrar_estado_error_interno()  # Deja la barra general en un estado coherente.
            QMessageBox.critical(self, "Error interno", f"No se pudo completar el análisis:\n{error}")  # Informa el problema sin cerrar TecNet Finder.
            return  # Finaliza porque no existe un resultado confiable que mostrar.

        self.ultimo_resultado = resultado  # Conserva la compilación más reciente.
        self.panel_diagnosticos.mostrar_diagnosticos(resultado.diagnosticos)  # Actualiza la tabla estructurada.
        self.editor_codigo.mostrar_diagnosticos(resultado.diagnosticos)  # Dibuja las ondas directamente sobre el código.
        self.panel_resultados.mostrar_resultado(resultado)  # Actualiza resumen, tablas y vistas de análisis.
        self._actualizar_estado(resultado)  # Actualiza finalmente la barra informativa superior.

    def _actualizar_estado(self, resultado) -> None:  # Construye el resumen visible según errores, advertencias y subredes obtenidas.
        cantidad_errores = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad == "error")  # Cuenta exclusivamente diagnósticos bloqueantes.
        cantidad_advertencias = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia"))  # Cuenta únicamente recomendaciones no bloqueantes.
        cantidad_subredes = len(resultado.subredes_vlsm)  # Obtiene cuántas subredes fueron realmente generadas.

        if cantidad_errores > 0:  # Da prioridad visual al estado de error cuando existe al menos uno.
            self.etiqueta_estado.setObjectName("EstadoError")  # Utiliza el estilo rojo.
            self.etiqueta_estado.setText(f"Análisis terminado con errores: {cantidad_errores} error(es) | Advertencias: {cantidad_advertencias} | Subredes generadas: {cantidad_subredes}")  # Resume el resultado conservando también posibles salidas parciales.
        elif cantidad_advertencias > 0:  # Atiende una compilación sin errores pero con recomendaciones.
            self.etiqueta_estado.setObjectName("EstadoAdvertencia")  # Utiliza el estilo amarillo.
            self.etiqueta_estado.setText(f"Análisis completo con advertencias: {cantidad_advertencias} | Bloques válidos: {len(resultado.bloques_validos)} | Subredes generadas: {cantidad_subredes}")  # Resume la compilación válida con avisos.
        else:  # Atiende una compilación completamente limpia.
            self.etiqueta_estado.setObjectName("EstadoCorrecto")  # Utiliza el estilo positivo.
            self.etiqueta_estado.setText(f"Análisis completo | Bloques válidos: {len(resultado.bloques_validos)} | Subredes generadas: {cantidad_subredes}")  # Muestra únicamente la información necesaria.

        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira temporalmente la apariencia anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente la hoja de estilos utilizando el nuevo ObjectName.
        self.etiqueta_estado.update()  # Solicita un redibujado inmediato.

    def _ir_a_diagnostico(self, diagnostico) -> None:  # Navega desde PanelDiagnosticos hacia la ubicación señalada dentro del código.
        self.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Utiliza directamente los datos estructurados del diagnóstico.

    def _restablecer_estado_neutral(self) -> None:  # Recupera el estado mostrado antes de ejecutar cualquier compilación.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Recupera la apariencia inicial.
        self.etiqueta_estado.setText("Sin análisis ejecutado.")  # Recupera el mensaje neutral.
        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira temporalmente el estilo anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente la apariencia neutral.
        self.etiqueta_estado.update()  # Redibuja inmediatamente la etiqueta.

    def _mostrar_estado_error_interno(self) -> None:  # Representa visualmente una excepción inesperada del flujo.
        self.etiqueta_estado.setObjectName("EstadoError")  # Utiliza la misma apariencia roja empleada por errores formales.
        self.etiqueta_estado.setText("Análisis interrumpido por un error interno.")  # Explica que cualquier resultado anterior fue descartado.
        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira el formato anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica inmediatamente el estado de error.
        self.etiqueta_estado.update()  # Solicita redibujar antes de abrir el cuadro modal.

    def _limpiar_resultados_conservando_entrada(self) -> None:  # Invalida toda salida anterior sin borrar el código fuente actual.
        self.editor_codigo.limpiar_diagnosticos()  # Elimina ondas pertenecientes a la compilación previa.
        self.panel_diagnosticos.limpiar()  # Vacía errores y advertencias detectados.
        self.panel_resultados.limpiar()  # Restaura resumen, tablas, sintaxis y acciones de resultados.
        self.ultimo_resultado = None  # Elimina la referencia hacia la compilación obsoleta.
        self._restablecer_estado_neutral()  # Recupera la barra general previa a una compilación.
        self.editor_codigo.setFocus()  # Permite continuar inmediatamente editando la entrada.

    def _limpiar_todo(self) -> None:  # Restaura completamente editor y resultados.
        self.editor_codigo.limpiar_diagnosticos()  # Elimina primero las ondas de la compilación anterior.
        self.editor_codigo.clear()  # Vacía completamente el código fuente.
        self.panel_diagnosticos.limpiar()  # Elimina los diagnósticos detectados.
        self.panel_resultados.limpiar()  # Restaura todas las pestañas de salida.
        self.ultimo_resultado = None  # Descarta el resultado anterior.
        self._restablecer_estado_neutral()  # Recupera mensaje y apariencia iniciales.
        self.editor_codigo.setFocus()  # Coloca nuevamente el cursor en el editor.

    def closeEvent(self, evento) -> None:  # Reproduce la animación final antes de permitir realmente el cierre.
        if self.cierre_autorizado:  # Comprueba si la animación ya terminó y esta es la segunda solicitud.
            evento.accept()  # Permite que Qt cierre definitivamente TecNet Finder.
            return  # Finaliza sin iniciar otra transición.

        evento.ignore()  # Detiene temporalmente la solicitud original.

        if self.transicion_ventana_activa:  # Comprueba si ya existe otra transición ejecutándose.
            return  # Evita iniciar dos animaciones simultáneamente.

        self.transicion_ventana_activa = True  # Bloquea los controles durante los últimos milisegundos.

        def finalizar_cierre() -> None:  # Autoriza y vuelve a solicitar el cierre después del desvanecimiento.
            self.cierre_autorizado = True  # Marca que la siguiente entrada a closeEvent puede aceptarse.
            self.close()  # Solicita nuevamente el cierre.

        self._animar_opacidad(1.0, 0.0, 160, finalizar_cierre)  # Desvanece progresivamente TecNet Finder antes de terminar.
