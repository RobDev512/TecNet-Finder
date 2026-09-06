# ============================================================
# Archivo: prueba_analizador_sintactico.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# al analizador sintáctico de TecNet Finder.
#
# Cada prueba utiliza primero el analizador léxico para obtener
# tokens reales y posteriormente envía esos tokens al parser.
#
# De esta manera se comprueba el mismo flujo que utilizará
# posteriormente la aplicación completa.
# ============================================================


# Importa el analizador léxico para transformar primero
# el código fuente en tokens.
from Compilador.analizador_lexico import AnalizadorLexico


# Importa el analizador sintáctico que será evaluado.
from Compilador.analizador_sintactico import AnalizadorSintactico


# Ejecuta consecutivamente el análisis léxico y sintáctico.
#
# Esta función auxiliar evita repetir las mismas instrucciones
# dentro de cada prueba.
def analizar_codigo(codigo_fuente: str):

    # Crea el analizador léxico.
    analizador_lexico = AnalizadorLexico()

    # Convierte el código fuente en tokens.
    resultado_lexico = analizador_lexico.analizar(
        codigo_fuente
    )

    # Crea el analizador sintáctico utilizando los tokens
    # reconocidos previamente.
    analizador_sintactico = AnalizadorSintactico(
        resultado_lexico.tokens
    )

    # Ejecuta el análisis sintáctico.
    resultado_sintactico = analizador_sintactico.analizar()

    # Devuelve ambos resultados para que las pruebas puedan
    # comprobar cada fase cuando sea necesario.
    return resultado_lexico, resultado_sintactico


# Comprueba una instrucción completa que incluye NAME.
def prueba_instruccion_valida_completa():

    # Define una instrucción completamente válida.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 "
        "HOSTS 50,30,10 NAME Oficina"
    )

    # Ejecuta las dos primeras fases.
    resultado_lexico, resultado_sintactico = (
        analizar_codigo(codigo_fuente)
    )

    # Comprueba que el lexer no haya producido errores.
    assert resultado_lexico.diagnosticos == []

    # Comprueba que el parser tampoco produzca errores.
    assert resultado_sintactico.diagnosticos == []

    # Comprueba que exista exactamente un bloque válido.
    assert len(resultado_sintactico.bloques) == 1

    # Obtiene el bloque reconocido.
    bloque = resultado_sintactico.bloques[0]

    # Comprueba la dirección IP almacenada.
    assert bloque.direccion_ip == "192.168.1.0"

    # Comprueba la máscara almacenada.
    assert bloque.mascara_subred == "/24"

    # Comprueba todas las cantidades de hosts.
    assert bloque.cantidades_hosts == [50, 30, 10]

    # Comprueba el nombre de la red.
    assert bloque.nombre == "Oficina"


# Comprueba que NAME sea realmente opcional.
def prueba_instruccion_valida_sin_nombre():

    # Define una instrucción válida sin NAME.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba que exista un bloque válido.
    assert len(resultado_sintactico.bloques) == 1

    # Comprueba que no exista ningún diagnóstico.
    assert resultado_sintactico.diagnosticos == []

    # Verifica que el nombre haya quedado representado como None.
    assert resultado_sintactico.bloques[0].nombre is None


# Comprueba el diagnóstico SIN-001 para una IP incompleta.
def prueba_ip_incompleta():

    # Define una dirección a la que le falta el último octeto.
    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba que el bloque incorrecto no sea aceptado.
    assert resultado_sintactico.bloques == []

    # Comprueba el código específico del diagnóstico.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-001"
    )


# Comprueba SIN-002 cuando falta la palabra MASK.
def prueba_falta_mask():

    # Omite deliberadamente MASK después de la dirección IP.
    codigo_fuente = (
        "IP 192.168.1.0 /24 HOSTS 50"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba el diagnóstico esperado.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-002"
    )


# Comprueba SIN-003 cuando MASK no tiene una máscara CIDR.
def prueba_falta_mascara_cidr():

    # Coloca HOSTS inmediatamente después de MASK.
    codigo_fuente = (
        "IP 192.168.1.0 MASK HOSTS 50"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba el diagnóstico esperado.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-003"
    )


# Comprueba SIN-004 cuando HOSTS no recibe ningún NUMBER.
def prueba_falta_cantidad_hosts():

    # Coloca NAME directamente después de HOSTS.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS NAME Oficina"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba el código del diagnóstico.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-004"
    )


# Comprueba SIN-005 cuando existe una coma sin otro NUMBER.
def prueba_lista_hosts_mal_formada():

    # Termina la lista dejando una coma sin cantidad posterior.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50,"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba que el bloque con error local no sea aceptado.
    assert resultado_sintactico.bloques == []

    # Comprueba el código correspondiente.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-005"
    )


# Comprueba SIN-006 cuando NAME queda incompleto.
def prueba_name_sin_identificador():

    # Termina la instrucción inmediatamente después de NAME.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba el código del diagnóstico.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-006"
    )


# Comprueba SIN-007 cuando se repite exactamente
# la misma instrucción.
def prueba_instruccion_duplicada():

    # Define dos instrucciones idénticas en líneas diferentes.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"
    )

    # Ejecuta el análisis.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba que solamente se conserve una copia válida.
    assert len(resultado_sintactico.bloques) == 1

    # Comprueba que exista exactamente un diagnóstico.
    assert len(resultado_sintactico.diagnosticos) == 1

    # Comprueba que se trate de una instrucción duplicada.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-007"
    )


# Comprueba SIN-008 y, al mismo tiempo, verifica que el
# modo pánico consiga continuar con una instrucción posterior.
def prueba_orden_incorrecto_y_recuperacion():

    # La primera línea comienza incorrectamente con MASK.
    #
    # La segunda línea contiene una instrucción completamente válida.
    codigo_fuente = (
        "MASK /24 HOSTS 50\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Segunda"
    )

    # Ejecuta ambas fases.
    _, resultado_sintactico = analizar_codigo(
        codigo_fuente
    )

    # Comprueba que exista el error de orden en la primera línea.
    assert resultado_sintactico.diagnosticos[0].codigo == (
        "SIN-008"
    )

    # Comprueba que el modo pánico haya permitido continuar
    # y recuperar la segunda instrucción.
    assert len(resultado_sintactico.bloques) == 1

    # Comprueba que el bloque recuperado sea la segunda red.
    assert (
        resultado_sintactico.bloques[0].direccion_ip
        == "10.0.0.0"
    )

    # Comprueba también su nombre.
    assert (
        resultado_sintactico.bloques[0].nombre
        == "Segunda"
    )