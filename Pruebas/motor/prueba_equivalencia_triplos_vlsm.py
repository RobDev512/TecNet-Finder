# ============================================================
# Archivo: prueba_equivalencia_triplos_vlsm.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Compara las subredes producidas por los triplos con las
# calculadas por la implementación VLSM existente.
# ============================================================

from ipaddress import IPv4Address  # Permite calcular primera y última IP utilizables para contrastarlas.

import pytest  # Habilita las pruebas parametrizadas y la comprobación de excepciones.
from Compilador.generador_triplos import GeneradorTriplos  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.interprete_triplos import AsignacionVLSM, InterpreteTriplos  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.modelos import BloqueRed  # Reutiliza la estructura de compilación compartida con las demás fases.
from Redes.calculadora_vlsm import calcular_vlsm  # Reutiliza la estructura de compilación compartida con las demás fases.

def comprobar_equivalencia(bloques: list[BloqueRed]) -> None:  # Compara el intérprete y la calculadora original para cada red.
    codigo = GeneradorTriplos().generar(bloques)  # Genera el código intermedio para el escenario de prueba.
    ejecucion = InterpreteTriplos().ejecutar(codigo)  # Ejecuta los triplos para obtener valores y comprobaciones.
    for indice_bloque, bloque in enumerate(bloques):  # Compara cada red sin mezclar las asignaciones de otras instrucciones.
        esperado = calcular_vlsm(bloque.direccion_ip, bloque.mascara_subred, bloque.cantidades_hosts, nombre_red=bloque.nombre)  # Calcula la referencia con el método VLSM anterior.
        operaciones = [triplo for triplo in codigo.triplos if triplo.operador == "ASIGNAR_VLSM" and triplo.origen.indice_bloque == indice_bloque]  # Filtra las asignaciones correspondientes a la red actual.
        orden_original = sorted(enumerate(bloque.cantidades_hosts), key=lambda item: item[1], reverse=True)  # Obtiene el orden de solicitudes VLSM conservando sus posiciones.
        assert len(operaciones) == len(esperado) == len(orden_original)  # Comprueba el número de elementos producidos por la operación.
        for triplo, referencia, (indice_host, hosts) in zip(operaciones, esperado, orden_original):  # Compara cada asignación generada con su subred de referencia.
            asignacion = ejecucion.valores[triplo.indice]  # Asocia la solicitud VLSM con el cursor de la red.
            assert isinstance(asignacion, AsignacionVLSM)  # Verifica que el resultado posea el modelo de datos esperado.
            subred = asignacion.subred  # Consulta la red IPv4 calculada por el intérprete.
            assert asignacion.hosts == referencia.hosts_solicitados == hosts  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert str(subred.network_address) == referencia.direccion_de_red  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert f'/{subred.prefixlen}' == referencia.nueva_mascara  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert str(subred.netmask) == referencia.mascara_decimal  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert str(subred.broadcast_address) == referencia.direccion_de_broadcast  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert subred.num_addresses - 2 == referencia.hosts_disponibles  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert asignacion.cursor_siguiente.direccion_actual == int(subred.broadcast_address) + 1  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert asignacion.cursor_siguiente.red_base.with_prefixlen == f'{bloque.direccion_ip}{bloque.mascara_subred}'  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert str(IPv4Address(int(subred.network_address) + 1)) == referencia.primera_ip_utilizable  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert str(IPv4Address(int(subred.broadcast_address) - 1)) == referencia.ultima_ip_utilizable  # Comprueba la coincidencia entre el intérprete y la calculadora VLSM.
            assert triplo.origen.indice_host == indice_host  # Verifica que se conserve la posición original de la solicitud HOSTS.

@pytest.mark.parametrize("ip, mascara, hosts", [("192.168.1.0", "/24", [10, 50, 20]), ("10.0.0.0", "/24", [20, 50, 20]), ("172.16.0.0", "/16", [1000, 500, 200, 30, 2, 1]), ("192.168.0.0", "/30", [1]), ("192.168.7.0", "/24", [126, 62, 30, 14, 6, 2, 1]), ("10.10.0.0", "/16", [2046, 1022, 510])])
def prueba_equivalencia_por_red(ip, mascara, hosts):  # Compara una red y sus solicitudes con los resultados de VLSM clásico.
    comprobar_equivalencia([BloqueRed(ip, mascara, hosts, "Prueba", 1)])  # Ejecuta la comparación completa contra la calculadora original.

def prueba_equivalencia_varias_redes():  # Verifica que la equivalencia también se mantenga entre redes independientes.
    bloques = [BloqueRed("192.168.1.0", "/24", [50, 10], "Oficina", 1), BloqueRed("10.0.0.0", "/24", [20, 20], "Laboratorio", 2), BloqueRed("172.16.0.0", "/16", [1000, 100], None, 3)]  # Prepara varias redes para comprobar su independencia.
    comprobar_equivalencia(bloques)  # Ejecuta la comparación completa contra la calculadora original.
