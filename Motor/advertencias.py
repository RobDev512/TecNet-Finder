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
# Actualmente se generan ADV-001 a ADV-008. ADV-005 utiliza
# específicamente los bloques que ya superaron el análisis
# semántico para comprobar el dimensionamiento de la red base.
# ============================================================

from collections import Counter  # Permite contar cantidades HOSTS repetidas dentro de una misma instrucción.
import re  # Permite detectar palabras reservadas escritas directamente junto con el valor siguiente.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Proporciona la estructura y fábrica utilizadas para construir advertencias uniformes.
from Motor.modelos import ResultadoLexico, ResultadoSemantico, ResultadoSintactico, Token  # Permite reutilizar los resultados y posiciones producidos por las fases formales.


NOMBRES_GENERICOS = {  # Conserva los identificadores considerados demasiado generales para distinguir claramente una red.
    "red",  # Detecta el nombre básico Red como poco descriptivo.
    "prueba",  # Detecta nombres temporales relacionados con pruebas.
    "test",  # Detecta también la variante común escrita en inglés.
    "network",  # Considera demasiado general utilizar únicamente la palabra inglesa para red.
    "temp",  # Detecta nombres que indican una identificación temporal.
    "default",  # Detecta identificadores predeterminados que aportan poca información.
}

FACTOR_SOBREDIMENSIONAMIENTO = 16  # Define que una red se considere claramente sobredimensionada desde dieciséis veces la capacidad realmente requerida.


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
    bloques_semanticos = resultado_semantico.bloques_validos  # Reserva comprobaciones de capacidad para redes que ya superaron realmente la semántica.

    if (resultado_lexico.tiene_errores or resultado_sintactico.tiene_errores) and bloques:  # Comprueba si existen errores pero el parser logró conservar al menos un bloque utilizable.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-001",  # Identifica la situación como procesamiento parcial.
                mensaje="La entrada contiene errores, pero se procesarán únicamente los bloques válidos reconocidos.",  # Explica que TecNet Finder continuará exclusivamente con las partes aceptadas.
                severidad="advertencia",  # Garantiza que esta información no se interprete como otro error bloqueante.
            )
        )  # Agrega la advertencia histórica de recuperación parcial.

    patron_pegado = re.compile(r"\b(?:IP(?=\d)|MASK(?=/)|HOSTS(?=\d))")  # Reconoce palabras reservadas válidas escritas directamente junto con el valor posterior.

    for numero_linea, texto_linea in enumerate(codigo_fuente.splitlines(), start=1):  # Recorre cada línea conservando el número utilizado por el editor.
        coincidencia = patron_pegado.search(texto_linea)  # Busca la primera palabra reservada que aparece sin un espacio posterior.

        if coincidencia is None:  # Comprueba si la línea actual no posee ninguna palabra reservada pegada.
            continue  # Pasa directamente a la siguiente línea porque no debe producir ADV-002.

        fragmento = coincidencia.group(0)  # Recupera exactamente la palabra reservada que produjo la recomendación.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-002",  # Clasifica el caso como palabra reservada pegada al valor.
                mensaje=f"En la línea {numero_linea}, la palabra reservada '{fragmento}' aparece pegada al valor siguiente. Es válido, pero se recomienda usar espacios para mejorar la legibilidad.",  # Explica que la escritura es aceptada aunque no sea la recomendada.
                linea=numero_linea,  # Relaciona la advertencia con la línea exacta del código fuente.
                columna=coincidencia.start(),  # Utiliza la posición donde comienza la palabra reservada.
                longitud=len(fragmento),  # Permite resaltar únicamente la palabra relacionada con la recomendación.
                fragmento=fragmento,  # Conserva el texto exacto reconocido.
                severidad="advertencia",  # Mantiene la instrucción completamente procesable.
            )
        )  # Registra la recomendación sin alterar los tokens ni los bloques reconocidos.

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
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-003",  # Identifica la repetición de un nombre entre bloques diferentes.
                mensaje=f"En la línea {bloque.linea_origen}, el nombre de red '{bloque.nombre}' está repetido. Ya se había utilizado en la línea {primera_linea}. Es válido, pero puede causar confusión.",  # Informa ambas líneas relacionadas con la repetición.
                linea=bloque.linea_origen,  # Ubica la advertencia sobre la aparición posterior del nombre.
                columna=token_nombre.columna if token_nombre else 0,  # Utiliza la columna exacta o una posición segura si el token no pudo localizarse.
                longitud=len(bloque.nombre),  # Resalta únicamente el identificador repetido.
                fragmento=bloque.nombre,  # Conserva el nombre que provocó la advertencia.
                severidad="advertencia",  # Mantiene ambos bloques como válidos.
            )
        )  # Agrega la recomendación sin modificar ninguna de las instrucciones.

    for bloque in bloques:  # Recorre cada instrucción para comprobar cantidades HOSTS repetidas internamente.
        contador = Counter(bloque.cantidades_hosts)  # Cuenta cuántas veces fue solicitada cada cantidad dentro de la misma lista.
        repetidos = sorted(host for host, cantidad in contador.items() if cantidad > 1)  # Conserva ordenadamente solo las cantidades que aparecen dos o más veces.

        if not repetidos:  # Comprueba si todas las cantidades del bloque son diferentes.
            continue  # Omite ADV-004 porque no existe ninguna repetición que revisar.

        primer_repetido = str(repetidos[0])  # Utiliza la primera cantidad duplicada como referencia visual para la advertencia.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_repetido)  # Localiza la primera aparición del número dentro del código fuente.
        texto_repetidos = ", ".join(str(host) for host in repetidos)  # Construye una lista legible con todas las cantidades repetidas.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-004",  # Identifica específicamente las cantidades HOSTS repetidas.
                mensaje=f"En la línea {bloque.linea_origen}, se detectaron cantidades de hosts repetidas ({texto_repetidos}). Es válido, pero conviene revisar si fueron escritas intencionalmente.",  # Pide verificar que la repetición haya sido intencional.
                linea=bloque.linea_origen,  # Relaciona la advertencia con la instrucción donde aparecen los duplicados.
                columna=token_host.columna if token_host else 0,  # Navega hacia la primera cantidad repetida cuando puede localizarse.
                longitud=len(primer_repetido),  # Resalta solamente la referencia utilizada por la advertencia.
                fragmento=primer_repetido,  # Conserva la cantidad concreta utilizada para ubicar visualmente el problema.
                severidad="advertencia",  # Permite generar todas las subredes solicitadas normalmente.
            )
        )  # Añade la recomendación sin eliminar ninguna cantidad de la lista.

    for bloque in bloques_semanticos:  # Evalúa sobredimensionamiento solamente sobre redes cuyo significado ya fue validado.
        prefijo = int(bloque.mascara_subred[1:])  # Convierte la máscara CIDR previamente validada en un número utilizable.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones pertenecientes a la red base.
        capacidad_requerida = sum(_calcular_tamano_bloque_vlsm(cantidad_hosts) for cantidad_hosts in bloque.cantidades_hosts)  # Suma el tamaño real de todos los bloques que ocuparían las solicitudes VLSM.

        if capacidad_red < capacidad_requerida * FACTOR_SOBREDIMENSIONAMIENTO:  # Comprueba si la diferencia todavía se encuentra por debajo del umbral conservador.
            continue  # Evita advertir sobre redes que no llegan a dieciséis veces el espacio realmente requerido.

        token_mascara = _buscar_token(tokens, bloque.linea_origen, "SUBNET_MASK", bloque.mascara_subred)  # Localiza la máscara porque es el elemento que determina directamente la capacidad de la red.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-005",  # Clasifica el caso como red base sobredimensionada.
                mensaje=f"En la línea {bloque.linea_origen}, la red {bloque.direccion_ip}{bloque.mascara_subred} dispone de {capacidad_red} direcciones, mientras que las solicitudes VLSM requieren {capacidad_requerida}. La red base tiene al menos {FACTOR_SOBREDIMENSIONAMIENTO} veces la capacidad necesaria.",  # Presenta al usuario las capacidades comparadas.
                linea=token_mascara.linea if token_mascara else bloque.linea_origen,  # Utiliza la línea exacta del token cuando se encuentra disponible.
                columna=token_mascara.columna if token_mascara else 0,  # Señala específicamente la máscara responsable del tamaño de la red.
                longitud=len(token_mascara.valor) if token_mascara else len(bloque.mascara_subred),  # Resalta la máscara completa incluso si debe utilizarse el dato del bloque como respaldo.
                fragmento=token_mascara.valor if token_mascara else bloque.mascara_subred,  # Conserva la máscara que produjo el dimensionamiento advertido.
                severidad="advertencia",  # Mantiene completamente válido el bloque porque la capacidad excesiva no impide utilizarlo.
            )
        )  # Agrega la recomendación de optimización del espacio IPv4.

    for bloque in bloques:  # Recorre los bloques para identificar nombres demasiado genéricos.
        if not bloque.nombre:  # Comprueba si existe realmente un NAME que pueda evaluarse.
            continue  # Reserva la ausencia de nombre para ADV-007.

        nombre_normalizado = bloque.nombre.strip().casefold()  # Elimina espacios exteriores y diferencias de capitalización antes de comparar.

        if nombre_normalizado not in NOMBRES_GENERICOS:  # Comprueba si el identificador aporta suficiente información para no pertenecer al catálogo genérico.
            continue  # Evita producir ADV-006 para nombres que ya resultan descriptivos.

        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza el identificador exacto utilizado dentro del código.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-006",  # Clasifica la recomendación como nombre de red genérico.
                mensaje=f"En la línea {bloque.linea_origen}, el nombre de red '{bloque.nombre}' es demasiado genérico. Es válido, pero puede causar confusión en los resultados.",  # Explica que el nombre es aceptado aunque poco descriptivo.
                linea=bloque.linea_origen,  # Relaciona la advertencia con la instrucción correspondiente.
                columna=token_nombre.columna if token_nombre else 0,  # Navega directamente al identificador cuando el token puede localizarse.
                longitud=len(bloque.nombre),  # Resalta todo el nombre utilizado.
                fragmento=bloque.nombre,  # Conserva el identificador concreto evaluado.
                severidad="advertencia",  # Mantiene la instrucción completamente válida.
            )
        )  # Sugiere utilizar un identificador más descriptivo sin modificar el bloque.

    for bloque in bloques:  # Recorre nuevamente los bloques para detectar instrucciones válidas que omitieron NAME.
        if bloque.nombre:  # Comprueba si la sección opcional ya fue utilizada.
            continue  # No produce ADV-007 porque la red sí posee un nombre explícito.

        ultimo_token = _ultimo_token_linea(tokens, bloque.linea_origen)  # Obtiene un punto visible dentro de la instrucción para asociar la advertencia.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-007",  # Identifica la ausencia del nombre opcional.
                mensaje=f"En la línea {bloque.linea_origen}, la instrucción no incluye un nombre de red. Es válido, pero se recomienda asignar uno para identificar mejor los resultados.",  # Aclara que NAME continúa siendo opcional.
                linea=bloque.linea_origen,  # Relaciona el aviso con la instrucción sin nombre.
                columna=ultimo_token.columna if ultimo_token else 0,  # Utiliza el último token disponible como punto práctico de navegación.
                longitud=len(ultimo_token.valor) if ultimo_token else 1,  # Mantiene al menos un carácter resaltable aun si no existe información léxica.
                fragmento=ultimo_token.valor if ultimo_token else "",  # Conserva el último elemento de la instrucción como referencia visual.
                severidad="advertencia",  # Evita convertir NAME en una sección obligatoria.
            )
        )  # Agrega la recomendación manteniendo intacto el bloque reconocido.

    for bloque in bloques:  # Comprueba finalmente si las cantidades fueron escritas en el mismo orden descendente utilizado por VLSM.
        hosts_ordenados = sorted(bloque.cantidades_hosts, reverse=True)  # Construye el orden de mayor a menor que utilizará internamente la calculadora.

        if bloque.cantidades_hosts == hosts_ordenados:  # Compara directamente la secuencia original con el orden recomendado.
            continue  # Omite ADV-008 cuando el usuario ya escribió las cantidades en orden descendente.

        primer_host = str(bloque.cantidades_hosts[0])  # Utiliza la primera cantidad escrita como referencia visual de la lista original.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_host)  # Localiza ese primer NUMBER dentro del código fuente.
        orden_original = ",".join(str(host) for host in bloque.cantidades_hosts)  # Reconstruye la secuencia exactamente en el orden almacenado.
        orden_recomendado = ",".join(str(host) for host in hosts_ordenados)  # Construye la versión ordenada que utilizará VLSM.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-008",  # Clasifica la recomendación relacionada con el orden de HOSTS.
                mensaje=f"En la línea {bloque.linea_origen}, las cantidades HOSTS ({orden_original}) no están escritas de mayor a menor. La entrada es válida y TecNet Finder las ordenará internamente como {orden_recomendado} para el cálculo VLSM.",  # Explica tanto el orden escrito como el realmente utilizado.
                linea=bloque.linea_origen,  # Relaciona la advertencia con la instrucción correspondiente.
                columna=token_host.columna if token_host else 0,  # Señala la primera cantidad escrita cuando se conoce su token.
                longitud=len(primer_host),  # Resalta únicamente la referencia inicial de la lista.
                fragmento=primer_host,  # Conserva el valor utilizado como punto de navegación.
                severidad="advertencia",  # Mantiene válida la instrucción porque TecNet Finder puede reorganizarla internamente.
            )
        )  # Informa el orden recomendado sin modificar el contenido escrito por el usuario.

    return advertencias  # Devuelve todas las recomendaciones generadas para que el flujo las agregue al resultado general.