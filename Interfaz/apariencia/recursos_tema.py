# ============================================================
# Archivo: recursos_tema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Centraliza las rutas de los recursos gráficos utilizados por
# TecNet Finder y resuelve automáticamente qué icono corresponde
# con el tema visual activo.
#
# Los iconos se organizan en:
# - Oscuro: recursos principales del modo oscuro y estados hover.
# - Claro: recursos principales adaptados para fondos claros.
# - Comunes: recursos independientes del tema.
#
# Los iconos de interacción que solamente existen dentro de
# Oscuro también pueden utilizarse desde un tema claro como
# alternativa, por ejemplo durante el hover de la barra.
# ============================================================

from pathlib import Path  # Permite construir rutas relativas al proyecto sin depender de ubicaciones absolutas.
from Motor.configuracion.catalogo_temas import MODO_CLARO, modo_del_tema  # Permite determinar si el tema activo pertenece al modo claro.

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent  # Localiza la raíz general de TecNet Finder desde el módulo de interfaz.
RUTA_RECURSOS = RAIZ_PROYECTO / "Recursos"  # Centraliza la carpeta principal donde viven todos los recursos gráficos.
RUTA_MARCA = RUTA_RECURSOS / "Marca"  # Centraliza logotipos e identidad visual general de TecNet Finder.
RUTA_ICONOS = RUTA_RECURSOS / "Iconos"  # Centraliza la carpeta exterior que agrupa todas las categorías de iconos.
RUTA_ICONOS_OSCURO = RUTA_ICONOS / "Oscuro"  # Contiene iconos normales oscuros y estados especiales de interacción.
RUTA_ICONOS_CLARO = RUTA_ICONOS / "Claro"  # Contiene las variantes preparadas específicamente para fondos claros.
RUTA_ICONOS_COMUNES = RUTA_ICONOS / "Comunes"  # Contiene iconos que conservan exactamente la misma apariencia en ambos modos.


def tema_utiliza_iconos_claros(tema_id: str) -> bool:
    return modo_del_tema(tema_id) == MODO_CLARO  # Indica si la primera búsqueda temática debe realizarse dentro de Claro.


def ruta_marca(nombre_archivo: str) -> Path:
    return RUTA_MARCA / nombre_archivo  # Construye la ubicación de un recurso perteneciente con la identidad visual general.


def ruta_icono_oscuro(nombre_archivo: str) -> Path:
    return RUTA_ICONOS_OSCURO / nombre_archivo  # Construye directamente la ubicación de un icono almacenado dentro de Oscuro.


def ruta_icono_claro(nombre_archivo: str) -> Path:
    return RUTA_ICONOS_CLARO / nombre_archivo  # Construye directamente la ubicación de un icono almacenado dentro de Claro.


def ruta_icono_comun(nombre_archivo: str) -> Path:
    return RUTA_ICONOS_COMUNES / nombre_archivo  # Construye directamente la ubicación de un recurso compartido entre ambos modos.


def resolver_icono_tema(nombre_archivo: str, tema_id: str) -> Path:
    ruta_comun = ruta_icono_comun(nombre_archivo)  # Comprueba primero si el recurso fue declarado explícitamente como independiente del tema.
    if ruta_comun.exists(): return ruta_comun  # Utiliza siempre el recurso común cuando realmente se encuentra disponible.

    ruta_preferida = ruta_icono_claro(nombre_archivo) if tema_utiliza_iconos_claros(tema_id) else ruta_icono_oscuro(nombre_archivo)  # Selecciona primero la carpeta correspondiente con el modo activo.
    if ruta_preferida.exists(): return ruta_preferida  # Devuelve inmediatamente la variante temática cuando existe.

    ruta_alternativa = ruta_icono_oscuro(nombre_archivo) if tema_utiliza_iconos_claros(tema_id) else ruta_icono_claro(nombre_archivo)  # Permite reutilizar recursos exclusivos del otro modo cuando no existe una versión propia.
    if ruta_alternativa.exists(): return ruta_alternativa  # Recupera, entre otros casos, los iconos hover oscuros utilizados también dentro del modo claro.

    return ruta_preferida  # Devuelve la ruta temática esperada aun cuando falte para permitir que el llamador compruebe su existencia.