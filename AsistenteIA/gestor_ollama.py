# ============================================================
# Archivo: gestor_ollama.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo administra el ciclo de vida de la instancia privada
# de Ollama utilizada por TecNet Finder.
#
# Utiliza el componente opcional instalado para el usuario,
# reutiliza un servidor existente cuando corresponde y solamente
# detiene procesos creados por la propia aplicación. En Windows
# también cierra los procesos secundarios utilizados para ejecutar
# el modelo local.
# ============================================================

import os  # Permite construir el entorno privado y detectar el sistema operativo actual.
import subprocess  # Permite iniciar y detener Ollama junto con sus procesos secundarios.
import time  # Permite esperar brevemente mientras el servidor privado comienza a responder.

from AsistenteIA.configuracion import HOST_OLLAMA, PUERTO_OLLAMA  # Importa la dirección reservada para la instancia propia de TecNet Finder.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Importa las rutas administradas del componente opcional.
from AsistenteIA.motor_local import MotorLocalOllama  # Permite comprobar cuándo la API privada se encuentra disponible.


class GestorOllama:  # Controla exclusivamente el servidor requerido por las funciones opcionales de inteligencia artificial.
    def __init__(
        self,
        motor: MotorLocalOllama | None = None,
        componente_ia: GestorComponenteIA | None = None,
        tiempo_inicio_segundos: float = 5.0,
        intervalo_comprobacion: float = 0.1,
    ):
        self.motor = motor or MotorLocalOllama()  # Reutiliza el mismo cliente HTTP empleado por el asistente.
        self.componente_ia = componente_ia or GestorComponenteIA()  # Utiliza la instalación administrada correspondiente al usuario.
        self.tiempo_inicio_segundos = tiempo_inicio_segundos  # Limita cuánto puede retrasarse el arranque del componente opcional.
        self.intervalo_comprobacion = intervalo_comprobacion  # Evita consultar continuamente la API durante el inicio.
        self._proceso: subprocess.Popen | None = None  # Conserva únicamente el proceso principal creado por esta instancia.
        self._iniciado_por_aplicacion = False  # Permite distinguir procesos propios de servidores previamente activos.

    @property
    def iniciado_por_aplicacion(self) -> bool:
        return self._iniciado_por_aplicacion  # Permite consultar la propiedad del proceso sin exponer su manipulación.

    def iniciar(self) -> bool:
        if self.motor.disponible():
            return True  # Reutiliza la instancia privada cuando ya se encuentra activa.

        if not self.componente_ia.instalado():
            return False  # Mantiene TecNet Finder operativo cuando el usuario decidió no instalar asistencia de IA.

        ruta_ollama = self.componente_ia.ruta_ejecutable_ollama  # Obtiene el ejecutable desde la instalación opcional administrada.
        ruta_modelos = self.componente_ia.ruta_modelos  # Obtiene el almacén privado desde la misma instalación.

        entorno = os.environ.copy()  # Conserva las variables normales del sistema antes de configurar Ollama.
        entorno["OLLAMA_HOST"] = f"{HOST_OLLAMA}:{PUERTO_OLLAMA}"  # Reserva el puerto privado utilizado únicamente por TecNet Finder.
        entorno["OLLAMA_MODELS"] = str(ruta_modelos)  # Evita utilizar accidentalmente modelos globales del usuario.
        entorno["OLLAMA_NO_CLOUD"] = "true"  # Mantiene la instancia orientada exclusivamente al procesamiento local.

        banderas_creacion = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # Evita mostrar una consola adicional en Windows.

        try:
            self._proceso = subprocess.Popen(
                [str(ruta_ollama), "serve"],
                cwd=str(ruta_ollama.parent),
                env=entorno,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=banderas_creacion,
            )  # Inicia el componente opcional silenciosamente.
        except OSError:
            self._proceso = None  # Elimina cualquier referencia incompleta tras un fallo de creación.
            return False  # Mantiene disponible el resto de TecNet Finder.

        self._iniciado_por_aplicacion = True  # Registra la propiedad antes de esperar la disponibilidad de la API.
        limite = time.monotonic() + self.tiempo_inicio_segundos  # Calcula un límite independiente de cambios en el reloj del sistema.

        while time.monotonic() < limite:
            if self._proceso.poll() is not None:
                self._proceso = None  # Descarta un proceso que terminó prematuramente.
                self._iniciado_por_aplicacion = False  # Libera inmediatamente la propiedad del proceso inexistente.
                return False  # Permite continuar sin funciones de IA.

            if self.motor.disponible():
                return True  # Finaliza el arranque tan pronto como la API privada responde.

            time.sleep(self.intervalo_comprobacion)  # Evita una espera activa mientras inicia Ollama.

        self.detener()  # Retira un proceso que no consiguió iniciar correctamente.
        return False  # Indica que la asistencia permanecerá inactiva durante esta ejecución.

    def detener(self) -> None:
        if not self._iniciado_por_aplicacion or self._proceso is None:
            return  # Nunca intenta cerrar una instancia que TecNet Finder no haya creado.

        proceso = self._proceso  # Conserva la referencia mientras se limpia inmediatamente el estado interno.
        self._proceso = None  # Evita procesar dos veces el mismo cierre.
        self._iniciado_por_aplicacion = False  # Libera la propiedad antes de cualquier operación potencialmente fallida.

        if proceso.poll() is not None:
            return  # Finaliza si el servidor ya había terminado por su cuenta.

        if self._es_windows() and self._detener_arbol_windows(proceso):
            return  # En Windows termina también llama-server y cualquier otro proceso secundario asociado.

        self._detener_proceso_directamente(proceso)  # Conserva una alternativa cuando no puede utilizarse el cierre del árbol completo.

    def _es_windows(self) -> bool:
        return os.name == "nt"  # Permite utilizar el mecanismo específico de Windows únicamente cuando corresponde.

    def _detener_arbol_windows(self, proceso: subprocess.Popen) -> bool:
        banderas_creacion = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # Evita mostrar una consola mientras taskkill realiza la limpieza.

        try:
            subprocess.run(
                ["taskkill", "/PID", str(proceso.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=banderas_creacion,
                check=False,
            )  # Solicita a Windows cerrar el proceso principal y todos los procesos secundarios antes de que puedan quedar huérfanos.
        except OSError:
            return False  # Permite recurrir al cierre directo si taskkill no se encuentra disponible.

        try:
            proceso.wait(timeout=3.0)  # Confirma que Windows haya retirado el proceso principal después de cerrar su árbol.
        except (OSError, subprocess.TimeoutExpired):
            return False  # Activa la alternativa directa cuando el árbol no pudo cerrarse completamente.

        return proceso.poll() is not None  # Considera correcta la limpieza solamente cuando el proceso principal dejó de existir.

    def _detener_proceso_directamente(self, proceso: subprocess.Popen) -> None:
        if proceso.poll() is not None:
            return  # Evita solicitar otra terminación cuando el proceso desapareció durante la limpieza anterior.

        try:
            proceso.terminate()  # Solicita primero una terminación normal como mecanismo alternativo.
            proceso.wait(timeout=2.0)  # Permite liberar puerto y recursos antes de recurrir a un cierre forzado.
        except subprocess.TimeoutExpired:
            try:
                proceso.kill()  # Fuerza el cierre solamente cuando la terminación normal no fue suficiente.
                proceso.wait(timeout=1.0)  # Espera brevemente a que el sistema retire el proceso.
            except (OSError, subprocess.TimeoutExpired):
                pass  # Evita que un problema de limpieza impida cerrar TecNet Finder.
        except OSError:
            pass  # Ignora procesos que desaparecieron durante la operación de cierre.