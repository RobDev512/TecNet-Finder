# ============================================================
# Archivo: prueba_preferencias_configuracion_temporales.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba la copia temporal de preferencias que
# utiliza la ventana de Configuración antes de pulsar Aplicar
# o Aceptar.
#
# Verifica que modificar la copia temporal no altere
# inmediatamente las preferencias persistentes, que pueda
# recuperar correctamente los valores reales y que Cancelar
# pueda descartar las modificaciones todavía no aplicadas.
#
# También comprueba la exclusión mutua entre las modalidades
# utilizadas para mostrar advertencias.
# ============================================================

from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona la configuración persistente que sirve como referencia para las pruebas.
from Motor.configuracion.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Proporciona la copia editable utilizada mientras Configuración permanece abierta.


def test_cambiar_preferencia_temporal_no_modifica_preferencia_real(tmp_path):  # Comprueba que una modificación temporal permanezca separada del archivo persistente.
    preferencias_reales = PreferenciasAplicacion(tmp_path)  # Crea una configuración real aislada de LocalAppData mediante la carpeta temporal de pytest.
    preferencias_temporales = PreferenciasConfiguracionTemporales(preferencias_reales)  # Construye una copia editable utilizando los valores reales como punto de partida.
    assert preferencias_reales.iniciar_maximizado() is True  # Confirma primero el valor persistente predeterminado.
    assert preferencias_temporales.iniciar_maximizado() is True  # Comprueba que la copia temporal haya iniciado con exactamente el mismo valor.
    assert preferencias_temporales.establecer_iniciar_maximizado(False) is True  # Modifica únicamente la sesión temporal sin escribir todavía en disco.
    assert preferencias_temporales.iniciar_maximizado() is False  # Confirma que el nuevo valor sea visible dentro de Configuración.
    assert preferencias_reales.iniciar_maximizado() is True  # Comprueba que la preferencia real continúe intacta hasta que se aplique expresamente el cambio.


def test_copia_temporal_recupera_preferencias_reales(tmp_path):  # Comprueba que una copia nueva refleje correctamente valores persistentes modificados previamente.
    preferencias_reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración persistente sobre una ruta temporal.
    preferencias_reales.establecer_navegacion_errores_activada(False)  # Modifica el comportamiento real relacionado con la navegación hacia errores.
    preferencias_reales.establecer_recordar_estado_ventana(True)  # Activa también la recuperación real del estado de la ventana.
    preferencias_temporales = PreferenciasConfiguracionTemporales(preferencias_reales)  # Crea una nueva sesión temporal después de realizar ambas modificaciones.
    assert preferencias_temporales.navegacion_errores_activada() is False  # Confirma que la copia haya leído correctamente la primera preferencia persistente.
    assert preferencias_temporales.recordar_estado_ventana() is True  # Comprueba que también haya recuperado la segunda decisión real.


def test_advertencias_temporales_son_mutuamente_excluyentes(tmp_path):  # Comprueba que las dos modalidades temporales de advertencias nunca permanezcan activadas simultáneamente.
    preferencias_reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración persistente con sus valores predeterminados.
    preferencias_temporales = PreferenciasConfiguracionTemporales(preferencias_reales)  # Construye la copia que será manipulada durante la prueba.
    assert preferencias_temporales.advertencias_vlsm_visibles() is True  # Confirma que inicialmente se utilice el panel integrado debajo de Tabla VLSM.
    assert preferencias_temporales.advertencias_ventana_independiente() is False  # Confirma que la modalidad independiente comience desactivada.
    preferencias_temporales.establecer_advertencias_ventana_independiente(True)  # Activa temporalmente la modalidad alternativa.
    assert preferencias_temporales.advertencias_vlsm_visibles() is False  # Comprueba que activar la ventana desactive automáticamente el panel integrado.
    assert preferencias_temporales.advertencias_ventana_independiente() is True  # Confirma que la modalidad solicitada permanezca seleccionada.
    preferencias_temporales.establecer_advertencias_vlsm_visibles(True)  # Activa nuevamente el panel integrado para comprobar la exclusión en sentido contrario.
    assert preferencias_temporales.advertencias_vlsm_visibles() is True  # Confirma que el panel vuelva a quedar seleccionado.
    assert preferencias_temporales.advertencias_ventana_independiente() is False  # Comprueba que la ventana independiente se desactive automáticamente.


def test_recargar_descarta_cambios_temporales(tmp_path):  # Comprueba el comportamiento utilizado por Cancelar para recuperar las preferencias realmente persistidas.
    preferencias_reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración que permanecerá sin modificaciones durante la prueba.
    preferencias_temporales = PreferenciasConfiguracionTemporales(preferencias_reales)  # Inicia una sesión temporal basada en esos valores reales.
    preferencias_temporales.establecer_iniciar_maximizado(False)  # Simula una modificación todavía no confirmada por Aplicar.
    preferencias_temporales.establecer_navegacion_vlsm_activada(False)  # Simula además un segundo cambio pendiente dentro de Configuración.
    preferencias_temporales.recargar_desde_preferencias_reales()  # Descarta ambas modificaciones recuperando nuevamente la configuración persistente.
    assert preferencias_temporales.iniciar_maximizado() is True  # Confirma que el primer cambio temporal haya desaparecido.
    assert preferencias_temporales.navegacion_vlsm_activada() is True  # Comprueba que la segunda preferencia también vuelva a su valor real.