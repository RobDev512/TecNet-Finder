# ============================================================
# Archivo: prueba_explicador_diagnosticos.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba que la IA únicamente mejore soluciones
# de diagnósticos ya existentes, valide la estructura recibida,
# reutilice caché y agrupe varias explicaciones sin depender de
# una instancia real de Ollama.
# ============================================================

from AsistenteIA.explicador_diagnosticos import ExplicadorDiagnosticos  # Importa la capa que transforma respuestas estructuradas en soluciones visuales.
from Motor.diagnosticos import Diagnostico  # Permite construir diagnósticos oficiales completamente controlados.


class MotorSimulado:  # Sustituye Ollama mediante respuestas deterministas preparadas por cada prueba.
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)  # Conserva una respuesta independiente para cada llamada esperada.
        self.cantidad_llamadas = 0  # Permite comprobar caché y tamaño de lote.
        self.prompts = []  # Conserva el contexto enviado para comprobar que la solución oficial sí fue proporcionada.

    def generar_json(self, prompt: str, maximo_tokens: int = 120, tiempo_espera_segundos: float | None = None):
        self.prompts.append(prompt)  # Registra exactamente el contenido que habría recibido el modelo local.
        indice = self.cantidad_llamadas  # Obtiene la posición correspondiente a esta consulta.
        self.cantidad_llamadas += 1  # Cuenta la generación antes de entregar su resultado.

        if indice >= len(self.respuestas):
            return None  # Simula ausencia de respuesta cuando la prueba no preparó más generaciones.

        return self.respuestas[indice]  # Devuelve exactamente la estructura definida para el escenario actual.


def _diagnostico(numero: int = 0) -> Diagnostico:
    return Diagnostico(
        codigo="SIN-002",
        categoria="Sintáctico",
        severidad="error",
        mensaje=f"Después de la dirección IP se esperaba MASK. Caso {numero}",
        linea=1,
        columna=15,
        longitud=5,
        fragmento="HOSTS",
        solucion="Coloca MASK después de la IP. Ejemplo: IP 192.168.1.0 MASK /24.",
    )


def prueba_explicador_construye_solucion_mejorada_sin_modificar_diagnostico():
    diagnostico = _diagnostico()
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 0,
                        "explicacion": "La instrucción continuó sin declarar la máscara.",
                        "correccion": "Agrega MASK y una máscara CIDR antes de HOSTS.",
                        "ejemplo": "IP 192.168.1.0 MASK /24 HOSTS 50",
                    }
                ]
            }
        ]
    )
    explicador = ExplicadorDiagnosticos(motor=motor)

    soluciones = explicador.mejorar_soluciones([diagnostico])
    clave = explicador.clave_diagnostico(diagnostico)

    assert soluciones[clave] == (
        "Explicación: La instrucción continuó sin declarar la máscara.\n\n"
        "Corrección: Agrega MASK y una máscara CIDR antes de HOSTS.\n\n"
        "Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50"
    )
    assert diagnostico.solucion == "Coloca MASK después de la IP. Ejemplo: IP 192.168.1.0 MASK /24."


def prueba_explicador_reutiliza_cache_para_diagnostico_identico():
    diagnostico = _diagnostico()
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 0,
                        "explicacion": "Falta la palabra MASK.",
                        "correccion": "Agrega MASK antes de la máscara CIDR.",
                        "ejemplo": "",
                    }
                ]
            }
        ]
    )
    explicador = ExplicadorDiagnosticos(motor=motor)

    primera = explicador.mejorar_soluciones([diagnostico])
    segunda = explicador.mejorar_soluciones([diagnostico])

    assert primera == segunda
    assert motor.cantidad_llamadas == 1


def prueba_explicador_descarta_elementos_con_indice_invalido():
    diagnostico = _diagnostico()
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 8,
                        "explicacion": "Texto que no corresponde con ningún diagnóstico.",
                        "correccion": "No debe mostrarse.",
                        "ejemplo": "",
                    }
                ]
            }
        ]
    )
    explicador = ExplicadorDiagnosticos(motor=motor)

    soluciones = explicador.mejorar_soluciones([diagnostico])

    assert soluciones == {}


def prueba_explicador_utiliza_solucion_oficial_si_modelo_omite_correccion():
    diagnostico = _diagnostico()
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 0,
                        "explicacion": "La estructura saltó la declaración de la máscara.",
                        "correccion": "",
                        "ejemplo": "",
                    }
                ]
            }
        ]
    )
    explicador = ExplicadorDiagnosticos(motor=motor)

    soluciones = explicador.mejorar_soluciones([diagnostico])
    clave = explicador.clave_diagnostico(diagnostico)

    assert "Corrección: Coloca MASK después de la IP." in soluciones[clave]


def prueba_explicador_divide_entradas_grandes_en_lotes():
    diagnosticos = [_diagnostico(numero) for numero in range(7)]
    respuesta_primera = {
        "soluciones": [
            {
                "indice": indice,
                "explicacion": f"Explicación {indice}.",
                "correccion": f"Corrección {indice}.",
                "ejemplo": "",
            }
            for indice in range(6)
        ]
    }
    respuesta_segunda = {
        "soluciones": [
            {
                "indice": 0,
                "explicacion": "Explicación final.",
                "correccion": "Corrección final.",
                "ejemplo": "",
            }
        ]
    }
    motor = MotorSimulado([respuesta_primera, respuesta_segunda])
    explicador = ExplicadorDiagnosticos(motor=motor)

    soluciones = explicador.mejorar_soluciones(diagnosticos)

    assert len(soluciones) == 7
    assert motor.cantidad_llamadas == 2
    assert "solucion_oficial" in motor.prompts[0]
    assert "IP <IP_ADDRESS> MASK <SUBNET_MASK>" in motor.prompts[0]
