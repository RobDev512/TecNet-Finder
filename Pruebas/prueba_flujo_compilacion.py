# ============================================================
# Archivo: prueba_flujo_compilacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba la integración de las fases disponibles
# actualmente dentro del flujo principal de TecNet Finder.
#
# Las pruebas verifican el recorrido completo desde el código
# fuente por análisis léxico, sintáctico y semántico hasta el
# cálculo de las subredes VLSM correspondientes.
# ============================================================

from Motor.flujo_compilacion import FlujoCompilacion  # Importa el coordinador que ejecuta las fases disponibles del proyecto.


def prueba_flujo_completo_con_entrada_valida():
    flujo = FlujoCompilacion()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"
    resultado = flujo.analizar(codigo_fuente)

    assert resultado.diagnosticos == []
    assert resultado.tiene_errores is False
    assert len(resultado.resultado_lexico.tokens) == 12
    assert len(resultado.bloques_validos) == 1
    assert len(resultado.subredes_vlsm) == 3


def prueba_flujo_conserva_resultados_sintacticos():
    flujo = FlujoCompilacion()
    codigo_fuente = "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"
    resultado = flujo.analizar(codigo_fuente)

    assert len(resultado.resultado_sintactico.arboles) == 1
    assert "BloqueRed: Laboratorio" in resultado.resultado_sintactico.arbol_textual
    assert "N → NAME IDENTIFIER" in resultado.resultado_sintactico.producciones_usadas
    assert "NAME Laboratorio" in resultado.resultado_sintactico.derivacion


def prueba_flujo_reune_diagnosticos_lexicos():
    flujo = FlujoCompilacion()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "LEX-002" in codigos
    assert resultado.tiene_errores is True


def prueba_flujo_recupera_instruccion_posterior():
    flujo = FlujoCompilacion()
    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SIN-001" in codigos
    assert len(resultado.bloques_validos) == 1
    assert resultado.bloques_validos[0].nombre == "Correcta"
    assert len(resultado.subredes_vlsm) == 1
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"


def prueba_flujo_procesa_multiples_bloques():
    flujo = FlujoCompilacion()
    codigo_fuente = (
        "IP 192.168.10.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"
    )
    resultado = flujo.analizar(codigo_fuente)

    assert len(resultado.bloques_validos) == 2
    assert len(resultado.subredes_vlsm) == 2
    assert resultado.subredes_vlsm[0].nombre_red == "Oficina"
    assert resultado.subredes_vlsm[1].nombre_red == "Laboratorio"


def prueba_flujo_semantico_controla_solicitud_extrema_antes_de_vlsm():
    flujo = FlujoCompilacion()
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 4294967296 NAME Gigante"
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert resultado.tiene_errores is True
    assert "SEM-005" in codigos
    assert "SEM-004" in codigos
    assert "GEN-001" not in codigos
    assert resultado.bloques_validos == []
    assert resultado.subredes_vlsm == []


def prueba_flujo_continua_despues_de_error_de_capacidad():
    flujo = FlujoCompilacion()
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 4294967296 NAME Gigante\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-005" in codigos
    assert "SEM-004" in codigos
    assert "ADV-001" in codigos
    assert "GEN-001" not in codigos
    assert len(resultado.bloques_validos) == 1
    assert resultado.bloques_validos[0].nombre == "Correcta"
    assert len(resultado.subredes_vlsm) == 1
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"


def prueba_flujo_sem001_impide_que_mascara_invalida_llegue_a_vlsm():
    flujo = FlujoCompilacion()
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida"
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert resultado.resultado_semantico is not None
    assert len(resultado.resultado_sintactico.bloques) == 1
    assert "SEM-001" in codigos
    assert resultado.bloques_validos == []
    assert resultado.subredes_vlsm == []
    assert resultado.tiene_errores is True


def prueba_flujo_sem001_permite_procesamiento_parcial():
    flujo = FlujoCompilacion()
    codigo_fuente = (
        "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-001" in codigos
    assert "ADV-001" in codigos
    assert len(resultado.resultado_sintactico.bloques) == 2
    assert len(resultado.bloques_validos) == 1
    assert resultado.bloques_validos[0].nombre == "Correcta"
    assert len(resultado.subredes_vlsm) == 1
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"


def prueba_flujo_sem002_impide_que_ip_host_llegue_a_vlsm():
    flujo = FlujoCompilacion()
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Invalida"
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-002" in codigos
    assert len(resultado.resultado_sintactico.bloques) == 1
    assert resultado.bloques_validos == []
    assert resultado.subredes_vlsm == []


def prueba_flujo_sem003_permite_procesamiento_parcial():
    flujo = FlujoCompilacion()
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Invalida\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )
    resultado = flujo.analizar(codigo_fuente)

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]

    assert "SEM-003" in codigos
    assert "ADV-001" in codigos
    assert len(resultado.resultado_sintactico.bloques) == 2
    assert len(resultado.bloques_validos) == 1
    assert resultado.bloques_validos[0].nombre == "Correcta"
    assert len(resultado.subredes_vlsm) == 1
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"