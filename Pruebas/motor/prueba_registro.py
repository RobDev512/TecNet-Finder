"""Pruebas del registro de eventos de TecNet Finder."""

import logging

from Motor.infraestructura.registro import configurar_registro, obtener_ruta_log


def prueba_crea_archivo(tmp_path):
    logger = configurar_registro(tmp_path)
    logger.info("evento de prueba")
    for manejador in logger.handlers:
        manejador.flush()
    archivo = obtener_ruta_log(logger)
    assert archivo == tmp_path / "tecnet-finder.log"
    assert "evento de prueba" in archivo.read_text(encoding="utf-8")


def prueba_no_duplica_manejadores(tmp_path):
    configurar_registro(tmp_path)
    logger = configurar_registro(tmp_path)
    manejadores = [
        h for h in logger.handlers if getattr(h, "_tecnet_logger", False)
    ]
    assert len(manejadores) == 1
    assert logger.propagate is False


def prueba_registra_excepciones(tmp_path):
    logger = configurar_registro(tmp_path, nivel=logging.DEBUG)
    try:
        raise ValueError("prueba controlada")
    except ValueError:
        logger.exception("Fallo inesperado")
    for manejador in logger.handlers:
        manejador.flush()
    contenido = (tmp_path / "tecnet-finder.log").read_text(encoding="utf-8")
    assert "Fallo inesperado" in contenido
    assert "ValueError: prueba controlada" in contenido
