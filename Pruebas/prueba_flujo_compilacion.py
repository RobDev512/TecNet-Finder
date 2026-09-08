# ============================================================
# Archivo: prueba_flujo_compilacion.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba la integración de las partes actualmente
# reconstruidas de TecNet Finder.
#
# Las pruebas verifican el recorrido completo desde el código
# fuente hasta los bloques sintácticos y las subredes VLSM.
# ============================================================

from Motor.flujo_compilacion import FlujoCompilacion  # Importa el coordinador que ejecuta las fases reconstruidas del proyecto.


def prueba_flujo_completo_con_entrada_valida():  # Comprueba que una entrada correcta atraviese todo el flujo sin producir diagnósticos.
    flujo = FlujoCompilacion()  # Crea una instancia independiente del coordinador.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción completa sintácticamente válida.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta análisis léxico, análisis sintáctico y cálculo VLSM.

    assert resultado.diagnosticos == []  # Comprueba que ninguna de las fases actuales haya producido errores.
    assert resultado.tiene_errores is False  # Comprueba la propiedad general utilizada posteriormente por la interfaz.
    assert len(resultado.resultado_lexico.tokens) == 12  # Verifica que el lexer haya producido la secuencia completa de tokens.
    assert len(resultado.bloques_validos) == 1  # Comprueba que el parser haya aceptado exactamente una instrucción.
    assert len(resultado.subredes_vlsm) == 3  # Comprueba que las tres cantidades de hosts produzcan tres subredes.


def prueba_flujo_conserva_resultados_sintacticos():  # Comprueba que árbol, producciones y derivación permanezcan disponibles dentro del resultado global.
    flujo = FlujoCompilacion()  # Crea el coordinador utilizado por la prueba.
    codigo_fuente = "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"  # Define una entrada válida que incluye nombre.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta todas las partes actualmente disponibles.

    assert len(resultado.resultado_sintactico.arboles) == 1  # Comprueba que el árbol sintáctico siga disponible después de pasar por el flujo.
    assert "BloqueRed: Laboratorio" in resultado.resultado_sintactico.arbol_textual  # Comprueba que la representación textual corresponda al bloque procesado.
    assert "N → NAME IDENTIFIER" in resultado.resultado_sintactico.producciones_usadas  # Comprueba que se conserve la producción utilizada por NAME.
    assert "NAME Laboratorio" in resultado.resultado_sintactico.derivacion  # Comprueba que la derivación mantenga el identificador real.


def prueba_flujo_reune_diagnosticos_lexicos():  # Comprueba que los errores del lexer sean accesibles desde el resultado general.
    flujo = FlujoCompilacion()  # Crea una instancia del coordinador.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"  # Agrega un símbolo que no pertenece al lenguaje.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta el flujo permitiendo que el lexer registre el símbolo incorrecto.

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Extrae todos los códigos reunidos por ResultadoCompilacion.
    assert "LEX-002" in codigos  # Comprueba que el diagnóstico léxico aparezca en el resultado global.
    assert resultado.tiene_errores is True  # Verifica que la propiedad general detecte correctamente la presencia del error.


def prueba_flujo_recupera_instruccion_posterior():  # Comprueba que un error sintáctico anterior no impida procesar una instrucción válida posterior.
    flujo = FlujoCompilacion()  # Crea una instancia nueva del flujo.
    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )  # Define una primera instrucción incorrecta y otra válida en la línea siguiente.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta el flujo completo utilizando la recuperación del parser.

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Reúne los códigos producidos durante la ejecución.
    assert "SIN-001" in codigos  # Comprueba que la IP incompleta de la primera línea haya sido diagnosticada.
    assert len(resultado.bloques_validos) == 1  # Comprueba que la segunda instrucción haya sido recuperada correctamente.
    assert resultado.bloques_validos[0].nombre == "Correcta"  # Verifica que el único bloque conservado sea el de la segunda línea.
    assert len(resultado.subredes_vlsm) == 1  # Comprueba que VLSM se calcule únicamente para el bloque sintáctico recuperado.
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"  # Verifica que la subred conserve el nombre de la instrucción válida.


def prueba_flujo_procesa_multiples_bloques():  # Comprueba que varias instrucciones válidas puedan recorrer juntas el flujo completo.
    flujo = FlujoCompilacion()  # Crea una instancia del coordinador.
    codigo_fuente = (
        "IP 192.168.10.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio"
    )  # Define dos bloques válidos independientes.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta las fases sobre ambas instrucciones.

    assert len(resultado.bloques_validos) == 2  # Comprueba que el parser haya conservado las dos instrucciones.
    assert len(resultado.subredes_vlsm) == 2  # Comprueba que cada solicitud individual haya producido una subred.
    assert resultado.subredes_vlsm[0].nombre_red == "Oficina"  # Verifica que el primer resultado conserve el nombre de su red.
    assert resultado.subredes_vlsm[1].nombre_red == "Laboratorio"  # Verifica que el segundo resultado conserve su nombre correspondiente.


def prueba_flujo_controla_desbordamiento_ipv4_sin_excepcion():  # Comprueba que una solicitud extrema se convierta en un diagnóstico ubicado sobre el HOSTS responsable.
    flujo = FlujoCompilacion()  # Crea una instancia independiente para reproducir el caso encontrado durante la auditoría.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 4294967296 NAME Gigante"  # Solicita un bloque imposible de representar dentro del espacio IPv4.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta el flujo esperando un diagnóstico controlado y no una excepción.

    diagnostico = next(
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "GEN-001"
    )  # Recupera específicamente el diagnóstico técnico producido por la solicitud extrema.

    assert resultado.tiene_errores is True  # Confirma que la interfaz podrá mostrar un estado rojo.
    assert len(resultado.bloques_validos) == 1  # Conserva que la instrucción sí era sintácticamente válida.
    assert len(resultado.subredes_vlsm) == 0  # Evita publicar una subred incompleta o imposible.
    assert diagnostico.linea == 1  # Comprueba que el diagnóstico permanezca relacionado con la instrucción correcta.
    assert diagnostico.columna == 30  # Comprueba que la onda comience exactamente sobre la cantidad escrita después de HOSTS.
    assert diagnostico.longitud == 10  # Comprueba que la onda cubra los diez dígitos de la cantidad problemática.
    assert diagnostico.fragmento == "4294967296"  # Conserva el NUMBER exacto para tooltips y futuras ayudas contextuales.


def prueba_flujo_continua_despues_de_desbordamiento_ipv4():  # Comprueba que un bloque imposible no elimine resultados correctos de instrucciones posteriores.
    flujo = FlujoCompilacion()  # Crea un coordinador aislado para comprobar procesamiento parcial.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 4294967296 NAME Gigante\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )  # Combina un bloque imposible de calcular con otro bloque completamente procesable.
    resultado = flujo.analizar(codigo_fuente)  # Ejecuta ambos bloques dentro de una sola compilación.

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Reúne errores y advertencias producidos durante el procesamiento.
    assert "GEN-001" in codigos  # Comprueba que el primer bloque quede representado mediante un error controlado.
    assert "ADV-001" in codigos  # Comprueba que se informe al usuario que solamente parte de la entrada pudo procesarse.
    assert len(resultado.bloques_validos) == 2  # Confirma que ambos bloques siguen siendo sintácticamente correctos.
    assert len(resultado.subredes_vlsm) == 1  # Comprueba que solamente el bloque procesable produzca una subred.
    assert resultado.subredes_vlsm[0].nombre_red == "Correcta"  # Confirma que la salida sobreviviente corresponda al segundo bloque.