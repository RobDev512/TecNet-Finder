
# ============================================================
# Archivo: generador_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Genera código intermedio mediante triplos a partir
# de los bloques de red validados por el compilador.
# ============================================================

from Motor.compilacion.modelos import BloqueRed
from Motor.compilacion.triplos import (
    ResultadoIntermedio,
    OrigenTriplo,
    ReferenciaTriplo,
)


class GeneradorTriplos:
    def generar(self, bloques: list[BloqueRed]) -> ResultadoIntermedio:
        resultado = ResultadoIntermedio()

        for indice, bloque in enumerate(bloques):
            origen = OrigenTriplo(
                linea_origen=bloque.linea_origen,
                indice_bloque=indice
            )

            # Crea el contexto inicial de la red.
            inicio_red = resultado.agregar(
                "INICIAR_RED", bloque.direccion_ip, bloque.mascara_subred, origen=origen
            )

            # El primer cursor apunta al inicio de esta red.
            cursor_actual = ReferenciaTriplo(inicio_red.indice)

            # Ordena los hosts de mayor a menor, conservando su posicion original.
            hosts_ordenados = sorted(
                enumerate(bloque.cantidades_hosts),
                key=lambda elemento: elemento[1],
                reverse=True
            )

            # Genera una operación por cada cantidad de hosts.
            for indice_host, cantidad_hosts in hosts_ordenados:
                origen_host = OrigenTriplo(
                    linea_origen=bloque.linea_origen,
                    indice_bloque=indice,
                    indice_host=indice_host
                )

                # Calcula las direcciones necesarias: hosts + 2
                suma = resultado.agregar(
                    "+", cantidad_hosts, 2, origen=origen_host
                )      

                # Obtiene el logaritmo base 2 de la suma anterior.
                logaritmo = resultado.agregar(
                    "LOG2", ReferenciaTriplo(suma.indice), origen=origen_host
                )

                # Redondea el logaritmo hacia arriba.
                redondeo = resultado.agregar(
                    "CEIL", ReferenciaTriplo(logaritmo.indice), origen=origen_host
                )

                # Calcula la potencia de dos necesaria.
                potencia = resultado.agregar(
                    "^", 2, ReferenciaTriplo(redondeo.indice), origen=origen_host
                )


                # Prepara la solicitud de hosts.
                solicitud = resultado.agregar(
                    "SOLICITUD", cantidad_hosts, ReferenciaTriplo(potencia.indice), origen=origen_host
                )

                # Asigna una subred usando el cursor actual.
                asignacion = resultado.agregar(
                    "ASIGNAR_VLSM", cursor_actual, ReferenciaTriplo(solicitud.indice), origen=origen_host
                )

                # Obtiene la referencia para la siguiente asignación.
                siguiente = resultado.agregar(
                    "SIGUIENTE_CURSOR", ReferenciaTriplo(asignacion.indice), origen=origen_host
                )

                # Actualiza el cursor para la siguiente solicitud.
                cursor_actual = ReferenciaTriplo(siguiente.indice)

        return resultado