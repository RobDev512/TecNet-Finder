# ============================================================
# Archivo: prueba_analizador_lexico.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo contiene las pruebas automáticas del analizador
# léxico de TecNet Finder. Las pruebas verifican entradas válidas,
# errores léxicos y comportamientos heredados de LyA I.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa el analizador léxico que será evaluado.


def prueba_entrada_valida_completa():  # Comprueba una instrucción válida que utiliza los elementos principales del lenguaje.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción válida completa.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis léxico sobre la entrada.

    tipos_esperados = [  # Define la secuencia exacta de tipos de token que debe producir el lexer.
        "IP",  # Espera la palabra reservada IP.
        "IP_ADDRESS",  # Espera la dirección IPv4 completa.
        "MASK",  # Espera la palabra reservada MASK.
        "SUBNET_MASK",  # Espera la máscara CIDR.
        "HOSTS",  # Espera la palabra reservada HOSTS.
        "NUMBER",  # Espera la primera cantidad de hosts.
        "COMMA",  # Espera la primera coma separadora.
        "NUMBER",  # Espera la segunda cantidad de hosts.
        "COMMA",  # Espera la segunda coma separadora.
        "NUMBER",  # Espera la tercera cantidad de hosts.
        "NAME",  # Espera la palabra reservada NAME.
        "IDENTIFIER",  # Espera el nombre de la red.
    ]

    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae únicamente el tipo de cada token producido.
    assert tipos_obtenidos == tipos_esperados  # Comprueba que la secuencia obtenida coincida exactamente con la esperada.
    assert resultado.diagnosticos == []  # Comprueba que una entrada válida no produzca diagnósticos léxicos.


def prueba_identificador_fuera_de_lugar():  # Comprueba que un identificador sin NAME produzca LEX-001.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 Oficina"  # Coloca Oficina en una posición no permitida.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis sobre la entrada incorrecta.
    assert len(resultado.diagnosticos) == 1  # Comprueba que se haya generado exactamente un diagnóstico.
    assert resultado.diagnosticos[0].codigo == "LEX-001"  # Verifica que el código del error sea el esperado.
    assert resultado.diagnosticos[0].fragmento == "Oficina"  # Verifica que el fragmento incorrecto sea Oficina.


def prueba_simbolo_no_reconocido():  # Comprueba que un símbolo ajeno al lenguaje produzca LEX-002.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"  # Agrega @ como símbolo no reconocido.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis sobre la entrada incorrecta.
    assert len(resultado.diagnosticos) == 1  # Comprueba que se haya generado exactamente un diagnóstico.
    assert resultado.diagnosticos[0].codigo == "LEX-002"  # Verifica que el código corresponda al símbolo desconocido.
    assert resultado.diagnosticos[0].fragmento == "@"  # Verifica que el fragmento señalado sea exactamente @.


def prueba_identificador_despues_de_name():  # Comprueba que un identificador después de NAME sea aceptado.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"  # Define una instrucción válida con nombre.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis léxico.
    identificadores = [token for token in resultado.tokens if token.tipo == "IDENTIFIER"]  # Filtra únicamente los identificadores reconocidos.
    assert len(identificadores) == 1  # Comprueba que exista un solo identificador.
    assert identificadores[0].valor == "Oficina"  # Comprueba que su valor sea el nombre esperado.
    assert resultado.diagnosticos == []  # Verifica que no se produzcan errores léxicos.


def prueba_palabras_reservadas_pegadas():  # Comprueba que IP, MASK y HOSTS puedan aparecer unidos a su valor siguiente.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"  # Define una entrada válida con palabras reservadas pegadas.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis léxico.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae los tipos de token producidos.
    tipos_esperados = ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "NUMBER", "NAME", "IDENTIFIER"]  # Define la secuencia esperada.
    assert tipos_obtenidos == tipos_esperados  # Comprueba que el comportamiento heredado se conserve.
    assert resultado.diagnosticos == []  # Verifica que esta escritura permitida no produzca errores.


def prueba_ip_incompleta_no_es_error_lexico():  # Comprueba que una IP incompleta se deje para el análisis sintáctico.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1. MASK /24 HOSTS 50"  # Define una dirección IPv4 incompleta.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis léxico.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae los tipos de token reconocidos.
    assert "NUMBER" in tipos_obtenidos  # Comprueba que las partes numéricas de la IP se hayan reconocido.
    assert "DOT" in tipos_obtenidos  # Comprueba que los puntos de la IP también se hayan reconocido.
    assert resultado.diagnosticos == []  # Verifica que la IP incompleta no se clasifique como error léxico.
