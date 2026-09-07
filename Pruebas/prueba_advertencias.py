# ============================================================
# Archivo: prueba_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba las advertencias no bloqueantes
# recuperadas desde la versión anterior de TecNet Finder.
#
# También verifica que ADV-005 permanezca reservado hasta la
# implementación formal del análisis semántico.
# ============================================================

from Motor.flujo_compilacion import FlujoCompilacion  # Importa el flujo real utilizado por la aplicación.


def _codigos_advertencia(codigo: str) -> list[str]:  # Ejecuta una entrada y devuelve solamente las advertencias producidas.
    resultado = FlujoCompilacion().analizar(codigo)  # Procesa la entrada mediante las mismas partes utilizadas por la interfaz.

    return [
        diagnostico.codigo
        for diagnostico in resultado.diagnosticos
        if diagnostico.severidad in ("warning", "advertencia")
    ]


def prueba_entrada_normal_no_genera_advertencias():  # Comprueba que una entrada convencional y descriptiva permanezca limpia.
    codigos = _codigos_advertencia(
        "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"
    )

    assert codigos == []


def prueba_adv_001_procesamiento_parcial():  # Comprueba que una entrada con errores y otro bloque válido informe el procesamiento parcial.
    codigo = (
        "IP 192.168.1.0 /24 HOSTS 50 NAME Incorrecta\n"
        "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Central"
    )

    codigos = _codigos_advertencia(codigo)

    assert "ADV-001" in codigos


def prueba_adv_002_palabras_reservadas_pegadas():  # Comprueba la recomendación de legibilidad para palabras reservadas pegadas.
    codigos = _codigos_advertencia(
        "IP192.168.40.0 MASK/24 HOSTS50 NAME Pegada"
    )

    assert "ADV-002" in codigos


def prueba_adv_003_nombre_repetido():  # Comprueba que dos redes distintas puedan compartir nombre pero produzcan advertencia.
    codigo = (
        "IP 192.168.50.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "IP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina"
    )

    codigos = _codigos_advertencia(codigo)

    assert "ADV-003" in codigos


def prueba_adv_004_hosts_repetidos():  # Comprueba la recomendación cuando una cantidad aparece varias veces.
    codigos = _codigos_advertencia(
        "IP 192.168.60.0 MASK /24 HOSTS 50,50,30 NAME Duplicados"
    )

    assert "ADV-004" in codigos


def prueba_adv_006_nombre_generico():  # Comprueba que nombres considerados poco descriptivos produzcan recomendación.
    codigos = _codigos_advertencia(
        "IP 192.168.70.0 MASK /24 HOSTS 50 NAME Red"
    )

    assert "ADV-006" in codigos


def prueba_adv_007_nombre_no_especificado():  # Comprueba que NAME siga siendo opcional pero se recomiende utilizarlo.
    codigos = _codigos_advertencia(
        "IP 192.168.80.0 MASK /24 HOSTS 50,30"
    )

    assert "ADV-007" in codigos


def prueba_adv_005_permanece_pendiente_hasta_analisis_semantico():  # Evita adelantar la evaluación de capacidad de la red base.
    codigos = _codigos_advertencia(
        "IP 10.0.0.0 MASK /8 HOSTS 10 NAME Sobrada"
    )

    assert "ADV-005" not in codigos