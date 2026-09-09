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
# encuentra instalado y prepara la futura instalación,
# reparación y desinstalación independiente de la aplicación.
# ============================================================

import os  # Permite localizar la carpeta LocalAppData correspondiente al usuario actual.
from pathlib import Path  # Permite administrar las rutas del componente de forma independiente al directorio de ejecución.
import shutil  # Permite retirar completamente los archivos administrados por TecNet Finder.


class GestorComponenteIA:  # Representa el componente opcional de inteligencia artificial instalado para el usuario.
    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante pruebas.
        self.ruta_base = self.ruta_datos_locales / "TecNetFinder" / "IA"  # Mantiene el componente fuera del código fuente y de la instalación principal.
        self.ruta_ollama = self.ruta_base / "Ollama"  # Reserva un directorio independiente para el runtime privado.
        self.ruta_ejecutable_ollama = self.ruta_ollama / "ollama.exe"  # Identifica el ejecutable que deberá controlar GestorOllama.
        self.ruta_modelos = self.ruta_ollama / "modelos"  # Conserva los modelos utilizados exclusivamente por TecNet Finder.

    def instalado(self) -> bool:
        if not self.ruta_ejecutable_ollama.is_file():
            return False  # Considera ausente el componente cuando no existe el runtime necesario.

        if not self.ruta_modelos.is_dir():
            return False  # Exige también el almacén privado de modelos.

        return any(archivo.is_file() for archivo in self.ruta_modelos.rglob("*"))  # Exige al menos un archivo de modelo antes de considerar completa la instalación.

    def preparar_directorio(self) -> bool:
        try:
            self.ruta_base.mkdir(parents=True, exist_ok=True)  # Prepara la ubicación administrada para una instalación futura.
            return True
        except OSError:
            return False  # Permite informar un fallo sin afectar al compilador principal.

    def desinstalar_archivos(self) -> bool:
        if not self.ruta_base.exists():
            return True  # Considera completada la operación cuando el componente ya estaba ausente.

        try:
            shutil.rmtree(self.ruta_base)  # Elimina exclusivamente el directorio dedicado al componente de TecNet Finder.
        except OSError:
            return False  # Permite que la interfaz informe cuando algún archivo se encuentra bloqueado.

        return not self.ruta_base.exists()  # Confirma que la instalación opcional haya desaparecido completamente.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Utiliza la ubicación oficial de datos locales del usuario en Windows.

        if ruta_local:
            return Path(ruta_local)  # Evita depender de una ruta fija o del nombre concreto de la cuenta.

        return Path.home() / "AppData" / "Local"  # Mantiene una alternativa razonable cuando la variable no se encuentra disponible.