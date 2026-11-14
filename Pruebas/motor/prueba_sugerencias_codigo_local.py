# ============================================================
# Archivo: prueba_sugerencias_codigo_local.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Verifica que el completador independiente de IA ofrezca
# solamente palabras reservadas, signos y una plantilla opcional.
# No sugiere IP, máscaras, cantidades ni identificadores.
# ============================================================

from Motor.compilacion.sugerencias_codigo_local import EJEMPLO_BLOQUE, ETIQUETA_PLANTILLA, obtener_sugerencias_codigo  # Reutiliza el motor de sugerencias puro.


def _etiquetas(linea: str, *, manual: bool = True) -> list[str]:
    return [opcion.etiqueta for opcion in obtener_sugerencias_codigo(linea, manual=manual)[1]]  # Reúne las opciones visibles.


def prueba_inicio_sugiere_ip():
    assert _etiquetas("", manual=True)[0] == "IP"  # El lenguaje comienza únicamente con IP.
    assert _etiquetas("", manual=False) == []  # No abre la lista en un editor sin escritura.


def prueba_plantilla_muestra_descripcion_sin_modificar_insercion():
    opciones = obtener_sugerencias_codigo("I", manual=True)[1]  # Presenta la plantilla tras el prefijo inicial.
    plantilla = next(opcion for opcion in opciones if opcion.etiqueta == ETIQUETA_PLANTILLA)
    assert plantilla.etiqueta == "IP xxx.xxx.x.x MASK /x HOSTS x,y,z NAME Nombre"  # Respeta la descripción solicitada.
    assert plantilla.insercion == EJEMPLO_BLOQUE  # No cambia el código que se insertará.
    assert plantilla.seleccionar_desde == 3 and plantilla.seleccionar_longitud == len("192.168.1.0")  # Permite editar la IP.


def prueba_no_propone_direcciones_ni_mascaras_numericas():
    assert _etiquetas("IP ") == []  # El valor de la dirección corresponde al usuario.
    assert _etiquetas("IP 192.168.1.0 MASK ") == ["/"]  # Únicamente puede sugerir el separador, no /24.
    assert _etiquetas("IP 192.168.1.0 MASK /24") == []  # No propone otras máscaras una vez escrita.


def prueba_mask_se_propone_tras_ipv4():
    assert _etiquetas("IP 192.168.1.0 M") == ["MASK"]  # El prefijo corresponde a una reservada válida.
    assert _etiquetas("IP 192.168.1.0 ", manual=False) == []  # No invade al escribir espacios.
    assert _etiquetas("IP 192.168.1.0 ") == ["MASK"]  # Ctrl+Espacio sí muestra el token esperado.


def prueba_hosts_se_propone_despues_cidr():
    assert _etiquetas("IP 192.168.1.0 MASK /24 H") == ["HOSTS"]  # Sugiere la siguiente reservada.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS ") == []  # No sugiere cantidades.


def prueba_coma_disponible_solo_manual():
    linea = "IP 192.168.1.0 MASK /24 HOSTS 50,30"
    assert _etiquetas(linea) == [","]  # Ctrl+Espacio permite insertar el signo.
    assert _etiquetas(linea, manual=False) == []  # No salta mientras se escriben cifras.
    assert _etiquetas(linea + ",") == []  # No propone la siguiente cantidad.


def prueba_punto_disponible_dentro_ipv4():
    assert _etiquetas("IP 192") == ["."]  # Ctrl+Espacio puede insertar un separador.
    assert _etiquetas("IP 192.168.1") == ["."]  # Los tres primeros octetos aceptan punto.
    assert _etiquetas("IP 192.168.1.0") == []  # La IPv4 completa no admite otro punto.
    assert _etiquetas("IP 192", manual=False) == []  # El separador no aparece automáticamente.


def prueba_name_se_propone_tras_hosts():
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50,30 N") == ["NAME"]  # Completa la reservada opcional.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50 NAME ") == []  # No propone nombres inventados.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50 NAME O") == []  # Ni siquiera propone nombres al escribir letras.


def prueba_contexto_invalido_no_ofrece_reservadas():
    assert _etiquetas("HOSTS ") == []  # No sugiere HOSTS sin IP ni MASK.
    assert _etiquetas("IP 192.168.1.0 NAME ") == []  # No adelanta NAME antes de HOSTS.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina") == []  # Termina al finalizar la instrucción.


def prueba_busqueda_ignora_mayusculas():
    assert _etiquetas("ip")[:1] == ["IP"]  # Permite corregir un prefijo de reservada en minúsculas.
    assert _etiquetas("IP 192.168.1.0 m") == ["MASK"]  # Sugiere la escritura correcta de MASK.


def prueba_no_propone_identificadores_arbitrarios():
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 25 NAME Lab") == []  # No inventa contenidos después de NAME.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 25 NAME M") == []  # La M de un nombre no equivale a MASK.


def prueba_automatica_solo_prefijo_reservado():
    assert _etiquetas("I", manual=False)[0] == "IP"  # Un prefijo incompleto activa el completado al escribir.
    assert _etiquetas("IP ", manual=False) == []  # Espacio no lo activa.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50,", manual=False) == []  # La coma tampoco.


def prueba_rechaza_entrada_muy_larga_o_multilinea():
    assert _etiquetas("I" * 501) == []  # Evita texto muy largo.
    assert _etiquetas("IP 10.0.0.0\nMASK") == []  # No mezcla varias instrucciones.


def prueba_no_sugiere_keyword_en_mitad_dato():
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50 NAME Lab") == []  # Respeta la etapa de IDENTIFIER.
    assert _etiquetas("IP 192.168.1.0 MASK /24 HOSTS 50N") == []  # No interpreta una reservada pegada a un valor.
