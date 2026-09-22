# ============================================================
# Archivo: prueba_idioma_ventana_principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que los seis catálogos incluyan las claves mínimas
# utilizadas para traducir la ventana principal.
# ============================================================

import json

from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


CLAVES_PRINCIPALES = {
    "principal.subtitulo",
    "principal.estado.neutral",
    "principal.estado.errores",
    "principal.estado.advertencias",
    "principal.estado.correcto",
    "principal.pestana.entrada_salida",
    "principal.pestana.tablas",
    "principal.salida.resumen",
    "principal.salida.vlsm",
    "principal.accion.compilar",
    "principal.accion.limpiar",
    "principal.editor.ampliar",
    "principal.editor.ejemplos",
    "principal.barra.configuracion",
    "principal.barra.elegir_modo",
    "principal.selector.izquierda",
    "principal.selector.derecha",
    "principal.selector.modo_ventana",
    "principal.selector.maximizar",
    "principal.vlsm.red",
    "diagnosticos.detectados",
    "diagnosticos.catalogo",
    "diagnosticos.codigo",
    "diagnosticos.solucion",
}


def prueba_seis_catalogos_contienen_claves_de_ventana_principal():
    gestor = GestorTraducciones("es")
    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = gestor.ruta_catalogos / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert CLAVES_PRINCIPALES.issubset(datos.keys())


def prueba_ingles_resuelve_textos_principales_sin_respaldo():
    gestor = GestorTraducciones("en")
    assert gestor.traducir("principal.subtitulo") == "Compiler for VLSM instruction analysis"
    assert gestor.traducir("principal.pestana.entrada_salida") == "Input / Output"
    assert gestor.traducir("principal.accion.compilar") == "Compile"
    assert gestor.traducir("diagnosticos.catalogo") == "Catalog"


def prueba_palabras_reservadas_del_dsl_no_forman_parte_de_las_claves_visuales():
    gestor = GestorTraducciones("en")
    textos = [
        gestor.traducir("principal.subtitulo"),
        gestor.traducir("principal.accion.compilar"),
        gestor.traducir("principal.pestana.entrada_salida"),
    ]
    assert all(texto not in ("IP", "MASK", "HOSTS", "NAME") for texto in textos)
