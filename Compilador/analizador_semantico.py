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
# Actualmente implementa SEM-001, SEM-002, SEM-003,
# SEM-004, SEM-005 y SEM-006.
# ============================================================

from dataclasses import dataclass  # Importa el decorador utilizado para representar de forma clara las ubicaciones de un bloque.
import ipaddress  # Importa las herramientas estándar utilizadas para interpretar direcciones y redes IPv4.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Importa el modelo y la función central utilizados para producir diagnósticos semánticos.
from Motor.modelos import BloqueRed, ResultadoSemantico, Token  # Importa los modelos requeridos por la fase semántica.


@dataclass(frozen=True)  # Impide modificar accidentalmente la correspondencia entre un bloque y sus tokens originales.
class UbicacionBloqueSemantico:  # Conserva los tokens originales asociados con un bloque aceptado por el parser.
    token_ip: Token  # Guarda el token que contiene la dirección IPv4 escrita por el usuario.
    token_mascara: Token  # Guarda el token que contiene la máscara CIDR del bloque.
    token_hosts: Token  # Guarda la palabra reservada HOSTS para ubicar diagnósticos relacionados con la lista completa.
    tokens_hosts: tuple[Token, ...]  # Guarda en orden los tokens correspondientes con cada cantidad de HOSTS.
    token_nombre: Token | None = None  # Guarda el identificador escrito después de NAME cuando existe.


class AnalizadorSemantico:  # Comprueba el significado de los bloques que ya superaron las fases anteriores.
    def __init__(self, bloques: list[BloqueRed], tokens: list[Token]):  # Recibe bloques sintácticos y tokens originales para ubicar los errores.
        self._bloques = list(bloques)  # Conserva una copia de los bloques para evitar modificar directamente el resultado sintáctico.
        self._tokens = list(tokens)  # Conserva una copia de los tokens para relacionar cada regla semántica con el código fuente.

    def analizar(self) -> ResultadoSemantico:  # Ejecuta todas las reglas semánticas disponibles sobre los bloques recibidos.
        candidatos_traslape: list[tuple[BloqueRed, UbicacionBloqueSemantico | None]] = []  # Conserva los bloques que superaron primero todas las reglas individuales.
        diagnosticos: list[Diagnostico] = []  # Reúne todos los diagnósticos producidos durante esta fase.

        for bloque in self._bloques:  # Analiza individualmente cada instrucción aceptada previamente por el parser.
            ubicacion = self._localizar_ubicacion_bloque(bloque)  # Recupera los tokens exactos asociados con el bloque actual.
            diagnosticos_bloque: list[Diagnostico] = []  # Conserva solamente los errores semánticos correspondientes con la instrucción actual.

            diagnosticos_mascara = self._validar_mascara(bloque, ubicacion)  # Ejecuta SEM-001 antes de las reglas que dependen del prefijo.
            diagnosticos_bloque.extend(diagnosticos_mascara)  # Agrega los posibles errores relacionados con el rango de la máscara.

            if not diagnosticos_mascara:  # Permite usar la máscara únicamente cuando su prefijo ya fue validado.
                diagnosticos_bloque.extend(
                    self._validar_direccion_red(bloque, ubicacion)
                )  # Ejecuta SEM-002 comprobando que la IP represente realmente el inicio de la red.

            diagnosticos_hosts = self._validar_hosts_positivos(bloque, ubicacion)  # Ejecuta SEM-003 antes de realizar cálculos de capacidad.
            diagnosticos_bloque.extend(diagnosticos_hosts)  # Agrega cada cantidad no positiva encontrada dentro de HOSTS.

            if not diagnosticos_mascara and not diagnosticos_hosts:  # Ejecuta capacidad únicamente con prefijo válido y cantidades positivas.
                diagnosticos_bloque.extend(
                    self._validar_capacidad_individual(bloque, ubicacion)
                )  # Ejecuta primero SEM-005 para comprobar cada solicitud individual.

                diagnosticos_bloque.extend(
                    self._validar_capacidad_total(bloque, ubicacion)
                )  # Ejecuta después SEM-004 para comprobar la suma real de bloques VLSM.

            diagnosticos.extend(diagnosticos_bloque)  # Incorpora al resultado general todos los errores encontrados dentro del bloque actual.

            if not diagnosticos_bloque:  # Comprueba si la instrucción superó todas las reglas que dependen únicamente de sí misma.
                candidatos_traslape.append((bloque, ubicacion))  # Reserva el bloque para comprobar después su relación con las demás redes base.

        bloques_validos, diagnosticos_traslape = self._validar_traslapes(candidatos_traslape)  # Ejecuta SEM-006 únicamente entre bloques individualmente correctos.
        diagnosticos.extend(diagnosticos_traslape)  # Agrega al resultado general los conflictos encontrados entre diferentes redes base.

        return ResultadoSemantico(
            bloques_validos=bloques_validos,
            diagnosticos=diagnosticos,
        )  # Devuelve únicamente las redes que superaron reglas individuales y relacionales.

    def _validar_mascara(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-001 sobre el rango admitido para la máscara CIDR.
        prefijo = int(bloque.mascara_subred[1:])  # Convierte únicamente los dígitos situados después de la diagonal.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección de errores producidos por esta regla.

        if 8 <= prefijo <= 30:  # Comprueba que el prefijo esté dentro del dominio permitido por TecNet Finder.
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

        if bloque.direccion_ip == direccion_red_correcta:  # Comprueba si la IP proporcionada ya coincide con la dirección de red.
            return diagnosticos  # Finaliza sin errores cuando la IP escrita representa correctamente la red.

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
            if cantidad_hosts > 0:  # Comprueba si la solicitud posee al menos un host utilizable.
                continue  # Ignora cualquier solicitud positiva porque cumple la regla semántica.

            token_host = None  # Considera inicialmente que no se dispone de una posición exacta para la cantidad actual.

            if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts):  # Comprueba que exista un token asociado con la cantidad actual.
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

    def _validar_capacidad_individual(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-005 sobre cada solicitud individual de hosts.
        diagnosticos: list[Diagnostico] = []  # Reúne las solicitudes individuales que excedan la capacidad de la red base.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera el prefijo previamente validado por SEM-001.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones contenidas por la red base.

        for indice_host, cantidad_hosts in enumerate(bloque.cantidades_hosts):  # Evalúa individualmente cada requerimiento HOSTS.
            tamano_bloque = self._calcular_tamano_bloque_vlsm(cantidad_hosts)  # Obtiene el bloque potencia de dos realmente requerido por VLSM.

            if tamano_bloque <= capacidad_red:  # Comprueba si la solicitud individual todavía cabe dentro de la red completa.
                continue  # Evita generar SEM-005 cuando la red base puede contener ese requerimiento por sí solo.

            token_host = None  # Considera inicialmente que la cantidad no posee una ubicación exacta disponible.

            if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts):  # Comprueba que el NUMBER original haya sido localizado.
                token_host = ubicacion.tokens_hosts[indice_host]  # Recupera el token exacto asociado con la solicitud demasiado grande.

            diagnosticos.append(
                crear_diagnostico(
                    codigo="SEM-005",
                    mensaje=(
                        f"La solicitud de {cantidad_hosts} hosts requiere un bloque VLSM "
                        f"de {tamano_bloque} direcciones, pero la red "
                        f"{bloque.direccion_ip}{bloque.mascara_subred} dispone solamente "
                        f"de {capacidad_red} direcciones."
                    ),
                    linea=token_host.linea if token_host is not None else bloque.linea_origen,
                    columna=token_host.columna if token_host is not None else None,
                    longitud=len(token_host.valor) if token_host is not None else len(str(cantidad_hosts)),
                    fragmento=token_host.valor if token_host is not None else str(cantidad_hosts),
                )
            )  # Registra SEM-005 exactamente sobre la cantidad HOSTS que excede por sí sola la capacidad disponible.

        return diagnosticos  # Devuelve un diagnóstico independiente para cada solicitud individual demasiado grande.

    def _validar_capacidad_total(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-004 usando la capacidad real requerida por todos los bloques VLSM.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección utilizada por la validación de capacidad global.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera el prefijo que ya superó SEM-001.
        capacidad_red = 1 << (32 - prefijo)  # Calcula el total de direcciones disponibles dentro de la red base.
        capacidad_requerida = sum(
            self._calcular_tamano_bloque_vlsm(cantidad_hosts)
            for cantidad_hosts in bloque.cantidades_hosts
        )  # Suma los tamaños potencia de dos que VLSM necesita realmente para todas las solicitudes.

        if capacidad_requerida <= capacidad_red:  # Comprueba si la combinación completa cabe dentro de la red base.
            return diagnosticos  # Finaliza sin SEM-004 cuando la capacidad disponible es suficiente.

        token_hosts = ubicacion.token_hosts if ubicacion is not None else None  # Recupera la palabra HOSTS para relacionar el diagnóstico con la lista completa.

        diagnosticos.append(
            crear_diagnostico(
                codigo="SEM-004",
                mensaje=(
                    f"Las subredes solicitadas requieren en conjunto "
                    f"{capacidad_requerida} direcciones mediante VLSM, pero la red "
                    f"{bloque.direccion_ip}{bloque.mascara_subred} dispone solamente "
                    f"de {capacidad_red} direcciones."
                ),
                linea=token_hosts.linea if token_hosts is not None else bloque.linea_origen,
                columna=token_hosts.columna if token_hosts is not None else None,
                longitud=len(token_hosts.valor) if token_hosts is not None else len("HOSTS"),
                fragmento=token_hosts.valor if token_hosts is not None else "HOSTS",
            )
        )  # Registra SEM-004 sobre la sección HOSTS porque el error depende de la combinación completa de solicitudes.

        return diagnosticos  # Devuelve el exceso global detectado para impedir que el bloque continúe hacia VLSM.

    def _validar_traslapes(
        self,
        candidatos: list[tuple[BloqueRed, UbicacionBloqueSemantico | None]],
    ) -> tuple[list[BloqueRed], list[Diagnostico]]:  # Comprueba SEM-006 comparando las redes base que ya superaron todas las reglas individuales.
        bloques_validos: list[BloqueRed] = []  # Conserva únicamente la primera red de cada espacio no conflictivo.
        redes_aceptadas: list[tuple[BloqueRed, ipaddress.IPv4Network]] = []  # Guarda los intervalos IPv4 ya aceptados para compararlos con los siguientes.
        diagnosticos: list[Diagnostico] = []  # Reúne los traslapes detectados entre diferentes instrucciones.

        for bloque, ubicacion in candidatos:  # Respeta el orden original para conservar la primera declaración válida.
            red_actual = ipaddress.IPv4Network(
                f"{bloque.direccion_ip}{bloque.mascara_subred}",
                strict=True,
            )  # Construye la red exacta porque IP y máscara ya superaron SEM-001 y SEM-002.

            conflicto = next(
                (
                    (bloque_anterior, red_anterior)
                    for bloque_anterior, red_anterior in redes_aceptadas
                    if red_actual.overlaps(red_anterior)
                ),
                None,
            )  # Recupera la primera red anteriormente aceptada cuyo intervalo se cruza con la red actual.

            if conflicto is None:  # Comprueba que la red actual sea independiente de todas las anteriores aceptadas.
                bloques_validos.append(bloque)  # Conserva el bloque para las siguientes etapas del compilador.
                redes_aceptadas.append((bloque, red_actual))  # Registra también su intervalo para revisar las instrucciones posteriores.
                continue  # Continúa con la siguiente red sin producir diagnóstico.

            bloque_anterior, red_anterior = conflicto  # Recupera la red previa que provoca el conflicto con la declaración actual.
            token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera la IP de la declaración posterior para señalarla en el editor.

            diagnosticos.append(
                crear_diagnostico(
                    codigo="SEM-006",
                    mensaje=(
                        f"La red base {red_actual.with_prefixlen} de la línea "
                        f"{bloque.linea_origen} se traslapa con la red "
                        f"{red_anterior.with_prefixlen} declarada anteriormente "
                        f"en la línea {bloque_anterior.linea_origen}."
                    ),
                    linea=token_ip.linea if token_ip is not None else bloque.linea_origen,
                    columna=token_ip.columna if token_ip is not None else None,
                    longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip),
                    fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip,
                )
            )  # Rechaza solamente la declaración posterior y conserva la primera red válida encontrada.

        return bloques_validos, diagnosticos  # Devuelve las redes independientes junto con los conflictos detectados.

    def _calcular_tamano_bloque_vlsm(self, cantidad_hosts: int) -> int:  # Calcula la potencia de dos mínima capaz de contener hosts, red y broadcast.
        direcciones_necesarias = cantidad_hosts + 2  # Agrega las direcciones reservadas para identificar la red y el broadcast.
        exponente = (direcciones_necesarias - 1).bit_length()  # Obtiene sin flotantes el exponente de la siguiente potencia de dos.
        return 1 << exponente  # Devuelve el tamaño real que ocupará la subred dentro del espacio IPv4.

    def _localizar_ubicacion_bloque(self, bloque: BloqueRed) -> UbicacionBloqueSemantico | None:  # Relaciona un bloque sintáctico con los tokens exactos que lo originaron.
        for indice_inicio, token_inicio in enumerate(self._tokens):  # Examina cada token que podría representar el comienzo de una instrucción.
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:  # Comprueba que el token pueda iniciar exactamente el bloque buscado.
                continue  # Descarta cualquier token que no pueda iniciar el bloque recibido.

            posicion = indice_inicio + 1  # Avanza desde la palabra reservada IP hacia la dirección IPv4.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "IP_ADDRESS":  # Comprueba que exista una dirección completa después de IP.
                continue  # Descarta una secuencia que no contenga la dirección esperada después de IP.

            token_ip = self._tokens[posicion]  # Conserva el token de la dirección para utilizar su ubicación posteriormente.

            if token_ip.valor != bloque.direccion_ip:  # Comprueba que la dirección encontrada corresponda con el bloque actual.
                continue  # Descarta una instrucción cuya dirección no coincida con el bloque buscado.

            posicion += 1  # Avanza desde la dirección IPv4 hacia la palabra reservada MASK.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "MASK":  # Comprueba la siguiente parte obligatoria de la instrucción.
                continue  # Descarta una secuencia que no corresponde con la estructura de un bloque válido.

            posicion += 1  # Avanza desde MASK hacia el token que contiene la máscara CIDR.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "SUBNET_MASK":  # Comprueba que exista la máscara esperada.
                continue  # Descarta una secuencia donde no exista la máscara reconocida por el parser.

            token_mascara = self._tokens[posicion]  # Conserva la máscara junto con su línea y columna originales.

            if token_mascara.valor != bloque.mascara_subred:  # Comprueba que la máscara corresponda con el bloque buscado.
                continue  # Descarta otra instrucción que utilice una máscara diferente.

            posicion += 1  # Avanza desde la máscara hacia la palabra reservada HOSTS.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "HOSTS":  # Comprueba que exista la sección obligatoria de cantidades.
                continue  # Descarta una secuencia que no posea la sección HOSTS esperada.

            token_hosts = self._tokens[posicion]  # Conserva también la palabra HOSTS para diagnósticos relacionados con toda la lista.
            posicion += 1  # Coloca el recorrido sobre la primera cantidad escrita después de HOSTS.
            tokens_hosts: list[Token] = []  # Reúne los NUMBER que pertenecen exclusivamente a la lista de hosts actual.

            while posicion < len(self._tokens):  # Recorre la lista de cantidades hasta encontrar NAME u otro elemento.
                token_actual = self._tokens[posicion]  # Obtiene el token ubicado actualmente dentro de la lista.

                if token_actual.tipo == "NUMBER":  # Comprueba si el token representa una solicitud individual de hosts.
                    tokens_hosts.append(token_actual)  # Conserva cada cantidad con su ubicación exacta dentro del código fuente.
                    posicion += 1  # Avanza hacia una posible coma o hacia el siguiente elemento.
                    continue  # Continúa recorriendo la lista HOSTS.

                if token_actual.tipo == "COMMA":  # Comprueba si el elemento solamente separa dos cantidades.
                    posicion += 1  # Omite la coma porque no representa una solicitud por sí misma.
                    continue  # Continúa buscando el siguiente NUMBER de la lista.

                break  # Finaliza la lectura de HOSTS cuando aparece NAME u otro comienzo de instrucción.

            cantidades_encontradas = [int(token.valor) for token in tokens_hosts]  # Convierte los NUMBER encontrados para compararlos con el resultado sintáctico.

            if cantidades_encontradas != bloque.cantidades_hosts:  # Comprueba que la lista localizada sea exactamente la del bloque buscado.
                continue  # Descarta una instrucción parecida cuya lista HOSTS no coincide exactamente.

            token_nombre = None  # Considera inicialmente que la instrucción no utilizó la sección opcional NAME.
            nombre_encontrado = None  # Conserva el valor textual del nombre cuando aparece en la instrucción.

            if posicion < len(self._tokens) and self._tokens[posicion].tipo == "NAME":  # Comprueba si la instrucción posee el componente opcional NAME.
                posicion += 1  # Avanza desde la palabra reservada NAME hacia su identificador.

                if posicion < len(self._tokens) and self._tokens[posicion].tipo == "IDENTIFIER":  # Comprueba que exista un nombre reconocido.
                    token_nombre = self._tokens[posicion]  # Conserva el token del nombre para futuras reglas semánticas.
                    nombre_encontrado = token_nombre.valor  # Obtiene el texto utilizado para distinguir instrucciones similares.

            if nombre_encontrado != bloque.nombre:  # Comprueba que el nombre localizado corresponda con el resultado sintáctico.
                continue  # Descarta otro bloque que coincida en red y hosts pero utilice un nombre diferente.

            return UbicacionBloqueSemantico(
                token_ip=token_ip,
                token_mascara=token_mascara,
                token_hosts=token_hosts,
                tokens_hosts=tuple(tokens_hosts),
                token_nombre=token_nombre,
            )  # Devuelve todos los tokens relevantes del bloque cuya correspondencia fue comprobada.

        return None  # Evita inventar posiciones cuando no puede establecerse una correspondencia segura con los tokens originales.