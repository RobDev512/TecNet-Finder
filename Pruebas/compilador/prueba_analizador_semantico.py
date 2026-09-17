# ============================================================
# Archivo: prueba_analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con la fase de análisis semántico de TecNet Finder.
#
# Comprueba las reglas SEM-001 a SEM-006:
#
# SEM-001 -> Máscara fuera del rango permitido.
# SEM-002 -> IP base que no representa una dirección de red.
# SEM-003 -> Cantidad de hosts no positiva.
# SEM-004 -> Capacidad total insuficiente para todas las subredes.
# SEM-005 -> Solicitud individual mayor que la red base.
# SEM-006 -> Traslape entre distintas redes base.
#
# Las pruebas también comprueban posiciones de los diagnósticos,
# recuperación de bloques válidos y convivencia entre varias
# reglas semánticas dentro de una misma instrucción.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Proporciona los tokens necesarios para construir correctamente los bloques que evaluará el semántico.
from Compilador.analizador_semantico import AnalizadorSemantico  # Importa directamente la fase cuya lógica se comprueba en este archivo.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Permite obtener bloques estructuralmente válidos antes de ejecutar las reglas semánticas.


def analizar_semanticamente(codigo_fuente: str):  # Ejecuta las dos fases previas y devuelve exclusivamente el resultado del análisis semántico.
    resultado_lexico = AnalizadorLexico().analizar(codigo_fuente)  # Convierte primero el código fuente en tokens utilizables por el parser.
    resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()  # Construye los bloques que posteriormente serán evaluados por significado.
    assert not resultado_lexico.tiene_errores  # Garantiza que cada prueba semántica utilice una entrada léxicamente correcta.
    assert not resultado_sintactico.tiene_errores  # Garantiza que el caso no falle antes de llegar realmente a la fase que se desea comprobar.
    return AnalizadorSemantico(bloques=resultado_sintactico.bloques, tokens=resultado_lexico.tokens).analizar()  # Ejecuta finalmente el semántico utilizando tanto bloques como ubicaciones léxicas.


def prueba_sem001_acepta_limites_y_mascara_intermedia():  # Comprueba que /8, /24 y /30 se encuentren dentro del rango semántico permitido.
    codigo_fuente = (
        "IP 10.0.0.0 MASK /8 HOSTS 50 NAME RedA\n"  # Utiliza exactamente el límite inferior permitido.
        "IP 192.168.1.0 MASK /24 HOSTS 30 NAME RedB\n"  # Utiliza una máscara intermedia habitual.
        "IP 192.168.2.0 MASK /30 HOSTS 1 NAME RedC"  # Utiliza exactamente el límite superior permitido.
    )
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta conjuntamente los tres casos válidos.
    assert len(resultado.bloques_validos) == 3  # Confirma que ninguna de las máscaras válidas sea descartada.
    assert resultado.diagnosticos == []  # Confirma que no exista ningún diagnóstico semántico.
    assert not resultado.tiene_errores  # Comprueba también la propiedad general calculada por ResultadoSemantico.


def prueba_sem001_rechaza_mascara_menor_que_ocho():  # Comprueba que cualquier prefijo inferior al límite permitido produzca SEM-001.
    resultado = analizar_semanticamente("IP 10.0.0.0 MASK /7 HOSTS 50 NAME Oficina")  # Utiliza /7, inmediatamente por debajo del límite aceptado.
    assert resultado.bloques_validos == []  # Confirma que el bloque semánticamente incorrecto no continúe como válido.
    assert len(resultado.diagnosticos) == 1  # Comprueba que solamente la máscara sea problemática en este caso.
    assert resultado.diagnosticos[0].codigo == "SEM-001"  # Verifica que la regla correspondiente sea la que rechace el bloque.
    assert resultado.diagnosticos[0].fragmento == "/7"  # Confirma que el diagnóstico conserve exactamente la máscara incorrecta.


def prueba_sem001_rechaza_mascara_mayor_que_treinta_y_ubica_fragmento():  # Comprueba SEM-001 sobre el límite superior y su ubicación exacta.
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 50 NAME Oficina"  # Utiliza /31, que se encuentra fuera del intervalo definido por TecNet Finder.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el caso para obtener su diagnóstico estructurado.
    diagnostico = resultado.diagnosticos[0]  # Recupera el único error esperado para revisar todos sus datos de posición.
    assert diagnostico.codigo == "SEM-001"  # Confirma que la máscara fuera de rango produzca el código esperado.
    assert diagnostico.linea == 1  # Comprueba que el diagnóstico se relacione con la primera línea.
    assert diagnostico.columna == codigo_fuente.index("/31")  # Verifica que la columna coincida exactamente con el comienzo de la máscara.
    assert diagnostico.longitud == len("/31")  # Confirma que el resaltado abarque la máscara completa.
    assert diagnostico.fragmento == "/31"  # Comprueba que se conserve el valor original del código fuente.


def prueba_sem001_conserva_bloques_validos_cuando_otro_falla():  # Comprueba que un error semántico no descarte instrucciones independientes correctas.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Valida\n"  # Declara un primer bloque completamente aceptable.
        "IP 10.0.0.0 MASK /31 HOSTS 1 NAME Invalida"  # Agrega un segundo bloque cuya máscara debe producir SEM-001.
    )
    resultado = analizar_semanticamente(codigo_fuente)  # Procesa conjuntamente ambas instrucciones.
    assert len(resultado.bloques_validos) == 1  # Confirma que solamente el primer bloque sobreviva al análisis.
    assert resultado.bloques_validos[0].nombre == "Valida"  # Comprueba que el bloque conservado sea exactamente el correcto.


def prueba_sem002_rechaza_ip_que_no_es_direccion_de_red():  # Comprueba que una dirección de host no pueda utilizarse directamente como IP base.
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina"  # Utiliza .5 donde la dirección de red correspondiente debería terminar en .0.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la validación conjunta de IP y máscara.
    diagnostico = resultado.diagnosticos[0]  # Recupera SEM-002 para comprobar contenido y ubicación.
    assert resultado.bloques_validos == []  # Confirma que una red con IP base incorrecta no llegue a las etapas posteriores.
    assert diagnostico.codigo == "SEM-002"  # Verifica que la regla aplicada corresponda específicamente con dirección de red.
    assert diagnostico.columna == codigo_fuente.index("192.168.1.5")  # Comprueba que el diagnóstico señale directamente la IP.
    assert diagnostico.fragmento == "192.168.1.5"  # Conserva exactamente la dirección original responsable del problema.
    assert "192.168.1.0" in diagnostico.mensaje  # Confirma que el mensaje incluya además la dirección de red correcta calculada.


def prueba_sem003_rechaza_cantidad_cero_y_ubica_host():  # Comprueba que una solicitud de cero hosts produzca SEM-003.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Oficina"  # Utiliza una cantidad sintácticamente válida pero semánticamente no positiva.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el análisis para localizar la cantidad específica.
    diagnostico = resultado.diagnosticos[0]  # Recupera el error producido por la solicitud inválida.
    assert resultado.bloques_validos == []  # Confirma que el bloque no continúe hacia VLSM.
    assert diagnostico.codigo == "SEM-003"  # Verifica que la cantidad cero utilice el código semántico correspondiente.
    assert diagnostico.columna == codigo_fuente.index("HOSTS 0") + len("HOSTS ")  # Comprueba que el resaltado comience exactamente sobre el número cero.
    assert diagnostico.fragmento == "0"  # Confirma que el valor problemático permanezca disponible dentro del diagnóstico.


def prueba_sem003_detecta_cada_cero_dentro_de_lista_hosts():  # Comprueba que cada cantidad inválida genere su propio SEM-003 dentro de una lista.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,0,0 NAME Oficina"  # Incluye dos cantidades cero en posiciones diferentes de HOSTS.
    resultado = analizar_semanticamente(codigo_fuente)  # Procesa la lista completa sin detenerse después del primer error.
    diagnosticos = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-003"]  # Conserva únicamente los errores pertenecientes a cantidades no positivas.
    inicio_lista = codigo_fuente.index("50,0,0")  # Localiza el comienzo de la lista para calcular las columnas esperadas.
    assert len(diagnosticos) == 2  # Confirma que cada cero haya producido un diagnóstico independiente.
    assert diagnosticos[0].columna == inicio_lista + len("50,")  # Verifica la ubicación exacta de la primera cantidad cero.
    assert diagnosticos[1].columna == inicio_lista + len("50,0,")  # Verifica la ubicación exacta de la segunda cantidad cero.


def prueba_sem002_y_sem003_pueden_detectarse_en_mismo_bloque():  # Comprueba que diferentes reglas independientes puedan informar problemas dentro de una misma instrucción.
    resultado = analizar_semanticamente("IP 192.168.1.5 MASK /24 HOSTS 0 NAME Oficina")  # Combina una IP base incorrecta con una cantidad no positiva.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los códigos obtenidos sin depender de su mensaje.
    assert "SEM-002" in codigos  # Confirma que la dirección de host continúe siendo detectada.
    assert "SEM-003" in codigos  # Confirma que la cantidad cero también se informe en la misma ejecución.
    assert resultado.bloques_validos == []  # Evita conservar un bloque que contiene cualquiera de estos problemas.


def prueba_sem005_rechaza_solicitud_individual_demasiado_grande():  # Comprueba que una sola subred que excede la capacidad completa produzca SEM-005.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 500 NAME Gigante"  # Solicita una cantidad que necesita un bloque de 512 direcciones dentro de una /24 de solamente 256.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la evaluación de capacidad individual.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-005")  # Recupera específicamente el diagnóstico de solicitud individual excesiva.
    assert diagnostico.fragmento == "500"  # Confirma que el NUMBER responsable sea utilizado como fragmento.
    assert "512 direcciones" in diagnostico.mensaje  # Comprueba que el mensaje informe el tamaño real del bloque requerido.
    assert "256 direcciones" in diagnostico.mensaje  # Comprueba que también muestre la capacidad de la red base disponible.


def prueba_sem005_acepta_solicitud_que_cabe_exactamente_en_red():  # Comprueba el caso límite donde una solicitud utiliza exactamente toda una /24.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /24 HOSTS 254 NAME Completa")  # Solicita 254 hosts, que junto con red y broadcast ocupan exactamente 256 direcciones.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera cualquier diagnóstico generado.
    assert "SEM-005" not in codigos  # Confirma que la solicitud individual no sea considerada demasiado grande.
    assert "SEM-004" not in codigos  # Confirma que la capacidad total tampoco exceda la red.
    assert len(resultado.bloques_validos) == 1  # Verifica que el bloque continúe completamente válido.


def prueba_sem004_rechaza_capacidad_total_real_de_vlsm():  # Comprueba que la suma utilice los bloques VLSM reales y no solamente la suma simple de hosts.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 100,100,100 NAME Saturada"  # Cada solicitud necesita un bloque de 128 direcciones, sumando 384 dentro de una red de 256.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la validación conjunta de capacidad.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-004")  # Recupera específicamente el error de capacidad global.
    assert diagnostico.fragmento == "HOSTS"  # Confirma que el problema general se relacione visualmente con la lista completa.
    assert "384 direcciones" in diagnostico.mensaje  # Comprueba que el cálculo muestre la capacidad realmente requerida por los tres bloques.
    assert "256 direcciones" in diagnostico.mensaje  # Comprueba que también se informe la capacidad total de la red base.


def prueba_sem004_acepta_dos_bloques_que_ocupan_exactamente_la_red():  # Comprueba que ocupar toda la capacidad disponible siga siendo válido.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /24 HOSTS 100,100 NAME Completa")  # Dos solicitudes de 100 hosts utilizan dos bloques /25 de 128 direcciones.
    assert resultado.diagnosticos == []  # Confirma que utilizar exactamente las 256 direcciones no produzca error.
    assert len(resultado.bloques_validos) == 1  # Comprueba que la red permanezca disponible para el cálculo VLSM.


def prueba_sem005_y_sem004_pueden_aparecer_juntos():  # Comprueba que los excesos individual y total puedan informarse simultáneamente cuando ambos existen.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /30 HOSTS 50 NAME Imposible")  # Utiliza una red de cuatro direcciones para una solicitud que necesita un bloque de 64.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todas las reglas semánticas activadas.
    assert "SEM-005" in codigos  # Confirma que individualmente la solicitud sea demasiado grande.
    assert "SEM-004" in codigos  # Confirma que, por consecuencia, la capacidad total también resulte insuficiente.


def prueba_capacidad_no_se_evalua_con_mascara_fuera_de_rango():  # Comprueba que las reglas de capacidad no utilicen una máscara que ya fue rechazada por SEM-001.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /31 HOSTS 500 NAME Invalida")  # Combina una máscara inválida con una solicitud extremadamente grande.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Obtiene las reglas que realmente fueron ejecutadas.
    assert codigos == ["SEM-001"]  # Confirma que la máscara detenga únicamente las comprobaciones que dependen matemáticamente de ella.


def prueba_sem006_rechaza_segunda_red_traslapada_y_ubica_ip():  # Comprueba que la segunda red superpuesta sea rechazada y señale su propia dirección.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara primero una red completa desde 192.168.1.0 hasta 192.168.1.255.
        "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"  # Declara después una /25 situada dentro del espacio ya ocupado.
    )
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la comparación entre ambas redes base.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-006")  # Recupera específicamente el conflicto de traslape.
    assert len(resultado.bloques_validos) == 1  # Confirma que solamente la primera red permanezca aceptada.
    assert resultado.bloques_validos[0].nombre == "Oficina"  # Comprueba que se conserve la declaración que apareció primero.
    assert diagnostico.linea == 2  # Confirma que el error se relacione con la red posterior que genera el conflicto.
    assert diagnostico.fragmento == "192.168.1.128"  # Verifica que la IP de la segunda red sea el fragmento señalado.
    assert "192.168.1.0/24" in diagnostico.mensaje  # Comprueba que el mensaje identifique claramente la red con la cual existe traslape.
    assert "línea 1" in diagnostico.mensaje  # Confirma que también se informe dónde fue declarada originalmente la red previa.


def prueba_sem006_acepta_redes_adyacentes_sin_traslape():  # Comprueba que dos redes consecutivas puedan tocar sus límites sin compartir ninguna dirección.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /25 HOSTS 50 NAME Izquierda\n"  # Declara la primera mitad de una antigua /24.
        "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Derecha"  # Declara la segunda mitad comenzando exactamente después del broadcast de la primera.
    )
    resultado = analizar_semanticamente(codigo_fuente)  # Comprueba ambas redes mediante la regla de traslape.
    assert resultado.diagnosticos == []  # Confirma que redes adyacentes no sean confundidas con redes superpuestas.
    assert len(resultado.bloques_validos) == 2  # Mantiene ambas instrucciones disponibles para las etapas posteriores.


def prueba_sem006_conserva_bloques_independientes_despues_de_conflicto():  # Comprueba que un traslape no impida procesar redes posteriores completamente independientes.
    codigo_fuente = (
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara la primera red que quedará aceptada.
        "IP 192.168.1.128 MASK /25 HOSTS 50 NAME Traslapada\n"  # Agrega una segunda red cuyo espacio se encuentra dentro de la primera.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"  # Declara una tercera red completamente independiente que debe conservarse.
    )
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la comparación de todos los candidatos en su orden original.
    nombres_validos = [bloque.nombre for bloque in resultado.bloques_validos]  # Recupera los nombres de las redes que sobrevivieron al análisis.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los códigos semánticos producidos.
    assert nombres_validos == ["Oficina", "Central"]  # Confirma que se rechace solamente la declaración traslapada y se conserve la red independiente posterior.
    assert codigos == ["SEM-006"]  # Confirma que el único problema semántico del conjunto sea precisamente el traslape.