# ============================================================
# Archivo: prueba_motor_local.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el procesamiento de las respuestas HTTP
# utilizadas por MotorLocalOllama sin depender de una instancia
# real de Ollama durante las pruebas automáticas.
#
# Mediante respuestas simuladas se verifica:
#
# - Conservación de espacios útiles en texto generado.
# - Rechazo de respuestas vacías.
# - Conversión de respuestas JSON.
# - Rechazo de JSON generado incorrectamente.
# - Uso independiente de tiempos de espera por función.
#
# Ninguna prueba realiza conexiones reales hacia Ollama.
# ============================================================

import urllib.request  # Permite sustituir temporalmente urlopen para evitar realizar conexiones HTTP reales.

from AsistenteIA.infraestructura.configuracion import TIEMPO_ESPERA_SEGUNDOS  # Proporciona el tiempo de espera predeterminado utilizado por el motor local.
from AsistenteIA.infraestructura.motor_local import MotorLocalOllama  # Importa la implementación encargada de comunicarse normalmente con Ollama.


class RespuestaHTTPSimulada:  # Imita únicamente las operaciones de una respuesta HTTP que MotorLocalOllama utiliza internamente.
    def __init__(self, contenido: str):  # Recibe el cuerpo textual que debe devolver la conexión simulada.
        self.contenido = contenido.encode("utf-8")  # Convierte el texto a bytes igual que una respuesta HTTP real.

    def __enter__(self):  # Permite utilizar la respuesta simulada dentro de un bloque with.
        return self  # Entrega la misma instancia como objeto disponible dentro del contexto.

    def __exit__(self, tipo, valor, traza):  # Atiende la salida del bloque with sin ocultar posibles excepciones.
        return False  # Devuelve False para conservar cualquier excepción que pudiera producirse durante la lectura.

    def read(self) -> bytes:  # Reproduce el método utilizado por urllib para recuperar el cuerpo de una respuesta.
        return self.contenido  # Devuelve exactamente los bytes preparados para el escenario actual.


def _simular_respuesta(monkeypatch, contenido: str, tiempos: list[float] | None = None) -> None:  # Sustituye urlopen por una respuesta HTTP completamente controlada.
    def urlopen_simulado(_solicitud, timeout=None):  # Imita solamente los argumentos de urlopen utilizados actualmente por MotorLocalOllama.
        if tiempos is not None:  # Comprueba si la prueba necesita registrar los tiempos de espera utilizados.
            tiempos.append(timeout)  # Conserva el valor real recibido para poder compararlo posteriormente.

        return RespuestaHTTPSimulada(contenido)  # Sustituye cualquier conexión real por el contenido preparado.

    monkeypatch.setattr(urllib.request, "urlopen", urlopen_simulado)  # Aplica la sustitución únicamente durante la prueba donde fue solicitado.


def prueba_motor_preserva_espacio_inicial_de_generacion(monkeypatch):  # Comprueba que un espacio inicial útil no sea eliminado de una sugerencia de código.
    _simular_respuesta(monkeypatch, '{"response": " MASK /24 HOSTS 50\\n"}')  # Simula una respuesta de Ollama cuyo texto comienza con un espacio necesario.
    motor = MotorLocalOllama()  # Crea el motor que utilizará automáticamente la conexión HTTP sustituida.
    resultado = motor.generar("prompt")  # Solicita una generación textual utilizando cualquier prompt de prueba.
    assert resultado == " MASK /24 HOSTS 50"  # Confirma que solamente se elimine el salto final y se conserve el espacio inicial.


def prueba_motor_descarta_respuesta_formada_solo_por_espacios(monkeypatch):  # Comprueba que una generación sin contenido útil sea tratada como ausencia de respuesta.
    _simular_respuesta(monkeypatch, '{"response": "   \\n"}')  # Simula una generación formada exclusivamente por espacios y un salto de línea.
    motor = MotorLocalOllama()  # Crea una instancia del motor utilizando la respuesta simulada.
    resultado = motor.generar("prompt")  # Solicita la generación para activar el procesamiento normal del contenido.
    assert resultado is None  # Confirma que el motor no entregue espacios vacíos como si fueran una sugerencia válida.


def prueba_motor_convierte_generacion_json_en_diccionario(monkeypatch):  # Comprueba que generar_json interprete correctamente un objeto JSON producido como texto por Ollama.
    _simular_respuesta(monkeypatch, '{"response": "{\\"ip\\": \\"10.5.0.0\\", \\"cidr\\": 24, \\"hosts\\": [20, 5], \\"nombre\\": \\"Campus\\"}"}')  # Simula el formato externo de Ollama conteniendo internamente otro JSON generado.
    motor = MotorLocalOllama()  # Crea el motor que procesará la respuesta HTTP controlada.
    resultado = motor.generar_json("prompt")  # Solicita directamente una generación cuya salida debe convertirse a estructura de Python.
    assert resultado == {
        "ip": "10.5.0.0",  # Comprueba que la dirección se recupere como texto.
        "cidr": 24,  # Comprueba que el prefijo permanezca como entero.
        "hosts": [20, 5],  # Comprueba que la lista de cantidades conserve sus valores y orden.
        "nombre": "Campus",  # Comprueba que también se recupere el identificador generado.
    }  # Verifica que la respuesta interna haya sido convertida completamente en el diccionario esperado.


def prueba_motor_descarta_generacion_json_invalida(monkeypatch):  # Comprueba que contenido generado que no sea JSON válido no se propague hacia las capas superiores.
    _simular_respuesta(monkeypatch, '{"response": "esto no es json"}')  # Simula una respuesta HTTP correcta cuyo contenido generado posee un formato inválido.
    motor = MotorLocalOllama()  # Crea el motor utilizando la conexión sustituida.
    resultado = motor.generar_json("prompt")  # Intenta interpretar el contenido como una estructura JSON.
    assert resultado is None  # Confirma que una respuesta inválida sea descartada de forma controlada.


def prueba_motor_permite_tiempo_de_espera_especifico_por_funcion(monkeypatch):  # Comprueba que una operación pueda ampliar su timeout sin modificar el valor predeterminado de las siguientes.
    tiempos = []  # Reunirá en orden todos los tiempos recibidos por la función HTTP simulada.
    _simular_respuesta(monkeypatch, '{"response": "{\\"soluciones\\": []}"}', tiempos)  # Prepara una respuesta JSON válida y habilita el registro de tiempos.
    motor = MotorLocalOllama()  # Crea una sola instancia para realizar ambas solicitudes consecutivamente.
    motor.generar_json("prompt", tiempo_espera_segundos=20.0)  # Ejecuta primero una operación que solicita explícitamente veinte segundos.
    motor.generar_json("prompt")  # Ejecuta otra generación sin proporcionar un tiempo personalizado.
    assert tiempos == [20.0, TIEMPO_ESPERA_SEGUNDOS]  # Confirma que la segunda llamada regrese al timeout predeterminado en vez de heredar el valor anterior.