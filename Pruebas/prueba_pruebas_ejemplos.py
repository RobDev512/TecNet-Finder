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
#
# También ejecuta los archivos reales de la carpeta Ejemplos
# para detectar expectativas desactualizadas cuando una regla
# pendiente pasa a estar disponible.
# ============================================================

from Motor.gestor_ejemplos import EjemploCodigo, GestorEjemplos  # Importa la estructura de cada ejemplo y el lector de los archivos reales del proyecto.
from Motor.pruebas_ejemplos import ESTADO_CORRECTO, ESTADO_PENDIENTE, EjecutorPruebasEjemplos, extraer_codigos_esperados, generar_reporte_pruebas  # Importa el comportamiento real utilizado para evaluar ejemplos y generar reportes.


def prueba_extrae_solamente_codigos_declarados_como_esperados():  # Comprueba que códigos explicativos posteriores no se confundan con expectativas formales.
    texto = (
        "Salida esperada: caso inválido. "
        "Códigos esperados: LEX-001, SIN-002, SEM-003, LEX-001, ADV-007. "
        "SEM-002 no se evalúa en este caso porque depende de otra condición."
    )  # Incluye deliberadamente SEM-002 fuera de la declaración para reproducir el problema encontrado en I20.

    codigos = extraer_codigos_esperados(texto)  # Extrae únicamente los identificadores situados dentro de la declaración formal.

    assert codigos == ["LEX-001", "SIN-002", "SEM-003", "ADV-007"]  # Confirma que SEM-002 explicativo sea ignorado y que los repetidos se eliminen.


def prueba_caso_valido_actual_genera_vlsm_y_pasa():  # Comprueba una entrada completamente evaluable con las características disponibles.
    ejemplo = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina",
        salida_esperada="Salida esperada: caso válido. Códigos esperados: ninguno.",
    )  # Define una instrucción que debe superar todas las fases actualmente conectadas.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el componente encargado de ejecutar el ejemplo mediante el flujo real.

    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta únicamente el caso preparado para esta prueba.
    resultado = resumen.resultados[0]  # Recupera el resultado individual producido por el ejecutor.

    assert resultado.estado == ESTADO_CORRECTO  # Confirma que la entrada sea considerada correcta.
    assert resultado.codigos_error == []  # Comprueba que ninguna fase produzca errores.
    assert resultado.bloques_validos == 1  # Confirma que el bloque supere también las reglas semánticas disponibles.
    assert resultado.subredes_generadas == 3  # Comprueba que las tres solicitudes HOSTS produzcan sus respectivas subredes.


def prueba_caso_sintactico_invalido_pasa_si_aparece_codigo_esperado():  # Comprueba que una prueba inválida sea correcta cuando aparece exactamente el diagnóstico esperado.
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="Falta MASK",
        comando="IP 192.168.1.0 /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SIN-002.",
    )  # Define una instrucción cuya estructura carece de la palabra reservada MASK.
    ejecutor = EjecutorPruebasEjemplos()  # Crea un ejecutor independiente para comprobar el caso sintáctico.

    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta el ejemplo mediante el mismo flujo utilizado por TecNet Finder.
    resultado = resumen.resultados[0]  # Recupera el resultado correspondiente con la entrada inválida.

    assert resultado.estado == ESTADO_CORRECTO  # Confirma que la prueba pase porque el error esperado sí fue producido.
    assert "SIN-002" in resultado.codigos_obtenidos  # Comprueba que el parser genere la clasificación declarada.
    assert resultado.codigos_faltantes == []  # Confirma que ninguna expectativa evaluable haya quedado ausente.


def prueba_sem002_ya_es_evaluable_y_pasa_si_aparece_codigo_esperado():  # Comprueba que SEM-002 forme parte efectiva del alcance actual.
    ejemplo = EjemploCodigo(
        tipo="Inválida",
        titulo="IP no alineada con la red",
        comando="IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina",
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-002.",
    )  # Define una dirección IPv4 válida que no corresponde con la dirección de red del prefijo indicado.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el evaluador automático empleado por los ejemplos del proyecto.

    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta la entrada utilizando el análisis semántico actual.
    resultado = resumen.resultados[0]  # Recupera la evaluación individual de SEM-002.

    assert resultado.estado == ESTADO_CORRECTO  # Confirma que la expectativa semántica ya pueda comprobarse completamente.
    assert resultado.codigos_evaluables == ["SEM-002"]  # Comprueba que SEM-002 esté disponible según el catálogo.
    assert resultado.codigos_pendientes == []  # Confirma que la regla ya no dependa de trabajo futuro.
    assert "SEM-002" in resultado.codigos_obtenidos  # Comprueba que el analizador produzca el diagnóstico esperado.
    assert "SEM-002" in resultado.codigos_error  # Confirma que la regla mantenga severidad bloqueante.
    assert resultado.bloques_validos == 0  # Comprueba que la instrucción sea descartada por análisis semántico.
    assert resultado.subredes_generadas == 0  # Confirma que una IP base incorrecta no alcance el cálculo VLSM.


def prueba_adv_recuperada_se_evalua_y_adv_005_permanece_pendiente():  # Distingue una advertencia disponible de otra reservada todavía para U1.
    sin_nombre = EjemploCodigo(
        tipo="Válida",
        titulo="Sin nombre",
        comando="IP 192.168.2.0 MASK /24 HOSTS 100,50",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-007.",
    )  # Define una entrada válida cuya advertencia por ausencia de NAME ya está disponible.
    red_sobredimensionada = EjemploCodigo(
        tipo="Válida",
        titulo="Red sobredimensionada",
        comando="IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada",
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-005.",
    )  # Define una entrada válida cuya advertencia de capacidad sobrada todavía no ha sido implementada.
    ejecutor = EjecutorPruebasEjemplos()  # Crea un único ejecutor para comparar ambos estados del catálogo.

    resumen = ejecutor.ejecutar([sin_nombre, red_sobredimensionada])  # Ejecuta consecutivamente las dos entradas preparadas.
    resultado_nombre = resumen.resultados[0]  # Recupera el caso correspondiente con ADV-007.
    resultado_sobredimensionada = resumen.resultados[1]  # Recupera el caso correspondiente con la expectativa futura ADV-005.

    assert resultado_nombre.estado == ESTADO_CORRECTO  # Confirma que una advertencia disponible no invalide la instrucción.
    assert resultado_nombre.codigos_evaluables == ["ADV-007"]  # Comprueba que ADV-007 ya pueda exigirse.
    assert "ADV-007" in resultado_nombre.codigos_advertencia  # Comprueba que la advertencia esperada realmente aparezca.
    assert resultado_nombre.codigos_pendientes == []  # Confirma que el primer ejemplo no dependa de reglas futuras.

    assert resultado_sobredimensionada.estado == ESTADO_CORRECTO  # Confirma que una advertencia futura no convierta el caso válido en un fallo.
    assert resultado_sobredimensionada.codigos_evaluables == []  # Comprueba que ADV-005 todavía no forme parte de la evaluación obligatoria.
    assert resultado_sobredimensionada.codigos_pendientes == ["ADV-005"]  # Conserva la advertencia como una expectativa futura.


def prueba_reporte_distingue_correctos_y_pendientes():  # Comprueba que el reporte diferencie correctamente las características disponibles de SEM-006 todavía pendiente.
    valido = EjemploCodigo(
        tipo="Válida",
        titulo="Caso válido",
        comando="IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central",
        salida_esperada="Salida esperada: caso válido.",
    )  # Define una entrada que puede evaluarse completamente con la versión actual.
    pendiente = EjemploCodigo(
        tipo="Inválida",
        titulo="Traslape pendiente",
        comando=(
            "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
            "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"
        ),
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-006.",
    )  # Define dos redes traslapadas cuya regla todavía permanece pendiente.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el componente utilizado para construir el resumen y el reporte.

    resumen = ejecutor.ejecutar([valido, pendiente])  # Ejecuta tanto el caso actual como la expectativa futura.
    reporte = generar_reporte_pruebas(resumen)  # Convierte los resultados estructurados en el texto mostrado por el sistema.

    assert "Alcance actual: análisis léxico, análisis sintáctico, análisis semántico" in reporte  # Confirma que el reporte incluya formalmente la fase de U1.
    assert "Total de casos probados: 2" in reporte  # Comprueba que ambos ejemplos hayan sido procesados.
    assert "Casos correctos actualmente: 1" in reporte  # Confirma que solamente el ejemplo completamente actual se clasifique como correcto.
    assert "Casos pendientes de fase futura: 1" in reporte  # Comprueba que SEM-006 siga representándose como trabajo pendiente.
    assert "[CORRECTO] Caso válido" in reporte  # Confirma la etiqueta visible del primer ejemplo.
    assert "[PENDIENTE] Traslape pendiente" in reporte  # Confirma la etiqueta correspondiente con la regla aún no implementada.


def prueba_archivos_reales_no_contienen_expectativas_actuales_fallidas():  # Ejecuta todos los ejemplos académicos para detectar expectativas que hayan quedado obsoletas.
    gestor = GestorEjemplos()  # Crea el lector real encargado de recuperar los ejemplos incluidos con TecNet Finder.
    validos, invalidos = gestor.cargar_ejemplos()  # Carga directamente las dos colecciones almacenadas dentro de la carpeta Ejemplos.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el evaluador que utiliza el catálogo y el flujo de compilación reales.

    resumen = ejecutor.ejecutar(validos + invalidos)  # Ejecuta conjuntamente todos los casos incluidos actualmente con el proyecto.

    assert resumen.fallidos == 0  # Exige que ninguna expectativa ya evaluable contradiga el comportamiento real del compilador.