# ============================================================
# Archivo: prueba_barrida_final_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que los textos residuales de Configuración e IA
# existan en los seis catálogos y que la capa final traduzca
# correctamente mensajes estáticos y dinámicos.
# ============================================================

import json

from Interfaz.internacionalizacion.control_barrida_final import ControlBarridaFinal
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


CLAVES_BARRIDA = {
    "configuracion.fuentes.buscar",
    "comun.si",
    "comun.no",
    "configuracion.ia.confirmacion.instalar.titulo",
    "configuracion.ia.confirmacion.instalar.mensaje",
    "configuracion.ia.confirmacion.desinstalar.titulo",
    "configuracion.ia.confirmacion.desinstalar.mensaje",
    "configuracion.ia.progreso.preparando",
    "configuracion.ia.progreso.descargando_ollama",
    "configuracion.ia.progreso.descargando_modelo",
    "configuracion.ia.mensaje.instalada",
    "configuracion.ia.mensaje.desinstalada",
    "configuracion.ia.error.guardar_autocompletado",
    "configuracion.ia.error.guardar_diagnosticos",
    "configuracion.error.guardar_elemento",
}


def _control(idioma: str) -> ControlBarridaFinal:
    control = ControlBarridaFinal.__new__(ControlBarridaFinal)
    control.ventana = None
    control.gestor = GestorTraducciones(idioma)
    control._ventanas_preparadas = set()
    return control


def prueba_seis_catalogos_contienen_claves_de_barrida_final():
    gestor = GestorTraducciones("es")

    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = gestor.ruta_catalogos / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert CLAVES_BARRIDA.issubset(datos.keys())


def prueba_confirmacion_instalacion_se_traduce_a_ingles():
    control = _control("en")

    assert (
        control._traducir_texto_ia("Instalar asistencia de IA")
        == "Install AI assistance"
    )


def prueba_progreso_dinamico_ollama_conserva_version():
    control = _control("en")
    texto = control._traducir_texto_ia("Descargando Ollama 0.12.0...")

    assert texto == "Downloading Ollama 0.12.0..."


def prueba_error_dinamico_conserva_detalle_tecnico():
    control = _control("en")
    texto = control._traducir_texto_ia(
        "No fue posible preparar los archivos temporales de instalación: acceso denegado"
    )

    assert texto.startswith("The temporary installation files could not be prepared:")
    assert "acceso denegado" in texto
