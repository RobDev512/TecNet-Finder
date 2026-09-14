# ============================================================
# Archivo: prueba_preferencias_configuracion_temporales.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo verifica que la copia temporal utilizada por
# Configuración permita editar preferencias sin modificar
# inmediatamente el archivo persistente de TecNet Finder.
#
# También comprueba la exclusividad entre las dos modalidades
# disponibles para mostrar advertencias.
# ============================================================

from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona la configuración real utilizada como referencia.
from Motor.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Proporciona la copia editable que no escribe en disco.


def test_cambiar_preferencia_temporal_no_modifica_preferencia_real(
    tmp_path,
):
    preferencias_reales = PreferenciasAplicacion(
        tmp_path
    )  # Crea una configuración real aislada de LocalAppData.

    preferencias_temporales = PreferenciasConfiguracionTemporales(
        preferencias_reales
    )  # Copia el estado inicial.

    assert preferencias_reales.iniciar_maximizado() is True
    assert preferencias_temporales.iniciar_maximizado() is True

    assert preferencias_temporales.establecer_iniciar_maximizado(
        False
    ) is True  # Cambia únicamente la sesión temporal.

    assert preferencias_temporales.iniciar_maximizado() is False
    assert preferencias_reales.iniciar_maximizado() is True  # Confirma que LocalAppData todavía no fue modificado.


def test_copia_temporal_recupera_preferencias_reales(
    tmp_path,
):
    preferencias_reales = PreferenciasAplicacion(
        tmp_path
    )

    preferencias_reales.establecer_navegacion_errores_activada(
        False
    )

    preferencias_reales.establecer_recordar_estado_ventana(
        True
    )

    preferencias_temporales = PreferenciasConfiguracionTemporales(
        preferencias_reales
    )

    assert preferencias_temporales.navegacion_errores_activada() is False
    assert preferencias_temporales.recordar_estado_ventana() is True


def test_advertencias_temporales_son_mutuamente_excluyentes(
    tmp_path,
):
    preferencias_reales = PreferenciasAplicacion(
        tmp_path
    )

    preferencias_temporales = PreferenciasConfiguracionTemporales(
        preferencias_reales
    )

    assert preferencias_temporales.advertencias_vlsm_visibles() is True
    assert preferencias_temporales.advertencias_ventana_independiente() is False

    preferencias_temporales.establecer_advertencias_ventana_independiente(
        True
    )

    assert preferencias_temporales.advertencias_vlsm_visibles() is False
    assert preferencias_temporales.advertencias_ventana_independiente() is True

    preferencias_temporales.establecer_advertencias_vlsm_visibles(
        True
    )

    assert preferencias_temporales.advertencias_vlsm_visibles() is True
    assert preferencias_temporales.advertencias_ventana_independiente() is False


def test_recargar_descarta_cambios_temporales(
    tmp_path,
):
    preferencias_reales = PreferenciasAplicacion(
        tmp_path
    )

    preferencias_temporales = PreferenciasConfiguracionTemporales(
        preferencias_reales
    )

    preferencias_temporales.establecer_iniciar_maximizado(
        False
    )

    preferencias_temporales.establecer_navegacion_vlsm_activada(
        False
    )

    preferencias_temporales.recargar_desde_preferencias_reales()

    assert preferencias_temporales.iniciar_maximizado() is True
    assert preferencias_temporales.navegacion_vlsm_activada() is True