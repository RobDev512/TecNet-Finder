# ============================================================
# Archivo: generador_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Genera código intermedio mediante triplos a partir
# de los bloques de red validados por el compilador.
# ============================================================

from Motor.compilacion.modelos import BloqueRed  # Reutiliza la estructura de compilación compartida con las demás fases.
from Motor.compilacion.triplos import ResultadoIntermedio, OrigenTriplo, ReferenciaTriplo  # Reutiliza la estructura de compilación compartida con las demás fases.

class GeneradorTriplos:  # Construye el código intermedio a partir de las redes validadas.

    def generar(self, bloques: list[BloqueRed]) -> ResultadoIntermedio:  # Genera un conjunto de operaciones por cada bloque de red validado.
        resultado = ResultadoIntermedio()  # Reserva una secuencia única para todos los bloques semánticamente válidos.
        for indice, bloque in enumerate(bloques):  # Recorre cada red y conserva su posición entre los bloques válidos.
            origen = OrigenTriplo(linea_origen=bloque.linea_origen, indice_bloque=indice)  # Conserva la línea del bloque del que procede el triplo.
            inicio_red = resultado.agregar("INICIAR_RED", bloque.direccion_ip, bloque.mascara_subred, origen=origen)  # Emite la operación que identifica la red base y su máscara.
            cursor_actual = ReferenciaTriplo(inicio_red.indice)  # Inicia el cursor de este bloque sin reutilizar el de otra red.
            hosts_ordenados = sorted(enumerate(bloque.cantidades_hosts), key=lambda elemento: elemento[1], reverse=True)  # Ordena solicitudes de mayor a menor sin perder sus índices originales.
            for indice_host, cantidad_hosts in hosts_ordenados:  # Genera las operaciones por host sin perder la posición original.
                origen_host = OrigenTriplo(linea_origen=bloque.linea_origen, indice_bloque=indice, indice_host=indice_host)  # Asocia cada operación con la solicitud HOSTS de la que procede.
                suma = resultado.agregar("+", cantidad_hosts, 2, origen=origen_host)  # Genera la suma de hosts más dos direcciones reservadas.
                logaritmo = resultado.agregar("LOG2", ReferenciaTriplo(suma.indice), origen=origen_host)  # Genera el cálculo del logaritmo con referencia a la suma.
                redondeo = resultado.agregar("CEIL", ReferenciaTriplo(logaritmo.indice), origen=origen_host)  # Genera el redondeo del resultado del logaritmo.
                potencia = resultado.agregar("^", 2, ReferenciaTriplo(redondeo.indice), origen=origen_host)  # Calcula el tamaño del bloque con una potencia de dos.
                solicitud = resultado.agregar("SOLICITUD", cantidad_hosts, ReferenciaTriplo(potencia.indice), origen=origen_host)  # Vincula los hosts solicitados con el tamaño de bloque calculado.
                asignacion = resultado.agregar("ASIGNAR_VLSM", cursor_actual, ReferenciaTriplo(solicitud.indice), origen=origen_host)  # Asocia la solicitud VLSM con el cursor de la red.
                siguiente = resultado.agregar("SIGUIENTE_CURSOR", ReferenciaTriplo(asignacion.indice), origen=origen_host)  # Recupera el cursor después de reservar la subred.
                cursor_actual = ReferenciaTriplo(siguiente.indice)  # Encadena la siguiente asignación con el cursor que acaba de generarse.
        return resultado  # Devuelve todas las operaciones generadas para las redes procesadas.
