# ============================================================
# Archivo: prueba_preferencias_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo verifica la persistencia y recuperación segura de
# las preferencias generales de TecNet Finder.
#
# Comprueba preferencias relacionadas con:
#
# - Ventana y apariencia.
# - Navegación hacia errores y VLSM.
# - Presentación de advertencias.
# - Interacción con la ventana independiente.
# - Compatibilidad con configuraciones pertenecientes a versiones
#   anteriores.
#
# Las pruebas utilizan una carpeta temporal para evitar modificar
# la configuración real almacenada dentro de LocalAppData.
# ============================================================

from Motor.preferencias_aplicacion import PreferenciasAplicacion


def test_valores_predeterminados(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.iniciar_maximizado() is True
    assert preferencias.recordar_estado_ventana() is False
    assert preferencias.ultimo_estado_ventana() is None

    assert preferencias.recordar_seccion_configuracion() is True
    assert (
        preferencias.ultima_seccion_configuracion()
        == PreferenciasAplicacion.SECCION_VENTANA
    )

    assert preferencias.navegacion_errores_activada() is True
    assert preferencias.navegacion_vlsm_activada() is True

    assert preferencias.advertencias_vlsm_visibles() is True
    assert preferencias.advertencias_ventana_independiente() is False

    assert preferencias.cerrar_ventana_advertencias_al_navegar() is True


def test_guarda_preferencias_de_ventana(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_iniciar_maximizado(
        False
    ) is True

    assert preferencias.establecer_recordar_estado_ventana(
        True
    ) is True

    assert preferencias.establecer_ultimo_estado_ventana(
        PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.iniciar_maximizado() is False
    assert preferencias_recargadas.recordar_estado_ventana() is True

    assert (
        preferencias_recargadas.ultimo_estado_ventana()
        == PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
    )


def test_rechaza_estado_de_ventana_no_persistente(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_ultimo_estado_ventana(
        "pantalla_completa"
    ) is False

    assert preferencias.ultimo_estado_ventana() is None


def test_guarda_ultima_seccion_configuracion(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_ultima_seccion_configuracion(
        PreferenciasAplicacion.SECCION_IA
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert (
        preferencias_recargadas.ultima_seccion_configuracion()
        == PreferenciasAplicacion.SECCION_IA
    )


def test_rechaza_seccion_configuracion_inexistente(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_ultima_seccion_configuracion(
        "seccion_inexistente"
    ) is False

    assert (
        preferencias.ultima_seccion_configuracion()
        == PreferenciasAplicacion.SECCION_VENTANA
    )


def test_guarda_navegaciones_independientemente(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_navegacion_errores_activada(
        False
    ) is True

    assert preferencias.establecer_navegacion_vlsm_activada(
        True
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.navegacion_errores_activada() is False
    assert preferencias_recargadas.navegacion_vlsm_activada() is True


def test_preferencia_antigua_navegacion_migra_a_ambas_opciones(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    preferencias.ruta_directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    preferencias.ruta_archivo.write_text(
        '{"navegacion_automatica": false}',
        encoding="utf-8",
    )

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.navegacion_errores_activada() is False
    assert preferencias_recargadas.navegacion_vlsm_activada() is False


def test_ventana_independiente_desactiva_panel_vlsm(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.advertencias_vlsm_visibles() is True

    assert preferencias.establecer_advertencias_ventana_independiente(
        True
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.advertencias_ventana_independiente() is True
    assert preferencias_recargadas.advertencias_vlsm_visibles() is False


def test_panel_vlsm_desactiva_ventana_independiente(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_advertencias_ventana_independiente(
        True
    ) is True

    assert preferencias.establecer_advertencias_vlsm_visibles(
        True
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.advertencias_vlsm_visibles() is True
    assert preferencias_recargadas.advertencias_ventana_independiente() is False


def test_ambas_modalidades_pueden_permanecer_apagadas(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.establecer_advertencias_vlsm_visibles(
        False
    ) is True

    assert preferencias.establecer_advertencias_ventana_independiente(
        False
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.advertencias_vlsm_visibles() is False
    assert preferencias_recargadas.advertencias_ventana_independiente() is False


def test_guarda_comportamiento_al_navegar_desde_advertencia(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias.cerrar_ventana_advertencias_al_navegar() is True

    assert preferencias.establecer_cerrar_ventana_advertencias_al_navegar(
        False
    ) is True

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.cerrar_ventana_advertencias_al_navegar() is False


def test_archivo_danado_recupera_valores_seguros(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    preferencias.ruta_directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    preferencias.ruta_archivo.write_text(
        "{contenido inválido",
        encoding="utf-8",
    )

    assert preferencias.iniciar_maximizado() is True
    assert preferencias.recordar_estado_ventana() is False

    assert preferencias.navegacion_errores_activada() is True
    assert preferencias.navegacion_vlsm_activada() is True

    assert preferencias.advertencias_vlsm_visibles() is True
    assert preferencias.advertencias_ventana_independiente() is False

    assert preferencias.cerrar_ventana_advertencias_al_navegar() is True


def test_clave_antigua_media_pantalla_no_afecta_resultados(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    preferencias.ruta_directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    preferencias.ruta_archivo.write_text(
        '{"lado_media_pantalla": "derecha"}',
        encoding="utf-8",
    )

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.iniciar_maximizado() is True
    assert preferencias_recargadas.recordar_estado_ventana() is False

    assert preferencias_recargadas.navegacion_errores_activada() is True
    assert preferencias_recargadas.navegacion_vlsm_activada() is True

    assert preferencias_recargadas.advertencias_vlsm_visibles() is True
    assert preferencias_recargadas.advertencias_ventana_independiente() is False


def test_archivo_con_ambas_modalidades_activas_prioriza_panel_vlsm(tmp_path):
    preferencias = PreferenciasAplicacion(
        tmp_path
    )

    preferencias.ruta_directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    preferencias.ruta_archivo.write_text(
        """
        {
            "mostrar_advertencias_vlsm": true,
            "mostrar_advertencias_ventana": true
        }
        """,
        encoding="utf-8",
    )

    preferencias_recargadas = PreferenciasAplicacion(
        tmp_path
    )

    assert preferencias_recargadas.advertencias_vlsm_visibles() is True
    assert preferencias_recargadas.advertencias_ventana_independiente() is False