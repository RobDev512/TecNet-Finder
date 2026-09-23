# ============================================================
# Archivo: prueba_ejemplos_localizados.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la localización visual de ejemplos y la eliminación
# del prefijo VALOR dentro de los árboles gráficos.
# ============================================================

import json
from pathlib import Path

from Interfaz.internacionalizacion.traductor_ejemplos import (
    RUTA_CATALOGOS_PREDETERMINADA,
    TraductorEjemplos,
    identificador_caso,
)
from Motor.ejemplos.gestor_ejemplos import EjemploCodigo


class _RectanguloFalso:
    def __init__(self, ancho=40.0, alto=30.0):
        self._ancho = ancho
        self._alto = alto

    def width(self):
        return self._ancho

    def height(self):
        return self._alto


class _PosicionFalsa:
    def __init__(self, x=10.0, y=15.0):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class _ItemTextoFalso:
    def __init__(self, texto):
        self.texto = texto
        self.posicion = _PosicionFalsa()

    def toPlainText(self):
        return self.texto

    def setPlainText(self, texto):
        self.texto = texto

    def boundingRect(self):
        return _RectanguloFalso(50.0 if "\n" in self.texto else 30.0, 30.0 if "\n" in self.texto else 15.0)

    def pos(self):
        return self.posicion

    def setPos(self, x, y):
        self.posicion = _PosicionFalsa(x, y)


class _EscenaFalsa:
    def __init__(self, items):
        self._items = items

    def items(self):
        return list(self._items)


class _VistaFalsa:
    def __init__(self, escena):
        self._escena = escena

    def scene(self):
        return self._escena


def prueba_identifica_casos_en_titulos_localizados():
    assert identificador_caso("CASO V12: ejemplo") == "V12"
    assert identificador_caso("CASE I25: example") == "I25"
    assert identificador_caso("FALL V3: Beispiel") == "V3"
    assert identificador_caso("sin identificador") is None


def prueba_catalogos_contienen_los_39_casos():
    esperados = {*(f"V{i}" for i in range(1, 15)), *(f"I{i}" for i in range(1, 26))}
    for codigo in ("es", "en", "pt", "fr", "de", "la"):
        ruta = RUTA_CATALOGOS_PREDETERMINADA / f"{codigo}.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert set(datos["casos"]) == esperados
        assert len(datos["nombres"]) >= 14


def prueba_ingles_traduce_textos_y_nombre_insertado_sin_tocar_dsl():
    original = EjemploCodigo(
        tipo="Válida",
        titulo="CASO V1: Entrada válida completa con nombre de red",
        comando="IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina",
        salida_esperada="Salida esperada: caso válido.",
    )
    traducido = TraductorEjemplos("en").traducir_ejemplo(original)

    assert traducido.titulo.startswith("CASE V1:")
    assert "Expected output:" in traducido.salida_esperada
    assert traducido.comando == "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Office"
    assert original.comando.endswith("NAME Oficina")


def prueba_identificador_fuera_de_name_tambien_se_localiza():
    original = EjemploCodigo(
        tipo="Inválida",
        titulo="CASO I3: Error léxico por identificador fuera de lugar",
        comando="IP 192.168.1.0 MASK /24 HOSTS 50 Oficina",
        salida_esperada="Salida esperada: caso inválido.",
    )
    traducido = TraductorEjemplos("de").traducir_ejemplo(original)
    assert traducido.comando.endswith("HOSTS 50 Buero")
    assert "IP " in traducido.comando
    assert " MASK " in traducido.comando
    assert " HOSTS " in traducido.comando


def prueba_nombre_generico_localizado_sigue_usando_valor_compatible_con_adv006():
    original = EjemploCodigo(
        tipo="Válida",
        titulo="CASO V10: Entrada válida con nombre de red genérico",
        comando="IP 192.168.70.0 MASK /24 HOSTS 50 NAME Red",
        salida_esperada="Salida esperada: caso válido con advertencia.",
    )
    assert TraductorEjemplos("en").traducir_ejemplo(original).comando.endswith("NAME Network")
    for codigo in ("pt", "fr", "de", "la"):
        assert TraductorEjemplos(codigo).traducir_ejemplo(original).comando.endswith("NAME Test")


def prueba_control_de_cierre_elimina_prefijo_valor_sin_tocar_otros_nodos():
    # Importación local para mantener esta prueba centrada en la lógica visual añadida.
    from Interfaz.internacionalizacion.control_cierre_interfaz import ControlCierreInterfaz

    valor = _ItemTextoFalso("VALOR\n50")
    reservado = _ItemTextoFalso("HOSTS")
    vista = _VistaFalsa(_EscenaFalsa([valor, reservado]))

    ControlCierreInterfaz._ocultar_etiqueta_valor_escena(None, vista)

    assert valor.toPlainText() == "50"
    assert reservado.toPlainText() == "HOSTS"


def prueba_comandos_localizados_conservan_comportamiento_de_casos_clave():
    from Motor.ejemplos.gestor_ejemplos import GestorEjemplos
    from Motor.ejemplos.pruebas_ejemplos import EjecutorPruebasEjemplos

    validos, invalidos = GestorEjemplos().cargar_ejemplos()
    originales = {identificador_caso(e.titulo): e for e in [*validos, *invalidos]}
    claves = ("V1", "V7", "V10", "I3", "I24")

    for idioma in ("en", "pt", "fr", "de", "la"):
        traductor = TraductorEjemplos(idioma)
        casos_prueba = []
        for clave in claves:
            original = originales[clave]
            localizado = traductor.traducir_ejemplo(original)
            casos_prueba.append(
                EjemploCodigo(
                    tipo=original.tipo,
                    titulo=original.titulo,
                    comando=localizado.comando,
                    salida_esperada=original.salida_esperada,
                )
            )

        resumen = EjecutorPruebasEjemplos().ejecutar(casos_prueba)
        assert resumen.fallidos == 0, idioma

def prueba_control_cierre_preserva_acciones_post_compilacion():
    import inspect
    from Interfaz.internacionalizacion.control_cierre_interfaz import ControlCierreInterfaz

    fuente = inspect.getsource(ControlCierreInterfaz._preparar_dialogos_principales)

    assert "boton.clicked.disconnect()" not in fuente
    assert "boton.clicked.disconnect(accion_original)" in fuente
    assert "panel.accion_analizar" in fuente


def prueba_entrada_mixta_conserva_vlsm_y_diagnosticos():
    from Motor.compilacion.flujo_compilacion import FlujoCompilacion

    codigo = (
        "IP 192.168.70.0 MASK /24 HOSTS 50 NAME Network\n"
        "IP 192.168.100.0 MASK /24 HOSTS 10,60,30\n"
        "IP 192.168.1.0 MASK /24 HOSTS 50 Office"
    )

    resultado = FlujoCompilacion().analizar(codigo)
    codigos = {diagnostico.codigo for diagnostico in resultado.diagnosticos}

    assert resultado.tiene_errores
    assert "LEX-001" in codigos
    assert len(resultado.subredes_vlsm) == 5

