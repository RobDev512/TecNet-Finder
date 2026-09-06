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
# La información de cada diagnóstico se guarda de forma
# estructurada para evitar manejar los errores únicamente como
# cadenas de texto.
#
# Esto permitirá que otras partes del programa, especialmente la
# interfaz gráfica, puedan conocer directamente datos como:
#
# - Código del diagnóstico.
# - Categoría.
# - Severidad.
# - Mensaje.
# - Línea.
# - Columna.
# - Longitud del fragmento incorrecto.
# - Fragmento relacionado con el problema.
# - Posible solución.
#
# Esta estructura será utilizada posteriormente para señalar
# errores directamente dentro del editor de código mediante
# subrayados y otras ayudas visuales.
# ============================================================


# Importa el decorador dataclass desde la biblioteca estándar de Python.
# Este decorador permite crear clases destinadas principalmente a guardar
# información sin tener que escribir manualmente métodos como __init__.
from dataclasses import dataclass


# Define el catálogo central de diagnósticos conocidos por TecNet Finder.
#
# Por el momento solamente contiene los errores correspondientes al
# análisis léxico, ya que todavía no se ha reconstruido el analizador
# sintáctico ni se ha comenzado el análisis semántico.
#
# Las categorías SIN, SEM y demás se agregarán conforme avance
# el desarrollo del compilador.
CATALOGO_DIAGNOSTICOS = {

    # Define el diagnóstico LEX-001.
    # Este error ocurre cuando se reconoce un identificador, pero aparece
    # en una posición donde el lenguaje TecNet Finder no lo permite.
    "LEX-001": {

        # Indica que este diagnóstico pertenece a la fase léxica.
        "categoria": "Léxico",

        # Guarda un nombre breve que permite identificar el problema.
        "nombre": "Identificador fuera de lugar",

        # Explica de manera general en qué consiste este error.
        "descripcion": (
            "Apareció un identificador en una posición no permitida."
        ),

        # Proporciona una recomendación que puede mostrarse posteriormente
        # al usuario dentro de la interfaz.
        "solucion": (
            "Revisa si escribiste mal una palabra reservada. "
            "Por ejemplo, usa MASK en lugar de MAS. "
            "Si era un nombre de red, debe escribirse después de NAME."
        ),
    },

    # Define el diagnóstico LEX-002.
    # Este error aparece cuando el analizador encuentra un símbolo o
    # fragmento que no coincide con ninguno de los patrones del lenguaje.
    "LEX-002": {

        # Indica que el problema pertenece al análisis léxico.
        "categoria": "Léxico",

        # Guarda un nombre breve para identificar este tipo de error.
        "nombre": "Símbolo o fragmento no reconocido",

        # Describe de manera general la causa del diagnóstico.
        "descripcion": (
            "Apareció un carácter o fragmento que no pertenece al lenguaje."
        ),

        # Indica al usuario qué puede revisar para corregir el problema.
        "solucion": (
            "Elimina el símbolo no permitido o reemplázalo por tokens válidos "
            "como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR."
        ),
    },

        # Define el diagnóstico SIN-001.
    #
    # Este error ocurre cuando después de la palabra reservada IP
    # no aparece una dirección IPv4 completa.
    "SIN-001": {

        # Indica que el diagnóstico pertenece al análisis sintáctico.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del diagnóstico.
        "nombre": "Dirección IP incompleta o mal formada",

        # Explica de manera general por qué ocurre el problema.
        "descripcion": (
            "Después de IP se esperaba una dirección IP completa."
        ),

        # Proporciona una recomendación para corregir la instrucción.
        "solucion": (
            "Escribe una dirección IPv4 completa. "
            "Ejemplo: 192.168.1.0."
        ),
    },

    # Define el diagnóstico SIN-002.
    #
    # Este error ocurre cuando después de la dirección IP
    # no aparece la palabra reservada MASK.
    "SIN-002": {

        # Indica que pertenece a la fase sintáctica.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del problema.
        "nombre": "Falta la palabra reservada MASK",

        # Describe la estructura que se esperaba.
        "descripcion": (
            "Después de la dirección IP se esperaba la palabra MASK."
        ),

        # Indica cómo puede corregirse la instrucción.
        "solucion": (
            "Coloca MASK después de la IP. "
            "Si escribiste MAS u otra variante, cámbiala por MASK. "
            "Ejemplo: IP 192.168.1.0 MASK /24."
        ),
    },

    # Define el diagnóstico SIN-003.
    #
    # Este error se genera cuando después de MASK no aparece
    # una máscara escrita en notación CIDR.
    "SIN-003": {

        # Indica que el diagnóstico pertenece al análisis sintáctico.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del problema.
        "nombre": "Máscara CIDR inválida o incompleta",

        # Describe qué elemento faltó dentro de la instrucción.
        "descripcion": (
            "Después de MASK se esperaba una máscara con diagonal."
        ),

        # Muestra al usuario un ejemplo de la forma correcta.
        "solucion": (
            "Escribe la máscara en formato CIDR. "
            "Ejemplo: /24."
        ),
    },

    # Define el diagnóstico SIN-004.
    #
    # Se genera cuando HOSTS no está seguido por al menos
    # una cantidad numérica.
    "SIN-004": {

        # Indica que el error pertenece al análisis sintáctico.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del diagnóstico.
        "nombre": "Falta cantidad de hosts",

        # Explica qué token se esperaba.
        "descripcion": (
            "Después de HOSTS se esperaba al menos un número."
        ),

        # Proporciona un ejemplo válido.
        "solucion": (
            "Escribe al menos una cantidad de hosts. "
            "Ejemplo: HOSTS 50."
        ),
    },

    # Define el diagnóstico SIN-005.
    #
    # Este error aparece cuando una lista de hosts contiene
    # una coma que no está seguida por otro número.
    "SIN-005": {

        # Indica la fase donde se detectó el problema.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del diagnóstico.
        "nombre": "Lista de hosts mal formada",

        # Explica la regla sintáctica que se incumplió.
        "descripcion": (
            "Después de una coma se esperaba otro número."
        ),

        # Muestra un ejemplo correcto de una lista de hosts.
        "solucion": (
            "Corrige la lista de hosts. "
            "Ejemplo correcto: HOSTS 100,200."
        ),
    },

    # Define el diagnóstico SIN-006.
    #
    # Este problema ocurre cuando aparece NAME pero no existe
    # después un identificador que represente el nombre de la red.
    "SIN-006": {

        # Indica que pertenece al análisis sintáctico.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del error.
        "nombre": "Nombre de red incompleto",

        # Describe el elemento que se esperaba después de NAME.
        "descripcion": (
            "Después de NAME se esperaba un identificador."
        ),

        # Explica las dos formas posibles de corregirlo.
        "solucion": (
            "Escribe un nombre después de NAME o elimina NAME "
            "si no usarás nombre."
        ),
    },

    # Define el diagnóstico SIN-007.
    #
    # Se utiliza cuando una instrucción completa es exactamente
    # igual a otra instrucción válida procesada anteriormente.
    "SIN-007": {

        # Indica que el diagnóstico pertenece a la sintaxis.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del problema.
        "nombre": "Instrucción duplicada",

        # Explica qué provoca este diagnóstico.
        "descripcion": (
            "Se declaró una instrucción exactamente igual a otra anterior."
        ),

        # Indica qué elementos pueden modificarse para evitar el duplicado.
        "solucion": (
            "Elimina la instrucción repetida o cambia IP, máscara, "
            "hosts o nombre."
        ),
    },

    # Define el diagnóstico SIN-008.
    #
    # Es el error sintáctico general utilizado cuando los tokens
    # existen, pero aparecen en un orden diferente al de la gramática.
    "SIN-008": {

        # Indica que pertenece al análisis sintáctico.
        "categoria": "Sintáctico",

        # Guarda el nombre breve del diagnóstico.
        "nombre": "Orden incorrecto de tokens",

        # Describe de manera general el problema encontrado.
        "descripcion": (
            "Los tokens existen, pero no aparecen en el orden esperado."
        ),

        # Muestra la estructura general de una instrucción válida
        # de TecNet Finder.
        "solucion": (
            "Revisa que la instrucción siga esta estructura: "
            "IP <IP_ADDRESS> MASK <SUBNET_MASK> "
            "HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]."
        ),
    },

    # Define un diagnóstico general de respaldo.
    # Se utiliza cuando se solicita crear un diagnóstico cuyo código todavía
    # no se encuentra registrado dentro del catálogo.
    "GEN-001": {

        # Este diagnóstico no pertenece a una fase específica.
        "categoria": "General",

        # Nombre utilizado para identificar el error de respaldo.
        "nombre": "Error no clasificado",

        # Explica que el problema existe, pero aún no está clasificado.
        "descripcion": (
            "El error fue detectado, pero no coincide con una categoría específica."
        ),

        # Ofrece una recomendación general mientras no exista una solución
        # más específica dentro del catálogo.
        "solucion": (
            "Revisa la estructura general de la instrucción."
        ),
    },
}


# Convierte la clase Diagnostico en una estructura de datos inmutable.
#
# frozen=True evita modificar accidentalmente la información de un
# diagnóstico después de que haya sido creado.
@dataclass(frozen=True)
class Diagnostico:

    # Guarda el código único que identifica el tipo de diagnóstico.
    # Ejemplos futuros: LEX-001, SIN-001 o SEM-001.
    codigo: str

    # Guarda la categoría o fase del compilador donde ocurrió el problema.
    categoria: str

    # Indica la gravedad del diagnóstico.
    # Por ahora normalmente será "error", aunque posteriormente también
    # podremos utilizar valores como "advertencia".
    severidad: str

    # Contiene el mensaje específico que se mostrará al usuario.
    mensaje: str

    # Guarda el número de línea donde ocurrió el problema.
    # Se permite None cuando un diagnóstico no está relacionado con
    # una línea específica del código fuente.
    linea: int | None = None

    # Guarda la columna donde comienza el fragmento problemático.
    # También puede ser None si no existe una posición concreta.
    columna: int | None = None

    # Indica cuántos caracteres ocupa el fragmento relacionado con el error.
    # Esta información será útil para subrayar el texto dentro del editor.
    longitud: int = 1

    # Guarda el texto exacto que produjo o se relaciona con el diagnóstico.
    fragmento: str = ""

    # Guarda una recomendación para ayudar al usuario a corregir el problema.
    solucion: str = ""


# Crea un objeto Diagnostico utilizando un código y la información
# correspondiente almacenada en el catálogo de diagnósticos.
def crear_diagnostico(
    codigo: str,
    mensaje: str,
    linea: int | None = None,
    columna: int | None = None,
    longitud: int = 1,
    fragmento: str = "",
    severidad: str = "error",
) -> Diagnostico:

    # Busca dentro del catálogo la información correspondiente al código.
    #
    # Si el código solicitado no existe, se utiliza GEN-001 para evitar
    # que el programa falle al intentar crear el diagnóstico.
    informacion = CATALOGO_DIAGNOSTICOS.get(
        codigo,
        CATALOGO_DIAGNOSTICOS["GEN-001"],
    )

    # Crea y devuelve el diagnóstico final utilizando tanto la información
    # general del catálogo como los datos específicos del error encontrado.
    return Diagnostico(

        # Guarda el código recibido por la función.
        codigo=codigo,

        # Obtiene la categoría correspondiente desde el catálogo.
        categoria=informacion["categoria"],

        # Guarda la severidad recibida.
        severidad=severidad,

        # Guarda el mensaje específico generado durante el análisis.
        mensaje=mensaje,

        # Guarda la línea donde se encontró el problema.
        linea=linea,

        # Guarda la columna donde comienza el problema.
        columna=columna,

        # Asegura que la longitud nunca sea menor que un carácter.
        longitud=max(longitud, 1),

        # Guarda el fragmento de código relacionado.
        fragmento=fragmento,

        # Obtiene del catálogo la recomendación correspondiente.
        solucion=informacion["solucion"],
    )