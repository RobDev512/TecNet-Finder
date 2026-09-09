# ============================================================
# Archivo: contexto_autocompletado.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo analiza el prefijo que el usuario está escribiendo
# para determinar qué elemento de la gramática de TecNet Finder
# se encuentra actualmente incompleto.
#
# No genera valores ni decide la validez final del código. Su
# función es proporcionar contexto formal al asistente de IA y
# completar únicamente palabras reservadas conocidas del lenguaje.
# ============================================================

from dataclasses import dataclass  # Permite representar el contexto formal mediante una estructura pequeña e inmutable.
from ipaddress import IPv4Address  # Permite comprobar cuándo una dirección escrita ya contiene una IPv4 completa.
import re  # Permite reconocer fragmentos parciales de los elementos que forman la instrucción.


@dataclass(frozen=True)
class ContextoAutocompletado:  # Describe la posición formal donde se encuentra actualmente el usuario.
    permitido: bool  # Indica si el prefijo todavía puede pertenecer al lenguaje TecNet Finder.
    elemento_actual: str = ""  # Identifica el elemento gramatical que debe continuar.
    fragmento_actual: str = ""  # Conserva la parte del elemento variable que el usuario ya escribió.
    completacion_fija: str = ""  # Contiene únicamente caracteres deterministas pertenecientes a la gramática.
    descripcion: str = ""  # Explica al modelo qué debe completar sin proporcionarle valores concretos.


class AnalizadorContextoAutocompletado:  # Reconoce progresivamente el punto de la gramática donde termina el prefijo.
    DESCRIPCIONES = {
        "IP_ADDRESS": (
            "Completa la direccion IPv4 que se encuentra en curso. "
            "Conserva exactamente cualquier octeto o fragmento que el usuario ya escribio. "
            "Despues de terminarla deben aparecer MASK, una mascara CIDR y HOSTS."
        ),
        "SUBNET_MASK": (
            "Completa la mascara en notacion CIDR comenzando con '/'. "
            "Despues deben aparecer HOSTS y una o mas cantidades enteras."
        ),
        "HOST_COUNT": (
            "Completa una cantidad entera de hosts o, si existe una coma al final, "
            "la siguiente cantidad. Puede continuar con mas cantidades separadas por comas "
            "y opcionalmente con NAME seguido de un identificador."
        ),
        "IDENTIFIER": (
            "Completa un identificador valido para NAME usando letras, numeros o guion bajo, "
            "sin espacios internos."
        ),
        "OPTIONAL_NAME": (
            "La instruccion ya posee cantidades de hosts. NAME es opcional y solamente debe "
            "aparecer si resulta apropiado continuar con un nombre de red."
        ),
    }  # Mantiene instrucciones formales y generales sin enseñar respuestas concretas al modelo.

    def analizar(self, prefijo: str) -> ContextoAutocompletado:
        if "\n" in prefijo or "\r" in prefijo:
            return self._invalido()  # El ghost text actual trabaja exclusivamente sobre una línea independiente.

        if not prefijo.strip():
            return self._invalido()  # No intenta construir instrucciones desde una entrada completamente vacía.

        if prefijo == "I":
            return self._crear("IP_ADDRESS", completacion_fija="P ")  # Completa determinísticamente la palabra reservada inicial.

        if prefijo == "IP":
            return self._crear("IP_ADDRESS", completacion_fija=" ")  # Añade únicamente el separador canónico antes de la dirección.

        if not prefijo.startswith("IP"):
            return self._invalido()  # Rechaza texto que ya no puede comenzar con la palabra reservada obligatoria.

        resto = prefijo[2:]  # Conserva todo lo escrito después de IP para analizar la dirección.

        if not resto:
            return self._crear("IP_ADDRESS", completacion_fija=" ")  # Prepara la separación necesaria antes del primer valor variable.

        if resto[0].isspace():
            contenido = resto.lstrip()  # Omite solamente el espacio estructural que separa IP de la dirección.
        elif resto[0].isdigit():
            contenido = resto  # Tolera la forma pegada que el lexer heredado todavía reconoce.
        else:
            return self._invalido()  # Descarta cualquier otro símbolo inmediatamente posterior a IP.

        if not contenido:
            return self._crear("IP_ADDRESS")  # El usuario ya proporcionó el separador y todavía falta la dirección.

        return self._analizar_direccion(contenido)  # Continúa recorriendo la gramática desde el valor IPv4.

    def _analizar_direccion(self, contenido: str) -> ContextoAutocompletado:
        coincidencia = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})(.*)$", contenido)  # Intenta separar una IPv4 completa del contenido posterior.

        if coincidencia:
            direccion = coincidencia.group(1)  # Recupera los cuatro octetos candidatos.
            resto = coincidencia.group(2)  # Conserva cualquier contenido situado después de la dirección.

            try:
                IPv4Address(direccion)  # Comprueba que cada octeto esté dentro del rango permitido.
            except ValueError:
                return self._invalido()  # No propone completar una dirección que ya resulta imposible.

            return self._analizar_mask(resto)  # Continúa hacia la palabra reservada MASK cuando la IPv4 ya terminó.

        if self._es_fragmento_ipv4(contenido):
            return self._crear("IP_ADDRESS", fragmento_actual=contenido)  # Informa al modelo del fragmento arbitrario que debe conservar.

        return self._invalido()  # Descarta combinaciones que ya no pueden formar una dirección IPv4.

    def _analizar_mask(self, resto: str) -> ContextoAutocompletado:
        if not resto:
            return self._crear("SUBNET_MASK", completacion_fija=" MASK ")  # Inserta la palabra formal completa cuando todavía no se comenzó a escribir.

        if not resto[0].isspace():
            return self._invalido()  # Evita recomendar una palabra nueva pegada a la dirección ya escrita.

        contenido = resto.lstrip()  # Retira únicamente la separación existente después de la dirección.

        if not contenido:
            return self._crear("SUBNET_MASK", completacion_fija="MASK ")  # Aprovecha el espacio que el usuario ya proporcionó.

        if contenido in {"M", "MA", "MAS", "MASK"}:
            faltante = "MASK"[len(contenido):]  # Calcula exclusivamente los caracteres deterministas que faltan.
            completacion = f"{faltante} " if faltante else " "  # Finaliza la palabra y prepara el valor CIDR.
            return self._crear("SUBNET_MASK", completacion_fija=completacion)  # Deja el valor real de la máscara para la IA.

        if not contenido.startswith("MASK"):
            return self._invalido()  # Descarta cualquier palabra diferente en esta posición obligatoria.

        return self._analizar_mascara(contenido[4:])  # Continúa después de MASK.

    def _analizar_mascara(self, resto: str) -> ContextoAutocompletado:
        if not resto:
            return self._crear("SUBNET_MASK", completacion_fija=" ")  # Añade el separador canónico cuando MASK acaba de escribirse.

        contenido = resto.lstrip()  # Permite analizar tanto MASK /24 como la forma pegada tolerada por el lexer.

        if not contenido:
            return self._crear("SUBNET_MASK")  # El usuario ya dejó espacio y todavía no escribió la máscara.

        coincidencia = re.match(r"^(/(?:\d+)?)(.*)$", contenido)  # Separa la máscara parcial o completa del contenido siguiente.

        if not coincidencia:
            return self._invalido()  # Exige que la máscara empiece mediante la diagonal propia del lenguaje.

        mascara = coincidencia.group(1)  # Conserva la parte CIDR encontrada.
        resto_posterior = coincidencia.group(2)  # Conserva cualquier contenido situado después de la máscara.

        if mascara == "/":
            if resto_posterior:
                return self._invalido()  # No permite comenzar otro elemento antes de proporcionar los dígitos.

            return self._crear("SUBNET_MASK", fragmento_actual="/")  # Solicita al modelo completar el valor numérico.

        if resto_posterior:
            return self._analizar_hosts(resto_posterior)  # Continúa hacia HOSTS cuando ya existe contenido posterior.

        return self._crear("HOST_COUNT", completacion_fija=" HOSTS ")  # Una máscara completa permite avanzar al siguiente elemento.

    def _analizar_hosts(self, resto: str) -> ContextoAutocompletado:
        if not resto:
            return self._crear("HOST_COUNT", completacion_fija=" HOSTS ")  # Inserta la palabra obligatoria cuando todavía no fue iniciada.

        if not resto[0].isspace():
            return self._invalido()  # Evita introducir HOSTS pegado a la máscara completa.

        contenido = resto.lstrip()  # Aprovecha la separación que el usuario ya escribió.

        if not contenido:
            return self._crear("HOST_COUNT", completacion_fija="HOSTS ")  # Completa la palabra y deja la cantidad para la IA.

        if contenido in {"H", "HO", "HOS", "HOST", "HOSTS"}:
            faltante = "HOSTS"[len(contenido):]  # Calcula la terminación exacta de la palabra reservada.
            completacion = f"{faltante} " if faltante else " "  # Deja preparado el comienzo de la lista numérica.
            return self._crear("HOST_COUNT", completacion_fija=completacion)  # No inventa todavía ninguna cantidad.

        if not contenido.startswith("HOSTS"):
            return self._invalido()  # Descarta palabras distintas en una posición formalmente obligatoria.

        return self._analizar_lista_hosts(contenido[5:])  # Continúa después de HOSTS.

    def _analizar_lista_hosts(self, resto: str) -> ContextoAutocompletado:
        if not resto:
            return self._crear("HOST_COUNT", completacion_fija=" ")  # Añade el separador habitual antes del primer número.

        contenido = resto.lstrip()  # Permite analizar la lista independientemente de la cantidad de espacios utilizada.

        if not contenido:
            return self._crear("HOST_COUNT")  # El usuario ya escribió el espacio pero todavía no comenzó una cantidad.

        coincidencia = re.match(r"^(\d+(?:,\d+)*,?)(.*)$", contenido)  # Reconoce una lista numérica completa o terminada temporalmente en coma.

        if not coincidencia:
            return self._invalido()  # Descarta cualquier contenido que no pueda comenzar una lista.

        lista = coincidencia.group(1)  # Conserva las cantidades escritas hasta el momento.
        resto_posterior = coincidencia.group(2)  # Obtiene cualquier contenido situado después de la lista.

        if lista.endswith(","):
            if resto_posterior:
                return self._invalido()  # Una coma exige otra cantidad antes de cualquier otra sección.

            return self._crear("HOST_COUNT")  # Solicita una nueva cantidad sin imponer un valor específico.

        if not resto_posterior:
            return self._crear("OPTIONAL_NAME")  # La lista ya podría terminar la instrucción y NAME continúa siendo opcional.

        return self._analizar_name(resto_posterior)  # Analiza la sección opcional cuando el usuario comenzó a escribir después.

    def _analizar_name(self, resto: str) -> ContextoAutocompletado:
        if not resto:
            return self._crear("OPTIONAL_NAME")  # No obliga a utilizar NAME cuando la lista ya es suficiente.

        if not resto[0].isspace():
            return self._invalido()  # Mantiene NAME separado de la cantidad anterior.

        contenido = resto.lstrip()  # Omite únicamente el espacio estructural antes de la palabra opcional.

        if not contenido:
            return self._crear("OPTIONAL_NAME")  # Conserva la posibilidad de terminar o comenzar NAME.

        if contenido in {"N", "NA", "NAM", "NAME"}:
            faltante = "NAME"[len(contenido):]  # Completa exclusivamente la palabra reservada opcional.
            completacion = f"{faltante} " if faltante else " "  # Prepara el identificador.
            return self._crear("IDENTIFIER", completacion_fija=completacion)  # Mantiene el nombre concreto como responsabilidad del modelo.

        if not contenido.startswith("NAME"):
            return self._invalido()  # Descarta cualquier palabra diferente después de la lista de hosts.

        return self._analizar_identificador(contenido[4:])  # Continúa hacia el identificador.

    def _analizar_identificador(self, resto: str) -> ContextoAutocompletado:
        if not resto:
            return self._crear("IDENTIFIER", completacion_fija=" ")  # Añade el separador requerido después de NAME.

        if not resto[0].isspace():
            return self._invalido()  # Exige separación antes del identificador.

        contenido = resto.lstrip()  # Obtiene únicamente el identificador que el usuario comenzó a escribir.

        if not contenido:
            return self._crear("IDENTIFIER")  # Solicita al modelo un identificador todavía inexistente.

        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", contenido):
            return self._crear("IDENTIFIER", fragmento_actual=contenido)  # Conserva un fragmento formalmente posible.

        return self._invalido()  # Descarta espacios internos o caracteres no permitidos.

    def _es_fragmento_ipv4(self, texto: str) -> bool:
        if not texto or any(caracter not in "0123456789." for caracter in texto):
            return False  # Una dirección parcial solamente puede contener dígitos y puntos.

        partes = texto.split(".")  # Divide los octetos parciales.

        if len(partes) > 4:
            return False  # Una IPv4 nunca puede contener más de cuatro octetos.

        for indice, parte in enumerate(partes):
            if not parte:
                if indice != len(partes) - 1:
                    return False  # Solo el último octeto puede estar temporalmente vacío.

                continue

            if len(parte) > 3 or int(parte) > 255:
                return False  # Evita continuar un octeto que ya no podría convertirse en válido.

        return True  # Considera posible cualquier fragmento que todavía pueda terminar como una IPv4.

    def _crear(
        self,
        elemento_actual: str,
        fragmento_actual: str = "",
        completacion_fija: str = "",
    ) -> ContextoAutocompletado:
        return ContextoAutocompletado(
            permitido=True,
            elemento_actual=elemento_actual,
            fragmento_actual=fragmento_actual,
            completacion_fija=completacion_fija,
            descripcion=self.DESCRIPCIONES.get(elemento_actual, ""),
        )  # Construye un contexto válido utilizando únicamente información formal del lenguaje.

    def _invalido(self) -> ContextoAutocompletado:
        return ContextoAutocompletado(permitido=False)  # Representa prefijos que el asistente no debe intentar reparar mediante IA.