# ============================================================
# Archivo: prueba_analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automatizadas correspondientes
# con la fase de análisis semántico de TecNet Finder.
#
# Actualmente verifica SEM-001 a SEM-006:
# máscara, dirección de red, hosts, capacidad y traslapes.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico
from Compilador.analizador_semantico import AnalizadorSemantico
from Compilador.analizador_sintactico import AnalizadorSintactico


def analizar_semanticamente(codigo_fuente: str):
    resultado_lexico = AnalizadorLexico().analizar(codigo_fuente)
    resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()

    assert not resultado_lexico.tiene_errores
    assert not resultado_sintactico.tiene_errores

    return AnalizadorSemantico(
        bloques=resultado_sintactico.bloques,
        tokens=resultado_lexico.tokens,
    ).analizar()


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
    resultado = analizar_semanticamente(
        "IP 10.0.0.0 MASK /7 HOSTS 50 NAME Oficina"
    )

    assert resultado.bloques_validos == []
    assert len(resultado.diagnosticos) == 1
    assert resultado.diagnosticos[0].codigo == "SEM-001"
    assert resultado.diagnosticos[0].fragmento == "/7"


def prueba_sem001_rechaza_mascara_mayor_que_treinta_y_ubica_fragmento():
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 50 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnostico = resultado.diagnosticos[0]

    assert diagnostico.codigo == "SEM-001"
    assert diagnostico.linea == 1
    assert diagnostico.columna == codigo_fuente.index("/31")
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


def prueba_sem002_rechaza_ip_que_no_es_direccion_de_red():
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnostico = resultado.diagnosticos[0]

    assert resultado.bloques_validos == []
    assert diagnostico.codigo == "SEM-002"
    assert diagnostico.columna == codigo_fuente.index("192.168.1.5")
    assert diagnostico.fragmento == "192.168.1.5"
    assert "192.168.1.0" in diagnostico.mensaje


def prueba_sem003_rechaza_cantidad_cero_y_ubica_host():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnostico = resultado.diagnosticos[0]

    assert resultado.bloques_validos == []
    assert diagnostico.codigo == "SEM-003"
    assert diagnostico.columna == codigo_fuente.index("HOSTS 0") + len("HOSTS ")
    assert diagnostico.fragmento == "0"


def prueba_sem003_detecta_cada_cero_dentro_de_lista_hosts():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,0,0 NAME Oficina"
    resultado = analizar_semanticamente(codigo_fuente)
    diagnosticos = [
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-003"
    ]

    inicio_lista = codigo_fuente.index("50,0,0")

    assert len(diagnosticos) == 2
    assert diagnosticos[0].columna == inicio_lista + len("50,")
    assert diagnosticos[1].columna == inicio_lista + len("50,0,")


def prueba_sem002_y_sem003_pueden_detectarse_en_mismo_bloque():
    resultado = analizar_semanticamente(
        "IP 192.168.1.5 MASK /24 HOSTS 0 NAME Oficina"
    )
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-002" in codigos
    assert "SEM-003" in codigos
    assert resultado.bloques_validos == []


def prueba_sem005_rechaza_solicitud_individual_demasiado_grande():
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 500 NAME Gigante"
    resultado = analizar_semanticamente(codigo_fuente)

    diagnostico = next(
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-005"
    )

    assert diagnostico.fragmento == "500"
    assert "512 direcciones" in diagnostico.mensaje
    assert "256 direcciones" in diagnostico.mensaje


def prueba_sem005_acepta_solicitud_que_cabe_exactamente_en_red():
    resultado = analizar_semanticamente(
        "IP 192.168.1.0 MASK /24 HOSTS 254 NAME Completa"
    )
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

    assert diagnostico.fragmento == "HOSTS"
    assert "384 direcciones" in diagnostico.mensaje
    assert "256 direcciones" in diagnostico.mensaje


def prueba_sem004_acepta_dos_bloques_que_ocupan_exactamente_la_red():
    resultado = analizar_semanticamente(
        "IP 192.168.1.0 MASK /24 HOSTS 100,100 NAME Completa"
    )

    assert resultado.diagnosticos == []
    assert len(resultado.bloques_validos) == 1


def prueba_sem005_y_sem004_pueden_aparecer_juntos():
    resultado = analizar_semanticamente(
        "IP 192.168.1.0 MASK /30 HOSTS 50 NAME Imposible"
    )
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-005" in codigos
    assert "SEM-004" in codigos


def prueba_capacidad_no_se_evalua_con_mascara_fuera_de_rango():
    resultado = analizar_semanticamente(
        "IP 192.168.1.0 MASK /31 HOSTS 500 NAME Invalida"
    )
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert codigos == ["SEM-001"]


def prueba_sem006_rechaza_segunda_red_traslapada_y_ubica_ip():
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"
    )
    resultado = analizar_semanticamente(codigo_fuente)

    diagnostico = next(
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-006"
    )

    assert len(resultado.bloques_validos) == 1
    assert resultado.bloques_validos[0].nombre == "Oficina"
    assert diagnostico.linea == 2
    assert diagnostico.fragmento == "192.168.1.128"
    assert "192.168.1.0/24" in diagnostico.mensaje
    assert "línea 1" in diagnostico.mensaje


def prueba_sem006_acepta_redes_adyacentes_sin_traslape():
    codigo_fuente = (
        "IP 192.168.1.0 MASK /25 HOSTS 50 NAME Izquierda\n"
        "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Derecha"
    )
    resultado = analizar_semanticamente(codigo_fuente)

    assert resultado.diagnosticos == []
    assert len(resultado.bloques_validos) == 2


def prueba_sem006_conserva_bloques_independientes_despues_de_conflicto():
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Traslapada\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"
    )
    resultado = analizar_semanticamente(codigo_fuente)

    nombres_validos = [bloque.nombre for bloque in resultado.bloques_validos]
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert nombres_validos == ["Oficina", "Central"]
    assert codigos == ["SEM-006"]