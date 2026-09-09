# ============================================================
# Archivo: prueba_motor_local.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba el procesamiento de las respuestas HTTP
# utilizadas por el motor local sin depender de una instancia
# real de Ollama durante pytest.
# ============================================================

import urllib.request  # Permite sustituir temporalmente la operación HTTP real utilizada por el motor.

from AsistenteIA.motor_local import MotorLocalOllama  # Importa la implementación completa que debe ejercitarse durante las pruebas.


class RespuestaHTTPSimulada:  # Imita únicamente el comportamiento utilizado por urllib dentro del motor.
    def __init__(self, contenido: str):
        self.contenido = contenido.encode("utf-8")  # Conserva una respuesta equivalente a los bytes entregados por HTTP.

    def __enter__(self):
        return self  # Permite utilizar la respuesta simulada mediante un bloque with.

    def __exit__(self, tipo, valor, traza):
        return False  # No oculta excepciones producidas dentro del bloque de lectura.

    def read(self) -> bytes:
        return self.contenido  # Devuelve exactamente el cuerpo preparado por la prueba.


def _simular_respuesta(monkeypatch, contenido: str) -> None:
    def urlopen_simulado(_solicitud, timeout=None):
        return RespuestaHTTPSimulada(contenido)  # Sustituye la conexión real por una respuesta completamente controlada.

    monkeypatch.setattr(urllib.request, "urlopen", urlopen_simulado)  # Aplica la sustitución solamente durante la prueba actual.


def prueba_motor_preserva_espacio_inicial_de_generacion(monkeypatch):
    _simular_respuesta(monkeypatch, '{"response": " MASK /24 HOSTS 50\\n"}')
    motor = MotorLocalOllama()

    resultado = motor.generar("prompt")

    assert resultado == " MASK /24 HOSTS 50"


def prueba_motor_descarta_respuesta_formada_solo_por_espacios(monkeypatch):
    _simular_respuesta(monkeypatch, '{"response": "   \\n"}')
    motor = MotorLocalOllama()

    resultado = motor.generar("prompt")

    assert resultado is None


def prueba_motor_convierte_generacion_json_en_diccionario(monkeypatch):
    _simular_respuesta(
        monkeypatch,
        '{"response": "{\\"ip\\": \\"10.5.0.0\\", \\"cidr\\": 24, \\"hosts\\": [20, 5], \\"nombre\\": \\"Campus\\"}"}',
    )
    motor = MotorLocalOllama()

    resultado = motor.generar_json("prompt")

    assert resultado == {
        "ip": "10.5.0.0",
        "cidr": 24,
        "hosts": [20, 5],
        "nombre": "Campus",
    }


def prueba_motor_descarta_generacion_json_invalida(monkeypatch):
    _simular_respuesta(monkeypatch, '{"response": "esto no es json"}')
    motor = MotorLocalOllama()

    resultado = motor.generar_json("prompt")

    assert resultado is None