# ============================================================
# Archivo: prueba_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el catálogo central de diagnósticos
# utilizado por TecNet Finder.
#
# Verifica que los códigos implementados estén disponibles,
# conserven la etapa y severidad correspondientes y puedan
# consultarse mediante las funciones auxiliares del catálogo.
#
# También comprueba que crear_diagnostico reutilice correctamente
# la información común definida para cada código.
# ============================================================

from Motor.compilacion.diagnosticos import CATALOGO_DIAGNOSTICOS, ESTADO_DIAGNOSTICO_DISPONIBLE, codigo_diagnostico_disponible, codigo_diagnostico_es_error, crear_diagnostico, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes, texto_estado_diagnostico  # Importa el catálogo central y todas las consultas públicas evaluadas por esta suite.


def prueba_catalogo_ya_no_conserva_diagnosticos_pendientes_de_u1():  # Comprueba que todas las reglas correspondientes con el cierre actual de Unidad 1 se encuentren disponibles.
    disponibles = obtener_codigos_diagnosticos_disponibles()  # Recupera todos los códigos que pueden producirse actualmente.
    pendientes = obtener_codigos_diagnosticos_pendientes()  # Recupera cualquier código reservado todavía para una fase futura.
    assert "SEM-009" in disponibles  # Confirma que la novena regla semántica ya forme parte del comportamiento actual.
    assert "ADV-009" in disponibles  # Confirma que la nueva advertencia de rango IPv4 especial también se encuentre activa.
    assert pendientes == []  # Verifica que el catálogo no mantenga reglas de Unidad 1 pendientes de implementación.


def prueba_sem001_a_sem009_figuran_como_disponibles_de_u1():  # Comprueba conjuntamente los nueve diagnósticos pertenecientes con el análisis semántico actual.
    for numero in range(1, 10):  # Recorre consecutivamente los identificadores comprendidos entre SEM-001 y SEM-009.
        codigo = f"SEM-{numero:03d}"  # Construye cada código oficial utilizando siempre tres dígitos numéricos.
        assert CATALOGO_DIAGNOSTICOS[codigo]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que cada regla se encuentre marcada como disponible.
        assert CATALOGO_DIAGNOSTICOS[codigo]["etapa"] == "U1"  # Comprueba que su procedencia académica permanezca registrada dentro de Unidad 1.
        assert codigo_diagnostico_disponible(codigo) is True  # Verifica también el resultado obtenido mediante la consulta pública del catálogo.
        assert texto_estado_diagnostico(codigo) == "Disponible"  # Confirma que la representación visible de cada estado sea coherente.


def prueba_nuevos_diagnosticos_semanticos_poseen_severidad_de_error():  # Comprueba que SEM-007, SEM-008 y SEM-009 sean reglas bloqueantes y no simples recomendaciones.
    assert CATALOGO_DIAGNOSTICOS["SEM-007"]["severidad"] == "error"  # Confirma que un octeto imposible invalide la dirección correspondiente.
    assert CATALOGO_DIAGNOSTICOS["SEM-008"]["severidad"] == "error"  # Confirma que la redefinición de una misma red base sea bloqueante.
    assert CATALOGO_DIAGNOSTICOS["SEM-009"]["severidad"] == "error"  # Confirma que reutilizar una IP base mediante otra máscara sea bloqueante.
    assert codigo_diagnostico_es_error("SEM-007") is True  # Comprueba la severidad de SEM-007 mediante la consulta pública.
    assert codigo_diagnostico_es_error("SEM-008") is True  # Comprueba la severidad de SEM-008 mediante la consulta pública.
    assert codigo_diagnostico_es_error("SEM-009") is True  # Comprueba la severidad de SEM-009 mediante la consulta pública.


def prueba_adv005_y_adv009_figuran_como_advertencias_disponibles_de_u1():  # Comprueba los metadatos principales de las advertencias asociadas directamente con decisiones de direccionamiento.
    assert CATALOGO_DIAGNOSTICOS["ADV-005"]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que la advertencia de sobredimensionamiento continúe habilitada.
    assert CATALOGO_DIAGNOSTICOS["ADV-005"]["etapa"] == "U1"  # Confirma que ADV-005 permanezca registrado dentro de Unidad 1.
    assert CATALOGO_DIAGNOSTICOS["ADV-005"]["severidad"] == "advertencia"  # Verifica que ADV-005 continúe siendo estrictamente informativo.
    assert CATALOGO_DIAGNOSTICOS["ADV-009"]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que la advertencia de rango especial ya se encuentre habilitada.
    assert CATALOGO_DIAGNOSTICOS["ADV-009"]["etapa"] == "U1"  # Confirma que ADV-009 se registre dentro del mismo cierre académico.
    assert CATALOGO_DIAGNOSTICOS["ADV-009"]["severidad"] == "advertencia"  # Verifica que utilizar un rango especial no se convierta accidentalmente en un error.
    assert codigo_diagnostico_disponible("ADV-009") is True  # Comprueba también la disponibilidad mediante la consulta pública utilizada por otros componentes.
    assert texto_estado_diagnostico("ADV-009") == "Disponible"  # Confirma que la representación visible del nuevo código sea coherente.


def prueba_catalogo_conserva_diagnosticos_anteriores_disponibles():  # Comprueba que las nuevas incorporaciones no hayan alterado los diagnósticos heredados de fases anteriores.
    assert CATALOGO_DIAGNOSTICOS["LEX-001"]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que el primer diagnóstico léxico continúe registrado como activo.
    assert texto_estado_diagnostico("LEX-001") == "Disponible"  # Comprueba que su representación visible continúe siendo correcta.


def prueba_catalogo_distingue_errores_de_advertencias():  # Comprueba que la consulta de severidad diferencie correctamente problemas bloqueantes y recomendaciones.
    assert codigo_diagnostico_es_error("LEX-001") is True  # Confirma que un problema léxico real continúe clasificado como error.
    assert codigo_diagnostico_es_error("SIN-002") is True  # Confirma que la ausencia sintáctica de MASK también sea bloqueante.
    assert codigo_diagnostico_es_error("SEM-006") is True  # Confirma que un traslape entre redes continúe siendo un error semántico.
    assert codigo_diagnostico_es_error("SEM-009") is True  # Confirma que el conflicto de IP base también sea un error.
    assert codigo_diagnostico_es_error("ADV-005") is False  # Confirma que el sobredimensionamiento permanezca como recomendación no bloqueante.
    assert codigo_diagnostico_es_error("ADV-007") is False  # Confirma que omitir NAME tampoco se convierta accidentalmente en un error.
    assert codigo_diagnostico_es_error("ADV-009") is False  # Confirma específicamente que un rango IPv4 especial continúe siendo utilizable.


def prueba_crear_diagnostico_usa_severidad_predeterminada_del_catalogo():  # Comprueba que la fábrica complete automáticamente la información común correspondiente con cada código.
    diagnostico = crear_diagnostico(codigo="ADV-005", mensaje="La red base posee mucha más capacidad de la necesaria.", linea=1, columna=20, fragmento="/8")  # Construye una aparición simulada sin proporcionar explícitamente su severidad.
    assert diagnostico.categoria == "Advertencia"  # Confirma que la categoría haya sido recuperada automáticamente desde el catálogo.
    assert diagnostico.severidad == "advertencia"  # Confirma que la fábrica utilice la severidad predeterminada correspondiente.
    assert diagnostico.solucion == CATALOGO_DIAGNOSTICOS["ADV-005"]["solucion"]  # Comprueba que la solución centralizada también se reutilice exactamente.