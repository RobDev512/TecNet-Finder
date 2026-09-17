# ============================================================
# Archivo: prueba_preferencias_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba la persistencia de las preferencias
# relacionadas con la inteligencia artificial local.
#
# Verifica que Autocompletado y mejora de Diagnósticos puedan
# administrarse de manera independiente, que las decisiones
# permanezcan entre ejecuciones y que configuraciones creadas
# por versiones anteriores continúen siendo interpretadas.
#
# También comprueba la recuperación segura ante archivos
# dañados y las rutas utilizadas para guardar estas preferencias.
#
# Todas las pruebas trabajan únicamente con carpetas temporales.
# ============================================================

import json  # Permite construir explícitamente una configuración perteneciente al formato histórico durante la prueba de compatibilidad.

from AsistenteIA.preferencias.preferencias_ia import PreferenciasIA  # Importa el administrador persistente encargado de las funciones opcionales de IA.


def prueba_preferencias_activadas_por_defecto(tmp_path):  # Comprueba los valores utilizados cuando todavía no existe ningún archivo de preferencias de IA.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Sustituye LocalAppData por una carpeta temporal inicialmente vacía.
    assert preferencias.asistencia_activada() is True  # Confirma que el nombre histórico continúe representando autocompletado activado de forma predeterminada.
    assert preferencias.autocompletado_activado() is True  # Comprueba que las sugerencias mediante ghost text comiencen habilitadas.
    assert preferencias.diagnosticos_ia_activados() is True  # Confirma que la mejora opcional de soluciones también comience habilitada.
    assert preferencias.alguna_funcion_activada() is True  # Comprueba que el administrador detecte correctamente que existe al menos una función que necesita IA.


def prueba_preferencias_guardan_desactivacion(tmp_path):  # Comprueba que el método histórico de asistencia todavía pueda persistir una desactivación.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Crea el administrador que realizará la primera escritura.
    assert preferencias.establecer_asistencia_activada(False) is True  # Desactiva el autocompletado mediante la interfaz de compatibilidad y confirma que pueda guardarse.
    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)  # Crea otra instancia para obligar a recuperar el valor desde el archivo.
    assert preferencias_recargadas.asistencia_activada() is False  # Confirma que la decisión permanezca después de recargar la configuración.


def prueba_preferencias_guardan_reactivacion(tmp_path):  # Comprueba que una función previamente desactivada pueda habilitarse nuevamente.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Crea una configuración temporal nueva.
    preferencias.establecer_asistencia_activada(False)  # Establece primero el estado contrario para que exista un cambio real.
    assert preferencias.establecer_asistencia_activada(True) is True  # Reactiva la función y confirma que la nueva decisión pueda persistirse.
    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)  # Recupera el archivo mediante una instancia distinta.
    assert preferencias_recargadas.asistencia_activada() is True  # Comprueba que la reactivación haya quedado almacenada correctamente.


def prueba_preferencias_guardan_funciones_independientes(tmp_path):  # Comprueba que autocompletado y diagnósticos no vuelvan a comportarse como una sola preferencia.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Prepara el administrador persistente utilizado por la prueba.
    assert preferencias.establecer_autocompletado_activado(False) is True  # Desactiva únicamente las sugerencias de código.
    assert preferencias.establecer_diagnosticos_ia_activados(True) is True  # Mantiene activa de forma independiente la mejora de diagnósticos.
    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)  # Crea una nueva instancia para recuperar los valores almacenados.
    assert preferencias_recargadas.autocompletado_activado() is False  # Confirma que el autocompletado permanezca deshabilitado.
    assert preferencias_recargadas.diagnosticos_ia_activados() is True  # Comprueba que la segunda función continúe activada.
    assert preferencias_recargadas.alguna_funcion_activada() is True  # Verifica que Ollama todavía pueda considerarse necesario gracias a diagnósticos.


def prueba_preferencias_detectan_cuando_ninguna_funcion_requiere_ia(tmp_path):  # Comprueba el estado utilizado cuando ninguna característica necesita mantener disponible Ollama.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Crea una configuración aislada para esta combinación.
    preferencias.establecer_autocompletado_activado(False)  # Desactiva la primera función opcional.
    preferencias.establecer_diagnosticos_ia_activados(False)  # Desactiva también la segunda función opcional.
    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)  # Fuerza la recuperación de ambas decisiones desde el archivo.
    assert preferencias_recargadas.alguna_funcion_activada() is False  # Confirma que el administrador detecte correctamente que ya no existe ningún consumidor de IA.


def prueba_preferencias_migran_logicamente_clave_anterior(tmp_path):  # Comprueba que una configuración antigua pueda alimentar las dos preferencias separadas actuales.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Prepara las rutas administradas donde se escribirá manualmente un archivo histórico.
    preferencias.ruta_directorio.mkdir(parents=True)  # Crea la carpeta persistente simulando una instalación previa.
    preferencias.ruta_archivo.write_text(json.dumps({"asistencia_ia_activada": False}), encoding="utf-8")  # Guarda únicamente la clave global utilizada antes de separar ambas funciones.
    preferencias_recargadas = PreferenciasIA(ruta_datos_locales=tmp_path)  # Recupera el archivo mediante la implementación actual.
    assert preferencias_recargadas.autocompletado_activado() is False  # Confirma que la antigua desactivación se aplique al autocompletado.
    assert preferencias_recargadas.diagnosticos_ia_activados() is False  # Comprueba que la misma decisión histórica se utilice como respaldo para diagnósticos.
    assert preferencias_recargadas.alguna_funcion_activada() is False  # Verifica que ninguna función quede activa después de interpretar el archivo antiguo.


def prueba_preferencias_ignoran_archivo_danado(tmp_path):  # Comprueba que un JSON inválido no afecte el inicio general de TecNet Finder.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Prepara las rutas donde se escribirá deliberadamente información corrupta.
    preferencias.ruta_directorio.mkdir(parents=True)  # Crea la carpeta utilizada normalmente por el archivo de preferencias.
    preferencias.ruta_archivo.write_text("{archivo dañado", encoding="utf-8")  # Guarda contenido que no puede convertirse en un objeto JSON válido.
    assert preferencias.asistencia_activada() is True  # Confirma que el administrador recupere el valor seguro predeterminado para autocompletado.
    assert preferencias.diagnosticos_ia_activados() is True  # Comprueba que la segunda función también utilice su comportamiento predeterminado seguro.


def prueba_preferencias_utilizan_ruta_administrada(tmp_path):  # Comprueba que la configuración de IA permanezca dentro de la carpeta privada perteneciente a TecNet Finder.
    preferencias = PreferenciasIA(ruta_datos_locales=tmp_path)  # Sustituye la ubicación real del usuario por una ruta temporal controlada.
    assert preferencias.ruta_directorio == tmp_path / "TecNetFinder"  # Confirma la carpeta general donde deben conservarse las preferencias de IA.
    assert preferencias.ruta_archivo == tmp_path / "TecNetFinder" / "preferencias_ia.json"  # Verifica también el nombre y ubicación exactos del archivo persistente.