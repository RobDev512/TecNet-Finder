# ============================================================
# Archivo: preferencias_tema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra exclusivamente la preferencia persistente del tema
# utilizado por TecNet Finder.
#
# Se mantiene en un archivo independiente para evitar cargar
# PreferenciasAplicacion con responsabilidades visuales nuevas.
#
# El archivo se almacena dentro de:
# LocalAppData/TecNetFinder/preferencias_tema.json
# ============================================================

import json  # Permite almacenar la preferencia mediante un archivo estructurado.
import os  # Permite consultar LocalAppData proporcionado por Windows.
from pathlib import Path  # Permite construir rutas independientes del usuario.
from Motor.catalogo_temas import TEMA_PREDETERMINADO, normalizar_tema, tema_existe  # Proporciona validación centralizada del catálogo.


class PreferenciasTema:
    CLAVE_TEMA = "tema"  # Define la única clave persistente administrada por este componente.

    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite utilizar carpetas temporales durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Reutiliza la carpeta general de datos locales de la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_tema.json"  # Mantiene esta configuración separada de las demás preferencias.

    def tema(self) -> str:
        datos = self._leer()  # Recupera la información persistida de forma segura.
        return normalizar_tema(datos.get(self.CLAVE_TEMA, TEMA_PREDETERMINADO))  # Devuelve siempre un identificador válido aunque el archivo haya sido editado externamente.

    def establecer_tema(self, tema_id: str) -> bool:
        if not tema_existe(tema_id):  # Comprueba que el valor pertenezca realmente al catálogo actual.
            return False  # Rechaza identificadores desconocidos sin modificar el archivo.
        return self._guardar({self.CLAVE_TEMA: tema_id})  # Persiste únicamente una selección previamente validada.

    def restablecer(self) -> bool:
        return self.establecer_tema(TEMA_PREDETERMINADO)  # Recupera de forma explícita la apariencia oficial de TecNet Finder.

    def _leer(self) -> dict:
        if not self.ruta_archivo.is_file():  # Comprueba si todavía no existe ninguna preferencia guardada.
            return {}  # Permite utilizar automáticamente el tema predeterminado.
        try:  # Protege el inicio frente a archivos corruptos o inaccesibles.
            datos = json.loads(self.ruta_archivo.read_text(encoding="utf-8"))  # Convierte el JSON almacenado en una estructura de Python.
        except (OSError, json.JSONDecodeError):  # Captura problemas del sistema de archivos o contenido inválido.
            return {}  # Recupera silenciosamente los valores seguros.
        return datos if isinstance(datos, dict) else {}  # Acepta únicamente un objeto JSON como configuración válida.

    def _guardar(self, cambios: dict) -> bool:
        datos = self._leer()  # Conserva cualquier clave futura que pudiera coexistir en este archivo.
        datos.update(cambios)  # Sustituye únicamente las preferencias solicitadas.
        try:  # Protege la aplicación frente a errores de escritura.
            self.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de datos cuando todavía no existe.
            ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Utiliza un archivo temporal para evitar dejar JSON incompleto.
            ruta_temporal.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")  # Guarda la configuración de manera legible.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye el archivo definitivo solamente después de terminar la escritura.
            return True  # Confirma que la preferencia fue persistida.
        except OSError:  # Captura cualquier problema del sistema de archivos.
            return False  # Mantiene TecNet Finder funcional aunque no pueda guardar la preferencia.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Consulta la ubicación oficial utilizada por Windows.
        return Path(ruta_local) if ruta_local else Path.home() / "AppData" / "Local"  # Conserva una alternativa segura cuando la variable no existe.