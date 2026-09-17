# ============================================================
# Archivo: explicador_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo utiliza la IA local únicamente para mejorar la
# presentación de soluciones pertenecientes a diagnósticos que
# TecNet Finder ya detectó mediante sus analizadores formales.
#
# La IA no crea diagnósticos, no modifica su severidad y no decide
# si una instrucción es válida. Las respuestas se validan antes de
# mostrarse y se conserva una caché para evitar consultas repetidas.
# ============================================================

import json  # Permite proporcionar al modelo los diagnósticos mediante una estructura inequívoca.

from AsistenteIA.configuracion import TIEMPO_ESPERA_DIAGNOSTICOS_SEGUNDOS  # Utiliza un tiempo independiente del autocompletado para respuestas más extensas.
from AsistenteIA.motor_local import MotorLocalOllama  # Reutiliza la misma instancia privada y el mismo modelo ya instalados.
from Motor.compilacion.diagnosticos import Diagnostico  # Utiliza directamente los diagnósticos oficiales producidos por TecNet Finder.


class ExplicadorDiagnosticos:  # Convierte soluciones oficiales en explicaciones más claras sin alterar el diagnóstico original.
    TAMANO_LOTE = 6  # Evita solicitar demasiadas explicaciones simultáneas al modelo pequeño utilizado localmente.
    LIMITE_CACHE = 256  # Impide que una sesión extensa conserve indefinidamente explicaciones antiguas.

    def __init__(self, motor: MotorLocalOllama | None = None):
        self.motor = motor or MotorLocalOllama()  # Utiliza el motor real salvo cuando una prueba proporciona una implementación simulada.
        self.cache: dict[tuple[str, str, str, str], str] = {}  # Conserva únicamente respuestas asociadas exactamente con el mismo diagnóstico.

    def mejorar_soluciones(self, diagnosticos: list[Diagnostico]) -> dict[tuple[str, str, str, str], str]:
        resultados: dict[tuple[str, str, str, str], str] = {}  # Reúne soluciones disponibles para la compilación solicitada.
        faltantes: list[Diagnostico] = []  # Conserva solamente diagnósticos que todavía necesitan consultar al modelo.
        claves_faltantes: set[tuple[str, str, str, str]] = set()  # Evita pedir dos veces la misma explicación dentro de un único análisis.

        for diagnostico in diagnosticos:
            clave = self.clave_diagnostico(diagnostico)  # Construye una identidad estable basada exclusivamente en el contenido oficial.
            solucion_cache = self.cache.get(clave)  # Consulta primero la respuesta local ya obtenida.

            if solucion_cache is not None:
                resultados[clave] = solucion_cache  # Reutiliza inmediatamente una explicación idéntica ya validada.
                continue

            if clave not in claves_faltantes:
                faltantes.append(diagnostico)  # Programa únicamente la primera aparición de cada diagnóstico equivalente.
                claves_faltantes.add(clave)  # Registra que la misma identidad ya pertenece a la consulta pendiente.

        for inicio in range(0, len(faltantes), self.TAMANO_LOTE):
            lote = faltantes[inicio:inicio + self.TAMANO_LOTE]  # Limita cada solicitud a un grupo pequeño apropiado para el modelo local.
            soluciones_lote = self._consultar_lote(lote)  # Realiza una sola generación estructurada para todos los elementos del lote.

            for indice, solucion in soluciones_lote.items():
                diagnostico = lote[indice]  # Relaciona la posición validada de la respuesta con el diagnóstico oficial correspondiente.
                clave = self.clave_diagnostico(diagnostico)  # Recupera la misma identidad utilizada por la caché.
                self._guardar_cache(clave, solucion)  # Conserva únicamente respuestas que ya superaron las validaciones.
                resultados[clave] = solucion  # Hace disponible la versión mejorada para la interfaz actual.

        return resultados  # Omite silenciosamente los diagnósticos cuya explicación no pudo generarse para que la interfaz conserve su solución oficial.

    @staticmethod
    def clave_diagnostico(diagnostico: Diagnostico) -> tuple[str, str, str, str]:
        return (
            diagnostico.codigo,
            diagnostico.mensaje,
            diagnostico.fragmento,
            diagnostico.solucion,
        )  # La ubicación no cambia el significado cuando código, mensaje, fragmento y solución oficial son idénticos.

    def limpiar_cache(self) -> None:
        self.cache.clear()  # Permite liberar manualmente todas las explicaciones temporales de la sesión.

    def _consultar_lote(self, diagnosticos: list[Diagnostico]) -> dict[int, str]:
        if not diagnosticos:
            return {}  # Evita realizar una solicitud cuando no existe ningún diagnóstico pendiente.

        prompt = self._construir_prompt(diagnosticos)  # Proporciona contexto, límites y estructura de salida antes de invocar al modelo.
        maximo_tokens = min(1200, 180 + len(diagnosticos) * 180)  # Reserva capacidad proporcional sin permitir respuestas innecesariamente extensas.

        respuesta = self.motor.generar_json(
            prompt,
            maximo_tokens=maximo_tokens,
            tiempo_espera_segundos=TIEMPO_ESPERA_DIAGNOSTICOS_SEGUNDOS,
        )  # Utiliza el mismo Qwen local con un tiempo mayor que el requerido por el ghost text.

        if not isinstance(respuesta, dict):
            return {}  # Mantiene las soluciones oficiales cuando Ollama no produjo una estructura utilizable.

        soluciones = respuesta.get("soluciones")  # Recupera exclusivamente la colección acordada con el modelo.

        if not isinstance(soluciones, list):
            return {}  # Rechaza respuestas cuyo formato no corresponda con el contrato esperado.

        resultados: dict[int, str] = {}  # Conserva únicamente elementos individuales completamente válidos.

        for elemento in soluciones:
            if not isinstance(elemento, dict):
                continue  # Ignora contenido adicional que no represente una solución estructurada.

            indice = elemento.get("indice")  # Obtiene la relación explícita con el diagnóstico enviado.

            if type(indice) is not int or not 0 <= indice < len(diagnosticos):
                continue  # Rechaza índices booleanos, negativos o fuera del lote actual.

            if indice in resultados:
                continue  # Conserva solamente la primera respuesta válida para evitar ambigüedades.

            explicacion = self._normalizar_texto(elemento.get("explicacion"), 520)  # Limita la explicación a una extensión apropiada para la tabla.
            correccion = self._normalizar_texto(elemento.get("correccion"), 520)  # Limita también la propuesta de corrección.
            ejemplo = self._normalizar_texto(elemento.get("ejemplo"), 300)  # Permite un ejemplo breve cuando realmente aporta claridad.

            if not explicacion:
                continue  # Exige que la IA aporte al menos una explicación útil del problema detectado.

            if not correccion:
                correccion = diagnosticos[indice].solucion.strip()  # Recupera la solución oficial cuando el modelo omitió una corrección utilizable.

            if not correccion:
                continue  # Evita sustituir una celda por una explicación que no indique cómo resolver el problema.

            texto = f"Explicación: {explicacion}\n\nCorrección: {correccion}"  # Presenta una estructura uniforme sin depender del estilo elegido por el modelo.

            if ejemplo:
                texto += f"\n\nEjemplo: {ejemplo}"  # Añade el ejemplo solamente cuando fue proporcionado como texto válido.

            resultados[indice] = texto  # Registra la solución final sin modificar el objeto Diagnostico original.

        return resultados  # Devuelve únicamente posiciones que pueden reemplazarse visualmente con seguridad.

    def _construir_prompt(self, diagnosticos: list[Diagnostico]) -> str:
        elementos = []  # Prepara una versión mínima de cada diagnóstico sin exponer información ajena a la tarea.

        for indice, diagnostico in enumerate(diagnosticos):
            elementos.append(
                {
                    "indice": indice,
                    "codigo": diagnostico.codigo,
                    "categoria": diagnostico.categoria,
                    "mensaje": diagnostico.mensaje,
                    "fragmento": diagnostico.fragmento,
                    "solucion_oficial": diagnostico.solucion,
                }
            )  # Entrega al modelo la misma información que TecNet Finder ya determinó oficialmente.

        datos = json.dumps(elementos, ensure_ascii=False, indent=2)  # Conserva acentos y separa claramente cada diagnóstico dentro del prompt.

        return (
            "Eres el asistente local de TecNet Finder.\n"
            "Tu única tarea es explicar con claridad diagnósticos que el compilador YA detectó.\n"
            "No determines si el código es válido o inválido, no cambies el código del diagnóstico, "
            "no contradigas la solución oficial y no inventes reglas nuevas.\n\n"
            "El lenguaje de TecNet Finder utiliza esta estructura:\n"
            "IP <IP_ADDRESS> MASK <SUBNET_MASK> HOSTS <NUMBER>[,<NUMBER>...] [NAME <IDENTIFIER>]\n\n"
            "Para cada elemento recibido devuelve una explicación breve en español, una corrección clara "
            "coherente con la solución oficial y, solo cuando sea útil, un ejemplo corto.\n"
            "No uses Markdown, listas con viñetas ni texto fuera del JSON.\n\n"
            "Responde exactamente con este esquema:\n"
            '{"soluciones":[{"indice":0,"explicacion":"...","correccion":"...","ejemplo":"..."}]}\n\n'
            f"Diagnósticos:\n{datos}"
        )  # Define límites estrictos para que la IA actúe únicamente como capa explicativa.

    def _normalizar_texto(self, valor, limite: int) -> str:
        if not isinstance(valor, str):
            return ""  # Rechaza valores numéricos, listas u otras estructuras inesperadas.

        texto = " ".join(valor.replace("\r", " ").replace("\n", " ").split())  # Convierte la respuesta a texto compacto apropiado para una celda.

        if not texto:
            return ""  # Descarta campos vacíos después de normalizar espacios.

        return texto[:limite].rstrip()  # Impide que una generación excesiva expanda desproporcionadamente la tabla.

    def _guardar_cache(self, clave: tuple[str, str, str, str], solucion: str) -> None:
        if clave in self.cache:
            self.cache.pop(clave)  # Actualiza también el orden de una entrada que pudiera haber sido regenerada.

        self.cache[clave] = solucion  # Conserva la explicación validada más reciente para esa identidad exacta.

        while len(self.cache) > self.LIMITE_CACHE:
            clave_antigua = next(iter(self.cache))  # Localiza la entrada con mayor antigüedad aprovechando el orden estable de dict.
            self.cache.pop(clave_antigua)  # Libera gradualmente memoria sin descartar toda la caché.
