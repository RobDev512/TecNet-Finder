# ROADMAP — TecNet Finder

## Estado actual

**Versión pública en GitHub:** v1.2.2
**Última versión cerrada y publicada:** v1.2.2 — Stability & Polish
**Estado general:** v1.2.2 cerrada, validada y publicada en GitHub Releases; v1.3.0 en desarrollo local.
**Etapa activa:** v1.3.0 — Intermediate Code Update (Unidad 2; representación mediante triplos)

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

**Estado:** En desarrollo local — Unidad 2 (no publicada).
**Rama de trabajo:** `feature/v1.3.0-triplos`. No desarrollar directamente en `main`.
**Base estable:** v1.2.2; último commit de la Etapa 1: `f25bcb2` (local).

Implementar **triplos** como única representación principal de código intermedio para el DSL de redes IPv4 y planificación VLSM. No añadir cuádruplos, Código P, NPI ni estructuras `if`/`while`/`for` artificiales al DSL principal.

### Función estrella

Visor educativo de transformación DSL → triplos, con referencias y comprobación de resultados paso a paso.

### Convenciones y diseño acordados

- Forma académica: `(n): (operador, argumento1, argumento2)`, con numeración consecutiva y referencias `(0)`, `(1)`, etc.
- Las referencias se representan internamente mediante `ReferenciaTriplo`, no como texto; los metadatos `OrigenTriplo` conservan línea, índice de bloque e índice de host original.
- Las solicitudes `HOSTS` se procesan de mayor a menor, sin perder su posición original; `NAME` debe preservarse al integrar la representación con las salidas.
- Operadores matemáticos actuales: `+`, `LOG2`, `CEIL`, `^` (la potencia se interpreta con `**` en Python). La secuencia documentada para el tamaño de bloque es `hosts + 2` → `LOG2` → `CEIL` → `2 ^ exponente`; comprobar equivalencia y precisión respecto a la calculadora actual.
- Operadores de red previstos: `INICIAR_RED`, `SOLICITUD`, `ASIGNAR_VLSM`, `SIGUIENTE_CURSOR`. Sus resultados deberán definirse e interpretarse explícitamente, sin efectos ocultos ni referencias ambiguas.
- El visor futuro usará un formato compacto de **tres columnas**: `(n) | (Op, Arg1, Arg2) | Pila o comprobación`; la tercera columna mostrará principalmente la comprobación de cada operación y los valores de las referencias. Mostrar una pila solo si existe una pila real en la implementación: los triplos por sí solos no la requieren.
- Presentar cálculos matemáticos con notación visual tipo LaTeX (por ejemplo, `log₂`, `⌈x⌉`, `2⁶`) al integrar PySide6; **no** almacenar LaTeX dentro de los modelos.
- Mantener la tabla de triplos y las comprobaciones como vistas de la misma información, sin confundir el árbol sintáctico con el código intermedio.

### Estado comprobado al 21 de noviembre de 2026

- [x] **Etapa 1 — Modelos y referencias:** `Motor/compilacion/triplos.py` con `ReferenciaTriplo`, `OrigenTriplo`, `Triplo`, `ResultadoIntermedio`; validaciones de índices, referencias anteriores, operadores, argumentos y metadatos.
- [x] **Etapa 1 — Pruebas:** `Pruebas/motor/prueba_modelos_triplos.py` con 15 pruebas nuevas; **333 pruebas totales aprobadas** en el equipo de desarrollo. Commit local `f25bcb2`; `main` intacta.
- [x] **Etapa 2 — Primer avance manual:** creado localmente `Compilador/generador_triplos.py`; genera `INICIAR_RED` por bloque y `+` por cada solicitud `HOSTS` en orden descendente. Comprobado manualmente con dos bloques, conservando línea, índice de bloque e índice original del host. Este archivo aún no se ha integrado al flujo principal ni queda incluido en el commit de la Etapa 1.

### Próximos pasos y pendientes

- [ ] **Etapa 2 — Continuar el generador manualmente:** por cada solicitud generar `LOG2`, `CEIL` y `^` mediante `ReferenciaTriplo` al resultado inmediatamente anterior.
- [ ] Generar `SOLICITUD`, `ASIGNAR_VLSM` y `SIGUIENTE_CURSOR` para cada host; encadenar el cursor entre solicitudes, y reiniciar el contexto al pasar a otro bloque.
- [ ] Precisar contratos semánticos de los operadores: entradas, salidas, tipos y dependencias correctas de las referencias; conservar los metadatos, la identidad de `NAME` y la posición original de cada host.
- [ ] Añadir pruebas automatizadas del generador con uno y varios bloques, solicitudes desordenadas y repetidas, y referencias/índices válidos.
- [ ] **Etapa 3 — Intérprete y comprobación:** evaluar cada triplo, registrar los valores resultantes por índice y construir la comprobación que aparecerá junto a cada operación; comparar direcciones, tamaños, máscaras, rangos y broadcast con `Redes/calculadora_vlsm.py`.
- [ ] Validar casos límite de precisión matemática, especialmente `LOG2` y tamaños potencia de dos, sin modificar todavía la calculadora VLSM estable.
- [ ] **Etapa 4 — Integración:** incorporar la generación y sus resultados a `FlujoCompilacion`/`ResultadoCompilacion` usando únicamente `resultado_semantico.bloques_validos`; mantener diagnósticos, advertencias, recuperación parcial y errores técnicos.
- [ ] **Etapa 5 — Interfaz:** reutilizar la pestaña reservada para «Código intermedio», implementar el visor compacto con comprobaciones, localización del origen, traducciones a los seis idiomas y representación matemática, respetando temas y tipografías.
- [ ] Copiar/exportar triplos y comprobaciones, si la integración mantiene la funcionalidad prevista.
- [ ] **Etapa 6 — Cierre:** ejecutar pruebas completas de regresión y las nuevas pruebas del generador/intérprete; actualizar documentación académica, README, roadmap y empaquetado solamente cuando corresponda. No anunciar ni publicar v1.3.0 antes de validarla.

### Regla de desarrollo

Implementar el **generador paso a paso y de forma manual** para comprenderlo. Para la futura integración de interfaz y cambios extensos, se podrán utilizar ZIP con archivos completos y rutas relativas. Cada paso debe probarse antes de declararlo terminado.

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

- Mantener la v1.2.2 cerrada; nuevas funciones pertenecen a versiones posteriores.
- Mantener enlazada la descarga publicada en GitHub Releases y sus verificaciones.
- Desde v1.3.0, cada versión debe tener una función estrella visible.
- Mantener separadas las herramientas educativas del DSL principal.
- No definir todavía la arquitectura objetivo de v2.0.0.
- Mantener v3.0.0 como evolución posterior al semestre.
