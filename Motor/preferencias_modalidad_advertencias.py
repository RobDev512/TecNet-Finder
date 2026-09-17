# ============================================================
# Archivo: preferencias_modalidad_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra exclusivamente el comportamiento modal de la
# ventana independiente de advertencias.
#
# Se mantiene en un archivo separado para evitar seguir
# aumentando PreferenciasAplicacion con opciones especializadas.
# ============================================================

import json  # Permite almacenar la preferencia mediante un archivo estructurado.
import os  # Permite localizar LocalAppData en Windows.
from pathlib import Path  # Permite construir rutas seguras e independientes del usuario.


class PreferenciasModalidadAdvertencias:  # Administra solamente si Advertencias debe bloquear la ventana principal.
    CLAVE_BLOQUEAR_INTERACCION = "bloquear_interaccion_fondo"  # Identifica la única preferencia administrada por este componente.
    BLOQUEAR_INTERACCION_PREDETERMINADO = True  # Conserva como comportamiento inicial el bloqueo solicitado actualmente.

    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Reutiliza la carpeta general de datos de la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_modalidad_advertencias.json"  # Separa esta decisión especializada de las preferencias generales.

    def bloquear_interaccion_fondo(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_BLOQUEAR_INTERACCION, self.BLOQUEAR_INTERACCION_PREDETERMINADO)  # Recupera el valor persistido o el comportamiento seguro.
        return valor if isinstance(valor, bool) else self.BLOQUEAR_INTERACCION_PREDETERMINADO  # Rechaza información incompatible.

    def establecer_bloquear_interaccion_fondo(self, bloquear: bool) -> bool:
        return self._guardar_valor(self.CLAVE_BLOQUEAR_INTERACCION, bool(bloquear))  # Persiste la decisión normalizada.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta = os.environ.get("LOCALAPPDATA")  # Consulta la ubicación oficial proporcionada por Windows.
        if ruta: return Path(ruta)  # Utiliza directamente LocalAppData cuando se encuentra disponible.
        return Path.home() / "AppData" / "Local"  # Conserva una ruta equivalente como respaldo.

    def _leer_preferencias(self) -> dict:
        if not self.ruta_archivo.exists(): return {}  # Evita considerar error la primera ejecución.
        try:
            contenido = json.loads(self.ruta_archivo.read_text(encoding="utf-8"))  # Decodifica el archivo persistente.
            return contenido if isinstance(contenido, dict) else {}  # Conserva exclusivamente una estructura válida.
        except (OSError, json.JSONDecodeError, UnicodeError):
            return {}  # Recupera valores predeterminados ante un archivo dañado o inaccesible.

    def _guardar_valor(self, clave: str, valor) -> bool:
        preferencias = self._leer_preferencias()  # Conserva cualquier dato previamente almacenado.
        preferencias[clave] = valor  # Sustituye únicamente la preferencia solicitada.
        ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Prepara una escritura temporal antes de reemplazar el archivo real.

        try:
            self.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Garantiza la existencia de la carpeta de datos.
            ruta_temporal.write_text(json.dumps(preferencias, ensure_ascii=False, indent=4), encoding="utf-8")  # Escribe primero una copia completa y válida.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye el archivo real solamente después de terminar correctamente.
            return True  # Informa que la preferencia quedó persistida.
        except OSError:
            try:
                if ruta_temporal.exists(): ruta_temporal.unlink()  # Retira una copia temporal incompleta cuando sea posible.
            except OSError:
                pass  # Evita convertir la limpieza secundaria en otro fallo visible.
            return False  # Informa al sistema de Configuración que la escritura no pudo completarse.