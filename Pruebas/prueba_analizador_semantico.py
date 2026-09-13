# ============================================================
# Archivo: prueba_analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automatizadas correspondientes
# con la fase de análisis semántico de TecNet Finder.
#
# Las pruebas verifican actualmente SEM-001, SEM-002 y SEM-003:
# rango de máscara CIDR, dirección base de red y cantidades
# positivas dentro de la lista HOSTS.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa el lexer real para generar los tokens utilizados por las pruebas.
from Compilador.analizador_semantico import AnalizadorSemantico  # Importa la fase semántica que será evaluada.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa el parser real para obtener bloques sintácticamente válidos.


def analizar_semanticamente(codigo_fuente: str):  # Ejecuta las fases previas necesarias antes de invocar directamente el analizador semántico.
    resultado_lexico = AnalizadorLexico().analizar(codigo_fuente)  # Convierte el código de prueba en tokens utilizando el lexer real.
    resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()  # Construye los bloques sintácticos a partir de los tokens reconocidos.

    assert not resultado_lexico.tiene_errores  # Garantiza que la prueba no esté fallando por una causa léxica ajena al semántico.
    assert not resultado_sintactico.tiene_errores  # Garantiza que todos los bloques usados para la prueba superaron la gramática.

    return AnalizadorSemantico(
        bloques=resultado_sintactico.bloques,
        tokens=resultado_lexico.tokens,
    ).analizar()  # Ejecuta exclusivamente la fase semántica sobre una entrada previamente válida.


def prueba_sem001_acepta_limites_y_mascara_intermedia():  # Comprueba que /8, /24 y /30 pertenezcan al rango permitido.
    codigo_fuente = (
        "IP 10.0.0.0 MASK /8 HOSTS 50 NAME RedA\n"
        "IP 192.168.1.0 MASK /24 HOSTS 30 NAME RedB\n"
        "IP 192.168.2.0 MASK /30 HOSTS 1 NAME RedC"
    )  # Crea tres bloques sintáctica y semánticamente válidos.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la fase utilizando los tres casos válidos.

    assert len(resultado.bloques_validos) == 3  # Confirma que ninguna de las instrucciones válidas haya sido rechazada.
    assert resultado.diagnosticos == []  # Confirma que ninguna regla semántica produzca errores.
    assert not resultado.tiene_errores  # Confirma que el resultado completo permanezca libre de errores semánticos.


def prueba_sem001_rechaza_mascara_menor_que_ocho():  # Comprueba el límite inferior definido para TecNet Finder.
    codigo_fuente = "IP 10.0.0.0 MASK /7 HOSTS 50 NAME Oficina"  # Utiliza una máscara sintácticamente correcta pero semánticamente fuera de rango.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el analizador semántico sobre el caso inválido.

    assert resultado.bloques_validos == []  # Confirma que el bloque afectado no pueda continuar hacia las siguientes etapas.
    assert len(resultado.diagnosticos) == 1  # Confirma que la condición produzca un único diagnóstico semántico.
    assert resultado.diagnosticos[0].codigo == "SEM-001"  # Comprueba que el error corresponda con el código reservado para la máscara.
    assert resultado.diagnosticos[0].fragmento == "/7"  # Comprueba que el diagnóstico conserve exactamente la máscara problemática.
    assert resultado.tiene_errores  # Confirma que SEM-001 marque el resultado semántico como erróneo.


def prueba_sem001_rechaza_mascara_mayor_que_treinta_y_ubica_fragmento():  # Comprueba el límite superior y la posición exacta del diagnóstico.
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 50 NAME Oficina"  # Coloca una máscara inválida en una posición conocida del código.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la validación semántica sobre la máscara /31.

    diagnostico = resultado.diagnosticos[0]  # Recupera el diagnóstico producido para revisar todos sus datos de ubicación.
    columna_esperada = codigo_fuente.index("/31")  # Calcula la posición exacta directamente desde el código utilizado por la prueba.

    assert diagnostico.codigo == "SEM-001"  # Confirma que la regla aplicada sea la correspondiente con máscaras fuera de rango.
    assert diagnostico.linea == 1  # Comprueba que el error apunte a la primera línea del código utilizado.
    assert diagnostico.columna == columna_esperada  # Comprueba que el resaltado comience exactamente sobre la diagonal de /31.
    assert diagnostico.longitud == len("/31")  # Comprueba que el resaltado cubra exactamente los caracteres de la máscara.
    assert diagnostico.fragmento == "/31"  # Comprueba que la interfaz pueda relacionar el diagnóstico con el texto correcto.


def prueba_sem001_conserva_bloques_validos_cuando_otro_falla():  # Comprueba que un error semántico no elimine instrucciones independientes correctas.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Valida\n"
        "IP 10.0.0.0 MASK /31 HOSTS 1 NAME Invalida"
    )  # Combina un bloque permitido y otro cuya máscara incumple SEM-001.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el semántico sobre una entrada parcialmente válida.

    assert len(resultado.bloques_validos) == 1  # Confirma que únicamente el bloque correcto permanezca disponible.
    assert resultado.bloques_validos[0].nombre == "Valida"  # Confirma que el bloque conservado sea exactamente el primero.
    assert len(resultado.diagnosticos) == 1  # Confirma que únicamente el bloque incorrecto produzca SEM-001.
    assert resultado.diagnosticos[0].fragmento == "/31"  # Comprueba que el error continúe asociado con la máscara incorrecta.


def prueba_sem002_rechaza_ip_que_no_es_direccion_de_red():  # Comprueba que una dirección de host no sea aceptada como IP base de una red.
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina"  # Utiliza una IP válida cuya parte de host no está en cero para /24.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la validación semántica sobre la relación entre IP y máscara.

    diagnostico = resultado.diagnosticos[0]  # Recupera SEM-002 para comprobar tanto su clasificación como su ubicación.
    ip_incorrecta = "192.168.1.5"  # Conserva el fragmento que debe señalarse para evitar repetir valores de prueba.
    columna_esperada = codigo_fuente.index(ip_incorrecta)  # Obtiene directamente la columna inicial de la dirección IPv4.

    assert resultado.bloques_validos == []  # Confirma que la instrucción no pueda continuar mientras su IP base sea incorrecta.
    assert diagnostico.codigo == "SEM-002"  # Comprueba que el problema corresponda con la regla de dirección de red.
    assert diagnostico.linea == 1  # Comprueba que el diagnóstico permanezca sobre la instrucción original.
    assert diagnostico.columna == columna_esperada  # Comprueba que el resaltado comience exactamente sobre la dirección IPv4.
    assert diagnostico.longitud == len(ip_incorrecta)  # Comprueba que el resaltado cubra exactamente todos los caracteres de la dirección.
    assert diagnostico.fragmento == ip_incorrecta  # Conserva exactamente la IP escrita por el usuario.
    assert "192.168.1.0" in diagnostico.mensaje  # Comprueba que el mensaje informe cuál sería la dirección de red correcta.


def prueba_sem003_rechaza_cantidad_cero_y_ubica_host():  # Comprueba que solicitar cero hosts sea un error semántico y no léxico o sintáctico.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Oficina"  # Coloca una cantidad cero dentro de una instrucción formalmente correcta.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la fase semántica sobre el valor cero.

    diagnostico = resultado.diagnosticos[0]  # Recupera el diagnóstico asociado con la cantidad no positiva.
    fragmento_hosts = "HOSTS 0"  # Conserva la sección concreta utilizada para localizar la cantidad de forma inequívoca.
    columna_esperada = codigo_fuente.index(fragmento_hosts) + len("HOSTS ")  # Calcula el inicio exacto del NUMBER ubicado después de HOSTS.

    assert resultado.bloques_validos == []  # Confirma que la instrucción no continúe hacia VLSM.
    assert diagnostico.codigo == "SEM-003"  # Comprueba que la cantidad sea clasificada mediante la regla correspondiente.
    assert diagnostico.linea == 1  # Comprueba que el diagnóstico permanezca en la línea original.
    assert diagnostico.columna == columna_esperada  # Comprueba que el resaltado comience exactamente sobre el NUMBER situado después de HOSTS.
    assert diagnostico.longitud == len("0")  # Comprueba que únicamente el carácter cero quede relacionado con el error.
    assert diagnostico.fragmento == "0"  # Conserva exactamente la cantidad problemática.


def prueba_sem003_detecta_cada_cero_dentro_de_lista_hosts():  # Comprueba que diferentes solicitudes inválidas dentro del mismo bloque produzcan diagnósticos independientes.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,0,0 NAME Oficina"  # Incluye dos cantidades inválidas dentro de una lista sintácticamente correcta.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el análisis sobre ambas apariciones de cero.

    diagnosticos_sem003 = [
        diagnostico
        for diagnostico in resultado.diagnosticos
        if diagnostico.codigo == "SEM-003"
    ]  # Reúne exclusivamente los errores correspondientes con cantidades no positivas.

    inicio_lista = codigo_fuente.index("50,0,0")  # Localiza exactamente el inicio de la lista HOSTS utilizada por esta prueba.
    columna_primer_cero = inicio_lista + len("50,")  # Calcula la posición del primer cero que constituye una solicitud independiente.
    columna_segundo_cero = inicio_lista + len("50,0,")  # Calcula la posición del segundo cero independiente dentro de la misma lista.

    assert resultado.bloques_validos == []  # Confirma que el bloque completo sea rechazado mientras contenga cantidades inválidas.
    assert len(diagnosticos_sem003) == 2  # Comprueba que cada cero produzca su propio diagnóstico.
    assert diagnosticos_sem003[0].columna == columna_primer_cero  # Comprueba la posición exacta de la primera cantidad cero.
    assert diagnosticos_sem003[1].columna == columna_segundo_cero  # Comprueba la posición exacta de la segunda cantidad cero.
    assert all(diagnostico.fragmento == "0" for diagnostico in diagnosticos_sem003)  # Confirma que ambos diagnósticos señalen únicamente su NUMBER correspondiente.


def prueba_sem002_y_sem003_pueden_detectarse_en_mismo_bloque():  # Comprueba que reglas independientes puedan informar varios problemas sin ocultarse entre ellas.
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 0 NAME Oficina"  # Combina una IP base incorrecta con una cantidad de hosts no válida.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta todas las reglas disponibles sobre la misma instrucción.

    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera las clasificaciones producidas durante el análisis.

    assert "SEM-002" in codigos  # Confirma que la relación incorrecta entre IP y máscara sea detectada.
    assert "SEM-003" in codigos  # Confirma que el cero sea detectado aunque el bloque ya tenga otro error semántico.
    assert len(resultado.diagnosticos) == 2  # Comprueba que no se produzcan diagnósticos adicionales inesperados.
    assert resultado.bloques_validos == []  # Confirma que un bloque con ambos problemas permanezca excluido.