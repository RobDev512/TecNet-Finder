# ============================================================
# Archivo: pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo ejecuta automáticamente los ejemplos almacenados
# por TecNet Finder utilizando el mismo FlujoCompilacion que usa
# normalmente la aplicación.
#
# Recupera los códigos declarados como esperados dentro de los
# archivos de ejemplos, consulta cuáles están disponibles en el
# catálogo actual y compara esas expectativas con los
# diagnósticos realmente producidos.
#
# Actualmente comprueba análisis léxico, sintáctico, semántico,
# advertencias y cálculo VLSM sin depender de la interfaz gráfica.
# ============================================================

import re  # Permite extraer únicamente las declaraciones formales de códigos esperados escritas dentro de los ejemplos.
from dataclasses import dataclass, field  # Permite representar de forma organizada los resultados individuales y sus resúmenes.

from Motor.diagnosticos import codigo_diagnostico_disponible, codigo_diagnostico_es_error, obtener_codigos_diagnosticos_disponibles, obtener_codigos_diagnosticos_pendientes  # Proporciona el estado centralizado de todos los códigos registrados.
from Motor.flujo_compilacion import FlujoCompilacion  # Ejecuta cada ejemplo mediante exactamente el mismo flujo utilizado por TecNet Finder.
from Motor.gestor_ejemplos import EjemploCodigo  # Proporciona la estructura con la que se representan los casos cargados desde los archivos TXT.


ESTADO_CORRECTO = "correcto"  # Representa un ejemplo cuya parte actualmente evaluable se comportó como se esperaba.
ESTADO_PENDIENTE = "pendiente"  # Representa un ejemplo cuya invalidez depende completamente de una característica todavía futura.
ESTADO_FALLIDO = "fallido"  # Representa un ejemplo que contradijo alguna expectativa correspondiente con el comportamiento actual.


@dataclass  # Organiza todos los datos obtenidos al ejecutar un ejemplo individual.
class ResultadoPruebaEjemplo:  # Representa el resultado detallado de una sola prueba procedente de los archivos de ejemplos.
    ejemplo: EjemploCodigo  # Conserva el caso original utilizado como entrada de la prueba.
    estado: str  # Indica si el resultado terminó correcto, pendiente o fallido.
    codigos_esperados: list[str] = field(default_factory=list)  # Conserva exclusivamente los códigos declarados formalmente dentro del ejemplo.
    codigos_evaluables: list[str] = field(default_factory=list)  # Conserva expectativas que ya pertenecen al comportamiento implementado.
    codigos_pendientes: list[str] = field(default_factory=list)  # Conserva expectativas reservadas para características todavía no disponibles.
    codigos_obtenidos: list[str] = field(default_factory=list)  # Conserva todos los códigos distintos que realmente produjo el flujo.
    codigos_error: list[str] = field(default_factory=list)  # Conserva únicamente los diagnósticos obtenidos cuya severidad es error.
    codigos_advertencia: list[str] = field(default_factory=list)  # Conserva únicamente las recomendaciones no bloqueantes obtenidas.
    codigos_faltantes: list[str] = field(default_factory=list)  # Conserva expectativas actuales que deberían haber aparecido pero no se produjeron.
    motivos: list[str] = field(default_factory=list)  # Explica las contradicciones que provocaron que una prueba fuera considerada fallida.
    tokens_reconocidos: int = 0  # Conserva la cantidad de tokens válidos que produjo el lexer.
    bloques_validos: int = 0  # Conserva la cantidad de bloques que superaron las fases formales disponibles.
    subredes_generadas: int = 0  # Conserva la cantidad total de subredes VLSM obtenidas.
    error_interno: str | None = None  # Conserva una excepción inesperada sin interrumpir la ejecución de todos los ejemplos.

    @property  # Expone como atributo calculado si el caso depende también de trabajo futuro.
    def tiene_expectativas_pendientes(self) -> bool:  # Indica si existe al menos un código esperado que todavía no está disponible.
        return bool(self.codigos_pendientes)  # Devuelve verdadero cuando la colección de expectativas pendientes contiene elementos.


@dataclass  # Reúne los resultados individuales producidos durante una ejecución completa.
class ResumenPruebasEjemplos:  # Proporciona totales y clasificaciones generales de todos los ejemplos probados.
    resultados: list[ResultadoPruebaEjemplo] = field(default_factory=list)  # Conserva cada resultado en el mismo orden en que fueron recibidos los ejemplos.

    @property  # Permite consultar directamente la cantidad total sin almacenarla por separado.
    def total(self) -> int:  # Devuelve cuántos ejemplos fueron ejecutados.
        return len(self.resultados)  # Cuenta directamente todos los resultados almacenados.

    @property  # Calcula automáticamente la cantidad de pruebas aprobadas.
    def correctos(self) -> int:  # Devuelve cuántos casos cumplieron las expectativas actualmente comprobables.
        return sum(resultado.estado == ESTADO_CORRECTO for resultado in self.resultados)  # Cuenta solamente resultados clasificados como correctos.

    @property  # Calcula automáticamente la cantidad de casos completamente aplazados.
    def pendientes(self) -> int:  # Devuelve cuántos ejemplos dependen exclusivamente de características futuras.
        return sum(resultado.estado == ESTADO_PENDIENTE for resultado in self.resultados)  # Cuenta solamente resultados clasificados como pendientes.

    @property  # Calcula automáticamente la cantidad de casos con contradicciones reales.
    def fallidos(self) -> int:  # Devuelve cuántos ejemplos fallaron frente al comportamiento disponible.
        return sum(resultado.estado == ESTADO_FALLIDO for resultado in self.resultados)  # Cuenta solamente resultados clasificados como fallidos.

    @property  # Cuenta casos que pueden estar correctos actualmente pero todavía incluyen alguna expectativa futura.
    def con_expectativas_pendientes(self) -> int:  # Devuelve cuántos resultados mencionan al menos un diagnóstico todavía pendiente.
        return sum(resultado.tiene_expectativas_pendientes for resultado in self.resultados)  # Incluye tanto pendientes completos como casos parcialmente comprobables.


def _elementos_unicos(elementos: list[str]) -> list[str]:  # Elimina valores repetidos manteniendo intacto el orden de su primera aparición.
    resultado: list[str] = []  # Prepara la colección final que almacenará únicamente elementos distintos.

    for elemento in elementos:  # Recorre todos los valores exactamente en el orden recibido.
        if elemento not in resultado:  # Comprueba si esta aparición todavía no fue conservada.
            resultado.append(elemento)  # Agrega solamente la primera aparición de cada valor.

    return resultado  # Devuelve la colección sin duplicados y sin reorganizar sus elementos.


def extraer_codigos_esperados(texto_esperado: str) -> list[str]:  # Extrae códigos únicamente desde una declaración formal Código esperado o Códigos esperados.
    if not texto_esperado:  # Comprueba si el ejemplo carece completamente de descripción de salida.
        return []  # Evita realizar expresiones regulares innecesarias sobre contenido vacío.

    patron_declaracion = r"\bC[oó]digos?\s+esperados?\s*:\s*([^.\n]*)"  # Captura únicamente el contenido escrito después de la etiqueta formal hasta el siguiente punto o salto.
    declaraciones = re.findall(patron_declaracion, texto_esperado, flags=re.IGNORECASE)  # Recupera todas las declaraciones explícitas de expectativas existentes en el texto.

    if not declaraciones:  # Comprueba si ningún fragmento utiliza la forma oficial de declarar códigos esperados.
        return []  # Evita considerar códigos mencionados solamente dentro de explicaciones informales.

    patron_codigo = r"\b(?:LEX|SIN|SEM|ADV|GEN)-\d{3}\b"  # Reconoce exclusivamente las familias oficiales de diagnósticos de TecNet Finder.
    coincidencias: list[str] = []  # Reunirá los códigos encontrados dentro de cada declaración formal.

    for declaracion in declaraciones:  # Recorre exclusivamente los fragmentos que fueron identificados como expectativas.
        codigos_declaracion = re.findall(patron_codigo, declaracion, flags=re.IGNORECASE)  # Obtiene todos los identificadores oficiales presentes en la declaración actual.
        coincidencias.extend(codigo.upper() for codigo in codigos_declaracion)  # Normaliza los códigos para conservar siempre su representación oficial en mayúsculas.

    return _elementos_unicos(coincidencias)  # Elimina duplicados manteniendo solamente las expectativas formalmente declaradas.


class EjecutorPruebasEjemplos:  # Ejecuta casos cargados desde los archivos TXT mediante el flujo real del compilador.
    def ejecutar(self, ejemplos: list[EjemploCodigo]) -> ResumenPruebasEjemplos:  # Ejecuta todos los ejemplos recibidos y construye un resumen conjunto.
        resultados: list[ResultadoPruebaEjemplo] = []  # Prepara la colección donde se almacenará cada resultado individual.

        for ejemplo in ejemplos:  # Recorre los casos respetando exactamente el orden proporcionado por GestorEjemplos.
            resultados.append(self._ejecutar_ejemplo(ejemplo))  # Ejecuta el ejemplo y conserva toda la información producida durante su evaluación.

        return ResumenPruebasEjemplos(resultados=resultados)  # Agrupa todos los resultados para facilitar estadísticas y reportes posteriores.

    def _ejecutar_ejemplo(self, ejemplo: EjemploCodigo) -> ResultadoPruebaEjemplo:  # Ejecuta un caso y compara su comportamiento real con las expectativas declaradas.
        codigos_esperados = extraer_codigos_esperados(ejemplo.salida_esperada)  # Recupera solamente diagnósticos declarados explícitamente como expectativas.
        codigos_evaluables = [codigo for codigo in codigos_esperados if codigo_diagnostico_disponible(codigo)]  # Separa expectativas cuya implementación ya forma parte de la versión actual.
        codigos_pendientes = [codigo for codigo in codigos_esperados if not codigo_diagnostico_disponible(codigo)]  # Conserva por separado expectativas asociadas con características futuras.

        try:  # Protege el conjunto completo de pruebas ante una excepción inesperada producida por un único ejemplo.
            flujo = FlujoCompilacion()  # Crea un coordinador completamente nuevo para evitar compartir estados entre ejemplos.
            resultado_compilacion = flujo.analizar(ejemplo.comando)  # Ejecuta la entrada mediante las mismas fases que utiliza normalmente la aplicación.
        except Exception as error:  # Convierte cualquier excepción inesperada en un resultado fallido controlado.
            return ResultadoPruebaEjemplo(
                ejemplo=ejemplo,  # Conserva qué caso produjo la excepción.
                estado=ESTADO_FALLIDO,  # Clasifica inmediatamente la ejecución como fallida.
                codigos_esperados=codigos_esperados,  # Conserva las expectativas declaradas para facilitar el diagnóstico.
                codigos_evaluables=codigos_evaluables,  # Conserva cuáles de esas expectativas ya podían comprobarse.
                codigos_pendientes=codigos_pendientes,  # Conserva también cualquier expectativa futura.
                motivos=[f"Se produjo un error interno durante la prueba: {error}."],  # Explica explícitamente la excepción que impidió completar el caso.
                error_interno=str(error),  # Guarda el texto original del error para poder mostrarlo o depurarlo posteriormente.
            )  # Devuelve el fallo sin detener la ejecución de los demás ejemplos.

        diagnosticos = resultado_compilacion.diagnosticos  # Recupera en una sola colección errores y advertencias procedentes de todo el flujo.
        codigos_obtenidos = _elementos_unicos([diagnostico.codigo for diagnostico in diagnosticos])  # Conserva una sola aparición de cada código realmente producido.
        codigos_error = _elementos_unicos([diagnostico.codigo for diagnostico in diagnosticos if diagnostico.severidad == "error"])  # Separa exclusivamente diagnósticos bloqueantes.
        codigos_advertencia = _elementos_unicos([diagnostico.codigo for diagnostico in diagnosticos if diagnostico.severidad in ("warning", "advertencia")])  # Separa exclusivamente recomendaciones no bloqueantes.
        codigos_obtenidos_evaluables = [codigo for codigo in codigos_obtenidos if codigo_diagnostico_disponible(codigo)]  # Limita la comparación a códigos que pertenecen al comportamiento actual.
        codigos_error_evaluables = [codigo for codigo in codigos_error if codigo_diagnostico_disponible(codigo)]  # Conserva únicamente errores pertenecientes a características ya disponibles.
        codigos_faltantes = [codigo for codigo in codigos_evaluables if codigo not in codigos_obtenidos_evaluables]  # Detecta expectativas actuales que deberían haberse producido pero no aparecieron.
        motivos: list[str] = []  # Reunirá todas las contradicciones que provoquen que el caso sea considerado fallido.

        if ejemplo.tipo == "Válida":  # Aplica las reglas correspondientes con ejemplos declarados formalmente correctos.
            if codigos_error_evaluables:  # Comprueba que el caso no haya producido ningún error perteneciente a las fases disponibles.
                motivos.append("El caso está declarado como válido, pero produjo errores actuales: " + ", ".join(codigos_error_evaluables) + ".")  # Explica exactamente qué errores contradicen la declaración de validez.

            if not resultado_compilacion.bloques_validos:  # Comprueba que al menos una instrucción haya superado todas las fases formales disponibles.
                motivos.append("El caso está declarado como válido, pero no produjo bloques válidos después de las fases actuales.")  # Detecta entradas declaradas válidas que realmente fueron descartadas.

            if resultado_compilacion.bloques_validos and not resultado_compilacion.subredes_vlsm:  # Comprueba que un bloque formalmente válido también haya producido el resultado de red esperado.
                motivos.append("El caso produjo bloques válidos, pero no generó ninguna subred VLSM.")  # Señala una contradicción entre la aceptación formal y la salida concreta.

        elif ejemplo.tipo == "Inválida":  # Aplica las reglas correspondientes con ejemplos diseñados deliberadamente para producir errores.
            errores_esperados_evaluables = [codigo for codigo in codigos_evaluables if codigo_diagnostico_es_error(codigo)]  # Identifica cuáles expectativas actuales corresponden específicamente con errores bloqueantes.

            if errores_esperados_evaluables and not codigos_error_evaluables:  # Comprueba si se esperaba al menos un error actual pero el flujo no produjo ninguno.
                motivos.append("El caso debería producir un error en las fases actuales, pero no se obtuvo ninguno.")  # Registra la ausencia de comportamiento que ya debería ser comprobable.
            elif not codigos_evaluables and codigos_pendientes and codigos_error_evaluables:  # Detecta casos reservados para el futuro que inesperadamente ya fallan por alguna regla actual.
                motivos.append("El caso está reservado para una característica futura, pero produjo errores actuales inesperados: " + ", ".join(codigos_error_evaluables) + ".")  # Impide clasificar como pendiente una entrada que ya posee problemas actuales.
            elif not codigos_evaluables and not codigos_pendientes and not codigos_error_evaluables:  # Detecta un ejemplo declarado inválido que no define expectativas ni produce errores actuales.
                motivos.append("El caso está declarado como inválido, pero no produjo ningún error en las fases actuales.")  # Señala que la declaración del ejemplo no coincide con el flujo disponible.

        if codigos_faltantes:  # Comprueba finalmente que todos los códigos actualmente evaluables hayan sido producidos.
            motivos.append("No aparecieron los códigos evaluables esperados: " + ", ".join(codigos_faltantes) + ".")  # Enumera exactamente cuáles expectativas no se cumplieron.

        if motivos:  # Da prioridad absoluta a cualquier contradicción encontrada durante la evaluación.
            estado = ESTADO_FALLIDO  # Clasifica el ejemplo como fallido cuando existe al menos un motivo concreto.
        elif ejemplo.tipo == "Inválida" and not codigos_evaluables and codigos_pendientes:  # Comprueba si la invalidez depende exclusivamente de códigos todavía futuros.
            estado = ESTADO_PENDIENTE  # Mantiene aplazado el caso hasta que su característica correspondiente se implemente.
        else:  # Atiende cualquier caso cuya parte actualmente comprobable se comportó de acuerdo con lo esperado.
            estado = ESTADO_CORRECTO  # Clasifica como correcto tanto un válido real como un inválido que produjo sus errores esperados.

        return ResultadoPruebaEjemplo(
            ejemplo=ejemplo,  # Conserva la definición original del caso evaluado.
            estado=estado,  # Guarda la clasificación final obtenida después de todas las comprobaciones.
            codigos_esperados=codigos_esperados,  # Conserva todos los códigos declarados formalmente.
            codigos_evaluables=codigos_evaluables,  # Conserva las expectativas que pertenecen al comportamiento actual.
            codigos_pendientes=codigos_pendientes,  # Conserva las expectativas todavía futuras.
            codigos_obtenidos=codigos_obtenidos,  # Conserva todos los códigos diferentes producidos realmente.
            codigos_error=codigos_error,  # Conserva los errores obtenidos por separado.
            codigos_advertencia=codigos_advertencia,  # Conserva las advertencias obtenidas por separado.
            codigos_faltantes=codigos_faltantes,  # Conserva expectativas actuales que estuvieron ausentes.
            motivos=motivos,  # Conserva todas las explicaciones relacionadas con posibles fallos.
            tokens_reconocidos=len(resultado_compilacion.resultado_lexico.tokens),  # Registra cuántos tokens válidos produjo el lexer.
            bloques_validos=len(resultado_compilacion.bloques_validos),  # Registra cuántos bloques superaron las fases formales.
            subredes_generadas=len(resultado_compilacion.subredes_vlsm),  # Registra cuántas subredes concretas produjo finalmente el flujo.
        )  # Entrega toda la información necesaria para reportes y pruebas automáticas.


def _texto_codigos(codigos: list[str], texto_vacio: str = "ninguno") -> str:  # Convierte una colección de códigos en una representación compacta adecuada para el reporte.
    return ", ".join(codigos) if codigos else texto_vacio  # Une los códigos encontrados o utiliza el texto alternativo cuando la colección está vacía.


def _nombre_estado(estado: str) -> str:  # Convierte la clasificación interna de una prueba en una etiqueta visible y destacable.
    if estado == ESTADO_CORRECTO:  # Comprueba si todas las expectativas actuales fueron satisfechas.
        return "CORRECTO"  # Utiliza la etiqueta correspondiente con una prueba aprobada.

    if estado == ESTADO_PENDIENTE:  # Comprueba si el caso depende únicamente de alguna característica futura.
        return "PENDIENTE"  # Utiliza una etiqueta distinta para evitar confundirlo con un fallo.

    return "FALLIDO"  # Considera la clasificación restante como una contradicción frente al comportamiento actual.


def generar_reporte_pruebas(resumen: ResumenPruebasEjemplos) -> str:  # Convierte los resultados estructurados en un reporte textual completo y legible.
    lineas: list[str] = []  # Prepara la colección que contendrá cada línea del reporte final.
    codigos_disponibles = obtener_codigos_diagnosticos_disponibles()  # Consulta dinámicamente todos los códigos que pueden evaluarse en la versión actual.
    codigos_pendientes = obtener_codigos_diagnosticos_pendientes()  # Consulta cualquier código reservado para etapas posteriores.

    lineas.append("=== PRUEBAS AUTOMÁTICAS DE EJEMPLOS ===")  # Agrega un encabezado principal fácilmente identificable.
    lineas.append("")  # Separa visualmente el encabezado del alcance de las pruebas.
    lineas.append("Alcance actual: análisis léxico, análisis sintáctico, análisis semántico, advertencias y cálculo VLSM.")  # Describe exactamente qué partes del proyecto están siendo evaluadas.
    lineas.append("Diagnósticos evaluables según catálogo: " + ", ".join(codigos_disponibles) + ".")  # Enumera dinámicamente todos los códigos considerados actuales.
    lineas.append("Diagnósticos pendientes según catálogo: " + ", ".join(codigos_pendientes) + ".")  # Muestra cualquier regla registrada pero todavía aplazada.
    lineas.append("")  # Separa la información del catálogo del resumen numérico.
    lineas.append(f"Total de casos probados: {resumen.total}")  # Informa la cantidad completa de ejemplos ejecutados.
    lineas.append(f"Casos correctos actualmente: {resumen.correctos}")  # Indica cuántas pruebas satisfecieron el comportamiento esperado.
    lineas.append(f"Casos pendientes de fase futura: {resumen.pendientes}")  # Indica cuántos casos dependen completamente de características futuras.
    lineas.append(f"Casos fallidos: {resumen.fallidos}")  # Indica cuántos ejemplos presentan contradicciones reales.
    lineas.append(f"Casos con alguna expectativa pendiente: {resumen.con_expectativas_pendientes}")  # Cuenta también casos actuales correctos que incluyen alguna expectativa futura.
    lineas.append("")  # Separa el resumen numérico del resultado general.

    if resumen.fallidos:  # Comprueba primero si existe al menos una contradicción real en las características disponibles.
        lineas.append("Resultado general: EXISTEN PRUEBAS FALLIDAS EN LAS CARACTERÍSTICAS ACTUALES.")  # Informa claramente que alguna parte del comportamiento actual no coincide con lo esperado.
    elif resumen.pendientes:  # Se ejecuta solamente cuando no existen fallos pero sí casos completamente aplazados.
        lineas.append("Resultado general: LAS PRUEBAS ACTUALES PASARON; EXISTEN CASOS PENDIENTES.")  # Diferencia explícitamente un pendiente académico de un problema del programa.
    else:  # Atiende el caso donde no existen ni fallos ni ejemplos completamente pendientes.
        lineas.append("Resultado general: TODAS LAS PRUEBAS EVALUABLES PASARON.")  # Confirma que todas las expectativas actuales fueron satisfechas.

    lineas.append("")  # Separa el resultado general del detalle individual.
    lineas.append("-" * 72)  # Agrega una división visual antes del listado de ejemplos.
    lineas.append("")  # Mantiene una separación después de la línea divisoria.

    for indice, resultado in enumerate(resumen.resultados, start=1):  # Recorre todos los resultados asignando una numeración visible desde uno.
        ejemplo = resultado.ejemplo  # Recupera la información original utilizada para identificar el caso actual.
        lineas.append(f"{indice}. [{_nombre_estado(resultado.estado)}] {ejemplo.titulo}")  # Muestra número, clasificación y título del ejemplo.
        lineas.append(f"   Tipo declarado: {ejemplo.tipo}")  # Informa si el caso fue definido originalmente como válido o inválido.
        lineas.append(f"   Códigos esperados: {_texto_codigos(resultado.codigos_esperados, 'no especificados')}")  # Muestra las expectativas declaradas dentro del archivo.
        lineas.append(f"   Códigos evaluables ahora: {_texto_codigos(resultado.codigos_evaluables)}")  # Distingue qué expectativas ya pueden comprobarse.
        lineas.append(f"   Expectativas pendientes: {_texto_codigos(resultado.codigos_pendientes)}")  # Muestra las reglas cuya implementación todavía no existe.
        lineas.append(f"   Códigos obtenidos: {_texto_codigos(resultado.codigos_obtenidos)}")  # Enumera todos los diagnósticos producidos durante la ejecución real.
        lineas.append(f"   Errores obtenidos: {_texto_codigos(resultado.codigos_error)}")  # Muestra exclusivamente diagnósticos bloqueantes.
        lineas.append(f"   Advertencias obtenidas: {_texto_codigos(resultado.codigos_advertencia)}")  # Muestra exclusivamente recomendaciones no bloqueantes.
        lineas.append(f"   Tokens reconocidos: {resultado.tokens_reconocidos}")  # Informa cuántos tokens válidos produjo el análisis léxico.
        lineas.append(f"   Bloques semánticamente válidos: {resultado.bloques_validos}")  # Informa cuántas instrucciones superaron las fases formales actuales.
        lineas.append(f"   Subredes VLSM generadas: {resultado.subredes_generadas}")  # Informa cuántos resultados concretos alcanzaron el cálculo VLSM.

        if resultado.motivos:  # Comprueba si la evaluación encontró alguna contradicción que necesite explicación.
            lineas.append("   Motivo(s):")  # Introduce el apartado donde se detallarán las causas del fallo.

            for motivo in resultado.motivos:  # Recorre individualmente cada contradicción registrada.
                lineas.append(f"   - {motivo}")  # Agrega cada explicación como una entrada independiente.

        elif resultado.estado == ESTADO_PENDIENTE:  # Comprueba si el caso completo está esperando alguna característica futura.
            lineas.append("   Motivo: la condición que vuelve inválido este caso pertenece a una característica todavía no implementada.")  # Explica por qué un pendiente no representa un fallo actual.

        elif resultado.codigos_pendientes:  # Detecta casos aprobados actualmente que además esperan alguna regla futura.
            lineas.append("   Nota: la parte disponible pasó correctamente; las expectativas pendientes se comprobarán más adelante.")  # Aclara que la porción ya implementada sí obtuvo el comportamiento esperado.

        lineas.append("")  # Separa visualmente el resultado actual del siguiente ejemplo.

    return "\n".join(lineas).rstrip() + "\n"  # Construye el reporte completo garantizando únicamente un salto final convencional.