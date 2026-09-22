# ============================================================
# Archivo: gestor_traducciones.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Carga y resuelve los textos traducibles de TecNet Finder.
#
# Reglas principales:
# - Español es siempre el catálogo de respaldo.
# - Si falta una clave en otro idioma, se usa español.
# - Si una clave tampoco existe en español, se devuelve la clave
#   entre corchetes para que el problema sea visible y nunca
#   aparezca un texto vacío.
# - Las palabras reservadas IP, MASK, HOSTS y NAME pertenecen al
#   DSL y no forman parte de esta capa de traducción.
# ============================================================

import json  # Permite cargar los catálogos de texto almacenados en Recursos/Idiomas.
from pathlib import Path  # Permite construir rutas de forma independiente del equipo.

from Motor.configuracion.catalogo_idiomas import IDIOMA_RESPALDO, normalizar_codigo_idioma  # Reutiliza los idiomas y reglas ya validados por Configuración.


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent  # Sigue la misma estrategia de rutas utilizada por los recursos visuales del proyecto.
RUTA_CATALOGOS_PREDETERMINADA = RAIZ_PROYECTO / "Recursos" / "Idiomas"  # Centraliza los archivos JSON utilizados por el motor.


class GestorTraducciones:  # Resuelve textos traducibles con respaldo automático a español.

    def __init__(self, idioma: str = IDIOMA_RESPALDO, ruta_catalogos: str | Path | None = None):
        self.ruta_catalogos = Path(ruta_catalogos) if ruta_catalogos is not None else RUTA_CATALOGOS_PREDETERMINADA  # Permite aislar las pruebas sin alterar Recursos.
        self._catalogos: dict[str, dict[str, str]] = {}  # Conserva en memoria únicamente los catálogos que ya fueron solicitados.
        self._idioma = IDIOMA_RESPALDO  # Parte siempre de un estado seguro.
        self.establecer_idioma(idioma)  # Normaliza la selección inicial solicitada.

    @property
    def idioma(self) -> str:
        return self._idioma  # Expone únicamente el código base actualmente activo.

    def establecer_idioma(self, idioma: str) -> bool:
        codigo = normalizar_codigo_idioma(idioma)  # Acepta variantes regionales de los seis idiomas configurados.
        if codigo is None:
            return False  # Conserva el idioma actual cuando la solicitud no pertenece al catálogo admitido.
        self._idioma = codigo  # Cambia únicamente el idioma de resolución; no modifica preferencias persistentes.
        return True  # Confirma que la selección fue aceptada.

    def traducir(self, clave: str, **variables) -> str:
        if not isinstance(clave, str) or not clave.strip():
            return "[]"  # Evita textos vacíos o tipos incompatibles dentro de la interfaz.

        clave_limpia = clave.strip()  # Utiliza una clave estable aunque el llamador haya enviado espacios accidentales.
        texto = self._buscar_texto(self._idioma, clave_limpia)  # Intenta primero resolver en el idioma elegido.

        if texto is None and self._idioma != IDIOMA_RESPALDO:
            texto = self._buscar_texto(IDIOMA_RESPALDO, clave_limpia)  # Recupera español cuando la traducción elegida todavía no existe.

        if texto is None:
            return f"[{clave_limpia}]"  # Hace visible una clave realmente inexistente sin romper ni dejar controles vacíos.

        if not variables:
            return texto  # Evita aplicar formato cuando el texto no necesita valores dinámicos.

        try:
            return texto.format(**variables)  # Sustituye campos nombrados como {cantidad} o {nombre}.
        except (KeyError, ValueError, IndexError):
            return texto  # Conserva el texto base si el llamador proporcionó variables incompletas o incompatibles.

    def recargar(self) -> None:
        self._catalogos.clear()  # Fuerza a releer los JSON durante desarrollo o después de una actualización de recursos.

    def _buscar_texto(self, idioma: str, clave: str) -> str | None:
        catalogo = self._cargar_catalogo(idioma)  # Obtiene el catálogo solicitado desde caché o disco.
        texto = catalogo.get(clave)  # Busca una coincidencia exacta para evitar traducciones ambiguas.
        return texto if isinstance(texto, str) and texto else None  # Rechaza valores no textuales o vacíos.

    def _cargar_catalogo(self, idioma: str) -> dict[str, str]:
        if idioma in self._catalogos:
            return self._catalogos[idioma]  # Reutiliza el catálogo ya cargado durante la sesión.

        ruta = self.ruta_catalogos / f"{idioma}.json"  # Resuelve el archivo correspondiente con el código base.
        catalogo: dict[str, str] = {}  # Parte de un catálogo vacío ante cualquier problema de recursos.

        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))  # Lee el JSON preservando acentos y caracteres internacionales.
            if isinstance(datos, dict):
                catalogo = {
                    str(clave): valor
                    for clave, valor in datos.items()
                    if isinstance(clave, str) and isinstance(valor, str) and valor
                }  # Conserva solamente pares de texto válidos.
        except (OSError, json.JSONDecodeError):
            catalogo = {}  # Permite que el respaldo español siga funcionando aunque falte o esté dañado un catálogo secundario.

        self._catalogos[idioma] = catalogo  # Evita repetir lecturas de disco para el mismo idioma.
        return catalogo  # Devuelve siempre un diccionario seguro.
