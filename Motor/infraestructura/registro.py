# ============================================================
# Archivo: registro.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra el registro local de eventos de TecNet Finder.
# Guarda información y excepciones en un archivo rotativo,
# con copias limitadas y sin depender de la interfaz PySide6.
#
# Los registros se almacenan fuera de la carpeta del proyecto
# para funcionar también desde el ejecutable instalado.
# ============================================================

from __future__ import annotations  # Permite utilizar anotaciones de tipos sin evaluarlas inmediatamente.

import logging  # Proporciona el sistema estándar de registro de eventos de Python.
import os  # Permite consultar las rutas configuradas en el entorno.
from logging.handlers import RotatingFileHandler  # Permite rotar los archivos al alcanzar su tamaño máximo.
from pathlib import Path  # Administra rutas locales sin concatenaciones manuales.
import tempfile  # Proporciona una carpeta alternativa si falla la ruta principal.


# ============================================================
# Identificación y límites del registro
# ============================================================

NOMBRE_LOGGER = "TecNetFinder"  # Identifica los eventos pertenecientes a la aplicación.
NOMBRE_ARCHIVO = "tecnet-finder.log"  # Define el nombre del archivo principal.
TAMANO_MAXIMO = 1_048_576  # Limita cada archivo a aproximadamente 1 MiB.
COPIAS = 3  # Conserva hasta tres respaldos rotativos.


# ============================================================
# Ubicación de los archivos de registro
# ============================================================

def carpeta_logs_predeterminada() -> Path:  # Obtiene la ubicación recomendada para guardar los eventos.
    """Evita escribir al lado del ejecutable o en Program Files."""
    carpeta_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")  # Prioriza el almacenamiento de usuario en Windows.

    if carpeta_base:  # Comprueba si el sistema proporcionó alguna de las rutas habituales.
        return Path(carpeta_base) / "TecNetFinder" / "logs"  # Evita guardar registros junto al ejecutable.

    return Path.home() / ".local" / "state" / "TecNetFinder" / "logs"  # Utiliza una ruta alternativa fuera de Windows.


# ============================================================
# Configuración del registro rotativo
# ============================================================

def configurar_registro(carpeta: str | os.PathLike[str] | None = None, *, nivel: int = logging.INFO) -> logging.Logger:  # Prepara el logger y sus archivos.
    """Configura un registro rotativo sin duplicar sus manejadores."""
    ruta_carpeta = Path(carpeta) if carpeta is not None else carpeta_logs_predeterminada()  # Acepta una ruta alternativa para las pruebas.

    try:  # Intenta preparar el directorio principal de registros.
        ruta_carpeta.mkdir(parents=True, exist_ok=True)  # Crea toda la estructura cuando todavía no existe.
    except OSError:  # Atiende falta de permisos u otros problemas con la ubicación principal.
        ruta_carpeta = Path(tempfile.gettempdir()) / "TecNetFinder" / "logs"  # Recupera una carpeta temporal del sistema.
        ruta_carpeta.mkdir(parents=True, exist_ok=True)  # Intenta crear el directorio alternativo.

    logger = logging.getLogger(NOMBRE_LOGGER)  # Recupera el identificador único del registro de TecNet Finder.
    logger.setLevel(nivel)  # Configura el nivel mínimo de eventos que serán guardados.
    logger.propagate = False  # Evita que los eventos se dupliquen en el logger raíz.

    for manejador in list(logger.handlers):  # Examina cualquier configuración anterior del mismo logger.
        if getattr(manejador, "_tecnet_logger", False):  # Identifica únicamente los manejadores propios de TecNet Finder.
            logger.removeHandler(manejador)  # Desvincula el archivo anterior para evitar duplicados.
            manejador.close()  # Libera el recurso asociado con el archivo.

    manejador = RotatingFileHandler(ruta_carpeta / NOMBRE_ARCHIVO, maxBytes=TAMANO_MAXIMO, backupCount=COPIAS, encoding="utf-8")  # Crea el archivo rotativo.
    manejador._tecnet_logger = True  # Marca el manejador para reconocerlo en futuras configuraciones.
    manejador.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))  # Define la presentación de cada evento.
    logger.addHandler(manejador)  # Activa la escritura de eventos en el archivo preparado.
    logger.info("Sistema de registro inicializado")  # Registra la finalización de la configuración.

    if carpeta is None:  # Instala el reporte de errores únicamente durante el inicio real; las pruebas aisladas no modifican los ganchos globales.
        from Motor.infraestructura.reporte_errores import instalar_reporte_errores  # Importa el capturador después de preparar el logger para evitar dependencias circulares.
        instalar_reporte_errores(logger)  # Conserva errores inesperados y permite ofrecer un reporte al usuario.

    return logger  # Devuelve el logger listo para ser utilizado por la aplicación.


# ============================================================
# Consulta de la ubicación activa
# ============================================================

def obtener_ruta_log(logger: logging.Logger | None = None) -> Path | None:  # Consulta el archivo realmente utilizado por el registro.
    """Devuelve la ruta real, incluso cuando se usa un directorio alternativo."""
    logger = logger or logging.getLogger(NOMBRE_LOGGER)  # Utiliza el logger recibido o recupera el principal.

    for manejador in logger.handlers:  # Examina los manejadores actualmente asociados con el registro.
        if getattr(manejador, "_tecnet_logger", False):  # Selecciona exclusivamente el archivo de TecNet Finder.
            return Path(manejador.baseFilename)  # Devuelve la ruta real, incluso si se utilizó una carpeta temporal.

    return None  # Indica que el registro todavía no ha sido configurado.
