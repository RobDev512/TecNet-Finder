# ============================================================
# Archivo: prueba_pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el sistema automático encargado de
# ejecutar y evaluar los ejemplos incluidos con TecNet Finder.
#
# Verifica:
#
# - Extracción de códigos declarados como esperados.
# - Ejecución de ejemplos válidos e inválidos.
# - Comparación entre códigos esperados y obtenidos.
# - Evaluación de diagnósticos actuales.
# - Generación del reporte general de pruebas.
# - Consistencia de los archivos reales de la carpeta Ejemplos.
#
# De esta manera, los ejemplos del programa también funcionan
# como una comprobación automática contra cambios accidentales.
# ============================================================

from Motor.ejemplos.gestor_ejemplos import EjemploCodigo, GestorEjemplos  # Proporciona tanto la representación de un ejemplo como el lector de los archivos TXT reales.
from Motor.ejemplos.pruebas_ejemplos import ESTADO_CORRECTO, EjecutorPruebasEjemplos, extraer_codigos_esperados, generar_reporte_pruebas  # Proporciona el evaluador automático y las utilidades empleadas por estas pruebas.


def prueba_extrae_solamente_codigos_declarados_como_esperados():  # Comprueba que solamente se interpreten códigos escritos después de la etiqueta formal correspondiente.
    texto = (
        "Salida esperada: caso inválido. "  # Incluye texto descriptivo que no debe afectar la extracción.
        "Códigos esperados: LEX-001, SIN-002, SEM-003, LEX-001, ADV-007. "  # Declara varios códigos e incluye deliberadamente LEX-001 dos veces.
        "SEM-002 no se evalúa en este caso porque depende de otra condición."  # Menciona otro código fuera de la declaración para comprobar que sea ignorado.
    )  # Construye una descripción semejante con las utilizadas dentro de los archivos reales.
    codigos = extraer_codigos_esperados(texto)  # Extrae únicamente códigos pertenecientes a la declaración formal Códigos esperados.
    assert codigos == ["LEX-001", "SIN-002", "SEM-003", "ADV-007"]  # Confirma que se ignore SEM-002 y que la aparición duplicada de LEX-001 se conserve una sola vez.


def prueba_caso_valido_actual_genera_vlsm_y_pasa():  # Comprueba que un ejemplo válido actual sea clasificado correctamente y produzca sus resultados VLSM.
    ejemplo = EjemploCodigo(
        tipo="Válida",  # Declara formalmente que este ejemplo no debería producir errores.
        titulo="Caso válido",  # Proporciona un nombre identificable dentro del resumen.
        comando="IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina",  # Utiliza una instrucción completa y semánticamente correcta.
        salida_esperada="Salida esperada: caso válido. Códigos esperados: ninguno.",  # Declara explícitamente que no se espera ningún diagnóstico.
    )  # Construye un caso equivalente con los cargados desde entrada_valida.txt.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el componente encargado de utilizar FlujoCompilacion sobre el ejemplo.
    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta una colección compuesta únicamente por este caso.
    resultado = resumen.resultados[0]  # Recupera el resultado individual generado por el evaluador.
    assert resultado.estado == ESTADO_CORRECTO  # Confirma que todas las expectativas actuales hayan sido satisfechas.
    assert resultado.codigos_error == []  # Comprueba que ninguna fase formal haya producido errores.
    assert resultado.bloques_validos == 1  # Confirma que la única instrucción haya superado completamente las fases actuales.
    assert resultado.subredes_generadas == 3  # Verifica que las tres cantidades HOSTS produzcan sus tres subredes correspondientes.


def prueba_caso_sintactico_invalido_pasa_si_aparece_codigo_esperado():  # Comprueba que un ejemplo inválido sea correcto como prueba cuando produce exactamente el problema esperado.
    ejemplo = EjemploCodigo(
        tipo="Inválida",  # Declara que la entrada está diseñada intencionalmente para fallar.
        titulo="Falta MASK",  # Identifica la situación sintáctica evaluada.
        comando="IP 192.168.1.0 /24 HOSTS 50 NAME Oficina",  # Omite deliberadamente la palabra reservada MASK.
        salida_esperada="Salida esperada: caso inválido. Código esperado: SIN-002.",  # Declara el diagnóstico que debe producir el parser.
    )  # Construye un ejemplo sintáctico incorrecto pero válido como caso de prueba.
    ejecutor = EjecutorPruebasEjemplos()  # Prepara el evaluador automático.
    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta únicamente el escenario preparado.
    resultado = resumen.resultados[0]  # Recupera su evaluación detallada.
    assert resultado.estado == ESTADO_CORRECTO  # Confirma que una entrada inválida puede representar una prueba correcta cuando falla de la manera esperada.
    assert "SIN-002" in resultado.codigos_obtenidos  # Verifica que realmente se haya producido el diagnóstico declarado.
    assert resultado.codigos_faltantes == []  # Confirma que ninguna expectativa actual haya quedado sin cumplir.


def prueba_sem006_ya_es_evaluable_y_pasa_si_aparece_codigo_esperado():  # Comprueba que SEM-006 forme parte del comportamiento actual del evaluador de ejemplos.
    ejemplo = EjemploCodigo(
        tipo="Inválida",  # Declara que el conjunto de redes contiene intencionalmente un conflicto.
        titulo="Redes traslapadas",  # Identifica claramente la regla semántica evaluada.
        comando=(
            "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara primero una red /24 completamente válida.
            "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"  # Declara después una /25 cuyo rango se encuentra dentro de la anterior.
        ),  # Construye dos bloques para activar exclusivamente la comprobación de traslape.
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-006.",  # Declara formalmente la regla que debe detectar el conflicto.
    )  # Prepara el ejemplo semánticamente inválido.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el evaluador automático.
    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta el caso mediante el flujo completo.
    resultado = resumen.resultados[0]  # Recupera toda la información obtenida.
    assert resultado.estado == ESTADO_CORRECTO  # Confirma que el ejemplo cumpla actualmente la expectativa declarada.
    assert resultado.codigos_evaluables == ["SEM-006"]  # Verifica que SEM-006 ya sea considerado parte de las reglas disponibles.
    assert resultado.codigos_pendientes == []  # Confirma que el caso no dependa de ninguna característica futura.
    assert "SEM-006" in resultado.codigos_error  # Comprueba que la regla haya aparecido realmente como error.
    assert resultado.bloques_validos == 1  # Confirma que solamente la primera red permanezca aceptada.
    assert resultado.subredes_generadas == 1  # Verifica que esa red válida todavía llegue normalmente hasta VLSM.


def prueba_adv005_ya_es_evaluable_y_no_invalida_el_caso():  # Comprueba que una advertencia esperada pueda evaluarse sin convertir una entrada válida en incorrecta.
    ejemplo = EjemploCodigo(
        tipo="Válida",  # Mantiene formalmente válida la instrucción porque ADV-005 no es bloqueante.
        titulo="Red sobredimensionada",  # Identifica la recomendación evaluada.
        comando="IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada",  # Utiliza una red claramente mayor que el espacio requerido por la solicitud.
        salida_esperada="Salida esperada: caso válido con advertencia. Código esperado: ADV-005.",  # Declara expresamente la recomendación que debe aparecer.
    )  # Construye un ejemplo correcto que intencionalmente produce una advertencia.
    ejecutor = EjecutorPruebasEjemplos()  # Prepara el componente encargado de comprobar la expectativa.
    resumen = ejecutor.ejecutar([ejemplo])  # Ejecuta la entrada mediante FlujoCompilacion.
    resultado = resumen.resultados[0]  # Recupera la evaluación individual.
    assert resultado.estado == ESTADO_CORRECTO  # Confirma que obtener la advertencia esperada represente una prueba satisfactoria.
    assert resultado.codigos_evaluables == ["ADV-005"]  # Comprueba que ADV-005 ya forme parte del catálogo evaluable actual.
    assert resultado.codigos_pendientes == []  # Confirma que no exista ninguna dependencia futura.
    assert "ADV-005" in resultado.codigos_advertencia  # Verifica que la recomendación haya sido producida realmente.
    assert resultado.codigos_error == []  # Confirma que una advertencia de dimensionamiento no convierta el bloque en error.
    assert resultado.subredes_generadas == 1  # Comprueba que el cálculo VLSM continúe normalmente.


def prueba_reporte_refleja_que_las_reglas_actuales_son_evaluables():  # Comprueba el contenido textual del reporte después de ejecutar ejemplos actuales.
    valido = EjemploCodigo(
        tipo="Válida",  # Declara una entrada normal que debe aprobar sin errores.
        titulo="Caso válido",  # Proporciona el título que deberá aparecer posteriormente dentro del reporte.
        comando="IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central",  # Utiliza una sola red válida y correctamente dimensionada.
        salida_esperada="Salida esperada: caso válido.",  # No exige ningún diagnóstico específico.
    )  # Construye el primer caso del resumen.
    invalido_esperado = EjemploCodigo(
        tipo="Inválida",  # Declara el segundo caso como intencionalmente incorrecto.
        titulo="Traslape detectado",  # Proporciona el título que deberá identificarse en el reporte final.
        comando=(
            "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara una primera red válida.
            "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"  # Agrega una segunda red que produce SEM-006.
        ),  # Construye el escenario semántico que debe considerarse correcto como prueba.
        salida_esperada="Salida esperada: caso inválido. Código esperado: SEM-006.",  # Define la expectativa formal correspondiente.
    )  # Construye el segundo ejemplo utilizado dentro del mismo resumen.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el evaluador que procesará ambos casos en conjunto.
    resumen = ejecutor.ejecutar([valido, invalido_esperado])  # Ejecuta las dos entradas respetando el orden proporcionado.
    reporte = generar_reporte_pruebas(resumen)  # Convierte el resumen estructurado en el texto utilizado para informar resultados.
    assert "Total de casos probados: 2" in reporte  # Confirma que el reporte refleje correctamente la cantidad ejecutada.
    assert "Casos correctos actualmente: 2" in reporte  # Verifica que ambos casos hayan satisfecho sus expectativas.
    assert "Casos pendientes de fase futura: 0" in reporte  # Comprueba que ninguna de las reglas utilizadas continúe pendiente.
    assert "[CORRECTO] Caso válido" in reporte  # Confirma que el primer ejemplo aparezca con su clasificación adecuada.
    assert "[CORRECTO] Traslape detectado" in reporte  # Confirma que el segundo ejemplo inválido también sea correcto como prueba al producir SEM-006.


def prueba_archivos_reales_no_contienen_expectativas_actuales_fallidas():  # Comprueba directamente que todos los ejemplos distribuidos actualmente con TecNet Finder sigan sincronizados con el compilador.
    gestor = GestorEjemplos()  # Crea el lector real de entrada_valida.txt y entradas_invalidas.txt.
    validos, invalidos = gestor.cargar_ejemplos()  # Recupera todas las entradas incluidas actualmente dentro de la carpeta Ejemplos.
    ejecutor = EjecutorPruebasEjemplos()  # Crea el mismo evaluador utilizado por las pruebas individuales anteriores.
    resumen = ejecutor.ejecutar(validos + invalidos)  # Ejecuta conjuntamente los 14 ejemplos válidos y los 25 inválidos actualmente incluidos.
    assert resumen.fallidos == 0  # Exige que ninguna expectativa correspondiente con características disponibles se encuentre desactualizada.