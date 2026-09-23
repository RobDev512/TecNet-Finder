# ============================================================
# Archivo: traductor_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Traduce la representación de los ejemplos académicos sin
# modificar los archivos TXT originales que continúan siendo la
# fuente canónica utilizada por las pruebas automáticas.
#
# También localiza únicamente identificadores escritos por el
# usuario después de NAME (o usados deliberadamente fuera de
# lugar en ejemplos inválidos). Las palabras reservadas del DSL
# IP, MASK, HOSTS y NAME permanecen intactas.
# ============================================================

import json
import re
from pathlib import Path

from Motor.configuracion.catalogo_idiomas import (
    IDIOMA_ESPANOL,
    normalizar_codigo_idioma,
    resolver_codigo_idioma,
)
from Motor.ejemplos.gestor_ejemplos import EjemploCodigo


RUTA_CATALOGOS_PREDETERMINADA = (
    Path(__file__).resolve().parent.parent.parent / "Recursos" / "Ejemplos"
)


PATRON_CASO = re.compile(r"\b([VI]\d+)\b", flags=re.IGNORECASE)


def identificador_caso(titulo: str) -> str | None:
    coincidencia = PATRON_CASO.search(str(titulo))
    if coincidencia is None:
        return None
    return coincidencia.group(1).upper()


class TraductorEjemplos:
    def __init__(self, idioma: str = IDIOMA_ESPANOL, ruta_catalogos: Path | None = None):
        self.ruta_catalogos = ruta_catalogos or RUTA_CATALOGOS_PREDETERMINADA
        self._cache: dict[str, dict] = {}
        self.idioma = resolver_codigo_idioma(idioma)

    def establecer_idioma(self, idioma: str) -> bool:
        normalizado = normalizar_codigo_idioma(idioma)
        if normalizado is None:
            return False
        self.idioma = normalizado
        return True

    def _cargar_catalogo(self, idioma: str) -> dict:
        if idioma in self._cache:
            return self._cache[idioma]

        ruta = self.ruta_catalogos / f"{idioma}.json"
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, dict):
                datos = {}
        except (OSError, json.JSONDecodeError):
            datos = {}

        self._cache[idioma] = datos
        return datos

    def _catalogo_activo(self) -> dict:
        return self._cargar_catalogo(self.idioma)

    def _traducir_identificadores(self, comando: str) -> str:
        catalogo = self._catalogo_activo()
        nombres = catalogo.get("nombres", {})
        if not isinstance(nombres, dict) or not nombres:
            return comando

        resultado = comando
        for original in sorted(nombres, key=len, reverse=True):
            traducido = nombres.get(original)
            if not isinstance(traducido, str) or not traducido:
                continue
            resultado = re.sub(
                rf"\b{re.escape(original)}\b",
                traducido,
                resultado,
            )
        return resultado

    def traducir_ejemplo(self, ejemplo: EjemploCodigo) -> EjemploCodigo:
        if self.idioma == IDIOMA_ESPANOL:
            return ejemplo

        codigo = identificador_caso(ejemplo.titulo)
        catalogo = self._catalogo_activo()
        casos = catalogo.get("casos", {})
        datos = casos.get(codigo, {}) if codigo is not None and isinstance(casos, dict) else {}

        titulo = datos.get("titulo", ejemplo.titulo) if isinstance(datos, dict) else ejemplo.titulo
        salida = datos.get("salida", ejemplo.salida_esperada) if isinstance(datos, dict) else ejemplo.salida_esperada
        comando = self._traducir_identificadores(ejemplo.comando)

        return EjemploCodigo(
            tipo=ejemplo.tipo,
            titulo=titulo,
            comando=comando,
            salida_esperada=salida,
        )

    def traducir_coleccion(self, ejemplos: list[EjemploCodigo]) -> list[EjemploCodigo]:
        return [self.traducir_ejemplo(ejemplo) for ejemplo in ejemplos]
