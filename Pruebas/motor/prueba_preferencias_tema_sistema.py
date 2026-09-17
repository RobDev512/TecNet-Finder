# ============================================================
# Archivo: prueba_preferencias_tema_sistema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la selección automática del tema del sistema y la
# transición segura hacia una preferencia manual del usuario.
# ============================================================

import json  # Permite preparar preferencias antiguas y comprobar la persistencia resultante.
import Motor.configuracion.preferencias_tema as modulo_preferencias_tema  # Permite sustituir de forma controlada la detección del sistema durante las pruebas.
from Motor.configuracion.catalogo_temas import TEMA_CLARO_NIEBLA, TEMA_CLARO_TECNET, TEMA_OSCURO_MEDIANOCHE, TEMA_OSCURO_TECNET  # Proporciona variantes reales del catálogo.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Proporciona el componente sometido a prueba.


def prueba_primera_ejecucion_sigue_tema_del_sistema(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo_preferencias_tema, "tema_recomendado_sistema", lambda: TEMA_CLARO_TECNET)  # Simula Windows configurado en modo claro.
    preferencias = PreferenciasTema(tmp_path)  # Crea una instalación completamente nueva dentro de una carpeta temporal.
    assert preferencias.utiliza_modo_sistema() is True  # Comprueba que todavía no exista una elección manual.
    assert preferencias.tema() == TEMA_CLARO_TECNET  # Comprueba que TecNet Finder utilice la variante clara equivalente.


def prueba_preferencia_antigua_tecnet_migra_a_modo_sistema(tmp_path, monkeypatch):
    preferencias = PreferenciasTema(tmp_path)  # Construye las rutas utilizadas por la preferencia.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Prepara la carpeta como lo habría hecho una versión anterior.
    preferencias.ruta_archivo.write_text(json.dumps({"tema": TEMA_OSCURO_TECNET}), encoding="utf-8")  # Simula el antiguo tema base sin información de origen.
    monkeypatch.setattr(modulo_preferencias_tema, "tema_recomendado_sistema", lambda: TEMA_CLARO_TECNET)  # Simula que Windows ahora utiliza modo claro.
    assert preferencias.utiliza_modo_sistema() is True  # Comprueba que la variante base antigua pueda adoptar el nuevo comportamiento automático.
    assert preferencias.tema() == TEMA_CLARO_TECNET  # Comprueba que el modo real del sistema tenga prioridad sobre el valor base histórico.


def prueba_preferencia_antigua_personalizada_se_conserva_manual(tmp_path, monkeypatch):
    preferencias = PreferenciasTema(tmp_path)  # Construye las rutas utilizadas por la preferencia.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Prepara la carpeta de datos temporal.
    preferencias.ruta_archivo.write_text(json.dumps({"tema": TEMA_CLARO_NIEBLA}), encoding="utf-8")  # Simula una variante personalizada seleccionada antes de esta actualización.
    monkeypatch.setattr(modulo_preferencias_tema, "tema_recomendado_sistema", lambda: TEMA_OSCURO_TECNET)  # Simula un sistema actualmente oscuro.
    assert preferencias.utiliza_modo_sistema() is False  # Comprueba que Niebla continúe interpretándose como elección manual.
    assert preferencias.tema() == TEMA_CLARO_NIEBLA  # Comprueba que la actualización no sobrescriba la decisión anterior del usuario.


def prueba_confirmar_mismo_tema_automatico_no_lo_vuelve_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo_preferencias_tema, "tema_recomendado_sistema", lambda: TEMA_OSCURO_TECNET)  # Simula el modo oscuro del sistema.
    preferencias = PreferenciasTema(tmp_path)  # Crea una instalación nueva todavía automática.
    assert preferencias.establecer_tema(TEMA_OSCURO_TECNET) is True  # Simula Aplicar después de modificar otra preferencia sin tocar el tema.
    assert preferencias.utiliza_modo_sistema() is True  # Comprueba que confirmar el mismo valor no cancele el seguimiento automático.


def prueba_elegir_otro_tema_crea_preferencia_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo_preferencias_tema, "tema_recomendado_sistema", lambda: TEMA_OSCURO_TECNET)  # Simula el modo oscuro predeterminado del sistema.
    preferencias = PreferenciasTema(tmp_path)  # Crea una preferencia automática.
    assert preferencias.establecer_tema(TEMA_OSCURO_MEDIANOCHE) is True  # Simula una elección explícita del usuario.
    assert preferencias.utiliza_modo_sistema() is False  # Comprueba que una variante distinta detenga el seguimiento automático.
    assert preferencias.tema() == TEMA_OSCURO_MEDIANOCHE  # Comprueba que la selección manual tenga prioridad desde ese momento.


def prueba_restablecer_recupera_seguimiento_del_sistema(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo_preferencias_tema, "tema_recomendado_sistema", lambda: TEMA_CLARO_TECNET)  # Simula un sistema en modo claro.
    preferencias = PreferenciasTema(tmp_path)  # Crea la preferencia temporal.
    assert preferencias.establecer_tema(TEMA_OSCURO_MEDIANOCHE) is True  # Fija primero una elección manual.
    assert preferencias.restablecer() is True  # Recupera después el comportamiento automático.
    assert preferencias.utiliza_modo_sistema() is True  # Comprueba que el origen vuelva a ser el sistema.
    assert preferencias.tema() == TEMA_CLARO_TECNET  # Comprueba que el modo claro del sistema vuelva a controlar la apariencia.

