# ============================================================
# Archivo: prueba_gestor_traducciones.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba el motor central de traducciones, el respaldo a
# español, la carga segura de JSON y el formato de variables.
# ============================================================

import json  # Permite construir catálogos aislados durante las pruebas.

from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones  # Proporciona el motor que será validado.


def _escribir_catalogo(ruta, codigo: str, datos: dict) -> None:
    ruta.mkdir(parents=True, exist_ok=True)  # Prepara la carpeta temporal cuando todavía no existe.
    (ruta / f"{codigo}.json").write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")  # Guarda un catálogo mínimo y legible.


def prueba_inicia_en_espanol_por_defecto(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Hola"})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.idioma == "es"
    assert gestor.traducir("mensaje") == "Hola"


def prueba_cambia_a_un_idioma_admitido_y_normaliza_variante(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Hola"})
    _escribir_catalogo(tmp_path, "en", {"mensaje": "Hello"})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.establecer_idioma("EN-us") is True
    assert gestor.idioma == "en"
    assert gestor.traducir("mensaje") == "Hello"


def prueba_rechaza_idioma_desconocido_sin_cambiar_el_actual(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Hola"})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.establecer_idioma("xx") is False
    assert gestor.idioma == "es"


def prueba_usa_espanol_si_falta_clave_en_idioma_activo(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"solo_es": "Respaldo español"})
    _escribir_catalogo(tmp_path, "fr", {"otra": "Autre"})
    gestor = GestorTraducciones("fr", ruta_catalogos=tmp_path)
    assert gestor.traducir("solo_es") == "Respaldo español"


def prueba_clave_inexistente_se_muestra_de_forma_visible(tmp_path):
    _escribir_catalogo(tmp_path, "es", {})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.traducir("clave.inexistente") == "[clave.inexistente]"


def prueba_catalogo_secundario_danado_no_rompe_respaldo(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Seguro"})
    (tmp_path / "de.json").write_text("{esto no es json", encoding="utf-8")
    gestor = GestorTraducciones("de", ruta_catalogos=tmp_path)
    assert gestor.traducir("mensaje") == "Seguro"


def prueba_catalogo_secundario_ausente_no_rompe_respaldo(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Seguro"})
    gestor = GestorTraducciones("pt", ruta_catalogos=tmp_path)
    assert gestor.traducir("mensaje") == "Seguro"


def prueba_reemplaza_variables_nombradas(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"saludo": "Hola, {nombre}."})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.traducir("saludo", nombre="Robert") == "Hola, Robert."


def prueba_variable_faltante_conserva_texto_base_sin_excepcion(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"saludo": "Hola, {nombre}."})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.traducir("saludo") == "Hola, {nombre}."


def prueba_recargar_descarta_cache_y_relee_catalogo(tmp_path):
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Primero"})
    gestor = GestorTraducciones(ruta_catalogos=tmp_path)
    assert gestor.traducir("mensaje") == "Primero"
    _escribir_catalogo(tmp_path, "es", {"mensaje": "Después"})
    assert gestor.traducir("mensaje") == "Primero"
    gestor.recargar()
    assert gestor.traducir("mensaje") == "Después"


def prueba_recursos_reales_incluyen_los_seis_catalogos():
    gestor = GestorTraducciones("es")
    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        assert gestor.establecer_idioma(codigo) is True
        assert gestor.traducir("configuracion.idioma") != "[configuracion.idioma]"


def prueba_respaldo_real_funciona_desde_ingles():
    gestor = GestorTraducciones("en")
    assert gestor.traducir("prueba.respaldo") == "Texto disponible solamente en español."


def prueba_catalogos_reales_contienen_textos_visibles_de_configuracion():
    claves_requeridas = {
        "configuracion.titulo",
        "configuracion.seccion.ventana",
        "configuracion.seccion.editor",
        "configuracion.seccion.resultados",
        "configuracion.seccion.ia",
        "configuracion.ventana.titulo",
        "configuracion.ventana.idioma.titulo",
        "configuracion.ventana.tipografia.titulo",
        "configuracion.ventana.configuracion.recordar",
        "configuracion.resumen.titulo",
        "configuracion.resumen.texto",
        "configuracion.error.aplicar",
    }  # Define el mínimo que este bloque necesita traducido directamente en cada catálogo.

    gestor = GestorTraducciones("es")
    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = gestor.ruta_catalogos / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert claves_requeridas.issubset(datos.keys())  # Impide que el respaldo español oculte accidentalmente una traducción faltante.


def prueba_configuracion_ingles_resuelve_textos_visibles():
    gestor = GestorTraducciones("en")
    assert gestor.traducir("configuracion.titulo") == "Settings"
    assert gestor.traducir("configuracion.seccion.ventana") == "Window and appearance"
    assert gestor.traducir("configuracion.ventana.idioma.titulo") == "Interface language"
    assert gestor.traducir("comun.aplicar") == "Apply"
    assert gestor.traducir("comun.cancelar") == "Cancel"
