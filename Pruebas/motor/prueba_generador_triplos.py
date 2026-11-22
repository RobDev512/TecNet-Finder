# ============================================================
# Archivo: prueba_generador_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que el generador construya correctamente
# las operaciones y referencias de los triplos.
# ============================================================

from Compilador.generador_triplos import GeneradorTriplos  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.modelos import BloqueRed  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.triplos import ReferenciaTriplo  # Reutiliza la estructura de compilación compartida con las demás fases.

def prueba_generacion_vlsm():  # Comprueba generacion vlsm mediante un caso reproducible.
    bloque = BloqueRed("192.168.1.0", "/24", [10, 50], "Oficina", 1)  # Conserva la información que se consulta en las verificaciones posteriores.
    resultado = GeneradorTriplos().generar([bloque])  # Obtiene los triplos de los bloques empleados en la prueba.
    triplos = resultado.triplos  # Conserva la información que se consulta en las verificaciones posteriores.
    assert len(triplos) == 15  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert triplos[1].argumento1 == 50  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[8].argumento1 == 10  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[6].operador == "ASIGNAR_VLSM"  # Comprueba que se haya generado el operador correcto.
    assert triplos[6].argumento1 == ReferenciaTriplo(0)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[6].argumento2 == ReferenciaTriplo(5)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[13].operador == "ASIGNAR_VLSM"  # Comprueba que se haya generado el operador correcto.
    assert triplos[13].argumento1 == ReferenciaTriplo(7)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[13].argumento2 == ReferenciaTriplo(12)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[1].origen.indice_host == 1  # Verifica que se conserve la posición original de la solicitud HOSTS.
    assert triplos[8].origen.indice_host == 0  # Verifica que se conserve la posición original de la solicitud HOSTS.

def prueba_generacion_varias_redes():  # Comprueba generacion varias redes mediante un caso reproducible.
    bloques = [BloqueRed("192.168.1.0", "/24", [50, 10], "Oficina", 1), BloqueRed("10.0.0.0", "/24", [20], "Laboratorio", 2)]  # Prepara varias redes para comprobar su independencia.
    resultado = GeneradorTriplos().generar(bloques)  # Obtiene los triplos de los bloques empleados en la prueba.
    triplos = resultado.triplos  # Conserva la información que se consulta en las verificaciones posteriores.
    assert len(triplos) == 23  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert triplos[15].operador == "INICIAR_RED"  # Comprueba que se haya generado el operador correcto.
    assert triplos[15].argumento1 == "10.0.0.0"  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[15].argumento2 == "/24"  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[21].operador == "ASIGNAR_VLSM"  # Comprueba que se haya generado el operador correcto.
    assert triplos[21].argumento1 == ReferenciaTriplo(15)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[21].argumento2 == ReferenciaTriplo(20)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[21].origen.linea_origen == 2  # Comprueba que la referencia conserve la línea real del código fuente.
    assert triplos[21].origen.indice_bloque == 1  # Verifica la procedencia del triplo dentro de los bloques validados.

def prueba_generacion_sin_bloques():  # Comprueba generacion sin bloques mediante un caso reproducible.
    resultado = GeneradorTriplos().generar([])  # Obtiene los triplos de los bloques empleados en la prueba.
    assert len(resultado.triplos) == 0  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert resultado.triplos == ()  # Comprueba el comportamiento esperado para esta entrada de prueba.

def prueba_generacion_hosts_repetidos():  # Comprueba generacion hosts repetidos mediante un caso reproducible.
    bloque = BloqueRed("192.168.1.0", "/24", [20, 50, 20], "Oficina", 1)  # Conserva la información que se consulta en las verificaciones posteriores.
    resultado = GeneradorTriplos().generar([bloque])  # Obtiene los triplos de los bloques empleados en la prueba.
    triplos = resultado.triplos  # Conserva la información que se consulta en las verificaciones posteriores.
    assert len(triplos) == 22  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert triplos[1].argumento1 == 50  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[8].argumento1 == 20  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[15].argumento1 == 20  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[1].origen.indice_host == 1  # Verifica que se conserve la posición original de la solicitud HOSTS.
    assert triplos[8].origen.indice_host == 0  # Verifica que se conserve la posición original de la solicitud HOSTS.
    assert triplos[15].origen.indice_host == 2  # Verifica que se conserve la posición original de la solicitud HOSTS.
    assert triplos[6].argumento1 == ReferenciaTriplo(0)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[13].argumento1 == ReferenciaTriplo(7)  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[20].argumento1 == ReferenciaTriplo(14)  # Verifica el argumento o la referencia usada por el triplo.
