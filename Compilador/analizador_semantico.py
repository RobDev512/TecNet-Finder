# ============================================================
# Archivo: analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la fase de análisis semántico del
# compilador de TecNet Finder.
#
# Su responsabilidad es comprobar que las instrucciones que ya
# superaron el análisis léxico y sintáctico también tengan un
# significado válido dentro de las reglas de direccionamiento
# utilizadas por TecNet Finder.
#
# El análisis semántico no modifica los bloques recibidos.
# Separa los bloques válidos de aquellos que contienen errores
# y genera diagnósticos con la ubicación exacta del problema.
#
# Actualmente implementa las reglas SEM-001, SEM-002 y SEM-003.
# ============================================================

from dataclasses import dataclass  # Importa el decorador utilizado para representar de forma clara las ubicaciones de un bloque.
import ipaddress  # Importa las herramientas estándar utilizadas para interpretar direcciones y redes IPv4.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Importa el modelo y la función central utilizados para producir diagnósticos semánticos.
from Motor.modelos import BloqueRed, ResultadoSemantico, Token  # Importa los modelos requeridos por la fase semántica.


@dataclass(frozen=True)
class UbicacionBloqueSemantico:  # Conserva los tokens originales asociados con un bloque aceptado por el parser.
    token_ip: Token  # Guarda el token que contiene la dirección IPv4 escrita por el usuario.
    token_mascara: Token  # Guarda el token que contiene la máscara CIDR del bloque.
    tokens_hosts: tuple[Token, ...]  # Guarda en orden los tokens correspondientes con cada cantidad de HOSTS.
    token_nombre: Token | None = None  # Guarda el identificador escrito después de NAME cuando existe.


class AnalizadorSemantico:  # Comprueba el significado de los bloques que ya superaron las fases anteriores.
    def __init__(self, bloques: list[BloqueRed], tokens: list[Token]):  # Recibe los bloques sintácticos y los tokens originales necesarios para ubicar errores.
        self._bloques = list(bloques)  # Conserva una copia de los bloques para evitar modificar directamente el resultado sintáctico.
        self._tokens = list(tokens)  # Conserva una copia de los tokens para relacionar cada regla semántica con el código fuente.

    def analizar(self) -> ResultadoSemantico:  # Ejecuta todas las reglas semánticas disponibles sobre los bloques recibidos.
        bloques_validos: list[BloqueRed] = []  # Reúne únicamente las instrucciones que no presentan errores semánticos.
        diagnosticos: list[Diagnostico] = []  # Reúne todos los diagnósticos producidos durante esta fase.

        for bloque in self._bloques:  # Analiza individualmente cada instrucción aceptada previamente por el parser.
            ubicacion = self._localizar_ubicacion_bloque(bloque)  # Recupera los tokens exactos asociados con el bloque actual.
            diagnosticos_bloque: list[Diagnostico] = []  # Conserva solamente los errores semánticos correspondientes con la instrucción actual.

            diagnosticos_mascara = self._validar_mascara(bloque, ubicacion)  # Ejecuta SEM-001 antes de realizar comprobaciones que dependan del prefijo.
            diagnosticos_bloque.extend(diagnosticos_mascara)  # Agrega los posibles errores relacionados con el rango de la máscara.

            if not diagnosticos_mascara:
                diagnosticos_bloque.extend(
                    self._validar_direccion_red(bloque, ubicacion)
                )  # Ejecuta SEM-002 únicamente cuando la máscara puede utilizarse correctamente para interpretar la red.

            diagnosticos_bloque.extend(
                self._validar_hosts_positivos(bloque, ubicacion)
            )  # Ejecuta SEM-003 independientemente de la IP y la máscara porque cada cantidad HOSTS posee significado propio.

            diagnosticos.extend(diagnosticos_bloque)  # Incorpora al resultado general todos los errores encontrados dentro del bloque actual.

            if not diagnosticos_bloque:
                bloques_validos.append(bloque)  # Conserva únicamente los bloques que superaron todas las reglas semánticas implementadas.

        return ResultadoSemantico(
            bloques_validos=bloques_validos,
            diagnosticos=diagnosticos,
        )  # Devuelve por separado los bloques aprobados y los errores semánticos detectados.

    def _validar_mascara(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-001 sobre el rango admitido para la máscara CIDR.
        prefijo = int(bloque.mascara_subred[1:])  # Convierte únicamente los dígitos situados después de la diagonal.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección de errores producidos por esta regla.

        if 8 <= prefijo <= 30:
            return diagnosticos  # Finaliza sin errores cuando el prefijo pertenece al rango permitido.

        token_mascara = ubicacion.token_mascara if ubicacion is not None else None  # Recupera la posición exacta de la máscara cuando fue posible localizar el bloque.

        diagnosticos.append(
            crear_diagnostico(
                codigo="SEM-001",
                mensaje=(
                    f"Máscara CIDR fuera del rango permitido en la línea "
                    f"{token_mascara.linea if token_mascara is not None else bloque.linea_origen}: "
                    f"'{bloque.mascara_subred}'. TecNet Finder acepta máscaras entre /8 y /30."
                ),
                linea=token_mascara.linea if token_mascara is not None else bloque.linea_origen,
                columna=token_mascara.columna if token_mascara is not None else None,
                longitud=len(token_mascara.valor) if token_mascara is not None else len(bloque.mascara_subred),
                fragmento=token_mascara.valor if token_mascara is not None else bloque.mascara_subred,
            )
        )  # Registra SEM-001 señalando específicamente la máscara que incumple la regla.

        return diagnosticos  # Devuelve el error encontrado para impedir que el bloque sea aceptado.

    def _validar_direccion_red(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-002 relacionando la IP base con la máscara válida.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección de errores producidos por esta regla.
        red = ipaddress.IPv4Network(
            f"{bloque.direccion_ip}{bloque.mascara_subred}",
            strict=False,
        )  # Obtiene la red real asociada con la IP y la máscara sin rechazar automáticamente una dirección de host.
        direccion_red_correcta = str(red.network_address)  # Recupera la dirección que realmente identifica el comienzo del bloque IPv4.

        if bloque.direccion_ip == direccion_red_correcta:
            return diagnosticos  # Finaliza sin errores cuando la IP escrita ya representa la dirección de red.

        token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera la ubicación exacta de la dirección escrita por el usuario.

        diagnosticos.append(
            crear_diagnostico(
                codigo="SEM-002",
                mensaje=(
                    f"La dirección IP '{bloque.direccion_ip}' de la línea "
                    f"{token_ip.linea if token_ip is not None else bloque.linea_origen} "
                    f"no representa la dirección de red para la máscara {bloque.mascara_subred}. "
                    f"La dirección de red correspondiente es '{direccion_red_correcta}'."
                ),
                linea=token_ip.linea if token_ip is not None else bloque.linea_origen,
                columna=token_ip.columna if token_ip is not None else None,
                longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip),
                fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip,
            )
        )  # Registra SEM-002 sobre la IP original e informa cuál sería la dirección de red correcta.

        return diagnosticos  # Devuelve el error encontrado para impedir que la instrucción llegue a etapas posteriores.

    def _validar_hosts_positivos(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-003 sobre cada solicitud individual escrita después de HOSTS.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección donde se almacenará cada cantidad no positiva.

        for indice_host, cantidad_hosts in enumerate(bloque.cantidades_hosts):  # Conserva el índice original para relacionar cada cantidad con su token exacto.
            if cantidad_hosts > 0:
                continue  # Ignora cualquier solicitud positiva porque cumple la regla semántica.

            token_host = None  # Considera inicialmente que no se dispone de una posición exacta para la cantidad actual.

            if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts):
                token_host = ubicacion.tokens_hosts[indice_host]  # Recupera el NUMBER correspondiente con la posición original dentro de HOSTS.

            diagnosticos.append(
                crear_diagnostico(
                    codigo="SEM-003",
                    mensaje=(
                        f"Cantidad de HOSTS no válida en la línea "
                        f"{token_host.linea if token_host is not None else bloque.linea_origen}: "
                        f"'{cantidad_hosts}'. Cada solicitud debe ser mayor que cero."
                    ),
                    linea=token_host.linea if token_host is not None else bloque.linea_origen,
                    columna=token_host.columna if token_host is not None else None,
                    longitud=len(token_host.valor) if token_host is not None else len(str(cantidad_hosts)),
                    fragmento=token_host.valor if token_host is not None else str(cantidad_hosts),
                )
            )  # Registra un SEM-003 independiente para cada cantidad que no posea hosts utilizables.

        return diagnosticos  # Devuelve todos los errores encontrados dentro de la lista HOSTS.

    def _localizar_ubicacion_bloque(self, bloque: BloqueRed) -> UbicacionBloqueSemantico | None:  # Relaciona un bloque sintáctico con los tokens exactos que lo originaron.
        for indice_inicio, token_inicio in enumerate(self._tokens):  # Examina cada token que podría representar el comienzo de una instrucción.
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:
                continue  # Descarta cualquier token que no pueda iniciar el bloque recibido.

            posicion = indice_inicio + 1  # Avanza desde la palabra reservada IP hacia la dirección IPv4.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "IP_ADDRESS":
                continue  # Descarta una secuencia que no contenga la dirección esperada después de IP.

            token_ip = self._tokens[posicion]  # Conserva el token de la dirección para utilizar su ubicación posteriormente.

            if token_ip.valor != bloque.direccion_ip:
                continue  # Descarta una instrucción cuya dirección no coincida con el bloque buscado.

            posicion += 1  # Avanza desde la dirección IPv4 hacia la palabra reservada MASK.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "MASK":
                continue  # Descarta una secuencia que no corresponde con la estructura de un bloque válido.

            posicion += 1  # Avanza desde MASK hacia el token que contiene la máscara CIDR.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "SUBNET_MASK":
                continue  # Descarta una secuencia donde no exista la máscara esperada.

            token_mascara = self._tokens[posicion]  # Conserva la máscara junto con su línea y columna originales.

            if token_mascara.valor != bloque.mascara_subred:
                continue  # Descarta otra instrucción que utilice una máscara diferente.

            posicion += 1  # Avanza desde la máscara hacia la palabra reservada HOSTS.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "HOSTS":
                continue  # Descarta una secuencia que no posea la sección HOSTS esperada.

            posicion += 1  # Coloca el recorrido sobre la primera cantidad escrita después de HOSTS.
            tokens_hosts: list[Token] = []  # Reúne los NUMBER que pertenecen exclusivamente a la lista de hosts actual.

            while posicion < len(self._tokens):  # Recorre la lista de cantidades hasta encontrar NAME u otro elemento.
                token_actual = self._tokens[posicion]  # Obtiene el token ubicado actualmente dentro de la lista.

                if token_actual.tipo == "NUMBER":
                    tokens_hosts.append(token_actual)  # Conserva cada cantidad con su ubicación exacta dentro del código fuente.
                    posicion += 1  # Avanza hacia una posible coma o hacia el siguiente elemento.
                    continue  # Continúa recorriendo la lista HOSTS.

                if token_actual.tipo == "COMMA":
                    posicion += 1  # Omite la coma porque solamente funciona como separador entre cantidades.
                    continue  # Continúa buscando el siguiente NUMBER de la lista.

                break  # Finaliza la lectura de HOSTS cuando aparece NAME u otro comienzo de instrucción.

            cantidades_encontradas = [int(token.valor) for token in tokens_hosts]  # Convierte los NUMBER encontrados para compararlos con el resultado sintáctico.

            if cantidades_encontradas != bloque.cantidades_hosts:
                continue  # Descarta una instrucción parecida cuya lista HOSTS no coincide exactamente.

            token_nombre = None  # Considera inicialmente que la instrucción no utilizó la sección opcional NAME.
            nombre_encontrado = None  # Conserva el valor textual del nombre cuando aparece en la instrucción.

            if posicion < len(self._tokens) and self._tokens[posicion].tipo == "NAME":
                posicion += 1  # Avanza desde la palabra reservada NAME hacia su identificador.

                if posicion < len(self._tokens) and self._tokens[posicion].tipo == "IDENTIFIER":
                    token_nombre = self._tokens[posicion]  # Conserva el token del nombre para futuras reglas semánticas.
                    nombre_encontrado = token_nombre.valor  # Obtiene el texto utilizado para distinguir instrucciones similares.

            if nombre_encontrado != bloque.nombre:
                continue  # Descarta otro bloque que coincida en red y hosts pero utilice un nombre diferente.

            return UbicacionBloqueSemantico(
                token_ip=token_ip,
                token_mascara=token_mascara,
                tokens_hosts=tuple(tokens_hosts),
                token_nombre=token_nombre,
            )  # Devuelve todos los tokens relevantes del bloque cuya correspondencia fue comprobada.

        return None  # Evita inventar posiciones cuando no puede establecerse una correspondencia segura con los tokens originales.