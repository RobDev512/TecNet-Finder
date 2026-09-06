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
# Actualmente contiene los modelos utilizados por los
# analizadores léxico y sintáctico.
# ============================================================

from dataclasses import dataclass, field  # Importa herramientas para crear clases de datos y valores predeterminados.
from Motor.diagnosticos import Diagnostico  # Importa la estructura utilizada para representar errores y advertencias.


@dataclass(frozen=True)  # Convierte Token en una clase de datos inmutable.
class Token:  # Representa un elemento reconocido por el analizador léxico.
    tipo: str       # Guarda el tipo del token, por ejemplo IP, MASK o NUMBER.
    valor: str      # Guarda exactamente el texto reconocido en el código fuente.
    linea: int      # Guarda la línea donde comienza el token.
    columna: int    # Guarda la columna donde comienza el token.


@dataclass  # Convierte ResultadoLexico en una clase destinada a almacenar resultados.
class ResultadoLexico:  # Agrupa los tokens y diagnósticos producidos por el analizador léxico.
    tokens: list[Token] = field(default_factory=list)  # Guarda los tokens reconocidos correctamente.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Guarda los errores o advertencias léxicas.

    @property  # Permite consultar el método como si fuera un atributo.
    def tiene_errores(self) -> bool:  # Indica si existe al menos un diagnóstico marcado como error.
        return any(  # Devuelve True si alguna condición del generador resulta verdadera.
            diagnostico.severidad == "error"  # Comprueba si el diagnóstico actual tiene severidad de error.
            for diagnostico in self.diagnosticos  # Recorre todos los diagnósticos léxicos obtenidos.
        )


@dataclass  # Convierte BloqueRed en una clase de datos organizada.
class BloqueRed:  # Representa una instrucción que cumplió correctamente la estructura sintáctica.
    direccion_ip: str  # Guarda la dirección IPv4 escrita después de IP.
    mascara_subred: str  # Guarda la máscara CIDR escrita después de MASK.
    cantidades_hosts: list[int] = field(default_factory=list)  # Guarda las cantidades escritas después de HOSTS.
    nombre: str | None = None  # Guarda el identificador opcional escrito después de NAME.
    linea_origen: int = 1  # Guarda la línea donde comenzó la instrucción.


@dataclass  # Convierte ResultadoSintactico en una clase destinada a almacenar resultados.
class ResultadoSintactico:  # Agrupa los bloques válidos y diagnósticos producidos por el parser.
    bloques: list[BloqueRed] = field(default_factory=list)  # Guarda únicamente las instrucciones sintácticamente válidas.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Guarda los errores o advertencias sintácticas.

    @property  # Permite consultar el método como si fuera un atributo.
    def tiene_errores(self) -> bool:  # Indica si existe al menos un diagnóstico sintáctico marcado como error.
        return any(  # Devuelve True si alguna condición del generador resulta verdadera.
            diagnostico.severidad == "error"  # Comprueba la severidad del diagnóstico actual.
            for diagnostico in self.diagnosticos  # Recorre todos los diagnósticos sintácticos obtenidos.
        )
