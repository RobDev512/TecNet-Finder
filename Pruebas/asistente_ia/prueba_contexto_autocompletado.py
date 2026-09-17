# ============================================================
# Archivo: prueba_contexto_autocompletado.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba el análisis contextual utilizado antes
# del autocompletado opcional mediante inteligencia artificial.
#
# Las pruebas verifican únicamente la interpretación formal del
# texto escrito por el usuario y no consultan ningún modelo.
#
# Se comprueba que el contexto pueda reconocer palabras
# reservadas parciales, direcciones IPv4 en construcción,
# máscaras, HOSTS, cantidades e identificadores después de NAME.
#
# También se verifica que texto ajeno al lenguaje no habilite
# solicitudes innecesarias hacia la inteligencia artificial.
# ============================================================

from AsistenteIA.autocompletado.contexto_autocompletado import AnalizadorContextoAutocompletado  # Importa el analizador determinista que interpreta el contexto antes de consultar cualquier modelo.


def prueba_contexto_completa_inicio_i():  # Comprueba el caso donde el usuario apenas comenzó a escribir la palabra reservada IP.
    contexto = AnalizadorContextoAutocompletado().analizar("I")  # Analiza un prefijo mínimo perteneciente al comienzo válido de una instrucción.
    assert contexto.permitido  # Confirma que el fragmento sea reconocido como un comienzo válido para autocompletado.
    assert contexto.elemento_actual == "IP_ADDRESS"  # Confirma que después de completar IP el siguiente elemento esperado será una dirección.
    assert contexto.completacion_fija == "P "  # Comprueba que la parte determinista pueda completar IP y agregar el espacio necesario.


def prueba_contexto_prepara_direccion_despues_de_ip():  # Comprueba el estado inmediatamente después de escribir completamente IP.
    contexto = AnalizadorContextoAutocompletado().analizar("IP")  # Analiza la palabra reservada sin el espacio posterior.
    assert contexto.permitido  # Confirma que la entrada pertenezca a una posición válida del lenguaje.
    assert contexto.elemento_actual == "IP_ADDRESS"  # Confirma que el siguiente componente variable sea la dirección IPv4.
    assert contexto.completacion_fija == " "  # Comprueba que solamente falte agregar el separador antes de comenzar la IP.


def prueba_contexto_reconoce_ip_con_espacio():  # Comprueba que una IP todavía vacía pueda comenzar después de escribir IP y su espacio.
    contexto = AnalizadorContextoAutocompletado().analizar("IP ")  # Analiza el punto exacto donde debe empezar la dirección IPv4.
    assert contexto.permitido  # Confirma que el autocompletado continúe permitido en esta posición.
    assert contexto.elemento_actual == "IP_ADDRESS"  # Confirma que la dirección siga siendo el elemento que debe generarse.
    assert contexto.completacion_fija == ""  # Comprueba que ya no exista ningún carácter fijo que deba insertarse antes de la dirección.


def prueba_contexto_reconoce_fragmento_ip_diez():  # Comprueba que una dirección parcialmente escrita sea entregada como contexto.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10")  # Utiliza los primeros dígitos de una dirección IPv4 válida.
    assert contexto.permitido  # Confirma que el fragmento todavía pueda completarse.
    assert contexto.elemento_actual == "IP_ADDRESS"  # Mantiene la generación dentro del componente correspondiente con la dirección.
    assert contexto.fragmento_actual == "10"  # Conserva exactamente la parte que el usuario ya escribió para evitar repetirla.


def prueba_contexto_reconoce_fragmento_ip_arbitrario():  # Comprueba que el analizador no esté limitado únicamente a direcciones de ejemplos conocidos.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 172.25.4")  # Utiliza una dirección parcial diferente de los casos habituales del proyecto.
    assert contexto.permitido  # Confirma que una IPv4 parcial arbitraria todavía sea un contexto válido.
    assert contexto.elemento_actual == "IP_ADDRESS"  # Confirma que la parte incompleta siga interpretándose como dirección.
    assert contexto.fragmento_actual == "172.25.4"  # Conserva todo el fragmento real escrito por el usuario.


def prueba_contexto_prepara_mask_despues_de_ip_completa():  # Comprueba la transición desde una dirección completa hacia la sección MASK.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0")  # Finaliza correctamente la dirección IPv4 pero todavía omite MASK.
    assert contexto.permitido  # Confirma que el punto actual sea apropiado para continuar la instrucción.
    assert contexto.elemento_actual == "SUBNET_MASK"  # Indica que después de completar la palabra fija MASK deberá generarse una máscara CIDR.
    assert contexto.completacion_fija == " MASK "  # Comprueba que MASK pueda agregarse determinísticamente sin solicitarla al modelo.


def prueba_contexto_completa_mask_parcial():  # Comprueba que una palabra reservada MASK parcialmente escrita pueda completarse localmente.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MAS")  # Omite deliberadamente la última letra de MASK.
    assert contexto.permitido  # Confirma que el fragmento continúe reconocido como parte válida de la instrucción.
    assert contexto.elemento_actual == "SUBNET_MASK"  # Mantiene como siguiente dato variable la máscara CIDR.
    assert contexto.completacion_fija == "K "  # Comprueba que solamente se sugiera la parte restante de la palabra reservada y su espacio.


def prueba_contexto_prepara_hosts_despues_de_mascara():  # Comprueba la transición desde una máscara CIDR completa hacia la sección HOSTS.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24")  # Completa IP y máscara pero todavía no escribe HOSTS.
    assert contexto.permitido  # Confirma que la instrucción todavía pueda continuarse mediante autocompletado.
    assert contexto.elemento_actual == "HOST_COUNT"  # Indica que después de HOSTS el siguiente valor variable será una cantidad.
    assert contexto.completacion_fija == " HOSTS "  # Comprueba que la palabra reservada completa pueda añadirse de manera determinista.


def prueba_contexto_completa_hosts_parcial():  # Comprueba que HOSTS parcialmente escrito pueda completarse sin recurrir a IA.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24 HOS")  # Omite deliberadamente las dos últimas letras de HOSTS.
    assert contexto.permitido  # Confirma que la entrada parcial continúe siendo reconocida.
    assert contexto.elemento_actual == "HOST_COUNT"  # Mantiene la cantidad de hosts como siguiente componente variable.
    assert contexto.completacion_fija == "TS "  # Comprueba que el analizador solamente complete la parte fija restante.


def prueba_contexto_reconoce_cantidad_despues_de_coma():  # Comprueba que una coma dentro de HOSTS permita comenzar inmediatamente otra cantidad.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24 HOSTS 40,")  # Finaliza la primera cantidad y deja preparada una segunda solicitud.
    assert contexto.permitido  # Confirma que continuar la lista HOSTS sea una operación válida.
    assert contexto.elemento_actual == "HOST_COUNT"  # Indica que el siguiente componente debe ser otra cantidad numérica.
    assert contexto.completacion_fija == ""  # Comprueba que después de la coma no haga falta insertar ningún texto fijo adicional.


def prueba_contexto_prepara_identificador_despues_de_name():  # Comprueba que la sección opcional NAME conduzca correctamente hacia un identificador.
    contexto = AnalizadorContextoAutocompletado().analizar("IP 10.44.2.0 MASK /24 HOSTS 40 NAME")  # Escribe NAME completamente pero todavía omite el nombre de red.
    assert contexto.permitido  # Confirma que el autocompletado pueda continuar desde esta posición.
    assert contexto.elemento_actual == "IDENTIFIER"  # Indica que ahora debe proponerse un nombre de red.
    assert contexto.completacion_fija == " "  # Comprueba que solamente falte el espacio que separa NAME del identificador.


def prueba_contexto_rechaza_texto_ajeno_al_lenguaje():  # Comprueba que el asistente no intente completar contenido que no pertenece al DSL.
    contexto = AnalizadorContextoAutocompletado().analizar("hola mundo")  # Utiliza una cadena completamente ajena a la estructura de TecNet Finder.
    assert not contexto.permitido  # Confirma que el contexto rechace la entrada y evite solicitar una sugerencia innecesaria a la IA.