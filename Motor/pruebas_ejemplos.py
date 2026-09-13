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
#
# Actualmente las pruebas consideran análisis léxico,
# sintáctico, semántico, advertencias y cálculo VLSM.
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
    bloques_validos: int = 0  # Guarda cuántos bloques superaron todas las fases formales actualmente disponibles.
    subredes_generadas: int = 0  # Guarda cuántas subredes VLSM produjo la entrada.
    error_interno: str | None = None  # Conserva una excepción inesperada sin cerrar el conjunto completo de pruebas.

    @property
    def tiene_expectativas_pendientes(self) -> bool:  # Indica si el ejemplo menciona al menos una característica futura.
        return bool(self.codigos_pendientes)  # Devuelve verdadero cuando existe al menos un código todavía pendiente.


@dataclass
class ResumenPruebasEjemplos:  # Agrupa todos los resultados obtenidos durante una ejecución automática.
    resultados: list[ResultadoPruebaEjemplo] = field(default_factory=list)  # Conserva cada caso individual en el mismo orden en que fue probado.

    @property
    def total(self) -> int:  # Devuelve la cantidad completa de ejemplos ejecutados.
        return len(self.resultados)  # Cuenta directamente todos los resultados almacenados.

    @property
    def correctos(self) -> int:  # Cuenta las pruebas cuya parte actual se comportó correctamente.
        return sum(
            resultado.estado == ESTADO_CORRECTO
            for resultado in self.resultados
        )  # Cuenta únicamente resultados clasificados como correctos.

    @property
    def pendientes(self) -> int:  # Cuenta los ejemplos completamente aplazados hasta una fase futura.
        return sum(
            resultado.estado == ESTADO_PENDIENTE
            for resultado in self.resultados
        )  # Cuenta únicamente resultados pendientes.

    @property
    def fallidos(self) -> int:  # Cuenta los casos que presentaron una diferencia real respecto al comportamiento esperado actual.
        return sum(
            resultado.estado == ESTADO_FALLIDO
            for resultado in self.resultados
        )  # Cuenta únicamente resultados fallidos.

    @property
    def con_expectativas_pendientes(self) -> int:  # Cuenta todos los casos que contienen al menos una expectativa futura.
        return sum(
            resultado.tiene_expectativas_pendientes
            for resultado in self.resultados
        )  # Incluye casos correctos que además esperan alguna característica posterior.


def _elementos_unicos(elementos: list[str]) -> list[str]:  # Elimina valores repetidos sin modificar el orden original.
    resultado: list[str] = []  # Conserva los elementos que ya fueron agregados a la colección final.

    for elemento in elementos:  # Recorre todos los valores respetando el orden recibido.
        if elemento not in resultado:  # Comprueba que el valor todavía no haya sido conservado.
            resultado.append(elemento)  # Agrega únicamente la primera aparición de cada elemento.

    return resultado  # Devuelve la colección sin duplicados y con su orden original.


def extraer_codigos_esperados(texto_esperado: str) -> list[str]:  # Extrae los códigos escritos dentro de la descripción de salida esperada.
    if not texto_esperado:  # Comprueba si el ejemplo no posee una descripción de salida.
        return []  # Evita realizar búsquedas sobre contenido vacío.

    patron = r"\b(?:LEX|SIN|SEM|ADV|GEN)-\d{3}\b"  # Reconoce las familias utilizadas por TecNet Finder.
    coincidencias = re.findall(patron, texto_esperado)  # Localiza todos los códigos mencionados en el texto.

    return _elementos_unicos(coincidencias)  # Elimina códigos repetidos sin perder el orden de aparición.


class EjecutorPruebasEjemplos:  # Ejecuta los ejemplos mediante el flujo real sin depender de componentes gráficos.
    def ejecutar(self, ejemplos: list[EjemploCodigo]) -> ResumenPruebasEjemplos:  # Ejecuta todos los casos recibidos y construye un resumen conjunto.
        resultados: list[ResultadoPruebaEjemplo] = []  # Prepara la colección donde se conservará cada resultado individual.

        for ejemplo in ejemplos:  # Recorre los ejemplos en el mismo orden utilizado por el selector.
            resultados.append(self._ejecutar_ejemplo(ejemplo))  # Ejecuta el caso y conserva su resultado estructurado.

        return ResumenPruebasEjemplos(resultados=resultados)  # Devuelve un resumen con todos los casos procesados.

    def _ejecutar_ejemplo(self, ejemplo: EjemploCodigo) -> ResultadoPruebaEjemplo:  # Ejecuta y evalúa un único ejemplo utilizando el estado actual del catálogo.
        codigos_esperados = extraer_codigos_esperados(ejemplo.salida_esperada)  # Recupera los diagnósticos declarados dentro de la salida esperada.
        codigos_evaluables = [
            codigo
            for codigo in codigos_esperados
            if codigo_diagnostico_disponible(codigo)
        ]  # Conserva únicamente expectativas cuya implementación ya está disponible.
        codigos_pendientes = [
            codigo
            for codigo in codigos_esperados
            if not codigo_diagnostico_disponible(codigo)
        ]  # Separa las expectativas reservadas para reglas todavía no implementadas.

        try:
            flujo = FlujoCompilacion()  # Crea el coordinador real utilizado normalmente por TecNet Finder.
            resultado_compilacion = flujo.analizar(ejemplo.comando)  # Ejecuta el código del ejemplo por todas las fases actualmente conectadas.
        except Exception as error:
            return ResultadoPruebaEjemplo(
                ejemplo=ejemplo,
                estado=ESTADO_FALLIDO,
                codigos_esperados=codigos_esperados,
                codigos_evaluables=codigos_evaluables,
                codigos_pendientes=codigos_pendientes,
                motivos=[f"Se produjo un error interno durante la prueba: {error}."],
                error_interno=str(error),
            )  # Convierte una excepción inesperada en un resultado fallido sin detener las demás pruebas.

        diagnosticos = resultado_compilacion.diagnosticos  # Recupera conjuntamente los diagnósticos generados por las fases disponibles.
        codigos_obtenidos = _elementos_unicos(
            [diagnostico.codigo for diagnostico in diagnosticos]
        )  # Conserva una única aparición de cada código realmente producido.
        codigos_error = _elementos_unicos(
            [
                diagnostico.codigo
                for diagnostico in diagnosticos
                if diagnostico.severidad == "error"
            ]
        )  # Separa únicamente los diagnósticos bloqueantes obtenidos.
        codigos_advertencia = _elementos_unicos(
            [
                diagnostico.codigo
                for diagnostico in diagnosticos
                if diagnostico.severidad in ("warning", "advertencia")
            ]
        )  # Separa los diagnósticos no bloqueantes producidos por el flujo.
        codigos_obtenidos_evaluables = [
            codigo
            for codigo in codigos_obtenidos
            if codigo_diagnostico_disponible(codigo)
        ]  # Ignora cualquier código que todavía no deba formar parte de la evaluación actual.
        codigos_error_evaluables = [
            codigo
            for codigo in codigos_error
            if codigo_diagnostico_disponible(codigo)
        ]  # Conserva exclusivamente errores pertenecientes a características disponibles.
        codigos_faltantes = [
            codigo
            for codigo in codigos_evaluables
            if codigo not in codigos_obtenidos_evaluables
        ]  # Detecta expectativas actuales que no fueron producidas por el flujo.

        motivos: list[str] = []  # Reúne las razones concretas que convertirían el ejemplo en una prueba fallida.

        if ejemplo.tipo == "Válida":  # Aplica las comprobaciones correspondientes con ejemplos declarados correctos.
            if codigos_error_evaluables:  # Comprueba que una entrada válida no haya producido errores actuales.
                motivos.append(
                    "El caso está declarado como válido, pero produjo errores actuales: "
                    + ", ".join(codigos_error_evaluables)
                    + "."
                )  # Explica exactamente cuáles errores contradicen la declaración del ejemplo.

            if not resultado_compilacion.bloques_validos:  # Comprueba que al menos un bloque haya superado las fases formales disponibles.
                motivos.append(
                    "El caso está declarado como válido, pero no produjo "
                    "bloques válidos después de las fases actuales."
                )  # Informa que la instrucción fue descartada antes de alcanzar normalmente VLSM.

            if (
                resultado_compilacion.bloques_validos
                and not resultado_compilacion.subredes_vlsm
            ):
                motivos.append(
                    "El caso produjo bloques válidos, pero no generó ninguna subred VLSM."
                )  # Detecta una entrada formalmente aceptada que no logró producir resultados de red.

        elif ejemplo.tipo == "Inválida":  # Aplica las comprobaciones correspondientes con casos que deben generar algún error.
            errores_esperados_evaluables = [
                codigo
                for codigo in codigos_evaluables
                if codigo_diagnostico_es_error(codigo)
            ]  # Identifica cuáles expectativas actuales corresponden específicamente con errores.

            if errores_esperados_evaluables and not codigos_error_evaluables:  # Comprueba si debía existir un error actual pero no apareció ninguno.
                motivos.append(
                    "El caso debería producir un error en las fases actuales, "
                    "pero no se obtuvo ninguno."
                )  # Registra la ausencia de un error que ya debería ser comprobable.

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
                )  # Evita considerar pendiente una entrada que ya falla por otra regla disponible.

            elif (
                not codigos_evaluables
                and not codigos_pendientes
                and not codigos_error_evaluables
            ):
                motivos.append(
                    "El caso está declarado como inválido, pero no produjo "
                    "ningún error en las fases actuales."
                )  # Señala casos inválidos que no especifican una expectativa futura ni generan errores actuales.

        if codigos_faltantes:  # Comprueba finalmente que todos los códigos disponibles esperados hayan aparecido.
            motivos.append(
                "No aparecieron los códigos evaluables esperados: "
                + ", ".join(codigos_faltantes)
                + "."
            )  # Describe exactamente cuáles diagnósticos esperados estuvieron ausentes.

        if motivos:  # Da prioridad a cualquier contradicción encontrada durante la evaluación.
            estado = ESTADO_FALLIDO  # Clasifica el ejemplo como fallido cuando existe al menos un motivo.
        elif (
            ejemplo.tipo == "Inválida"
            and not codigos_evaluables
            and codigos_pendientes
        ):
            estado = ESTADO_PENDIENTE  # Mantiene pendiente un caso cuya invalidez depende exclusivamente de reglas futuras.
        else:
            estado = ESTADO_CORRECTO  # Considera correcto cualquier caso cuya parte actualmente comprobable se comportó como se esperaba.

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
        )  # Conserva toda la información necesaria para el reporte y para las pruebas automatizadas.


def _texto_codigos(
    codigos: list[str],  # Recibe la colección de códigos que debe mostrarse.
    texto_vacio: str = "ninguno",  # Define el texto utilizado cuando no existe ningún elemento.
) -> str:
    return ", ".join(codigos) if codigos else texto_vacio  # Produce una representación compacta para las líneas del reporte.


def _nombre_estado(estado: str) -> str:  # Convierte el estado interno en una etiqueta visible dentro del reporte.
    if estado == ESTADO_CORRECTO:  # Comprueba si la ejecución satisfizo todas las expectativas actuales.
        return "CORRECTO"  # Devuelve la etiqueta correspondiente con una prueba aprobada.

    if estado == ESTADO_PENDIENTE:  # Comprueba si el ejemplo depende solamente de una regla todavía futura.
        return "PENDIENTE"  # Devuelve la etiqueta utilizada para casos aplazados.

    return "FALLIDO"  # Utiliza la etiqueta restante para cualquier prueba con contradicciones actuales.


def generar_reporte_pruebas(
    resumen: ResumenPruebasEjemplos,  # Recibe los resultados que deben convertirse en un reporte legible.
) -> str:
    lineas: list[str] = []  # Prepara las líneas que compondrán el texto final.
    codigos_disponibles = obtener_codigos_diagnosticos_disponibles()  # Consulta dinámicamente todos los diagnósticos implementados.
    codigos_pendientes = obtener_codigos_diagnosticos_pendientes()  # Consulta dinámicamente las reglas todavía reservadas.

    lineas.append("=== PRUEBAS AUTOMÁTICAS DE EJEMPLOS ===")  # Agrega el encabezado principal del reporte.
    lineas.append("")  # Separa visualmente el encabezado del alcance actual.
    lineas.append(
        "Alcance actual: análisis léxico, análisis sintáctico, análisis semántico, "
        "advertencias y cálculo VLSM."
    )  # Refleja que U1 ya incorporó formalmente la fase semántica al flujo.
    lineas.append(
        "Diagnósticos evaluables según catálogo: "
        + ", ".join(codigos_disponibles)
        + "."
    )  # Enumera únicamente los códigos disponibles en el estado actual del proyecto.
    lineas.append(
        "Diagnósticos pendientes según catálogo: "
        + ", ".join(codigos_pendientes)
        + "."
    )  # Mantiene visibles las reglas previstas que todavía no se han implementado.
    lineas.append("")  # Separa el catálogo del resumen numérico.
    lineas.append(f"Total de casos probados: {resumen.total}")  # Informa la cantidad total de ejemplos ejecutados.
    lineas.append(f"Casos correctos actualmente: {resumen.correctos}")  # Informa cuántos casos superaron las expectativas actuales.
    lineas.append(f"Casos pendientes de fase futura: {resumen.pendientes}")  # Informa cuántos casos dependen completamente de trabajo posterior.
    lineas.append(f"Casos fallidos: {resumen.fallidos}")  # Informa cuántos ejemplos contradijeron el comportamiento esperado.
    lineas.append(
        f"Casos con alguna expectativa pendiente: "
        f"{resumen.con_expectativas_pendientes}"
    )  # Incluye también ejemplos correctos que esperan advertencias u otras reglas futuras.
    lineas.append("")  # Separa el resumen numérico del resultado general.

    if resumen.fallidos:  # Prioriza cualquier diferencia real detectada en las características disponibles.
        lineas.append(
            "Resultado general: EXISTEN PRUEBAS FALLIDAS "
            "EN LAS CARACTERÍSTICAS ACTUALES."
        )  # Informa claramente que existe al menos un comportamiento incorrecto.
    elif resumen.pendientes:  # Comprueba si no hubo fallos pero todavía existen casos totalmente aplazados.
        lineas.append(
            "Resultado general: LAS PRUEBAS ACTUALES PASARON; "
            "EXISTEN CASOS PENDIENTES."
        )  # Diferencia un pendiente académico de un fallo real.
    else:
        lineas.append(
            "Resultado general: TODAS LAS PRUEBAS EVALUABLES PASARON."
        )  # Confirma que todas las expectativas actualmente comprobables tuvieron éxito.

    lineas.append("")  # Separa el resultado general del detalle de cada ejemplo.
    lineas.append("-" * 72)  # Agrega una división visual antes del listado individual.
    lineas.append("")  # Conserva espacio después de la división.

    for indice, resultado in enumerate(
        resumen.resultados,
        start=1,
    ):  # Recorre todos los casos conservando un número visible desde uno.
        ejemplo = resultado.ejemplo  # Recupera los datos originales utilizados para identificar el caso.

        lineas.append(
            f"{indice}. [{_nombre_estado(resultado.estado)}] "
            f"{ejemplo.titulo}"
        )  # Muestra número, estado y título del ejemplo.
        lineas.append(f"   Tipo declarado: {ejemplo.tipo}")  # Informa si el ejemplo fue definido como válido o inválido.
        lineas.append(
            f"   Códigos esperados: "
            f"{_texto_codigos(resultado.codigos_esperados, 'no especificados')}"
        )  # Muestra todos los códigos mencionados originalmente en la expectativa.
        lineas.append(
            f"   Códigos evaluables ahora: "
            f"{_texto_codigos(resultado.codigos_evaluables)}"
        )  # Distingue los diagnósticos que ya pueden comprobarse.
        lineas.append(
            f"   Expectativas pendientes: "
            f"{_texto_codigos(resultado.codigos_pendientes)}"
        )  # Muestra únicamente los códigos todavía reservados para etapas futuras.
        lineas.append(
            f"   Códigos obtenidos: "
            f"{_texto_codigos(resultado.codigos_obtenidos)}"
        )  # Enumera los diagnósticos realmente producidos durante la ejecución.
        lineas.append(
            f"   Errores obtenidos: "
            f"{_texto_codigos(resultado.codigos_error)}"
        )  # Muestra exclusivamente los diagnósticos bloqueantes.
        lineas.append(
            f"   Advertencias obtenidas: "
            f"{_texto_codigos(resultado.codigos_advertencia)}"
        )  # Muestra separadamente las recomendaciones no bloqueantes.
        lineas.append(
            f"   Tokens reconocidos: {resultado.tokens_reconocidos}"
        )  # Informa cuántos tokens válidos produjo la primera fase.
        lineas.append(
            f"   Bloques semánticamente válidos: {resultado.bloques_validos}"
        )  # Informa cuántos bloques superaron todas las fases formales disponibles hasta U1.
        lineas.append(
            f"   Subredes VLSM generadas: {resultado.subredes_generadas}"
        )  # Informa cuántos resultados concretos alcanzaron el cálculo VLSM.

        if resultado.motivos:  # Comprueba si el ejemplo fue marcado con alguna contradicción concreta.
            lineas.append("   Motivo(s):")  # Introduce las explicaciones asociadas con el fallo.

            for motivo in resultado.motivos:  # Recorre individualmente las causas detectadas.
                lineas.append(f"   - {motivo}")  # Agrega cada motivo como una entrada independiente.

        elif resultado.estado == ESTADO_PENDIENTE:  # Explica los casos totalmente aplazados cuando no existe un fallo actual.
            lineas.append(
                "   Motivo: la condición que vuelve inválido este caso "
                "pertenece a una característica todavía no implementada."
            )  # Aclara por qué el resultado pendiente no debe interpretarse como error del programa.

        elif resultado.codigos_pendientes:  # Detecta casos correctos que además contienen alguna expectativa futura.
            lineas.append(
                "   Nota: la parte disponible pasó correctamente; "
                "las expectativas pendientes se comprobarán más adelante."
            )  # Explica que el caso actual pasó aunque todavía queden reglas por incorporar.

        lineas.append("")  # Separa visualmente un ejemplo del siguiente.

    return "\n".join(lineas).rstrip() + "\n"  # Construye el reporte final con una sola línea de cierre.