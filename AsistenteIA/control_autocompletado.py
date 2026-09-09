# ============================================================
# Archivo: control_autocompletado.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo coordina el autocompletado local sin bloquear la
# interfaz gráfica de TecNet Finder.
#
# Espera una breve pausa al escribir, ejecuta la predicción en
# segundo plano, descarta respuestas obsoletas y otorga prioridad
# a Escape cuando existe un ghost text visible.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot  # Importa eventos, temporización, señales y ejecución en segundo plano.

from AsistenteIA.predictor_codigo import PredictorCodigo  # Importa el predictor que combina IA con validación formal.


class SenalesPrediccion(QObject):  # Define el canal seguro utilizado para regresar desde un hilo secundario.
    terminada = Signal(int, str, object)  # Envía identificador, prefijo original y sugerencia obtenida.


class TrabajoPrediccion(QRunnable):  # Ejecuta una consulta al predictor sin ocupar el hilo gráfico.
    def __init__(self, identificador: int, prefijo: str, predictor: PredictorCodigo):
        super().__init__()  # Inicializa el trabajo administrado por QThreadPool.
        self.identificador = identificador  # Conserva la versión de la solicitud.
        self.prefijo = prefijo  # Conserva exactamente el texto que originó la petición.
        self.predictor = predictor  # Reutiliza el predictor configurado.
        self.senales = SenalesPrediccion()  # Crea el canal utilizado para devolver la respuesta.

    @Slot()
    def run(self) -> None:
        try:
            sugerencia = self.predictor.sugerir(self.prefijo)  # Consulta el modelo y deja que lexer y parser aprueben o rechacen.
        except Exception:
            sugerencia = None  # Trata cualquier fallo inesperado como ausencia de autocompletado.

        self.senales.terminada.emit(self.identificador, self.prefijo, sugerencia)  # Regresa el resultado sin modificar widgets desde el hilo secundario.


class ControlAutocompletado(QObject):  # Administra debounce, concurrencia, cancelación y prioridad del teclado.
    sugerencia_lista = Signal(str, str)  # Informa al editor qué prefijo produjo una continuación válida.

    def __init__(self, padre=None, predictor: PredictorCodigo | None = None, demora_ms: int = 500):
        super().__init__(padre)  # Asocia el ciclo de vida del controlador con el editor propietario.
        self.editor = padre  # Conserva el editor para interceptar Escape cuando exista una sugerencia.
        self.predictor = predictor or PredictorCodigo()  # Utiliza el predictor real salvo en pruebas.
        self.demora_ms = demora_ms  # Mantiene una breve pausa para no consultar el modelo después de cada tecla.
        self.prefijo_pendiente = ""  # Conserva el texto asociado con la solicitud más reciente.
        self.identificador_solicitud = 0  # Aumenta con cada cambio para invalidar respuestas anteriores.

        self.temporizador = QTimer(self)  # Crea el temporizador utilizado como debounce.
        self.temporizador.setSingleShot(True)  # Ejecuta una única consulta después de cada pausa.
        self.temporizador.setInterval(self.demora_ms)  # Configura cuánto tiempo debe dejar de escribir el usuario.
        self.temporizador.timeout.connect(self._iniciar_prediccion)  # Lanza el trabajo cuando finaliza la pausa.

        self.hilos = QThreadPool(self)  # Mantiene las solicitudes fuera de la interfaz.
        self.hilos.setMaxThreadCount(1)  # Evita ejecutar varias generaciones simultáneas.

        if self.editor is not None:
            self.editor.installEventFilter(self)  # Permite reclamar Escape antes del atajo global de la ventana principal.

    def programar(self, prefijo: str) -> None:
        self.identificador_solicitud += 1  # Invalida cualquier respuesta asociada con una versión anterior.
        self.prefijo_pendiente = prefijo  # Conserva el texto exacto que deberá completarse.
        self.temporizador.stop()  # Reinicia la espera cada vez que el usuario continúa escribiendo.

        if not prefijo.strip():
            return  # Evita utilizar recursos para entradas sin contenido significativo.

        self.temporizador.start()  # Comienza una nueva espera antes de consultar la IA.

    def cancelar(self) -> None:
        self.identificador_solicitud += 1  # Hace obsoleta cualquier generación todavía ejecutándose.
        self.prefijo_pendiente = ""  # Elimina el contexto que ya no debe recibir sugerencia.
        self.temporizador.stop()  # Impide que una petición todavía no iniciada llegue al modelo.

    def eventFilter(self, objeto, evento):
        if objeto is self.editor and evento.type() == QEvent.Type.ShortcutOverride:
            if evento.key() == Qt.Key.Key_Escape and self._hay_sugerencia_visible():
                evento.accept()  # Reclama Escape para impedir que el QShortcut global lo consuma.
                return True

        if objeto is self.editor and evento.type() == QEvent.Type.KeyPress:
            if evento.key() == Qt.Key.Key_Escape and self._hay_sugerencia_visible():
                self.cancelar()  # Invalida cualquier respuesta pendiente relacionada con el mismo texto.
                ocultar = getattr(self.editor, "_ocultar_sugerencia_ia", None)  # Obtiene la acción visual implementada por el editor.

                if callable(ocultar):
                    ocultar()  # Retira inmediatamente el ghost text sin modificar el documento.

                evento.accept()  # Marca la pulsación como procesada.
                return True

        return super().eventFilter(objeto, evento)  # Mantiene intacto el comportamiento de los demás eventos.

    def _hay_sugerencia_visible(self) -> bool:
        if self.editor is None:
            return False  # No puede existir ghost text sin editor asociado.

        return bool(getattr(self.editor, "sugerencia_ia", ""))  # Consulta si existe una continuación virtual visible.

    def _iniciar_prediccion(self) -> None:
        prefijo = self.prefijo_pendiente  # Copia el texto para evitar depender de modificaciones posteriores.
        identificador = self.identificador_solicitud  # Copia también la versión utilizada para comprobar vigencia.

        if not prefijo.strip():
            return  # Evita crear un trabajo si la solicitud fue cancelada.

        trabajo = TrabajoPrediccion(identificador, prefijo, self.predictor)  # Prepara una única generación.
        trabajo.senales.terminada.connect(self._recibir_prediccion)  # Conecta la respuesta con la comprobación de vigencia.
        self.hilos.start(trabajo)  # Entrega la operación al hilo secundario.

    @Slot(int, str, object)
    def _recibir_prediccion(self, identificador: int, prefijo: str, sugerencia) -> None:
        if identificador != self.identificador_solicitud:
            return  # Descarta respuestas terminadas después de que el usuario cambió la entrada.

        if prefijo != self.prefijo_pendiente:
            return  # Mantiene una segunda barrera frente a respuestas de otro texto.

        if not isinstance(sugerencia, str) or not sugerencia:
            return  # No muestra nada cuando no existe continuación aprobada.

        self.sugerencia_lista.emit(prefijo, sugerencia)  # Entrega al editor únicamente una respuesta vigente y válida.