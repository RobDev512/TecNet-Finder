# ============================================================
# Archivo: prueba_analizador_semantico.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con la fase de análisis semántico de TecNet Finder.
#
# Comprueba las reglas SEM-001 a SEM-009:
#
# SEM-001 -> Máscara fuera del rango permitido.
# SEM-002 -> IP base que no representa una dirección de red.
# SEM-003 -> Cantidad de hosts no positiva.
# SEM-004 -> Capacidad total insuficiente para las subredes.
# SEM-005 -> Solicitud individual mayor que la red base.
# SEM-006 -> Traslape entre distintas redes base.
# SEM-007 -> Octeto IPv4 fuera del rango 0 a 255.
# SEM-008 -> Red base declarada nuevamente con otros datos.
# SEM-009 -> Misma IP base utilizada con otra máscara.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Proporciona los tokens necesarios para construir correctamente los bloques evaluados por esta fase.
from Compilador.analizador_semantico import AnalizadorSemantico  # Importa directamente el analizador cuya lógica será comprobada.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Permite construir bloques estructuralmente válidos antes de ejecutar las reglas semánticas.


def analizar_semanticamente(codigo_fuente: str):  # Ejecuta las fases previas y devuelve exclusivamente el resultado producido por el análisis semántico.
    resultado_lexico = AnalizadorLexico().analizar(codigo_fuente)  # Convierte primero el texto recibido en una secuencia de tokens.
    resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()  # Construye los bloques utilizados posteriormente por el semántico.
    assert not resultado_lexico.tiene_errores  # Garantiza que cada caso de esta suite alcance realmente la fase semántica.
    assert not resultado_sintactico.tiene_errores  # Garantiza que ninguna prueba falle previamente debido con la estructura gramatical.
    return AnalizadorSemantico(bloques=resultado_sintactico.bloques, tokens=resultado_lexico.tokens).analizar()  # Ejecuta finalmente el análisis semántico utilizando bloques y ubicaciones léxicas.


def prueba_sem001_acepta_limites_y_mascara_intermedia():  # Comprueba que /8, /24 y /30 pertenezcan al rango de máscaras admitido.
    codigo_fuente = "IP 10.0.0.0 MASK /8 HOSTS 50 NAME RedA\nIP 192.168.1.0 MASK /24 HOSTS 30 NAME RedB\nIP 192.168.2.0 MASK /30 HOSTS 1 NAME RedC"  # Declara conjuntamente el límite inferior, un valor intermedio y el límite superior.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta las tres instrucciones dentro de una misma entrada.
    assert len(resultado.bloques_validos) == 3  # Confirma que ninguna máscara perteneciente al intervalo sea descartada.
    assert resultado.diagnosticos == []  # Confirma que ninguna regla semántica produzca errores sobre estos casos.
    assert not resultado.tiene_errores  # Comprueba también la propiedad general calculada por ResultadoSemantico.


def prueba_sem001_rechaza_mascara_menor_que_ocho():  # Comprueba que un prefijo inmediatamente inferior al límite permitido produzca SEM-001.
    resultado = analizar_semanticamente("IP 10.0.0.0 MASK /7 HOSTS 50 NAME Oficina")  # Utiliza deliberadamente /7 como máscara fuera del intervalo admitido.
    assert resultado.bloques_validos == []  # Confirma que la instrucción semánticamente incorrecta no permanezca como bloque válido.
    assert len(resultado.diagnosticos) == 1  # Comprueba que solamente exista el problema correspondiente con la máscara.
    assert resultado.diagnosticos[0].codigo == "SEM-001"  # Verifica que se produzca exactamente el código esperado.
    assert resultado.diagnosticos[0].fragmento == "/7"  # Confirma que el diagnóstico conserve la máscara responsable.


def prueba_sem001_rechaza_mascara_mayor_que_treinta_y_ubica_fragmento():  # Comprueba el límite superior de SEM-001 y la precisión de su ubicación.
    codigo_fuente = "IP 192.168.1.0 MASK /31 HOSTS 50 NAME Oficina"  # Utiliza deliberadamente /31, que se encuentra fuera del intervalo definido por TecNet Finder.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el análisis semántico para recuperar el diagnóstico estructurado.
    diagnostico = resultado.diagnosticos[0]  # Obtiene el único error esperado para revisar todos sus datos.
    assert diagnostico.codigo == "SEM-001"  # Confirma que la regla aplicada corresponda específicamente con máscara fuera de rango.
    assert diagnostico.linea == 1  # Comprueba que el diagnóstico pertenezca con la primera línea.
    assert diagnostico.columna == codigo_fuente.index("/31")  # Verifica que el resaltado comience exactamente sobre la máscara.
    assert diagnostico.longitud == len("/31")  # Confirma que la longitud cubra completamente el valor incorrecto.
    assert diagnostico.fragmento == "/31"  # Comprueba que el texto original permanezca disponible dentro del diagnóstico.


def prueba_sem001_conserva_bloques_validos_cuando_otro_falla():  # Comprueba que un error de máscara no descarte otras instrucciones independientes.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Valida\nIP 10.0.0.0 MASK /31 HOSTS 1 NAME Invalida"  # Combina una red correcta con otra cuya máscara debe producir SEM-001.
    resultado = analizar_semanticamente(codigo_fuente)  # Procesa ambas instrucciones dentro de una misma ejecución.
    assert len(resultado.bloques_validos) == 1  # Confirma que solamente permanezca disponible la primera declaración.
    assert resultado.bloques_validos[0].nombre == "Valida"  # Comprueba que el bloque conservado sea exactamente el correcto.


def prueba_sem002_rechaza_ip_que_no_es_direccion_de_red():  # Comprueba que una dirección de host no pueda utilizarse directamente como dirección base.
    codigo_fuente = "IP 192.168.1.5 MASK /24 HOSTS 50 NAME Oficina"  # Utiliza .5 donde la dirección de red correspondiente con /24 debería terminar en .0.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la validación conjunta de IP y máscara.
    diagnostico = resultado.diagnosticos[0]  # Recupera SEM-002 para comprobar su contenido y ubicación.
    assert resultado.bloques_validos == []  # Confirma que una IP base incorrecta no continúe disponible para VLSM.
    assert diagnostico.codigo == "SEM-002"  # Verifica que se utilice específicamente la regla de dirección de red.
    assert diagnostico.columna == codigo_fuente.index("192.168.1.5")  # Comprueba que el diagnóstico señale directamente la IP proporcionada.
    assert diagnostico.fragmento == "192.168.1.5"  # Conserva exactamente la dirección original responsable del problema.
    assert "192.168.1.0" in diagnostico.mensaje  # Confirma que el mensaje también incluya la dirección de red correcta calculada.


def prueba_sem003_rechaza_cantidad_cero_y_ubica_host():  # Comprueba que una solicitud igual con cero produzca SEM-003.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 0 NAME Oficina"  # Utiliza una cantidad sintácticamente válida pero semánticamente inutilizable.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el análisis para localizar la cantidad específica.
    diagnostico = resultado.diagnosticos[0]  # Recupera el error producido por la cantidad no positiva.
    assert resultado.bloques_validos == []  # Confirma que el bloque no continúe disponible para VLSM.
    assert diagnostico.codigo == "SEM-003"  # Verifica que cero utilice exactamente la regla correspondiente.
    assert diagnostico.columna == codigo_fuente.index("HOSTS 0") + len("HOSTS ")  # Comprueba que el resaltado comience sobre el NUMBER y no sobre HOSTS.
    assert diagnostico.fragmento == "0"  # Confirma que se conserve exactamente el valor problemático.


def prueba_sem003_detecta_cada_cero_dentro_de_lista_hosts():  # Comprueba que cada cantidad no positiva genere su propio diagnóstico independiente.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50,0,0 NAME Oficina"  # Incluye deliberadamente dos cantidades cero dentro de una misma lista.
    resultado = analizar_semanticamente(codigo_fuente)  # Procesa la lista completa sin detenerse después del primer valor inválido.
    diagnosticos = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-003"]  # Conserva exclusivamente los errores pertenecientes con cantidades no positivas.
    inicio_lista = codigo_fuente.index("50,0,0")  # Localiza el comienzo de la lista para calcular las columnas esperadas.
    assert len(diagnosticos) == 2  # Confirma que cada cero haya producido un diagnóstico independiente.
    assert diagnosticos[0].columna == inicio_lista + len("50,")  # Verifica la ubicación exacta del primer cero.
    assert diagnosticos[1].columna == inicio_lista + len("50,0,")  # Verifica la ubicación exacta del segundo cero.


def prueba_sem002_y_sem003_pueden_detectarse_en_mismo_bloque():  # Comprueba que reglas independientes puedan informar simultáneamente problemas diferentes dentro de una misma instrucción.
    resultado = analizar_semanticamente("IP 192.168.1.5 MASK /24 HOSTS 0 NAME Oficina")  # Combina una IP base incorrecta con una cantidad de hosts no positiva.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los identificadores producidos sin depender de sus mensajes.
    assert "SEM-002" in codigos  # Confirma que continúe detectándose la dirección de host utilizada como base.
    assert "SEM-003" in codigos  # Confirma que también sea detectada la cantidad cero dentro de la misma ejecución.
    assert resultado.bloques_validos == []  # Evita conservar un bloque que contiene cualquiera de estos problemas.


def prueba_sem005_rechaza_solicitud_individual_demasiado_grande():  # Comprueba que una sola solicitud mayor con toda la red produzca SEM-005.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 500 NAME Gigante"  # Solicita una cantidad que requiere 512 direcciones dentro de una red que solamente dispone de 256.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la evaluación de capacidad individual.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-005")  # Recupera específicamente el diagnóstico correspondiente con la solicitud excesiva.
    assert diagnostico.fragmento == "500"  # Confirma que el NUMBER responsable sea utilizado como fragmento visible.
    assert "512 direcciones" in diagnostico.mensaje  # Comprueba que el mensaje indique el tamaño real del bloque requerido.
    assert "256 direcciones" in diagnostico.mensaje  # Comprueba que también informe la capacidad completa de la red base.


def prueba_sem005_acepta_solicitud_que_cabe_exactamente_en_red():  # Comprueba el caso límite donde una solicitud utiliza exactamente toda la capacidad disponible.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /24 HOSTS 254 NAME Completa")  # Solicita 254 hosts que junto con red y broadcast necesitan exactamente 256 direcciones.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera cualquier diagnóstico producido por esta entrada.
    assert "SEM-005" not in codigos  # Confirma que la solicitud individual no sea considerada demasiado grande.
    assert "SEM-004" not in codigos  # Confirma que la capacidad total tampoco sea considerada insuficiente.
    assert len(resultado.bloques_validos) == 1  # Verifica que la instrucción permanezca completamente válida.


def prueba_sem004_rechaza_capacidad_total_real_de_vlsm():  # Comprueba que la capacidad conjunta utilice los bloques VLSM reales y no solamente la suma simple de hosts.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 100,100,100 NAME Saturada"  # Cada solicitud necesita un bloque de 128 direcciones y las tres juntas requieren 384.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la comprobación completa de capacidad.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-004")  # Recupera específicamente el error global de capacidad.
    assert diagnostico.fragmento == "HOSTS"  # Confirma que el problema perteneciente con la lista completa señale la palabra reservada HOSTS.
    assert "384 direcciones" in diagnostico.mensaje  # Comprueba que el cálculo muestre la capacidad realmente requerida por las tres solicitudes.
    assert "256 direcciones" in diagnostico.mensaje  # Comprueba que también informe la capacidad disponible dentro de la /24.


def prueba_sem004_acepta_dos_bloques_que_ocupan_exactamente_la_red():  # Comprueba que utilizar exactamente toda la capacidad disponible continúe siendo válido.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /24 HOSTS 100,100 NAME Completa")  # Dos solicitudes de 100 hosts utilizan conjuntamente dos bloques /25.
    assert resultado.diagnosticos == []  # Confirma que ocupar exactamente las 256 direcciones no produzca error.
    assert len(resultado.bloques_validos) == 1  # Comprueba que la red permanezca disponible para el cálculo VLSM.


def prueba_sem005_y_sem004_pueden_aparecer_juntos():  # Comprueba que los excesos individual y global puedan informarse simultáneamente cuando ambos existen.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /30 HOSTS 50 NAME Imposible")  # Utiliza una red de cuatro direcciones para una solicitud que necesita un bloque de 64.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todas las reglas semánticas activadas.
    assert "SEM-005" in codigos  # Confirma que individualmente la solicitud sea demasiado grande.
    assert "SEM-004" in codigos  # Confirma que por consecuencia la capacidad total también resulte insuficiente.


def prueba_capacidad_no_se_evalua_con_mascara_fuera_de_rango():  # Comprueba que las reglas matemáticas de capacidad no utilicen una máscara previamente rechazada.
    resultado = analizar_semanticamente("IP 192.168.1.0 MASK /31 HOSTS 500 NAME Invalida")  # Combina una máscara inválida con una solicitud extremadamente grande.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera las reglas que realmente fueron ejecutadas.
    assert codigos == ["SEM-001"]  # Confirma que únicamente se informe primero la máscara cuyo valor impide realizar los cálculos posteriores.


def prueba_sem006_rechaza_segunda_red_traslapada_y_ubica_ip():  # Comprueba que una red posterior contenida dentro de otra produzca SEM-006 y señale su dirección.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\nIP 192.168.1.128 MASK /25 HOSTS 50 NAME Laboratorio"  # Declara primero una /24 y después una /25 situada dentro del mismo espacio.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la comparación entre ambas redes base.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-006")  # Recupera específicamente el conflicto de traslape.
    assert len(resultado.bloques_validos) == 1  # Confirma que solamente la primera declaración permanezca aceptada.
    assert resultado.bloques_validos[0].nombre == "Oficina"  # Comprueba que se conserve la red que apareció primero.
    assert diagnostico.linea == 2  # Confirma que el error se relacione con la declaración posterior.
    assert diagnostico.fragmento == "192.168.1.128"  # Verifica que la dirección de la segunda red sea utilizada como fragmento.
    assert "192.168.1.0/24" in diagnostico.mensaje  # Comprueba que el mensaje identifique también la red previamente aceptada.
    assert "línea 1" in diagnostico.mensaje  # Confirma que se informe dónde apareció originalmente la red con la cual existe traslape.


def prueba_sem006_acepta_redes_adyacentes_sin_traslape():  # Comprueba que dos redes consecutivas puedan tocar sus límites sin compartir ninguna dirección.
    codigo_fuente = "IP 192.168.1.0 MASK /25 HOSTS 50 NAME Izquierda\nIP 192.168.1.128 MASK /25 HOSTS 50 NAME Derecha"  # Declara las dos mitades independientes de una antigua red /24.
    resultado = analizar_semanticamente(codigo_fuente)  # Comprueba ambas redes mediante las reglas de conflicto.
    assert resultado.diagnosticos == []  # Confirma que redes adyacentes no sean confundidas con redes superpuestas.
    assert len(resultado.bloques_validos) == 2  # Mantiene ambas instrucciones disponibles para las etapas posteriores.


def prueba_sem006_conserva_bloques_independientes_despues_de_conflicto():  # Comprueba que un traslape intermedio no impida procesar una red posterior completamente independiente.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\nIP 192.168.1.128 MASK /25 HOSTS 50 NAME Traslapada\nIP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"  # Combina una red válida, otra traslapada y una tercera completamente independiente.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta las comparaciones respetando el orden original de aparición.
    nombres_validos = [bloque.nombre for bloque in resultado.bloques_validos]  # Recupera los nombres correspondientes con las redes que sobrevivieron.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los diagnósticos semánticos producidos.
    assert nombres_validos == ["Oficina", "Central"]  # Confirma que solamente se descarte la declaración responsable del conflicto.
    assert codigos == ["SEM-006"]  # Confirma que el único problema de este conjunto sea el traslape esperado.


def prueba_sem007_acepta_octeto_en_limite_255():  # Comprueba que el valor máximo permitido de un octeto no produzca SEM-007.
    resultado = analizar_semanticamente("IP 10.255.0.0 MASK /16 HOSTS 50 NAME Limite")  # Utiliza exactamente 255 dentro del segundo componente de una dirección base válida.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera cualquier diagnóstico semántico producido.
    assert "SEM-007" not in codigos  # Confirma que el límite superior permitido continúe considerándose válido.
    assert len(resultado.bloques_validos) == 1  # Comprueba que la instrucción pueda continuar normalmente hacia las etapas posteriores.


def prueba_sem007_rechaza_octeto_mayor_255_y_ubica_fragmento():  # Comprueba que el primer valor inmediatamente superior al máximo permitido produzca SEM-007.
    codigo_fuente = "IP 192.168.1.256 MASK /24 HOSTS 50 NAME Invalida"  # Utiliza deliberadamente 256 como cuarto componente de una dirección estructuralmente completa.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la validación semántica que ahora posee la responsabilidad de comprobar los octetos.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-007")  # Recupera específicamente el nuevo error de rango IPv4.
    assert resultado.bloques_validos == []  # Confirma que una dirección imposible no pueda continuar hacia VLSM.
    assert diagnostico.fragmento == "256"  # Verifica que solamente el octeto incorrecto sea utilizado como fragmento.
    assert diagnostico.linea == 1  # Confirma que el diagnóstico permanezca relacionado con la primera línea.
    assert diagnostico.columna == codigo_fuente.index("256")  # Comprueba que la columna señale directamente el inicio del componente incorrecto.
    assert diagnostico.longitud == 3  # Verifica que el resaltado cubra exactamente los tres dígitos del octeto.
    assert "0 y 255" in diagnostico.mensaje  # Confirma que el mensaje informe claramente el intervalo permitido.


def prueba_sem007_detecta_varios_octetos_fuera_de_rango():  # Comprueba que una misma dirección pueda producir un SEM-007 independiente por cada componente inválido.
    codigo_fuente = "IP 300.168.999.0 MASK /24 HOSTS 50 NAME Invalida"  # Utiliza deliberadamente dos componentes superiores con 255 dentro de una dirección estructuralmente completa.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta el análisis semántico sobre los cuatro componentes.
    diagnosticos = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-007"]  # Conserva únicamente los errores pertenecientes con octetos fuera de rango.
    assert len(diagnosticos) == 2  # Confirma que ambos componentes inválidos produzcan su propio diagnóstico.
    assert diagnosticos[0].fragmento == "300"  # Comprueba que el primer diagnóstico corresponda con el primer octeto incorrecto.
    assert diagnosticos[1].fragmento == "999"  # Comprueba que el segundo diagnóstico corresponda con el tercer octeto incorrecto.
    assert diagnosticos[0].columna == codigo_fuente.index("300")  # Verifica la ubicación exacta del primer componente problemático.
    assert diagnosticos[1].columna == codigo_fuente.index("999")  # Verifica la ubicación exacta del segundo componente problemático.


def prueba_sem008_rechaza_red_base_declarada_nuevamente_con_otros_datos():  # Comprueba que el mismo espacio IPv4 declarado con otros HOSTS o NAME produzca SEM-008.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\nIP 192.168.1.0 MASK /24 HOSTS 30 NAME Laboratorio"  # Utiliza la misma red y máscara pero modifica los datos asociados con la segunda declaración.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la comparación semántica entre ambas redes.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los identificadores producidos durante la comprobación.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-008")  # Recupera específicamente el diagnóstico correspondiente con la red repetida.
    assert codigos == ["SEM-008"]  # Confirma que el caso específico no sea degradado innecesariamente a SEM-006.
    assert len(resultado.bloques_validos) == 1  # Comprueba que únicamente permanezca la primera definición del espacio IPv4.
    assert resultado.bloques_validos[0].nombre == "Oficina"  # Confirma que la primera declaración sea la conservada.
    assert diagnostico.linea == 2  # Verifica que el error se asocie con la definición posterior.
    assert diagnostico.fragmento == "192.168.1.0"  # Comprueba que la IP reutilizada sea el fragmento señalado.
    assert "ya fue declarada" in diagnostico.mensaje  # Confirma que el mensaje explique directamente que la red ya existía.


def prueba_sem009_rechaza_misma_ip_base_con_mascara_diferente():  # Comprueba que una dirección base previamente utilizada con otra máscara produzca SEM-009.
    codigo_fuente = "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Principal\nIP 192.168.1.0 MASK /25 HOSTS 30 NAME Secundaria"  # Reutiliza deliberadamente la misma dirección de inicio utilizando un prefijo diferente.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta la comparación de significado entre ambas declaraciones.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera todos los códigos producidos por la entrada.
    diagnostico = next(diagnostico for diagnostico in resultado.diagnosticos if diagnostico.codigo == "SEM-009")  # Recupera específicamente el conflicto correspondiente con la reutilización de IP.
    assert codigos == ["SEM-009"]  # Confirma que el caso específico no sea reportado simplemente como traslape.
    assert len(resultado.bloques_validos) == 1  # Comprueba que solamente permanezca aceptada la primera declaración.
    assert resultado.bloques_validos[0].nombre == "Principal"  # Verifica que la red conservada corresponda con la definición original.
    assert diagnostico.linea == 2  # Confirma que la segunda utilización sea la señalada como conflictiva.
    assert diagnostico.fragmento == "192.168.1.0"  # Comprueba que la dirección reutilizada sea utilizada como fragmento.
    assert "/24" in diagnostico.mensaje  # Confirma que el mensaje informe cuál era la máscara utilizada inicialmente.
    assert "/25" in diagnostico.mensaje  # Confirma que también informe cuál es la máscara incompatible utilizada después.


def prueba_sem006_sigue_reservado_para_traslape_que_no_es_sem008_ni_sem009():  # Comprueba que SEM-006 continúe atendiendo los traslapes que no corresponden con las dos reglas más específicas.
    codigo_fuente = "IP 192.168.10.0 MASK /24 HOSTS 50 NAME Principal\nIP 192.168.10.128 MASK /25 HOSTS 30 NAME Interna"  # Declara una segunda red diferente que se encuentra contenida dentro de la primera.
    resultado = analizar_semanticamente(codigo_fuente)  # Ejecuta todas las comprobaciones de conflicto entre ambas redes.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos]  # Recupera los códigos producidos para determinar cuál regla clasificó el caso.
    assert codigos == ["SEM-006"]  # Confirma que el traslape normal continúe utilizando exclusivamente SEM-006.
    assert "SEM-008" not in codigos  # Evita considerar iguales dos redes cuyos espacios no son exactamente los mismos.
    assert "SEM-009" not in codigos  # Evita utilizar la regla de misma IP base cuando ambas declaraciones comienzan en direcciones diferentes.