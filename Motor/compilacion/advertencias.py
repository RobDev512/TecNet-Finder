# ============================================================
# Archivo: advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo genera advertencias no bloqueantes relacionadas
# con legibilidad, organización y uso de las instrucciones.
#
# Las advertencias no forman una fase formal del compilador ni
# determinan por sí mismas si una instrucción es válida.
# Solamente informan situaciones que conviene revisar mientras
# el flujo continúa procesando los bloques aceptados.
#
# Actualmente se generan ADV-001 a ADV-009.
#
# ADV-005 y ADV-009 utilizan específicamente bloques que ya
# superaron el análisis semántico para evitar recomendaciones
# sobre redes cuyo significado todavía no es válido.
# ============================================================

from collections import Counter  # Permite contar cantidades HOSTS repetidas dentro de una misma instrucción.
import ipaddress  # Permite comparar las redes válidas con rangos IPv4 destinados a usos especiales.
import re  # Permite detectar palabras reservadas escritas directamente junto con el valor siguiente.

from Motor.compilacion.diagnosticos import Diagnostico, crear_diagnostico  # Proporciona la estructura y fábrica utilizadas para construir advertencias uniformes.
from Motor.compilacion.modelos import ResultadoLexico, ResultadoSemantico, ResultadoSintactico, Token  # Permite reutilizar resultados y posiciones producidos por las fases formales.


NOMBRES_GENERICOS = {  # Conserva los identificadores considerados demasiado generales para distinguir claramente una red.
    "red",  # Detecta el nombre básico Red como poco descriptivo.
    "prueba",  # Detecta nombres temporales relacionados con pruebas.
    "test",  # Detecta también la variante común escrita en inglés.
    "network",  # Considera demasiado general utilizar únicamente la palabra inglesa para red.
    "temp",  # Detecta nombres que indican una identificación temporal.
    "default",  # Detecta identificadores predeterminados que aportan poca información.
}  # Finaliza el catálogo de nombres considerados genéricos.

FACTOR_SOBREDIMENSIONAMIENTO = 16  # Define que una red se considere claramente sobredimensionada desde dieciséis veces la capacidad realmente requerida.

RANGOS_IPV4_ESPECIALES = (  # Define rangos IPv4 cuyo uso merece una advertencia informativa sin impedir el cálculo VLSM.
    (ipaddress.IPv4Network("0.0.0.0/8"), "direcciones reservadas para identificación de esta red"),  # Identifica el espacio 0.0.0.0/8 como un rango de propósito especial.
    (ipaddress.IPv4Network("127.0.0.0/8"), "direcciones de loopback"),  # Identifica el espacio utilizado para comunicaciones con el propio equipo.
    (ipaddress.IPv4Network("169.254.0.0/16"), "direcciones de enlace local"),  # Identifica el espacio utilizado para direccionamiento automático dentro del enlace local.
    (ipaddress.IPv4Network("224.0.0.0/4"), "direcciones multicast"),  # Identifica el espacio reservado para comunicaciones multicast.
    (ipaddress.IPv4Network("240.0.0.0/4"), "direcciones reservadas para usos especiales"),  # Identifica el espacio superior reservado dentro de IPv4.
)  # Finaliza el conjunto de rangos que pueden producir ADV-009.


def _buscar_token(tokens: list[Token], linea: int, tipo: str, valor: str | None = None) -> Token | None:  # Localiza un token concreto para relacionar una advertencia con el editor.
    for token in tokens:  # Recorre todos los tokens respetando exactamente el orden en que fueron reconocidos.
        if token.linea != linea:  # Comprueba si el token pertenece a una línea diferente de la solicitada.
            continue  # Ignora el elemento porque no puede corresponder con la advertencia actual.

        if token.tipo != tipo:  # Comprueba si el token pertenece a otra categoría léxica.
            continue  # Continúa buscando hasta encontrar el tipo requerido.

        if valor is not None and token.valor != valor:  # Cuando se proporcionó contenido concreto, exige también que coincida exactamente.
            continue  # Ignora tokens del mismo tipo cuyo valor pertenece a otro elemento.

        return token  # Devuelve inmediatamente la primera coincidencia válida encontrada.

    return None  # Informa que no pudo determinarse una ubicación concreta para la advertencia.


def _ultimo_token_linea(tokens: list[Token], linea: int) -> Token | None:  # Obtiene el token situado más a la derecha dentro de una instrucción.
    tokens_linea = [token for token in tokens if token.linea == linea]  # Reúne únicamente los tokens reconocidos en la línea solicitada.

    if not tokens_linea:  # Comprueba si no existe ningún token disponible para esa línea.
        return None  # Evita intentar calcular una posición inexistente.

    return max(tokens_linea, key=lambda token: token.columna)  # Selecciona el elemento cuya columna inicial se encuentra más a la derecha.


def _calcular_tamano_bloque_vlsm(cantidad_hosts: int) -> int:  # Calcula cuántas direcciones ocuparía una solicitud individual dentro de VLSM.
    direcciones_necesarias = cantidad_hosts + 2  # Reserva adicionalmente las direcciones de red y broadcast.
    exponente = (direcciones_necesarias - 1).bit_length()  # Obtiene el exponente de la siguiente potencia de dos sin utilizar operaciones flotantes.
    return 1 << exponente  # Convierte el exponente en la cantidad real de direcciones que ocupará el bloque.


def generar_advertencias(codigo_fuente: str, resultado_lexico: ResultadoLexico, resultado_sintactico: ResultadoSintactico, resultado_semantico: ResultadoSemantico) -> list[Diagnostico]:  # Analiza situaciones recomendables sin alterar la aceptación formal de los bloques.
    advertencias: list[Diagnostico] = []  # Prepara la colección donde se reunirán todas las recomendaciones encontradas.
    tokens = resultado_lexico.tokens  # Reutiliza las posiciones léxicas para relacionar cada advertencia con el código fuente.
    bloques = resultado_sintactico.bloques  # Utiliza los bloques sintácticamente válidos para advertencias relacionadas con estilo y escritura.
    bloques_semanticos = resultado_semantico.bloques_validos  # Reserva determinadas comprobaciones para redes que ya superaron realmente la semántica.

    if (resultado_lexico.tiene_errores or resultado_sintactico.tiene_errores) and bloques:  # Comprueba si existen errores pero el parser logró conservar al menos un bloque utilizable.
        advertencias.append(crear_diagnostico(codigo="ADV-001", mensaje="La entrada contiene errores, pero se procesarán únicamente los bloques válidos reconocidos.", severidad="advertencia"))  # Agrega la advertencia histórica de procesamiento parcial sin convertirla en otro error.

    patron_pegado = re.compile(r"\b(?:IP(?=\d)|MASK(?=/)|HOSTS(?=\d))")  # Reconoce palabras reservadas válidas escritas directamente junto con el valor posterior.

    for numero_linea, texto_linea in enumerate(codigo_fuente.splitlines(), start=1):  # Recorre cada línea conservando el número utilizado por el editor.
        coincidencia = patron_pegado.search(texto_linea)  # Busca la primera palabra reservada que aparece sin un espacio posterior.

        if coincidencia is None:  # Comprueba si la línea actual no posee ninguna palabra reservada pegada.
            continue  # Pasa directamente a la siguiente línea porque no debe producir ADV-002.

        fragmento = coincidencia.group(0)  # Recupera exactamente la palabra reservada que produjo la recomendación.
        advertencias.append(crear_diagnostico(codigo="ADV-002", mensaje=f"En la línea {numero_linea}, la palabra reservada '{fragmento}' aparece pegada al valor siguiente. Es válido, pero se recomienda usar espacios para mejorar la legibilidad.", linea=numero_linea, columna=coincidencia.start(), longitud=len(fragmento), fragmento=fragmento, severidad="advertencia"))  # Registra ADV-002 sin alterar los tokens ni el bloque reconocido.

    nombres_vistos: dict[str, int] = {}  # Relaciona cada nombre normalizado con la primera línea donde apareció.

    for bloque in bloques:  # Recorre los bloques sintácticos para localizar nombres repetidos.
        if not bloque.nombre:  # Comprueba si la instrucción omitió la sección opcional NAME.
            continue  # Reserva esa situación para ADV-007 y evita utilizar None como nombre repetido.

        nombre_normalizado = bloque.nombre.casefold()  # Elimina diferencias entre mayúsculas y minúsculas durante la comparación.

        if nombre_normalizado not in nombres_vistos:  # Comprueba si se trata de la primera aparición de este nombre.
            nombres_vistos[nombre_normalizado] = bloque.linea_origen  # Guarda la línea original para poder mencionarla si vuelve a aparecer.
            continue  # No genera advertencia porque la primera utilización de un nombre es completamente normal.

        primera_linea = nombres_vistos[nombre_normalizado]  # Recupera dónde fue utilizado originalmente el identificador repetido.
        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza el token exacto del nombre repetido para navegación.
        advertencias.append(crear_diagnostico(codigo="ADV-003", mensaje=f"En la línea {bloque.linea_origen}, el nombre de red '{bloque.nombre}' está repetido. Ya se había utilizado en la línea {primera_linea}. Es válido, pero puede causar confusión.", linea=bloque.linea_origen, columna=token_nombre.columna if token_nombre else 0, longitud=len(bloque.nombre), fragmento=bloque.nombre, severidad="advertencia"))  # Registra ADV-003 manteniendo completamente válidas ambas instrucciones.

    for bloque in bloques:  # Recorre cada instrucción para comprobar cantidades HOSTS repetidas internamente.
        contador = Counter(bloque.cantidades_hosts)  # Cuenta cuántas veces fue solicitada cada cantidad dentro de la misma lista.
        repetidos = sorted(host for host, cantidad in contador.items() if cantidad > 1)  # Conserva ordenadamente solamente las cantidades que aparecen dos o más veces.

        if not repetidos:  # Comprueba si todas las cantidades del bloque son diferentes.
            continue  # Omite ADV-004 porque no existe ninguna repetición que revisar.

        primer_repetido = str(repetidos[0])  # Utiliza la primera cantidad duplicada como referencia visual para la advertencia.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_repetido)  # Localiza la primera aparición del número dentro del código fuente.
        texto_repetidos = ", ".join(str(host) for host in repetidos)  # Construye una lista legible con todas las cantidades repetidas.
        advertencias.append(crear_diagnostico(codigo="ADV-004", mensaje=f"En la línea {bloque.linea_origen}, se detectaron cantidades de hosts repetidas ({texto_repetidos}). Es válido, pero conviene revisar si fueron escritas intencionalmente.", linea=bloque.linea_origen, columna=token_host.columna if token_host else 0, longitud=len(primer_repetido), fragmento=primer_repetido, severidad="advertencia"))  # Registra ADV-004 sin eliminar ninguna de las solicitudes proporcionadas.

    for bloque in bloques_semanticos:  # Evalúa sobredimensionamiento solamente sobre redes cuyo significado ya fue validado.
        prefijo = int(bloque.mascara_subred[1:])  # Convierte la máscara CIDR previamente validada en un número utilizable.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones pertenecientes a la red base.
        capacidad_requerida = sum(_calcular_tamano_bloque_vlsm(cantidad_hosts) for cantidad_hosts in bloque.cantidades_hosts)  # Suma el tamaño real de todos los bloques que ocuparían las solicitudes VLSM.

        if capacidad_red < capacidad_requerida * FACTOR_SOBREDIMENSIONAMIENTO:  # Comprueba si la diferencia todavía se encuentra por debajo del umbral conservador.
            continue  # Evita advertir sobre redes que no llegan a dieciséis veces el espacio realmente requerido.

        token_mascara = _buscar_token(tokens, bloque.linea_origen, "SUBNET_MASK", bloque.mascara_subred)  # Localiza la máscara porque es el elemento que determina directamente la capacidad de la red.
        advertencias.append(crear_diagnostico(codigo="ADV-005", mensaje=f"En la línea {bloque.linea_origen}, la red {bloque.direccion_ip}{bloque.mascara_subred} dispone de {capacidad_red} direcciones, mientras que las solicitudes VLSM requieren {capacidad_requerida}. La red base tiene al menos {FACTOR_SOBREDIMENSIONAMIENTO} veces la capacidad necesaria.", linea=token_mascara.linea if token_mascara else bloque.linea_origen, columna=token_mascara.columna if token_mascara else 0, longitud=len(token_mascara.valor) if token_mascara else len(bloque.mascara_subred), fragmento=token_mascara.valor if token_mascara else bloque.mascara_subred, severidad="advertencia"))  # Registra ADV-005 manteniendo completamente válido el bloque sobredimensionado.

    for bloque in bloques:  # Recorre los bloques sintácticos para identificar nombres demasiado genéricos.
        if not bloque.nombre:  # Comprueba si existe realmente un NAME que pueda evaluarse.
            continue  # Reserva la ausencia de nombre para ADV-007.

        nombre_normalizado = bloque.nombre.strip().casefold()  # Elimina espacios exteriores y diferencias de capitalización antes de comparar.

        if nombre_normalizado not in NOMBRES_GENERICOS:  # Comprueba si el identificador aporta suficiente información para no pertenecer al catálogo genérico.
            continue  # Evita producir ADV-006 para nombres que ya resultan descriptivos.

        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza el identificador exacto utilizado dentro del código.
        advertencias.append(crear_diagnostico(codigo="ADV-006", mensaje=f"En la línea {bloque.linea_origen}, el nombre de red '{bloque.nombre}' es demasiado genérico. Es válido, pero puede causar confusión en los resultados.", linea=bloque.linea_origen, columna=token_nombre.columna if token_nombre else 0, longitud=len(bloque.nombre), fragmento=bloque.nombre, severidad="advertencia"))  # Registra ADV-006 sin modificar ni invalidar el nombre proporcionado.

    for bloque in bloques:  # Recorre nuevamente los bloques para detectar instrucciones válidas que omitieron NAME.
        if bloque.nombre:  # Comprueba si la sección opcional ya fue utilizada.
            continue  # No produce ADV-007 porque la red sí posee un nombre explícito.

        ultimo_token = _ultimo_token_linea(tokens, bloque.linea_origen)  # Obtiene un punto visible dentro de la instrucción para asociar la advertencia.
        advertencias.append(crear_diagnostico(codigo="ADV-007", mensaje=f"En la línea {bloque.linea_origen}, la instrucción no incluye un nombre de red. Es válido, pero se recomienda asignar uno para identificar mejor los resultados.", linea=bloque.linea_origen, columna=ultimo_token.columna if ultimo_token else 0, longitud=len(ultimo_token.valor) if ultimo_token else 1, fragmento=ultimo_token.valor if ultimo_token else "", severidad="advertencia"))  # Registra ADV-007 sin convertir NAME en una sección obligatoria.

    for bloque in bloques:  # Comprueba si las cantidades fueron escritas en el mismo orden descendente utilizado internamente por VLSM.
        hosts_ordenados = sorted(bloque.cantidades_hosts, reverse=True)  # Construye la secuencia recomendada de mayor a menor.

        if bloque.cantidades_hosts == hosts_ordenados:  # Compara directamente la secuencia original con el orden recomendado.
            continue  # Omite ADV-008 cuando el usuario ya escribió las cantidades en orden descendente.

        primer_host = str(bloque.cantidades_hosts[0])  # Utiliza la primera cantidad escrita como referencia visual de la lista original.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_host)  # Localiza ese primer NUMBER dentro del código fuente.
        orden_original = ",".join(str(host) for host in bloque.cantidades_hosts)  # Reconstruye la secuencia exactamente en el orden almacenado.
        orden_recomendado = ",".join(str(host) for host in hosts_ordenados)  # Construye la versión ordenada que utilizará VLSM.
        advertencias.append(crear_diagnostico(codigo="ADV-008", mensaje=f"En la línea {bloque.linea_origen}, las cantidades HOSTS ({orden_original}) no están escritas de mayor a menor. La entrada es válida y TecNet Finder las ordenará internamente como {orden_recomendado} para el cálculo VLSM.", linea=bloque.linea_origen, columna=token_host.columna if token_host else 0, longitud=len(primer_host), fragmento=primer_host, severidad="advertencia"))  # Registra ADV-008 sin modificar el contenido escrito originalmente por el usuario.

    for bloque in bloques_semanticos:  # Evalúa rangos especiales únicamente sobre redes que ya superaron todas las reglas SEM disponibles.
        red_bloque = ipaddress.IPv4Network(f"{bloque.direccion_ip}{bloque.mascara_subred}", strict=True)  # Reconstruye el intervalo exacto de una red cuya dirección base y máscara ya fueron validadas.
        coincidencia = next(((rango, descripcion) for rango, descripcion in RANGOS_IPV4_ESPECIALES if red_bloque.overlaps(rango)), None)  # Busca el primer rango especial que se encuentre dentro de la red o se superponga con ella.

        if coincidencia is None:  # Comprueba si todo el espacio de la red permanece fuera de los rangos especiales definidos.
            continue  # Omite ADV-009 porque no existe ninguna situación adicional que informar.

        rango_especial, descripcion_uso = coincidencia  # Recupera tanto el intervalo especial como la descripción de su propósito principal.
        token_ip = _buscar_token(tokens, bloque.linea_origen, "IP_ADDRESS", bloque.direccion_ip)  # Localiza la dirección original para relacionar visualmente la advertencia con el editor.
        advertencias.append(crear_diagnostico(codigo="ADV-009", mensaje=f"En la línea {bloque.linea_origen}, la red {red_bloque.with_prefixlen} coincide o se superpone con el rango IPv4 especial {rango_especial.with_prefixlen}, utilizado para {descripcion_uso}. El cálculo puede realizarse normalmente, pero conviene comprobar que este espacio sea apropiado para el propósito de la red.", linea=token_ip.linea if token_ip else bloque.linea_origen, columna=token_ip.columna if token_ip else 0, longitud=len(token_ip.valor) if token_ip else len(bloque.direccion_ip), fragmento=token_ip.valor if token_ip else bloque.direccion_ip, severidad="advertencia"))  # Registra ADV-009 exclusivamente como información no bloqueante y conserva disponible la red para VLSM.

    return advertencias  # Devuelve todas las recomendaciones generadas para que el flujo las incorpore al resultado general.