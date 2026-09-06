import re

from Motor.diagnosticos import crear_diagnostico
from Motor.modelos import ResultadoLexico, Token


class AnalizadorLexico:
    """
    Analizador léxico del lenguaje TecNet Finder.

    Recibe código fuente y lo transforma en una secuencia de tokens.
    También detecta errores léxicos.
    """

    def __init__(self):
        # Un octeto IPv4 válido debe estar entre 0 y 255.
        octeto = (
            r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
        )

        # Dirección IPv4 completa.
        direccion_ip = (
            rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b"
        )

        # El orden representa la prioridad de reconocimiento.
        especificaciones = [
            # Palabras reservadas.
            #
            # IP, MASK y HOSTS pueden reconocerse pegadas
            # al valor siguiente, como:
            #
            # IP192.168.1.0
            # MASK/24
            # HOSTS50
            (r"\bIP(?=\s|\d|$)", "IP"),
            (r"\bMASK(?=\s|/|$)", "MASK"),
            (r"\bHOSTS(?=\s|\d|,|$)", "HOSTS"),
            (r"\bNAME\b", "NAME"),

            # La dirección completa debe intentarse reconocer
            # antes que NUMBER y DOT.
            (direccion_ip, "IP_ADDRESS"),

            # Máscara CIDR.
            (r"/\d+", "SUBNET_MASK"),

            # El punto se reconoce individualmente para permitir
            # que una IP incompleta llegue al analizador sintáctico.
            (r"\.", "DOT"),

            # Otros elementos del lenguaje.
            (r"\d+", "NUMBER"),
            (r"[A-Za-z_][A-Za-z0-9_]*", "IDENTIFIER"),
            (r",", "COMMA"),

            # Los espacios se consumen, pero no generan token.
            (r"\s+", None),
        ]

        # Las expresiones se compilan una sola vez.
        self._patrones = [
            (re.compile(patron), tipo_token)
            for patron, tipo_token in especificaciones
        ]

    def analizar(self, codigo_fuente: str) -> ResultadoLexico:
        """
        Analiza el código fuente y devuelve los tokens y
        diagnósticos léxicos encontrados.
        """

        tokens: list[Token] = []
        diagnosticos = []

        texto_restante = codigo_fuente

        linea_actual = 1
        columna_actual = 0

        tipo_anterior: str | None = None

        while texto_restante:
            coincidencia_encontrada = False

            for patron, tipo_token in self._patrones:
                coincidencia = patron.match(texto_restante)

                if coincidencia is None:
                    continue

                coincidencia_encontrada = True

                texto = coincidencia.group(0)

                linea_inicio = linea_actual
                columna_inicio = columna_actual

                # Se elimina del texto pendiente lo que ya fue reconocido.
                texto_restante = texto_restante[len(texto):]

                # Actualizar línea y columna.
                if "\n" in texto:
                    partes = texto.split("\n")
                    linea_actual += len(partes) - 1
                    columna_actual = len(partes[-1])
                else:
                    columna_actual += len(texto)

                # Los espacios no producen tokens.
                if tipo_token is None:
                    break

                # Los identificadores solamente son válidos
                # inmediatamente después de NAME.
                if tipo_token == "IDENTIFIER":
                    if tipo_anterior == "NAME":
                        tokens.append(
                            Token(
                                tipo=tipo_token,
                                valor=texto,
                                linea=linea_inicio,
                                columna=columna_inicio,
                            )
                        )

                        tipo_anterior = tipo_token

                    else:
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

                    break

                tokens.append(
                    Token(
                        tipo=tipo_token,
                        valor=texto,
                        linea=linea_inicio,
                        columna=columna_inicio,
                    )
                )

                tipo_anterior = tipo_token
                break

            if coincidencia_encontrada:
                continue

            # Si nada coincide, se considera un fragmento no reconocido.
            partes = texto_restante.split()

            if partes:
                fragmento = partes[0]
            else:
                fragmento = texto_restante[0]

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

            texto_restante = texto_restante[len(fragmento):]
            columna_actual += len(fragmento)

        return ResultadoLexico(
            tokens=tokens,
            diagnosticos=diagnosticos,
        )