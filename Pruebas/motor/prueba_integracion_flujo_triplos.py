
# ============================================================
# Archivo: prueba_integracion_flujo_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la integración del código intermedio
# con el flujo principal de compilación.
# ============================================================

from Motor.compilacion.flujo_compilacion import FlujoCompilacion
from Motor.compilacion.interprete_triplos import AsignacionVLSM


def prueba_flujo_genera_codigo_intermedio():
    fuente = "IP 192.168.1.0 MASK /24 HOSTS 10,50 NAME Oficina"
    resultado = FlujoCompilacion().analizar(fuente)

    assert resultado.codigo_intermedio is not None
    assert resultado.ejecucion_intermedia is not None

    codigo = resultado.codigo_intermedio.triplos
    valores = resultado.ejecucion_intermedia.valores
    comprobaciones = resultado.ejecucion_intermedia.comprobaciones

    assert len(codigo) == 15
    assert len(comprobaciones) == 15

    asignaciones = [
        valores[t.indice]
        for t in codigo
        if t.operador == "ASIGNAR_VLSM"
    ]

    assert len(asignaciones) == len(resultado.subredes_vlsm) == 2

    for asignacion, subred in zip(
        asignaciones, resultado.subredes_vlsm
    ):
        assert isinstance(asignacion, AsignacionVLSM)
        assert str(asignacion.subred.network_address) == subred.direccion_de_red
        assert f"/{asignacion.subred.prefixlen}" == subred.nueva_mascara
        assert str(asignacion.subred.broadcast_address) == (
            subred.direccion_de_broadcast
        )

    assert resultado.subredes_vlsm[0].nombre_red == "Oficina"


def prueba_flujo_varias_redes_con_triplos():
    fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"
    )

    resultado = FlujoCompilacion().analizar(fuente)

    assert resultado.codigo_intermedio is not None
    assert resultado.ejecucion_intermedia is not None

    triplos = resultado.codigo_intermedio.triplos

    assert len(triplos) == 16
    assert triplos[0].operador == "INICIAR_RED"
    assert triplos[8].operador == "INICIAR_RED"
    assert triplos[8].origen.linea_origen == 2
    assert triplos[8].origen.indice_bloque == 1


def prueba_flujo_triplos_con_error_y_recuperacion():
    fuente = (
        "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )

    resultado = FlujoCompilacion().analizar(fuente)

    assert resultado.tiene_errores
    assert len(resultado.bloques_validos) == 1
    assert len(resultado.subredes_vlsm) == 1
    assert resultado.codigo_intermedio is not None

    triplos = resultado.codigo_intermedio.triplos

    assert len(triplos) == 8
    assert triplos[0].argumento1 == "10.0.0.0"
    assert triplos[0].origen.linea_origen == 2
    assert triplos[0].origen.indice_bloque == 0


def prueba_flujo_sin_bloques_validos():
    fuente = "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida"
    resultado = FlujoCompilacion().analizar(fuente)

    assert resultado.bloques_validos == []
    assert resultado.subredes_vlsm == []

    assert resultado.codigo_intermedio is not None
    assert resultado.codigo_intermedio.triplos == ()

    assert resultado.ejecucion_intermedia is not None
    assert resultado.ejecucion_intermedia.valores == {}
    assert resultado.ejecucion_intermedia.comprobaciones == {}
