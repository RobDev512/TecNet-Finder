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
# determinan si una instrucción es válida. Únicamente informan
# situaciones que conviene revisar mientras el flujo continúa.
#
# También recomienda escribir las cantidades de HOSTS de mayor
# a menor para reflejar desde la entrada el orden que utiliza
# internamente el cálculo VLSM.
# ============================================================

from collections import Counter  # Importa Counter para localizar cantidades de hosts repetidas.
import re  # Importa expresiones regulares para detectar palabras reservadas escritas sin espacios.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Importa el modelo y la fábrica utilizada para producir advertencias estructuradas.
from Motor.modelos import ResultadoLexico, ResultadoSintactico, Token  # Importa los resultados y tokens ya producidos por las fases actuales.


NOMBRES_GENERICOS = {  # Conserva los identificadores considerados demasiado generales para describir una red.
    "red",  # Considera Red como un nombre válido pero poco descriptivo.
    "prueba",  # Considera Prueba como un nombre utilizado normalmente de forma temporal.
    "test",  # Considera Test como equivalente genérico utilizado durante pruebas.
    "network",  # Considera Network como una descripción demasiado general.
    "temp",  # Considera Temp como un identificador temporal poco descriptivo.
    "default",  # Considera Default como un nombre que no diferencia claramente una red.
}


def _buscar_token(
    tokens: list[Token],  # Recibe todos los tokens producidos por el lexer.
    linea: int,  # Recibe la línea concreta donde debe realizarse la búsqueda.
    tipo: str,  # Recibe el tipo de token que debe localizarse.
    valor: str | None = None,  # Permite exigir también un valor concreto cuando resulta necesario.
) -> Token | None:  # Localiza un token para relacionar correctamente una advertencia con el código fuente.
    for token in tokens:  # Recorre los tokens reconocidos conservando el orden original.
        if token.linea != linea:  # Comprueba que el token pertenezca a la instrucción solicitada.
            continue  # Ignora elementos ubicados en cualquier otra línea.

        if token.tipo != tipo:  # Comprueba que el token coincida con el tipo solicitado.
            continue  # Ignora elementos pertenecientes a otras categorías léxicas.

        if valor is not None and token.valor != valor:  # Comprueba el valor cuando la búsqueda exige una coincidencia concreta.
            continue  # Ignora tokens del mismo tipo cuyo contenido sea diferente.

        return token  # Devuelve inmediatamente la primera coincidencia válida.

    return None  # Indica que no fue posible encontrar una posición concreta.


def _ultimo_token_linea(tokens: list[Token], linea: int) -> Token | None:  # Obtiene el último token de una instrucción para ubicar advertencias sobre elementos opcionales ausentes.
    tokens_linea = [token for token in tokens if token.linea == linea]  # Reúne únicamente los tokens pertenecientes a la línea solicitada.

    if not tokens_linea:  # Comprueba que la línea haya producido algún token válido.
        return None  # Evita intentar obtener una posición inexistente.

    return max(tokens_linea, key=lambda token: token.columna)  # Devuelve el token situado más a la derecha dentro de la instrucción.


def generar_advertencias(
    codigo_fuente: str,  # Recibe el código original para revisar aspectos de escritura que no aparecen completamente en los modelos.
    resultado_lexico: ResultadoLexico,  # Recibe los tokens y diagnósticos producidos previamente por el lexer.
    resultado_sintactico: ResultadoSintactico,  # Recibe exclusivamente los bloques que lograron cumplir la gramática.
) -> list[Diagnostico]:  # Genera recomendaciones sin modificar los resultados formales de las fases anteriores.
    advertencias: list[Diagnostico] = []  # Crea la colección donde se reunirán todas las recomendaciones detectadas.
    tokens = resultado_lexico.tokens  # Reutiliza los tokens existentes para asociar cada advertencia con una posición exacta.
    bloques = resultado_sintactico.bloques  # Utiliza únicamente instrucciones sintácticamente válidas para las revisiones estructurales.

    if (resultado_lexico.tiene_errores or resultado_sintactico.tiene_errores) and bloques:  # Comprueba si existen errores junto con al menos un bloque que sí puede continuar.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-001",  # Clasifica la situación como procesamiento parcial.
                mensaje="La entrada contiene errores, pero se procesarán únicamente los bloques válidos reconocidos.",  # Explica que las instrucciones correctas podrán continuar.
                severidad="advertencia",  # Conserva el diagnóstico como una recomendación no bloqueante adicional.
            )
        )

    patron_pegado = re.compile(r"\b(?:IP(?=\d)|MASK(?=/)|HOSTS(?=\d))")  # Reconoce palabras reservadas válidas que aparecen unidas directamente con su valor siguiente.

    for numero_linea, texto_linea in enumerate(codigo_fuente.splitlines(), start=1):  # Recorre el código original línea por línea conservando la numeración visible.
        coincidencia = patron_pegado.search(texto_linea)  # Busca la primera palabra reservada escrita sin separación.

        if coincidencia is None:  # Comprueba si la línea ya utiliza una separación convencional.
            continue  # Evita producir ADV-002 cuando no existe ningún caso relevante.

        fragmento = coincidencia.group(0)  # Recupera exactamente la palabra reservada que apareció pegada.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-002",  # Clasifica la recomendación como palabra reservada pegada al valor.
                mensaje=f"En la línea {numero_linea}, la palabra reservada '{fragmento}' aparece pegada al valor siguiente. Es válido, pero se recomienda usar espacios para mejorar la legibilidad.",  # Explica que la construcción continúa siendo reconocida por el lenguaje.
                linea=numero_linea,  # Guarda la línea exacta donde apareció la escritura compacta.
                columna=coincidencia.start(),  # Guarda la posición donde comienza la palabra reservada.
                longitud=len(fragmento),  # Señala solamente los caracteres pertenecientes a la palabra reservada.
                fragmento=fragmento,  # Conserva el texto concreto utilizado para navegación.
                severidad="advertencia",  # Mantiene completamente válida la instrucción.
            )
        )

    nombres_vistos: dict[str, int] = {}  # Conserva la primera línea donde apareció cada identificador para detectar repeticiones posteriores.

    for bloque in bloques:  # Recorre todas las instrucciones sintácticamente válidas.
        if not bloque.nombre:  # Comprueba si la instrucción realmente posee un nombre opcional.
            continue  # Deja la ausencia de NAME para la comprobación específica ADV-007.

        nombre_normalizado = bloque.nombre.casefold()  # Normaliza diferencias entre mayúsculas y minúsculas para comparar los nombres.

        if nombre_normalizado not in nombres_vistos:  # Comprueba si se trata de la primera aparición del identificador.
            nombres_vistos[nombre_normalizado] = bloque.linea_origen  # Conserva la línea original como referencia para futuras repeticiones.
            continue  # Evita producir una advertencia sobre la primera aparición.

        primera_linea = nombres_vistos[nombre_normalizado]  # Recupera la línea donde se declaró inicialmente el mismo nombre.
        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza exactamente el identificador repetido.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-003",  # Clasifica la recomendación como repetición del nombre de red.
                mensaje=f"En la línea {bloque.linea_origen}, el nombre de red '{bloque.nombre}' está repetido. Ya se había utilizado en la línea {primera_linea}. Es válido, pero puede causar confusión en los resultados.",  # Explica dónde se utilizó previamente el mismo identificador.
                linea=bloque.linea_origen,  # Guarda la ubicación de la aparición repetida.
                columna=token_nombre.columna if token_nombre else 0,  # Utiliza la posición exacta del identificador cuando pudo localizarse.
                longitud=len(bloque.nombre),  # Señala visualmente el nombre completo.
                fragmento=bloque.nombre,  # Conserva el identificador relacionado con la advertencia.
                severidad="advertencia",  # Permite conservar ambos bloques porque compartir nombre no rompe la gramática.
            )
        )

    for bloque in bloques:  # Recorre las listas HOSTS de todas las instrucciones válidas.
        contador = Counter(bloque.cantidades_hosts)  # Cuenta cuántas veces aparece cada cantidad dentro de la lista actual.
        repetidos = sorted(host for host, cantidad in contador.items() if cantidad > 1)  # Reúne de forma ordenada únicamente los valores que aparecen más de una vez.

        if not repetidos:  # Comprueba si todas las cantidades son diferentes.
            continue  # Evita producir ADV-004 cuando no existen repeticiones.

        primer_repetido = str(repetidos[0])  # Utiliza la primera cantidad repetida como referencia visual.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_repetido)  # Localiza la primera aparición del valor repetido.
        texto_repetidos = ", ".join(str(host) for host in repetidos)  # Construye una representación legible de todas las cantidades duplicadas.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-004",  # Clasifica la recomendación como cantidades de hosts repetidas.
                mensaje=f"En la línea {bloque.linea_origen}, se detectaron cantidades de hosts repetidas ({texto_repetidos}). Es válido, pero conviene revisar si fueron escritas intencionalmente.",  # Explica que las repeticiones continúan siendo aceptadas.
                linea=bloque.linea_origen,  # Guarda la línea correspondiente con la lista.
                columna=token_host.columna if token_host else 0,  # Navega hasta la cantidad concreta cuando el token pudo localizarse.
                longitud=len(primer_repetido),  # Señala la longitud de la cantidad utilizada como referencia.
                fragmento=primer_repetido,  # Conserva el número relacionado con la advertencia.
                severidad="advertencia",  # Mantiene la lista completamente procesable.
            )
        )

    for bloque in bloques:  # Recorre los identificadores presentes en las instrucciones válidas.
        if not bloque.nombre:  # Comprueba que exista un nombre antes de evaluar su claridad.
            continue  # Reserva la ausencia de NAME para ADV-007.

        nombre_normalizado = bloque.nombre.strip().casefold()  # Normaliza el identificador únicamente para compararlo con el conjunto de nombres genéricos.

        if nombre_normalizado not in NOMBRES_GENERICOS:  # Comprueba si el identificador aporta información suficiente.
            continue  # Evita producir una recomendación cuando el nombre no figura entre los casos genéricos.

        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza el identificador concreto dentro del código fuente.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-006",  # Clasifica la recomendación como nombre de red demasiado genérico.
                mensaje=f"En la línea {bloque.linea_origen}, el nombre de red '{bloque.nombre}' es demasiado genérico. Es válido, pero puede causar confusión en los resultados.",  # Explica por qué conviene utilizar un identificador más descriptivo.
                linea=bloque.linea_origen,  # Guarda la línea donde aparece el nombre.
                columna=token_nombre.columna if token_nombre else 0,  # Navega hasta el identificador cuando fue localizado.
                longitud=len(bloque.nombre),  # Señala visualmente el nombre completo.
                fragmento=bloque.nombre,  # Conserva el identificador relacionado con la advertencia.
                severidad="advertencia",  # Permite conservar normalmente el nombre original.
            )
        )

    for bloque in bloques:  # Revisa las instrucciones válidas donde la sección opcional NAME pudo omitirse.
        if bloque.nombre:  # Comprueba si el bloque ya posee un identificador.
            continue  # Evita producir ADV-007 cuando NAME fue especificado correctamente.

        ultimo_token = _ultimo_token_linea(tokens, bloque.linea_origen)  # Obtiene el último elemento real para disponer de un destino de navegación.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-007",  # Clasifica la recomendación como ausencia del nombre opcional.
                mensaje=f"En la línea {bloque.linea_origen}, la instrucción no incluye un nombre de red. Es válido, pero se recomienda asignar uno para identificar mejor los resultados.",  # Explica que NAME no es obligatorio.
                linea=bloque.linea_origen,  # Guarda la línea correspondiente con la instrucción.
                columna=ultimo_token.columna if ultimo_token else 0,  # Utiliza el último token como posición de referencia.
                longitud=len(ultimo_token.valor) if ultimo_token else 1,  # Señala el último fragmento disponible cuando existe.
                fragmento=ultimo_token.valor if ultimo_token else "",  # Conserva el texto utilizado como destino de navegación.
                severidad="advertencia",  # Mantiene la instrucción sintácticamente válida.
            )
        )

    for bloque in bloques:  # Revisa finalmente si la lista HOSTS ya refleja el orden descendente utilizado por el cálculo VLSM.
        hosts_ordenados = sorted(bloque.cantidades_hosts, reverse=True)  # Calcula cómo quedarán organizadas internamente las solicitudes antes de asignar subredes.

        if bloque.cantidades_hosts == hosts_ordenados:  # Comprueba si el usuario ya escribió las cantidades de mayor a menor.
            continue  # Evita producir ADV-008 cuando la entrada coincide con el orden recomendado.

        primer_host = str(bloque.cantidades_hosts[0])  # Utiliza la primera cantidad escrita como punto visual de referencia.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_host)  # Localiza la primera cantidad HOSTS de la instrucción.
        orden_original = ",".join(str(host) for host in bloque.cantidades_hosts)  # Reconstruye la secuencia que escribió el usuario.
        orden_recomendado = ",".join(str(host) for host in hosts_ordenados)  # Construye la misma lista en el orden descendente recomendado.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-008",  # Clasifica la nueva recomendación como orden de hosts.
                mensaje=f"En la línea {bloque.linea_origen}, las cantidades HOSTS ({orden_original}) no están escritas de mayor a menor. La entrada es válida y TecNet Finder las ordenará internamente como {orden_recomendado} para el cálculo VLSM.",  # Explica tanto la situación como el comportamiento real del programa.
                linea=bloque.linea_origen,  # Guarda la línea donde aparece la lista desordenada.
                columna=token_host.columna if token_host else 0,  # Navega hacia la primera cantidad HOSTS cuando pudo localizarse.
                longitud=len(primer_host),  # Señala la primera cantidad utilizada como referencia.
                fragmento=primer_host,  # Conserva el valor concreto asociado con la advertencia.
                severidad="advertencia",  # Mantiene el bloque completamente válido y procesable.
            )
        )

    return advertencias  # Devuelve todas las recomendaciones detectadas sin alterar los resultados léxicos ni sintácticos.