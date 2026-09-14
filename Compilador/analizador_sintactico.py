# ============================================================
# Archivo: analizador_sintactico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene exclusivamente la fase de análisis
# sintáctico del compilador de TecNet Finder.
#
# Recibe los tokens producidos por el analizador léxico y
# comprueba que aparezcan respetando la gramática definida para
# las instrucciones de direccionamiento.
#
# Estructura general:
# IP <IP_ADDRESS> MASK <SUBNET_MASK>
# HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]
#
# También implementa recuperación por modo pánico, recuperación
# local de listas HOSTS, detección de instrucciones duplicadas,
# construcción de árboles sintácticos, producciones utilizadas
# y derivaciones de los bloques reconocidos correctamente.
#
# Actualmente implementa SIN-001 a SIN-008.
# ============================================================

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Proporciona la estructura y fábrica utilizadas para generar errores sintácticos.
from Motor.modelos import BloqueRed, NodoSintactico, ResultadoSintactico, Token  # Proporciona los tokens recibidos y las estructuras producidas por el parser.


DESCRIPCIONES_TOKEN = {  # Relaciona cada categoría léxica con una descripción comprensible para los mensajes del parser.
    "IP": "palabra reservada IP",  # Describe el token obligatorio que inicia cada instrucción.
    "MASK": "palabra reservada MASK",  # Describe la palabra que introduce la máscara CIDR.
    "HOSTS": "palabra reservada HOSTS",  # Describe la palabra que introduce la lista de cantidades.
    "NAME": "palabra reservada NAME",  # Describe la sección opcional destinada al nombre de la red.
    "IP_ADDRESS": "dirección IP completa",  # Describe una dirección IPv4 reconocida completamente por el lexer.
    "SUBNET_MASK": "máscara CIDR",  # Describe una máscara escrita mediante diagonal y prefijo.
    "NUMBER": "número entero",  # Describe las cantidades utilizadas principalmente dentro de HOSTS.
    "IDENTIFIER": "identificador o nombre de red",  # Describe el nombre aceptado después de NAME.
    "COMMA": "coma separadora",  # Describe el separador permitido entre cantidades de hosts.
    "DOT": "punto",  # Describe puntos individuales que pueden aparecer cuando una dirección quedó incompleta.
}


class ErrorSintacticoInterno(Exception):  # Permite abandonar solamente la instrucción actual y regresar al ciclo general del parser.
    def __init__(self, diagnostico: Diagnostico):  # Recibe un diagnóstico ya construido para transportarlo durante la recuperación.
        self.diagnostico = diagnostico  # Conserva el error exacto que deberá agregarse al resultado sintáctico.
        super().__init__(diagnostico.mensaje)  # Inicializa también Exception utilizando el mensaje legible del diagnóstico.


class AnalizadorSintactico:  # Comprueba que la secuencia de tokens respete el orden establecido por la gramática de TecNet Finder.
    def __init__(self, tokens: list[Token]):  # Prepara el parser utilizando la salida producida previamente por el lexer.
        self.tokens = tokens  # Conserva la secuencia completa que será recorrida de izquierda a derecha.
        self.posicion = 0  # Indica el índice del token que se encuentra actualmente bajo análisis.
        self.diagnosticos: list[Diagnostico] = []  # Reúne todos los errores sintácticos encontrados sin detener el análisis global.

    def analizar(self) -> ResultadoSintactico:  # Procesa toda la secuencia y devuelve únicamente los bloques que cumplen la gramática.
        bloques: list[BloqueRed] = []  # Conserva las instrucciones sintácticamente aceptadas.
        bloques_vistos = set()  # Conserva firmas inmutables para detectar declaraciones exactamente repetidas.

        while self.posicion < len(self.tokens):  # Continúa hasta consumir o recuperar todos los tokens recibidos.
            posicion_inicio = self.posicion  # Recuerda dónde comenzó el bloque actual para recuperación y detección de duplicados.

            try:  # Intenta reconocer una instrucción completa sin permitir que un error detenga los bloques posteriores.
                errores_antes = len(self.diagnosticos)  # Registra cuántos errores existían antes de comenzar esta instrucción.
                bloque = self.analizar_bloque()  # Intenta reconocer IP, MASK, HOSTS y NAME respetando la gramática.
                bloque_tiene_errores = len(self.diagnosticos) > errores_antes  # Detecta errores locales recuperables producidos dentro de HOSTS.

                firma = (
                    bloque.direccion_ip,  # Incluye la dirección IPv4 para distinguir la red declarada.
                    bloque.mascara_subred,  # Incluye la máscara utilizada por la instrucción.
                    tuple(bloque.cantidades_hosts),  # Convierte HOSTS a tupla para permitir almacenar la firma dentro de un set.
                    bloque.nombre,  # Incluye también NAME para que solamente una instrucción completamente idéntica sea duplicada.
                )  # Construye una representación comparable del contenido sintáctico reconocido.

                if firma in bloques_vistos:  # Comprueba si exactamente la misma instrucción ya había sido aceptada anteriormente.
                    token_inicio = self.tokens[posicion_inicio]  # Recupera el token inicial para señalar la segunda aparición en el editor.
                    self.diagnosticos.append(
                        crear_diagnostico(
                            codigo="SIN-007",  # Clasifica el problema como instrucción duplicada.
                            mensaje=f"Error sintáctico: instrucción duplicada en línea {token_inicio.linea}. La red con IP {bloque.direccion_ip}, máscara {bloque.mascara_subred} y nombre {bloque.nombre} ya fue declarada anteriormente.",  # Explica qué declaración se encontró repetida.
                            linea=token_inicio.linea,  # Relaciona el diagnóstico con la línea donde comienza la copia.
                            columna=token_inicio.columna,  # Utiliza la posición exacta de la palabra IP duplicada.
                            longitud=len(token_inicio.valor),  # Resalta inicialmente el token que introduce el bloque repetido.
                            fragmento=token_inicio.valor,  # Conserva el texto exacto utilizado como punto de navegación.
                        )
                    )  # Registra SIN-007 sin almacenar una segunda copia de la instrucción.

                elif not bloque_tiene_errores:  # Comprueba que el bloque tampoco haya requerido recuperación local durante HOSTS.
                    bloques_vistos.add(firma)  # Registra la firma para comparar las instrucciones posteriores.
                    bloques.append(bloque)  # Conserva el bloque porque cumplió completamente la estructura sintáctica.

            except ErrorSintacticoInterno as error:  # Atiende errores que impiden terminar normalmente la instrucción actual.
                self.diagnosticos.append(error.diagnostico)  # Incorpora el diagnóstico transportado por la excepción interna.
                self.sincronizar(posicion_inicio)  # Activa modo pánico para buscar el comienzo de una instrucción posterior.

            if self.posicion == posicion_inicio:  # Comprueba defensivamente que el parser haya consumido al menos algún token.
                self.posicion += 1  # Fuerza un avance para impedir un ciclo infinito ante una situación inesperada.

        arboles = [self.construir_arbol_bloque(bloque) for bloque in bloques]  # Construye árboles únicamente para instrucciones completamente válidas.
        producciones_usadas = self.generar_producciones_usadas(bloques)  # Obtiene la gramática base y las producciones empleadas por la entrada.
        derivacion = self.generar_derivacion(bloques)  # Construye la derivación general y las derivaciones individuales.
        arbol_textual = self.generar_arbol_textual(arboles)  # Convierte los árboles estructurados en una representación con ramas.

        return ResultadoSintactico(
            bloques=bloques,  # Entrega solamente instrucciones que superaron completamente la gramática.
            diagnosticos=self.diagnosticos.copy(),  # Entrega una copia de todos los errores producidos durante el análisis.
            arboles=arboles,  # Entrega los árboles correspondientes con cada bloque válido.
            producciones_usadas=producciones_usadas,  # Entrega el texto explicativo de las producciones aplicadas.
            derivacion=derivacion,  # Entrega las sustituciones realizadas desde los símbolos no terminales.
            arbol_textual=arbol_textual,  # Entrega la representación legible de la estructura sintáctica.
        )  # Reúne toda la información producida por esta fase dentro de una sola estructura.

    def sincronizar(self, posicion_inicio: int | None = None) -> None:  # Implementa recuperación por modo pánico buscando otra instrucción que comience con IP.
        linea_error = None  # Parte sin conocer una línea concreta cuando no se proporcionó una posición inicial válida.

        if posicion_inicio is not None and posicion_inicio < len(self.tokens):  # Comprueba que la posición inicial realmente exista dentro de la secuencia.
            linea_error = self.tokens[posicion_inicio].linea  # Conserva la línea donde comenzó el bloque que acaba de fallar.

        while self.posicion < len(self.tokens):  # Descarta tokens hasta encontrar un posible punto seguro para continuar.
            token = self.tokens[self.posicion]  # Recupera el elemento que se encuentra actualmente bajo revisión.

            if token.tipo == "IP":  # Comprueba si este elemento podría iniciar una instrucción nueva.
                if linea_error is None or token.linea > linea_error:  # Exige que la nueva IP pertenezca a una línea posterior al bloque fallido.
                    return  # Detiene la recuperación sin consumir IP para que analizar pueda procesarla normalmente.

            self.posicion += 1  # Descarta el token actual porque todavía pertenece a la zona afectada por el error.

    def analizar_bloque(self) -> BloqueRed:  # Reconoce una instrucción completa aplicando en orden las producciones correspondientes con B.
        linea_origen = self.tokens[self.posicion].linea  # Conserva la línea inicial para relacionarla posteriormente con el bloque construido.
        self.esperar("IP")  # Exige y consume la palabra reservada con la que debe comenzar toda instrucción.

        if self.posicion >= len(self.tokens) or self.tokens[self.posicion].tipo != "IP_ADDRESS":  # Comprueba específicamente que después de IP exista una dirección completa.
            ejemplo_ip = self.describir_token_esperado("IP_ADDRESS")  # Construye una sugerencia aprovechando cualquier dirección parcial disponible.

            if self.posicion >= len(self.tokens):  # Comprueba si el flujo de tokens terminó inmediatamente después de IP.
                self.lanzar_error(
                    codigo="SIN-001",  # Clasifica el problema como dirección IP incompleta o mal formada.
                    mensaje=f"Error sintáctico: dirección IP incompleta o mal formada. Después de IP se esperaba IP_ADDRESS ({ejemplo_ip}), pero se llegó al fin de la entrada.",  # Explica que ningún elemento completó la dirección esperada.
                )  # Finaliza solamente el bloque actual y permite posteriormente la recuperación general.

            token = self.tokens[self.posicion]  # Recupera el elemento que apareció donde debía existir IP_ADDRESS.
            self.lanzar_error(
                codigo="SIN-001",  # Mantiene la misma clasificación porque el problema continúa perteneciendo a la dirección esperada.
                mensaje=f"Error sintáctico: dirección IP incompleta o mal formada. Después de IP se esperaba IP_ADDRESS ({ejemplo_ip}), pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, posición {token.columna}.",  # Compara lo esperado con el elemento realmente encontrado.
                token=token,  # Relaciona el diagnóstico con la ubicación exacta del fragmento incorrecto.
            )  # Abandona la instrucción actual mediante la excepción interna controlada.

        direccion_ip = self.esperar("IP_ADDRESS")  # Consume la dirección IPv4 completa y conserva su representación textual.
        self.esperar("MASK")  # Exige que inmediatamente después aparezca la palabra reservada MASK.
        mascara_subred = self.esperar("SUBNET_MASK")  # Consume la máscara CIDR que sigue a MASK.
        self.esperar("HOSTS")  # Exige la sección obligatoria donde se escribirán las cantidades solicitadas.

        if self.posicion >= len(self.tokens) or self.tokens[self.posicion].tipo != "NUMBER":  # Comprueba que HOSTS posea al menos una cantidad numérica.
            if self.posicion >= len(self.tokens):  # Comprueba si la instrucción terminó sin proporcionar ningún NUMBER.
                self.lanzar_error(
                    codigo="SIN-004",  # Clasifica específicamente la ausencia de cantidad después de HOSTS.
                    mensaje="Error sintáctico: después de HOSTS se esperaba al menos un NUMBER con la cantidad de hosts, por ejemplo 50, pero se llegó al fin de la entrada.",  # Explica el elemento mínimo requerido por la lista.
                )  # Finaliza el bloque porque una lista HOSTS vacía no cumple la gramática.

            token = self.tokens[self.posicion]  # Obtiene el elemento que apareció inmediatamente después de HOSTS.
            self.lanzar_error(
                codigo="SIN-004",  # Identifica que la sección carece de la primera cantidad válida.
                mensaje=f"Error sintáctico: después de HOSTS se esperaba al menos un NUMBER con la cantidad de hosts, por ejemplo 50, pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, posición {token.columna}.",  # Explica el token inesperado encontrado.
                token=token,  # Permite señalar directamente el elemento ubicado donde debía existir una cantidad.
            )  # Abandona este bloque para que el flujo pueda intentar recuperar otro posterior.

        cantidades_hosts = self.analizar_hosts()  # Procesa el primer NUMBER y todas las continuaciones COMMA NUMBER posibles.
        nombre = None  # Considera inicialmente ausente la sección opcional NAME.

        if self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo == "NAME":  # Comprueba si la instrucción utiliza también el componente opcional de nombre.
            token_name = self.tokens[self.posicion]  # Conserva NAME para poder señalarlo si quedó incompleto.
            self.posicion += 1  # Consume la palabra reservada antes de comprobar su identificador.

            if self.posicion >= len(self.tokens):  # Comprueba si la entrada terminó inmediatamente después de NAME.
                self.lanzar_error(
                    codigo="SIN-006",  # Clasifica el problema como nombre de red incompleto.
                    mensaje=f"Error sintáctico: después de NAME se esperaba IDENTIFIER con el nombre de la red, pero se llegó al fin de la entrada en línea {token_name.linea}, posición {token_name.columna}.",  # Explica que la sección opcional fue iniciada pero no terminada.
                    token=token_name,  # Señala la propia palabra NAME como origen de la construcción incompleta.
                )  # Abandona el bloque porque NAME deja de ser opcional una vez que fue escrito.

            token = self.tokens[self.posicion]  # Recupera el token situado inmediatamente después de NAME.

            if token.tipo == "IP" and token.linea > token_name.linea:  # Detecta el comienzo de otra instrucción antes de haber recibido el identificador pendiente.
                self.lanzar_error(
                    codigo="SIN-006",  # Mantiene la clasificación de nombre de red incompleto.
                    mensaje=f"Error sintáctico: después de NAME se esperaba IDENTIFIER con el nombre de la red, pero la instrucción terminó sin indicar el nombre antes de iniciar otra instrucción en línea {token.linea}, posición {token.columna}.",  # Explica que una nueva línea comenzó antes de completar NAME.
                    token=token_name,  # Señala NAME porque es el elemento que quedó esperando un identificador.
                )  # Permite que modo pánico conserve posteriormente la nueva IP como punto de recuperación.

            if token.tipo != "IDENTIFIER":  # Comprueba que cualquier otro token sea rechazado como continuación de NAME.
                self.lanzar_error(
                    codigo="SIN-006",  # Identifica nuevamente una sección NAME que no contiene un identificador válido.
                    mensaje=f"Error sintáctico: después de NAME se esperaba IDENTIFIER con el nombre de la red, pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, posición {token.columna}.",  # Compara el elemento esperado con el encontrado.
                    token=token,  # Relaciona el diagnóstico con el elemento incorrecto que ocupa esa posición.
                )  # Finaliza el bloque sin aceptar una sección NAME mal formada.

            nombre = token.valor  # Conserva el identificador reconocido como nombre opcional del bloque.
            self.posicion += 1  # Consume el IDENTIFIER antes de devolver la instrucción completamente reconocida.

        return BloqueRed(
            direccion_ip=direccion_ip,  # Conserva la dirección reconocida durante esta producción.
            mascara_subred=mascara_subred,  # Conserva la máscara CIDR aceptada sintácticamente.
            cantidades_hosts=cantidades_hosts,  # Conserva la lista completa obtenida después de HOSTS.
            nombre=nombre,  # Conserva el identificador opcional o None cuando NAME no fue utilizado.
            linea_origen=linea_origen,  # Conserva la línea donde comenzó la instrucción dentro del código fuente.
        )  # Construye la representación que posteriormente será enviada al análisis semántico.

    def analizar_hosts(self) -> list[int]:  # Reconoce L → NUMBER C y las repeticiones C → COMMA NUMBER C.
        cantidades = []  # Prepara la colección donde se almacenarán todas las cantidades reconocidas.
        token = self.tokens[self.posicion]  # Obtiene el primer NUMBER cuya presencia ya fue comprobada por analizar_bloque.
        cantidades.append(int(token.valor))  # Convierte el texto numérico y conserva la primera solicitud.
        self.posicion += 1  # Consume el primer NUMBER para continuar con posibles comas posteriores.

        while self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo == "COMMA":  # Continúa mientras la producción C comience con otra coma.
            token_coma = self.tokens[self.posicion]  # Conserva el separador actual para poder ubicar una lista incompleta.
            self.posicion += 1  # Consume la coma antes de comprobar el elemento obligatorio que debe seguirla.

            if self.posicion >= len(self.tokens):  # Comprueba si la entrada terminó inmediatamente después del separador.
                self.diagnosticos.append(
                    crear_diagnostico(
                        codigo="SIN-005",  # Clasifica el problema como lista de HOSTS mal formada.
                        mensaje=f"Error sintáctico: después de la coma se esperaba NUMBER con otra cantidad de hosts, pero no hay más tokens en línea {token_coma.linea}, posición {token_coma.columna}.",  # Explica que la coma quedó sin una cantidad posterior.
                        linea=token_coma.linea,  # Ubica el error en la misma línea del separador incompleto.
                        columna=token_coma.columna,  # Señala exactamente la posición de la coma.
                        longitud=len(token_coma.valor),  # Utiliza la longitud del separador como área de resaltado.
                        fragmento=token_coma.valor,  # Conserva la coma que produjo el problema.
                    )
                )  # Registra el error local sin activar todavía el modo pánico global.
                return cantidades  # Conserva las cantidades correctas reconocidas antes del punto donde falló la lista.

            token = self.tokens[self.posicion]  # Recupera el elemento situado inmediatamente después de la coma.

            if token.tipo != "NUMBER":  # Comprueba si apareció cualquier elemento diferente de la cantidad requerida.
                self.diagnosticos.append(
                    crear_diagnostico(
                        codigo="SIN-005",  # Mantiene la clasificación correspondiente con una continuación inválida de HOSTS.
                        mensaje=f"Error sintáctico: después de la coma se esperaba NUMBER con otra cantidad de hosts, pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, posición {token.columna}.",  # Explica qué token interrumpió la lista.
                        linea=token.linea,  # Relaciona el error con la línea donde apareció el elemento inesperado.
                        columna=token.columna,  # Utiliza la columna exacta del token incorrecto.
                        longitud=len(token.valor),  # Permite resaltar completamente el elemento encontrado.
                        fragmento=token.valor,  # Conserva el contenido concreto que apareció después de la coma.
                    )
                )  # Registra SIN-005 como error recuperable dentro de la lista actual.

                while self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo not in ("NUMBER", "NAME", "IP"):  # Descarta elementos hasta encontrar un punto donde pueda retomarse el análisis con seguridad.
                    self.posicion += 1  # Consume cada token que no sirve como cantidad recuperada ni como límite de la instrucción.

                if self.posicion < len(self.tokens) and self.tokens[self.posicion].tipo == "NUMBER":  # Comprueba si la recuperación local logró encontrar una cantidad posterior.
                    cantidades.append(int(self.tokens[self.posicion].valor))  # Conserva el NUMBER recuperado para seguir reconstruyendo la lista.
                    self.posicion += 1  # Consume la cantidad encontrada durante la recuperación.
                    continue  # Regresa al ciclo para comprobar si todavía existen otras comas.

                return cantidades  # Termina la lista cuando la recuperación alcanza NAME, una nueva IP o el final.

            cantidades.append(int(token.valor))  # Conserva normalmente la cantidad situada después de una coma correcta.
            self.posicion += 1  # Consume el NUMBER que acaba de incorporarse a la lista.

        return cantidades  # Devuelve todas las cantidades reconocidas antes de continuar con NAME o con otra instrucción.

    def esperar(self, tipo_esperado: str) -> str:  # Comprueba y consume un token obligatorio perteneciente a la producción actual.
        if self.posicion < len(self.tokens):  # Comprueba si todavía existe algún elemento disponible para comparar.
            token = self.tokens[self.posicion]  # Obtiene el token situado en la posición actual del parser.

            if token.tipo == tipo_esperado:  # Comprueba si la categoría coincide exactamente con la exigida por la gramática.
                self.posicion += 1  # Consume el token aceptado y mueve el cursor hacia el siguiente elemento.
                return token.valor  # Devuelve su representación textual para construir posteriormente BloqueRed.

            descripcion = self.describir_token_esperado(tipo_esperado, token)  # Construye una explicación o ejemplo útil del elemento que faltaba.
            codigo = self.codigo_token_esperado(tipo_esperado)  # Selecciona el código SIN específico correspondiente con esa ausencia.
            self.lanzar_error(
                codigo=codigo,  # Utiliza el diagnóstico relacionado con el tipo que debía aparecer.
                mensaje=f"Error sintáctico: se esperaba {tipo_esperado} ({descripcion}), pero se encontró {token.tipo} ('{token.valor}') en línea {token.linea}, posición {token.columna}.",  # Explica simultáneamente lo esperado y lo realmente encontrado.
                token=token,  # Relaciona el diagnóstico con la posición exacta del elemento inesperado.
            )  # Abandona el bloque actual para permitir la recuperación general.

        descripcion = self.describir_token_esperado(tipo_esperado)  # Obtiene una descripción aunque ya no exista ningún token actual.
        codigo = self.codigo_token_esperado(tipo_esperado)  # Obtiene el diagnóstico correspondiente con el elemento ausente.
        self.lanzar_error(
            codigo=codigo,  # Utiliza la clasificación específica de la parte de la gramática que quedó incompleta.
            mensaje=f"Error sintáctico: se esperaba {tipo_esperado} ({descripcion}), pero no hay más tokens.",  # Explica que la entrada terminó antes de completar la producción.
        )  # Genera una ubicación aproximada utilizando el último token procesado.

    def describir_token_esperado(self, tipo_esperado: str, token_actual: Token | None = None) -> str:  # Produce una descripción legible y, cuando es posible, un ejemplo basado en lo escrito.
        if tipo_esperado == "SUBNET_MASK" and token_actual is not None and token_actual.tipo == "NUMBER":  # Detecta una máscara posiblemente escrita sin su diagonal.
            return f"máscara CIDR, por ejemplo /{token_actual.valor}"  # Aprovecha el número proporcionado para sugerir la forma correcta.

        if tipo_esperado == "IP_ADDRESS":  # Aplica una reconstrucción especial cuando la entrada contiene partes de una IPv4 incompleta.
            partes = []  # Reunirá temporalmente NUMBER y DOT consecutivos sin alterar la posición real del parser.
            indice = self.posicion  # Utiliza un índice auxiliar para inspeccionar los tokens pendientes.

            while indice < len(self.tokens) and self.tokens[indice].tipo in ("NUMBER", "DOT"):  # Recupera únicamente fragmentos que podrían pertenecer a una IP parcial.
                partes.append(self.tokens[indice].valor)  # Conserva el texto original de cada número o punto.
                indice += 1  # Avanza solamente el cursor auxiliar utilizado para construir la sugerencia.

            ip_parcial = "".join(partes)  # Reconstruye el fragmento escrito originalmente a partir de los tokens disponibles.

            if ip_parcial:  # Comprueba si realmente existe información parcial que pueda aprovecharse.
                if ip_parcial.endswith("."):  # Detecta el caso donde la dirección termina justo después de un separador.
                    ip_parcial += "0"  # Agrega un valor únicamente para formar un ejemplo comprensible sin modificar el código real.

                while ip_parcial.count(".") < 3:  # Comprueba si todavía faltan separadores para llegar a cuatro octetos.
                    ip_parcial += ".0"  # Completa el ejemplo con octetos cero hasta obtener una forma IPv4 completa.

                octetos = ip_parcial.split(".")  # Divide la dirección reconstruida para validar cada componente del ejemplo.

                while len(octetos) < 4:  # Comprueba defensivamente que existan cuatro posiciones.
                    octetos.append("0")  # Agrega componentes de respaldo únicamente a la sugerencia mostrada.

                octetos_corregidos = []  # Preparará una versión que contenga exclusivamente valores compatibles con IPv4.

                for octeto in octetos[:4]:  # Revisa únicamente los cuatro primeros componentes porque una IPv4 no puede contener más.
                    if octeto.isdigit() and 0 <= int(octeto) <= 255:  # Comprueba que el componente sea numérico y permanezca dentro del rango permitido.
                        octetos_corregidos.append(octeto)  # Conserva el valor original cuando todavía resulta válido.
                    else:  # Atiende cualquier componente que no pueda formar parte de una IPv4 correcta.
                        octetos_corregidos.append("0")  # Sustituye el elemento únicamente dentro del ejemplo generado por el mensaje.

                return "dirección IP completa, por ejemplo " + ".".join(octetos_corregidos)  # Devuelve una sugerencia basada en la dirección parcial del usuario.

            return "dirección IP completa, por ejemplo 192.168.1.0"  # Utiliza un ejemplo general cuando no existe ningún fragmento aprovechable.

        return DESCRIPCIONES_TOKEN.get(tipo_esperado, tipo_esperado)  # Devuelve la descripción registrada o conserva el nombre técnico como respaldo.

    def codigo_token_esperado(self, tipo_esperado: str) -> str:  # Relaciona cada elemento obligatorio con su diagnóstico sintáctico correspondiente.
        codigos = {
            "IP_ADDRESS": "SIN-001",  # Relaciona una dirección faltante o incorrecta con SIN-001.
            "MASK": "SIN-002",  # Relaciona la ausencia de MASK con SIN-002.
            "SUBNET_MASK": "SIN-003",  # Relaciona la ausencia de una máscara CIDR con SIN-003.
            "NUMBER": "SIN-004",  # Relaciona una cantidad requerida después de HOSTS con SIN-004.
            "IDENTIFIER": "SIN-006",  # Relaciona un identificador requerido después de NAME con SIN-006.
        }  # Mantiene centralizada la selección de diagnósticos utilizada por esperar.

        return codigos.get(tipo_esperado, "SIN-008")  # Utiliza SIN-008 como respaldo cuando existen tokens pero su orden no corresponde con ninguna ausencia específica.

    def lanzar_error(self, codigo: str, mensaje: str, token: Token | None = None) -> None:  # Construye un diagnóstico y finaliza solamente la instrucción sintáctica actual.
        if token is not None:  # Comprueba si existe un elemento concreto que pueda señalarse directamente.
            diagnostico = crear_diagnostico(
                codigo=codigo,  # Conserva el identificador seleccionado por la regla que encontró el problema.
                mensaje=mensaje,  # Conserva la explicación específica construida por el parser.
                linea=token.linea,  # Utiliza la línea exacta donde se encuentra el token relacionado.
                columna=token.columna,  # Utiliza su posición horizontal original.
                longitud=len(token.valor),  # Resalta la extensión completa del elemento problemático.
                fragmento=token.valor,  # Conserva exactamente el contenido encontrado.
            )  # Construye un error con ubicación precisa dentro del código fuente.
        else:  # Atiende principalmente elementos obligatorios que faltan al final de la entrada.
            linea = None  # Parte sin una línea conocida cuando no existe un token actual.
            columna = None  # Parte sin una posición horizontal conocida.

            if self.posicion > 0 and self.posicion - 1 < len(self.tokens):  # Comprueba si existe un token anterior con el cual aproximar la posición faltante.
                token_anterior = self.tokens[self.posicion - 1]  # Recupera el último elemento que sí fue procesado correctamente.
                linea = token_anterior.linea  # Sitúa el problema sobre la misma línea del último token disponible.
                columna = token_anterior.columna + len(token_anterior.valor)  # Coloca la marca inmediatamente después del final de ese elemento.

            diagnostico = crear_diagnostico(
                codigo=codigo,  # Conserva el código correspondiente con el elemento que no llegó a aparecer.
                mensaje=mensaje,  # Conserva la explicación preparada por la regla sintáctica.
                linea=linea,  # Utiliza la línea aproximada cuando pudo calcularse.
                columna=columna,  # Utiliza la posición situada después del último token válido.
                longitud=1,  # Mantiene al menos un carácter como área mínima de resaltado.
                fragmento="",  # No inventa ningún contenido cuando realmente no existe un token incorrecto.
            )  # Construye un diagnóstico utilizable aun ante un fin inesperado de la entrada.

        raise ErrorSintacticoInterno(diagnostico)  # Transporta el diagnóstico hacia analizar para activar posteriormente la recuperación por modo pánico.

    def crear_nodo_token(self, tipo_token: str, valor: str) -> NodoSintactico:  # Construye la representación utilizada para un token dentro del árbol sintáctico.
        nodo_valor = NodoSintactico(etiqueta="VALOR", valor=str(valor))  # Crea primero un nodo terminal que contiene el texto concreto reconocido.
        return NodoSintactico(etiqueta=tipo_token, hijos=[nodo_valor])  # Envuelve el valor dentro de un nodo cuyo nombre representa la categoría léxica.

    def construir_arbol_bloque(self, bloque: BloqueRed) -> NodoSintactico:  # Construye el árbol correspondiente con una instrucción previamente validada.
        hijos = []  # Reunirá en orden todas las partes obligatorias y opcionales del bloque.
        hijos.append(self.crear_nodo_token("IP", "IP"))  # Agrega la palabra reservada inicial.
        hijos.append(self.crear_nodo_token("IP_ADDRESS", bloque.direccion_ip))  # Agrega la dirección IPv4 reconocida.
        hijos.append(self.crear_nodo_token("MASK", "MASK"))  # Agrega la palabra que introduce la máscara.
        hijos.append(self.crear_nodo_token("SUBNET_MASK", bloque.mascara_subred))  # Agrega la máscara CIDR real.
        hijos.append(self.crear_nodo_token("HOSTS", "HOSTS"))  # Agrega la palabra que introduce la lista de cantidades.
        hijos_hosts = []  # Reunirá NUMBER y COMMA dentro de un nodo agrupador HOSTS_LIST.

        for indice, cantidad in enumerate(bloque.cantidades_hosts):  # Recorre todas las cantidades conservando su posición original.
            if indice > 0:  # Comprueba si la cantidad actual debe estar precedida por un separador.
                hijos_hosts.append(self.crear_nodo_token("COMMA", ","))  # Representa explícitamente la coma utilizada dentro de la lista.

            hijos_hosts.append(self.crear_nodo_token("NUMBER", str(cantidad)))  # Agrega la cantidad actual mediante su nodo NUMBER.

        hijos.append(NodoSintactico(etiqueta="HOSTS_LIST", hijos=hijos_hosts))  # Agrupa la secuencia completa como una sola parte sintáctica de la instrucción.

        if bloque.nombre is not None:  # Comprueba si la sección opcional NAME estuvo presente.
            hijos.append(self.crear_nodo_token("NAME", "NAME"))  # Representa la palabra reservada utilizada.
            hijos.append(self.crear_nodo_token("IDENTIFIER", bloque.nombre))  # Representa el identificador concreto asignado a la red.

        etiqueta_raiz = f"BloqueRed: {bloque.nombre}" if bloque.nombre else "BloqueRed"  # Añade el nombre a la raíz solamente cuando existe para facilitar su identificación.
        return NodoSintactico(etiqueta=etiqueta_raiz, hijos=hijos)  # Devuelve la estructura completa correspondiente con el bloque.

    def obtener_gramatica_base(self) -> str:  # Devuelve la gramática utilizada para reconocer programas compuestos por uno o más bloques.
        return (
            "=== GRAMÁTICA BASE ===\n\n"  # Introduce la sección donde se muestran formalmente las producciones.
            "S → B A\n"  # Define que un programa comienza necesariamente con un bloque.
            "A → B A | ε\n"  # Permite continuar con más bloques o terminar mediante epsilon.
            "B → IP IP_ADDRESS MASK SUBNET_MASK HOSTS L N\n"  # Define la estructura completa de una instrucción de red.
            "L → NUMBER C\n"  # Exige al menos una cantidad después de HOSTS.
            "C → COMMA NUMBER C | ε\n"  # Permite cantidades adicionales separadas por comas.
            "N → NAME IDENTIFIER | ε\n\n"  # Define NAME como una sección completamente opcional.
            "S = Programa completo\n"  # Describe el significado del símbolo inicial.
            "A = Continuación del programa\n"  # Describe el no terminal encargado de bloques posteriores.
            "B = Bloque o instrucción de red\n"  # Describe la producción principal de cada instrucción.
            "L = Lista de hosts\n"  # Describe el comienzo obligatorio de HOSTS.
            "C = Continuación de la lista de hosts\n"  # Describe las cantidades adicionales.
            "N = Nombre opcional\n"  # Describe la sección final opcional.
        )  # Entrega la gramática como texto para mostrarla directamente desde la interfaz o los reportes.

    def generar_producciones_usadas(self, bloques: list[BloqueRed]) -> str:  # Describe cuáles producciones fueron necesarias para construir los bloques realmente aceptados.
        salida = self.obtener_gramatica_base()  # Comienza mostrando la gramática completa antes de señalar reglas utilizadas.
        salida += "\n=== PRODUCCIONES USADAS EN LA ENTRADA ===\n\n"  # Abre una segunda sección dedicada al código procesado.

        if not bloques:  # Comprueba si ninguna instrucción logró superar el análisis sintáctico.
            return salida + "No hay bloques válidos para mostrar producciones usadas.\n"  # Explica por qué no existen producciones aplicadas que puedan mostrarse.

        total_bloques = len(bloques)  # Obtiene cuántas instrucciones válidas forman el programa.
        salida += "Producciones del programa completo:\n"  # Introduce primero las reglas pertenecientes a S y A.
        salida += "S → B A\n"  # Registra la producción utilizada obligatoriamente al comenzar cualquier programa.

        if total_bloques > 1:  # Comprueba si A tuvo que expandirse para admitir bloques adicionales.
            salida += f"A → B A    ({total_bloques - 1} vez/veces para continuar con más instrucciones)\n"  # Indica cuántas continuaciones fueron necesarias.

        salida += "A → ε      (termina el programa)\n\n"  # Registra la producción que finalmente cierra la secuencia de bloques.

        for indice, bloque in enumerate(bloques, start=1):  # Recorre cada instrucción válida para describir sus producciones internas.
            hosts_texto = ",".join(map(str, bloque.cantidades_hosts))  # Reconstruye la lista HOSTS utilizando la forma terminal del lenguaje.
            entrada = f"IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_texto}"  # Reconstruye primero toda la sección obligatoria.
            entrada += f" NAME {bloque.nombre}" if bloque.nombre else ""  # Añade la parte opcional únicamente cuando realmente estuvo presente.
            salida += f"--- Bloque {indice} ---\n"  # Separa e identifica las reglas correspondientes con esta instrucción.
            salida += f"Entrada equivalente: {entrada}\n\n"  # Muestra la cadena terminal representada por el bloque.
            salida += "B → IP IP_ADDRESS MASK SUBNET_MASK HOSTS L N\n"  # Registra la expansión principal utilizada por B.
            salida += "L → NUMBER C\n"  # Registra el comienzo obligatorio de la lista.
            hosts_adicionales = max(len(bloque.cantidades_hosts) - 1, 0)  # Calcula cuántas veces C tuvo que producir una coma y otra cantidad.

            if hosts_adicionales > 0:  # Comprueba si existieron solicitudes posteriores al primer NUMBER.
                salida += f"C → COMMA NUMBER C    ({hosts_adicionales} vez/veces)\n"  # Informa cuántas expansiones fueron necesarias.

            salida += "C → ε\n"  # Registra finalmente la producción que termina la lista HOSTS.
            salida += "N → NAME IDENTIFIER\n\n" if bloque.nombre else "N → ε\n\n"  # Indica si N produjo la sección NAME o terminó mediante epsilon.

        return salida  # Devuelve la gramática y todas las producciones correspondientes con la entrada procesada.

    def generar_derivacion(self, bloques: list[BloqueRed]) -> str:  # Construye primero la derivación general del programa y luego la de cada instrucción.
        salida = "=== DERIVACIÓN GENERADA ===\n\n"  # Introduce el apartado destinado a mostrar las sustituciones formales.

        if not bloques:  # Comprueba si no existe ningún bloque válido desde el cual construir una derivación.
            return salida + "No hay bloques válidos para generar derivación.\n"  # Evita inventar sustituciones cuando ninguna instrucción fue aceptada.

        total_bloques = len(bloques)  # Obtiene la cantidad de símbolos B que deberá producir finalmente el programa.
        salida += "Derivación general del programa:\n\nS\n⇒ B A\n"  # Comienza desde S y aplica la producción inicial.

        if total_bloques == 1:  # Comprueba si solamente se necesita una instrucción.
            salida += "⇒ B ε\n⇒ B\n"  # Sustituye inmediatamente A por epsilon y muestra la forma sin el símbolo vacío.
        else:  # Atiende programas formados por dos o más bloques.
            for cantidad in range(2, total_bloques + 1):  # Expande A tantas veces como bloques adicionales sean necesarios.
                forma = (("B " * cantidad) + "A").strip()  # Construye la forma sentencial correspondiente con la expansión actual.
                salida += f"⇒ {forma}\n"  # Agrega la nueva forma al historial de derivación.

            bloques_texto = ("B " * total_bloques).strip()  # Construye la secuencia final formada por todos los bloques requeridos.
            salida += f"⇒ {bloques_texto} ε\n⇒ {bloques_texto}\n"  # Sustituye la última A por epsilon y posteriormente elimina visualmente ε.

        salida += "\n"  # Separa la derivación general de las derivaciones internas de cada bloque.

        for indice, bloque in enumerate(bloques, start=1):  # Recorre cada instrucción aceptada respetando su orden original.
            salida += self.generar_derivacion_bloque(bloque, indice)  # Agrega todas las sustituciones correspondientes con B, L, C y N.
            salida += "\n"  # Deja una separación visible antes del siguiente bloque.

        return salida  # Devuelve la derivación completa de todo el programa reconocido.

    def generar_derivacion_bloque(self, bloque: BloqueRed, indice: int) -> str:  # Construye una derivación izquierda sustituyendo los valores reales de una instrucción.
        salida = f"--- Derivación del bloque {indice} ---\n\n"  # Identifica el bloque que será desarrollado a partir del no terminal B.

        if not bloque.cantidades_hosts:  # Mantiene una protección defensiva ante un bloque que inesperadamente carezca de HOSTS.
            return salida + "No hay hosts para derivar.\n"  # Finaliza sin intentar acceder a una primera cantidad inexistente.

        hosts_actuales = str(bloque.cantidades_hosts[0])  # Conserva la primera cantidad que sustituirá inicialmente NUMBER.
        salida += "B\n"  # Comienza la derivación específica desde el símbolo de bloque.
        salida += "⇒ IP IP_ADDRESS MASK SUBNET_MASK HOSTS L N\n"  # Expande B mediante la producción principal.
        salida += f"⇒ IP {bloque.direccion_ip} MASK SUBNET_MASK HOSTS L N\n"  # Sustituye el terminal variable correspondiente con IP_ADDRESS.
        salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS L N\n"  # Sustituye posteriormente SUBNET_MASK.
        salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS NUMBER C N\n"  # Expande L para introducir la lista de cantidades.
        salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} C N\n"  # Sustituye NUMBER por la primera cantidad real.

        for host in bloque.cantidades_hosts[1:]:  # Recorre únicamente las solicitudes adicionales existentes después de la primera.
            salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} COMMA NUMBER C N\n"  # Expande C para introducir otra coma y otro NUMBER.
            hosts_actuales += f",{host}"  # Incorpora la nueva cantidad a la porción terminal ya sustituida.
            salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} C N\n"  # Sustituye COMMA y NUMBER por sus representaciones reales.

        salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} ε N\n"  # Termina la continuación de HOSTS aplicando C → ε.
        salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} N\n"  # Elimina visualmente epsilon para continuar solamente con N.

        if bloque.nombre:  # Comprueba si la cadena terminal final debe incluir también la sección opcional NAME.
            salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} NAME IDENTIFIER\n"  # Expande N utilizando la alternativa que contiene nombre.
            salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} NAME {bloque.nombre}\n"  # Sustituye IDENTIFIER por el nombre real de la red.
        else:  # Atiende los bloques donde el componente opcional no fue utilizado.
            salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} ε\n"  # Termina N mediante la producción vacía.
            salida += f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales}\n"  # Elimina epsilon y deja solamente la cadena terminal completa.

        return salida  # Devuelve todas las formas sentenciales correspondientes con el bloque actual.

    def generar_arbol_textual(self, arboles: list[NodoSintactico]) -> str:  # Convierte todos los árboles estructurados en una representación legible mediante caracteres de ramas.
        if not arboles:  # Comprueba si ninguna instrucción válida produjo un árbol.
            return "No hay árboles válidos para mostrar.\n"  # Devuelve un mensaje explícito en lugar de una sección vacía.

        salida = "=== REPRESENTACIÓN TEXTUAL DEL ÁRBOL SINTÁCTICO ===\n\n"  # Introduce la sección dedicada a la visualización de los árboles.

        for indice, arbol in enumerate(arboles, start=1):  # Recorre las estructuras en el mismo orden que sus bloques correspondientes.
            salida += f"--- Árbol {indice} ---\n"  # Identifica individualmente el árbol que se mostrará.
            salida += self.formatear_nodo_arbol(arbol)  # Convierte recursivamente el nodo raíz y todos sus descendientes.
            salida += "\n"  # Separa visualmente este árbol del siguiente.

        return salida  # Devuelve todas las representaciones unidas dentro de un único texto.

    def formatear_nodo_arbol(self, nodo: NodoSintactico, prefijo: str = "", es_ultimo: bool = True) -> str:  # Recorre recursivamente un nodo y conserva la alineación gráfica de sus ramas.
        etiqueta = str(nodo.valor) if nodo.etiqueta == "VALOR" else nodo.etiqueta  # Muestra directamente el contenido cuando se alcanzó un nodo terminal VALOR.
        conector = "└── " if es_ultimo else "├── "  # Selecciona el símbolo adecuado según exista o no otro hermano posteriormente.
        salida = prefijo + conector + etiqueta + "\n"  # Construye la línea correspondiente con el nodo actual.
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")  # Conserva visualmente las ramas verticales necesarias para sus descendientes.

        for indice, hijo in enumerate(nodo.hijos):  # Recorre todos los hijos manteniendo el orden estructural del árbol.
            hijo_es_ultimo = indice == len(nodo.hijos) - 1  # Determina si el descendiente actual ocupa la última posición de su nivel.
            salida += self.formatear_nodo_arbol(hijo, nuevo_prefijo, hijo_es_ultimo)  # Agrega recursivamente todo el subárbol correspondiente.

        return salida  # Devuelve la representación completa del nodo actual y todos sus descendientes.