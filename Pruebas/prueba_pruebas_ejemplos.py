# ============================================================
# Archivo: prueba_pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el sistema automático encargado de
# ejecutar y evaluar los ejemplos de TecNet Finder.
#
# También ejecuta los archivos reales de la carpeta Ejemplos
# para detectar expectativas desactualizadas conforme avanza U1.
# ============================================================

from Motor.gestor_ejemplos import EjemploCodigo, GestorEjemplos  # Importa tanto la representación individual como el lector de los archivos reales.
from Motor.pruebas_ejemplos import ESTADO_CORRECTO, EjecutorPruebasEjemplos, extraer_codigos_esperados, generar_reporte_pruebas  # Importa el evaluador automático y sus utilidades.


def prueba_extrae_solamente_codigos_declarados_como_esperados():
    texto = (
        "Salida esperada: caso inválido. "
        "Códigos esperados: LEX-001, SIN-002, SEM-003, LEX-001, ADV-007. "
        "SEM-002 no se evalúa en este caso porque depende de otra condición."
    )

    codigos = extraer_codigos_esperados(texto)

    assert codigos == ["LEX-001", "SIN-002", "SEM-003", "ADV-007"]


def prueba_caso_valido_actual_genera_vlsm_y_pasa():
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


def prueba_caso_sintactico_invalido_pasa_si_aparece_codigo_esperado():
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


def prueba_sem006_ya_es_evaluable_y_pasa_si_aparece_codigo_esperado():
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="Redes traslapadas",
        comando=(
            "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
            "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"
        ),
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-006.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([ejemplo])
    resultado = resumen.resultados[0]

    assert resultado.estado == ESTADO_CORRECTO
    assert resultado.codigos_evaluables == ["SEM-006"]
    assert resultado.codigos_pendientes == []
    assert "SEM-006" in resultado.codigos_error
    assert resultado.bloques_validos == 1
    assert resultado.subredes_generadas == 1


def prueba_adv005_ya_es_evaluable_y_no_invalida_el_caso():
    ejemplo = EjemploCodigo(
        tipo="Válida",
        titulo="Red sobredimensionada",
        comando="IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-005.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([ejemplo])
    resultado = resumen.resultados[0]

    assert resultado.estado == ESTADO_CORRECTO
    assert resultado.codigos_evaluables == ["ADV-005"]
    assert resultado.codigos_pendientes == []
    assert "ADV-005" in resultado.codigos_advertencia
    assert resultado.codigos_error == []
    assert resultado.subredes_generadas == 1


def prueba_reporte_refleja_que_las_reglas_actuales_son_evaluables():
    valido = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central",
        salida_esperada="Salida esperada: caso válido.",
    )
    invalido_esperado = EjemploCodigo(
        tipo="Inválida",
        titulo="Traslape detectado",
        comando=(
            "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
            "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"
        ),
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-006.",
    )
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar([valido, invalido_esperado])
    reporte = generar_reporte_pruebas(resumen)

    assert "Total de casos probados: 2" in reporte
    assert "Casos correctos actualmente: 2" in reporte
    assert "Casos pendientes de fase futura: 0" in reporte
    assert "[CORRECTO] Caso válido" in reporte
    assert "[CORRECTO] Traslape detectado" in reporte


def prueba_archivos_reales_no_contienen_expectativas_actuales_fallidas():
    gestor = GestorEjemplos()
    validos, invalidos = gestor.cargar_ejemplos()
    ejecutor = EjecutorPruebasEjemplos()

    resumen = ejecutor.ejecutar(validos + invalidos)

    assert resumen.fallidos == 0  # Exige que todos los ejemplos correspondientes con características disponibles concuerden con el comportamiento real.