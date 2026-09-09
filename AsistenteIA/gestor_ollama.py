# ============================================================
# Archivo: gestor_ollama.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo administra el ciclo de vida de la instancia privada
# de Ollama utilizada por TecNet Finder.
#
# Reutiliza un servidor existente cuando ya se encuentra activo,
# inicia silenciosamente el runtime local cuando hace falta y
# solamente detiene procesos que fueron creados por la propia
# aplicación. Cualquier fallo mantiene disponible el compilador
# aunque el asistente de inteligencia artificial quede inactivo.
# ============================================================

import os  # Permite construir un entorno exclusivo para la instancia privada de Ollama.
from pathlib import Path  # Permite resolver las dependencias locales sin depender del directorio desde donde se ejecute la aplicación.
import subprocess  # Permite iniciar y detener el servidor local como un proceso independiente.
import time  # Permite esperar brevemente mientras Ollama comienza a escuchar en su puerto privado.

from AsistenteIA.configuracion import HOST_OLLAMA, PUERTO_OLLAMA  # Importa la dirección reservada para la instancia propia de TecNet Finder.
from AsistenteIA.motor_local import MotorLocalOllama  # Permite comprobar cuándo la API privada se encuentra disponible.


class GestorOllama:  # Controla exclusivamente el servidor local requerido por las funciones de inteligencia artificial.
    def __init__(
        self,
        motor: MotorLocalOllama | None = None,
        ruta_proyecto: str | Path | None = None,
        tiempo_inicio_segundos: float = 5.0,
        intervalo_comprobacion: float = 0.1,
    ):
        self.motor = motor or MotorLocalOllama()  # Reutiliza el mismo tipo de cliente HTTP empleado por el asistente.
        self.ruta_proyecto = Path(ruta_proyecto) if ruta_proyecto else Path(__file__).resolve().parent.parent  # Localiza automáticamente la raíz de TecNet Finder.
        self.ruta_ollama = self.ruta_proyecto / "Dependencias" / "Ollama" / "ollama.exe"  # Apunta al runtime independiente incluido localmente.
        self.ruta_modelos = self.ruta_proyecto / "Dependencias" / "Ollama" / "modelos"  # Apunta exclusivamente al almacén privado de modelos.
        self.tiempo_inicio_segundos = tiempo_inicio_segundos  # Limita cuánto tiempo puede retrasarse el arranque esperando al servidor.
        self.intervalo_comprobacion = intervalo_comprobacion  # Evita consultar continuamente la API mientras Ollama inicia.
        self._proceso: subprocess.Popen | None = None  # Conserva únicamente el proceso que haya sido creado por esta instancia del gestor.
        self._iniciado_por_aplicacion = False  # Distingue un servidor propio de otro que ya estuviera ejecutándose.

    @property
    def iniciado_por_aplicacion(self) -> bool:
        return self._iniciado_por_aplicacion  # Permite conocer la propiedad del proceso sin exponer su manipulación directa.

    def iniciar(self) -> bool:
        if self.motor.disponible():
            return True  # Reutiliza el servidor existente y evita crear o reclamar un proceso ajeno.

        if not self.ruta_ollama.is_file():
            return False  # Mantiene TecNet Finder operativo cuando el runtime local no se encuentra instalado.

        if not self.ruta_modelos.is_dir():
            return False  # Evita iniciar Ollama sin el almacén privado que contiene el modelo de la aplicación.

        entorno = os.environ.copy()  # Conserva las variables normales del sistema antes de aislar la configuración de Ollama.
        entorno["OLLAMA_HOST"] = f"{HOST_OLLAMA}:{PUERTO_OLLAMA}"  # Obliga al proceso privado a utilizar exclusivamente el puerto reservado.
        entorno["OLLAMA_MODELS"] = str(self.ruta_modelos)  # Evita utilizar accidentalmente el almacén global del usuario.
        entorno["OLLAMA_NO_CLOUD"] = "true"  # Mantiene esta instancia orientada exclusivamente a los modelos locales de TecNet Finder.

        banderas_creacion = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # Impide que Windows muestre una consola negra para el servidor interno.

        try:
            self._proceso = subprocess.Popen(
                [str(self.ruta_ollama), "serve"],
                cwd=str(self.ruta_ollama.parent),
                env=entorno,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=banderas_creacion,
            )  # Inicia Ollama silenciosamente y sin conectar su salida con la interfaz gráfica.
        except OSError:
            self._proceso = None  # Elimina cualquier referencia incompleta si Windows no pudo crear el proceso.
            return False  # Permite continuar utilizando el resto de TecNet Finder.

        self._iniciado_por_aplicacion = True  # Registra inmediatamente la propiedad para poder limpiar incluso un arranque incompleto.
        limite = time.monotonic() + self.tiempo_inicio_segundos  # Calcula un límite independiente de cambios en el reloj del sistema.

        while time.monotonic() < limite:
            if self._proceso.poll() is not None:
                self._proceso = None  # Descarta la referencia cuando Ollama terminó antes de llegar a estar disponible.
                self._iniciado_por_aplicacion = False  # Ya no existe ningún proceso propio que deba cerrarse posteriormente.
                return False  # Mantiene la aplicación abierta aunque la dependencia haya fallado.

            if self.motor.disponible():
                return True  # Finaliza la espera tan pronto como la API privada acepta conexiones.

            time.sleep(self.intervalo_comprobacion)  # Deja un pequeño intervalo entre intentos para evitar espera activa.

        self.detener()  # Elimina el proceso que no consiguió iniciar correctamente dentro del tiempo permitido.
        return False  # Indica que la IA permanecerá inactiva durante esta ejecución.

    def detener(self) -> None:
        if not self._iniciado_por_aplicacion or self._proceso is None:
            return  # Nunca intenta detener un Ollama que ya estuviera activo antes de abrir TecNet Finder.

        proceso = self._proceso  # Conserva una referencia local mientras se limpia inmediatamente el estado del gestor.
        self._proceso = None  # Evita intentar cerrar dos veces el mismo proceso.
        self._iniciado_por_aplicacion = False  # Libera la propiedad antes de realizar operaciones que podrían fallar.

        if proceso.poll() is not None:
            return  # No realiza ninguna acción adicional si Ollama ya terminó por sí mismo.

        try:
            proceso.terminate()  # Solicita primero un cierre normal del servidor privado.
            proceso.wait(timeout=2.0)  # Permite que Ollama libere el puerto y sus recursos antes de forzar el cierre.
        except subprocess.TimeoutExpired:
            try:
                proceso.kill()  # Fuerza el cierre únicamente si el proceso ignoró la terminación normal.
                proceso.wait(timeout=1.0)  # Espera brevemente para evitar dejar el proceso en segundo plano.
            except (OSError, subprocess.TimeoutExpired):
                pass  # Evita que un fallo de limpieza impida cerrar TecNet Finder.
        except OSError:
            pass  # Considera irrelevante un proceso que desapareció durante la operación de cierre.