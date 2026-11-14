# ============================================================
# Archivo: restaurador_preferencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Restablece exclusivamente las preferencias locales conocidas.
# Conserva los registros, los ejemplos y los modelos de IA.
# Crea un respaldo previo y evita cambios parciales ante fallos.
# ============================================================

from dataclasses import dataclass  # Estructura el resultado entregado a la interfaz.
from datetime import datetime  # Identifica los respaldos por fecha y hora.
import os  # Consulta el directorio local del usuario.
from pathlib import Path  # Administra las ubicaciones sin concatenaciones inseguras.
from uuid import uuid4  # Evita colisiones en los nombres temporales.
from zipfile import ZIP_DEFLATED, ZipFile  # Conserva los archivos anteriores en un respaldo pequeño.


ARCHIVOS_GENERALES = ("preferencias_aplicacion.json", "preferencias_tema.json", "preferencias_modalidad_advertencias.json")  # Configuración general, visual y de advertencias.
ARCHIVO_IA = "preferencias_ia.json"  # Se restablece solamente cuando el usuario lo pide de manera explícita.


@dataclass(frozen=True)
class ResultadoRestauracion:  # Comunica qué archivos se restablecieron y dónde quedó el respaldo.
    archivos: tuple[str, ...]
    respaldo: Path | None


def _directorio_usuario() -> Path:  # Utiliza la ubicación persistente oficial del proyecto.
    local = os.environ.get("LOCALAPPDATA")  # Busca primero la ruta recomendada por Windows.
    return (Path(local) if local else Path.home() / "AppData" / "Local") / "TecNetFinder"  # No toca el directorio del código fuente.


def _reponer_original(ruta: Path, original: bytes | None) -> None:  # Recupera un archivo anterior cuando falla una operación.
    if original is None:  # El archivo no existía antes del intento.
        if ruta.exists(): ruta.unlink()  # Retira únicamente el archivo que se acababa de crear.
        return
    temporal = ruta.with_name(f".{ruta.name}.{uuid4().hex}.rollback")  # Escribe primero una copia íntegra del original.
    try:
        temporal.write_bytes(original)  # Recupera los bytes originales, incluso si el JSON estaba dañado.
        temporal.replace(ruta)  # Reemplaza el valor incompleto sin modificar otros archivos.
    finally:
        if temporal.exists(): temporal.unlink()  # No conserva archivos temporales innecesarios.


def restaurar_preferencias(*, incluir_ia: bool = False, directorio: str | Path | None = None) -> ResultadoRestauracion:  # Restablece los valores que sus propios gestores consideran predeterminados.
    raiz = Path(directorio) if directorio is not None else _directorio_usuario()  # Acepta una ruta aislada para pruebas.
    nombres = ARCHIVOS_GENERALES + ((ARCHIVO_IA,) if incluir_ia else ())  # No modifica la IA por accidente.
    rutas = [raiz / nombre for nombre in nombres]  # Limita las modificaciones a los archivos conocidos.
    originales: dict[Path, bytes | None] = {}  # Conserva el estado anterior para respaldo y reversión.

    for ruta in rutas:  # Comprueba todos los archivos antes de cambiar uno solo.
        originales[ruta] = ruta.read_bytes() if ruta.exists() else None  # Guarda bytes exactos, sin reformatear JSON.

    respaldo = None  # Un usuario nuevo no requiere un ZIP de archivos inexistentes.
    existentes = [ruta for ruta in rutas if originales[ruta] is not None]  # Incluye solamente archivos que realmente estaban guardados.
    if existentes:  # Genera el respaldo antes de efectuar cualquier modificación.
        carpeta_respaldos = raiz / "respaldos"  # Los respaldos permanecen fuera del proyecto y del repositorio Git.
        carpeta_respaldos.mkdir(parents=True, exist_ok=True)  # Crea la carpeta únicamente cuando hace falta.
        respaldo = carpeta_respaldos / f"preferencias_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.zip"  # Evita reemplazar respaldos anteriores.
        try:
            with ZipFile(respaldo, "w", compression=ZIP_DEFLATED) as archivo:  # Escribe un respaldo que podrá utilizarse en el futuro.
                for ruta in existentes: archivo.writestr(ruta.name, originales[ruta])  # Conserva el contenido exacto de cada JSON.
        except Exception:  # No toca preferencias si ni siquiera pudo crearse el respaldo.
            if respaldo.exists(): respaldo.unlink()  # Evita dejar un ZIP a medio escribir.
            raise

    raiz.mkdir(parents=True, exist_ok=True)  # Permite guardar las preferencias iniciales en una instalación nueva.
    temporales: dict[Path, Path] = {}  # Prepara todos los archivos antes de comenzar a sustituirlos.
    cambiados: list[Path] = []  # Registra qué preferencias deben revertirse ante un error.
    try:
        for ruta in rutas:
            temporal = ruta.with_name(f".{ruta.name}.{uuid4().hex}.tmp")  # Evita interferir con los .tmp propios de los gestores.
            temporales[ruta] = temporal  # Recuerda el archivo para limpiarlo si algo falla.
            temporal.write_text("{}\n", encoding="utf-8")  # La ausencia de claves recupera los valores por defecto de cada gestor.
        for ruta, temporal in temporales.items():
            temporal.replace(ruta)  # Sustituye cada preferencia solamente después de completar todas las escrituras.
            cambiados.append(ruta)  # Permite una reversión selectiva en caso de error posterior.
    except Exception as error:
        errores_reversion = []  # Informa si Windows impide devolver alguno de los archivos anteriores.
        for ruta in reversed(cambiados):
            try: _reponer_original(ruta, originales[ruta])  # Recupera el estado original de las preferencias ya sustituidas.
            except OSError as fallo: errores_reversion.append(f"{ruta.name}: {fallo}")  # No oculta una reversión fallida.
        detalle = "; ".join(errores_reversion)  # Evita perder información ante un fallo de recuperación.
        if detalle: raise OSError(f"No se completó la restauración; falló también la reversión de: {detalle}") from error
        raise  # Propaga el fallo original para que la interfaz lo muestre.
    finally:
        for temporal in temporales.values():  # No deja residuos temporales después de aplicar o cancelar.
            if temporal.exists(): temporal.unlink()  # Limpia únicamente archivos creados por esta operación.

    return ResultadoRestauracion(tuple(nombres), respaldo)  # Informa al usuario que debe reiniciar la aplicación.
