# ============================================================
# Archivo: prueba_equivalencia_triplos_vlsm.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Compara las subredes producidas por los triplos con las
# calculadas por la implementación VLSM existente.
# ============================================================

from ipaddress import IPv4Address

import pytest

from Compilador.generador_triplos import GeneradorTriplos
from Motor.compilacion.interprete_triplos import AsignacionVLSM, InterpreteTriplos
from Motor.compilacion.modelos import BloqueRed
from Redes.calculadora_vlsm import calcular_vlsm


def comprobar_equivalencia(bloques: list[BloqueRed]) -> None:
    codigo = GeneradorTriplos().generar(bloques)
    ejecucion = InterpreteTriplos().ejecutar(codigo)

    for indice_bloque, bloque in enumerate(bloques):
        esperado = calcular_vlsm(
            bloque.direccion_ip,
            bloque.mascara_subred,
            bloque.cantidades_hosts,
            nombre_red=bloque.nombre,
        )

        operaciones = [
            triplo for triplo in codigo.triplos
            if triplo.operador == "ASIGNAR_VLSM"
            and triplo.origen.indice_bloque == indice_bloque
        ]
        orden_original = sorted(
            enumerate(bloque.cantidades_hosts),
            key=lambda item: item[1],
            reverse=True,
        )

        assert len(operaciones) == len(esperado) == len(orden_original)

        for triplo, referencia, (indice_host, hosts) in zip(
            operaciones, esperado, orden_original
        ):
            asignacion = ejecucion.valores[triplo.indice]
            assert isinstance(asignacion, AsignacionVLSM)
            subred = asignacion.subred

            # Compara cada parte importante del cálculo VLSM.
            assert asignacion.hosts == referencia.hosts_solicitados == hosts
            assert str(subred.network_address) == referencia.direccion_de_red
            assert f"/{subred.prefixlen}" == referencia.nueva_mascara
            assert str(subred.netmask) == referencia.mascara_decimal
            assert str(subred.broadcast_address) == referencia.direccion_de_broadcast
            assert subred.num_addresses - 2 == referencia.hosts_disponibles
            assert asignacion.cursor_siguiente.direccion_actual == (
                int(subred.broadcast_address) + 1
            )
            assert asignacion.cursor_siguiente.red_base.with_prefixlen == (
                f"{bloque.direccion_ip}{bloque.mascara_subred}"
            )
            assert str(IPv4Address(int(subred.network_address) + 1)) == (
                referencia.primera_ip_utilizable
            )
            assert str(IPv4Address(int(subred.broadcast_address) - 1)) == (
                referencia.ultima_ip_utilizable
            )

            # Verifica que no se haya perdido la solicitud original.
            assert triplo.origen.indice_host == indice_host


@pytest.mark.parametrize(
    "ip, mascara, hosts",
    [
        ("192.168.1.0", "/24", [10, 50, 20]),
        ("10.0.0.0", "/24", [20, 50, 20]),
        ("172.16.0.0", "/16", [1000, 500, 200, 30, 2, 1]),
        ("192.168.0.0", "/30", [1]),
        ("192.168.7.0", "/24", [126, 62, 30, 14, 6, 2, 1]),
        ("10.10.0.0", "/16", [2046, 1022, 510]),
    ],
)
def prueba_equivalencia_por_red(ip, mascara, hosts):
    comprobar_equivalencia([BloqueRed(ip, mascara, hosts, "Prueba", 1)])


def prueba_equivalencia_varias_redes():
    bloques = [
        BloqueRed("192.168.1.0", "/24", [50, 10], "Oficina", 1),
        BloqueRed("10.0.0.0", "/24", [20, 20], "Laboratorio", 2),
        BloqueRed("172.16.0.0", "/16", [1000, 100], None, 3),
    ]
    comprobar_equivalencia(bloques)
