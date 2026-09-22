# ============================================================
# Archivo: preferencias_configuracion_temporales.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Mantiene una copia temporal de las preferencias generales.
#
# Los paneles modifican esta copia mientras Configuración permanece
# abierta. Aplicar o Aceptar trasladan después esos valores hacia
# las preferencias reales; Cancelar simplemente descarta la copia.
# ============================================================

from Motor.configuracion.catalogo_idiomas import normalizar_codigo_idioma  # Reutiliza las mismas reglas de idioma sin escribir todavía en disco.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona los valores reales y reglas compartidas.


class PreferenciasConfiguracionTemporales:  # Representa las preferencias todavía no confirmadas.

    def __init__(self, preferencias_reales: PreferenciasAplicacion):
        self.preferencias_reales = preferencias_reales  # Conserva la configuración persistente como referencia.
        self.recargar_desde_preferencias_reales()  # Copia todos los valores actuales.

    def recargar_desde_preferencias_reales(self) -> None:
        self._iniciar_maximizado = self.preferencias_reales.iniciar_maximizado()  # Copia el estado inicial de ventana.
        self._recordar_estado_ventana = self.preferencias_reales.recordar_estado_ventana()  # Copia la recuperación entre sesiones.
        self._recordar_seccion_configuracion = self.preferencias_reales.recordar_seccion_configuracion()  # Copia la recuperación de categoría.
        self._familia_fuente_interfaz = self.preferencias_reales.familia_fuente_interfaz()  # Copia la tipografía general de la interfaz.
        self._tamano_fuente_interfaz = self.preferencias_reales.tamano_fuente_interfaz()  # Copia el tamaño base de la interfaz.
        self._idioma_interfaz = self.preferencias_reales.idioma_interfaz()  # Copia el idioma real sin aplicarlo todavía a la interfaz.

        self._ajuste_linea_editor = self.preferencias_reales.ajuste_linea_editor_activado()  # Copia el ajuste de líneas.
        self._botones_rapidos_editor = self.preferencias_reales.botones_rapidos_editor_visibles()  # Copia la visibilidad de controles rápidos.
        self._familia_fuente_editor = self.preferencias_reales.familia_fuente_editor()  # Copia la tipografía del editor.
        self._tamano_fuente_editor = self.preferencias_reales.tamano_fuente_editor()  # Copia el tamaño del texto.
        self._espacios_tabulacion_editor = self.preferencias_reales.espacios_tabulacion_editor()  # Copia el ancho de Tab.

        self._navegacion_errores = self.preferencias_reales.navegacion_errores_activada()  # Copia la navegación hacia errores.
        self._navegacion_vlsm = self.preferencias_reales.navegacion_vlsm_activada()  # Copia la navegación hacia VLSM.
        self._advertencias_vlsm = self.preferencias_reales.advertencias_vlsm_visibles()  # Copia la modalidad compacta.
        self._advertencias_ventana = self.preferencias_reales.advertencias_ventana_independiente()  # Copia la modalidad independiente.
        self._cerrar_ventana_advertencias = self.preferencias_reales.cerrar_ventana_advertencias_al_navegar()  # Copia el comportamiento del doble clic.

    # ========================================================
    # Ventana y apariencia
    # ========================================================

    def iniciar_maximizado(self) -> bool:
        return self._iniciar_maximizado  # Devuelve el valor temporal actual.

    def establecer_iniciar_maximizado(self, activado: bool) -> bool:
        self._iniciar_maximizado = bool(activado)  # Cambia únicamente la copia en memoria.
        return True  # Mantiene la interfaz utilizada por los paneles.

    def recordar_estado_ventana(self) -> bool:
        return self._recordar_estado_ventana  # Devuelve la decisión temporal.

    def establecer_recordar_estado_ventana(self, activado: bool) -> bool:
        self._recordar_estado_ventana = bool(activado)  # Conserva temporalmente la selección.
        return True  # Confirma el cambio en memoria.

    def recordar_seccion_configuracion(self) -> bool:
        return self._recordar_seccion_configuracion  # Devuelve la preferencia temporal de Configuración.

    def establecer_recordar_seccion_configuracion(self, activado: bool) -> bool:
        self._recordar_seccion_configuracion = bool(activado)  # Conserva el nuevo valor en memoria.
        return True  # Mantiene el mismo contrato que la configuración real.

    def familia_fuente_interfaz(self) -> str:
        return self._familia_fuente_interfaz  # Devuelve la tipografía general todavía no confirmada.

    def establecer_familia_fuente_interfaz(self, familia: str) -> bool:
        if not isinstance(familia, str) or not familia.strip():  # Comprueba que exista un nombre utilizable.
            return False  # Rechaza valores vacíos o incompatibles.
        self._familia_fuente_interfaz = familia.strip()  # Conserva solamente el nombre limpio.
        return True  # Confirma el cambio temporal.

    def tamano_fuente_interfaz(self) -> int:
        return self._tamano_fuente_interfaz  # Devuelve el tamaño base todavía no confirmado.

    def establecer_tamano_fuente_interfaz(self, tamano: int) -> bool:
        if not isinstance(tamano, int) or isinstance(tamano, bool):  # Comprueba que sea un entero real.
            return False  # Rechaza booleanos y otros tipos.
        if not PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_MINIMO <= tamano <= PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_MAXIMO:  # Comprueba los límites compartidos.
            return False  # Rechaza valores capaces de romper la interfaz.
        self._tamano_fuente_interfaz = tamano  # Conserva temporalmente el nuevo tamaño.
        return True  # Confirma el cambio.

    def idioma_interfaz(self) -> str:
        return self._idioma_interfaz  # Devuelve el código temporal todavía no confirmado.

    def establecer_idioma_interfaz(self, idioma: str) -> bool:
        codigo = normalizar_codigo_idioma(idioma)  # Aplica exactamente las mismas reglas utilizadas por la preferencia persistente.
        if codigo is None:
            return False  # Rechaza selecciones fuera del catálogo sin alterar la copia actual.
        self._idioma_interfaz = codigo  # Conserva exclusivamente el código base dentro de esta sesión.
        return True  # Confirma el cambio temporal.

    # ========================================================
    # Editor
    # ========================================================

    def ajuste_linea_editor_activado(self) -> bool:
        return self._ajuste_linea_editor  # Devuelve el ajuste temporal.

    def establecer_ajuste_linea_editor_activado(self, activado: bool) -> bool:
        self._ajuste_linea_editor = bool(activado)  # Modifica solamente la copia temporal.
        return True  # Confirma la actualización.

    def botones_rapidos_editor_visibles(self) -> bool:
        return self._botones_rapidos_editor  # Devuelve la visibilidad temporal.

    def establecer_botones_rapidos_editor_visibles(self, visibles: bool) -> bool:
        self._botones_rapidos_editor = bool(visibles)  # Cambia únicamente el valor temporal.
        return True  # Confirma la actualización.

    def familia_fuente_editor(self) -> str:
        return self._familia_fuente_editor  # Devuelve la tipografía todavía no confirmada.

    def establecer_familia_fuente_editor(self, familia: str) -> bool:
        if not isinstance(familia, str) or not familia.strip():  # Comprueba que exista un nombre utilizable.
            return False  # Rechaza una selección inválida.
        self._familia_fuente_editor = familia.strip()  # Conserva únicamente el nombre limpio.
        return True  # Confirma el cambio temporal.

    def tamano_fuente_editor(self) -> int:
        return self._tamano_fuente_editor  # Devuelve el tamaño todavía no aplicado.

    def establecer_tamano_fuente_editor(self, tamano: int) -> bool:
        if not isinstance(tamano, int) or isinstance(tamano, bool):  # Comprueba el tipo recibido.
            return False  # Rechaza valores incompatibles.
        if not PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MINIMO <= tamano <= PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MAXIMO:  # Comprueba los límites compartidos.
            return False  # Rechaza tamaños fuera de rango.
        self._tamano_fuente_editor = tamano  # Conserva temporalmente el nuevo tamaño.
        return True  # Confirma el cambio.

    def espacios_tabulacion_editor(self) -> int:
        return self._espacios_tabulacion_editor  # Devuelve el ancho temporal de Tab.

    def establecer_espacios_tabulacion_editor(self, espacios: int) -> bool:
        if espacios not in PreferenciasAplicacion.ESPACIOS_TABULACION_VALIDOS:  # Comprueba que pertenezca a las opciones soportadas.
            return False  # Rechaza cualquier otra cantidad.
        self._espacios_tabulacion_editor = espacios  # Conserva temporalmente la selección.
        return True  # Confirma el cambio temporal.

    # ========================================================
    # Navegación
    # ========================================================

    def navegacion_errores_activada(self) -> bool:
        return self._navegacion_errores  # Devuelve la navegación temporal.

    def establecer_navegacion_errores_activada(self, activada: bool) -> bool:
        self._navegacion_errores = bool(activada)  # Modifica únicamente la copia.
        return True  # Confirma el cambio.

    def navegacion_vlsm_activada(self) -> bool:
        return self._navegacion_vlsm  # Devuelve la navegación temporal hacia VLSM.

    def establecer_navegacion_vlsm_activada(self, activada: bool) -> bool:
        self._navegacion_vlsm = bool(activada)  # Conserva la decisión en memoria.
        return True  # Confirma el cambio.

    def navegacion_automatica_activada(self) -> bool:
        return self._navegacion_errores and self._navegacion_vlsm  # Mantiene compatibilidad con la antigua preferencia.

    def establecer_navegacion_automatica_activada(self, activada: bool) -> bool:
        valor = bool(activada)  # Normaliza una única vez el valor recibido.
        self._navegacion_errores = valor  # Aplica temporalmente la decisión a errores.
        self._navegacion_vlsm = valor  # Aplica temporalmente la misma decisión a VLSM.
        return True  # Confirma la modificación.

    # ========================================================
    # Presentación de advertencias
    # ========================================================

    def advertencias_vlsm_visibles(self) -> bool:
        return self._advertencias_vlsm  # Devuelve la modalidad compacta temporal.

    def advertencias_ventana_independiente(self) -> bool:
        return self._advertencias_ventana  # Devuelve la modalidad independiente temporal.

    def establecer_advertencias_vlsm_visibles(self, visibles: bool) -> bool:
        self._advertencias_vlsm = bool(visibles)  # Actualiza temporalmente el panel compacto.
        if visibles:  # Comprueba si acaba de activarse.
            self._advertencias_ventana = False  # Mantiene exclusividad desactivando la ventana.
        return True  # Confirma la modificación temporal.

    def establecer_advertencias_ventana_independiente(self, visibles: bool) -> bool:
        self._advertencias_ventana = bool(visibles)  # Actualiza temporalmente la ventana independiente.
        if visibles:  # Comprueba si acaba de activarse.
            self._advertencias_vlsm = False  # Mantiene exclusividad desactivando el panel.
        return True  # Confirma el cambio temporal.

    def cerrar_ventana_advertencias_al_navegar(self) -> bool:
        return self._cerrar_ventana_advertencias  # Devuelve la decisión temporal.

    def establecer_cerrar_ventana_advertencias_al_navegar(self, cerrar: bool) -> bool:
        self._cerrar_ventana_advertencias = bool(cerrar)  # Conserva temporalmente el comportamiento elegido.
        return True  # Confirma la modificación en memoria.