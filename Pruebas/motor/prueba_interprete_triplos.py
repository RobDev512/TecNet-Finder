# ============================================================
# Archivo: prueba_interprete_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
# ============================================================

from math import log2

import pytest

from Compilador.generador_triplos import GeneradorTriplos
from Motor.compilacion.modelos import BloqueRed
from Motor.compilacion.interprete_triplos import (
    AsignacionVLSM,
    CursorRed,
    InterpreteTriplos,
)
from Motor.compilacion.triplos import ReferenciaTriplo, ResultadoIntermedio


def prueba_operaciones_matematicas():
    codigo = ResultadoIntermedio()
    suma = codigo.agregar("+", 50, 2)
    logaritmo = codigo.agregar("LOG2", ReferenciaTriplo(suma.indice))
    redondeo = codigo.agregar("CEIL", ReferenciaTriplo(logaritmo.indice))
    codigo.agregar("^", 2, ReferenciaTriplo(redondeo.indice))
    ejecucion = InterpreteTriplos().ejecutar(codigo)
    assert ejecucion.valores[0] == 52
    assert ejecucion.valores[1] == pytest.approx(log2(52))
    assert ejecucion.valores[2] == 6
    assert ejecucion.valores[3] == 64
    assert ejecucion.comprobaciones[0] == "50 + 2 = 52 -> (0) = 52"
    assert "(3) = 64" in ejecucion.comprobaciones[3]


def prueba_suma_con_referencia():
    codigo = ResultadoIntermedio()
    primero = codigo.agregar("+", 50, 2)
    codigo.agregar("+", ReferenciaTriplo(primero.indice), 10)
    ejecucion = InterpreteTriplos().ejecutar(codigo)
    assert ejecucion.valores[1] == 62
    assert ejecucion.comprobaciones[1] == "(0) + 10 -> 52 + 10 = 62 -> (1) = 62"


@pytest.mark.parametrize("valor", [0, -5])
def prueba_logaritmo_invalido(valor):
    codigo = ResultadoIntermedio()
    codigo.agregar("LOG2", valor)
    with pytest.raises(ValueError, match="LOG2"):
        InterpreteTriplos().ejecutar(codigo)


def prueba_potencia_exponente_negativo():
    codigo = ResultadoIntermedio()
    codigo.agregar("^", 2, -1)
    with pytest.raises(ValueError, match="potencia"):
        InterpreteTriplos().ejecutar(codigo)


def prueba_iniciar_red():
    codigo = ResultadoIntermedio()
    codigo.agregar("INICIAR_RED", "192.168.1.0", "/24")
    ejecucion = InterpreteTriplos().ejecutar(codigo)
    cursor = ejecucion.valores[0]
    assert isinstance(cursor, CursorRed)
    assert cursor.red_base.with_prefixlen == "192.168.1.0/24"
    assert cursor.direccion_actual == int(cursor.red_base.network_address)


def prueba_interprete_sin_triplos():
    ejecucion = InterpreteTriplos().ejecutar(ResultadoIntermedio())
    assert ejecucion.valores == {}
    assert ejecucion.comprobaciones == {}


def prueba_asignacion_vlsm_completa():
    bloque = BloqueRed("192.168.1.0", "/24", [10, 50, 20], "Oficina", 1)
    codigo = GeneradorTriplos().generar([bloque])
    ejecucion = InterpreteTriplos().ejecutar(codigo)
    asignaciones = [
        ejecucion.valores[triplo.indice]
        for triplo in codigo.triplos
        if triplo.operador == "ASIGNAR_VLSM"
    ]
    assert [valor.subred.with_prefixlen for valor in asignaciones] == [
        "192.168.1.0/26", "192.168.1.64/27", "192.168.1.96/28"
    ]
    assert [valor.hosts for valor in asignaciones] == [50, 20, 10]
    assert [str(valor.subred.broadcast_address) for valor in asignaciones] == [
        "192.168.1.63", "192.168.1.95", "192.168.1.111"
    ]
    assert str(ejecucion.valores[21].red_base.network_address) == "192.168.1.0"
    assert "192.168.1.64" in ejecucion.comprobaciones[7]


def prueba_varias_redes_independientes():
    bloques = [
        BloqueRed("192.168.1.0", "/24", [50, 10], "Oficina", 1),
        BloqueRed("10.0.0.0", "/24", [20], "Laboratorio", 2),
    ]
    codigo = GeneradorTriplos().generar(bloques)
    ejecucion = InterpreteTriplos().ejecutar(codigo)
    assert ejecucion.valores[6].subred.with_prefixlen == "192.168.1.0/26"
    assert ejecucion.valores[13].subred.with_prefixlen == "192.168.1.64/28"
    assert ejecucion.valores[21].subred.with_prefixlen == "10.0.0.0/27"


def prueba_hosts_repetidos():
    codigo = GeneradorTriplos().generar([
        BloqueRed("192.168.1.0", "/24", [20, 50, 20], "Oficina", 1)
    ])
    ejecucion = InterpreteTriplos().ejecutar(codigo)
    assert [ejecucion.valores[i].subred.with_prefixlen for i in (6, 13, 20)] == [
        "192.168.1.0/26", "192.168.1.64/27", "192.168.1.96/27"
    ]
    assert [codigo.triplos[i].origen.indice_host for i in (6, 13, 20)] == [1, 0, 2]


def prueba_red_sin_capacidad():
    # Caso deliberadamente inválido: el semántico lo rechazaría antes.
    codigo = GeneradorTriplos().generar([
        BloqueRed("192.168.1.0", "/30", [2, 1], "Invalida", 1)
    ])
    with pytest.raises(ValueError, match="capacidad"):
        InterpreteTriplos().ejecutar(codigo)


def prueba_solicitud_tamano_incorrecto():
    codigo = ResultadoIntermedio()
    suma = codigo.agregar("+", 50, 2)
    codigo.agregar("SOLICITUD", 50, ReferenciaTriplo(suma.indice))
    with pytest.raises(ValueError, match="tamaño de bloque"):
        InterpreteTriplos().ejecutar(codigo)


def prueba_asignacion_referencias_invalidas():
    codigo = ResultadoIntermedio()
    t0 = codigo.agregar("+", 50, 2)
    codigo.agregar(
        "ASIGNAR_VLSM", ReferenciaTriplo(t0.indice), ReferenciaTriplo(t0.indice)
    )
    with pytest.raises(ValueError, match="cursor y una solicitud"):
        InterpreteTriplos().ejecutar(codigo)


def prueba_red_ipv4_invalida():
    codigo = ResultadoIntermedio()
    codigo.agregar("INICIAR_RED", "192.168.1.10", "/24")
    with pytest.raises(ValueError, match="red IPv4 válida"):
        InterpreteTriplos().ejecutar(codigo)
