# ============================================================
# Archivo: prueba_flujo_compilacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas de integración
# correspondientes con FlujoCompilacion.
#
# Comprueba el recorrido completo desde el código fuente hasta:
#
# - Análisis léxico.
# - Análisis sintáctico.
# - Análisis semántico.
# - Advertencias.
# - Cálculo VLSM.
#
# También verifica recuperación de bloques posteriores,
# procesamiento parcial y protección de VLSM ante bloques que
# ya fueron rechazados por alguna regla semántica.
# ============================================================

from Motor.compilacion.flujo_compilacion import FlujoCompilacion  # Importa el coordinador real que conecta todas las fases disponibles de TecNet Finder.


def prueba_flujo_completo_con_entrada_valida():  # Comprueba el recorrido normal de una instrucción correcta desde el código fuente hasta VLSM.
    flujo = FlujoCompilacion()  # Crea una instancia limpia del coordinador principal.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción que supera todas las fases actuales.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta exactamente el mismo recorrido utilizado por la aplicación.
    assert resultado.diagnosticos == []  # Confirma que la entrada no produzca errores ni advertencias.
    assert resultado.tiene_errores is False  # Comprueba también el estado global calculado por ResultadoCompilacion.
    assert len(resultado.resultado_lexico.tokens) == 12  # Verifica que el lexer produzca la secuencia completa de doce tokens esperados.
    assert len(resultado.bloques_validos) == 1  # Confirma que una sola instrucción llegue hasta el final de las fases formales.
    assert len(resultado.subredes_vlsm) == 3  # Comprueba que las tres cantidades HOSTS produzcan tres subredes independientes.


def prueba_flujo_conserva_resultados_sintacticos():  # Comprueba que FlujoCompilacion no descarte árboles, producciones ni derivaciones generadas por el parser.
    flujo = FlujoCompilacion()  # Prepara el coordinador utilizado por esta prueba.
    codigo_fuente = "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"  # Utiliza un bloque sencillo cuya información sintáctica pueda comprobarse claramente.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta el recorrido completo aunque esta prueba inspeccione específicamente la salida sintáctica.
    assert len(resultado.resultado_sintactico.arboles) == 1  # Confirma que exista un árbol correspondiente con el único bloque válido.
    assert "BloqueRed: Laboratorio" in resultado.resultado_sintactico.arbol_textual  # Comprueba que la representación textual identifique correctamente la red.
    assert "N → NAME IDENTIFIER" in resultado.resultado_sintactico.producciones_usadas  # Confirma que se registre la producción opcional utilizada por NAME.
    assert "NAME Laboratorio" in resultado.resultado_sintactico.derivacion  # Comprueba que la derivación llegue finalmente hasta el identificador real escrito.


def prueba_flujo_reune_diagnosticos_lexicos():  # Comprueba que los errores producidos en la primera fase aparezcan también dentro del resultado global.
    flujo = FlujoCompilacion()  # Crea una instancia independiente del flujo.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"  # Añade un símbolo desconocido para producir LEX-002.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta el flujo completo permitiendo que el resultado conserve el error original.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los códigos combinados por ResultadoCompilacion.
    assert "LEX-002" in codigos  # Confirma que el problema detectado por el lexer permanezca disponible desde el resultado general.
    assert resultado.tiene_errores is True  # Comprueba que cualquier error léxico marque también la compilación completa como incorrecta.


def prueba_flujo_recupera_instruccion_posterior():  # Comprueba que un error sintáctico en una línea no impida procesar una instrucción válida posterior.
    flujo = FlujoCompilacion()  # Prepara una instancia nueva del coordinador.
    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50\n"  # Utiliza una primera dirección incompleta que deberá producir SIN-001.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"  # Agrega un segundo bloque que debe sobrevivir mediante la recuperación del parser.
    )
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta toda la entrada para comprobar tanto el error como la recuperación.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los códigos generados durante el procesamiento.
    assert "SIN-001" in codigos  # Confirma que la primera instrucción produzca el diagnóstico sintáctico esperado.
    assert len(resultado.bloques_validos) == 1  # Verifica que el segundo bloque continúe disponible después de la recuperación.
    assert resultado.bloques_validos[0].nombre == "Correcta"  # Comprueba que el bloque conservado sea exactamente la segunda instrucción.
    assert len(resultado.subredes_vlsm) == 1  # Confirma que solamente esa red produzca una subred.
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"  # Comprueba que VLSM conserve correctamente su nombre.


def prueba_flujo_procesa_multiples_bloques():  # Comprueba que varias instrucciones válidas independientes puedan procesarse dentro de una sola compilación.
    flujo = FlujoCompilacion()  # Crea el flujo utilizado por el conjunto de redes.
    codigo_fuente = (
        "IP 192.168.10.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara una primera red válida con una sola solicitud.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"  # Declara una segunda red válida e independiente de la anterior.
    )
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta conjuntamente ambas instrucciones.
    assert len(resultado.bloques_validos) == 2  # Confirma que las dos redes superen todas las fases disponibles.
    assert len(resultado.subredes_vlsm) == 2  # Comprueba que cada solicitud produzca exactamente una subred.
    assert resultado.subredes_vlsm[0].nombre_red == "Oficina"  # Verifica que la primera salida mantenga la identificación de su red base.
    assert resultado.subredes_vlsm[1].nombre_red == "Laboratorio"  # Verifica igualmente la identificación de la segunda red.


def prueba_flujo_semantico_controla_solicitud_extrema_antes_de_vlsm():  # Comprueba que el semántico detenga cantidades imposibles antes de alcanzar la calculadora VLSM.
    flujo = FlujoCompilacion()  # Crea el coordinador utilizado en esta prueba de protección.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 4294967296 NAME Gigante"  # Utiliza una cantidad muy superior al espacio disponible dentro de IPv4.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta la entrada para comprobar en qué fase debe ser rechazada.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los diagnósticos producidos.
    assert resultado.tiene_errores is True  # Confirma que la compilación completa sea considerada incorrecta.
    assert "SEM-005" in codigos  # Comprueba que la solicitud individual sea detectada como demasiado grande.
    assert "SEM-004" in codigos  # Comprueba que también se informe la insuficiencia total de capacidad.
    assert "GEN-001" not in codigos  # Garantiza que VLSM no tenga que capturar tardíamente la situación mediante un error general.
    assert resultado.bloques_validos == []  # Confirma que la red no llegue a la colección semánticamente aceptada.
    assert resultado.subredes_vlsm == []  # Evita producir cualquier salida VLSM a partir de una solicitud imposible.


def prueba_flujo_continua_despues_de_error_de_capacidad():  # Comprueba que un bloque semánticamente imposible no impida procesar otra red posterior válida.
    flujo = FlujoCompilacion()  # Prepara el coordinador utilizado por la prueba.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 4294967296 NAME Gigante\n"  # Utiliza un primer bloque que debe producir SEM-005 y SEM-004.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"  # Agrega un segundo bloque completamente válido que debe llegar hasta VLSM.
    )
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta conjuntamente ambas instrucciones para comprobar procesamiento parcial.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los diagnósticos producidos durante el flujo.
    assert "SEM-005" in codigos  # Confirma el exceso de la solicitud individual del primer bloque.
    assert "SEM-004" in codigos  # Confirma también su exceso de capacidad total.
    assert "ADV-001" in codigos  # Comprueba que el flujo informe que todavía existen resultados válidos aprovechables.
    assert "GEN-001" not in codigos  # Confirma nuevamente que la situación haya sido controlada antes de llegar a VLSM.
    assert len(resultado.bloques_validos) == 1  # Mantiene únicamente la red semánticamente correcta.
    assert resultado.bloques_validos[0].nombre == "Correcta"  # Comprueba que la red conservada sea la segunda instrucción.
    assert len(resultado.subredes_vlsm) == 1  # Confirma que esa red produzca normalmente su única subred.
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"  # Mantiene el identificador correcto dentro del resultado VLSM.


def prueba_flujo_sem001_impide_que_mascara_invalida_llegue_a_vlsm():  # Comprueba que una máscara fuera del rango permitido sea detenida por el semántico.
    flujo = FlujoCompilacion()  # Crea el coordinador utilizado por esta comprobación.
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida"  # Utiliza una máscara sintácticamente correcta pero semánticamente rechazada.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta todas las fases disponibles.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los códigos presentes en el resultado combinado.
    assert resultado.resultado_semantico is not None  # Confirma que la fase semántica sí haya sido ejecutada por el flujo.
    assert len(resultado.resultado_sintactico.bloques) == 1  # Verifica que el parser haya aceptado correctamente la estructura antes del rechazo semántico.
    assert "SEM-001" in codigos  # Confirma que la máscara fuera de rango sea la responsable del rechazo.
    assert resultado.bloques_validos == []  # Impide que el bloque llegue a considerarse válido globalmente.
    assert resultado.subredes_vlsm == []  # Confirma que VLSM nunca procese una red con máscara inválida.
    assert resultado.tiene_errores is True  # Marca globalmente la compilación como incorrecta.


def prueba_flujo_sem001_permite_procesamiento_parcial():  # Comprueba que SEM-001 no impida procesar otra red válida incluida posteriormente.
    flujo = FlujoCompilacion()  # Crea un coordinador independiente.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /31 HOSTS 1 NAME Invalida\n"  # Declara una primera red cuya máscara será rechazada.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"  # Declara otra red completamente válida e independiente.
    )
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta ambas instrucciones mediante las fases actuales.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera errores y advertencias generados.
    assert "SEM-001" in codigos  # Confirma el rechazo semántico de la primera red.
    assert "ADV-001" in codigos  # Confirma que exista procesamiento parcial gracias a la segunda instrucción.
    assert len(resultado.resultado_sintactico.bloques) == 2  # Verifica que ambas estructuras hayan sido correctas desde el punto de vista gramatical.
    assert len(resultado.bloques_validos) == 1  # Conserva solamente el bloque que también supera la fase semántica.
    assert resultado.bloques_validos[0].nombre == "Correcta"  # Comprueba cuál de las dos redes sobrevivió.
    assert len(resultado.subredes_vlsm) == 1  # Confirma que solamente la red válida llegue al cálculo.
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"  # Comprueba que la salida conserve su identificación original.


def prueba_flujo_sem002_impide_que_ip_host_llegue_a_vlsm():  # Comprueba que una IP que representa un host sea rechazada antes del cálculo VLSM.
    flujo = FlujoCompilacion()  # Prepara el coordinador para este caso.
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Invalida"  # Utiliza una dirección que no corresponde con el comienzo de la red /24.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta la entrada mediante el flujo completo.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los códigos producidos.
    assert "SEM-002" in codigos  # Confirma que la relación incorrecta entre IP y máscara sea detectada.
    assert len(resultado.resultado_sintactico.bloques) == 1  # Verifica que la instrucción sí era gramaticalmente válida antes del análisis de significado.
    assert resultado.bloques_validos == []  # Impide conservar la red después del error semántico.
    assert resultado.subredes_vlsm == []  # Confirma que VLSM nunca reciba la dirección de host como red base.


def prueba_flujo_sem003_permite_procesamiento_parcial():  # Comprueba que una cantidad cero no impida procesar otro bloque válido posterior.
    flujo = FlujoCompilacion()  # Crea una nueva instancia del flujo principal.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Invalida\n"  # Declara una red cuya cantidad no posee significado válido.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"  # Agrega una segunda instrucción que debe continuar normalmente.
    )
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta ambas redes para comprobar la recuperación semántica.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los diagnósticos generados durante todas las etapas.
    assert "SEM-003" in codigos  # Confirma que el cero sea detectado por la regla correspondiente.
    assert "ADV-001" in codigos  # Confirma que el flujo informe la existencia de procesamiento parcial.
    assert len(resultado.resultado_sintactico.bloques) == 2  # Verifica que ambos bloques hayan superado correctamente la gramática.
    assert len(resultado.bloques_validos) == 1  # Mantiene únicamente la red con una cantidad semánticamente válida.
    assert resultado.bloques_validos[0].nombre == "Correcta"  # Comprueba que la instrucción conservada sea exactamente la segunda.
    assert len(resultado.subredes_vlsm) == 1  # Confirma que se genere solamente una subred VLSM.
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"  # Conserva el nombre de la red válida dentro del resultado final.