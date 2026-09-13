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
# El modo Media pantalla utiliza exactamente la mitad horizontal
# del monitor actual. Puede colocarse a la izquierda o derecha
# mediante el selector visual de la barra superior.
#
# El mismo selector permite regresar explícitamente al modo de
# ventana maximizada sin confundirlo con pantalla completa.
#
# Mientras Media pantalla está activo, TecNet Finder mantiene
# ese ancho fijo para conservar una distribución 50/50.
#
# Fuera de Media pantalla, la restricción máxima se elimina
# para permitir maximizado y pantalla completa normalmente.
#
# También puede recuperarse y llevarse al frente cuando otra
# ejecución detecta que TecNet Finder ya se encuentra abierto.
# ============================================================

import ctypes  # Permite recuperar capacidades nativas de ventana mediante la API Win32 sin agregar dependencias externas.
from ctypes import wintypes  # Proporciona tipos compatibles con las funciones de Windows utilizadas por la integración de Snap.
import sys  # Permite distinguir Windows de otros sistemas antes de utilizar funciones específicas de Win32.
from pathlib import Path  # Permite localizar los recursos del proyecto sin depender de rutas absolutas.

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QTimer, Qt  # Importa eventos, animaciones, temporización y estados de Qt.
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut  # Importa iconos, atajos de teclado e imágenes.
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget  # Importa los componentes principales de la ventana.

from Interfaz.barra_titulo import BarraTitulo  # Importa la barra personalizada que sustituye visualmente la barra convencional de Windows.
from Interfaz.editor_codigo import EditorCodigo  # Importa el editor especializado con números de línea y diagnósticos.
from Interfaz.panel_diagnosticos import PanelDiagnosticos  # Importa la tabla estructurada de errores y advertencias.
from Interfaz.panel_resultados import PanelResultados  # Importa las vistas utilizadas para mostrar resultados del compilador.
from Interfaz.resaltador_sintaxis import ResaltadorSintaxis  # Importa el resaltado del lenguaje TecNet Finder.
from Motor.flujo_compilacion import FlujoCompilacion  # Importa el coordinador central de las fases disponibles.


GWL_STYLE = -16  # Identifica el conjunto de estilos principales asociado con una ventana Win32.
WS_SYSMENU = 0x00080000  # Recupera capacidades estándar relacionadas con la administración del sistema.
WS_THICKFRAME = 0x00040000  # Indica a Windows que la ventana puede cambiar de tamaño y participar correctamente en Snap.
WS_MINIMIZEBOX = 0x00020000  # Informa que la ventana admite minimización.
WS_MAXIMIZEBOX = 0x00010000  # Informa que la ventana admite maximización y layouts de ajuste.

SWP_NOSIZE = 0x0001  # Evita cambiar el tamaño al actualizar únicamente los estilos nativos.
SWP_NOMOVE = 0x0002  # Evita cambiar la posición al actualizar únicamente los estilos nativos.
SWP_NOZORDER = 0x0004  # Conserva el orden actual entre ventanas.
SWP_NOACTIVATE = 0x0010  # Evita alterar el foco únicamente por refrescar el marco nativo.
SWP_FRAMECHANGED = 0x0020  # Obliga a Windows a recalcular el marco después de modificar sus estilos.

VK_LWIN = 0x5B  # Representa la tecla Windows izquierda para SendInput.
VK_LEFT = 0x25  # Representa la flecha izquierda utilizada para solicitar Snap sobre ese lado.
VK_RIGHT = 0x27  # Representa la flecha derecha utilizada para solicitar Snap sobre ese lado.
KEYEVENTF_KEYUP = 0x0002  # Indica que una entrada de teclado corresponde con la liberación de una tecla.
INPUT_KEYBOARD = 1  # Identifica una entrada simulada como evento de teclado para la API SendInput.

ANCHO_MAXIMO_QT = 16777215  # Representa el límite máximo convencional utilizado por Qt cuando una dimensión no debe estar restringida.


class EntradaTecladoWindows(ctypes.Structure):  # Representa un evento individual de teclado compatible con SendInput.
    _fields_ = [
        ("wVk", wintypes.WORD),  # Guarda el código virtual correspondiente con la tecla.
        ("wScan", wintypes.WORD),  # Reserva el código de escaneo cuando fuera necesario.
        ("dwFlags", wintypes.DWORD),  # Guarda banderas como la liberación de una tecla.
        ("time", wintypes.DWORD),  # Permite utilizar la marca temporal proporcionada automáticamente por Windows.
        ("dwExtraInfo", wintypes.WPARAM),  # Reserva información adicional asociada con la entrada.
    ]


class UnionEntradaWindows(ctypes.Union):  # Representa la sección variable de una estructura INPUT.
    _fields_ = [
        ("ki", EntradaTecladoWindows),  # Utiliza exclusivamente la variante correspondiente con teclado.
    ]


class EntradaWindows(ctypes.Structure):  # Representa una entrada completa compatible con SendInput.
    _anonymous_ = ("contenido",)  # Permite acceder directamente mediante entrada.ki sin mencionar explícitamente la unión.
    _fields_ = [
        ("tipo", wintypes.DWORD),  # Identifica la entrada como teclado.
        ("contenido", UnionEntradaWindows),  # Conserva los datos específicos del evento.
    ]


class VentanaPrincipal(QMainWindow):  # Define la ventana principal y controla maximizado, Media pantalla y fullscreen.
    def __init__(self):
        super().__init__()  # Inicializa el comportamiento base proporcionado por QMainWindow.
        self.flujo = FlujoCompilacion()  # Crea el coordinador encargado de ejecutar las fases reconstruidas.
        self.ultimo_resultado = None  # Reserva una referencia para conservar el resultado más reciente.
        self.en_pantalla_completa = False  # Indica si actualmente se utiliza fullscreen.
        self.en_media_pantalla = False  # Indica si TecNet Finder se encuentra actualmente en una de las dos mitades.
        self.lado_media_pantalla = "izquierda"  # Conserva la última mitad seleccionada como referencia del estado actual.
        self.modo_antes_pantalla_completa = "maximizado"  # Recuerda el tamaño que debe recuperarse después de abandonar fullscreen.
        self.transicion_ventana_activa = False  # Impide iniciar varias animaciones de ventana simultáneamente.
        self.animacion_opacidad = None  # Conserva la animación activa para evitar que Python la destruya antes de terminar.
        self.cierre_autorizado = False  # Permite diferenciar el cierre animado inicial del cierre definitivo.
        self.integracion_snap_configurada = False  # Registra si Win32 ya recibió los estilos nativos requeridos por Snap.
        self.conexion_cambio_pantalla_configurada = False  # Evita conectar varias veces la señal utilizada para recalcular los límites.

        self.setWindowTitle("TecNet Finder")  # Conserva el nombre visible para Windows y la barra de tareas.
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        )  # Mantiene visualmente nuestra barra personalizada en lugar de la barra convencional del sistema.
        self.setMinimumHeight(560)  # Impide reducir verticalmente la aplicación hasta una altura poco funcional.

        self._cargar_icono()  # Carga el icono oficial desde Recursos.
        self._construir_interfaz()  # Construye la barra propia y el contenido principal.
        self._configurar_atajos()  # Activa F11 y Escape para controlar fullscreen.

    def _ruta_recurso(self, nombre_archivo: str) -> Path:
        raiz_proyecto = Path(__file__).resolve().parent.parent  # Obtiene la carpeta raíz de TecNet Finder.
        return raiz_proyecto / "Recursos" / nombre_archivo  # Devuelve la ruta correspondiente con el recurso solicitado.

    def _cargar_icono(self) -> None:
        ruta_icono = self._ruta_recurso("LogoTNF.ico")  # Obtiene la ubicación del archivo ICO existente.

        if ruta_icono.exists():
            self.setWindowIcon(QIcon(str(ruta_icono)))  # Establece el icono general utilizado por Windows.

    def _construir_interfaz(self) -> None:
        central = QWidget()  # Crea el widget raíz que ocupa toda la ventana.
        central.setObjectName("VentanaCentral")  # Permite aplicar el fondo general desde estilos.py.
        self.setCentralWidget(central)  # Asigna el widget como contenido principal.

        diseno_general = QVBoxLayout(central)  # Organiza barra personalizada y contenido de forma vertical.
        diseno_general.setContentsMargins(0, 0, 0, 0)  # Permite que la barra llegue exactamente a los bordes.
        diseno_general.setSpacing(0)  # Evita cualquier separación entre barra y contenido.

        self.barra_titulo = BarraTitulo(
            self,
            self._ruta_recurso("LogoTNF.ico"),
            mostrar_media_pantalla=True,
        )  # Crea la barra principal habilitando específicamente el selector visual de Media pantalla.
        diseno_general.addWidget(self.barra_titulo)  # Coloca la barra personalizada permanentemente en la parte superior.

        contenido = QWidget()  # Crea el contenedor donde se muestra realmente TecNet Finder.
        contenido.setObjectName("ContenidoPrincipal")  # Permite diferenciarlo visualmente de la barra superior.
        diseno_contenido = QVBoxLayout(contenido)  # Organiza encabezado, estado y pestañas.
        diseno_contenido.setContentsMargins(14, 10, 14, 14)  # Mantiene el espacio visual utilizado por la interfaz.
        diseno_contenido.setSpacing(9)  # Define una separación uniforme entre secciones.

        self._construir_encabezado(diseno_contenido)  # Agrega el logotipo y el nombre grande.

        self.etiqueta_estado = QLabel("Sin análisis ejecutado.")  # Crea la barra informativa situada debajo del encabezado.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Aplica inicialmente el estado visual neutro.
        diseno_contenido.addWidget(self.etiqueta_estado)  # Coloca el estado encima del área principal de pestañas.

        self.editor_codigo = EditorCodigo()  # Crea el editor especializado de TecNet Finder.
        self.resaltador_sintaxis = ResaltadorSintaxis(
            self.editor_codigo.document()
        )  # Conecta el resaltador con el documento utilizado por el editor.
        self.panel_diagnosticos = PanelDiagnosticos()  # Crea la tabla estructurada de errores y advertencias.

        self.panel_resultados = PanelResultados(
            editor_codigo=self.editor_codigo,
            panel_diagnosticos=self.panel_diagnosticos,
            accion_analizar=self._analizar_codigo,
            accion_limpiar=self._limpiar_todo,
        )  # Construye el área de trabajo completa.

        diseno_contenido.addWidget(self.panel_resultados, 1)  # Permite que las pestañas utilicen todo el espacio restante.
        diseno_general.addWidget(contenido, 1)  # Coloca el contenido debajo de la barra personalizada.

        self.panel_diagnosticos.diagnostico_activado.connect(
            self._ir_a_diagnostico
        )  # Permite navegar desde un diagnóstico hasta el código fuente.
        self.editor_codigo.ejemplos_insertados.connect(
            self._limpiar_resultados_conservando_entrada
        )  # Descarta resultados antiguos después de insertar ejemplos.

        self.barra_titulo.actualizar_estado_media_pantalla(
            False,
            self.lado_media_pantalla,
        )  # Inicializa el selector sin ninguna mitad activa.

    def _construir_encabezado(self, diseno_principal: QVBoxLayout) -> None:
        encabezado = QHBoxLayout()  # Organiza horizontalmente logotipo y textos.
        encabezado.setSpacing(12)  # Mantiene una separación cómoda entre ambos elementos.
        ruta_logo = self._ruta_recurso("LogoTNF.png")  # Obtiene la ruta del logotipo de mayor resolución.

        if ruta_logo.exists():
            etiqueta_logo = QLabel()  # Crea el contenedor de la imagen.
            imagen = QPixmap(str(ruta_logo)).scaled(
                58,
                58,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )  # Reduce el logotipo conservando calidad y proporción.
            etiqueta_logo.setPixmap(imagen)  # Coloca la imagen escalada.
            encabezado.addWidget(etiqueta_logo)  # Agrega el logotipo al lado izquierdo.

        caja_titulos = QVBoxLayout()  # Crea una columna para nombre y descripción.
        titulo = QLabel("TecNet Finder")  # Crea el nombre principal del proyecto.
        titulo.setObjectName("TituloPrincipal")  # Aplica el estilo reservado para el título grande.
        subtitulo = QLabel(
            "Compilador para análisis de instrucciones VLSM"
        )  # Conserva la descripción breve del proyecto.
        subtitulo.setObjectName("SubtituloPrincipal")  # Aplica el estilo secundario.

        caja_titulos.addWidget(titulo)  # Coloca el nombre como primera línea.
        caja_titulos.addWidget(subtitulo)  # Coloca la descripción debajo.
        encabezado.addLayout(caja_titulos)  # Agrega ambos textos al encabezado.
        encabezado.addStretch()  # Mantiene el conjunto alineado hacia la izquierda.
        diseno_principal.addLayout(encabezado)  # Inserta el encabezado en el contenido principal.

    def _configurar_atajos(self) -> None:
        self.atajo_pantalla_completa = QShortcut(
            QKeySequence("F11"),
            self,
        )  # Crea el atajo convencional utilizado para fullscreen.
        self.atajo_pantalla_completa.activated.connect(
            self.alternar_pantalla_completa
        )  # Hace que F11 alterne pantalla completa.

        self.atajo_salir_pantalla_completa = QShortcut(
            QKeySequence("Escape"),
            self,
        )  # Permite utilizar Escape para abandonar fullscreen.
        self.atajo_salir_pantalla_completa.activated.connect(
            self.salir_pantalla_completa
        )  # Solo modifica el estado cuando fullscreen está activo.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt complete primero la creación o restauración visual de la ventana.

        QTimer.singleShot(
            0,
            self._configurar_ventana_para_pantalla_actual,
        )  # Configura límites, seguimiento del monitor y soporte Snap después de crear el HWND.

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)  # Permite que Qt actualice primero todos los componentes internos.

        if self.isVisible() and not self.en_pantalla_completa:
            QTimer.singleShot(
                120,
                self._sincronizar_estado_media_pantalla,
            )  # Detecta cambios realizados directamente por Snap después de que Windows termine su animación.

    def moveEvent(self, evento) -> None:
        super().moveEvent(evento)  # Conserva el procesamiento normal del desplazamiento de la ventana.

        if self.isVisible() and not self.en_pantalla_completa:
            QTimer.singleShot(
                120,
                self._sincronizar_estado_media_pantalla,
            )  # Actualiza el estado cuando Windows modifica la posición durante Snap.

    def _configurar_ventana_para_pantalla_actual(self) -> None:
        self._actualizar_limites_ancho_pantalla()  # Configura el límite apropiado según el modo actual.
        self._conectar_cambio_pantalla()  # Escucha cambios de monitor para recalcular dimensiones.
        self._habilitar_integracion_snap_windows()  # Recupera las capacidades Win32 necesarias para Snap.

    def _conectar_cambio_pantalla(self) -> None:
        if self.conexion_cambio_pantalla_configurada:
            return  # Evita conectar varias veces la misma señal durante restauraciones posteriores.

        manejador = self.windowHandle()  # Obtiene la representación nativa administrada por Qt.

        if manejador is None:
            return  # Espera una visualización posterior si Qt todavía no creó el manejador.

        manejador.screenChanged.connect(
            self._al_cambiar_pantalla
        )  # Recalcula límites cuando TecNet Finder pasa físicamente a otro monitor.
        self.conexion_cambio_pantalla_configurada = True  # Registra que la señal quedó conectada correctamente.

    def _al_cambiar_pantalla(self, pantalla) -> None:
        self._actualizar_limites_ancho_pantalla(
            pantalla
        )  # Adapta inmediatamente el ancho mínimo y máximo al nuevo monitor.
        QTimer.singleShot(
            0,
            self._habilitar_integracion_snap_windows,
        )  # Refresca también las capacidades nativas después de cambiar de monitor.

    def _obtener_ancho_mitad_pantalla(self, pantalla=None) -> int:
        pantalla_objetivo = (
            pantalla or self.screen() or QApplication.primaryScreen()
        )  # Prioriza la pantalla recibida y utiliza la principal como respaldo.

        if pantalla_objetivo is None:
            return max(self.width(), 1)  # Conserva un valor seguro si Qt todavía no conoce ningún monitor.

        area = pantalla_objetivo.availableGeometry()  # Obtiene el escritorio utilizable sin incluir la barra de tareas.
        return max(area.width() // 2, 1)  # Devuelve exactamente la mitad lógica del monitor actual.

    def _actualizar_limites_ancho_pantalla(self, pantalla=None) -> None:
        ancho_mitad = self._obtener_ancho_mitad_pantalla(
            pantalla
        )  # Calcula una sola vez la mitad correspondiente con la pantalla actual.
        pantalla_objetivo = (
            pantalla or self.screen() or QApplication.primaryScreen()
        )  # Recupera también la pantalla para ajustar la altura mínima.

        if self.en_media_pantalla and not self.en_pantalla_completa:
            self.setMinimumWidth(
                ancho_mitad
            )  # Impide reducir TecNet Finder por debajo de media pantalla.
            self.setMaximumWidth(
                ancho_mitad
            )  # Impide ampliar TecNet Finder por encima del 50 % mientras Media pantalla está activo.
        else:
            self.setMinimumWidth(
                ancho_mitad
            )  # Conserva media pantalla como ancho mínimo incluso fuera del modo dividido.
            self.setMaximumWidth(
                ANCHO_MAXIMO_QT
            )  # Libera el límite superior para permitir maximizado y fullscreen.

        if pantalla_objetivo is not None:
            alto_minimo = min(
                560,
                pantalla_objetivo.availableGeometry().height(),
            )  # Mantiene una altura cómoda sin superar pantallas excepcionalmente pequeñas.
            self.setMinimumHeight(
                alto_minimo
            )  # Actualiza el límite vertical apropiado para el monitor actual.

    def _habilitar_integracion_snap_windows(self) -> bool:
        if sys.platform != "win32":
            return False  # Mantiene el programa funcional en otros sistemas sin ejecutar funciones exclusivas de Windows.

        try:
            identificador_ventana = int(self.winId())  # Recupera el HWND perteneciente con la ventana principal.
            usuario32 = ctypes.windll.user32  # Obtiene las funciones relacionadas con ventanas del sistema.

            usuario32.GetWindowLongW.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
            ]  # Define los argumentos utilizados para consultar el estilo actual.
            usuario32.GetWindowLongW.restype = ctypes.c_long  # Define el tipo de resultado devuelto por Windows.

            usuario32.SetWindowLongW.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_long,
            ]  # Define los argumentos utilizados para sustituir el estilo.
            usuario32.SetWindowLongW.restype = ctypes.c_long  # Define el tipo devuelto por la modificación.

            estilo_actual = usuario32.GetWindowLongW(
                identificador_ventana,
                GWL_STYLE,
            )  # Recupera las capacidades que Qt asignó inicialmente a la ventana.

            capacidades_snap = (
                WS_SYSMENU
                | WS_THICKFRAME
                | WS_MINIMIZEBOX
                | WS_MAXIMIZEBOX
            )  # Agrupa las capacidades nativas requeridas sin recuperar la barra estándar.

            estilo_actualizado = (
                estilo_actual | capacidades_snap
            )  # Mantiene los estilos actuales y agrega soporte de administración por Windows.

            if estilo_actualizado != estilo_actual:
                usuario32.SetWindowLongW(
                    identificador_ventana,
                    GWL_STYLE,
                    estilo_actualizado,
                )  # Recupera las capacidades perdidas por FramelessWindowHint.

                usuario32.SetWindowPos(
                    identificador_ventana,
                    0,
                    0,
                    0,
                    0,
                    0,
                    SWP_NOMOVE
                    | SWP_NOSIZE
                    | SWP_NOZORDER
                    | SWP_NOACTIVATE
                    | SWP_FRAMECHANGED,
                )  # Solicita a Windows recalcular internamente la ventana sin cambiar su geometría.

            self.integracion_snap_configurada = True  # Registra que el HWND actual recibió correctamente las capacidades nativas.
            return True  # Confirma que la integración pudo configurarse.
        except (AttributeError, OSError, TypeError, ValueError):
            self.integracion_snap_configurada = False  # Conserva un estado seguro cuando Win32 no permite modificar la ventana.
            return False  # Permite utilizar posteriormente el respaldo geométrico.

    def _crear_entrada_teclado(
        self,
        tecla: int,
        liberar: bool = False,
    ) -> EntradaWindows:
        banderas = KEYEVENTF_KEYUP if liberar else 0  # Decide si la estructura representa pulsación o liberación.

        return EntradaWindows(
            tipo=INPUT_KEYBOARD,
            ki=EntradaTecladoWindows(
                wVk=tecla,
                wScan=0,
                dwFlags=banderas,
                time=0,
                dwExtraInfo=0,
            ),
        )  # Devuelve una entrada completamente preparada para SendInput.

    def _enviar_atajo_snap(self, lado: str) -> bool:
        if sys.platform != "win32":
            return False  # Impide utilizar una API inexistente fuera de Windows.

        tecla_direccion = VK_RIGHT if lado == "derecha" else VK_LEFT  # Selecciona la flecha correspondiente con la mitad solicitada.

        try:
            self._habilitar_integracion_snap_windows()  # Garantiza que el HWND posea las capacidades necesarias antes de solicitar Snap.

            identificador_ventana = int(self.winId())  # Recupera la ventana que debe recibir el atajo.
            usuario32 = ctypes.windll.user32  # Obtiene las funciones de entrada y activación de Windows.

            usuario32.SetForegroundWindow(
                identificador_ventana
            )  # Solicita que TecNet Finder sea realmente la ventana activa antes de enviar el atajo.
            self.raise_()  # Refuerza desde Qt que la aplicación permanezca encima.
            self.activateWindow()  # Solicita también el foco mediante la capa de Qt.
            QApplication.processEvents()  # Procesa la activación antes de enviar las teclas.

            entradas = (EntradaWindows * 4)(
                self._crear_entrada_teclado(VK_LWIN),
                self._crear_entrada_teclado(tecla_direccion),
                self._crear_entrada_teclado(tecla_direccion, liberar=True),
                self._crear_entrada_teclado(VK_LWIN, liberar=True),
            )  # Construye Win+Izquierda o Win+Derecha según la mitad elegida.

            entradas_enviadas = usuario32.SendInput(
                len(entradas),
                ctypes.byref(entradas),
                ctypes.sizeof(EntradaWindows),
            )  # Envía la secuencia mediante el mecanismo moderno de entrada sintetizada de Windows.

            return entradas_enviadas == len(entradas)  # Confirma que Windows aceptó toda la secuencia.
        except (AttributeError, OSError, TypeError, ValueError):
            return False  # Permite recurrir al ajuste manual cuando la API nativa falla.

    def _animar_opacidad(
        self,
        inicio: float,
        fin: float,
        duracion: int,
        al_terminar=None,
    ) -> None:
        if self.animacion_opacidad is not None:
            self.animacion_opacidad.stop()  # Detiene una animación anterior para evitar que ambas controlen la misma propiedad.

        self.setWindowOpacity(inicio)  # Coloca inmediatamente la ventana en la opacidad inicial.

        self.animacion_opacidad = QPropertyAnimation(
            self,
            b"windowOpacity",
            self,
        )  # Crea una animación sobre la opacidad general.
        self.animacion_opacidad.setDuration(duracion)  # Define cuántos milisegundos durará la transición.
        self.animacion_opacidad.setStartValue(inicio)  # Define la opacidad inicial.
        self.animacion_opacidad.setEndValue(fin)  # Define la opacidad final.
        self.animacion_opacidad.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )  # Utiliza una aceleración y desaceleración progresivas.

        if al_terminar is not None:
            self.animacion_opacidad.finished.connect(
                al_terminar
            )  # Ejecuta la acción solicitada al terminar la transición.

        self.animacion_opacidad.start()  # Inicia la animación configurada.

    def minimizar_animado(self) -> None:
        if self.transicion_ventana_activa:
            return  # Ignora clics adicionales hasta terminar otra transición.

        self.transicion_ventana_activa = True  # Bloquea temporalmente otros cambios de estado.

        def finalizar_minimizado() -> None:
            self.showMinimized()  # Envía finalmente TecNet Finder hacia la barra de tareas.
            self.setWindowOpacity(1.0)  # Deja preparada la opacidad normal para cuando vuelva a mostrarse.
            self.transicion_ventana_activa = False  # Permite nuevamente utilizar los controles de ventana.

        self._animar_opacidad(
            1.0,
            0.35,
            130,
            finalizar_minimizado,
        )  # Reduce rápidamente la presencia visual antes de minimizar.

    def alternar_media_pantalla(self) -> None:
        if self.en_media_pantalla:
            self._cambiar_media_pantalla(False)  # Recupera maximizado cuando el modo dividido ya se encuentra activo.
        else:
            self._cambiar_media_pantalla(
                True,
                self.lado_media_pantalla,
            )  # Utiliza el último lado seleccionado cuando otro control solicita alternar directamente.

    def colocar_media_pantalla(self, lado: str) -> None:
        if lado not in ("izquierda", "derecha"):
            return  # Ignora cualquier posición distinta de las dos opciones admitidas.

        self._cambiar_media_pantalla(
            True,
            lado,
        )  # Coloca directamente TecNet Finder sobre la mitad elegida desde el selector visual.

    def maximizar_ventana(self) -> None:
        self._cambiar_media_pantalla(
            False
        )  # Utiliza la transición común para abandonar Media pantalla o fullscreen y regresar a maximizado.

    def _cambiar_media_pantalla(
        self,
        activar: bool,
        lado: str | None = None,
    ) -> None:
        lado_objetivo = (
            lado if lado in ("izquierda", "derecha") else self.lado_media_pantalla
        )  # Utiliza la posición solicitada y conserva la anterior cuando no se proporcionó una nueva.

        if (
            activar
            and self.en_media_pantalla
            and not self.en_pantalla_completa
            and lado_objetivo == self.lado_media_pantalla
            and self._geometria_corresponde_media_pantalla(lado_objetivo)
        ):
            return  # Evita repetir una operación cuando TecNet Finder ya ocupa exactamente la mitad elegida.

        if (
            not activar
            and not self.en_media_pantalla
            and not self.en_pantalla_completa
        ):
            return  # Evita solicitar nuevamente maximizado cuando el modo dividido ya está desactivado.

        if self.transicion_ventana_activa:
            return  # Impide iniciar simultáneamente dos cambios de geometría.

        self.transicion_ventana_activa = True  # Bloquea temporalmente los demás controles de ventana.

        if activar:
            self.lado_media_pantalla = lado_objetivo  # Conserva inmediatamente la mitad elegida para todas las operaciones posteriores.

        def aplicar_estado() -> None:
            self.en_pantalla_completa = False  # Abandona fullscreen cuando el cambio se solicitó desde ese modo.

            if activar:
                self.en_media_pantalla = True  # Registra que el modo fijo 50/50 pasa a estar activo.
                self.showNormal()  # Sale de maximizado o fullscreen antes de solicitar un Snap normal de Windows.
                self._actualizar_limites_ancho_pantalla()  # Fija simultáneamente mínimo y máximo en exactamente media pantalla.
                self._habilitar_integracion_snap_windows()  # Recupera las capacidades nativas que Qt pudiera haber actualizado.
                self.barra_titulo.actualizar_estado_pantalla_completa(False)  # Recupera el control convencional de fullscreen.
                self.barra_titulo.actualizar_estado_media_pantalla(
                    True,
                    self.lado_media_pantalla,
                )  # Mantiene sincronizado el selector visual con la mitad elegida.
                QApplication.processEvents()  # Permite completar la restauración antes de solicitar Snap.
                QTimer.singleShot(
                    80,
                    self._activar_snap_media_pantalla,
                )  # Solicita el Snap cuando Windows ya reconoce nuevamente la ventana normal.
            else:
                self.en_media_pantalla = False  # Registra que se abandona el modo dividido.
                self._actualizar_limites_ancho_pantalla()  # Libera el ancho máximo antes de solicitar maximizado.
                self.showMaximized()  # Recupera el tamaño principal utilizado habitualmente.
                self._habilitar_integracion_snap_windows()  # Conserva las capacidades nativas después de cambiar de estado.
                self.barra_titulo.actualizar_estado_pantalla_completa(False)  # Mantiene fullscreen preparado para una nueva entrada.
                self.barra_titulo.actualizar_estado_media_pantalla(
                    False,
                    self.lado_media_pantalla,
                )  # Informa al selector que ninguna mitad se encuentra activa.

            self.setWindowOpacity(0.72)  # Prepara una aparición progresiva después del cambio de tamaño.

            def finalizar_transicion() -> None:
                self.setWindowOpacity(1.0)  # Garantiza que la aplicación termine completamente visible.
                self.transicion_ventana_activa = False  # Libera los controles para nuevas acciones.

            self._animar_opacidad(
                0.72,
                1.0,
                170,
                finalizar_transicion,
            )  # Hace aparecer progresivamente el nuevo estado.

        self._animar_opacidad(
            1.0,
            0.72,
            95,
            aplicar_estado,
        )  # Atenúa ligeramente la ventana antes de cambiar su geometría.

    def _activar_snap_media_pantalla(self) -> None:
        if not self.en_media_pantalla or self.en_pantalla_completa:
            return  # Cancela solicitudes antiguas cuando el usuario ya cambió nuevamente de modo.

        self._actualizar_limites_ancho_pantalla()  # Confirma nuevamente que el ancho siga fijado al 50 % antes de invocar Snap.
        snap_solicitado = self._enviar_atajo_snap(
            self.lado_media_pantalla
        )  # Solicita Win+Izquierda o Win+Derecha según la posición actualmente elegida.

        if snap_solicitado:
            QTimer.singleShot(
                450,
                self._verificar_snap_media_pantalla,
            )  # Comprueba después de la animación nativa que Windows haya aplicado la geometría esperada.
        else:
            self._aplicar_geometria_media_pantalla()  # Utiliza la geometría manual únicamente como respaldo.

    def _verificar_snap_media_pantalla(self) -> None:
        if not self.en_media_pantalla or self.en_pantalla_completa:
            return  # Evita modificar la ventana si el usuario ya abandonó el modo dividido.

        self._actualizar_limites_ancho_pantalla()  # Refuerza el ancho fijo incluso después de que Windows forme un grupo Snap.

        if self._geometria_corresponde_media_pantalla(
            self.lado_media_pantalla
        ):
            self.barra_titulo.actualizar_estado_media_pantalla(
                True,
                self.lado_media_pantalla,
            )  # Conserva sincronizado el selector cuando Snap tuvo éxito.
            return  # No altera la geometría administrada correctamente por Windows.

        self._aplicar_geometria_media_pantalla()  # Recurre al respaldo visual únicamente cuando Windows no produjo Snap.

    def _aplicar_geometria_media_pantalla(self) -> None:
        pantalla = (
            self.screen() or QApplication.primaryScreen()
        )  # Utiliza el monitor actual y recurre al principal únicamente como respaldo.

        if pantalla is None:
            return  # Evita modificar la geometría si Qt todavía no dispone de información de pantalla.

        area = pantalla.availableGeometry()  # Obtiene el escritorio utilizable excluyendo la barra de tareas.
        ancho_objetivo = area.width() // 2  # Utiliza exactamente la mitad del monitor como ancho del modo dividido.

        if self.lado_media_pantalla == "derecha":
            posicion_x = (
                area.left() + area.width() - ancho_objetivo
            )  # Calcula el comienzo exacto de la mitad derecha.
        else:
            posicion_x = area.left()  # Utiliza directamente el borde izquierdo para la primera mitad.

        self._actualizar_limites_ancho_pantalla(
            pantalla
        )  # Fija primero el mismo ancho como mínimo y máximo para evitar cambios posteriores.

        self.setGeometry(
            posicion_x,
            area.top(),
            ancho_objetivo,
            area.height(),
        )  # Coloca TecNet Finder exactamente en la mitad elegida cuando Windows no pudo realizar Snap nativo.

    def _detectar_lado_media_pantalla(self) -> str | None:
        pantalla = (
            self.screen() or QApplication.primaryScreen()
        )  # Obtiene la pantalla actual utilizada para comparar la geometría.

        if pantalla is None:
            return None  # Indica que todavía no puede analizarse la posición de la ventana.

        area = pantalla.availableGeometry()  # Obtiene el área utilizable del monitor.
        geometria_actual = self.frameGeometry()  # Obtiene la geometría real asignada a TecNet Finder.
        ancho_esperado = area.width() // 2  # Calcula la mitad horizontal esperada.
        posicion_derecha = (
            area.left() + area.width() - ancho_esperado
        )  # Calcula dónde debe comenzar la mitad derecha.
        tolerancia = 32  # Admite pequeñas diferencias producidas por escalado, bordes invisibles y animaciones de Windows.

        ancho_correcto = (
            abs(geometria_actual.width() - ancho_esperado) <= tolerancia
        )  # Comprueba que la ventana mida aproximadamente media pantalla.
        altura_correcta = (
            abs(geometria_actual.height() - area.height()) <= tolerancia
        )  # Comprueba que la ventana ocupe aproximadamente toda la altura disponible.

        if not ancho_correcto or not altura_correcta:
            return None  # Descarta cualquier geometría que no represente una media pantalla convencional.

        if abs(geometria_actual.left() - area.left()) <= tolerancia:
            return "izquierda"  # Reconoce una ventana colocada sobre el borde izquierdo.

        if abs(geometria_actual.left() - posicion_derecha) <= tolerancia:
            return "derecha"  # Reconoce una ventana colocada sobre el borde derecho.

        return None  # Descarta geometrías de media anchura que no estén alineadas con ninguno de los dos bordes.

    def _geometria_corresponde_media_pantalla(
        self,
        lado: str | None = None,
    ) -> bool:
        lado_detectado = self._detectar_lado_media_pantalla()  # Obtiene la mitad real a partir de la geometría administrada por Windows.

        if lado is None:
            return lado_detectado is not None  # Considera válida cualquiera de las dos mitades cuando no se exige una posición concreta.

        return lado_detectado == lado  # Confirma que la geometría corresponda exactamente con el lado solicitado.

    def _sincronizar_estado_media_pantalla(self) -> None:
        if self.en_pantalla_completa or self.isMinimized():
            return  # Evita interpretar fullscreen o minimizado como una geometría normal.

        if self.en_media_pantalla:
            self._actualizar_limites_ancho_pantalla()  # Mantiene bloqueado el ancho en 50 % mientras el modo propio siga activo.

            if not self._geometria_corresponde_media_pantalla(
                self.lado_media_pantalla
            ):
                QTimer.singleShot(
                    0,
                    self._aplicar_geometria_media_pantalla,
                )  # Corrige cualquier cambio externo que altere la proporción o el lado solicitado.

            return  # Conserva el modo explícitamente seleccionado desde nuestra interfaz.

        if self.isMaximized():
            self.barra_titulo.actualizar_estado_media_pantalla(
                False,
                self.lado_media_pantalla,
            )  # Mantiene el selector preparado aunque ninguna mitad esté activa.
            return  # Una ventana maximizada no requiere ninguna sincronización adicional.

        lado_detectado = self._detectar_lado_media_pantalla()  # Reconoce también un Snap ejecutado manualmente mediante Windows.

        if lado_detectado is not None:
            self.en_media_pantalla = True  # Registra que Windows colocó realmente TecNet Finder sobre una mitad.
            self.lado_media_pantalla = lado_detectado  # Conserva esa mitad como estado actual.
            self._actualizar_limites_ancho_pantalla()  # Convierte esa geometría detectada en nuestro modo fijo 50/50.
            self.barra_titulo.actualizar_estado_media_pantalla(
                True,
                self.lado_media_pantalla,
            )  # Sincroniza el selector visual con la posición detectada.

    def alternar_pantalla_completa(self) -> None:
        self._cambiar_pantalla_completa(
            not self.en_pantalla_completa
        )  # Solicita el estado contrario al utilizado actualmente.

    def entrar_pantalla_completa(self) -> None:
        self._cambiar_pantalla_completa(True)  # Indica que el estado final debe ser fullscreen.

    def salir_pantalla_completa(self) -> None:
        if self.en_pantalla_completa:
            self._cambiar_pantalla_completa(False)  # Abandona fullscreen únicamente cuando realmente se encuentra activo.

    def _cambiar_pantalla_completa(self, activar: bool) -> None:
        if activar == self.en_pantalla_completa:
            return  # Evita realizar una transición innecesaria.

        if self.transicion_ventana_activa:
            return  # Ignora nuevas solicitudes mientras otra transición continúa activa.

        self.transicion_ventana_activa = True  # Bloquea temporalmente los demás cambios de ventana.

        def aplicar_estado() -> None:
            if activar:
                self.modo_antes_pantalla_completa = (
                    "media" if self.en_media_pantalla else "maximizado"
                )  # Conserva el tamaño que debe recuperarse posteriormente.
                self.en_media_pantalla = False  # Suspende temporalmente el modo fijo de Media pantalla.
                self.en_pantalla_completa = True  # Registra que fullscreen pasa a ser el estado actual.
                self._actualizar_limites_ancho_pantalla()  # Libera el ancho máximo antes de solicitar fullscreen.
                self.showFullScreen()  # Hace que TecNet Finder ocupe completamente el monitor.
            else:
                self.en_pantalla_completa = False  # Registra primero la salida de fullscreen.

                if self.modo_antes_pantalla_completa == "media":
                    self.en_media_pantalla = True  # Recupera el modo de Media pantalla existente antes de fullscreen.
                    self.showNormal()  # Permite nuevamente que Windows gestione Snap.
                    self._actualizar_limites_ancho_pantalla()  # Fija otra vez mínimo y máximo en exactamente la mitad.
                    self._habilitar_integracion_snap_windows()  # Recupera capacidades que pudieran haberse actualizado al entrar o salir de fullscreen.
                    QApplication.processEvents()  # Completa la restauración a ventana normal.
                    QTimer.singleShot(
                        100,
                        self._restaurar_snap_media_pantalla,
                    )  # Devuelve TecNet Finder a la misma mitad utilizada antes de fullscreen.
                else:
                    self.en_media_pantalla = False  # Recupera el modo maximizado convencional.
                    self._actualizar_limites_ancho_pantalla()  # Mantiene libre el ancho máximo.
                    self.showMaximized()  # Vuelve a ocupar toda el área disponible sin ocultar la barra de tareas.
                    self._habilitar_integracion_snap_windows()  # Mantiene las capacidades nativas después del cambio.

            self.barra_titulo.actualizar_estado_pantalla_completa(
                activar
            )  # Cambia el icono y tooltip según el estado fullscreen.
            self.barra_titulo.actualizar_estado_media_pantalla(
                self.en_media_pantalla,
                self.lado_media_pantalla,
            )  # Mantiene sincronizados el selector visual y la posición actual.
            self.setWindowOpacity(0.72)  # Prepara una aparición progresiva después del cambio de geometría.

            def finalizar_transicion() -> None:
                self.setWindowOpacity(1.0)  # Garantiza que la aplicación termine totalmente visible.
                self.transicion_ventana_activa = False  # Libera nuevamente los controles de ventana.

            self._animar_opacidad(
                0.72,
                1.0,
                170,
                finalizar_transicion,
            )  # Hace aparecer progresivamente el nuevo estado.

        self._animar_opacidad(
            1.0,
            0.72,
            95,
            aplicar_estado,
        )  # Atenúa la ventana antes de cambiar su geometría.

    def _restaurar_snap_media_pantalla(self) -> None:
        if not self.en_media_pantalla or self.en_pantalla_completa:
            return  # Evita restaurar un modo que dejó de ser el solicitado.

        self._actualizar_limites_ancho_pantalla()  # Recupera exactamente el límite fijo del modo 50/50.
        self._habilitar_integracion_snap_windows()  # Comprueba nuevamente las capacidades nativas de la ventana.

        if self._geometria_corresponde_media_pantalla(
            self.lado_media_pantalla
        ):
            return  # Conserva la geometría cuando Windows ya recuperó correctamente la mitad esperada.

        self._activar_snap_media_pantalla()  # Solicita nuevamente el acoplamiento cuando la geometría se perdió.

    def changeEvent(self, evento) -> None:
        super().changeEvent(evento)  # Permite que Qt procese primero el cambio solicitado.

        if evento.type() != QEvent.Type.WindowStateChange:
            return  # Ignora eventos que no correspondan con el estado de la ventana.

        estado = self.windowState()  # Obtiene el nuevo estado asignado por Qt o Windows.
        estado_anterior = evento.oldState()  # Obtiene el estado existente antes del cambio actual.

        if (
            estado_anterior & Qt.WindowState.WindowMinimized
            and not estado & Qt.WindowState.WindowMinimized
        ):
            QTimer.singleShot(
                0,
                self._restaurar_animado,
            )  # Recupera el modo utilizado antes de minimizar.
            return

        if estado & Qt.WindowState.WindowMinimized:
            return  # Permite minimizar normalmente.

        if self.en_pantalla_completa:
            return  # Evita interferir con fullscreen solicitado explícitamente.

        if estado & Qt.WindowState.WindowMaximized:
            self.en_media_pantalla = False  # Una maximización convencional abandona cualquier Snap anterior.
            self._actualizar_limites_ancho_pantalla()  # Libera nuevamente el límite máximo.
            self.barra_titulo.actualizar_estado_media_pantalla(
                False,
                self.lado_media_pantalla,
            )  # Mantiene registrada la última mitad utilizada aunque ya no esté activa.
            QTimer.singleShot(
                0,
                self._configurar_ventana_para_pantalla_actual,
            )  # Conserva tamaño mínimo e integración Win32 después de maximizar.
            return

        QTimer.singleShot(
            120,
            self._sincronizar_estado_media_pantalla,
        )  # Permite reconocer una Media pantalla administrada directamente por Windows.

    def _restaurar_animado(self) -> None:
        if self.en_pantalla_completa:
            self._actualizar_limites_ancho_pantalla()  # Garantiza que fullscreen no conserve un máximo de media pantalla.
            self.showFullScreen()  # Recupera fullscreen cuando la aplicación fue minimizada desde ese modo.
        elif self.en_media_pantalla:
            self.showNormal()  # Recupera una ventana administrable mediante Snap.
            self._actualizar_limites_ancho_pantalla()  # Recupera mínimo y máximo fijos en media pantalla.
            self._habilitar_integracion_snap_windows()  # Garantiza la presencia de los estilos nativos.
            QTimer.singleShot(
                120,
                self._restaurar_snap_media_pantalla,
            )  # Devuelve la ventana a la misma mitad cuando sea necesario.
        else:
            self._actualizar_limites_ancho_pantalla()  # Conserva únicamente el ancho mínimo.
            self.showMaximized()  # Recupera el modo principal utilizado por defecto.
            self._habilitar_integracion_snap_windows()  # Mantiene activas las capacidades nativas.

        self.setWindowOpacity(0.55)  # Comienza la restauración parcialmente transparente.

        def finalizar_restauracion() -> None:
            self.setWindowOpacity(1.0)  # Garantiza que TecNet Finder quede completamente visible.
            self.transicion_ventana_activa = False  # Libera los controles para nuevas acciones.

        self._animar_opacidad(
            0.55,
            1.0,
            180,
            finalizar_restauracion,
        )  # Hace aparecer progresivamente la ventana restaurada.

    def activar_desde_instancia_secundaria(self) -> None:
        if self.isMinimized():
            if self.en_media_pantalla:
                self.showNormal()  # Recupera una ventana normal antes de restablecer Snap.
                self._actualizar_limites_ancho_pantalla()  # Recupera el ancho fijo correspondiente con el monitor actual.
                self._habilitar_integracion_snap_windows()  # Garantiza la integración Win32 después de restaurar.
                QTimer.singleShot(
                    120,
                    self._restaurar_snap_media_pantalla,
                )  # Recupera la misma mitad únicamente cuando corresponde.
            elif self.en_pantalla_completa:
                self._actualizar_limites_ancho_pantalla()  # Garantiza que no exista un máximo de media pantalla antes de restaurar fullscreen.
                self.showFullScreen()  # Recupera fullscreen cuando ese era el modo activo.
            else:
                self._actualizar_limites_ancho_pantalla()  # Libera cualquier límite máximo anterior.
                self.showMaximized()  # Recupera maximizado cuando ese era el modo habitual.
                self._habilitar_integracion_snap_windows()  # Conserva la compatibilidad con Snap.
        else:
            self.show()  # Garantiza que una ventana no minimizada continúe visible.

        self.setWindowOpacity(1.0)  # Evita conservar una opacidad parcial si el segundo inicio ocurrió durante una transición.
        self.raise_()  # Solicita colocar la instancia existente por encima de las demás ventanas.
        self.activateWindow()  # Solicita el foco de entrada para continuar trabajando en la instancia original.

        manejador = self.windowHandle()  # Obtiene la representación nativa de la ventana cuando ya existe.

        if manejador is not None:
            manejador.requestActivate()  # Solicita adicionalmente a Windows la activación de la instancia existente.

    def _analizar_codigo(self) -> None:
        codigo_fuente = self.editor_codigo.toPlainText()  # Recupera exactamente lo escrito por el usuario.

        if not codigo_fuente.strip():
            QMessageBox.warning(
                self,
                "Entrada vacía",
                "Introduce una instrucción de TecNet Finder antes de compilar.",
            )  # Informa el problema sin ejecutar el flujo.
            return

        try:
            resultado = self.flujo.analizar(codigo_fuente)  # Ejecuta las etapas actualmente disponibles mediante Motor.
        except Exception as error:
            self._limpiar_resultados_conservando_entrada()  # Elimina resultados anteriores para no mostrar información obsoleta.
            self._mostrar_estado_error_interno()  # Deja visible un estado coherente mientras se informa el fallo inesperado.
            QMessageBox.critical(
                self,
                "Error interno",
                f"No se pudo completar el análisis:\n{error}",
            )  # Muestra el problema sin cerrar TecNet Finder.
            return

        self.ultimo_resultado = resultado  # Conserva el resultado global más reciente.
        self.panel_diagnosticos.mostrar_diagnosticos(
            resultado.diagnosticos
        )  # Actualiza la tabla estructurada de errores y advertencias.
        self.editor_codigo.mostrar_diagnosticos(
            resultado.diagnosticos
        )  # Dibuja los mismos diagnósticos directamente sobre el código fuente.
        self.panel_resultados.mostrar_resultado(
            resultado
        )  # Actualiza resumen, tablas y vistas sintácticas.
        self._actualizar_estado(resultado)  # Actualiza la barra superior de estado.

    def _actualizar_estado(self, resultado) -> None:
        cantidad_errores = sum(
            1
            for diagnostico in resultado.diagnosticos
            if diagnostico.severidad == "error"
        )  # Cuenta únicamente diagnósticos clasificados como error.
        cantidad_advertencias = sum(
            1
            for diagnostico in resultado.diagnosticos
            if diagnostico.severidad in ("warning", "advertencia")
        )  # Cuenta recomendaciones no bloqueantes.
        cantidad_subredes = len(resultado.subredes_vlsm)  # Obtiene la cantidad de subredes calculadas.

        if cantidad_errores > 0:
            self.etiqueta_estado.setObjectName("EstadoError")  # Aplica el estilo rojo correspondiente.
            self.etiqueta_estado.setText(
                f"Análisis terminado con errores: {cantidad_errores} error(es) | "
                f"Advertencias: {cantidad_advertencias} | "
                f"Subredes generadas: {cantidad_subredes}"
            )
        elif cantidad_advertencias > 0:
            self.etiqueta_estado.setObjectName("EstadoAdvertencia")  # Aplica el estado amarillo.
            self.etiqueta_estado.setText(
                f"Análisis completo con advertencias: {cantidad_advertencias} | "
                f"Bloques válidos: {len(resultado.bloques_validos)} | "
                f"Subredes generadas: {cantidad_subredes}"
            )
        else:
            self.etiqueta_estado.setObjectName("EstadoCorrecto")  # Aplica el estilo positivo.
            self.etiqueta_estado.setText(
                f"Análisis completo | "
                f"Bloques válidos: {len(resultado.bloques_validos)} | "
                f"Subredes generadas: {cantidad_subredes}"
            )

        self.etiqueta_estado.style().unpolish(
            self.etiqueta_estado
        )  # Retira temporalmente el formato anterior.
        self.etiqueta_estado.style().polish(
            self.etiqueta_estado
        )  # Aplica nuevamente la hoja de estilos.
        self.etiqueta_estado.update()  # Solicita el redibujado inmediato del estado.

    def _ir_a_diagnostico(self, diagnostico) -> None:
        self.editor_codigo.ir_a_posicion(
            diagnostico.linea,
            diagnostico.columna,
            diagnostico.longitud,
        )  # Utiliza directamente los datos estructurados del diagnóstico.

    def _restablecer_estado_neutral(self) -> None:
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Recupera el estilo inicial de la barra de estado.
        self.etiqueta_estado.setText("Sin análisis ejecutado.")  # Recupera el mensaje mostrado antes de compilar.
        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira temporalmente el estilo anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente el estilo neutral.
        self.etiqueta_estado.update()  # Redibuja inmediatamente el mensaje.

    def _mostrar_estado_error_interno(self) -> None:
        self.etiqueta_estado.setObjectName("EstadoError")  # Utiliza el mismo estilo rojo empleado por los diagnósticos normales.
        self.etiqueta_estado.setText(
            "Análisis interrumpido por un error interno."
        )  # Indica que los resultados visibles fueron descartados por seguridad.
        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira el estilo anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica inmediatamente el estado de error.
        self.etiqueta_estado.update()  # Solicita el redibujado antes de mostrar el cuadro modal.

    def _limpiar_resultados_conservando_entrada(self) -> None:
        self.editor_codigo.limpiar_diagnosticos()  # Elimina cualquier onda perteneciente al análisis anterior.
        self.panel_diagnosticos.limpiar()  # Vacía la tabla estructurada de errores y advertencias.
        self.panel_resultados.limpiar()  # Restaura resumen, tablas, sintaxis y acciones asociadas con resultados.
        self.ultimo_resultado = None  # Descarta la compilación que dejó de corresponder con la entrada.
        self._restablecer_estado_neutral()  # Recupera el estado general previo a una compilación.
        self.editor_codigo.setFocus()  # Permite continuar inmediatamente con los ejemplos insertados.

    def _limpiar_todo(self) -> None:
        self.editor_codigo.limpiar_diagnosticos()  # Elimina primero las marcas onduladas de la compilación anterior.
        self.editor_codigo.clear()  # Elimina completamente el código fuente.
        self.panel_diagnosticos.limpiar()  # Elimina los diagnósticos anteriores.
        self.panel_resultados.limpiar()  # Restaura resumen, tablas y sintaxis.
        self.ultimo_resultado = None  # Descarta el resultado de la compilación anterior.
        self._restablecer_estado_neutral()  # Recupera el mensaje y estilo utilizados al iniciar.
        self.editor_codigo.setFocus()  # Devuelve el cursor al editor para comenzar otra entrada.

    def closeEvent(self, evento) -> None:
        if self.cierre_autorizado:
            evento.accept()  # Permite que Qt cierre definitivamente TecNet Finder.
            return

        evento.ignore()  # Detiene temporalmente el cierre solicitado para reproducir primero la animación.

        if self.transicion_ventana_activa:
            return  # Evita iniciar dos animaciones simultáneamente.

        self.transicion_ventana_activa = True  # Bloquea los controles durante los últimos milisegundos de la aplicación.

        def finalizar_cierre() -> None:
            self.cierre_autorizado = True  # Indica que la siguiente solicitud de cierre ya puede aceptarse.
            self.close()  # Solicita nuevamente el cierre, que ahora pasará directamente por closeEvent.

        self._animar_opacidad(
            1.0,
            0.0,
            160,
            finalizar_cierre,
        )  # Desvanece progresivamente la aplicación antes de cerrarla.