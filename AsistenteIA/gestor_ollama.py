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
# permite iniciar temporalmente el runtime durante su instalación
# y conserva información sobre cualquier problema ocurrido
# durante el arranque.
#
# En Windows también garantiza la limpieza de los procesos
# secundarios creados por Ollama.
# ============================================================

import os  # Permite construir el entorno privado y detectar el sistema operativo actual.
import subprocess  # Permite iniciar y detener Ollama junto con sus procesos secundarios.
import time  # Permite esperar mientras el servidor privado comienza a responder.

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
        self.tiempo_inicio_segundos = tiempo_inicio_segundos  # Conserva el tiempo normal permitido durante el arranque cotidiano.
        self.intervalo_comprobacion = intervalo_comprobacion  # Evita consultar continuamente la API durante el inicio.
        self._proceso: subprocess.Popen | None = None  # Conserva únicamente el proceso principal creado por esta instancia.
        self._iniciado_por_aplicacion = False  # Permite distinguir procesos propios de servidores previamente activos.
        self.ultimo_error_inicio = ""  # Conserva una explicación controlada cuando el servicio no consigue iniciar.

    @property
    def iniciado_por_aplicacion(self) -> bool:
        return self._iniciado_por_aplicacion  # Permite consultar la propiedad del proceso sin exponer su manipulación.

    def iniciar(
        self,
        requerir_modelo: bool = True,
        tiempo_inicio_segundos: float | None = None,
    ) -> bool:
        self.ultimo_error_inicio = ""  # Descarta cualquier problema perteneciente a un intento anterior.

        if self.motor.disponible():
            return True  # Reutiliza la instancia privada cuando ya se encuentra activa.

        if requerir_modelo and not self.componente_ia.instalado():
            self.ultimo_error_inicio = "El componente completo de asistencia de IA no se encuentra instalado."  # Explica por qué no puede iniciarse un uso normal.
            return False  # Mantiene TecNet Finder operativo cuando falta runtime o modelo.

        if not requerir_modelo and not self.componente_ia.ruta_ejecutable_ollama.is_file():
            self.ultimo_error_inicio = "No se encontró el ejecutable privado de Ollama después de preparar el runtime."  # Diferencia un problema de archivos de un fallo del servidor.
            return False  # Impide continuar una instalación cuyo ejecutable no existe.

        ruta_ollama = self.componente_ia.ruta_ejecutable_ollama  # Obtiene el ejecutable desde la instalación opcional administrada.
        ruta_modelos = self.componente_ia.ruta_modelos  # Obtiene el almacén privado utilizado exclusivamente por TecNet Finder.

        try:
            ruta_modelos.mkdir(parents=True, exist_ok=True)  # Prepara el almacén incluso durante una instalación todavía sin modelo.
        except OSError as error:
            self.ultimo_error_inicio = f"No fue posible preparar la carpeta privada de modelos: {error}"  # Conserva la causa concreta para diagnóstico.
            return False  # Evita iniciar Ollama con una ubicación de modelos inutilizable.

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
        except OSError as error:
            self._proceso = None  # Elimina cualquier referencia incompleta tras un fallo de creación.
            self.ultimo_error_inicio = f"Windows no pudo iniciar el ejecutable privado de Ollama: {error}"  # Conserva la causa reportada por el sistema.
            return False  # Mantiene disponible el resto de TecNet Finder.

        self._iniciado_por_aplicacion = True  # Registra la propiedad antes de esperar la disponibilidad de la API.

        tiempo_permitido = (
            self.tiempo_inicio_segundos
            if tiempo_inicio_segundos is None
            else max(0.0, float(tiempo_inicio_segundos))
        )  # Permite que una primera instalación espere más sin ralentizar los arranques normales.

        limite = time.monotonic() + tiempo_permitido  # Calcula un límite independiente de cambios en el reloj del sistema.

        while time.monotonic() < limite:
            codigo_salida = self._proceso.poll()  # Comprueba si el proceso terminó antes de que la API pudiera responder.

            if codigo_salida is not None:
                self._proceso = None  # Descarta inmediatamente una referencia hacia un proceso ya terminado.
                self._iniciado_por_aplicacion = False  # Libera la propiedad del proceso inexistente.
                self.ultimo_error_inicio = f"El proceso privado de Ollama terminó durante el inicio con código {codigo_salida}."  # Permite distinguir un cierre real de un simple retraso.
                return False  # Informa que el servicio no consiguió permanecer activo.

            if self.motor.disponible():
                self.ultimo_error_inicio = ""  # Confirma que no existe ningún problema pendiente después de responder la API.
                return True  # Finaliza el arranque tan pronto como la instancia privada responde.

            time.sleep(self.intervalo_comprobacion)  # Evita una espera activa mientras Ollama prepara sus bibliotecas y servidor.

        self.ultimo_error_inicio = f"El servicio privado de Ollama no respondió después de {tiempo_permitido:g} segundos."  # Explica explícitamente cuando el proceso permaneció vivo pero tardó demasiado.
        self.detener()  # Retira un proceso que no consiguió quedar disponible dentro del tiempo permitido.
        return False  # Mantiene TecNet Finder operativo sin asistencia de IA.

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
            )  # Solicita a Windows cerrar el proceso principal y todos sus procesos secundarios.
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