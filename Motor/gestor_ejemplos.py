# ============================================================
# Archivo: gestor_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo se encarga de localizar, leer e interpretar los
# archivos de ejemplos utilizados por TecNet Finder.
#
# Mantiene la lectura de ejemplos separada de la interfaz para
# que los casos puedan reutilizarse posteriormente en pruebas
# automáticas sin depender de PySide6.
# ============================================================

import re  # Importa expresiones regulares para reconocer las líneas que contienen instrucciones TecNet Finder.
from dataclasses import dataclass  # Importa dataclass para representar cada ejemplo mediante una estructura sencilla.
from pathlib import Path  # Importa Path para localizar los archivos de ejemplos desde la raíz del proyecto.


@dataclass(frozen=True)
class EjemploCodigo:  # Representa un caso individual cargado desde los archivos de ejemplos.
    tipo: str  # Indica si el caso pertenece al grupo de entradas válidas o inválidas.
    titulo: str  # Conserva el nombre descriptivo utilizado dentro del archivo.
    comando: str  # Guarda una o varias instrucciones pertenecientes al mismo caso.
    salida_esperada: str  # Conserva el texto descriptivo asociado con el resultado esperado.


def acortar_texto(texto: str, limite: int = 95) -> str:  # Construye una versión compacta adecuada para mostrar dentro de una tabla.
    texto_limpio = str(texto).replace("\n", " | ").strip()  # Sustituye saltos de línea para mostrar varias instrucciones en una sola celda.

    if len(texto_limpio) <= limite:  # Comprueba si el contenido ya cabe completamente dentro del límite solicitado.
        return texto_limpio  # Devuelve el texto original sin modificaciones innecesarias.

    return texto_limpio[: limite - 3] + "..."  # Recorta únicamente la vista previa y conserva intacto el contenido real.


class GestorEjemplos:  # Coordina la carga de los archivos disponibles dentro de la carpeta Ejemplos.
    def __init__(self, raiz_proyecto: Path | None = None):  # Permite utilizar la raíz real del proyecto o una ubicación alternativa durante pruebas.
        self.raiz_proyecto = raiz_proyecto or Path(__file__).resolve().parent.parent  # Obtiene TecNet-Finder cuando no se proporciona otra ubicación.
        self.carpeta_ejemplos = self.raiz_proyecto / "Ejemplos"  # Localiza la carpeta donde se conservan los casos heredados.
        self.ruta_validos = self.carpeta_ejemplos / "entrada_valida.txt"  # Conserva la ubicación oficial de las entradas válidas.
        self.ruta_invalidos = self.carpeta_ejemplos / "entradas_invalidas.txt"  # Conserva la ubicación oficial de las entradas inválidas.

    def cargar_ejemplos(self) -> tuple[list[EjemploCodigo], list[EjemploCodigo]]:  # Lee y transforma las dos categorías utilizadas por el selector.
        texto_validos = self._leer_archivo(self.ruta_validos)  # Recupera el contenido completo del archivo de entradas válidas.
        texto_invalidos = self._leer_archivo(self.ruta_invalidos)  # Recupera el contenido completo del archivo de entradas inválidas.

        ejemplos_validos = self.analizar_texto(texto_validos, "Válida")  # Convierte el primer archivo en casos estructurados.
        ejemplos_invalidos = self.analizar_texto(texto_invalidos, "Inválida")  # Convierte el segundo archivo en casos estructurados.

        return ejemplos_validos, ejemplos_invalidos  # Devuelve ambas colecciones manteniendo sus categorías separadas.

    def _leer_archivo(self, ruta: Path) -> str:  # Recupera un archivo de ejemplos sin producir errores cuando el recurso no existe.
        if not ruta.exists():  # Comprueba que el archivo realmente se encuentre disponible.
            return ""  # Permite que la interfaz informe posteriormente que no existen casos.

        return ruta.read_text(encoding="utf-8")  # Lee el contenido conservando correctamente los caracteres del español.

    def analizar_texto(self, texto: str, tipo: str) -> list[EjemploCodigo]:  # Extrae casos individuales siguiendo la estructura utilizada por los archivos originales.
        ejemplos: list[EjemploCodigo] = []  # Conserva los registros creados en el mismo orden del archivo.
        titulo_actual = ""  # Guarda temporalmente el título relacionado con las siguientes instrucciones.
        comandos_actuales: list[str] = []  # Acumula una o varias instrucciones pertenecientes al mismo caso.
        salida_actual = ""  # Conserva temporalmente la salida esperada asociada con el caso.

        def finalizar_actual() -> None:  # Convierte el contenido temporal en un ejemplo antes de comenzar el siguiente caso.
            nonlocal titulo_actual, comandos_actuales, salida_actual  # Permite actualizar las variables utilizadas por el analizador exterior.

            if comandos_actuales:  # Comprueba que realmente exista alguna instrucción que deba conservarse.
                titulo = titulo_actual or f"{tipo} #{len(ejemplos) + 1}"  # Genera un nombre sencillo solamente cuando el archivo no proporcionó título.
                comando = "\n".join(comando.strip() for comando in comandos_actuales if comando.strip())  # Une las instrucciones pertenecientes al mismo caso.

                ejemplos.append(  # Agrega el registro completamente estructurado a la colección final.
                    EjemploCodigo(
                        tipo=tipo,
                        titulo=titulo,
                        comando=comando,
                        salida_esperada=salida_actual.strip(),
                    )
                )

            titulo_actual = ""  # Limpia el título temporal para el siguiente caso.
            comandos_actuales = []  # Vacía las instrucciones ya almacenadas.
            salida_actual = ""  # Descarta la salida esperada del ejemplo finalizado.

        for linea in texto.splitlines():  # Recorre el archivo conservando el orden original de todas sus líneas.
            contenido = linea.strip()  # Elimina únicamente espacios exteriores para facilitar la clasificación.

            if not contenido:  # Comprueba si la línea no contiene información útil.
                continue  # Ignora separaciones visuales existentes dentro del archivo.

            contenido_minusculas = contenido.lower()  # Crea una variante normalizada utilizada únicamente para comparaciones.

            if contenido.startswith("#"):  # Detecta los títulos escritos como comentarios.
                finalizar_actual()  # Conserva cualquier caso anterior antes de comenzar el nuevo.
                titulo_actual = contenido.lstrip("#").strip()  # Elimina solamente el marcador de comentario.
                continue  # Evita interpretar también el título como una instrucción.

            if contenido_minusculas.startswith("caso"):  # Permite también títulos que no utilicen el símbolo de comentario.
                finalizar_actual()  # Finaliza el registro anterior antes de cambiar de caso.
                titulo_actual = contenido  # Conserva el texto completo como título.
                continue  # Continúa directamente con la siguiente línea.

            if contenido_minusculas.startswith(("salida esperada", "resultado esperado")):  # Detecta la descripción asociada con el resultado esperado.
                salida_actual = contenido  # Conserva íntegramente la salida escrita en el archivo.
                finalizar_actual()  # Cierra el caso porque la salida esperada marca su final.
                continue  # Continúa buscando el siguiente ejemplo.

            if contenido_minusculas.startswith(("entrada válida", "entrada valida", "entrada inválida", "entrada invalida")):  # Detecta encabezados generales compatibles con archivos anteriores.
                if not titulo_actual:  # Comprueba que no exista ya un título específico para el caso.
                    titulo_actual = contenido  # Utiliza provisionalmente el encabezado como nombre.

                continue  # Evita interpretar el encabezado como código.

            if re.match(r"^IP(?=\s|\d|$)", contenido):  # Comprueba que la línea comience como una instrucción real del DSL.
                if "<" in contenido or ">" in contenido:  # Detecta ejemplos genéricos que contienen marcadores y no código ejecutable.
                    continue  # Omite las plantillas utilizadas solamente como explicación.

                if not titulo_actual and comandos_actuales:  # Detecta archivos antiguos donde cada línea sin título representa un caso independiente.
                    finalizar_actual()  # Conserva la instrucción anterior antes de comenzar otra.

                comandos_actuales.append(contenido)  # Agrega la instrucción al caso actualmente activo.

        finalizar_actual()  # Conserva cualquier ejemplo pendiente después de recorrer la última línea.

        return ejemplos  # Devuelve todos los registros encontrados en el archivo.