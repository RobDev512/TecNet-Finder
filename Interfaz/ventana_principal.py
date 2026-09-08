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
# La ventana utiliza una barra de título personalizada y solo
# permite trabajar maximizada o en modo de pantalla completa.
# ============================================================

from pathlib import Path  # Importa Path para localizar los recursos del proyecto sin depender de rutas absolutas.

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QTimer, Qt  # Importa eventos, animaciones y estados utilizados para controlar suavemente la ventana.
from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut  # Importa iconos, atajos de teclado e imágenes.
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget  # Importa los componentes principales utilizados por la ventana.

from Interfaz.barra_titulo import BarraTitulo  # Importa la barra personalizada que sustituye la barra estándar de Windows.
from Interfaz.editor_codigo import EditorCodigo  # Importa el editor especializado con números de línea, diagnósticos y acciones flotantes.
from Interfaz.panel_diagnosticos import PanelDiagnosticos  # Importa la tabla estructurada de errores y advertencias.
from Interfaz.panel_resultados import PanelResultados  # Importa el área de trabajo organizada según la interfaz original.
from Interfaz.resaltador_sintaxis import ResaltadorSintaxis  # Importa el resaltador visual del lenguaje TecNet Finder.
from Motor.flujo_compilacion import FlujoCompilacion  # Importa el coordinador central de las fases disponibles.


class VentanaPrincipal(QMainWindow):  # Define la ventana principal y controla sus dos estados permitidos.
    def __init__(self):  # Inicializa la aplicación, sus componentes y su comportamiento de ventana.
        super().__init__()  # Inicializa el comportamiento base de QMainWindow.
        self.flujo = FlujoCompilacion()  # Crea el coordinador encargado de ejecutar las fases reconstruidas.
        self.ultimo_resultado = None  # Reserva una referencia para conservar el resultado más reciente.
        self.en_pantalla_completa = False  # Indica si actualmente se está utilizando el modo fullscreen.
        self.transicion_ventana_activa = False  # Impide iniciar varias animaciones de ventana simultáneamente.
        self.animacion_opacidad = None  # Conserva la animación activa para evitar que Python la elimine antes de terminar.
        self.cierre_autorizado = False  # Permite distinguir el cierre animado inicial del cierre definitivo.

        self.setWindowTitle("TecNet Finder")  # Conserva el nombre utilizado por Windows y la barra de tareas.
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)  # Elimina la barra estándar de Windows para sustituirla por la propia.
        self.setMinimumSize(1000, 650)  # Evita dimensiones poco utilizables durante cambios de estado internos.

        self._cargar_icono()  # Carga el icono oficial desde Recursos.
        self._construir_interfaz()  # Construye la barra propia y el contenido de la aplicación.
        self._configurar_atajos()  # Activa F11 y Escape para controlar fullscreen.

    def _ruta_recurso(self, nombre_archivo: str) -> Path:  # Construye la ubicación de un recurso partiendo del propio proyecto.
        raiz_proyecto = Path(__file__).resolve().parent.parent  # Obtiene la carpeta raíz de TecNet Finder.
        return raiz_proyecto / "Recursos" / nombre_archivo  # Devuelve la ruta correspondiente al recurso solicitado.

    def _cargar_icono(self) -> None:  # Carga el icono usado por Windows y por la barra personalizada.
        ruta_icono = self._ruta_recurso("LogoTNF.ico")  # Obtiene la ubicación del archivo ICO existente.

        if ruta_icono.exists():  # Comprueba que el recurso esté disponible antes de utilizarlo.
            self.setWindowIcon(QIcon(str(ruta_icono)))  # Establece el icono general de la ventana.

    def _construir_interfaz(self) -> None:  # Construye toda la ventana sin incluir lógica de compilación.
        central = QWidget()  # Crea el widget raíz que ocupará toda la ventana sin marco.
        central.setObjectName("VentanaCentral")  # Permite aplicar el fondo general desde estilos.py.
        self.setCentralWidget(central)  # Asigna el widget como contenido principal.

        diseno_general = QVBoxLayout(central)  # Organiza barra personalizada y contenido de forma vertical.
        diseno_general.setContentsMargins(0, 0, 0, 0)  # Permite que la barra llegue exactamente a los bordes de la pantalla.
        diseno_general.setSpacing(0)  # Evita cualquier separación entre barra y contenido.

        self.barra_titulo = BarraTitulo(self, self._ruta_recurso("LogoTNF.ico"))  # Crea la barra propia utilizando el mismo icono de la aplicación.
        diseno_general.addWidget(self.barra_titulo)  # Coloca la barra personalizada en la parte superior permanente.

        contenido = QWidget()  # Crea el contenedor donde se mostrará realmente TecNet Finder.
        contenido.setObjectName("ContenidoPrincipal")  # Permite diferenciarlo de la barra superior.
        diseno_contenido = QVBoxLayout(contenido)  # Organiza encabezado, estado y pestañas.
        diseno_contenido.setContentsMargins(14, 10, 14, 14)  # Mantiene el espacio visual utilizado por la interfaz actual.
        diseno_contenido.setSpacing(9)  # Define una separación uniforme entre las secciones.

        self._construir_encabezado(diseno_contenido)  # Agrega el logotipo y nombre grande utilizados por la versión anterior.

        self.etiqueta_estado = QLabel("Sin análisis ejecutado.")  # Crea la barra informativa situada debajo del encabezado.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Aplica inicialmente el estado visual neutro.
        diseno_contenido.addWidget(self.etiqueta_estado)  # Coloca el estado encima del área principal de pestañas.

        self.editor_codigo = EditorCodigo()  # Crea el editor especializado de TecNet Finder.
        self.resaltador_sintaxis = ResaltadorSintaxis(self.editor_codigo.document())  # Conecta el resaltador con el documento del editor.
        self.panel_diagnosticos = PanelDiagnosticos()  # Crea la tabla estructurada de errores y advertencias.

        self.panel_resultados = PanelResultados(  # Construye el área de trabajo completa utilizando el acomodo inspirado en LyA I.
            editor_codigo=self.editor_codigo,
            panel_diagnosticos=self.panel_diagnosticos,
            accion_analizar=self._analizar_codigo,
            accion_limpiar=self._limpiar_todo,
        )

        diseno_contenido.addWidget(self.panel_resultados, 1)  # Permite que las pestañas utilicen todo el espacio restante.
        diseno_general.addWidget(contenido, 1)  # Coloca el contenido debajo de la barra personalizada.

        self.panel_diagnosticos.diagnostico_activado.connect(self._ir_a_diagnostico)  # Permite navegar desde un diagnóstico hasta el código fuente.
        self.editor_codigo.ejemplos_insertados.connect(self._limpiar_resultados_conservando_entrada)  # Descarta resultados antiguos después de insertar casos desde el selector.

    def _construir_encabezado(self, diseno_principal: QVBoxLayout) -> None:  # Construye el encabezado grande conservado de la interfaz anterior.
        encabezado = QHBoxLayout()  # Organiza horizontalmente logotipo y textos.
        encabezado.setSpacing(12)  # Mantiene una separación cómoda entre ambos elementos.
        ruta_logo = self._ruta_recurso("LogoTNF.png")  # Obtiene la ruta del logotipo de mayor resolución.

        if ruta_logo.exists():  # Comprueba que el recurso realmente se encuentre disponible.
            etiqueta_logo = QLabel()  # Crea el contenedor de la imagen.
            imagen = QPixmap(str(ruta_logo)).scaled(58, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Reduce el logotipo conservando calidad y proporción.
            etiqueta_logo.setPixmap(imagen)  # Coloca la imagen escalada.
            encabezado.addWidget(etiqueta_logo)  # Agrega el logotipo al lado izquierdo.

        caja_titulos = QVBoxLayout()  # Crea una columna para nombre y descripción.
        titulo = QLabel("TecNet Finder")  # Crea el nombre principal del proyecto.
        titulo.setObjectName("TituloPrincipal")  # Aplica el estilo utilizado para el título grande.
        subtitulo = QLabel("Compilador para análisis de instrucciones VLSM")  # Conserva la descripción breve del proyecto.
        subtitulo.setObjectName("SubtituloPrincipal")  # Aplica el estilo secundario.

        caja_titulos.addWidget(titulo)  # Coloca el nombre como primera línea.
        caja_titulos.addWidget(subtitulo)  # Coloca la descripción debajo.
        encabezado.addLayout(caja_titulos)  # Agrega ambos textos al encabezado.
        encabezado.addStretch()  # Mantiene el conjunto alineado hacia la izquierda.
        diseno_principal.addLayout(encabezado)  # Inserta el encabezado en el contenido principal.

    def _configurar_atajos(self) -> None:  # Registra los controles rápidos relacionados con la ventana.
        self.atajo_pantalla_completa = QShortcut(QKeySequence("F11"), self)  # Crea el atajo convencional utilizado para fullscreen.
        self.atajo_pantalla_completa.activated.connect(self.alternar_pantalla_completa)  # Hace que F11 alterne los dos estados permitidos.

        self.atajo_salir_pantalla_completa = QShortcut(QKeySequence("Escape"), self)  # Permite utilizar Escape para abandonar fullscreen.
        self.atajo_salir_pantalla_completa.activated.connect(self.salir_pantalla_completa)  # Solo realiza cambios cuando fullscreen está activo.

    def _animar_opacidad(self, inicio: float, fin: float, duracion: int, al_terminar=None) -> None:  # Ejecuta una transición suave sobre la opacidad general.
        if self.animacion_opacidad is not None:  # Comprueba si todavía existe una animación anterior almacenada.
            self.animacion_opacidad.stop()  # Detiene la animación anterior para evitar que ambas controlen la misma propiedad.

        self.setWindowOpacity(inicio)  # Coloca inmediatamente la ventana en la opacidad inicial.

        self.animacion_opacidad = QPropertyAnimation(self, b"windowOpacity", self)  # Crea una animación sobre la opacidad de la ventana.
        self.animacion_opacidad.setDuration(duracion)  # Define cuántos milisegundos durará la transición.
        self.animacion_opacidad.setStartValue(inicio)  # Define la opacidad inicial.
        self.animacion_opacidad.setEndValue(fin)  # Define la opacidad final.
        self.animacion_opacidad.setEasingCurve(QEasingCurve.Type.InOutCubic)  # Utiliza aceleración y desaceleración progresivas.

        if al_terminar is not None:  # Comprueba si debe ejecutarse alguna acción al concluir la animación.
            self.animacion_opacidad.finished.connect(al_terminar)  # Ejecuta la acción al finalizar la transición.

        self.animacion_opacidad.start()  # Inicia la animación configurada.

    def minimizar_animado(self) -> None:  # Minimiza TecNet Finder después de una transición visual breve.
        if self.transicion_ventana_activa:  # Comprueba que otro cambio de estado no se encuentre ejecutándose.
            return  # Ignora clics adicionales hasta terminar la transición.

        self.transicion_ventana_activa = True  # Bloquea temporalmente otras transiciones de ventana.

        def finalizar_minimizado() -> None:  # Ejecuta el cambio real de estado después del desvanecimiento.
            self.showMinimized()  # Envía finalmente TecNet Finder hacia la barra de tareas.
            self.setWindowOpacity(1.0)  # Deja preparada la opacidad normal para cuando la ventana vuelva a mostrarse.
            self.transicion_ventana_activa = False  # Permite nuevamente utilizar los controles de ventana.

        self._animar_opacidad(1.0, 0.35, 130, finalizar_minimizado)  # Reduce rápidamente la presencia visual antes de minimizar.

    def alternar_pantalla_completa(self) -> None:  # Alterna suavemente entre maximizado y pantalla completa.
        self._cambiar_pantalla_completa(not self.en_pantalla_completa)  # Solicita el estado contrario al utilizado actualmente.

    def entrar_pantalla_completa(self) -> None:  # Solicita entrar a pantalla completa utilizando la transición común.
        self._cambiar_pantalla_completa(True)  # Indica que el estado final debe ser fullscreen.

    def salir_pantalla_completa(self) -> None:  # Solicita regresar al modo maximizado.
        self._cambiar_pantalla_completa(False)  # Indica que el estado final debe ser maximizado.

    def _cambiar_pantalla_completa(self, activar: bool) -> None:  # Realiza la transición visual y modifica después el estado real.
        if activar == self.en_pantalla_completa:  # Comprueba si la ventana ya se encuentra en el estado solicitado.
            return  # Evita realizar una transición innecesaria.

        if self.transicion_ventana_activa:  # Comprueba si todavía se está ejecutando otro movimiento.
            return  # Ignora nuevas solicitudes hasta finalizar la transición anterior.

        self.transicion_ventana_activa = True  # Bloquea temporalmente los demás cambios de estado.

        def aplicar_estado() -> None:  # Cambia realmente el estado una vez concluida la primera parte.
            self.en_pantalla_completa = activar  # Actualiza el estado lógico antes de modificar la ventana.

            if activar:  # Comprueba si el destino solicitado es pantalla completa.
                self.showFullScreen()  # Hace que TecNet Finder ocupe completamente el monitor.
            else:  # Se ejecuta cuando se desea volver al modo habitual.
                self.showMaximized()  # Regresa directamente al estado maximizado obligatorio.

            self.barra_titulo.actualizar_estado_pantalla_completa(activar)  # Actualiza la ayuda del botón según su nueva función.
            self.setWindowOpacity(0.72)  # Prepara una aparición progresiva después del cambio de geometría.

            def finalizar_transicion() -> None:  # Finaliza completamente el cambio de estado.
                self.setWindowOpacity(1.0)  # Garantiza que la aplicación termine totalmente visible.
                self.transicion_ventana_activa = False  # Libera nuevamente los controles de ventana.

            self._animar_opacidad(0.72, 1.0, 170, finalizar_transicion)  # Hace aparecer progresivamente el nuevo estado.

        self._animar_opacidad(1.0, 0.72, 95, aplicar_estado)  # Atenúa ligeramente la ventana antes de cambiar su geometría.

    def changeEvent(self, evento) -> None:  # Vigila cambios externos para impedir que TecNet Finder permanezca en modo ventana normal.
        super().changeEvent(evento)  # Permite que Qt procese primero el cambio solicitado.

        if evento.type() != QEvent.Type.WindowStateChange:  # Comprueba que el evento realmente corresponda al estado de la ventana.
            return  # Ignora otros tipos de evento.

        if self.en_pantalla_completa:  # Evita interferir con fullscreen solicitado explícitamente.
            return  # Mantiene el estado actual.

        estado = self.windowState()  # Obtiene el nuevo estado asignado por Qt o Windows.
        estado_anterior = evento.oldState()  # Obtiene el estado existente antes del cambio actual.

        if estado_anterior & Qt.WindowState.WindowMinimized and not estado & Qt.WindowState.WindowMinimized:  # Detecta que TecNet Finder regresó desde la barra de tareas.
            QTimer.singleShot(0, self._restaurar_animado)  # Espera a que Windows termine de restaurar para aplicar la transición.
            return  # Evita ejecutar al mismo tiempo la corrección general.

        if estado & Qt.WindowState.WindowMinimized:  # Comprueba si el usuario simplemente minimizó la aplicación.
            return  # Permite minimizar normalmente.

        if estado & Qt.WindowState.WindowMaximized:  # Comprueba si la ventana ya está en el modo permitido.
            return  # No hace falta realizar ninguna corrección.

        if self.isVisible():  # Comprueba que la ventana realmente esté mostrada.
            QTimer.singleShot(0, self.showMaximized)  # Devuelve cualquier intento de restauración al estado maximizado.

    def _restaurar_animado(self) -> None:  # Recupera TecNet Finder desde la barra de tareas con una aparición progresiva.
        self.showMaximized()  # Garantiza que la aplicación regrese directamente al único tamaño normal permitido.
        self.setWindowOpacity(0.55)  # Comienza la restauración parcialmente transparente.

        def finalizar_restauracion() -> None:  # Finaliza la transición después de recuperar completamente la ventana.
            self.setWindowOpacity(1.0)  # Garantiza que TecNet Finder quede completamente visible.
            self.transicion_ventana_activa = False  # Libera los controles para nuevas acciones.

        self._animar_opacidad(0.55, 1.0, 180, finalizar_restauracion)  # Hace aparecer progresivamente la ventana restaurada.

    def _analizar_codigo(self) -> None:  # Obtiene la entrada y ejecuta el flujo actual de TecNet Finder.
        codigo_fuente = self.editor_codigo.toPlainText()  # Recupera exactamente lo escrito por el usuario.

        if not codigo_fuente.strip():  # Comprueba que la entrada contenga información real.
            QMessageBox.warning(self, "Entrada vacía", "Introduce una instrucción de TecNet Finder antes de compilar.")  # Informa el problema sin ejecutar el flujo.
            return  # Finaliza la acción actual.

        try:  # Protege la interfaz frente a una excepción interna todavía no representada mediante Diagnostico.
            resultado = self.flujo.analizar(codigo_fuente)  # Ejecuta las etapas actualmente disponibles mediante Motor.
        except Exception as error:  # Captura únicamente fallos inesperados del propio programa.
            QMessageBox.critical(self, "Error interno", f"No se pudo completar el análisis:\n{error}")  # Muestra el problema sin cerrar TecNet Finder.
            return  # Mantiene disponible la aplicación.

        self.ultimo_resultado = resultado  # Conserva el resultado global más reciente.
        self.panel_diagnosticos.mostrar_diagnosticos(resultado.diagnosticos)  # Actualiza la tabla estructurada de errores y advertencias.
        self.editor_codigo.mostrar_diagnosticos(resultado.diagnosticos)  # Dibuja los mismos diagnósticos directamente sobre el código fuente.
        self.panel_resultados.mostrar_resultado(resultado)  # Actualiza resumen, tablas y vistas sintácticas.
        self._actualizar_estado(resultado)  # Actualiza la barra superior de estado.

    def _actualizar_estado(self, resultado) -> None:  # Cambia el mensaje general distinguiendo errores, advertencias y resultados completamente limpios.
        cantidad_errores = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad == "error")  # Cuenta únicamente diagnósticos clasificados como error.
        cantidad_advertencias = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia"))  # Cuenta recomendaciones no bloqueantes.
        cantidad_subredes = len(resultado.subredes_vlsm)  # Obtiene la cantidad de subredes que sí pudieron calcularse.

        if cantidad_errores > 0:  # Da prioridad al estado de error cuando existe al menos un problema real.
            self.etiqueta_estado.setObjectName("EstadoError")  # Aplica el estilo rojo correspondiente.
            self.etiqueta_estado.setText(
                f"Análisis terminado con errores: {cantidad_errores} error(es) | "
                f"Advertencias: {cantidad_advertencias} | "
                f"Subredes generadas: {cantidad_subredes}"
            )
        elif cantidad_advertencias > 0:  # Comprueba si el resultado es válido pero contiene recomendaciones.
            self.etiqueta_estado.setObjectName("EstadoAdvertencia")  # Aplica el nuevo estado amarillo.
            self.etiqueta_estado.setText(
                f"Análisis completo con advertencias: {cantidad_advertencias} | "
                f"Bloques válidos: {len(resultado.bloques_validos)} | "
                f"Subredes generadas: {cantidad_subredes}"
            )
        else:  # Se ejecuta únicamente cuando la compilación quedó completamente limpia.
            self.etiqueta_estado.setObjectName("EstadoCorrecto")  # Aplica el estilo positivo.
            self.etiqueta_estado.setText(
                f"Análisis completo | "
                f"Bloques válidos: {len(resultado.bloques_validos)} | "
                f"Subredes generadas: {cantidad_subredes}"
            )

        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira temporalmente el formato anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente la hoja de estilos.
        self.etiqueta_estado.update()  # Solicita el redibujado inmediato del estado.

    def _ir_a_diagnostico(self, diagnostico) -> None:  # Permite navegar al código desde una fila de error.
        self.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Utiliza directamente los datos estructurados del diagnóstico.

    def _restablecer_estado_neutral(self) -> None:  # Recupera la apariencia utilizada cuando todavía no existe una compilación vigente.
        self.etiqueta_estado.setObjectName("EstadoNeutral")  # Recupera el estilo inicial de la barra de estado.
        self.etiqueta_estado.setText("Sin análisis ejecutado.")  # Recupera el mensaje mostrado antes de compilar.
        self.etiqueta_estado.style().unpolish(self.etiqueta_estado)  # Retira temporalmente el estilo anterior.
        self.etiqueta_estado.style().polish(self.etiqueta_estado)  # Aplica nuevamente el estilo neutral.
        self.etiqueta_estado.update()  # Redibuja inmediatamente el mensaje.

    def _limpiar_resultados_conservando_entrada(self) -> None:  # Descarta resultados anteriores sin eliminar los ejemplos recién insertados.
        self.editor_codigo.limpiar_diagnosticos()  # Elimina cualquier onda perteneciente al análisis anterior.
        self.panel_diagnosticos.limpiar()  # Vacía la tabla estructurada de errores y advertencias.
        self.panel_resultados.limpiar()  # Restaura resumen, tablas, sintaxis y acciones asociadas con resultados.
        self.ultimo_resultado = None  # Descarta la compilación que dejó de corresponder con la entrada.
        self._restablecer_estado_neutral()  # Recupera el estado general previo a una compilación.
        self.editor_codigo.setFocus()  # Permite continuar inmediatamente con los ejemplos insertados.

    def _limpiar_todo(self) -> None:  # Restaura entrada y salidas sin modificar el estado de la ventana.
        self.editor_codigo.limpiar_diagnosticos()  # Elimina primero las marcas onduladas de la compilación anterior.
        self.editor_codigo.clear()  # Elimina completamente el código fuente.
        self.panel_diagnosticos.limpiar()  # Elimina los diagnósticos anteriores.
        self.panel_resultados.limpiar()  # Restaura resumen, tablas y sintaxis.
        self.ultimo_resultado = None  # Descarta el resultado de la compilación anterior.
        self._restablecer_estado_neutral()  # Recupera el mensaje y estilo utilizados al iniciar.
        self.editor_codigo.setFocus()  # Devuelve el cursor al editor para comenzar otra entrada.

    def closeEvent(self, evento) -> None:  # Intercepta el cierre para reproducir una animación antes de destruir la ventana.
        if self.cierre_autorizado:  # Comprueba si la animación de cierre ya terminó anteriormente.
            evento.accept()  # Permite que Qt cierre definitivamente TecNet Finder.
            return  # Evita comenzar otra animación durante el cierre final.

        evento.ignore()  # Detiene temporalmente el cierre solicitado para poder animarlo primero.

        if self.transicion_ventana_activa:  # Comprueba si ya existe otra transición ejecutándose.
            return  # Evita iniciar dos animaciones simultáneamente.

        self.transicion_ventana_activa = True  # Bloquea los controles durante los últimos milisegundos de la aplicación.

        def finalizar_cierre() -> None:  # Ejecuta el cierre definitivo una vez terminado el desvanecimiento.
            self.cierre_autorizado = True  # Indica que la siguiente solicitud de cierre ya puede aceptarse.
            self.close()  # Solicita nuevamente el cierre, que ahora pasará directamente por closeEvent.

        self._animar_opacidad(1.0, 0.0, 160, finalizar_cierre)  # Desvanece progresivamente la aplicación antes de cerrarla.