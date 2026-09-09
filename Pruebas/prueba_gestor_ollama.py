# ============================================================
# Archivo: prueba_gestor_ollama.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba el ciclo de vida del servidor privado
# utilizando una instalación opcional simulada.
#
# También verifica que en Windows se cierre el árbol completo
# iniciado por Ollama para evitar procesos secundarios huérfanos.
# ============================================================

import subprocess  # Permite sustituir la creación y terminación real de procesos durante las comprobaciones.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite crear instalaciones opcionales aisladas durante las pruebas.
from AsistenteIA.gestor_ollama import GestorOllama  # Importa el administrador cuyo comportamiento debe comprobarse.


class MotorSimulado:  # Representa diferentes estados de disponibilidad sin realizar peticiones HTTP reales.
    def __init__(self, estados: list[bool]):
        self.estados = list(estados)  # Conserva la secuencia utilizada en consultas sucesivas.
        self.llamadas = 0  # Permite conocer cuántas comprobaciones realizó el gestor.

    def disponible(self) -> bool:
        self.llamadas += 1  # Registra cada consulta equivalente a comprobar la API privada.

        if len(self.estados) > 1:
            return self.estados.pop(0)  # Avanza mientras existan varios estados pendientes.

        if self.estados:
            return self.estados[0]  # Mantiene estable el último estado disponible.

        return False  # Considera inactivo el servidor cuando no se proporcionó ningún estado.


class ProcesoSimulado:  # Imita únicamente las operaciones utilizadas para controlar el proceso principal de Ollama.
    def __init__(self, terminado: bool = False, pid: int = 12345):
        self.pid = pid  # Proporciona un identificador equivalente al utilizado por taskkill.
        self.terminado = terminado  # Permite representar procesos activos o fallos inmediatos.
        self.terminacion_solicitada = False  # Registra cuándo se pidió un cierre normal.
        self.cierre_forzado = False  # Registra cuándo fue necesario utilizar kill.

    def poll(self):
        return 0 if self.terminado else None  # Devuelve un código únicamente cuando el proceso ya terminó.

    def terminate(self) -> None:
        self.terminacion_solicitada = True  # Registra que TecNet Finder tomó responsabilidad del cierre.
        self.terminado = True  # Simula una terminación normal inmediata.

    def wait(self, timeout=None):
        if not self.terminado:
            raise subprocess.TimeoutExpired("ollama", timeout)  # Imita un proceso que continúa activo.

        return 0  # Representa una terminación satisfactoria.

    def kill(self) -> None:
        self.cierre_forzado = True  # Registra el cierre forzado.
        self.terminado = True  # Simula la terminación definitiva.


def _crear_componente_temporal(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza una ubicación equivalente a LocalAppData pero aislada.
    componente.ruta_modelos.mkdir(parents=True)  # Prepara la estructura administrada del componente.
    componente.ruta_ejecutable_ollama.write_bytes(b"ollama simulado")  # Representa la presencia del runtime.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Hace que la instalación sea considerada completa.

    return componente  # Entrega el componente preparado al escenario correspondiente.


def prueba_gestor_reutiliza_servidor_ya_activo(tmp_path, monkeypatch):
    motor = MotorSimulado([True])  # Representa un servidor activo antes de abrir TecNet Finder.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # La instalación local resulta irrelevante cuando la API ya responde.

    def popen_no_permitido(*_argumentos, **_opciones):
        raise AssertionError("No debe iniciarse un segundo Ollama.")  # Convierte una duplicación accidental en un fallo explícito.

    monkeypatch.setattr(subprocess, "Popen", popen_no_permitido)  # Impide crear un proceso durante este escenario.
    gestor = GestorOllama(motor=motor, componente_ia=componente)

    resultado = gestor.iniciar()
    gestor.detener()

    assert resultado is True
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_no_inicia_si_falta_componente(tmp_path, monkeypatch):
    motor = MotorSimulado([False])  # Representa una API privada apagada.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Representa un usuario que no instaló asistencia de IA.

    def popen_no_permitido(*_argumentos, **_opciones):
        raise AssertionError("No debe iniciarse un componente inexistente.")  # Confirma que la ausencia de IA se respete.

    monkeypatch.setattr(subprocess, "Popen", popen_no_permitido)  # Evita ocultar una creación incorrecta del proceso.
    gestor = GestorOllama(motor=motor, componente_ia=componente)

    resultado = gestor.iniciar()

    assert resultado is False
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_inicia_componente_privado_con_configuracion_correcta(tmp_path, monkeypatch):
    componente = _crear_componente_temporal(tmp_path)  # Prepara una instalación opcional válida.
    motor = MotorSimulado([False, True])  # Fuerza primero el arranque y después confirma disponibilidad.
    proceso = ProcesoSimulado()  # Representa el proceso creado correctamente.
    captura = {}  # Conserva los argumentos entregados a subprocess.

    def popen_simulado(argumentos, **opciones):
        captura["argumentos"] = argumentos  # Registra el comando utilizado.
        captura["opciones"] = opciones  # Registra entorno, redirecciones y banderas.
        return proceso  # Sustituye el proceso real.

    monkeypatch.setattr(subprocess, "Popen", popen_simulado)  # Evita ejecutar Ollama durante pytest.
    gestor = GestorOllama(motor=motor, componente_ia=componente)

    resultado = gestor.iniciar()

    assert resultado is True
    assert gestor.iniciado_por_aplicacion is True
    assert captura["argumentos"] == [str(componente.ruta_ejecutable_ollama), "serve"]
    assert captura["opciones"]["env"]["OLLAMA_HOST"] == "127.0.0.1:11435"
    assert captura["opciones"]["env"]["OLLAMA_MODELS"] == str(componente.ruta_modelos)
    assert captura["opciones"]["env"]["OLLAMA_NO_CLOUD"] == "true"
    assert captura["opciones"]["stdin"] is subprocess.DEVNULL
    assert captura["opciones"]["stdout"] is subprocess.DEVNULL
    assert captura["opciones"]["stderr"] is subprocess.DEVNULL
    assert captura["opciones"]["creationflags"] == getattr(subprocess, "CREATE_NO_WINDOW", 0)


def prueba_gestor_detiene_solamente_proceso_creado_por_aplicacion(tmp_path, monkeypatch):
    componente = _crear_componente_temporal(tmp_path)  # Prepara una instalación válida.
    motor = MotorSimulado([False, True])  # Obliga al gestor a crear su propio proceso.
    proceso = ProcesoSimulado()  # Conserva el estado utilizado para verificar el cierre.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Evita ejecutar el runtime verdadero.
    gestor = GestorOllama(motor=motor, componente_ia=componente)
    monkeypatch.setattr(gestor, "_es_windows", lambda: False)  # Fuerza el mecanismo directo para comprobarlo de forma independiente.

    assert gestor.iniciar() is True

    gestor.detener()

    assert proceso.terminacion_solicitada is True
    assert proceso.terminado is True
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_cierra_arbol_completo_en_windows(tmp_path, monkeypatch):
    componente = _crear_componente_temporal(tmp_path)  # Prepara el componente requerido antes de iniciar el servidor.
    motor = MotorSimulado([False, True])  # Obliga a TecNet Finder a crear su propia instancia.
    proceso = ProcesoSimulado(pid=54321)  # Proporciona un PID conocido para comprobar el comando enviado a Windows.
    captura = {}  # Conserva el comando utilizado para cerrar el árbol.

    def run_simulado(argumentos, **opciones):
        captura["argumentos"] = argumentos  # Registra la llamada equivalente a taskkill.
        captura["opciones"] = opciones  # Conserva las opciones utilizadas durante la terminación silenciosa.
        proceso.terminado = True  # Simula que Windows cerró correctamente el proceso principal y sus secundarios.

        class Resultado:
            returncode = 0

        return Resultado()  # Representa una ejecución satisfactoria de taskkill.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye el arranque real de Ollama.
    monkeypatch.setattr(subprocess, "run", run_simulado)  # Sustituye taskkill para evitar terminar procesos verdaderos durante pytest.

    gestor = GestorOllama(motor=motor, componente_ia=componente)
    monkeypatch.setattr(gestor, "_es_windows", lambda: True)  # Comprueba el comportamiento específico utilizado en Windows.

    assert gestor.iniciar() is True

    gestor.detener()

    assert captura["argumentos"] == ["taskkill", "/PID", "54321", "/T", "/F"]
    assert captura["opciones"]["stdin"] is subprocess.DEVNULL
    assert captura["opciones"]["stdout"] is subprocess.DEVNULL
    assert captura["opciones"]["stderr"] is subprocess.DEVNULL
    assert captura["opciones"]["check"] is False
    assert proceso.terminado is True
    assert proceso.terminacion_solicitada is False
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_detecta_proceso_que_falla_durante_arranque(tmp_path, monkeypatch):
    componente = _crear_componente_temporal(tmp_path)  # Permite llegar hasta la creación del proceso.
    motor = MotorSimulado([False])  # Mantiene la API como no disponible.
    proceso = ProcesoSimulado(terminado=True)  # Representa un proceso que termina inmediatamente.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye la ejecución real.
    gestor = GestorOllama(motor=motor, componente_ia=componente)

    resultado = gestor.iniciar()

    assert resultado is False
    assert gestor.iniciado_por_aplicacion is False