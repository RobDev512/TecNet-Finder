# ============================================================
# Archivo: analizador_lexico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene exclusivamente la fase de análisis léxico
# del compilador de TecNet Finder.
#
# El analizador léxico recibe el código fuente escrito por el
# usuario y recorre el texto para reconocer los elementos válidos
# del lenguaje mediante expresiones regulares.
#
# Cada elemento reconocido se convierte en un Token que almacena:
#
# - Tipo.
# - Valor.
# - Línea.
# - Columna.
#
# El analizador también genera diagnósticos cuando encuentra
# símbolos, fragmentos o identificadores que no son válidos en
# la posición donde aparecen.
#
# Esta fase no valida todavía la estructura completa de una
# instrucción. Esa responsabilidad pertenece al analizador
# sintáctico.
# ============================================================


# Importa el módulo re de la biblioteca estándar de Python.
# Este módulo permite crear y utilizar expresiones regulares.
from re import compile as compilar_expresion


# Importa la función encargada de crear diagnósticos estructurados.
# De esta forma el lexer no maneja los errores solamente como texto.
from Motor.diagnosticos import crear_diagnostico


# Importa las estructuras utilizadas para representar los tokens
# reconocidos y el resultado completo del análisis léxico.
from Motor.modelos import ResultadoLexico, Token


# Define la clase encargada de realizar el análisis léxico.
class AnalizadorLexico:

    # Inicializa el analizador y prepara todas las expresiones
    # regulares que serán utilizadas para reconocer los tokens.
    def __init__(self):

        # Define la expresión regular correspondiente a un octeto IPv4.
        #
        # El patrón permite únicamente valores comprendidos entre
        # 0 y 255.
        octeto = (
            r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
        )

        # Construye la expresión regular correspondiente a una
        # dirección IPv4 completa.
        #
        # Se utilizan cuatro octetos separados por puntos.
        direccion_ip = (
            rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b"
        )

        # Define las expresiones regulares de todos los elementos
        # que puede reconocer el lenguaje TecNet Finder.
        #
        # El orden es importante porque los patrones se prueban
        # desde el primero hasta el último.
        especificaciones = [

            # Reconoce la palabra reservada IP.
            #
            # La anticipación permite reconocer también casos como:
            # IP192.168.1.0
            (r"\bIP(?=\s|\d|$)", "IP"),

            # Reconoce la palabra reservada MASK.
            #
            # También permite escribir MASK directamente junto
            # a una máscara CIDR, por ejemplo MASK/24.
            (r"\bMASK(?=\s|/|$)", "MASK"),

            # Reconoce la palabra reservada HOSTS.
            #
            # También permite casos como HOSTS50.
            (r"\bHOSTS(?=\s|\d|,|$)", "HOSTS"),

            # Reconoce la palabra reservada NAME.
            (r"\bNAME\b", "NAME"),

            # Intenta reconocer primero una dirección IPv4 completa.
            #
            # Este patrón debe aparecer antes de NUMBER y DOT para
            # evitar que una dirección válida sea dividida en partes.
            (direccion_ip, "IP_ADDRESS"),

            # Reconoce una máscara en notación CIDR.
            #
            # Algunos ejemplos que reconoce son /8, /16 o /24.
            (r"/\d+", "SUBNET_MASK"),

            # Reconoce un punto individual.
            #
            # Este token existe para permitir que una dirección IP
            # incompleta pueda ser enviada al analizador sintáctico
            # en vez de tratar automáticamente el punto como error léxico.
            (r"\.", "DOT"),

            # Reconoce uno o más dígitos como un número entero.
            #
            # Este token se utiliza principalmente para las cantidades
            # solicitadas después de la palabra HOSTS.
            (r"\d+", "NUMBER"),

            # Reconoce identificadores formados por letras, números
            # y guion bajo.
            #
            # El primer carácter debe ser una letra o guion bajo.
            (r"[A-Za-z_][A-Za-z0-9_]*", "IDENTIFIER"),

            # Reconoce la coma utilizada para separar cantidades de hosts.
            (r",", "COMMA"),

            # Reconoce espacios, tabulaciones y saltos de línea.
            #
            # El valor None indica que estos caracteres se consumirán
            # durante el análisis, pero no generarán un Token.
            (r"\s+", None),
        ]

        # Compila todas las expresiones regulares una sola vez.
        #
        # Esto evita recompilar los mismos patrones cada vez que se
        # analiza una nueva posición del código fuente.
        self._patrones = [
            (compilar_expresion(patron), tipo_token)
            for patron, tipo_token in especificaciones
        ]

    # Analiza todo el código fuente recibido y devuelve los tokens
    # y diagnósticos léxicos encontrados.
    def analizar(self, codigo_fuente: str) -> ResultadoLexico:

        # Crea la lista donde se almacenarán los tokens reconocidos.
        tokens: list[Token] = []

        # Crea la lista donde se almacenarán los diagnósticos
        # encontrados durante el análisis.
        diagnosticos = []

        # Copia el código fuente recibido.
        #
        # Esta variable irá reduciéndose conforme se reconozcan y
        # consuman fragmentos del texto.
        texto_restante = codigo_fuente

        # Inicializa el número de línea en uno.
        #
        # Para el usuario, la primera línea del archivo es la línea 1.
        linea_actual = 1

        # Inicializa la columna en cero.
        #
        # Esta posición representa el desplazamiento dentro de la línea
        # y posteriormente servirá para localizar visualmente errores.
        columna_actual = 0

        # Guarda el tipo del último token reconocido.
        #
        # Esta información se utiliza principalmente para comprobar
        # que un IDENTIFIER aparezca inmediatamente después de NAME.
        tipo_anterior: str | None = None

        # Continúa analizando mientras todavía exista texto pendiente.
        while texto_restante:

            # Indica si alguno de los patrones pudo reconocer texto
            # en la posición actual.
            coincidencia_encontrada = False

            # Recorre las expresiones regulares en el orden definido.
            for patron, tipo_token in self._patrones:

                # Intenta aplicar el patrón exclusivamente desde el
                # comienzo del texto que todavía no ha sido procesado.
                coincidencia = patron.match(texto_restante)

                # Si el patrón actual no coincide, continúa probando
                # con la siguiente expresión regular.
                if coincidencia is None:
                    continue

                # Indica que al menos un patrón reconoció correctamente
                # el fragmento actual.
                coincidencia_encontrada = True

                # Obtiene exactamente el texto reconocido por el patrón.
                texto = coincidencia.group(0)

                # Guarda la línea donde comienza el token o fragmento.
                linea_inicio = linea_actual

                # Guarda la columna donde comienza el token o fragmento.
                columna_inicio = columna_actual

                # Elimina del texto pendiente la parte que acaba de
                # ser reconocida.
                texto_restante = texto_restante[len(texto):]

                # Comprueba si el fragmento reconocido contiene uno
                # o más saltos de línea.
                if "\n" in texto:

                    # Divide el fragmento utilizando los saltos de línea
                    # para poder calcular la nueva posición.
                    partes = texto.split("\n")

                    # Aumenta el número de línea según la cantidad de
                    # saltos encontrados.
                    linea_actual += len(partes) - 1

                    # La nueva columna corresponde a la cantidad de
                    # caracteres existentes después del último salto.
                    columna_actual = len(partes[-1])

                # Si no hubo salto de línea, simplemente avanza la
                # columna según la longitud del texto reconocido.
                else:
                    columna_actual += len(texto)

                # Comprueba si el patrón reconocido corresponde a
                # espacios u otros caracteres que no generan token.
                if tipo_token is None:

                    # Finaliza este recorrido y vuelve al ciclo principal
                    # para continuar analizando el texto restante.
                    break

                # Comprueba si el elemento reconocido tiene la forma
                # de un identificador.
                if tipo_token == "IDENTIFIER":

                    # Verifica que el token inmediatamente anterior
                    # haya sido la palabra reservada NAME.
                    if tipo_anterior == "NAME":

                        # Crea el token IDENTIFIER con la información
                        # correspondiente al fragmento reconocido.
                        tokens.append(
                            Token(
                                tipo=tipo_token,
                                valor=texto,
                                linea=linea_inicio,
                                columna=columna_inicio,
                            )
                        )

                        # Actualiza el tipo del último token válido.
                        tipo_anterior = tipo_token

                    # Si el identificador no apareció después de NAME,
                    # se considera un error léxico.
                    else:

                        # Agrega un diagnóstico estructurado indicando
                        # la posición y el fragmento problemático.
                        diagnosticos.append(
                            crear_diagnostico(
                                codigo="LEX-001",
                                mensaje=(
                                    f"Identificador fuera de lugar en la línea "
                                    f"{linea_inicio}, posición {columna_inicio}: "
                                    f"'{texto}'. Los identificadores solo son "
                                    f"válidos después de NAME."
                                ),
                                linea=linea_inicio,
                                columna=columna_inicio,
                                longitud=len(texto),
                                fragmento=texto,
                            )
                        )

                    # Termina el recorrido de patrones porque el
                    # fragmento actual ya fue procesado.
                    break

                # Crea un Token para cualquier otro elemento reconocido.
                tokens.append(
                    Token(
                        tipo=tipo_token,
                        valor=texto,
                        linea=linea_inicio,
                        columna=columna_inicio,
                    )
                )

                # Guarda el tipo del token actual para poder utilizarlo
                # durante el reconocimiento del siguiente elemento.
                tipo_anterior = tipo_token

                # Sale del recorrido de patrones porque ya se encontró
                # una coincidencia válida para la posición actual.
                break

            # Si se reconoció algún patrón, regresa directamente al
            # comienzo del ciclo para procesar el siguiente fragmento.
            if coincidencia_encontrada:
                continue

            # Si ningún patrón coincidió, divide el texto restante
            # utilizando espacios para intentar identificar el fragmento
            # problemático completo.
            partes = texto_restante.split()

            # Comprueba si se pudo obtener al menos un fragmento.
            if partes:

                # Toma el primer fragmento no reconocido.
                fragmento = partes[0]

            # Si no se obtuvo un fragmento completo, toma únicamente
            # el primer carácter pendiente.
            else:
                fragmento = texto_restante[0]

            # Crea y almacena el diagnóstico correspondiente al símbolo
            # o fragmento que no pertenece al lenguaje.
            diagnosticos.append(
                crear_diagnostico(
                    codigo="LEX-002",
                    mensaje=(
                        f"Símbolo o fragmento no reconocido en la línea "
                        f"{linea_actual}, posición {columna_actual}: "
                        f"'{fragmento}'. Revise que la entrada use palabras "
                        f"reservadas válidas como IP, MASK, HOSTS o NAME."
                    ),
                    linea=linea_actual,
                    columna=columna_actual,
                    longitud=len(fragmento),
                    fragmento=fragmento,
                )
            )

            # Elimina del texto pendiente el fragmento incorrecto para
            # que el analizador pueda continuar con el resto de la entrada.
            texto_restante = texto_restante[len(fragmento):]

            # Avanza la posición actual según la longitud del fragmento
            # que acaba de ser descartado.
            columna_actual += len(fragmento)

        # Devuelve un objeto que contiene todos los tokens reconocidos
        # y todos los diagnósticos léxicos encontrados.
        return ResultadoLexico(
            tokens=tokens,
            diagnosticos=diagnosticos,
        )