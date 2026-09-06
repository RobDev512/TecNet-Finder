from Compilador.analizador_lexico import AnalizadorLexico


def prueba_entrada_valida_completa():
    analizador = AnalizadorLexico()

    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"
    )

    resultado = analizador.analizar(codigo_fuente)

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

    tipos_obtenidos = [
        token.tipo
        for token in resultado.tokens
    ]

    assert tipos_obtenidos == tipos_esperados
    assert resultado.diagnosticos == []


def prueba_identificador_fuera_de_lugar():
    analizador = AnalizadorLexico()

    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 Oficina"
    )

    resultado = analizador.analizar(codigo_fuente)

    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].codigo == "LEX-001"
    assert resultado.diagnosticos[0].fragmento == "Oficina"


def prueba_simbolo_no_reconocido():
    analizador = AnalizadorLexico()

    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"
    )

    resultado = analizador.analizar(codigo_fuente)

    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].codigo == "LEX-002"
    assert resultado.diagnosticos[0].fragmento == "@"


def prueba_identificador_despues_de_name():
    analizador = AnalizadorLexico()

    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"
    )

    resultado = analizador.analizar(codigo_fuente)

    identificadores = [
        token
        for token in resultado.tokens
        if token.tipo == "IDENTIFIER"
    ]

    assert len(identificadores) == 1
    assert identificadores[0].valor == "Oficina"
    assert resultado.diagnosticos == []


def prueba_palabras_reservadas_pegadas():
    analizador = AnalizadorLexico()

    codigo_fuente = (
        "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"
    )

    resultado = analizador.analizar(codigo_fuente)

    tipos_obtenidos = [
        token.tipo
        for token in resultado.tokens
    ]

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


def prueba_ip_incompleta_no_es_error_lexico():
    analizador = AnalizadorLexico()

    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50"
    )

    resultado = analizador.analizar(codigo_fuente)

    # La IP incompleta debe dividirse en NUMBER y DOT.
    # Será responsabilidad del sintáctico rechazarla posteriormente.
    tipos_obtenidos = [
        token.tipo
        for token in resultado.tokens
    ]

    assert "NUMBER" in tipos_obtenidos
    assert "DOT" in tipos_obtenidos
    assert resultado.diagnosticos == []