# ============================================================
# Archivo: prueba_modelos_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba los modelos y las referencias de los triplos.
# ============================================================

import pytest

from Motor.compilacion.triplos import (
    ReferenciaTriplo,
    OrigenTriplo,
    Triplo,
    ResultadoIntermedio,
)


def prueba_referencia_valida():
    referencia = ReferenciaTriplo(0)

    assert referencia.indice == 0
    assert str(referencia) == "(0)"


def prueba_referencia_invalida():
    with pytest.raises(ValueError):
        ReferenciaTriplo(-1)

    with pytest.raises(ValueError):
        ReferenciaTriplo("0")


def prueba_origen_valido():
    origen = OrigenTriplo(2, 1, 0)

    assert origen.linea_origen == 2
    assert origen.indice_bloque == 1
    assert origen.indice_host == 0


def prueba_origen_invalido():
    with pytest.raises(ValueError):
        OrigenTriplo(0, 0)

    with pytest.raises(ValueError):
        OrigenTriplo(1, -1)

    with pytest.raises(ValueError):
        OrigenTriplo(1, 0, -1)


def prueba_triplo_valido():
    triplo = Triplo(0, "+", 50, 2)

    assert triplo.indice == 0
    assert triplo.operador == "+"
    assert str(triplo) == "(0): (+, 50, 2)"


def prueba_operador_invalido():
    with pytest.raises(ValueError):
        Triplo(0, "HOLA", 50, 2)


def prueba_cantidad_argumentos():
    with pytest.raises(ValueError):
        Triplo(0, "+", 50)

    with pytest.raises(ValueError):
        Triplo(0, "LOG2", 52, 2)


def prueba_numeracion_automatica():
    resultado = ResultadoIntermedio()

    primero = resultado.agregar("+", 50, 2)
    segundo = resultado.agregar(
        "LOG2",
        ReferenciaTriplo(primero.indice)
    )

    assert primero.indice == 0
    assert segundo.indice == 1
    assert len(resultado.triplos) == 2


def prueba_referencia_futura():
    resultado = ResultadoIntermedio()

    with pytest.raises(ValueError):
        resultado.agregar("+", ReferenciaTriplo(5), 2)

    assert len(resultado.triplos) == 0


def prueba_conserva_origen():
    resultado = ResultadoIntermedio()
    origen = OrigenTriplo(1, 0, 0)

    triplo = resultado.agregar("+", 50, 2, origen=origen)

    assert triplo.origen == origen
    assert triplo.origen.linea_origen == 1
    assert triplo.origen.indice_host == 0


def prueba_argumentos_invalidos():
    valores_invalidos = [
        [50, 30],
        True,
        3.5,
        "",
    ]

    for valor in valores_invalidos:
        with pytest.raises(ValueError):
            Triplo(0, "+", valor, 2)


def prueba_argumentos_validos():
    resultado = ResultadoIntermedio()

    primero = resultado.agregar("+", 50, 2)

    segundo = resultado.agregar(
        "LOG2",
        ReferenciaTriplo(primero.indice)
    )

    tercero = resultado.agregar(
        "INICIAR_RED",
        "192.168.1.0",
        "/24"
    )

    assert len(resultado.triplos) == 3
    assert segundo.argumento1 == ReferenciaTriplo(0)
    assert tercero.argumento1 == "192.168.1.0"



def prueba_operaciones_matematicas_rechazan_texto():
    casos_invalidos = [
        ("+", "Hola", 2),
        ("^", 2, "Mundo"),
        ("LOG2", "Texto", None),
        ("CEIL", "Texto", None),
    ]

    for operador, argumento1, argumento2 in casos_invalidos:
        with pytest.raises(ValueError):
            Triplo(0, operador, argumento1, argumento2)


def prueba_operadores_vlsm_validos():
    resultado = ResultadoIntermedio()

    t0 = resultado.agregar("INICIAR_RED", "192.168.1.0", "/24")
    t1 = resultado.agregar("+", 50, 2)
    t2 = resultado.agregar("LOG2", ReferenciaTriplo(t1.indice))
    t3 = resultado.agregar("CEIL", ReferenciaTriplo(t2.indice))
    t4 = resultado.agregar("^", 2, ReferenciaTriplo(t3.indice))

    t5 = resultado.agregar(
        "SOLICITUD", 50, ReferenciaTriplo(t4.indice)
    )

    t6 = resultado.agregar(
        "ASIGNAR_VLSM",
        ReferenciaTriplo(t0.indice),
        ReferenciaTriplo(t5.indice)
    )

    resultado.agregar(
        "SIGUIENTE_CURSOR",
        ReferenciaTriplo(t6.indice)
    )

    assert len(resultado.triplos) == 8
    assert resultado.triplos[6].operador == "ASIGNAR_VLSM"


def prueba_operadores_vlsm_invalidos():
    casos = [
        ("INICIAR_RED", 50, 2),
        ("SOLICITUD", 0, ReferenciaTriplo(0)),
        ("SOLICITUD", 50, 64),
        ("ASIGNAR_VLSM", 0, ReferenciaTriplo(1)),
        ("SIGUIENTE_CURSOR", 20, None),
    ]

    for operador, argumento1, argumento2 in casos:
        with pytest.raises(ValueError):
            Triplo(0, operador, argumento1, argumento2)
