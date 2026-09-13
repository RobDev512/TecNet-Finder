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
# distinguir códigos disponibles de códigos todavía pendientes
# conforme avanza la implementación de Lenguajes y Autómatas II.
# ============================================================

from Motor.diagnosticos import CATALOGO_DIAGNOSTICOS, ESTADO_DIAGNOSTICO_DISPONIBLE, ESTADO_DIAGNOSTICO_PENDIENTE, codigo_diagnostico_disponible, codigo_diagnostico_es_error, crear_diagnostico, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes, texto_estado_diagnostico  # Importa el catálogo central y las consultas que deben permanecer sincronizadas.


def prueba_catalogo_distingue_codigos_disponibles_y_pendientes():  # Comprueba que el catálogo refleje el alcance académico actualmente implementado.
    disponibles = obtener_codigos_diagnosticos_disponibles()  # Obtiene todos los códigos cuya lógica ya forma parte del programa.
    pendientes = obtener_codigos_diagnosticos_pendientes()  # Obtiene los códigos reservados para validaciones todavía no implementadas.

    assert "LEX-001" in disponibles  # Confirma que los diagnósticos léxicos implementados continúen disponibles.
    assert "SIN-008" in disponibles  # Confirma que los diagnósticos sintácticos implementados continúen disponibles.
    assert "SEM-001" in disponibles  # Confirma que la primera regla semántica continúe disponible.
    assert "SEM-002" in disponibles  # Confirma que la validación de dirección de red ya forme parte del comportamiento actual.
    assert "SEM-003" in disponibles  # Confirma que la validación de cantidades positivas ya forme parte del comportamiento actual.
    assert "ADV-007" in disponibles  # Confirma que las advertencias activas permanezcan disponibles.
    assert "GEN-001" in disponibles  # Confirma que el diagnóstico técnico de respaldo continúe habilitado.

    assert "ADV-005" in pendientes  # Confirma que la advertencia semántica todavía no implementada permanezca pendiente.
    assert "SEM-004" in pendientes  # Confirma que la siguiente regla de capacidad global continúe reservada.
    assert "SEM-005" in pendientes  # Confirma que la validación individual de capacidad continúe reservada.
    assert "SEM-006" in pendientes  # Confirma que la regla de traslape continúe reservada.
    assert "SEM-001" not in pendientes  # Evita que una regla disponible aparezca simultáneamente como pendiente.
    assert "SEM-002" not in pendientes  # Evita que SEM-002 mantenga un estado contradictorio.
    assert "SEM-003" not in pendientes  # Evita que SEM-003 mantenga un estado contradictorio.


def prueba_sem001_a_sem003_figuran_como_diagnosticos_disponibles_de_u1():  # Comprueba formalmente el estado de las tres reglas semánticas implementadas.
    for numero in range(1, 4):  # Recorre SEM-001, SEM-002 y SEM-003.
        codigo = f"SEM-{numero:03d}"  # Construye el identificador oficial de la regla evaluada.

        assert CATALOGO_DIAGNOSTICOS[codigo]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que la regla ya esté habilitada.
        assert CATALOGO_DIAGNOSTICOS[codigo]["etapa"] == "U1"  # Conserva la unidad académica correspondiente.
        assert codigo_diagnostico_disponible(codigo) is True  # Comprueba la consulta utilizada por consumidores del catálogo.
        assert texto_estado_diagnostico(codigo) == "Disponible"  # Comprueba la etiqueta visible que utilizará la interfaz.


def prueba_reglas_semanticas_restantes_permanecen_pendientes_en_u1():  # Evita presentar como implementadas reglas semánticas que todavía no existen.
    for numero in range(4, 7):  # Recorre SEM-004, SEM-005 y SEM-006.
        codigo = f"SEM-{numero:03d}"  # Construye el identificador oficial de cada diagnóstico pendiente.

        assert CATALOGO_DIAGNOSTICOS[codigo]["estado"] == ESTADO_DIAGNOSTICO_PENDIENTE  # Confirma que la regla todavía permanezca reservada.
        assert CATALOGO_DIAGNOSTICOS[codigo]["etapa"] == "U1"  # Confirma que la validación siga perteneciendo a la unidad semántica.
        assert codigo_diagnostico_disponible(codigo) is False  # Evita que consumidores del catálogo puedan tratarla como activa.
        assert texto_estado_diagnostico(codigo) == "Pendiente U1"  # Conserva la etiqueta adecuada mientras todavía no se implementa.


def prueba_catalogo_conserva_diagnosticos_anteriores_disponibles():  # Comprueba que el avance de U1 no altere los estados de las fases ya cerradas.
    assert CATALOGO_DIAGNOSTICOS["LEX-001"]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que el diagnóstico léxico permanezca habilitado.
    assert texto_estado_diagnostico("LEX-001") == "Disponible"  # Comprueba que su estado visible no cambie.


def prueba_catalogo_distingue_errores_de_advertencias():  # Comprueba que la severidad también provenga de una única fuente central.
    assert codigo_diagnostico_es_error("LEX-001") is True  # Confirma que los errores léxicos mantengan severidad de error.
    assert codigo_diagnostico_es_error("SIN-002") is True  # Confirma que los errores sintácticos mantengan severidad de error.
    assert codigo_diagnostico_es_error("SEM-001") is True  # Confirma que la primera regla semántica sea bloqueante.
    assert codigo_diagnostico_es_error("SEM-002") is True  # Confirma que una IP base incorrecta sea un error.
    assert codigo_diagnostico_es_error("SEM-003") is True  # Confirma que una cantidad no positiva sea un error.
    assert codigo_diagnostico_es_error("ADV-007") is False  # Confirma que una advertencia no sea clasificada como error.


def prueba_crear_diagnostico_usa_severidad_predeterminada_del_catalogo():  # Comprueba que una advertencia pueda construirse sin repetir manualmente su severidad.
    diagnostico = crear_diagnostico(
        codigo="ADV-007",
        mensaje="La instrucción no incluye un nombre de red.",
        linea=1,
        columna=30,
        fragmento="50",
    )  # Construye una advertencia usando únicamente los datos concretos de su aparición.

    assert diagnostico.categoria == "Advertencia"  # Comprueba que la categoría proceda correctamente del catálogo.
    assert diagnostico.severidad == "advertencia"  # Comprueba que crear_diagnostico recupere la severidad registrada.
    assert diagnostico.solucion == CATALOGO_DIAGNOSTICOS["ADV-007"]["solucion"]  # Comprueba que la solución oficial también proceda de la fuente central.