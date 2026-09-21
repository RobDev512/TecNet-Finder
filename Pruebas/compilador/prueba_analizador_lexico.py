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
# También verifica que una IPv4 formada por cuatro componentes
# numéricos siga siendo IP_ADDRESS aunque un octeto exceda 255,
# dejando esa comprobación para SEM-007.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa exclusivamente la fase léxica que será evaluada por este conjunto de pruebas.


def prueba_entrada_valida_completa():  # Comprueba que una instrucción completa y correcta produzca exactamente la secuencia esperada de tokens.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer para evitar compartir estado entre pruebas.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Define una instrucción que utiliza todos los elementos principales del DSL.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta exclusivamente la fase léxica sobre la entrada proporcionada.
    tipos_esperados = ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "NUMBER", "COMMA", "NUMBER", "COMMA", "NUMBER", "NAME", "IDENTIFIER"]  # Define el orden exacto de categorías que debe generar el lexer.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Recupera solamente la categoría de cada token producido.
    assert tipos_obtenidos == tipos_esperados  # Confirma que todos los elementos hayan sido reconocidos en el orden correcto.
    assert resultado.diagnosticos == []  # Confirma que una entrada léxicamente correcta no produzca errores.


def prueba_identificador_fuera_de_lugar():  # Comprueba que un identificador utilizado sin NAME produzca específicamente LEX-001.
    analizador = AnalizadorLexico()  # Prepara una instancia limpia del analizador léxico.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 Oficina"  # Coloca deliberadamente Oficina en una posición donde el lenguaje no permite identificadores.
    resultado = analizador.analizar(codigo_fuente)  # Procesa la entrada para obtener el diagnóstico correspondiente.
    assert len(resultado.diagnosticos) == 1  # Confirma que solamente exista un problema léxico.
    assert resultado.diagnosticos[0].codigo == "LEX-001"  # Verifica que se utilice exactamente el código correspondiente con un identificador fuera de lugar.
    assert resultado.diagnosticos[0].categoria == "Léxico"  # Confirma que el problema pertenezca formalmente con la fase léxica.
    assert resultado.diagnosticos[0].fragmento == "Oficina"  # Comprueba que el diagnóstico conserve exactamente el texto responsable.


def prueba_simbolo_no_reconocido():  # Comprueba que un carácter ajeno al DSL produzca específicamente LEX-002.
    analizador = AnalizadorLexico()  # Crea una instancia nueva del lexer para este caso.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina @"  # Añade deliberadamente un símbolo que no pertenece con el lenguaje.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento completo sobre la entrada alterada.
    assert len(resultado.diagnosticos) == 1  # Confirma que el único problema corresponda con el símbolo agregado.
    assert resultado.diagnosticos[0].codigo == "LEX-002"  # Comprueba que un elemento completamente desconocido utilice el código esperado.
    assert resultado.diagnosticos[0].categoria == "Léxico"  # Confirma la categoría formal asociada con el diagnóstico.
    assert resultado.diagnosticos[0].fragmento == "@"  # Verifica que se conserve exactamente el símbolo responsable.


def prueba_identificador_despues_de_name():  # Comprueba que un identificador escrito inmediatamente después de NAME sea aceptado normalmente.
    analizador = AnalizadorLexico()  # Crea un lexer independiente para evitar cualquier estado compartido.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"  # Utiliza NAME seguido correctamente por un identificador.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento léxico de la instrucción.
    identificadores = [token for token in resultado.tokens if token.tipo == "IDENTIFIER"]  # Recupera exclusivamente los tokens clasificados como identificadores.
    assert len(identificadores) == 1  # Confirma que solamente Oficina haya sido reconocida dentro de esta categoría.
    assert identificadores[0].valor == "Oficina"  # Comprueba que el contenido del token corresponda exactamente con el nombre escrito.
    assert resultado.diagnosticos == []  # Confirma que la utilización correcta de NAME no produzca errores.


def prueba_palabras_reservadas_pegadas():  # Comprueba que las formas históricamente permitidas IP192, MASK/24 y HOSTS50 continúen reconociéndose correctamente.
    analizador = AnalizadorLexico()  # Prepara una nueva instancia del analizador.
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"  # Utiliza deliberadamente las tres palabras reservadas sin espacio posterior.
    resultado = analizador.analizar(codigo_fuente)  # Procesa la entrada para comprobar que pueda dividirse correctamente.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Recupera la secuencia de categorías realmente producida.
    tipos_esperados = ["IP", "IP_ADDRESS", "MASK", "SUBNET_MASK", "HOSTS", "NUMBER", "NAME", "IDENTIFIER"]  # Define la secuencia esperada aun cuando determinadas palabras estén pegadas.
    assert tipos_obtenidos == tipos_esperados  # Confirma que cada palabra reservada y su valor hayan sido separados correctamente.
    assert resultado.diagnosticos == []  # Confirma que esta escritura admitida no produzca un error léxico.


def prueba_ip_incompleta_no_es_error_lexico():  # Comprueba que una dirección incompleta permanezca disponible para que posteriormente sea rechazada por el parser.
    analizador = AnalizadorLexico()  # Crea el lexer utilizado exclusivamente por esta prueba.
    codigo_fuente = "IP 192.168.1. MASK /24 HOSTS 50"  # Utiliza una IPv4 incompleta cuyo problema corresponde con la estructura sintáctica.
    resultado = analizador.analizar(codigo_fuente)  # Recupera los elementos parciales que todavía pueden reconocerse léxicamente.
    tipos_obtenidos = [token.tipo for token in resultado.tokens]  # Extrae las categorías producidas dentro de la dirección incompleta.
    assert "NUMBER" in tipos_obtenidos  # Confirma que los componentes numéricos parciales sigan representados mediante NUMBER.
    assert "DOT" in tipos_obtenidos  # Confirma que los puntos individuales permanezcan disponibles para la recuperación sintáctica.
    assert resultado.diagnosticos == []  # Evita convertir en error léxico una construcción cuyo problema corresponde con SIN-001.


def prueba_ip_con_octeto_mayor_255_sigue_siendo_ip_address():  # Comprueba que la estructura de una IPv4 completa se reconozca aunque su significado numérico deba rechazarse posteriormente.
    analizador = AnalizadorLexico()  # Prepara una nueva instancia del lexer.
    codigo_fuente = "IP 192.168.1.256 MASK /24 HOSTS 50 NAME Oficina"  # Utiliza deliberadamente un cuarto componente numérico que excede el valor permitido de un octeto.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta exclusivamente el análisis léxico para comprobar la separación correcta de responsabilidades.
    direcciones = [token for token in resultado.tokens if token.tipo == "IP_ADDRESS"]  # Recupera solamente las direcciones estructuralmente reconocidas.
    assert len(direcciones) == 1  # Confirma que la secuencia completa se haya reconocido como una única dirección.
    assert direcciones[0].valor == "192.168.1.256"  # Comprueba que el lexer conserve sin alterar el texto que posteriormente evaluará SEM-007.
    assert resultado.diagnosticos == []  # Confirma que exceder 255 ya no se clasifique como problema perteneciente con la fase léxica.


def prueba_palabra_reservada_con_mayusculas_incorrectas():  # Comprueba que una palabra reservada real con capitalización incorrecta produzca LEX-003.
    analizador = AnalizadorLexico()  # Crea una instancia independiente del lexer.
    codigo_fuente = "IP 192.168.1.0 mask /24 HOSTS 50 NAME Oficina"  # Escribe deliberadamente MASK utilizando letras minúsculas.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta la fase léxica para detectar la variante incorrecta.
    diagnosticos_lex_003 = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "LEX-003"]  # Conserva exclusivamente las apariciones correspondientes con esta regla.
    assert len(diagnosticos_lex_003) == 1  # Confirma que solamente la palabra mask produzca LEX-003.
    assert diagnosticos_lex_003[0].categoria == "Léxico"  # Comprueba que la categoría formal permanezca correcta.
    assert diagnosticos_lex_003[0].fragmento == "mask"  # Conserva exactamente la variante escrita por el usuario.
    assert diagnosticos_lex_003[0].linea == 1  # Confirma que el problema se encuentre asociado con la única línea de la prueba.
    assert diagnosticos_lex_003[0].columna == 15  # Comprueba que el diagnóstico señale exactamente la posición donde comienza mask.


def prueba_lex_003_no_reemplaza_identificador_mal_escrito_generico():  # Comprueba que un texto parecido con una reservada pero realmente inexistente conserve LEX-001.
    analizador = AnalizadorLexico()  # Crea una instancia limpia del analizador.
    codigo_fuente = "IP 192.168.1.0 MAS /24 HOSTS 50 NAME Oficina"  # Utiliza MAS, que no representa ninguna variante válida de MASK.
    resultado = analizador.analizar(codigo_fuente)  # Procesa la instrucción para distinguir ambos tipos de diagnóstico.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera únicamente los identificadores producidos.
    assert "LEX-001" in codigos  # Confirma que MAS permanezca clasificado como identificador fuera de lugar.
    assert "LEX-003" not in codigos  # Evita tratar cualquier palabra semejante como una simple diferencia de capitalización.


def prueba_elemento_numerico_unido_a_texto():  # Comprueba que una cantidad seguida directamente por letras produzca específicamente LEX-004.
    analizador = AnalizadorLexico()  # Prepara el lexer utilizado por esta prueba.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50NAME Oficina"  # Une deliberadamente la cantidad 50 con la palabra NAME.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento para impedir que el fragmento sea dividido artificialmente.
    diagnosticos_lex_004 = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "LEX-004"]  # Recupera exclusivamente los diagnósticos pertenecientes con esta regla.
    assert len(diagnosticos_lex_004) == 1  # Confirma que exista exactamente una aparición del problema esperado.
    assert diagnosticos_lex_004[0].categoria == "Léxico"  # Verifica que LEX-004 pertenezca formalmente con el lexer.
    assert diagnosticos_lex_004[0].fragmento == "50NAME"  # Confirma que el lexema completo permanezca unido dentro del diagnóstico.


def prueba_mascara_unida_a_texto_produce_lex_004():  # Comprueba que una máscara CIDR escrita directamente junto con letras también produzca LEX-004.
    analizador = AnalizadorLexico()  # Crea un analizador independiente para este escenario.
    codigo_fuente = "IP 192.168.1.0 MASK /24HOSTS 50 NAME Oficina"  # Une deliberadamente /24 con la siguiente palabra reservada.
    resultado = analizador.analizar(codigo_fuente)  # Procesa el fragmento para comprobar que se conserve como una unidad incorrecta.
    diagnosticos_lex_004 = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "LEX-004"]  # Filtra únicamente los errores pertenecientes con LEX-004.
    assert len(diagnosticos_lex_004) == 1  # Confirma que la máscara unida produzca solamente una aparición del diagnóstico.
    assert diagnosticos_lex_004[0].fragmento == "/24HOSTS"  # Comprueba que todo el lexema incorrecto se señale conjuntamente.


def prueba_lex_004_no_afecta_palabra_reservada_pegada_al_valor():  # Comprueba que LEX-004 no interfiera con las combinaciones IP192, MASK/24 y HOSTS50 permitidas por el DSL.
    analizador = AnalizadorLexico()  # Prepara una nueva instancia de la fase léxica.
    codigo_fuente = "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"  # Utiliza las tres combinaciones históricamente aceptadas.
    resultado = analizador.analizar(codigo_fuente)  # Ejecuta el reconocimiento para comprobar que la regla no produzca falsos positivos.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los códigos producidos durante esta ejecución.
    assert "LEX-004" not in codigos  # Confirma que ninguna combinación válida sea confundida con un número unido incorrectamente con texto.
    assert resultado.diagnosticos == []  # Confirma que toda la instrucción continúe siendo léxicamente válida.