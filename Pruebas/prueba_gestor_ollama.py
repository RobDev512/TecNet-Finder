# ============================================================
# Archivo: prueba_gestor_ollama.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el ciclo de vida del servidor privado
# de Ollama administrado por TecNet Finder.
#
# Todos los procesos y estados de disponibilidad son simulados.
# Las pruebas verifican:
#
# - Reutilización de un servidor que ya estaba activo.
# - Rechazo cuando falta el componente opcional.
# - Inicio del runtime privado con su entorno correcto.
# - Cierre exclusivo de procesos creados por TecNet Finder.
# - Terminación completa del árbol de procesos en Windows.
# - Detección de procesos que fallan durante el arranque.
# - Uso de tiempos especiales durante una instalación nueva.
#
# Ninguna prueba inicia realmente ollama.exe.
# ============================================================

import subprocess  # Permite sustituir creación, espera y terminación de procesos sin ejecutar Ollama realmente.

from AsistenteIA.infraestructura.gestor_componente_ia import GestorComponenteIA  # Permite crear instalaciones temporales equivalentes con el componente opcional real.
from AsistenteIA.infraestructura.gestor_ollama import GestorOllama  # Importa el administrador de procesos cuyo comportamiento se comprueba en este archivo.


class MotorSimulado:  # Representa diferentes estados consecutivos de disponibilidad sin realizar solicitudes HTTP.
    def __init__(self, estados: list[bool]):  # Recibe la secuencia que deberá devolver conforme el gestor compruebe la API privada.
        self.estados = list(estados)  # Conserva una copia de la secuencia para consumirla sin modificar los datos originales.
        self.llamadas = 0  # Registra cuántas veces GestorOllama intentó comprobar la disponibilidad del servidor.

    def disponible(self) -> bool:  # Reproduce la consulta que normalmente realizaría MotorLocalOllama.
        self.llamadas += 1  # Incrementa el contador en cada comprobación efectuada por el gestor.

        if len(self.estados) > 1:  # Comprueba si todavía existen diferentes estados pendientes dentro de la secuencia.
            return self.estados.pop(0)  # Consume el primero para permitir que una consulta posterior observe un nuevo estado.

        if self.estados:  # Comprueba si queda al menos un estado estable.
            return self.estados[0]  # Mantiene ese último valor para cualquier consulta adicional.

        return False  # Considera apagado el servidor cuando la prueba no proporcionó ningún estado.


class ProcesoSimulado:  # Imita exclusivamente las operaciones que GestorOllama utiliza sobre subprocess.Popen.
    def __init__(self, terminado: bool = False, pid: int = 12345):  # Permite representar procesos activos, fallidos y con identificadores conocidos.
        self.pid = pid  # Conserva el identificador utilizado especialmente por taskkill en Windows.
        self.terminado = terminado  # Permite iniciar el escenario con el proceso activo o ya finalizado.
        self.terminacion_solicitada = False  # Registra si GestorOllama pidió un cierre normal mediante terminate.
        self.cierre_forzado = False  # Registra si fue necesario recurrir posteriormente al método kill.

    def poll(self):  # Reproduce la consulta utilizada para comprobar si el proceso continúa ejecutándose.
        return 0 if self.terminado else None  # Devuelve un código de salida solamente cuando ya se considera finalizado.

    def terminate(self) -> None:  # Simula la terminación normal empleada fuera del flujo específico de Windows.
        self.terminacion_solicitada = True  # Registra que el gestor pidió cerrar el proceso.
        self.terminado = True  # Considera que la operación consiguió finalizarlo inmediatamente.

    def wait(self, timeout=None):  # Reproduce la espera realizada después de solicitar la terminación.
        if not self.terminado:  # Comprueba si el proceso continúa activo después del tiempo otorgado.
            raise subprocess.TimeoutExpired("ollama", timeout)  # Imita la misma excepción producida por subprocess ante un timeout real.

        return 0  # Representa un cierre satisfactorio cuando el proceso ya terminó.

    def kill(self) -> None:  # Simula la alternativa utilizada cuando terminate no consigue finalizar el proceso.
        self.cierre_forzado = True  # Registra que fue necesario utilizar una terminación más agresiva.
        self.terminado = True  # Marca definitivamente el proceso como finalizado.


def _crear_componente_temporal(tmp_path):  # Construye una instalación mínima completa que GestorOllama pueda utilizar durante las pruebas.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Sustituye LocalAppData por el directorio aislado proporcionado por pytest.
    componente.ruta_modelos.mkdir(parents=True)  # Crea la carpeta requerida para almacenar el modelo privado.
    componente.ruta_ejecutable_ollama.write_bytes(b"ollama simulado")  # Crea un archivo que representa el ejecutable administrado.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Agrega un archivo de modelo para completar la instalación física.
    return componente  # Devuelve la instalación lista para el escenario correspondiente.


def prueba_gestor_reutiliza_servidor_ya_activo(tmp_path, monkeypatch):  # Comprueba que nunca se cree un segundo Ollama cuando la API privada ya responde.
    motor = MotorSimulado([True])  # Representa un servidor que se encontraba activo antes de iniciar TecNet Finder.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Prepara un componente local cuya existencia resulta irrelevante mientras ya exista servicio.

    def popen_no_permitido(*_argumentos, **_opciones):  # Sustituye Popen para convertir cualquier intento de duplicación en un fallo de prueba.
        raise AssertionError("No debe iniciarse un segundo Ollama.")  # Indica claramente que el gestor no debía crear otro proceso.

    monkeypatch.setattr(subprocess, "Popen", popen_no_permitido)  # Impide físicamente que la prueba pueda iniciar un proceso real.
    gestor = GestorOllama(motor=motor, componente_ia=componente)  # Construye el administrador utilizando la API ya disponible.
    resultado = gestor.iniciar()  # Solicita iniciar la asistencia aunque el servidor ya se encuentre respondiendo.
    gestor.detener()  # Solicita después detener, operación que tampoco debe cerrar un proceso ajeno.
    assert resultado is True  # Confirma que reutilizar el servidor existente se considere un inicio satisfactorio.
    assert gestor.iniciado_por_aplicacion is False  # Comprueba que el servidor ajeno nunca sea registrado como propiedad de TecNet Finder.
    assert gestor.ultimo_error_inicio == ""  # Verifica que reutilizar una instancia válida no deje ningún mensaje de error.


def prueba_gestor_no_inicia_si_falta_componente(tmp_path, monkeypatch):  # Comprueba que el gestor no intente ejecutar un runtime que todavía no se encuentra instalado.
    motor = MotorSimulado([False])  # Representa una API privada actualmente apagada.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Representa un usuario sin runtime ni modelo instalados.

    def popen_no_permitido(*_argumentos, **_opciones):  # Sustituye Popen para detectar inmediatamente cualquier intento incorrecto de arranque.
        raise AssertionError("No debe iniciarse un componente inexistente.")  # Explica el motivo exacto por el que una llamada sería incorrecta.

    monkeypatch.setattr(subprocess, "Popen", popen_no_permitido)  # Garantiza que ningún ejecutable pueda iniciarse durante el escenario.
    gestor = GestorOllama(motor=motor, componente_ia=componente)  # Construye el gestor sobre una instalación inexistente.
    resultado = gestor.iniciar()  # Intenta activar la asistencia para comprobar que la validación previa lo impida.
    assert resultado is False  # Confirma que el inicio sea rechazado.
    assert gestor.iniciado_por_aplicacion is False  # Comprueba que nunca se registre un proceso que realmente no existe.
    assert gestor.ultimo_error_inicio  # Verifica que el gestor conserve una explicación útil del motivo del rechazo.


def prueba_gestor_inicia_componente_privado_con_configuracion_correcta(tmp_path, monkeypatch):  # Comprueba comando, variables de entorno y redirecciones utilizadas al iniciar el runtime privado.
    componente = _crear_componente_temporal(tmp_path)  # Prepara una instalación opcional completa y reconocible.
    motor = MotorSimulado([False, True])  # Obliga primero a crear el proceso y posteriormente simula que su API ya responde.
    proceso = ProcesoSimulado()  # Representa el proceso satisfactorio que devolvería subprocess.Popen.
    captura = {}  # Reunirá los argumentos y opciones utilizados para poder comprobar su configuración exacta.

    def popen_simulado(argumentos, **opciones):  # Sustituye la creación real del proceso registrando toda la información recibida.
        captura["argumentos"] = argumentos  # Conserva el comando completo utilizado para ejecutar Ollama.
        captura["opciones"] = opciones  # Conserva entorno, redirecciones y banderas entregadas a subprocess.
        return proceso  # Devuelve el proceso controlado en lugar de iniciar realmente ollama.exe.

    monkeypatch.setattr(subprocess, "Popen", popen_simulado)  # Sustituye la operación real únicamente durante este escenario.
    gestor = GestorOllama(motor=motor, componente_ia=componente)  # Construye el gestor utilizando componentes completamente simulados.
    resultado = gestor.iniciar()  # Ejecuta el recorrido normal de inicio hasta detectar que la API quedó disponible.
    assert resultado is True  # Confirma que el proceso configurado correctamente se considere iniciado.
    assert gestor.iniciado_por_aplicacion is True  # Comprueba que TecNet Finder recuerde que este proceso sí le pertenece.
    assert gestor.ultimo_error_inicio == ""  # Verifica que un inicio exitoso elimine cualquier posible error previo.
    assert captura["argumentos"] == [str(componente.ruta_ejecutable_ollama), "serve"]  # Confirma que se utilice exclusivamente el ejecutable privado con el comando serve.
    assert captura["opciones"]["env"]["OLLAMA_HOST"] == "127.0.0.1:11435"  # Comprueba que el servidor utilice únicamente el puerto privado previsto por TecNet Finder.
    assert captura["opciones"]["env"]["OLLAMA_MODELS"] == str(componente.ruta_modelos)  # Confirma que el runtime utilice la carpeta privada de modelos administrada.
    assert captura["opciones"]["env"]["OLLAMA_NO_CLOUD"] == "true"  # Verifica que Ollama se configure explícitamente para no utilizar servicios en la nube.
    assert captura["opciones"]["stdin"] is subprocess.DEVNULL  # Comprueba que el proceso no dependa de una entrada interactiva.
    assert captura["opciones"]["stdout"] is subprocess.DEVNULL  # Confirma que la salida normal permanezca oculta para el usuario.
    assert captura["opciones"]["stderr"] is subprocess.DEVNULL  # Confirma que tampoco aparezca una consola con errores del runtime.
    assert captura["opciones"]["creationflags"] == getattr(subprocess, "CREATE_NO_WINDOW", 0)  # Comprueba la bandera utilizada para evitar una ventana de consola adicional en Windows.


def prueba_gestor_detiene_solamente_proceso_creado_por_aplicacion(tmp_path, monkeypatch):  # Comprueba el cierre normal de un proceso cuya propiedad pertenece realmente a TecNet Finder.
    componente = _crear_componente_temporal(tmp_path)  # Prepara una instalación válida que permita llegar al inicio del servidor.
    motor = MotorSimulado([False, True])  # Obliga a crear un proceso propio y posteriormente confirma que su API responde.
    proceso = ProcesoSimulado()  # Conserva el estado necesario para comprobar las operaciones de cierre.
    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye el arranque real por el objeto controlado.
    gestor = GestorOllama(motor=motor, componente_ia=componente)  # Construye el gestor real utilizando el proceso simulado.
    monkeypatch.setattr(gestor, "_es_windows", lambda: False)  # Fuerza la ruta de terminación directa para aislarla de taskkill.
    assert gestor.iniciar() is True  # Confirma primero que el servidor sea reconocido como iniciado correctamente.
    gestor.detener()  # Solicita el cierre del proceso que acaba de crear la aplicación.
    assert proceso.terminacion_solicitada is True  # Comprueba que se haya utilizado terminate sobre el proceso propio.
    assert proceso.terminado is True  # Verifica que después del procedimiento el proceso se considere finalizado.
    assert gestor.iniciado_por_aplicacion is False  # Confirma que el gestor elimine correctamente su marca de propiedad.


def prueba_gestor_cierra_arbol_completo_en_windows(tmp_path, monkeypatch):  # Comprueba que Windows utilice taskkill con /T para cerrar también procesos descendientes.
    componente = _crear_componente_temporal(tmp_path)  # Prepara el componente necesario para permitir el inicio.
    motor = MotorSimulado([False, True])  # Obliga a crear un servidor propio antes de comprobar su cierre.
    proceso = ProcesoSimulado(pid=54321)  # Utiliza un PID conocido para poder verificar exactamente el comando taskkill.
    captura = {}  # Reunirá tanto el comando como las opciones utilizadas para cerrar el árbol.

    def run_simulado(argumentos, **opciones):  # Sustituye taskkill registrando los datos recibidos y simulando una ejecución correcta.
        captura["argumentos"] = argumentos  # Conserva la lista completa de argumentos solicitada al sistema.
        captura["opciones"] = opciones  # Conserva redirecciones y configuración utilizadas durante la operación.
        proceso.terminado = True  # Simula que Windows cerró correctamente el proceso principal y todos sus descendientes.

        class Resultado:  # Proporciona únicamente el atributo consultado después de ejecutar subprocess.run.
            returncode = 0  # Representa una ejecución satisfactoria de taskkill.

        return Resultado()  # Devuelve la estructura mínima equivalente con el resultado real.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye el arranque verdadero del servidor.
    monkeypatch.setattr(subprocess, "run", run_simulado)  # Sustituye también la ejecución real de taskkill.
    gestor = GestorOllama(motor=motor, componente_ia=componente)  # Construye el administrador que realizará inicio y cierre.
    monkeypatch.setattr(gestor, "_es_windows", lambda: True)  # Fuerza específicamente el comportamiento diseñado para Windows.
    assert gestor.iniciar() is True  # Confirma que el proceso simulado quede registrado como propio.
    gestor.detener()  # Solicita su cierre para activar la ruta basada en taskkill.
    assert captura["argumentos"] == ["taskkill", "/PID", "54321", "/T", "/F"]  # Comprueba que se solicite cerrar el PID, todo su árbol y de manera forzada.
    assert captura["opciones"]["stdin"] is subprocess.DEVNULL  # Confirma que taskkill no requiera ninguna interacción.
    assert captura["opciones"]["stdout"] is subprocess.DEVNULL  # Evita mostrar salida de consola durante el cierre.
    assert captura["opciones"]["stderr"] is subprocess.DEVNULL  # Evita mostrar mensajes adicionales del comando del sistema.
    assert captura["opciones"]["check"] is False  # Comprueba que un código distinto de cero pueda tratarse posteriormente sin una excepción automática.
    assert proceso.terminado is True  # Verifica que el árbol simulado haya quedado cerrado.
    assert proceso.terminacion_solicitada is False  # Confirma que en Windows no se utilice además terminate sobre el proceso principal.
    assert gestor.iniciado_por_aplicacion is False  # Comprueba que la propiedad se libere después de cerrar correctamente el árbol.


def prueba_gestor_detecta_proceso_que_falla_durante_arranque(tmp_path, monkeypatch):  # Comprueba que un ollama.exe que termina inmediatamente produzca un fallo de inicio controlado.
    componente = _crear_componente_temporal(tmp_path)  # Prepara una instalación válida para que el gestor alcance realmente Popen.
    motor = MotorSimulado([False])  # Mantiene la API apagada durante todo el escenario.
    proceso = ProcesoSimulado(terminado=True)  # Representa un proceso que termina antes de que la API consiga responder.
    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye la creación del runtime por el proceso ya finalizado.
    gestor = GestorOllama(motor=motor, componente_ia=componente)  # Construye el administrador encargado de detectar el fallo.
    resultado = gestor.iniciar()  # Intenta arrancar y comprueba inmediatamente el estado del proceso simulado.
    assert resultado is False  # Confirma que un proceso terminado no sea considerado un servidor válido.
    assert gestor.iniciado_por_aplicacion is False  # Comprueba que la aplicación no conserve la propiedad de un proceso que ya desapareció.
    assert "código 0" in gestor.ultimo_error_inicio  # Verifica que la explicación conserve el código de salida detectado.


def prueba_gestor_permite_tiempo_especial_para_primera_instalacion(tmp_path, monkeypatch):  # Comprueba que iniciar pueda sustituir temporalmente el timeout normal durante una instalación nueva.
    componente = _crear_componente_temporal(tmp_path)  # Prepara una instalación completa para concentrar la prueba únicamente en la política de espera.
    motor = MotorSimulado([False, True])  # Simula una API apagada antes del proceso y disponible inmediatamente después.
    proceso = ProcesoSimulado()  # Representa un servidor que consigue iniciar dentro del tiempo especial.
    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Sustituye cualquier ejecución real de ollama.exe.

    gestor = GestorOllama(
        motor=motor,  # Utiliza la secuencia de disponibilidad controlada.
        componente_ia=componente,  # Utiliza la instalación temporal completa.
        tiempo_inicio_segundos=0.0,  # Configura deliberadamente un timeout normal insuficiente.
        intervalo_comprobacion=0.01,  # Mantiene muy pequeño el intervalo utilizado por esta prueba.
    )  # Prepara un gestor cuya única posibilidad de éxito depende del tiempo especial proporcionado a iniciar.

    resultado = gestor.iniciar(
        requerir_modelo=False,  # Permite reproducir el mismo arranque temporal utilizado durante instalación.
        tiempo_inicio_segundos=0.5,  # Sustituye para esta llamada el timeout normal configurado en cero.
    )  # Ejecuta el inicio utilizando exclusivamente el margen especial proporcionado.

    assert resultado is True  # Confirma que el tiempo personalizado permita completar el arranque.
    assert gestor.iniciado_por_aplicacion is True  # Comprueba que el proceso quede correctamente registrado como propio.
    assert gestor.ultimo_error_inicio == ""  # Verifica que una operación exitosa no conserve mensajes de error.
    monkeypatch.setattr(gestor, "_es_windows", lambda: False)  # Fuerza una limpieza directa para evitar ejecutar taskkill durante la prueba.
    gestor.detener()  # Cierra el proceso simulado después de completar las comprobaciones.
    assert proceso.terminacion_solicitada is True  # Confirma que la limpieza haya solicitado correctamente terminar el servidor creado.