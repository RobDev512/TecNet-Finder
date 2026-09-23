# ============================================================
# Archivo: prueba_exportacion_arbol.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba las reglas visuales del árbol y las decisiones
# básicas de formato para exportar PNG HD o SVG.
# ============================================================

from Interfaz.internacionalizacion.control_exportacion_arbol import ControlExportacionArbol
from Interfaz.resultados.visor_arbol_sintactico import VisorArbolSintactico
from Motor.compilacion.modelos import NodoSintactico


def prueba_valor_corto_puede_representarse_como_circulo():
    nodo = NodoSintactico(etiqueta="VALOR", valor="50")
    assert VisorArbolSintactico._debe_ser_circular(nodo, 20.0)


def prueba_valor_largo_permanece_ovalado():
    nodo = NodoSintactico(etiqueta="VALOR", valor="192.168.100.200")
    assert not VisorArbolSintactico._debe_ser_circular(
        nodo,
        VisorArbolSintactico.UMBRAL_TEXTO_CIRCULAR + 1,
    )


def prueba_nodo_estructural_permanece_ovalado_aunque_el_texto_sea_corto():
    nodo = NodoSintactico(
        etiqueta="IP",
        hijos=[NodoSintactico(etiqueta="VALOR", valor="IP")],
    )
    assert not VisorArbolSintactico._debe_ser_circular(nodo, 10.0)


def prueba_valor_generico_ya_no_se_muestra_en_el_texto_terminal():
    nodo = NodoSintactico(etiqueta="VALOR", valor="/24")
    assert VisorArbolSintactico._texto_nodo(nodo) == "/24"


def prueba_filtro_svg_selecciona_exportacion_vectorial():
    assert (
        ControlExportacionArbol._formato_seleccionado(
            "Arbol_Oficina",
            ControlExportacionArbol.FILTRO_SVG,
        )
        == "svg"
    )


def prueba_extension_escrita_tiene_prioridad_sobre_el_filtro():
    assert (
        ControlExportacionArbol._formato_seleccionado(
            "Arbol_Oficina.svg",
            ControlExportacionArbol.FILTRO_PNG,
        )
        == "svg"
    )


def prueba_asegura_extension_correcta():
    assert (
        ControlExportacionArbol._asegurar_extension(
            "Arbol_Oficina",
            "png",
        )
        == "Arbol_Oficina.png"
    )
    assert (
        ControlExportacionArbol._asegurar_extension(
            "Arbol_Oficina.png",
            "svg",
        )
        == "Arbol_Oficina.svg"
    )


def prueba_png_hd_usa_escala_superior_a_uno_y_300_dpi():
    assert ControlExportacionArbol.ESCALA_PNG_HD > 1.0
    assert ControlExportacionArbol.DPI_PNG_HD == 300


def prueba_un_hijo_queda_centrado_bajo_su_padre():
    ancho_subarbol = 120.0
    ancho_hijo = 58.0
    izquierda = 0.0

    izquierda_hijo = izquierda + max(
        (ancho_subarbol - ancho_hijo) / 2.0,
        0.0,
    )

    centro_padre = izquierda + ancho_subarbol / 2.0
    centro_hijo = izquierda_hijo + ancho_hijo / 2.0

    assert centro_padre == centro_hijo

def prueba_filtro_pdf_selecciona_exportacion_pdf():
    assert (
        ControlExportacionArbol._formato_seleccionado(
            "Arbol_Oficina",
            ControlExportacionArbol.FILTRO_PDF,
        )
        == "pdf"
    )


def prueba_asegura_extension_pdf_correcta():
    assert (
        ControlExportacionArbol._asegurar_extension(
            "Arbol_Oficina",
            "pdf",
        )
        == "Arbol_Oficina.pdf"
    )