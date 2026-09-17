# ============================================================
# Archivo: motor_local.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comunica TecNet Finder con la instancia privada
# de Ollama utilizada por el asistente local.
#
# Permite obtener texto normal o datos JSON estructurados sin
# introducir dependencias externas de Python. Cada consumidor
# puede utilizar el tiempo de espera apropiado para su tarea sin
# afectar a las demás funciones del asistente.
# ============================================================

import json  # Permite construir las solicitudes HTTP y convertir las respuestas JSON recibidas desde Ollama.
import urllib.error  # Permite controlar errores producidos por la comunicación HTTP.
import urllib.request  # Permite utilizar la API local de Ollama sin agregar librerías externas.

from AsistenteIA.infraestructura.configuracion import MODELO_IA, TIEMPO_ESPERA_SEGUNDOS, URL_BASE_OLLAMA  # Importa la configuración central de la instancia privada.


class MotorLocalOllama:  # Encapsula todas las comunicaciones realizadas con el servidor local de Ollama.
    def __init__(self, url_base: str = URL_BASE_OLLAMA, modelo: str = MODELO_IA):
        self.url_base = url_base.rstrip("/")  # Normaliza la dirección para construir endpoints sin diagonales duplicadas.
        self.modelo = modelo  # Conserva el modelo local que deberá utilizar cada generación.

    def disponible(self) -> bool:
        try:
            self._solicitar_json("/api/tags")  # Consulta un endpoint ligero para comprobar que el servidor privado responde.
            return True  # Considera disponible la IA cuando Ollama devuelve una respuesta válida.
        except OSError:
            return False  # Mantiene TecNet Finder funcional aunque el servidor local no se encuentre iniciado.

    def generar(
        self,
        prompt: str,
        maximo_tokens: int = 80,
        tiempo_espera_segundos: float | None = None,
    ) -> str | None:
        datos = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": maximo_tokens,
            },
        }  # Construye una generación breve y poco aleatoria apropiada para autocompletado.

        try:
            respuesta = self._solicitar_json(
                "/api/generate",
                datos=datos,
                metodo="POST",
                tiempo_espera_segundos=tiempo_espera_segundos,
            )  # Envía la solicitud utilizando el tiempo específico cuando el consumidor lo proporciona.
        except OSError:
            return None  # Trata los problemas del modelo o del servidor como ausencia de sugerencia.

        texto = respuesta.get("response")  # Recupera exclusivamente el texto producido por el modelo.

        if not isinstance(texto, str):
            return None  # Rechaza respuestas inesperadas que no contengan texto.

        texto = texto.strip("\r\n")  # Conserva espacios horizontales porque pueden ser significativos para el autocompletado.

        if not texto.strip():
            return None  # Descarta generaciones vacías o compuestas solamente por espacios.

        return texto  # Entrega el contenido sin interpretarlo como código válido.

    def generar_json(
        self,
        prompt: str,
        maximo_tokens: int = 120,
        tiempo_espera_segundos: float | None = None,
    ) -> dict | None:
        datos = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.3,
                "num_predict": maximo_tokens,
            },
        }  # Solicita explícitamente a Ollama una respuesta JSON para reducir errores de formato del modelo.

        try:
            respuesta = self._solicitar_json(
                "/api/generate",
                datos=datos,
                metodo="POST",
                tiempo_espera_segundos=tiempo_espera_segundos,
            )  # Obtiene la generación estructurada usando el tiempo apropiado para la tarea solicitante.
        except OSError:
            return None  # Permite continuar utilizando TecNet Finder aunque la consulta de IA falle.

        contenido = respuesta.get("response")  # Recupera la cadena JSON generada por el modelo.

        if not isinstance(contenido, str) or not contenido.strip():
            return None  # Descarta respuestas sin contenido estructurado utilizable.

        try:
            resultado = json.loads(contenido)  # Convierte la cadena generada en una estructura Python controlable.
        except json.JSONDecodeError:
            return None  # Rechaza cualquier generación que no sea realmente JSON válido.

        if not isinstance(resultado, dict):
            return None  # Exige un objeto porque los consumidores trabajan mediante campos con nombres conocidos.

        return resultado  # Entrega los datos todavía sin considerarlos válidos para ninguna función concreta.

    def _solicitar_json(
        self,
        endpoint: str,
        datos: dict | None = None,
        metodo: str = "GET",
        tiempo_espera_segundos: float | None = None,
    ) -> dict:
        cuerpo = None  # Mantiene vacía la solicitud cuando el endpoint solamente necesita lectura.

        if datos is not None:
            cuerpo = json.dumps(datos).encode("utf-8")  # Serializa el contenido de una solicitud POST mediante UTF-8.

        solicitud = urllib.request.Request(
            f"{self.url_base}{endpoint}",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method=metodo,
        )  # Construye una solicitud HTTP explícita hacia la instancia local configurada.

        tiempo_espera = TIEMPO_ESPERA_SEGUNDOS if tiempo_espera_segundos is None else max(0.1, float(tiempo_espera_segundos))  # Conserva el tiempo breve predeterminado y permite ampliarlo únicamente donde se necesita.

        try:
            with urllib.request.urlopen(solicitud, timeout=tiempo_espera) as respuesta:
                contenido = respuesta.read().decode("utf-8")  # Lee completamente la respuesta y la convierte desde UTF-8.
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise OSError("No fue posible comunicarse con Ollama.") from error  # Unifica los fallos de red para que las capas superiores puedan degradarse con seguridad.

        try:
            resultado = json.loads(contenido)  # Interpreta la respuesta HTTP utilizando el formato esperado por la API de Ollama.
        except json.JSONDecodeError as error:
            raise OSError("Ollama devolvió una respuesta JSON inválida.") from error  # Impide propagar respuestas corruptas hacia el asistente.

        if not isinstance(resultado, dict):
            raise OSError("Ollama devolvió una estructura inesperada.")  # Exige que el cuerpo principal corresponda con un objeto de la API.

        return resultado  # Devuelve la respuesta normalizada a la operación que realizó la consulta.
