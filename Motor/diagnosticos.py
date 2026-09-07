# ============================================================
# Archivo: diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las estructuras y funciones utilizadas
# para representar los errores y advertencias detectados durante
# las diferentes partes de TecNet Finder.
#
# Cada diagnóstico guarda información estructurada como código,
# categoría, severidad, posición, fragmento y posible solución.
# ============================================================

from dataclasses import dataclass  # Importa el decorador utilizado para crear clases de datos.


CATALOGO_DIAGNOSTICOS = {  # Centraliza la información general de los diagnósticos conocidos por TecNet Finder.
    "LEX-001": {  # Define el error producido por un identificador escrito fuera de una posición permitida.
        "categoria": "Léxico",
        "nombre": "Identificador fuera de lugar",
        "descripcion": "Apareció un identificador en una posición no permitida.",
        "solucion": (
            "Revisa si escribiste mal una palabra reservada. "
            "Por ejemplo, usa MASK en lugar de MAS. "
            "Si era un nombre de red, debe escribirse después de NAME."
        ),
    },
    "LEX-002": {  # Define el error producido por un símbolo o fragmento que no pertenece al lenguaje.
        "categoria": "Léxico",
        "nombre": "Símbolo o fragmento no reconocido",
        "descripcion": "Apareció un carácter o fragmento que no pertenece al lenguaje.",
        "solucion": (
            "Elimina el símbolo no permitido o reemplázalo por tokens válidos "
            "como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR."
        ),
    },
    "SIN-001": {  # Define el error producido por una dirección IP incompleta o mal formada.
        "categoria": "Sintáctico",
        "nombre": "Dirección IP incompleta o mal formada",
        "descripcion": "Después de IP se esperaba una dirección IP completa.",
        "solucion": "Escribe una dirección IPv4 completa. Ejemplo: 192.168.1.0.",
    },
    "SIN-002": {  # Define el error producido cuando falta la palabra reservada MASK.
        "categoria": "Sintáctico",
        "nombre": "Falta la palabra reservada MASK",
        "descripcion": "Después de la dirección IP se esperaba la palabra MASK.",
        "solucion": (
            "Coloca MASK después de la IP. Si escribiste MAS u otra variante, "
            "cámbiala por MASK. Ejemplo: IP 192.168.1.0 MASK /24."
        ),
    },
    "SIN-003": {  # Define el error producido cuando falta una máscara escrita en notación CIDR.
        "categoria": "Sintáctico",
        "nombre": "Máscara CIDR inválida o incompleta",
        "descripcion": "Después de MASK se esperaba una máscara con diagonal.",
        "solucion": "Escribe la máscara en formato CIDR. Ejemplo: /24.",
    },
    "SIN-004": {  # Define el error producido cuando HOSTS no recibe ninguna cantidad numérica.
        "categoria": "Sintáctico",
        "nombre": "Falta cantidad de hosts",
        "descripcion": "Después de HOSTS se esperaba al menos un número.",
        "solucion": "Escribe al menos una cantidad de hosts. Ejemplo: HOSTS 50.",
    },
    "SIN-005": {  # Define el error producido por una lista de hosts mal formada.
        "categoria": "Sintáctico",
        "nombre": "Lista de hosts mal formada",
        "descripcion": "Después de una coma se esperaba otro número.",
        "solucion": "Corrige la lista de hosts. Ejemplo correcto: HOSTS 100,200.",
    },
    "SIN-006": {  # Define el error producido cuando NAME no recibe un identificador.
        "categoria": "Sintáctico",
        "nombre": "Nombre de red incompleto",
        "descripcion": "Después de NAME se esperaba un identificador.",
        "solucion": "Escribe un nombre después de NAME o elimina NAME si no usarás nombre.",
    },
    "SIN-007": {  # Define el error producido cuando una instrucción válida se repite exactamente.
        "categoria": "Sintáctico",
        "nombre": "Instrucción duplicada",
        "descripcion": "Se declaró una instrucción exactamente igual a otra anterior.",
        "solucion": "Elimina la instrucción repetida o cambia IP, máscara, hosts o nombre.",
    },
    "SIN-008": {  # Define el error general producido por un orden incorrecto de tokens.
        "categoria": "Sintáctico",
        "nombre": "Orden incorrecto de tokens",
        "descripcion": "Los tokens existen, pero no aparecen en el orden esperado.",
        "solucion": (
            "Revisa que la instrucción siga esta estructura: "
            "IP <IP_ADDRESS> MASK <SUBNET_MASK> "
            "HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]."
        ),
    },
    "ADV-001": {  # Define la advertencia utilizada cuando algunos bloques pueden procesarse a pesar de existir errores.
        "categoria": "Advertencia",
        "nombre": "Procesamiento parcial",
        "descripcion": "Hay errores, pero también existen bloques válidos que pueden procesarse.",
        "solucion": "Revisa las líneas con error. El sistema continuará únicamente con bloques válidos.",
    },
    "ADV-002": {  # Define la recomendación sobre separación entre palabras reservadas y valores.
        "categoria": "Advertencia",
        "nombre": "Palabra reservada pegada al valor",
        "descripcion": "Una palabra reservada aparece pegada al valor siguiente.",
        "solucion": (
            "Se recomienda separar con espacios. "
            "Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50."
        ),
    },
    "ADV-003": {  # Define la advertencia producida cuando diferentes instrucciones comparten nombre.
        "categoria": "Advertencia",
        "nombre": "Nombre de red repetido",
        "descripcion": "Dos o más instrucciones usan el mismo nombre de red.",
        "solucion": (
            "Usa nombres distintos para evitar confusión en la tabla VLSM, "
            "en el Excel o en la interpretación de resultados."
        ),
    },
    "ADV-004": {  # Define la advertencia producida por cantidades repetidas dentro de HOSTS.
        "categoria": "Advertencia",
        "nombre": "Hosts repetidos",
        "descripcion": "La lista de hosts contiene cantidades repetidas dentro de la misma instrucción.",
        "solucion": (
            "Revisa si los hosts repetidos fueron intencionales. "
            "Si no, elimina o corrige los valores duplicados."
        ),
    },
    "ADV-005": {  # Reserva el diagnóstico de red sobredimensionada para la futura integración con análisis semántico.
        "categoria": "Advertencia",
        "nombre": "Red base sobredimensionada",
        "descripcion": "La red base tiene mucha más capacidad de la que realmente se utiliza.",
        "solucion": (
            "Considera usar una máscara base más pequeña si deseas optimizar "
            "mejor el espacio de direcciones."
        ),
    },
    "ADV-006": {  # Define la recomendación sobre nombres demasiado genéricos.
        "categoria": "Advertencia",
        "nombre": "Nombre de red genérico",
        "descripcion": "El nombre de la red es demasiado genérico y puede causar confusión.",
        "solucion": (
            "Usa un nombre más descriptivo, por ejemplo OficinaCentral, "
            "LaboratorioRedes o SucursalTepic."
        ),
    },
    "ADV-007": {  # Define la recomendación producida cuando NAME no fue especificado.
        "categoria": "Advertencia",
        "nombre": "Nombre de red no especificado",
        "descripcion": "La instrucción no incluye un nombre para identificar la red.",
        "solucion": (
            "Agrega NAME seguido de un identificador para facilitar la lectura "
            "de resultados y reportes."
        ),
    },
    "GEN-001": {  # Define un diagnóstico de respaldo para códigos todavía no registrados.
        "categoria": "General",
        "nombre": "Error no clasificado",
        "descripcion": "El error fue detectado, pero no coincide con una categoría específica.",
        "solucion": "Revisa la estructura general de la instrucción.",
    },
}


@dataclass(frozen=True)
class Diagnostico:  # Representa un error o advertencia detectado por TecNet Finder.
    codigo: str  # Guarda el código único del diagnóstico, por ejemplo LEX-001 o ADV-002.
    categoria: str  # Guarda la fase o categoría donde ocurrió el problema.
    severidad: str  # Indica si se trata de un error o una advertencia.
    mensaje: str  # Guarda el mensaje específico que se mostrará al usuario.
    linea: int | None = None  # Guarda la línea del problema cuando existe una posición concreta.
    columna: int | None = None  # Guarda la columna donde comienza el fragmento problemático.
    longitud: int = 1  # Indica cuántos caracteres deben relacionarse visualmente con el diagnóstico.
    fragmento: str = ""  # Guarda el texto exacto relacionado con el problema.
    solucion: str = ""  # Guarda una recomendación para ayudar a corregir el problema.


def crear_diagnostico(
    codigo: str,
    mensaje: str,
    linea: int | None = None,
    columna: int | None = None,
    longitud: int = 1,
    fragmento: str = "",
    severidad: str = "error",
) -> Diagnostico:  # Crea un objeto Diagnostico usando los datos específicos del error y su catálogo.
    informacion = CATALOGO_DIAGNOSTICOS.get(
        codigo,
        CATALOGO_DIAGNOSTICOS["GEN-001"],
    )

    return Diagnostico(
        codigo=codigo,
        categoria=informacion["categoria"],
        severidad=severidad,
        mensaje=mensaje,
        linea=linea,
        columna=columna,
        longitud=max(longitud, 1),
        fragmento=fragmento,
        solucion=informacion["solucion"],
    )