# ============================================================
# Archivo: interprete_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Ejecuta el código intermedio y registra comprobaciones
# matemáticas y de asignación de subredes VLSM.
# ============================================================

from dataclasses import dataclass, field  # Proporciona modelos de datos y valores predeterminados independientes.
from ipaddress import IPv4Address, IPv4Network  # Permite representar redes IPv4 y calcular sus límites.
from math import ceil, isfinite, log2  # Aporta cálculos matemáticos para potencias, logaritmos y redondeos.
from Motor.compilacion.triplos import ReferenciaTriplo, ResultadoIntermedio  # Reutiliza la estructura de compilación compartida con las demás fases.

@dataclass(frozen=True)
class CursorRed:  # Conserva la red base y la próxima dirección disponible.
    red_base: IPv4Network  # Conserva la información que se consulta en las verificaciones posteriores.
    direccion_actual: int  # Conserva la información que se consulta en las verificaciones posteriores.

@dataclass(frozen=True)
class SolicitudVLSM:  # Relaciona los hosts pedidos con el tamaño del bloque.
    hosts: int  # Recupera la cantidad de equipos solicitada en el código fuente.
    tamano_bloque: int  # Conserva la información que se consulta en las verificaciones posteriores.

@dataclass(frozen=True)
class AsignacionVLSM:  # Guarda la subred asignada y el cursor que resulta de ella.
    subred: IPv4Network  # Construye la subred resultante con su prefijo específico.
    hosts: int  # Recupera la cantidad de equipos solicitada en el código fuente.
    cursor_siguiente: CursorRed  # Conserva la información que se consulta en las verificaciones posteriores.

@dataclass
class ResultadoEjecucion:  # Reúne los valores y las comprobaciones de la ejecución.
    valores: dict[int, object] = field(default_factory=dict)  # Conserva la información que se consulta en las verificaciones posteriores.
    comprobaciones: dict[int, str] = field(default_factory=dict)  # Conserva la información que se consulta en las verificaciones posteriores.

class InterpreteTriplos:  # Evalúa las operaciones y resuelve sus referencias anteriores.

    def ejecutar(self, codigo: ResultadoIntermedio) -> ResultadoEjecucion:  # Recorre los triplos y conserva sus resultados y comprobaciones.
        ejecucion = ResultadoEjecucion()  # Inicializa o consulta las salidas numéricas y explicativas del intérprete.
        for triplo in codigo.triplos:  # Ejecuta cada triplo en el orden de generación.
            operador = triplo.operador  # Identifica la operación que se ejecutará en esta iteración.
            indice = triplo.indice  # Obtiene el índice consecutivo de la nueva operación.
            argumento1 = triplo.argumento1  # Conserva la información que se consulta en las verificaciones posteriores.
            argumento2 = triplo.argumento2  # Conserva el segundo argumento o un guion cuando no existe.
            if operador == "+":  # Suma la cantidad de hosts y las direcciones reservadas para red y broadcast.
                valor1 = self._resolver(argumento1, ejecucion.valores)  # Sustituye el primer operando por el valor de su referencia, si existe.
                valor2 = self._resolver(argumento2, ejecucion.valores)  # Resuelve el segundo operando antes de efectuar la operación.
                if type(valor1) is not int or type(valor2) is not int:  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("La suma necesita dos valores enteros.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                total = valor1 + valor2  # Calcula la suma de los dos operandos enteros.
                original = f'{argumento1} + {argumento2}'  # Conserva la expresión con sus referencias originales.
                sustituida = f'{valor1} + {valor2}'  # Construye la expresión con los valores ya resueltos.
                comprobacion = f'{original} -> {sustituida} = {total}' if original != sustituida else f'{sustituida} = {total}'  # Prepara el desarrollo matemático con sustitución y resultado.
                ejecucion.valores[indice] = total  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'{comprobacion} -> ({indice}) = {total}'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "LOG2":  # Obtiene los bits necesarios a partir del logaritmo en base dos.
                valor = self._resolver(argumento1, ejecucion.valores)  # Sustituye la referencia por el valor obtenido anteriormente.
                if type(valor) not in (int, float) or valor <= 0 or (not isfinite(valor)):  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("LOG2 necesita un número positivo y finito.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                resultado = log2(valor)  # Calcula el logaritmo binario del número de direcciones requeridas.
                ejecucion.valores[indice] = resultado  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'log2({argumento1}) -> log2({valor}) ≈ {resultado:.4f} -> ({indice}) ≈ {resultado:.4f}'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "CEIL":  # Redondea hacia arriba la cantidad de bits requerida.
                valor = self._resolver(argumento1, ejecucion.valores)  # Sustituye la referencia por el valor obtenido anteriormente.
                if type(valor) not in (int, float) or not isfinite(valor):  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("CEIL necesita un número finito.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                resultado = ceil(valor)  # Redondea hacia arriba para calcular los bits necesarios.
                ejecucion.valores[indice] = resultado  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'ceil({argumento1}) -> ceil({valor:.4f}) = {resultado} -> ({indice}) = {resultado}'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "^":  # Calcula el tamaño de bloque como potencia de dos.
                base = self._resolver(argumento1, ejecucion.valores)  # Obtiene la base numérica que se elevará a una potencia.
                exponente = self._resolver(argumento2, ejecucion.valores)  # Obtiene el exponente requerido para el tamaño del bloque.
                if type(base) is not int or type(exponente) is not int or exponente < 0:  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("La potencia necesita una base entera y un exponente entero no negativo.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                resultado = base ** exponente  # Calcula la potencia de dos del tamaño de bloque.
                ejecucion.valores[indice] = resultado  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'{argumento1} ^ {argumento2} -> {base} ^ {exponente} = {resultado} -> ({indice}) = {resultado}'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "INICIAR_RED":  # Valida la red base y crea un cursor al comienzo de su intervalo.
                try:  # Intenta construir la red y transforma fallos técnicos en errores controlados.
                    red = IPv4Network(f'{argumento1}{argumento2}', strict=True)  # Construye la red IPv4 a partir de la dirección y la máscara.
                except (ValueError, TypeError) as error:  # Convierte errores técnicos en un diagnóstico claro del intérprete.
                    raise ValueError("INICIAR_RED requiere una red IPv4 válida.") from error  # Detiene el procesamiento cuando se incumple la condición requerida.
                if not 8 <= red.prefixlen <= 30:  # Comprueba el rango CIDR admitido por el analizador semántico.
                    raise ValueError("INICIAR_RED necesita una máscara entre /8 y /30.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                cursor = CursorRed(red, int(red.network_address))  # Obtiene o valida la posición de asignación en la red base.
                ejecucion.valores[indice] = cursor  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'INICIAR_RED({argumento1}, {argumento2}) -> red {red.with_prefixlen} -> ({indice}) = cursor {red.network_address}'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "SOLICITUD":  # Prepara la solicitud y comprueba que su bloque tenga el tamaño mínimo.
                hosts = self._resolver(argumento1, ejecucion.valores)  # Recupera la cantidad de equipos solicitada en el código fuente.
                tamano = self._resolver(argumento2, ejecucion.valores)  # Obtiene la cantidad de direcciones de la subred requerida.
                if type(hosts) is not int or hosts <= 0 or type(tamano) is not int:  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("SOLICITUD necesita hosts y tamaño enteros positivos.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                tamano_minimo = 1 << (hosts + 1).bit_length()  # Obtiene la potencia mínima que puede alojar hosts + 2 direcciones.
                if tamano != tamano_minimo:  # Rechaza tamaños que no correspondan a la solicitud VLSM.
                    raise ValueError("SOLICITUD recibió un tamaño de bloque incorrecto.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                solicitud = SolicitudVLSM(hosts, tamano)  # Vincula los hosts solicitados con el tamaño de bloque calculado.
                ejecucion.valores[indice] = solicitud  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'SOLICITUD({argumento1}, {argumento2}) -> {hosts} hosts, {tamano} direcciones -> ({indice}) = solicitud preparada'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "ASIGNAR_VLSM":  # Asigna la subred sobre el cursor, respetando capacidad y alineación.
                cursor = self._resolver(argumento1, ejecucion.valores)  # Obtiene o valida la posición de asignación en la red base.
                solicitud = self._resolver(argumento2, ejecucion.valores)  # Vincula los hosts solicitados con el tamaño de bloque calculado.
                if not isinstance(cursor, CursorRed) or not isinstance(solicitud, SolicitudVLSM):  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("ASIGNAR_VLSM necesita un cursor y una solicitud.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                inicio = cursor.direccion_actual  # Obtiene la dirección inicial de la subred actual.
                tamano = solicitud.tamano_bloque  # Obtiene la cantidad de direcciones de la subred requerida.
                fin = inicio + tamano - 1  # Calcula el último valor IPv4 que ocupará esta asignación.
                if fin > int(cursor.red_base.broadcast_address):  # Detiene la asignación cuando excede los límites de la red base.
                    raise ValueError("ASIGNAR_VLSM excede la capacidad de la red base.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                if inicio % tamano != 0:  # Exige que la dirección de inicio esté alineada al bloque.
                    raise ValueError("ASIGNAR_VLSM necesita una dirección alineada al bloque.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                prefijo = 32 - (tamano.bit_length() - 1)  # Determina la máscara CIDR correspondiente al tamaño del bloque.
                subred = IPv4Network((inicio, prefijo), strict=True)  # Calcula la red, el broadcast y el prefijo de la asignación.
                siguiente = CursorRed(cursor.red_base, fin + 1)  # Conserva los límites originales al avanzar después del broadcast.
                asignacion = AsignacionVLSM(subred, solicitud.hosts, siguiente)  # Agrupa subred, hosts y cursor siguiente en un único resultado.
                ejecucion.valores[indice] = asignacion  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'ASIGNAR_VLSM({argumento1}, {argumento2}) -> inicio {subred.network_address}, bloque {tamano} -> ({indice}) = {subred.with_prefixlen} (broadcast {subred.broadcast_address})'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            elif operador == "SIGUIENTE_CURSOR":  # Recupera la próxima dirección libre dentro de la red base.
                asignacion = self._resolver(argumento1, ejecucion.valores)  # Recupera la subred asignada para conocer la siguiente dirección.
                if not isinstance(asignacion, AsignacionVLSM):  # Impide valores de tipo incorrecto en esta operación.
                    raise ValueError("SIGUIENTE_CURSOR necesita una asignación VLSM.")  # Detiene el procesamiento cuando se incumple la condición requerida.
                siguiente = asignacion.cursor_siguiente  # Recupera el cursor después de reservar la subred.
                if siguiente.direccion_actual > 4294967295:  # Evita convertir a IPv4 una posición fuera del rango de 32 bits.
                    texto = "fin del espacio IPv4"  # Representa el final del rango cuando no existe otra IPv4.
                else:
                    texto = str(IPv4Address(siguiente.direccion_actual))  # Muestra la siguiente dirección en notación IPv4.
                ejecucion.valores[indice] = siguiente  # Guarda el resultado con el índice del triplo para resolver referencias posteriores.
                ejecucion.comprobaciones[indice] = f'SIGUIENTE_CURSOR({argumento1}) -> {asignacion.subred.broadcast_address} + 1 -> ({indice}) = {texto}'  # Registra el desarrollo original, los valores sustituidos y el resultado.
            else:
                raise NotImplementedError(f'Operador pendiente de implementar: {operador}')  # Detiene el procesamiento cuando se incumple la condición requerida.
        return ejecucion  # Entrega los resultados y comprobaciones obtenidos en esta ejecución.

    def _resolver(self, argumento, valores: dict[int, object]) -> object:  # Sustituye una referencia por el resultado de un triplo anterior.
        if isinstance(argumento, ReferenciaTriplo):  # Distingue resultados anteriores de operandos literales.
            if argumento.indice not in valores:  # Comprueba que la referencia ya haya sido evaluada.
                raise ValueError(f'No existe un resultado para el triplo ({argumento.indice}).')  # Detiene el procesamiento cuando se incumple la condición requerida.
            return valores[argumento.indice]  # Entrega el resultado asociado con la referencia indicada.
        return argumento  # Devuelve el valor definido por esta operación.
