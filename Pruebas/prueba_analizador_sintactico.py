# ============================================================
# Archivo: prueba_analizador_sintactico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con la fase de análisis sintáctico de TecNet Finder.
#
# Cada caso utiliza primero el analizador léxico y posteriormente
# el sintáctico para reproducir el recorrido real de las dos
# primeras fases del compilador.
#
# Se comprueban SIN-001 a SIN-008, recuperación por modo pánico,
# instrucciones duplicadas, árboles sintácticos, producciones
# utilizadas y derivaciones con los valores reales de la entrada.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Produce los tokens que posteriormente serán enviados al analizador sintáctico.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Comprueba el orden gramatical de los tokens y construye las representaciones sintácticas.

def analizar_codigo(codigo_fuente: str):  # Ejecuta consecutivamente las fases léxica y sintáctica para evitar repetir el mismo procedimiento en cada prueba.
    analizador_lexico = AnalizadorLexico()  # Crea un lexer independiente para la entrada actual.
    resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Convierte el código fuente en tokens y posibles diagnósticos léxicos.
    analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Construye el parser utilizando exactamente los tokens reconocidos.
    resultado_sintactico = analizador_sintactico.analizar()  # Ejecuta la validación gramatical y genera bloques, diagnósticos y representaciones.
    return resultado_lexico, resultado_sintactico  # Entrega ambas fases para que cada prueba pueda comprobar únicamente la información que necesita.

def prueba_instruccion_valida_completa():  # Comprueba una instrucción correcta que utiliza IP, MASK, HOSTS y la sección opcional NAME.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define un bloque completo que cumple la gramática.
    resultado_lexico, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las dos primeras fases sobre la instrucción.
    assert resultado_lexico.diagnosticos == []  # Confirma que ningún elemento de la entrada produzca un problema léxico.
    assert resultado_sintactico.diagnosticos == []  # Confirma que la secuencia completa respete la gramática definida.
    assert len(resultado_sintactico.bloques) == 1  # Verifica que se haya construido exactamente un bloque sintáctico válido.
    bloque = resultado_sintactico.bloques[0]  # Recupera el bloque generado para comprobar individualmente sus componentes.
    assert bloque.direccion_ip == "192.168.1.0"  # Comprueba que la dirección reconocida se conserve sin modificaciones.
    assert bloque.mascara_subred == "/24"  # Comprueba que la máscara CIDR sea almacenada correctamente.
    assert bloque.cantidades_hosts == [50, 30, 10]  # Comprueba que todas las cantidades y su orden original permanezcan intactos.
    assert bloque.nombre == "Oficina"  # Verifica que el identificador opcional se conserve dentro del bloque.

def prueba_instruccion_valida_sin_nombre():  # Comprueba que NAME sea realmente una parte opcional de la producción.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50"  # Define una instrucción correcta que termina después de la lista HOSTS.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta ambas fases y descarta el resultado léxico porque no se necesita comprobarlo.
    assert len(resultado_sintactico.bloques) == 1  # Confirma que omitir NAME no impida construir un bloque válido.
    assert resultado_sintactico.diagnosticos == []  # Comprueba que la ausencia de la sección opcional no produzca ningún error.
    assert resultado_sintactico.bloques[0].nombre is None  # Verifica que un nombre inexistente se represente mediante None.

def prueba_ip_incompleta():  # Comprueba SIN-001 cuando la dirección escrita después de IP no posee sus cuatro octetos completos.
    codigo_fuente = "IP 192.168.1. MASK /24 HOSTS 50"  # Omite deliberadamente el último octeto de la dirección.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Permite que el lexer conserve las partes individuales y que el parser detecte la estructura incorrecta.
    assert resultado_sintactico.bloques == []  # Confirma que una dirección incompleta impida aceptar el bloque.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-001"  # Verifica que se utilice específicamente el diagnóstico de IP incompleta.

def prueba_falta_mask():  # Comprueba SIN-002 cuando después de la dirección no aparece la palabra reservada MASK.
    codigo_fuente = "IP 192.168.1.0 /24 HOSTS 50"  # Coloca directamente la máscara CIDR para omitir deliberadamente MASK.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta ambas fases para comprobar el token obligatorio ausente.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-002"  # Confirma que el parser clasifique correctamente la ausencia de MASK.

def prueba_falta_mascara_cidr():  # Comprueba SIN-003 cuando MASK no recibe posteriormente una máscara CIDR.
    codigo_fuente = "IP 192.168.1.0 MASK HOSTS 50"  # Coloca HOSTS inmediatamente después de MASK para dejar incompleta esa parte de la producción.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el parser sobre la estructura incompleta.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-003"  # Confirma que el elemento ausente se identifique como máscara CIDR.

def prueba_falta_cantidad_hosts():  # Comprueba SIN-004 cuando la sección HOSTS no contiene ni siquiera su primera cantidad.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS NAME Oficina"  # Coloca NAME directamente después de HOSTS para omitir NUMBER.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las fases necesarias para producir el error sintáctico.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-004"  # Confirma que el parser detecte específicamente la falta de una cantidad.

def prueba_lista_hosts_mal_formada():  # Comprueba SIN-005 cuando una coma queda sin otro NUMBER después de ella.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,"  # Termina deliberadamente la lista inmediatamente después del separador.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta ambas fases para activar la recuperación local de HOSTS.
    assert resultado_sintactico.bloques == []  # Confirma que el bloque que requirió recuperación local no sea aceptado como válido.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-005"  # Verifica que la coma incompleta produzca el diagnóstico correspondiente.

def prueba_name_sin_identificador():  # Comprueba SIN-006 cuando NAME aparece pero no posee un IDENTIFIER posterior.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME"  # Termina la entrada inmediatamente después de iniciar la sección opcional.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las fases necesarias para comprobar la construcción incompleta.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-006"  # Confirma que una vez escrito NAME el identificador posterior sea obligatorio.

def prueba_instruccion_duplicada():  # Comprueba SIN-007 cuando la misma instrucción completa aparece dos veces.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara por primera vez la instrucción que debe conservarse.
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"  # Repite exactamente todos sus elementos para activar la detección de duplicados.
    )
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Procesa conjuntamente las dos declaraciones.
    assert len(resultado_sintactico.bloques) == 1  # Confirma que solamente se conserve una copia de la instrucción.
    assert len(resultado_sintactico.diagnosticos) == 1  # Comprueba que la repetición produzca exactamente un diagnóstico.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-007"  # Verifica que el problema se clasifique como instrucción duplicada.

def prueba_orden_incorrecto_y_recuperacion():  # Comprueba SIN-008 y que el modo pánico pueda continuar desde una IP encontrada en una línea posterior.
    codigo_fuente = (
        "MASK /24 HOSTS 50\n"  # Comienza deliberadamente con MASK para romper el orden definido por la gramática.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Segunda"  # Coloca después una instrucción correcta que debe recuperarse.
    )
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el parser sobre ambas líneas.
    assert resultado_sintactico.diagnosticos[0].codigo == "SIN-008"  # Confirma que la primera línea produzca el error de orden esperado.
    assert len(resultado_sintactico.bloques) == 1  # Comprueba que el modo pánico encuentre y procese la segunda instrucción.
    assert resultado_sintactico.bloques[0].direccion_ip == "10.0.0.0"  # Verifica que el bloque recuperado pertenezca realmente a la segunda línea.
    assert resultado_sintactico.bloques[0].nombre == "Segunda"  # Confirma que la recuperación continúe hasta completar también la sección NAME.

def prueba_genera_arbol_sintactico():  # Comprueba que cada bloque válido produzca una representación estructurada mediante NodoSintactico.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30 NAME Oficina"  # Utiliza una lista con varias cantidades y un nombre para obtener un árbol completo.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta las fases léxica y sintáctica.
    assert len(resultado_sintactico.arboles) == 1  # Confirma que exista exactamente un árbol para el único bloque aceptado.
    arbol = resultado_sintactico.arboles[0]  # Recupera la raíz para revisar su estructura.
    assert arbol.etiqueta == "BloqueRed: Oficina"  # Comprueba que la raíz identifique el bloque utilizando su NAME.
    assert [hijo.etiqueta for hijo in arbol.hijos] == ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "HOSTS_LIST", "NAME", "IDENTIFIER"]  # Verifica el orden de los componentes principales del árbol.

def prueba_arbol_conserva_hosts_y_comas():  # Comprueba que HOSTS_LIST represente explícitamente tanto cantidades como separadores.
    codigo_fuente = "IP 10.0.0.0 MASK /24 HOSTS 100,50,20"  # Define una lista compuesta por tres NUMBER y dos COMMA.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Construye el árbol correspondiente con la instrucción.
    arbol = resultado_sintactico.arboles[0]  # Recupera la raíz del único árbol generado.
    nodo_hosts = next(hijo for hijo in arbol.hijos if hijo.etiqueta == "HOSTS_LIST")  # Localiza el nodo agrupador correspondiente con la lista HOSTS.
    assert [hijo.etiqueta for hijo in nodo_hosts.hijos] == ["NUMBER", "COMMA", "NUMBER", "COMMA", "NUMBER"]  # Confirma que la estructura mantenga también las comas originales.

def prueba_genera_producciones_usadas():  # Comprueba que el parser describa las producciones de la gramática realmente necesarias para la entrada.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30 NAME Oficina"  # Obliga a utilizar continuación de HOSTS y la alternativa NAME IDENTIFIER.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta la fase para obtener el texto de producciones utilizadas.
    assert "S → B A" in resultado_sintactico.producciones_usadas  # Confirma que se muestre la producción inicial del programa.
    assert "C → COMMA NUMBER C" in resultado_sintactico.producciones_usadas  # Confirma que se registre la continuación necesaria para el segundo host.
    assert "N → NAME IDENTIFIER" in resultado_sintactico.producciones_usadas  # Confirma que aparezca la alternativa empleada por la sección NAME.

def prueba_genera_derivacion_con_valores_reales():  # Comprueba que la derivación formal termine sustituyendo los símbolos por los valores originales.
    codigo_fuente = "IP 172.16.0.0 MASK /20 HOSTS 200,40 NAME Campus"  # Proporciona valores concretos fáciles de distinguir dentro de la derivación.
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta el parser y genera la derivación asociada con el bloque.
    assert "⇒ IP 172.16.0.0 MASK /20 HOSTS 200,40 NAME Campus" in resultado_sintactico.derivacion  # Confirma que la cadena terminal final reproduzca la instrucción original.

def prueba_solo_bloques_validos_generan_representaciones():  # Comprueba que árboles y derivaciones se construyan exclusivamente para bloques sintácticamente aceptados.
    codigo_fuente = (
        "IP 192.168.1. MASK /24 HOSTS 50\n"  # Crea una primera instrucción incorrecta que debe producir SIN-001.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Correcta"  # Agrega una segunda instrucción válida que será recuperada mediante modo pánico.
    )
    _, resultado_sintactico = analizar_codigo(codigo_fuente)  # Ejecuta ambas fases y permite que el parser continúe después del primer problema.
    assert len(resultado_sintactico.arboles) == 1  # Confirma que solamente la segunda instrucción produzca árbol.
    assert "BloqueRed: Correcta" in resultado_sintactico.arbol_textual  # Verifica que la representación textual identifique exclusivamente el bloque válido.
    assert "10.0.0.0" in resultado_sintactico.derivacion  # Comprueba que la dirección válida aparezca dentro de las sustituciones generadas.
    assert "192.168.1." not in resultado_sintactico.derivacion  # Evita incluir dentro de la derivación una instrucción que nunca completó la gramática.