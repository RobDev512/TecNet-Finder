# ============================================================
# Archivo: prueba_contexto_autocompletado.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba que el análisis contextual reconozca
# distintas etapas y valores parciales del lenguaje sin utilizar
# respuestas específicas de inteligencia artificial.
# ============================================================

from AsistenteIA.contexto_autocompletado import AnalizadorContextoAutocompletado  # Importa el analizador formal utilizado antes de consultar al modelo.


def prueba_contexto_completa_inicio_i():
    contexto = AnalizadorContextoAutocompletado().analizar("I")

    assert contexto.permitido
    assert contexto.elemento_actual == "IP_ADDRESS"
    assert contexto.completacion_fija == "P "


def prueba_contexto_prepara_direccion_despues_de_ip():
    contexto = AnalizadorContextoAutocompletado().analizar("IP")

    assert contexto.permitido
    assert contexto.elemento_actual == "IP_ADDRESS"
    assert contexto.completacion_fija == " "


def prueba_contexto_reconoce_ip_con_espacio():
    contexto = AnalizadorContextoAutocompletado().analizar("IP ")

    assert contexto.permitido
    assert contexto.elemento_actual == "IP_ADDRESS"
    assert contexto.completacion_fija == ""


def prueba_contexto_reconoce_fragmento_ip_diez():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10")

    assert contexto.permitido
    assert contexto.elemento_actual == "IP_ADDRESS"
    assert contexto.fragmento_actual == "10"


def prueba_contexto_reconoce_fragmento_ip_arbitrario():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 172.25.4")

    assert contexto.permitido
    assert contexto.elemento_actual == "IP_ADDRESS"
    assert contexto.fragmento_actual == "172.25.4"


def prueba_contexto_prepara_mask_despues_de_ip_completa():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0")

    assert contexto.permitido
    assert contexto.elemento_actual == "SUBNET_MASK"
    assert contexto.completacion_fija == " MASK "


def prueba_contexto_completa_mask_parcial():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MAS")

    assert contexto.permitido
    assert contexto.elemento_actual == "SUBNET_MASK"
    assert contexto.completacion_fija == "K "


def prueba_contexto_prepara_hosts_despues_de_mascara():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24")

    assert contexto.permitido
    assert contexto.elemento_actual == "HOST_COUNT"
    assert contexto.completacion_fija == " HOSTS "


def prueba_contexto_completa_hosts_parcial():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24 HOS")

    assert contexto.permitido
    assert contexto.elemento_actual == "HOST_COUNT"
    assert contexto.completacion_fija == "TS "


def prueba_contexto_reconoce_cantidad_despues_de_coma():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24 HOSTS 40,")

    assert contexto.permitido
    assert contexto.elemento_actual == "HOST_COUNT"
    assert contexto.completacion_fija == ""


def prueba_contexto_prepara_identificador_despues_de_name():
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24 HOSTS 40 NAME")

    assert contexto.permitido
    assert contexto.elemento_actual == "IDENTIFIER"
    assert contexto.completacion_fija == " "


def prueba_contexto_rechaza_texto_ajeno_al_lenguaje():
    contexto = AnalizadorContextoAutocompletado().analizar("hola mundo")

    assert not contexto.permitido