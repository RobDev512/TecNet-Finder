# ============================================================
# Archivo: prueba_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba las advertencias no bloqueantes
# utilizadas actualmente por TecNet Finder.
#
# Incluye ADV-005 como advertencia semánticamente informada
# para redes base claramente sobredimensionadas.
# ============================================================

from Motor.flujo_compilacion import FlujoCompilacion  # Importa el flujo real utilizado por la aplicación.


def _codigos_advertencia(codigo: str) -> list[str]:
    resultado = FlujoCompilacion().analizar(codigo)  # Procesa la entrada utilizando exactamente el flujo de la interfaz.

    return [
        diagnostico.codigo
        for diagnostico in resultado.diagnosticos
        if diagnostico.severidad in ("warning", "advertencia")
    ]  # Devuelve únicamente códigos no bloqueantes.


def prueba_entrada_normal_no_genera_advertencias():
    codigos = _codigos_advertencia(
        "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"
    )

    assert codigos == []  # Confirma que una red razonablemente dimensionada permanezca limpia.


def prueba_adv_001_procesamiento_parcial():
    codigo = (
        "IP 192.168.1.0 /24 HOSTS 50 NAME Incorrecta\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"
    )

    codigos = _codigos_advertencia(codigo)

    assert "ADV-001" in codigos  # Confirma que un bloque recuperado produzca la advertencia de procesamiento parcial.


def prueba_adv_002_palabras_reservadas_pegadas():
    codigos = _codigos_advertencia(
        "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"
    )

    assert "ADV-002" in codigos


def prueba_adv_003_nombre_repetido():
    codigo = (
        "IP 192.168.50.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina"
    )

    codigos = _codigos_advertencia(codigo)

    assert "ADV-003" in codigos


def prueba_adv_004_hosts_repetidos():
    codigos = _codigos_advertencia(
        "IP 192.168.60.0 MASK /24 HOSTS 50,50,30 NAME Duplicados"
    )

    assert "ADV-004" in codigos


def prueba_adv_005_detecta_red_claramente_sobredimensionada():
    codigos = _codigos_advertencia(
        "IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada"
    )

    assert "ADV-005" in codigos  # Confirma que el caso académico reservado ya pueda evaluarse realmente.


def prueba_adv_005_se_activa_en_umbral_de_dieciseis_veces():
    codigos = _codigos_advertencia(
        "IP 192.168.1.0 MASK /24 HOSTS 10 NAME Sobrada"
    )

    assert "ADV-005" in codigos  # Una /24 tiene 256 direcciones y HOSTS 10 requiere un bloque de 16, exactamente una relación de 16 a 1.


def prueba_adv_005_no_se_activa_con_solo_ocho_veces_la_capacidad():
    codigos = _codigos_advertencia(
        "IP 192.168.1.0 MASK /24 HOSTS 20 NAME Adecuada"
    )

    assert "ADV-005" not in codigos  # HOSTS 20 requiere 32 direcciones y una /24 solamente es ocho veces mayor.


def prueba_adv_005_no_se_emite_sobre_bloque_semanticamente_invalido():
    codigos = _codigos_advertencia(
        "IP 10.20.0.0 MASK /8 HOSTS 10 NAME Invalida"
    )

    assert "ADV-005" not in codigos  # Evita recomendar tamaño sobre una red que ya fue rechazada por SEM-002.


def prueba_adv_006_nombre_generico():
    codigos = _codigos_advertencia(
        "IP 192.168.70.0 MASK /24 HOSTS 50 NAME Red"
    )

    assert "ADV-006" in codigos


def prueba_adv_007_nombre_no_especificado():
    codigos = _codigos_advertencia(
        "IP 192.168.80.0 MASK /24 HOSTS 50,30"
    )

    assert "ADV-007" in codigos