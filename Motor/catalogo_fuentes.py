# ============================================================
# Archivo: catalogo_fuentes.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Centraliza la consulta y validación de familias tipográficas
# disponibles para TecNet Finder.
#
# Solamente expone fuentes suavemente escalables que Qt puede
# utilizar correctamente con el sistema moderno de renderizado.
#
# De esta manera se evitan fuentes antiguas de Windows, como
# algunas fuentes raster, que pueden producir advertencias de
# DirectWrite al intentar utilizarlas dentro de PySide6.
# ============================================================

from functools import lru_cache  # Permite consultar el catálogo una sola vez durante cada ejecución.
from PySide6.QtGui import QFontDatabase  # Proporciona la información de las fuentes instaladas en el sistema.


def familia_fuente_compatible(familia: str) -> bool:  # Comprueba si una familia puede utilizarse de forma segura dentro de TecNet Finder.
    if not isinstance(familia, str) or not familia.strip():  # Rechaza valores vacíos o de un tipo incompatible.
        return False  # Informa inmediatamente que la familia no es utilizable.
    familia = familia.strip()  # Elimina espacios accidentales alrededor del nombre.
    estilos = QFontDatabase.styles(familia) or [""]  # Recupera los estilos disponibles y conserva una alternativa cuando la familia no declara ninguno.
    return any(QFontDatabase.isSmoothlyScalable(familia, estilo) for estilo in estilos)  # Acepta la familia cuando al menos uno de sus estilos es suavemente escalable.


@lru_cache(maxsize=1)  # Evita recorrer todas las fuentes del sistema cada vez que se abre un selector.
def obtener_fuentes_compatibles() -> tuple[str, ...]:  # Devuelve el catálogo seguro ordenado alfabéticamente.
    familias = sorted({familia.strip() for familia in QFontDatabase.families() if familia.strip()}, key=str.casefold)  # Recupera nombres únicos y los ordena sin distinguir mayúsculas.
    return tuple(familia for familia in familias if familia_fuente_compatible(familia))  # Conserva únicamente las fuentes que Qt puede escalar correctamente.


def normalizar_fuente(familia: str, alternativa: str = "Consolas") -> str:  # Obtiene una familia segura aunque la preferencia almacenada haya dejado de ser compatible.
    disponibles = obtener_fuentes_compatibles()  # Recupera el catálogo ya filtrado y normalmente almacenado en caché.
    familia = familia.strip() if isinstance(familia, str) else ""  # Normaliza el valor solicitado sin asumir que siempre sea una cadena.
    alternativa = alternativa.strip() if isinstance(alternativa, str) else "Consolas"  # Normaliza también la fuente alternativa.
    if familia in disponibles:  # Comprueba si la preferencia solicitada continúa siendo válida.
        return familia  # Conserva exactamente la familia elegida por el usuario.
    if alternativa in disponibles:  # Comprueba si la alternativa predeterminada está instalada y es compatible.
        return alternativa  # Recupera la fuente predeterminada sin producir advertencias.
    if disponibles:  # Comprueba si existe al menos una fuente compatible dentro del equipo.
        return disponibles[0]  # Utiliza la primera familia disponible como último respaldo.
    return alternativa or "Consolas"  # Mantiene un valor razonable incluso en un sistema excepcional sin catálogo disponible.