# ============================================================
# Archivo: prueba_analizador_sintactico.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo contiene las pruebas automáticas del analizador
# sintáctico. Cada caso utiliza primero el lexer y después el parser
# para reproducir el flujo real de las dos primeras fases.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa el lexer que transforma el código fuente en tokens.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa el parser que valida el orden de los tokens.


def analizar_codigo(codigo_fuente: str):  # Ejecuta consecutivamente las fases léxica y sintáctica sobre una entrada.
    analizador_lexico = AnalizadorLexico()  # Crea una instancia del analizador léxico.
    resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Convierte el código fuente en tokens y diagnósticos léxicos.
    analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Crea el parser usando los tokens obtenidos.
    resultado_sintactico = analizador_sintactico.analizar()  # Ejecuta la validación sintáctica de la secuencia.
    return resultado_lexico, resultado_sintactico  # Devuelve ambos resultados para poder comprobar cada fase.


def prueba_instruccion_valida_completa():  # Comprueba una instrucción válida que incluye NAME.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción completa válida.
    resultado_lexico, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_lexico.diagnosticos == []  # Comprueba que el lexer no haya detectado errores.
    assert resultado_sintactico.diagnosticos == []  # Comprueba que el parser tampoco haya detectado errores.
    assert len(resultado_sintactico.bloques) == 1  # Comprueba que exista exactamente un bloque válido.
    bloque = resultado_sintactico.bloques[0]  # Obtiene el bloque reconocido para revisar sus datos.
    assert bloque.direccion_ip == "192.168.1.0"  # Verifica la dirección IP almacenada.
    assert bloque.mascara_subred == "/24"  # Verifica la máscara CIDR almacenada.
    assert bloque.cantidades_hosts == [50, 30, 10]  # Verifica todas las cantidades de hosts.
    assert bloque.nombre == "Oficina"  # Verifica el nombre opcional de la red.


def prueba_instruccion_valida_sin_nombre():  # Comprueba que la sección NAME sea realmente opcional.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50"  # Define una instrucción válida sin nombre.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases y conserva el resultado sintáctico.
    assert len(resultado_sintactico.bloques) == 1  # Comprueba que la instrucción sea aceptada.
    assert resultado_sintactico.diagnosticos == []  # Verifica que no se produzcan diagnósticos sintácticos.
    assert resultado_sintactico.bloques[0].nombre is None  # Comprueba que el nombre ausente se represente con None.


def prueba_ip_incompleta():  # Comprueba SIN-001 cuando la dirección IP está incompleta.
    codigo_fuente = "IP 192.168.1. MASK /24 HOSTS 50"  # Define una dirección a la que le falta el último octeto.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.bloques == []  # Comprueba que el bloque incorrecto no sea aceptado.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-001"  # Verifica el código específico del diagnóstico.


def prueba_falta_mask():  # Comprueba SIN-002 cuando falta la palabra reservada MASK.
    codigo_fuente = "IP 192.168.1.0 /24 HOSTS 50"  # Omite MASK después de la dirección IP.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-002"  # Verifica que el parser detecte la ausencia de MASK.


def prueba_falta_mascara_cidr():  # Comprueba SIN-003 cuando MASK no recibe una máscara CIDR.
    codigo_fuente = "IP 192.168.1.0 MASK HOSTS 50"  # Coloca HOSTS inmediatamente después de MASK.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-003"  # Verifica que se detecte la máscara faltante.


def prueba_falta_cantidad_hosts():  # Comprueba SIN-004 cuando HOSTS no recibe ningún número.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS NAME Oficina"  # Coloca NAME inmediatamente después de HOSTS.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-004"  # Verifica que se detecte la cantidad faltante.


def prueba_lista_hosts_mal_formada():  # Comprueba SIN-005 cuando una coma no está seguida por otro número.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,"  # Termina la lista de hosts dejando una coma incompleta.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.bloques == []  # Comprueba que el bloque con error local no sea aceptado.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-005"  # Verifica el diagnóstico de lista mal formada.


def prueba_name_sin_identificador():  # Comprueba SIN-006 cuando NAME no tiene un identificador posterior.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME"  # Termina la instrucción inmediatamente después de NAME.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-006"  # Verifica el diagnóstico de nombre incompleto.


def prueba_instruccion_duplicada():  # Comprueba SIN-007 cuando se repite exactamente la misma instrucción.
    codigo_fuente = (  # Define dos instrucciones idénticas en líneas diferentes.
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"
    )
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert len(resultado_sintactico.bloques) == 1  # Comprueba que solamente se conserve una copia válida.
    assert len(resultado_sintactico.diagnosticos) == 1  # Comprueba que exista exactamente un diagnóstico.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-007"  # Verifica que el diagnóstico corresponda a duplicado.


def prueba_orden_incorrecto_y_recuperacion():  # Comprueba SIN-008 y que el modo pánico recupere una instrucción posterior.
    codigo_fuente = (  # Define una primera línea incorrecta y una segunda instrucción válida.
        "MASK /24 HOSTS 50\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Segunda"
    )
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-008"  # Comprueba el error de orden en la primera línea.
    assert len(resultado_sintactico.bloques) == 1  # Verifica que el modo pánico haya recuperado la segunda instrucción.
    assert resultado_sintactico.bloques[0].direccion_ip == "10.0.0.0"  # Comprueba que el bloque recuperado sea la segunda red.
    assert resultado_sintactico.bloques[0].nombre == "Segunda"  # Comprueba también el nombre del bloque recuperado.


def prueba_genera_arbol_sintactico():  # Comprueba que un bloque válido produzca un árbol con la misma estructura básica de la versión anterior.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30 NAME Oficina"  # Define una instrucción válida con varios hosts y nombre.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el flujo léxico y sintáctico completo.
    assert len(resultado_sintactico.arboles) == 1  # Comprueba que exista exactamente un árbol para el único bloque válido.
    arbol = resultado_sintactico.arboles[0]  # Obtiene la raíz del árbol generado.
    assert arbol.etiqueta == "BloqueRed: Oficina"  # Verifica que la raíz incluya el nombre de la red.
    assert [hijo.etiqueta for hijo in arbol.hijos] == ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "HOSTS_LIST", "NAME", "IDENTIFIER"]  # Comprueba el orden principal de los nodos del bloque.


def prueba_arbol_conserva_hosts_y_comas():  # Comprueba que HOSTS_LIST represente tanto los números como las comas de la lista.
    codigo_fuente = "IP 10.0.0.0 MASK /24 HOSTS 100,50,20"  # Define una instrucción válida con tres cantidades.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta ambas fases de análisis.
    arbol = resultado_sintactico.arboles[0]  # Obtiene el único árbol generado.
    nodo_hosts = next(hijo for hijo in arbol.hijos if hijo.etiqueta == "HOSTS_LIST")  # Localiza el nodo que agrupa la lista de hosts.
    assert [hijo.etiqueta for hijo in nodo_hosts.hijos] == ["NUMBER", "COMMA", "NUMBER", "COMMA", "NUMBER"]  # Verifica que la estructura mantenga los separadores originales.


def prueba_genera_producciones_usadas():  # Comprueba que el resultado sintáctico incluya la gramática base y las reglas realmente aplicadas.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30 NAME Oficina"  # Define un bloque que obliga a usar C y la producción opcional de NAME.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el análisis completo de la entrada.
    assert "S → B A" in resultado_sintactico.producciones_usadas  # Comprueba que aparezca la producción inicial de la gramática.
    assert "C → COMMA NUMBER C" in resultado_sintactico.producciones_usadas  # Comprueba que se registre la continuación de la lista de hosts.
    assert "N → NAME IDENTIFIER" in resultado_sintactico.producciones_usadas  # Comprueba que se registre la producción usada por el nombre opcional.


def prueba_genera_derivacion_con_valores_reales():  # Comprueba que la derivación sustituya los terminales por los valores concretos de la entrada.
    codigo_fuente = "IP 172.16.0.0 MASK /20 HOSTS 200,40 NAME Campus"  # Define una instrucción con valores fáciles de localizar en la derivación.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el flujo de análisis.
    assert "⇒ IP 172.16.0.0 MASK /20 HOSTS 200,40 NAME Campus" in resultado_sintactico.derivacion  # Verifica que la cadena terminal final contenga los valores originales.


def prueba_solo_bloques_validos_generan_representaciones():  # Comprueba que un bloque incorrecto no produzca árbol ni derivación propia mientras otro válido sí se conserva.
    codigo_fuente = (  # Define una primera instrucción inválida y una segunda correctamente formada.
        "IP 192.168.1. MASK /24 HOSTS 50\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"
    )
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el análisis y permite que el modo pánico recupere la segunda línea.
    assert len(resultado_sintactico.arboles) == 1  # Comprueba que solamente el bloque válido produzca un árbol.
    assert "BloqueRed: Correcta" in resultado_sintactico.arbol_textual  # Verifica que la representación textual corresponda al bloque recuperado.
    assert "10.0.0.0" in resultado_sintactico.derivacion  # Comprueba que la derivación incluya el bloque válido.
    assert "192.168.1." not in resultado_sintactico.derivacion  # Comprueba que la instrucción sintácticamente incorrecta no se derive.