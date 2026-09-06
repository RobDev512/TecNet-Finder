# ============================================================
# Archivo: prueba_calculadora_vlsm.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo contiene las pruebas automáticas del cálculo VLSM.
# Los casos verifican la misma lógica utilizada por la versión de
# Lenguajes y Autómatas I: orden descendente de hosts, cálculo de
# bloques, direcciones utilizables y conservación del nombre de red.
# ============================================================

from Redes.calculadora_vlsm import calcular_vlsm  # Importa la función de cálculo VLSM que será evaluada.


def prueba_calcula_una_subred():  # Comprueba el cálculo completo de una sola solicitud de 50 hosts.
    resultados = calcular_vlsm("192.168.1.0", "/24", [50], "Oficina")  # Calcula una subred partiendo de una red base /24.
    assert len(resultados) == 1  # Verifica que una sola solicitud produzca exactamente una subred.
    subred = resultados[0]  # Obtiene la única subred calculada para revisar todos sus datos.
    assert subred.hosts_solicitados == 50  # Comprueba que se conserve la cantidad solicitada.
    assert subred.hosts_disponibles == 62  # Comprueba que un bloque /26 proporcione 62 direcciones utilizables.
    assert subred.direccion_de_red == "192.168.1.0"  # Comprueba la dirección de red calculada.
    assert subred.nueva_mascara == "/26"  # Comprueba el prefijo CIDR necesario para 50 hosts.
    assert subred.mascara_decimal == "255.255.255.192"  # Comprueba la máscara decimal equivalente a /26.
    assert subred.primera_ip_utilizable == "192.168.1.1"  # Comprueba la primera dirección utilizable.
    assert subred.ultima_ip_utilizable == "192.168.1.62"  # Comprueba la última dirección utilizable.
    assert subred.direccion_de_broadcast == "192.168.1.63"  # Comprueba la dirección de broadcast.


def prueba_ordena_hosts_de_mayor_a_menor():  # Comprueba que VLSM asigne primero las subredes que requieren mayor espacio.
    resultados = calcular_vlsm("192.168.30.0", "/24", [10, 50, 30], "Optimizada")  # Usa el caso de hosts desordenados existente en LyA I.
    assert [subred.hosts_solicitados for subred in resultados] == [50, 30, 10]  # Verifica que las solicitudes se procesen en orden descendente.


def prueba_asigna_bloques_consecutivos():  # Comprueba que cada nueva subred comience después del bloque asignado anteriormente.
    resultados = calcular_vlsm("192.168.1.0", "/24", [50, 30, 10], "Oficina")  # Calcula tres subredes consecutivas dentro de la misma dirección base.
    assert resultados[0].direccion_de_red == "192.168.1.0"  # Comprueba que la primera subred comience en la dirección base.
    assert resultados[1].direccion_de_red == "192.168.1.64"  # Comprueba que la segunda subred comience después del bloque /26 anterior.
    assert resultados[2].direccion_de_red == "192.168.1.96"  # Comprueba que la tercera subred comience después del bloque /27 anterior.
    assert resultados[2].direccion_de_broadcast == "192.168.1.111"  # Comprueba el final del bloque /28 asignado a 10 hosts.


def prueba_usa_ip_base_cuando_no_hay_nombre():  # Comprueba el comportamiento original cuando la instrucción no incluye NAME.
    resultados = calcular_vlsm("192.168.2.0", "/24", [100, 50])  # Calcula subredes sin proporcionar un nombre de red.
    assert all(subred.nombre_red == "192.168.2.0" for subred in resultados)  # Verifica que cada resultado utilice la IP base como identificador.
    assert all(subred.ip_base == "192.168.2.0" for subred in resultados)  # Comprueba que también se conserve explícitamente la IP de origen.


def prueba_no_modifica_lista_original_de_hosts():  # Comprueba que ordenar las solicitudes no altere la lista entregada por el bloque sintáctico.
    cantidades_hosts = [10, 50, 30]  # Crea una lista deliberadamente desordenada.
    calcular_vlsm("192.168.30.0", "/24", cantidades_hosts, "Optimizada")  # Ejecuta el cálculo VLSM sobre la lista original.
    assert cantidades_hosts == [10, 50, 30]  # Verifica que sorted haya creado un nuevo orden sin modificar la entrada original.