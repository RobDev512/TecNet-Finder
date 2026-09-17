# ============================================================
# Archivo: preferencias_tema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra exclusivamente la preferencia persistente del tema
# utilizado por TecNet Finder.
#
# Mientras el usuario no seleccione manualmente una variante,
# TecNet Finder utiliza el modo claro u oscuro configurado en el
# sistema y elige la variante TecNet equivalente.
#
# Al confirmar un tema diferente desde Configuración se conserva
# esa elección manual para las ejecuciones posteriores.
#
# El archivo se almacena dentro de:
# LocalAppData/TecNetFinder/preferencias_tema.json
# ============================================================

import json  # Permite almacenar la preferencia mediante un archivo estructurado.
import os  # Permite consultar LocalAppData proporcionado por Windows.
from pathlib import Path  # Permite construir rutas independientes del usuario.
from Motor.configuracion.catalogo_temas import TEMA_CLARO_TECNET, TEMA_OSCURO_TECNET, TEMA_PREDETERMINADO, normalizar_tema, tema_existe  # Proporciona validación centralizada del catálogo.
from Motor.configuracion.detector_tema_sistema import tema_recomendado_sistema  # Proporciona la variante adecuada mientras no exista una elección manual.


class PreferenciasTema:
    CLAVE_TEMA = "tema"  # Conserva la variante utilizada cuando existe una selección manual.
    CLAVE_ORIGEN = "origen"  # Distingue automáticamente una preferencia manual de la selección basada en el sistema.
    ORIGEN_AUTOMATICO = "sistema"  # Indica que TecNet Finder debe detectar el modo del sistema al iniciar.
    ORIGEN_MANUAL = "manual"  # Indica que el usuario ya eligió explícitamente un tema propio.

    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite utilizar carpetas temporales durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Reutiliza la carpeta general de datos locales de la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_tema.json"  # Mantiene esta configuración separada de las demás preferencias.

    def tema(self) -> str:
        datos = self._leer()  # Recupera la información persistida de forma segura.
        if self._origen(datos) == self.ORIGEN_AUTOMATICO: return tema_recomendado_sistema()  # Sigue el modo del sistema mientras todavía no existe una selección manual.
        return normalizar_tema(datos.get(self.CLAVE_TEMA, TEMA_PREDETERMINADO))  # Devuelve siempre un identificador manual válido aunque el archivo haya sido editado externamente.

    def utiliza_modo_sistema(self) -> bool:
        return self._origen(self._leer()) == self.ORIGEN_AUTOMATICO  # Permite consultar explícitamente si la apariencia todavía es automática.

    def establecer_tema(self, tema_id: str) -> bool:
        if not tema_existe(tema_id): return False  # Rechaza identificadores desconocidos sin modificar el archivo.
        tema_id = normalizar_tema(tema_id)  # Normaliza la variante antes de compararla y almacenarla.
        if self.utiliza_modo_sistema() and tema_id == self.tema(): return True  # Evita convertir una preferencia automática en manual cuando Configuración confirma otros cambios sin tocar el tema.
        return self._guardar({self.CLAVE_TEMA: tema_id, self.CLAVE_ORIGEN: self.ORIGEN_MANUAL})  # Guarda la variante y marca desde ese momento la elección como manual.

    def restablecer(self) -> bool:
        return self._guardar({self.CLAVE_TEMA: TEMA_PREDETERMINADO, self.CLAVE_ORIGEN: self.ORIGEN_AUTOMATICO})  # Recupera la detección automática del sistema y conserva un respaldo válido.

    def _origen(self, datos: dict) -> str:
        origen = datos.get(self.CLAVE_ORIGEN)  # Recupera el origen almacenado por las versiones nuevas.
        if origen == self.ORIGEN_AUTOMATICO: return self.ORIGEN_AUTOMATICO  # Respeta una selección automática guardada explícitamente.
        if origen == self.ORIGEN_MANUAL and tema_existe(datos.get(self.CLAVE_TEMA)): return self.ORIGEN_MANUAL  # Respeta una elección manual declarada expresamente por una versión nueva.
        tema_guardado = datos.get(self.CLAVE_TEMA)  # Recupera una posible preferencia creada por versiones anteriores que todavía no conocían el campo origen.
        if tema_guardado in (TEMA_OSCURO_TECNET, TEMA_CLARO_TECNET): return self.ORIGEN_AUTOMATICO  # Migra solamente las variantes TecNet base a seguimiento del sistema porque representan la apariencia predeterminada de cada modo.
        if tema_existe(tema_guardado): return self.ORIGEN_MANUAL  # Conserva Medianoche, Océano o Niebla como decisiones explícitas del usuario.
        return self.ORIGEN_AUTOMATICO  # Utiliza el sistema cuando nunca existió una selección válida o el archivo está dañado.

    def _leer(self) -> dict:
        if not self.ruta_archivo.is_file(): return {}  # Permite utilizar automáticamente el tema del sistema durante la primera ejecución.
        try: datos = json.loads(self.ruta_archivo.read_text(encoding="utf-8"))  # Convierte el JSON almacenado en una estructura de Python.
        except (OSError, json.JSONDecodeError): return {}  # Recupera silenciosamente el modo automático ante archivos corruptos o inaccesibles.
        return datos if isinstance(datos, dict) else {}  # Acepta únicamente un objeto JSON como configuración válida.

    def _guardar(self, cambios: dict) -> bool:
        datos = self._leer()  # Conserva cualquier clave futura que pudiera coexistir en este archivo.
        datos.update(cambios)  # Sustituye únicamente las preferencias solicitadas.
        try:
            self.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta de datos cuando todavía no existe.
            ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Utiliza un archivo temporal para evitar dejar JSON incompleto.
            ruta_temporal.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")  # Guarda la configuración de manera legible.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye el archivo definitivo solamente después de terminar la escritura.
            return True  # Confirma que la preferencia fue persistida.
        except OSError:
            return False  # Mantiene TecNet Finder funcional aunque no pueda guardar la preferencia.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Consulta la ubicación oficial utilizada por Windows.
        return Path(ruta_local) if ruta_local else Path.home() / "AppData" / "Local"  # Conserva una alternativa segura cuando la variable no existe.
