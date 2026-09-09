# ============================================================
# Archivo: prueba_gestor_ollama.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba el ciclo de vida del servidor privado
# utilizado por el asistente local.
#
# Todas las operaciones de procesos se simulan para verificar
# configuración, propiedad y limpieza sin ejecutar realmente
# ollama.exe durante pytest.
# ============================================================

import subprocess  # Permite sustituir la creación real de procesos y utilizar sus constantes durante las comprobaciones.

from AsistenteIA.gestor_ollama import GestorOllama  # Importa el administrador cuyo comportamiento debe comprobarse.


class MotorSimulado:  # Representa diferentes estados de disponibilidad del servidor sin realizar peticiones HTTP.
    def __init__(self, estados: list[bool]):
        self.estados = list(estados)  # Conserva la secuencia que deberá devolver en consultas sucesivas.
        self.llamadas = 0  # Permite confirmar cuántas comprobaciones realizó el gestor.

    def disponible(self) -> bool:
        self.llamadas += 1  # Registra cada consulta equivalente a comprobar la API privada.

        if len(self.estados) > 1:
            return self.estados.pop(0)  # Avanza por la secuencia mientras existan distintos estados pendientes.

        if self.estados:
            return self.estados[0]  # Mantiene estable el último estado disponible.

        return False  # Considera inactivo el servidor cuando la prueba no proporcionó ningún estado.


class ProcesoSimulado:  # Imita solamente las operaciones utilizadas para controlar ollama.exe.
    def __init__(self, terminado: bool = False):
        self.terminado = terminado  # Permite representar procesos activos o procesos que fallaron inmediatamente.
        self.terminacion_solicitada = False  # Registra si el gestor intentó realizar un cierre normal.
        self.cierre_forzado = False  # Registra si fue necesario recurrir a kill.

    def poll(self):
        return 0 if self.terminado else None  # Imita el código de salida solamente después de finalizar.

    def terminate(self) -> None:
        self.terminacion_solicitada = True  # Registra que el proceso era propiedad de TecNet Finder.
        self.terminado = True  # Simula un cierre normal inmediato.

    def wait(self, timeout=None):
        if not self.terminado:
            raise subprocess.TimeoutExpired("ollama", timeout)  # Imita un proceso que todavía continúa activo.

        return 0  # Representa una terminación satisfactoria.

    def kill(self) -> None:
        self.cierre_forzado = True  # Registra que el gestor tuvo que utilizar la alternativa forzada.
        self.terminado = True  # Simula el cierre definitivo del proceso.


def _crear_dependencias_temporales(tmp_path):
    ruta_ollama = tmp_path / "Dependencias" / "Ollama"  # Reproduce únicamente la estructura que el gestor espera encontrar.
    ruta_ollama.mkdir(parents=True)  # Crea el runtime simulado dentro de la carpeta temporal de pytest.
    ejecutable = ruta_ollama / "ollama.exe"  # Genera la misma ruta relativa utilizada por la aplicación.
    ejecutable.write_bytes(b"ollama simulado")  # Hace que is_file reconozca un ejecutable presente sin necesitar uno real.
    modelos = ruta_ollama / "modelos"  # Reproduce el almacén privado de modelos.
    modelos.mkdir()  # Permite superar la validación previa al arranque.

    return ejecutable, modelos  # Entrega las rutas para comprobar posteriormente el entorno utilizado.


def prueba_gestor_reutiliza_servidor_ya_activo(tmp_path, monkeypatch):
    motor = MotorSimulado([True])  # Representa un Ollama que estaba activo antes de iniciar TecNet Finder.

    def popen_no_permitido(*_argumentos, **_opciones):
        raise AssertionError("No debe iniciarse un segundo Ollama.")  # Convierte cualquier intento de crear proceso en un fallo explícito.

    monkeypatch.setattr(subprocess, "Popen", popen_no_permitido)  # Protege la prueba contra duplicación accidental del servidor.
    gestor = GestorOllama(motor=motor, ruta_proyecto=tmp_path)

    resultado = gestor.iniciar()
    gestor.detener()

    assert resultado is True
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_no_inicia_si_falta_runtime(tmp_path, monkeypatch):
    motor = MotorSimulado([False])  # Representa la ausencia de un servidor previamente iniciado.

    def popen_no_permitido(*_argumentos, **_opciones):
        raise AssertionError("No debe intentarse iniciar un ejecutable inexistente.")  # Confirma que las rutas se validen antes de crear procesos.

    monkeypatch.setattr(subprocess, "Popen", popen_no_permitido)  # Impide ocultar una creación incorrecta del proceso.
    gestor = GestorOllama(motor=motor, ruta_proyecto=tmp_path)

    resultado = gestor.iniciar()

    assert resultado is False
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_inicia_runtime_privado_con_configuracion_correcta(tmp_path, monkeypatch):
    ejecutable, modelos = _crear_dependencias_temporales(tmp_path)  # Prepara una instalación local simulada.
    motor = MotorSimulado([False, True])  # Primero representa el servidor apagado y después disponible.
    proceso = ProcesoSimulado()  # Representa el ollama.exe iniciado correctamente.
    captura = {}  # Conserva los argumentos entregados a Popen para comprobar su aislamiento.

    def popen_simulado(argumentos, **opciones):
        captura["argumentos"] = argumentos  # Registra el comando utilizado para iniciar Ollama.
        captura["opciones"] = opciones  # Registra entorno, redirecciones y banderas de creación.
        return proceso  # Evita ejecutar un proceso verdadero durante pytest.

    monkeypatch.setattr(subprocess, "Popen", popen_simulado)  # Sustituye únicamente la creación del proceso durante esta prueba.
    gestor = GestorOllama(motor=motor, ruta_proyecto=tmp_path)

    resultado = gestor.iniciar()

    assert resultado is True
    assert gestor.iniciado_por_aplicacion is True
    assert captura["argumentos"] == [str(ejecutable), "serve"]
    assert captura["opciones"]["env"]["OLLAMA_HOST"] == "127.0.0.1:11435"
    assert captura["opciones"]["env"]["OLLAMA_MODELS"] == str(modelos)
    assert captura["opciones"]["env"]["OLLAMA_NO_CLOUD"] == "true"
    assert captura["opciones"]["stdin"] is subprocess.DEVNULL
    assert captura["opciones"]["stdout"] is subprocess.DEVNULL
    assert captura["opciones"]["stderr"] is subprocess.DEVNULL
    assert captura["opciones"]["creationflags"] == getattr(subprocess, "CREATE_NO_WINDOW", 0)


def prueba_gestor_detiene_solamente_proceso_creado_por_aplicacion(tmp_path, monkeypatch):
    _crear_dependencias_temporales(tmp_path)  # Prepara las dependencias requeridas para permitir el arranque.
    motor = MotorSimulado([False, True])  # Fuerza a TecNet Finder a crear su propia instancia.
    proceso = ProcesoSimulado()  # Conserva el estado que permitirá verificar el cierre posterior.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Evita ejecutar Ollama real.
    gestor = GestorOllama(motor=motor, ruta_proyecto=tmp_path)

    assert gestor.iniciar() is True

    gestor.detener()

    assert proceso.terminacion_solicitada is True
    assert proceso.terminado is True
    assert gestor.iniciado_por_aplicacion is False


def prueba_gestor_detecta_proceso_que_falla_durante_arranque(tmp_path, monkeypatch):
    _crear_dependencias_temporales(tmp_path)  # Permite llegar hasta la fase donde se crea el proceso.
    motor = MotorSimulado([False])  # Mantiene la API privada como no disponible.
    proceso = ProcesoSimulado(terminado=True)  # Simula un ollama.exe que termina inmediatamente al ejecutarse.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye la creación real por el fallo controlado.
    gestor = GestorOllama(motor=motor, ruta_proyecto=tmp_path)

    resultado = gestor.iniciar()

    assert resultado is False
    assert gestor.iniciado_por_aplicacion is False