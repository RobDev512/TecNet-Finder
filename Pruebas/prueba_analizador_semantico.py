# ============================================================
# Archivo: prueba_analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automatizadas correspondientes
# con la fase de análisis semántico de TecNet Finder.
#
# Actualmente verifica SEM-001 a SEM-005:
# máscara, dirección de red, hosts positivos y capacidad VLSM.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa el lexer real para generar los tokens utilizados por las pruebas.
from Compilador.analizador_semantico import AnalizadorSemantico  # Importa la fase semántica que será evaluada.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa el parser real para obtener bloques sintácticamente válidos.


def analizar_semanticamente(codigo_fuente: str):  # Ejecuta las fases previas necesarias antes de invocar directamente el analizador semántico.
    resultado_lexico = AnalizadorLexico().analizar(codigo_fuente)  # Convierte el código de prueba en tokens utilizando el lexer real.
    resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()  # Construye los bloques sintácticos a partir de los tokens reconocidos.

    assert not resultado_lexico.tiene_errores  # Garantiza que la prueba no esté fallando por una causa léxica ajena al semántico.
    assert not resultado_sintactico.tiene_errores  # Garantiza que todos los bloques usados para la prueba superaron la gramática.

    return AnalizadorSemantico(
        bloques=resultado_sintactico.bloques,
        tokens=resultado_lexico.tokens,
    ).analizar()  # Ejecuta exclusivamente la fase semántica sobre una entrada previamente válida.


def prueba_sem001_acepta_limites_y_mascara_intermedia():
    codigo_fuente = (
        "IP 10.0.0.0 MASK /8 HOSTS 50 NAME RedA\n"
        "IP 192.168.1.0 MASK /24 HOSTS 30 NAME RedB\n"
        "IP 192.168.2.0 MASK /30 HOSTS 1 NAME RedC"
    )
    resultado = analizar_semanticamente(codigo_fuente)

    assert len(resultado.bloques_validos) == 3
    assert resultado.diagnosticos == []
    assert not resultado.tiene_errores


def prueba_sem001_rechaza_mascara_menor_que_ocho():
    codigo_fuente = "IP 10.0.0.0 MASK /7 HOSTS 50 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)

    assert resultado.bloques_validos == []
    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].codigo == "SEM-001"
    assert resultado.diagnosticos[0].fragmento == "/7"
    assert resultado.tiene_errores


def prueba_sem001_rechaza_mascara_mayor_que_treinta_y_ubica_fragmento():
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 50 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnostico = resultado.diagnosticos[0]
    columna_esperada = codigo_fuente.index("/31")

    assert diagnostico.codigo == "SEM-001"
    assert diagnostico.linea == 1
    assert diagnostico.columna == columna_esperada
    assert diagnostico.longitud == len("/31")
    assert diagnostico.fragmento == "/31"


def prueba_sem001_conserva_bloques_validos_cuando_otro_falla():
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Valida\n"
        "IP 10.0.0.0 MASK /31 HOSTS 1 NAME Invalida"
    )
    resultado = analizar_semanticamente(codigo_fuente)

    assert len(resultado.bloques_validos) == 1
    assert resultado.bloques_validos[0].nombre == "Valida"
    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].fragmento == "/31"


def prueba_sem002_rechaza_ip_que_no_es_direccion_de_red():
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnostico = resultado.diagnosticos[0]
    ip_incorrecta = "192.168.1.5"
    columna_esperada = codigo_fuente.index(ip_incorrecta)

    assert resultado.bloques_validos == []
    assert diagnostico.codigo == "SEM-002"
    assert diagnostico.linea == 1
    assert diagnostico.columna == columna_esperada
    assert diagnostico.longitud == len(ip_incorrecta)
    assert diagnostico.fragmento == ip_incorrecta
    assert "192.168.1.0" in diagnostico.mensaje


def prueba_sem003_rechaza_cantidad_cero_y_ubica_host():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnostico = resultado.diagnosticos[0]
    fragmento_hosts = "HOSTS 0"
    columna_esperada = codigo_fuente.index(fragmento_hosts) + len("HOSTS ")

    assert resultado.bloques_validos == []
    assert diagnostico.codigo == "SEM-003"
    assert diagnostico.linea == 1
    assert diagnostico.columna == columna_esperada
    assert diagnostico.longitud == len("0")
    assert diagnostico.fragmento == "0"


def prueba_sem003_detecta_cada_cero_dentro_de_lista_hosts():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,0,0 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)

    diagnosticos_sem003 = [
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-003"
    ]

    inicio_lista = codigo_fuente.index("50,0,0")
    columna_primer_cero = inicio_lista + len("50,")
    columna_segundo_cero = inicio_lista + len("50,0,")

    assert resultado.bloques_validos == []
    assert len(diagnosticos_sem003) == 2
    assert diagnosticos_sem003[0].columna == columna_primer_cero
    assert diagnosticos_sem003[1].columna == columna_segundo_cero
    assert all(diagnostico.fragmento == "0" for diagnostico in diagnosticos_sem003)


def prueba_sem002_y_sem003_pueden_detectarse_en_mismo_bloque():
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 0 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-002" in codigos
    assert "SEM-003" in codigos
    assert len(resultado.diagnosticos) == 2
    assert resultado.bloques_validos == []


def prueba_sem005_rechaza_solicitud_individual_demasiado_grande():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 500 NAME Gigante"
    resultado = analizar_semanticamente(codigo_fuente)

    diagnostico = next(
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-005"
    )

    assert resultado.bloques_validos == []
    assert diagnostico.fragmento == "500"
    assert diagnostico.columna == codigo_fuente.index("500")
    assert "512 direcciones" in diagnostico.mensaje
    assert "256 direcciones" in diagnostico.mensaje


def prueba_sem005_acepta_solicitud_que_cabe_exactamente_en_red():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 254 NAME Completa"
    resultado = analizar_semanticamente(codigo_fuente)
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-005" not in codigos
    assert "SEM-004" not in codigos
    assert len(resultado.bloques_validos) == 1


def prueba_sem004_rechaza_capacidad_total_real_de_vlsm():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 100,100,100 NAME Saturada"
    resultado = analizar_semanticamente(codigo_fuente)

    diagnostico = next(
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-004"
    )
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert resultado.bloques_validos == []
    assert "SEM-005" not in codigos
    assert diagnostico.fragmento == "HOSTS"
    assert diagnostico.columna == codigo_fuente.index("HOSTS")
    assert "384 direcciones" in diagnostico.mensaje
    assert "256 direcciones" in diagnostico.mensaje


def prueba_sem004_acepta_dos_bloques_que_ocupan_exactamente_la_red():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 100,100 NAME Completa"
    resultado = analizar_semanticamente(codigo_fuente)
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-004" not in codigos
    assert "SEM-005" not in codigos
    assert len(resultado.bloques_validos) == 1


def prueba_sem005_y_sem004_pueden_aparecer_juntos():
    codigo_fuente = "IP 192.168.1.0 MASK /30 HOSTS 50 NAME Imposible"
    resultado = analizar_semanticamente(codigo_fuente)
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-005" in codigos
    assert "SEM-004" in codigos
    assert resultado.bloques_validos == []


def prueba_capacidad_no_se_evalua_con_mascara_fuera_de_rango():
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 500 NAME Invalida"
    resultado = analizar_semanticamente(codigo_fuente)
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert codigos == ["SEM-001"]
    assert resultado.bloques_validos == []