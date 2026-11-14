# TecNet Finder

**TecNet Finder v1.2.2 — Stability & Polish** es una aplicación de escritorio en Python y PySide6 y un lenguaje específico de dominio (DSL) para analizar instrucciones de redes IPv4 y realizar cálculos VLSM.

El proyecto comenzó en Lenguajes y Autómatas I (análisis léxico y sintáctico) y continuó en Lenguajes y Autómatas II, cuya Unidad 1 incorporó el análisis semántico. La v1.2.2 consolida la estabilidad del producto **sin agregar todavía generación de código intermedio**.

**Estado de la v1.2.2:** cerrada, validada en Windows (318 pruebas aprobadas, EXE e instalador probados) y publicada en [GitHub Releases](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.2.2).

## Lenguaje fuente

El DSL propio de TecNet Finder utiliza las palabras reservadas `IP`, `MASK`, `HOSTS` y `NAME` (opcional), siempre en mayúsculas.

```text
IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina
```

## Fases del compilador

- [x] Análisis léxico.
- [x] Análisis sintáctico.
- [x] Análisis semántico.
- [ ] Generación de código intermedio (planificada para v1.3.0 / Unidad 2).
- [ ] Optimización de código.
- [ ] Generación de código objeto.

## Funcionalidad actual

- Validación de instrucciones, diagnósticos léxicos, sintácticos y semánticos, advertencias y recuperación parcial.
- Planificación VLSM y visualización de resultados con exportación.
- Visor de árbol sintáctico y exportación PNG HD, SVG y PDF.
- Interfaz traducida a español, inglés, portugués, francés, alemán y latín; diez temas claros y oscuros.
- Configuración de fuentes, tamaño, ventana, editor, navegación y asistencia de IA.
- Autocompletado opcional con IA local y completador ligero sin IA para palabras reservadas del DSL.
- Menú contextual del editor traducido y adaptado al tema.
- Centro de estabilidad y mantenimiento con información del proyecto y consulta de logs rotativos.
- Restauración, importación y exportación de preferencias con validación y respaldos.
- Reporte local de excepciones inesperadas con opciones de copiar o guardar; no se envía a servidores.

## Ejecutar desde código fuente

Con Python 3.11 y las dependencias instaladas:

```powershell
python -m pip install -r requirements-build.txt
python -m pytest -q
python principal.py
```

Los modelos de IA y Ollama son **opcionales** para las fases básicas del compilador.

## Crear EXE e instalador en Windows

Requiere **Python 3.11, PyInstaller e Inno Setup 6 o 7**. El empaquetado se hace manualmente con los tres archivos permanentes de `Empaquetado/`:

- `TecNetFinder.spec`: configuración de PyInstaller para generar el EXE con sus dependencias.
- `TecNetFinder.iss`: configuración de Inno Setup para crear el instalador.
- `version_info.txt`: metadatos de versión del EXE.

Desde la raíz del proyecto, ejecuta las pruebas y compila mediante el archivo `.spec`:

```powershell
python -m pytest -q
python -m PyInstaller --noconfirm --clean --workpath "$env:TEMP\TecNetFinder-Build" --distpath ".\dist" ".\Empaquetado\TecNetFinder.spec"
```

Luego abre `Empaquetado/TecNetFinder.iss` con **Inno Setup**, comprueba que la versión indicada y la ruta de la carpeta `dist/TecNetFinder` sean correctas, y compila el instalador desde su interfaz. La versión y el contenido deben actualizarse antes de empaquetar futuras releases.

**Precaución con OneDrive:** el directorio del proyecto está sincronizado. Si PyInstaller no puede reemplazar `dist/TecNetFinder` por un bloqueo de archivos, cierra las instancias abiertas de la app y utiliza una carpeta de distribución fuera de OneDrive. En ese caso, adapta la ruta de origen del instalador en Inno Setup antes de compilar. No elimines forzosamente carpetas que estén en uso.

**Importante:** el ejecutable `TecNetFinder.exe` depende de los archivos de la carpeta `TecNetFinder/_internal`. Para distribuirlo, conserva toda la carpeta o utiliza el instalador; no copies únicamente el EXE.

Antes de publicar una versión, comprueba manualmente el EXE, realiza una prueba del instalador y verifica la suma SHA-256 del archivo final.

## Página web y demostración

La carpeta `site/` contiene la página del proyecto y una vista previa con slideshow y una **demo educativa de VLSM en JavaScript**. La demo no ejecuta el compilador Python, sus diagnósticos completos, ni la IA de escritorio; no envía el texto a servidores.


### Publicación y actualización de la página

La versión pública actual es [v1.2.2](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.2.2). El instalador oficial se ofrece desde GitHub Releases y la suma SHA-256 está escrita en la descripción de esa release.

Cuando se publique una nueva versión, actualiza manualmente el enlace de descarga, la descripción, el estado de la versión y el roadmap en `site/project-config.json`, `ROADMAP.md`, `site/ROADMAP.md` y, en el repositorio separado del Hub, `data/project-pages.json` y `projects/tecnet-finder/ROADMAP.md`. Publica los cambios en GitHub cuando la nueva descarga exista realmente.

Los archivos `site/index.html`, `site/tecnet-showcase.css` y `site/tecnet-showcase.js` aportan la demo visual en la página propia. La página del Hub conserva sus equivalentes en `projects/tecnet-finder/`.

## Licencia y documentación

Consulta `ROADMAP.md` para la evolución del producto. La publicación de un instalador o código fuente no implica añadir funciones de las unidades siguientes. Las evidencias académicas anteriores permanecen separadas de la nueva entrega.
