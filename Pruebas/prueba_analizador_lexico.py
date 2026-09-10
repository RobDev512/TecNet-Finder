# ============================================================
# Archivo: prueba_analizador_lexico.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo contiene las pruebas automáticas del analizador
# léxico de TecNet Finder. Las pruebas verifican entradas válidas,
# errores léxicos y comportamientos heredados de LyA I.
#
# También comprueba los diagnósticos agregados durante el refuerzo
# previo a la implementación formal del análisis semántico.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa el analizador léxico que será evaluado.


def prueba_entrada_valida_completa():  # Comprueba una instrucción válida que utiliza los elementos principales del lenguaje.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción válida completa.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el análisis léxico sobre la entrada.

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

    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae únicamente el tipo de cada token producido.
    assert tipos_obtenidos == tipos_esperados  # Comprueba que la secuencia obtenida coincida exactamente con la esperada.
    assert resultado.diagnosticos == []  # Comprueba que una entrada válida no produzca diagnósticos léxicos.


def prueba_identificador_fuera_de_lugar():  # Comprueba que un identificador sin NAME produzca LEX-001.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 Oficina"
    resultado = analizador.analizar(codigo_fuente)

    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].codigo == "LEX-001"
    assert resultado.diagnosticos[0].categoria == "Léxico"
    assert resultado.diagnosticos[0].fragmento == "Oficina"


def prueba_simbolo_no_reconocido():  # Comprueba que un símbolo ajeno al lenguaje produzca LEX-002.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"
    resultado = analizador.analizar(codigo_fuente)

    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].codigo == "LEX-002"
    assert resultado.diagnosticos[0].categoria == "Léxico"
    assert resultado.diagnosticos[0].fragmento == "@"


def prueba_identificador_despues_de_name():  # Comprueba que un identificador después de NAME sea aceptado.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"
    resultado = analizador.analizar(codigo_fuente)

    identificadores = [token for token in resultado.tokens if token.tipo == "IDENTIFIER"]

    assert len(identificadores) == 1
    assert identificadores[0].valor == "Oficina"
    assert resultado.diagnosticos == []


def prueba_palabras_reservadas_pegadas():  # Comprueba que IP, MASK y HOSTS puedan aparecer unidos a su valor siguiente.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"
    resultado = analizador.analizar(codigo_fuente)

    tipos_obtenidos = [token.tipo for token in resultado.tokens]
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

    assert tipos_obtenidos == tipos_esperados
    assert resultado.diagnosticos == []


def prueba_ip_incompleta_no_es_error_lexico():  # Comprueba que una IP incompleta se deje para el análisis sintáctico.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1. MASK /24 HOSTS 50"
    resultado = analizador.analizar(codigo_fuente)

    tipos_obtenidos = [token.tipo for token in resultado.tokens]

    assert "NUMBER" in tipos_obtenidos
    assert "DOT" in tipos_obtenidos
    assert resultado.diagnosticos == []


def prueba_palabra_reservada_con_mayusculas_incorrectas():  # Comprueba que una palabra reservada existente pero mal capitalizada produzca LEX-003.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 mask /24 HOSTS 50 NAME Oficina"
    resultado = analizador.analizar(codigo_fuente)

    diagnosticos_lex_003 = [
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "LEX-003"
    ]

    assert len(diagnosticos_lex_003) == 1
    assert diagnosticos_lex_003[0].categoria == "Léxico"
    assert diagnosticos_lex_003[0].fragmento == "mask"
    assert diagnosticos_lex_003[0].linea == 1
    assert diagnosticos_lex_003[0].columna == 15


def prueba_lex_003_no_reemplaza_identificador_mal_escrito_generico():  # Conserva LEX-001 para textos como MAS que no son una palabra reservada real.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 MAS /24 HOSTS 50 NAME Oficina"
    resultado = analizador.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "LEX-001" in codigos
    assert "LEX-003" not in codigos


def prueba_elemento_numerico_unido_a_texto():  # Comprueba que un número seguido directamente por letras produzca LEX-004.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50NAME Oficina"
    resultado = analizador.analizar(codigo_fuente)

    diagnosticos_lex_004 = [
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "LEX-004"
    ]

    assert len(diagnosticos_lex_004) == 1
    assert diagnosticos_lex_004[0].categoria == "Léxico"
    assert diagnosticos_lex_004[0].fragmento == "50NAME"


def prueba_mascara_unida_a_texto_produce_lex_004():  # Comprueba que una máscara CIDR pegada a letras tampoco se divida artificialmente en dos tokens.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP 192.168.1.0 MASK /24HOSTS 50 NAME Oficina"
    resultado = analizador.analizar(codigo_fuente)

    diagnosticos_lex_004 = [
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "LEX-004"
    ]

    assert len(diagnosticos_lex_004) == 1
    assert diagnosticos_lex_004[0].fragmento == "/24HOSTS"


def prueba_lex_004_no_afecta_palabra_reservada_pegada_al_valor():  # Conserva la escritura histórica IP192, MASK/24 y HOSTS50 como léxicamente válida.
    analizador = AnalizadorLexico()
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"
    resultado = analizador.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "LEX-004" not in codigos
    assert resultado.diagnosticos == []