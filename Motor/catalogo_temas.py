# ============================================================
# Archivo: catalogo_temas.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Centraliza todos los temas visuales disponibles en TecNet
# Finder y las paletas asociadas con cada variante.
#
# Cada tema posee:
# - Un identificador interno estable.
# - Un modo: oscuro o claro.
# - Un nombre visible.
# - Una descripción.
# - Una paleta completa de interfaz.
#
# Los colores semánticos conservan siempre su significado:
# error, advertencia, éxito, sintaxis, semántica y subred.
# Sin embargo, se utilizan tonos diferentes en modo claro para
# conservar suficiente contraste sobre fondos luminosos.
# ============================================================

MODO_OSCURO = "oscuro"  # Identifica la familia de temas oscuros.
MODO_CLARO = "claro"  # Identifica la familia de temas claros.

TEMA_OSCURO_TECNET = "oscuro_tecnet"  # Conserva la apariencia oscura original de TecNet Finder.
TEMA_OSCURO_MEDIANOCHE = "oscuro_medianoche"  # Utiliza fondos violetas profundos y acento lavanda.
TEMA_OSCURO_OCEANO = "oscuro_oceano"  # Utiliza fondos azul petróleo y acento cian.
TEMA_CLARO_TECNET = "claro_tecnet"  # Representa la versión clara principal de TecNet Finder.
TEMA_CLARO_NIEBLA = "claro_niebla"  # Representa una variante clara más gris y discreta.

TEMA_PREDETERMINADO = TEMA_OSCURO_TECNET  # Mantiene la apariencia histórica como valor inicial.

MODOS = (
    {"id": MODO_OSCURO, "nombre": "Oscuro"},  # Presenta el modo oscuro dentro de Configuración.
    {"id": MODO_CLARO, "nombre": "Claro"},  # Presenta el modo claro dentro de Configuración.
)  # El orden declarado también determina el orden visible de los modos.

SEMANTICOS_OSCUROS = {
    "exito": "#a6e3a1",  # Mantiene verde claro para resultados satisfactorios.
    "advertencia": "#f9e2af",  # Mantiene amarillo para recomendaciones no bloqueantes.
    "error": "#f38ba8",  # Mantiene rosa/rojo para errores y estados bloqueantes.
    "sintactico": "#fab387",  # Mantiene naranja para diagnósticos sintácticos.
    "semantico": "#cba6f7",  # Mantiene morado para diagnósticos semánticos.
    "subred": "#94e2d5",  # Mantiene turquesa para información relacionada con subredes.
}  # Estos tonos funcionan correctamente sobre fondos oscuros.

SEMANTICOS_CLAROS = {
    "exito": "#287a3d",  # Utiliza un verde más oscuro para conservar contraste sobre blanco.
    "advertencia": "#946200",  # Utiliza ámbar oscuro para mantener legibles las advertencias.
    "error": "#c42b1c",  # Utiliza rojo intenso para errores sobre fondos claros.
    "sintactico": "#b45309",  # Utiliza naranja oscuro para diagnósticos sintácticos.
    "semantico": "#7c3aed",  # Utiliza violeta intenso para diagnósticos semánticos.
    "subred": "#0f766e",  # Utiliza turquesa oscuro para información de subredes.
}  # El significado no cambia aunque los tonos se adapten al modo claro.

TEMAS = {
    TEMA_OSCURO_TECNET: {
        "id": TEMA_OSCURO_TECNET,  # Conserva un identificador estable independiente del idioma.
        "modo": MODO_OSCURO,  # Agrupa esta variante dentro del modo oscuro.
        "nombre": "TecNet",  # Presenta el nombre corto dentro de Configuración.
        "descripcion": "Tema oscuro original de TecNet Finder con fondos gris azulados y acento azul.",  # Resume su apariencia.
        "fondo": "#1e1e2e",  # Define el fondo principal actual.
        "panel": "#181825",  # Define tarjetas, menús y barras secundarias.
        "editor": "#11111b",  # Define el fondo profundo utilizado por código y tablas.
        "superficie": "#313244",  # Define botones, pestañas y controles convencionales.
        "superficie_suave": "#363649",  # Define una variación ligera utilizada durante algunas interacciones.
        "superficie_hover": "#45475a",  # Define el fondo utilizado al colocar el cursor.
        "superficie_presionada": "#585b70",  # Define el estado presionado.
        "fondo_deshabilitado": "#242536",  # Define componentes temporalmente no disponibles.
        "borde": "#313244",  # Define separadores y bordes discretos.
        "borde_fuerte": "#45475a",  # Define contornos que necesitan mayor contraste.
        "borde_deshabilitado": "#3b3d56",  # Define el contorno de componentes deshabilitados.
        "texto": "#cdd6f4",  # Define el texto principal.
        "texto_secundario": "#a6adc8",  # Define explicaciones y contenido menos prioritario.
        "texto_deshabilitado": "#6c7086",  # Define contenido temporalmente no disponible.
        "texto_inverso": "#1e1e2e",  # Define texto oscuro utilizado encima del acento claro.
        "acento": "#89b4fa",  # Mantiene el azul oficial utilizado actualmente.
        "acento_hover": "#b4befe",  # Utiliza una variante más clara durante hover.
        **SEMANTICOS_OSCUROS,  # Incorpora los colores funcionales adecuados para fondos oscuros.
    },
    TEMA_OSCURO_MEDIANOCHE: {
        "id": TEMA_OSCURO_MEDIANOCHE,  # Conserva un identificador estable.
        "modo": MODO_OSCURO,  # Agrupa la variante dentro del modo oscuro.
        "nombre": "Medianoche",  # Presenta el nombre visible.
        "descripcion": "Tema oscuro con fondos violeta profundo, superficies púrpura y acento lavanda.",  # Describe la diferencia completa, no solo el acento.
        "fondo": "#17141f",  # Utiliza un fondo principal violeta casi negro.
        "panel": "#201a2b",  # Utiliza paneles ligeramente más claros y cálidos.
        "editor": "#100d17",  # Mantiene el editor especialmente profundo.
        "superficie": "#31283f",  # Utiliza controles con un matiz púrpura visible.
        "superficie_suave": "#392e49",  # Proporciona un nivel intermedio para interacciones suaves.
        "superficie_hover": "#463856",  # Utiliza un violeta más claro durante hover.
        "superficie_presionada": "#5a486d",  # Marca claramente el estado presionado.
        "fondo_deshabilitado": "#25202d",  # Mantiene componentes deshabilitados dentro de la misma familia cromática.
        "borde": "#2b2435",  # Utiliza separadores violetas discretos.
        "borde_fuerte": "#4a3b5a",  # Utiliza bordes de contraste medio.
        "borde_deshabilitado": "#3a3045",  # Mantiene el contorno deshabilitado visible pero discreto.
        "texto": "#eadff7",  # Utiliza texto principal ligeramente cálido.
        "texto_secundario": "#bba9cc",  # Mantiene una jerarquía secundaria claramente distinguible.
        "texto_deshabilitado": "#756881",  # Define contenido no disponible.
        "texto_inverso": "#17141f",  # Utiliza el fondo profundo encima del acento lavanda.
        "acento": "#cba6f7",  # Utiliza lavanda como identidad principal.
        "acento_hover": "#ddb6f2",  # Aclara ligeramente el acento durante hover.
        **SEMANTICOS_OSCUROS,  # Conserva intacto el significado de diagnósticos y estados.
    },
    TEMA_OSCURO_OCEANO: {
        "id": TEMA_OSCURO_OCEANO,  # Conserva un identificador interno estable.
        "modo": MODO_OSCURO,  # Agrupa esta variante dentro del modo oscuro.
        "nombre": "Océano",  # Presenta el nombre visible.
        "descripcion": "Tema oscuro con fondos azul petróleo, superficies frías y acento cian.",  # Describe la identidad completa del tema.
        "fondo": "#111c24",  # Utiliza azul petróleo muy oscuro como fondo general.
        "panel": "#162630",  # Utiliza un azul profundo para paneles y tarjetas.
        "editor": "#0a141b",  # Mantiene el editor especialmente oscuro para mejorar el contraste.
        "superficie": "#223844",  # Utiliza azul grisáceo para controles.
        "superficie_suave": "#28434f",  # Proporciona una transición intermedia.
        "superficie_hover": "#2d4c5a",  # Aclara los controles al colocar el cursor.
        "superficie_presionada": "#3b5f6f",  # Marca el estado presionado mediante un azul más intenso.
        "fondo_deshabilitado": "#17252d",  # Mantiene elementos inactivos dentro de la misma gama.
        "borde": "#1e3440",  # Define separadores azulados discretos.
        "borde_fuerte": "#365968",  # Define contornos de mayor contraste.
        "borde_deshabilitado": "#29424d",  # Define bordes de elementos no disponibles.
        "texto": "#d7eef7",  # Utiliza texto claro con un ligero matiz frío.
        "texto_secundario": "#9fb9c5",  # Mantiene explicaciones menos prioritarias.
        "texto_deshabilitado": "#65808b",  # Define contenido temporalmente no disponible.
        "texto_inverso": "#0e1b22",  # Utiliza azul casi negro encima del acento cian.
        "acento": "#74c7ec",  # Utiliza cian como identidad principal.
        "acento_hover": "#89dceb",  # Aclara el acento durante hover.
        **SEMANTICOS_OSCUROS,  # Mantiene los colores funcionales apropiados para fondos oscuros.
    },
    TEMA_CLARO_TECNET: {
        "id": TEMA_CLARO_TECNET,  # Conserva un identificador estable independiente del nombre visible.
        "modo": MODO_CLARO,  # Agrupa esta variante dentro del modo claro.
        "nombre": "TecNet Claro",  # Presenta el nombre principal del modo claro.
        "descripcion": "Tema claro de TecNet Finder con fondos blancos suaves, controles azul grisáceos y acento azul.",  # Resume su apariencia completa.
        "fondo": "#f4f7fb",  # Utiliza un blanco azulado suave en lugar de blanco puro.
        "panel": "#ffffff",  # Utiliza blanco para tarjetas y superficies elevadas.
        "editor": "#eef2f7",  # Mantiene el editor ligeramente diferenciado del resto.
        "superficie": "#e2e8f0",  # Utiliza gris azulado para botones y controles.
        "superficie_suave": "#d8e0ea",  # Proporciona una transición suave entre controles.
        "superficie_hover": "#cbd5e1",  # Oscurece ligeramente las superficies durante hover.
        "superficie_presionada": "#b6c2d0",  # Marca claramente el estado presionado.
        "fondo_deshabilitado": "#edf0f4",  # Define controles inactivos sin introducir demasiado contraste.
        "borde": "#d7dee8",  # Utiliza separadores gris azulados discretos.
        "borde_fuerte": "#aeb8c5",  # Utiliza bordes más visibles donde resulta necesario.
        "borde_deshabilitado": "#d2d8e0",  # Define contornos de elementos deshabilitados.
        "texto": "#1f2937",  # Utiliza gris muy oscuro como texto principal.
        "texto_secundario": "#5f6b7a",  # Utiliza gris medio para explicaciones.
        "texto_deshabilitado": "#98a2b3",  # Define contenido no disponible.
        "texto_inverso": "#ffffff",  # Utiliza blanco sobre botones y pestañas azules.
        "acento": "#3b82f6",  # Utiliza un azul más intenso para conservar contraste sobre fondos claros.
        "acento_hover": "#2563eb",  # Oscurece el azul durante hover en lugar de aclararlo.
        **SEMANTICOS_CLAROS,  # Incorpora colores funcionales apropiados para superficies claras.
    },
    TEMA_CLARO_NIEBLA: {
        "id": TEMA_CLARO_NIEBLA,  # Conserva un identificador estable.
        "modo": MODO_CLARO,  # Agrupa esta variante dentro del modo claro.
        "nombre": "Niebla",  # Presenta un nombre breve y reconocible.
        "descripcion": "Tema claro grisáceo y menos brillante, pensado para reducir el predominio del blanco.",  # Explica su principal diferencia.
        "fondo": "#e9edf2",  # Utiliza gris frío como fondo general.
        "panel": "#f7f9fb",  # Utiliza un blanco grisáceo para superficies elevadas.
        "editor": "#e2e7ed",  # Mantiene el editor distinguible sin hacerlo blanco puro.
        "superficie": "#d5dce5",  # Utiliza gris azulado para los controles.
        "superficie_suave": "#cdd6e0",  # Proporciona una transición suave.
        "superficie_hover": "#c2ccd8",  # Oscurece los controles al colocar el cursor.
        "superficie_presionada": "#adb9c7",  # Marca claramente el estado presionado.
        "fondo_deshabilitado": "#e1e5ea",  # Mantiene componentes deshabilitados discretos.
        "borde": "#cbd3dc",  # Define separadores suaves.
        "borde_fuerte": "#9faab8",  # Define contornos visibles.
        "borde_deshabilitado": "#c7ced7",  # Define bordes de componentes inactivos.
        "texto": "#2e3440",  # Utiliza gris oscuro para el contenido principal.
        "texto_secundario": "#626d7a",  # Utiliza gris medio para contenido secundario.
        "texto_deshabilitado": "#929ca8",  # Define texto no disponible.
        "texto_inverso": "#ffffff",  # Mantiene blanco sobre el acento oscuro.
        "acento": "#5e81ac",  # Utiliza un azul grisáceo menos intenso.
        "acento_hover": "#4c6f99",  # Oscurece el acento durante hover.
        **SEMANTICOS_CLAROS,  # Mantiene el significado funcional con tonos adecuados para fondos claros.
    },
}  # El catálogo contiene ahora temas completos de ambos modos.


def tema_existe(tema_id: str) -> bool:
    return isinstance(tema_id, str) and tema_id in TEMAS  # Comprueba que el identificador pertenezca realmente al catálogo.


def modo_existe(modo_id: str) -> bool:
    return isinstance(modo_id, str) and any(modo["id"] == modo_id for modo in MODOS)  # Comprueba que el modo solicitado se encuentre registrado.


def normalizar_tema(tema_id: str) -> str:
    return tema_id if tema_existe(tema_id) else TEMA_PREDETERMINADO  # Recupera el tema seguro ante cualquier identificador desconocido.


def obtener_tema(tema_id: str) -> dict:
    return dict(TEMAS[normalizar_tema(tema_id)])  # Devuelve una copia para impedir modificaciones accidentales sobre el catálogo.


def obtener_temas_disponibles() -> tuple[dict, ...]:
    return tuple(dict(tema) for tema in TEMAS.values())  # Entrega copias siguiendo el mismo orden en que fueron declaradas.


def obtener_temas_por_modo(modo: str) -> tuple[dict, ...]:
    return tuple(dict(tema) for tema in TEMAS.values() if tema["modo"] == modo)  # Filtra exclusivamente las variantes pertenecientes al modo solicitado.


def obtener_modos_disponibles() -> tuple[dict, ...]:
    return tuple(dict(modo) for modo in MODOS)  # Entrega una copia segura de los modos que puede mostrar Configuración.


def modo_del_tema(tema_id: str) -> str:
    return obtener_tema(tema_id)["modo"]  # Permite reconstruir automáticamente el selector Modo desde una única preferencia persistente.


def nombre_tema(tema_id: str) -> str:
    return obtener_tema(tema_id)["nombre"]  # Recupera únicamente el nombre visible de una variante.