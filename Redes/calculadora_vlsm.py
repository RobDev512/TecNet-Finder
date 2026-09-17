# ============================================================
# Archivo: calculadora_vlsm.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el cálculo VLSM utilizado por TecNet Finder.
# Su responsabilidad es recibir una dirección IP base, una máscara y
# una lista de hosts, ordenar las solicitudes de mayor a menor y
# calcular las subredes correspondientes.
#
# La lógica conserva el comportamiento de la versión final de LyA I.
# Las validaciones sobre rango de máscara, capacidad o dirección de red
# pertenecen al análisis semántico y no se realizan en este módulo.
# ============================================================

import ipaddress  # Importa las herramientas estándar de Python para trabajar con direcciones y redes IPv4.
import math  # Importa funciones matemáticas utilizadas para calcular la cantidad de bits necesarios.

from Motor.compilacion.modelos import SubredVLSM  # Importa el modelo utilizado para representar cada subred calculada.


class ErrorCalculoVLSM(Exception):  # Representa una imposibilidad técnica de cálculo conservando la solicitud concreta que la produjo.
    def __init__(self, hosts_solicitados: int, indice_host_original: int, detalle: str):
        self.hosts_solicitados = hosts_solicitados  # Conserva la cantidad concreta que no pudo representarse.
        self.indice_host_original = indice_host_original  # Conserva su posición dentro de la lista HOSTS escrita por el usuario.
        self.detalle = detalle  # Conserva el mensaje técnico original únicamente para depuración interna.
        super().__init__(detalle)  # Inicializa la excepción estándar con el detalle recibido.


def calcular_vlsm(direccion_ip: str, mascara_subred: str, cantidades_hosts: list[int], nombre_red: str | None = None) -> list[SubredVLSM]:  # Calcula las subredes VLSM; la máscara base se validará posteriormente en la fase semántica.
    resultados: list[SubredVLSM] = []  # Crea la lista donde se almacenarán las subredes calculadas.
    ip_actual = int(ipaddress.IPv4Address(direccion_ip))  # Convierte la IP base a entero para poder avanzar entre bloques de direcciones.
    hosts_ordenados = sorted(enumerate(cantidades_hosts), key=lambda elemento: elemento[1], reverse=True)  # Ordena por cantidad sin perder la posición original escrita después de HOSTS.

    for indice_host_original, hosts_solicitados in hosts_ordenados:  # Recorre las solicitudes de mayor a menor conservando su ubicación original.
        try:
            bits_necesarios = math.ceil(math.log2(hosts_solicitados + 2))  # Suma red y broadcast y calcula cuántos bits se necesitan para contener todas las direcciones.
            nuevo_cidr = 32 - bits_necesarios  # Obtiene el prefijo CIDR correspondiente al tamaño del bloque calculado.
            tamano_bloque = 2 ** bits_necesarios  # Calcula la cantidad total de direcciones que ocupará la subred actual.
            direccion_red = ipaddress.IPv4Address(ip_actual)  # Convierte la posición actual en la dirección de red de la nueva subred.
            direccion_broadcast = ipaddress.IPv4Address(ip_actual + tamano_bloque - 1)  # Calcula la última dirección del bloque y la utiliza como broadcast.
            primera_ip_utilizable = ipaddress.IPv4Address(ip_actual + 1)  # Calcula la primera dirección disponible para un host.
            ultima_ip_utilizable = ipaddress.IPv4Address(ip_actual + tamano_bloque - 2)  # Calcula la última dirección disponible para un host.
            mascara_decimal = str(ipaddress.IPv4Network(f"0.0.0.0/{nuevo_cidr}").netmask)  # Convierte el nuevo prefijo CIDR a una máscara decimal punteada.
        except (ValueError, OverflowError) as error:
            raise ErrorCalculoVLSM(
                hosts_solicitados=hosts_solicitados,
                indice_host_original=indice_host_original,
                detalle=str(error),
            ) from error  # Convierte el fallo técnico en información que Motor puede relacionar con el NUMBER exacto del código fuente.

        resultados.append(
            SubredVLSM(
                hosts_solicitados=hosts_solicitados,  # Guarda la cantidad de hosts pedida para esta subred.
                hosts_disponibles=tamano_bloque - 2,  # Guarda las direcciones utilizables después de reservar red y broadcast.
                direccion_de_red=str(direccion_red),  # Guarda la dirección de red calculada como texto.
                nueva_mascara=f"/{nuevo_cidr}",  # Guarda el prefijo CIDR específico calculado para esta subred.
                mascara_decimal=mascara_decimal,  # Guarda la máscara equivalente en notación decimal punteada.
                primera_ip_utilizable=str(primera_ip_utilizable),  # Guarda la primera IP que puede asignarse a un host.
                ultima_ip_utilizable=str(ultima_ip_utilizable),  # Guarda la última IP que puede asignarse a un host.
                direccion_de_broadcast=str(direccion_broadcast),  # Guarda la dirección de broadcast calculada.
                ip_base=direccion_ip,  # Conserva la IP original de la instrucción que produjo esta subred.
                nombre_red=nombre_red or direccion_ip,  # Usa el nombre indicado o la IP base cuando NAME no fue especificado.
            )
        )

        ip_actual += tamano_bloque  # Avanza al primer espacio disponible después del bloque que acaba de asignarse.

    return resultados  # Devuelve todas las subredes calculadas en orden de mayor a menor cantidad de hosts.