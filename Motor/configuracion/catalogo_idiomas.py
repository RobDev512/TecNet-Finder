# ============================================================
# Archivo: catalogo_idiomas.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Define los idiomas de interfaz reconocidos por TecNet Finder.
#
# Esta capa solo administra idiomas de la interfaz. Las palabras
# reservadas del DSL (IP, MASK, HOSTS y NAME) pertenecen al
# compilador y no deben traducirse.
# ============================================================

IDIOMA_ESPANOL = "es"  # Identifica el idioma predeterminado y de respaldo.
IDIOMA_INGLES = "en"  # Identifica la interfaz en inglés.
IDIOMA_PORTUGUES = "pt"  # Identifica la interfaz en portugués.
IDIOMA_FRANCES = "fr"  # Identifica la interfaz en francés.
IDIOMA_ALEMAN = "de"  # Identifica la interfaz en alemán.
IDIOMA_LATIN = "la"  # Identifica la interfaz en latín.

IDIOMA_PREDETERMINADO = IDIOMA_ESPANOL  # Mantiene español como idioma inicial de TecNet Finder.
IDIOMA_RESPALDO = IDIOMA_ESPANOL  # Utiliza español cuando una selección almacenada no puede resolverse.

ORDEN_IDIOMAS = (
    IDIOMA_ESPANOL,
    IDIOMA_INGLES,
    IDIOMA_PORTUGUES,
    IDIOMA_FRANCES,
    IDIOMA_ALEMAN,
    IDIOMA_LATIN,
)  # Conserva un orden estable para futuros selectores de interfaz.

NOMBRES_IDIOMAS = {
    IDIOMA_ESPANOL: "Español",
    IDIOMA_INGLES: "English",
    IDIOMA_PORTUGUES: "Português",
    IDIOMA_FRANCES: "Français",
    IDIOMA_ALEMAN: "Deutsch",
    IDIOMA_LATIN: "Lingua Latina",
}  # Utiliza nombres reconocibles por hablantes de cada idioma.


def normalizar_codigo_idioma(codigo) -> str | None:
    if not isinstance(codigo, str):
        return None  # Rechaza tipos incompatibles sin convertirlos silenciosamente.

    limpio = codigo.strip().lower().replace("_", "-")  # Normaliza mayúsculas y variantes habituales como en_US.

    if not limpio:
        return None  # Rechaza cadenas vacías.

    base = limpio.split("-", 1)[0]  # Reduce variantes regionales como es-MX o pt-BR al idioma base.
    return base if base in NOMBRES_IDIOMAS else None  # Acepta exclusivamente idiomas declarados por TecNet Finder.


def resolver_codigo_idioma(codigo) -> str:
    return normalizar_codigo_idioma(codigo) or IDIOMA_RESPALDO  # Recupera español ante datos ausentes, corruptos o desconocidos.


def nombre_idioma(codigo) -> str:
    return NOMBRES_IDIOMAS[resolver_codigo_idioma(codigo)]  # Entrega un nombre seguro incluso si el código recibido no es válido.


def idiomas_disponibles() -> tuple[tuple[str, str], ...]:
    return tuple((codigo, NOMBRES_IDIOMAS[codigo]) for codigo in ORDEN_IDIOMAS)  # Entrega pares estables listos para un selector gráfico.
