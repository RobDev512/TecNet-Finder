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
# ============================================================

from collections import Counter  # Importa Counter para localizar cantidades de hosts repetidas.
import re  # Importa expresiones regulares para detectar palabras reservadas escritas sin espacios.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Importa el modelo y la fábrica utilizada para producir advertencias estructuradas.
from Motor.modelos import ResultadoLexico, ResultadoSintactico, Token  # Importa los resultados y tokens ya producidos por las fases actuales.


NOMBRES_GENERICOS = {  # Conserva los nombres considerados poco descriptivos por la versión anterior.
    "red",
    "prueba",
    "test",
    "network",
    "temp",
    "default",
}


def _buscar_token(
    tokens: list[Token],
    linea: int,
    tipo: str,
    valor: str | None = None,
) -> Token | None:  # Localiza un token concreto dentro de una línea para asociar correctamente la advertencia.
    for token in tokens:  # Recorre los tokens reconocidos por el lexer en su orden original.
        if token.linea != linea:  # Comprueba que el token pertenezca a la misma instrucción.
            continue  # Ignora tokens ubicados en otras líneas.

        if token.tipo != tipo:  # Comprueba que corresponda con el tipo solicitado.
            continue  # Ignora cualquier token de otra clase.

        if valor is not None and token.valor != valor:  # Comprueba también el valor cuando se solicitó una coincidencia concreta.
            continue  # Ignora valores diferentes aunque compartan el mismo tipo.

        return token  # Devuelve la primera coincidencia válida.

    return None  # Indica que no fue posible localizar una posición concreta.


def _ultimo_token_linea(tokens: list[Token], linea: int) -> Token | None:  # Obtiene el último token de una instrucción para ubicar advertencias sobre elementos opcionales ausentes.
    tokens_linea = [token for token in tokens if token.linea == linea]  # Reúne solamente los tokens pertenecientes a la línea solicitada.

    if not tokens_linea:  # Comprueba que la línea haya producido al menos un token.
        return None  # Evita intentar obtener una posición inexistente.

    return max(tokens_linea, key=lambda token: token.columna)  # Devuelve el token situado más a la derecha dentro de la línea.


def generar_advertencias(
    codigo_fuente: str,
    resultado_lexico: ResultadoLexico,
    resultado_sintactico: ResultadoSintactico,
) -> list[Diagnostico]:  # Genera las advertencias actualmente recuperadas sin modificar los resultados de las fases formales.
    advertencias: list[Diagnostico] = []  # Conserva todas las recomendaciones encontradas durante la revisión.
    tokens = resultado_lexico.tokens  # Reutiliza los tokens existentes para ubicar advertencias con precisión.
    bloques = resultado_sintactico.bloques  # Utiliza únicamente instrucciones que ya cumplieron la gramática.

    if (resultado_lexico.tiene_errores or resultado_sintactico.tiene_errores) and bloques:  # Detecta entradas donde algunos bloques fallaron pero otros pueden procesarse.
        advertencias.append(
            crear_diagnostico(
                codigo="ADV-001",
                mensaje=(
                    "La entrada contiene errores, pero se procesarán únicamente "
                    "los bloques válidos reconocidos."
                ),
                severidad="advertencia",
            )
        )

    patron_pegado = re.compile(r"\b(?:IP(?=\d)|MASK(?=/)|HOSTS(?=\d))")  # Reconoce las tres palabras reservadas que el lexer acepta pegadas al valor siguiente.

    for numero_linea, texto_linea in enumerate(codigo_fuente.splitlines(), start=1):  # Recorre cada línea para conservar la misma detección utilizada por el proyecto original.
        coincidencia = patron_pegado.search(texto_linea)  # Busca la primera palabra reservada escrita sin separación dentro de la línea.

        if coincidencia is None:  # Comprueba si la línea utiliza la separación recomendada.
            continue  # Avanza sin generar ninguna advertencia.

        fragmento = coincidencia.group(0)  # Recupera exactamente la palabra reservada que aparece pegada.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-002",
                mensaje=(
                    f"En la línea {numero_linea}, la palabra reservada '{fragmento}' "
                    "aparece pegada al valor siguiente. Es válido, pero se recomienda "
                    "usar espacios para mejorar la legibilidad."
                ),
                linea=numero_linea,
                columna=coincidencia.start(),
                longitud=len(fragmento),
                fragmento=fragmento,
                severidad="advertencia",
            )
        )

    nombres_vistos: dict[str, int] = {}  # Conserva la primera línea donde apareció cada nombre para detectar repeticiones posteriores.

    for bloque in bloques:  # Recorre solamente bloques sintácticamente válidos.
        if not bloque.nombre:  # Comprueba si la instrucción realmente posee un identificador.
            continue  # La ausencia de nombre será atendida posteriormente por ADV-007.

        nombre_normalizado = bloque.nombre.casefold()  # Normaliza mayúsculas y minúsculas para reconocer nombres equivalentes.

        if nombre_normalizado not in nombres_vistos:  # Comprueba si se trata de la primera aparición del nombre.
            nombres_vistos[nombre_normalizado] = bloque.linea_origen  # Conserva su línea como referencia para futuras repeticiones.
            continue  # No genera advertencia en la primera aparición.

        primera_linea = nombres_vistos[nombre_normalizado]  # Recupera dónde se declaró anteriormente el mismo nombre.
        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza visualmente el identificador repetido.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-003",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, el nombre de red "
                    f"'{bloque.nombre}' está repetido. Ya se había utilizado en "
                    f"la línea {primera_linea}. Es válido, pero puede causar "
                    "confusión en los resultados."
                ),
                linea=bloque.linea_origen,
                columna=token_nombre.columna if token_nombre else 0,
                longitud=len(bloque.nombre),
                fragmento=bloque.nombre,
                severidad="advertencia",
            )
        )

    for bloque in bloques:  # Recorre las listas de hosts de cada instrucción válida.
        contador = Counter(bloque.cantidades_hosts)  # Cuenta cuántas veces aparece cada cantidad solicitada.
        repetidos = sorted(host for host, cantidad in contador.items() if cantidad > 1)  # Conserva solamente valores que aparecen más de una vez.

        if not repetidos:  # Comprueba si todas las cantidades son distintas.
            continue  # Evita generar una advertencia innecesaria.

        primer_repetido = str(repetidos[0])  # Utiliza la primera cantidad repetida para ubicar visualmente la recomendación.
        token_host = _buscar_token(tokens, bloque.linea_origen, "NUMBER", primer_repetido)  # Localiza el número dentro de la instrucción.
        texto_repetidos = ", ".join(str(host) for host in repetidos)  # Prepara una representación legible de todos los valores duplicados.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-004",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, se detectaron cantidades "
                    f"de hosts repetidas ({texto_repetidos}). Es válido, pero "
                    "conviene revisar si fueron escritas intencionalmente."
                ),
                linea=bloque.linea_origen,
                columna=token_host.columna if token_host else 0,
                longitud=len(primer_repetido),
                fragmento=primer_repetido,
                severidad="advertencia",
            )
        )

    for bloque in bloques:  # Revisa los identificadores utilizados por todas las instrucciones válidas.
        if not bloque.nombre:  # Comprueba que exista un nombre antes de evaluar su claridad.
            continue  # La ausencia del identificador pertenece a ADV-007.

        nombre_normalizado = bloque.nombre.strip().casefold()  # Normaliza el identificador únicamente para compararlo con el catálogo.

        if nombre_normalizado not in NOMBRES_GENERICOS:  # Comprueba si el nombre aporta suficiente información.
            continue  # Conserva sin advertencia los identificadores descriptivos.

        token_nombre = _buscar_token(tokens, bloque.linea_origen, "IDENTIFIER", bloque.nombre)  # Localiza el nombre dentro del código fuente.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-006",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, el nombre de red "
                    f"'{bloque.nombre}' es demasiado genérico. Es válido, pero "
                    "puede causar confusión en los resultados."
                ),
                linea=bloque.linea_origen,
                columna=token_nombre.columna if token_nombre else 0,
                longitud=len(bloque.nombre),
                fragmento=bloque.nombre,
                severidad="advertencia",
            )
        )

    for bloque in bloques:  # Revisa finalmente las instrucciones donde NAME no fue especificado.
        if bloque.nombre:  # Comprueba si el bloque ya posee un identificador.
            continue  # No requiere ninguna recomendación adicional.

        ultimo_token = _ultimo_token_linea(tokens, bloque.linea_origen)  # Obtiene el último elemento real para poder navegar hasta la instrucción.

        advertencias.append(
            crear_diagnostico(
                codigo="ADV-007",
                mensaje=(
                    f"En la línea {bloque.linea_origen}, la instrucción no incluye "
                    "un nombre de red. Es válido, pero se recomienda asignar uno "
                    "para identificar mejor los resultados."
                ),
                linea=bloque.linea_origen,
                columna=ultimo_token.columna if ultimo_token else 0,
                longitud=len(ultimo_token.valor) if ultimo_token else 1,
                fragmento=ultimo_token.valor if ultimo_token else "",
                severidad="advertencia",
            )
        )

    return advertencias  # Devuelve todas las advertencias sin modificar la validez de ningún bloque.