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