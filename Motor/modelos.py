# ============================================================
# Archivo: modelos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las estructuras de datos compartidas
# entre las diferentes partes de TecNet Finder.
#
# Su objetivo es almacenar la información del compilador de
# manera organizada mediante clases de datos, evitando depender
# de listas, tuplas o diccionarios con posiciones difíciles
# de recordar.
#
# Aquí se representan tokens, bloques de red, árboles
# sintácticos, resultados de cada fase, subredes VLSM y el
# resultado general producido por el flujo de compilación.
# ============================================================

from dataclasses import dataclass, field  # Proporciona clases de datos y fábricas seguras para colecciones con valores predeterminados.

from Motor.diagnosticos import Diagnostico  # Permite utilizar la misma estructura de errores y advertencias en los resultados de todas las fases.


@dataclass(frozen=True)  # Mantiene inmutable cada token después de que el analizador léxico lo reconoce.
class Token:  # Representa un elemento individual reconocido dentro del código fuente.
    tipo: str  # Guarda la categoría léxica del elemento, por ejemplo IP, MASK, NUMBER o IDENTIFIER.
    valor: str  # Conserva exactamente el texto que apareció originalmente en el editor.
    linea: int  # Indica la línea donde comienza el token dentro del código fuente.
    columna: int  # Indica la columna donde comienza el token dentro de su línea.


@dataclass  # Facilita almacenar conjuntamente la salida completa producida por el análisis léxico.
class ResultadoLexico:  # Agrupa los tokens reconocidos y los diagnósticos generados por el lexer.
    tokens: list[Token] = field(default_factory=list)  # Conserva en orden todos los tokens que pudieron reconocerse correctamente.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Conserva todos los problemas encontrados durante esta fase.

    @property  # Permite consultar el estado como un atributo calculado sin almacenarlo por separado.
    def tiene_errores(self) -> bool:  # Indica si el lexer produjo al menos un diagnóstico bloqueante.
        return any(diagnostico.severidad == "error" for diagnostico in self.diagnosticos)  # Busca cualquier diagnóstico cuya severidad corresponda con un error.


@dataclass  # Organiza los datos extraídos de una instrucción que superó la estructura gramatical.
class BloqueRed:  # Representa una instrucción de red reconocida correctamente por el analizador sintáctico.
    direccion_ip: str  # Guarda la dirección IPv4 escrita después de la palabra reservada IP.
    mascara_subred: str  # Guarda la máscara CIDR escrita después de la palabra reservada MASK.
    cantidades_hosts: list[int] = field(default_factory=list)  # Conserva todas las cantidades solicitadas después de HOSTS.
    nombre: str | None = None  # Guarda el identificador opcional indicado después de NAME o None cuando no fue utilizado.
    linea_origen: int = 1  # Conserva la línea donde comenzó la instrucción para relacionarla posteriormente con diagnósticos.


@dataclass  # Facilita construir recursivamente la representación estructural generada por el parser.
class NodoSintactico:  # Representa un nodo individual perteneciente a un árbol sintáctico.
    etiqueta: str  # Guarda el nombre visible del nodo, por ejemplo IP, HOSTS_LIST o BloqueRed.
    valor: str | None = None  # Conserva el contenido terminal cuando el nodo representa un valor concreto.
    hijos: list["NodoSintactico"] = field(default_factory=list)  # Mantiene los nodos descendientes conectados directamente con este elemento.


@dataclass  # Agrupa todas las salidas producidas durante la fase sintáctica.
class ResultadoSintactico:  # Conserva bloques, diagnósticos y representaciones de la gramática utilizada.
    bloques: list[BloqueRed] = field(default_factory=list)  # Guarda únicamente las instrucciones que cumplieron correctamente la sintaxis.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Conserva los errores producidos por el parser.
    arboles: list[NodoSintactico] = field(default_factory=list)  # Conserva un árbol sintáctico por cada bloque aceptado.
    producciones_usadas: str = ""  # Guarda el texto de la gramática y las producciones aplicadas durante el análisis.
    derivacion: str = ""  # Guarda la derivación construida para los bloques sintácticamente válidos.
    arbol_textual: str = ""  # Guarda una representación legible de los árboles utilizando ramas de texto.

    @property  # Expone de manera calculada si la fase produjo algún error.
    def tiene_errores(self) -> bool:  # Indica si existe al menos un diagnóstico sintáctico bloqueante.
        return any(diagnostico.severidad == "error" for diagnostico in self.diagnosticos)  # Revisa todas las severidades producidas por el parser.


@dataclass  # Reúne los datos obtenidos después de validar el significado de cada bloque.
class ResultadoSemantico:  # Agrupa los bloques aceptados definitivamente y los diagnósticos semánticos.
    bloques_validos: list[BloqueRed] = field(default_factory=list)  # Guarda únicamente instrucciones que cumplen todas las reglas semánticas actuales.
    diagnosticos: list[Diagnostico] = field(default_factory=list)  # Conserva los errores relacionados con significado, capacidad y coherencia de las redes.

    @property  # Permite consultar el estado semántico sin mantener otra variable sincronizada.
    def tiene_errores(self) -> bool:  # Indica si se produjo al menos un error durante la validación semántica.
        return any(diagnostico.severidad == "error" for diagnostico in self.diagnosticos)  # Examina directamente los diagnósticos almacenados.


@dataclass  # Organiza todos los datos calculados para una subred individual.
class SubredVLSM:  # Representa una subred generada por la calculadora VLSM de TecNet Finder.
    hosts_solicitados: int  # Conserva la cantidad de hosts pedida originalmente para esta subred.
    hosts_disponibles: int  # Guarda la cantidad real de direcciones utilizables que ofrece el bloque asignado.
    direccion_de_red: str  # Guarda la dirección de red calculada para esta subred.
    nueva_mascara: str  # Conserva el prefijo CIDR calculado según la cantidad solicitada.
    mascara_decimal: str  # Guarda la equivalencia del prefijo mediante máscara decimal punteada.
    primera_ip_utilizable: str  # Guarda la primera dirección que puede asignarse a un dispositivo.
    ultima_ip_utilizable: str  # Guarda la última dirección que puede asignarse a un dispositivo.
    direccion_de_broadcast: str  # Conserva la dirección utilizada como broadcast de la subred.
    ip_base: str  # Mantiene la IP original del bloque que produjo esta subred.
    nombre_red: str  # Conserva NAME o utiliza la IP base como identificador cuando el nombre no fue especificado.


@dataclass  # Reúne en una sola estructura todo lo producido durante una compilación.
class ResultadoCompilacion:  # Representa el resultado general que posteriormente utiliza la interfaz.
    resultado_lexico: ResultadoLexico  # Conserva íntegramente la salida obtenida durante el análisis léxico.
    resultado_sintactico: ResultadoSintactico  # Conserva íntegramente la salida obtenida durante el análisis sintáctico.
    resultado_semantico: ResultadoSemantico | None = None  # Conserva la salida semántica cuando esta fase ya fue ejecutada.
    subredes_vlsm: list[SubredVLSM] = field(default_factory=list)  # Guarda todas las subredes producidas a partir de los bloques finalmente válidos.
    advertencias: list[Diagnostico] = field(default_factory=list)  # Conserva recomendaciones no bloqueantes que acompañan al resultado.
    diagnosticos_generales: list[Diagnostico] = field(default_factory=list)  # Conserva fallos técnicos controlados que no pertenecen a una fase formal concreta.

    @property  # Construye dinámicamente una única colección con todos los diagnósticos existentes.
    def diagnosticos(self) -> list[Diagnostico]:  # Devuelve errores y advertencias respetando el orden de las etapas del flujo.
        diagnosticos_semanticos = self.resultado_semantico.diagnosticos if self.resultado_semantico is not None else []  # Incluye la fase semántica únicamente cuando realmente fue ejecutada.
        return [  # Construye una sola colección para facilitar su consumo desde la interfaz y las pruebas.
            *self.resultado_lexico.diagnosticos,  # Coloca primero los problemas encontrados directamente sobre los lexemas.
            *self.resultado_sintactico.diagnosticos,  # Agrega después los errores relacionados con la estructura gramatical.
            *diagnosticos_semanticos,  # Incorpora los problemas relacionados con significado y capacidad de las redes.
            *self.diagnosticos_generales,  # Añade cualquier fallo técnico controlado producido por el flujo.
            *self.advertencias,  # Coloca finalmente las recomendaciones que no afectan la validez formal.
        ]

    @property  # Expone automáticamente los bloques que deben considerarse aceptados por el estado actual del flujo.
    def bloques_validos(self) -> list[BloqueRed]:  # Devuelve los bloques preparados para las siguientes etapas.
        if self.resultado_semantico is not None:  # Comprueba si el análisis semántico ya participó en esta compilación.
            return self.resultado_semantico.bloques_validos  # Utiliza únicamente los bloques que superaron también las reglas semánticas.
        return self.resultado_sintactico.bloques  # Mantiene como respaldo los bloques sintácticos cuando todavía no existe resultado semántico.

    @property  # Permite conocer el estado global sin almacenar manualmente una bandera adicional.
    def tiene_errores(self) -> bool:  # Indica si cualquier fase produjo al menos un diagnóstico bloqueante.
        return any(diagnostico.severidad == "error" for diagnostico in self.diagnosticos)  # Examina la colección combinada de diagnósticos de toda la compilación.