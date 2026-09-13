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
# ADV-005 utiliza los bloques que ya superaron el análisis
# semántico para advertir cuando la red base tiene al menos
# dieciséis veces la capacidad realmente requerida por VLSM.
# ============================================================

from collections import Counter  # Importa Counter para localizar cantidades de hosts repetidas.
import re  # Importa expresiones regulares para detectar palabras reservadas escritas sin espacios.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Importa el modelo y la fábrica utilizada para producir advertencias estructuradas.
from Motor.modelos import ResultadoLexico, ResultadoSemantico, ResultadoSintactico, Token  # Importa los resultados y tokens producidos por las fases actuales.


NOMBRES_GENERICOS = {  # Conserva los identificadores considerados demasiado generales para describir una red.
    "red",
    "prueba",
    "test",
    "network",
    "temp",
    "default",
}

FACTOR_SOBREDIMENSIONAMIENTO = 16  # Considera sobredimensionada una red cuya capacidad sea al menos dieciséis veces mayor que el espacio VLSM requerido.


def _buscar_token(
    tokens: list[Token],
    linea: int,
    tipo: str,
    valor: str | None = None,
) -> Token | None:  # Localiza un token para relacionar correctamente una advertencia con el código fuente.
    for token in tokens:  # Recorre los tokens reconocidos conservando el orden original.
        if token.linea != linea:
            continue  # Ignora elementos ubicados en cualquier otra línea.

        if token.tipo != tipo:
            continue  # Ignora elementos pertenecientes a otras categorías léxicas.

        if valor is not None and token.valor != valor:
            continue  # Ignora tokens del mismo tipo cuyo contenido sea diferente.

        return token  # Devuelve inmediatamente la primera coincidencia válida.

    return None  # Indica que no fue posible encontrar una posición concreta.


def _ultimo_token_linea(tokens: list[Token], linea: int) -> Token | None:  # Obtiene el último token de una instrucción.
    tokens_linea = [token for token in tokens if token.linea == linea]  # Reúne únicamente los tokens pertenecientes a la línea solicitada.

    if not tokens_linea:
        return None  # Evita intentar obtener una posición inexistente.

    return max(tokens_linea, key=lambda token: token.columna)  # Devuelve el token situado más a la derecha dentro de la instrucción.


def _calcular_tamano_bloque_vlsm(cantidad_hosts: int) -> int:  # Calcula el bloque potencia de dos requerido para una solicitud.
    direcciones_necesarias = cantidad_hosts + 2  # Agrega las direcciones reservadas para red y broadcast.
    exponente = (direcciones_necesarias - 1).bit_length()  # Obtiene el exponente de la siguiente potencia de dos sin utilizar flotantes.
    return 1 << exponente  # Devuelve la cantidad real de direcciones que ocupará la subred.


def generar_advertencias(
    codigo_fuente: str,
    resultado_lexico: ResultadoLexico,
    resultado_sintactico: ResultadoSintactico,
    resultado_semantico: ResultadoSemantico,
) -> list[Diagnostico]:  # Genera recomendaciones sin modificar la aceptación formal de los bloques.
    advertencias: list[Diagnostico] = []  # Crea la colección donde se reunirán todas las recomendaciones detectadas.
    tokens = resultado_lexico.tokens  # Reutiliza los tokens existentes para asociar cada advertencia con una posición exacta.
    bloques = resultado_sintactico.bloques  # Conserva las advertencias de estilo sobre todos los bloques sintácticamente válidos.
    bloques_semanticos = resultado_semantico.bloques_validos  # Reserva las advertencias de capacidad para bloques que superaron realmente la semántica.

    if (resultado_lexico.tiene_errores or resultado_sintactico.tiene_errores) and bloques:
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-001",
                mensaje="La entrada contiene errores, pero se procesarán únicamente los bloques válidos reconocidos.",
                severidad="advertencia",
            )
        )  # Conserva temporalmente la advertencia histórica de procesamiento parcial.

    patron_pegado = re.compile(r"\b(?:IP(?=\d)|MASK(?=/)|HOSTS(?=\d))")  # Reconoce palabras reservadas válidas que aparecen unidas directamente con su valor siguiente.

    for numero_linea, texto_linea in enumerate(codigo_fuente.splitlines(), start=1):
        coincidencia = patron_pegado.search(texto_linea)  # Busca la primera palabra reservada escrita sin separación.

        if coincidencia is None:
            continue  # Evita producir ADV-002 cuando no existe ningún caso relevante.

        fragmento = coincidencia.group(0)  # Recupera exactamente la palabra reservada que apareció pegada.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-002",
                mensaje=(
                    f"En la línea {numero_linea}, la palabra reservada '{fragmento}' "
                    f"aparece pegada al valor siguiente. Es válido, pero se recomienda "
                    f"usar espacios para mejorar la legibilidad."
                ),
                linea=numero_linea,
                columna=coincidencia.start(),
                longitud=len(fragmento),
                fragmento=fragmento,
                severidad="advertencia",
            )
        )  # Registra la recomendación sin invalidar la instrucción.

    nombres_vistos: dict[str, int] = {}  # Conserva la primera línea donde apareció cada identificador.

    for bloque in bloques:
        if not bloque.nombre:
            continue  # Reserva la ausencia de NAME para ADV-007.

        nombre_normalizado = bloque.nombre.casefold()  # Normaliza diferencias de mayúsculas y minúsculas.

        if nombre_normalizado not in nombres_vistos:
            nombres_vistos[nombre_normalizado] = bloque.linea_origen  # Conserva la primera aparición del nombre.
            continue  # Evita advertir sobre la primera declaración.

        primera_linea = nombres_vistos[nombre_normalizado]  # Recupera la línea donde apareció originalmente el mismo nombre.
        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza exactamente el identificador repetido.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-003",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, el nombre de red "
                    f"'{bloque.nombre}' está repetido. Ya se había utilizado en "
                    f"la línea {primera_linea}. Es válido, pero puede causar confusión."
                ),
                linea=bloque.linea_origen,
                columna=token_nombre.columna if token_nombre else 0,
                longitud=len(bloque.nombre),
                fragmento=bloque.nombre,
                severidad="advertencia",
            )
        )  # Informa la repetición sin impedir el procesamiento.

    for bloque in bloques:
        contador = Counter(bloque.cantidades_hosts)  # Cuenta cuántas veces aparece cada cantidad dentro de la lista actual.
        repetidos = sorted(
            host
            for host, cantidad in contador.items()
            if cantidad > 1
        )  # Reúne únicamente los valores que aparecen más de una vez.

        if not repetidos:
            continue  # Evita producir ADV-004 cuando todas las cantidades son diferentes.

        primer_repetido = str(repetidos[0])  # Utiliza la primera cantidad repetida como referencia visual.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_repetido)  # Localiza la primera aparición del valor repetido.
        texto_repetidos = ", ".join(str(host) for host in repetidos)  # Construye una representación legible de las cantidades duplicadas.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-004",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, se detectaron cantidades "
                    f"de hosts repetidas ({texto_repetidos}). Es válido, pero conviene "
                    f"revisar si fueron escritas intencionalmente."
                ),
                linea=bloque.linea_origen,
                columna=token_host.columna if token_host else 0,
                longitud=len(primer_repetido),
                fragmento=primer_repetido,
                severidad="advertencia",
            )
        )  # Mantiene la lista procesable y únicamente recomienda revisarla.

    for bloque in bloques_semanticos:  # Evalúa ADV-005 solamente sobre redes que ya poseen significado semántico correcto.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera el prefijo que ya superó SEM-001.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones disponibles en la red base.
        capacidad_requerida = sum(
            _calcular_tamano_bloque_vlsm(cantidad_hosts)
            for cantidad_hosts in bloque.cantidades_hosts
        )  # Calcula el espacio total que realmente ocuparán las solicitudes VLSM.

        if capacidad_red < capacidad_requerida * FACTOR_SOBREDIMENSIONAMIENTO:
            continue  # Evita advertir mientras la red base no llegue al umbral conservador definido.

        token_mascara = _buscar_token(
            tokens,
            bloque.linea_origen,
            "SUBNET_MASK",
            bloque.mascara_subred,
        )  # Localiza la máscara porque es el elemento que determina el tamaño de la red base.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-005",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, la red "
                    f"{bloque.direccion_ip}{bloque.mascara_subred} dispone de "
                    f"{capacidad_red} direcciones, mientras que las solicitudes "
                    f"VLSM requieren {capacidad_requerida}. La red base tiene al "
                    f"menos {FACTOR_SOBREDIMENSIONAMIENTO} veces la capacidad necesaria."
                ),
                linea=token_mascara.linea if token_mascara else bloque.linea_origen,
                columna=token_mascara.columna if token_mascara else 0,
                longitud=len(token_mascara.valor) if token_mascara else len(bloque.mascara_subred),
                fragmento=token_mascara.valor if token_mascara else bloque.mascara_subred,
                severidad="advertencia",
            )
        )  # Señala específicamente la máscara que vuelve excesivamente amplia la red base.

    for bloque in bloques:
        if not bloque.nombre:
            continue  # Reserva la ausencia de NAME para ADV-007.

        nombre_normalizado = bloque.nombre.strip().casefold()  # Normaliza el identificador antes de compararlo con los nombres genéricos.

        if nombre_normalizado not in NOMBRES_GENERICOS:
            continue  # Evita producir la recomendación cuando el nombre ya resulta descriptivo.

        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza el identificador concreto.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-006",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, el nombre de red "
                    f"'{bloque.nombre}' es demasiado genérico. Es válido, pero "
                    f"puede causar confusión en los resultados."
                ),
                linea=bloque.linea_origen,
                columna=token_nombre.columna if token_nombre else 0,
                longitud=len(bloque.nombre),
                fragmento=bloque.nombre,
                severidad="advertencia",
            )
        )  # Recomienda un nombre más descriptivo sin rechazar el bloque.

    for bloque in bloques:
        if bloque.nombre:
            continue  # Evita ADV-007 cuando la sección NAME fue especificada correctamente.

        ultimo_token = _ultimo_token_linea(tokens, bloque.linea_origen)  # Obtiene un punto de navegación dentro de la instrucción.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-007",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, la instrucción no incluye "
                    f"un nombre de red. Es válido, pero se recomienda asignar uno "
                    f"para identificar mejor los resultados."
                ),
                linea=bloque.linea_origen,
                columna=ultimo_token.columna if ultimo_token else 0,
                longitud=len(ultimo_token.valor) if ultimo_token else 1,
                fragmento=ultimo_token.valor if ultimo_token else "",
                severidad="advertencia",
            )
        )  # Conserva NAME como elemento opcional y únicamente recomienda utilizarlo.

    for bloque in bloques:
        hosts_ordenados = sorted(bloque.cantidades_hosts, reverse=True)  # Calcula el orden descendente empleado internamente por VLSM.

        if bloque.cantidades_hosts == hosts_ordenados:
            continue  # Evita ADV-008 cuando la entrada ya coincide con el orden recomendado.

        primer_host = str(bloque.cantidades_hosts[0])  # Utiliza la primera cantidad como punto visual de referencia.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_host)  # Localiza la primera cantidad HOSTS.
        orden_original = ",".join(str(host) for host in bloque.cantidades_hosts)  # Reconstruye la secuencia escrita por el usuario.
        orden_recomendado = ",".join(str(host) for host in hosts_ordenados)  # Construye la misma lista ordenada de mayor a menor.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-008",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, las cantidades HOSTS "
                    f"({orden_original}) no están escritas de mayor a menor. "
                    f"La entrada es válida y TecNet Finder las ordenará internamente "
                    f"como {orden_recomendado} para el cálculo VLSM."
                ),
                linea=bloque.linea_origen,
                columna=token_host.columna if token_host else 0,
                longitud=len(primer_host),
                fragmento=primer_host,
                severidad="advertencia",
            )
        )  # Informa el orden recomendado sin cambiar la validez del bloque.

    return advertencias  # Devuelve todas las recomendaciones detectadas sin alterar los resultados formales.