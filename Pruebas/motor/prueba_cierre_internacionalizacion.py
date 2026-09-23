# ============================================================
# Archivo: prueba_cierre_internacionalizacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba las traducciones utilizadas por el cierre visual de
# internacionalización sin depender de una interfaz gráfica.
# ============================================================

import json

from Interfaz.internacionalizacion.traductor_sintaxis import TraductorSintaxis
from Motor.compilacion.modelos import BloqueRed, NodoSintactico
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


CLAVES_CIERRE = {
    "sintaxis.gramatica.titulo",
    "sintaxis.gramatica.programa",
    "sintaxis.producciones.titulo",
    "sintaxis.producciones.entrada",
    "sintaxis.derivacion.titulo",
    "sintaxis.derivacion.bloque",
    "sintaxis.arbol.textual.titulo",
    "sintaxis.arbol.raiz_nombre",
    "configuracion.editor.descripcion",
    "configuracion.resultados.titulo",
    "configuracion.ia.estado.instalacion",
    "configuracion.ia.estado.ejecucion",
    "configuracion.tema.modo.oscuro",
    "configuracion.tema.modo.claro",
    "configuracion.tema.oscuro_oceano.nombre",
    "configuracion.tema.oscuro_oceano.descripcion",
    "configuracion.cambio.tema",
    "configuracion.cambio.idioma",
    "dialogos.entrada_vacia.titulo",
    "dialogos.entrada_vacia.mensaje",
    "dialogos.exportacion.completada_titulo",
    "dialogos.exportar_excel.completada",
    "dialogos.exportar_reporte.completada",
    "dialogos.arbol.guardar_titulo",
}


def prueba_seis_catalogos_contienen_claves_de_cierre():
    gestor = GestorTraducciones("es")

    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = gestor.ruta_catalogos / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert CLAVES_CIERRE.issubset(datos.keys())


def prueba_producciones_ingles_traducen_texto_pero_no_el_dsl():
    gestor = GestorTraducciones("en")
    traductor = TraductorSintaxis(gestor)
    bloque = BloqueRed(
        direccion_ip="192.168.1.0",
        mascara_subred="/24",
        cantidades_hosts=[50, 30, 10],
        nombre="Oficina",
    )

    texto = traductor.producciones([bloque])

    assert "=== BASE GRAMMAR ===" in texto
    assert "Complete program" in texto
    assert "--- Block 1 ---" in texto
    assert "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina" in texto
    assert "GRAMÁTICA BASE" not in texto


def prueba_derivacion_ingles_conserva_simbolos_formales():
    gestor = GestorTraducciones("en")
    traductor = TraductorSintaxis(gestor)
    bloque = BloqueRed(
        direccion_ip="10.0.0.0",
        mascara_subred="/24",
        cantidades_hosts=[20, 10],
        nombre="Central",
    )

    texto = traductor.derivacion([bloque])

    assert "=== GENERATED DERIVATION ===" in texto
    assert "--- Derivation of block 1 ---" in texto
    assert "IP_ADDRESS" in texto
    assert "SUBNET_MASK" in texto
    assert "HOSTS" in texto
    assert "NAME IDENTIFIER" in texto


def prueba_arbol_textual_traduce_solo_etiqueta_visual_de_raiz():
    gestor = GestorTraducciones("en")
    traductor = TraductorSintaxis(gestor)
    arbol = NodoSintactico(
        etiqueta="BloqueRed: Oficina",
        hijos=[
            NodoSintactico(
                etiqueta="IP",
                hijos=[NodoSintactico(etiqueta="VALOR", valor="IP")],
            ),
            NodoSintactico(etiqueta="HOSTS_LIST"),
            NodoSintactico(etiqueta="NAME"),
        ],
    )

    texto = traductor.arbol_textual([arbol])

    assert "=== TEXT REPRESENTATION OF THE SYNTAX TREE ===" in texto
    assert "Network: Oficina" in texto
    assert "HOSTS_LIST" in texto
    assert "NAME" in texto
    assert "BloqueRed" not in texto


def prueba_tema_ingles_resuelve_modo_variante_y_descripcion():
    gestor = GestorTraducciones("en")

    assert gestor.traducir("configuracion.tema.modo.oscuro") == "Dark"
    assert gestor.traducir("configuracion.tema.oscuro_oceano.nombre") == "Ocean"
    descripcion = gestor.traducir("configuracion.tema.oscuro_oceano.descripcion")
    assert "petroleum-blue" in descripcion
    assert "Tema oscuro" not in descripcion


def prueba_dialogos_finales_ingles_no_caen_en_espanol():
    gestor = GestorTraducciones("en")

    assert gestor.traducir("dialogos.entrada_vacia.titulo") == "Empty input"
    assert "before compiling" in gestor.traducir("dialogos.entrada_vacia.mensaje")
    assert gestor.traducir("dialogos.exportacion.completada_titulo") == "Export completed"
    assert "saved successfully" in gestor.traducir(
        "dialogos.exportar_excel.completada",
        ruta="C:/tmp/TecNetFinder_VLSM.xlsx",
    )
    assert gestor.traducir("dialogos.arbol.guardar_titulo") == "Save syntax tree"
    assert gestor.traducir("configuracion.cambio.tema") == "Application theme"
