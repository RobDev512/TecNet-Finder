# ============================================================
# Archivo: prueba_temas_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba catálogo, modos, paletas, persistencia y copia
# temporal del sistema de temas de TecNet Finder.
#
# Las pruebas no modifican la configuración real del usuario.
# ============================================================

import json  # Permite preparar archivos alterados manualmente durante algunas pruebas.
from Motor.configuracion.catalogo_temas import MODO_CLARO, MODO_OSCURO, TEMA_CLARO_NIEBLA, TEMA_CLARO_TECNET, TEMA_OSCURO_MEDIANOCHE, TEMA_OSCURO_OCEANO, TEMA_OSCURO_TECNET, TEMA_PREDETERMINADO, modo_del_tema, normalizar_tema, obtener_modos_disponibles, obtener_tema, obtener_temas_por_modo, tema_existe  # Importa las operaciones públicas del catálogo.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Proporciona la persistencia real del tema.
from Motor.configuracion.preferencias_tema_temporales import PreferenciasTemaTemporales  # Proporciona la copia temporal utilizada por Configuración.


def test_catalogo_incluye_tres_variantes_oscuras():
    temas = {tema["id"] for tema in obtener_temas_por_modo(MODO_OSCURO)}  # Recupera los identificadores pertenecientes al modo oscuro.
    assert {TEMA_OSCURO_TECNET, TEMA_OSCURO_MEDIANOCHE, TEMA_OSCURO_OCEANO}.issubset(temas)  # Comprueba que las tres variantes oscuras estén disponibles.


def test_catalogo_incluye_dos_variantes_claras():
    temas = {tema["id"] for tema in obtener_temas_por_modo(MODO_CLARO)}  # Recupera los identificadores pertenecientes al modo claro.
    assert {TEMA_CLARO_TECNET, TEMA_CLARO_NIEBLA}.issubset(temas)  # Comprueba que ambas variantes claras estén disponibles.


def test_catalogo_expone_modos_oscuro_y_claro():
    modos = {modo["id"] for modo in obtener_modos_disponibles()}  # Recupera los modos ofrecidos por Configuración.
    assert modos == {MODO_OSCURO, MODO_CLARO}  # Comprueba que no falte ninguno de los dos modos actuales.


def test_tema_predeterminado_continua_siendo_tecnet_oscuro():
    assert TEMA_PREDETERMINADO == TEMA_OSCURO_TECNET  # Garantiza que una instalación nueva conserve la apariencia histórica.


def test_modo_se_obtiene_directamente_del_tema():
    assert modo_del_tema(TEMA_OSCURO_OCEANO) == MODO_OSCURO  # Comprueba una variante oscura.
    assert modo_del_tema(TEMA_CLARO_TECNET) == MODO_CLARO  # Comprueba una variante clara.


def test_variantes_oscuras_utilizan_fondos_principales_diferentes():
    fondos = {obtener_tema(TEMA_OSCURO_TECNET)["fondo"], obtener_tema(TEMA_OSCURO_MEDIANOCHE)["fondo"], obtener_tema(TEMA_OSCURO_OCEANO)["fondo"]}  # Recupera el fondo principal de cada variante.
    assert len(fondos) == 3  # Garantiza que los tres temas ya no sean solamente cambios de acento.


def test_variantes_claras_utilizan_fondos_diferentes():
    assert obtener_tema(TEMA_CLARO_TECNET)["fondo"] != obtener_tema(TEMA_CLARO_NIEBLA)["fondo"]  # Comprueba que Niebla sea una variante real y no un alias visual.


def test_colores_semanticos_se_adaptan_al_modo():
    assert obtener_tema(TEMA_OSCURO_TECNET)["error"] != obtener_tema(TEMA_CLARO_TECNET)["error"]  # Comprueba que error utilice un tono con contraste apropiado para cada fondo.
    assert obtener_tema(TEMA_OSCURO_TECNET)["advertencia"] != obtener_tema(TEMA_CLARO_TECNET)["advertencia"]  # Comprueba también la adaptación de advertencias.


def test_catalogo_rechaza_identificador_desconocido():
    assert tema_existe("tema_que_no_existe") is False  # Comprueba que un valor arbitrario no sea aceptado.
    assert normalizar_tema("tema_que_no_existe") == TEMA_PREDETERMINADO  # Comprueba que el sistema pueda recuperarse utilizando la variante segura.


def test_obtener_tema_devuelve_una_copia():
    tema = obtener_tema(TEMA_OSCURO_TECNET)  # Recupera una copia de la paleta azul.
    tema["acento"] = "#000000"  # Modifica solamente la copia recibida.
    assert obtener_tema(TEMA_OSCURO_TECNET)["acento"] == "#89b4fa"  # Comprueba que el catálogo central permanezca intacto.


def test_preferencia_tema_utiliza_tecnet_oscuro_en_instalacion_nueva(tmp_path):
    preferencias = PreferenciasTema(tmp_path)  # Crea una configuración completamente aislada.
    assert preferencias.tema() == TEMA_PREDETERMINADO  # Comprueba que el valor inicial siga siendo TecNet oscuro.


def test_preferencia_tema_puede_persistir_un_tema_claro(tmp_path):
    preferencias = PreferenciasTema(tmp_path)  # Prepara la instancia que realizará la escritura.
    assert preferencias.establecer_tema(TEMA_CLARO_TECNET) is True  # Guarda explícitamente una variante clara.
    assert PreferenciasTema(tmp_path).tema() == TEMA_CLARO_TECNET  # Comprueba que permanezca entre sesiones.


def test_preferencia_tema_rechaza_valor_desconocido(tmp_path):
    preferencias = PreferenciasTema(tmp_path)  # Prepara una configuración aislada.
    assert preferencias.establecer_tema("inexistente") is False  # Rechaza un identificador desconocido.
    assert preferencias.tema() == TEMA_PREDETERMINADO  # Comprueba que la selección anterior no se altere.


def test_preferencia_tema_recupera_archivo_con_valor_invalido(tmp_path):
    preferencias = PreferenciasTema(tmp_path)  # Prepara las rutas utilizadas por el administrador.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta antes de escribir manualmente.
    preferencias.ruta_archivo.write_text(json.dumps({"tema": "valor_antiguo"}), encoding="utf-8")  # Simula una preferencia perteneciente a una versión diferente.
    assert PreferenciasTema(tmp_path).tema() == TEMA_PREDETERMINADO  # Comprueba que un valor desconocido nunca impida iniciar la aplicación.


def test_copia_temporal_no_modifica_preferencia_real(tmp_path):
    reales = PreferenciasTema(tmp_path)  # Crea la configuración persistente.
    temporales = PreferenciasTemaTemporales(reales)  # Crea la copia utilizada por Configuración.
    assert temporales.establecer_tema(TEMA_CLARO_NIEBLA) is True  # Cambia exclusivamente la copia temporal.
    assert temporales.tema() == TEMA_CLARO_NIEBLA  # Comprueba que Configuración vea la nueva selección.
    assert reales.tema() == TEMA_PREDETERMINADO  # Comprueba que Cancelar todavía pueda descartar completamente el cambio.


def test_copia_temporal_puede_recargar_tema_real(tmp_path):
    reales = PreferenciasTema(tmp_path)  # Crea las preferencias persistentes.
    assert reales.establecer_tema(TEMA_OSCURO_MEDIANOCHE) is True  # Guarda Medianoche como selección definitiva.
    temporales = PreferenciasTemaTemporales(reales)  # Abre una nueva sesión temporal.
    assert temporales.establecer_tema(TEMA_CLARO_TECNET) is True  # Simula una selección clara todavía no confirmada.
    temporales.recargar()  # Simula descartar esa decisión.
    assert temporales.tema() == TEMA_OSCURO_MEDIANOCHE  # Comprueba que vuelva exactamente al valor persistido.