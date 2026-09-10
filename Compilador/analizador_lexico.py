# ============================================================
# Archivo: analizador_lexico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene exclusivamente la fase de análisis léxico
# del compilador de TecNet Finder.
#
# El analizador léxico recibe el código fuente, reconoce los
# elementos válidos mediante expresiones regulares, genera tokens
# con su posición y registra los diagnósticos léxicos encontrados.
#
# También identifica palabras reservadas escritas con una
# combinación incorrecta de mayúsculas y minúsculas, además de
# fragmentos numéricos unidos directamente a texto.
#
# Esta fase no valida todavía la estructura completa de una
# instrucción; esa responsabilidad pertenece al sintáctico.
# ============================================================

import re  # Importa expresiones regulares para construir y compilar los patrones léxicos.

from Motor.diagnosticos import crear_diagnostico  # Importa la función que construye errores léxicos estructurados.
from Motor.modelos import ResultadoLexico, Token  # Importa los modelos utilizados como salida del lexer.


class AnalizadorLexico:  # Define la clase responsable de convertir el código fuente en tokens.
    def __init__(self):  # Prepara una sola vez los patrones utilizados durante el reconocimiento léxico.
        octeto = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"  # Reconoce un octeto IPv4 válido entre 0 y 255.
        direccion_ip = rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b"  # Forma una dirección IPv4 completa con cuatro octetos.
        reservada_mayusculas_incorrectas = (  # Reconoce solamente variantes de las palabras reservadas que no fueron aceptadas antes en su forma oficial.
            r"(?i:\bIP(?=\s|\d|$)|"
            r"\bMASK(?=\s|/|$)|"
            r"\bHOSTS(?=\s|\d|,|$)|"
            r"\bNAME\b)"
        )
        elemento_numerico_unido_texto = r"(?:/\d+|\d+)[A-Za-z_][A-Za-z0-9_]*\b"  # Reconoce números o máscaras CIDR pegados directamente a texto.

        especificaciones = [  # Define los patrones en el orden de prioridad con que serán evaluados.
            (r"\bIP(?=\s|\d|$)", "IP"),  # Reconoce IP incluso cuando aparece pegado a una dirección válida.
            (r"\bMASK(?=\s|/|$)", "MASK"),  # Reconoce MASK incluso cuando aparece pegado a una máscara CIDR.
            (r"\bHOSTS(?=\s|\d|,|$)", "HOSTS"),  # Reconoce HOSTS incluso cuando aparece pegado a una cantidad.
            (r"\bNAME\b", "NAME"),  # Reconoce la palabra reservada opcional NAME.
            (reservada_mayusculas_incorrectas, "RESERVADA_MAYUSCULAS_INCORRECTAS"),  # Separa las variantes de capitalización del error genérico de identificadores.
            (direccion_ip, "IP_ADDRESS"),  # Reconoce una dirección IPv4 completa antes de NUMBER y DOT.
            (elemento_numerico_unido_texto, "ELEMENTO_NUMERICO_UNIDO_TEXTO"),  # Detecta lexemas numéricos unidos a letras antes de que puedan dividirse artificialmente.
            (r"/\d+", "SUBNET_MASK"),  # Reconoce una máscara escrita en notación CIDR.
            (r"\.", "DOT"),  # Reconoce puntos individuales para que una IP incompleta pueda llegar al sintáctico.
            (r"\d+", "NUMBER"),  # Reconoce números enteros utilizados principalmente para cantidades de hosts.
            (r"[A-Za-z_][A-Za-z0-9_]*", "IDENTIFIER"),  # Reconoce nombres formados por letras, números y guion bajo.
            (r",", "COMMA"),  # Reconoce la coma utilizada para separar cantidades de hosts.
            (r"\s+", None),  # Consume espacios, tabulaciones y saltos de línea sin producir tokens.
        ]

        self._patrones = [  # Guarda todos los patrones ya compilados para reutilizarlos durante el análisis.
            (re.compile(patron), tipo_token)  # Compila cada expresión y conserva el tipo de token asociado.
            for patron, tipo_token in especificaciones  # Recorre todas las especificaciones definidas anteriormente.
        ]

    def analizar(self, codigo_fuente: str) -> ResultadoLexico:  # Recorre el código fuente y devuelve tokens y diagnósticos léxicos.
        tokens: list[Token] = []  # Crea la lista donde se almacenarán los tokens reconocidos.
        diagnosticos = []  # Crea la lista donde se almacenarán los errores encontrados.
        texto_restante = codigo_fuente  # Conserva la parte del código que todavía falta por analizar.
        linea_actual = 1  # Inicia el conteo de líneas desde la primera línea visible para el usuario.
        columna_actual = 0  # Inicia el desplazamiento de caracteres desde la columna cero.
        tipo_anterior: str | None = None  # Guarda el tipo del último token válido para comprobar IDENTIFIER después de NAME.

        while texto_restante:  # Continúa mientras todavía exista texto pendiente por analizar.
            coincidencia_encontrada = False  # Indica si alguno de los patrones reconoció el inicio del texto restante.

            for patron, tipo_token in self._patrones:  # Prueba los patrones siguiendo su prioridad de reconocimiento.
                coincidencia = patron.match(texto_restante)  # Intenta reconocer texto exclusivamente desde la posición actual.

                if coincidencia is None:
                    continue  # Prueba inmediatamente el siguiente patrón disponible.

                coincidencia_encontrada = True  # Registra que el fragmento actual sí pudo ser reconocido.
                texto = coincidencia.group(0)  # Obtiene exactamente el fragmento reconocido por la expresión regular.
                linea_inicio = linea_actual  # Guarda la línea donde comienza el fragmento reconocido.
                columna_inicio = columna_actual  # Guarda la columna donde comienza el fragmento reconocido.
                texto_restante = texto_restante[len(texto):]  # Elimina del pendiente el texto que acaba de ser procesado.

                if "\n" in texto:
                    partes = texto.split("\n")  # Divide el fragmento para calcular la nueva posición del cursor léxico.
                    linea_actual += len(partes) - 1  # Aumenta la línea según los saltos encontrados.
                    columna_actual = len(partes[-1])  # Coloca la columna después del último salto de línea reconocido.
                else:
                    columna_actual += len(texto)  # Avanza la columna según la longitud del fragmento consumido.

                if tipo_token is None:
                    break  # Finaliza este recorrido porque el fragmento ya fue consumido correctamente.

                if tipo_token == "RESERVADA_MAYUSCULAS_INCORRECTAS":
                    forma_correcta = texto.upper()  # Obtiene directamente la escritura oficial de la palabra reservada detectada.

                    diagnosticos.append(
                        crear_diagnostico(
                            codigo="LEX-003",
                            mensaje=(
                                f"Palabra reservada escrita con mayúsculas incorrectas en la línea "
                                f"{linea_inicio}, posición {columna_inicio}: '{texto}'. "
                                f"Debe escribirse como '{forma_correcta}'."
                            ),
                            linea=linea_inicio,
                            columna=columna_inicio,
                            longitud=len(texto),
                            fragmento=texto,
                        )
                    )

                    if forma_correcta == "NAME":
                        tipo_anterior = "NAME"  # Permite reconocer posteriormente el identificador sin generar un segundo error léxico innecesario.

                    break

                if tipo_token == "ELEMENTO_NUMERICO_UNIDO_TEXTO":
                    diagnosticos.append(
                        crear_diagnostico(
                            codigo="LEX-004",
                            mensaje=(
                                f"Elemento numérico unido a texto en la línea {linea_inicio}, "
                                f"posición {columna_inicio}: '{texto}'. Debe existir un espacio "
                                f"entre el valor numérico y el elemento siguiente."
                            ),
                            linea=linea_inicio,
                            columna=columna_inicio,
                            longitud=len(texto),
                            fragmento=texto,
                        )
                    )

                    break

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
                                    f"Identificador fuera de lugar en la línea {linea_inicio}, "
                                    f"posición {columna_inicio}: '{texto}'. Los identificadores "
                                    f"solo son válidos después de NAME."
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
                tipo_anterior = tipo_token  # Conserva el tipo actual para validar el siguiente elemento.
                break

            if coincidencia_encontrada:
                continue  # Regresa al inicio del ciclo para procesar el siguiente fragmento pendiente.

            partes = texto_restante.split()  # Separa el texto pendiente para aislar un fragmento no reconocido.

            if partes:
                fragmento = partes[0]  # Toma el primer fragmento no reconocido como origen del diagnóstico.
            else:
                fragmento = texto_restante[0]  # Toma únicamente el primer carácter todavía pendiente.

            diagnosticos.append(
                crear_diagnostico(
                    codigo="LEX-002",
                    mensaje=(
                        f"Símbolo o fragmento no reconocido en la línea {linea_actual}, "
                        f"posición {columna_actual}: '{fragmento}'. Revise que la entrada use "
                        f"palabras reservadas válidas como IP, MASK, HOSTS o NAME."
                    ),
                    linea=linea_actual,
                    columna=columna_actual,
                    longitud=len(fragmento),
                    fragmento=fragmento,
                )
            )
            texto_restante = texto_restante[len(fragmento):]  # Descarta el fragmento incorrecto para continuar el análisis.
            columna_actual += len(fragmento)  # Avanza la posición según la longitud del fragmento descartado.

        return ResultadoLexico(
            tokens=tokens,
            diagnosticos=diagnosticos,
        )  # Devuelve todos los tokens válidos y diagnósticos encontrados durante esta fase.