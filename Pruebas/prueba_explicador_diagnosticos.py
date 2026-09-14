# ============================================================
# Archivo: prueba_explicador_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con ExplicadorDiagnosticos.
#
# No utiliza una instancia real de Ollama. En su lugar emplea un
# motor simulado con respuestas deterministas para comprobar:
#
# - Construcción de soluciones mejoradas.
# - Conservación del diagnóstico oficial original.
# - Reutilización de caché.
# - Rechazo de índices inválidos.
# - Uso de la solución oficial como respaldo.
# - División de grupos grandes en varios lotes.
# - Inclusión del contexto formal dentro del prompt.
# ============================================================

from AsistenteIA.explicador_diagnosticos import ExplicadorDiagnosticos  # Importa la capa encargada de convertir respuestas estructuradas del modelo en soluciones visuales.
from Motor.diagnosticos import Diagnostico  # Permite construir diagnósticos oficiales completamente controlados para cada prueba.


class MotorSimulado:  # Sustituye el motor local mediante respuestas preparadas para que las pruebas nunca dependan de Ollama.
    def __init__(self, respuestas):  # Recibe en orden las estructuras que deben devolverse durante las llamadas simuladas.
        self.respuestas = list(respuestas)  # Conserva una respuesta independiente para cada generación que espera realizar la prueba.
        self.cantidad_llamadas = 0  # Permite comprobar cuántas veces ExplicadorDiagnosticos consultaría realmente al modelo.
        self.prompts = []  # Conserva los prompts recibidos para verificar posteriormente qué contexto fue enviado.

    def generar_json(self, prompt: str, maximo_tokens: int = 120, tiempo_espera_segundos: float | None = None):  # Reproduce únicamente la interfaz utilizada por ExplicadorDiagnosticos.
        self.prompts.append(prompt)  # Registra exactamente el prompt que habría recibido el modelo local real.
        indice = self.cantidad_llamadas  # Utiliza el número de llamada actual para seleccionar la respuesta preparada correspondiente.
        self.cantidad_llamadas += 1  # Incrementa el contador antes de entregar la generación simulada.

        if indice >= len(self.respuestas):  # Comprueba si la prueba no preparó ninguna respuesta adicional.
            return None  # Simula una ausencia de resultado del modelo sin provocar una excepción artificial.

        return self.respuestas[indice]  # Devuelve exactamente la estructura determinista correspondiente con esta llamada.


def _diagnostico(numero: int = 0) -> Diagnostico:  # Construye un diagnóstico SIN-002 controlado que puede diferenciarse mediante un número.
    return Diagnostico(
        codigo="SIN-002",  # Utiliza el error correspondiente con la ausencia de MASK.
        categoria="Sintáctico",  # Conserva la categoría formal del diagnóstico utilizado en la prueba.
        severidad="error",  # Marca el elemento como un problema bloqueante igual que en producción.
        mensaje=f"Después de la dirección IP se esperaba MASK. Caso {numero}",  # Añade un número para producir claves distintas cuando se crean varios diagnósticos.
        linea=1,  # Sitúa todos los casos simulados dentro de la primera línea.
        columna=15,  # Proporciona una posición estable para construir la clave del diagnóstico.
        longitud=5,  # Simula el resaltado del fragmento HOSTS.
        fragmento="HOSTS",  # Representa el token encontrado donde debía aparecer MASK.
        solucion="Coloca MASK después de la IP. Ejemplo: IP 192.168.1.0 MASK /24.",  # Proporciona la solución oficial que siempre debe permanecer disponible.
    )  # Devuelve una estructura equivalente con las que recibe realmente el explicador desde el compilador.


def prueba_explicador_construye_solucion_mejorada_sin_modificar_diagnostico():  # Comprueba que la IA complemente la solución visual sin sobrescribir el diagnóstico oficial.
    diagnostico = _diagnostico()  # Crea un SIN-002 completamente controlado para esta prueba.
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 0,  # Relaciona la respuesta simulada con el único diagnóstico solicitado.
                        "explicacion": "La instrucción continuó sin declarar la máscara.",  # Proporciona una explicación adicional generada por el modelo simulado.
                        "correccion": "Agrega MASK y una máscara CIDR antes de HOSTS.",  # Proporciona una corrección más detallada.
                        "ejemplo": "IP 192.168.1.0 MASK /24 HOSTS 50",  # Proporciona un ejemplo completo que debe incorporarse al texto final.
                    }
                ]
            }
        ]
    )  # Prepara una respuesta válida con los tres componentes opcionales producidos por la IA.
    explicador = ExplicadorDiagnosticos(motor=motor)  # Utiliza el motor simulado en lugar del componente local real.
    soluciones = explicador.mejorar_soluciones([diagnostico])  # Solicita la mejora del único diagnóstico preparado.
    clave = explicador.clave_diagnostico(diagnostico)  # Calcula la misma clave que utiliza internamente la caché de soluciones.
    assert soluciones[clave] == (
        "Explicación: La instrucción continuó sin declarar la máscara.\n\n"
        "Corrección: Agrega MASK y una máscara CIDR antes de HOSTS.\n\n"
        "Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50"
    )  # Comprueba que explicación, corrección y ejemplo se combinen exactamente mediante el formato esperado.
    assert diagnostico.solucion == "Coloca MASK después de la IP. Ejemplo: IP 192.168.1.0 MASK /24."  # Confirma que la estructura oficial permanezca completamente intacta.


def prueba_explicador_reutiliza_cache_para_diagnostico_identico():  # Comprueba que una segunda solicitud idéntica no vuelva a consultar innecesariamente el modelo.
    diagnostico = _diagnostico()  # Crea el diagnóstico que será solicitado dos veces.
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 0,  # Relaciona la respuesta con el único diagnóstico del lote.
                        "explicacion": "Falta la palabra MASK.",  # Proporciona el texto mejorado que quedará almacenado en caché.
                        "correccion": "Agrega MASK antes de la máscara CIDR.",  # Proporciona la corrección correspondiente.
                        "ejemplo": "",  # Omite voluntariamente un ejemplo porque no es necesario para probar la caché.
                    }
                ]
            }
        ]
    )  # Prepara solamente una respuesta porque una implementación correcta no deberá pedir una segunda.
    explicador = ExplicadorDiagnosticos(motor=motor)  # Crea el explicador utilizando el motor controlado.
    primera = explicador.mejorar_soluciones([diagnostico])  # Realiza la primera solicitud y permite almacenar su resultado.
    segunda = explicador.mejorar_soluciones([diagnostico])  # Solicita exactamente el mismo diagnóstico por segunda ocasión.
    assert primera == segunda  # Confirma que el resultado recuperado de caché sea idéntico con el generado inicialmente.
    assert motor.cantidad_llamadas == 1  # Comprueba que el modelo simulado haya sido consultado solamente una vez.


def prueba_explicador_descarta_elementos_con_indice_invalido():  # Comprueba que una respuesta del modelo no pueda asociarse con un diagnóstico inexistente.
    diagnostico = _diagnostico()  # Prepara un lote que contiene solamente el índice válido cero.
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 8,  # Utiliza deliberadamente un índice completamente fuera del lote solicitado.
                        "explicacion": "Texto que no corresponde con ningún diagnóstico.",  # Simula contenido que nunca debe llegar a la interfaz.
                        "correccion": "No debe mostrarse.",  # Proporciona también una corrección inválidamente asociada.
                        "ejemplo": "",  # Mantiene vacío el ejemplo porque la prueba se centra únicamente en el índice.
                    }
                ]
            }
        ]
    )  # Prepara una respuesta estructuralmente legible pero semánticamente inválida para el lote.
    explicador = ExplicadorDiagnosticos(motor=motor)  # Crea el componente utilizando la respuesta controlada.
    soluciones = explicador.mejorar_soluciones([diagnostico])  # Intenta procesar la estructura devuelta por el motor simulado.
    assert soluciones == {}  # Confirma que ninguna solución inválidamente indexada pueda mostrarse ni almacenarse.


def prueba_explicador_utiliza_solucion_oficial_si_modelo_omite_correccion():  # Comprueba que la respuesta de IA nunca elimine la corrección oficial cuando viene incompleta.
    diagnostico = _diagnostico()  # Crea un diagnóstico que ya posee una solución oficial válida.
    motor = MotorSimulado(
        [
            {
                "soluciones": [
                    {
                        "indice": 0,  # Relaciona correctamente la respuesta con el diagnóstico solicitado.
                        "explicacion": "La estructura saltó la declaración de la máscara.",  # Proporciona solamente una explicación útil adicional.
                        "correccion": "",  # Simula que el modelo no fue capaz de generar una corrección propia.
                        "ejemplo": "",  # Omite también un ejemplo para comprobar exclusivamente el mecanismo de respaldo.
                    }
                ]
            }
        ]
    )  # Prepara una respuesta parcial que deberá complementarse con información oficial.
    explicador = ExplicadorDiagnosticos(motor=motor)  # Construye la capa de mejora utilizando el motor simulado.
    soluciones = explicador.mejorar_soluciones([diagnostico])  # Procesa la respuesta incompleta.
    clave = explicador.clave_diagnostico(diagnostico)  # Recupera la clave correspondiente con el diagnóstico mejorado.
    assert "Corrección: Coloca MASK después de la IP." in soluciones[clave]  # Confirma que la solución oficial se utilice automáticamente cuando la IA omite la corrección.


def prueba_explicador_divide_entradas_grandes_en_lotes():  # Comprueba que una colección mayor que el tamaño máximo se reparta entre varias consultas controladas.
    diagnosticos = [_diagnostico(numero) for numero in range(7)]  # Crea siete diagnósticos diferentes para superar el lote máximo de seis elementos.
    respuesta_primera = {
        "soluciones": [
            {
                "indice": indice,  # Relaciona cada solución con su posición dentro del primer lote.
                "explicacion": f"Explicación {indice}.",  # Genera un texto diferente para distinguir cada diagnóstico procesado.
                "correccion": f"Corrección {indice}.",  # Genera igualmente una corrección independiente para cada elemento.
                "ejemplo": "",  # Omite ejemplos porque esta prueba se centra en la división de las consultas.
            }
            for indice in range(6)  # Construye respuestas para los primeros seis diagnósticos del grupo.
        ]
    }  # Representa la generación completa correspondiente con el primer lote.
    respuesta_segunda = {
        "soluciones": [
            {
                "indice": 0,  # El segundo lote comienza nuevamente desde el índice local cero.
                "explicacion": "Explicación final.",  # Proporciona la mejora correspondiente con el séptimo diagnóstico.
                "correccion": "Corrección final.",  # Proporciona su corrección independiente.
                "ejemplo": "",  # Mantiene vacío el ejemplo porque no afecta la comprobación realizada.
            }
        ]
    }  # Representa la generación correspondiente con el único elemento restante.
    motor = MotorSimulado([respuesta_primera, respuesta_segunda])  # Prepara exactamente las dos respuestas que deberán consumirse.
    explicador = ExplicadorDiagnosticos(motor=motor)  # Crea la capa de mejora utilizando el motor de prueba.
    soluciones = explicador.mejorar_soluciones(diagnosticos)  # Solicita la mejora conjunta de los siete diagnósticos.
    assert len(soluciones) == 7  # Confirma que ninguna solución se pierda al dividir la colección en lotes.
    assert motor.cantidad_llamadas == 2  # Comprueba que seis elementos se procesen en la primera llamada y el séptimo en una segunda.
    assert "solucion_oficial" in motor.prompts[0]  # Verifica que el prompt proporcione al modelo la corrección oficial como referencia obligatoria.
    assert "IP <IP_ADDRESS> MASK <SUBNET_MASK>" in motor.prompts[0]  # Confirma que también se incluya la estructura formal del lenguaje dentro del contexto enviado.