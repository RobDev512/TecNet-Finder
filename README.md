# TecNet Finder

**TecNet Finder v1.2.2 — Stability & Polish** es una aplicación de escritorio en Python y PySide6 y un lenguaje específico de dominio (DSL) para analizar instrucciones de redes IPv4 y realizar cálculos VLSM.

El proyecto comenzó en Lenguajes y Autómatas I (análisis léxico y sintáctico) y continuó en Lenguajes y Autómatas II, cuya Unidad 1 incorporó el análisis semántico. La v1.2.2 consolida la estabilidad del producto **sin agregar todavía generación de código intermedio**.

**Estado de la v1.2.2:** cerrada y validada en Windows (318 pruebas, EXE, instalación, archivos de distribución y copia académica). **Publicación en GitHub Releases pendiente.**

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

Requiere **PyInstaller** e **Inno Setup 6 o 7**. No se puede construir de manera fiable el instalador de Windows desde un entorno que no sea Windows.

```powershell
.\Empaquetado\preparar_release_v122.ps1
```

El script ejecuta las pruebas y genera la distribución **onedir** de PyInstaller, el instalador de Inno Setup y los ZIP de distribución en una carpeta independiente bajo `%LOCALAPPDATA%\TecNetFinder\Releases`, fuera de OneDrive. Después de comprobar manualmente el EXE, instalar y desinstalar el paquete, copia los entregables al archivo académico **sin tocar las entregas antiguas**:

```powershell
.\Empaquetado\preparar_release_v122.ps1 -SoloCopiarAvance
```

Este segundo paso comprueba los SHA-256 existentes y crea exclusivamente `Avance 1/Release 1.2.2`.

**Importante:** el archivo `.exe` dentro de `dist/TecNetFinder` depende de otros archivos en esa misma carpeta. Para distribución utiliza el instalador o el ZIP portable completo; no copies únicamente el ejecutable.

Antes de publicar, ejecuta el EXE compilado, instala y desinstala el instalador en Windows y verifica SHA-256. El empaquetado por sí solo no confirma que la versión esté validada.

## Página web y demostración

La carpeta `site/` contiene la página del proyecto y una vista previa con slideshow y una **demo educativa de VLSM en JavaScript**. La demo no ejecuta el compilador Python, sus diagnósticos completos, ni la IA de escritorio; no envía el texto a servidores.


### Actualizar los datos públicos después de publicar

**No actualices el botón de descarga a v1.2.2 antes de que el instalador real esté disponible en GitHub Releases.** Después de crear la release `v1.2.2` y confirmar la URL del archivo, ejecuta:

```powershell
python .\Empaquetado\actualizar_web_release_v122.py --url "URL_REAL_DEL_INSTALADOR"
```

Si también tienes clonado el Hub `RobDev512.github.io`, añade `--hub "RUTA_LOCAL_DEL_REPOSITORIO_DEL_HUB"`. El script actualiza únicamente los metadatos locales de TecNet Finder y sincroniza los ROADMAP; **no publica ni hace push**. Los archivos `site/index.html`, `tecnet-showcase.css` y `tecnet-showcase.js` aportan la demo visual, mientras que el ZIP separado del Hub incluye los tres equivalentes para `projects/tecnet-finder/`.

## Licencia y documentación

Consulta `ROADMAP.md` para la evolución del producto. La publicación de un instalador o código fuente no implica añadir funciones de las unidades siguientes. Las evidencias académicas anteriores permanecen separadas de la nueva entrega.
