# TecNet Finder

**TecNet Finder** es una aplicación de escritorio en Python y PySide6 que utiliza un lenguaje específico de dominio (DSL) para analizar instrucciones de redes IPv4 y calcular subredes mediante VLSM.

La **[v1.3.0 — Código intermedio y triplos](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0)** corresponde a la Unidad 2 de Lenguajes y Autómatas II. Ya se integró en `main`, se publicó con el tag `v1.3.0` y cuenta con un instalador de Windows verificado. La rama `feature/v1.3.0-triplos` conserva el historial de desarrollo.

**Última release estable:** [v1.3.0 — Código intermedio y triplos](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0), publicada el 22 de noviembre de 2026 (hora de Nayarit) y validada con **399 pruebas automatizadas aprobadas en Windows**. Conserva las fases léxica, sintáctica y semántica y añade la generación, ejecución y visualización de triplos. La versión anterior, [v1.2.2 — Stability & Polish](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.2.2), permanece disponible en el historial de releases.

## Lenguaje fuente

El DSL propio de TecNet Finder utiliza las palabras reservadas `IP`, `MASK`, `HOSTS` y `NAME` (opcional), siempre en mayúsculas.

```text
IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina
```

## Fases del compilador

- [x] Análisis léxico.
- [x] Análisis sintáctico.
- [x] Análisis semántico.
- [x] Generación, interpretación y visualización de código intermedio mediante triplos (publicada en v1.3.0).
- [ ] Optimización de código.
- [ ] Generación de código objeto.

## Código intermedio de la v1.3.0

El generador trabaja **solo con los bloques aceptados por el análisis semántico**. Para cada instrucción `IP ... MASK ... HOSTS ...`, crea `INICIAR_RED` y procesa las solicitudes `HOSTS` de mayor a menor sin perder su índice de origen. Cada solicitud genera siete operaciones: `+`, `LOG2`, `CEIL`, `^`, `SOLICITUD`, `ASIGNAR_VLSM` y `SIGUIENTE_CURSOR`.

- `Motor/compilacion/triplos.py`: modelos `ReferenciaTriplo`, `OrigenTriplo`, `Triplo` y `ResultadoIntermedio`, con validación de índices, argumentos y referencias.
- `Compilador/generador_triplos.py`: transformación de bloques semánticamente válidos a operaciones consecutivas con metadatos de origen.
- `Motor/compilacion/interprete_triplos.py`: evaluación de cada triplo, resolución de referencias, asignación VLSM y registro de comprobaciones.
- `Motor/compilacion/modelos.py` y `Motor/compilacion/flujo_compilacion.py`: incorporación de `codigo_intermedio` y `ejecucion_intermedia` al resultado y al flujo general, sin sustituir la calculadora VLSM existente.
- `Interfaz/resultados/visor_triplos.py` y `Interfaz/resultados/panel_resultados.py`: visor en **Fases posteriores → Código intermedio**, con columnas `(n)`, `(Op, Arg1, Arg2)` y `Comprobación`, notación matemática, referencias de origen y botón para copiar.
- `Pruebas/motor/prueba_*triplos*.py`, `Pruebas/motor/prueba_integracion_flujo_triplos.py` y `Pruebas/interfaz/prueba_visor_triplos.py`: validaciones del modelo, generador, intérprete, equivalencia con VLSM, integración y presentación.

Ejemplo comprobado:

```text
IP 192.168.2.0 MASK /24 HOSTS 100,50 NAME Oficina
```

Genera **15 triplos**, asigna `192.168.2.0/25` a 100 hosts y `192.168.2.128/26` a 50 hosts. El cursor termina en `192.168.2.192`, dejando 64 direcciones sin asignar dentro de la red base. `NAME` evita la advertencia informativa `ADV-007`; no cambia el cálculo ni los triplos.

La representación intermedia **no es un programa ensamblador ni una pila**: sus referencias `(n)` conectan resultados anteriores y la columna de comprobación muestra los cálculos realizados. La optimización y la generación de código objeto siguen pendientes para unidades posteriores.

## Funcionalidad actual

- Validación de instrucciones, diagnósticos léxicos, sintácticos y semánticos, advertencias y recuperación parcial.
- Planificación VLSM, visualización de resultados y exportación; visor de triplos con comprobaciones matemáticas incluido en v1.3.0.
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

Comprueba que el comando termine con `Build complete!` y abre `dist\TecNetFinder\TecNetFinder.exe` para probar la aplicación. El archivo `.spec` **no requiere modificaciones** para la v1.3.0 porque ya incluye los recursos y el código de la aplicación.

**Precaución con OneDrive:** si aparece `PermissionError: [WinError 5]` cuando PyInstaller intenta reemplazar la carpeta `dist\TecNetFinder`, cierra los programas abiertos y genera la distribución fuera de OneDrive, por ejemplo:

```powershell
python -m PyInstaller --noconfirm --clean --workpath "$env:TEMP\TecNetFinder-Build" --distpath "$env:LOCALAPPDATA\TecNetFinder-Pruebas\dist" ".\Empaquetado\TecNetFinder.spec"
```

En ciertas instalaciones de Python desde Microsoft Store, esa ruta se redirige a `AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\TecNetFinder-Pruebas\dist`. Comprueba la ubicación real antes de copiar **la carpeta `TecNetFinder` completa** a `dist` en el proyecto; no borres carpetas bloqueadas ni sobrescribas una compilación en ejecución.

La **v1.3.0** se compiló con PyInstaller y se empaquetó mediante Inno Setup 7; su instalador definitivo fue probado en Windows y está disponible en [GitHub Releases](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0). El archivo `.iss` conserva el mismo `AppId` que la versión 1.2.2: la instalación de v1.3.0 puede actualizar la instalación anterior del mismo usuario.

**Instalador oficial:** [TecNet.Finder.1.3.0.Setup.exe](https://github.com/RobDev512/TecNet-Finder/releases/download/v1.3.0/TecNet.Finder.1.3.0.Setup.exe) (Windows). **SHA-256:** `ACC3BC65599A95DC0FFB2EAF107B07F15612A5C13EC152C3E77EA9B27CDE0424`. Se verificaron instalación, apertura y cálculos de triplos; no se afirma haber probado exhaustivamente la desinstalación.

**Importante:** el ejecutable `TecNetFinder.exe` depende de los archivos de la carpeta `TecNetFinder/_internal`. Para distribuirlo, conserva toda la carpeta o utiliza el instalador; no copies únicamente el EXE.

Para futuras versiones, comprueba manualmente el EXE, prueba el instalador y verifica el SHA-256 del archivo final antes de publicarlo.

## Página web y demostración

La carpeta `site/` contiene la página del proyecto y una vista previa con slideshow y una **demo educativa de VLSM en JavaScript**. La demo no ejecuta el compilador Python, sus diagnósticos completos, ni la IA de escritorio; no envía el texto a servidores.


### Publicación y actualización de la página

La última versión publicada es **[v1.3.0](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0)**. La descarga de Windows está disponible en [GitHub Releases](https://github.com/RobDev512/TecNet-Finder/releases/download/v1.3.0/TecNet.Finder.1.3.0.Setup.exe) y su SHA-256 coincide con el registrado en la descripción de la release.

La página de este repositorio utiliza `site/project-config.json`, `ROADMAP.md` y `site/ROADMAP.md` para mostrar la versión publicada. El **Hub de proyectos es un repositorio independiente**; si se utiliza, sus archivos `data/project-pages.json` y `projects/tecnet-finder/ROADMAP.md` requieren una actualización por separado. No se han modificado desde este paquete.

La guía técnica breve para el equipo de la Unidad 2 sigue pendiente: documentará **los archivos creados/modificados, la integración y las pruebas del código**, sin repetir teoría general sobre triplos.

Los archivos `site/index.html`, `site/tecnet-showcase.css` y `site/tecnet-showcase.js` aportan la demo visual en la página propia. La página del Hub conserva sus equivalentes en `projects/tecnet-finder/`.

## Licencia y documentación

Consulta `ROADMAP.md` para la evolución del producto. La release [v1.3.0](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0) cubre únicamente código intermedio y mejoras asociadas; no implica implementar las unidades siguientes. Las evidencias académicas anteriores permanecen separadas de la nueva entrega.
