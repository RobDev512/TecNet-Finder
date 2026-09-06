from dataclasses import dataclass


# Catálogo de diagnósticos implementados actualmente.
# Los errores sintácticos, semánticos y demás se agregarán
# conforme se reconstruyan esas fases.
CATALOGO_DIAGNOSTICOS = {
    "LEX-001": {
        "categoria": "Léxico",
        "nombre": "Identificador fuera de lugar",
        "descripcion": (
            "Apareció un identificador en una posición no permitida."
        ),
        "solucion": (
            "Revisa si escribiste mal una palabra reservada. "
            "Por ejemplo, usa MASK en lugar de MAS. "
            "Si era un nombre de red, debe escribirse después de NAME."
        ),
    },

    "LEX-002": {
        "categoria": "Léxico",
        "nombre": "Símbolo o fragmento no reconocido",
        "descripcion": (
            "Apareció un carácter o fragmento que no pertenece al lenguaje."
        ),
        "solucion": (
            "Elimina el símbolo no permitido o reemplázalo por tokens válidos "
            "como IP, MASK, HOSTS, NAME, números, comas o máscaras CIDR."
        ),
    },

    "GEN-001": {
        "categoria": "General",
        "nombre": "Error no clasificado",
        "descripcion": (
            "El error fue detectado, pero no coincide con una categoría específica."
        ),
        "solucion": (
            "Revisa la estructura general de la instrucción."
        ),
    },
}


@dataclass(frozen=True)
class Diagnostico:
    codigo: str
    categoria: str
    severidad: str
    mensaje: str
    linea: int | None = None
    columna: int | None = None
    longitud: int = 1
    fragmento: str = ""
    solucion: str = ""


def crear_diagnostico(
    codigo: str,
    mensaje: str,
    linea: int | None = None,
    columna: int | None = None,
    longitud: int = 1,
    fragmento: str = "",
    severidad: str = "error",
) -> Diagnostico:
    """
    Crea un diagnóstico utilizando la información del catálogo.
    """

    informacion = CATALOGO_DIAGNOSTICOS.get(
        codigo,
        CATALOGO_DIAGNOSTICOS["GEN-001"],
    )

    return Diagnostico(
        codigo=codigo,
        categoria=informacion["categoria"],
        severidad=severidad,
        mensaje=mensaje,
        linea=linea,
        columna=columna,
        longitud=max(longitud, 1),
        fragmento=fragmento,
        solucion=informacion["solucion"],
    )