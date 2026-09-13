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


class FlujoCompilacion:  # Coordina las fases disponibles sin colocar su lógica dentro de la interfaz gráfica.
    def analizar(self, codigo_fuente: str) -> ResultadoCompilacion:  # Ejecuta ordenadamente todas las etapas actualmente disponibles.
        analizador_lexico = AnalizadorLexico()  # Crea una nueva instancia del lexer para analizar el código fuente recibido.
        resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Obtiene los tokens y diagnósticos generados durante la fase léxica.

        analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Crea el parser utilizando únicamente los tokens reconocidos por el lexer.
        resultado_sintactico = analizador_sintactico.analizar()  # Obtiene bloques válidos, diagnósticos, árboles, producciones y derivación.

        analizador_semantico = AnalizadorSemantico(
            bloques=resultado_sintactico.bloques,
            tokens=resultado_lexico.tokens,
        )  # Crea la fase semántica utilizando solamente los bloques aceptados por el parser y sus tokens originales.
        resultado_semantico = analizador_semantico.analizar()  # Obtiene los bloques que también cumplen las reglas semánticas disponibles.

        advertencias = generar_advertencias(
            codigo_fuente=codigo_fuente,
            resultado_lexico=resultado_lexico,
            resultado_sintactico=resultado_sintactico,
        )  # Genera recomendaciones sin alterar la aceptación formal de los bloques.

        advertencias = [
            diagnostico
            for diagnostico in advertencias
            if diagnostico.codigo != "ADV-001"
        ]  # Retira temporalmente ADV-001 para recalcularlo después usando también el resultado semántico real.

        subredes_vlsm = []  # Crea la lista donde se reunirán las subredes calculadas para los bloques semánticamente válidos.
        diagnosticos_generales = []  # Conserva fallos técnicos controlados que todavía no pertenecen a una fase formal específica.

        for bloque in resultado_semantico.bloques_validos:  # Permite llegar a VLSM únicamente a las instrucciones aprobadas también por el semántico.
            try:
                resultados_bloque = calcular_vlsm(
                    direccion_ip=bloque.direccion_ip,
                    mascara_subred=bloque.mascara_subred,
                    cantidades_hosts=bloque.cantidades_hosts,
                    nombre_red=bloque.nombre,
                )  # Calcula las subredes solamente después de superar todas las fases formales disponibles.
            except ErrorCalculoVLSM as error:
                token_host = self._localizar_token_host(
                    tokens=resultado_lexico.tokens,
                    bloque=bloque,
                    indice_host=error.indice_host_original,
                )  # Recupera el NUMBER original para señalar exactamente la cantidad que produjo el fallo.

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
                )  # Convierte el fallo técnico de VLSM en un diagnóstico controlado y localizado.
                continue  # Permite que otros bloques independientes continúen procesándose.

            subredes_vlsm.extend(resultados_bloque)  # Agrega las subredes calculadas correctamente a la salida general.

        existen_errores = (
            resultado_lexico.tiene_errores
            or resultado_sintactico.tiene_errores
            or resultado_semantico.tiene_errores
            or bool(diagnosticos_generales)
        )  # Comprueba errores de todas las fases ejecutadas antes de decidir si hubo procesamiento parcial.

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
            )  # Informa procesamiento parcial únicamente cuando existen errores y al menos algún resultado VLSM válido.

        return ResultadoCompilacion(
            resultado_lexico=resultado_lexico,
            resultado_sintactico=resultado_sintactico,
            resultado_semantico=resultado_semantico,
            subredes_vlsm=subredes_vlsm,
            advertencias=advertencias,
            diagnosticos_generales=diagnosticos_generales,
        )  # Reúne los resultados de todas las fases actualmente conectadas al compilador.

    def _localizar_token_host(self, tokens: list[Token], bloque: BloqueRed, indice_host: int) -> Token | None:  # Relaciona una solicitud VLSM con el NUMBER exacto reconocido originalmente por el lexer.
        for indice_inicio, token_inicio in enumerate(tokens):  # Recorre todos los posibles comienzos de instrucción conservados por el lexer.
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:
                continue  # Descarta tokens que no puedan pertenecer al bloque sintáctico recibido.

            posicion = indice_inicio + 1  # Avanza hacia la dirección IPv4 que debe seguir a IP.

            if posicion >= len(tokens) or tokens[posicion].tipo != "IP_ADDRESS":
                continue  # Descarta secuencias que no correspondan a un bloque sintácticamente válido.

            if tokens[posicion].valor != bloque.direccion_ip:
                continue  # Descarta otra instrucción iniciada en la misma línea pero con una IP diferente.

            posicion += 1  # Avanza hacia MASK.

            if posicion >= len(tokens) or tokens[posicion].tipo != "MASK":
                continue  # Descarta secuencias donde MASK no aparezca en la posición esperada.

            posicion += 1  # Avanza hacia la máscara CIDR.

            if posicion >= len(tokens) or tokens[posicion].tipo != "SUBNET_MASK":
                continue  # Descarta secuencias que no contengan una máscara reconocida.

            if tokens[posicion].valor != bloque.mascara_subred:
                continue  # Descarta bloques con la misma IP pero distinta máscara.

            posicion += 1  # Avanza hacia HOSTS.

            if posicion >= len(tokens) or tokens[posicion].tipo != "HOSTS":
                continue  # Descarta secuencias donde no pueda localizarse la lista solicitada.

            posicion += 1  # Coloca el recorrido sobre la primera cantidad solicitada.
            tokens_hosts: list[Token] = []  # Conserva los NUMBER que pertenecen exclusivamente a la lista HOSTS actual.

            while posicion < len(tokens):  # Recorre NUMBER y COMMA hasta alcanzar NAME, otra instrucción o cualquier otro token.
                token_actual = tokens[posicion]  # Obtiene el siguiente elemento perteneciente potencialmente a la lista.

                if token_actual.tipo == "NUMBER":
                    tokens_hosts.append(token_actual)  # Conserva el NUMBER con su línea y columna originales.
                    posicion += 1  # Avanza después de registrar la cantidad encontrada.
                    continue  # Continúa examinando la lista actual.

                if token_actual.tipo == "COMMA":
                    posicion += 1  # Omite únicamente el separador porque no representa una solicitud de hosts.
                    continue  # Continúa hacia la siguiente cantidad.

                break  # Finaliza la lista al encontrar la sección NAME o el comienzo de otro bloque.

            cantidades_candidatas = [int(token.valor) for token in tokens_hosts]  # Convierte los NUMBER encontrados para compararlos con el bloque aceptado.

            if cantidades_candidatas != bloque.cantidades_hosts:
                continue  # Descarta una instrucción parecida cuya lista HOSTS no sea exactamente la misma.

            nombre_candidato = None  # Considera inicialmente que la instrucción no contiene NAME.

            if posicion < len(tokens) and tokens[posicion].tipo == "NAME":
                posicion += 1  # Avanza hacia el identificador asociado con NAME.

                if posicion < len(tokens) and tokens[posicion].tipo == "IDENTIFIER":
                    nombre_candidato = tokens[posicion].valor  # Recupera el nombre para distinguir bloques similares.

            if nombre_candidato != bloque.nombre:
                continue  # Descarta otro bloque con los mismos valores pero un nombre diferente.

            if 0 <= indice_host < len(tokens_hosts):
                return tokens_hosts[indice_host]  # Devuelve exactamente el NUMBER situado en la posición original informada por VLSM.

        return None  # Evita inventar una ubicación si por alguna razón no puede reconstruirse la correspondencia.