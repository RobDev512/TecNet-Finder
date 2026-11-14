# ============================================================
# Archivo: sugerencias_codigo_local.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Ofrece únicamente palabras reservadas y signos del DSL.
# Las direcciones, máscaras, cantidades y nombres son datos
# del usuario y nunca aparecen como valores sugeridos.
# Conserva una plantilla completa de inserción opcional.
# ============================================================

from dataclasses import dataclass  # Define opciones inmutables sin depender de la interfaz.
import re  # Reconoce el contexto de cada token dentro de la instrucción.


@dataclass(frozen=True)
class SugerenciaCodigo:  # Describe una sugerencia visible y su inserción real.
    etiqueta: str  # Muestra una palabra reservada, signo o descripción de plantilla.
    insercion: str  # Inserta exactamente este texto al confirmar.
    descripcion: str  # Explica la opción mediante una ayuda contextual.
    seleccionar_desde: int = -1  # Indica el comienzo del campo editable de la plantilla.
    seleccionar_longitud: int = 0  # Conserva la longitud de la primera selección.


EJEMPLO_BLOQUE = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Conserva intacta la inserción anterior.
ETIQUETA_PLANTILLA = "IP xxx.xxx.x.x MASK /x HOSTS x,y,z NAME Nombre"  # Muestra la estructura sin proponer datos concretos.
IPV4 = r"\d{1,3}(?:\.\d{1,3}){3}"  # Reconoce la estructura de cuatro octetos para ubicar MASK.
HOSTS = r"\d+(?:,\d+)*"  # Reconoce una lista de cantidades para ubicar NAME o una coma.


def _reservada(nombre: str, descripcion: str) -> SugerenciaCodigo:
    return SugerenciaCodigo(nombre, nombre + " ", descripcion)  # Separa la palabra reservada de su siguiente valor.


def obtener_sugerencias_codigo(linea: str, *, manual: bool = False) -> tuple[str, list[SugerenciaCodigo]]:
    """Devuelve (prefijo, opciones) sin sugerir datos que debe escribir el usuario."""
    if not isinstance(linea, str) or "\n" in linea or "\r" in linea or len(linea) > 500: return "", []  # Trabaja solo con una línea razonable.
    palabra = re.search(r"([A-Za-z_][A-Za-z_0-9]*)$", linea)  # Detecta únicamente un prefijo alfabético de palabra reservada.
    prefijo = palabra.group(1) if palabra else ""  # No interpreta números ni signos como prefijos de funciones.
    contexto = linea[:palabra.start()] if palabra else linea  # Conserva el texto anterior para comprobar la etapa actual.
    opciones: list[SugerenciaCodigo] = []  # No propone nada mientras no exista un token apropiado.

    if not contexto.strip():  # Antes de IP no hay ninguna otra palabra reservada válida.
        opciones = [_reservada("IP", "Palabra reservada que inicia una instrucción de red"), SugerenciaCodigo(ETIQUETA_PLANTILLA, EJEMPLO_BLOQUE, "Inserta una instrucción completa y selecciona la dirección IP para editarla", 3, len("192.168.1.0"))]
    elif re.fullmatch(rf"\s*IP\s+{IPV4}\s+", contexto, re.IGNORECASE):
        opciones = [_reservada("MASK", "Palabra reservada que introduce la máscara CIDR")]
    elif re.fullmatch(rf"\s*IP\s+{IPV4}\s+MASK\s+/\d+\s+", contexto, re.IGNORECASE):
        opciones = [_reservada("HOSTS", "Palabra reservada que introduce la cantidad de hosts")]
    elif re.fullmatch(rf"\s*IP\s+{IPV4}\s+MASK\s+/\d+\s+HOSTS\s+{HOSTS}\s+", contexto, re.IGNORECASE):
        opciones = [_reservada("NAME", "Palabra reservada opcional que asigna un nombre a la red")]

    # Los signos solo se ofrecen bajo solicitud Ctrl+Espacio; no irrumpen al escribir números o espacios.
    if manual and not prefijo:
        if re.fullmatch(rf"\s*IP\s+{IPV4}\s+MASK\s+", linea, re.IGNORECASE):
            opciones = [SugerenciaCodigo("/", "/", "Separador inicial de la máscara CIDR")]
        elif re.fullmatch(r"\s*IP\s+\d{1,3}(?:\.\d{1,3}){0,2}", linea, re.IGNORECASE):
            opciones = [SugerenciaCodigo(".", ".", "Separador entre los octetos de una IPv4")]
        elif re.fullmatch(rf"\s*IP\s+{IPV4}\s+MASK\s+/\d+\s+HOSTS\s+{HOSTS}", linea, re.IGNORECASE):
            opciones = [SugerenciaCodigo(",", ",", "Separador entre cantidades de hosts")]

    if not manual and not prefijo: return "", []  # Evita desplegables invasivos al escribir espacios, cifras o signos.
    if prefijo and not (len(prefijo) >= 1 and prefijo[0].upper() in "IMHN"): return prefijo, []  # Descarta rápidamente nombres y texto ajeno a las palabras reservadas.
    filtradas = [opcion for opcion in opciones if opcion.etiqueta.casefold().startswith(prefijo.casefold()) and opcion.etiqueta != prefijo]  # Filtra por prefijo, sin mostrar el token terminado.
    return prefijo, filtradas  # Deja al editor la presentación y aceptación de opciones.
