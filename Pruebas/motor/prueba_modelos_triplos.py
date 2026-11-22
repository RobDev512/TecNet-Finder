# ============================================================
# Archivo: prueba_modelos_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba los modelos y las referencias de los triplos.
# ============================================================

import pytest  # Habilita las pruebas parametrizadas y la comprobación de excepciones.
from Motor.compilacion.triplos import ReferenciaTriplo, OrigenTriplo, Triplo, ResultadoIntermedio  # Reutiliza la estructura de compilación compartida con las demás fases.

def prueba_referencia_valida():  # Comprueba referencia valida mediante un caso reproducible.
    referencia = ReferenciaTriplo(0)  # Consulta el resultado esperado para compararlo con los triplos.
    assert referencia.indice == 0  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert str(referencia) == "(0)"  # Comprueba la representación textual del resultado.

def prueba_referencia_invalida():  # Comprueba referencia invalida mediante un caso reproducible.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        ReferenciaTriplo(-1)  # Ejecuta la operación necesaria para la prueba o el procesamiento.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        ReferenciaTriplo("0")  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_origen_valido():  # Comprueba origen valido mediante un caso reproducible.
    origen = OrigenTriplo(2, 1, 0)  # Conserva la línea del bloque del que procede el triplo.
    assert origen.linea_origen == 2  # Comprueba que la referencia conserve la línea real del código fuente.
    assert origen.indice_bloque == 1  # Verifica la procedencia del triplo dentro de los bloques validados.
    assert origen.indice_host == 0  # Verifica que se conserve la posición original de la solicitud HOSTS.

def prueba_origen_invalido():  # Comprueba origen invalido mediante un caso reproducible.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        OrigenTriplo(0, 0)  # Ejecuta la operación necesaria para la prueba o el procesamiento.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        OrigenTriplo(1, -1)  # Ejecuta la operación necesaria para la prueba o el procesamiento.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        OrigenTriplo(1, 0, -1)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_triplo_valido():  # Comprueba triplo valido mediante un caso reproducible.
    triplo = Triplo(0, "+", 50, 2)  # Conserva la información que se consulta en las verificaciones posteriores.
    assert triplo.indice == 0  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert triplo.operador == "+"  # Comprueba que se haya generado el operador correcto.
    assert str(triplo) == "(0): (+, 50, 2)"  # Comprueba la representación textual del resultado.

def prueba_operador_invalido():  # Comprueba operador invalido mediante un caso reproducible.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        Triplo(0, "HOLA", 50, 2)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_cantidad_argumentos():  # Comprueba cantidad argumentos mediante un caso reproducible.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        Triplo(0, "+", 50)  # Ejecuta la operación necesaria para la prueba o el procesamiento.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        Triplo(0, "LOG2", 52, 2)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_numeracion_automatica():  # Comprueba numeracion automatica mediante un caso reproducible.
    resultado = ResultadoIntermedio()  # Prepara una nueva colección vacía de código intermedio.
    primero = resultado.agregar("+", 50, 2)  # Conserva el primer triplo que será referenciado.
    segundo = resultado.agregar("LOG2", ReferenciaTriplo(primero.indice))  # Comprueba que pueda generarse una referencia al primer triplo.
    assert primero.indice == 0  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert segundo.indice == 1  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert len(resultado.triplos) == 2  # Comprueba que la cantidad de operaciones generadas sea la prevista.

def prueba_referencia_futura():  # Comprueba referencia futura mediante un caso reproducible.
    resultado = ResultadoIntermedio()  # Prepara una nueva colección vacía de código intermedio.
    with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
        resultado.agregar("+", ReferenciaTriplo(5), 2)  # Agrega la operación y conserva su origen o referencia.
    assert len(resultado.triplos) == 0  # Comprueba que la cantidad de operaciones generadas sea la prevista.

def prueba_conserva_origen():  # Comprueba conserva origen mediante un caso reproducible.
    resultado = ResultadoIntermedio()  # Prepara una nueva colección vacía de código intermedio.
    origen = OrigenTriplo(1, 0, 0)  # Conserva la línea del bloque del que procede el triplo.
    triplo = resultado.agregar("+", 50, 2, origen=origen)  # Conserva la información que se consulta en las verificaciones posteriores.
    assert triplo.origen == origen  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert triplo.origen.linea_origen == 1  # Comprueba que la referencia conserve la línea real del código fuente.
    assert triplo.origen.indice_host == 0  # Verifica que se conserve la posición original de la solicitud HOSTS.

def prueba_argumentos_invalidos():  # Comprueba argumentos invalidos mediante un caso reproducible.
    valores_invalidos = [[50, 30], True, 3.5, ""]  # Reúne operandos de tipos que no son aceptables.
    for valor in valores_invalidos:  # Recorre los elementos necesarios sin cambiar su orden original.
        with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
            Triplo(0, "+", valor, 2)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_argumentos_validos():  # Comprueba argumentos validos mediante un caso reproducible.
    resultado = ResultadoIntermedio()  # Prepara una nueva colección vacía de código intermedio.
    primero = resultado.agregar("+", 50, 2)  # Conserva el primer triplo que será referenciado.
    segundo = resultado.agregar("LOG2", ReferenciaTriplo(primero.indice))  # Comprueba que pueda generarse una referencia al primer triplo.
    tercero = resultado.agregar("INICIAR_RED", "192.168.1.0", "/24")  # Construye una operación de red con argumentos textuales.
    assert len(resultado.triplos) == 3  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert segundo.argumento1 == ReferenciaTriplo(0)  # Verifica el argumento o la referencia usada por el triplo.
    assert tercero.argumento1 == "192.168.1.0"  # Verifica el argumento o la referencia usada por el triplo.

def prueba_operaciones_matematicas_rechazan_texto():  # Comprueba operaciones matematicas rechazan texto mediante un caso reproducible.
    casos_invalidos = [("+", "Hola", 2), ("^", 2, "Mundo"), ("LOG2", "Texto", None), ("CEIL", "Texto", None)]  # Agrupa entradas que deben provocar una validación fallida.
    for operador, argumento1, argumento2 in casos_invalidos:  # Recorre los elementos necesarios sin cambiar su orden original.
        with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
            Triplo(0, operador, argumento1, argumento2)  # Ejecuta la operación necesaria para la prueba o el procesamiento.

def prueba_operadores_vlsm_validos():  # Comprueba operadores vlsm validos mediante un caso reproducible.
    resultado = ResultadoIntermedio()  # Prepara una nueva colección vacía de código intermedio.
    t0 = resultado.agregar("INICIAR_RED", "192.168.1.0", "/24")  # Conserva la información que se consulta en las verificaciones posteriores.
    t1 = resultado.agregar("+", 50, 2)  # Conserva la información que se consulta en las verificaciones posteriores.
    t2 = resultado.agregar("LOG2", ReferenciaTriplo(t1.indice))  # Conserva la información que se consulta en las verificaciones posteriores.
    t3 = resultado.agregar("CEIL", ReferenciaTriplo(t2.indice))  # Conserva la información que se consulta en las verificaciones posteriores.
    t4 = resultado.agregar("^", 2, ReferenciaTriplo(t3.indice))  # Conserva la información que se consulta en las verificaciones posteriores.
    t5 = resultado.agregar("SOLICITUD", 50, ReferenciaTriplo(t4.indice))  # Conserva la información que se consulta en las verificaciones posteriores.
    t6 = resultado.agregar("ASIGNAR_VLSM", ReferenciaTriplo(t0.indice), ReferenciaTriplo(t5.indice))  # Conserva la información que se consulta en las verificaciones posteriores.
    resultado.agregar("SIGUIENTE_CURSOR", ReferenciaTriplo(t6.indice))  # Agrega la operación y conserva su origen o referencia.
    assert len(resultado.triplos) == 8  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert resultado.triplos[6].operador == "ASIGNAR_VLSM"  # Comprueba que se haya generado el operador correcto.

def prueba_operadores_vlsm_invalidos():  # Comprueba operadores vlsm invalidos mediante un caso reproducible.
    casos = [("INICIAR_RED", 50, 2), ("SOLICITUD", 0, ReferenciaTriplo(0)), ("SOLICITUD", 50, 64), ("ASIGNAR_VLSM", 0, ReferenciaTriplo(1)), ("SIGUIENTE_CURSOR", 20, None)]  # Agrupa combinaciones de operadores que deben rechazarse.
    for operador, argumento1, argumento2 in casos:  # Recorre los elementos necesarios sin cambiar su orden original.
        with pytest.raises(ValueError):  # Exige que el dato inválido sea rechazado con la excepción esperada.
            Triplo(0, operador, argumento1, argumento2)  # Ejecuta la operación necesaria para la prueba o el procesamiento.
