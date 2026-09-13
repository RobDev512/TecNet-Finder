# ============================================================
# Archivo: prueba_analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automatizadas correspondientes
# con la fase de análisis semántico de TecNet Finder.
#
# Las primeras pruebas verifican SEM-001, encargado de comprobar
# que la máscara CIDR se encuentre dentro del rango /8 a /30.
# También se verifica que un error semántico impida que solamente
# el bloque afectado continúe hacia las siguientes etapas.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa el lexer real para generar los tokens utilizados por las pruebas.
from Compilador.analizador_semantico import AnalizadorSemantico  # Importa la nueva fase semántica que será evaluada.
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


def prueba_sem001_acepta_limites_y_mascara_intermedia():  # Comprueba que /8, /24 y /30 pertenecen al rango permitido.
    codigo_fuente = (
        "IP 10.0.0.0 MASK /8 HOSTS 50 NAME RedA\n"
        "IP 192.168.1.0 MASK /24 HOSTS 30 NAME RedB\n"
        "IP 192.168.2.0 MASK /30 HOSTS 1 NAME RedC"
    )  # Crea tres bloques sintácticamente válidos con máscaras permitidas.

    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la nueva fase utilizando los tres casos válidos.

    assert len(resultado.bloques_validos) == 3  # Confirma que ninguna de las máscaras válidas fue rechazada.
    assert resultado.diagnosticos == []  # Confirma que SEM-001 no aparezca dentro del rango permitido.
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

    assert diagnostico.codigo == "SEM-001"  # Confirma que la regla aplicada sea la correspondiente con máscaras fuera de rango.
    assert diagnostico.linea == 1  # Comprueba que el error apunte a la primera línea del código utilizado.
    assert diagnostico.columna == 20  # Comprueba que el resaltado comience exactamente sobre la diagonal de /31.
    assert diagnostico.longitud == 3  # Comprueba que el resaltado cubra los tres caracteres de la máscara.
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