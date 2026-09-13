# ============================================================
# Archivo: prueba_pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el sistema automático encargado de
# ejecutar y evaluar los ejemplos de TecNet Finder.
#
# Verifica diagnósticos disponibles, análisis semántico,
# expectativas futuras, generación VLSM y reporte general.
# ============================================================

from Motor.gestor_ejemplos import EjemploCodigo  # Importa la estructura utilizada por el selector y el ejecutor de pruebas.
from Motor.pruebas_ejemplos import ESTADO_CORRECTO, ESTADO_PENDIENTE, EjecutorPruebasEjemplos, extraer_codigos_esperados, generar_reporte_pruebas  # Importa el comportamiento real que debe comprobarse.


def prueba_extrae_codigos_esperados_sin_repetirlos():  # Comprueba que una salida esperada pueda contener distintas familias de diagnósticos.
    texto = "Códigos esperados: LEX-001, SIN-002, SEM-003, LEX-001, ADV-007."  # Define una salida esperada con un diagnóstico repetido.

    codigos = extraer_codigos_esperados(texto)  # Extrae y normaliza los códigos utilizando el comportamiento real del ejecutor.

    assert codigos == ["LEX-001", "SIN-002", "SEM-003", "ADV-007"]  # Comprueba que cada código aparezca una sola vez y conserve su orden.


def prueba_caso_valido_actual_genera_vlsm_y_pasa():  # Comprueba una entrada completamente evaluable con las características disponibles.
    ejemplo = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina",
        salida_esperada="Salida esperada: caso válido. Códigos esperados: ninguno.",
    )  # Define un ejemplo que debe superar léxico, sintaxis, semántica y VLSM.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el componente encargado de evaluar automáticamente el ejemplo.

    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta únicamente el caso válido definido para esta prueba.
    resultado = resumen.resultados[0]  # Recupera el resultado individual generado por el ejecutor.

    assert resultado.estado == ESTADO_CORRECTO  # Confirma que la entrada completa sea considerada correcta.
    assert resultado.codigos_error == []  # Comprueba que ninguna fase formal produzca errores.
    assert resultado.bloques_validos == 1  # Confirma que el bloque también supere el análisis semántico.
    assert resultado.subredes_generadas == 3  # Comprueba que cada solicitud HOSTS produzca una subred VLSM.


def prueba_caso_sintactico_invalido_pasa_si_aparece_codigo_esperado():  # Comprueba que una entrada inválida apruebe cuando aparece el error solicitado.
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="Falta MASK",
        comando="IP 192.168.1.0 /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SIN-002.",
    )  # Define un error sintáctico cuya clasificación ya está disponible.
    ejecutor = EjecutorPruebasEjemplos()  # Crea un ejecutor independiente para este caso.

    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta el ejemplo inválido a través del flujo completo.
    resultado = resumen.resultados[0]  # Recupera el resultado individual.

    assert resultado.estado == ESTADO_CORRECTO  # Confirma que la prueba pase porque el error esperado sí apareció.
    assert "SIN-002" in resultado.codigos_obtenidos  # Comprueba que el parser haya producido el diagnóstico solicitado.
    assert resultado.codigos_faltantes == []  # Confirma que ninguna expectativa actual haya quedado sin cumplirse.


def prueba_sem002_ya_es_evaluable_y_pasa_si_aparece_codigo_esperado():  # Comprueba que el antiguo caso pendiente ya sea evaluable después de incorporar análisis semántico.
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="IP no alineada con la red",
        comando="IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-002.",
    )  # Define una IP sintácticamente válida que no representa la dirección base de su red.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el evaluador automático utilizado por el proyecto.

    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta la entrada utilizando SEM-002 ya disponible.
    resultado = resumen.resultados[0]  # Recupera el resultado correspondiente con el caso semántico.

    assert resultado.estado == ESTADO_CORRECTO  # Confirma que la prueba ahora pueda comprobarse completamente.
    assert resultado.codigos_evaluables == ["SEM-002"]  # Comprueba que SEM-002 ya pertenezca al alcance actual.
    assert resultado.codigos_pendientes == []  # Confirma que esta expectativa ya no esté reservada para el futuro.
    assert "SEM-002" in resultado.codigos_obtenidos  # Comprueba que el analizador semántico realmente produzca el código esperado.
    assert "SEM-002" in resultado.codigos_error  # Confirma que la regla continúe siendo bloqueante.
    assert resultado.bloques_validos == 0  # Comprueba que la instrucción sea descartada por análisis semántico.
    assert resultado.subredes_generadas == 0  # Confirma que el bloque rechazado nunca llegue al cálculo VLSM.


def prueba_adv_recuperada_se_evalua_y_adv_005_permanece_pendiente():  # Distingue advertencias disponibles de la comprobación semántica todavía reservada.
    sin_nombre = EjemploCodigo(
        tipo="Válida",
        titulo="Sin nombre",
        comando="IP 192.168.2.0 MASK /24 HOSTS 100,50",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-007.",
    )  # Define una advertencia disponible que debe comprobarse normalmente.
    red_sobredimensionada = EjemploCodigo(
        tipo="Válida",
        titulo="Red sobredimensionada",
        comando="IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-005.",
    )  # Define una expectativa válida cuya advertencia todavía no ha sido implementada.
    ejecutor = EjecutorPruebasEjemplos()  # Crea un único ejecutor para comprobar ambos estados en la misma ejecución.

    resumen = ejecutor.ejecutar([sin_nombre, red_sobredimensionada])  # Ejecuta consecutivamente los dos ejemplos.
    resultado_nombre = resumen.resultados[0]  # Recupera el caso correspondiente con ADV-007.
    resultado_sobredimensionada = resumen.resultados[1]  # Recupera el caso cuya advertencia ADV-005 sigue pendiente.

    assert resultado_nombre.estado == ESTADO_CORRECTO  # Confirma que una advertencia actual no invalide la entrada.
    assert resultado_nombre.codigos_evaluables == ["ADV-007"]  # Comprueba que ADV-007 ya pueda evaluarse.
    assert "ADV-007" in resultado_nombre.codigos_advertencia  # Comprueba que la advertencia esperada realmente aparezca.
    assert resultado_nombre.codigos_pendientes == []  # Confirma que el primer caso no dependa de trabajo futuro.

    assert resultado_sobredimensionada.estado == ESTADO_CORRECTO  # Confirma que una advertencia futura no convierta un caso válido en pendiente completo.
    assert resultado_sobredimensionada.codigos_evaluables == []  # Confirma que ADV-005 todavía no deba exigirse.
    assert resultado_sobredimensionada.codigos_pendientes == ["ADV-005"]  # Conserva ADV-005 como expectativa futura de U1.


def prueba_reporte_distingue_correctos_y_pendientes():  # Comprueba que el reporte siga diferenciando reglas actuales de reglas semánticas todavía pendientes.
    valido = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central",
        salida_esperada="Salida esperada: caso válido.",
    )  # Define una instrucción completamente evaluable con las reglas actuales.
    pendiente = EjemploCodigo(
        tipo="Inválida",
        titulo="Capacidad total pendiente",
        comando="IP 192.168.1.0 MASK /24 HOSTS 100,100,100 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-004.",
    )  # Utiliza SEM-004 para conservar un ejemplo cuya invalidez todavía depende de una regla futura.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el evaluador utilizado para generar el reporte conjunto.

    resumen = ejecutor.ejecutar([valido, pendiente])  # Ejecuta un ejemplo completamente actual y otro todavía pendiente.
    reporte = generar_reporte_pruebas(resumen)  # Convierte los resultados obtenidos en el reporte textual del sistema.

    assert "Alcance actual: análisis léxico, análisis sintáctico, análisis semántico" in reporte  # Comprueba que el reporte ya reconozca formalmente la incorporación de U1.
    assert "Total de casos probados: 2" in reporte  # Comprueba que ambos ejemplos formen parte del resumen.
    assert "Casos correctos actualmente: 1" in reporte  # Confirma que únicamente la entrada completamente evaluable cuente como correcta.
    assert "Casos pendientes de fase futura: 1" in reporte  # Confirma que SEM-004 mantenga un caso reservado para trabajo posterior.
    assert "[CORRECTO] Caso válido" in reporte  # Comprueba la etiqueta del ejemplo que supera las fases disponibles.
    assert "[PENDIENTE] Capacidad total pendiente" in reporte  # Comprueba que la regla futura continúe representada correctamente.