# ============================================================
# Archivo: prueba_recursos_tema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la resolución centralizada de recursos gráficos
# según el tema y la categoría física donde se almacenan.
# ============================================================

import Interfaz.apariencia.recursos_tema as recursos_tema  # Permite sustituir temporalmente las carpetas utilizadas por el resolvedor.
from Motor.catalogo_temas import TEMA_CLARO_NIEBLA, TEMA_CLARO_TECNET, TEMA_OSCURO_OCEANO, TEMA_OSCURO_TECNET  # Proporciona temas representativos de ambos modos.


def _preparar_carpetas(monkeypatch, tmp_path):
    oscuro = tmp_path / "Oscuro"  # Simula la carpeta destinada a los recursos oscuros.
    claro = tmp_path / "Claro"  # Simula la carpeta destinada a las variantes claras.
    comunes = tmp_path / "Comunes"  # Simula la carpeta utilizada por recursos independientes del tema.
    oscuro.mkdir(); claro.mkdir(); comunes.mkdir()  # Crea las tres categorías requeridas por el resolvedor.
    monkeypatch.setattr(recursos_tema, "RUTA_ICONOS_OSCURO", oscuro)  # Redirige temporalmente las búsquedas oscuras.
    monkeypatch.setattr(recursos_tema, "RUTA_ICONOS_CLARO", claro)  # Redirige temporalmente las búsquedas claras.
    monkeypatch.setattr(recursos_tema, "RUTA_ICONOS_COMUNES", comunes)  # Redirige temporalmente las búsquedas compartidas.
    return oscuro, claro, comunes  # Entrega las carpetas para preparar cada escenario específico.


def prueba_temas_claros_utilizan_iconos_claros():
    assert recursos_tema.tema_utiliza_iconos_claros(TEMA_CLARO_TECNET) is True  # Comprueba la variante clara principal.
    assert recursos_tema.tema_utiliza_iconos_claros(TEMA_CLARO_NIEBLA) is True  # Comprueba una segunda variante clara.


def prueba_temas_oscuros_no_utilizan_iconos_claros():
    assert recursos_tema.tema_utiliza_iconos_claros(TEMA_OSCURO_TECNET) is False  # Comprueba la variante oscura principal.
    assert recursos_tema.tema_utiliza_iconos_claros(TEMA_OSCURO_OCEANO) is False  # Comprueba una segunda variante oscura.


def prueba_resolvedor_prefiere_variante_clara(monkeypatch, tmp_path):
    oscuro, claro, _comunes = _preparar_carpetas(monkeypatch, tmp_path)  # Prepara una estructura temporal equivalente con la real.
    (oscuro / "Pegar.png").write_bytes(b"oscuro")  # Crea la versión oscura del mismo recurso.
    esperado = claro / "Pegar.png"; esperado.write_bytes(b"claro")  # Crea y conserva la variante clara esperada.
    assert recursos_tema.resolver_icono_tema("Pegar.png", TEMA_CLARO_TECNET) == esperado  # Comprueba que el modo claro tenga prioridad sobre su propia carpeta.


def prueba_resolvedor_prefiere_variante_oscura(monkeypatch, tmp_path):
    oscuro, claro, _comunes = _preparar_carpetas(monkeypatch, tmp_path)  # Prepara las tres categorías temporales.
    esperado = oscuro / "Pegar.png"; esperado.write_bytes(b"oscuro")  # Crea y conserva la variante oscura esperada.
    (claro / "Pegar.png").write_bytes(b"claro")  # Crea también una alternativa clara que no debe tener prioridad.
    assert recursos_tema.resolver_icono_tema("Pegar.png", TEMA_OSCURO_TECNET) == esperado  # Comprueba que un tema oscuro utilice primero Oscuro.


def prueba_resolvedor_prioriza_recurso_comun(monkeypatch, tmp_path):
    oscuro, claro, comunes = _preparar_carpetas(monkeypatch, tmp_path)  # Prepara las categorías utilizadas para comprobar prioridad.
    (oscuro / "Error.png").write_bytes(b"oscuro")  # Simula incluso una posible copia temática que no debe imponerse.
    (claro / "Error.png").write_bytes(b"claro")  # Simula una segunda copia temática que tampoco debe utilizarse.
    esperado = comunes / "Error.png"; esperado.write_bytes(b"comun")  # Crea el recurso compartido que debe tener prioridad absoluta.
    assert recursos_tema.resolver_icono_tema("Error.png", TEMA_CLARO_TECNET) == esperado  # Comprueba que Comunes sea independiente del modo activo.


def prueba_resolvedor_claro_reutiliza_hover_oscuro(monkeypatch, tmp_path):
    oscuro, _claro, _comunes = _preparar_carpetas(monkeypatch, tmp_path)  # Prepara una estructura donde el recurso solo existe dentro de Oscuro.
    esperado = oscuro / "Engrane_Hover.png"; esperado.write_bytes(b"hover")  # Simula el hover oscuro que también debe utilizarse sobre la barra clara.
    assert recursos_tema.resolver_icono_tema("Engrane_Hover.png", TEMA_CLARO_TECNET) == esperado  # Comprueba específicamente el comportamiento requerido para los estados hover.
