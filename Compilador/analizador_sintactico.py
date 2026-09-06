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
# previamente por el analizador léxico y comprueba que dichos
# tokens aparezcan en el orden establecido por la gramática.
#
# La estructura general aceptada es:
#
# IP <IP_ADDRESS> MASK <SUBNET_MASK>
# HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]
#
# El analizador también conserva mecanismos existentes desde
# Lenguajes y Autómatas I, como:
#
# - Detección de instrucciones duplicadas.
# - Recuperación local dentro de la lista de hosts.
# - Modo pánico para continuar después de errores.
# - Procesamiento de instrucciones válidas aunque otras fallen.
#
# Este archivo no realiza todavía validaciones semánticas.
# ============================================================


# Importa la estructura Diagnostico para poder transportar
# internamente un error sintáctico con todos sus datos.
#
# También importa crear_diagnostico para generar los errores
# estructurados que posteriormente utilizará la interfaz.
from Motor.diagnosticos import Diagnostico, crear_diagnostico


# Importa los modelos utilizados por el analizador sintáctico.
#
# BloqueRed representa una instrucción sintácticamente correcta.
# ResultadoSintactico representa el resultado completo de esta fase.
# Token representa cada elemento previamente reconocido por el lexer.
from Motor.modelos import BloqueRed, ResultadoSintactico, Token


# Define descripciones más fáciles de entender para los diferentes
# tipos de token utilizados por TecNet Finder.
#
# Estas descripciones se utilizan principalmente para construir
# mensajes de error sintáctico más claros.
DESCRIPCIONES_TOKEN = {

    # Describe la palabra reservada IP.
    "IP": "palabra reservada IP",

    # Describe la palabra reservada MASK.
    "MASK": "palabra reservada MASK",

    # Describe la palabra reservada HOSTS.
    "HOSTS": "palabra reservada HOSTS",

    # Describe la palabra reservada NAME.
    "NAME": "palabra reservada NAME",

    # Describe una dirección IPv4 completa.
    "IP_ADDRESS": "dirección IP completa",

    # Describe una máscara escrita en formato CIDR.
    "SUBNET_MASK": "máscara CIDR",

    # Describe un número entero.
    "NUMBER": "número entero",

    # Describe un identificador utilizado como nombre de red.
    "IDENTIFIER": "identificador o nombre de red",

    # Describe una coma utilizada dentro de la lista de hosts.
    "COMMA": "coma separadora",

    # Describe un punto individual.
    "DOT": "punto",
}


# Define una excepción utilizada únicamente de manera interna
# por el analizador sintáctico.
#
# Su propósito es detener el análisis del bloque actual cuando
# aparece un error que impide continuar con esa instrucción.
#
# El error no termina todo el programa porque posteriormente
# el modo pánico intentará encontrar la siguiente instrucción.
class ErrorSintacticoInterno(Exception):

    # Inicializa la excepción utilizando un diagnóstico estructurado.
    def __init__(self, diagnostico: Diagnostico):

        # Guarda el diagnóstico para que pueda recuperarse cuando
        # la excepción sea capturada por el método analizar.
        self.diagnostico = diagnostico

        # Inicializa también la clase Exception de Python utilizando
        # el mensaje descriptivo del diagnóstico.
        super().__init__(diagnostico.mensaje)


# Define la clase responsable de realizar el análisis sintáctico.
class AnalizadorSintactico:

    # Inicializa el analizador utilizando la lista de tokens
    # previamente producida por el analizador léxico.
    def __init__(self, tokens: list[Token]):

        # Guarda la secuencia completa de tokens que será analizada.
        self.tokens = tokens

        # Indica la posición del token que se está revisando actualmente.
        self.posicion = 0

        # Crea la lista donde se almacenarán todos los diagnósticos
        # sintácticos encontrados durante el análisis.
        self.diagnosticos: list[Diagnostico] = []

    # Procesa toda la secuencia de tokens y devuelve únicamente
    # los bloques que cumplen correctamente la gramática.
    def analizar(self) -> ResultadoSintactico:

        # Crea la lista que almacenará las instrucciones válidas.
        bloques: list[BloqueRed] = []

        # Crea un conjunto utilizado para recordar las instrucciones
        # válidas que ya aparecieron anteriormente.
        #
        # Esto permite detectar bloques exactamente duplicados.
        bloques_vistos = set()

        # Continúa mientras todavía queden tokens sin procesar.
        while self.posicion < len(self.tokens):

            # Guarda la posición donde comienza la instrucción actual.
            #
            # Este valor será utilizado tanto para detectar duplicados
            # como para aplicar posteriormente el modo pánico.
            posicion_inicio = self.posicion

            # Intenta analizar una instrucción completa.
            try:

                # Guarda cuántos diagnósticos existían antes de entrar
                # al bloque actual.
                #
                # Esto permite saber después si ocurrió un error local
                # durante el procesamiento de la lista de hosts.
                errores_antes = len(self.diagnosticos)

                # Intenta reconocer una instrucción completa de red.
                bloque = self.analizar_bloque()

                # Comprueba si el bloque produjo algún diagnóstico
                # durante su análisis.
                bloque_tiene_errores = (
                    len(self.diagnosticos) > errores_antes
                )

                # Construye una firma con los elementos principales
                # de la instrucción.
                #
                # La lista de hosts se convierte temporalmente en tupla
                # porque una lista no puede utilizarse dentro de un set.
                firma = (
                    bloque.direccion_ip,
                    bloque.mascara_subred,
                    tuple(bloque.cantidades_hosts),
                    bloque.nombre,
                )

                # Comprueba si exactamente la misma instrucción ya
                # había sido aceptada anteriormente.
                if firma in bloques_vistos:

                    # Recupera el primer token de la instrucción duplicada
                    # para obtener su posición dentro del código fuente.
                    token_inicio = self.tokens[posicion_inicio]

                    # Agrega el diagnóstico correspondiente al duplicado.
                    self.diagnosticos.append(
                        crear_diagnostico(
                            codigo="SIN-007",
                            mensaje=(
                                f"Error sintáctico: instrucción duplicada "
                                f"en línea {token_inicio.linea}. "
                                f"La red con IP {bloque.direccion_ip}, "
                                f"máscara {bloque.mascara_subred} "
                                f"y nombre {bloque.nombre} ya fue "
                                f"declarada anteriormente."
                            ),
                            linea=token_inicio.linea,
                            columna=token_inicio.columna,
                            longitud=len(token_inicio.valor),
                            fragmento=token_inicio.valor,
                        )
                    )

                # Si el bloque no está duplicado y tampoco produjo
                # errores locales, puede considerarse sintácticamente válido.
                elif not bloque_tiene_errores:

                    # Registra la firma para detectar posibles
                    # instrucciones duplicadas posteriores.
                    bloques_vistos.add(firma)

                    # Guarda el bloque dentro de los resultados válidos.
                    bloques.append(bloque)

            # Captura un error sintáctico que impidió completar
            # normalmente la instrucción actual.
            except ErrorSintacticoInterno as error:

                # Guarda el diagnóstico transportado por la excepción.
                self.diagnosticos.append(error.diagnostico)

                # Activa el modo pánico para intentar localizar
                # el comienzo de otra instrucción.
                self.sincronizar(posicion_inicio)

            # Comprueba que el analizador realmente haya avanzado.
            #
            # Esta protección evita un ciclo infinito en caso de que
            # una condición inesperada deje la posición sin modificar.
            if self.posicion == posicion_inicio:

                # Avanza manualmente un token para poder continuar.
                self.posicion += 1

        # Devuelve todos los bloques válidos y diagnósticos encontrados.
        return ResultadoSintactico(
            bloques=bloques,
            diagnosticos=self.diagnosticos.copy(),
        )

    # Implementa el modo pánico utilizado para recuperarse de
    # errores sintácticos graves.
    #
    # En TecNet Finder una nueva instrucción normalmente comienza
    # con la palabra reservada IP.
    def sincronizar(
        self,
        posicion_inicio: int | None = None,
    ) -> None:

        # Inicializa sin información la línea donde comenzó el error.
        linea_error = None

        # Comprueba si se recibió una posición inicial válida.
        if (
            posicion_inicio is not None
            and posicion_inicio < len(self.tokens)
        ):

            # Obtiene la línea de la instrucción que produjo el error.
            linea_error = self.tokens[posicion_inicio].linea

        # Continúa avanzando mientras todavía existan tokens.
        while self.posicion < len(self.tokens):

            # Obtiene el token ubicado en la posición actual.
            token = self.tokens[self.posicion]

            # Comprueba si se encontró la palabra reservada IP.
            if token.tipo == "IP":

                # Verifica que esta IP pertenezca a una línea posterior
                # a aquella donde comenzó la instrucción incorrecta.
                if (
                    linea_error is None
                    or token.linea > linea_error
                ):

                    # Detiene la sincronización sin consumir la IP.
                    #
                    # Así el ciclo principal podrá utilizarla como
                    # comienzo de la siguiente instrucción.
                    return

            # Descarta el token actual porque todavía forma parte
            # de la sección donde ocurrió el error.
            self.posicion += 1

    # Analiza una instrucción completa según la estructura
    # definida por la gramática de TecNet Finder.
    def analizar_bloque(self) -> BloqueRed:

        # Guarda la línea donde comienza la instrucción actual.
        linea_origen = self.tokens[self.posicion].linea

        # Exige que la instrucción comience con la palabra reservada IP.
        self.esperar("IP")

        # Comprueba explícitamente que después de IP aparezca
        # una dirección IPv4 completa.
        #
        # Esta validación especial permite generar el diagnóstico
        # SIN-001 cuando una IP quedó dividida en NUMBER y DOT.
        if (
            self.posicion >= len(self.tokens)
            or self.tokens[self.posicion].tipo != "IP_ADDRESS"
        ):

            # Genera un ejemplo de cómo debería verse la dirección
            # IP que se esperaba.
            ejemplo_ip = self.describir_token_esperado(
                "IP_ADDRESS"
            )

            # Comprueba si el código terminó inmediatamente después de IP.
            if self.posicion >= len(self.tokens):

                # Genera un error indicando que faltó la dirección completa.
                self.lanzar_error(
                    codigo="SIN-001",
                    mensaje=(
                        "Error sintáctico: dirección IP incompleta "
                        "o mal formada. Después de IP se esperaba "
                        f"IP_ADDRESS ({ejemplo_ip}), pero se llegó "
                        "al fin de la entrada."
                    ),
                )

            # Obtiene el token encontrado en lugar de IP_ADDRESS.
            token = self.tokens[self.posicion]

            # Genera un diagnóstico específico para la dirección
            # incompleta o mal formada.
            self.lanzar_error(
                codigo="SIN-001",
                mensaje=(
                    "Error sintáctico: dirección IP incompleta "
                    "o mal formada. Después de IP se esperaba "
                    f"IP_ADDRESS ({ejemplo_ip}), pero se encontró "
                    f"{token.tipo} ('{token.valor}') "
                    f"en línea {token.linea}, "
                    f"posición {token.columna}."
                ),
                token=token,
            )

        # Consume la dirección IPv4 completa y guarda su valor.
        direccion_ip = self.esperar("IP_ADDRESS")

        # Exige la palabra reservada MASK.
        self.esperar("MASK")

        # Exige una máscara escrita en formato CIDR.
        mascara_subred = self.esperar("SUBNET_MASK")

        # Exige la palabra reservada HOSTS.
        self.esperar("HOSTS")

        # Comprueba que HOSTS esté seguido por al menos
        # una cantidad numérica.
        if (
            self.posicion >= len(self.tokens)
            or self.tokens[self.posicion].tipo != "NUMBER"
        ):

            # Comprueba si el código terminó inmediatamente
            # después de la palabra HOSTS.
            if self.posicion >= len(self.tokens):

                # Genera el diagnóstico correspondiente.
                self.lanzar_error(
                    codigo="SIN-004",
                    mensaje=(
                        "Error sintáctico: después de HOSTS se "
                        "esperaba al menos un NUMBER con la cantidad "
                        "de hosts, por ejemplo 50, pero se llegó al "
                        "fin de la entrada."
                    ),
                )

            # Obtiene el token incorrecto encontrado después de HOSTS.
            token = self.tokens[self.posicion]

            # Genera un diagnóstico indicando qué token apareció.
            self.lanzar_error(
                codigo="SIN-004",
                mensaje=(
                    "Error sintáctico: después de HOSTS se esperaba "
                    "al menos un NUMBER con la cantidad de hosts, "
                    f"por ejemplo 50, pero se encontró {token.tipo} "
                    f"('{token.valor}') en línea {token.linea}, "
                    f"posición {token.columna}."
                ),
                token=token,
            )

        # Procesa la primera cantidad de hosts y todos los números
        # adicionales separados mediante comas.
        cantidades_hosts = self.analizar_hosts()

        # Inicializa el nombre de la red como ausente.
        #
        # NAME es una parte opcional de la gramática.
        nombre = None

        # Comprueba si después de los hosts aparece NAME.
        if (
            self.posicion < len(self.tokens)
            and self.tokens[self.posicion].tipo == "NAME"
        ):

            # Guarda el token NAME para conservar su posición.
            token_name = self.tokens[self.posicion]

            # Consume la palabra reservada NAME.
            self.posicion += 1

            # Comprueba si la entrada terminó inmediatamente
            # después de NAME.
            if self.posicion >= len(self.tokens):

                # Genera el diagnóstico SIN-006 porque falta
                # el identificador correspondiente.
                self.lanzar_error(
                    codigo="SIN-006",
                    mensaje=(
                        "Error sintáctico: después de NAME se "
                        "esperaba IDENTIFIER con el nombre de la red, "
                        "pero se llegó al fin de la entrada "
                        f"en línea {token_name.linea}, "
                        f"posición {token_name.columna}."
                    ),
                    token=token_name,
                )

            # Obtiene el token que aparece después de NAME.
            token = self.tokens[self.posicion]

            # Comprueba si comenzó una nueva instrucción en una
            # línea posterior sin haberse indicado el nombre.
            if (
                token.tipo == "IP"
                and token.linea > token_name.linea
            ):

                # Genera el diagnóstico correspondiente al nombre faltante.
                self.lanzar_error(
                    codigo="SIN-006",
                    mensaje=(
                        "Error sintáctico: después de NAME se "
                        "esperaba IDENTIFIER con el nombre de la red, "
                        "pero la instrucción terminó sin indicar el "
                        "nombre antes de iniciar otra instrucción "
                        f"en línea {token.linea}, "
                        f"posición {token.columna}."
                    ),
                    token=token_name,
                )

            # Comprueba que el token encontrado sea realmente
            # un identificador.
            if token.tipo != "IDENTIFIER":

                # Genera SIN-006 cuando después de NAME aparece
                # cualquier otro tipo de token.
                self.lanzar_error(
                    codigo="SIN-006",
                    mensaje=(
                        "Error sintáctico: después de NAME se "
                        "esperaba IDENTIFIER con el nombre de la red, "
                        f"pero se encontró {token.tipo} "
                        f"('{token.valor}') en línea {token.linea}, "
                        f"posición {token.columna}."
                    ),
                    token=token,
                )

            # Guarda el texto del identificador como nombre de la red.
            nombre = token.valor

            # Consume el IDENTIFIER que acaba de ser procesado.
            self.posicion += 1

        # Construye y devuelve la representación organizada
        # de la instrucción sintácticamente reconocida.
        return BloqueRed(
            direccion_ip=direccion_ip,
            mascara_subred=mascara_subred,
            cantidades_hosts=cantidades_hosts,
            nombre=nombre,
            linea_origen=linea_origen,
        )

    # Procesa la lista de cantidades ubicada después de HOSTS.
    #
    # La estructura esperada es:
    #
    # NUMBER
    #
    # o:
    #
    # NUMBER , NUMBER , NUMBER ...
    def analizar_hosts(self) -> list[int]:

        # Crea la lista donde se guardarán las cantidades reconocidas.
        cantidades = []

        # Obtiene el primer NUMBER.
        #
        # analizar_bloque ya comprobó previamente que este token existe.
        token = self.tokens[self.posicion]

        # Convierte el texto numérico a entero y lo guarda.
        cantidades.append(int(token.valor))

        # Consume el primer NUMBER.
        self.posicion += 1

        # Continúa mientras el siguiente elemento sea una coma.
        while (
            self.posicion < len(self.tokens)
            and self.tokens[self.posicion].tipo == "COMMA"
        ):

            # Guarda el token COMMA para conservar su posición.
            token_coma = self.tokens[self.posicion]

            # Consume la coma.
            self.posicion += 1

            # Comprueba si la entrada terminó después de la coma.
            if self.posicion >= len(self.tokens):

                # Agrega un diagnóstico local SIN-005.
                #
                # Este error no utiliza el modo pánico inmediatamente
                # porque la lista de hosts intenta recuperarse localmente.
                self.diagnosticos.append(
                    crear_diagnostico(
                        codigo="SIN-005",
                        mensaje=(
                            "Error sintáctico: después de la coma "
                            "se esperaba NUMBER con otra cantidad "
                            "de hosts, pero no hay más tokens "
                            f"en línea {token_coma.linea}, "
                            f"posición {token_coma.columna}."
                        ),
                        linea=token_coma.linea,
                        columna=token_coma.columna,
                        longitud=len(token_coma.valor),
                        fragmento=token_coma.valor,
                    )
                )

                # Devuelve las cantidades que pudieron reconocerse
                # antes de encontrar el error.
                return cantidades

            # Obtiene el token ubicado después de la coma.
            token = self.tokens[self.posicion]

            # Comprueba si después de la coma apareció algo
            # diferente de NUMBER.
            if token.tipo != "NUMBER":

                # Guarda el diagnóstico SIN-005.
                self.diagnosticos.append(
                    crear_diagnostico(
                        codigo="SIN-005",
                        mensaje=(
                            "Error sintáctico: después de la coma "
                            "se esperaba NUMBER con otra cantidad "
                            f"de hosts, pero se encontró {token.tipo} "
                            f"('{token.valor}') en línea {token.linea}, "
                            f"posición {token.columna}."
                        ),
                        linea=token.linea,
                        columna=token.columna,
                        longitud=len(token.valor),
                        fragmento=token.valor,
                    )
                )

                # Aplica una recuperación local.
                #
                # Descarta tokens hasta encontrar:
                #
                # NUMBER -> otra cantidad de hosts.
                # NAME   -> sección opcional del nombre.
                # IP     -> posible siguiente instrucción.
                while (
                    self.posicion < len(self.tokens)
                    and self.tokens[self.posicion].tipo
                    not in ("NUMBER", "NAME", "IP")
                ):

                    # Descarta el token actual.
                    self.posicion += 1

                # Comprueba si la recuperación encontró otro NUMBER.
                if (
                    self.posicion < len(self.tokens)
                    and self.tokens[self.posicion].tipo == "NUMBER"
                ):

                    # Convierte y guarda el número recuperado.
                    cantidades.append(
                        int(self.tokens[self.posicion].valor)
                    )

                    # Consume el número recuperado.
                    self.posicion += 1

                    # Continúa revisando la lista de hosts.
                    continue

                # Si apareció NAME, IP o terminó la entrada,
                # deja de procesar la lista de hosts.
                return cantidades

            # Si el token después de la coma sí es NUMBER,
            # convierte y almacena normalmente su valor.
            cantidades.append(int(token.valor))

            # Consume el número que acaba de procesarse.
            self.posicion += 1

        # Devuelve todas las cantidades reconocidas.
        return cantidades

    # Comprueba que el token ubicado en la posición actual
    # corresponda exactamente al tipo esperado.
    def esperar(self, tipo_esperado: str) -> str:

        # Comprueba que todavía exista algún token disponible.
        if self.posicion < len(self.tokens):

            # Obtiene el token actual.
            token = self.tokens[self.posicion]

            # Comprueba si coincide con el tipo solicitado.
            if token.tipo == tipo_esperado:

                # Consume el token correcto.
                self.posicion += 1

                # Devuelve su valor textual.
                return token.valor

            # Obtiene una descripción legible del elemento esperado.
            descripcion = self.describir_token_esperado(
                tipo_esperado,
                token,
            )

            # Determina qué código de diagnóstico corresponde
            # al tipo de token que hacía falta.
            codigo = self.codigo_token_esperado(tipo_esperado)

            # Detiene el bloque actual mediante un error sintáctico
            # estructurado.
            self.lanzar_error(
                codigo=codigo,
                mensaje=(
                    f"Error sintáctico: se esperaba {tipo_esperado} "
                    f"({descripcion}), pero se encontró {token.tipo} "
                    f"('{token.valor}') en línea {token.linea}, "
                    f"posición {token.columna}."
                ),
                token=token,
            )

        # Obtiene una descripción del elemento que se esperaba
        # cuando ya no existen más tokens.
        descripcion = self.describir_token_esperado(
            tipo_esperado
        )

        # Obtiene el código correspondiente.
        codigo = self.codigo_token_esperado(tipo_esperado)

        # Genera el error indicando que terminó la entrada.
        self.lanzar_error(
            codigo=codigo,
            mensaje=(
                f"Error sintáctico: se esperaba {tipo_esperado} "
                f"({descripcion}), pero no hay más tokens."
            ),
        )

    # Genera una descripción más clara del token esperado.
    #
    # En algunos casos también intenta construir un ejemplo
    # basándose en lo que escribió el usuario.
    def describir_token_esperado(
        self,
        tipo_esperado: str,
        token_actual: Token | None = None,
    ) -> str:

        # Comprueba el caso especial de una máscara CIDR
        # escrita sin la diagonal.
        if (
            tipo_esperado == "SUBNET_MASK"
            and token_actual is not None
            and token_actual.tipo == "NUMBER"
        ):

            # Utiliza el número escrito para proponer el ejemplo
            # de máscara correspondiente.
            return (
                f"máscara CIDR, por ejemplo /{token_actual.valor}"
            )

        # Comprueba el caso especial de una dirección IPv4.
        if tipo_esperado == "IP_ADDRESS":

            # Crea una lista para reconstruir las partes de una IP
            # incompleta reconocidas por el lexer.
            partes = []

            # Comienza a revisar desde la posición actual del parser.
            indice = self.posicion

            # Reúne todos los NUMBER y DOT consecutivos.
            while (
                indice < len(self.tokens)
                and self.tokens[indice].tipo in ("NUMBER", "DOT")
            ):

                # Guarda el valor textual de la parte encontrada.
                partes.append(self.tokens[indice].valor)

                # Avanza temporalmente al siguiente token.
                indice += 1

            # Une las partes para reconstruir la dirección parcial.
            ip_parcial = "".join(partes)

            # Comprueba si realmente se encontró una IP parcial.
            if ip_parcial:

                # Si termina con punto, agrega temporalmente un cero
                # para poder construir un ejemplo completo.
                if ip_parcial.endswith("."):
                    ip_parcial += "0"

                # Agrega octetos faltantes hasta alcanzar tres puntos.
                while ip_parcial.count(".") < 3:
                    ip_parcial += ".0"

                # Divide la dirección en octetos.
                octetos = ip_parcial.split(".")

                # Completa cualquier octeto faltante adicional.
                while len(octetos) < 4:
                    octetos.append("0")

                # Crea la lista que almacenará los octetos
                # corregidos para el ejemplo.
                octetos_corregidos = []

                # Revisa únicamente los primeros cuatro octetos.
                for octeto in octetos[:4]:

                    # Comprueba que el octeto sea numérico y se
                    # encuentre dentro del rango IPv4 permitido.
                    if (
                        octeto.isdigit()
                        and 0 <= int(octeto) <= 255
                    ):

                        # Conserva el octeto válido.
                        octetos_corregidos.append(octeto)

                    # Sustituye cualquier octeto inválido por cero.
                    else:
                        octetos_corregidos.append("0")

                # Devuelve un ejemplo de dirección IPv4 completa.
                return (
                    "dirección IP completa, por ejemplo "
                    f"{'.'.join(octetos_corregidos)}"
                )

            # Devuelve un ejemplo genérico cuando no existe
            # ninguna parte aprovechable de la dirección.
            return (
                "dirección IP completa, "
                "por ejemplo 192.168.1.0"
            )

        # Busca una descripción normal dentro del catálogo local.
        #
        # Si no existe, devuelve directamente el nombre técnico
        # del tipo de token.
        return DESCRIPCIONES_TOKEN.get(
            tipo_esperado,
            tipo_esperado,
        )

    # Determina el código de diagnóstico correspondiente
    # al token que el parser esperaba encontrar.
    def codigo_token_esperado(
        self,
        tipo_esperado: str,
    ) -> str:

        # Define los errores específicos conocidos.
        codigos = {

            # Una dirección IP faltante corresponde a SIN-001.
            "IP_ADDRESS": "SIN-001",

            # La ausencia de MASK corresponde a SIN-002.
            "MASK": "SIN-002",

            # Una máscara CIDR faltante corresponde a SIN-003.
            "SUBNET_MASK": "SIN-003",

            # Un número faltante después de HOSTS corresponde
            # normalmente a SIN-004.
            "NUMBER": "SIN-004",

            # Un identificador faltante después de NAME
            # corresponde a SIN-006.
            "IDENTIFIER": "SIN-006",
        }

        # Devuelve el código específico cuando existe.
        #
        # En cualquier otro caso se utiliza SIN-008 como error
        # general de orden incorrecto de tokens.
        return codigos.get(
            tipo_esperado,
            "SIN-008",
        )

    # Construye un diagnóstico sintáctico y utiliza una excepción
    # interna para detener el procesamiento del bloque actual.
    def lanzar_error(
        self,
        codigo: str,
        mensaje: str,
        token: Token | None = None,
    ) -> None:

        # Comprueba si existe un token concreto relacionado
        # con el problema.
        if token is not None:

            # Crea el diagnóstico utilizando directamente
            # la posición y el contenido del token incorrecto.
            diagnostico = crear_diagnostico(
                codigo=codigo,
                mensaje=mensaje,
                linea=token.linea,
                columna=token.columna,
                longitud=len(token.valor),
                fragmento=token.valor,
            )

        # Si no existe un token actual, intenta localizar el
        # diagnóstico inmediatamente después del token anterior.
        else:

            # Inicializa la línea sin una posición concreta.
            linea = None

            # Inicializa también la columna.
            columna = None

            # Comprueba si existe un token anterior disponible.
            if (
                self.posicion > 0
                and self.posicion - 1 < len(self.tokens)
            ):

                # Obtiene el token procesado inmediatamente antes.
                token_anterior = self.tokens[
                    self.posicion - 1
                ]

                # Utiliza la línea del token anterior.
                linea = token_anterior.linea

                # Calcula la posición ubicada justo después
                # del final del token anterior.
                columna = (
                    token_anterior.columna
                    + len(token_anterior.valor)
                )

            # Crea el diagnóstico para el final de la entrada.
            diagnostico = crear_diagnostico(
                codigo=codigo,
                mensaje=mensaje,
                linea=linea,
                columna=columna,
                longitud=1,
                fragmento="",
            )

        # Lanza la excepción interna transportando el diagnóstico.
        #
        # El método analizar capturará posteriormente esta excepción
        # y activará la recuperación mediante modo pánico.
        raise ErrorSintacticoInterno(diagnostico)