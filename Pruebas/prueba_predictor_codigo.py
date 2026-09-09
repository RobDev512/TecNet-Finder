# ============================================================
# Archivo: prueba_predictor_codigo.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba que el predictor solicite únicamente los
# datos todavía faltantes y conserve de forma determinista todo
# valor que el usuario ya haya escrito.
#
# Las propuestas se simulan mediante JSON para que las pruebas no
# dependan de Ollama ni de respuestas aleatorias de un modelo real.
# ============================================================

from AsistenteIA.predictor_codigo import PredictorCodigo  # Importa el predictor contextual utilizado por el ghost text.


class MotorSimulado:  # Sustituye el modelo local mediante una respuesta JSON completamente controlada.
    def __init__(self, respuesta: dict | None):
        self.respuesta = respuesta  # Conserva los datos preparados para el escenario actual.
        self.cantidad_llamadas = 0  # Permite comprobar cuándo la IA no debería utilizarse.

    def generar_json(self, prompt: str, maximo_tokens: int = 120) -> dict | None:
        self.cantidad_llamadas += 1  # Registra cada solicitud que habría llegado al modelo local.
        return self.respuesta  # Devuelve exactamente la estructura preparada por la prueba.


def prueba_predictor_generaliza_desde_i():
    motor = MotorSimulado(
        {
            "ip": "10.44.2.0",
            "cidr": 20,
            "hosts": [40],
            "nombre": "Campus",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("I")

    assert sugerencia == "P 10.44.2.0 MASK /20 HOSTS 40 NAME Campus"


def prueba_predictor_continua_direccion_iniciada_en_diez():
    motor = MotorSimulado(
        {
            "ip": "10.30.5.0",
            "cidr": 24,
            "hosts": [18],
            "nombre": "Taller",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 10")

    assert sugerencia == ".30.5.0 MASK /24 HOSTS 18 NAME Taller"


def prueba_predictor_continua_direccion_arbitraria():
    motor = MotorSimulado(
        {
            "ip": "172.25.4.0",
            "cidr": 24,
            "hosts": [26],
            "nombre": "Laboratorio",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 172.25.4")

    assert sugerencia == ".0 MASK /24 HOSTS 26 NAME Laboratorio"


def prueba_predictor_ip_completa_no_vuelve_a_pedir_ip():
    motor = MotorSimulado(
        {
            "cidr": 27,
            "hosts": [7, 3],
            "nombre": "Taller",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 172.22.8.0")

    assert sugerencia == " MASK /27 HOSTS 7,3 NAME Taller"


def prueba_predictor_completa_mask_parcial_con_ip_bloqueada():
    motor = MotorSimulado(
        {
            "cidr": 26,
            "hosts": [22],
            "nombre": "OficinaSur",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 10.55.0.0 MAS")

    assert sugerencia == "K /26 HOSTS 22 NAME OficinaSur"


def prueba_predictor_completa_hosts_sin_repetir_ip_ni_cidr():
    motor = MotorSimulado(
        {
            "hosts_nuevos": [13],
            "nombre": "Laboratorio",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 192.168.50.0 MASK /24 HOS")

    assert sugerencia == "TS 13 NAME Laboratorio"


def prueba_predictor_conserva_host_existente_despues_de_coma():
    motor = MotorSimulado(
        {
            "hosts_nuevos": [20],
            "nombre": "Sucursal",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 10.5.0.0 MASK /24 HOSTS 50,")

    assert sugerencia == "20 NAME Sucursal"


def prueba_predictor_rechaza_ip_generada_incompatible_con_fragmento():
    motor = MotorSimulado(
        {
            "ip": "192.168.1.0",
            "cidr": 24,
            "hosts": [20],
            "nombre": "OtraRed",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 10")

    assert sugerencia is None


def prueba_predictor_rechaza_hosts_nuevos_invalidos():
    motor = MotorSimulado(
        {
            "hosts_nuevos": "20",
            "nombre": "Sucursal",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia = predictor.sugerir("IP 10.5.0.0 MASK /24 HOSTS 50,")

    assert sugerencia is None


def prueba_predictor_no_consulta_ia_para_linea_valida_o_texto_ajeno():
    motor = MotorSimulado(
        {
            "ip": "10.20.30.0",
            "cidr": 24,
            "hosts": [15],
            "nombre": "",
        }
    )
    predictor = PredictorCodigo(motor=motor)

    sugerencia_valida = predictor.sugerir("IP 10.20.30.0 MASK /24 HOSTS 15")
    sugerencia_ajena = predictor.sugerir("hola mundo")

    assert sugerencia_valida is None
    assert sugerencia_ajena is None
    assert motor.cantidad_llamadas == 0