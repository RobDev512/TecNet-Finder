# ============================================================
# Archivo: prueba_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba que el catálogo central de diagnósticos
# conserve correctamente sus estados, severidades y etapas.
#
# También verifica que las funciones consumidoras puedan
# distinguir códigos disponibles de códigos todavía pendientes.
# ============================================================

from Motor.diagnosticos import CATALOGO_DIAGNOSTICOS, ESTADO_DIAGNOSTICO_DISPONIBLE, ESTADO_DIAGNOSTICO_PENDIENTE, codigo_diagnostico_disponible, codigo_diagnostico_es_error, crear_diagnostico, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes, texto_estado_diagnostico  # Importa el catálogo central y las consultas que deben permanecer sincronizadas.


def prueba_catalogo_distingue_codigos_disponibles_y_pendientes():  # Comprueba que el catálogo refleje el alcance académico actual.
    disponibles = obtener_codigos_diagnosticos_disponibles()
    pendientes = obtener_codigos_diagnosticos_pendientes()

    assert "LEX-001" in disponibles
    assert "SIN-008" in disponibles
    assert "ADV-007" in disponibles
    assert "GEN-001" in disponibles

    assert "ADV-005" in pendientes
    assert "SEM-001" in pendientes
    assert "SEM-006" in pendientes


def prueba_estados_semanticos_permanecen_reservados_para_u1():  # Evita que el catálogo presente como implementada una fase que todavía no comienza.
    for numero in range(1, 7):
        codigo = f"SEM-{numero:03d}"

        assert (
            CATALOGO_DIAGNOSTICOS[codigo]["estado"]
            == ESTADO_DIAGNOSTICO_PENDIENTE
        )
        assert (
            CATALOGO_DIAGNOSTICOS[codigo]["etapa"]
            == "U1"
        )
        assert codigo_diagnostico_disponible(
            codigo
        ) is False
        assert texto_estado_diagnostico(
            codigo
        ) == "Pendiente U1"

    assert (
        CATALOGO_DIAGNOSTICOS["LEX-001"]["estado"]
        == ESTADO_DIAGNOSTICO_DISPONIBLE
    )
    assert texto_estado_diagnostico(
        "LEX-001"
    ) == "Disponible"


def prueba_catalogo_distingue_errores_de_advertencias():  # Comprueba que la severidad también provenga de una única fuente central.
    assert codigo_diagnostico_es_error(
        "LEX-001"
    ) is True

    assert codigo_diagnostico_es_error(
        "SIN-002"
    ) is True

    assert codigo_diagnostico_es_error(
        "SEM-002"
    ) is True

    assert codigo_diagnostico_es_error(
        "ADV-007"
    ) is False


def prueba_crear_diagnostico_usa_severidad_predeterminada_del_catalogo():  # Comprueba que una advertencia pueda construirse sin repetir manualmente su severidad.
    diagnostico = crear_diagnostico(
        codigo="ADV-007",
        mensaje="La instrucción no incluye un nombre de red.",
        linea=1,
        columna=30,
        fragmento="50",
    )

    assert diagnostico.categoria == "Advertencia"
    assert diagnostico.severidad == "advertencia"
    assert (
        diagnostico.solucion
        == CATALOGO_DIAGNOSTICOS["ADV-007"]["solucion"]
    )