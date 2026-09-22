# ============================================================
# Archivo: prueba_traductor_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
# ============================================================

import json

from Interfaz.internacionalizacion.traductor_diagnosticos import TraductorDiagnosticos
from Motor.compilacion.diagnosticos import CATALOGO_DIAGNOSTICOS, Diagnostico
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


def prueba_todos_los_codigos_tienen_tres_textos_en_los_seis_catalogos():
    gestor = GestorTraducciones("es")
    for idioma in ("es", "en", "pt", "fr", "de", "la"):
        datos = json.loads((gestor.ruta_catalogos / f"{idioma}.json").read_text(encoding="utf-8"))
        for codigo in CATALOGO_DIAGNOSTICOS:
            assert f"diagnosticos.codigo.{codigo}.nombre" in datos
            assert f"diagnosticos.codigo.{codigo}.descripcion" in datos
            assert f"diagnosticos.codigo.{codigo}.solucion" in datos


def prueba_ingles_traduce_catalogo_y_conserva_reservadas_del_dsl():
    gestor = GestorTraducciones("en")
    traductor = TraductorDiagnosticos(gestor)
    assert traductor.categoria("Sintáctico") == "Syntactic"
    assert traductor.nombre("SIN-002") == "Missing reserved word MASK"
    solucion = traductor.solucion("SIN-008")
    for reservada in ("IP", "MASK", "HOSTS", "NAME"):
        assert reservada in solucion


def prueba_espanol_conserva_mensaje_contextual_original():
    gestor = GestorTraducciones("es")
    traductor = TraductorDiagnosticos(gestor)
    diagnostico = Diagnostico(
        codigo="SEM-007",
        categoria="Semántico",
        severidad="error",
        mensaje="El octeto 256 está fuera de rango.",
        fragmento="256",
        solucion="Corrige el octeto.",
    )
    assert traductor.mensaje(diagnostico) == "El octeto 256 está fuera de rango."


def prueba_idioma_secundario_usa_descripcion_traducida_y_fragmento():
    gestor = GestorTraducciones("en")
    traductor = TraductorDiagnosticos(gestor)
    diagnostico = Diagnostico(
        codigo="SEM-007",
        categoria="Semántico",
        severidad="error",
        mensaje="El octeto 256 está fuera de rango.",
        fragmento="256",
        solucion="Corrige el octeto.",
    )
    texto = traductor.mensaje(diagnostico)
    assert "IPv4 octet outside range" in traductor.nombre("SEM-007")
    assert "256" in texto
    assert "Fragment" in texto


def prueba_estado_disponible_se_traduce_sin_modificar_codigo():
    gestor = GestorTraducciones("de")
    traductor = TraductorDiagnosticos(gestor)
    assert traductor.estado("LEX-001") == "Verfügbar"
    assert "LEX-001" in CATALOGO_DIAGNOSTICOS
