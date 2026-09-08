# ============================================================
# Archivo: prueba_predictor_codigo.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba que el predictor de código basado en IA
# mantenga la autoridad del compilador formal.
#
# Las pruebas utilizan un motor simulado para no depender de
# Ollama, Internet, GPU ni del modelo real durante pytest.
# ============================================================

from AsistenteIA.predictor_codigo import PredictorCodigo  # Importa el predictor que filtra las propuestas antes de entregarlas a la interfaz.


class MotorSimulado:  # Sustituye Ollama durante las pruebas para producir respuestas completamente controladas.
    def __init__(self, respuesta: str | None):
        self.respuesta = respuesta  # Conserva la salida que será devuelta cuando el predictor solicite una generación.
        self.cantidad_llamadas = 0  # Permite comprobar cuándo el predictor evita consultar innecesariamente la IA.

    def generar(self, prompt: str, maximo_tokens: int = 48) -> str | None:
        self.cantidad_llamadas += 1  # Registra cada solicitud realizada por el predictor.
        return self.respuesta  # Devuelve exactamente la respuesta preparada para cada escenario.


def prueba_predictor_devuelve_solo_continuacion_valida():  # Comprueba que una línea correcta produzca únicamente la parte todavía no escrita.
    motor = MotorSimulado(
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir(
        "IP 192.168.1.0 MASK /24 HOSTS"
    )

    assert sugerencia == " 50 NAME Oficina"
    assert motor.cantidad_llamadas == 1


def prueba_predictor_completa_palabra_reservada_incompleta():  # Comprueba que la IA pueda terminar una palabra reservada sin modificar el prefijo existente.
    motor = MotorSimulado(
        "IP 192.168.10.0 MASK /24 HOSTS 30 NAME Oficina"
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir(
        "IP 192.168.10.0 MAS"
    )

    assert sugerencia == "K /24 HOSTS 30 NAME Oficina"


def prueba_predictor_rechaza_respuesta_que_modifica_prefijo():  # Impide que la IA cambie caracteres que el usuario ya escribió.
    motor = MotorSimulado(
        "IP 10.0.0.0 MASK /24 HOSTS 50 NAME Oficina"
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir(
        "IP 192.168.1.0 MASK"
    )

    assert sugerencia is None


def prueba_predictor_rechaza_propuesta_lexicamente_invalida():  # Comprueba que símbolos ajenos al lenguaje nunca lleguen al ghost text.
    motor = MotorSimulado(
        "IP 192.168.1.0 MASK /24 HOSTS 50 @ Oficina"
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir(
        "IP 192.168.1.0 MASK /24 HOSTS"
    )

    assert sugerencia is None


def prueba_predictor_rechaza_propuesta_sintacticamente_invalida():  # Comprueba que una secuencia con tokens válidos pero orden incorrecto también sea descartada.
    motor = MotorSimulado(
        "IP 192.168.1.0 MASK /24 HOSTS NAME Oficina"
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir(
        "IP 192.168.1.0 MASK /24 HOSTS"
    )

    assert sugerencia is None


def prueba_predictor_no_consulta_ia_con_entrada_vacia():  # Evita consumir recursos del modelo cuando el usuario todavía no ha escrito contenido útil.
    motor = MotorSimulado(
        "IP 192.168.1.0 MASK /24 HOSTS 50"
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("   ")

    assert sugerencia is None
    assert motor.cantidad_llamadas == 0