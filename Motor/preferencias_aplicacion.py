# ============================================================
# Archivo: preferencias_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo administra las preferencias generales persistentes
# de TecNet Finder que no pertenecen a la inteligencia artificial.
#
# Conserva el lado predeterminado utilizado por Media pantalla,
# la navegación automática después de compilar y la visibilidad
# del panel compacto de advertencias situado debajo de Tabla VLSM.
#
# Las preferencias se almacenan dentro de LocalAppData para no
# mezclar configuración personal con el código fuente del proyecto.
# ============================================================

import json  # Permite guardar las preferencias generales mediante una estructura sencilla y legible.
import os  # Permite localizar la carpeta LocalAppData correspondiente con la cuenta actual de Windows.
from pathlib import Path  # Permite administrar rutas persistentes sin depender de nombres concretos de usuario.


class PreferenciasAplicacion:  # Administra las preferencias generales que deben conservarse entre ejecuciones.
    CLAVE_LADO_MEDIA_PANTALLA = "lado_media_pantalla"  # Identifica la mitad preferida dentro del selector de pantalla dividida.
    CLAVE_NAVEGACION_AUTOMATICA = "navegacion_automatica"  # Identifica si la compilación debe abrir automáticamente la salida más relevante.
    CLAVE_ADVERTENCIAS_VLSM = "mostrar_advertencias_vlsm"  # Identifica si las advertencias deben acompañar visualmente a Tabla VLSM.

    LADO_IZQUIERDO = "izquierda"  # Representa la mitad izquierda admitida por la ventana principal.
    LADO_DERECHO = "derecha"  # Representa la mitad derecha admitida por la ventana principal.

    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante las pruebas automatizadas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Comparte la carpeta general utilizada por los datos locales de la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_aplicacion.json"  # Mantiene separadas estas opciones respecto con las preferencias específicas de IA.

    def lado_media_pantalla(self) -> str:
        datos = self._leer_preferencias()  # Recupera únicamente una configuración estructuralmente válida.
        lado = datos.get(self.CLAVE_LADO_MEDIA_PANTALLA, self.LADO_IZQUIERDO)  # Utiliza izquierda como comportamiento predeterminado.

        if lado in (self.LADO_IZQUIERDO, self.LADO_DERECHO):
            return lado  # Respeta únicamente posiciones reconocidas por TecNet Finder.

        return self.LADO_IZQUIERDO  # Recupera el valor seguro si el archivo contiene una posición desconocida.

    def navegacion_automatica_activada(self) -> bool:
        datos = self._leer_preferencias()  # Recupera la configuración general existente.
        valor = datos.get(self.CLAVE_NAVEGACION_AUTOMATICA, True)  # Mantiene activado por defecto el comportamiento actual de navegación.

        if isinstance(valor, bool):
            return valor  # Respeta únicamente estados booleanos explícitos.

        return True  # Recupera el comportamiento recomendado cuando el archivo contiene información inesperada.

    def advertencias_vlsm_visibles(self) -> bool:
        datos = self._leer_preferencias()  # Recupera la configuración general existente.
        valor = datos.get(self.CLAVE_ADVERTENCIAS_VLSM, True)  # Mantiene visible por defecto el panel compacto implementado.

        if isinstance(valor, bool):
            return valor  # Respeta únicamente estados booleanos explícitos.

        return True  # Recupera el comportamiento recomendado ante información inválida.

    def establecer_lado_media_pantalla(self, lado: str) -> bool:
        if lado not in (self.LADO_IZQUIERDO, self.LADO_DERECHO):
            return False  # Rechaza cualquier posición que la ventana principal no pueda interpretar.

        return self._guardar_valor(
            self.CLAVE_LADO_MEDIA_PANTALLA,
            lado,
        )  # Persiste exclusivamente la mitad seleccionada.

    def establecer_navegacion_automatica_activada(self, activada: bool) -> bool:
        return self._guardar_valor(
            self.CLAVE_NAVEGACION_AUTOMATICA,
            bool(activada),
        )  # Persiste únicamente el comportamiento posterior a la compilación.

    def establecer_advertencias_vlsm_visibles(self, visibles: bool) -> bool:
        return self._guardar_valor(
            self.CLAVE_ADVERTENCIAS_VLSM,
            bool(visibles),
        )  # Persiste únicamente la visibilidad del panel compacto de advertencias.

    def _guardar_valor(self, clave: str, valor) -> bool:
        datos = self._leer_preferencias()  # Conserva las demás opciones existentes antes de modificar una sola preferencia.
        datos[clave] = valor  # Sustituye exclusivamente el valor solicitado.

        try:
            self.ruta_directorio.mkdir(
                parents=True,
                exist_ok=True,
            )  # Crea la carpeta persistente cuando todavía no existe.

            ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Prepara una escritura temporal para evitar archivos parciales.
            ruta_temporal.write_text(
                json.dumps(datos, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )  # Guarda primero toda la configuración en el archivo temporal.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye la configuración anterior únicamente después de completar correctamente la escritura.
            return True  # Confirma que la preferencia pudo conservarse.
        except OSError:
            return False  # Mantiene funcional la aplicación aunque Windows impida escribir la configuración.

    def _leer_preferencias(self) -> dict:
        if not self.ruta_archivo.is_file():
            return {}  # Utiliza los valores predeterminados durante la primera ejecución.

        try:
            datos = json.loads(
                self.ruta_archivo.read_text(encoding="utf-8")
            )  # Recupera la configuración persistente existente.
        except (OSError, json.JSONDecodeError):
            return {}  # Evita que un archivo inaccesible o dañado afecte al inicio de TecNet Finder.

        if not isinstance(datos, dict):
            return {}  # Descarta estructuras distintas del objeto esperado.

        return datos  # Entrega únicamente una configuración utilizable.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Consulta la ubicación oficial proporcionada por Windows.

        if ruta_local:
            return Path(ruta_local)  # Utiliza directamente LocalAppData cuando está disponible.

        return Path.home() / "AppData" / "Local"  # Mantiene una alternativa compatible para entornos donde la variable no esté definida.