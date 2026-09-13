# ============================================================
# Archivo: flujo_compilacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo coordina las diferentes partes de TecNet Finder
# sin implementar directamente ninguna fase del compilador.
#
# Actualmente ejecuta análisis léxico, análisis sintáctico,
# análisis semántico, advertencias no bloqueantes y cálculo VLSM.
#
# Conforme avance Lenguajes y Autómatas II, este mismo flujo
# incorporará código intermedio, optimización y generación
# de código objeto.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa la primera fase encargada de convertir el código fuente en tokens.
from Compilador.analizador_semantico import AnalizadorSemantico  # Importa la fase que comprueba el significado de los bloques sintácticamente válidos.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa la fase que comprueba el orden gramatical de los tokens.
from Motor.advertencias import generar_advertencias  # Importa las recomendaciones no bloqueantes separadas de las fases formales.
from Motor.diagnosticos import crear_diagnostico  # Importa la construcción estructurada utilizada para controlar fallos técnicos conocidos.
from Motor.modelos import BloqueRed, ResultadoCompilacion, Token  # Importa los modelos utilizados para reunir resultados y localizar solicitudes originales.
from Redes.calculadora_vlsm import ErrorCalculoVLSM, calcular_vlsm  # Importa el cálculo de red y el fallo controlado que identifica la solicitud problemática.


class FlujoCompilacion:
    def analizar(self, codigo_fuente: str) -> ResultadoCompilacion:
        analizador_lexico = AnalizadorLexico()  # Crea una nueva instancia del lexer para la compilación actual.
        resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Obtiene tokens y diagnósticos léxicos.

        analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Construye el parser sobre los tokens reconocidos.
        resultado_sintactico = analizador_sintactico.analizar()  # Obtiene bloques, diagnósticos y representaciones sintácticas.

        analizador_semantico = AnalizadorSemantico(
            bloques=resultado_sintactico.bloques,
            tokens=resultado_lexico.tokens,
        )  # Construye la fase semántica únicamente con estructuras previamente aceptadas.
        resultado_semantico = analizador_semantico.analizar()  # Obtiene los bloques que superan todas las reglas SEM disponibles.

        advertencias = generar_advertencias(
            codigo_fuente=codigo_fuente,
            resultado_lexico=resultado_lexico,
            resultado_sintactico=resultado_sintactico,
            resultado_semantico=resultado_semantico,
        )  # Genera advertencias de estilo y capacidad utilizando el estado real de las fases formales.

        advertencias = [
            diagnostico
            for diagnostico in advertencias
            if diagnostico.codigo != "ADV-001"
        ]  # Retira ADV-001 temporal para recalcularla después de conocer también la salida VLSM real.

        subredes_vlsm = []  # Reúne las subredes calculadas para bloques completamente válidos.
        diagnosticos_generales = []  # Conserva fallos técnicos controlados ajenos a una fase formal específica.

        for bloque in resultado_semantico.bloques_validos:
            try:
                resultados_bloque = calcular_vlsm(
                    direccion_ip=bloque.direccion_ip,
                    mascara_subred=bloque.mascara_subred,
                    cantidades_hosts=bloque.cantidades_hosts,
                    nombre_red=bloque.nombre,
                )  # Calcula VLSM únicamente después de superar el análisis semántico completo.
            except ErrorCalculoVLSM as error:
                token_host = self._localizar_token_host(
                    tokens=resultado_lexico.tokens,
                    bloque=bloque,
                    indice_host=error.indice_host_original,
                )  # Recupera el NUMBER original relacionado con el fallo técnico.

                diagnosticos_generales.append(
                    crear_diagnostico(
                        codigo="GEN-001",
                        mensaje=(
                            f"No fue posible calcular VLSM porque la cantidad de HOSTS "
                            f"{error.hosts_solicitados} produce un resultado que no puede "
                            f"representarse dentro del espacio IPv4 disponible."
                        ),
                        linea=token_host.linea if token_host is not None else None,
                        columna=token_host.columna if token_host is not None else None,
                        longitud=len(token_host.valor) if token_host is not None else 1,
                        fragmento=token_host.valor if token_host is not None else str(error.hosts_solicitados),
                    )
                )  # Mantiene GEN-001 únicamente como protección técnica de respaldo.
                continue  # Permite que cualquier otro bloque independiente continúe normalmente.

            subredes_vlsm.extend(resultados_bloque)  # Incorpora al resultado global las subredes calculadas correctamente.

        existen_errores = (
            resultado_lexico.tiene_errores
            or resultado_sintactico.tiene_errores
            or resultado_semantico.tiene_errores
            or bool(diagnosticos_generales)
        )  # Reúne el estado de error de todas las fases formales y protecciones técnicas.

        if existen_errores and subredes_vlsm:
            advertencias.append(
                crear_diagnostico(
                    codigo="ADV-001",
                    mensaje=(
                        "La entrada contiene errores, pero se procesarán únicamente "
                        "los bloques que superaron las fases disponibles correctamente."
                    ),
                    severidad="advertencia",
                )
            )  # Informa procesamiento parcial solamente cuando existe al menos una salida aprovechable.

        return ResultadoCompilacion(
            resultado_lexico=resultado_lexico,
            resultado_sintactico=resultado_sintactico,
            resultado_semantico=resultado_semantico,
            subredes_vlsm=subredes_vlsm,
            advertencias=advertencias,
            diagnosticos_generales=diagnosticos_generales,
        )  # Devuelve en una sola estructura todo lo producido por el flujo actual.

    def _localizar_token_host(self, tokens: list[Token], bloque: BloqueRed, indice_host: int) -> Token | None:
        for indice_inicio, token_inicio in enumerate(tokens):
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:
                continue  # Descarta tokens que no puedan representar el comienzo del bloque buscado.

            posicion = indice_inicio + 1  # Avanza hacia la dirección IPv4.

            if posicion >= len(tokens) or tokens[posicion].tipo != "IP_ADDRESS":
                continue  # Descarta secuencias que no posean la estructura esperada.

            if tokens[posicion].valor != bloque.direccion_ip:
                continue  # Descarta instrucciones con una IP diferente.

            posicion += 1  # Avanza hacia MASK.

            if posicion >= len(tokens) or tokens[posicion].tipo != "MASK":
                continue  # Descarta secuencias sin la palabra reservada esperada.

            posicion += 1  # Avanza hacia la máscara CIDR.

            if posicion >= len(tokens) or tokens[posicion].tipo != "SUBNET_MASK":
                continue  # Descarta secuencias sin máscara reconocida.

            if tokens[posicion].valor != bloque.mascara_subred:
                continue  # Descarta otra instrucción con máscara diferente.

            posicion += 1  # Avanza hacia HOSTS.

            if posicion >= len(tokens) or tokens[posicion].tipo != "HOSTS":
                continue  # Descarta una secuencia que no posea la lista esperada.

            posicion += 1  # Avanza hacia la primera cantidad.
            tokens_hosts: list[Token] = []  # Reúne únicamente los NUMBER de esta lista HOSTS.

            while posicion < len(tokens):
                token_actual = tokens[posicion]  # Obtiene el siguiente elemento de la secuencia.

                if token_actual.tipo == "NUMBER":
                    tokens_hosts.append(token_actual)  # Conserva el NUMBER con su ubicación original.
                    posicion += 1
                    continue

                if token_actual.tipo == "COMMA":
                    posicion += 1  # Omite los separadores entre cantidades.
                    continue

                break  # Finaliza al alcanzar NAME u otro elemento.

            cantidades_candidatas = [int(token.valor) for token in tokens_hosts]  # Reconstruye las cantidades localizadas.

            if cantidades_candidatas != bloque.cantidades_hosts:
                continue  # Descarta una lista que no pertenezca exactamente al bloque recibido.

            nombre_candidato = None  # Considera inicialmente que NAME no fue utilizado.

            if posicion < len(tokens) and tokens[posicion].tipo == "NAME":
                posicion += 1  # Avanza hacia el identificador opcional.

                if posicion < len(tokens) and tokens[posicion].tipo == "IDENTIFIER":
                    nombre_candidato = tokens[posicion].valor  # Recupera el nombre para diferenciar bloques similares.

            if nombre_candidato != bloque.nombre:
                continue  # Descarta bloques con otro nombre.

            if 0 <= indice_host < len(tokens_hosts):
                return tokens_hosts[indice_host]  # Devuelve exactamente la cantidad informada por VLSM.

        return None  # Evita inventar una posición cuando no puede reconstruirse una correspondencia segura.