# ============================================================
# Archivo: prueba_generador_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que el generador construya correctamente
# las operaciones y referencias de los triplos.
# ============================================================

from Compilador.generador_triplos import GeneradorTriplos
from Motor.compilacion.modelos import BloqueRed
from Motor.compilacion.triplos import ReferenciaTriplo


def prueba_generacion_vlsm():
    bloque = BloqueRed(
        "192.168.1.0",
        "/24",
        [10, 50],
        "Oficina",
        1
    )

    resultado = GeneradorTriplos().generar([bloque])
    triplos = resultado.triplos

    # Una red y dos solicitudes de siete operaciones cada una.
    assert len(triplos) == 15

    # Comprueba que los hosts se procesen de mayor a menor.
    assert triplos[1].argumento1 == 50
    assert triplos[8].argumento1 == 10

    # Comprueba las referencias de la primera asignación.
    assert triplos[6].operador == "ASIGNAR_VLSM"
    assert triplos[6].argumento1 == ReferenciaTriplo(0)
    assert triplos[6].argumento2 == ReferenciaTriplo(5)

    # La segunda asignación utiliza el cursor anterior.
    assert triplos[13].operador == "ASIGNAR_VLSM"
    assert triplos[13].argumento1 == ReferenciaTriplo(7)
    assert triplos[13].argumento2 == ReferenciaTriplo(12)

    # Conserva la posición original de cada solicitud.
    assert triplos[1].origen.indice_host == 1
    assert triplos[8].origen.indice_host == 0


def prueba_generacion_varias_redes():
    bloques = [
        BloqueRed(
            "192.168.1.0", "/24", [50, 10], "Oficina", 1
        ),
        BloqueRed(
            "10.0.0.0", "/24", [20], "Laboratorio", 2
        ),
    ]

    resultado = GeneradorTriplos().generar(bloques)
    triplos = resultado.triplos

    # La primera red genera 15 triplos y la segunda genera 8.
    assert len(triplos) == 23

    # Comprueba que la segunda red comience en su propio contexto.
    assert triplos[15].operador == "INICIAR_RED"
    assert triplos[15].argumento1 == "10.0.0.0"
    assert triplos[15].argumento2 == "/24"

    # La asignación del Laboratorio debe usar su propio cursor.
    assert triplos[21].operador == "ASIGNAR_VLSM"
    assert triplos[21].argumento1 == ReferenciaTriplo(15)
    assert triplos[21].argumento2 == ReferenciaTriplo(20)

    # Comprueba que se conserve el origen de la segunda red.
    assert triplos[21].origen.linea_origen == 2
    assert triplos[21].origen.indice_bloque == 1


def prueba_generacion_sin_bloques():
    resultado = GeneradorTriplos().generar([])

    assert len(resultado.triplos) == 0
    assert resultado.triplos == ()


def prueba_generacion_hosts_repetidos():
    bloque = BloqueRed(
        "192.168.1.0",
        "/24",
        [20, 50, 20],
        "Oficina",
        1
    )

    resultado = GeneradorTriplos().generar([bloque])
    triplos = resultado.triplos

    # Una red y tres solicitudes de siete operaciones.
    assert len(triplos) == 22

    # Comprueba el orden de procesamiento de los hosts.
    assert triplos[1].argumento1 == 50
    assert triplos[8].argumento1 == 20
    assert triplos[15].argumento1 == 20

    # Comprueba que se conserven las posiciones originales.
    assert triplos[1].origen.indice_host == 1
    assert triplos[8].origen.indice_host == 0
    assert triplos[15].origen.indice_host == 2

    # Cada solicitud debe continuar desde el cursor anterior.
    assert triplos[6].argumento1 == ReferenciaTriplo(0)
    assert triplos[13].argumento1 == ReferenciaTriplo(7)
    assert triplos[20].argumento1 == ReferenciaTriplo(14)
