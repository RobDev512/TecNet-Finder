# ============================================================
# Archivo: preferencias_tema_temporales.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Mantiene una copia temporal de la selección de tema mientras
# Configuración permanece abierta.
#
# Elegir una variante solamente modifica esta copia.
# Aplicar o Aceptar confirmarán posteriormente el valor real.
# Cancelar descartará la selección sin tocar el archivo.
# ============================================================

from Motor.configuracion.catalogo_temas import normalizar_tema, tema_existe  # Proporciona la validación compartida del catálogo.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Proporciona la preferencia realmente persistida.


class PreferenciasTemaTemporales:
    def __init__(self, preferencias_reales: PreferenciasTema):
        self.preferencias_reales = preferencias_reales  # Conserva la configuración persistente como referencia.
        self._tema = preferencias_reales.tema()  # Copia la selección actual sin modificar todavía el archivo.

    def tema(self) -> str:
        return self._tema  # Devuelve la variante todavía no confirmada.

    def establecer_tema(self, tema_id: str) -> bool:
        if not tema_existe(tema_id):  # Comprueba que la selección continúe perteneciendo al catálogo.
            return False  # Rechaza silenciosamente cualquier identificador desconocido.
        self._tema = tema_id  # Conserva únicamente el nuevo valor dentro de memoria.
        return True  # Confirma que la copia temporal fue modificada.

    def recargar(self) -> None:
        self._tema = self.preferencias_reales.tema()  # Recupera la selección persistente y descarta cualquier cambio pendiente.

    def normalizar(self) -> None:
        self._tema = normalizar_tema(self._tema)  # Garantiza que una actualización futura del catálogo deje la copia en un estado seguro.