# ============================================================
# Archivo: prueba_preferencias_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la base de internacionalización relacionada con el
# catálogo de idiomas y la preferencia persistente/temporal.
# ============================================================

import json  # Permite simular también preferencias externas o corruptas.

from Motor.configuracion.catalogo_idiomas import IDIOMA_PREDETERMINADO, IDIOMA_RESPALDO, idiomas_disponibles, normalizar_codigo_idioma, resolver_codigo_idioma  # Proporciona el catálogo central.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona la persistencia real.
from Motor.configuracion.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Proporciona la copia utilizada por Configuración.


def prueba_catalogo_contiene_los_seis_idiomas_planeados():
    codigos = tuple(codigo for codigo, _nombre in idiomas_disponibles())  # Recupera únicamente los códigos ofrecidos por la aplicación.
    assert codigos == ("es", "en", "pt", "fr", "de", "la")  # Mantiene exactamente el alcance definido para esta etapa.


def prueba_espanol_es_predeterminado_y_respaldo():
    assert IDIOMA_PREDETERMINADO == "es"  # Comprueba el idioma utilizado en una instalación nueva.
    assert IDIOMA_RESPALDO == "es"  # Comprueba el idioma utilizado ante una selección inválida.
    assert resolver_codigo_idioma("desconocido") == "es"  # Confirma la recuperación segura del respaldo.


def prueba_normaliza_variantes_regionales_sin_crear_idiomas_nuevos():
    assert normalizar_codigo_idioma("ES-mx") == "es"  # Reduce una variante regional española.
    assert normalizar_codigo_idioma("en_US") == "en"  # Acepta también la notación con guion bajo.
    assert normalizar_codigo_idioma("pt-BR") == "pt"  # Reduce portugués regional al código soportado.
    assert normalizar_codigo_idioma("xx-YY") is None  # Rechaza idiomas fuera del catálogo.


def prueba_preferencia_de_idioma_inicia_en_espanol(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Aísla la prueba de LocalAppData.
    assert preferencias.idioma_interfaz() == "es"  # Mantiene español cuando todavía no existe una selección guardada.


def prueba_preferencia_de_idioma_persiste_codigo_normalizado(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.establecer_idioma_interfaz("EN-us") is True  # Acepta una variante regional válida.
    recargadas = PreferenciasAplicacion(tmp_path)  # Simula una nueva ejecución de TecNet Finder.
    assert recargadas.idioma_interfaz() == "en"  # Comprueba que se haya persistido únicamente el código base.


def prueba_preferencia_rechaza_idioma_desconocido_sin_perder_el_actual(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada.
    assert preferencias.establecer_idioma_interfaz("fr") is True  # Establece primero una selección válida.
    assert preferencias.establecer_idioma_interfaz("xx") is False  # Rechaza un código fuera del catálogo.
    assert preferencias.idioma_interfaz() == "fr"  # Conserva la selección válida anterior.


def prueba_preferencia_corrupta_recupera_espanol(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Obtiene las rutas oficiales utilizadas por la clase.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Prepara el directorio aislado.
    preferencias.ruta_archivo.write_text(json.dumps({"idioma_interfaz": "xx"}), encoding="utf-8")  # Simula un archivo editado externamente.
    assert preferencias.idioma_interfaz() == "es"  # Recupera el respaldo sin impedir el inicio de la aplicación.


def prueba_idioma_temporal_no_modifica_preferencia_real_hasta_aplicar(tmp_path):
    reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración persistente.
    temporales = PreferenciasConfiguracionTemporales(reales)  # Crea una sesión de Configuración.
    assert temporales.establecer_idioma_interfaz("de") is True  # Cambia únicamente la copia en memoria.
    assert temporales.idioma_interfaz() == "de"  # Comprueba el valor temporal seleccionado.
    assert reales.idioma_interfaz() == "es"  # Confirma que todavía no se haya escrito el cambio real.


def prueba_recargar_temporales_descarta_cambio_de_idioma(tmp_path):
    reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración persistente en español.
    temporales = PreferenciasConfiguracionTemporales(reales)  # Crea una copia editable.
    temporales.establecer_idioma_interfaz("la")  # Simula una selección de latín todavía no confirmada.
    temporales.recargar_desde_preferencias_reales()  # Imita Cancelar o una nueva sesión de Configuración.
    assert temporales.idioma_interfaz() == "es"  # Recupera exactamente la preferencia persistente.
