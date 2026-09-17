# ============================================================
# Archivo: prueba_preferencias_editor.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba las preferencias persistentes y temporales del Editor,
# incluyendo familia tipográfica, tamaño, ajuste de línea, botones
# rápidos y tabulación.
# ============================================================

from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Importa la configuración persistente.
from Motor.configuracion.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Importa la copia utilizada por Configuración.


def test_valores_predeterminados_editor(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.ajuste_linea_editor_activado() is True  # Comprueba el ajuste predeterminado.
    assert preferencias.botones_rapidos_editor_visibles() is True  # Comprueba la visibilidad predeterminada.
    assert preferencias.familia_fuente_editor() == "Consolas"  # Comprueba que se conserve la tipografía histórica.
    assert preferencias.tamano_fuente_editor() == 10  # Comprueba el tamaño original.
    assert preferencias.espacios_tabulacion_editor() == 4  # Comprueba el ancho original de Tab.


def test_guarda_preferencias_editor(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.establecer_ajuste_linea_editor_activado(False) is True  # Cambia el ajuste.
    assert preferencias.establecer_botones_rapidos_editor_visibles(False) is True  # Cambia los botones rápidos.
    assert preferencias.establecer_familia_fuente_editor("Cascadia Code") is True  # Cambia la familia.
    assert preferencias.establecer_tamano_fuente_editor(13) is True  # Cambia el tamaño.
    assert preferencias.establecer_espacios_tabulacion_editor(8) is True  # Cambia Tab.
    recargadas = PreferenciasAplicacion(tmp_path)  # Simula una nueva ejecución.
    assert recargadas.ajuste_linea_editor_activado() is False  # Comprueba persistencia del ajuste.
    assert recargadas.botones_rapidos_editor_visibles() is False  # Comprueba persistencia de botones.
    assert recargadas.familia_fuente_editor() == "Cascadia Code"  # Comprueba persistencia de la familia.
    assert recargadas.tamano_fuente_editor() == 13  # Comprueba persistencia del tamaño.
    assert recargadas.espacios_tabulacion_editor() == 8  # Comprueba persistencia de Tab.


def test_rechaza_familia_fuente_vacia(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.establecer_familia_fuente_editor("") is False  # Rechaza una familia vacía.
    assert preferencias.familia_fuente_editor() == "Consolas"  # Mantiene el valor seguro original.


def test_rechaza_tamano_fuente_fuera_de_rango(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.establecer_tamano_fuente_editor(4) is False  # Rechaza un valor demasiado pequeño.
    assert preferencias.establecer_tamano_fuente_editor(50) is False  # Rechaza un valor demasiado grande.
    assert preferencias.tamano_fuente_editor() == 10  # Mantiene el tamaño original.


def test_rechaza_tabulacion_no_permitida(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.establecer_espacios_tabulacion_editor(3) is False  # Rechaza un valor no ofrecido.
    assert preferencias.espacios_tabulacion_editor() == 4  # Mantiene la opción original.


def test_editor_temporal_no_modifica_preferencias_reales(tmp_path):
    reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración realmente persistente.
    temporales = PreferenciasConfiguracionTemporales(reales)  # Crea la copia utilizada por Configuración.
    assert temporales.establecer_familia_fuente_editor("Cascadia Mono") is True  # Modifica temporalmente la familia.
    assert temporales.establecer_tamano_fuente_editor(15) is True  # Modifica temporalmente el tamaño.
    assert temporales.familia_fuente_editor() == "Cascadia Mono"  # Comprueba la copia temporal.
    assert temporales.tamano_fuente_editor() == 15  # Comprueba el tamaño temporal.
    assert reales.familia_fuente_editor() == "Consolas"  # Confirma que la preferencia real continúa intacta.
    assert reales.tamano_fuente_editor() == 10  # Confirma que el tamaño real continúa intacto.


def test_recargar_temporales_descarta_cambios_editor(tmp_path):
    reales = PreferenciasAplicacion(tmp_path)  # Crea las preferencias reales.
    temporales = PreferenciasConfiguracionTemporales(reales)  # Crea una sesión temporal.
    temporales.establecer_familia_fuente_editor("Courier New")  # Simula una modificación sin aplicar.
    temporales.establecer_tamano_fuente_editor(18)  # Simula una segunda modificación.
    temporales.recargar_desde_preferencias_reales()  # Descarta los cambios temporales.
    assert temporales.familia_fuente_editor() == "Consolas"  # Comprueba la recuperación de la familia real.
    assert temporales.tamano_fuente_editor() == 10  # Comprueba la recuperación del tamaño real.