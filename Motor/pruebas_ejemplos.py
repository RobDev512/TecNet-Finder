# ============================================================
# Archivo: pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo ejecuta automáticamente los ejemplos almacenados
# por TecNet Finder utilizando únicamente las características
# que están disponibles actualmente en el proyecto.
#
# El estado de cada diagnóstico se consulta directamente desde
# el catálogo central para evitar listas duplicadas.
# ============================================================

import re  # Importa expresiones regulares para extraer códigos de diagnóstico desde las salidas esperadas.
from dataclasses import dataclass, field  # Importa herramientas para representar resultados y resúmenes estructurados.

from Motor.diagnosticos import codigo_diagnostico_disponible, codigo_diagnostico_es_error, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes  # Importa el estado centralizado de los diagnósticos.
from Motor.flujo_compilacion import FlujoCompilacion  # Importa el coordinador real utilizado por TecNet Finder para analizar cada ejemplo.
from Motor.gestor_ejemplos import EjemploCodigo  # Importa la estructura utilizada para representar cada caso de prueba.


ESTADO_CORRECTO = "correcto"  # Representa un ejemplo cuya parte actualmente evaluable se comportó como se esperaba.
ESTADO_PENDIENTE = "pendiente"  # Representa un ejemplo cuya invalidez depende completamente de una característica todavía no implementada.
ESTADO_FALLIDO = "fallido"  # Representa un ejemplo que no produjo el comportamiento esperado en las características disponibles.


@dataclass
class ResultadoPruebaEjemplo:  # Guarda toda la información obtenida al ejecutar un ejemplo individual.
    ejemplo: EjemploCodigo  # Conserva el ejemplo original que produjo este resultado.
    estado: str  # Indica si la prueba terminó correctamente, quedó pendiente o falló.
    codigos_esperados: list[str] = field(default_factory=list)  # Guarda todos los códigos mencionados en la salida esperada.
    codigos_evaluables: list[str] = field(default_factory=list)  # Guarda únicamente códigos disponibles actualmente.
    codigos_pendientes: list[str] = field(default_factory=list)  # Guarda expectativas pertenecientes a características todavía no implementadas.
    codigos_obtenidos: list[str] = field(default_factory=list)  # Guarda todos los códigos realmente producidos por el flujo actual.
    codigos_error: list[str] = field(default_factory=list)  # Guarda únicamente los diagnósticos obtenidos con severidad de error.
    codigos_advertencia: list[str] = field(default_factory=list)  # Guarda únicamente los diagnósticos obtenidos como advertencia.
    codigos_faltantes: list[str] = field(default_factory=list)  # Guarda expectativas evaluables que no aparecieron durante la ejecución.
    motivos: list[str] = field(default_factory=list)  # Explica por qué una prueba fue considerada fallida.
    tokens_reconocidos: int = 0  # Guarda cuántos tokens produjo el análisis léxico.
    bloques_validos: int = 0  # Guarda cuántos bloques logró aceptar el analizador sintáctico.
    subredes_generadas: int = 0  # Guarda cuántas subredes VLSM produjo la entrada.
    error_interno: str | None = None  # Conserva una excepción inesperada sin cerrar el conjunto completo de pruebas.

    @property
    def tiene_expectativas_pendientes(self) -> bool:  # Indica si el ejemplo menciona al menos una característica futura.
        return bool(self.codigos_pendientes)


@dataclass
class ResumenPruebasEjemplos:  # Agrupa todos los resultados obtenidos durante una ejecución automática.
    resultados: list[ResultadoPruebaEjemplo] = field(default_factory=list)  # Conserva cada caso individual en el mismo orden en que fue probado.

    @property
    def total(self) -> int:  # Devuelve la cantidad completa de ejemplos ejecutados.
        return len(self.resultados)

    @property
    def correctos(self) -> int:  # Cuenta las pruebas cuya parte actual se comportó correctamente.
        return sum(
            resultado.estado == ESTADO_CORRECTO
            for resultado in self.resultados
        )

    @property
    def pendientes(self) -> int:  # Cuenta los ejemplos completamente aplazados hasta una fase futura.
        return sum(
            resultado.estado == ESTADO_PENDIENTE
            for resultado in self.resultados
        )

    @property
    def fallidos(self) -> int:  # Cuenta los casos que presentaron una diferencia real respecto al comportamiento esperado actual.
        return sum(
            resultado.estado == ESTADO_FALLIDO
            for resultado in self.resultados
        )

    @property
    def con_expectativas_pendientes(self) -> int:  # Cuenta todos los casos que contienen al menos una expectativa futura.
        return sum(
            resultado.tiene_expectativas_pendientes
            for resultado in self.resultados
        )


def _elementos_unicos(elementos: list[str]) -> list[str]:  # Elimina valores repetidos sin modificar el orden original.
    resultado: list[str] = []  # Conserva los elementos que ya fueron agregados a la colección final.

    for elemento in elementos:  # Recorre todos los valores respetando el orden recibido.
        if elemento not in resultado:
            resultado.append(elemento)

    return resultado


def extraer_codigos_esperados(texto_esperado: str) -> list[str]:  # Extrae los códigos escritos dentro de la descripción de salida esperada.
    if not texto_esperado:
        return []

    patron = r"\b(?:LEX|SIN|SEM|ADV|GEN)-\d{3}\b"  # Reconoce las familias utilizadas por TecNet Finder.
    coincidencias = re.findall(patron, texto_esperado)

    return _elementos_unicos(coincidencias)


class EjecutorPruebasEjemplos:  # Ejecuta los ejemplos mediante el flujo real sin depender de componentes gráficos.
    def ejecutar(self, ejemplos: list[EjemploCodigo]) -> ResumenPruebasEjemplos:
        resultados: list[ResultadoPruebaEjemplo] = []

        for ejemplo in ejemplos:
            resultados.append(self._ejecutar_ejemplo(ejemplo))

        return ResumenPruebasEjemplos(resultados=resultados)

    def _ejecutar_ejemplo(self, ejemplo: EjemploCodigo) -> ResultadoPruebaEjemplo:
        codigos_esperados = extraer_codigos_esperados(ejemplo.salida_esperada)
        codigos_evaluables = [
            codigo
            for codigo in codigos_esperados
            if codigo_diagnostico_disponible(codigo)
        ]
        codigos_pendientes = [
            codigo
            for codigo in codigos_esperados
            if not codigo_diagnostico_disponible(codigo)
        ]

        try:
            flujo = FlujoCompilacion()
            resultado_compilacion = flujo.analizar(ejemplo.comando)
        except Exception as error:
            return ResultadoPruebaEjemplo(
                ejemplo=ejemplo,
                estado=ESTADO_FALLIDO,
                codigos_esperados=codigos_esperados,
                codigos_evaluables=codigos_evaluables,
                codigos_pendientes=codigos_pendientes,
                motivos=[f"Se produjo un error interno durante la prueba: {error}."],
                error_interno=str(error),
            )

        diagnosticos = resultado_compilacion.diagnosticos
        codigos_obtenidos = _elementos_unicos(
            [diagnostico.codigo for diagnostico in diagnosticos]
        )
        codigos_error = _elementos_unicos(
            [
                diagnostico.codigo
                for diagnostico in diagnosticos
                if diagnostico.severidad == "error"
            ]
        )
        codigos_advertencia = _elementos_unicos(
            [
                diagnostico.codigo
                for diagnostico in diagnosticos
                if diagnostico.severidad in ("warning", "advertencia")
            ]
        )
        codigos_obtenidos_evaluables = [
            codigo
            for codigo in codigos_obtenidos
            if codigo_diagnostico_disponible(codigo)
        ]
        codigos_error_evaluables = [
            codigo
            for codigo in codigos_error
            if codigo_diagnostico_disponible(codigo)
        ]
        codigos_faltantes = [
            codigo
            for codigo in codigos_evaluables
            if codigo not in codigos_obtenidos_evaluables
        ]

        motivos: list[str] = []

        if ejemplo.tipo == "Válida":
            if codigos_error_evaluables:
                motivos.append(
                    "El caso está declarado como válido, pero produjo errores actuales: "
                    + ", ".join(codigos_error_evaluables)
                    + "."
                )

            if not resultado_compilacion.bloques_validos:
                motivos.append(
                    "El caso está declarado como válido, pero no produjo "
                    "bloques sintácticamente válidos."
                )

            if (
                resultado_compilacion.bloques_validos
                and not resultado_compilacion.subredes_vlsm
            ):
                motivos.append(
                    "El caso produjo bloques válidos, pero no generó ninguna subred VLSM."
                )

        elif ejemplo.tipo == "Inválida":
            errores_esperados_evaluables = [
                codigo
                for codigo in codigos_evaluables
                if codigo_diagnostico_es_error(codigo)
            ]

            if errores_esperados_evaluables and not codigos_error_evaluables:
                motivos.append(
                    "El caso debería producir un error en las fases actuales, "
                    "pero no se obtuvo ninguno."
                )

            elif (
                not codigos_evaluables
                and codigos_pendientes
                and codigos_error_evaluables
            ):
                motivos.append(
                    "El caso está reservado para una característica futura, pero produjo "
                    "errores actuales inesperados: "
                    + ", ".join(codigos_error_evaluables)
                    + "."
                )

            elif (
                not codigos_evaluables
                and not codigos_pendientes
                and not codigos_error_evaluables
            ):
                motivos.append(
                    "El caso está declarado como inválido, pero no produjo "
                    "ningún error en las fases actuales."
                )

        if codigos_faltantes:
            motivos.append(
                "No aparecieron los códigos evaluables esperados: "
                + ", ".join(codigos_faltantes)
                + "."
            )

        if motivos:
            estado = ESTADO_FALLIDO
        elif (
            ejemplo.tipo == "Inválida"
            and not codigos_evaluables
            and codigos_pendientes
        ):
            estado = ESTADO_PENDIENTE
        else:
            estado = ESTADO_CORRECTO

        return ResultadoPruebaEjemplo(
            ejemplo=ejemplo,
            estado=estado,
            codigos_esperados=codigos_esperados,
            codigos_evaluables=codigos_evaluables,
            codigos_pendientes=codigos_pendientes,
            codigos_obtenidos=codigos_obtenidos,
            codigos_error=codigos_error,
            codigos_advertencia=codigos_advertencia,
            codigos_faltantes=codigos_faltantes,
            motivos=motivos,
            tokens_reconocidos=len(resultado_compilacion.resultado_lexico.tokens),
            bloques_validos=len(resultado_compilacion.bloques_validos),
            subredes_generadas=len(resultado_compilacion.subredes_vlsm),
        )


def _texto_codigos(
    codigos: list[str],
    texto_vacio: str = "ninguno",
) -> str:
    return ", ".join(codigos) if codigos else texto_vacio


def _nombre_estado(estado: str) -> str:
    if estado == ESTADO_CORRECTO:
        return "CORRECTO"

    if estado == ESTADO_PENDIENTE:
        return "PENDIENTE"

    return "FALLIDO"


def generar_reporte_pruebas(
    resumen: ResumenPruebasEjemplos,
) -> str:
    lineas: list[str] = []
    codigos_disponibles = obtener_codigos_diagnosticos_disponibles()
    codigos_pendientes = obtener_codigos_diagnosticos_pendientes()

    lineas.append("=== PRUEBAS AUTOMÁTICAS DE EJEMPLOS ===")
    lineas.append("")
    lineas.append(
        "Alcance actual: análisis léxico, análisis sintáctico, "
        "advertencias recuperadas y cálculo VLSM."
    )
    lineas.append(
        "Diagnósticos evaluables según catálogo: "
        + ", ".join(codigos_disponibles)
        + "."
    )
    lineas.append(
        "Diagnósticos pendientes según catálogo: "
        + ", ".join(codigos_pendientes)
        + "."
    )
    lineas.append("")
    lineas.append(f"Total de casos probados: {resumen.total}")
    lineas.append(f"Casos correctos actualmente: {resumen.correctos}")
    lineas.append(f"Casos pendientes de fase futura: {resumen.pendientes}")
    lineas.append(f"Casos fallidos: {resumen.fallidos}")
    lineas.append(
        f"Casos con alguna expectativa pendiente: "
        f"{resumen.con_expectativas_pendientes}"
    )
    lineas.append("")

    if resumen.fallidos:
        lineas.append(
            "Resultado general: EXISTEN PRUEBAS FALLIDAS "
            "EN LAS CARACTERÍSTICAS ACTUALES."
        )
    elif resumen.pendientes:
        lineas.append(
            "Resultado general: LAS PRUEBAS ACTUALES PASARON; "
            "EXISTEN CASOS PENDIENTES."
        )
    else:
        lineas.append(
            "Resultado general: TODAS LAS PRUEBAS EVALUABLES PASARON."
        )

    lineas.append("")
    lineas.append("-" * 72)
    lineas.append("")

    for indice, resultado in enumerate(
        resumen.resultados,
        start=1,
    ):
        ejemplo = resultado.ejemplo

        lineas.append(
            f"{indice}. [{_nombre_estado(resultado.estado)}] "
            f"{ejemplo.titulo}"
        )
        lineas.append(f"   Tipo declarado: {ejemplo.tipo}")
        lineas.append(
            f"   Códigos esperados: "
            f"{_texto_codigos(resultado.codigos_esperados, 'no especificados')}"
        )
        lineas.append(
            f"   Códigos evaluables ahora: "
            f"{_texto_codigos(resultado.codigos_evaluables)}"
        )
        lineas.append(
            f"   Expectativas pendientes: "
            f"{_texto_codigos(resultado.codigos_pendientes)}"
        )
        lineas.append(
            f"   Códigos obtenidos: "
            f"{_texto_codigos(resultado.codigos_obtenidos)}"
        )
        lineas.append(
            f"   Errores obtenidos: "
            f"{_texto_codigos(resultado.codigos_error)}"
        )
        lineas.append(
            f"   Advertencias obtenidas: "
            f"{_texto_codigos(resultado.codigos_advertencia)}"
        )
        lineas.append(
            f"   Tokens reconocidos: {resultado.tokens_reconocidos}"
        )
        lineas.append(
            f"   Bloques sintácticamente válidos: {resultado.bloques_validos}"
        )
        lineas.append(
            f"   Subredes VLSM generadas: {resultado.subredes_generadas}"
        )

        if resultado.motivos:
            lineas.append("   Motivo(s):")

            for motivo in resultado.motivos:
                lineas.append(f"   - {motivo}")

        elif resultado.estado == ESTADO_PENDIENTE:
            lineas.append(
                "   Motivo: la condición que vuelve inválido este caso "
                "pertenece a una característica todavía no implementada."
            )

        elif resultado.codigos_pendientes:
            lineas.append(
                "   Nota: la parte disponible pasó correctamente; "
                "las expectativas pendientes se comprobarán más adelante."
            )

        lineas.append("")

    return "\n".join(lineas).rstrip() + "\n"