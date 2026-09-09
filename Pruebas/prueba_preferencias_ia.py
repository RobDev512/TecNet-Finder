# ============================================================
# Archivo: prueba_preferencias_ia.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba la persistencia de las preferencias del
# asistente local utilizando únicamente directorios temporales.
# ============================================================

from AsistenteIA.preferencias_ia import PreferenciasIA  # Importa el administrador cuya persistencia debe comprobarse.


def prueba_preferencias_activadas_por_defecto(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias.asistencia_activada() is True


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


def prueba_preferencias_ignoran_archivo_danado(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)
    preferencias.ruta_directorio.mkdir(parents=True)
    preferencias.ruta_archivo.write_text("{archivo dañado", encoding="utf-8")

    assert preferencias.asistencia_activada() is True


def prueba_preferencias_utilizan_ruta_administrada(tmp_path):
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)

    assert preferencias.ruta_directorio == tmp_path / "TecNetFinder"
    assert preferencias.ruta_archivo == tmp_path / "TecNetFinder" / "preferencias_ia.json"