# ============================================================
# Archivo: interprete_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Ejecuta el código intermedio y registra comprobaciones
# matemáticas y de asignación de subredes VLSM.
# ============================================================

from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network
from math import ceil, isfinite, log2

from Motor.compilacion.triplos import ReferenciaTriplo, ResultadoIntermedio


@dataclass(frozen=True)
class CursorRed:
    red_base: IPv4Network
    direccion_actual: int


@dataclass(frozen=True)
class SolicitudVLSM:
    hosts: int
    tamano_bloque: int


@dataclass(frozen=True)
class AsignacionVLSM:
    subred: IPv4Network
    hosts: int
    cursor_siguiente: CursorRed


@dataclass
class ResultadoEjecucion:
    valores: dict[int, object] = field(default_factory=dict)
    comprobaciones: dict[int, str] = field(default_factory=dict)


class InterpreteTriplos:

    def ejecutar(self, codigo: ResultadoIntermedio) -> ResultadoEjecucion:
        ejecucion = ResultadoEjecucion()

        for triplo in codigo.triplos:
            operador = triplo.operador
            indice = triplo.indice
            argumento1 = triplo.argumento1
            argumento2 = triplo.argumento2

            if operador == "+":
                valor1 = self._resolver(argumento1, ejecucion.valores)
                valor2 = self._resolver(argumento2, ejecucion.valores)
                if type(valor1) is not int or type(valor2) is not int:
                    raise ValueError("La suma necesita dos valores enteros.")
                total = valor1 + valor2
                original = f"{argumento1} + {argumento2}"
                sustituida = f"{valor1} + {valor2}"
                comprobacion = (
                    f"{original} -> {sustituida} = {total}"
                    if original != sustituida else f"{sustituida} = {total}"
                )
                ejecucion.valores[indice] = total
                ejecucion.comprobaciones[indice] = (
                    f"{comprobacion} -> ({indice}) = {total}"
                )

            elif operador == "LOG2":
                valor = self._resolver(argumento1, ejecucion.valores)
                if type(valor) not in (int, float) or valor <= 0 or not isfinite(valor):
                    raise ValueError("LOG2 necesita un número positivo y finito.")
                resultado = log2(valor)
                ejecucion.valores[indice] = resultado
                ejecucion.comprobaciones[indice] = (
                    f"log2({argumento1}) -> log2({valor}) ≈ {resultado:.4f}"
                    f" -> ({indice}) ≈ {resultado:.4f}"
                )

            elif operador == "CEIL":
                valor = self._resolver(argumento1, ejecucion.valores)
                if type(valor) not in (int, float) or not isfinite(valor):
                    raise ValueError("CEIL necesita un número finito.")
                resultado = ceil(valor)
                ejecucion.valores[indice] = resultado
                ejecucion.comprobaciones[indice] = (
                    f"ceil({argumento1}) -> ceil({valor:.4f}) = {resultado}"
                    f" -> ({indice}) = {resultado}"
                )

            elif operador == "^":
                base = self._resolver(argumento1, ejecucion.valores)
                exponente = self._resolver(argumento2, ejecucion.valores)
                if type(base) is not int or type(exponente) is not int or exponente < 0:
                    raise ValueError(
                        "La potencia necesita una base entera y un exponente entero no negativo."
                    )
                resultado = base ** exponente
                ejecucion.valores[indice] = resultado
                ejecucion.comprobaciones[indice] = (
                    f"{argumento1} ^ {argumento2}"
                    f" -> {base} ^ {exponente} = {resultado}"
                    f" -> ({indice}) = {resultado}"
                )

            elif operador == "INICIAR_RED":
                try:
                    red = IPv4Network(f"{argumento1}{argumento2}", strict=True)
                except (ValueError, TypeError) as error:
                    raise ValueError("INICIAR_RED requiere una red IPv4 válida.") from error
                if not 8 <= red.prefixlen <= 30:
                    raise ValueError("INICIAR_RED necesita una máscara entre /8 y /30.")
                cursor = CursorRed(red, int(red.network_address))
                ejecucion.valores[indice] = cursor
                ejecucion.comprobaciones[indice] = (
                    f"INICIAR_RED({argumento1}, {argumento2})"
                    f" -> red {red.with_prefixlen}"
                    f" -> ({indice}) = cursor {red.network_address}"
                )

            elif operador == "SOLICITUD":
                hosts = self._resolver(argumento1, ejecucion.valores)
                tamano = self._resolver(argumento2, ejecucion.valores)
                if type(hosts) is not int or hosts <= 0 or type(tamano) is not int:
                    raise ValueError("SOLICITUD necesita hosts y tamaño enteros positivos.")
                tamano_minimo = 1 << (hosts + 1).bit_length()
                if tamano != tamano_minimo:
                    raise ValueError("SOLICITUD recibió un tamaño de bloque incorrecto.")
                solicitud = SolicitudVLSM(hosts, tamano)
                ejecucion.valores[indice] = solicitud
                ejecucion.comprobaciones[indice] = (
                    f"SOLICITUD({argumento1}, {argumento2})"
                    f" -> {hosts} hosts, {tamano} direcciones"
                    f" -> ({indice}) = solicitud preparada"
                )

            elif operador == "ASIGNAR_VLSM":
                cursor = self._resolver(argumento1, ejecucion.valores)
                solicitud = self._resolver(argumento2, ejecucion.valores)
                if not isinstance(cursor, CursorRed) or not isinstance(solicitud, SolicitudVLSM):
                    raise ValueError("ASIGNAR_VLSM necesita un cursor y una solicitud.")
                inicio = cursor.direccion_actual
                tamano = solicitud.tamano_bloque
                fin = inicio + tamano - 1
                if fin > int(cursor.red_base.broadcast_address):
                    raise ValueError("ASIGNAR_VLSM excede la capacidad de la red base.")
                if inicio % tamano != 0:
                    raise ValueError("ASIGNAR_VLSM necesita una dirección alineada al bloque.")
                prefijo = 32 - (tamano.bit_length() - 1)
                subred = IPv4Network((inicio, prefijo), strict=True)
                siguiente = CursorRed(cursor.red_base, fin + 1)
                asignacion = AsignacionVLSM(subred, solicitud.hosts, siguiente)
                ejecucion.valores[indice] = asignacion
                ejecucion.comprobaciones[indice] = (
                    f"ASIGNAR_VLSM({argumento1}, {argumento2})"
                    f" -> inicio {subred.network_address}, bloque {tamano}"
                    f" -> ({indice}) = {subred.with_prefixlen}"
                    f" (broadcast {subred.broadcast_address})"
                )

            elif operador == "SIGUIENTE_CURSOR":
                asignacion = self._resolver(argumento1, ejecucion.valores)
                if not isinstance(asignacion, AsignacionVLSM):
                    raise ValueError("SIGUIENTE_CURSOR necesita una asignación VLSM.")
                siguiente = asignacion.cursor_siguiente
                if siguiente.direccion_actual > 0xFFFFFFFF:
                    texto = "fin del espacio IPv4"
                else:
                    texto = str(IPv4Address(siguiente.direccion_actual))
                ejecucion.valores[indice] = siguiente
                ejecucion.comprobaciones[indice] = (
                    f"SIGUIENTE_CURSOR({argumento1})"
                    f" -> {asignacion.subred.broadcast_address} + 1"
                    f" -> ({indice}) = {texto}"
                )

            else:
                raise NotImplementedError(f"Operador pendiente de implementar: {operador}")

        return ejecucion

    def _resolver(self, argumento, valores: dict[int, object]) -> object:
        if isinstance(argumento, ReferenciaTriplo):
            if argumento.indice not in valores:
                raise ValueError(
                    f"No existe un resultado para el triplo ({argumento.indice})."
                )
            return valores[argumento.indice]
        return argumento
