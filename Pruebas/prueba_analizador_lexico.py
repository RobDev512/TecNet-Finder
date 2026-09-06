# ============================================================
# Archivo: prueba_analizador_lexico.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# al analizador léxico de TecNet Finder.
#
# Las pruebas permiten comprobar que el lexer siga reconociendo
# correctamente las entradas válidas y detectando los errores
# esperados después de realizar cambios en el proyecto.
#
# pytest ejecutará automáticamente todas las funciones cuyo nombre
# comience con "prueba_" gracias a la configuración de pytest.ini.
# ============================================================


# Importa el analizador léxico que será evaluado durante las pruebas.
from Compilador.analizador_lexico import AnalizadorLexico


# Comprueba que una instrucción completa y correctamente escrita
# sea reconocida sin producir diagnósticos léxicos.
def prueba_entrada_valida_completa():

    # Crea una instancia del analizador léxico.
    analizador = AnalizadorLexico()

    # Define una instrucción válida utilizando todos los elementos
    # principales del lenguaje TecNet Finder.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"
    )

    # Ejecuta el análisis léxico sobre la entrada.
    resultado = analizador.analizar(codigo_fuente)

    # Define la secuencia exacta de tipos de token que esperamos obtener.
    tipos_esperados = [
        "IP",
        "IP_ADDRESS",
        "MASK",
        "SUBNET_MASK",
        "HOSTS",
        "NUMBER",
        "COMMA",
        "NUMBER",
        "COMMA",
        "NUMBER",
        "NAME",
        "IDENTIFIER",
    ]

    # Extrae únicamente el tipo de cada token obtenido.
    tipos_obtenidos = [
        token.tipo
        for token in resultado.tokens
    ]

    # Comprueba que los tokens obtenidos coincidan exactamente
    # con la secuencia esperada.
    assert tipos_obtenidos == tipos_esperados

    # Comprueba que una entrada válida no genere diagnósticos léxicos.
    assert resultado.diagnosticos == []


# Comprueba que un identificador escrito fuera de la sección NAME
# sea detectado como un error léxico.
def prueba_identificador_fuera_de_lugar():

    # Crea una nueva instancia independiente del analizador.
    analizador = AnalizadorLexico()

    # Define una instrucción donde "Oficina" aparece sin utilizar
    # previamente la palabra reservada NAME.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 Oficina"
    )

    # Analiza la entrada incorrecta.
    resultado = analizador.analizar(codigo_fuente)

    # Comprueba que se haya generado exactamente un diagnóstico.
    assert len(resultado.diagnosticos) == 1

    # Comprueba que el diagnóstico corresponda al error LEX-001.
    assert resultado.diagnosticos[0].codigo == "LEX-001"

    # Comprueba que el fragmento detectado sea exactamente "Oficina".
    assert resultado.diagnosticos[0].fragmento == "Oficina"


# Comprueba que un símbolo que no pertenece al lenguaje sea
# identificado como un error léxico.
def prueba_simbolo_no_reconocido():

    # Crea una instancia del analizador léxico.
    analizador = AnalizadorLexico()

    # Define una entrada válida excepto por el símbolo @ colocado
    # al final de la instrucción.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"
    )

    # Ejecuta el análisis sobre la entrada.
    resultado = analizador.analizar(codigo_fuente)

    # Comprueba que solamente exista un diagnóstico.
    assert len(resultado.diagnosticos) == 1

    # Verifica que el error detectado corresponda a LEX-002.
    assert resultado.diagnosticos[0].codigo == "LEX-002"

    # Comprueba que el fragmento relacionado con el error sea @.
    assert resultado.diagnosticos[0].fragmento == "@"


# Comprueba que un identificador colocado correctamente después
# de NAME sea aceptado por el analizador.
def prueba_identificador_despues_de_name():

    # Crea una instancia del analizador.
    analizador = AnalizadorLexico()

    # Define una instrucción válida que utiliza NAME correctamente.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"
    )

    # Ejecuta el análisis léxico.
    resultado = analizador.analizar(codigo_fuente)

    # Filtra la lista de tokens para conservar únicamente aquellos
    # cuyo tipo sea IDENTIFIER.
    identificadores = [
        token
        for token in resultado.tokens
        if token.tipo == "IDENTIFIER"
    ]

    # Comprueba que exista exactamente un identificador reconocido.
    assert len(identificadores) == 1

    # Comprueba que el valor del identificador sea "Oficina".
    assert identificadores[0].valor == "Oficina"

    # Verifica que no se haya generado ningún diagnóstico.
    assert resultado.diagnosticos == []


# Comprueba una característica conservada desde TecNet Finder de LyA I:
# IP, MASK y HOSTS pueden aparecer directamente unidos al valor
# siguiente cuando la expresión regular permite reconocerlos sin
# producir ambigüedad.
def prueba_palabras_reservadas_pegadas():

    # Crea una instancia del analizador.
    analizador = AnalizadorLexico()

    # Define una entrada donde algunas palabras reservadas aparecen
    # directamente unidas al valor que las sigue.
    codigo_fuente = (
        "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"
    )

    # Ejecuta el análisis léxico.
    resultado = analizador.analizar(codigo_fuente)

    # Obtiene los tipos de todos los tokens reconocidos.
    tipos_obtenidos = [
        token.tipo
        for token in resultado.tokens
    ]

    # Define la secuencia de tokens que debería producir esta entrada.
    tipos_esperados = [
        "IP",
        "IP_ADDRESS",
        "MASK",
        "SUBNET_MASK",
        "HOSTS",
        "NUMBER",
        "NAME",
        "IDENTIFIER",
    ]

    # Comprueba que la secuencia obtenida sea correcta.
    assert tipos_obtenidos == tipos_esperados

    # Verifica que esta forma permitida no produzca errores léxicos.
    assert resultado.diagnosticos == []


# Comprueba que una dirección IP incompleta no sea tratada
# automáticamente como error léxico.
#
# Esta decisión viene del diseño realizado en Lenguajes y Autómatas I.
# El lexer reconoce las partes posibles de la dirección mediante
# NUMBER y DOT para que posteriormente el analizador sintáctico pueda
# determinar que la estructura de la IP está incompleta.
def prueba_ip_incompleta_no_es_error_lexico():

    # Crea una instancia del analizador léxico.
    analizador = AnalizadorLexico()

    # Define una instrucción cuya dirección IP está incompleta.
    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50"
    )

    # Ejecuta el análisis.
    resultado = analizador.analizar(codigo_fuente)

    # Obtiene solamente los tipos de token reconocidos.
    tipos_obtenidos = [
        token.tipo
        for token in resultado.tokens
    ]

    # Comprueba que las partes numéricas de la IP hayan sido
    # reconocidas mediante tokens NUMBER.
    assert "NUMBER" in tipos_obtenidos

    # Comprueba que los puntos también hayan sido reconocidos.
    assert "DOT" in tipos_obtenidos

    # Verifica que el lexer no produzca un error por la IP incompleta.
    #
    # Posteriormente será responsabilidad del analizador sintáctico
    # determinar que la dirección no cumple la estructura esperada.
    assert resultado.diagnosticos == []