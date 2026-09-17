# ============================================================
# Archivo: recursos_tema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Resuelve recursos gráficos dependientes del tema visual.
#
# En modo oscuro utiliza los recursos originales.
# En modo claro busca automáticamente una variante terminada
# en "_Claro" y, si no existe, conserva el archivo original.
#
# Esto permite que iconos semánticos como Error, Advertencia o
# Correcto continúen utilizando su color propio sin necesidad
# de duplicarlos.
# ============================================================

from pathlib import Path  # Permite construir y comprobar rutas de recursos.
from Motor.catalogo_temas import MODO_CLARO, modo_del_tema  # Permite conocer si la variante activa pertenece al modo claro.


def tema_utiliza_iconos_claros(tema_id: str) -> bool:
    return modo_del_tema(tema_id) == MODO_CLARO  # Utiliza recursos oscuros sobre fondo claro exclusivamente en las variantes claras.


def nombre_icono_claro(nombre_archivo: str) -> str:
    ruta = Path(nombre_archivo)  # Separa de forma segura el nombre y su extensión.
    return f"{ruta.stem}_Claro{ruta.suffix}"  # Inserta "_Claro" antes de la extensión original.


def resolver_icono_tema(ruta_iconos: Path, nombre_archivo: str, tema_id: str) -> Path:
    ruta_original = ruta_iconos / nombre_archivo  # Construye primero la ruta utilizada históricamente por TecNet Finder.
    if not tema_utiliza_iconos_claros(tema_id): return ruta_original  # Conserva directamente el recurso original dentro de cualquier tema oscuro.
    ruta_clara = ruta_iconos / nombre_icono_claro(nombre_archivo)  # Construye automáticamente el nombre de la posible variante clara.
    return ruta_clara if ruta_clara.exists() else ruta_original  # Utiliza la variante clara solamente cuando realmente existe.