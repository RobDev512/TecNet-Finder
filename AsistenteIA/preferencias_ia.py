# ============================================================
# Archivo: preferencias_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo conserva las preferencias del usuario relacionadas
# con la asistencia de inteligencia artificial local.
#
# Las preferencias se almacenan fuera del código fuente para que
# permanezcan disponibles entre ejecuciones e instalaciones de la
# aplicación sin formar parte del repositorio.
# ============================================================

import json  # Permite conservar las preferencias en un formato pequeño y legible.
import os  # Permite localizar la carpeta LocalAppData correspondiente al usuario.
from pathlib import Path  # Permite administrar la ubicación persistente sin utilizar rutas absolutas.


class PreferenciasIA:  # Administra únicamente las decisiones persistentes relacionadas con la asistencia local.
    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Comparte la carpeta administrada general de la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_ia.json"  # Mantiene separada la configuración de los archivos pesados del modelo.

    def asistencia_activada(self) -> bool:
        datos = self._leer_preferencias()  # Recupera únicamente información válida o una configuración vacía.

        valor = datos.get("asistencia_ia_activada", True)  # Mantiene activado por defecto el comportamiento existente de TecNet Finder.

        if isinstance(valor, bool):
            return valor  # Respeta únicamente valores booleanos explícitos.

        return True  # Recupera el valor seguro por defecto si el archivo contiene información inesperada.

    def establecer_asistencia_activada(self, activada: bool) -> bool:
        datos = self._leer_preferencias()  # Conserva posibles opciones adicionales que puedan agregarse posteriormente.
        datos["asistencia_ia_activada"] = bool(activada)  # Actualiza exclusivamente la preferencia correspondiente al asistente.

        try:
            self.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Prepara la carpeta persistente sin depender de una instalación previa de IA.
            ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Evita dejar el archivo principal incompleto si una escritura falla.
            ruta_temporal.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")  # Guarda la configuración completa antes de reemplazar la versión anterior.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye la configuración solamente después de completar correctamente la escritura.
            return True
        except OSError:
            return False  # Permite que la interfaz continúe aunque Windows no permita persistir la preferencia.

    def _leer_preferencias(self) -> dict:
        if not self.ruta_archivo.is_file():
            return {}  # Utiliza los valores predeterminados cuando todavía no existe configuración.

        try:
            datos = json.loads(self.ruta_archivo.read_text(encoding="utf-8"))  # Recupera la configuración persistente del usuario.
        except (OSError, json.JSONDecodeError):
            return {}  # Evita que un archivo dañado afecte al funcionamiento general de TecNet Finder.

        if not isinstance(datos, dict):
            return {}  # Descarta configuraciones cuya estructura no corresponde con la esperada.

        return datos  # Entrega únicamente una configuración estructuralmente válida.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Utiliza la carpeta oficial de datos locales cuando Windows la proporciona.

        if ruta_local:
            return Path(ruta_local)  # Evita depender del nombre concreto de la cuenta del usuario.

        return Path.home() / "AppData" / "Local"  # Mantiene una alternativa compatible cuando la variable no se encuentra definida.