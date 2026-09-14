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

from Motor.diagnosticos import CATALOGO_DIAGNOSTICOS, ESTADO_DIAGNOSTICO_DISPONIBLE, codigo_diagnostico_disponible, codigo_diagnostico_es_error, crear_diagnostico, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes, texto_estado_diagnostico  # Importa el catálogo central y todas las consultas evaluadas por estas pruebas.


def prueba_catalogo_ya_no_conserva_diagnosticos_pendientes_de_u1():  # Comprueba que todas las reglas correspondientes con Unidad 1 ya estén implementadas.
    disponibles = obtener_codigos_diagnosticos_disponibles()  # Recupera los códigos que pueden producirse actualmente.
    pendientes = obtener_codigos_diagnosticos_pendientes()  # Recupera cualquier código que todavía haya quedado reservado para una fase futura.
    assert "SEM-006" in disponibles  # Confirma que la comprobación de redes base traslapadas ya forma parte del comportamiento actual.
    assert "ADV-005" in disponibles  # Confirma que la advertencia de sobredimensionamiento también se encuentra disponible.
    assert pendientes == []  # Confirma que el catálogo actual no conserva ninguna regla pendiente de U1.


def prueba_sem001_a_sem006_figuran_como_disponibles_de_u1():  # Comprueba conjuntamente los seis diagnósticos pertenecientes al análisis semántico actual.
    for numero in range(1, 7):  # Recorre consecutivamente SEM-001, SEM-002, SEM-003, SEM-004, SEM-005 y SEM-006.
        codigo = f"SEM-{numero:03d}"  # Construye el identificador oficial conservando siempre tres dígitos.
        assert CATALOGO_DIAGNOSTICOS[codigo]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que la regla ya pueda ser producida por TecNet Finder.
        assert CATALOGO_DIAGNOSTICOS[codigo]["etapa"] == "U1"  # Comprueba que su procedencia académica permanezca registrada como Unidad 1.
        assert codigo_diagnostico_disponible(codigo) is True  # Comprueba también la consulta pública utilizada por otros componentes.
        assert texto_estado_diagnostico(codigo) == "Disponible"  # Confirma que la representación visible del estado sea coherente con el catálogo.


def prueba_adv005_figura_como_advertencia_disponible_de_u1():  # Comprueba individualmente los metadatos correspondientes con ADV-005.
    informacion = CATALOGO_DIAGNOSTICOS["ADV-005"]  # Recupera directamente la definición registrada para la advertencia de sobredimensionamiento.
    assert informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que la advertencia ya se encuentre habilitada.
    assert informacion["etapa"] == "U1"  # Confirma que se mantenga registrada dentro del trabajo realizado en Unidad 1.
    assert informacion["severidad"] == "advertencia"  # Verifica que nunca se trate como un error bloqueante.
    assert codigo_diagnostico_disponible("ADV-005") is True  # Comprueba la misma disponibilidad mediante la función pública.
    assert texto_estado_diagnostico("ADV-005") == "Disponible"  # Confirma que la interfaz pueda mostrar correctamente su estado.


def prueba_catalogo_conserva_diagnosticos_anteriores_disponibles():  # Comprueba que las incorporaciones nuevas no hayan alterado diagnósticos heredados de fases anteriores.
    assert CATALOGO_DIAGNOSTICOS["LEX-001"]["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE  # Confirma que el primer diagnóstico léxico continúa registrado como activo.
    assert texto_estado_diagnostico("LEX-001") == "Disponible"  # Confirma que su representación visible siga siendo correcta.


def prueba_catalogo_distingue_errores_de_advertencias():  # Comprueba que la consulta de severidad diferencie correctamente códigos bloqueantes y recomendaciones.
    assert codigo_diagnostico_es_error("LEX-001") is True  # Confirma que un problema léxico se clasifique como error.
    assert codigo_diagnostico_es_error("SIN-002") is True  # Confirma que la ausencia sintáctica de MASK también sea bloqueante.
    assert codigo_diagnostico_es_error("SEM-006") is True  # Confirma que dos redes traslapadas produzcan un error semántico real.
    assert codigo_diagnostico_es_error("ADV-005") is False  # Confirma que el sobredimensionamiento permanezca como una recomendación.
    assert codigo_diagnostico_es_error("ADV-007") is False  # Confirma que omitir NAME tampoco se convierta accidentalmente en error.


def prueba_crear_diagnostico_usa_severidad_predeterminada_del_catalogo():  # Comprueba que la fábrica complete automáticamente la información común correspondiente con cada código.
    diagnostico = crear_diagnostico(
        codigo="ADV-005",  # Solicita específicamente la advertencia relacionada con una red base demasiado grande.
        mensaje="La red base posee mucha más capacidad de la necesaria.",  # Proporciona el mensaje concreto correspondiente con esta aparición.
        linea=1,  # Relaciona el diagnóstico de prueba con la primera línea.
        columna=20,  # Proporciona una posición simulada dentro de la instrucción.
        fragmento="/8",  # Conserva como referencia la máscara responsable del dimensionamiento.
    )  # Construye el objeto utilizando los metadatos centrales registrados para ADV-005.
    assert diagnostico.categoria == "Advertencia"  # Confirma que la categoría haya sido recuperada automáticamente desde el catálogo.
    assert diagnostico.severidad == "advertencia"  # Confirma que la fábrica utilice la severidad predeterminada cuando no se proporciona otra.
    assert diagnostico.solucion == CATALOGO_DIAGNOSTICOS["ADV-005"]["solucion"]  # Confirma que también reutilice exactamente la solución centralizada.