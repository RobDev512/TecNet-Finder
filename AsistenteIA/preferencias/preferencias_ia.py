# ============================================================
# Archivo: preferencias_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo conserva las preferencias del usuario relacionadas
# con las funciones de inteligencia artificial local.
#
# Autocompletado y mejora de diagnósticos se almacenan de manera
# independiente y se conserva compatibilidad con la preferencia
# utilizada por versiones anteriores de TecNet Finder.
# ============================================================

import json  # Permite guardar y recuperar las preferencias utilizando un archivo JSON legible.
import os  # Permite localizar LocalAppData sin depender del nombre concreto de la cuenta de Windows.
from pathlib import Path  # Facilita la construcción y administración segura de las rutas persistentes.


class PreferenciasIA:  # Administra las decisiones persistentes relacionadas con las funciones opcionales de IA local.
    CLAVE_ANTERIOR = "asistencia_ia_activada"  # Reconoce la preferencia utilizada antes de separar las funciones de inteligencia artificial.
    CLAVE_AUTOCOMPLETADO = "autocompletado_ia_activado"  # Identifica exclusivamente el estado persistente del ghost text.
    CLAVE_DIAGNOSTICOS = "diagnosticos_ia_activados"  # Identifica exclusivamente el uso de IA para mejorar soluciones de diagnósticos.

    def __init__(self, ruta_datos_locales: str | Path | None = None):  # Prepara las rutas donde permanecerán las preferencias entre ejecuciones.
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite sustituir LocalAppData durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Utiliza la carpeta persistente general perteneciente a la aplicación.
        self.ruta_archivo = self.ruta_directorio / "preferencias_ia.json"  # Mantiene las decisiones separadas de los archivos físicos de IA.

    def autocompletado_activado(self) -> bool:  # Consulta si el usuario desea utilizar las sugerencias automáticas de código.
        datos = self._leer_preferencias()  # Recupera primero una configuración cuya estructura haya sido validada.
        return self._obtener_booleano(datos, self.CLAVE_AUTOCOMPLETADO)  # Obtiene el valor actual o utiliza la preferencia histórica como compatibilidad.

    def diagnosticos_ia_activados(self) -> bool:  # Consulta si la IA puede mejorar las soluciones mostradas en los diagnósticos.
        datos = self._leer_preferencias()  # Lee la configuración persistente sin depender del estado físico del modelo.
        return self._obtener_booleano(datos, self.CLAVE_DIAGNOSTICOS)  # Obtiene exclusivamente la opción relacionada con diagnósticos.

    def alguna_funcion_activada(self) -> bool:  # Indica si alguna característica necesita potencialmente mantener disponible Ollama.
        return self.autocompletado_activado() or self.diagnosticos_ia_activados()  # Combina ambas decisiones sin volverlas una sola preferencia.

    def establecer_autocompletado_activado(self, activado: bool) -> bool:  # Cambia solamente la preferencia correspondiente con el ghost text.
        return self._guardar_booleano(self.CLAVE_AUTOCOMPLETADO, activado)  # Persiste la nueva elección sin alterar la asistencia de diagnósticos.

    def establecer_diagnosticos_ia_activados(self, activados: bool) -> bool:  # Cambia solamente la preferencia correspondiente con las soluciones de IA.
        return self._guardar_booleano(self.CLAVE_DIAGNOSTICOS, activados)  # Guarda el nuevo valor sin modificar el autocompletado.

    def asistencia_activada(self) -> bool:  # Conserva una consulta utilizada por versiones anteriores del proyecto.
        return self.autocompletado_activado()  # Mantiene el comportamiento antiguo relacionándolo únicamente con el autocompletado.

    def establecer_asistencia_activada(self, activada: bool) -> bool:  # Conserva el método histórico para evitar romper código o pruebas anteriores.
        return self.establecer_autocompletado_activado(activada)  # Redirige la operación hacia la preferencia nueva correspondiente.

    def _obtener_booleano(self, datos: dict, clave: str) -> bool:  # Obtiene de manera segura una preferencia booleana actual o histórica.
        valor = datos.get(clave)  # Busca primero la clave independiente introducida por la versión actual.

        if isinstance(valor, bool):  # Comprueba que el contenido encontrado sea realmente un booleano válido.
            return valor  # Respeta directamente la decisión guardada por el usuario.

        valor_anterior = datos.get(self.CLAVE_ANTERIOR, True)  # Busca como alternativa la preferencia global utilizada por versiones anteriores.

        if isinstance(valor_anterior, bool):  # Comprueba también la validez del valor histórico antes de utilizarlo.
            return valor_anterior  # Conserva la elección previa durante la migración natural del archivo.

        return True  # Recupera el comportamiento predeterminado cuando la información almacenada no es válida.

    def _guardar_booleano(self, clave: str, valor: bool) -> bool:  # Persiste una única preferencia sin eliminar las demás opciones existentes.
        datos = self._leer_preferencias()  # Recupera primero cualquier configuración que ya pertenezca al usuario.
        datos[clave] = bool(valor)  # Actualiza únicamente la clave solicitada normalizando su valor a booleano.

        try:  # Intenta escribir la configuración de una manera segura para evitar archivos incompletos.
            self.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Garantiza que exista la carpeta persistente de TecNet Finder.
            ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Prepara un archivo temporal antes de modificar el archivo real.
            ruta_temporal.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")  # Escribe completamente la nueva configuración.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye el archivo anterior únicamente después de completar correctamente la escritura.
            return True  # Confirma a la interfaz que el cambio pudo conservarse.
        except OSError:  # Atiende problemas de permisos, almacenamiento o acceso al archivo.
            return False  # Permite que TecNet Finder continúe funcionando aunque la preferencia no pueda guardarse.

    def _leer_preferencias(self) -> dict:  # Recupera solamente un diccionario JSON válido desde el archivo persistente.
        if not self.ruta_archivo.is_file():  # Comprueba si todavía existe un archivo de preferencias para este usuario.
            return {}  # Devuelve configuración vacía para que se utilicen los valores predeterminados.

        try:  # Intenta leer y convertir el contenido persistente.
            datos = json.loads(self.ruta_archivo.read_text(encoding="utf-8"))  # Convierte el JSON almacenado en una estructura de Python.
        except (OSError, json.JSONDecodeError):  # Atiende tanto problemas de lectura como archivos JSON dañados.
            return {}  # Ignora la configuración incorrecta para no afectar el funcionamiento general.

        if not isinstance(datos, dict):  # Verifica que la raíz del JSON tenga la estructura esperada.
            return {}  # Descarta otros tipos de contenido aunque sean JSON sintácticamente válidos.

        return datos  # Entrega exclusivamente preferencias que superaron las comprobaciones básicas.

    def _obtener_ruta_datos_locales(self) -> Path:  # Determina dónde debe guardar TecNet Finder los datos privados del usuario.
        ruta_local = os.environ.get("LOCALAPPDATA")  # Consulta primero la ubicación oficial proporcionada por Windows.

        if ruta_local:  # Comprueba si la variable del sistema se encuentra disponible.
            return Path(ruta_local)  # Utiliza directamente la ubicación oficial sin depender del nombre de la cuenta.

        return Path.home() / "AppData" / "Local"  # Utiliza una ruta compatible como respaldo cuando LOCALAPPDATA no está definida.