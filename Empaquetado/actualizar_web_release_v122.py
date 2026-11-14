# ============================================================
# Archivo: actualizar_web_release_v122.py
# Proyecto: TecNet Finder
#
# Descripción:
# Actualiza METADATOS LOCALES de la web tras publicar la release.
# No realiza solicitudes de red, git commit, push ni publicación.
# ============================================================

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

VERSION = "1.2.2"
NOMBRE = "Stability & Polish"
RAIZ = Path(__file__).resolve().parent.parent


def comprobar_enlace(url: str) -> str:
    valor = url.strip()
    parsed = urlparse(valor)
    if (parsed.scheme != "https" or parsed.netloc != "github.com" or
            not parsed.path.startswith("/RobDev512/TecNet-Finder/releases/download/v1.2.2/")):
        raise ValueError("Indica la URL real del instalador publicado en la release v1.2.2 de GitHub.")
    return valor


def actualizar_pagina(datos: dict, enlace: str) -> dict:
    paginas = datos.get("pages")
    if not isinstance(paginas, list):
        raise ValueError("No se encontró la colección de páginas de proyecto.")
    pagina = next((x for x in paginas if isinstance(x, dict) and x.get("id") == "tecnet-finder"), None)
    if pagina is None:
        raise ValueError("No se encontró la página tecnet-finder.")

    acciones = pagina["hero"]["actions"]
    descarga = next((x for x in acciones if x.get("style") == "primary"), None)
    if descarga is None:
        raise ValueError("No se encontró la acción de descarga del proyecto.")
    descarga["label"] = "Descargar 1.2.2"
    descarga["url"] = enlace
    pagina["hero"]["meta"][0].update({"strong": "v1.2.2", "small": NOMBRE})

    pagina["release"].update({
        "kicker": "Release actual", "version": "v1.2.2", "status": "Publicada", "title": NOMBRE,
        "summary": "v1.2.2 consolida la estabilidad del compilador y mejora mantenimiento, preferencias y edición sin introducir todavía generación de código intermedio.",
        "items": [
            "Logs rotativos y Centro de estabilidad y mantenimiento.",
            "Restaurar, exportar e importar preferencias con respaldos.",
            "Reporte local de errores inesperados.",
            "Menú contextual traducido y completador local de palabras reservadas.",
            "Correcciones visuales y funcionamiento conservado en seis idiomas y diez temas.",
        ],
    })
    pagina["nextRelease"].update({
        "kicker": "Siguiente etapa", "title": "v1.3.0 · Intermediate Code Update",
        "text": "Unidad 2: generación de código intermedio, tripletas, cuádruplos y Código P adaptados al DSL de redes.",
    })
    return datos


def roadmap_publicado(texto: str) -> str:
    # A partir del cierre local, cambia a publicada SOLO cuando exista
    # la URL real del instalador en GitHub Releases.
    texto = texto.replace("**Versión pública en GitHub:** v1.2.1", "**Versión pública en GitHub:** v1.2.2")
    texto = texto.replace("**Última versión cerrada y validada:** v1.2.2 — Stability & Polish", "**Última versión cerrada y publicada:** v1.2.2 — Stability & Polish")
    texto = texto.replace("**Estado general:** v1.2.2 cerrada y validada en Windows el 14 de noviembre de 2026; publicación en GitHub Releases pendiente.", "**Estado general:** v1.2.2 cerrada, validada y publicada en GitHub Releases; v1.3.0 es la siguiente etapa.")
    texto = texto.replace("- [ ] Publicar la release v1.2.2 en GitHub y actualizar su enlace público.", "- [x] Publicar la release v1.2.2 en GitHub y actualizar su enlace público.")
    texto = texto.replace("- Mantener el enlace de descarga pública v1.2.1 hasta publicar realmente el instalador v1.2.2.", "- Mantener enlazada la descarga publicada en GitHub Releases y sus verificaciones.")
    # Retrocompatibilidad con el roadmap de preparación original.
    texto = texto.replace("**Última versión pública comprobada:** v1.2.1", "**Versión pública en GitHub:** v1.2.2")
    texto = texto.replace("**Versión candidata a publicación:** v1.2.2 — Stability & Polish", "**Última versión cerrada y publicada:** v1.2.2 — Stability & Polish")
    texto = texto.replace("**Estado general:** Funciones v1.2.2 terminadas; pendiente validación del EXE, instalador y publicación", "**Estado general:** v1.2.2 cerrada, validada y publicada en GitHub Releases; v1.3.0 es la siguiente etapa.")
    texto = texto.replace("**Estado:** Cierre funcional realizado; pendiente validación de release Windows y publicación.", "**Estado:** Aplicada")
    return texto


def escribir_json(ruta: Path, datos: dict) -> None:
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    try:
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal.replace(ruta)
    finally:
        if temporal.exists():
            temporal.unlink()


def ejecutar(enlace: str, raiz_hub: Path | None = None) -> list[Path]:
    url = comprobar_enlace(enlace)
    proyecto = RAIZ
    config_app = proyecto / "site" / "project-config.json"
    mapa_app = proyecto / "ROADMAP.md"
    if not config_app.is_file() or not mapa_app.is_file():
        raise FileNotFoundError("Faltan site/project-config.json o ROADMAP.md en TecNet Finder.")
    datos_app = json.loads(config_app.read_text(encoding="utf-8"))
    mapa = roadmap_publicado(mapa_app.read_text(encoding="utf-8"))
    actualizar_pagina(datos_app, url)

    hub_config = None
    datos_hub = None
    if raiz_hub is not None:
        hub_config = raiz_hub / "data" / "project-pages.json"
        if not hub_config.is_file():
            raise FileNotFoundError(f"No existe el archivo del Hub: {hub_config}")
        datos_hub = json.loads(hub_config.read_text(encoding="utf-8"))
        actualizar_pagina(datos_hub, url)
        if not (raiz_hub / "projects" / "tecnet-finder").is_dir():
            raise FileNotFoundError("No existe projects/tecnet-finder en el Hub.")

    escribir_json(config_app, datos_app)
    mapa_app.write_text(mapa, encoding="utf-8")
    ruta_mapa_site = proyecto / "site" / "ROADMAP.md"
    ruta_mapa_site.write_text(mapa, encoding="utf-8")
    modificados = [config_app, mapa_app, ruta_mapa_site]
    if hub_config is not None and datos_hub is not None:
        escribir_json(hub_config, datos_hub)
        ruta_mapa_hub = raiz_hub / "projects" / "tecnet-finder" / "ROADMAP.md"
        ruta_mapa_hub.write_text(mapa, encoding="utf-8")
        modificados.extend((hub_config, ruta_mapa_hub))
    return modificados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actualizar referencias web después de publicar el instalador v1.2.2")
    parser.add_argument("--url", required=True, help="Enlace REAL al instalador de GitHub Releases v1.2.2")
    parser.add_argument("--hub", type=Path, default=None, help="Ruta local del repositorio RobDev512.github.io")
    argumentos = parser.parse_args()
    try:
        for archivo in ejecutar(argumentos.url, argumentos.hub):
            print("Actualizado:", archivo)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.error(str(error))
