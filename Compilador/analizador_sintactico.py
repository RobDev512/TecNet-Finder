# ============================================================
# Archivo: analizador_sintactico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene exclusivamente la fase de análisis
# sintáctico del compilador de TecNet Finder.
#
# El analizador sintáctico recibe la lista de tokens producida
# por el lexer y comprueba que aparezcan en el orden establecido
# por la gramática de TecNet Finder.
#
# Estructura general:
# IP <IP_ADDRESS> MASK <SUBNET_MASK>
# HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]
#
# También conserva recuperación por modo pánico, recuperación
# local en HOSTS, detección de duplicados y procesamiento de
# instrucciones válidas aunque otras fallen.
# ============================================================

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Importa el modelo y la función usados para producir errores sintácticos.
from Motor.modelos import BloqueRed, ResultadoSintactico, Token  # Importa los modelos que recibe y devuelve el parser.


DESCRIPCIONES_TOKEN = {  # Relaciona cada tipo de token con una descripción más fácil de mostrar al usuario.
    "IP": "palabra reservada IP",  # Describe la palabra reservada IP.
    "MASK": "palabra reservada MASK",  # Describe la palabra reservada MASK.
    "HOSTS": "palabra reservada HOSTS",  # Describe la palabra reservada HOSTS.
    "NAME": "palabra reservada NAME",  # Describe la palabra reservada NAME.
    "IP_ADDRESS": "dirección IP completa",  # Describe una dirección IPv4 reconocida como unidad.
    "SUBNET_MASK": "máscara CIDR",  # Describe una máscara escrita con diagonal y prefijo.
    "NUMBER": "número entero",  # Describe una cantidad numérica utilizada principalmente en HOSTS.
    "IDENTIFIER": "identificador o nombre de red",  # Describe el nombre opcional colocado después de NAME.
    "COMMA": "coma separadora",  # Describe el separador usado entre cantidades de hosts.
    "DOT": "punto",  # Describe un punto individual producido por una IP incompleta.
}


class ErrorSintacticoInterno(Exception):  # Define una excepción interna usada para abandonar solo el bloque sintáctico actual.
    def __init__(self, diagnostico: Diagnostico):  # Inicializa la excepción utilizando un diagnóstico ya estructurado.
        self.diagnostico = diagnostico  # Conserva el diagnóstico para que analizar pueda recuperarlo posteriormente.
        super().__init__(diagnostico.mensaje)  # Inicializa también Exception usando el mensaje legible del diagnóstico.


class AnalizadorSintactico:  # Define la clase que valida el orden gramatical de los tokens recibidos.
    def __init__(self, tokens: list[Token]):  # Inicializa el parser con la secuencia generada previamente por el lexer.
        self.tokens = tokens  # Guarda todos los tokens que serán procesados.
        self.posicion = 0  # Indica el índice del token que se revisa actualmente.
        self.diagnosticos: list[Diagnostico] = []  # Guarda todos los errores sintácticos encontrados durante el análisis.

    def analizar(self) -> ResultadoSintactico:  # Procesa toda la secuencia y devuelve bloques válidos junto con diagnósticos.
        bloques: list[BloqueRed] = []  # Guarda únicamente las instrucciones que cumplen correctamente la gramática.
        bloques_vistos = set()  # Guarda firmas de instrucciones válidas para detectar repeticiones exactas.

        while self.posicion < len(self.tokens):  # Continúa mientras todavía existan tokens sin procesar.
            posicion_inicio = self.posicion  # Recuerda dónde comenzó el bloque actual para duplicados y recuperación.

            try:  # Intenta reconocer una instrucción completa sin detener el análisis global si falla.
                errores_antes = len(self.diagnosticos)  # Guarda cuántos diagnósticos existían antes de analizar este bloque.
                bloque = self.analizar_bloque()  # Intenta construir una instrucción completa siguiendo la gramática.
                bloque_tiene_errores = len(self.diagnosticos) > errores_antes  # Detecta si hubo errores locales dentro del bloque actual.
                firma = (  # Construye una representación comparable de los datos principales de la instrucción.
                    bloque.direccion_ip,  # Incluye la dirección IP del bloque.
                    bloque.mascara_subred,  # Incluye la máscara CIDR del bloque.
                    tuple(bloque.cantidades_hosts),  # Convierte los hosts a tupla para poder guardar la firma en un set.
                    bloque.nombre,  # Incluye el nombre opcional del bloque.
                )

                if firma in bloques_vistos:  # Comprueba si exactamente la misma instrucción ya había sido aceptada.
                    token_inicio = self.tokens[posicion_inicio]  # Recupera el primer token para ubicar el duplicado en el código fuente.
                    self.diagnosticos.append(  # Agrega un diagnóstico SIN-007 sin conservar una segunda copia del bloque.
                        crear_diagnostico(  # Construye el diagnóstico estructurado de instrucción duplicada.
                            codigo="SIN-007",  # Identifica el error como una instrucción repetida.
                            mensaje=(  # Construye un mensaje específico con los datos de la red duplicada.
                                f"Error sintáctico: instrucción duplicada en línea {token_inicio.linea}. "
                                f"La red con IP {bloque.direccion_ip}, máscara {bloque.mascara_subred} "
                                f"y nombre {bloque.nombre} ya fue declarada anteriormente."
                            ),
                            linea=token_inicio.linea,  # Guarda la línea donde comienza la copia duplicada.
                            columna=token_inicio.columna,  # Guarda la columna del primer token de la copia duplicada.
                            longitud=len(token_inicio.valor),  # Señala inicialmente la longitud del token IP.
                            fragmento=token_inicio.valor,  # Conserva el texto del token donde comienza la instrucción duplicada.
                        )
                    )
                elif not bloque_tiene_errores:  # Comprueba que el bloque no sea duplicado ni haya sufrido errores locales.
                    bloques_vistos.add(firma)  # Registra la firma para detectar futuras repeticiones.
                    bloques.append(bloque)  # Conserva el bloque como una instrucción sintácticamente válida.

            except ErrorSintacticoInterno as error:  # Captura un error grave que impidió terminar el bloque actual.
                self.diagnosticos.append(error.diagnostico)  # Guarda el diagnóstico transportado por la excepción interna.
                self.sincronizar(posicion_inicio)  # Activa el modo pánico para intentar localizar la siguiente instrucción.

            if self.posicion == posicion_inicio:  # Comprueba que alguna parte del parser haya avanzado al menos un token.
                self.posicion += 1  # Fuerza un avance para evitar un ciclo infinito ante una condición inesperada.

        return ResultadoSintactico(  # Devuelve el resultado completo de la fase sintáctica.
            bloques=bloques,  # Entrega todos los bloques sintácticamente válidos.
            diagnosticos=self.diagnosticos.copy(),  # Entrega una copia de todos los diagnósticos encontrados.
        )

    def sincronizar(self, posicion_inicio: int | None = None) -> None:  # Implementa el modo pánico buscando el inicio de otra instrucción.
        linea_error = None  # Inicializa sin conocer todavía la línea donde comenzó el bloque incorrecto.

        if posicion_inicio is not None and posicion_inicio < len(self.tokens):  # Comprueba que se recibió una posición inicial válida.
            linea_error = self.tokens[posicion_inicio].linea  # Obtiene la línea donde comenzó la instrucción que produjo el error.

        while self.posicion < len(self.tokens):  # Avanza por los tokens hasta encontrar un punto adecuado de sincronización.
            token = self.tokens[self.posicion]  # Obtiene el token que se está revisando durante la recuperación.

            if token.tipo == "IP":  # Comprueba si el token podría representar el inicio de una nueva instrucción.
                if linea_error is None or token.linea > linea_error:  # Exige que la nueva IP esté en una línea posterior al bloque fallido.
                    return  # Detiene la recuperación sin consumir IP para que el ciclo principal pueda procesarla.

            self.posicion += 1  # Descarta el token actual porque todavía pertenece a la zona donde ocurrió el error.

    def analizar_bloque(self) -> BloqueRed:  # Reconoce una instrucción completa siguiendo la gramática de TecNet Finder.
        linea_origen = self.tokens[self.posicion].linea  # Guarda la línea donde comienza la instrucción actual.
        self.esperar("IP")  # Exige que cada instrucción comience con la palabra reservada IP.

        if self.posicion >= len(self.tokens) or self.tokens[self.posicion].tipo != "IP_ADDRESS":  # Comprueba que después de IP exista una IPv4 completa.
            ejemplo_ip = self.describir_token_esperado("IP_ADDRESS")  # Construye un ejemplo útil según la IP parcial detectada.

            if self.posicion >= len(self.tokens):  # Comprueba si la entrada terminó inmediatamente después de IP.
                self.lanzar_error(  # Genera SIN-001 porque no existe una dirección completa.
                    codigo="SIN-001",  # Identifica el error como una dirección IP incompleta o mal formada.
                    mensaje=(  # Construye el mensaje correspondiente al fin inesperado de la entrada.
                        "Error sintáctico: dirección IP incompleta o mal formada. Después de IP se esperaba "
                        f"IP_ADDRESS ({ejemplo_ip}), pero se llegó al fin de la entrada."
                    ),
                )

            token = self.tokens[self.posicion]  # Obtiene el token que apareció en lugar de IP_ADDRESS.
            self.lanzar_error(  # Genera SIN-001 usando la posición exacta del token encontrado.
                codigo="SIN-001",  # Identifica el problema como dirección IP incompleta o mal formada.
                mensaje=(  # Construye un mensaje que compara lo esperado con lo encontrado.
                    "Error sintáctico: dirección IP incompleta o mal formada. Después de IP se esperaba "
                    f"IP_ADDRESS ({ejemplo_ip}), pero se encontró {token.tipo} ('{token.valor}') "
                    f"en línea {token.linea}, posición {token.columna}."
                ),
                token=token,  # Relaciona el diagnóstico con el token incorrecto actual.
            )

        direccion_ip = self.esperar("IP_ADDRESS")  # Consume y guarda la dirección IPv4 completa.
        self.esperar("MASK")  # Exige la palabra reservada MASK después de la dirección.
        mascara_subred = self.esperar("SUBNET_MASK")  # Consume y guarda la máscara CIDR.
        self.esperar("HOSTS")  # Exige la palabra reservada HOSTS después de la máscara.

        if self.posicion >= len(self.tokens) or self.tokens[self.posicion].tipo != "NUMBER":  # Comprueba que HOSTS tenga al menos una cantidad.
            if self.posicion >= len(self.tokens):  # Comprueba si la entrada terminó inmediatamente después de HOSTS.
                self.lanzar_error(  # Genera SIN-004 porque no existe ninguna cantidad de hosts.
                    codigo="SIN-004",  # Identifica el problema como ausencia de cantidad después de HOSTS.
                    mensaje=(  # Construye el mensaje correspondiente al fin inesperado de la entrada.
                        "Error sintáctico: después de HOSTS se esperaba al menos un NUMBER con la cantidad "
                        "de hosts, por ejemplo 50, pero se llegó al fin de la entrada."
                    ),
                )

            token = self.tokens[self.posicion]  # Obtiene el token incorrecto que apareció después de HOSTS.
            self.lanzar_error(  # Genera SIN-004 usando la posición exacta del token encontrado.
                codigo="SIN-004",  # Identifica el error como ausencia de una cantidad numérica válida.
                mensaje=(  # Construye un mensaje que compara el NUMBER esperado con el token encontrado.
                    "Error sintáctico: después de HOSTS se esperaba al menos un NUMBER con la cantidad "
                    f"de hosts, por ejemplo 50, pero se encontró {token.tipo} ('{token.valor}') "
                    f"en línea {token.linea}, posición {token.columna}."
                ),
                token=token,  # Relaciona el diagnóstico con el token incorrecto actual.
            )

        cantidades_hosts = self.analizar_hosts()  # Procesa la primera cantidad y las cantidades adicionales separadas por comas.
        nombre = None  # Inicializa el nombre como ausente porque NAME es una parte opcional de la gramática.

        if self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo == "NAME":  # Comprueba si después de HOSTS aparece la sección opcional NAME.
            token_name = self.tokens[self.posicion]  # Guarda el token NAME para conservar su posición ante posibles errores.
            self.posicion += 1  # Consume la palabra reservada NAME.

            if self.posicion >= len(self.tokens):  # Comprueba si la entrada terminó inmediatamente después de NAME.
                self.lanzar_error(  # Genera SIN-006 porque falta el identificador del nombre.
                    codigo="SIN-006",  # Identifica el error como nombre de red incompleto.
                    mensaje=(  # Construye un mensaje específico para el final inesperado de la entrada.
                        "Error sintáctico: después de NAME se esperaba IDENTIFIER con el nombre de la red, "
                        f"pero se llegó al fin de la entrada en línea {token_name.linea}, posición {token_name.columna}."
                    ),
                    token=token_name,  # Relaciona el error con la palabra NAME que quedó incompleta.
                )

            token = self.tokens[self.posicion]  # Obtiene el token que aparece inmediatamente después de NAME.

            if token.tipo == "IP" and token.linea > token_name.linea:  # Detecta una nueva instrucción en otra línea antes de recibir el nombre esperado.
                self.lanzar_error(  # Genera SIN-006 porque la instrucción anterior terminó sin identificador.
                    codigo="SIN-006",  # Identifica el error como nombre de red incompleto.
                    mensaje=(  # Construye un mensaje que explica que comenzó otra instrucción antes del nombre.
                        "Error sintáctico: después de NAME se esperaba IDENTIFIER con el nombre de la red, "
                        "pero la instrucción terminó sin indicar el nombre antes de iniciar otra instrucción "
                        f"en línea {token.linea}, posición {token.columna}."
                    ),
                    token=token_name,  # Señala NAME como origen de la construcción incompleta.
                )

            if token.tipo != "IDENTIFIER":  # Comprueba que cualquier otro token posterior a NAME sea rechazado.
                self.lanzar_error(  # Genera SIN-006 porque NAME no está seguido por un identificador.
                    codigo="SIN-006",  # Identifica el error como nombre de red incompleto.
                    mensaje=(  # Construye un mensaje que compara IDENTIFIER con el token encontrado.
                        "Error sintáctico: después de NAME se esperaba IDENTIFIER con el nombre de la red, "
                        f"pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, "
                        f"posición {token.columna}."
                    ),
                    token=token,  # Relaciona el diagnóstico con el token incorrecto encontrado.
                )

            nombre = token.valor  # Guarda el texto del identificador como nombre de la red.
            self.posicion += 1  # Consume el IDENTIFIER que acaba de ser aceptado.

        return BloqueRed(  # Construye la representación organizada de la instrucción reconocida.
            direccion_ip=direccion_ip,  # Guarda la dirección IP obtenida durante el análisis.
            mascara_subred=mascara_subred,  # Guarda la máscara CIDR obtenida durante el análisis.
            cantidades_hosts=cantidades_hosts,  # Guarda todas las cantidades de hosts reconocidas.
            nombre=nombre,  # Guarda el nombre opcional o None cuando no se utilizó NAME.
            linea_origen=linea_origen,  # Guarda la línea donde comenzó la instrucción.
        )

    def analizar_hosts(self) -> list[int]:  # Procesa NUMBER y las repeticiones opcionales de COMMA NUMBER después de HOSTS.
        cantidades = []  # Crea la lista donde se almacenarán las cantidades reconocidas.
        token = self.tokens[self.posicion]  # Obtiene el primer NUMBER cuya existencia ya comprobó analizar_bloque.
        cantidades.append(int(token.valor))  # Convierte el primer número a entero y lo agrega a la lista.
        self.posicion += 1  # Consume el primer NUMBER de la lista de hosts.

        while self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo == "COMMA":  # Continúa mientras exista otra cantidad separada por coma.
            token_coma = self.tokens[self.posicion]  # Guarda la coma actual para poder ubicar un error si queda incompleta.
            self.posicion += 1  # Consume la coma antes de revisar qué aparece después.

            if self.posicion >= len(self.tokens):  # Comprueba si la entrada terminó inmediatamente después de la coma.
                self.diagnosticos.append(  # Registra un error local sin lanzar modo pánico global.
                    crear_diagnostico(  # Construye el diagnóstico SIN-005 de lista de hosts mal formada.
                        codigo="SIN-005",  # Identifica el problema como una coma sin cantidad posterior.
                        mensaje=(  # Construye un mensaje indicando la posición de la coma incompleta.
                            "Error sintáctico: después de la coma se esperaba NUMBER con otra cantidad de hosts, "
                            f"pero no hay más tokens en línea {token_coma.linea}, posición {token_coma.columna}."
                        ),
                        linea=token_coma.linea,  # Guarda la línea donde apareció la coma incompleta.
                        columna=token_coma.columna,  # Guarda la columna donde apareció la coma incompleta.
                        longitud=len(token_coma.valor),  # Señala la longitud de la coma problemática.
                        fragmento=token_coma.valor,  # Conserva la coma como fragmento relacionado con el error.
                    )
                )
                return cantidades  # Devuelve las cantidades válidas reconocidas antes de encontrar el error local.

            token = self.tokens[self.posicion]  # Obtiene el token ubicado inmediatamente después de la coma.

            if token.tipo != "NUMBER":  # Comprueba si después de la coma apareció algo distinto de otra cantidad.
                self.diagnosticos.append(  # Guarda SIN-005 sin abandonar inmediatamente todo el bloque.
                    crear_diagnostico(  # Construye el diagnóstico estructurado de lista mal formada.
                        codigo="SIN-005",  # Identifica el error como una coma seguida por un elemento incorrecto.
                        mensaje=(  # Construye un mensaje que compara NUMBER con el token realmente encontrado.
                            "Error sintáctico: después de la coma se esperaba NUMBER con otra cantidad de hosts, "
                            f"pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, "
                            f"posición {token.columna}."
                        ),
                        linea=token.linea,  # Guarda la línea del token incorrecto.
                        columna=token.columna,  # Guarda la columna del token incorrecto.
                        longitud=len(token.valor),  # Guarda la longitud del fragmento incorrecto.
                        fragmento=token.valor,  # Conserva exactamente el token que apareció donde no correspondía.
                    )
                )

                while self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo not in ("NUMBER", "NAME", "IP"):  # Descarta tokens hasta encontrar un punto local de recuperación.
                    self.posicion += 1  # Avanza sobre cada token que no permite continuar de forma segura.

                if self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo == "NUMBER":  # Comprueba si la recuperación logró encontrar otra cantidad válida.
                    cantidades.append(int(self.tokens[self.posicion].valor))  # Convierte y guarda el número recuperado.
                    self.posicion += 1  # Consume la cantidad recuperada.
                    continue  # Continúa revisando posibles comas posteriores dentro de la lista.

                return cantidades  # Termina la lista si apareció NAME, IP o se alcanzó el final de los tokens.

            cantidades.append(int(token.valor))  # Convierte y guarda normalmente el NUMBER ubicado después de la coma.
            self.posicion += 1  # Consume el número que acaba de ser aceptado.

        return cantidades  # Devuelve todas las cantidades de hosts reconocidas correctamente.

    def esperar(self, tipo_esperado: str) -> str:  # Exige que el token actual coincida con un tipo concreto de la gramática.
        if self.posicion < len(self.tokens):  # Comprueba que todavía exista un token disponible para comparar.
            token = self.tokens[self.posicion]  # Obtiene el token ubicado en la posición actual.

            if token.tipo == tipo_esperado:  # Comprueba que el token tenga exactamente el tipo esperado.
                self.posicion += 1  # Consume el token correcto y avanza al siguiente.
                return token.valor  # Devuelve el texto del token que cumplió la regla gramatical.

            descripcion = self.describir_token_esperado(tipo_esperado, token)  # Obtiene una explicación legible del elemento que hacía falta.
            codigo = self.codigo_token_esperado(tipo_esperado)  # Selecciona el código SIN correspondiente al token esperado.
            self.lanzar_error(  # Detiene el bloque actual mediante un diagnóstico estructurado.
                codigo=codigo,  # Usa el código específico obtenido para este tipo de ausencia.
                mensaje=(  # Construye un mensaje que compara lo esperado con lo encontrado.
                    f"Error sintáctico: se esperaba {tipo_esperado} ({descripcion}), pero se encontró "
                    f"{token.tipo} ('{token.valor}') en línea {token.linea}, posición {token.columna}."
                ),
                token=token,  # Relaciona el diagnóstico con el token incorrecto actual.
            )

        descripcion = self.describir_token_esperado(tipo_esperado)  # Obtiene la descripción del elemento faltante cuando ya no existen tokens.
        codigo = self.codigo_token_esperado(tipo_esperado)  # Obtiene el código de diagnóstico correspondiente al tipo esperado.
        self.lanzar_error(  # Genera el error correspondiente al final inesperado de la entrada.
            codigo=codigo,  # Usa el código específico del token que hacía falta.
            mensaje=f"Error sintáctico: se esperaba {tipo_esperado} ({descripcion}), pero no hay más tokens.",  # Explica que la entrada terminó antes de completar la regla.
        )

    def describir_token_esperado(self, tipo_esperado: str, token_actual: Token | None = None) -> str:  # Genera una descripción o ejemplo útil del token que hacía falta.
        if tipo_esperado == "SUBNET_MASK" and token_actual is not None and token_actual.tipo == "NUMBER":  # Detecta una máscara probablemente escrita sin diagonal.
            return f"máscara CIDR, por ejemplo /{token_actual.valor}"  # Usa el número escrito para sugerir la forma CIDR correcta.

        if tipo_esperado == "IP_ADDRESS":  # Aplica una construcción especial cuando se esperaba una dirección IPv4 completa.
            partes = []  # Crea una lista para reunir NUMBER y DOT consecutivos de una IP parcial.
            indice = self.posicion  # Comienza a revisar temporalmente desde la posición actual sin mover el parser real.

            while indice < len(self.tokens) and self.tokens[indice].tipo in ("NUMBER", "DOT"):  # Reúne todas las partes consecutivas que podrían formar una IP incompleta.
                partes.append(self.tokens[indice].valor)  # Agrega el texto del NUMBER o DOT encontrado.
                indice += 1  # Avanza únicamente el índice temporal utilizado para construir el ejemplo.

            ip_parcial = "".join(partes)  # Une las partes reconocidas para reconstruir la dirección parcial escrita por el usuario.

            if ip_parcial:  # Comprueba si realmente fue posible recuperar alguna parte de una IP.
                if ip_parcial.endswith("."):  # Detecta una dirección parcial que termina justo después de un punto.
                    ip_parcial += "0"  # Agrega temporalmente un cero para poder formar un ejemplo completo.

                while ip_parcial.count(".") < 3:  # Comprueba cuántos separadores faltan para completar cuatro octetos.
                    ip_parcial += ".0"  # Agrega octetos de ejemplo hasta alcanzar tres puntos.

                octetos = ip_parcial.split(".")  # Divide la dirección reconstruida en sus componentes.

                while len(octetos) < 4:  # Comprueba si todavía faltan elementos para representar cuatro octetos.
                    octetos.append("0")  # Agrega un octeto de ejemplo cuando sea necesario.

                octetos_corregidos = []  # Crea la lista donde se guardarán únicamente valores válidos para el ejemplo final.

                for octeto in octetos[:4]:  # Revisa únicamente los primeros cuatro componentes de la dirección reconstruida.
                    if octeto.isdigit() and 0 <= int(octeto) <= 255:  # Comprueba que el componente sea numérico y esté dentro del rango IPv4.
                        octetos_corregidos.append(octeto)  # Conserva el octeto original cuando su valor es válido.
                    else:  # Se ejecuta cuando el componente reconstruido no puede ser un octeto IPv4 válido.
                        octetos_corregidos.append("0")  # Sustituye el valor inválido por cero únicamente dentro del ejemplo sugerido.

                return "dirección IP completa, por ejemplo " + ".".join(octetos_corregidos)  # Devuelve un ejemplo completo basado en lo que alcanzó a escribir el usuario.

            return "dirección IP completa, por ejemplo 192.168.1.0"  # Devuelve un ejemplo genérico cuando no existe una IP parcial aprovechable.

        return DESCRIPCIONES_TOKEN.get(tipo_esperado, tipo_esperado)  # Devuelve la descripción conocida o el nombre técnico si no existe una especial.

    def codigo_token_esperado(self, tipo_esperado: str) -> str:  # Relaciona un token faltante con el código de diagnóstico sintáctico adecuado.
        codigos = {  # Define los errores específicos que pueden seleccionarse según el elemento esperado.
            "IP_ADDRESS": "SIN-001",  # Asocia una dirección IP faltante con SIN-001.
            "MASK": "SIN-002",  # Asocia la palabra MASK faltante con SIN-002.
            "SUBNET_MASK": "SIN-003",  # Asocia una máscara CIDR faltante con SIN-003.
            "NUMBER": "SIN-004",  # Asocia un número requerido después de HOSTS con SIN-004.
            "IDENTIFIER": "SIN-006",  # Asocia un identificador faltante después de NAME con SIN-006.
        }
        return codigos.get(tipo_esperado, "SIN-008")  # Devuelve el código específico o SIN-008 para cualquier otro error de orden.

    def lanzar_error(self, codigo: str, mensaje: str, token: Token | None = None) -> None:  # Crea un diagnóstico y detiene únicamente el bloque sintáctico actual.
        if token is not None:  # Comprueba si existe un token concreto relacionado con el problema.
            diagnostico = crear_diagnostico(  # Construye el diagnóstico usando directamente la posición del token incorrecto.
                codigo=codigo,  # Guarda el código sintáctico recibido.
                mensaje=mensaje,  # Guarda el mensaje específico construido por el parser.
                linea=token.linea,  # Usa la línea del token relacionado.
                columna=token.columna,  # Usa la columna del token relacionado.
                longitud=len(token.valor),  # Usa la longitud del texto del token para señalarlo visualmente.
                fragmento=token.valor,  # Conserva exactamente el fragmento relacionado con el error.
            )
        else:  # Se ejecuta cuando el error ocurre sin un token actual, normalmente al final de la entrada.
            linea = None  # Inicializa la línea sin una ubicación concreta.
            columna = None  # Inicializa la columna sin una ubicación concreta.

            if self.posicion > 0 and self.posicion - 1 < len(self.tokens):  # Comprueba si existe un token anterior que permita aproximar la ubicación.
                token_anterior = self.tokens[self.posicion - 1]  # Obtiene el último token procesado correctamente.
                linea = token_anterior.linea  # Usa la misma línea del token anterior como ubicación del problema.
                columna = token_anterior.columna + len(token_anterior.valor)  # Coloca el error inmediatamente después del final del token anterior.

            diagnostico = crear_diagnostico(  # Construye el diagnóstico correspondiente a un elemento faltante al final.
                codigo=codigo,  # Guarda el código sintáctico recibido.
                mensaje=mensaje,  # Guarda el mensaje específico construido por el parser.
                linea=linea,  # Guarda la línea aproximada calculada.
                columna=columna,  # Guarda la columna aproximada calculada.
                longitud=1,  # Usa un carácter como longitud mínima para futuras marcas visuales.
                fragmento="",  # Deja vacío el fragmento porque no existe un token incorrecto concreto.
            )

        raise ErrorSintacticoInterno(diagnostico)  # Lanza la excepción interna para que analizar active la recuperación por modo pánico.
