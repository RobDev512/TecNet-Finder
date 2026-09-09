# ============================================================
# Archivo: prueba_gestor_instalacion_ia.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba instalación, verificación, rollback y
# desinstalación del componente opcional de inteligencia artificial
# sin descargar binarios o modelos reales desde Internet.
#
# También comprueba que una instalación nueva solicite un tiempo
# de inicio mayor para el runtime recién preparado.
# ============================================================

import hashlib  # Permite calcular el SHA-256 del pequeño paquete construido específicamente para las pruebas.
from pathlib import Path  # Permite crear archivos temporales utilizando las mismas rutas empleadas por producción.
import subprocess  # Permite simular el proceso utilizado por GestorOllama.
import zipfile  # Permite construir paquetes mínimos equivalentes al formato utilizado por Ollama.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite utilizar una instalación aislada dentro del directorio temporal.
from AsistenteIA.gestor_instalacion_ia import GestorInstalacionIA, TIEMPO_INICIO_INSTALACION_SEGUNDOS  # Importa el administrador físico y su política especial de inicio.
from AsistenteIA.gestor_ollama import GestorOllama  # Permite comprobar también el arranque temporal del runtime sin modelo.


class MotorSimulado:  # Representa únicamente la disponibilidad de la API privada sin realizar conexiones HTTP.
    def __init__(self, disponible: bool = False):
        self.estado = disponible  # Conserva el valor que deberá devolverse en cada consulta.

    def disponible(self) -> bool:
        return self.estado  # Devuelve inmediatamente el estado controlado por la prueba.


class GestorOllamaSimulado:  # Representa el ciclo mínimo requerido por GestorInstalacionIA.
    def __init__(self, disponible: bool = False, propio: bool = False):
        self.motor = MotorSimulado(disponible)  # Permite simular un servidor apagado o ya activo.
        self._iniciado_por_aplicacion = propio  # Permite distinguir una instancia propia de un servidor ajeno.
        self.requerir_modelo_recibido = None  # Conserva cómo fue solicitado el arranque durante la instalación.
        self.tiempo_inicio_recibido = None  # Conserva cuánto tiempo adicional recibió el primer arranque.
        self.ultimo_error_inicio = ""  # Mantiene la misma propiedad pública utilizada por el gestor de producción.

    @property
    def iniciado_por_aplicacion(self) -> bool:
        return self._iniciado_por_aplicacion  # Expone el mismo estado consultado por el gestor real.

    def iniciar(
        self,
        requerir_modelo: bool = True,
        tiempo_inicio_segundos: float | None = None,
    ) -> bool:
        self.requerir_modelo_recibido = requerir_modelo  # Registra si la instalación permitió iniciar antes de descargar el modelo.
        self.tiempo_inicio_recibido = tiempo_inicio_segundos  # Registra el margen de tiempo utilizado durante el primer arranque.
        self._iniciado_por_aplicacion = True  # Simula que TecNet Finder pasó a ser propietario del proceso.
        self.motor.estado = True  # Simula que la API comenzó a responder correctamente.
        return True  # Considera exitoso el arranque simulado.

    def detener(self) -> None:
        self._iniciado_por_aplicacion = False  # Libera la propiedad equivalente al cierre del proceso.
        self.motor.estado = False  # Simula que el puerto privado dejó de responder.


class MotorSecuencial:  # Permite reproducir el cambio de apagado a disponible durante el inicio real simulado.
    def __init__(self, estados: list[bool]):
        self.estados = list(estados)  # Conserva la secuencia utilizada en consultas sucesivas.

    def disponible(self) -> bool:
        if len(self.estados) > 1:
            return self.estados.pop(0)  # Avanza mientras todavía existen varios estados pendientes.

        return self.estados[0] if self.estados else False  # Mantiene estable el último estado disponible.


class ProcesoSimulado:  # Imita únicamente las operaciones utilizadas por GestorOllama para controlar su proceso.
    def __init__(self, pid: int = 12345):
        self.pid = pid  # Proporciona un identificador equivalente al requerido por taskkill.
        self.terminado = False  # Comienza representando un proceso todavía activo.
        self.terminacion_solicitada = False  # Registra cuándo el gestor tomó responsabilidad de cerrarlo.

    def poll(self):
        return 0 if self.terminado else None  # Devuelve código de salida solamente cuando el proceso ya terminó.

    def terminate(self) -> None:
        self.terminacion_solicitada = True  # Registra la solicitud de cierre normal.
        self.terminado = True  # Simula una terminación inmediata.

    def wait(self, timeout=None):
        if not self.terminado:
            raise subprocess.TimeoutExpired("ollama", timeout)  # Imita un proceso todavía activo cuando se intenta esperar su cierre.

        return 0  # Representa una terminación satisfactoria.

    def kill(self) -> None:
        self.terminado = True  # Simula la terminación forzada utilizada solamente como alternativa.


def _crear_paquete_ollama(tmp_path: Path, nombre_adicional: str | None = None) -> tuple[Path, str]:
    ruta_zip = tmp_path / "ollama-prueba.zip"  # Reserva un archivo pequeño que sustituirá la descarga oficial.

    with zipfile.ZipFile(ruta_zip, "w") as archivo_zip:
        archivo_zip.writestr("ollama.exe", b"runtime simulado")  # Representa el ejecutable mínimo requerido por GestorOllama.
        archivo_zip.writestr("lib/ollama/prueba.dll", b"biblioteca simulada")  # Representa la estructura auxiliar incluida en el runtime real.

        if nombre_adicional is not None:
            archivo_zip.writestr(nombre_adicional, b"contenido adicional")  # Permite construir paquetes maliciosos controlados durante pruebas de seguridad.

    resumen = hashlib.sha256(ruta_zip.read_bytes()).hexdigest()  # Calcula el resumen exacto que deberá aceptar la instalación simulada.
    return ruta_zip, resumen  # Entrega archivo y SHA-256 al escenario correspondiente.


def _crear_componente_instalado(tmp_path: Path) -> GestorComponenteIA:
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza una ubicación completamente aislada del componente real del usuario.
    componente.ruta_modelos.mkdir(parents=True)  # Prepara la estructura requerida para considerar instalada la IA.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime")  # Representa la presencia física del ejecutable.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo")  # Representa al menos un archivo perteneciente al modelo privado.
    return componente  # Entrega una instalación completa y controlada.


def prueba_instalador_coloca_runtime_y_modelo_verificados(tmp_path, monkeypatch):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Prepara una instalación inicialmente ausente.
    gestor_ollama = GestorOllamaSimulado()  # Simula el servidor utilizado durante la descarga posterior del modelo.
    ruta_zip, resumen = _crear_paquete_ollama(tmp_path)  # Construye un paquete local cuyo SHA-256 sí debe aceptarse.

    gestor = GestorInstalacionIA(
        componente_ia=componente,
        gestor_ollama=gestor_ollama,
        url_paquete=ruta_zip.as_uri(),
        sha256_paquete=resumen,
    )  # Sustituye la descarga de Internet por el archivo local recién construido.

    def descargar_modelo_simulado(_notificar):
        componente.ruta_modelos.mkdir(parents=True, exist_ok=True)  # Representa la creación realizada normalmente por Ollama.
        (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Hace que GestorComponenteIA pueda reconocer la instalación completa.

    monkeypatch.setattr(gestor, "_descargar_modelo", descargar_modelo_simulado)  # Evita utilizar la API real durante pytest.

    resultado, _mensaje = gestor.instalar()

    assert resultado is True
    assert componente.ruta_ejecutable_ollama.is_file()
    assert (componente.ruta_ollama / "lib" / "ollama" / "prueba.dll").is_file()
    assert componente.instalado() is True
    assert gestor_ollama.requerir_modelo_recibido is False
    assert gestor_ollama.tiempo_inicio_recibido == TIEMPO_INICIO_INSTALACION_SEGUNDOS


def prueba_instalador_rechaza_paquete_con_hash_incorrecto(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Mantiene completamente separada la instalación utilizada por este escenario.
    gestor_ollama = GestorOllamaSimulado()  # Evita crear cualquier proceso real.
    ruta_zip, _resumen = _crear_paquete_ollama(tmp_path)  # Construye un paquete válido cuya huella será comparada contra otra diferente.

    gestor = GestorInstalacionIA(
        componente_ia=componente,
        gestor_ollama=gestor_ollama,
        url_paquete=ruta_zip.as_uri(),
        sha256_paquete="0" * 64,
    )  # Proporciona deliberadamente un SHA-256 que nunca coincidirá.

    resultado, mensaje = gestor.instalar()

    assert resultado is False
    assert "SHA-256" in mensaje
    assert not componente.ruta_ollama.exists()


def prueba_instalador_rechaza_rutas_inseguras_del_zip(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza una instalación aislada.
    gestor_ollama = GestorOllamaSimulado()  # Evita procesos reales durante la comprobación.
    ruta_zip, resumen = _crear_paquete_ollama(tmp_path, "../escape.txt")  # Introduce una ruta que intentaría abandonar el directorio de extracción.

    gestor = GestorInstalacionIA(
        componente_ia=componente,
        gestor_ollama=gestor_ollama,
        url_paquete=ruta_zip.as_uri(),
        sha256_paquete=resumen,
    )  # Permite superar la verificación criptográfica para llegar específicamente a la protección de rutas.

    resultado, mensaje = gestor.instalar()

    assert resultado is False
    assert "ruta no permitida" in mensaje
    assert not componente.ruta_ollama.exists()


def prueba_instalador_desinstala_solamente_componente_administrado(tmp_path):
    componente = _crear_componente_instalado(tmp_path)  # Prepara una IA completa dentro de la ubicación temporal.
    archivo_ajeno = tmp_path / "archivo-ajeno.txt"  # Crea información fuera de la carpeta administrada que nunca debe eliminarse.
    archivo_ajeno.write_text("conservar", encoding="utf-8")  # Permite comprobar posteriormente que la eliminación quedó correctamente limitada.
    gestor_ollama = GestorOllamaSimulado()  # Representa una asistencia actualmente apagada.

    gestor = GestorInstalacionIA(componente, gestor_ollama)  # Utiliza la administración normal porque este escenario no necesita descargar nada.

    resultado, _mensaje = gestor.desinstalar()

    assert resultado is True
    assert not componente.ruta_base.exists()
    assert archivo_ajeno.is_file()


def prueba_instalador_no_elimina_componente_usado_por_servidor_ajeno(tmp_path):
    componente = _crear_componente_instalado(tmp_path)  # Prepara archivos que permanecerán intactos durante el rechazo.
    gestor_ollama = GestorOllamaSimulado(disponible=True, propio=False)  # Representa otro proceso respondiendo en el puerto privado.

    gestor = GestorInstalacionIA(componente, gestor_ollama)

    resultado, mensaje = gestor.desinstalar()

    assert resultado is False
    assert "otra instancia" in mensaje
    assert componente.instalado() is True


def prueba_gestor_ollama_permite_arranque_temporal_sin_modelo(tmp_path, monkeypatch):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Representa el punto intermedio donde ya existe runtime pero todavía no modelo.
    componente.ruta_ollama.mkdir(parents=True)  # Prepara únicamente la carpeta del runtime.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Hace disponible el ejecutable requerido por el arranque temporal.

    motor = MotorSecuencial([False, True])  # Obliga primero a crear el proceso y después simula que la API ya responde.
    proceso = ProcesoSimulado()  # Sustituye el proceso real de Ollama.

    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Evita ejecutar binarios reales durante pytest.

    gestor = GestorOllama(
        motor=motor,
        componente_ia=componente,
        tiempo_inicio_segundos=0.5,
        intervalo_comprobacion=0.01,
    )  # Utiliza tiempos pequeños porque el servidor simulado responde inmediatamente.

    monkeypatch.setattr(gestor, "_es_windows", lambda: False)  # Utiliza la terminación directa para no ejecutar taskkill durante la prueba.

    resultado = gestor.iniciar(requerir_modelo=False)

    assert resultado is True
    assert componente.ruta_modelos.is_dir()
    assert gestor.iniciado_por_aplicacion is True

    gestor.detener()

    assert proceso.terminacion_solicitada is True
    assert gestor.iniciado_por_aplicacion is False