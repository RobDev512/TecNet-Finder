# ============================================================
# Archivo: prueba_preferencias_ia.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba la persistencia independiente de las
# funciones del asistente local utilizando únicamente directorios
# temporales y verifica la compatibilidad con configuraciones
# creadas por versiones anteriores.
# ============================================================

import json  # Permite construir explícitamente una preferencia histórica durante la prueba de migración.

from AsistenteIA.preferencias_ia import PreferenciasIA  # Importa el administrador cuya persistencia debe comprobarse.


def prueba_preferencias_activadas_por_defecto(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias.asistencia_activada() is True
    assert preferencias.autocompletado_activado() is True
    assert preferencias.diagnosticos_ia_activados() is True
    assert preferencias.alguna_funcion_activada() is True


def prueba_preferencias_guardan_desactivacion(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias.establecer_asistencia_activada(False) is True

    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias_recargadas.asistencia_activada() is False


def prueba_preferencias_guardan_reactivacion(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)
    preferencias.establecer_asistencia_activada(False)

    assert preferencias.establecer_asistencia_activada(True) is True

    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias_recargadas.asistencia_activada() is True


def prueba_preferencias_guardan_funciones_independientes(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias.establecer_autocompletado_activado(False) is True
    assert preferencias.establecer_diagnosticos_ia_activados(True) is True

    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias_recargadas.autocompletado_activado() is False
    assert preferencias_recargadas.diagnosticos_ia_activados() is True
    assert preferencias_recargadas.alguna_funcion_activada() is True


def prueba_preferencias_detectan_cuando_ninguna_funcion_requiere_ia(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)
    preferencias.establecer_autocompletado_activado(False)
    preferencias.establecer_diagnosticos_ia_activados(False)

    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias_recargadas.alguna_funcion_activada() is False


def prueba_preferencias_migran_logicamente_clave_anterior(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)
    preferencias.ruta_directorio.mkdir(parents=True)
    preferencias.ruta_archivo.write_text(
        json.dumps({"asistencia_ia_activada": False}),
        encoding="utf-8",
    )

    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias_recargadas.autocompletado_activado() is False
    assert preferencias_recargadas.diagnosticos_ia_activados() is False
    assert preferencias_recargadas.alguna_funcion_activada() is False


def prueba_preferencias_ignoran_archivo_danado(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)
    preferencias.ruta_directorio.mkdir(parents=True)
    preferencias.ruta_archivo.write_text("{archivo dañado", encoding="utf-8")

    assert preferencias.asistencia_activada() is True
    assert preferencias.diagnosticos_ia_activados() is True


def prueba_preferencias_utilizan_ruta_administrada(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias.ruta_directorio == tmp_path / "TecNetFinder"
    assert preferencias.ruta_archivo == tmp_path / "TecNetFinder" / "preferencias_ia.json"
