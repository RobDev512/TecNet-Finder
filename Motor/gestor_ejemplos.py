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
#
# También conserva instrucciones deliberadamente incorrectas
# que comienzan con otras palabras reservadas para permitir
# probar errores de orden y recuperación sintáctica.
# ============================================================

import re  # Permite reconocer líneas que representan código del lenguaje incluso cuando están deliberadamente mal ordenadas.
from dataclasses import dataclass  # Permite representar cada ejemplo mediante una estructura sencilla e inmutable.
from pathlib import Path  # Permite localizar los archivos de ejemplos desde la raíz real del proyecto.


@dataclass(frozen=True)
class EjemploCodigo:  # Representa un caso individual cargado desde los archivos de ejemplos.
    tipo: str  # Indica si el caso pertenece al grupo de entradas válidas o inválidas.
    titulo: str  # Conserva el nombre descriptivo utilizado dentro del archivo.
    comando: str  # Guarda una o varias instrucciones pertenecientes al mismo caso.
    salida_esperada: str  # Conserva el texto descriptivo asociado con el resultado esperado.


def acortar_texto(texto: str, limite: int = 95) -> str:  # Construye una versión compacta adecuada para mostrar dentro de una tabla.
    texto_limpio = str(texto).replace("\n", " | ").strip()  # Sustituye saltos de línea solamente en la representación visual.

    if len(texto_limpio) <= limite:
        return texto_limpio  # Devuelve íntegro el contenido cuando ya cabe en el espacio disponible.

    return texto_limpio[: limite - 3] + "..."  # Recorta únicamente la vista previa sin alterar el código verdadero.


class GestorEjemplos:  # Coordina la carga de los archivos disponibles dentro de la carpeta Ejemplos.
    def __init__(self, raiz_proyecto: Path | None = None):
        self.raiz_proyecto = raiz_proyecto or Path(__file__).resolve().parent.parent  # Utiliza TecNet-Finder como raíz cuando no se proporciona una alternativa.
        self.carpeta_ejemplos = self.raiz_proyecto / "Ejemplos"  # Localiza la carpeta que contiene los casos reutilizables.
        self.ruta_validos = self.carpeta_ejemplos / "entrada_valida.txt"  # Conserva la ruta oficial de los ejemplos válidos.
        self.ruta_invalidos = self.carpeta_ejemplos / "entradas_invalidas.txt"  # Conserva la ruta oficial de los ejemplos inválidos.

    def cargar_ejemplos(self) -> tuple[list[EjemploCodigo], list[EjemploCodigo]]:
        texto_validos = self._leer_archivo(self.ruta_validos)  # Recupera el contenido completo de los ejemplos válidos.
        texto_invalidos = self._leer_archivo(self.ruta_invalidos)  # Recupera el contenido completo de los ejemplos inválidos.
        ejemplos_validos = self.analizar_texto(texto_validos, "Válida")  # Convierte cada caso válido en una estructura reutilizable.
        ejemplos_invalidos = self.analizar_texto(texto_invalidos, "Inválida")  # Convierte cada caso inválido en una estructura reutilizable.

        return ejemplos_validos, ejemplos_invalidos  # Devuelve ambas colecciones manteniendo su separación original.

    def _leer_archivo(self, ruta: Path) -> str:
        if not ruta.exists():
            return ""  # Permite que el programa siga funcionando aunque algún archivo de ejemplos no esté disponible.

        return ruta.read_text(encoding="utf-8")  # Lee los ejemplos conservando correctamente los caracteres utilizados en español.

    def _es_linea_codigo(self, contenido: str) -> bool:
        patron_inicio = r"^(?:IP(?=\s|\d|$)|MASK(?=\s|/|$)|HOSTS(?=\s|\d|,|$)|NAME(?=\s|$))"  # Reconoce posibles inicios del lenguaje aunque el orden sea intencionalmente incorrecto.

        return re.match(patron_inicio, contenido) is not None  # Permite conservar casos como MASK... para comprobar SIN-008 en vez de descartarlos antes del compilador.

    def analizar_texto(self, texto: str, tipo: str) -> list[EjemploCodigo]:
        ejemplos: list[EjemploCodigo] = []  # Conserva todos los casos encontrados respetando el mismo orden del archivo.
        titulo_actual = ""  # Guarda temporalmente el título perteneciente al caso que se está construyendo.
        comandos_actuales: list[str] = []  # Acumula todas las líneas de código pertenecientes al mismo ejemplo.
        salida_actual = ""  # Conserva temporalmente la descripción del resultado esperado.

        def finalizar_actual() -> None:
            nonlocal titulo_actual, comandos_actuales, salida_actual  # Permite cerrar y limpiar el caso construido por la función exterior.

            if comandos_actuales:
                titulo = titulo_actual or f"{tipo} #{len(ejemplos) + 1}"  # Genera un título auxiliar únicamente cuando el archivo no proporcionó uno.
                comando = "\n".join(comando.strip() for comando in comandos_actuales if comando.strip())  # Conserva juntas las instrucciones pertenecientes al mismo caso.

                ejemplos.append(
                    EjemploCodigo(
                        tipo=tipo,
                        titulo=titulo,
                        comando=comando,
                        salida_esperada=salida_actual.strip(),
                    )
                )  # Registra el ejemplo completo para la interfaz y las pruebas.

            titulo_actual = ""  # Limpia el título para impedir que se reutilice accidentalmente en el siguiente caso.
            comandos_actuales = []  # Vacía las instrucciones que ya fueron almacenadas.
            salida_actual = ""  # Limpia también la descripción asociada con el caso finalizado.

        for linea in texto.splitlines():
            contenido = linea.strip()  # Elimina espacios exteriores sin modificar el código significativo de cada ejemplo.

            if not contenido:
                continue  # Ignora las líneas vacías utilizadas solamente para separar visualmente los casos.

            contenido_minusculas = contenido.lower()  # Crea una copia normalizada únicamente para reconocer encabezados y descripciones.

            if contenido.startswith("#"):
                finalizar_actual()  # Finaliza cualquier ejemplo anterior antes de comenzar un título nuevo.
                titulo_actual = contenido.lstrip("#").strip()  # Conserva el título sin el marcador utilizado como comentario.
                continue

            if contenido_minusculas.startswith("caso"):
                finalizar_actual()  # Mantiene compatibilidad con archivos donde los títulos no utilizan #.
                titulo_actual = contenido  # Conserva el encabezado completo como nombre del nuevo ejemplo.
                continue

            if contenido_minusculas.startswith(("salida esperada", "resultado esperado")):
                salida_actual = contenido  # Conserva íntegra la expectativa porque también es utilizada por las pruebas automáticas.
                finalizar_actual()  # Cierra el ejemplo porque esta línea marca el final de su definición.
                continue

            if contenido_minusculas.startswith(("entrada válida", "entrada valida", "entrada inválida", "entrada invalida")):
                if not titulo_actual:
                    titulo_actual = contenido  # Utiliza el encabezado general como título solamente cuando todavía no existe otro más específico.

                continue

            if self._es_linea_codigo(contenido):
                if "<" in contenido or ">" in contenido:
                    continue  # Descarta plantillas explicativas que contienen marcadores y no representan código ejecutable real.

                if not titulo_actual and comandos_actuales:
                    finalizar_actual()  # Mantiene compatibilidad con archivos antiguos donde cada línea independiente representaba un ejemplo.

                comandos_actuales.append(contenido)  # Conserva instrucciones correctas y líneas deliberadamente mal ordenadas para que lleguen al compilador.

        finalizar_actual()  # Guarda cualquier ejemplo pendiente al terminar de recorrer el archivo.

        return ejemplos  # Devuelve la colección completa preparada para la interfaz y las pruebas automáticas.