# ============================================================
# Archivo: transferencia_preferencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Exporta e importa exclusivamente las preferencias conocidas.
# Verifica el formato antes de escribir, conserva un respaldo y
# revierte los cambios parciales ante errores de almacenamiento.
# No incluye registros, proyectos ni archivos de modelos de IA.
# ============================================================

import json  # Serializa las preferencias en un formato portátil y legible.
from dataclasses import dataclass  # Describe el resultado de una importación.
from datetime import datetime  # Fecha los archivos exportados y los respaldos.
from pathlib import Path  # Administra las rutas seleccionadas por el usuario.
from uuid import uuid4  # Evita colisiones al crear archivos temporales.
from zipfile import ZIP_DEFLATED, ZipFile  # Guarda una copia exacta antes de importar.

from Motor.configuracion.restaurador_preferencias import ARCHIVO_IA, ARCHIVOS_GENERALES, _directorio_usuario, _reponer_original  # Reutiliza la ubicación y la recuperación ya comprobadas.
from Motor.configuracion.version_aplicacion import VERSION_VISIBLE  # Identifica la versión que generó el respaldo.


FORMATO = "TecNetFinder.Preferencias"  # Distingue estos archivos de cualquier otro JSON.
VERSION_FORMATO = 1  # Permite rechazar formatos futuros incompatibles.
LIMITE_ARCHIVO = 262144  # Rechaza archivos superiores a 256 KiB antes de procesarlos.
LIMITE_SECCION = 65536  # Evita importar archivos individuales desproporcionados.
SECCIONES = {"aplicacion": ARCHIVOS_GENERALES[0], "tema": ARCHIVOS_GENERALES[1], "advertencias": ARCHIVOS_GENERALES[2], "ia": ARCHIVO_IA}  # Relaciona las secciones con los gestores existentes.

CLAVES_BOOLEANAS_APLICACION = {  # Identifica exactamente las opciones que admiten verdadero o falso.
    "iniciar_maximizado", "recordar_estado_ventana", "recordar_seccion_configuracion",
    "ajuste_linea_editor", "mostrar_botones_rapidos_editor", "navegacion_automatica",
    "navegacion_errores", "navegacion_vlsm", "mostrar_advertencias_vlsm",
    "mostrar_advertencias_ventana", "cerrar_ventana_advertencias_al_navegar",
}
CLAVES_NUMERICAS = {"tamano_fuente_interfaz": (8, 14), "tamano_fuente_editor": (8, 20), "espacios_tabulacion_editor": (2, 8)}  # Replica los rangos de Configuración.
CLAVES_FUENTE = {"familia_fuente_interfaz", "familia_fuente_editor"}  # Solo admite nombres de tipografía no vacíos.
CLAVES_IA = {"asistencia_ia_activada", "autocompletado_ia_activado", "diagnosticos_ia_activados"}  # No exporta modelos ni rutas del runtime.
TEMAS = {  # Conserva los diez identificadores declarados en el catálogo visual.
    "oscuro_tecnet", "oscuro_medianoche", "oscuro_oceano", "oscuro_bosque", "oscuro_borgona",
    "claro_tecnet", "claro_niebla", "claro_marfil", "claro_lavanda", "claro_cerezo",
}


@dataclass(frozen=True)
class ResultadoImportacion:  # Permite mostrar el alcance real y la ubicación de recuperación.
    archivos: tuple[str, ...]
    respaldo: Path | None


def _validar_seccion(nombre: str, datos: object) -> dict:  # Impide sobrescribir preferencias con valores fuera de rango.
    if not isinstance(datos, dict): raise ValueError(f"La sección '{nombre}' debe ser un objeto JSON.")
    if len(json.dumps(datos, ensure_ascii=False).encode("utf-8")) > LIMITE_SECCION: raise ValueError(f"La sección '{nombre}' es demasiado grande.")
    aceptadas = {}  # Solo se entregan claves reconocidas por esta versión.
    for clave, valor in datos.items():
        if not isinstance(clave, str): raise ValueError("El archivo contiene una clave inválida.")
        valido = False  # Comprueba cada clave con sus reglas propias.
        if nombre == "aplicacion":
            if clave in CLAVES_BOOLEANAS_APLICACION: valido = type(valor) is bool
            elif clave in CLAVES_NUMERICAS: valido = type(valor) is int and (valor in (2, 4, 8) if clave == "espacios_tabulacion_editor" else CLAVES_NUMERICAS[clave][0] <= valor <= CLAVES_NUMERICAS[clave][1])
            elif clave in CLAVES_FUENTE: valido = isinstance(valor, str) and 0 < len(valor.strip()) <= 120
            elif clave == "idioma_interfaz": valido = isinstance(valor, str) and valor in ("es", "en", "pt", "fr", "de", "la")
            elif clave == "ultimo_estado_ventana": valido = valor is None or valor in ("normal", "maximizada")
            elif clave == "ultima_seccion_configuracion": valido = isinstance(valor, str) and valor in ("ventana", "editor", "resultados", "ia", "datos_preferencias")
        elif nombre == "tema":
            if clave == "tema": valido = isinstance(valor, str) and valor in TEMAS
            elif clave == "origen": valido = isinstance(valor, str) and valor in ("sistema", "manual")
        elif nombre == "advertencias":
            if clave == "bloquear_interaccion_fondo": valido = type(valor) is bool
        elif nombre == "ia":
            if clave in CLAVES_IA: valido = type(valor) is bool
        if not valido: raise ValueError(f"Preferencia no compatible o inválida: {nombre}.{clave}.")
        aceptadas[clave] = valor  # Agrega únicamente campos revisados.
    if nombre == "aplicacion" and aceptadas.get("mostrar_advertencias_vlsm") is True and aceptadas.get("mostrar_advertencias_ventana") is True:
        raise ValueError("El archivo intenta activar simultáneamente las dos modalidades de advertencias.")
    if nombre == "tema" and aceptadas.get("origen") == "manual" and "tema" not in aceptadas:
        raise ValueError("El tema manual requiere una variante válida.")
    return aceptadas  # Devuelve valores ya comprobados.


def _leer_json_limitado(ruta: Path) -> object:  # No carga en memoria archivos externos sin límite de tamaño.
    if not ruta.is_file(): raise ValueError(f"No se encontró el archivo: {ruta.name}.")
    if ruta.stat().st_size > LIMITE_ARCHIVO: raise ValueError("El archivo supera el tamaño máximo permitido (256 KiB).")
    try: return json.loads(ruta.read_text(encoding="utf-8"))  # Rechaza codificaciones y JSON incompatibles.
    except (OSError, UnicodeError, json.JSONDecodeError) as error: raise ValueError(f"No fue posible leer un JSON válido: {ruta.name}.") from error


def _cargar_paquete(ruta: str | Path) -> dict:  # Comprueba todo el paquete antes de presentar confirmaciones.
    paquete = _leer_json_limitado(Path(ruta))  # Lee el archivo sin modificar preferencias.
    if not isinstance(paquete, dict) or paquete.get("formato") != FORMATO or type(paquete.get("version_formato")) is not int or paquete["version_formato"] != VERSION_FORMATO:
        raise ValueError("El archivo no es un respaldo de preferencias compatible con TecNet Finder v1.2.2.")
    if not isinstance(paquete.get("preferencias"), dict): raise ValueError("Faltan las preferencias del archivo.")
    secciones = paquete["preferencias"]  # Recupera el contenido que debe importarse.
    if not {"aplicacion", "tema", "advertencias"}.issubset(secciones) or set(secciones) - set(SECCIONES): raise ValueError("El archivo contiene secciones faltantes o desconocidas.")
    return {nombre: _validar_seccion(nombre, datos) for nombre, datos in secciones.items()}  # Revisa todo, incluso la IA opcional.


def inspeccionar_preferencias(ruta: str | Path) -> bool:  # Informa si el archivo incluye IA sin importar ningún dato.
    return "ia" in _cargar_paquete(ruta)  # Permite que la interfaz prepare una confirmación informada.


def exportar_preferencias(ruta_destino: str | Path, *, incluir_ia: bool = False, directorio: str | Path | None = None) -> Path:  # Copia únicamente preferencias guardadas.
    raiz = Path(directorio) if directorio is not None else _directorio_usuario()  # Permite pruebas aisladas.
    secciones = {}  # Prepara el documento público, sin registros ni rutas personales.
    for seccion, archivo in SECCIONES.items():
        if seccion == "ia" and not incluir_ia: continue  # Excluye IA por defecto.
        ruta = raiz / archivo  # Accede únicamente a archivos del perfil conocidos.
        datos = _leer_json_limitado(ruta) if ruta.exists() else {}  # Usa valores iniciales si el usuario no tiene archivo.
        secciones[seccion] = _validar_seccion(seccion, datos)  # Evita exportar configuraciones dañadas.
    paquete = {"formato": FORMATO, "version_formato": VERSION_FORMATO, "version_aplicacion": VERSION_VISIBLE, "creado": datetime.now().isoformat(timespec="seconds"), "preferencias": secciones}  # Incluye metadatos mínimos.
    destino = Path(ruta_destino)  # Respeta la carpeta y el nombre elegidos por el usuario.
    if destino.suffix.lower() != ".json": raise ValueError("El archivo de exportación debe tener extensión .json.")
    if destino.resolve() in {(raiz / nombre).resolve() for nombre in SECCIONES.values()}:
        raise ValueError("No se puede exportar directamente sobre un archivo interno de preferencias.")
    temporal = destino.with_name(f".{destino.name}.{uuid4().hex}.tmp")  # Prepara la escritura atómica.
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)  # Crea el destino seleccionado cuando corresponde.
        temporal.write_text(json.dumps(paquete, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")  # Construye una copia legible.
        temporal.replace(destino)  # Nunca deja un JSON incompleto durante una interrupción.
    finally:
        if temporal.exists(): temporal.unlink()  # Elimina únicamente el temporal de esta exportación.
    return destino  # Informa la ruta guardada.


def importar_preferencias(ruta_origen: str | Path, *, incluir_ia: bool = False, directorio: str | Path | None = None) -> ResultadoImportacion:  # Importa solo después de validar todo.
    secciones = _cargar_paquete(ruta_origen)  # No toca archivos mientras el respaldo sea inválido.
    if incluir_ia and "ia" not in secciones: raise ValueError("El archivo no incluye preferencias de IA.")
    raiz = Path(directorio) if directorio is not None else _directorio_usuario()  # Reutiliza LocalAppData o una carpeta de prueba.
    nombres = ["aplicacion", "tema", "advertencias"] + (["ia"] if incluir_ia else [])  # Delimita las modificaciones autorizadas.
    rutas = {raiz / SECCIONES[seccion]: secciones[seccion] for seccion in nombres}  # Construye los archivos finales ya validados.
    originales = {ruta: ruta.read_bytes() if ruta.exists() else None for ruta in rutas}  # Conserva bytes exactos para revertir.
    existentes = [ruta for ruta, original in originales.items() if original is not None]  # Evita respaldos vacíos.
    respaldo = None  # Se informa si se creó una copia.
    if existentes:
        carpeta = raiz / "respaldos"  # Coloca respaldos fuera del código del proyecto.
        carpeta.mkdir(parents=True, exist_ok=True)  # Solo crea la carpeta para conservar archivos existentes.
        respaldo = carpeta / f"antes_importar_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.zip"  # Nunca pisa respaldos anteriores.
        try:
            with ZipFile(respaldo, "w", compression=ZIP_DEFLATED) as copia:
                for ruta in existentes: copia.writestr(ruta.name, originales[ruta])  # Guarda todos los valores que se reemplazarán.
        except Exception:
            if respaldo.exists(): respaldo.unlink()  # Impide continuar con una copia incompleta.
            raise
    temporales = {}  # Cada sección se escribe completa antes de sustituir un archivo real.
    cambiados = []  # Conserva el orden necesario para recuperar el perfil anterior.
    try:
        raiz.mkdir(parents=True, exist_ok=True)  # Permite importar a una instalación nueva.
        for ruta, datos in rutas.items():
            temporal = ruta.with_name(f".{ruta.name}.{uuid4().hex}.tmp")  # Evita interferir con los gestores actuales.
            temporales[ruta] = temporal  # Recuerda la ruta para el bloque finally.
            temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")  # No importa claves sin validar.
        for ruta, temporal in temporales.items():
            temporal.replace(ruta)  # Solo reemplaza cuando todos los temporales existen.
            cambiados.append(ruta)  # Permite recuperar un archivo ya escrito.
    except Exception as error:
        fallos = []  # No oculta los fallos secundarios al intentar revertir.
        for ruta in reversed(cambiados):
            try: _reponer_original(ruta, originales[ruta])  # Recupera los bytes previos o elimina un archivo inexistente.
            except OSError as fallo: fallos.append(f"{ruta.name}: {fallo}")  # Informa una reversión incompleta.
        if fallos: raise OSError("No se completó la importación y falló la reversión de: " + "; ".join(fallos)) from error
        raise  # Permite mostrar el fallo original.
    finally:
        for temporal in temporales.values():
            if temporal.exists(): temporal.unlink()  # No deja basura junto a las preferencias del usuario.
    return ResultadoImportacion(tuple(ruta.name for ruta in rutas), respaldo)  # Informa lo importado y la ruta de recuperación.
