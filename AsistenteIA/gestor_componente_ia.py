# ============================================================
# Archivo: gestor_componente_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo representa la instalación opcional del componente
# de inteligencia artificial local de TecNet Finder.
#
# Centraliza sus rutas, permite conocer si el componente se
# encuentra instalado y administra la eliminación segura de los
# archivos que pertenecen exclusivamente a TecNet Finder.
#
# La desinstalación utiliza varios intentos porque Windows puede
# tardar brevemente en liberar bibliotecas después de terminar
# los procesos locales de Ollama.
# ============================================================

import os  # Permite localizar la carpeta LocalAppData correspondiente al usuario actual.
from pathlib import Path  # Permite administrar las rutas del componente independientemente del directorio de ejecución.
import shutil  # Permite retirar completamente los archivos administrados por TecNet Finder.
import time  # Permite esperar brevemente entre intentos cuando Windows todavía está liberando archivos.


class GestorComponenteIA:  # Representa el componente opcional de inteligencia artificial instalado para el usuario.
    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante pruebas.
        self.ruta_base = self.ruta_datos_locales / "TecNetFinder" / "IA"  # Mantiene el componente fuera del código fuente y de la instalación principal.
        self.ruta_ollama = self.ruta_base / "Ollama"  # Reserva un directorio independiente para el runtime privado.
        self.ruta_ejecutable_ollama = self.ruta_ollama / "ollama.exe"  # Identifica el ejecutable que deberá controlar GestorOllama.
        self.ruta_modelos = self.ruta_ollama / "modelos"  # Conserva los modelos utilizados exclusivamente por TecNet Finder.

    def instalado(self) -> bool:
        if not self.ruta_ejecutable_ollama.is_file():
            return False  # Considera incompleta cualquier instalación que no conserve el runtime requerido.

        if not self.ruta_modelos.is_dir():
            return False  # Exige también la ubicación privada destinada al modelo.

        return any(archivo.is_file() for archivo in self.ruta_modelos.rglob("*"))  # Reconoce la instalación solamente cuando existe al menos un archivo perteneciente al modelo.

    def preparar_directorio(self) -> bool:
        try:
            self.ruta_base.mkdir(parents=True, exist_ok=True)  # Prepara únicamente la carpeta administrada correspondiente al componente opcional.
            return True  # Confirma que la ubicación quedó disponible para una instalación posterior.
        except OSError:
            return False  # Mantiene controlado cualquier problema de permisos o almacenamiento.

    def desinstalar_archivos(
        self,
        intentos: int = 8,
        espera_segundos: float = 0.25,
    ) -> bool:
        if not self.ruta_base.exists():
            return True  # Considera terminada la operación cuando el componente ya no posee archivos administrados.

        total_intentos = max(1, int(intentos))  # Garantiza que siempre exista al menos una oportunidad real de eliminación.
        pausa = max(0.0, float(espera_segundos))  # Evita tiempos negativos cuando una prueba sustituye los valores predeterminados.

        for numero_intento in range(total_intentos):
            try:
                shutil.rmtree(self.ruta_base)  # Intenta retirar exclusivamente la carpeta dedicada a la asistencia de IA.
            except OSError:
                if numero_intento == total_intentos - 1:
                    return False  # Declara fallo solamente después de agotar todos los intentos permitidos.

                if pausa > 0:
                    time.sleep(pausa)  # Permite a Windows terminar de liberar DLL y ejecutables después del cierre de Ollama.

                continue  # Reintenta sobre los archivos restantes que todavía no pudieron eliminarse.

            if not self.ruta_base.exists():
                return True  # Finaliza inmediatamente cuando desapareció completamente la carpeta administrada.

            if numero_intento < total_intentos - 1 and pausa > 0:
                time.sleep(pausa)  # Espera también cuando la operación terminó sin excepción pero aún quedan archivos visibles.

        return not self.ruta_base.exists()  # Realiza una última comprobación física antes de informar el resultado.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Utiliza la ubicación oficial de datos locales cuando Windows la proporciona.

        if ruta_local:
            return Path(ruta_local)  # Evita depender del nombre concreto de la cuenta del usuario.

        return Path.home() / "AppData" / "Local"  # Mantiene una alternativa compatible cuando la variable de entorno no se encuentra disponible.