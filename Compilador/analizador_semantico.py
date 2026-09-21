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
# superaron el análisis léxico y sintáctico también posean un
# significado válido dentro de las reglas de direccionamiento.
#
# El análisis semántico no modifica los bloques recibidos.
# Separa los bloques válidos de aquellos que contienen errores
# y genera diagnósticos relacionados con su ubicación original.
#
# Actualmente implementa SEM-001 a SEM-009.
# ============================================================

from dataclasses import dataclass  # Permite representar de manera estructurada e inmutable las ubicaciones léxicas recuperadas para cada bloque.
import ipaddress  # Proporciona las operaciones estándar utilizadas para interpretar direcciones y redes IPv4 válidas.

from Motor.compilacion.diagnosticos import Diagnostico, crear_diagnostico  # Proporciona la estructura y fábrica central utilizadas para generar errores semánticos.
from Motor.compilacion.modelos import BloqueRed, ResultadoSemantico, Token  # Proporciona los bloques sintácticos, tokens originales y estructura de salida de esta fase.


@dataclass(frozen=True)  # Impide modificar accidentalmente la correspondencia recuperada entre un bloque sintáctico y sus tokens originales.
class UbicacionBloqueSemantico:  # Conserva los elementos léxicos requeridos para señalar con precisión cualquier diagnóstico semántico.
    token_ip: Token  # Guarda el token correspondiente con la dirección IPv4 escrita después de IP.
    token_mascara: Token  # Guarda el token correspondiente con la máscara CIDR escrita después de MASK.
    token_hosts: Token  # Guarda la palabra reservada HOSTS para relacionar diagnósticos pertenecientes a la lista completa.
    tokens_hosts: tuple[Token, ...]  # Conserva en orden cada NUMBER perteneciente a las cantidades solicitadas.
    token_nombre: Token | None = None  # Conserva el identificador opcional escrito después de NAME cuando se encuentra presente.


class AnalizadorSemantico:  # Comprueba el significado de los bloques que superaron correctamente las fases léxica y sintáctica.
    def __init__(self, bloques: list[BloqueRed], tokens: list[Token]):  # Recibe los bloques sintácticos y sus tokens originales para poder relacionar cada error con el editor.
        self._bloques = list(bloques)  # Conserva una copia de los bloques para evitar modificar directamente el resultado producido por el parser.
        self._tokens = list(tokens)  # Conserva una copia de los tokens para reconstruir posteriormente la ubicación exacta de cada dato.

    def analizar(self) -> ResultadoSemantico:  # Ejecuta en orden todas las reglas semánticas implementadas actualmente.
        candidatos_conflicto: list[tuple[BloqueRed, UbicacionBloqueSemantico | None]] = []  # Reúne las redes individualmente válidas que posteriormente deberán compararse entre sí.
        diagnosticos: list[Diagnostico] = []  # Conserva conjuntamente todos los diagnósticos producidos durante esta fase.

        for bloque in self._bloques:  # Recorre individualmente cada instrucción aceptada previamente por el analizador sintáctico.
            ubicacion = self._localizar_ubicacion_bloque(bloque)  # Intenta recuperar los tokens exactos que originaron el bloque actual.
            diagnosticos_bloque: list[Diagnostico] = []  # Mantiene temporalmente separados los errores pertenecientes únicamente con esta instrucción.

            diagnosticos_ip = self._validar_octetos_ipv4(bloque, ubicacion)  # Ejecuta SEM-007 antes de utilizar la dirección con las operaciones estándar de IPv4.
            diagnosticos_bloque.extend(diagnosticos_ip)  # Incorpora al bloque cualquier octeto cuyo valor se encuentre fuera del intervalo permitido.

            diagnosticos_mascara = self._validar_mascara(bloque, ubicacion)  # Ejecuta SEM-001 antes de utilizar matemáticamente el prefijo recibido.
            diagnosticos_bloque.extend(diagnosticos_mascara)  # Incorpora cualquier máscara que se encuentre fuera del intervalo admitido por TecNet Finder.

            if not diagnosticos_ip and not diagnosticos_mascara:  # Comprueba que dirección y máscara puedan interpretarse conjuntamente de forma segura.
                diagnosticos_bloque.extend(self._validar_direccion_red(bloque, ubicacion))  # Ejecuta SEM-002 comprobando que la dirección proporcionada represente realmente el inicio de la red.

            diagnosticos_hosts = self._validar_hosts_positivos(bloque, ubicacion)  # Ejecuta SEM-003 sobre cada cantidad solicitada antes de realizar cálculos VLSM.
            diagnosticos_bloque.extend(diagnosticos_hosts)  # Incorpora todos los errores correspondientes con cantidades de hosts no positivas.

            if not diagnosticos_mascara and not diagnosticos_hosts:  # Comprueba que máscara y cantidades posean valores utilizables para calcular capacidades.
                diagnosticos_bloque.extend(self._validar_capacidad_individual(bloque, ubicacion))  # Ejecuta SEM-005 comprobando cada solicitud de hosts de manera independiente.
                diagnosticos_bloque.extend(self._validar_capacidad_total(bloque, ubicacion))  # Ejecuta SEM-004 comprobando el espacio requerido por todas las solicitudes en conjunto.

            diagnosticos.extend(diagnosticos_bloque)  # Agrega al resultado general todos los problemas encontrados dentro del bloque actual.

            if not diagnosticos_bloque:  # Comprueba si la instrucción superó completamente las reglas semánticas que dependen solamente de sí misma.
                candidatos_conflicto.append((bloque, ubicacion))  # Reserva la red para comprobar posteriormente SEM-006, SEM-008 y SEM-009.

        bloques_validos, diagnosticos_conflicto = self._validar_conflictos_entre_redes(candidatos_conflicto)  # Compara las redes válidas individualmente para detectar reutilizaciones y traslapes.
        diagnosticos.extend(diagnosticos_conflicto)  # Incorpora al resultado general los errores que solamente pueden detectarse comparando varias declaraciones.

        return ResultadoSemantico(bloques_validos=bloques_validos, diagnosticos=diagnosticos)  # Devuelve únicamente los bloques definitivamente aceptados junto con todos los errores semánticos encontrados.

    def _validar_octetos_ipv4(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-007 individualmente sobre cada componente numérico de la dirección IPv4.
        diagnosticos: list[Diagnostico] = []  # Reunirá un diagnóstico independiente por cada octeto que se encuentre fuera del intervalo válido.
        octetos = bloque.direccion_ip.split(".")  # Divide la dirección estructuralmente correcta en los cuatro componentes reconocidos previamente por el lexer.
        token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera la ubicación completa de la dirección cuando pudo reconstruirse el bloque.

        for indice, texto_octeto in enumerate(octetos):  # Recorre cada componente numérico conservando su posición relativa dentro de la dirección.
            valor_octeto = int(texto_octeto)  # Convierte el componente textual a entero para evaluar su significado real como octeto IPv4.

            if 0 <= valor_octeto <= 255:  # Comprueba que el valor pertenezca al intervalo definido para cualquier octeto IPv4.
                continue  # Omite los componentes válidos y continúa inmediatamente con el octeto siguiente.

            desplazamiento = sum(len(octeto_anterior) + 1 for octeto_anterior in octetos[:indice])  # Calcula la posición interna del octeto contando también los puntos que lo preceden.
            columna_octeto = token_ip.columna + desplazamiento if token_ip is not None else None  # Calcula la columna exacta del componente inválido cuando existe información léxica.
            linea_octeto = token_ip.linea if token_ip is not None else bloque.linea_origen  # Conserva la línea exacta de la dirección utilizando el bloque como respaldo.
            diagnosticos.append(crear_diagnostico(codigo="SEM-007", mensaje=f"Octeto IPv4 fuera del rango permitido en la línea {linea_octeto}: '{texto_octeto}'. Cada octeto debe encontrarse entre 0 y 255.", linea=linea_octeto, columna=columna_octeto, longitud=len(texto_octeto), fragmento=texto_octeto))  # Registra SEM-007 resaltando únicamente el octeto numéricamente incorrecto.

        return diagnosticos  # Devuelve todos los octetos inválidos encontrados dentro de la misma dirección.

    def _validar_mascara(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-001 sobre el rango permitido para una máscara CIDR.
        prefijo = int(bloque.mascara_subred[1:])  # Convierte en entero únicamente la parte numérica situada después de la diagonal.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección donde se almacenará el posible error de máscara.

        if 8 <= prefijo <= 30:  # Comprueba si el prefijo pertenece al intervalo admitido actualmente por TecNet Finder.
            return diagnosticos  # Finaliza sin errores cuando la máscara puede utilizarse de forma segura en las reglas posteriores.

        token_mascara = ubicacion.token_mascara if ubicacion is not None else None  # Recupera la posición exacta de la máscara cuando pudo reconstruirse el bloque original.
        diagnosticos.append(crear_diagnostico(codigo="SEM-001", mensaje=f"Máscara CIDR fuera del rango permitido en la línea {token_mascara.linea if token_mascara is not None else bloque.linea_origen}: '{bloque.mascara_subred}'. TecNet Finder acepta máscaras entre /8 y /30.", linea=token_mascara.linea if token_mascara is not None else bloque.linea_origen, columna=token_mascara.columna if token_mascara is not None else None, longitud=len(token_mascara.valor) if token_mascara is not None else len(bloque.mascara_subred), fragmento=token_mascara.valor if token_mascara is not None else bloque.mascara_subred))  # Registra SEM-001 señalando directamente la máscara semánticamente inválida.
        return diagnosticos  # Devuelve el diagnóstico producido para impedir que el bloque sea considerado válido.

    def _validar_direccion_red(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-002 relacionando una IPv4 numéricamente válida con una máscara también validada.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección utilizada por esta regla.
        red = ipaddress.IPv4Network(f"{bloque.direccion_ip}{bloque.mascara_subred}", strict=False)  # Calcula la red correspondiente sin rechazar automáticamente que la dirección proporcionada pertenezca a un host.
        direccion_red_correcta = str(red.network_address)  # Recupera la dirección que realmente representa el comienzo del bloque IPv4 calculado.

        if bloque.direccion_ip == direccion_red_correcta:  # Comprueba si la dirección proporcionada coincide exactamente con el inicio de la red.
            return diagnosticos  # Finaliza sin SEM-002 cuando IP y máscara poseen una relación válida.

        token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera el token completo de la dirección cuando existe una correspondencia con el código original.
        diagnosticos.append(crear_diagnostico(codigo="SEM-002", mensaje=f"La dirección IP '{bloque.direccion_ip}' de la línea {token_ip.linea if token_ip is not None else bloque.linea_origen} no representa la dirección de red para la máscara {bloque.mascara_subred}. La dirección de red correspondiente es '{direccion_red_correcta}'.", linea=token_ip.linea if token_ip is not None else bloque.linea_origen, columna=token_ip.columna if token_ip is not None else None, longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip), fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip))  # Registra SEM-002 mostrando además la dirección de red que correspondería realmente con la máscara.
        return diagnosticos  # Devuelve el error encontrado para impedir que esta red continúe como semánticamente válida.

    def _validar_hosts_positivos(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-003 individualmente sobre cada cantidad escrita después de HOSTS.
        diagnosticos: list[Diagnostico] = []  # Reunirá un diagnóstico independiente por cada cantidad no positiva encontrada.

        for indice_host, cantidad_hosts in enumerate(bloque.cantidades_hosts):  # Recorre todas las solicitudes conservando además su posición dentro de la lista.
            if cantidad_hosts > 0:  # Comprueba si la cantidad representa al menos un host real.
                continue  # Omite las cantidades positivas porque poseen un significado válido para VLSM.

            token_host = ubicacion.tokens_hosts[indice_host] if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts) else None  # Recupera exactamente el NUMBER original cuando existe correspondencia léxica.
            diagnosticos.append(crear_diagnostico(codigo="SEM-003", mensaje=f"Cantidad de HOSTS no válida en la línea {token_host.linea if token_host is not None else bloque.linea_origen}: '{cantidad_hosts}'. Cada solicitud debe ser mayor que cero.", linea=token_host.linea if token_host is not None else bloque.linea_origen, columna=token_host.columna if token_host is not None else None, longitud=len(token_host.valor) if token_host is not None else len(str(cantidad_hosts)), fragmento=token_host.valor if token_host is not None else str(cantidad_hosts)))  # Registra SEM-003 señalando directamente la cantidad cuyo valor no es utilizable.

        return diagnosticos  # Devuelve todas las cantidades no positivas encontradas dentro de la instrucción.

    def _validar_capacidad_individual(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-005 comparando cada solicitud individual con toda la capacidad de la red base.
        diagnosticos: list[Diagnostico] = []  # Reunirá todas las solicitudes individuales que no pueden contenerse dentro de la red proporcionada.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera numéricamente la máscara que ya superó SEM-001.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones pertenecientes a la red base.

        for indice_host, cantidad_hosts in enumerate(bloque.cantidades_hosts):  # Evalúa cada cantidad independientemente antes de revisar el conjunto completo.
            tamano_bloque = self._calcular_tamano_bloque_vlsm(cantidad_hosts)  # Calcula la potencia de dos mínima que necesitaría realmente esta solicitud.

            if tamano_bloque <= capacidad_red:  # Comprueba si el bloque VLSM requerido todavía puede caber dentro de toda la red base.
                continue  # Omite SEM-005 cuando la solicitud es individualmente posible.

            token_host = ubicacion.tokens_hosts[indice_host] if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts) else None  # Recupera exactamente el NUMBER responsable cuando existe una ubicación léxica.
            diagnosticos.append(crear_diagnostico(codigo="SEM-005", mensaje=f"La solicitud de {cantidad_hosts} hosts requiere un bloque VLSM de {tamano_bloque} direcciones, pero la red {bloque.direccion_ip}{bloque.mascara_subred} dispone solamente de {capacidad_red} direcciones.", linea=token_host.linea if token_host is not None else bloque.linea_origen, columna=token_host.columna if token_host is not None else None, longitud=len(token_host.valor) if token_host is not None else len(str(cantidad_hosts)), fragmento=token_host.valor if token_host is not None else str(cantidad_hosts)))  # Registra SEM-005 mostrando la capacidad requerida y la capacidad realmente disponible.

        return diagnosticos  # Devuelve todas las solicitudes individuales imposibles encontradas dentro de la instrucción.

    def _validar_capacidad_total(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-004 comparando la capacidad base con el espacio requerido por todas las solicitudes VLSM juntas.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección para el posible error global de capacidad.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera la máscara cuyo rango ya fue validado previamente.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones disponibles dentro de la red base.
        capacidad_requerida = sum(self._calcular_tamano_bloque_vlsm(cantidad_hosts) for cantidad_hosts in bloque.cantidades_hosts)  # Suma el tamaño real de los bloques potencia de dos que necesitarán todas las solicitudes.

        if capacidad_requerida <= capacidad_red:  # Comprueba si el conjunto completo de subredes puede acomodarse dentro del espacio disponible.
            return diagnosticos  # Finaliza sin SEM-004 cuando la red posee capacidad suficiente.

        token_hosts = ubicacion.token_hosts if ubicacion is not None else None  # Recupera la palabra HOSTS porque el problema pertenece a la lista completa y no a una única cantidad.
        diagnosticos.append(crear_diagnostico(codigo="SEM-004", mensaje=f"Las subredes solicitadas requieren en conjunto {capacidad_requerida} direcciones mediante VLSM, pero la red {bloque.direccion_ip}{bloque.mascara_subred} dispone solamente de {capacidad_red} direcciones.", linea=token_hosts.linea if token_hosts is not None else bloque.linea_origen, columna=token_hosts.columna if token_hosts is not None else None, longitud=len(token_hosts.valor) if token_hosts is not None else len("HOSTS"), fragmento=token_hosts.valor if token_hosts is not None else "HOSTS"))  # Registra SEM-004 señalando la sección responsable del exceso total de capacidad.
        return diagnosticos  # Devuelve el error global para impedir que el bloque continúe como válido.

    def _validar_conflictos_entre_redes(self, candidatos: list[tuple[BloqueRed, UbicacionBloqueSemantico | None]]) -> tuple[list[BloqueRed], list[Diagnostico]]:  # Comprueba SEM-006, SEM-008 y SEM-009 entre redes que ya son correctas individualmente.
        bloques_validos: list[BloqueRed] = []  # Reunirá solamente las declaraciones que no entren en conflicto con ninguna red previamente aceptada.
        redes_aceptadas: list[tuple[BloqueRed, ipaddress.IPv4Network]] = []  # Conserva conjuntamente cada bloque admitido y el intervalo IPv4 que representa.
        diagnosticos: list[Diagnostico] = []  # Reúne todos los conflictos encontrados entre distintas declaraciones.

        for bloque, ubicacion in candidatos:  # Recorre las redes respetando estrictamente el mismo orden en que fueron escritas por el usuario.
            red_actual = ipaddress.IPv4Network(f"{bloque.direccion_ip}{bloque.mascara_subred}", strict=True)  # Construye el intervalo exacto después de que IP y máscara superaron todas sus comprobaciones individuales.
            token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera la dirección de la declaración actual para señalar cualquier conflicto posterior.
            misma_red = next(((bloque_anterior, red_anterior) for bloque_anterior, red_anterior in redes_aceptadas if red_actual == red_anterior), None)  # Busca primero una declaración anterior que represente exactamente el mismo espacio IPv4.

            if misma_red is not None:  # Comprueba SEM-008 antes de clasificar el caso como un traslape genérico.
                bloque_anterior, red_anterior = misma_red  # Recupera la primera declaración del mismo espacio IPv4 para informar dónde apareció originalmente.
                diagnosticos.append(crear_diagnostico(codigo="SEM-008", mensaje=f"La red base {red_actual.with_prefixlen} de la línea {bloque.linea_origen} ya fue declarada anteriormente en la línea {bloque_anterior.linea_origen}. Una misma red base no debe declararse nuevamente con otros datos.", linea=token_ip.linea if token_ip is not None else bloque.linea_origen, columna=token_ip.columna if token_ip is not None else None, longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip), fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip))  # Registra SEM-008 sobre la declaración posterior que reutiliza exactamente la misma red.
                continue  # Conserva la primera definición del espacio y descarta únicamente la declaración posterior.

            misma_ip_distinta_mascara = next(((bloque_anterior, red_anterior) for bloque_anterior, red_anterior in redes_aceptadas if bloque.direccion_ip == bloque_anterior.direccion_ip and bloque.mascara_subred != bloque_anterior.mascara_subred), None)  # Busca una dirección base previamente utilizada con un prefijo diferente.

            if misma_ip_distinta_mascara is not None:  # Comprueba SEM-009 antes de utilizar la regla general de traslape.
                bloque_anterior, red_anterior = misma_ip_distinta_mascara  # Recupera la definición anterior cuya IP base coincide pero cuya máscara es diferente.
                diagnosticos.append(crear_diagnostico(codigo="SEM-009", mensaje=f"La dirección base '{bloque.direccion_ip}' de la línea {bloque.linea_origen} ya fue utilizada con la máscara {bloque_anterior.mascara_subred} en la línea {bloque_anterior.linea_origen}. No puede declararse nuevamente con la máscara {bloque.mascara_subred} porque ambas redes ocuparían parte del mismo espacio IPv4.", linea=token_ip.linea if token_ip is not None else bloque.linea_origen, columna=token_ip.columna if token_ip is not None else None, longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip), fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip))  # Registra SEM-009 diferenciando explícitamente ambas máscaras utilizadas.
                continue  # Conserva la primera definición y rechaza únicamente la declaración posterior incompatible.

            conflicto_traslape = next(((bloque_anterior, red_anterior) for bloque_anterior, red_anterior in redes_aceptadas if red_actual.overlaps(red_anterior)), None)  # Busca finalmente cualquier superposición que no haya sido clasificada como SEM-008 o SEM-009.

            if conflicto_traslape is not None:  # Comprueba SEM-006 para redes diferentes cuyos espacios IPv4 se cruzan.
                bloque_anterior, red_anterior = conflicto_traslape  # Recupera la primera red previamente aceptada responsable de la superposición.
                diagnosticos.append(crear_diagnostico(codigo="SEM-006", mensaje=f"La red base {red_actual.with_prefixlen} de la línea {bloque.linea_origen} se traslapa con la red {red_anterior.with_prefixlen} declarada anteriormente en la línea {bloque_anterior.linea_origen}.", linea=token_ip.linea if token_ip is not None else bloque.linea_origen, columna=token_ip.columna if token_ip is not None else None, longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip), fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip))  # Registra SEM-006 sobre la declaración posterior que invade un espacio previamente aceptado.
                continue  # Descarta únicamente la red posterior y conserva disponible la primera declaración válida.

            bloques_validos.append(bloque)  # Conserva la instrucción actual porque no entra en conflicto con ninguna declaración anterior.
            redes_aceptadas.append((bloque, red_actual))  # Registra su intervalo para poder compararlo con las redes que aparezcan posteriormente.

        return bloques_validos, diagnosticos  # Devuelve conjuntamente las declaraciones aceptadas y todos los conflictos semánticos encontrados.

    def _calcular_tamano_bloque_vlsm(self, cantidad_hosts: int) -> int:  # Calcula la potencia de dos mínima capaz de contener los hosts solicitados más red y broadcast.
        direcciones_necesarias = cantidad_hosts + 2  # Agrega las dos direcciones reservadas que no pueden asignarse directamente a dispositivos.
        exponente = (direcciones_necesarias - 1).bit_length()  # Obtiene el exponente correspondiente con la siguiente potencia de dos suficiente.
        return 1 << exponente  # Devuelve la cantidad real de direcciones que ocuparía la subred dentro del espacio IPv4.

    def _localizar_ubicacion_bloque(self, bloque: BloqueRed) -> UbicacionBloqueSemantico | None:  # Reconstruye la instrucción original para relacionar un bloque sintáctico con sus tokens exactos.
        for indice_inicio, token_inicio in enumerate(self._tokens):  # Recorre cada token que podría representar el comienzo de la instrucción buscada.
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:  # Comprueba que el token pertenezca al comienzo y línea del bloque actual.
                continue  # Descarta cualquier elemento perteneciente a otra instrucción.

            posicion = indice_inicio + 1  # Avanza desde la palabra reservada IP hacia el elemento que debería contener la dirección.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "IP_ADDRESS":  # Comprueba que exista realmente una dirección completa después de IP.
                continue  # Descarta cualquier secuencia incompatible con el comienzo de un bloque semántico válido.

            token_ip = self._tokens[posicion]  # Conserva el token correspondiente con la dirección IPv4 original.

            if token_ip.valor != bloque.direccion_ip:  # Comprueba que la dirección encontrada coincida exactamente con la almacenada por el parser.
                continue  # Evita relacionar accidentalmente el bloque con otra instrucción semejante.

            posicion += 1  # Avanza desde la dirección hacia la palabra reservada MASK.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "MASK":  # Comprueba que la secuencia contenga la palabra obligatoria MASK.
                continue  # Descarta cualquier secuencia que no corresponda con la estructura del bloque buscado.

            posicion += 1  # Avanza desde MASK hacia la máscara CIDR.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "SUBNET_MASK":  # Comprueba que exista un token correspondiente con la máscara.
                continue  # Descarta cualquier secuencia sin la máscara perteneciente al bloque.

            token_mascara = self._tokens[posicion]  # Conserva el token de máscara junto con su ubicación original.

            if token_mascara.valor != bloque.mascara_subred:  # Comprueba que la máscara encontrada coincida exactamente con la almacenada por el parser.
                continue  # Evita relacionar el bloque con otra instrucción que utilice un prefijo diferente.

            posicion += 1  # Avanza desde la máscara hacia la palabra reservada HOSTS.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "HOSTS":  # Comprueba que exista la sección obligatoria correspondiente con las cantidades.
                continue  # Descarta cualquier secuencia incompatible con la instrucción buscada.

            token_hosts = self._tokens[posicion]  # Conserva la propia palabra HOSTS para diagnósticos que correspondan con la lista completa.
            posicion += 1  # Coloca el recorrido sobre el primer elemento que podría representar una cantidad.
            tokens_hosts: list[Token] = []  # Prepara la colección que relacionará cada cantidad sintáctica con su NUMBER original.

            while posicion < len(self._tokens):  # Recorre todos los elementos consecutivos que todavía puedan pertenecer a la lista HOSTS.
                token_actual = self._tokens[posicion]  # Recupera el token situado actualmente bajo revisión.

                if token_actual.tipo == "NUMBER":  # Comprueba si el elemento representa una cantidad individual de hosts.
                    tokens_hosts.append(token_actual)  # Conserva el NUMBER junto con su ubicación exacta.
                    posicion += 1  # Avanza hacia una posible coma o hacia el elemento posterior de la instrucción.
                    continue  # Continúa reconstruyendo la lista mientras todavía existan cantidades.

                if token_actual.tipo == "COMMA":  # Comprueba si el elemento únicamente separa dos cantidades consecutivas.
                    posicion += 1  # Omite la coma porque no representa por sí misma una solicitud de hosts.
                    continue  # Continúa buscando el NUMBER situado después del separador.

                break  # Finaliza la reconstrucción cuando aparece NAME, otra instrucción o cualquier token diferente.

            cantidades_encontradas = [int(token.valor) for token in tokens_hosts]  # Convierte las cantidades recuperadas para poder compararlas con el resultado sintáctico.

            if cantidades_encontradas != bloque.cantidades_hosts:  # Comprueba que toda la lista encontrada coincida exactamente con la almacenada dentro del bloque.
                continue  # Descarta otra instrucción que pueda compartir dirección y máscara pero posea solicitudes diferentes.

            token_nombre = None  # Considera inicialmente que el bloque no contiene la sección opcional NAME.
            nombre_encontrado = None  # Conserva por separado el texto utilizado para comparar el nombre encontrado con el bloque.

            if posicion < len(self._tokens) and self._tokens[posicion].tipo == "NAME":  # Comprueba si después de HOSTS aparece la sección opcional de nombre.
                posicion += 1  # Avanza desde NAME hacia el posible identificador asociado.

                if posicion < len(self._tokens) and self._tokens[posicion].tipo == "IDENTIFIER":  # Comprueba que exista realmente un identificador reconocido.
                    token_nombre = self._tokens[posicion]  # Conserva el token opcional para utilizarlo posteriormente en diagnósticos relacionados.
                    nombre_encontrado = token_nombre.valor  # Recupera el texto concreto para distinguir correctamente bloques semejantes.

            if nombre_encontrado != bloque.nombre:  # Comprueba que la sección opcional coincida también con la información almacenada por el parser.
                continue  # Descarta cualquier instrucción semejante cuyo nombre no pertenezca realmente con el bloque buscado.

            return UbicacionBloqueSemantico(token_ip=token_ip, token_mascara=token_mascara, token_hosts=token_hosts, tokens_hosts=tuple(tokens_hosts), token_nombre=token_nombre)  # Devuelve toda la correspondencia solamente después de comprobar cada componente relevante.

        return None  # Evita inventar posiciones cuando no puede reconstruirse de forma segura la instrucción original.