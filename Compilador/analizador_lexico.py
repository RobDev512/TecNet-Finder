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
# Esta fase no valida todavía la estructura completa de una
# instrucción; esa responsabilidad pertenece al sintáctico.
# ============================================================

from re import compile as compilar_expresion  # Importa la función que compila las expresiones regulares.
from Motor.diagnosticos import crear_diagnostico  # Importa la función que construye errores léxicos estructurados.
from Motor.modelos import ResultadoLexico, Token  # Importa los modelos utilizados como salida del lexer.


class AnalizadorLexico:  # Define la clase responsable de convertir el código fuente en tokens.
    def __init__(self):  # Prepara una sola vez los patrones utilizados durante el reconocimiento léxico.
        octeto = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"  # Reconoce un octeto IPv4 válido entre 0 y 255.
        direccion_ip = rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b"  # Forma una dirección IPv4 completa con cuatro octetos.

        especificaciones = [  # Define los patrones en el orden de prioridad con que serán evaluados.
            (r"\bIP(?=\s|\d|$)", "IP"),  # Reconoce IP incluso cuando aparece pegado a una dirección válida.
            (r"\bMASK(?=\s|/|$)", "MASK"),  # Reconoce MASK incluso cuando aparece pegado a una máscara CIDR.
            (r"\bHOSTS(?=\s|\d|,|$)", "HOSTS"),  # Reconoce HOSTS incluso cuando aparece pegado a una cantidad.
            (r"\bNAME\b", "NAME"),  # Reconoce la palabra reservada opcional NAME.
            (direccion_ip, "IP_ADDRESS"),  # Reconoce una dirección IPv4 completa antes de NUMBER y DOT.
            (r"/\d+", "SUBNET_MASK"),  # Reconoce una máscara escrita en notación CIDR.
            (r"\.", "DOT"),  # Reconoce puntos individuales para que una IP incompleta pueda llegar al sintáctico.
            (r"\d+", "NUMBER"),  # Reconoce números enteros utilizados principalmente para cantidades de hosts.
            (r"[A-Za-z_][A-Za-z0-9_]*", "IDENTIFIER"),  # Reconoce nombres formados por letras, números y guion bajo.
            (r",", "COMMA"),  # Reconoce la coma utilizada para separar cantidades de hosts.
            (r"\s+", None),  # Consume espacios, tabulaciones y saltos de línea sin producir tokens.
        ]

        self._patrones = [  # Guarda todos los patrones ya compilados para reutilizarlos durante el análisis.
            (compilar_expresion(patron), tipo_token)  # Compila cada expresión y conserva el tipo de token asociado.
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

                if coincidencia is None:  # Comprueba si el patrón actual no coincide con el texto restante.
                    continue  # Prueba inmediatamente el siguiente patrón disponible.

                coincidencia_encontrada = True  # Registra que el fragmento actual sí pudo ser reconocido.
                texto = coincidencia.group(0)  # Obtiene exactamente el fragmento reconocido por la expresión regular.
                linea_inicio = linea_actual  # Guarda la línea donde comienza el fragmento reconocido.
                columna_inicio = columna_actual  # Guarda la columna donde comienza el fragmento reconocido.
                texto_restante = texto_restante[len(texto):]  # Elimina del pendiente el texto que acaba de ser procesado.

                if "\n" in texto:  # Comprueba si el fragmento consumido contiene uno o más saltos de línea.
                    partes = texto.split("\n")  # Divide el fragmento para calcular la nueva posición del cursor léxico.
                    linea_actual += len(partes) - 1  # Aumenta la línea según los saltos encontrados.
                    columna_actual = len(partes[-1])  # Coloca la columna después del último salto de línea reconocido.
                else:  # Se ejecuta cuando el fragmento no contiene saltos de línea.
                    columna_actual += len(texto)  # Avanza la columna según la longitud del fragmento consumido.

                if tipo_token is None:  # Comprueba si el patrón corresponde a espacios que no deben generar un token.
                    break  # Finaliza este recorrido porque el fragmento ya fue consumido correctamente.

                if tipo_token == "IDENTIFIER":  # Aplica la regla especial que controla dónde puede aparecer un identificador.
                    if tipo_anterior == "NAME":  # Verifica que el último token válido haya sido la palabra reservada NAME.
                        tokens.append(  # Agrega el identificador válido a la lista de tokens reconocidos.
                            Token(  # Construye el token con su tipo, valor y posición original.
                                tipo=tipo_token,  # Guarda IDENTIFIER como tipo del token.
                                valor=texto,  # Guarda el nombre exacto reconocido.
                                linea=linea_inicio,  # Guarda la línea donde comenzó el identificador.
                                columna=columna_inicio,  # Guarda la columna donde comenzó el identificador.
                            )
                        )
                        tipo_anterior = tipo_token  # Actualiza el último tipo reconocido para el siguiente fragmento.
                    else:  # Se ejecuta cuando un identificador aparece sin estar inmediatamente después de NAME.
                        diagnosticos.append(  # Agrega un error léxico sin detener el análisis del resto de la entrada.
                            crear_diagnostico(  # Construye el diagnóstico estructurado LEX-001.
                                codigo="LEX-001",  # Identifica el error como un identificador fuera de lugar.
                                mensaje=(  # Construye un mensaje específico usando la posición y el texto encontrado.
                                    f"Identificador fuera de lugar en la línea {linea_inicio}, "
                                    f"posición {columna_inicio}: '{texto}'. Los identificadores "
                                    f"solo son válidos después de NAME."
                                ),
                                linea=linea_inicio,  # Guarda la línea del fragmento problemático.
                                columna=columna_inicio,  # Guarda la columna del fragmento problemático.
                                longitud=len(texto),  # Guarda cuántos caracteres ocupa el identificador incorrecto.
                                fragmento=texto,  # Guarda exactamente el identificador detectado.
                            )
                        )
                    break  # Finaliza el recorrido porque el identificador ya fue procesado.

                tokens.append(  # Agrega cualquier otro token reconocido normalmente.
                    Token(  # Construye el token con su información léxica.
                        tipo=tipo_token,  # Guarda el tipo asociado al patrón que coincidió.
                        valor=texto,  # Guarda exactamente el texto reconocido.
                        linea=linea_inicio,  # Guarda la línea donde comenzó el token.
                        columna=columna_inicio,  # Guarda la columna donde comenzó el token.
                    )
                )
                tipo_anterior = tipo_token  # Conserva el tipo actual para validar el siguiente elemento.
                break  # Sale del recorrido porque ya se encontró una coincidencia para esta posición.

            if coincidencia_encontrada:  # Comprueba si el fragmento actual fue reconocido o consumido por algún patrón.
                continue  # Regresa al inicio del ciclo para procesar el siguiente fragmento pendiente.

            partes = texto_restante.split()  # Separa el texto pendiente para aislar un fragmento no reconocido.

            if partes:  # Comprueba si existe al menos un fragmento separado por espacios.
                fragmento = partes[0]  # Toma el primer fragmento no reconocido como origen del diagnóstico.
            else:  # Se ejecuta cuando no fue posible obtener un fragmento completo.
                fragmento = texto_restante[0]  # Toma únicamente el primer carácter todavía pendiente.

            diagnosticos.append(  # Agrega el diagnóstico correspondiente al fragmento desconocido.
                crear_diagnostico(  # Construye el diagnóstico estructurado LEX-002.
                    codigo="LEX-002",  # Identifica el problema como símbolo o fragmento no reconocido.
                    mensaje=(  # Construye un mensaje específico usando la posición y el fragmento encontrado.
                        f"Símbolo o fragmento no reconocido en la línea {linea_actual}, "
                        f"posición {columna_actual}: '{fragmento}'. Revise que la entrada use "
                        f"palabras reservadas válidas como IP, MASK, HOSTS o NAME."
                    ),
                    linea=linea_actual,  # Guarda la línea donde apareció el fragmento desconocido.
                    columna=columna_actual,  # Guarda la columna donde apareció el fragmento desconocido.
                    longitud=len(fragmento),  # Guarda la longitud que deberá señalarse visualmente.
                    fragmento=fragmento,  # Guarda el texto exacto que no pudo reconocerse.
                )
            )
            texto_restante = texto_restante[len(fragmento):]  # Descarta el fragmento incorrecto para continuar el análisis.
            columna_actual += len(fragmento)  # Avanza la posición según la longitud del fragmento descartado.

        return ResultadoLexico(  # Devuelve todos los tokens válidos y diagnósticos encontrados durante esta fase.
            tokens=tokens,  # Entrega la lista completa de tokens reconocidos.
            diagnosticos=diagnosticos,  # Entrega la lista completa de diagnósticos léxicos.
        )
