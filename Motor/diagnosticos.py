# ============================================================
# Archivo: diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las estructuras, el catálogo y las
# funciones utilizadas para representar los diagnósticos de
# TecNet Finder.
#
# El catálogo también indica qué códigos están disponibles en
# la base actual y cuáles permanecen pendientes para LyAII.
#
# Al finalizar las validaciones de U1, SEM-001 a SEM-006 y
# ADV-005 forman parte del comportamiento disponible.
# ============================================================

from dataclasses import dataclass  # Importa el decorador utilizado para crear clases de datos.


ESTADO_DIAGNOSTICO_DISPONIBLE = "disponible"  # Identifica diagnósticos que la versión actual ya puede producir y evaluar.
ESTADO_DIAGNOSTICO_PENDIENTE = "pendiente"  # Identifica diagnósticos reservados para una fase posterior.


CATALOGO_DIAGNOSTICOS = {
    "LEX-001": {
        "categoria": "Léxico",
        "nombre": "Identificador fuera de lugar",
        "descripcion": "Apareció un identificador en una posición no permitida.",
        "solucion": "Revisa si escribiste mal una palabra reservada. Por ejemplo, usa MASK en lugar de MAS. Si era un nombre de red, debe escribirse después de NAME.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "LEX-002": {
        "categoria": "Léxico",
        "nombre": "Símbolo o fragmento no reconocido",
        "descripcion": "Apareció un carácter o fragmento que no pertenece al lenguaje.",
        "solucion": "Elimina el símbolo no permitido o reemplázalo por tokens válidos como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "LEX-003": {
        "categoria": "Léxico",
        "nombre": "Palabra reservada con mayúsculas incorrectas",
        "descripcion": "Una palabra reservada fue escrita con una combinación de mayúsculas y minúsculas distinta de la definida por el lenguaje.",
        "solucion": "Escribe las palabras reservadas exactamente como IP, MASK, HOSTS o NAME. Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Refuerzo LyAII",
    },
    "LEX-004": {
        "categoria": "Léxico",
        "nombre": "Elemento numérico unido a texto",
        "descripcion": "Un número o una máscara CIDR apareció unido directamente a letras sin un separador válido entre ambos elementos.",
        "solucion": "Separa los elementos con un espacio. Ejemplo: HOSTS 50 NAME Oficina o MASK /24 HOSTS 50.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Refuerzo LyAII",
    },
    "SIN-001": {
        "categoria": "Sintáctico",
        "nombre": "Dirección IP incompleta o mal formada",
        "descripcion": "Después de IP se esperaba una dirección IP completa.",
        "solucion": "Escribe una dirección IPv4 completa. Ejemplo: 192.168.1.0.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-002": {
        "categoria": "Sintáctico",
        "nombre": "Falta la palabra reservada MASK",
        "descripcion": "Después de la dirección IP se esperaba la palabra MASK.",
        "solucion": "Coloca MASK después de la IP. Si escribiste MAS u otra variante, cámbiala por MASK. Ejemplo: IP 192.168.1.0 MASK /24.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-003": {
        "categoria": "Sintáctico",
        "nombre": "Máscara CIDR inválida o incompleta",
        "descripcion": "Después de MASK se esperaba una máscara con diagonal.",
        "solucion": "Escribe la máscara en formato CIDR. Ejemplo: /24.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-004": {
        "categoria": "Sintáctico",
        "nombre": "Falta cantidad de hosts",
        "descripcion": "Después de HOSTS se esperaba al menos un número.",
        "solucion": "Escribe al menos una cantidad de hosts. Ejemplo: HOSTS 50.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-005": {
        "categoria": "Sintáctico",
        "nombre": "Lista de hosts mal formada",
        "descripcion": "Después de una coma se esperaba otro número.",
        "solucion": "Corrige la lista de hosts. Ejemplo correcto: HOSTS 100,200.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-006": {
        "categoria": "Sintáctico",
        "nombre": "Nombre de red incompleto",
        "descripcion": "Después de NAME se esperaba un identificador.",
        "solucion": "Escribe un nombre después de NAME o elimina NAME si no usarás nombre.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-007": {
        "categoria": "Sintáctico",
        "nombre": "Instrucción duplicada",
        "descripcion": "Se declaró una instrucción exactamente igual a otra anterior.",
        "solucion": "Elimina la instrucción repetida o cambia IP, máscara, hosts o nombre.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SIN-008": {
        "categoria": "Sintáctico",
        "nombre": "Orden incorrecto de tokens",
        "descripcion": "Los tokens existen, pero no aparecen en el orden esperado.",
        "solucion": "Revisa que la instrucción siga esta estructura: IP <IP_ADDRESS> MASK <SUBNET_MASK> HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>].",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "SEM-001": {
        "categoria": "Semántico",
        "nombre": "Máscara fuera de rango",
        "descripcion": "La máscara CIDR existe sintácticamente, pero está fuera del rango permitido.",
        "solucion": "Usa una máscara entre /8 y /30. Ejemplo: MASK /24.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "SEM-002": {
        "categoria": "Semántico",
        "nombre": "IP base no es dirección de red",
        "descripcion": "La IP indicada no corresponde a la dirección de red para la máscara dada.",
        "solucion": "Usa la dirección de red correcta para esa máscara. Por ejemplo, para 192.168.1.5/24 la red correcta sería 192.168.1.0.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "SEM-003": {
        "categoria": "Semántico",
        "nombre": "Cantidad de hosts no válida",
        "descripcion": "Una cantidad de hosts debe ser mayor que cero.",
        "solucion": "Cambia la cantidad de hosts por un número positivo. Ejemplo: HOSTS 50.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "SEM-004": {
        "categoria": "Semántico",
        "nombre": "Hosts no caben en la red base",
        "descripcion": "La suma de los bloques VLSM solicitados excede la capacidad de la red base.",
        "solucion": "Usa una red base con mayor capacidad, por ejemplo /23 en lugar de /24, o reduce las cantidades de hosts solicitadas.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "SEM-005": {
        "categoria": "Semántico",
        "nombre": "Subred individual demasiado grande",
        "descripcion": "Una cantidad de hosts necesita un bloque VLSM mayor que toda la red base disponible.",
        "solucion": "Reduce la cantidad de hosts o utiliza una red base con mayor capacidad.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "SEM-006": {
        "categoria": "Semántico",
        "nombre": "Redes base traslapadas",
        "descripcion": "Una red base válida se cruza con otra red base declarada anteriormente.",
        "solucion": "Cambia la IP base o la máscara de la red posterior para que sus rangos IPv4 no se traslapen.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "ADV-001": {
        "categoria": "Advertencia",
        "nombre": "Procesamiento parcial",
        "descripcion": "Hay errores, pero también existen bloques válidos que pueden procesarse.",
        "solucion": "Revisa las líneas con error. El sistema continuará únicamente con bloques válidos.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "ADV-002": {
        "categoria": "Advertencia",
        "nombre": "Palabra reservada pegada al valor",
        "descripcion": "Una palabra reservada aparece pegada al valor siguiente.",
        "solucion": "Se recomienda separar con espacios. Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "ADV-003": {
        "categoria": "Advertencia",
        "nombre": "Nombre de red repetido",
        "descripcion": "Dos o más instrucciones usan el mismo nombre de red.",
        "solucion": "Usa nombres distintos para evitar confusión en la tabla VLSM, en el Excel o en la interpretación de resultados.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "ADV-004": {
        "categoria": "Advertencia",
        "nombre": "Hosts repetidos",
        "descripcion": "La lista de hosts contiene cantidades repetidas dentro de la misma instrucción.",
        "solucion": "Revisa si los hosts repetidos fueron intencionales. Si no, elimina o corrige los valores duplicados.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "ADV-005": {
        "categoria": "Advertencia",
        "nombre": "Red base sobredimensionada",
        "descripcion": "La red base dispone de al menos dieciséis veces la capacidad realmente requerida por las solicitudes VLSM.",
        "solucion": "Considera utilizar una máscara base más específica para aprovechar mejor el espacio de direcciones disponible.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "U1",
    },
    "ADV-006": {
        "categoria": "Advertencia",
        "nombre": "Nombre de red genérico",
        "descripcion": "El nombre de la red es demasiado genérico y puede causar confusión.",
        "solucion": "Usa un nombre más descriptivo, por ejemplo OficinaCentral, LaboratorioRedes o SucursalTepic.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "ADV-007": {
        "categoria": "Advertencia",
        "nombre": "Nombre de red no especificado",
        "descripcion": "La instrucción no incluye un nombre para identificar la red.",
        "solucion": "Agrega NAME seguido de un identificador para facilitar la lectura de resultados y reportes.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
    "ADV-008": {
        "categoria": "Advertencia",
        "nombre": "Hosts fuera del orden recomendado",
        "descripcion": "Las cantidades de HOSTS no están escritas de mayor a menor, aunque TecNet Finder puede ordenarlas internamente para realizar el cálculo VLSM.",
        "solucion": "Se recomienda escribir las cantidades de mayor a menor para que la entrada coincida con el orden utilizado por VLSM. Ejemplo: HOSTS 100,50,20.",
        "severidad": "advertencia",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Refuerzo LyAII",
    },
    "GEN-001": {
        "categoria": "General",
        "nombre": "Error no clasificado",
        "descripcion": "El error fue detectado, pero no coincide con una categoría específica.",
        "solucion": "Revisa la estructura general de la instrucción.",
        "severidad": "error",
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,
        "etapa": "Base LyAI",
    },
}


@dataclass(frozen=True)
class Diagnostico:
    codigo: str
    categoria: str
    severidad: str
    mensaje: str
    linea: int | None = None
    columna: int | None = None
    longitud: int = 1
    fragmento: str = ""
    solucion: str = ""


def obtener_informacion_diagnostico(codigo: str) -> dict:
    return CATALOGO_DIAGNOSTICOS.get(codigo, CATALOGO_DIAGNOSTICOS["GEN-001"])


def obtener_catalogo_diagnosticos() -> list[tuple[str, dict]]:
    return list(CATALOGO_DIAGNOSTICOS.items())


def codigo_diagnostico_disponible(codigo: str) -> bool:
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)
    return bool(informacion and informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE)


def codigo_diagnostico_es_error(codigo: str) -> bool:
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)
    return bool(informacion and informacion["severidad"] == "error")


def obtener_codigos_diagnosticos_disponibles() -> list[str]:
    return [
        codigo
        for codigo, informacion in CATALOGO_DIAGNOSTICOS.items()
        if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE
    ]


def obtener_codigos_diagnosticos_pendientes() -> list[str]:
    return [
        codigo
        for codigo, informacion in CATALOGO_DIAGNOSTICOS.items()
        if informacion["estado"] == ESTADO_DIAGNOSTICO_PENDIENTE
    ]


def texto_estado_diagnostico(codigo: str) -> str:
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)

    if informacion is None:
        return "No registrado"

    if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE:
        return "Disponible"

    etapa = informacion.get("etapa", "").strip()
    return f"Pendiente {etapa}" if etapa else "Pendiente"


def crear_diagnostico(
    codigo: str,
    mensaje: str,
    linea: int | None = None,
    columna: int | None = None,
    longitud: int = 1,
    fragmento: str = "",
    severidad: str | None = None,
) -> Diagnostico:
    informacion = obtener_informacion_diagnostico(codigo)
    severidad_final = severidad or informacion["severidad"]

    return Diagnostico(
        codigo=codigo,
        categoria=informacion["categoria"],
        severidad=severidad_final,
        mensaje=mensaje,
        linea=linea,
        columna=columna,
        longitud=max(longitud, 1),
        fragmento=fragmento,
        solucion=informacion["solucion"],
    )