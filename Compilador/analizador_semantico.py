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
# Actualmente implementa SEM-001, SEM-002, SEM-003,
# SEM-004, SEM-005 y SEM-006.
# ============================================================

from dataclasses import dataclass  # Permite representar de forma organizada e inmutable las ubicaciones léxicas relacionadas con cada bloque.
import ipaddress  # Proporciona las operaciones estándar utilizadas para interpretar direcciones y redes IPv4.

from Motor.diagnosticos import Diagnostico, crear_diagnostico  # Proporciona la estructura y fábrica utilizadas para generar los errores semánticos.
from Motor.modelos import BloqueRed, ResultadoSemantico, Token  # Proporciona los bloques recibidos, el resultado de esta fase y los tokens originales.


@dataclass(frozen=True)  # Impide modificar accidentalmente la correspondencia recuperada entre un bloque y sus tokens originales.
class UbicacionBloqueSemantico:  # Conserva los elementos léxicos necesarios para señalar con precisión los errores semánticos.
    token_ip: Token  # Guarda el token correspondiente con la dirección IPv4 escrita después de IP.
    token_mascara: Token  # Guarda el token correspondiente con la máscara CIDR escrita después de MASK.
    token_hosts: Token  # Guarda la palabra reservada HOSTS para relacionar errores pertenecientes a la lista completa.
    tokens_hosts: tuple[Token, ...]  # Conserva en orden cada NUMBER perteneciente a las cantidades solicitadas.
    token_nombre: Token | None = None  # Conserva el identificador opcional escrito después de NAME cuando existe.


class AnalizadorSemantico:  # Comprueba el significado de los bloques que ya superaron correctamente las fases anteriores.
    def __init__(self, bloques: list[BloqueRed], tokens: list[Token]):  # Recibe los bloques sintácticos junto con sus tokens originales para poder localizar errores.
        self._bloques = list(bloques)  # Conserva una copia de los bloques para no modificar directamente el resultado del parser.
        self._tokens = list(tokens)  # Conserva una copia de los tokens para reconstruir posteriormente la ubicación de cada dato.

    def analizar(self) -> ResultadoSemantico:  # Ejecuta en orden todas las reglas semánticas disponibles actualmente.
        candidatos_traslape: list[tuple[BloqueRed, UbicacionBloqueSemantico | None]] = []  # Reúne redes que superaron todas las reglas individuales antes de comprobar conflictos entre bloques.
        diagnosticos: list[Diagnostico] = []  # Conserva conjuntamente todos los diagnósticos producidos durante esta fase.

        for bloque in self._bloques:  # Recorre individualmente cada instrucción aceptada previamente por el analizador sintáctico.
            ubicacion = self._localizar_ubicacion_bloque(bloque)  # Intenta recuperar los tokens exactos que originaron el bloque actual.
            diagnosticos_bloque: list[Diagnostico] = []  # Mantiene separados los errores correspondientes únicamente con la instrucción actual.

            diagnosticos_mascara = self._validar_mascara(bloque, ubicacion)  # Ejecuta SEM-001 antes de utilizar el prefijo en cualquier otro cálculo.
            diagnosticos_bloque.extend(diagnosticos_mascara)  # Incorpora al bloque cualquier error relacionado con el rango permitido de la máscara.

            if not diagnosticos_mascara:  # Comprueba que la máscara pueda utilizarse de manera segura para interpretar la dirección base.
                diagnosticos_bloque.extend(self._validar_direccion_red(bloque, ubicacion))  # Ejecuta SEM-002 comprobando que la IP represente realmente el inicio de la red.

            diagnosticos_hosts = self._validar_hosts_positivos(bloque, ubicacion)  # Ejecuta SEM-003 antes de calcular bloques VLSM con las cantidades recibidas.
            diagnosticos_bloque.extend(diagnosticos_hosts)  # Incorpora todos los errores correspondientes con cantidades no positivas.

            if not diagnosticos_mascara and not diagnosticos_hosts:  # Permite calcular capacidad solamente cuando máscara y cantidades poseen valores utilizables.
                diagnosticos_bloque.extend(self._validar_capacidad_individual(bloque, ubicacion))  # Ejecuta SEM-005 comprobando cada solicitud de hosts por separado.
                diagnosticos_bloque.extend(self._validar_capacidad_total(bloque, ubicacion))  # Ejecuta SEM-004 comprobando el espacio requerido por todas las solicitudes juntas.

            diagnosticos.extend(diagnosticos_bloque)  # Agrega al resultado general todos los problemas encontrados dentro del bloque actual.

            if not diagnosticos_bloque:  # Comprueba si la instrucción superó completamente las reglas que dependen solamente de sí misma.
                candidatos_traslape.append((bloque, ubicacion))  # Reserva la red para la comprobación posterior de traslapes con otros bloques válidos.

        bloques_validos, diagnosticos_traslape = self._validar_traslapes(candidatos_traslape)  # Ejecuta SEM-006 exclusivamente entre redes individualmente válidas.
        diagnosticos.extend(diagnosticos_traslape)  # Incorpora al resultado general los conflictos encontrados entre redes diferentes.

        return ResultadoSemantico(
            bloques_validos=bloques_validos,  # Conserva únicamente las instrucciones que superaron también la comprobación de traslapes.
            diagnosticos=diagnosticos,  # Devuelve todos los errores semánticos detectados durante la fase.
        )  # Entrega conjuntamente los bloques definitivamente aceptados y sus posibles diagnósticos.

    def _validar_mascara(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-001 sobre el rango permitido de una máscara CIDR.
        prefijo = int(bloque.mascara_subred[1:])  # Convierte en entero únicamente la parte numérica situada después de la diagonal.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección donde se almacenará cualquier error producido por esta regla.

        if 8 <= prefijo <= 30:  # Comprueba si la máscara pertenece al intervalo admitido actualmente por TecNet Finder.
            return diagnosticos  # Finaliza sin errores cuando el prefijo puede utilizarse en las reglas posteriores.

        token_mascara = ubicacion.token_mascara if ubicacion is not None else None  # Recupera la posición exacta de la máscara cuando pudo reconstruirse el bloque.
        diagnosticos.append(
            crear_diagnostico(
                codigo="SEM-001",  # Identifica específicamente una máscara cuyo valor se encuentra fuera del rango permitido.
                mensaje=f"Máscara CIDR fuera del rango permitido en la línea {token_mascara.linea if token_mascara is not None else bloque.linea_origen}: '{bloque.mascara_subred}'. TecNet Finder acepta máscaras entre /8 y /30.",  # Explica el valor incorrecto y recuerda el intervalo aceptado.
                linea=token_mascara.linea if token_mascara is not None else bloque.linea_origen,  # Utiliza la línea exacta del token o la línea general del bloque como respaldo.
                columna=token_mascara.columna if token_mascara is not None else None,  # Conserva la columna de la máscara cuando existe una correspondencia léxica.
                longitud=len(token_mascara.valor) if token_mascara is not None else len(bloque.mascara_subred),  # Permite resaltar toda la máscara tanto con token como mediante el dato del bloque.
                fragmento=token_mascara.valor if token_mascara is not None else bloque.mascara_subred,  # Conserva exactamente la máscara que produjo el diagnóstico.
            )
        )  # Registra SEM-001 señalando el elemento semánticamente inválido.

        return diagnosticos  # Devuelve el diagnóstico para impedir que el bloque continúe como válido.

    def _validar_direccion_red(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-002 relacionando la dirección base con una máscara ya validada.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección utilizada por esta validación.
        red = ipaddress.IPv4Network(f"{bloque.direccion_ip}{bloque.mascara_subred}", strict=False)  # Calcula la red correspondiente sin rechazar automáticamente que la IP recibida sea una dirección de host.
        direccion_red_correcta = str(red.network_address)  # Recupera la dirección que realmente representa el inicio del bloque IPv4 calculado.

        if bloque.direccion_ip == direccion_red_correcta:  # Comprueba si la dirección proporcionada coincide exactamente con el inicio de la red.
            return diagnosticos  # Finaliza sin SEM-002 cuando IP y máscara poseen una relación válida.

        token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera el token de la dirección original cuando se encuentra disponible.
        diagnosticos.append(
            crear_diagnostico(
                codigo="SEM-002",  # Identifica que la IP indicada representa un host en vez de la dirección base correspondiente.
                mensaje=f"La dirección IP '{bloque.direccion_ip}' de la línea {token_ip.linea if token_ip is not None else bloque.linea_origen} no representa la dirección de red para la máscara {bloque.mascara_subred}. La dirección de red correspondiente es '{direccion_red_correcta}'.",  # Explica la inconsistencia y muestra cuál debería ser la dirección correcta.
                linea=token_ip.linea if token_ip is not None else bloque.linea_origen,  # Señala la misma línea donde fue escrita la dirección incorrecta.
                columna=token_ip.columna if token_ip is not None else None,  # Conserva la columna exacta cuando existe el token asociado.
                longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip),  # Permite resaltar toda la dirección IPv4.
                fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip,  # Conserva la IP original responsable del problema.
            )
        )  # Registra SEM-002 sin modificar automáticamente la dirección proporcionada por el usuario.

        return diagnosticos  # Devuelve el error encontrado para impedir que esta red continúe hacia VLSM.

    def _validar_hosts_positivos(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-003 individualmente sobre cada cantidad escrita después de HOSTS.
        diagnosticos: list[Diagnostico] = []  # Reunirá un diagnóstico independiente por cada cantidad inválida encontrada.

        for indice_host, cantidad_hosts in enumerate(bloque.cantidades_hosts):  # Recorre las solicitudes conservando también su posición original dentro de la lista.
            if cantidad_hosts > 0:  # Comprueba si la solicitud representa al menos un host real.
                continue  # Omite cualquier cantidad positiva porque cumple la regla semántica.

            token_host = None  # Parte sin asumir que pudo localizarse un token exacto para la cantidad actual.

            if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts):  # Comprueba que la cantidad posea una correspondencia léxica recuperada.
                token_host = ubicacion.tokens_hosts[indice_host]  # Obtiene el NUMBER perteneciente exactamente a esa posición dentro de HOSTS.

            diagnosticos.append(
                crear_diagnostico(
                    codigo="SEM-003",  # Identifica una solicitud cuya cantidad no representa hosts utilizables.
                    mensaje=f"Cantidad de HOSTS no válida en la línea {token_host.linea if token_host is not None else bloque.linea_origen}: '{cantidad_hosts}'. Cada solicitud debe ser mayor que cero.",  # Explica cuál cantidad incumple la regla semántica.
                    linea=token_host.linea if token_host is not None else bloque.linea_origen,  # Ubica el error sobre la misma instrucción donde apareció la cantidad.
                    columna=token_host.columna if token_host is not None else None,  # Señala exactamente el NUMBER cuando pudo recuperarse.
                    longitud=len(token_host.valor) if token_host is not None else len(str(cantidad_hosts)),  # Permite resaltar todos los dígitos del valor incorrecto.
                    fragmento=token_host.valor if token_host is not None else str(cantidad_hosts),  # Conserva la cantidad concreta que produjo SEM-003.
                )
            )  # Agrega el error y continúa revisando las demás solicitudes del mismo bloque.

        return diagnosticos  # Devuelve todas las cantidades no positivas encontradas dentro de la instrucción.

    def _validar_capacidad_individual(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-005 sobre cada solicitud individual respecto a la red base.
        diagnosticos: list[Diagnostico] = []  # Reunirá todas las solicitudes que no caben individualmente dentro de la red.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera numéricamente la máscara que ya superó SEM-001.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones pertenecientes a la red base.

        for indice_host, cantidad_hosts in enumerate(bloque.cantidades_hosts):  # Evalúa cada solicitud de manera independiente antes de analizar su suma.
            tamano_bloque = self._calcular_tamano_bloque_vlsm(cantidad_hosts)  # Calcula la potencia de dos que ocuparía realmente esta subred.

            if tamano_bloque <= capacidad_red:  # Comprueba si el bloque requerido todavía puede contenerse dentro de toda la red base.
                continue  # Evita producir SEM-005 para cantidades que sí caben individualmente.

            token_host = None  # Parte sin asumir que la cantidad problemática posee ubicación léxica disponible.

            if ubicacion is not None and indice_host < len(ubicacion.tokens_hosts):  # Comprueba si puede relacionarse el índice con su NUMBER original.
                token_host = ubicacion.tokens_hosts[indice_host]  # Recupera exactamente el token de la solicitud excesivamente grande.

            diagnosticos.append(
                crear_diagnostico(
                    codigo="SEM-005",  # Identifica una solicitud individual cuyo bloque VLSM supera por sí solo la capacidad completa.
                    mensaje=f"La solicitud de {cantidad_hosts} hosts requiere un bloque VLSM de {tamano_bloque} direcciones, pero la red {bloque.direccion_ip}{bloque.mascara_subred} dispone solamente de {capacidad_red} direcciones.",  # Compara directamente el espacio requerido con la capacidad disponible.
                    linea=token_host.linea if token_host is not None else bloque.linea_origen,  # Asocia el problema con la instrucción correspondiente.
                    columna=token_host.columna if token_host is not None else None,  # Señala directamente la cantidad problemática cuando fue localizada.
                    longitud=len(token_host.valor) if token_host is not None else len(str(cantidad_hosts)),  # Permite resaltar la solicitud completa.
                    fragmento=token_host.valor if token_host is not None else str(cantidad_hosts),  # Conserva el NUMBER responsable del exceso.
                )
            )  # Registra un SEM-005 independiente para cada solicitud imposible dentro de la red base.

        return diagnosticos  # Devuelve todos los excesos individuales encontrados.

    def _validar_capacidad_total(self, bloque: BloqueRed, ubicacion: UbicacionBloqueSemantico | None) -> list[Diagnostico]:  # Comprueba SEM-004 comparando la capacidad base con todas las solicitudes VLSM juntas.
        diagnosticos: list[Diagnostico] = []  # Prepara la colección para el posible error global de capacidad.
        prefijo = int(bloque.mascara_subred[1:])  # Recupera la máscara cuyo rango ya fue comprobado previamente.
        capacidad_red = 1 << (32 - prefijo)  # Calcula la cantidad total de direcciones disponibles dentro de la red base.
        capacidad_requerida = sum(self._calcular_tamano_bloque_vlsm(cantidad_hosts) for cantidad_hosts in bloque.cantidades_hosts)  # Suma los bloques potencia de dos que realmente necesitará VLSM.

        if capacidad_requerida <= capacidad_red:  # Comprueba si el conjunto completo de subredes puede acomodarse dentro de la red base.
            return diagnosticos  # Finaliza sin SEM-004 cuando existe suficiente espacio total.

        token_hosts = ubicacion.token_hosts if ubicacion is not None else None  # Recupera la palabra HOSTS porque el problema pertenece a la lista completa.
        diagnosticos.append(
            crear_diagnostico(
                codigo="SEM-004",  # Identifica un conjunto de solicitudes cuyo espacio total supera la capacidad disponible.
                mensaje=f"Las subredes solicitadas requieren en conjunto {capacidad_requerida} direcciones mediante VLSM, pero la red {bloque.direccion_ip}{bloque.mascara_subred} dispone solamente de {capacidad_red} direcciones.",  # Explica la diferencia entre capacidad requerida y disponible.
                linea=token_hosts.linea if token_hosts is not None else bloque.linea_origen,  # Relaciona el error con la línea donde se encuentra la lista completa.
                columna=token_hosts.columna if token_hosts is not None else None,  # Señala la palabra reservada HOSTS cuando existe una ubicación precisa.
                longitud=len(token_hosts.valor) if token_hosts is not None else len("HOSTS"),  # Resalta el elemento que introduce las solicitudes responsables del exceso.
                fragmento=token_hosts.valor if token_hosts is not None else "HOSTS",  # Conserva una referencia visible incluso si no pudo recuperarse el token original.
            )
        )  # Registra SEM-004 como un único error perteneciente al conjunto completo de cantidades.

        return diagnosticos  # Devuelve el exceso total para impedir que el bloque continúe hacia el cálculo.

    def _validar_traslapes(self, candidatos: list[tuple[BloqueRed, UbicacionBloqueSemantico | None]]) -> tuple[list[BloqueRed], list[Diagnostico]]:  # Comprueba SEM-006 entre redes que ya son correctas individualmente.
        bloques_validos: list[BloqueRed] = []  # Reunirá solamente las redes que no se traslapan con ninguna declaración previamente aceptada.
        redes_aceptadas: list[tuple[BloqueRed, ipaddress.IPv4Network]] = []  # Conserva cada red ya admitida junto con su intervalo IPv4 calculado.
        diagnosticos: list[Diagnostico] = []  # Reúne todos los conflictos encontrados entre diferentes instrucciones.

        for bloque, ubicacion in candidatos:  # Recorre los candidatos respetando el orden original de aparición del código.
            red_actual = ipaddress.IPv4Network(f"{bloque.direccion_ip}{bloque.mascara_subred}", strict=True)  # Construye el intervalo exacto porque IP y máscara ya superaron SEM-001 y SEM-002.
            conflicto = next(((bloque_anterior, red_anterior) for bloque_anterior, red_anterior in redes_aceptadas if red_actual.overlaps(red_anterior)), None)  # Recupera la primera red previamente aceptada cuyo rango se cruza con la red actual.

            if conflicto is None:  # Comprueba si la nueva red permanece completamente independiente de todas las anteriores.
                bloques_validos.append(bloque)  # Conserva la instrucción para las etapas posteriores del flujo.
                redes_aceptadas.append((bloque, red_actual))  # Registra su intervalo para comparar las declaraciones que aparezcan después.
                continue  # Avanza hacia el siguiente candidato porque no existe ningún conflicto que diagnosticar.

            bloque_anterior, red_anterior = conflicto  # Recupera la primera red previa responsable del traslape encontrado.
            token_ip = ubicacion.token_ip if ubicacion is not None else None  # Recupera la IP de la declaración posterior para relacionar el error con el editor.
            diagnosticos.append(
                crear_diagnostico(
                    codigo="SEM-006",  # Identifica específicamente el conflicto entre dos redes base.
                    mensaje=f"La red base {red_actual.with_prefixlen} de la línea {bloque.linea_origen} se traslapa con la red {red_anterior.with_prefixlen} declarada anteriormente en la línea {bloque_anterior.linea_origen}.",  # Informa ambos intervalos y conserva cuál fue declarado primero.
                    linea=token_ip.linea if token_ip is not None else bloque.linea_origen,  # Ubica el diagnóstico sobre la declaración posterior que produce el conflicto.
                    columna=token_ip.columna if token_ip is not None else None,  # Señala específicamente la dirección de la red posterior.
                    longitud=len(token_ip.valor) if token_ip is not None else len(bloque.direccion_ip),  # Permite resaltar toda la IP correspondiente.
                    fragmento=token_ip.valor if token_ip is not None else bloque.direccion_ip,  # Conserva la dirección exacta responsable del nuevo traslape.
                )
            )  # Rechaza solamente la red posterior para conservar el primer espacio IPv4 previamente aceptado.

        return bloques_validos, diagnosticos  # Devuelve conjuntamente las redes independientes y todos los conflictos encontrados.

    def _calcular_tamano_bloque_vlsm(self, cantidad_hosts: int) -> int:  # Calcula la potencia de dos mínima capaz de contener hosts, red y broadcast.
        direcciones_necesarias = cantidad_hosts + 2  # Agrega las dos direcciones reservadas que no pueden asignarse a dispositivos.
        exponente = (direcciones_necesarias - 1).bit_length()  # Obtiene el exponente de la siguiente potencia de dos sin utilizar números flotantes.
        return 1 << exponente  # Devuelve la cantidad real de direcciones que ocuparía la subred dentro del espacio IPv4.

    def _localizar_ubicacion_bloque(self, bloque: BloqueRed) -> UbicacionBloqueSemantico | None:  # Reconstruye una instrucción para relacionar el bloque sintáctico con sus tokens originales.
        for indice_inicio, token_inicio in enumerate(self._tokens):  # Recorre cada token que podría representar el comienzo de una instrucción.
            if token_inicio.tipo != "IP" or token_inicio.linea != bloque.linea_origen:  # Comprueba que el elemento pueda ser realmente el IP inicial del bloque buscado.
                continue  # Descarta tokens pertenecientes a otra línea o a otra categoría.

            posicion = indice_inicio + 1  # Avanza desde la palabra reservada IP hacia la dirección IPv4.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "IP_ADDRESS":  # Comprueba que la secuencia posea realmente una dirección completa.
                continue  # Descarta cualquier conjunto de tokens que no represente el comienzo correcto de un bloque.

            token_ip = self._tokens[posicion]  # Conserva el token de la dirección junto con su posición original.

            if token_ip.valor != bloque.direccion_ip:  # Comprueba que la IP encontrada coincida exactamente con la almacenada en el bloque.
                continue  # Evita relacionar el bloque con otra instrucción semejante.

            posicion += 1  # Avanza desde la dirección IPv4 hacia MASK.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "MASK":  # Comprueba la siguiente palabra reservada obligatoria.
                continue  # Descarta cualquier secuencia que no corresponda con la estructura esperada.

            posicion += 1  # Avanza desde MASK hacia la máscara CIDR.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "SUBNET_MASK":  # Comprueba que exista realmente un token de máscara.
                continue  # Descarta secuencias que no posean la máscara utilizada por el bloque.

            token_mascara = self._tokens[posicion]  # Conserva el token CIDR con su línea y columna originales.

            if token_mascara.valor != bloque.mascara_subred:  # Comprueba que la máscara localizada sea exactamente la misma del bloque sintáctico.
                continue  # Descarta otra instrucción cuya máscara sea diferente.

            posicion += 1  # Avanza desde la máscara hacia HOSTS.

            if posicion >= len(self._tokens) or self._tokens[posicion].tipo != "HOSTS":  # Comprueba que la sección obligatoria de cantidades exista.
                continue  # Descarta cualquier secuencia incompatible con el bloque recibido.

            token_hosts = self._tokens[posicion]  # Conserva la propia palabra HOSTS para diagnósticos relacionados con el conjunto de solicitudes.
            posicion += 1  # Coloca el recorrido sobre el primer NUMBER de la lista.
            tokens_hosts: list[Token] = []  # Preparará la correspondencia exacta con las cantidades almacenadas en BloqueRed.

            while posicion < len(self._tokens):  # Recorre todos los elementos que todavía puedan pertenecer a la lista HOSTS.
                token_actual = self._tokens[posicion]  # Recupera el token que se encuentra actualmente bajo revisión.

                if token_actual.tipo == "NUMBER":  # Comprueba si el elemento representa una solicitud individual de hosts.
                    tokens_hosts.append(token_actual)  # Conserva el NUMBER junto con su ubicación exacta.
                    posicion += 1  # Avanza hacia una posible coma o hacia el siguiente elemento de la instrucción.
                    continue  # Continúa reconstruyendo la lista mientras existan más cantidades.

                if token_actual.tipo == "COMMA":  # Comprueba si el elemento solamente separa dos solicitudes consecutivas.
                    posicion += 1  # Omite la coma porque no representa una cantidad por sí misma.
                    continue  # Continúa buscando el siguiente NUMBER.

                break  # Finaliza la lista cuando aparece NAME, otra instrucción o cualquier elemento diferente.

            cantidades_encontradas = [int(token.valor) for token in tokens_hosts]  # Convierte las cantidades reconstruidas para compararlas con el resultado sintáctico.

            if cantidades_encontradas != bloque.cantidades_hosts:  # Comprueba que la lista completa coincida exactamente con la instrucción buscada.
                continue  # Descarta otra secuencia cuya red pueda parecerse pero posea distintas solicitudes.

            token_nombre = None  # Considera inicialmente que el bloque no contiene la sección opcional NAME.
            nombre_encontrado = None  # Conserva por separado el texto que permitirá verificar el nombre del bloque.

            if posicion < len(self._tokens) and self._tokens[posicion].tipo == "NAME":  # Comprueba si después de HOSTS aparece la sección opcional.
                posicion += 1  # Avanza desde la palabra reservada NAME hacia su identificador.

                if posicion < len(self._tokens) and self._tokens[posicion].tipo == "IDENTIFIER":  # Comprueba que exista realmente un identificador reconocido.
                    token_nombre = self._tokens[posicion]  # Conserva el token para cualquier validación o navegación posterior.
                    nombre_encontrado = token_nombre.valor  # Recupera el nombre concreto para diferenciar bloques semejantes.

            if nombre_encontrado != bloque.nombre:  # Comprueba que también coincida la sección opcional con la información del parser.
                continue  # Descarta otra instrucción que comparta red y cantidades pero utilice un nombre diferente.

            return UbicacionBloqueSemantico(
                token_ip=token_ip,  # Conserva la dirección IPv4 exacta encontrada para este bloque.
                token_mascara=token_mascara,  # Conserva la máscara CIDR correspondiente.
                token_hosts=token_hosts,  # Conserva la palabra reservada que introduce las solicitudes.
                tokens_hosts=tuple(tokens_hosts),  # Convierte la lista de cantidades a una estructura inmutable.
                token_nombre=token_nombre,  # Conserva el identificador opcional cuando fue utilizado.
            )  # Devuelve la correspondencia solamente después de comprobar todos los componentes relevantes.

        return None  # Evita inventar posiciones cuando no puede reconstruirse de forma segura la instrucción original.