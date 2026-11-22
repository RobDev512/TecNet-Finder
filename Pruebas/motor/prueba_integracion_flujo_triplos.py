# ============================================================
# Archivo: prueba_integracion_flujo_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la integración del código intermedio
# con el flujo principal de compilación.
# ============================================================

from Motor.compilacion.flujo_compilacion import FlujoCompilacion  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.interprete_triplos import AsignacionVLSM  # Reutiliza la estructura de compilación compartida con las demás fases.

def prueba_flujo_genera_codigo_intermedio():  # Verifica que una instrucción válida produzca triplos, valores y subredes equivalentes.
    fuente = "IP 192.168.1.0 MASK /24 HOSTS 10,50 NAME Oficina"  # Define el código del DSL que se utilizará para la prueba.
    resultado = FlujoCompilacion().analizar(fuente)  # Ejecuta el flujo real de compilación sobre la entrada de prueba.
    assert resultado.codigo_intermedio is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    assert resultado.ejecucion_intermedia is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    codigo = resultado.codigo_intermedio.triplos  # Construye o conserva la secuencia utilizada en la prueba.
    valores = resultado.ejecucion_intermedia.valores  # Recupera los resultados de cada triplo ejecutado.
    comprobaciones = resultado.ejecucion_intermedia.comprobaciones  # Consulta las explicaciones que mostrará la interfaz.
    assert len(codigo) == 15  # Comprueba el número de elementos producidos por la operación.
    assert len(comprobaciones) == 15  # Comprueba el número de elementos producidos por la operación.
    asignaciones = [valores[t.indice] for t in codigo if t.operador == "ASIGNAR_VLSM"]  # Reúne las subredes producidas al ejecutar ASIGNAR_VLSM.
    assert len(asignaciones) == len(resultado.subredes_vlsm) == 2  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    for asignacion, subred in zip(asignaciones, resultado.subredes_vlsm):  # Recorre los elementos necesarios sin cambiar su orden original.
        assert isinstance(asignacion, AsignacionVLSM)  # Verifica que el resultado posea el modelo de datos esperado.
        assert str(asignacion.subred.network_address) == subred.direccion_de_red  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
        assert f'/{asignacion.subred.prefixlen}' == subred.nueva_mascara  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
        assert str(asignacion.subred.broadcast_address) == subred.direccion_de_broadcast  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    assert resultado.subredes_vlsm[0].nombre_red == "Oficina"  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.

def prueba_flujo_varias_redes_con_triplos():  # Verifica los índices de inicio y la procedencia al compilar dos redes.
    fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\nIP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"  # Define el código del DSL que se utilizará para la prueba.
    resultado = FlujoCompilacion().analizar(fuente)  # Ejecuta el flujo real de compilación sobre la entrada de prueba.
    assert resultado.codigo_intermedio is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    assert resultado.ejecucion_intermedia is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    triplos = resultado.codigo_intermedio.triplos  # Conserva la información que se consulta en las verificaciones posteriores.
    assert len(triplos) == 16  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert triplos[0].operador == "INICIAR_RED"  # Comprueba que se haya generado el operador correcto.
    assert triplos[8].operador == "INICIAR_RED"  # Comprueba que se haya generado el operador correcto.
    assert triplos[8].origen.linea_origen == 2  # Comprueba que la referencia conserve la línea real del código fuente.
    assert triplos[8].origen.indice_bloque == 1  # Verifica la procedencia del triplo dentro de los bloques validados.

def prueba_flujo_triplos_con_error_y_recuperacion():  # Comprueba que un bloque rechazado no impida generar los triplos del siguiente.
    fuente = "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida\nIP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"  # Define el código del DSL que se utilizará para la prueba.
    resultado = FlujoCompilacion().analizar(fuente)  # Ejecuta el flujo real de compilación sobre la entrada de prueba.
    assert resultado.tiene_errores  # Verifica el estado de error y la recuperación del compilador.
    assert len(resultado.bloques_validos) == 1  # Comprueba el número de elementos producidos por la operación.
    assert len(resultado.subredes_vlsm) == 1  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    assert resultado.codigo_intermedio is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    triplos = resultado.codigo_intermedio.triplos  # Conserva la información que se consulta en las verificaciones posteriores.
    assert len(triplos) == 8  # Comprueba que la cantidad de operaciones generadas sea la prevista.
    assert triplos[0].argumento1 == "10.0.0.0"  # Verifica el argumento o la referencia usada por el triplo.
    assert triplos[0].origen.linea_origen == 2  # Comprueba que la referencia conserve la línea real del código fuente.
    assert triplos[0].origen.indice_bloque == 0  # Verifica la procedencia del triplo dentro de los bloques validados.

def prueba_flujo_sin_bloques_validos():  # Verifica que una entrada inválida produzca código y ejecución vacíos.
    fuente = "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida"  # Define el código del DSL que se utilizará para la prueba.
    resultado = FlujoCompilacion().analizar(fuente)  # Ejecuta el flujo real de compilación sobre la entrada de prueba.
    assert resultado.bloques_validos == []  # Comprueba el comportamiento esperado para esta entrada de prueba.
    assert resultado.subredes_vlsm == []  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
    assert resultado.codigo_intermedio is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    assert resultado.codigo_intermedio.triplos == ()  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    assert resultado.ejecucion_intermedia is not None  # Comprueba que el flujo conserve el código intermedio y su evaluación.
    assert resultado.ejecucion_intermedia.valores == {}  # Verifica el resultado numérico o de red obtenido al ejecutar el triplo.
    assert resultado.ejecucion_intermedia.comprobaciones == {}  # Comprueba el desarrollo que aparecerá en la futura interfaz.
