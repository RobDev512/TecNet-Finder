# ============================================================
# Archivo: diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la estructura, el catálogo y las
# funciones utilizadas para representar los diagnósticos de
# TecNet Finder.
#
# El catálogo centraliza nombre, descripción, solución,
# severidad, estado y etapa de cada código para evitar mantener
# esa información repetida en distintas partes del proyecto.
#
# Actualmente se encuentran disponibles los diagnósticos
# LEX-001 a LEX-004, SIN-001 a SIN-008, SEM-001 a SEM-006,
# ADV-001 a ADV-008 y GEN-001.
# ============================================================

from dataclasses import dataclass  # Proporciona la estructura utilizada para representar cada diagnóstico de manera organizada.


ESTADO_DIAGNOSTICO_DISPONIBLE = "disponible"  # Identifica códigos que la versión actual ya puede producir y comprobar.
ESTADO_DIAGNOSTICO_PENDIENTE = "pendiente"  # Reserva un estado común para diagnósticos pertenecientes a etapas futuras.


CATALOGO_DIAGNOSTICOS = {  # Centraliza toda la información descriptiva utilizada por errores y advertencias.
    "LEX-001": {  # Describe el error producido por un identificador ubicado fuera de NAME.
        "categoria": "Léxico",  # Relaciona este código con la primera fase formal del compilador.
        "nombre": "Identificador fuera de lugar",  # Proporciona el título breve mostrado al usuario.
        "descripcion": "Apareció un identificador en una posición no permitida.",  # Resume la condición que origina el diagnóstico.
        "solucion": "Revisa si escribiste mal una palabra reservada. Por ejemplo, usa MASK en lugar de MAS. Si era un nombre de red, debe escribirse después de NAME.",  # Indica cómo corregir normalmente el problema.
        "severidad": "error",  # Marca este diagnóstico como bloqueante para la parte afectada de la entrada.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que el lexer actual ya puede producir este código.
        "etapa": "Base LyAI",  # Conserva la etapa del proyecto donde se incorporó originalmente.
    },
    "LEX-002": {  # Describe símbolos o fragmentos que no pertenecen al lenguaje.
        "categoria": "Léxico",  # Clasifica el problema dentro del reconocimiento de lexemas.
        "nombre": "Símbolo o fragmento no reconocido",  # Proporciona un título breve para la interfaz.
        "descripcion": "Apareció un carácter o fragmento que no pertenece al lenguaje.",  # Resume el significado del error.
        "solucion": "Elimina el símbolo no permitido o reemplázalo por tokens válidos como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR.",  # Sugiere utilizar únicamente elementos definidos por el DSL.
        "severidad": "error",  # Impide considerar completamente correcta la entrada afectada.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la regla se encuentra implementada.
        "etapa": "Base LyAI",  # Señala que pertenece a la base heredada de Lenguajes y Autómatas I.
    },
    "LEX-003": {  # Describe palabras reservadas escritas con capitalización distinta de la oficial.
        "categoria": "Léxico",  # Mantiene la validación dentro del reconocimiento de tokens.
        "nombre": "Palabra reservada con mayúsculas incorrectas",  # Resume de forma visible el problema.
        "descripcion": "Una palabra reservada fue escrita con una combinación de mayúsculas y minúsculas distinta de la definida por el lenguaje.",  # Explica la diferencia respecto al lenguaje formal.
        "solucion": "Escribe las palabras reservadas exactamente como IP, MASK, HOSTS o NAME. Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50.",  # Muestra la escritura aceptada por TecNet Finder.
        "severidad": "error",  # Considera incorrecta la palabra reservada escrita con otra capitalización.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la validación se encuentra activa.
        "etapa": "Refuerzo LyAII",  # Identifica que esta comprobación fue reforzada durante Lenguajes y Autómatas II.
    },
    "LEX-004": {  # Describe valores numéricos escritos directamente junto con texto.
        "categoria": "Léxico",  # Clasifica el problema antes de la validación gramatical.
        "nombre": "Elemento numérico unido a texto",  # Proporciona un nombre breve para el diagnóstico.
        "descripcion": "Un número o una máscara CIDR apareció unido directamente a letras sin un separador válido entre ambos elementos.",  # Explica por qué el lexema no puede dividirse automáticamente.
        "solucion": "Separa los elementos con un espacio. Ejemplo: HOSTS 50 NAME Oficina o MASK /24 HOSTS 50.",  # Muestra las separaciones esperadas por el lenguaje.
        "severidad": "error",  # Considera inválido el lexema unido.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la regla ya forma parte del lexer.
        "etapa": "Refuerzo LyAII",  # Registra que esta comprobación pertenece al refuerzo actual del compilador.
    },
    "SIN-001": {  # Describe una dirección IPv4 incompleta o estructuralmente incorrecta después de IP.
        "categoria": "Sintáctico",  # Relaciona este código con la validación gramatical.
        "nombre": "Dirección IP incompleta o mal formada",  # Proporciona el título utilizado en los resultados.
        "descripcion": "Después de IP se esperaba una dirección IP completa.",  # Resume el elemento exigido por la producción correspondiente.
        "solucion": "Escribe una dirección IPv4 completa. Ejemplo: 192.168.1.0.",  # Ofrece una forma válida de la dirección esperada.
        "severidad": "error",  # Impide construir correctamente el bloque afectado.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el parser puede producir este diagnóstico.
        "etapa": "Base LyAI",  # Registra su origen dentro de la versión base.
    },
    "SIN-002": {  # Describe la ausencia de MASK después de una dirección IP.
        "categoria": "Sintáctico",  # Mantiene el problema dentro de la estructura de la instrucción.
        "nombre": "Falta la palabra reservada MASK",  # Resume el token obligatorio que no apareció.
        "descripcion": "Después de la dirección IP se esperaba la palabra MASK.",  # Explica la regla gramatical incumplida.
        "solucion": "Coloca MASK después de la IP. Si escribiste MAS u otra variante, cámbiala por MASK. Ejemplo: IP 192.168.1.0 MASK /24.",  # Indica cómo restaurar el orden correcto.
        "severidad": "error",  # Marca el bloque como sintácticamente incorrecto.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la ausencia de MASK se detecta actualmente.
        "etapa": "Base LyAI",  # Conserva la etapa histórica del diagnóstico.
    },
    "SIN-003": {  # Describe la ausencia o forma incorrecta de la máscara CIDR.
        "categoria": "Sintáctico",  # Clasifica el problema dentro del parser.
        "nombre": "Máscara CIDR inválida o incompleta",  # Resume el elemento esperado después de MASK.
        "descripcion": "Después de MASK se esperaba una máscara con diagonal.",  # Explica la forma gramatical requerida.
        "solucion": "Escribe la máscara en formato CIDR. Ejemplo: /24.",  # Proporciona un ejemplo válido.
        "severidad": "error",  # Impide aceptar el bloque afectado.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la regla ya está implementada.
        "etapa": "Base LyAI",  # Registra que forma parte de la base histórica del proyecto.
    },
    "SIN-004": {  # Describe HOSTS sin al menos una cantidad posterior.
        "categoria": "Sintáctico",  # Mantiene el diagnóstico dentro de la estructura gramatical.
        "nombre": "Falta cantidad de hosts",  # Resume el elemento ausente.
        "descripcion": "Después de HOSTS se esperaba al menos un número.",  # Explica el requisito mínimo de la lista HOSTS.
        "solucion": "Escribe al menos una cantidad de hosts. Ejemplo: HOSTS 50.",  # Proporciona una forma válida.
        "severidad": "error",  # Impide considerar completa la instrucción.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el parser detecta actualmente este caso.
        "etapa": "Base LyAI",  # Conserva la etapa histórica del código.
    },
    "SIN-005": {  # Describe una lista HOSTS cuya continuación después de coma está incompleta.
        "categoria": "Sintáctico",  # Clasifica el problema dentro de la estructura de la lista.
        "nombre": "Lista de hosts mal formada",  # Resume el error mostrado en la interfaz.
        "descripcion": "Después de una coma se esperaba otro número.",  # Explica qué elemento de la producción no apareció.
        "solucion": "Corrige la lista de hosts. Ejemplo correcto: HOSTS 100,200.",  # Muestra una lista correctamente formada.
        "severidad": "error",  # Marca como incorrecta la construcción de la lista.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que esta validación forma parte del parser actual.
        "etapa": "Base LyAI",  # Conserva su procedencia dentro de la versión base.
    },
    "SIN-006": {  # Describe NAME sin un identificador posterior.
        "categoria": "Sintáctico",  # Relaciona el problema con la parte opcional de la gramática.
        "nombre": "Nombre de red incompleto",  # Resume el problema para la interfaz.
        "descripcion": "Después de NAME se esperaba un identificador.",  # Explica qué terminal falta para completar la sección.
        "solucion": "Escribe un nombre después de NAME o elimina NAME si no usarás nombre.",  # Ofrece las dos correcciones válidas posibles.
        "severidad": "error",  # Considera incompleta la instrucción cuando NAME sí fue escrito.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el caso se detecta actualmente.
        "etapa": "Base LyAI",  # Mantiene la clasificación histórica de la regla.
    },
    "SIN-007": {  # Describe la repetición exacta de una instrucción ya aceptada.
        "categoria": "Sintáctico",  # Se mantiene en el parser porque depende de bloques estructuralmente completos.
        "nombre": "Instrucción duplicada",  # Proporciona un título directo para el usuario.
        "descripcion": "Se declaró una instrucción exactamente igual a otra anterior.",  # Resume la condición necesaria para producir este diagnóstico.
        "solucion": "Elimina la instrucción repetida o cambia IP, máscara, hosts o nombre.",  # Indica cómo diferenciar o retirar el duplicado.
        "severidad": "error",  # Evita conservar dos veces el mismo bloque como válido.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el parser actual realiza esta comprobación.
        "etapa": "Base LyAI",  # Conserva la procedencia del código dentro del proyecto.
    },
    "SIN-008": {  # Describe tokens existentes que aparecen en un orden distinto de la gramática.
        "categoria": "Sintáctico",  # Relaciona directamente el problema con la secuencia esperada.
        "nombre": "Orden incorrecto de tokens",  # Resume la condición detectada.
        "descripcion": "Los tokens existen, pero no aparecen en el orden esperado.",  # Distingue este caso de un token léxicamente desconocido.
        "solucion": "Revisa que la instrucción siga esta estructura: IP <IP_ADDRESS> MASK <SUBNET_MASK> HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>].",  # Presenta la estructura formal que debe respetarse.
        "severidad": "error",  # Impide aceptar una instrucción cuya secuencia es incorrecta.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la recuperación sintáctica actual ya produce este código.
        "etapa": "Base LyAI",  # Conserva la clasificación del diagnóstico en la base del proyecto.
    },
    "SEM-001": {  # Describe una máscara CIDR válida sintácticamente pero fuera del rango aceptado por TecNet Finder.
        "categoria": "Semántico",  # Relaciona la validación con el significado de la máscara.
        "nombre": "Máscara fuera de rango",  # Proporciona un título breve para el diagnóstico.
        "descripcion": "La máscara CIDR existe sintácticamente, pero está fuera del rango permitido.",  # Explica por qué el parser pudo aceptarla y el semántico no.
        "solucion": "Usa una máscara entre /8 y /30. Ejemplo: MASK /24.",  # Muestra el intervalo permitido por las reglas actuales.
        "severidad": "error",  # Impide utilizar el bloque para el cálculo VLSM.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la regla forma parte de U1.
        "etapa": "U1",  # Identifica la unidad donde fue incorporado el análisis semántico.
    },
    "SEM-002": {  # Describe una IP que no corresponde con la dirección inicial de la red indicada por su máscara.
        "categoria": "Semántico",  # Clasifica el problema dentro del significado conjunto de IP y máscara.
        "nombre": "IP base no es dirección de red",  # Resume la inconsistencia encontrada.
        "descripcion": "La IP indicada no corresponde a la dirección de red para la máscara dada.",  # Explica la relación inválida entre ambos elementos.
        "solucion": "Usa la dirección de red correcta para esa máscara. Por ejemplo, para 192.168.1.5/24 la red correcta sería 192.168.1.0.",  # Proporciona un ejemplo concreto de corrección.
        "severidad": "error",  # Evita generar VLSM desde una dirección de host utilizada como base.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la validación ya está implementada.
        "etapa": "U1",  # Registra que pertenece al análisis semántico de Unidad 1.
    },
    "SEM-003": {  # Describe cantidades HOSTS que no representan una solicitud positiva.
        "categoria": "Semántico",  # La forma NUMBER es válida pero su valor no posee significado permitido.
        "nombre": "Cantidad de hosts no válida",  # Resume el problema encontrado.
        "descripcion": "Una cantidad de hosts debe ser mayor que cero.",  # Expresa la regla semántica correspondiente.
        "solucion": "Cambia la cantidad de hosts por un número positivo. Ejemplo: HOSTS 50.",  # Ofrece una cantidad válida como referencia.
        "severidad": "error",  # Impide calcular una subred para cantidades no positivas.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el semántico ya verifica esta condición.
        "etapa": "U1",  # Conserva la unidad en la que se agregó.
    },
    "SEM-004": {  # Describe solicitudes VLSM cuyo espacio conjunto supera la red base.
        "categoria": "Semántico",  # Relaciona el problema con la capacidad real disponible.
        "nombre": "Hosts no caben en la red base",  # Resume el conflicto de capacidad.
        "descripcion": "La suma de los bloques VLSM solicitados excede la capacidad de la red base.",  # Explica que el problema corresponde al conjunto de solicitudes.
        "solucion": "Usa una red base con mayor capacidad, por ejemplo /23 en lugar de /24, o reduce las cantidades de hosts solicitadas.",  # Sugiere ampliar la red o reducir las solicitudes.
        "severidad": "error",  # Evita producir resultados parciales que excedan el espacio disponible.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el cálculo previo de capacidad está activo.
        "etapa": "U1",  # Identifica el diagnóstico como parte del trabajo semántico de Unidad 1.
    },
    "SEM-005": {  # Describe una solicitud individual que necesita más espacio que toda la red base.
        "categoria": "Semántico",  # Clasifica el conflicto dentro del significado y capacidad de la red.
        "nombre": "Subred individual demasiado grande",  # Resume el problema de una solicitud concreta.
        "descripcion": "Una cantidad de hosts necesita un bloque VLSM mayor que toda la red base disponible.",  # Distingue este caso del exceso producido por la suma de varias solicitudes.
        "solucion": "Reduce la cantidad de hosts o utiliza una red base con mayor capacidad.",  # Proporciona las dos correcciones principales.
        "severidad": "error",  # Impide intentar generar una subred imposible dentro de la red proporcionada.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la regla se evalúa actualmente.
        "etapa": "U1",  # Conserva la etapa académica correspondiente.
    },
    "SEM-006": {  # Describe dos redes base válidas individualmente cuyos rangos se cruzan.
        "categoria": "Semántico",  # Relaciona el problema con la interacción entre varios bloques.
        "nombre": "Redes base traslapadas",  # Proporciona el título visible del conflicto.
        "descripcion": "Una red base válida se cruza con otra red base declarada anteriormente.",  # Explica que existe superposición entre rangos IPv4.
        "solucion": "Cambia la IP base o la máscara de la red posterior para que sus rangos IPv4 no se traslapen.",  # Indica qué elementos pueden modificarse para separar las redes.
        "severidad": "error",  # Impide aceptar el bloque posterior que invade una red anterior.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la comparación entre redes ya forma parte del semántico.
        "etapa": "U1",  # Mantiene la referencia con la unidad donde fue implementado.
    },
    "ADV-001": {  # Informa que existen errores pero al menos un bloque reconocido puede continuar.
        "categoria": "Advertencia",  # Identifica este diagnóstico como una recomendación no bloqueante.
        "nombre": "Procesamiento parcial",  # Resume que únicamente una parte de la entrada podrá procesarse.
        "descripcion": "Hay errores, pero también existen bloques válidos que pueden procesarse.",  # Explica la situación general de recuperación.
        "solucion": "Revisa las líneas con error. El sistema continuará únicamente con bloques válidos.",  # Aclara qué hará TecNet Finder mientras existen problemas.
        "severidad": "advertencia",  # Evita tratar esta información como otro error adicional.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el flujo puede producir actualmente esta advertencia.
        "etapa": "Base LyAI",  # Conserva su procedencia dentro del comportamiento histórico.
    },
    "ADV-002": {  # Informa que una palabra reservada está pegada directamente con su valor.
        "categoria": "Advertencia",  # Mantiene válida la instrucción aunque recomienda mejorar su escritura.
        "nombre": "Palabra reservada pegada al valor",  # Resume la condición detectada.
        "descripcion": "Una palabra reservada aparece pegada al valor siguiente.",  # Explica el detalle de legibilidad encontrado.
        "solucion": "Se recomienda separar con espacios. Ejemplo: IP 192.168.1.0 MASK /24 HOSTS 50.",  # Muestra el estilo recomendado para las instrucciones.
        "severidad": "advertencia",  # Confirma que la situación no invalida el bloque.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Indica que esta comprobación ya está implementada.
        "etapa": "Base LyAI",  # Conserva su clasificación histórica.
    },
    "ADV-003": {  # Informa que distintas instrucciones comparten el mismo nombre.
        "categoria": "Advertencia",  # Considera válida la repetición pero potencialmente confusa.
        "nombre": "Nombre de red repetido",  # Resume el problema de identificación encontrado.
        "descripcion": "Dos o más instrucciones usan el mismo nombre de red.",  # Explica cuándo se produce la recomendación.
        "solucion": "Usa nombres distintos para evitar confusión en la tabla VLSM, en el Excel o en la interpretación de resultados.",  # Recomienda nombres únicos para distinguir las redes.
        "severidad": "advertencia",  # No bloquea ninguna de las instrucciones afectadas.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que se comprueban actualmente nombres repetidos.
        "etapa": "Base LyAI",  # Mantiene la etapa histórica de la regla.
    },
    "ADV-004": {  # Informa que una misma instrucción solicita varias veces la misma cantidad de hosts.
        "categoria": "Advertencia",  # Mantiene válida la lista porque la repetición puede ser intencional.
        "nombre": "Hosts repetidos",  # Resume la situación encontrada.
        "descripcion": "La lista de hosts contiene cantidades repetidas dentro de la misma instrucción.",  # Explica exactamente la condición de la advertencia.
        "solucion": "Revisa si los hosts repetidos fueron intencionales. Si no, elimina o corrige los valores duplicados.",  # Recomienda verificar la intención antes de cambiar los datos.
        "severidad": "advertencia",  # No impide generar todas las subredes solicitadas.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el comportamiento ya está activo.
        "etapa": "Base LyAI",  # Conserva su clasificación dentro de la base histórica.
    },
    "ADV-005": {  # Informa que la red base es mucho mayor de lo requerido por las solicitudes VLSM.
        "categoria": "Advertencia",  # Considera válida la red aunque pueda desaprovechar demasiado espacio.
        "nombre": "Red base sobredimensionada",  # Resume el problema de dimensionamiento.
        "descripcion": "La red base dispone de al menos dieciséis veces la capacidad realmente requerida por las solicitudes VLSM.",  # Expresa el umbral exacto utilizado actualmente.
        "solucion": "Considera utilizar una máscara base más específica para aprovechar mejor el espacio de direcciones disponible.",  # Sugiere reducir el tamaño innecesario de la red.
        "severidad": "advertencia",  # Mantiene completamente válido el cálculo.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que esta regla semánticamente informada ya está implementada.
        "etapa": "U1",  # Identifica que esta advertencia se incorporó durante Unidad 1.
    },
    "ADV-006": {  # Informa que NAME utiliza una palabra demasiado general para identificar claramente la red.
        "categoria": "Advertencia",  # La elección del nombre no afecta la validez formal.
        "nombre": "Nombre de red genérico",  # Resume la recomendación mostrada al usuario.
        "descripcion": "El nombre de la red es demasiado genérico y puede causar confusión.",  # Explica por qué conviene utilizar otro identificador.
        "solucion": "Usa un nombre más descriptivo, por ejemplo OficinaCentral, LaboratorioRedes o SucursalTepic.",  # Proporciona ejemplos de nombres más útiles.
        "severidad": "advertencia",  # Mantiene el bloque disponible para VLSM.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la comparación con nombres genéricos está activa.
        "etapa": "Base LyAI",  # Conserva la etapa histórica asociada.
    },
    "ADV-007": {  # Informa que una instrucción válida no utilizó la sección opcional NAME.
        "categoria": "Advertencia",  # Mantiene NAME como parte opcional de la gramática.
        "nombre": "Nombre de red no especificado",  # Resume la recomendación.
        "descripcion": "La instrucción no incluye un nombre para identificar la red.",  # Explica la ausencia detectada.
        "solucion": "Agrega NAME seguido de un identificador para facilitar la lectura de resultados y reportes.",  # Recomienda agregar información descriptiva sin volverla obligatoria.
        "severidad": "advertencia",  # No afecta la validez del bloque.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la advertencia se encuentra disponible.
        "etapa": "Base LyAI",  # Mantiene su clasificación dentro de la base anterior.
    },
    "ADV-008": {  # Informa que HOSTS no fue escrito siguiendo el orden descendente utilizado internamente por VLSM.
        "categoria": "Advertencia",  # La calculadora puede ordenar las cantidades sin invalidar la entrada.
        "nombre": "Hosts fuera del orden recomendado",  # Resume el detalle encontrado.
        "descripcion": "Las cantidades de HOSTS no están escritas de mayor a menor, aunque TecNet Finder puede ordenarlas internamente para realizar el cálculo VLSM.",  # Explica que el orden escrito no impide procesar la instrucción.
        "solucion": "Se recomienda escribir las cantidades de mayor a menor para que la entrada coincida con el orden utilizado por VLSM. Ejemplo: HOSTS 100,50,20.",  # Muestra el orden recomendado.
        "severidad": "advertencia",  # Conserva completamente válida la solicitud.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que la regla ya está activa.
        "etapa": "Refuerzo LyAII",  # Identifica que esta recomendación se agregó durante el refuerzo actual.
    },
    "GEN-001": {  # Proporciona un diagnóstico de respaldo para fallos que todavía no poseen una categoría más específica.
        "categoria": "General",  # Distingue este código de las fases formales del compilador.
        "nombre": "Error no clasificado",  # Proporciona un título general para la interfaz.
        "descripcion": "El error fue detectado, pero no coincide con una categoría específica.",  # Explica por qué se utilizó el diagnóstico de respaldo.
        "solucion": "Revisa la estructura general de la instrucción.",  # Ofrece una recomendación genérica cuando no existe una solución más concreta.
        "severidad": "error",  # Mantiene estos fallos controlados como errores bloqueantes.
        "estado": ESTADO_DIAGNOSTICO_DISPONIBLE,  # Confirma que el código puede utilizarse actualmente.
        "etapa": "Base LyAI",  # Conserva su origen dentro de la infraestructura base.
    },
}


@dataclass(frozen=True)  # Evita modificar accidentalmente un diagnóstico después de haber sido generado.
class Diagnostico:  # Representa de manera estructurada un error o una advertencia producida por TecNet Finder.
    codigo: str  # Conserva el identificador oficial, por ejemplo LEX-002, SEM-004 o ADV-008.
    categoria: str  # Guarda la fase o clasificación visible asociada con el diagnóstico.
    severidad: str  # Indica si el elemento corresponde con un error o una advertencia.
    mensaje: str  # Conserva la explicación concreta generada para la situación encontrada.
    linea: int | None = None  # Guarda la línea relacionada con el problema cuando existe una ubicación precisa.
    columna: int | None = None  # Guarda la posición horizontal donde comienza el fragmento relacionado.
    longitud: int = 1  # Indica cuántos caracteres deben resaltarse dentro del editor.
    fragmento: str = ""  # Conserva exactamente la parte del código fuente asociada con el diagnóstico.
    solucion: str = ""  # Guarda la recomendación central obtenida desde el catálogo.


def obtener_informacion_diagnostico(codigo: str) -> dict:  # Recupera la definición completa correspondiente con un código concreto.
    return CATALOGO_DIAGNOSTICOS.get(codigo, CATALOGO_DIAGNOSTICOS["GEN-001"])  # Utiliza GEN-001 como respaldo cuando el identificador solicitado no está registrado.


def obtener_catalogo_diagnosticos() -> list[tuple[str, dict]]:  # Entrega todas las definiciones respetando el orden declarado en el catálogo.
    return list(CATALOGO_DIAGNOSTICOS.items())  # Convierte el diccionario central en una colección fácil de recorrer desde la interfaz.


def codigo_diagnostico_disponible(codigo: str) -> bool:  # Indica si un código pertenece al comportamiento evaluable de la versión actual.
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)  # Busca la definición exacta sin utilizar el respaldo GEN-001.
    return bool(informacion and informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE)  # Devuelve verdadero solamente cuando el código existe y está marcado como disponible.


def codigo_diagnostico_es_error(codigo: str) -> bool:  # Permite distinguir códigos bloqueantes de las advertencias informativas.
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)  # Recupera la definición real del identificador solicitado.
    return bool(informacion and informacion["severidad"] == "error")  # Devuelve verdadero exclusivamente para diagnósticos registrados con severidad de error.


def obtener_codigos_diagnosticos_disponibles() -> list[str]:  # Construye la lista de códigos que pueden producirse y comprobarse actualmente.
    return [codigo for codigo, informacion in CATALOGO_DIAGNOSTICOS.items() if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE]  # Filtra el catálogo conservando únicamente las entradas marcadas como disponibles.


def obtener_codigos_diagnosticos_pendientes() -> list[str]:  # Construye la lista reservada para diagnósticos pertenecientes a fases futuras.
    return [codigo for codigo, informacion in CATALOGO_DIAGNOSTICOS.items() if informacion["estado"] == ESTADO_DIAGNOSTICO_PENDIENTE]  # Filtra únicamente códigos cuyo estado todavía sea pendiente.


def texto_estado_diagnostico(codigo: str) -> str:  # Convierte el estado interno de un diagnóstico en texto adecuado para mostrar al usuario.
    informacion = CATALOGO_DIAGNOSTICOS.get(codigo)  # Busca exclusivamente la definición exacta del código recibido.

    if informacion is None:  # Comprueba si el identificador no pertenece al catálogo actual.
        return "No registrado"  # Informa claramente que TecNet Finder no conoce ese código.

    if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE:  # Comprueba si el diagnóstico forma parte del comportamiento actual.
        return "Disponible"  # Devuelve un texto breve apropiado para la interfaz.

    etapa = informacion.get("etapa", "").strip()  # Recupera la etapa futura asociada con un código pendiente cuando se encuentra definida.
    return f"Pendiente {etapa}" if etapa else "Pendiente"  # Añade la etapa solamente cuando existe información útil para mostrar.


def crear_diagnostico(codigo: str, mensaje: str, linea: int | None = None, columna: int | None = None, longitud: int = 1, fragmento: str = "", severidad: str | None = None) -> Diagnostico:  # Construye un diagnóstico concreto utilizando la información común almacenada en el catálogo.
    informacion = obtener_informacion_diagnostico(codigo)  # Recupera categoría, solución y severidad predeterminada correspondientes al código.
    severidad_final = severidad or informacion["severidad"]  # Permite sustituir la severidad solamente cuando el llamador necesita indicarlo explícitamente.
    return Diagnostico(
        codigo=codigo,  # Conserva el identificador específico solicitado por la fase que produjo el problema.
        categoria=informacion["categoria"],  # Obtiene automáticamente la categoría común definida en el catálogo.
        severidad=severidad_final,  # Utiliza la severidad indicada o la predeterminada correspondiente con el código.
        mensaje=mensaje,  # Conserva la explicación concreta producida para esta aparición del diagnóstico.
        linea=linea,  # Guarda la línea de origen cuando la fase logró determinarla.
        columna=columna,  # Guarda la columna de origen cuando existe una posición precisa.
        longitud=max(longitud, 1),  # Garantiza que cualquier resaltado visible tenga al menos un carácter de longitud.
        fragmento=fragmento,  # Conserva el texto exacto relacionado con esta aparición concreta.
        solucion=informacion["solucion"],  # Reutiliza la solución centralizada correspondiente con el código.
    )