# TecNet Finder

TecNet Finder es un lenguaje específico de dominio orientado al análisis y planificación de redes mediante VLSM.

## Lenguaje fuente

TecNet Finder.

## Lenguaje de implementación

Python.

## Interfaz gráfica

PySide6.

## Descripción

El proyecto fue iniciado en la asignatura Lenguajes y Autómatas I, donde se desarrollaron las fases de análisis léxico y análisis sintáctico.

En Lenguajes y Autómatas II se retomará el proyecto para continuar con las fases restantes de un compilador, comenzando con el análisis semántico.

## Fases del compilador

- [x] Análisis léxico
- [x] Análisis sintáctico
- [ ] Análisis semántico
- [ ] Generación de código intermedio
- [ ] Optimización de código
- [ ] Generación de código objeto

## Funcionalidad

TecNet Finder permite procesar instrucciones relacionadas con direcciones IPv4, máscaras de red y requerimientos de hosts para realizar cálculos VLSM.

Ejemplo:

IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina