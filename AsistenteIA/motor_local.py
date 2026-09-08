# ============================================================
# Archivo: motor_local.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo implementa la comunicación entre TecNet Finder
# y el servidor Ollama privado utilizado por la aplicación.
#
# Utiliza únicamente la biblioteca estándar de Python y trata
# la IA como un componente opcional: si Ollama no responde,
# el compilador continúa funcionando con normalidad.
# ============================================================

import json  # Convierte las solicitudes y respuestas entre objetos de Python y JSON.
import urllib.error  # Permite distinguir fallos de conexión o respuestas HTTP incorrectas.
import urllib.request  # Realiza las peticiones HTTP contra la API local de Ollama.

from AsistenteIA.configuracion import MODELO_IA, TIEMPO_ESPERA_SEGUNDOS, URL_BASE_OLLAMA  # Importa la configuración única utilizada por el motor local.


class MotorLocalOllama:  # Encapsula las operaciones de red necesarias para utilizar el modelo privado.
    def __init__(self, url_base: str = URL_BASE_OLLAMA, modelo: str = MODELO_IA):  # Permite sustituir dirección o modelo durante pruebas sin cambiar la configuración global.
        self.url_base = url_base.rstrip("/")  # Normaliza la dirección evitando diagonales duplicadas al formar endpoints.
        self.modelo = modelo  # Conserva el nombre exacto del modelo que TecNet Finder debe solicitar.

    def disponible(self) -> bool:  # Comprueba rápidamente si el servidor privado responde y contiene el modelo requerido.
        try:
            respuesta = self._solicitar_json("/api/tags", metodo="GET")  # Consulta la lista de modelos disponibles en Ollama.
        except (OSError, ValueError):
            return False  # Considera la IA inactiva si la API no puede consultarse correctamente.

        modelos = respuesta.get("models", [])  # Obtiene la colección devuelta por Ollama sin asumir que siempre estará presente.

        return any(
            modelo.get("name") == self.modelo or modelo.get("model") == self.modelo
            for modelo in modelos
        )  # Exige que además del servidor esté disponible exactamente el modelo configurado.

    def generar(self, prompt: str, maximo_tokens: int = 48) -> str | None:  # Solicita una respuesta breve apropiada para autocompletado.
        datos = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": maximo_tokens,
            },
        }  # Limita creatividad y longitud para obtener propuestas rápidas y más deterministas.

        try:
            respuesta = self._solicitar_json("/api/generate", datos=datos, metodo="POST")  # Envía la solicitud de generación al proceso privado.
        except (OSError, ValueError):
            return None  # Convierte cualquier indisponibilidad de IA en ausencia silenciosa de sugerencia.

        texto = respuesta.get("response")  # Recupera únicamente el contenido generado por el modelo.

        if not isinstance(texto, str):
            return None  # Descarta respuestas incompletas o con un formato inesperado.

        texto = texto.strip()  # Elimina espacios y saltos agregados alrededor de la generación.

        return texto or None  # Devuelve None cuando el modelo no produjo contenido útil.

    def _solicitar_json(self, endpoint: str, datos: dict | None = None, metodo: str = "GET") -> dict:  # Ejecuta una petición JSON reutilizable contra la API local.
        cuerpo = None  # Mantiene las peticiones GET sin cuerpo de forma predeterminada.
        encabezados = {"Content-Type": "application/json"}  # Informa que cualquier contenido enviado utiliza JSON.

        if datos is not None:
            cuerpo = json.dumps(datos).encode("utf-8")  # Serializa la solicitud utilizando UTF-8 antes de enviarla.

        solicitud = urllib.request.Request(
            url=f"{self.url_base}{endpoint}",
            data=cuerpo,
            headers=encabezados,
            method=metodo,
        )  # Construye una petición explícita para evitar dependencias HTTP externas.

        try:
            with urllib.request.urlopen(solicitud, timeout=TIEMPO_ESPERA_SEGUNDOS) as respuesta:
                contenido = respuesta.read().decode("utf-8")  # Lee completamente la respuesta local y la convierte nuevamente en texto.
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            raise OSError("No fue posible comunicarse con la IA local.") from error  # Normaliza los fallos de transporte para que el resto del proyecto no dependa de urllib.

        try:
            datos_respuesta = json.loads(contenido)  # Convierte el JSON devuelto por Ollama en una estructura de Python.
        except json.JSONDecodeError as error:
            raise ValueError("Ollama devolvió una respuesta JSON inválida.") from error  # Impide propagar contenido corrupto hacia el predictor.

        if not isinstance(datos_respuesta, dict):
            raise ValueError("Ollama devolvió una respuesta inesperada.")  # Exige la estructura utilizada por todos los endpoints consumidos.

        return datos_respuesta  # Entrega únicamente respuestas ya comprobadas y convertidas.