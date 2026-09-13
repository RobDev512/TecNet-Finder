# ============================================================
# Archivo: prueba_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba que el catálogo central de diagnósticos
# conserve correctamente sus estados, severidades y etapas.
#
# Al finalizar el bloque funcional de U1, todas las reglas
# semánticas y ADV-005 deben figurar como disponibles.
# ============================================================

from Motor.diagnosticos import CATALOGO_DIAGNOSTICOS, ESTADO_DIAGNOSTICO_DISPONIBLE, codigo_diagnostico_disponible, codigo_diagnostico_es_error, crear_diagnostico, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes, texto_estado_diagnostico  # Importa el catálogo central y las consultas utilizadas por sus consumidores.


def prueba_catalogo_ya_no_conserva_diagnosticos_pendientes_de_u1():
    disponibles = obtener_codigos_diagnosticos_disponibles()
    pendientes = obtener_codigos_diagnosticos_pendientes()

    assert "SEM-006" in disponibles
    assert "ADV-005" in disponibles
    assert pendientes == []  # Confirma que el catálogo actual ya no contiene reglas reservadas de U1.


def prueba_sem001_a_sem006_figuran_como_disponibles_de_u1():
    for numero in range(1, 7):
        codigo = f"SEM-{numero:03d}"

        assert CATALOGO_DIAGNOSTICOS[codigo]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE
        assert CATALOGO_DIAGNOSTICOS[codigo]["etapa"] == "U1"
        assert codigo_diagnostico_disponible(codigo) is True
        assert texto_estado_diagnostico(codigo) == "Disponible"


def prueba_adv005_figura_como_advertencia_disponible_de_u1():
    informacion = CATALOGO_DIAGNOSTICOS["ADV-005"]

    assert informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE
    assert informacion["etapa"] == "U1"
    assert informacion["severidad"] == "advertencia"
    assert codigo_diagnostico_disponible("ADV-005") is True
    assert texto_estado_diagnostico("ADV-005") == "Disponible"


def prueba_catalogo_conserva_diagnosticos_anteriores_disponibles():
    assert CATALOGO_DIAGNOSTICOS["LEX-001"]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE
    assert texto_estado_diagnostico("LEX-001") == "Disponible"


def prueba_catalogo_distingue_errores_de_advertencias():
    assert codigo_diagnostico_es_error("LEX-001") is True
    assert codigo_diagnostico_es_error("SIN-002") is True
    assert codigo_diagnostico_es_error("SEM-006") is True
    assert codigo_diagnostico_es_error("ADV-005") is False
    assert codigo_diagnostico_es_error("ADV-007") is False


def prueba_crear_diagnostico_usa_severidad_predeterminada_del_catalogo():
    diagnostico = crear_diagnostico(
        codigo="ADV-005",
        mensaje="La red base posee mucha más capacidad de la necesaria.",
        linea=1,
        columna=20,
        fragmento="/8",
    )

    assert diagnostico.categoria == "Advertencia"
    assert diagnostico.severidad == "advertencia"
    assert diagnostico.solucion == CATALOGO_DIAGNOSTICOS["ADV-005"]["solucion"]