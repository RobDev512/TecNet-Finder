# ============================================================
# Archivo: cerrar_version_v122.py
# Proyecto: TecNet Finder
#
# Marca la v1.2.2 como cerrada y validada EN LOCAL en la
# documentación y páginas web, sin publicar en GitHub.
# Mantiene el enlace de descarga pública v1.2.1.
# ============================================================

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

VERSION = "v1.2.2"
NOMBRE = "Stability & Polish"
RAIZ = Path(__file__).resolve().parents[1]
URL_DESCARGA_ANTERIOR = "https://github.com/RobDev512/TecNet-Finder/releases/download/v1.2.1/"


def preparar_roadmap(texto: str) -> str:
    """Actualiza solo el estado de cierre y deja las demás versiones intactas."""
    if "## v1.2.2 — Stability & Polish" not in texto:
        raise ValueError("ROADMAP.md no contiene la sección v1.2.2 esperada.")

    inicio = texto.index("## Estado actual")
    fin = texto.index("\n---", inicio)
    cabecera = """## Estado actual

**Versión pública en GitHub:** v1.2.1
**Última versión cerrada y validada:** v1.2.2 — Stability & Polish
**Estado general:** v1.2.2 cerrada y validada en Windows el 14 de noviembre de 2026; publicación en GitHub Releases pendiente.
**Siguiente etapa planificada:** v1.3.0 — Intermediate Code Update

> Cada versión debe cubrir una necesidad académica concreta y, además,
> incorporar una mejora visible del producto.

> Nota histórica: el repositorio conserva el hito `lya1-base` como base final
> de Lenguajes y Autómatas I. Para que el roadmap SemVer muestre la evolución
> completa, ese hito se representa aquí como `v1.0.0`, aunque no existió un tag
> o release público con ese número.
"""
    texto = texto[:inicio] + cabecera.rstrip("\n") + "\n" + texto[fin:]

    inicio = texto.index("## v1.2.2 — Stability & Polish")
    fin = texto.index("\n---", inicio)
    seccion = texto[inicio:fin]
    seccion = re.sub(r"(?m)^\*\*Estado:\*\*.*$", "**Estado:** Aplicada", seccion, count=1)
    if "**Estado:** Aplicada" not in seccion:
        raise ValueError("No se pudo actualizar el estado de v1.2.2.")
    if "**Cierre local:**" not in seccion:
        seccion = re.sub(r"\*\*Estado:\*\* Aplicada\n", "**Estado:** Aplicada\n\n**Cierre local:** 14 de noviembre de 2026. EXE e instalador probados; 318 pruebas superadas.\n", seccion, count=1)
    validacion = """### Validación de cierre

- [x] 318 pruebas automatizadas aprobadas en Windows.
- [x] EXE generado con PyInstaller y aplicación comprobada visualmente.
- [x] Instalador generado con Inno Setup 7 e instalación probada.
- [x] ZIP portable, ZIP de código fuente y comprobaciones SHA-256 generados.
- [x] Entrega de release copiada a `Avance 1/Release 1.2.2` conservando las evidencias anteriores.
- [x] Slideshow y demo web VLSM revisados localmente.
- [ ] Publicar la release v1.2.2 en GitHub y actualizar su enlace público.

**Nota:** no se afirma haber probado la desinstalación ni todos los escenarios de idiomas y temas.
"""
    seccion, sustituciones = re.subn(r"(?s)### Comprobaciones antes de publicar\n.*$", validacion.rstrip("\n"), seccion, count=1)
    if sustituciones != 1 and "### Validación de cierre" not in seccion:
        raise ValueError("No se encontró la lista original de comprobaciones de v1.2.2.")
    texto = texto[:inicio] + seccion + texto[fin:]

    texto = texto.replace(
        "- No añadir nuevas funciones grandes a v1.2.2 durante su empaquetado y validación.",
        "- Mantener la v1.2.2 cerrada; nuevas funciones pertenecen a versiones posteriores.",
    ).replace(
        "- Conservar la última release publicada hasta validar y subir realmente el instalador v1.2.2.",
        "- Mantener el enlace de descarga pública v1.2.1 hasta publicar realmente el instalador v1.2.2.",
    )
    return texto


def preparar_readme(texto: str) -> str:
    aviso = "**Estado de la v1.2.2:** cerrada y validada en Windows (318 pruebas, EXE, instalación, archivos de distribución y copia académica). **Publicación en GitHub Releases pendiente.**"
    if aviso not in texto:
        if "## Lenguaje fuente" not in texto:
            raise ValueError("README.md no contiene el encabezado esperado.")
        texto = texto.replace("## Lenguaje fuente", aviso + "\n\n## Lenguaje fuente", 1)
    texto = texto.replace("**PyInstaller** e **Inno Setup 6**", "**PyInstaller** e **Inno Setup 6 o 7**")
    texto = texto.replace(
        "El script verifica las pruebas, empaqueta `dist/TecNetFinder/TecNetFinder.exe` en modo **onedir**, genera `dist/Instalador/TecNet Finder 1.2.2 Setup.exe` y prepara los ZIP portable y de código fuente.",
        "El script ejecuta las pruebas y genera la distribución **onedir** de PyInstaller, el instalador de Inno Setup y los ZIP de distribución en una carpeta independiente bajo `%LOCALAPPDATA%\\TecNetFinder\\Releases`, fuera de OneDrive.",
    )
    return texto


def preparar_pagina(datos: dict) -> dict:
    paginas = datos.get("pages", [])
    pagina = next((p for p in paginas if isinstance(p, dict) and p.get("id") == "tecnet-finder"), None)
    if not pagina:
        raise ValueError("No se encontró tecnet-finder en la configuración web.")
    acciones = pagina["hero"]["actions"]
    descarga = next((a for a in acciones if a.get("style") == "primary"), None)
    if descarga is None:
        raise ValueError("Falta el botón de descarga actual.")
    url = descarga.get("url", "")
    if not url.startswith(URL_DESCARGA_ANTERIOR):
        raise ValueError("El enlace público ya no es el de v1.2.1; no se modificará para evitar un retroceso.")

    # El botón sigue ofreciendo la última versión realmente publicada.
    descarga["label"] = "Descargar 1.2.1 (pública)"
    pagina["hero"]["meta"][0].update({
        "strong": VERSION,
        "small": "Cerrada · publicación pendiente",
    })
    pagina["release"].update({
        "kicker": "Versión cerrada · publicación pendiente",
        "version": VERSION,
        "status": "Cerrada y validada",
        "title": NOMBRE,
        "summary": "La v1.2.2 terminó su cierre local: 318 pruebas aprobadas, EXE e instalador verificados, respaldo académico y demo web revisada. La descarga pública permanece en v1.2.1 hasta publicar la nueva release en GitHub.",
        "items": [
            "Logs rotativos y Centro de estabilidad y mantenimiento.",
            "Restauración, exportación e importación de preferencias con validación.",
            "Reporte local de excepciones inesperadas.",
            "Menú contextual traducido y completador local independiente de la IA.",
            "Ajustes visuales, empaquetado Windows y 318 pruebas satisfactorias.",
        ],
    })
    pagina["nextRelease"].update({
        "kicker": "Siguiente etapa",
        "title": "v1.3.0 · Intermediate Code Update",
        "text": "Unidad 2: generación de código intermedio mediante tripletas, cuádruplos y Código P adaptados al DSL de redes.",
    })
    return datos


def escribir_atomico(ruta: Path, contenido: str) -> None:
    auxiliar = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=ruta.parent, prefix=ruta.name + ".", suffix=".tmp", delete=False) as archivo:
            auxiliar = Path(archivo.name)
            archivo.write(contenido)
        os.replace(auxiliar, ruta)
    finally:
        if auxiliar is not None and auxiliar.exists():
            auxiliar.unlink()


def ejecutar(hub: Path) -> list[Path]:
    rutas = {
        "readme": RAIZ / "README.md",
        "roadmap": RAIZ / "ROADMAP.md",
        "site_roadmap": RAIZ / "site" / "ROADMAP.md",
        "site_json": RAIZ / "site" / "project-config.json",
        "hub_roadmap": hub / "projects" / "tecnet-finder" / "ROADMAP.md",
        "hub_json": hub / "data" / "project-pages.json",
    }
    faltantes = [str(ruta) for ruta in rutas.values() if not ruta.is_file()]
    if faltantes:
        raise FileNotFoundError("Faltan archivos requeridos:\n" + "\n".join(faltantes))

    # Preparar y validar TODO antes de escribir un archivo.
    roadmap = preparar_roadmap(rutas["roadmap"].read_text(encoding="utf-8-sig"))
    readme = preparar_readme(rutas["readme"].read_text(encoding="utf-8-sig"))
    cambios = {
        rutas["readme"]: readme,
        rutas["roadmap"]: roadmap,
        rutas["site_roadmap"]: roadmap,
        rutas["hub_roadmap"]: roadmap,
    }
    for clave in ("site_json", "hub_json"):
        archivo = rutas[clave]
        datos = json.loads(archivo.read_text(encoding="utf-8-sig"))
        cambios[archivo] = json.dumps(preparar_pagina(datos), ensure_ascii=False, indent=2) + "\n"
    for archivo, contenido in cambios.items():
        actual = archivo.read_text(encoding="utf-8-sig")
        if actual != contenido:
            escribir_atomico(archivo, contenido)
            print("Actualizado:", archivo)
        else:
            print("Sin cambios:", archivo)
    print("\nCierre v1.2.2 registrado. La descarga pública sigue siendo v1.2.1.")
    print("No se ejecutó Git ni se publicó nada en Internet.")
    return list(cambios)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Marcar cierre local v1.2.2 en TecNet Finder y el Hub, sin publicar.")
    parser.add_argument("--hub", type=Path, default=RAIZ.parent.parent / "Proyectos HTML" / "RobDev512.github.io",
                        help="Raíz del repositorio local RobDev512.github.io")
    argumentos = parser.parse_args()
    try:
        ejecutar(argumentos.hub.expanduser().resolve())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.error(str(error))
