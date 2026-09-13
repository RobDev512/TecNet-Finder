# ============================================================
# Archivo: prueba_preferencias_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo verifica la persistencia y recuperación segura de
# las preferencias generales de TecNet Finder.
#
# Las pruebas utilizan una carpeta temporal para evitar modificar
# la configuración real almacenada dentro de LocalAppData.
# ============================================================

from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Importa exclusivamente el componente general que será validado.


def test_valores_predeterminados(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración completamente aislada de los datos reales del usuario.

    assert preferencias.lado_media_pantalla() == "izquierda"  # Comprueba que la primera ejecución proponga la mitad izquierda.
    assert preferencias.navegacion_automatica_activada() is True  # Comprueba que la navegación automática permanezca activa inicialmente.
    assert preferencias.advertencias_vlsm_visibles() is True  # Comprueba que el panel compacto de advertencias sea visible inicialmente.


def test_guarda_lado_media_pantalla(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada para esta prueba.
    guardado = preferencias.establecer_lado_media_pantalla("derecha")  # Cambia la mitad predeterminada.

    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Simula una nueva ejecución de TecNet Finder.

    assert guardado is True  # Comprueba que la escritura haya sido aceptada.
    assert preferencias_recargadas.lado_media_pantalla() == "derecha"  # Comprueba que la decisión persista entre instancias.


def test_rechaza_lado_media_pantalla_desconocido(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada sin valores anteriores.
    guardado = preferencias.establecer_lado_media_pantalla("centro")  # Intenta almacenar una posición inexistente.

    assert guardado is False  # Comprueba que posiciones desconocidas no sean aceptadas.
    assert preferencias.lado_media_pantalla() == "izquierda"  # Comprueba que el valor seguro permanezca intacto.


def test_guarda_preferencias_de_resultados(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración aislada para modificar ambas opciones booleanas.

    assert preferencias.establecer_navegacion_automatica_activada(False) is True  # Desactiva la navegación automática.
    assert preferencias.establecer_advertencias_vlsm_visibles(False) is True  # Oculta el panel compacto de advertencias.

    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Simula el inicio posterior de la aplicación.

    assert preferencias_recargadas.navegacion_automatica_activada() is False  # Comprueba que la primera decisión permanezca guardada.
    assert preferencias_recargadas.advertencias_vlsm_visibles() is False  # Comprueba que la segunda decisión también permanezca guardada.


def test_archivo_danado_recupera_valores_seguros(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Obtiene las rutas administradas utilizadas por la configuración.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Prepara manualmente la carpeta destinada al archivo.
    preferencias.ruta_archivo.write_text("{contenido inválido", encoding="utf-8")  # Simula una configuración JSON dañada.

    assert preferencias.lado_media_pantalla() == "izquierda"  # Comprueba que un archivo dañado no impida recuperar el lado seguro.
    assert preferencias.navegacion_automatica_activada() is True  # Comprueba que también se recupere la navegación recomendada.
    assert preferencias.advertencias_vlsm_visibles() is True  # Comprueba que la presentación de advertencias conserve su valor seguro.