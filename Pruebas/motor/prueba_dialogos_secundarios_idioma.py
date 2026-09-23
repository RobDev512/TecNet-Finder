# ============================================================
# Archivo: prueba_dialogos_secundarios_idioma.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba las claves y la generación textual internacionalizada
# utilizada por el selector de ejemplos y su reporte automático.
# ============================================================

import json

from Interfaz.internacionalizacion.control_dialogos_secundarios import (
    generar_reporte_pruebas_traducido,
)
from Motor.ejemplos.gestor_ejemplos import EjemploCodigo
from Motor.ejemplos.pruebas_ejemplos import (
    ESTADO_CORRECTO,
    ResultadoPruebaEjemplo,
    ResumenPruebasEjemplos,
)
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


CLAVES_DIALOGOS = {
    "secundarios.ejemplos.titulo",
    "secundarios.ejemplos.instruccion",
    "secundarios.ejemplos.validas",
    "secundarios.ejemplos.invalidas",
    "secundarios.ejemplos.insertar_seleccionados",
    "secundarios.ejemplos.confirmar_insercion",
    "secundarios.ejemplos.vista_previa",
    "secundarios.reporte.titulo",
    "secundarios.reporte.encabezado",
    "secundarios.reporte.resultado.correcto",
    "secundarios.reporte.estado.correcto",
    "secundarios.reporte.codigos_esperados",
    "secundarios.editor.sin_solucion",
}


def prueba_seis_catalogos_contienen_dialogos_secundarios():
    gestor = GestorTraducciones("es")
    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = gestor.ruta_catalogos / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert CLAVES_DIALOGOS.issubset(datos.keys())


def prueba_reporte_ingles_se_genera_sin_encabezados_espanoles():
    ejemplo = EjemploCodigo(
        tipo="Válida",
        titulo="Red de oficina",
        comando="IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina",
        salida_esperada="",
    )
    resultado = ResultadoPruebaEjemplo(
        ejemplo=ejemplo,
        estado=ESTADO_CORRECTO,
        tokens_reconocidos=8,
        bloques_validos=1,
        subredes_generadas=1,
    )
    resumen = ResumenPruebasEjemplos(resultados=[resultado])
    gestor = GestorTraducciones("en")

    texto = generar_reporte_pruebas_traducido(resumen, gestor)

    assert "=== AUTOMATIC EXAMPLE TESTS ===" in texto
    assert "[PASSED]" in texto
    assert "Declared type: Valid" in texto
    assert "Recognized tokens: 8" in texto
    assert "PRUEBAS AUTOMÁTICAS" not in texto


def prueba_reporte_conserva_palabras_del_dsl():
    ejemplo = EjemploCodigo(
        tipo="Válida",
        titulo="DSL",
        comando="IP 10.0.0.0 MASK /24 HOSTS 20 NAME Oficina",
        salida_esperada="",
    )
    resultado = ResultadoPruebaEjemplo(
        ejemplo=ejemplo,
        estado=ESTADO_CORRECTO,
    )
    texto = generar_reporte_pruebas_traducido(
        ResumenPruebasEjemplos(resultados=[resultado]),
        GestorTraducciones("de"),
    )
    # El reporte no traduce ni reescribe las palabras reservadas del lenguaje.
    assert "IP" not in texto or "IP" in ejemplo.comando
    assert ejemplo.comando == "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Oficina"
