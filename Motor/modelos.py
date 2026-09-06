# ============================================================
# Archivo: modelos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las estructuras de datos compartidas
# entre diferentes partes del proyecto TecNet Finder.
#
# Su objetivo es almacenar la información de manera organizada
# mediante clases, evitando utilizar listas, tuplas o
# diccionarios cuyos índices sean difíciles de recordar.
#
# Por el momento se definen las estructuras utilizadas por el
# analizador léxico.
#
# Conforme avance el proyecto se podrán agregar aquí otros
# modelos utilizados por el analizador sintáctico, semántico
# y las siguientes fases del compilador.
# ============================================================


# Importa dataclass desde la biblioteca estándar de Python.
#
# dataclass permite crear clases diseñadas principalmente para
# almacenar información sin tener que escribir manualmente
# métodos como __init__.
#
# También se importa field, que permite definir valores
# predeterminados de forma segura para atributos como listas.
from dataclasses import dataclass, field


# Importa la clase Diagnostico definida dentro del Motor.
#
# Los resultados de las diferentes fases del compilador pueden
# incluir una lista de diagnósticos encontrados durante el análisis.
from Motor.diagnosticos import Diagnostico


# Convierte la clase Token en una estructura de datos inmutable.
#
# frozen=True impide modificar accidentalmente los datos de un
# token después de que haya sido creado por el analizador léxico.
@dataclass(frozen=True)
class Token:

    # Guarda el tipo de token reconocido.
    #
    # Algunos ejemplos son:
    # IP, MASK, HOSTS, NUMBER o IDENTIFIER.
    tipo: str

    # Guarda exactamente el texto que fue reconocido dentro
    # del código fuente.
    valor: str

    # Guarda el número de línea donde comienza el token.
    #
    # Las líneas se numeran comenzando desde 1.
    linea: int

    # Guarda la columna donde comienza el token dentro de la línea.
    columna: int


# Convierte ResultadoLexico en una estructura de datos.
#
# Esta clase representa todo lo obtenido después de ejecutar
# el analizador léxico sobre un código fuente.
@dataclass
class ResultadoLexico:

    # Guarda todos los tokens que fueron reconocidos correctamente.
    #
    # default_factory=list crea una lista nueva para cada objeto,
    # evitando que diferentes resultados compartan accidentalmente
    # la misma lista.
    tokens: list[Token] = field(default_factory=list)

    # Guarda todos los errores o advertencias encontrados durante
    # el análisis léxico.
    #
    # Cada elemento de esta lista será un objeto Diagnostico.
    diagnosticos: list[Diagnostico] = field(default_factory=list)

    # Define una propiedad que permite consultar fácilmente si
    # el resultado contiene al menos un diagnóstico de severidad error.
    @property
    def tiene_errores(self) -> bool:

        # Recorre los diagnósticos y devuelve True cuando encuentra
        # por lo menos uno cuya severidad sea exactamente "error".
        #
        # Si ninguno cumple la condición, any devuelve False.
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )


# ============================================================
# MODELOS UTILIZADOS POR EL ANALIZADOR SINTÁCTICO
# ============================================================


# Convierte BloqueRed en una estructura organizada de datos.
#
# Esta clase representa una instrucción de TecNet Finder que
# consiguió cumplir correctamente la estructura sintáctica
# esperada por el lenguaje.
@dataclass
class BloqueRed:

    # Guarda la dirección IPv4 escrita después de la palabra IP.
    direccion_ip: str

    # Guarda la máscara CIDR escrita después de MASK.
    #
    # Algunos ejemplos posibles son /8, /16 o /24.
    mascara_subred: str

    # Guarda todas las cantidades escritas después de HOSTS.
    #
    # Se utiliza default_factory para crear una lista independiente
    # para cada bloque de red.
    cantidades_hosts: list[int] = field(default_factory=list)

    # Guarda el identificador escrito después de NAME.
    #
    # El valor puede ser None porque NAME es una parte opcional
    # de la gramática de TecNet Finder.
    nombre: str | None = None

    # Guarda la línea donde comenzó la instrucción.
    #
    # Este dato será útil posteriormente para relacionar resultados,
    # errores y elementos de la interfaz con el código fuente.
    linea_origen: int = 1


# Convierte ResultadoSintactico en una estructura de datos.
#
# Esta clase almacena todo lo que produce el analizador sintáctico
# después de procesar la secuencia de tokens recibida del lexer.
@dataclass
class ResultadoSintactico:

    # Guarda únicamente los bloques que lograron cumplir
    # correctamente las reglas sintácticas.
    bloques: list[BloqueRed] = field(default_factory=list)

    # Guarda todos los diagnósticos sintácticos encontrados.
    diagnosticos: list[Diagnostico] = field(default_factory=list)

    # Permite consultar fácilmente si ocurrió al menos un error
    # sintáctico durante el análisis.
    @property
    def tiene_errores(self) -> bool:

        # Devuelve True si existe al menos un diagnóstico cuya
        # severidad esté marcada como error.
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )