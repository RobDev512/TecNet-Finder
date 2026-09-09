# ============================================================
# Archivo: predictor_codigo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo coordina el autocompletado generativo de TecNet
# Finder utilizando el contexto formal de la instrucción.
#
# La IA propone únicamente los datos que todavía hacen falta.
# Los valores ya escritos permanecen bajo control determinista
# de TecNet Finder y nunca se vuelven a delegar al modelo.
# Lexer y parser conservan la decisión final sobre cada propuesta.
# ============================================================

from ipaddress import IPv4Address  # Permite comprobar y normalizar las direcciones IPv4 propuestas por el modelo.
import re  # Permite recuperar los valores que el usuario ya escribió dentro de la instrucción.

from AsistenteIA.contexto_autocompletado import AnalizadorContextoAutocompletado, ContextoAutocompletado  # Importa el reconocimiento formal del punto actual de la gramática.
from AsistenteIA.motor_local import MotorLocalOllama  # Importa el motor encargado de obtener propuestas JSON desde el modelo local.
from Compilador.analizador_lexico import AnalizadorLexico  # Importa el lexer oficial que conserva autoridad sobre los tokens.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa el parser oficial que conserva autoridad sobre la estructura.


class PredictorCodigo:  # Combina valores fijados por el usuario con datos nuevos propuestos por IA.
    def __init__(
        self,
        motor: MotorLocalOllama | None = None,
        analizador_contexto: AnalizadorContextoAutocompletado | None = None,
    ):
        self.motor = motor or MotorLocalOllama()  # Utiliza la instancia local salvo que una prueba proporcione otro motor.
        self.analizador_contexto = analizador_contexto or AnalizadorContextoAutocompletado()  # Prepara el reconocimiento progresivo del prefijo.

    def sugerir(self, prefijo: str) -> str | None:
        prefijo = prefijo.rstrip("\r\n")  # Conserva los espacios horizontales porque forman parte del texto real del editor.

        if not prefijo.strip():
            return None  # Evita generar una instrucción completa desde una línea vacía.

        if self._linea_valida(prefijo):
            return None  # No ofrece más contenido cuando la instrucción ya pertenece completamente al lenguaje.

        resolucion = self._resolver_contexto(prefijo)  # Completa únicamente palabras reservadas determinadas por la gramática.

        if resolucion is None:
            return None  # No consulta IA para texto que ya dejó de pertenecer a una trayectoria válida del DSL.

        prefijo_modelo, completacion_fija, contexto = resolucion  # Separa el texto canónico, el ghost determinista y el elemento variable actual.
        estado = self._extraer_estado(prefijo_modelo)  # Recupera los valores que TecNet Finder ya debe conservar sin volverlos a delegar.
        prompt = self._construir_prompt(contexto, estado)  # Solicita solamente los campos que todavía hacen falta.
        datos = self.motor.generar_json(prompt, maximo_tokens=120)  # Obtiene una pequeña estructura JSON desde Qwen.

        if datos is None:
            return None  # Mantiene el editor sin sugerencia si el modelo no consigue producir datos utilizables.

        linea_completa = self._construir_linea(contexto, estado, datos)  # Fusiona los valores fijos con los nuevos sin permitir sustituciones.

        if linea_completa is None:
            return None  # Descarta tipos, rangos o valores incompatibles con el contexto actual.

        if not linea_completa.startswith(prefijo_modelo):
            return None  # Garantiza que ningún carácter ya escrito o completado formalmente haya sido reemplazado.

        if not self._linea_valida(linea_completa):
            return None  # Conserva lexer y parser como última barrera determinista.

        continuacion_variable = linea_completa[len(prefijo_modelo):]  # Extrae únicamente lo que todavía debe aparecer después del prefijo canónico.
        sugerencia = f"{completacion_fija}{continuacion_variable}"  # Reincorpora la parte formal que debe mostrarse después del texto real.

        return sugerencia or None  # Evita crear un ghost text sin caracteres visibles.

    def _resolver_contexto(
        self,
        prefijo: str,
    ) -> tuple[str, str, ContextoAutocompletado] | None:
        prefijo_modelo = prefijo  # Conserva una copia extensible que nunca modifica directamente el documento.
        completacion_fija = ""  # Acumula exclusivamente caracteres determinados por la gramática.

        for _indice in range(8):
            contexto = self.analizador_contexto.analizar(prefijo_modelo)  # Identifica el elemento que falta después del prefijo actual.

            if not contexto.permitido:
                return None  # Interrumpe el proceso cuando el texto ya no puede continuar dentro del lenguaje.

            if not contexto.completacion_fija:
                return prefijo_modelo, completacion_fija, contexto  # Detiene la expansión al llegar al siguiente valor variable.

            prefijo_modelo += contexto.completacion_fija  # Añade internamente únicamente palabras reservadas y separadores seguros.
            completacion_fija += contexto.completacion_fija  # Conserva los mismos caracteres para el ghost text final.

        return None  # Protege frente a un ciclo inesperado dentro del análisis contextual.

    def _extraer_estado(self, prefijo: str) -> dict:
        estado = {
            "ip": None,
            "fragmento_ip": "",
            "cidr": None,
            "hosts": [],
            "hosts_termina_coma": False,
            "fragmento_nombre": "",
        }  # Reúne únicamente información obtenida del propio texto del usuario.

        coincidencia_ip = re.match(r"^IP\s*([0-9.]*)", prefijo)  # Recupera la dirección completa o parcial situada después de IP.

        if coincidencia_ip:
            fragmento_ip = coincidencia_ip.group(1)  # Conserva exactamente los dígitos y puntos existentes.
            estado["fragmento_ip"] = fragmento_ip  # Permite exigir que una propuesta de dirección mantenga este comienzo.

            if fragmento_ip and self._ipv4_valida(fragmento_ip):
                estado["ip"] = fragmento_ip  # Bloquea una IPv4 completa para que la IA ya no tenga que volver a producirla.

        coincidencia_cidr = re.search(r"\bMASK\s*/(\d+)", prefijo)  # Busca una longitud de prefijo que ya forme parte del texto.

        if coincidencia_cidr:
            estado["cidr"] = int(coincidencia_cidr.group(1))  # Conserva el CIDR existente como valor determinista.

        coincidencia_hosts = re.search(r"\bHOSTS\s+([0-9,]*)", prefijo)  # Recupera la lista parcial de cantidades posterior a HOSTS.

        if coincidencia_hosts:
            texto_hosts = coincidencia_hosts.group(1)  # Conserva la representación escrita hasta la posición actual.
            estado["hosts_termina_coma"] = texto_hosts.endswith(",")  # Permite distinguir una lista terminada de otra que solicita otra cantidad.

            for fragmento in texto_hosts.split(","):
                if fragmento:
                    estado["hosts"].append(int(fragmento))  # Conserva cada cantidad ya escrita para impedir que el modelo la reemplace.

        coincidencia_nombre = re.search(r"\bNAME\s+([A-Za-z_][A-Za-z0-9_]*)$", prefijo)  # Detecta un identificador opcional iniciado.

        if coincidencia_nombre:
            estado["fragmento_nombre"] = coincidencia_nombre.group(1)  # Conserva el inicio exacto del nombre escrito por el usuario.

        return estado  # Entrega un estado exclusivamente derivado del código real del editor.

    def _construir_prompt(
        self,
        contexto: ContextoAutocompletado,
        estado: dict,
    ) -> str:
        if contexto.elemento_actual == "IP_ADDRESS":
            fragmento = estado["fragmento_ip"]  # Recupera cualquier comienzo de dirección que deba respetarse.
            condicion_ip = (
                f'La direccion debe comenzar exactamente con "{fragmento}".'
                if fragmento
                else "Puedes elegir cualquier direccion IPv4 valida."
            )  # Permite libertad cuando todavía no existe dirección y restringe solamente cuando el usuario ya escribió parte.

            return (
                "Genera los datos faltantes para una instruccion TecNet Finder.\n"
                "Devuelve solamente un objeto JSON con las claves ip, cidr, hosts y nombre.\n"
                f"{condicion_ip}\n"
                "ip debe ser una IPv4 completa.\n"
                "cidr debe ser un entero entre 8 y 30.\n"
                "hosts debe ser una lista no vacia de enteros positivos.\n"
                "nombre debe ser un identificador sin espacios o una cadena vacia.\n"
                "No escribas codigo TecNet Finder y no expliques nada."
            )  # Solicita todos los datos porque todavía falta completar la propia dirección.

        if contexto.elemento_actual == "SUBNET_MASK":
            return (
                "Genera solamente los datos que faltan despues de una direccion IPv4 ya fijada.\n"
                "Devuelve solamente un objeto JSON con las claves cidr, hosts y nombre.\n"
                "cidr debe ser un entero entre 8 y 30.\n"
                "hosts debe ser una lista no vacia de enteros positivos.\n"
                "nombre debe ser un identificador sin espacios o una cadena vacia.\n"
                "No incluyas una direccion IP porque ya fue proporcionada por el usuario.\n"
                "No escribas codigo TecNet Finder y no expliques nada."
            )  # Evita pedir nuevamente la IP que TecNet Finder ya conoce.

        if contexto.elemento_actual == "HOST_COUNT":
            existentes = estado["hosts"]  # Recupera las cantidades que no deben volver a ser generadas.

            if existentes:
                informacion = (
                    f"El usuario ya escribio estas cantidades: {existentes}. "
                    "No las repitas; genera una o mas cantidades adicionales."
                )  # Explica únicamente qué valores nuevos se necesitan después de una coma.
            else:
                informacion = "Todavia no existe ninguna cantidad de hosts; genera una o mas."  # Permite construir la lista inicial.

            return (
                "Genera solamente las cantidades de hosts que faltan y un nombre opcional.\n"
                "Devuelve solamente un objeto JSON con las claves hosts_nuevos y nombre.\n"
                f"{informacion}\n"
                "hosts_nuevos debe ser una lista no vacia de enteros positivos.\n"
                "nombre debe ser un identificador sin espacios o una cadena vacia.\n"
                "No incluyas direccion IP ni CIDR porque ya fueron fijados por el usuario.\n"
                "No escribas codigo TecNet Finder y no expliques nada."
            )  # Solicita exclusivamente información nueva de la lista.

        if contexto.elemento_actual == "IDENTIFIER":
            fragmento = estado["fragmento_nombre"]  # Conserva cualquier comienzo de identificador ya escrito.
            condicion = (
                f'El nombre debe comenzar exactamente con "{fragmento}".'
                if fragmento
                else "Genera un identificador valido."
            )  # Impide reemplazar un fragmento de nombre existente.

            return (
                "Genera solamente el nombre faltante de una instruccion TecNet Finder.\n"
                "Devuelve solamente un objeto JSON con la clave nombre.\n"
                f"{condicion}\n"
                "nombre debe comenzar por letra o guion bajo y continuar con letras, numeros o guion bajo.\n"
                "No incluyas direccion IP, CIDR ni hosts porque ya fueron fijados por el usuario.\n"
                "No escribas codigo TecNet Finder y no expliques nada."
            )  # Reduce la generación a un único valor cuando toda la estructura previa ya existe.

        return ""  # Mantiene una salida segura ante cualquier contexto futuro todavía no contemplado.

    def _construir_linea(
        self,
        contexto: ContextoAutocompletado,
        estado: dict,
        datos: dict,
    ) -> str | None:
        ip = estado["ip"]  # Prefiere siempre la dirección ya escrita y bloqueada por TecNet Finder.

        if contexto.elemento_actual == "IP_ADDRESS":
            ip = self._obtener_ip_generada(datos.get("ip"), estado["fragmento_ip"])  # Utiliza IA solamente cuando la dirección todavía está incompleta.

        if ip is None:
            return None  # No puede construirse una instrucción final sin una dirección completa.

        cidr = estado["cidr"]  # Conserva una máscara ya escrita sin pedirla nuevamente.

        if cidr is None:
            cidr = self._obtener_cidr(datos.get("cidr"))  # Solicita un CIDR nuevo únicamente cuando todavía no existe.

        if cidr is None:
            return None  # Descarta propuestas sin una longitud de prefijo válida.

        hosts_existentes = list(estado["hosts"])  # Copia las cantidades escritas para que nunca sean modificadas por la generación.

        if contexto.elemento_actual == "HOST_COUNT":
            hosts_nuevos = self._normalizar_hosts(datos.get("hosts_nuevos"))  # Obtiene únicamente cantidades posteriores a la posición actual.

            if hosts_nuevos is None:
                return None  # Exige al menos una cantidad nueva cuando el cursor se encuentra completando HOSTS.

            hosts = hosts_existentes + hosts_nuevos  # Fusiona determinísticamente lo escrito con los valores nuevos.
        elif hosts_existentes:
            hosts = hosts_existentes  # Conserva la lista completa cuando ya fue fijada por el usuario.
        else:
            hosts = self._normalizar_hosts(datos.get("hosts"))  # Solicita la lista completa solamente antes de comenzar a escribirla.

            if hosts is None:
                return None  # Descarta respuestas sin una lista válida.

        nombre = self._obtener_nombre(contexto, estado, datos)  # Recupera un identificador nuevo o conserva las restricciones del fragmento actual.

        if nombre is None:
            return None  # Descarta nombres con tipos o caracteres incompatibles.

        lista_hosts = ",".join(str(cantidad) for cantidad in hosts)  # Serializa las cantidades utilizando la coma propia de la gramática.
        linea = f"IP {ip} MASK /{cidr} HOSTS {lista_hosts}"  # Construye internamente toda la sección obligatoria.

        if nombre:
            linea += f" NAME {nombre}"  # Agrega NAME únicamente cuando existe realmente un identificador.

        return linea  # Devuelve la línea completa todavía pendiente de lexer y parser.

    def _obtener_ip_generada(self, valor, fragmento: str) -> str | None:
        if not isinstance(valor, str):
            return None  # Exige que la IA represente la dirección mediante una cadena JSON.

        try:
            ip = str(IPv4Address(valor.strip()))  # Normaliza y valida los cuatro octetos mediante la biblioteca estándar.
        except ValueError:
            return None  # Rechaza cualquier valor que no sea una IPv4 real.

        if fragmento and not ip.startswith(fragmento):
            return None  # Impide que la IA sustituya un fragmento que ya fue escrito por el usuario.

        return ip  # Entrega una dirección compatible con el texto existente.

    def _obtener_cidr(self, valor) -> int | None:
        if not isinstance(valor, int) or isinstance(valor, bool):
            return None  # Exige un entero JSON real en lugar de cadenas o booleanos.

        if not 8 <= valor <= 30:
            return None  # Mantiene las propuestas dentro del rango utilizado por TecNet Finder.

        return valor  # Entrega una longitud de prefijo estructuralmente utilizable.

    def _normalizar_hosts(self, valor) -> list[int] | None:
        if not isinstance(valor, list) or not valor:
            return None  # Exige una lista no vacía cuando realmente hacen falta cantidades nuevas.

        resultado: list[int] = []  # Conserva solamente valores enteros positivos.

        for cantidad in valor:
            if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
                return None  # Rechaza cadenas, booleanos, cero y cantidades negativas.

            resultado.append(cantidad)  # Conserva cada cantidad válida sin reinterpretar su valor.

        return resultado  # Entrega una lista segura para la serialización del DSL.

    def _obtener_nombre(
        self,
        contexto: ContextoAutocompletado,
        estado: dict,
        datos: dict,
    ) -> str | None:
        valor = datos.get("nombre", "")  # Interpreta la ausencia de NAME como una cadena vacía.

        if valor is None:
            valor = ""  # Tolera null únicamente como ausencia de la sección opcional.

        if not isinstance(valor, str):
            return None  # Exige un nombre textual cuando el modelo decide proporcionar uno.

        nombre = valor.strip()  # Elimina espacios externos que nunca formarían parte del identificador.

        if not nombre:
            if contexto.elemento_actual == "IDENTIFIER":
                return None  # NAME ya iniciado exige que finalmente exista un identificador.

            return ""  # Permite omitir completamente la sección opcional en los demás contextos.

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nombre):
            return None  # Rechaza cualquier valor que el lexer no pueda tratar como identificador.

        fragmento = estado["fragmento_nombre"]  # Recupera el inicio de nombre ya escrito, cuando exista.

        if fragmento and not nombre.startswith(fragmento):
            return None  # Impide sustituir caracteres que el usuario ya colocó después de NAME.

        return nombre  # Entrega un identificador compatible con el prefijo actual.

    def _ipv4_valida(self, texto: str) -> bool:
        try:
            IPv4Address(texto)  # Comprueba si el fragmento ya representa una dirección IPv4 completa.
            return True
        except ValueError:
            return False  # Considera incompleto cualquier fragmento que todavía no forme cuatro octetos válidos.

    def _linea_valida(self, linea: str) -> bool:
        resultado_lexico = AnalizadorLexico().analizar(linea)  # Ejecuta el lexer oficial sobre la línea construida.

        if resultado_lexico.tiene_errores:
            return False  # Rechaza cualquier propuesta con errores léxicos.

        resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()  # Entrega los tokens al parser oficial.

        if resultado_sintactico.tiene_errores:
            return False  # Rechaza cualquier propuesta fuera de la estructura aceptada.

        return len(resultado_sintactico.bloques) == 1  # Exige exactamente una instrucción completa antes de mostrarla.