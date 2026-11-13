"""Registro local de eventos para TecNet Finder, sin dependencias de Qt."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import tempfile

NOMBRE_LOGGER = "TecNetFinder"
NOMBRE_ARCHIVO = "tecnet-finder.log"
TAMANO_MAXIMO = 1_048_576
COPIAS = 3


def carpeta_logs_predeterminada() -> Path:
    """Evita escribir al lado del ejecutable o en Program Files."""
    carpeta_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if carpeta_base:
        return Path(carpeta_base) / "TecNetFinder" / "logs"
    return Path.home() / ".local" / "state" / "TecNetFinder" / "logs"


def configurar_registro(
    carpeta: str | os.PathLike[str] | None = None,
    *,
    nivel: int = logging.INFO,
) -> logging.Logger:
    """Configura un registro rotativo sin duplicar sus manejadores."""
    ruta_carpeta = Path(carpeta) if carpeta is not None else carpeta_logs_predeterminada()
    try:
        ruta_carpeta.mkdir(parents=True, exist_ok=True)
    except OSError:
        ruta_carpeta = Path(tempfile.gettempdir()) / "TecNetFinder" / "logs"
        ruta_carpeta.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(NOMBRE_LOGGER)
    logger.setLevel(nivel)
    logger.propagate = False
    for manejador in list(logger.handlers):
        if getattr(manejador, "_tecnet_logger", False):
            logger.removeHandler(manejador)
            manejador.close()

    manejador = RotatingFileHandler(
        ruta_carpeta / NOMBRE_ARCHIVO,
        maxBytes=TAMANO_MAXIMO,
        backupCount=COPIAS,
        encoding="utf-8",
    )
    manejador._tecnet_logger = True
    manejador.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(manejador)
    logger.info("Sistema de registro inicializado")
    return logger


def obtener_ruta_log(logger: logging.Logger | None = None) -> Path | None:
    """Devuelve la ruta real, incluso cuando se usa un directorio alternativo."""
    logger = logger or logging.getLogger(NOMBRE_LOGGER)
    for manejador in logger.handlers:
        if getattr(manejador, "_tecnet_logger", False):
            return Path(manejador.baseFilename)
    return None
