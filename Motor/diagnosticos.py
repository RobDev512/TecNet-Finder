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
# Durante Lenguajes y Autómatas II, el estado de cada diagnóstico
# semántico se actualiza únicamente cuando su validación ya está
# implementada, integrada y comprobada mediante pruebas.
# ============================================================

from dataclasses import dataclass  # Importa el decorador utilizado para crear clases de datos.


ESTADO_DIAGNOSTICO_DISPONIBLE = "disponible"  # Identifica diagnósticos que la versión actual ya puede producir y evaluar.
ESTADO_DIAGNOSTICO_PENDIENTE = "pendiente"  # Identifica diagnósticos reservados para una fase posterior.


CATALOGO_DIAGNOSTICOS = {  # Centraliza la información general de todos los códigos reconocidos por TecNet Finder.
    "LEX-001": {  # Registra el primer diagnóstico léxico heredado de la base de LyA I.
        "categoria": "Léxico",  # Clasifica el diagnóstico dentro de la fase léxica.
        "nombre": "Identificador fuera de lugar",  # Proporciona un nombre breve para mostrarlo dentro del catálogo.
        "descripcion": "Apareció un identificador en una posición no permitida.",  # Explica de forma general qué situación representa el código.
        "solucion": "Revisa si escribiste mal una palabra reservada. Por ejemplo, usa MASK en lugar de MAS. Si era un nombre de red, debe escribirse después de NAME.",  # Conserva la recomendación oficial asociada con el error.
        "severidad": "error",  # Determina que este diagnóstico invalida la entrada relacionada.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el lexer actual ya puede producir este código.
        "etapa": "Base LyAI",  # Registra la etapa académica donde se incorporó originalmente.
    },
    "LEX-002": {  # Registra el diagnóstico utilizado para símbolos o fragmentos ajenos al lenguaje.
        "categoria": "Léxico",  # Clasifica el diagnóstico dentro de la fase léxica.
        "nombre": "Símbolo o fragmento no reconocido",  # Proporciona el título visible del diagnóstico.
        "descripcion": "Apareció un carácter o fragmento que no pertenece al lenguaje.",  # Describe el tipo de lexema rechazado.
        "solucion": "Elimina el símbolo no permitido o reemplázalo por tokens válidos como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR.",  # Indica los elementos aceptados por el lenguaje.
        "severidad": "error",  # Determina que el fragmento desconocido representa un error formal.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el diagnóstico ya forma parte del comportamiento actual.
        "etapa": "Base LyAI",  # Conserva su procedencia académica original.
    },
    "LEX-003": {  # Registra el diagnóstico específico para palabras reservadas con capitalización incorrecta.
        "categoria": "Léxico",  # Clasifica el diagnóstico dentro de la fase léxica.
        "nombre": "Palabra reservada con mayúsculas incorrectas",  # Resume el problema detectado.
        "descripcion": "Una palabra reservada fue escrita con una combinación de mayúsculas y minúsculas distinta de la definida por el lenguaje.",  # Explica que el lexema existe pero su escritura no coincide con la forma oficial.
        "solucion": "Escribe las palabras reservadas exactamente como IP, MASK, HOSTS o NAME. Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50.",  # Muestra las formas correctas admitidas por el DSL.
        "severidad": "error",  # Determina que una palabra reservada mal escrita no puede aceptarse formalmente.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el lexer reforzado ya produce este diagnóstico.
        "etapa": "Refuerzo LyAII",  # Identifica que se agregó durante la preparación previa a U1.
    },
    "LEX-004": {  # Registra el diagnóstico utilizado cuando un elemento numérico queda unido directamente con texto.
        "categoria": "Léxico",  # Clasifica el problema dentro del análisis léxico.
        "nombre": "Elemento numérico unido a texto",  # Resume la construcción léxica incorrecta.
        "descripcion": "Un número o una máscara CIDR apareció unido directamente a letras sin un separador válido entre ambos elementos.",  # Explica por qué el fragmento no debe separarse artificialmente en tokens independientes.
        "solucion": "Separa los elementos con un espacio. Ejemplo: HOSTS 50 NAME Oficina o MASK /24 HOSTS 50.",  # Proporciona dos formas correctas de separación.
        "severidad": "error",  # Indica que la construcción impide reconocer correctamente los lexemas.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Marca el código como utilizable por la versión actual.
        "etapa": "Refuerzo LyAII",  # Registra que se añadió durante el refuerzo previo a U1.
    },
    "SIN-001": {  # Registra el diagnóstico para direcciones IPv4 incompletas o mal formadas.
        "categoria": "Sintáctico",  # Clasifica el diagnóstico dentro del análisis sintáctico.
        "nombre": "Dirección IP incompleta o mal formada",  # Define el nombre visible del problema.
        "descripcion": "Después de IP se esperaba una dirección IP completa.",  # Describe la expectativa gramatical incumplida.
        "solucion": "Escribe una dirección IPv4 completa. Ejemplo: 192.168.1.0.",  # Proporciona un ejemplo de la forma esperada.
        "severidad": "error",  # Determina que la instrucción afectada no puede aceptarse.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el parser actual ya detecta este caso.
        "etapa": "Base LyAI",  # Conserva su procedencia de la primera materia.
    },
    "SIN-002": {  # Registra el diagnóstico utilizado cuando falta la palabra reservada MASK.
        "categoria": "Sintáctico",  # Clasifica el código dentro del parser.
        "nombre": "Falta la palabra reservada MASK",  # Resume la ausencia detectada.
        "descripcion": "Después de la dirección IP se esperaba la palabra MASK.",  # Explica la posición gramatical de MASK.
        "solucion": "Coloca MASK después de la IP. Si escribiste MAS u otra variante, cámbiala por MASK. Ejemplo: IP 192.168.1.0 MASK /24.",  # Indica cómo reconstruir correctamente esa parte de la instrucción.
        "severidad": "error",  # Determina que la instrucción queda sintácticamente inválida.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que este error ya puede producirse.
        "etapa": "Base LyAI",  # Conserva la etapa académica original.
    },
    "SIN-003": {  # Registra el diagnóstico para una máscara CIDR ausente o sintácticamente incompleta.
        "categoria": "Sintáctico",  # Clasifica el diagnóstico dentro del parser.
        "nombre": "Máscara CIDR inválida o incompleta",  # Proporciona el título mostrado al usuario.
        "descripcion": "Después de MASK se esperaba una máscara con diagonal.",  # Explica la construcción esperada.
        "solucion": "Escribe la máscara en formato CIDR. Ejemplo: /24.",  # Muestra la notación requerida por el lenguaje.
        "severidad": "error",  # Indica que no puede construirse un bloque sintáctico válido.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el parser ya evalúa este caso.
        "etapa": "Base LyAI",  # Registra su procedencia de LyA I.
    },
    "SIN-004": {  # Registra la ausencia de la primera cantidad requerida después de HOSTS.
        "categoria": "Sintáctico",  # Clasifica el problema dentro del análisis sintáctico.
        "nombre": "Falta cantidad de hosts",  # Resume la construcción incompleta.
        "descripcion": "Después de HOSTS se esperaba al menos un número.",  # Explica el elemento obligatorio que falta.
        "solucion": "Escribe al menos una cantidad de hosts. Ejemplo: HOSTS 50.",  # Proporciona una estructura mínima válida.
        "severidad": "error",  # Determina que la instrucción no puede aceptarse.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el diagnóstico está implementado.
        "etapa": "Base LyAI",  # Conserva su procedencia académica.
    },
    "SIN-005": {  # Registra errores dentro de la lista de cantidades separadas por comas.
        "categoria": "Sintáctico",  # Clasifica el código dentro del parser.
        "nombre": "Lista de hosts mal formada",  # Resume el problema de separación.
        "descripcion": "Después de una coma se esperaba otro número.",  # Explica la producción de la gramática que quedó incompleta.
        "solucion": "Corrige la lista de hosts. Ejemplo correcto: HOSTS 100,200.",  # Muestra una lista válida.
        "severidad": "error",  # Determina que el bloque afectado es sintácticamente inválido.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el caso ya puede ser detectado.
        "etapa": "Base LyAI",  # Conserva la etapa donde se incorporó.
    },
    "SIN-006": {  # Registra el uso de NAME sin el identificador requerido.
        "categoria": "Sintáctico",  # Clasifica el diagnóstico como sintáctico.
        "nombre": "Nombre de red incompleto",  # Resume la construcción opcional incompleta.
        "descripcion": "Después de NAME se esperaba un identificador.",  # Explica qué token debe aparecer después de NAME.
        "solucion": "Escribe un nombre después de NAME o elimina NAME si no usarás nombre.",  # Ofrece las dos formas válidas de resolver la construcción.
        "severidad": "error",  # Determina que NAME incompleto invalida el bloque.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el parser actual evalúa el caso.
        "etapa": "Base LyAI",  # Conserva la etapa académica original.
    },
    "SIN-007": {  # Registra una instrucción completa repetida exactamente.
        "categoria": "Sintáctico",  # Clasifica el diagnóstico dentro del análisis sintáctico.
        "nombre": "Instrucción duplicada",  # Resume el problema de repetición.
        "descripcion": "Se declaró una instrucción exactamente igual a otra anterior.",  # Explica la condición necesaria para producir el código.
        "solucion": "Elimina la instrucción repetida o cambia IP, máscara, hosts o nombre.",  # Indica cómo diferenciar o retirar el bloque.
        "severidad": "error",  # Conserva el duplicado como error de la base actual.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el parser detecta duplicados.
        "etapa": "Base LyAI",  # Conserva su origen académico.
    },
    "SIN-008": {  # Registra cualquier orden de tokens que no coincida con la gramática y no posea un código más específico.
        "categoria": "Sintáctico",  # Clasifica el problema dentro del parser.
        "nombre": "Orden incorrecto de tokens",  # Resume el incumplimiento de la estructura general.
        "descripcion": "Los tokens existen, pero no aparecen en el orden esperado.",  # Explica que el problema pertenece a la organización y no al reconocimiento léxico.
        "solucion": "Revisa que la instrucción siga esta estructura: IP <IP_ADDRESS> MASK <SUBNET_MASK> HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>].",  # Muestra la gramática práctica de una instrucción.
        "severidad": "error",  # Determina que un orden incorrecto impide construir un bloque válido.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el diagnóstico se encuentra implementado.
        "etapa": "Base LyAI",  # Conserva su procedencia académica.
    },
    "SEM-001": {  # Registra la validación semántica de máscaras fuera del rango permitido por TecNet Finder.
        "categoria": "Semántico",  # Clasifica el diagnóstico dentro del análisis semántico.
        "nombre": "Máscara fuera de rango",  # Resume la condición comprobada durante U1.
        "descripcion": "La máscara CIDR existe sintácticamente, pero está fuera del rango permitido.",  # Diferencia explícitamente validez sintáctica y validez semántica.
        "solucion": "Usa una máscara entre /8 y /30. Ejemplo: MASK /24.",  # Indica el rango admitido por la validación semántica.
        "severidad": "error",  # Determina que una máscara fuera del rango impide continuar con el bloque.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que SEM-001 ya está implementado e integrado en el flujo principal.
        "etapa": "U1",  # Registra que la validación pertenece a la primera unidad de LyAII.
    },
    "SEM-002": {  # Registra la comprobación de una IP que no representa la dirección de su red base.
        "categoria": "Semántico",  # Clasifica la comprobación dentro del análisis semántico.
        "nombre": "IP base no es dirección de red",  # Resume la relación incorrecta entre la IP y su máscara.
        "descripcion": "La IP indicada no corresponde a la dirección de red para la máscara dada.",  # Explica la condición evaluada por la regla.
        "solucion": "Usa la dirección de red correcta para esa máscara. Por ejemplo, para 192.168.1.5/24 la red correcta sería 192.168.1.0.",  # Proporciona un ejemplo de corrección.
        "severidad": "error",  # Determina que una IP base incorrecta invalida semánticamente la instrucción.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que SEM-002 ya está implementado e integrado en el flujo.
        "etapa": "U1",  # Registra la unidad responsable de la validación.
    },
    "SEM-003": {  # Registra la comprobación semántica de cantidades de hosts no positivas.
        "categoria": "Semántico",  # Clasifica el código dentro de la fase semántica.
        "nombre": "Cantidad de hosts no válida",  # Resume la regla asociada con NUMBER dentro de HOSTS.
        "descripcion": "Una cantidad de hosts debe ser mayor que cero.",  # Define la condición semántica evaluada.
        "solucion": "Cambia la cantidad de hosts por un número positivo. Ejemplo: HOSTS 50.",  # Indica una corrección válida.
        "severidad": "error",  # Establece que una cantidad no positiva impide continuar con el bloque.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que SEM-003 ya está implementado e integrado en el flujo.
        "etapa": "U1",  # Asigna la comprobación a la primera unidad de LyAII.
    },
    "SEM-004": {  # Reserva la comprobación de capacidad total de la red base.
        "categoria": "Semántico",  # Clasifica la regla dentro del análisis semántico.
        "nombre": "Hosts no caben en la red base",  # Resume el exceso global de capacidad.
        "descripcion": "La suma de subredes solicitadas excede la capacidad de la red base.",  # Explica la condición que deberá calcularse.
        "solucion": "Usa una máscara base más grande, por ejemplo /23 en lugar de /24, o reduce los hosts solicitados.",  # Sugiere aumentar capacidad o reducir requerimientos.
        "severidad": "error",  # Determina que el exceso de capacidad invalidará el bloque.
        "estado": ESTADO_DIAGNOSTICO_PENDIENTE,  # Mantiene la validación pendiente hasta implementarla.
        "etapa": "U1",  # Registra la unidad correspondiente.
    },
    "SEM-005": {  # Reserva la comprobación de una solicitud individual demasiado grande.
        "categoria": "Semántico",  # Clasifica el diagnóstico en la fase semántica.
        "nombre": "Subred individual demasiado grande",  # Resume el exceso de una sola cantidad de hosts.
        "descripcion": "Una cantidad de hosts necesita más direcciones de las disponibles en la red base.",  # Explica la diferencia respecto del exceso total.
        "solucion": "Reduce la cantidad de hosts o usa una red base con más direcciones disponibles.",  # Indica las alternativas de corrección.
        "severidad": "error",  # Determina que la solicitud no podrá procesarse normalmente.
        "estado": ESTADO_DIAGNOSTICO_PENDIENTE,  # Conserva la comprobación fuera del comportamiento disponible.
        "etapa": "U1",  # Asocia el código con análisis semántico.
    },
    "SEM-006": {  # Reserva la comprobación de redes base que ocupan direcciones comunes.
        "categoria": "Semántico",  # Clasifica el código dentro de U1.
        "nombre": "Redes base traslapadas",  # Resume el conflicto entre instrucciones distintas.
        "descripcion": "Dos instrucciones usan redes base que se cruzan entre sí.",  # Explica el problema de solapamiento.
        "solucion": "Cambia la IP base o la máscara para que las redes no se traslapen.",  # Indica cómo separar los espacios de direcciones.
        "severidad": "error",  # Determina que el conflicto será bloqueante.
        "estado": ESTADO_DIAGNOSTICO_PENDIENTE,  # Mantiene la comprobación pendiente hasta su implementación.
        "etapa": "U1",  # Registra la unidad donde será implementada.
    },
    "ADV-001": {  # Registra la advertencia utilizada cuando algunos bloques fallan y otros pueden continuar.
        "categoria": "Advertencia",  # Clasifica el diagnóstico como recomendación no bloqueante.
        "nombre": "Procesamiento parcial",  # Resume que solamente una parte de la entrada podrá continuar.
        "descripcion": "Hay errores, pero también existen bloques válidos que pueden procesarse.",  # Explica la condición que activa la advertencia.
        "solucion": "Revisa las líneas con error. El sistema continuará únicamente con bloques válidos.",  # Informa el comportamiento que seguirá TecNet Finder.
        "severidad": "advertencia",  # Evita tratar este diagnóstico como un error formal adicional.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la advertencia está implementada.
        "etapa": "Base LyAI",  # Conserva su procedencia académica.
    },
    "ADV-002": {  # Registra la recomendación de separar palabras reservadas de los valores siguientes.
        "categoria": "Advertencia",  # Clasifica el diagnóstico como advertencia.
        "nombre": "Palabra reservada pegada al valor",  # Resume la condición de legibilidad detectada.
        "descripcion": "Una palabra reservada aparece pegada al valor siguiente.",  # Explica la escritura válida pero poco recomendable.
        "solucion": "Se recomienda separar con espacios. Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50.",  # Muestra el formato más legible.
        "severidad": "advertencia",  # Permite continuar el procesamiento de la instrucción.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que la advertencia está activa.
        "etapa": "Base LyAI",  # Conserva su procedencia original.
    },
    "ADV-003": {  # Registra la reutilización de un mismo nombre entre instrucciones distintas.
        "categoria": "Advertencia",  # Clasifica el diagnóstico como no bloqueante.
        "nombre": "Nombre de red repetido",  # Resume la posible ambigüedad de nombres.
        "descripcion": "Dos o más instrucciones usan el mismo nombre de red.",  # Explica la condición detectada.
        "solucion": "Usa nombres distintos para evitar confusión en la tabla VLSM, en el Excel o en la interpretación de resultados.",  # Indica por qué conviene utilizar identificadores diferentes.
        "severidad": "advertencia",  # Mantiene válidas las instrucciones aunque compartan nombre.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que esta recomendación ya está implementada.
        "etapa": "Base LyAI",  # Conserva la etapa donde apareció originalmente.
    },
    "ADV-004": {  # Registra cantidades de hosts repetidas dentro de una misma lista.
        "categoria": "Advertencia",  # Clasifica el código como recomendación.
        "nombre": "Hosts repetidos",  # Resume la condición observada.
        "descripcion": "La lista de hosts contiene cantidades repetidas dentro de la misma instrucción.",  # Explica que la repetición es válida pero merece revisión.
        "solucion": "Revisa si los hosts repetidos fueron intencionales. Si no, elimina o corrige los valores duplicados.",  # Sugiere verificar la intención del usuario.
        "severidad": "advertencia",  # Permite continuar normalmente con el cálculo.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el comportamiento está disponible.
        "etapa": "Base LyAI",  # Conserva la procedencia de LyA I.
    },
    "ADV-005": {  # Reserva una futura advertencia basada en la capacidad calculada de la red.
        "categoria": "Advertencia",  # Clasifica el código como recomendación semántica.
        "nombre": "Red base sobredimensionada",  # Resume el desperdicio considerable de direcciones.
        "descripcion": "La red base tiene mucha más capacidad de la que realmente se utiliza.",  # Explica la condición futura.
        "solucion": "Considera usar una máscara base más pequeña si deseas optimizar mejor el espacio de direcciones.",  # Sugiere ajustar el tamaño de la red.
        "severidad": "advertencia",  # Mantiene la condición como recomendación y no como error.
        "estado": ESTADO_DIAGNOSTICO_PENDIENTE,  # Evita ejecutarla antes de tener disponible la información semántica necesaria.
        "etapa": "U1",  # Registra la unidad donde podrá evaluarse correctamente.
    },
    "ADV-006": {  # Registra identificadores considerados demasiado genéricos.
        "categoria": "Advertencia",  # Clasifica la observación como no bloqueante.
        "nombre": "Nombre de red genérico",  # Resume el posible problema de claridad.
        "descripcion": "El nombre de la red es demasiado genérico y puede causar confusión.",  # Explica la razón de la recomendación.
        "solucion": "Usa un nombre más descriptivo, por ejemplo OficinaCentral, LaboratorioRedes o SucursalTepic.",  # Proporciona ejemplos de identificadores más claros.
        "severidad": "advertencia",  # Permite conservar el nombre aunque sea genérico.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la recomendación ya funciona.
        "etapa": "Base LyAI",  # Conserva su procedencia original.
    },
    "ADV-007": {  # Registra una instrucción válida donde el componente opcional NAME no fue utilizado.
        "categoria": "Advertencia",  # Clasifica el código como recomendación.
        "nombre": "Nombre de red no especificado",  # Resume la ausencia del identificador opcional.
        "descripcion": "La instrucción no incluye un nombre para identificar la red.",  # Explica la condición que produce la advertencia.
        "solucion": "Agrega NAME seguido de un identificador para facilitar la lectura de resultados y reportes.",  # Recomienda aprovechar el componente opcional.
        "severidad": "advertencia",  # Mantiene completamente válida la instrucción sin NAME.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que esta recomendación se encuentra activa.
        "etapa": "Base LyAI",  # Conserva su procedencia académica.
    },
    "ADV-008": {  # Registra una lista HOSTS válida que no fue escrita en el orden descendente recomendado para VLSM.
        "categoria": "Advertencia",  # Clasifica la observación como una recomendación no bloqueante.
        "nombre": "Hosts fuera del orden recomendado",  # Proporciona el título visible de la nueva advertencia.
        "descripcion": "Las cantidades de HOSTS no están escritas de mayor a menor, aunque TecNet Finder puede ordenarlas internamente para realizar el cálculo VLSM.",  # Explica por qué la entrada sigue siendo válida.
        "solucion": "Se recomienda escribir las cantidades de mayor a menor para que la entrada coincida con el orden utilizado por VLSM. Ejemplo: HOSTS 100,50,20.",  # Proporciona una lista ordenada correctamente.
        "severidad": "advertencia",  # Permite continuar con la compilación sin alterar la validez de la instrucción.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Marca la nueva recomendación como disponible inmediatamente.
        "etapa": "Refuerzo LyAII",  # Registra que fue incorporada antes del inicio formal de U1.
    },
    "GEN-001": {  # Conserva el diagnóstico técnico de respaldo utilizado cuando un fallo no posee clasificación específica.
        "categoria": "General",  # Clasifica el diagnóstico fuera de las fases formales.
        "nombre": "Error no clasificado",  # Proporciona un nombre general para situaciones excepcionales.
        "descripcion": "El error fue detectado, pero no coincide con una categoría específica.",  # Explica el uso del respaldo.
        "solucion": "Revisa la estructura general de la instrucción.",  # Proporciona una recomendación mínima cuando no existe una solución especializada.
        "severidad": "error",  # Mantiene el fallo técnico como bloqueante.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Permite utilizar el respaldo en la versión actual.
        "etapa": "Base LyAI",  # Conserva su procedencia original.
    },
}


@dataclass(frozen=True)  # Impide modificar accidentalmente un diagnóstico después de haber sido creado.
class Diagnostico:  # Representa un error o advertencia detectado por TecNet Finder.
    codigo: str  # Guarda el código único del diagnóstico, por ejemplo LEX-001 o ADV-008.
    categoria: str  # Guarda la fase o categoría donde ocurrió el problema.
    severidad: str  # Indica si se trata de un error o una advertencia.
    mensaje: str  # Guarda el mensaje específico que se mostrará al usuario.
    linea: int | None = None  # Guarda la línea del problema cuando existe una posición concreta.
    columna: int | None = None  # Guarda la columna donde comienza el fragmento problemático.
    longitud: int = 1  # Indica cuántos caracteres deben relacionarse visualmente con el diagnóstico.
    fragmento: str = ""  # Guarda el texto exacto relacionado con el problema.
    solucion: str = ""  # Guarda la recomendación oficial asociada con el diagnóstico.


def obtener_informacion_diagnostico(codigo: str) -> dict:  # Obtiene la ficha registrada para un código y utiliza GEN-001 como respaldo.
    return CATALOGO_DIAGNOSTICOS.get(codigo, CATALOGO_DIAGNOSTICOS["GEN-001"])  # Devuelve la ficha concreta o el diagnóstico general cuando el código no existe.


def obtener_catalogo_diagnosticos() -> list[tuple[str, dict]]:  # Devuelve el catálogo completo conservando el orden declarado.
    return list(CATALOGO_DIAGNOSTICOS.items())  # Convierte el diccionario en pares código-información para facilitar su consumo en la interfaz.


def codigo_diagnostico_disponible(codigo: str) -> bool:  # Indica si un código ya pertenece al comportamiento evaluable de la versión actual.
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)  # Busca exclusivamente la ficha solicitada sin aplicar el respaldo general.
    return bool(informacion and informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE)  # Devuelve verdadero únicamente cuando el código existe y está marcado como disponible.


def codigo_diagnostico_es_error(codigo: str) -> bool:  # Indica si el catálogo clasifica el código recibido como error.
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)  # Recupera exclusivamente la ficha registrada para el código.
    return bool(informacion and informacion["severidad"] == "error")  # Devuelve verdadero únicamente para diagnósticos existentes con severidad de error.


def obtener_codigos_diagnosticos_disponibles() -> list[str]:  # Reúne todos los códigos que la versión actual puede producir.
    return [codigo for codigo, informacion in CATALOGO_DIAGNOSTICOS.items() if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE]  # Filtra el catálogo utilizando su estado centralizado.


def obtener_codigos_diagnosticos_pendientes() -> list[str]:  # Reúne los códigos reservados para fases posteriores.
    return [codigo for codigo, informacion in CATALOGO_DIAGNOSTICOS.items() if informacion["estado"] == ESTADO_DIAGNOSTICO_PENDIENTE]  # Filtra únicamente las fichas todavía pendientes.


def texto_estado_diagnostico(codigo: str) -> str:  # Convierte el estado interno de un diagnóstico en una etiqueta legible para la interfaz.
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)  # Busca la ficha concreta solicitada.

    if informacion is None:  # Comprueba si el código no forma parte del catálogo.
        return "No registrado"  # Informa claramente que no existe una ficha asociada.

    if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE:  # Comprueba si el diagnóstico se encuentra habilitado actualmente.
        return "Disponible"  # Devuelve la etiqueta utilizada por la tabla Catálogo.

    etapa = informacion.get("etapa", "").strip()  # Recupera la unidad o etapa prevista cuando el diagnóstico todavía está pendiente.
    return f"Pendiente {etapa}" if etapa else "Pendiente"  # Incluye la unidad futura cuando esa información se encuentra disponible.


def crear_diagnostico(
    codigo: str,  # Recibe el identificador único que determina la ficha general del diagnóstico.
    mensaje: str,  # Recibe el mensaje específico correspondiente con la aparición actual.
    linea: int | None = None,  # Recibe opcionalmente la línea exacta relacionada con el problema.
    columna: int | None = None,  # Recibe opcionalmente la columna inicial del fragmento relacionado.
    longitud: int = 1,  # Recibe cuántos caracteres deben asociarse visualmente con el diagnóstico.
    fragmento: str = "",  # Recibe el texto concreto que originó el diagnóstico.
    severidad: str | None = None,  # Permite reemplazar excepcionalmente la severidad registrada en el catálogo.
) -> Diagnostico:  # Construye un diagnóstico estructurado utilizando el catálogo como fuente central.
    informacion = obtener_informacion_diagnostico(codigo)  # Recupera categoría, solución y severidad predeterminada.
    severidad_final = severidad or informacion["severidad"]  # Utiliza una severidad explícita o conserva la definida por la ficha oficial.

    return Diagnostico(
        codigo=codigo,  # Conserva el identificador concreto solicitado por la fase que detectó el problema.
        categoria=informacion["categoria"],  # Obtiene automáticamente la categoría registrada en el catálogo.
        severidad=severidad_final,  # Guarda la severidad definitiva que utilizarán Motor e interfaz.
        mensaje=mensaje,  # Conserva la explicación específica correspondiente con esta aparición.
        linea=linea,  # Guarda la línea exacta cuando se proporcionó una ubicación.
        columna=columna,  # Guarda la columna inicial cuando existe una posición conocida.
        longitud=max(longitud, 1),  # Garantiza una longitud mínima de un carácter para navegación y resaltado.
        fragmento=fragmento,  # Conserva el texto exacto relacionado con el diagnóstico.
        solucion=informacion["solucion"],  # Obtiene siempre la solución oficial desde la fuente central.
    )