# ============================================================
# Archivo: prueba_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con las advertencias no bloqueantes de TecNet Finder.
#
# Comprueba que ADV-001 a ADV-009 aparezcan únicamente en las
# situaciones para las que fueron diseñadas.
#
# También verifica que ADV-009 informe rangos IPv4 especiales
# sin impedir que TecNet Finder continúe calculando VLSM.
# ============================================================

from Motor.compilacion.flujo_compilacion import FlujoCompilacion  # Utiliza exactamente el mismo flujo de compilación ejecutado normalmente por la aplicación.


def _codigos_advertencia(codigo: str) -> list[str]:  # Ejecuta una entrada y devuelve exclusivamente los códigos correspondientes con advertencias.
    resultado = FlujoCompilacion().analizar(codigo)  # Procesa la entrada mediante las fases reales conectadas actualmente en TecNet Finder.
    return [diagnostico.codigo for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Filtra los diagnósticos bloqueantes y conserva solamente las recomendaciones.


def prueba_entrada_normal_no_genera_advertencias():  # Comprueba que una instrucción correctamente escrita y dimensionada permanezca completamente limpia.
    codigos = _codigos_advertencia("IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina")  # Utiliza una red privada ordinaria con HOSTS descendentes y un nombre descriptivo.
    assert codigos == []  # Confirma que ninguna regla ADV encuentre una situación que deba recomendarse.


def prueba_adv_001_procesamiento_parcial():  # Comprueba que ADV-001 aparezca cuando existen errores pero otro bloque todavía puede procesarse.
    codigo = "IP 192.168.1.0 /24 HOSTS 50 NAME Incorrecta\nIP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"  # Combina un bloque sintácticamente incorrecto con otro completamente válido.
    codigos = _codigos_advertencia(codigo)  # Ejecuta conjuntamente ambas instrucciones para activar el procesamiento parcial.
    assert "ADV-001" in codigos  # Confirma que TecNet Finder informe que solamente procesará la parte válida de la entrada.


def prueba_adv_002_palabras_reservadas_pegadas():  # Comprueba la recomendación de separar palabras reservadas de sus valores.
    codigos = _codigos_advertencia("IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada")  # Utiliza deliberadamente IP, MASK y HOSTS sin espacios posteriores.
    assert "ADV-002" in codigos  # Confirma que la escritura aceptada pero poco legible produzca la advertencia correspondiente.


def prueba_adv_003_nombre_repetido():  # Comprueba que dos redes distintas con el mismo NAME generen una recomendación.
    codigo = "IP 192.168.50.0 MASK /24 HOSTS 50 NAME Oficina\nIP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina"  # Reutiliza deliberadamente el mismo identificador dentro de dos redes diferentes.
    codigos = _codigos_advertencia(codigo)  # Procesa ambas instrucciones para comparar sus nombres.
    assert "ADV-003" in codigos  # Confirma que la segunda utilización del mismo nombre sea detectada.


def prueba_adv_004_hosts_repetidos():  # Comprueba que cantidades duplicadas dentro de una misma lista HOSTS produzcan una advertencia.
    codigos = _codigos_advertencia("IP 192.168.60.0 MASK /24 HOSTS 50,50,30 NAME Duplicados")  # Solicita deliberadamente dos subredes con 50 hosts.
    assert "ADV-004" in codigos  # Confirma que TecNet Finder pida revisar si la repetición fue realmente intencional.


def prueba_adv_005_detecta_red_claramente_sobredimensionada():  # Comprueba ADV-005 mediante una red considerablemente mayor que la solicitud VLSM.
    codigos = _codigos_advertencia("IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada")  # Utiliza una red /8 para una solicitud que solamente requiere un bloque de 16 direcciones.
    assert "ADV-005" in codigos  # Confirma que una diferencia extremadamente grande de capacidad produzca la recomendación.


def prueba_adv_005_se_activa_en_umbral_de_dieciseis_veces():  # Comprueba exactamente el límite inferior definido para considerar sobredimensionada una red.
    codigos = _codigos_advertencia("IP 192.168.1.0 MASK /24 HOSTS 10 NAME Sobrada")  # Utiliza una /24 de 256 direcciones para una solicitud que necesita exactamente un bloque de 16.
    assert "ADV-005" in codigos  # Confirma que una relación exactamente de dieciséis a uno active la advertencia.


def prueba_adv_005_no_se_activa_con_solo_ocho_veces_la_capacidad():  # Comprueba que el umbral de sobredimensionamiento no sea más agresivo de lo establecido.
    codigos = _codigos_advertencia("IP 192.168.1.0 MASK /24 HOSTS 20 NAME Adecuada")  # Utiliza una solicitud de 20 hosts que necesita 32 direcciones dentro de una /24.
    assert "ADV-005" not in codigos  # Confirma que una relación de ocho a uno todavía no se considere claramente sobredimensionada.


def prueba_adv_005_no_se_emite_sobre_bloque_semanticamente_invalido():  # Comprueba que ADV-005 solamente evalúe bloques que ya superaron el análisis semántico.
    codigos = _codigos_advertencia("IP 10.20.0.0 MASK /8 HOSTS 10 NAME Invalida")  # Utiliza una dirección que no representa el comienzo correspondiente con la máscara /8.
    assert "ADV-005" not in codigos  # Evita recomendar optimizaciones sobre una red que primero debe corregirse mediante SEM-002.


def prueba_adv_006_nombre_generico():  # Comprueba que un NAME demasiado general produzca la recomendación correspondiente.
    codigos = _codigos_advertencia("IP 192.168.70.0 MASK /24 HOSTS 50 NAME Red")  # Utiliza deliberadamente Red como identificador poco descriptivo.
    assert "ADV-006" in codigos  # Confirma que TecNet Finder sugiera utilizar un nombre más claro.


def prueba_adv_007_nombre_no_especificado():  # Comprueba que omitir la sección opcional NAME siga siendo válido pero produzca una recomendación.
    codigos = _codigos_advertencia("IP 192.168.80.0 MASK /24 HOSTS 50,30")  # Declara una red válida sin proporcionar ningún identificador.
    assert "ADV-007" in codigos  # Confirma que se sugiera añadir un nombre sin convertir su ausencia en error.


def prueba_adv_008_hosts_fuera_de_orden_descendente():  # Comprueba que una lista válida escrita de menor a mayor produzca la recomendación correspondiente.
    codigos = _codigos_advertencia("IP 192.168.90.0 MASK /24 HOSTS 10,30,50 NAME Desordenada")  # Utiliza deliberadamente cantidades que no siguen el orden descendente recomendado para VLSM.
    assert "ADV-008" in codigos  # Confirma que TecNet Finder informe el orden recomendado sin rechazar la instrucción.


def prueba_adv_009_detecta_rango_loopback_y_no_bloquea_vlsm():  # Comprueba que una red loopback produzca ADV-009 mientras el cálculo VLSM continúa disponible.
    resultado = FlujoCompilacion().analizar("IP 127.0.0.0 MASK /24 HOSTS 50 NAME Loopback")  # Utiliza una red semánticamente válida situada dentro del rango especial de loopback.
    codigos = [diagnostico.codigo for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Recupera solamente las recomendaciones producidas.
    errores = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.severidad == "error"]  # Recupera cualquier diagnóstico bloqueante para comprobar que ADV-009 no genere errores indirectos.
    assert "ADV-009" in codigos  # Confirma que el rango especial haya sido reconocido.
    assert errores == []  # Confirma que la advertencia no convierta una red formalmente válida en un error.
    assert resultado.subredes_vlsm  # Confirma que TecNet Finder haya continuado calculando VLSM normalmente.


def prueba_adv_009_detecta_rango_enlace_local():  # Comprueba que una red perteneciente con 169.254.0.0/16 produzca la nueva advertencia.
    codigos = _codigos_advertencia("IP 169.254.10.0 MASK /24 HOSTS 50 NAME EnlaceLocal")  # Utiliza una dirección base correctamente alineada dentro del espacio de enlace local.
    assert "ADV-009" in codigos  # Confirma que TecNet Finder informe el uso especial del espacio sin bloquearlo.


def prueba_adv_009_detecta_multicast_y_rango_reservado():  # Comprueba conjuntamente dos categorías adicionales registradas dentro del catálogo de rangos especiales.
    codigo = "IP 224.0.1.0 MASK /24 HOSTS 50 NAME Multicast\nIP 240.0.1.0 MASK /24 HOSTS 50 NAME Reservada"  # Declara dos redes independientes pertenecientes con multicast y espacio reservado respectivamente.
    codigos = _codigos_advertencia(codigo)  # Ejecuta conjuntamente ambas redes para recuperar sus recomendaciones.
    assert codigos.count("ADV-009") == 2  # Confirma que cada red especial produzca exactamente su propia advertencia.


def prueba_adv_009_no_confunde_red_privada_ordinaria_con_rango_especial():  # Comprueba que las redes privadas utilizadas normalmente por TecNet Finder no sean clasificadas como especiales.
    codigos = _codigos_advertencia("IP 10.20.30.0 MASK /24 HOSTS 50 NAME Privada")  # Utiliza una red privada RFC1918 completamente ordinaria para planificación VLSM.
    assert "ADV-009" not in codigos  # Confirma que el nuevo aviso no interfiera con el uso normal de direcciones privadas.