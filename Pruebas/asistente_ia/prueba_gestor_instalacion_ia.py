# ============================================================
# Archivo: prueba_gestor_instalacion_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba GestorInstalacionIA sin descargar
# binarios ni modelos reales desde Internet.
#
# Mediante componentes, procesos y servidores simulados se
# verifican:
#
# - Instalación del runtime privado.
# - Verificación SHA-256 del paquete.
# - Protección contra rutas ZIP inseguras.
# - Descarga simulada del modelo.
# - Desinstalación limitada a archivos administrados.
# - Protección frente a servidores Ollama ajenos.
# - Arranque temporal del runtime antes de existir el modelo.
# - Tiempo especial utilizado durante una instalación nueva.
#
# Todas las operaciones utilizan directorios temporales y nunca
# modifican la instalación real de TecNet Finder.
# ============================================================

import hashlib  # Permite calcular el SHA-256 del pequeño paquete construido específicamente para las pruebas.
from pathlib import Path  # Permite crear y manipular rutas temporales utilizando la misma interfaz empleada por producción.
import subprocess  # Permite simular el proceso que normalmente correspondería con el servidor privado de Ollama.
import zipfile  # Permite construir paquetes ZIP mínimos semejantes con el formato utilizado por el runtime real.

from AsistenteIA.infraestructura.gestor_componente_ia import GestorComponenteIA  # Permite utilizar una instalación física aislada dentro del directorio temporal.
from AsistenteIA.infraestructura.gestor_instalacion_ia import GestorInstalacionIA, TIEMPO_INICIO_INSTALACION_SEGUNDOS  # Importa el administrador de instalación y el tiempo especial aplicado al primer arranque.
from AsistenteIA.infraestructura.gestor_ollama import GestorOllama  # Permite comprobar también el arranque temporal real del gestor sin utilizar un servidor verdadero.


class MotorSimulado:  # Representa únicamente la disponibilidad de la API privada sin realizar ninguna petición HTTP.
    def __init__(self, disponible: bool = False):  # Recibe el estado inicial que deberá responder el motor.
        self.estado = disponible  # Conserva la disponibilidad controlada por cada escenario de prueba.

    def disponible(self) -> bool:  # Reproduce la consulta utilizada normalmente para comprobar si Ollama responde.
        return self.estado  # Devuelve inmediatamente el estado preparado sin realizar conexiones reales.


class GestorOllamaSimulado:  # Representa el ciclo mínimo de Ollama que GestorInstalacionIA necesita durante instalación y desinstalación.
    def __init__(self, disponible: bool = False, propio: bool = False):  # Permite preparar un servidor apagado, activo o perteneciente a TecNet Finder.
        self.motor = MotorSimulado(disponible)  # Simula la API privada consultada por el gestor de instalación.
        self._iniciado_por_aplicacion = propio  # Indica si el proceso simulado pertenece actualmente a TecNet Finder.
        self.requerir_modelo_recibido = None  # Registrará si el arranque permitió ejecutarse antes de descargar el modelo.
        self.tiempo_inicio_recibido = None  # Registrará el margen especial solicitado durante el primer inicio.
        self.ultimo_error_inicio = ""  # Conserva la misma propiedad pública expuesta por GestorOllama real.

    @property  # Permite consultar el estado mediante la misma interfaz pública utilizada en producción.
    def iniciado_por_aplicacion(self) -> bool:  # Indica si TecNet Finder es propietario del servidor simulado.
        return self._iniciado_por_aplicacion  # Devuelve directamente el valor controlado por la prueba.

    def iniciar(self, requerir_modelo: bool = True, tiempo_inicio_segundos: float | None = None) -> bool:  # Simula un inicio satisfactorio registrando exactamente cómo fue solicitado.
        self.requerir_modelo_recibido = requerir_modelo  # Conserva si la instalación permitió arrancar temporalmente sin modelo.
        self.tiempo_inicio_recibido = tiempo_inicio_segundos  # Conserva el tiempo especial que GestorInstalacionIA decidió utilizar.
        self._iniciado_por_aplicacion = True  # Simula que TecNet Finder creó y pasó a controlar el proceso.
        self.motor.estado = True  # Simula que después del arranque la API privada ya responde.
        return True  # Informa un inicio exitoso sin lanzar ningún proceso real.

    def detener(self) -> None:  # Simula el cierre del servidor creado durante una instalación.
        self._iniciado_por_aplicacion = False  # Libera la propiedad del proceso.
        self.motor.estado = False  # Simula que la API privada dejó de encontrarse disponible.


class MotorSecuencial:  # Permite representar distintos estados de disponibilidad en consultas consecutivas.
    def __init__(self, estados: list[bool]):  # Recibe la secuencia que deberá consumirse conforme GestorOllama compruebe la API.
        self.estados = list(estados)  # Conserva una copia para poder retirar estados sin modificar la lista original de la prueba.

    def disponible(self) -> bool:  # Devuelve el estado correspondiente con la consulta actual.
        if len(self.estados) > 1:  # Comprueba si todavía existen varios estados diferentes pendientes.
            return self.estados.pop(0)  # Consume el primero para simular una transición posterior del servidor.

        return self.estados[0] if self.estados else False  # Mantiene estable el último estado o devuelve False si nunca se proporcionó ninguno.


class ProcesoSimulado:  # Imita únicamente las operaciones de proceso que GestorOllama utiliza durante las pruebas.
    def __init__(self, pid: int = 12345):  # Permite proporcionar un identificador conocido para las operaciones de cierre.
        self.pid = pid  # Conserva un PID semejante con el que proporcionaría subprocess.Popen.
        self.terminado = False  # Inicia representando un proceso que todavía se encuentra ejecutándose.
        self.terminacion_solicitada = False  # Registra si TecNet Finder solicitó explícitamente un cierre normal.

    def poll(self):  # Reproduce la consulta utilizada para saber si el proceso continúa activo.
        return 0 if self.terminado else None  # Devuelve un código únicamente después de marcar el proceso como finalizado.

    def terminate(self) -> None:  # Simula una solicitud normal de terminación.
        self.terminacion_solicitada = True  # Registra que GestorOllama tomó responsabilidad de cerrar el proceso.
        self.terminado = True  # Considera la terminación inmediata para simplificar el escenario controlado.

    def wait(self, timeout=None):  # Reproduce la espera utilizada después de solicitar el cierre.
        if not self.terminado:  # Comprueba si el proceso simulado todavía continúa activo.
            raise subprocess.TimeoutExpired("ollama", timeout)  # Imita la excepción real que produciría subprocess al superar el tiempo permitido.

        return 0  # Representa un proceso que terminó satisfactoriamente.

    def kill(self) -> None:  # Simula el mecanismo de terminación forzada utilizado como último recurso.
        self.terminado = True  # Marca definitivamente el proceso como finalizado.


def _crear_paquete_ollama(tmp_path: Path, nombre_adicional: str | None = None) -> tuple[Path, str]:  # Construye un ZIP mínimo y devuelve también su SHA-256 correcto.
    ruta_zip = tmp_path / "ollama-prueba.zip"  # Reserva una ruta temporal que sustituirá el paquete oficial descargado desde Internet.

    with zipfile.ZipFile(ruta_zip, "w") as archivo_zip:  # Crea físicamente el pequeño paquete utilizado por el escenario.
        archivo_zip.writestr("ollama.exe", b"runtime simulado")  # Incluye el ejecutable mínimo requerido para que el runtime parezca completo.
        archivo_zip.writestr("lib/ollama/prueba.dll", b"biblioteca simulada")  # Incluye una biblioteca dentro de una estructura semejante con el paquete real.

        if nombre_adicional is not None:  # Comprueba si la prueba desea insertar además una ruta especial o maliciosa.
            archivo_zip.writestr(nombre_adicional, b"contenido adicional")  # Añade el archivo exactamente con el nombre proporcionado para comprobar la seguridad de extracción.

    resumen = hashlib.sha256(ruta_zip.read_bytes()).hexdigest()  # Calcula la huella real del ZIP recién generado.
    return ruta_zip, resumen  # Entrega conjuntamente la ruta del paquete y el SHA-256 que debería ser considerado válido.


def _crear_componente_instalado(tmp_path: Path) -> GestorComponenteIA:  # Construye físicamente una instalación mínima que GestorComponenteIA considere completa.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Sustituye LocalAppData por el directorio temporal proporcionado por pytest.
    componente.ruta_modelos.mkdir(parents=True)  # Crea la carpeta necesaria para almacenar los archivos del modelo.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime")  # Crea un archivo que representa el ejecutable privado de Ollama.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo")  # Agrega al menos un archivo real para que la instalación pueda considerarse completa.
    return componente  # Devuelve la instalación temporal preparada para el escenario correspondiente.


def prueba_instalador_coloca_runtime_y_modelo_verificados(tmp_path, monkeypatch):  # Comprueba el recorrido satisfactorio de una instalación completa y verificada.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Prepara un usuario que inicialmente no posee componente de IA.
    gestor_ollama = GestorOllamaSimulado()  # Sustituye cualquier servidor real por un administrador completamente controlado.
    ruta_zip, resumen = _crear_paquete_ollama(tmp_path)  # Construye localmente un paquete cuyo SHA-256 sí debe coincidir.

    gestor = GestorInstalacionIA(
        componente_ia=componente,  # Indica dónde deberán colocarse los archivos simulados del componente.
        gestor_ollama=gestor_ollama,  # Utiliza el servidor simulado para evitar ejecutar Ollama.
        url_paquete=ruta_zip.as_uri(),  # Sustituye la descarga remota por la URI del ZIP temporal.
        sha256_paquete=resumen,  # Proporciona exactamente la huella calculada para permitir la instalación.
    )  # Construye un instalador equivalente con producción pero totalmente aislado de Internet.

    def descargar_modelo_simulado(_notificar):  # Sustituye la descarga real del modelo por la creación directa de un archivo pequeño.
        componente.ruta_modelos.mkdir(parents=True, exist_ok=True)  # Crea la misma carpeta que normalmente prepararía la descarga mediante Ollama.
        (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Agrega contenido suficiente para que GestorComponenteIA considere instalada la IA.

    monkeypatch.setattr(gestor, "_descargar_modelo", descargar_modelo_simulado)  # Sustituye solamente durante esta prueba la operación que requeriría acceso al modelo real.
    resultado, _mensaje = gestor.instalar()  # Ejecuta todo el procedimiento de instalación utilizando exclusivamente recursos temporales.
    assert resultado is True  # Confirma que el flujo completo pueda finalizar correctamente.
    assert componente.ruta_ejecutable_ollama.is_file()  # Comprueba que ollama.exe haya sido extraído dentro de la ubicación administrada.
    assert (componente.ruta_ollama / "lib" / "ollama" / "prueba.dll").is_file()  # Comprueba que también se preserve correctamente la estructura auxiliar del paquete.
    assert componente.instalado() is True  # Verifica que runtime y modelo sean reconocidos conjuntamente como una instalación válida.
    assert gestor_ollama.requerir_modelo_recibido is False  # Confirma que el primer arranque permita ejecutarse antes de existir el modelo.
    assert gestor_ollama.tiempo_inicio_recibido == TIEMPO_INICIO_INSTALACION_SEGUNDOS  # Comprueba que una instalación nueva utilice el margen especial de inicio definido para este caso.


def prueba_instalador_rechaza_paquete_con_hash_incorrecto(tmp_path):  # Comprueba que un paquete modificado o no esperado sea rechazado antes de su extracción.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza una instalación temporal completamente separada.
    gestor_ollama = GestorOllamaSimulado()  # Evita cualquier intento de iniciar un proceso real.
    ruta_zip, _resumen = _crear_paquete_ollama(tmp_path)  # Construye un ZIP válido cuya huella correcta se ignorará deliberadamente.

    gestor = GestorInstalacionIA(
        componente_ia=componente,  # Utiliza la carpeta temporal como destino de cualquier operación.
        gestor_ollama=gestor_ollama,  # Mantiene simulado el servicio local.
        url_paquete=ruta_zip.as_uri(),  # Utiliza el archivo local en lugar de realizar una descarga.
        sha256_paquete="0" * 64,  # Proporciona deliberadamente una huella que nunca coincidirá con el paquete generado.
    )  # Prepara específicamente el escenario destinado a comprobar la validación criptográfica.

    resultado, mensaje = gestor.instalar()  # Intenta instalar el paquete cuya huella no coincide con la esperada.
    assert resultado is False  # Confirma que la instalación sea detenida.
    assert "SHA-256" in mensaje  # Comprueba que el usuario reciba una explicación relacionada directamente con la verificación fallida.
    assert not componente.ruta_ollama.exists()  # Verifica que un paquete rechazado no deje una instalación parcial del runtime.


def prueba_instalador_rechaza_rutas_inseguras_del_zip(tmp_path):  # Comprueba la protección contra archivos ZIP que intentan escribir fuera del directorio permitido.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza una instalación temporal aislada.
    gestor_ollama = GestorOllamaSimulado()  # Sustituye cualquier interacción posterior con Ollama.
    ruta_zip, resumen = _crear_paquete_ollama(tmp_path, "../escape.txt")  # Añade deliberadamente una ruta relativa que intentaría escapar del destino de extracción.

    gestor = GestorInstalacionIA(
        componente_ia=componente,  # Mantiene toda posible extracción dentro del espacio temporal.
        gestor_ollama=gestor_ollama,  # Evita procesos reales durante la prueba.
        url_paquete=ruta_zip.as_uri(),  # Utiliza el paquete malicioso construido localmente.
        sha256_paquete=resumen,  # Proporciona su huella correcta para superar SHA-256 y alcanzar específicamente la validación de rutas.
    )  # Prepara el instalador para comprobar solamente la seguridad de extracción.

    resultado, mensaje = gestor.instalar()  # Ejecuta el flujo hasta que la ruta insegura sea detectada.
    assert resultado is False  # Confirma que la instalación completa sea rechazada.
    assert "ruta no permitida" in mensaje  # Comprueba que el motivo comunicado corresponda con la protección de rutas.
    assert not componente.ruta_ollama.exists()  # Verifica que tampoco quede un runtime parcialmente extraído.


def prueba_instalador_desinstala_solamente_componente_administrado(tmp_path):  # Comprueba que la eliminación se limite estrictamente a los archivos pertenecientes a TecNet Finder.
    componente = _crear_componente_instalado(tmp_path)  # Prepara una instalación privada completa dentro de la carpeta temporal.
    archivo_ajeno = tmp_path / "archivo-ajeno.txt"  # Define un archivo situado fuera del directorio administrado de IA.
    archivo_ajeno.write_text("conservar", encoding="utf-8")  # Crea físicamente información que nunca debe ser eliminada por la desinstalación.
    gestor_ollama = GestorOllamaSimulado()  # Representa un servidor actualmente apagado que no bloquea la eliminación.
    gestor = GestorInstalacionIA(componente, gestor_ollama)  # Construye el administrador normal porque en este escenario no se necesita descargar ningún paquete.
    resultado, _mensaje = gestor.desinstalar()  # Ejecuta la desinstalación completa sobre la instalación simulada.
    assert resultado is True  # Confirma que la eliminación pueda finalizar correctamente.
    assert not componente.ruta_base.exists()  # Verifica que desaparezca toda la carpeta privada de IA perteneciente a TecNet Finder.
    assert archivo_ajeno.is_file()  # Comprueba que cualquier archivo externo permanezca completamente intacto.


def prueba_instalador_no_elimina_componente_usado_por_servidor_ajeno(tmp_path):  # Comprueba que TecNet Finder no desinstale archivos mientras otro Ollama ajeno responde en el puerto privado.
    componente = _crear_componente_instalado(tmp_path)  # Prepara archivos reales que deberán permanecer después del rechazo.
    gestor_ollama = GestorOllamaSimulado(disponible=True, propio=False)  # Representa una API activa cuyo proceso no fue creado por esta aplicación.
    gestor = GestorInstalacionIA(componente, gestor_ollama)  # Construye el administrador que evaluará la seguridad antes de eliminar.
    resultado, mensaje = gestor.desinstalar()  # Solicita la desinstalación mientras existe el servidor ajeno simulado.
    assert resultado is False  # Confirma que el gestor se niegue a continuar con una situación que no controla.
    assert "otra instancia" in mensaje  # Comprueba que la explicación permita distinguir claramente un servidor externo.
    assert componente.instalado() is True  # Verifica que ningún archivo del componente haya sido eliminado después del rechazo.


def prueba_gestor_ollama_permite_arranque_temporal_sin_modelo(tmp_path, monkeypatch):  # Comprueba el estado intermedio necesario durante una instalación nueva.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Representa un usuario donde todavía se está construyendo el componente.
    componente.ruta_ollama.mkdir(parents=True)  # Crea únicamente la carpeta correspondiente con el runtime.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Proporciona el ejecutable aunque todavía no exista ningún modelo descargado.
    motor = MotorSecuencial([False, True])  # Simula primero una API apagada y después disponible tras crear el proceso.
    proceso = ProcesoSimulado()  # Sustituye el proceso real que ejecutaría ollama serve.
    monkeypatch.setattr(subprocess, "Popen", lambda *_argumentos, **_opciones: proceso)  # Impide ejecutar cualquier binario real durante pytest.

    gestor = GestorOllama(
        motor=motor,  # Utiliza la secuencia controlada de disponibilidad.
        componente_ia=componente,  # Apunta al runtime temporal que todavía no posee modelo.
        tiempo_inicio_segundos=0.5,  # Utiliza un margen pequeño suficiente para el proceso simulado.
        intervalo_comprobacion=0.01,  # Reduce también el intervalo para mantener rápida la prueba.
    )  # Construye el gestor real de procesos utilizando únicamente dependencias simuladas.

    monkeypatch.setattr(gestor, "_es_windows", lambda: False)  # Obliga a utilizar la terminación directa y evita ejecutar taskkill.
    resultado = gestor.iniciar(requerir_modelo=False)  # Solicita expresamente iniciar aun cuando todavía no exista el modelo.
    assert resultado is True  # Confirma que el modo temporal de instalación permita arrancar el runtime.
    assert componente.ruta_modelos.is_dir()  # Comprueba que GestorOllama prepare la carpeta donde posteriormente se descargará el modelo.
    assert gestor.iniciado_por_aplicacion is True  # Verifica que el proceso simulado quede registrado como propiedad de TecNet Finder.
    gestor.detener()  # Cierra el servidor temporal igual que ocurriría al finalizar la operación correspondiente.
    assert proceso.terminacion_solicitada is True  # Confirma que el gestor haya solicitado explícitamente cerrar el proceso que creó.
    assert gestor.iniciado_por_aplicacion is False  # Comprueba que después del cierre ya no se conserve una propiedad inexistente.