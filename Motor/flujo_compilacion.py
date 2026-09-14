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
# También controla fallos técnicos producidos durante VLSM,
# conserva los bloques válidos y reúne todo en un único
# ResultadoCompilacion utilizado posteriormente por la interfaz.
#
# Conforme avance Lenguajes y Autómatas II, este mismo flujo
# podrá incorporar las siguientes etapas del compilador.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Proporciona la primera fase encargada de convertir el código fuente en tokens.
from Compilador.analizador_semantico import AnalizadorSemantico  # Proporciona la fase que valida el significado de los bloques sintácticamente correctos.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Proporciona la fase que comprueba el orden gramatical de los tokens reconocidos.
from Motor.advertencias import generar_advertencias  # Genera recomendaciones no bloqueantes independientes de las fases formales.
from Motor.diagnosticos import crear_diagnostico  # Permite construir diagnósticos generales cuando ocurre un fallo técnico controlado.
from Motor.modelos import BloqueRed, ResultadoCompilacion, Token  # Proporciona los modelos utilizados para reunir resultados y localizar elementos originales.
from Redes.calculadora_vlsm import ErrorCalculoVLSM, calcular_vlsm  # Proporciona el cálculo VLSM y su excepción técnica controlada.


class FlujoCompilacion:  # Coordina en orden todas las etapas actualmente conectadas dentro de TecNet Finder.
    def analizar(self, codigo_fuente: str) -> ResultadoCompilacion:  # Ejecuta una compilación completa sobre el código recibido desde el editor.
        analizador_lexico = AnalizadorLexico()  # Crea un lexer independiente para la compilación actual.
        resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Obtiene todos los tokens válidos y diagnósticos léxicos encontrados.

        analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Construye el parser utilizando exclusivamente los tokens reconocidos.
        resultado_sintactico = analizador_sintactico.analizar()  # Obtiene bloques válidos, errores sintácticos, árboles, producciones y derivación.

        analizador_semantico = AnalizadorSemantico(
            bloques=resultado_sintactico.bloques,  # Entrega solamente estructuras que ya superaron correctamente el análisis sintáctico.
            tokens=resultado_lexico.tokens,  # Conserva los tokens originales para ubicar con precisión los errores semánticos.
        )  # Prepara la fase encargada de comprobar significado, capacidad y coherencia de las redes.
        resultado_semantico = analizador_semantico.analizar()  # Obtiene únicamente los bloques que superan todas las reglas SEM disponibles.

        advertencias = generar_advertencias(
            codigo_fuente=codigo_fuente,  # Permite detectar recomendaciones relacionadas directamente con la escritura original.
            resultado_lexico=resultado_lexico,  # Proporciona tokens y errores léxicos para ubicar advertencias.
            resultado_sintactico=resultado_sintactico,  # Proporciona los bloques estructuralmente válidos.
            resultado_semantico=resultado_semantico,  # Proporciona las redes cuyo significado ya fue validado.
        )  # Genera las recomendaciones no bloqueantes utilizando el estado real de las fases formales.
        advertencias = [diagnostico for diagnostico in advertencias if diagnostico.codigo != "ADV-001"]  # Retira temporalmente ADV-001 para recalcularla después de conocer también el resultado VLSM.

        subredes_vlsm = []  # Reúne todas las subredes calculadas a partir de los bloques semánticamente válidos.
        diagnosticos_generales = []  # Conserva fallos técnicos controlados que no pertenecen directamente a una fase formal.

        for bloque in resultado_semantico.bloques_validos:  # Procesa individualmente cada red que logró superar las tres fases formales.
            try:  # Intenta calcular VLSM sin permitir que un fallo técnico detenga toda la compilación.
                resultados_bloque = calcular_vlsm(
                    direccion_ip=bloque.direccion_ip,  # Utiliza la dirección de red validada semánticamente.
                    mascara_subred=bloque.mascara_subred,  # Utiliza la máscara que ya superó las reglas de rango y capacidad.
                    cantidades_hosts=bloque.cantidades_hosts,  # Entrega las solicitudes HOSTS pertenecientes al bloque actual.
                    nombre_red=bloque.nombre,  # Conserva el identificador opcional para relacionar posteriormente las subredes.
                )  # Calcula exclusivamente resultados que provienen de una instrucción completamente válida.
            except ErrorCalculoVLSM as error:  # Atiende una imposibilidad técnica de representación detectada por la calculadora.
                token_host = self._localizar_token_host(
                    tokens=resultado_lexico.tokens,  # Utiliza los tokens originales producidos por el lexer.
                    bloque=bloque,  # Indica cuál de las instrucciones válidas produjo el fallo.
                    indice_host=error.indice_host_original,  # Identifica la cantidad concreta dentro de la lista HOSTS.
                )  # Intenta recuperar el NUMBER exacto para mostrar una ubicación útil en el diagnóstico.

                diagnosticos_generales.append(
                    crear_diagnostico(
                        codigo="GEN-001",  # Utiliza el respaldo general porque el problema no pertenece directamente a LEX, SIN o SEM.
                        mensaje=f"No fue posible calcular VLSM porque la cantidad de HOSTS {error.hosts_solicitados} produce un resultado que no puede representarse dentro del espacio IPv4 disponible.",  # Explica cuál solicitud provocó el fallo técnico.
                        linea=token_host.linea if token_host is not None else None,  # Usa la línea exacta cuando pudo reconstruirse la correspondencia.
                        columna=token_host.columna if token_host is not None else None,  # Usa la columna del NUMBER cuando se encuentra disponible.
                        longitud=len(token_host.valor) if token_host is not None else 1,  # Resalta el número completo o al menos un carácter como respaldo.
                        fragmento=token_host.valor if token_host is not None else str(error.hosts_solicitados),  # Conserva la cantidad relacionada aun si no pudo encontrarse su token.
                    )
                )  # Registra el fallo técnico sin cancelar los demás bloques independientes.
                continue  # Continúa con la siguiente red semánticamente válida cuando exista alguna.

            subredes_vlsm.extend(resultados_bloque)  # Incorpora al resultado global todas las subredes calculadas correctamente para este bloque.

        existen_errores = resultado_lexico.tiene_errores or resultado_sintactico.tiene_errores or resultado_semantico.tiene_errores or bool(diagnosticos_generales)  # Reúne el estado de error de las tres fases y de las protecciones técnicas.

        if existen_errores and subredes_vlsm:  # Comprueba si la entrada contiene problemas pero todavía produjo al menos una salida aprovechable.
            advertencias.append(
                crear_diagnostico(
                    codigo="ADV-001",  # Clasifica la situación final como procesamiento parcial.
                    mensaje="La entrada contiene errores, pero se procesarán únicamente los bloques que superaron las fases disponibles correctamente.",  # Aclara que los resultados mostrados proceden solamente de bloques válidos.
                    severidad="advertencia",  # Mantiene ADV-001 como información no bloqueante adicional.
                )
            )  # Agrega ADV-001 únicamente cuando realmente existe una combinación de errores y resultados VLSM.

        return ResultadoCompilacion(
            resultado_lexico=resultado_lexico,  # Conserva íntegramente los tokens y errores producidos por el lexer.
            resultado_sintactico=resultado_sintactico,  # Conserva bloques, errores y representaciones producidas por el parser.
            resultado_semantico=resultado_semantico,  # Conserva los bloques definitivamente aceptados por las reglas actuales.
            subredes_vlsm=subredes_vlsm,  # Incluye todas las subredes que pudieron calcularse correctamente.
            advertencias=advertencias,  # Incluye las recomendaciones que acompañan la compilación.
            diagnosticos_generales=diagnosticos_generales,  # Incluye cualquier protección técnica que haya sido necesaria.
        )  # Devuelve a la interfaz una sola estructura con toda la información producida durante la compilación.

    def _localizar_token_host(self, tokens: list[Token], bloque: BloqueRed, indice_host: int) -> Token | None:  # Reconstruye el bloque original para localizar una cantidad HOSTS concreta.
        for indice_inicio, token_inicio in enumerate(tokens):  # Busca posibles comienzos de instrucciones dentro de la secuencia léxica completa.
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:  # Comprueba que el token pueda corresponder al inicio del bloque recibido.
                continue  # Descarta cualquier IP ubicada en otra línea o cualquier elemento de otro tipo.

            posicion = indice_inicio + 1  # Avanza hacia el token que debería contener la dirección IPv4.

            if posicion >= len(tokens) or tokens[posicion].tipo != "IP_ADDRESS":  # Comprueba que después de IP exista realmente una dirección reconocida.
                continue  # Descarta la secuencia si no corresponde con la estructura de un bloque válido.

            if tokens[posicion].valor != bloque.direccion_ip:  # Comprueba que la dirección coincida exactamente con la almacenada en el bloque.
                continue  # Evita relacionar accidentalmente la solicitud con otra instrucción diferente.

            posicion += 1  # Avanza desde la dirección IPv4 hacia la palabra reservada MASK.

            if posicion >= len(tokens) or tokens[posicion].tipo != "MASK":  # Comprueba la siguiente parte obligatoria de la instrucción.
                continue  # Descarta la secuencia si no reproduce correctamente el bloque buscado.

            posicion += 1  # Avanza desde MASK hacia la máscara CIDR.

            if posicion >= len(tokens) or tokens[posicion].tipo != "SUBNET_MASK":  # Comprueba que exista un token de máscara reconocido.
                continue  # Descarta secuencias que no contienen la estructura requerida.

            if tokens[posicion].valor != bloque.mascara_subred:  # Comprueba que la máscara pertenezca realmente al bloque recibido.
                continue  # Evita confundir dos instrucciones que compartan dirección pero utilicen otra máscara.

            posicion += 1  # Avanza desde la máscara hacia la palabra reservada HOSTS.

            if posicion >= len(tokens) or tokens[posicion].tipo != "HOSTS":  # Comprueba que la siguiente sección corresponda con la lista de solicitudes.
                continue  # Descarta cualquier secuencia que no represente correctamente el bloque.

            posicion += 1  # Avanza hacia la primera cantidad escrita después de HOSTS.
            tokens_hosts: list[Token] = []  # Reunirá únicamente los NUMBER pertenecientes a la lista actual.

            while posicion < len(tokens):  # Recorre los tokens posteriores mientras todavía formen parte de la lista HOSTS.
                token_actual = tokens[posicion]  # Recupera el elemento que se encuentra actualmente bajo revisión.

                if token_actual.tipo == "NUMBER":  # Comprueba si el elemento corresponde con una cantidad solicitada.
                    tokens_hosts.append(token_actual)  # Conserva el NUMBER junto con su ubicación original.
                    posicion += 1  # Avanza hacia la posible coma o hacia el siguiente elemento de la instrucción.
                    continue  # Continúa reconstruyendo la lista HOSTS.

                if token_actual.tipo == "COMMA":  # Comprueba si el elemento actual solamente separa dos cantidades.
                    posicion += 1  # Omite la coma porque no representa una solicitud individual.
                    continue  # Continúa buscando otro NUMBER después del separador.

                break  # Finaliza la lista al alcanzar NAME, otra instrucción o cualquier elemento diferente.

            cantidades_candidatas = [int(token.valor) for token in tokens_hosts]  # Convierte los NUMBER encontrados para compararlos con la información almacenada en el bloque.

            if cantidades_candidatas != bloque.cantidades_hosts:  # Comprueba que la lista reconstruida pertenezca exactamente a la instrucción buscada.
                continue  # Descarta la secuencia cuando sus solicitudes son diferentes.

            nombre_candidato = None  # Considera inicialmente que el bloque no posee la sección opcional NAME.

            if posicion < len(tokens) and tokens[posicion].tipo == "NAME":  # Comprueba si después de HOSTS aparece la sección opcional de nombre.
                posicion += 1  # Avanza desde NAME hacia el posible identificador.

                if posicion < len(tokens) and tokens[posicion].tipo == "IDENTIFIER":  # Comprueba que exista un nombre reconocido correctamente.
                    nombre_candidato = tokens[posicion].valor  # Conserva el identificador para distinguir bloques con datos semejantes.

            if nombre_candidato != bloque.nombre:  # Compara también el nombre reconstruido con el almacenado originalmente.
                continue  # Descarta otra instrucción que coincida en red y hosts pero posea un nombre diferente.

            if 0 <= indice_host < len(tokens_hosts):  # Comprueba que el índice proporcionado por VLSM corresponda con una cantidad realmente localizada.
                return tokens_hosts[indice_host]  # Devuelve exactamente el NUMBER original que produjo el fallo técnico.

        return None  # Evita inventar una ubicación cuando no puede reconstruirse una correspondencia completamente segura.