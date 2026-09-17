# ============================================================
# Archivo: prueba_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con las advertencias no bloqueantes de TecNet Finder.
#
# Comprueba que ADV-001 a ADV-007 aparezcan únicamente en las
# situaciones para las que fueron diseñadas.
#
# También verifica específicamente el umbral utilizado por
# ADV-005 para detectar redes base claramente sobredimensionadas
# sin producir esa recomendación sobre bloques semánticamente
# inválidos.
# ============================================================

from Motor.compilacion.flujo_compilacion import FlujoCompilacion  # Utiliza exactamente el mismo flujo de compilación ejecutado normalmente por la aplicación.


def _codigos_advertencia(codigo: str) -> list[str]:  # Ejecuta una entrada y devuelve exclusivamente los códigos correspondientes con advertencias.
    resultado = FlujoCompilacion().analizar(codigo)  # Procesa la entrada mediante las fases reales conectadas actualmente en TecNet Finder.
    return [diagnostico.codigo for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Filtra los diagnósticos bloqueantes y conserva solamente recomendaciones.


def prueba_entrada_normal_no_genera_advertencias():  # Comprueba que una instrucción correctamente escrita y dimensionada permanezca completamente limpia.
    codigos = _codigos_advertencia("IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina")  # Utiliza una red normal con HOSTS descendentes y un nombre descriptivo.
    assert codigos == []  # Confirma que ninguna regla ADV encuentre una situación que deba recomendarse.


def prueba_adv_001_procesamiento_parcial():  # Comprueba que ADV-001 aparezca cuando existen errores pero otro bloque todavía puede procesarse.
    codigo = (
        "IP 192.168.1.0 /24 HOSTS 50 NAME Incorrecta\n"  # Crea un primer bloque sintácticamente incorrecto porque falta MASK.
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"  # Agrega un segundo bloque completamente válido que sí debe llegar hasta VLSM.
    )
    codigos = _codigos_advertencia(codigo)  # Ejecuta conjuntamente ambos bloques para activar el procesamiento parcial.
    assert "ADV-001" in codigos  # Confirma que TecNet Finder informe que solamente procesará la parte válida de la entrada.


def prueba_adv_002_palabras_reservadas_pegadas():  # Comprueba la recomendación de separar palabras reservadas de sus valores.
    codigos = _codigos_advertencia("IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada")  # Utiliza deliberadamente IP, MASK y HOSTS sin espacios posteriores.
    assert "ADV-002" in codigos  # Confirma que la escritura aceptada pero poco legible produzca la advertencia correspondiente.


def prueba_adv_003_nombre_repetido():  # Comprueba que dos redes distintas con el mismo NAME generen una recomendación.
    codigo = (
        "IP 192.168.50.0 MASK /24 HOSTS 50 NAME Oficina\n"  # Declara la primera red utilizando el nombre Oficina.
        "IP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina"  # Reutiliza intencionalmente el mismo identificador en otra red diferente.
    )
    codigos = _codigos_advertencia(codigo)  # Procesa ambas instrucciones para comparar sus nombres.
    assert "ADV-003" in codigos  # Confirma que la segunda utilización del mismo nombre sea detectada.


def prueba_adv_004_hosts_repetidos():  # Comprueba que cantidades duplicadas dentro de una misma lista HOSTS produzcan una advertencia.
    codigos = _codigos_advertencia("IP 192.168.60.0 MASK /24 HOSTS 50,50,30 NAME Duplicados")  # Solicita deliberadamente dos subredes con 50 hosts.
    assert "ADV-004" in codigos  # Confirma que TecNet Finder pida revisar si la repetición fue realmente intencional.


def prueba_adv_005_detecta_red_claramente_sobredimensionada():  # Comprueba ADV-005 mediante una red considerablemente mayor que la solicitud VLSM.
    codigos = _codigos_advertencia("IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada")  # Utiliza una red /8 para una solicitud que solamente requiere un bloque de 16 direcciones.
    assert "ADV-005" in codigos  # Confirma que una diferencia extremadamente grande de capacidad produzca la recomendación.


def prueba_adv_005_se_activa_en_umbral_de_dieciseis_veces():  # Comprueba exactamente el límite inferior definido para considerar sobredimensionada una red.
    codigos = _codigos_advertencia("IP 192.168.1.0 MASK /24 HOSTS 10 NAME Sobrada")  # Una /24 contiene 256 direcciones y HOSTS 10 necesita un bloque de 16.
    assert "ADV-005" in codigos  # Confirma que una relación exactamente de dieciséis a uno ya active la advertencia.


def prueba_adv_005_no_se_activa_con_solo_ocho_veces_la_capacidad():  # Comprueba que el umbral no sea más agresivo de lo establecido.
    codigos = _codigos_advertencia("IP 192.168.1.0 MASK /24 HOSTS 20 NAME Adecuada")  # HOSTS 20 necesita 32 direcciones mientras una /24 dispone de 256.
    assert "ADV-005" not in codigos  # Confirma que una relación de ocho a uno todavía no se considere claramente sobredimensionada.


def prueba_adv_005_no_se_emite_sobre_bloque_semanticamente_invalido():  # Comprueba que ADV-005 solamente evalúe bloques que ya superaron el análisis semántico.
    codigos = _codigos_advertencia("IP 10.20.0.0 MASK /8 HOSTS 10 NAME Invalida")  # Utiliza una IP que no representa la dirección base correspondiente con /8.
    assert "ADV-005" not in codigos  # Evita recomendar una máscara diferente sobre una red que primero debe corregirse por SEM-002.


def prueba_adv_006_nombre_generico():  # Comprueba que un NAME demasiado general produzca la recomendación correspondiente.
    codigos = _codigos_advertencia("IP 192.168.70.0 MASK /24 HOSTS 50 NAME Red")  # Utiliza deliberadamente Red como identificador poco descriptivo.
    assert "ADV-006" in codigos  # Confirma que TecNet Finder sugiera utilizar un nombre más claro.


def prueba_adv_007_nombre_no_especificado():  # Comprueba que omitir la sección opcional NAME siga siendo válido pero produzca una recomendación.
    codigos = _codigos_advertencia("IP 192.168.80.0 MASK /24 HOSTS 50,30")  # Declara una red válida sin proporcionar ningún identificador.
    assert "ADV-007" in codigos  # Confirma que se sugiera añadir un nombre sin convertir su ausencia en error.