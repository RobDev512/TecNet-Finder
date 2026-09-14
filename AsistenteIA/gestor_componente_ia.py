# ============================================================
# Archivo: gestor_componente_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo representa la instalación opcional del componente
# de inteligencia artificial local de TecNet Finder.
#
# Centraliza sus rutas, permite saber si el componente se
# encuentra instalado y administra la eliminación segura de los
# archivos pertenecientes exclusivamente a TecNet Finder.
#
# La desinstalación utiliza varios intentos porque Windows puede
# tardar brevemente en liberar archivos después de terminar los
# procesos locales utilizados por Ollama.
# ============================================================

import os  # Permite localizar LocalAppData para almacenar el componente dentro de los datos privados del usuario.
from pathlib import Path  # Permite construir las rutas del componente sin depender del directorio actual de ejecución.
import shutil  # Permite retirar completamente la carpeta administrada correspondiente con la inteligencia artificial.
import time  # Permite esperar entre intentos cuando Windows todavía mantiene archivos del componente en uso.


class GestorComponenteIA:  # Administra las rutas y el estado físico del componente opcional de inteligencia artificial.
    def __init__(self, ruta_datos_locales: str | Path | None = None):  # Prepara todas las ubicaciones utilizadas por la instalación privada.
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite utilizar una ubicación temporal durante pruebas.
        self.ruta_base = self.ruta_datos_locales / "TecNetFinder" / "IA"  # Mantiene la IA fuera del código fuente y de la instalación principal.
        self.ruta_ollama = self.ruta_base / "Ollama"  # Reserva una carpeta privada para el runtime administrado por TecNet Finder.
        self.ruta_ejecutable_ollama = self.ruta_ollama / "ollama.exe"  # Identifica exactamente el ejecutable que controlará GestorOllama.
        self.ruta_modelos = self.ruta_ollama / "modelos"  # Conserva los modelos descargados exclusivamente para TecNet Finder.

    def instalado(self) -> bool:  # Comprueba que existan los elementos mínimos requeridos para considerar instalada la IA.
        if not self.ruta_ejecutable_ollama.is_file():  # Verifica primero la existencia del runtime privado de Ollama.
            return False  # Considera incompleta cualquier instalación que haya perdido su ejecutable.

        if not self.ruta_modelos.is_dir():  # Comprueba también que exista la carpeta donde deben conservarse los modelos.
            return False  # Rechaza instalaciones que no posean la estructura esperada.

        return any(archivo.is_file() for archivo in self.ruta_modelos.rglob("*"))  # Confirma finalmente que exista al menos un archivo real perteneciente al modelo.

    def preparar_directorio(self) -> bool:  # Prepara la carpeta raíz antes de iniciar una instalación del componente.
        try:  # Intenta crear toda la estructura faltante sin eliminar contenido existente.
            self.ruta_base.mkdir(parents=True, exist_ok=True)  # Crea exclusivamente la ubicación administrada por TecNet Finder.
            return True  # Confirma al instalador que ya puede utilizar la carpeta.
        except OSError:  # Atiende errores de permisos, almacenamiento o acceso al sistema de archivos.
            return False  # Permite que la interfaz informe el problema sin cerrar la aplicación.

    def desinstalar_archivos(self, intentos: int = 8, espera_segundos: float = 0.25) -> bool:  # Elimina el componente permitiendo varios intentos ante bloqueos temporales de Windows.
        if not self.ruta_base.exists():  # Comprueba si todavía existe algún contenido administrado por la aplicación.
            return True  # Considera terminada la desinstalación cuando la carpeta ya desapareció.

        total_intentos = max(1, int(intentos))  # Garantiza que siempre exista al menos un intento real de eliminación.
        pausa = max(0.0, float(espera_segundos))  # Evita utilizar tiempos negativos si una prueba proporciona parámetros diferentes.

        for numero_intento in range(total_intentos):  # Repite la eliminación hasta completar la operación o agotar los intentos permitidos.
            try:  # Intenta retirar toda la carpeta privada del componente.
                shutil.rmtree(self.ruta_base)  # Elimina únicamente archivos pertenecientes a la IA administrada por TecNet Finder.
            except OSError:  # Atiende principalmente archivos que Windows todavía mantiene bloqueados.
                if numero_intento == total_intentos - 1:  # Comprueba si acaba de agotarse la última oportunidad disponible.
                    return False  # Informa que la desinstalación no logró completar la eliminación.

                if pausa > 0:  # Comprueba si se configuró un tiempo real de espera entre reintentos.
                    time.sleep(pausa)  # Permite que Windows termine de liberar ejecutables, DLL u otros archivos utilizados por Ollama.

                continue  # Regresa al siguiente intento después de esperar la liberación de los archivos.

            if not self.ruta_base.exists():  # Comprueba físicamente si la eliminación terminó correctamente.
                return True  # Finaliza inmediatamente porque ya no existe ningún contenido administrado.

            if numero_intento < total_intentos - 1 and pausa > 0:  # Determina si todavía quedan reintentos y se permite realizar una pausa.
                time.sleep(pausa)  # Espera antes de volver a intentar retirar cualquier contenido restante.

        return not self.ruta_base.exists()  # Realiza una última comprobación física antes de informar el resultado definitivo.

    def _obtener_ruta_datos_locales(self) -> Path:  # Determina dónde se almacenará físicamente el componente para el usuario actual.
        ruta_local = os.environ.get("LOCALAPPDATA")  # Consulta la carpeta oficial destinada por Windows a los datos locales.

        if ruta_local:  # Comprueba si Windows proporcionó correctamente esa ubicación.
            return Path(ruta_local)  # Utiliza la carpeta oficial sin depender del nombre concreto de la cuenta.

        return Path.home() / "AppData" / "Local"  # Mantiene una ruta equivalente como respaldo si la variable no está disponible.