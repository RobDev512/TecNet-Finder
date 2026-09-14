# ============================================================
# Archivo: analizador_lexico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene exclusivamente la fase de análisis
# léxico del compilador de TecNet Finder.
#
# Recibe el código fuente, reconoce los elementos válidos
# mediante expresiones regulares, genera tokens con su posición
# y registra los diagnósticos léxicos encontrados.
#
# También detecta palabras reservadas escritas con mayúsculas
# incorrectas y elementos numéricos unidos directamente a texto.
#
# Esta fase no comprueba todavía la estructura completa de una
# instrucción; esa responsabilidad pertenece al sintáctico.
# ============================================================

import re  # Permite definir y compilar los patrones utilizados para reconocer los elementos del lenguaje.

from Motor.diagnosticos import crear_diagnostico  # Construye los diagnósticos léxicos estructurados utilizados por TecNet Finder.
from Motor.modelos import ResultadoLexico, Token  # Proporciona las estructuras utilizadas para devolver tokens y diagnósticos.


class AnalizadorLexico:  # Convierte el código fuente de TecNet Finder en una secuencia ordenada de tokens.
    def __init__(self):  # Prepara una sola vez todos los patrones empleados durante el reconocimiento léxico.
        octeto = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"  # Reconoce individualmente un octeto IPv4 válido entre 0 y 255.
        direccion_ip = rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b"  # Construye el patrón utilizado para reconocer una dirección IPv4 completa.
        reservada_mayusculas_incorrectas = (  # Agrupa las variantes de palabras reservadas cuya escritura no coincide con la forma oficial.
            r"(?i:\bIP(?=\s|\d|$)|"  # Reconoce cualquier combinación de mayúsculas o minúsculas equivalente con IP.
            r"\bMASK(?=\s|/|$)|"  # Reconoce cualquier combinación equivalente con MASK.
            r"\bHOSTS(?=\s|\d|,|$)|"  # Reconoce cualquier combinación equivalente con HOSTS.
            r"\bNAME\b)"  # Reconoce cualquier combinación equivalente con NAME.
        )
        elemento_numerico_unido_texto = r"(?:/\d+|\d+)[A-Za-z_][A-Za-z0-9_]*\b"  # Detecta cantidades o máscaras pegadas directamente con texto.

        especificaciones = [  # Mantiene los patrones en el orden exacto de prioridad utilizado por el lexer.
            (r"\bIP(?=\s|\d|$)", "IP"),  # Reconoce IP incluso cuando aparece pegado directamente con una dirección.
            (r"\bMASK(?=\s|/|$)", "MASK"),  # Reconoce MASK incluso cuando aparece pegado con una máscara CIDR.
            (r"\bHOSTS(?=\s|\d|,|$)", "HOSTS"),  # Reconoce HOSTS incluso cuando aparece pegado directamente con una cantidad.
            (r"\bNAME\b", "NAME"),  # Reconoce la palabra reservada opcional utilizada para nombrar una red.
            (reservada_mayusculas_incorrectas, "RESERVADA_MAYUSCULAS_INCORRECTAS"),  # Separa los errores de capitalización del identificador genérico.
            (direccion_ip, "IP_ADDRESS"),  # Reconoce una dirección completa antes de permitir interpretar sus partes por separado.
            (elemento_numerico_unido_texto, "ELEMENTO_NUMERICO_UNIDO_TEXTO"),  # Evita dividir artificialmente entradas incorrectas como 50ABC.
            (r"/\d+", "SUBNET_MASK"),  # Reconoce máscaras escritas utilizando notación CIDR.
            (r"\.", "DOT"),  # Conserva puntos individuales para que una IP incompleta llegue hasta el sintáctico.
            (r"\d+", "NUMBER"),  # Reconoce cantidades numéricas utilizadas principalmente después de HOSTS.
            (r"[A-Za-z_][A-Za-z0-9_]*", "IDENTIFIER"),  # Reconoce nombres permitidos después de la palabra reservada NAME.
            (r",", "COMMA"),  # Reconoce las comas utilizadas para separar cantidades de hosts.
            (r"\s+", None),  # Consume espacios, tabulaciones y saltos de línea sin convertirlos en tokens.
        ]
        self._patrones = [(re.compile(patron), tipo_token) for patron, tipo_token in especificaciones]  # Compila todos los patrones una sola vez para reutilizarlos.

    def analizar(self, codigo_fuente: str) -> ResultadoLexico:  # Recorre completamente el código y devuelve sus tokens y diagnósticos.
        tokens: list[Token] = []  # Conserva en orden todos los elementos válidos reconocidos por el lexer.
        diagnosticos = []  # Reúne los errores léxicos encontrados sin detener el análisis ante el primero.
        texto_restante = codigo_fuente  # Mantiene solamente la parte del código que todavía no ha sido procesada.
        linea_actual = 1  # Inicia el seguimiento en la primera línea visible del editor.
        columna_actual = 0  # Inicia la posición horizontal desde la columna cero utilizada internamente.
        tipo_anterior: str | None = None  # Permite comprobar si un identificador aparece realmente después de NAME.

        while texto_restante:  # Continúa analizando mientras todavía exista código fuente pendiente.
            coincidencia_encontrada = False  # Registra si alguno de los patrones pudo consumir la posición actual.

            for patron, tipo_token in self._patrones:  # Recorre los patrones respetando estrictamente su prioridad de reconocimiento.
                coincidencia = patron.match(texto_restante)  # Intenta reconocer únicamente el comienzo del texto que todavía falta analizar.

                if coincidencia is None:  # Comprueba si el patrón actual no corresponde con el fragmento ubicado en el cursor léxico.
                    continue  # Prueba inmediatamente el siguiente patrón sin modificar ninguna posición.

                coincidencia_encontrada = True  # Confirma que el fragmento actual sí pertenece a alguno de los patrones conocidos.
                texto = coincidencia.group(0)  # Recupera exactamente el lexema reconocido por la expresión regular.
                linea_inicio = linea_actual  # Guarda la línea original antes de avanzar la posición.
                columna_inicio = columna_actual  # Guarda la columna original donde comienza el lexema.
                texto_restante = texto_restante[len(texto):]  # Elimina del texto pendiente el fragmento que acaba de ser consumido.

                if "\n" in texto:  # Comprueba si el fragmento reconocido contiene uno o más cambios de línea.
                    partes = texto.split("\n")  # Divide el fragmento para conocer cuánto debe avanzar el cursor vertical.
                    linea_actual += len(partes) - 1  # Aumenta la línea según la cantidad de saltos encontrados.
                    columna_actual = len(partes[-1])  # Reubica la columna después del último salto consumido.
                else:  # Atiende los lexemas que permanecen dentro de la misma línea.
                    columna_actual += len(texto)  # Avanza horizontalmente según la longitud exacta del fragmento.

                if tipo_token is None:  # Comprueba si el patrón corresponde únicamente con espacios u otros separadores ignorados.
                    break  # Termina la revisión de patrones porque el separador ya fue consumido correctamente.

                if tipo_token == "RESERVADA_MAYUSCULAS_INCORRECTAS":  # Detecta específicamente una palabra reservada escrita con capitalización incorrecta.
                    forma_correcta = texto.upper()  # Obtiene la forma oficial que se mostrará al usuario como corrección.
                    diagnosticos.append(
                        crear_diagnostico(
                            codigo="LEX-003",  # Identifica el problema como palabra reservada con mayúsculas incorrectas.
                            mensaje=f"Palabra reservada escrita con mayúsculas incorrectas en la línea {linea_inicio}, posición {columna_inicio}: '{texto}'. Debe escribirse como '{forma_correcta}'.",  # Explica dónde apareció y cuál es su escritura correcta.
                            linea=linea_inicio,  # Relaciona el diagnóstico con la línea exacta del editor.
                            columna=columna_inicio,  # Relaciona el diagnóstico con la columna donde comienza el lexema.
                            longitud=len(texto),  # Permite resaltar visualmente toda la palabra incorrecta.
                            fragmento=texto,  # Conserva el texto original que produjo el diagnóstico.
                        )
                    )  # Agrega el error sin detener el resto del análisis léxico.

                    if forma_correcta == "NAME":  # Comprueba si la palabra incorrecta correspondía con NAME.
                        tipo_anterior = "NAME"  # Permite que el identificador posterior no produzca además un LEX-001 innecesario.

                    break  # Finaliza el procesamiento del lexema porque ya fue diagnosticado.

                if tipo_token == "ELEMENTO_NUMERICO_UNIDO_TEXTO":  # Detecta un número o máscara pegado directamente con letras.
                    diagnosticos.append(
                        crear_diagnostico(
                            codigo="LEX-004",  # Identifica específicamente el problema de separación entre número y texto.
                            mensaje=f"Elemento numérico unido a texto en la línea {linea_inicio}, posición {columna_inicio}: '{texto}'. Debe existir un espacio entre el valor numérico y el elemento siguiente.",  # Explica el fragmento encontrado y la separación requerida.
                            linea=linea_inicio,  # Conserva la línea donde se encontró el lexema incorrecto.
                            columna=columna_inicio,  # Conserva su posición horizontal.
                            longitud=len(texto),  # Permite marcar visualmente el fragmento completo.
                            fragmento=texto,  # Guarda exactamente el texto unido que causó el error.
                        )
                    )  # Incorpora el diagnóstico a la colección de resultados.

                    break  # Evita interpretar partes internas del mismo lexema como tokens independientes.

                if tipo_token == "IDENTIFIER":  # Procesa de manera especial los identificadores porque solamente son válidos después de NAME.
                    if tipo_anterior == "NAME":  # Comprueba que el identificador aparezca en la posición permitida por el lenguaje.
                        tokens.append(Token(tipo=tipo_token, valor=texto, linea=linea_inicio, columna=columna_inicio))  # Conserva el nombre válido junto con su ubicación.
                        tipo_anterior = tipo_token  # Impide que un segundo identificador consecutivo también se considere parte del mismo NAME.
                    else:  # Atiende cualquier identificador que aparezca fuera de la sección opcional de nombre.
                        diagnosticos.append(
                            crear_diagnostico(
                                codigo="LEX-001",  # Clasifica el problema como identificador fuera de lugar.
                                mensaje=f"Identificador fuera de lugar en la línea {linea_inicio}, posición {columna_inicio}: '{texto}'. Los identificadores solo son válidos después de NAME.",  # Explica la única posición donde puede utilizarse ese tipo de lexema.
                                linea=linea_inicio,  # Conserva la línea del identificador incorrecto.
                                columna=columna_inicio,  # Conserva la columna exacta del identificador.
                                longitud=len(texto),  # Permite resaltar toda la palabra dentro del editor.
                                fragmento=texto,  # Conserva el identificador original para mostrarlo en el diagnóstico.
                            )
                        )  # Registra el error sin convertir el identificador incorrecto en un token válido.

                    break  # Termina el tratamiento especial del identificador actual.

                tokens.append(Token(tipo=tipo_token, valor=texto, linea=linea_inicio, columna=columna_inicio))  # Conserva cualquier otro token válido junto con su ubicación.
                tipo_anterior = tipo_token  # Recuerda el tipo aceptado para validar correctamente el siguiente elemento.
                break  # Finaliza la búsqueda porque el fragmento actual ya fue consumido por un patrón válido.

            if coincidencia_encontrada:  # Comprueba si la iteración anterior logró reconocer o consumir algún elemento.
                continue  # Regresa al inicio para analizar el nuevo comienzo del texto pendiente.

            partes = texto_restante.split()  # Intenta separar una palabra desconocida completa para producir un diagnóstico más útil.
            fragmento = partes[0] if partes else texto_restante[0]  # Usa el fragmento completo disponible o un carácter como respaldo.
            diagnosticos.append(
                crear_diagnostico(
                    codigo="LEX-002",  # Identifica cualquier elemento que no pertenece al lenguaje definido.
                    mensaje=f"Símbolo o fragmento no reconocido en la línea {linea_actual}, posición {columna_actual}: '{fragmento}'. Revise que la entrada use palabras reservadas válidas como IP, MASK, HOSTS o NAME.",  # Informa al usuario qué parte no pudo reconocer el lexer.
                    linea=linea_actual,  # Conserva la línea actual del cursor léxico.
                    columna=columna_actual,  # Conserva la posición donde empieza el fragmento desconocido.
                    longitud=len(fragmento),  # Permite resaltar todo el elemento incorrecto.
                    fragmento=fragmento,  # Guarda el texto original que provocó el diagnóstico.
                )
            )  # Añade el error genérico sin finalizar prematuramente el análisis.
            texto_restante = texto_restante[len(fragmento):]  # Descarta el fragmento desconocido para continuar buscando tokens posteriores.
            columna_actual += len(fragmento)  # Mantiene sincronizada la posición después de retirar el elemento inválido.

        return ResultadoLexico(tokens=tokens, diagnosticos=diagnosticos)  # Devuelve conjuntamente todos los tokens válidos y diagnósticos detectados.