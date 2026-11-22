# ============================================================
# Archivo: prueba_interprete_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
# ============================================================

from math import log2  # Aporta cálculos matemáticos para potencias, logaritmos y redondeos.
import pytest  # Habilita las pruebas parametrizadas y la comprobación de excepciones.
from Compilador.generador_triplos import GeneradorTriplos  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.modelos import BloqueRed  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.interprete_triplos import AsignacionVLSM, CursorRed, InterpreteTriplos  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.triplos import ReferenciaTriplo, ResultadoIntermedio  # Reutiliza la estructura de compilación compartida con las demás fases.

def prueba_operaciones_matematicas():  # Comprueba operaciones matematicas mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    suma = codigo.agregar("+", 50, 2)  # Genera la suma de hosts más dos direcciones reservadas.
    logaritmo = codigo.agregar("LOG2", ReferenciaTriplo(suma.indice))  # Genera el cálculo del logaritmo con referencia a la suma.
    redondeo = codigo.agregar("CEIL", ReferenciaTriplo(logaritmo.indice))  # Genera el redondeo del resultado del logaritmo.
    codigo.agregar("^", 2, ReferenciaTriplo(redondeo.indice))  # Agrega la operación y conserva su origen o referencia.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    assert ejecucion.valores[0] == 52  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.valores[1] == pytest.approx(log2(52))  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.valores[2] == 6  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.valores[3] == 64  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.comprobaciones[0] == "50 + 2 = 52 -> (0) = 52"  # Comprueba el desarrollo que aparecerá en la futura interfaz.
    assert "(3) = 64" in ejecucion.comprobaciones[3]  # Comprueba el desarrollo que aparecerá en la futura interfaz.

def prueba_suma_con_referencia():  # Comprueba suma con referencia mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    primero = codigo.agregar("+", 50, 2)  # Conserva el primer triplo que será referenciado.
    codigo.agregar("+", ReferenciaTriplo(primero.indice), 10)  # Agrega la operación y conserva su origen o referencia.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    assert ejecucion.valores[1] == 62  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.comprobaciones[1] == "(0) + 10 -> 52 + 10 = 62 -> (1) = 62"  # Comprueba el desarrollo que aparecerá en la futura interfaz.

@pytest.mark.parametrize("valor", [0, -5])
def prueba_logaritmo_invalido(valor):  # Comprueba logaritmo invalido mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    codigo.agregar("LOG2", valor)  # Agrega la operación y conserva su origen o referencia.
    with pytest.raises(ValueError, match="LOG2"):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        InterpreteTriplos().ejecutar(codigo)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_potencia_exponente_negativo():  # Comprueba potencia exponente negativo mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    codigo.agregar("^", 2, -1)  # Agrega la operación y conserva su origen o referencia.
    with pytest.raises(ValueError, match="potencia"):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        InterpreteTriplos().ejecutar(codigo)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_iniciar_red():  # Comprueba iniciar red mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    codigo.agregar("INICIAR_RED", "192.168.1.0", "/24")  # Agrega la operación y conserva su origen o referencia.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    cursor = ejecucion.valores[0]  # Obtiene o valida la posición de asignación en la red base.
    assert isinstance(cursor, CursorRed)  # Verifica que el resultado posea el modelo de datos esperado.
    assert cursor.red_base.with_prefixlen == "192.168.1.0/24"  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert cursor.direccion_actual == int(cursor.red_base.network_address)  # Comprueba el comportamiento esperado para esta entrada de prueba.

def prueba_interprete_sin_triplos():  # Comprueba interprete sin triplos mediante un caso reproducible.
    ejecucion = InterpreteTriplos().ejecutar(ResultadoIntermedio())  # Ejecuta los triplos para obtener valores y comprobaciones.
    assert ejecucion.valores == {}  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.comprobaciones == {}  # Comprueba el desarrollo que aparecerá en la futura interfaz.

def prueba_asignacion_vlsm_completa():  # Comprueba asignacion vlsm completa mediante un caso reproducible.
    bloque = BloqueRed("192.168.1.0", "/24", [10, 50, 20], "Oficina", 1)  # Conserva la información que se consulta en las verificaciones posteriores.
    codigo = GeneradorTriplos().generar([bloque])  # Genera el código intermedio para el escenario de prueba.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    asignaciones = [ejecucion.valores[triplo.indice] for triplo in codigo.triplos if triplo.operador == "ASIGNAR_VLSM"]  # Reúne las subredes producidas al ejecutar ASIGNAR_VLSM.
    assert [valor.subred.with_prefixlen for valor in asignaciones] == ["192.168.1.0/26", "192.168.1.64/27", "192.168.1.96/28"]  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    assert [valor.hosts for valor in asignaciones] == [50, 20, 10]  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    assert [str(valor.subred.broadcast_address) for valor in asignaciones] == ["192.168.1.63", "192.168.1.95", "192.168.1.111"]  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    assert str(ejecucion.valores[21].red_base.network_address) == "192.168.1.0"  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert "192.168.1.64" in ejecucion.comprobaciones[7]  # Comprueba el desarrollo que aparecerá en la futura interfaz.

def prueba_varias_redes_independientes():  # Comprueba varias redes independientes mediante un caso reproducible.
    bloques = [BloqueRed("192.168.1.0", "/24", [50, 10], "Oficina", 1), BloqueRed("10.0.0.0", "/24", [20], "Laboratorio", 2)]  # Prepara varias redes para comprobar su independencia.
    codigo = GeneradorTriplos().generar(bloques)  # Genera el código intermedio para el escenario de prueba.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    assert ejecucion.valores[6].subred.with_prefixlen == "192.168.1.0/26"  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.valores[13].subred.with_prefixlen == "192.168.1.64/28"  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert ejecucion.valores[21].subred.with_prefixlen == "10.0.0.0/27"  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.

def prueba_hosts_repetidos():  # Comprueba hosts repetidos mediante un caso reproducible.
    codigo = GeneradorTriplos().generar([BloqueRed("192.168.1.0", "/24", [20, 50, 20], "Oficina", 1)])  # Genera el código intermedio para el escenario de prueba.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    assert [ejecucion.valores[i].subred.with_prefixlen for i in (6, 13, 20)] == ["192.168.1.0/26", "192.168.1.64/27", "192.168.1.96/27"]  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert [codigo.triplos[i].origen.indice_host for i in (6, 13, 20)] == [1, 0, 2]  # Verifica que se conserve la posición original de la solicitud HOSTS.

def prueba_red_sin_capacidad():  # Comprueba red sin capacidad mediante un caso reproducible.
    codigo = GeneradorTriplos().generar([BloqueRed("192.168.1.0", "/30", [2, 1], "Invalida", 1)])  # Genera el código intermedio para el escenario de prueba.
    with pytest.raises(ValueError, match="capacidad"):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        InterpreteTriplos().ejecutar(codigo)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_solicitud_tamano_incorrecto():  # Comprueba solicitud tamano incorrecto mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    suma = codigo.agregar("+", 50, 2)  # Genera la suma de hosts más dos direcciones reservadas.
    codigo.agregar("SOLICITUD", 50, ReferenciaTriplo(suma.indice))  # Agrega la operación y conserva su origen o referencia.
    with pytest.raises(ValueError, match="tamaño de bloque"):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        InterpreteTriplos().ejecutar(codigo)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_asignacion_referencias_invalidas():  # Comprueba asignacion referencias invalidas mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    t0 = codigo.agregar("+", 50, 2)  # Conserva la información que se consulta en las verificaciones posteriores.
    codigo.agregar("ASIGNAR_VLSM", ReferenciaTriplo(t0.indice), ReferenciaTriplo(t0.indice))  # Agrega la operación y conserva su origen o referencia.
    with pytest.raises(ValueError, match="cursor y una solicitud"):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        InterpreteTriplos().ejecutar(codigo)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_red_ipv4_invalida():  # Comprueba red ipv4 invalida mediante un caso reproducible.
    codigo = ResultadoIntermedio()  # Prepara una secuencia de triplos para esta comprobación.
    codigo.agregar("INICIAR_RED", "192.168.1.10", "/24")  # Agrega la operación y conserva su origen o referencia.
    with pytest.raises(ValueError, match="red IPv4 válida"):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        InterpreteTriplos().ejecutar(codigo)  # Ejecuta la operación necesaria para la prueba o el procesamiento.
