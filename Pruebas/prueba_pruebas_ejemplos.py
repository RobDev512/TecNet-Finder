# ============================================================
# Archivo: prueba_pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el sistema automático encargado de
# ejecutar y evaluar los ejemplos de TecNet Finder.
#
# Verifica diagnósticos actuales, advertencias recuperadas,
# expectativas futuras, generación VLSM y reporte general.
# ============================================================

from Motor.gestor_ejemplos import EjemploCodigo  # Importa la estructura utilizada por el selector y el ejecutor de pruebas.
from Motor.pruebas_ejemplos import ESTADO_CORRECTO, ESTADO_PENDIENTE, EjecutorPruebasEjemplos, extraer_codigos_esperados, generar_reporte_pruebas  # Importa el comportamiento real que debe comprobarse.


def prueba_extrae_codigos_esperados_sin_repetirlos():  # Comprueba que una salida esperada pueda contener distintas familias de diagnósticos.
    texto = "Códigos esperados: LEX-001, SIN-002, SEM-003, LEX-001, ADV-007."

    codigos = extraer_codigos_esperados(texto)

    assert codigos == ["LEX-001", "SIN-002", "SEM-003", "ADV-007"]


def prueba_caso_valido_actual_genera_vlsm_y_pasa():  # Comprueba una entrada completamente evaluable con las características disponibles.
    ejemplo = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina",
        salida_esperada="Salida esperada: caso válido. Códigos esperados: ninguno.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([ejemplo])
    resultado = resumen.resultados[0]

    assert resultado.estado == ESTADO_CORRECTO
    assert resultado.codigos_error == []
    assert resultado.bloques_validos == 1
    assert resultado.subredes_generadas == 3


def prueba_caso_sintactico_invalido_pasa_si_aparece_codigo_esperado():  # Comprueba que una entrada inválida apruebe cuando aparece el error solicitado.
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="Falta MASK",
        comando="IP 192.168.1.0 /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SIN-002.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([ejemplo])
    resultado = resumen.resultados[0]

    assert resultado.estado == ESTADO_CORRECTO
    assert "SIN-002" in resultado.codigos_obtenidos
    assert resultado.codigos_faltantes == []


def prueba_error_semantico_permanece_pendiente_antes_de_unidad_uno():  # Comprueba que SEM no provoque un falso fallo mientras la fase todavía no existe.
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="IP no alineada con la red",
        comando="IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-002.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([ejemplo])
    resultado = resumen.resultados[0]

    assert resultado.estado == ESTADO_PENDIENTE
    assert resultado.codigos_evaluables == []
    assert resultado.codigos_pendientes == ["SEM-002"]


def prueba_adv_recuperada_se_evalua_y_adv_005_permanece_pendiente():  # Distingue advertencias disponibles de la comprobación semántica todavía reservada.
    sin_nombre = EjemploCodigo(
        tipo="Válida",
        titulo="Sin nombre",
        comando="IP 192.168.2.0 MASK /24 HOSTS 100,50",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-007.",
    )
    red_sobredimensionada = EjemploCodigo(
        tipo="Válida",
        titulo="Red sobredimensionada",
        comando="IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-005.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([sin_nombre, red_sobredimensionada])
    resultado_nombre = resumen.resultados[0]
    resultado_sobredimensionada = resumen.resultados[1]

    assert resultado_nombre.estado == ESTADO_CORRECTO
    assert resultado_nombre.codigos_evaluables == ["ADV-007"]
    assert "ADV-007" in resultado_nombre.codigos_advertencia
    assert resultado_nombre.codigos_pendientes == []

    assert resultado_sobredimensionada.estado == ESTADO_CORRECTO
    assert resultado_sobredimensionada.codigos_evaluables == []
    assert resultado_sobredimensionada.codigos_pendientes == ["ADV-005"]


def prueba_reporte_distingue_correctos_y_pendientes():  # Comprueba que el texto final explique claramente los distintos estados.
    valido = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central",
        salida_esperada="Salida esperada: caso válido.",
    )
    pendiente = EjemploCodigo(
        tipo="Inválida",
        titulo="Caso semántico",
        comando="IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-002.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([valido, pendiente])
    reporte = generar_reporte_pruebas(resumen)

    assert "Total de casos probados: 2" in reporte
    assert "Casos correctos actualmente: 1" in reporte
    assert "Casos pendientes de fase futura: 1" in reporte
    assert "[CORRECTO] Caso válido" in reporte
    assert "[PENDIENTE] Caso semántico" in reporte