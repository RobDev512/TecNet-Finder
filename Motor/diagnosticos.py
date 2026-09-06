# ============================================================
# Archivo: diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las estructuras y funciones utilizadas
# para representar los errores y advertencias detectados durante
# las diferentes fases del compilador.
#
# Cada diagnóstico guarda información estructurada como código,
# categoría, severidad, posición, fragmento y posible solución.
# Actualmente contiene diagnósticos léxicos y sintácticos.
# ============================================================

from dataclasses import dataclass  # Importa el decorador utilizado para crear clases de datos.


CATALOGO_DIAGNOSTICOS = {  # Centraliza la información general de los diagnósticos conocidos por TecNet Finder.
    "LEX-001": {  # Define el error producido por un identificador escrito fuera de una posición permitida.
        "categoria": "Léxico",  # Indica la fase donde se detecta el problema.
        "nombre": "Identificador fuera de lugar",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Apareció un identificador en una posición no permitida.",  # Resume la causa del error.
        "solucion": (  # Guarda la recomendación que podrá mostrarse al usuario.
            "Revisa si escribiste mal una palabra reservada. "
            "Por ejemplo, usa MASK en lugar de MAS. "
            "Si era un nombre de red, debe escribirse después de NAME."
        ),
    },
    "LEX-002": {  # Define el error producido por un símbolo o fragmento que no pertenece al lenguaje.
        "categoria": "Léxico",  # Indica la fase donde se detecta el problema.
        "nombre": "Símbolo o fragmento no reconocido",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Apareció un carácter o fragmento que no pertenece al lenguaje.",  # Resume la causa del error.
        "solucion": (  # Guarda la recomendación que podrá mostrarse al usuario.
            "Elimina el símbolo no permitido o reemplázalo por tokens válidos "
            "como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR."
        ),
    },
    "SIN-001": {  # Define el error producido por una dirección IP incompleta o mal formada.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Dirección IP incompleta o mal formada",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Después de IP se esperaba una dirección IP completa.",  # Resume la regla sintáctica incumplida.
        "solucion": "Escribe una dirección IPv4 completa. Ejemplo: 192.168.1.0.",  # Sugiere una forma válida.
    },
    "SIN-002": {  # Define el error producido cuando falta la palabra reservada MASK.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Falta la palabra reservada MASK",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Después de la dirección IP se esperaba la palabra MASK.",  # Resume la regla sintáctica incumplida.
        "solucion": (  # Guarda una recomendación para corregir la instrucción.
            "Coloca MASK después de la IP. Si escribiste MAS u otra variante, "
            "cámbiala por MASK. Ejemplo: IP 192.168.1.0 MASK /24."
        ),
    },
    "SIN-003": {  # Define el error producido cuando falta una máscara escrita en notación CIDR.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Máscara CIDR inválida o incompleta",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Después de MASK se esperaba una máscara con diagonal.",  # Resume la regla sintáctica incumplida.
        "solucion": "Escribe la máscara en formato CIDR. Ejemplo: /24.",  # Sugiere una forma válida.
    },
    "SIN-004": {  # Define el error producido cuando HOSTS no recibe ninguna cantidad numérica.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Falta cantidad de hosts",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Después de HOSTS se esperaba al menos un número.",  # Resume la regla sintáctica incumplida.
        "solucion": "Escribe al menos una cantidad de hosts. Ejemplo: HOSTS 50.",  # Sugiere una forma válida.
    },
    "SIN-005": {  # Define el error producido por una lista de hosts mal formada.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Lista de hosts mal formada",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Después de una coma se esperaba otro número.",  # Resume la regla sintáctica incumplida.
        "solucion": "Corrige la lista de hosts. Ejemplo correcto: HOSTS 100,200.",  # Sugiere una forma válida.
    },
    "SIN-006": {  # Define el error producido cuando NAME no recibe un identificador.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Nombre de red incompleto",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Después de NAME se esperaba un identificador.",  # Resume la regla sintáctica incumplida.
        "solucion": "Escribe un nombre después de NAME o elimina NAME si no usarás nombre.",  # Sugiere cómo corregirlo.
    },
    "SIN-007": {  # Define el error producido cuando una instrucción válida se repite exactamente.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Instrucción duplicada",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Se declaró una instrucción exactamente igual a otra anterior.",  # Resume la causa del error.
        "solucion": "Elimina la instrucción repetida o cambia IP, máscara, hosts o nombre.",  # Sugiere cómo corregirlo.
    },
    "SIN-008": {  # Define el error general producido por un orden incorrecto de tokens.
        "categoria": "Sintáctico",  # Indica la fase donde se detecta el problema.
        "nombre": "Orden incorrecto de tokens",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "Los tokens existen, pero no aparecen en el orden esperado.",  # Resume la causa del error.
        "solucion": (  # Muestra la estructura general aceptada por la gramática.
            "Revisa que la instrucción siga esta estructura: "
            "IP <IP_ADDRESS> MASK <SUBNET_MASK> "
            "HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]."
        ),
    },
    "GEN-001": {  # Define un diagnóstico de respaldo para códigos todavía no registrados.
        "categoria": "General",  # Indica que no pertenece a una fase específica.
        "nombre": "Error no clasificado",  # Guarda el nombre corto del diagnóstico.
        "descripcion": "El error fue detectado, pero no coincide con una categoría específica.",  # Resume su propósito.
        "solucion": "Revisa la estructura general de la instrucción.",  # Proporciona una recomendación general.
    },
}


@dataclass(frozen=True)  # Convierte Diagnostico en una clase de datos inmutable.
class Diagnostico:  # Representa un error o advertencia detectado por TecNet Finder.
    codigo: str  # Guarda el código único del diagnóstico, por ejemplo LEX-001 o SIN-001.
    categoria: str  # Guarda la fase o categoría donde ocurrió el problema.
    severidad: str  # Indica si se trata de un error, advertencia u otra severidad futura.
    mensaje: str  # Guarda el mensaje específico que se mostrará al usuario.
    linea: int | None = None  # Guarda la línea del problema cuando existe una posición concreta.
    columna: int | None = None  # Guarda la columna donde comienza el fragmento problemático.
    longitud: int = 1  # Indica cuántos caracteres deben relacionarse visualmente con el diagnóstico.
    fragmento: str = ""  # Guarda el texto exacto relacionado con el problema.
    solucion: str = ""  # Guarda una recomendación para ayudar a corregir el problema.


def crear_diagnostico(  # Crea un objeto Diagnostico usando los datos específicos del error y su catálogo.
    codigo: str,  # Recibe el código del diagnóstico que se desea crear.
    mensaje: str,  # Recibe el mensaje específico generado durante el análisis.
    linea: int | None = None,  # Recibe la línea donde ocurrió el problema.
    columna: int | None = None,  # Recibe la columna donde comienza el problema.
    longitud: int = 1,  # Recibe la cantidad de caracteres relacionados con el problema.
    fragmento: str = "",  # Recibe el texto exacto que produjo o acompaña al diagnóstico.
    severidad: str = "error",  # Recibe la gravedad del diagnóstico y usa error como valor predeterminado.
) -> Diagnostico:  # Devuelve un diagnóstico completamente estructurado.
    informacion = CATALOGO_DIAGNOSTICOS.get(  # Busca la información general asociada al código solicitado.
        codigo,  # Utiliza el código recibido como clave de búsqueda.
        CATALOGO_DIAGNOSTICOS["GEN-001"],  # Usa el diagnóstico general si el código todavía no existe.
    )

    return Diagnostico(  # Construye y devuelve el diagnóstico final.
        codigo=codigo,  # Guarda el código recibido.
        categoria=informacion["categoria"],  # Obtiene la categoría registrada en el catálogo.
        severidad=severidad,  # Guarda la severidad recibida.
        mensaje=mensaje,  # Guarda el mensaje específico del problema.
        linea=linea,  # Guarda la línea relacionada con el diagnóstico.
        columna=columna,  # Guarda la columna relacionada con el diagnóstico.
        longitud=max(longitud, 1),  # Evita que la longitud visual sea menor que un carácter.
        fragmento=fragmento,  # Guarda el fragmento relacionado con el diagnóstico.
        solucion=informacion["solucion"],  # Obtiene la recomendación correspondiente desde el catálogo.
    )
