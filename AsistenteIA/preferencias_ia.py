# ============================================================
# Archivo: preferencias_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo conserva las preferencias del usuario relacionadas
# con las funciones de inteligencia artificial local.
#
# Autocompletado y mejora de diagnósticos se guardan de forma
# independiente. También se conserva compatibilidad con la
# preferencia utilizada por versiones anteriores de TecNet Finder.
# ============================================================

import json  # Permite conservar las preferencias en un formato pequeño y legible.
import os  # Permite localizar la carpeta LocalAppData correspondiente al usuario.
from pathlib import Path  # Permite administrar la ubicación persistente sin utilizar rutas absolutas.


class PreferenciasIA:  # Administra las decisiones persistentes relacionadas con las funciones del asistente local.
    CLAVE_ANTERIOR = "asistencia_ia_activada"  # Reconoce el nombre utilizado antes de separar las funciones de IA.
    CLAVE_AUTOCOMPLETADO = "autocompletado_ia_activado"  # Identifica exclusivamente la preferencia del ghost text.
    CLAVE_DIAGNOSTICOS = "diagnosticos_ia_activados"  # Identifica exclusivamente la mejora automática de soluciones.

    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Comparte la carpeta administrada general de la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_ia.json"  # Mantiene separada la configuración de los archivos pesados del modelo.

    def autocompletado_activado(self) -> bool:
        datos = self._leer_preferencias()  # Recupera la configuración estructuralmente válida antes de consultar la función concreta.
        return self._obtener_booleano(datos, self.CLAVE_AUTOCOMPLETADO)  # Utiliza la preferencia nueva y migra lógicamente desde la clave anterior cuando todavía sea necesario.

    def diagnosticos_ia_activados(self) -> bool:
        datos = self._leer_preferencias()  # Recupera la misma configuración sin mezclarla con el estado físico del componente.
        return self._obtener_booleano(datos, self.CLAVE_DIAGNOSTICOS)  # Activa por defecto la nueva ayuda cuando la asistencia anterior también estaba habilitada.

    def alguna_funcion_activada(self) -> bool:
        return self.autocompletado_activado() or self.diagnosticos_ia_activados()  # Mantiene Ollama activo mientras al menos una función local lo necesite.

    def establecer_autocompletado_activado(self, activado: bool) -> bool:
        return self._guardar_booleano(self.CLAVE_AUTOCOMPLETADO, activado)  # Modifica únicamente el ghost text sin alterar la mejora de diagnósticos.

    def establecer_diagnosticos_ia_activados(self, activados: bool) -> bool:
        return self._guardar_booleano(self.CLAVE_DIAGNOSTICOS, activados)  # Modifica únicamente las soluciones generadas por IA.

    def asistencia_activada(self) -> bool:
        return self.autocompletado_activado()  # Mantiene compatible el nombre utilizado por código y pruebas anteriores.

    def establecer_asistencia_activada(self, activada: bool) -> bool:
        return self.establecer_autocompletado_activado(activada)  # Conserva compatibilidad sin volver a unir ambas preferencias.

    def _obtener_booleano(self, datos: dict, clave: str) -> bool:
        valor = datos.get(clave)  # Busca primero la preferencia independiente introducida por la versión actual.

        if isinstance(valor, bool):
            return valor  # Respeta exclusivamente estados booleanos explícitos.

        valor_anterior = datos.get(self.CLAVE_ANTERIOR, True)  # Utiliza la elección histórica como migración natural para instalaciones existentes.

        if isinstance(valor_anterior, bool):
            return valor_anterior  # Mantiene la experiencia previa sin exigir que el usuario configure nuevamente la IA.

        return True  # Recupera el valor seguro predeterminado cuando el archivo contiene información inesperada.

    def _guardar_booleano(self, clave: str, valor: bool) -> bool:
        datos = self._leer_preferencias()  # Conserva cualquier otra opción almacenada en el mismo archivo.
        datos[clave] = bool(valor)  # Actualiza exclusivamente la función solicitada.

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
