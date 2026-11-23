# ROADMAP — TecNet Finder

## Estado actual

**Versión pública en GitHub:** [v1.3.0](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0)
**Última versión cerrada y publicada:** v1.3.0 — Código intermedio y triplos
**Estado general:** v1.3.0 publicada e instalada en Windows; 399 pruebas automatizadas aprobadas y SHA-256 del instalador verificado.
**Siguiente etapa planificada:** v1.3.1 — Language Lab (pendiente; v1.4.0 optimización y v2.0.0 código objeto continúan en el roadmap).

> Cada versión debe cubrir una necesidad académica concreta y, además,
> incorporar una mejora visible del producto.

> Nota histórica: el repositorio conserva el hito `lya1-base` como base final
> de Lenguajes y Autómatas I. Para que el roadmap SemVer muestre la evolución
> completa, ese hito se representa aquí como `v1.0.0`, aunque no existió un tag
> o release público con ese número.

---

## v1.0.0 — Base de Lenguajes y Autómatas I

**Estado:** Aplicada
**Hito histórico:** reconstrucción SemVer del tag `lya1-base`

Primera base funcional del proyecto desarrollada en Lenguajes y Autómatas I.

### Compilador

- Análisis léxico.
- Análisis sintáctico.
- Análisis semántico todavía pendiente.

### Producto

- DSL orientado a redes.
- Procesamiento de IPv4, máscaras y requerimientos de hosts.
- Cálculo VLSM.
- Interfaz gráfica en PySide6.

---

## v1.1.0 — Packaged Release

**Estado:** Aplicada

Primera versión empaquetada y distribuible de TecNet Finder.

### Incluido

- Analizador léxico y sintáctico.
- Cálculo VLSM.
- Diagnósticos y advertencias.
- Exportación de resultados.
- Interfaz gráfica de escritorio.
- Integración opcional de asistencia local con IA.
- Instalador para Windows.

---

## v1.2.0 — Semantic Update

**Estado:** Aplicada

Cierre funcional de la Unidad 1 de Lenguajes y Autómatas II mediante la
incorporación del análisis semántico.

### Compilador

- Análisis léxico.
- Análisis sintáctico.
- Análisis semántico.
- Cálculo VLSM.
- Diagnósticos léxicos, sintácticos y semánticos.
- Advertencias.
- Recuperación parcial ante entradas con errores.
- Exportación de resultados.

### Infraestructura y producto

- Ejemplos válidos e inválidos ampliados.
- Pruebas automáticas de ejemplos y diagnósticos.
- Arquitectura interna reorganizada por áreas funcionales.
- Separación de Interfaz, Motor y Asistente IA.
- Suite de pruebas reorganizada por dominio.
- Temas claros y oscuros mejorados.
- Empaquetado e instalación actualizados.
- 164 pruebas automáticas superadas al cierre de la versión.

---

## v1.2.1 — Final Polish & Internationalization

**Estado:** Aplicada

Versión estable anterior y cierre de estabilización posterior a la integración semántica.

### Internacionalización

- Español.
- English.
- Português.
- Français.
- Deutsch.
- Lingua Latina.
- Ejemplos localizados sin modificar palabras reservadas del DSL.
- Diagnósticos, diálogos y configuraciones traducidos.

### Interfaz y editor

- Configuración de tipografía de interfaz y editor.
- Tamaños de fuente configurables.
- Números de línea sincronizados con el tamaño de fuente.
- Correcciones finales de interfaz y estabilidad.

### Árbol sintáctico y exportación

- Visualización del árbol sintáctico mejorada.
- Nodos circulares para terminales cortos.
- Centrado de ramas y nodos corregido.
- Exportación PNG de alta resolución.
- Exportación vectorial SVG.
- Exportación directa a PDF.

### Compilador consolidado

- Análisis léxico.
- Análisis sintáctico.
- Análisis semántico.
- Diagnósticos y advertencias.
- Recuperación parcial ante bloques con errores.
- Cálculo VLSM.
- Asistencia local opcional mediante IA.

---

## v1.2.2 — Stability & Polish

**Estado:** Aplicada

**Cierre local:** 14 de noviembre de 2026. EXE e instalador probados; 318 pruebas superadas.

Versión de estabilidad posterior a la revisión docente. No introduce una unidad nueva ni genera código intermedio.

### Función estrella

Centro de estabilidad y mantenimiento.

### Funciones implementadas

- Sistema de logs rotativos y consulta desde la interfaz.
- Información de la aplicación, sección Acerca de y versión centralizada.
- Restauración de preferencias con confirmación y respaldo.
- Exportación/importación de preferencias en JSON con validación.
- Reportes locales de excepciones inesperadas (copiar y guardar).
- Menús contextuales del editor traducidos y acordes con los temas.
- Completador local sin IA para palabras reservadas del DSL, separado del autocompletado con IA.
- Correcciones visuales: centrado, estilos, barras de desplazamiento y ventanas.
- Slideshow de presentación y demo educativa web de cálculo VLSM, independiente del compilador Python.

### Validación de cierre

- [x] 318 pruebas automatizadas aprobadas en Windows.
- [x] EXE generado con PyInstaller y aplicación comprobada visualmente.
- [x] Instalador generado con Inno Setup 7 e instalación probada.
- [x] ZIP portable, ZIP de código fuente y comprobaciones SHA-256 generados.
- [x] Entrega de release copiada a `Avance 1/Release 1.2.2` conservando las evidencias anteriores.
- [x] Slideshow y demo web VLSM revisados localmente.
- [x] Publicar la release v1.2.2 en GitHub y actualizar su enlace público.

**Nota:** no se afirma haber probado la desinstalación ni todos los escenarios de idiomas y temas.
---

## v1.3.0 — Intermediate Code Update

**Estado:** Publicada como release estable el 22 de noviembre de 2026 (hora de Nayarit), con instalador de Windows validado.
**Rama estable:** `main` (integración *fast-forward* de `feature/v1.3.0-triplos`).
**Versión anterior:** v1.2.2 — Stability & Polish.
**Commit y tag de publicación:** [`885a2a3`](https://github.com/RobDev512/TecNet-Finder/commit/885a2a3) · [`v1.3.0`](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0).
**Pruebas automatizadas:** **399 aprobadas** en Windows después de actualizar los metadatos de versión.
**Instalador publicado:** [TecNet.Finder.1.3.0.Setup.exe](https://github.com/RobDev512/TecNet-Finder/releases/download/v1.3.0/TecNet.Finder.1.3.0.Setup.exe) (56 015 714 bytes).
**SHA-256:** `ACC3BC65599A95DC0FFB2EAF107B07F15612A5C13EC152C3E77EA9B27CDE0424`.

### Función estrella

Visor educativo de **código intermedio mediante triplos** con referencias a resultados anteriores, comprobaciones matemáticas y asignaciones reales de subredes IPv4 mediante VLSM.

### Implementación completada

- [x] **Modelos:** `Motor/compilacion/triplos.py` incorpora `ReferenciaTriplo`, `OrigenTriplo`, `Triplo` y `ResultadoIntermedio`. Valida aridad, tipos, secuencia de índices y referencias solo a triplos anteriores.
- [x] **Generación:** `Compilador/generador_triplos.py` produce `INICIAR_RED` por bloque y, por cada solicitud `HOSTS` de mayor a menor, `+`, `LOG2`, `CEIL`, `^`, `SOLICITUD`, `ASIGNAR_VLSM`, `SIGUIENTE_CURSOR`. Preserva la posición original de cada solicitud, incluso cuando se reordena.
- [x] **Ejecución:** `Motor/compilacion/interprete_triplos.py` resuelve referencias `(n)`, conserva resultados por índice, calcula límites de subred y comprueba cada operación; el cursor avanza a la primera dirección disponible después del broadcast.
- [x] **Integración:** `Motor/compilacion/flujo_compilacion.py` y `Motor/compilacion/modelos.py` adjuntan `codigo_intermedio` y `ejecucion_intermedia` al resultado general. Solo se utilizan bloques semánticamente válidos; la calculadora VLSM original, las advertencias y la recuperación parcial se conservan.
- [x] **Errores controlados:** los fallos técnicos de generación o ejecución se transforman en diagnóstico `GEN-002` sin sustituir los resultados anteriores de VLSM.
- [x] **Visor de PySide6:** `Interfaz/resultados/visor_triplos.py`, integrado en `Interfaz/resultados/panel_resultados.py` dentro de «Fases posteriores → Código intermedio». Tres columnas: `(n)`, `(Op, Arg1, Arg2)` y «Comprobación», con representación matemática de `log₂`, potencias y redondeos.
- [x] **Experiencia de usuario:** botón de copiar con icono, ayudas de origen por línea/bloque/host, vaciado al modificar el código y adaptación a temas y seis idiomas.
- [x] **Mantenimiento y versiones:** los seis catálogos muestran **v1.3.0** como versión actual y estable, con las novedades de código intermedio y triplos.
- [x] **Pruebas:** modelos, generación, ejecución, equivalencia VLSM, recuperación parcial, visor, selectores y traducciones. Suite completa final: **399 passed** en Windows.
- [x] **Control de versiones:** los 11 commits de `feature/v1.3.0-triplos` se integraron en `main` mediante *fast-forward*, y se publicó el tag `v1.3.0`.

### Ejemplo comprobado

```text
IP 192.168.2.0 MASK /24 HOSTS 100,50 NAME Oficina
```

- Triplos generados: **15**; el primero inicia la red y se producen siete por solicitud.
- Para 100 hosts: `192.168.2.0/25`, 128 direcciones, broadcast `192.168.2.127`.
- Para 50 hosts: `192.168.2.128/26`, 64 direcciones, broadcast `192.168.2.191`.
- Cursor posterior: `192.168.2.192`; quedan 64 direcciones de la red base sin asignar.
- `NAME` evita la advertencia informativa `ADV-007` por nombre ausente; no cambia los triplos ni el resultado de VLSM.

### Convenciones y alcance

- Representación académica única: `(n): (operador, argumento1, argumento2)`; referencias `(0)`, `(1)` y sucesivas.
- `ReferenciaTriplo` es una referencia tipada, no una sustitución de texto; `OrigenTriplo` conserva la trazabilidad de línea y solicitud.
- Operaciones matemáticas: `+`, `LOG2`, `CEIL`, `^`; operaciones de red: `INICIAR_RED`, `SOLICITUD`, `ASIGNAR_VLSM`, `SIGUIENTE_CURSOR`.
- La tercera columna contiene **comprobaciones**, no una pila de ejecución. El visor presenta notación matemática sin incluir LaTeX en los modelos.
- No se añadieron cuádruplos, Código P, NPI ni instrucciones artificiales `if`/`while`/`for` al DSL principal.
- La optimización de código y la generación de código objeto **no forman parte de v1.3.0**.

### Validación y publicación de v1.3.0

- [x] Probar la generación, interpretación y visualización de triplos desde la aplicación en Windows.
- [x] Confirmar 399 pruebas automatizadas y ausencia de regresiones después de modificar los metadatos finales.
- [x] Corregir traducciones del Centro de mantenimiento y verificar visualmente su presentación.
- [x] Preparar `Empaquetado/TecNetFinder.iss` y `Empaquetado/version_info.txt` para **v1.3.0**; el `.spec` ya funciona y no requiere modificaciones.
- [x] Reconstruir el EXE con PyInstaller después de cambiar los metadatos de versión y probar la aplicación empaquetada.
- [x] Compilar el instalador definitivo con Inno Setup 7, comprobar su instalación y apertura y validar la actualización de la instalación existente.
- [x] Verificar el SHA-256 del **instalador definitivo**: `ACC3BC65599A95DC0FFB2EAF107B07F15612A5C13EC152C3E77EA9B27CDE0424`.
- [x] Confirmar la suite después de modificar los metadatos estables y recompilar EXE e instalador; comprobar que el archivo publicado coincide con su hash.
- [x] Integrar la rama a `main` y publicar el tag y [release oficial v1.3.0](https://github.com/RobDev512/TecNet-Finder/releases/tag/v1.3.0) después de concluir las validaciones.
- [ ] Elaborar un **PDF breve para los compañeros de Lenguajes y Autómatas II** centrado en qué archivos se crearon y modificaron, qué código se implementó, cómo se conectó y cómo probarlo; omitir explicaciones introductorias de compiladores o triplos.
- [ ] Sincronizar el repositorio separado del Hub de proyectos, si se utiliza; la página `site/` de TecNet Finder se mantiene en este repositorio.

### Regla de trabajo para esta fase

Mantener las aportaciones del generador y del intérprete con comentarios en español junto a las instrucciones y saltos de línea solo cuando aclaren bloques lógicos. Para cambios amplios de interfaz y empaquetado, entregar archivos completos en ZIP con rutas relativas; validar la suite antes de guardar un commit.

---

## v1.3.1 — Language Lab

**Estado:** Pendiente

Complementar contenidos de notación infija, prefija y postfija sin alterar
artificialmente el DSL principal.

### Función estrella

Laboratorio independiente de expresiones.

### Objetivos

- Conversión infija/prefija/postfija.
- Árbol de expresión.
- Ejemplos automáticos.
- Generación de ejercicios.
- Copia rápida de resultados.

---

## v1.4.0 — Optimizer Update

**Estado:** Pendiente

Unidad 3: optimización local, global y de mirilla sobre la representación
intermedia.

### Función estrella

Comparador visual antes/después.

### Objetivos

- Códigos OPT.
- Conteo de instrucciones.
- Temporales eliminados.
- Porcentaje de reducción.
- Explicación de cada optimización aplicada.

---

## v1.4.1 — Performance Update

**Estado:** Pendiente

Consolidar la Unidad 3 y hacer observables sus costos.

### Función estrella

Perfilador del compilador por fases.

### Objetivos

- Tiempo de lexer.
- Tiempo de parser.
- Tiempo de semántico.
- Tiempo de IR.
- Tiempo de optimizador.
- Activar/desactivar optimizaciones individuales.
- Comparar compilación con y sin optimización.

---

## v2.0.0 — Compiler Update

**Estado:** Pendiente

Unidad 4: generación de código objeto o ensamblador a partir de la IR
optimizada.

### Función estrella

Mapa IR → ensamblador.

### Objetivos

- Resaltado cruzado IR / instrucciones.
- Mapa de registros.
- Administración de memoria.
- Exportación `.asm`.
- Compilación o simulación si el entorno definido por la maestra lo permite.

---

## v2.1.0 — Workspace Update

**Estado:** Pendiente

Evolución del producto posterior al compilador completo.

### Función estrella

Sistema de proyectos TecNet Finder.

### Objetivos

- Nuevo/Abrir proyecto.
- Recientes.
- Sesiones guardadas.
- Código, resultados y preferencias por proyecto.
- Historial básico de compilaciones.

---

## v2.2.0 — Learning Update

**Estado:** Pendiente

Modo educativo integral para visualizar todo el proceso de compilación.

### Función estrella

Modo aprendizaje paso a paso.

### Flujo

`Lexer → Parser → Semántico → IR → Optimización → Código objeto`

### Objetivos

- Explicación de entrada, transformación y salida en cada fase.
- Proyecto de demostración reproducible.

---

## v3.0.0 — Language Evolution

**Estado:** Visión

Evolución futura del DSL después de terminar la materia.

### Función estrella

Nueva sintaxis orientada a redes y subredes.

### Objetivos

- Bloques `NETWORK` / `SUBNET`.
- Nuevas construcciones semánticas.
- Gramática ampliada.
- AST renovado.
- Compatibilidad/migración con el DSL anterior.

---

## Regla de avance

**Unidad terminada → revisión de la maestra → release estable → siguiente unidad.**

## Prioridades

- Mantener v1.3.0 como versión estable publicada; las funciones de optimización y código objeto pertenecen a versiones posteriores.
- Mantener enlazada la descarga publicada en GitHub Releases y sus verificaciones.
- Desde v1.3.0, cada versión debe tener una función estrella visible.
- Mantener separadas las herramientas educativas del DSL principal.
- No definir todavía la arquitectura objetivo de v2.0.0.
- Mantener v3.0.0 como evolución posterior al semestre.
