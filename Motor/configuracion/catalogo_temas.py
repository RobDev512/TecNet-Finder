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
# - Identificador interno estable.
# - Modo oscuro o claro.
# - Nombre y descripción.
# - Paleta general.
# - Colores específicos del editor.
# - Colores semánticos.
#
# El modo se obtiene siempre desde el propio tema para impedir
# combinaciones inconsistentes entre modo y variante.
# ============================================================

MODO_OSCURO = "oscuro"  # Identifica todos los temas diseñados para fondos oscuros.
MODO_CLARO = "claro"  # Identifica todos los temas diseñados para fondos claros.

TEMA_OSCURO_TECNET = "oscuro_tecnet"  # Conserva la apariencia histórica azul de TecNet Finder.
TEMA_OSCURO_MEDIANOCHE = "oscuro_medianoche"  # Utiliza fondos violetas profundos y acento lavanda.
TEMA_OSCURO_OCEANO = "oscuro_oceano"  # Utiliza fondos azul petróleo y acento cian.
TEMA_OSCURO_BOSQUE = "oscuro_bosque"  # Utiliza fondos verdes profundos y acento menta.
TEMA_OSCURO_BORGONA = "oscuro_borgona"  # Utiliza fondos vino oscuros y acento rosa.
TEMA_CLARO_TECNET = "claro_tecnet"  # Representa la variante clara principal.
TEMA_CLARO_NIEBLA = "claro_niebla"  # Representa una variante gris clara menos luminosa.
TEMA_CLARO_MARFIL = "claro_marfil"  # Utiliza superficies cálidas crema con acento índigo.
TEMA_CLARO_LAVANDA = "claro_lavanda"  # Utiliza superficies violeta muy claras con acento púrpura.
TEMA_CLARO_CEREZO = "claro_cerezo"  # Utiliza fondos rosados suaves y acento magenta.
TEMA_PREDETERMINADO = TEMA_OSCURO_TECNET  # Mantiene la apariencia conocida como respaldo seguro.

MODOS = (
    {"id": MODO_OSCURO, "nombre": "Oscuro"},  # Presenta primero las variantes oscuras.
    {"id": MODO_CLARO, "nombre": "Claro"},  # Presenta después las variantes luminosas.
)  # El orden también determina la presentación dentro de Configuración.

SEMANTICOS_OSCUROS = {
    "exito": "#a6e3a1",  # Mantiene verde claro para estados satisfactorios.
    "advertencia": "#f9e2af",  # Mantiene amarillo claro para advertencias.
    "error": "#f38ba8",  # Mantiene rosa rojizo para errores.
    "sintactico": "#fab387",  # Mantiene naranja para diagnósticos sintácticos.
    "semantico": "#cba6f7",  # Mantiene violeta para diagnósticos semánticos.
    "subred": "#94e2d5",  # Mantiene turquesa para información de subredes.
}  # Estos tonos ofrecen buen contraste sobre todas las variantes oscuras.

SEMANTICOS_CLAROS = {
    "exito": "#287a3d",  # Utiliza verde oscuro legible sobre fondos claros.
    "advertencia": "#946200",  # Utiliza ámbar oscuro para advertencias.
    "error": "#c42b1c",  # Utiliza rojo intenso para errores.
    "sintactico": "#b45309",  # Utiliza naranja oscuro para sintaxis.
    "semantico": "#7c3aed",  # Utiliza violeta intenso para semántica.
    "subred": "#0f766e",  # Utiliza turquesa oscuro para subredes.
}  # Conserva el significado funcional de cada color sobre superficies claras.

TEMAS = {
    TEMA_OSCURO_TECNET: {
        "id": TEMA_OSCURO_TECNET,  # Conserva el identificador utilizado por las preferencias.
        "modo": MODO_OSCURO,  # Agrupa esta variante dentro del modo oscuro.
        "nombre": "TecNet",  # Presenta el nombre corto original.
        "descripcion": "Tema oscuro original de TecNet Finder con fondos gris azulados y acento azul.",  # Resume su apariencia.
        "fondo": "#1e1e2e",  # Define el fondo general.
        "panel": "#181825",  # Define paneles y superficies elevadas.
        "editor": "#11111b",  # Define el fondo profundo del editor.
        "superficie": "#313244",  # Define controles convencionales.
        "superficie_suave": "#363649",  # Define una transición visual intermedia.
        "superficie_hover": "#45475a",  # Define el estado hover.
        "superficie_presionada": "#585b70",  # Define el estado presionado.
        "fondo_deshabilitado": "#242536",  # Define controles temporalmente deshabilitados.
        "borde": "#313244",  # Define separadores discretos.
        "borde_fuerte": "#45475a",  # Define contornos con mayor contraste.
        "borde_deshabilitado": "#3b3d56",  # Define contornos deshabilitados.
        "texto": "#cdd6f4",  # Define texto principal.
        "texto_secundario": "#a6adc8",  # Define texto explicativo.
        "texto_deshabilitado": "#6c7086",  # Define texto no disponible.
        "texto_inverso": "#1e1e2e",  # Define texto sobre superficies de acento.
        "acento": "#89b4fa",  # Conserva el azul oficial actual.
        "acento_hover": "#b4befe",  # Conserva el hover azul claro.
        "editor_gutter": "#181825",  # Mantiene el margen de líneas utilizado históricamente.
        "editor_linea_activa": "#181825",  # Mantiene el resaltado actual de la línea activa.
        **SEMANTICOS_OSCUROS,  # Añade los colores funcionales apropiados.
    },

    TEMA_OSCURO_MEDIANOCHE: {
        "id": TEMA_OSCURO_MEDIANOCHE,  # Conserva un identificador persistente propio.
        "modo": MODO_OSCURO,  # Agrupa esta variante dentro del modo oscuro.
        "nombre": "Medianoche",  # Presenta el nombre visible.
        "descripcion": "Tema oscuro con fondos violeta profundo, superficies púrpura y acento lavanda.",  # Resume su identidad visual.
        "fondo": "#17141f",  # Utiliza violeta casi negro.
        "panel": "#201a2b",  # Diferencia paneles mediante un violeta ligeramente más claro.
        "editor": "#100d17",  # Mantiene el editor especialmente profundo.
        "superficie": "#31283f",  # Utiliza controles púrpura.
        "superficie_suave": "#392e49",  # Define una transición intermedia.
        "superficie_hover": "#463856",  # Define hover violeta.
        "superficie_presionada": "#5a486d",  # Define estado presionado.
        "fondo_deshabilitado": "#25202d",  # Mantiene componentes inactivos dentro de la misma gama.
        "borde": "#2b2435",  # Define separadores sutiles.
        "borde_fuerte": "#4a3b5a",  # Define contornos visibles.
        "borde_deshabilitado": "#3a3045",  # Define contornos de controles no disponibles.
        "texto": "#eadff7",  # Utiliza texto claro cálido.
        "texto_secundario": "#bba9cc",  # Define contenido secundario.
        "texto_deshabilitado": "#756881",  # Define contenido no disponible.
        "texto_inverso": "#17141f",  # Define texto sobre lavanda.
        "acento": "#cba6f7",  # Utiliza lavanda como identidad.
        "acento_hover": "#ddb6f2",  # Aclara el acento al colocar el cursor.
        "editor_gutter": "#201a2b",  # Integra el margen del editor con la paleta violeta.
        "editor_linea_activa": "#201a2b",  # Mantiene una línea activa discreta.
        **SEMANTICOS_OSCUROS,  # Conserva colores funcionales de alto contraste.
    },

    TEMA_OSCURO_OCEANO: {
        "id": TEMA_OSCURO_OCEANO,  # Conserva un identificador interno estable.
        "modo": MODO_OSCURO,  # Agrupa esta variante dentro del modo oscuro.
        "nombre": "Océano",  # Presenta el nombre visible.
        "descripcion": "Tema oscuro con fondos azul petróleo, superficies frías y acento cian.",  # Resume su apariencia.
        "fondo": "#111c24",  # Utiliza azul petróleo muy oscuro.
        "panel": "#162630",  # Diferencia paneles mediante un azul profundo.
        "editor": "#0a141b",  # Mantiene el editor especialmente oscuro.
        "superficie": "#223844",  # Define controles azul grisáceos.
        "superficie_suave": "#28434f",  # Define una transición fría.
        "superficie_hover": "#2d4c5a",  # Define hover azul.
        "superficie_presionada": "#3b5f6f",  # Define estado presionado.
        "fondo_deshabilitado": "#17252d",  # Mantiene controles inactivos dentro de la gama.
        "borde": "#1e3440",  # Define separadores discretos.
        "borde_fuerte": "#365968",  # Define contornos de mayor contraste.
        "borde_deshabilitado": "#29424d",  # Define contornos deshabilitados.
        "texto": "#d7eef7",  # Define texto principal frío.
        "texto_secundario": "#9fb9c5",  # Define contenido secundario.
        "texto_deshabilitado": "#65808b",  # Define contenido no disponible.
        "texto_inverso": "#0e1b22",  # Define texto sobre el acento cian.
        "acento": "#74c7ec",  # Utiliza cian como identidad.
        "acento_hover": "#89dceb",  # Aclara el acento durante hover.
        "editor_gutter": "#162630",  # Integra el margen de líneas con el fondo petróleo.
        "editor_linea_activa": "#162630",  # Mantiene una línea activa fría y discreta.
        **SEMANTICOS_OSCUROS,  # Conserva los colores funcionales apropiados.
    },

    TEMA_OSCURO_BOSQUE: {
        "id": TEMA_OSCURO_BOSQUE,  # Conserva un identificador persistente independiente.
        "modo": MODO_OSCURO,  # Agrupa Bosque dentro de las variantes oscuras.
        "nombre": "Bosque",  # Presenta un nombre breve relacionado con su gama verde.
        "descripcion": "Tema oscuro con fondos verde profundo, superficies naturales y acento menta.",  # Resume claramente su identidad.
        "fondo": "#10201a",  # Utiliza verde muy oscuro como fondo general.
        "panel": "#152820",  # Diferencia paneles mediante una capa verde ligeramente más luminosa.
        "editor": "#0a1511",  # Mantiene el editor especialmente profundo.
        "superficie": "#223a30",  # Define controles mediante un verde grisáceo.
        "superficie_suave": "#29463a",  # Introduce una transición natural entre superficies.
        "superficie_hover": "#315444",  # Hace visible el hover sin romper la gama.
        "superficie_presionada": "#3e6754",  # Marca claramente el estado presionado.
        "fondo_deshabilitado": "#182820",  # Mantiene componentes inactivos dentro de la paleta.
        "borde": "#1f362c",  # Define separadores discretos.
        "borde_fuerte": "#3d6553",  # Define contornos claramente perceptibles.
        "borde_deshabilitado": "#2d483c",  # Define contornos para controles no disponibles.
        "texto": "#d9f0e4",  # Utiliza un blanco verdoso para el contenido principal.
        "texto_secundario": "#a6c5b5",  # Define explicaciones mediante un verde gris claro.
        "texto_deshabilitado": "#6f8f7f",  # Mantiene visible el contenido deshabilitado.
        "texto_inverso": "#0d1c16",  # Utiliza verde casi negro sobre el acento menta.
        "acento": "#6ee7b7",  # Utiliza menta como identidad principal.
        "acento_hover": "#a7f3d0",  # Aclara el acento durante hover.
        "editor_gutter": "#152820",  # Integra el margen del editor con los paneles.
        "editor_linea_activa": "#152820",  # Marca la línea actual de forma discreta.
        **SEMANTICOS_OSCUROS,  # Mantiene la semántica funcional utilizada por todos los temas oscuros.
    },

    TEMA_OSCURO_BORGONA: {
        "id": TEMA_OSCURO_BORGONA,  # Conserva un identificador independiente para la quinta variante oscura.
        "modo": MODO_OSCURO,  # Agrupa Borgoña dentro del modo oscuro.
        "nombre": "Borgoña",  # Presenta un nombre relacionado con su gama vino.
        "descripcion": "Tema oscuro cálido con fondos borgoña profundos, superficies vino y acento rosa.",  # Resume su personalidad visual.
        "fondo": "#211419",  # Utiliza rojo vino casi negro para el fondo general.
        "panel": "#2a191f",  # Añade una superficie borgoña ligeramente más clara.
        "editor": "#160c10",  # Mantiene el editor muy oscuro y discreto.
        "superficie": "#3b252c",  # Define controles mediante vino grisáceo.
        "superficie_suave": "#452c34",  # Introduce una transición cálida intermedia.
        "superficie_hover": "#563741",  # Hace evidente el estado hover.
        "superficie_presionada": "#704854",  # Marca claramente una pulsación.
        "fondo_deshabilitado": "#2b1d22",  # Mantiene controles inactivos dentro de la misma gama.
        "borde": "#3b272e",  # Define separadores discretos.
        "borde_fuerte": "#65424d",  # Proporciona contornos visibles.
        "borde_deshabilitado": "#4b333a",  # Define contornos de elementos deshabilitados.
        "texto": "#f5e5e9",  # Utiliza blanco rosado como texto principal.
        "texto_secundario": "#cfabb4",  # Define explicaciones mediante rosa grisáceo.
        "texto_deshabilitado": "#8f7078",  # Mantiene legible el contenido no disponible.
        "texto_inverso": "#241319",  # Define texto oscuro sobre el acento rosa.
        "acento": "#f472b6",  # Utiliza rosa intenso como identidad principal.
        "acento_hover": "#f9a8d4",  # Aclara el rosa durante hover.
        "editor_gutter": "#2a191f",  # Integra los números de línea con la paleta borgoña.
        "editor_linea_activa": "#2a191f",  # Mantiene una línea activa cálida y discreta.
        **SEMANTICOS_OSCUROS,  # Conserva colores funcionales independientes del acento principal.
    },

    TEMA_CLARO_TECNET: {
        "id": TEMA_CLARO_TECNET,  # Conserva el identificador persistente de la variante clara principal.
        "modo": MODO_CLARO,  # Agrupa la variante dentro del modo claro.
        "nombre": "TecNet Claro",  # Presenta el nombre visible.
        "descripcion": "Tema claro con jerarquía azul grisácea, paneles definidos y acento azul TecNet.",  # Resume su apariencia.
        "fondo": "#e4eaf1",  # Utiliza gris azulado perceptible para separar la superficie general.
        "panel": "#f7f9fc",  # Utiliza un panel casi blanco claramente distinto del fondo exterior.
        "editor": "#ffffff",  # Utiliza blanco limpio para maximizar la legibilidad del código.
        "superficie": "#d5dee8",  # Hace visibles botones y pestañas sin parecer deshabilitados.
        "superficie_suave": "#cbd6e2",  # Define controles ligeramente más marcados.
        "superficie_hover": "#bcc9d7",  # Hace evidente el estado hover.
        "superficie_presionada": "#a7b6c8",  # Marca con claridad una pulsación.
        "fondo_deshabilitado": "#e8edf3",  # Mantiene controles inactivos visualmente distintos.
        "borde": "#c0cbd8",  # Define separadores claramente visibles.
        "borde_fuerte": "#8ea0b5",  # Define contornos de botones, tablas y campos.
        "borde_deshabilitado": "#cdd5de",  # Mantiene un borde tenue para controles inactivos.
        "texto": "#172033",  # Utiliza un azul negro para mejorar legibilidad.
        "texto_secundario": "#45546a",  # Utiliza gris azul oscuro para explicaciones.
        "texto_deshabilitado": "#8795a8",  # Mantiene contenido deshabilitado sin hacerlo invisible.
        "texto_inverso": "#ffffff",  # Utiliza blanco sobre el azul de acento.
        "acento": "#2563eb",  # Utiliza azul intenso para conservar contraste.
        "acento_hover": "#1d4ed8",  # Oscurece el acento durante hover.
        "editor_gutter": "#cfd9e5",  # Reserva una franja azul grisácea para números de línea.
        "editor_linea_activa": "#edf3fa",  # Utiliza un azul extremadamente suave para la línea actual.
        **SEMANTICOS_CLAROS,  # Utiliza versiones oscuras de los colores funcionales.
    },

    TEMA_CLARO_NIEBLA: {
        "id": TEMA_CLARO_NIEBLA,  # Conserva un identificador estable propio.
        "modo": MODO_CLARO,  # Agrupa la variante dentro del modo claro.
        "nombre": "Niebla",  # Presenta un nombre breve.
        "descripcion": "Tema claro grisáceo, menos brillante y con contraste suave entre superficies.",  # Explica su diferencia respecto a TecNet Claro.
        "fondo": "#d7dde4",  # Utiliza gris frío claramente visible como fondo general.
        "panel": "#eef2f6",  # Utiliza gris muy claro para tarjetas y paneles.
        "editor": "#f8fafc",  # Evita blanco puro sin perder legibilidad.
        "superficie": "#c6ced7",  # Define botones y pestañas mediante un gris claro reconocible.
        "superficie_suave": "#bbc5d0",  # Añade otra capa visual entre controles.
        "superficie_hover": "#abb7c3",  # Define claramente el hover.
        "superficie_presionada": "#95a4b3",  # Marca el estado presionado.
        "fondo_deshabilitado": "#dee3e8",  # Diferencia controles no disponibles.
        "borde": "#b4bec8",  # Define separadores grises.
        "borde_fuerte": "#7f8d9d",  # Define contornos claramente visibles.
        "borde_deshabilitado": "#c3cbd3",  # Define contornos inactivos.
        "texto": "#252c36",  # Utiliza gris carbón para el contenido principal.
        "texto_secundario": "#505b68",  # Utiliza gris medio oscuro para explicaciones.
        "texto_deshabilitado": "#818c98",  # Define contenido no disponible.
        "texto_inverso": "#ffffff",  # Mantiene blanco sobre el acento.
        "acento": "#55789f",  # Utiliza azul grisáceo como identidad.
        "acento_hover": "#42678f",  # Oscurece el acento durante hover.
        "editor_gutter": "#c3ccd6",  # Define una franja gris específica para números de línea.
        "editor_linea_activa": "#e8ecf0",  # Define una línea activa extremadamente suave.
        **SEMANTICOS_CLAROS,  # Utiliza colores semánticos legibles sobre gris claro.
    },

    TEMA_CLARO_MARFIL: {
        "id": TEMA_CLARO_MARFIL,  # Conserva un identificador persistente independiente.
        "modo": MODO_CLARO,  # Agrupa Marfil dentro de las variantes claras.
        "nombre": "Marfil",  # Presenta un nombre relacionado con su fondo cálido.
        "descripcion": "Tema claro cálido con fondos marfil, superficies crema y acento índigo.",  # Resume su identidad.
        "fondo": "#eee9df",  # Utiliza un beige muy claro como fondo exterior.
        "panel": "#fffaf2",  # Utiliza crema casi blanco para las superficies elevadas.
        "editor": "#fffdf8",  # Evita blanco puro mediante un matiz cálido casi imperceptible.
        "superficie": "#ded5c6",  # Define controles mediante beige medio claro.
        "superficie_suave": "#d4c9b9",  # Introduce una segunda capa cálida.
        "superficie_hover": "#c5b8a5",  # Hace evidente el hover sin oscurecer demasiado.
        "superficie_presionada": "#b2a38e",  # Marca claramente la pulsación.
        "fondo_deshabilitado": "#eee9e0",  # Mantiene componentes deshabilitados dentro de la misma temperatura.
        "borde": "#c7bca9",  # Define separadores cálidos.
        "borde_fuerte": "#978a76",  # Proporciona contornos suficientemente visibles.
        "borde_deshabilitado": "#d6ccbd",  # Define contornos suaves para controles inactivos.
        "texto": "#2b261f",  # Utiliza marrón carbón para el texto principal.
        "texto_secundario": "#5d5448",  # Utiliza marrón grisáceo para explicaciones.
        "texto_deshabilitado": "#958b7d",  # Mantiene visible el contenido deshabilitado.
        "texto_inverso": "#ffffff",  # Conserva blanco sobre el acento índigo.
        "acento": "#4f46e5",  # Utiliza índigo para diferenciarse del azul TecNet.
        "acento_hover": "#4338ca",  # Oscurece ligeramente el índigo durante hover.
        "editor_gutter": "#e3dacd",  # Utiliza beige suave para los números de línea.
        "editor_linea_activa": "#f5efe5",  # Marca la línea actual mediante un crema discreto.
        **SEMANTICOS_CLAROS,  # Conserva colores funcionales suficientemente oscuros.
    },

    TEMA_CLARO_LAVANDA: {
        "id": TEMA_CLARO_LAVANDA,  # Conserva un identificador estable independiente.
        "modo": MODO_CLARO,  # Agrupa Lavanda dentro de las variantes claras.
        "nombre": "Lavanda",  # Presenta un nombre breve relacionado con la paleta.
        "descripcion": "Tema claro violeta suave con paneles luminosos y acento púrpura.",  # Resume la apariencia.
        "fondo": "#ebe7f3",  # Utiliza gris violeta muy claro para el fondo general.
        "panel": "#faf8ff",  # Define paneles casi blancos con un matiz lavanda.
        "editor": "#fffefe",  # Mantiene el editor prácticamente blanco para facilitar lectura.
        "superficie": "#ddd5ea",  # Define controles mediante lavanda clara.
        "superficie_suave": "#d3c8e3",  # Introduce una segunda profundidad violeta.
        "superficie_hover": "#c3b4d7",  # Hace visible el estado hover.
        "superficie_presionada": "#ad9ac5",  # Marca claramente las pulsaciones.
        "fondo_deshabilitado": "#eeeaf4",  # Mantiene los controles inactivos dentro de la misma gama.
        "borde": "#c7bdd5",  # Define separadores violeta grisáceos.
        "borde_fuerte": "#9585ab",  # Define contornos visibles sin resultar demasiado oscuros.
        "borde_deshabilitado": "#d7d0e0",  # Mantiene contornos suaves en controles inactivos.
        "texto": "#282035",  # Utiliza violeta casi negro como texto principal.
        "texto_secundario": "#5d506f",  # Define texto secundario con violeta grisáceo.
        "texto_deshabilitado": "#8c8198",  # Conserva suficiente contraste para información deshabilitada.
        "texto_inverso": "#ffffff",  # Utiliza blanco sobre el acento púrpura.
        "acento": "#7c3aed",  # Utiliza púrpura intenso como identidad.
        "acento_hover": "#6d28d9",  # Oscurece el acento durante hover.
        "editor_gutter": "#ddd6e8",  # Integra el margen de líneas con la paleta lavanda.
        "editor_linea_activa": "#f1edf8",  # Define una línea activa muy suave.
        **SEMANTICOS_CLAROS,  # Conserva los colores funcionales preparados para fondos claros.
    },

    TEMA_CLARO_CEREZO: {
        "id": TEMA_CLARO_CEREZO,  # Conserva un identificador independiente para la quinta variante clara.
        "modo": MODO_CLARO,  # Agrupa Cerezo dentro del modo claro.
        "nombre": "Cerezo",  # Presenta un nombre relacionado con su gama rosada.
        "descripcion": "Tema claro rosado con superficies suaves, fondos luminosos y acento magenta.",  # Resume su identidad visual.
        "fondo": "#f0e4e8",  # Utiliza rosa grisáceo muy claro como fondo general.
        "panel": "#fff8fa",  # Define paneles casi blancos con un matiz rosado.
        "editor": "#fffdfd",  # Mantiene el editor prácticamente blanco.
        "superficie": "#e3d0d7",  # Define controles mediante rosa gris suave.
        "superficie_suave": "#dac3cc",  # Añade una segunda profundidad rosada.
        "superficie_hover": "#cbb0bb",  # Hace visible el hover sin resultar demasiado oscuro.
        "superficie_presionada": "#b796a3",  # Marca claramente las pulsaciones.
        "fondo_deshabilitado": "#f0e8eb",  # Mantiene controles inactivos dentro de la misma gama.
        "borde": "#cfb9c1",  # Define separadores suaves.
        "borde_fuerte": "#a17d8b",  # Define contornos con contraste suficiente.
        "borde_deshabilitado": "#ddcdd3",  # Mantiene bordes discretos en controles inactivos.
        "texto": "#332229",  # Utiliza vino casi negro para el contenido principal.
        "texto_secundario": "#68505a",  # Define explicaciones mediante un rosa gris oscuro.
        "texto_deshabilitado": "#97848b",  # Mantiene visible el contenido deshabilitado.
        "texto_inverso": "#ffffff",  # Utiliza blanco sobre el acento magenta.
        "acento": "#be185d",  # Utiliza magenta oscuro como identidad principal.
        "acento_hover": "#9d174d",  # Oscurece el acento durante hover.
        "editor_gutter": "#e2d2d8",  # Integra el margen de líneas con la gama rosada.
        "editor_linea_activa": "#f8eef2",  # Marca la línea actual mediante rosa extremadamente suave.
        **SEMANTICOS_CLAROS,  # Mantiene la semántica funcional preparada para fondos claros.
    },
}  # Centraliza diez variantes: cinco oscuras y cinco claras.


def tema_existe(tema_id: str) -> bool:
    return isinstance(tema_id, str) and tema_id in TEMAS  # Acepta exclusivamente identificadores registrados.


def modo_existe(modo_id: str) -> bool:
    return isinstance(modo_id, str) and any(modo["id"] == modo_id for modo in MODOS)  # Comprueba que el modo pertenezca al catálogo.


def normalizar_tema(tema_id: str) -> str:
    return tema_id if tema_existe(tema_id) else TEMA_PREDETERMINADO  # Recupera TecNet oscuro ante una preferencia inválida.


def obtener_tema(tema_id: str) -> dict:
    return dict(TEMAS[normalizar_tema(tema_id)])  # Devuelve una copia para proteger el catálogo global.


def obtener_temas_disponibles() -> tuple[dict, ...]:
    return tuple(dict(tema) for tema in TEMAS.values())  # Entrega copias siguiendo el orden declarado.


def obtener_temas_por_modo(modo: str) -> tuple[dict, ...]:
    return tuple(dict(tema) for tema in TEMAS.values() if tema["modo"] == modo)  # Filtra únicamente las variantes del modo solicitado.


def obtener_modos_disponibles() -> tuple[dict, ...]:
    return tuple(dict(modo) for modo in MODOS)  # Entrega una copia segura de los modos disponibles.


def modo_del_tema(tema_id: str) -> str:
    return obtener_tema(tema_id)["modo"]  # Deriva el modo directamente desde una variante válida.


def tema_es_claro(tema_id: str) -> bool:
    return modo_del_tema(tema_id) == MODO_CLARO  # Permite consultar rápidamente si debe utilizarse una apariencia luminosa.


def nombre_tema(tema_id: str) -> str:
    return obtener_tema(tema_id)["nombre"]  # Recupera solamente el nombre visible de una variante.