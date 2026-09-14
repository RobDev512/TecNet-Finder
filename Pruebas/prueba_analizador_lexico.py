# ============================================================
# Archivo: prueba_analizador_lexico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con la fase de análisis léxico de TecNet Finder.
#
# Comprueba el reconocimiento de tokens válidos y los
# diagnósticos LEX-001, LEX-002, LEX-003 y LEX-004.
#
# También verifica comportamientos aceptados por el lenguaje,
# como palabras reservadas pegadas a determinados valores, y
# confirma que estructuras incompletas que pertenecen a la
# sintaxis no se conviertan incorrectamente en errores léxicos.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa exclusivamente la fase léxica que será evaluada por estas pruebas.


def prueba_entrada_valida_completa():  # Comprueba una instrucción válida que utiliza todos los elementos principales del lenguaje.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer para evitar compartir estado entre pruebas.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción completa que debe reconocerse sin errores.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta únicamente el análisis léxico sobre la entrada proporcionada.
    tipos_esperados = ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "NUMBER", "COMMA", "NUMBER", "COMMA", "NUMBER", "NAME", "IDENTIFIER"]  # Define el orden exacto de categorías que debe producir el lexer.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae solamente la categoría de cada token para compararla con la secuencia esperada.
    assert tipos_obtenidos == tipos_esperados  # Confirma que todos los elementos hayan sido reconocidos en el mismo orden en que aparecen.
    assert resultado.diagnosticos == []  # Confirma que una entrada léxicamente correcta no produzca ningún diagnóstico.


def prueba_identificador_fuera_de_lugar():  # Comprueba que un identificador utilizado sin NAME produzca específicamente LEX-001.
    analizador = AnalizadorLexico()  # Prepara una nueva instancia del analizador léxico.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 Oficina"  # Coloca deliberadamente Oficina en una posición donde el lenguaje no permite identificadores.
    resultado = analizador.analizar(codigo_fuente)  # Procesa la entrada para obtener el diagnóstico correspondiente.
    assert len(resultado.diagnosticos) == 1  # Confirma que solamente exista un problema léxico en esta entrada.
    assert resultado.diagnosticos[0].codigo == "LEX-001"  # Verifica que el identificador fuera de NAME utilice el código correcto.
    assert resultado.diagnosticos[0].categoria == "Léxico"  # Confirma que el problema pertenezca formalmente a esta fase.
    assert resultado.diagnosticos[0].fragmento == "Oficina"  # Comprueba que el diagnóstico conserve exactamente el identificador incorrecto.


def prueba_simbolo_no_reconocido():  # Comprueba que un carácter ajeno al lenguaje produzca específicamente LEX-002.
    analizador = AnalizadorLexico()  # Crea una instancia nueva del lexer.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"  # Añade deliberadamente un símbolo que no pertenece al DSL.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento sobre la entrada alterada.
    assert len(resultado.diagnosticos) == 1  # Confirma que el único problema sea el símbolo agregado al final.
    assert resultado.diagnosticos[0].codigo == "LEX-002"  # Comprueba que un elemento completamente desconocido utilice el código correspondiente.
    assert resultado.diagnosticos[0].categoria == "Léxico"  # Confirma la categoría asociada con el diagnóstico.
    assert resultado.diagnosticos[0].fragmento == "@"  # Verifica que se conserve exactamente el símbolo responsable del error.


def prueba_identificador_despues_de_name():  # Comprueba que un identificador escrito después de NAME sea aceptado normalmente.
    analizador = AnalizadorLexico()  # Crea un lexer independiente para este caso.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"  # Utiliza NAME seguido correctamente por un identificador.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta la fase léxica sobre la instrucción.
    identificadores = [token for token in resultado.tokens if token.tipo == "IDENTIFIER"]  # Recupera exclusivamente los tokens clasificados como identificadores.
    assert len(identificadores) == 1  # Confirma que solamente Oficina haya sido reconocida con esta categoría.
    assert identificadores[0].valor == "Oficina"  # Comprueba que el valor almacenado corresponda con el nombre escrito.
    assert resultado.diagnosticos == []  # Confirma que la utilización correcta de NAME no produzca errores.


def prueba_palabras_reservadas_pegadas():  # Comprueba que IP, MASK y HOSTS puedan aparecer unidos directamente con determinados valores.
    analizador = AnalizadorLexico()  # Prepara una instancia limpia del analizador.
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"  # Utiliza deliberadamente la escritura histórica admitida por el lexer.
    resultado = analizador.analizar(codigo_fuente)  # Procesa la entrada para verificar que pueda dividirse correctamente.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Recupera la secuencia de categorías generadas.
    tipos_esperados = ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "NUMBER", "NAME", "IDENTIFIER"]  # Define la secuencia que debe obtenerse aun cuando no existan ciertos espacios.
    assert tipos_obtenidos == tipos_esperados  # Confirma que las palabras reservadas y sus valores se hayan separado correctamente.
    assert resultado.diagnosticos == []  # Confirma que esta escritura permitida no se convierta en un error léxico.


def prueba_ip_incompleta_no_es_error_lexico():  # Comprueba que una dirección incompleta se conserve para que posteriormente sea evaluada por el parser.
    analizador = AnalizadorLexico()  # Crea el lexer utilizado exclusivamente por esta prueba.
    codigo_fuente = "IP 192.168.1. MASK /24 HOSTS 50"  # Utiliza una IPv4 incompleta cuyo problema pertenece a la estructura sintáctica.
    resultado = analizador.analizar(codigo_fuente)  # Obtiene los elementos parciales que el lexer todavía puede reconocer.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae las categorías reconocidas dentro de la dirección incompleta.
    assert "NUMBER" in tipos_obtenidos  # Confirma que los octetos parciales continúen representados mediante tokens numéricos.
    assert "DOT" in tipos_obtenidos  # Confirma que los puntos individuales se conserven para que el sintáctico pueda reconstruir el problema.
    assert resultado.diagnosticos == []  # Evita clasificar como error léxico una estructura que debe producir posteriormente SIN-001.


def prueba_palabra_reservada_con_mayusculas_incorrectas():  # Comprueba que una palabra reservada real con capitalización incorrecta produzca LEX-003.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 mask /24 HOSTS 50 NAME Oficina"  # Escribe MASK deliberadamente en minúsculas.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta la fase léxica para detectar la variante incorrecta.
    diagnosticos_lex_003 = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "LEX-003"]  # Conserva únicamente las apariciones específicas de este diagnóstico.
    assert len(diagnosticos_lex_003) == 1  # Confirma que solamente la palabra mask produzca LEX-003.
    assert diagnosticos_lex_003[0].categoria == "Léxico"  # Comprueba que la categoría formal permanezca correcta.
    assert diagnosticos_lex_003[0].fragmento == "mask"  # Conserva exactamente la variante escrita por el usuario.
    assert diagnosticos_lex_003[0].linea == 1  # Confirma que el problema se ubique en la única línea de la prueba.
    assert diagnosticos_lex_003[0].columna == 15  # Comprueba que el diagnóstico señale la posición exacta donde comienza mask.


def prueba_lex_003_no_reemplaza_identificador_mal_escrito_generico():  # Comprueba que un texto parecido a una reservada pero realmente inexistente conserve LEX-001.
    analizador = AnalizadorLexico()  # Crea una instancia limpia del analizador.
    codigo_fuente = "IP 192.168.1.0 MAS /24 HOSTS 50 NAME Oficina"  # Utiliza MAS, que no representa ninguna variante real de MASK.
    resultado = analizador.analizar(codigo_fuente)  # Procesa la instrucción para distinguir ambos tipos de error.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera únicamente los identificadores producidos.
    assert "LEX-001" in codigos  # Confirma que MAS permanezca clasificado como identificador fuera de lugar.
    assert "LEX-003" not in codigos  # Evita tratar cualquier palabra semejante como una simple diferencia de mayúsculas.


def prueba_elemento_numerico_unido_a_texto():  # Comprueba que un número seguido directamente por letras produzca LEX-004.
    analizador = AnalizadorLexico()  # Prepara el lexer utilizado por esta prueba.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50NAME Oficina"  # Une deliberadamente la cantidad 50 con la palabra NAME.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento para impedir que el fragmento se divida artificialmente.
    diagnosticos_lex_004 = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "LEX-004"]  # Recupera únicamente los diagnósticos correspondientes con elementos numéricos unidos a texto.
    assert len(diagnosticos_lex_004) == 1  # Confirma que exista exactamente una aparición del problema esperado.
    assert diagnosticos_lex_004[0].categoria == "Léxico"  # Verifica que LEX-004 pertenezca formalmente al lexer.
    assert diagnosticos_lex_004[0].fragmento == "50NAME"  # Confirma que se conserve el lexema completo en vez de separarlo entre NUMBER y NAME.


def prueba_mascara_unida_a_texto_produce_lex_004():  # Comprueba que una máscara CIDR pegada con letras también produzca LEX-004.
    analizador = AnalizadorLexico()  # Crea un analizador independiente.
    codigo_fuente = "IP 192.168.1.0 MASK /24HOSTS 50 NAME Oficina"  # Une deliberadamente /24 con la siguiente palabra reservada.
    resultado = analizador.analizar(codigo_fuente)  # Procesa el fragmento para comprobar que permanezca unido dentro del diagnóstico.
    diagnosticos_lex_004 = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "LEX-004"]  # Filtra exclusivamente los errores pertenecientes a esta regla.
    assert len(diagnosticos_lex_004) == 1  # Confirma que la máscara unida produzca una sola aparición.
    assert diagnosticos_lex_004[0].fragmento == "/24HOSTS"  # Comprueba que todo el lexema incorrecto sea señalado conjuntamente.


def prueba_lex_004_no_afecta_palabra_reservada_pegada_al_valor():  # Comprueba que LEX-004 no interfiera con IP192, MASK/24 y HOSTS50, que siguen permitidos.
    analizador = AnalizadorLexico()  # Prepara una nueva instancia de la fase léxica.
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"  # Utiliza las tres combinaciones aceptadas históricamente por el DSL.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento para comprobar que la nueva regla no genere falsos positivos.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los códigos producidos para esta entrada.
    assert "LEX-004" not in codigos  # Confirma que ninguna de las combinaciones válidas sea confundida con número unido a texto.
    assert resultado.diagnosticos == []  # Confirma que toda la instrucción continúe siendo léxicamente válida.