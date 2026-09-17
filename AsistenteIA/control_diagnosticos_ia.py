# ============================================================
# Archivo: control_diagnosticos_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo coordina la mejora automática de soluciones de
# diagnósticos mediante la IA local sin bloquear la interfaz.
#
# Las solicitudes se ejecutan en segundo plano, los resultados
# obsoletos se descartan y la función puede desactivarse sin
# afectar a los diagnósticos oficiales del compilador.
# ============================================================

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot  # Permite ejecutar generaciones fuera del hilo gráfico y devolver resultados de forma segura.

from AsistenteIA.explicador_diagnosticos import ExplicadorDiagnosticos  # Realiza la generación estructurada y mantiene la caché validada.
from Motor.compilacion.diagnosticos import Diagnostico  # Conserva el tipo oficial utilizado por todas las fases del compilador.


class SenalesTrabajoDiagnosticos(QObject):  # Define el canal utilizado por cada trabajo de generación automática.
    terminado = Signal(int, object)  # Devuelve el identificador de solicitud y las soluciones mejoradas obtenidas.


class TrabajoDiagnosticosIA(QRunnable):  # Ejecuta una generación completa sin modificar widgets desde el hilo secundario.
    def __init__(
        self,
        identificador: int,
        diagnosticos: list[Diagnostico],
        explicador: ExplicadorDiagnosticos,
    ):
        super().__init__()  # Inicializa el trabajo administrado por QThreadPool.
        self.identificador = identificador  # Conserva la versión de la compilación que originó esta solicitud.
        self.diagnosticos = list(diagnosticos)  # Trabaja sobre una copia estable aunque la interfaz cambie posteriormente.
        self.explicador = explicador  # Reutiliza el mismo explicador para aprovechar su caché durante toda la sesión.
        self.senales = SenalesTrabajoDiagnosticos()  # Prepara el canal seguro de regreso al hilo principal.

    @Slot()
    def run(self) -> None:
        try:
            soluciones = self.explicador.mejorar_soluciones(self.diagnosticos)  # Obtiene únicamente explicaciones validadas asociadas con diagnósticos oficiales.
        except Exception:
            soluciones = {}  # Convierte un fallo inesperado de la capa opcional en ausencia de mejora sin afectar al compilador.

        self.senales.terminado.emit(self.identificador, soluciones)  # Devuelve el resultado sin acceder directamente a la tabla.


class ControlDiagnosticosIA(QObject):  # Administra concurrencia, cancelación lógica y vigencia de las soluciones generadas.
    soluciones_listas = Signal(object)  # Entrega a la interfaz un diccionario de identidades y soluciones mejoradas.

    def __init__(self, padre=None, explicador: ExplicadorDiagnosticos | None = None):
        super().__init__(padre)  # Vincula el controlador con el ciclo de vida del panel de diagnósticos.
        self.explicador = explicador or ExplicadorDiagnosticos()  # Utiliza la implementación real salvo cuando una prueba proporciona otra.
        self.habilitado = False  # Mantiene inactiva la generación hasta que Configuración confirme la preferencia y el servicio.
        self.identificador_solicitud = 0  # Aumenta con cada compilación para invalidar respuestas anteriores.
        self.hilos = QThreadPool(self)  # Mantiene la generación fuera del hilo gráfico.
        self.hilos.setMaxThreadCount(1)  # Evita ejecutar simultáneamente varias consultas pesadas sobre el mismo modelo local.
        self.trabajos_activos: dict[int, TrabajoDiagnosticosIA] = {}  # Conserva referencias a trabajos en curso o pendientes hasta recibir su señal final.

    def establecer_habilitado(self, habilitado: bool) -> None:
        nuevo_estado = bool(habilitado)  # Conserva únicamente un estado booleano explícito.

        if self.habilitado == nuevo_estado:
            return  # Evita invalidar innecesariamente una solicitud cuando no existe ningún cambio real.

        self.habilitado = nuevo_estado  # Actualiza primero el permiso utilizado al recibir futuros resultados.

        if not self.habilitado:
            self.cancelar()  # Invalida cualquier explicación iniciada antes de desactivar la función.

    def procesar(self, diagnosticos: list[Diagnostico]) -> None:
        self.identificador_solicitud += 1  # Invalida cualquier resultado relacionado con la compilación anterior.
        identificador = self.identificador_solicitud  # Conserva la versión exacta que pertenecerá al nuevo trabajo.

        if not self.habilitado or not diagnosticos:
            return  # No utiliza recursos cuando la función está apagada o la compilación no produjo diagnósticos.

        trabajo = TrabajoDiagnosticosIA(
            identificador=identificador,
            diagnosticos=diagnosticos,
            explicador=self.explicador,
        )  # Prepara una única operación que internamente agrupa y reutiliza explicaciones.

        trabajo.senales.terminado.connect(self._recibir_soluciones)  # Recupera el resultado solamente mediante una señal segura hacia el hilo principal.
        self.trabajos_activos[identificador] = trabajo  # Evita perder la referencia mientras QThreadPool todavía administra el trabajo.
        self.hilos.start(trabajo)  # Inicia o encola la generación sin congelar TecNet Finder.

    def cancelar(self) -> None:
        self.identificador_solicitud += 1  # Hace obsoletos todos los resultados que todavía pudieran finalizar posteriormente.

    @Slot(int, object)
    def _recibir_soluciones(self, identificador: int, soluciones) -> None:
        self.trabajos_activos.pop(identificador, None)  # Libera la referencia al trabajo independientemente de que su resultado siga vigente.

        if not self.habilitado:
            return  # Descarta generaciones terminadas después de que el usuario apagó la función.

        if identificador != self.identificador_solicitud:
            return  # Impide que una compilación anterior reemplace soluciones pertenecientes al código actual.

        if not isinstance(soluciones, dict):
            soluciones = {}  # Normaliza cualquier resultado inesperado para que la interfaz pueda restaurar sus soluciones oficiales.

        self.soluciones_listas.emit(soluciones)  # Informa también resultados vacíos para retirar correctamente cualquier estado visual de carga.
