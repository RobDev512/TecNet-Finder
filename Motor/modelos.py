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
# ============================================================

from dataclasses import dataclass, field  # Importa herramientas para crear clases de datos y valores predeterminados.

from Motor.diagnosticos import Diagnostico  # Importa la estructura utilizada para representar errores y advertencias.


@dataclass(frozen=True)
class Token:  # Representa un elemento reconocido por el analizador léxico.
    tipo: str  # Guarda el tipo del token, por ejemplo IP, MASK o NUMBER.
    valor: str  # Guarda exactamente el texto reconocido en el código fuente.
    linea: int  # Guarda la línea donde comienza el token.
    columna: int  # Guarda la columna donde comienza el token.


@dataclass
class ResultadoLexico:  # Agrupa los tokens y diagnósticos producidos por el analizador léxico.
    tokens: list[Token] = field(default_factory=list)  # Guarda los tokens reconocidos correctamente.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Guarda los errores o advertencias léxicas.

    @property
    def tiene_errores(self) -> bool:  # Indica si existe al menos un diagnóstico marcado como error.
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )


@dataclass
class BloqueRed:  # Representa una instrucción que cumplió correctamente la estructura sintáctica.
    direccion_ip: str  # Guarda la dirección IPv4 escrita después de IP.
    mascara_subred: str  # Guarda la máscara CIDR escrita después de MASK.
    cantidades_hosts: list[int] = field(default_factory=list)  # Guarda las cantidades escritas después de HOSTS.
    nombre: str | None = None  # Guarda el identificador opcional escrito después de NAME.
    linea_origen: int = 1  # Guarda la línea donde comenzó la instrucción.


@dataclass
class NodoSintactico:  # Representa un nodo del árbol sintáctico generado para una instrucción válida.
    etiqueta: str  # Guarda el nombre visible del nodo, por ejemplo BloqueRed, IP o HOSTS_LIST.
    valor: str | None = None  # Guarda un valor concreto cuando el nodo representa contenido terminal.
    hijos: list["NodoSintactico"] = field(default_factory=list)  # Guarda los nodos descendientes conectados al nodo actual.


@dataclass
class ResultadoSintactico:  # Agrupa los bloques válidos y diagnósticos producidos por el parser.
    bloques: list[BloqueRed] = field(default_factory=list)  # Guarda únicamente las instrucciones sintácticamente válidas.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Guarda los errores o advertencias sintácticas.
    arboles: list[NodoSintactico] = field(default_factory=list)  # Guarda un árbol sintáctico por cada bloque válido reconocido.
    producciones_usadas: str = ""  # Guarda la gramática base y las producciones aplicadas a la entrada válida.
    derivacion: str = ""  # Guarda la derivación generada para el programa y para cada bloque válido.
    arbol_textual: str = ""  # Guarda una representación del árbol usando ramas de texto para facilitar su lectura.

    @property
    def tiene_errores(self) -> bool:  # Indica si existe al menos un diagnóstico sintáctico marcado como error.
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )


@dataclass
class ResultadoSemantico:  # Agrupa los bloques aceptados y los diagnósticos producidos por el análisis semántico.
    bloques_validos: list[BloqueRed] = field(default_factory=list)  # Guarda únicamente las instrucciones que cumplen las reglas semánticas.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Guarda los errores detectados durante la validación semántica.

    @property
    def tiene_errores(self) -> bool:  # Indica si existe al menos un diagnóstico semántico marcado como error.
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )


@dataclass
class SubredVLSM:  # Representa una subred calculada a partir de una solicitud de hosts.
    hosts_solicitados: int  # Guarda la cantidad de hosts pedida para esta subred.
    hosts_disponibles: int  # Guarda la cantidad real de hosts utilizables dentro del bloque asignado.
    direccion_de_red: str  # Guarda la dirección de red calculada para la subred.
    nueva_mascara: str  # Guarda el nuevo prefijo CIDR calculado según los hosts solicitados.
    mascara_decimal: str  # Guarda la máscara equivalente en notación decimal punteada.
    primera_ip_utilizable: str  # Guarda la primera dirección que puede asignarse a un host.
    ultima_ip_utilizable: str  # Guarda la última IP que puede asignarse a un host.
    direccion_de_broadcast: str  # Guarda la dirección de broadcast calculada.
    ip_base: str  # Conserva la dirección IP base recibida para identificar el bloque original.
    nombre_red: str  # Conserva el nombre de la red o utiliza la IP base cuando no se indicó NAME.


@dataclass
class ResultadoCompilacion:  # Agrupa en un solo objeto todo lo producido por el flujo actual de TecNet Finder.
    resultado_lexico: ResultadoLexico  # Guarda el resultado completo producido por el analizador léxico.
    resultado_sintactico: ResultadoSintactico  # Guarda el resultado completo producido por el analizador sintáctico.
    resultado_semantico: ResultadoSemantico | None = None  # Guarda el resultado semántico cuando esta fase ya fue ejecutada.
    subredes_vlsm: list[SubredVLSM] = field(default_factory=list)  # Guarda todas las subredes generadas a partir de los bloques válidos.
    advertencias: list[Diagnostico] = field(default_factory=list)  # Guarda recomendaciones no bloqueantes producidas fuera de las fases formales.
    diagnosticos_generales: list[Diagnostico] = field(default_factory=list)  # Guarda errores técnicos controlados que no pertenecen todavía a una fase formal específica.

    @property
    def diagnosticos(self) -> list[Diagnostico]:  # Reúne en una sola colección todos los diagnósticos disponibles.
        diagnosticos_semanticos = (
            self.resultado_semantico.diagnosticos
            if self.resultado_semantico is not None
            else []
        )  # Utiliza los diagnósticos semánticos únicamente cuando la nueva fase ya fue ejecutada.

        return [
            *self.resultado_lexico.diagnosticos,
            *self.resultado_sintactico.diagnosticos,
            *diagnosticos_semanticos,
            *self.diagnosticos_generales,
            *self.advertencias,
        ]

    @property
    def bloques_validos(self) -> list[BloqueRed]:  # Devuelve los bloques que pueden continuar hacia las siguientes etapas del compilador.
        if self.resultado_semantico is not None:
            return self.resultado_semantico.bloques_validos  # Prioriza los bloques aprobados por la fase semántica cuando esta ya fue ejecutada.

        return self.resultado_sintactico.bloques  # Conserva temporalmente el comportamiento anterior mientras el semántico aún no participe en el flujo.

    @property
    def tiene_errores(self) -> bool:  # Indica si al menos un diagnóstico combinado posee severidad de error.
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )