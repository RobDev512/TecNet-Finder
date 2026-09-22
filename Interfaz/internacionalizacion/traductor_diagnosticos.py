# ============================================================
# Archivo: traductor_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Traduce únicamente la representación visual de los diagnósticos.
#
# Los objetos Diagnostico, sus códigos oficiales y el catálogo
# formal de Motor permanecen intactos en español para no alterar
# el comportamiento del compilador ni las pruebas existentes.
# ============================================================

from Motor.compilacion.diagnosticos import (
    CATALOGO_DIAGNOSTICOS,
    ESTADO_DIAGNOSTICO_DISPONIBLE,
    Diagnostico,
    obtener_informacion_diagnostico,
)
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class TraductorDiagnosticos:
    def __init__(self, gestor: GestorTraducciones):
        self.gestor = gestor

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)

    def categoria(self, categoria: str) -> str:
        claves = {
            "Léxico": "diagnosticos.categoria.lexico",
            "Sintáctico": "diagnosticos.categoria.sintactico",
            "Semántico": "diagnosticos.categoria.semantico",
            "Advertencia": "diagnosticos.categoria.advertencia",
            "General": "diagnosticos.categoria.general",
        }
        clave = claves.get(categoria)
        return self._t(clave) if clave is not None else categoria

    def nombre(self, codigo: str) -> str:
        return self._campo_codigo(codigo, "nombre")

    def descripcion(self, codigo: str) -> str:
        return self._campo_codigo(codigo, "descripcion")

    def solucion(self, codigo: str) -> str:
        return self._campo_codigo(codigo, "solucion")

    def _campo_codigo(self, codigo: str, campo: str) -> str:
        codigo_real = codigo if codigo in CATALOGO_DIAGNOSTICOS else "GEN-001"
        clave = f"diagnosticos.codigo.{codigo_real}.{campo}"
        texto = self._t(clave)
        if texto.startswith("[") and texto.endswith("]"):
            return str(obtener_informacion_diagnostico(codigo_real).get(campo, ""))
        return texto

    def estado(self, codigo: str) -> str:
        if codigo not in CATALOGO_DIAGNOSTICOS:
            return self._t("diagnosticos.estado.no_registrado")

        informacion = CATALOGO_DIAGNOSTICOS[codigo]
        if informacion["estado"] == ESTADO_DIAGNOSTICO_DISPONIBLE:
            return self._t("diagnosticos.estado.disponible")

        etapa = str(informacion.get("etapa", "")).strip()
        return self._t("diagnosticos.estado.pendiente_etapa", etapa=etapa) if etapa else self._t("diagnosticos.estado.pendiente")

    def mensaje(self, diagnostico: Diagnostico) -> str:
        # En español conserva exactamente el mensaje contextual original generado
        # por lexer/parser/semántico. En otros idiomas utiliza la descripción
        # oficial traducida y conserva el fragmento concreto cuando existe.
        if self.gestor.idioma == "es":
            return diagnostico.mensaje

        texto = self.descripcion(diagnostico.codigo)
        fragmento = (diagnostico.fragmento or "").strip()
        if fragmento:
            texto = f"{texto} {self._t('diagnosticos.fragmento_detectado', fragmento=fragmento)}"
        return texto

    def solucion_diagnostico(self, diagnostico: Diagnostico) -> str:
        texto = self.solucion(diagnostico.codigo)
        return texto or diagnostico.solucion
