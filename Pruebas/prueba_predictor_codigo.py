# ============================================================
# Archivo: prueba_predictor_codigo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba PredictorCodigo, utilizado por el
# autocompletado opcional con inteligencia artificial.
#
# Las respuestas del modelo se sustituyen mediante un motor
# simulado para comprobar de forma determinista que el predictor:
#
# - Conserve cualquier dato ya escrito por el usuario.
# - Solicite únicamente información todavía faltante.
# - Complete palabras reservadas de manera determinista.
# - Continúe direcciones IPv4 parciales.
# - Respete cantidades HOSTS existentes.
# - Rechace respuestas incompatibles o mal estructuradas.
# - No consulte IA cuando el contexto no la necesita.
#
# Ninguna prueba requiere una instancia real de Ollama.
# ============================================================

from AsistenteIA.autocompletado.predictor_codigo import PredictorCodigo  # Importa el componente que combina análisis contextual y datos generados por IA.


class MotorSimulado:  # Sustituye el modelo local mediante una única respuesta JSON completamente controlada.
    def __init__(self, respuesta: dict | None):  # Recibe la estructura que debe entregarse cada vez que PredictorCodigo consulte el motor.
        self.respuesta = respuesta  # Conserva exactamente los datos preparados para el escenario actual.
        self.cantidad_llamadas = 0  # Permite comprobar cuándo el predictor evita correctamente utilizar inteligencia artificial.

    def generar_json(self, prompt: str, maximo_tokens: int = 120) -> dict | None:  # Reproduce la interfaz mínima de MotorLocalOllama utilizada por el predictor.
        self.cantidad_llamadas += 1  # Registra cada consulta que en una ejecución real habría llegado hasta Ollama.
        return self.respuesta  # Devuelve siempre la respuesta determinista definida por la prueba.


def prueba_predictor_generaliza_desde_i():  # Comprueba que incluso un prefijo mínimo pueda conducir hacia una instrucción completa.
    motor = MotorSimulado(
        {
            "ip": "10.44.2.0",  # Proporciona la dirección que debe incorporarse después de completar IP.
            "cidr": 20,  # Proporciona el prefijo solicitado para MASK.
            "hosts": [40],  # Proporciona una sola cantidad HOSTS.
            "nombre": "Campus",  # Proporciona el identificador opcional de la red.
        }
    )  # Prepara todos los datos variables necesarios para completar la instrucción desde el principio.
    predictor = PredictorCodigo(motor=motor)  # Crea el predictor utilizando exclusivamente el motor controlado.
    sugerencia = predictor.sugerir("I")  # Solicita una continuación partiendo solamente de la primera letra de IP.
    assert sugerencia == "P 10.44.2.0 MASK /20 HOSTS 40 NAME Campus"  # Confirma que P se complete localmente y que los demás datos provengan de la respuesta preparada.


def prueba_predictor_continua_direccion_iniciada_en_diez():  # Comprueba que una dirección parcial conserve exactamente los caracteres ya escritos.
    motor = MotorSimulado(
        {
            "ip": "10.30.5.0",  # Proporciona una IP completa compatible con el prefijo 10 escrito por el usuario.
            "cidr": 24,  # Proporciona la máscara que deberá continuar después de completar la dirección.
            "hosts": [18],  # Proporciona la cantidad de dispositivos solicitada.
            "nombre": "Taller",  # Proporciona el nombre opcional generado.
        }
    )  # Prepara una continuación compatible con el contexto escrito.
    predictor = PredictorCodigo(motor=motor)  # Construye el predictor utilizando el motor simulado.
    sugerencia = predictor.sugerir("IP 10")  # Solicita completar una dirección cuyos dos primeros dígitos ya existen.
    assert sugerencia == ".30.5.0 MASK /24 HOSTS 18 NAME Taller"  # Confirma que la sugerencia no vuelva a escribir el fragmento 10.


def prueba_predictor_continua_direccion_arbitraria():  # Comprueba que el predictor pueda continuar una IP parcial distinta de los ejemplos más comunes.
    motor = MotorSimulado(
        {
            "ip": "172.25.4.0",  # Proporciona una dirección completa que coincide con todo el fragmento existente.
            "cidr": 24,  # Proporciona una máscara válida para continuar la instrucción.
            "hosts": [26],  # Proporciona la solicitud HOSTS correspondiente.
            "nombre": "Laboratorio",  # Proporciona el identificador final.
        }
    )  # Prepara una respuesta compatible con un prefijo IPv4 arbitrario.
    predictor = PredictorCodigo(motor=motor)  # Crea el predictor mediante el motor controlado.
    sugerencia = predictor.sugerir("IP 172.25.4")  # Solicita completar únicamente la parte restante de la dirección y de la instrucción.
    assert sugerencia == ".0 MASK /24 HOSTS 26 NAME Laboratorio"  # Comprueba que el contenido existente permanezca bloqueado y no se repita.


def prueba_predictor_ip_completa_no_vuelve_a_pedir_ip():  # Comprueba que una IP ya terminada deje de formar parte de los datos solicitados al modelo.
    motor = MotorSimulado(
        {
            "cidr": 27,  # Proporciona directamente el siguiente dato todavía faltante.
            "hosts": [7, 3],  # Proporciona dos cantidades que deben conservar su orden.
            "nombre": "Taller",  # Proporciona la sección opcional final.
        }
    )  # Omite deliberadamente ip porque ese valor ya existe dentro del código del usuario.
    predictor = PredictorCodigo(motor=motor)  # Construye el predictor mediante la respuesta incompleta intencionalmente.
    sugerencia = predictor.sugerir("IP 172.22.8.0")  # Solicita continuar una línea cuya dirección ya se encuentra completa.
    assert sugerencia == " MASK /27 HOSTS 7,3 NAME Taller"  # Confirma que el predictor continúe exactamente desde MASK sin solicitar ni repetir IP.


def prueba_predictor_completa_mask_parcial_con_ip_bloqueada():  # Comprueba que una palabra MASK incompleta se termine localmente sin modificar la dirección existente.
    motor = MotorSimulado(
        {
            "cidr": 26,  # Proporciona únicamente el valor variable de la máscara.
            "hosts": [22],  # Proporciona la cantidad que deberá seguir después de HOSTS.
            "nombre": "OficinaSur",  # Proporciona el nombre opcional de la red.
        }
    )  # No incluye IP porque el predictor debe conservar la ya escrita.
    predictor = PredictorCodigo(motor=motor)  # Crea el componente con la respuesta determinista.
    sugerencia = predictor.sugerir("IP 10.55.0.0 MAS")  # Solicita una continuación justo antes de terminar la palabra reservada MASK.
    assert sugerencia == "K /26 HOSTS 22 NAME OficinaSur"  # Confirma que K se complete de forma fija y la IA aporte únicamente los valores faltantes.


def prueba_predictor_completa_hosts_sin_repetir_ip_ni_cidr():  # Comprueba que IP y máscara ya escritas permanezcan fuera de la respuesta generada.
    motor = MotorSimulado(
        {
            "hosts_nuevos": [13],  # Proporciona únicamente la primera cantidad que todavía falta después de HOSTS.
            "nombre": "Laboratorio",  # Proporciona además un posible nombre de red.
        }
    )  # Omite IP y CIDR porque ambos valores ya se encuentran completos dentro de la línea.
    predictor = PredictorCodigo(motor=motor)  # Construye el predictor con el motor simulado.
    sugerencia = predictor.sugerir("IP 192.168.50.0 MASK /24 HOS")  # Solicita continuar desde una palabra HOSTS parcialmente escrita.
    assert sugerencia == "TS 13 NAME Laboratorio"  # Confirma que solamente se complete la palabra y se agreguen los datos que todavía faltaban.


def prueba_predictor_conserva_host_existente_despues_de_coma():  # Comprueba que continuar una lista HOSTS nunca reescriba cantidades ya introducidas.
    motor = MotorSimulado(
        {
            "hosts_nuevos": [20],  # Proporciona únicamente la cantidad que debe agregarse después de la coma existente.
            "nombre": "Sucursal",  # Proporciona el identificador opcional para completar después la instrucción.
        }
    )  # Prepara exclusivamente información posterior al valor 50 que ya escribió el usuario.
    predictor = PredictorCodigo(motor=motor)  # Crea el predictor utilizando la respuesta simulada.
    sugerencia = predictor.sugerir("IP 10.5.0.0 MASK /24 HOSTS 50,")  # Solicita continuar inmediatamente después de la coma.
    assert sugerencia == "20 NAME Sucursal"  # Confirma que 50 no se repita y solamente aparezca la nueva solicitud.


def prueba_predictor_rechaza_ip_generada_incompatible_con_fragmento():  # Comprueba que la IA no pueda sustituir una dirección parcial que ya pertenece al usuario.
    motor = MotorSimulado(
        {
            "ip": "192.168.1.0",  # Proporciona deliberadamente una dirección incompatible con el fragmento IP 10.
            "cidr": 24,  # Incluye datos posteriores que tampoco deben utilizarse si falla la compatibilidad de la IP.
            "hosts": [20],  # Proporciona una cantidad válida pero perteneciente a la sugerencia incompatible.
            "nombre": "OtraRed",  # Proporciona un nombre que igualmente deberá descartarse.
        }
    )  # Simula una respuesta formalmente correcta pero contradictoria con lo que ya escribió el usuario.
    predictor = PredictorCodigo(motor=motor)  # Construye el predictor con la respuesta incompatible.
    sugerencia = predictor.sugerir("IP 10")  # Solicita continuar desde un fragmento que debe permanecer inmutable.
    assert sugerencia is None  # Confirma que el predictor descarte completamente la propuesta en vez de reemplazar el texto del usuario.


def prueba_predictor_rechaza_hosts_nuevos_invalidos():  # Comprueba que hosts_nuevos posea realmente la estructura de lista esperada.
    motor = MotorSimulado(
        {
            "hosts_nuevos": "20",  # Utiliza deliberadamente una cadena en lugar de la lista requerida.
            "nombre": "Sucursal",  # Incluye otro dato válido para confirmar que un campo incorrecto invalide la propuesta completa.
        }
    )  # Prepara una respuesta cuya estructura no cumple el contrato esperado por el predictor.
    predictor = PredictorCodigo(motor=motor)  # Crea el predictor utilizando los datos inválidos.
    sugerencia = predictor.sugerir("IP 10.5.0.0 MASK /24 HOSTS 50,")  # Solicita una nueva cantidad después de otra ya escrita.
    assert sugerencia is None  # Confirma que el predictor no intente interpretar arbitrariamente una estructura incorrecta.


def prueba_predictor_no_consulta_ia_para_linea_valida_o_texto_ajeno():  # Comprueba que el modelo solamente se consulte cuando el análisis contextual realmente necesita generación.
    motor = MotorSimulado(
        {
            "ip": "10.20.30.0",  # Prepara datos que nunca deberían utilizarse en esta prueba.
            "cidr": 24,  # Incluye también una máscara para detectar cualquier consulta innecesaria.
            "hosts": [15],  # Incluye una cantidad igualmente innecesaria.
            "nombre": "",  # Mantiene NAME vacío porque el contenido concreto no debe llegar a consumirse.
        }
    )  # Prepara una respuesta únicamente para detectar accidentalmente cualquier uso del motor.
    predictor = PredictorCodigo(motor=motor)  # Construye el predictor que registrará cuántas consultas intenta realizar.
    sugerencia_valida = predictor.sugerir("IP 10.20.30.0 MASK /24 HOSTS 15")  # Entrega una línea que ya se encuentra completa y no necesita generación.
    sugerencia_ajena = predictor.sugerir("hola mundo")  # Entrega además contenido que no pertenece al lenguaje de TecNet Finder.
    assert sugerencia_valida is None  # Confirma que una instrucción terminada no reciba una continuación artificial.
    assert sugerencia_ajena is None  # Confirma que texto ajeno al DSL tampoco habilite el autocompletado.
    assert motor.cantidad_llamadas == 0  # Verifica que ninguno de ambos casos haya llegado realmente hasta el modelo local.