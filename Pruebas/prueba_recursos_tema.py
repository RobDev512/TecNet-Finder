# ============================================================
# Archivo: prueba_recursos_tema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la selección automática de iconos según el tema.
#
# Utiliza tmp_path para no depender de los recursos reales del
# proyecto ni modificar ningún archivo del usuario.
# ============================================================

from Interfaz.recursos_tema import nombre_icono_claro, resolver_icono_tema, tema_utiliza_iconos_claros  # Importa las operaciones públicas del resolvedor.
from Motor.catalogo_temas import TEMA_CLARO_NIEBLA, TEMA_CLARO_TECNET, TEMA_OSCURO_OCEANO, TEMA_OSCURO_TECNET  # Proporciona temas representativos de ambos modos.


def test_nombre_icono_claro_conserva_extension():
    assert nombre_icono_claro("Engrane.png") == "Engrane_Claro.png"  # Comprueba la convención utilizada por los recursos entregados.


def test_temas_claros_utilizan_iconos_claros():
    assert tema_utiliza_iconos_claros(TEMA_CLARO_TECNET) is True  # Comprueba la variante principal clara.
    assert tema_utiliza_iconos_claros(TEMA_CLARO_NIEBLA) is True  # Comprueba también Niebla.


def test_temas_oscuros_no_utilizan_iconos_claros():
    assert tema_utiliza_iconos_claros(TEMA_OSCURO_TECNET) is False  # Comprueba TecNet oscuro.
    assert tema_utiliza_iconos_claros(TEMA_OSCURO_OCEANO) is False  # Comprueba otra variante oscura.


def test_resolvedor_prefiere_variante_clara_cuando_existe(tmp_path):
    original = tmp_path / "Pegar.png"  # Prepara un recurso oscuro simulado.
    claro = tmp_path / "Pegar_Claro.png"  # Prepara su variante clara simulada.
    original.write_bytes(b"oscuro")  # Crea físicamente el archivo original.
    claro.write_bytes(b"claro")  # Crea físicamente la alternativa clara.
    assert resolver_icono_tema(tmp_path, "Pegar.png", TEMA_CLARO_TECNET) == claro  # Comprueba que el modo claro seleccione la variante adecuada.


def test_resolvedor_conserva_original_en_modo_oscuro(tmp_path):
    original = tmp_path / "Pegar.png"  # Prepara un recurso convencional.
    claro = tmp_path / "Pegar_Claro.png"  # Prepara también una variante clara.
    original.write_bytes(b"oscuro")  # Crea el recurso original.
    claro.write_bytes(b"claro")  # Crea la alternativa.
    assert resolver_icono_tema(tmp_path, "Pegar.png", TEMA_OSCURO_TECNET) == original  # Comprueba que un tema oscuro jamás sustituya innecesariamente su icono.


def test_resolvedor_conserva_original_si_no_hay_variante_clara(tmp_path):
    original = tmp_path / "Advertencia.png"  # Simula un icono semántico sin versión alternativa.
    original.write_bytes(b"semantico")  # Crea exclusivamente el recurso original.
    assert resolver_icono_tema(tmp_path, "Advertencia.png", TEMA_CLARO_TECNET) == original  # Comprueba que los iconos semánticos continúen funcionando en modo claro.