# ============================================================
# Archivo: gestor_tipografia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra de forma centralizada la apariencia dinámica de
# TecNet Finder relacionada con temas y tipografías.
#
# Además de aplicar el QSS general, transforma los colores de
# controles que poseen hojas de estilos locales propias.
#
# Esto resulta necesario para componentes como:
# - Configuración.
# - Selectores personalizados.
# - Popups.
# - Algunos controles de ventana.
#
# El editor mantiene siempre su fuente independiente.
# ============================================================

from PySide6.QtGui import QFontMetricsF  # Permite calcular el ancho visual real de una tabulación.
from PySide6.QtWidgets import QApplication  # Permite acceder a QApplication y a todos los widgets existentes.
from Interfaz.estilos_temas import construir_estilo_aplicacion  # Construye la hoja visual correspondiente con el tema actual.
from Motor.catalogo_fuentes import normalizar_fuente  # Evita aplicar familias incompatibles con Qt.
from Motor.catalogo_temas import obtener_tema  # Permite consultar la paleta completa seleccionada.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona las preferencias persistentes de fuente.
from Motor.preferencias_tema import PreferenciasTema  # Proporciona el tema persistente.


class GestorTipografia:  # Coordina fuentes y tema sin cargar esa responsabilidad dentro de ControlConfiguracion.
    PROPIEDAD_ESTILO_BASE = "_tecnet_estilo_base"  # Conserva el estilo local original de cada widget.
    PROPIEDAD_ESTILO_APLICADO = "_tecnet_estilo_aplicado"  # Conserva la última transformación realizada por este gestor.

    def __init__(self, ventana, preferencias_aplicacion: PreferenciasAplicacion, preferencias_tema: PreferenciasTema):
        self.ventana = ventana  # Conserva acceso a la ventana principal y al editor.
        self.preferencias_aplicacion = preferencias_aplicacion  # Reutiliza la misma instancia general de preferencias.
        self.preferencias_tema = preferencias_tema  # Conserva la selección visual persistente.

    def aplicar(self, *_argumentos) -> None:
        aplicacion = QApplication.instance()  # Recupera la única aplicación gráfica activa.
        if aplicacion is None: return  # Evita cualquier operación antes de inicializar Qt.

        familia_interfaz_guardada = self.preferencias_aplicacion.familia_fuente_interfaz()  # Recupera la familia global persistida.
        familia_editor_guardada = self.preferencias_aplicacion.familia_fuente_editor()  # Recupera la familia propia del editor.
        familia_interfaz = normalizar_fuente(familia_interfaz_guardada, PreferenciasAplicacion.FUENTE_INTERFAZ_PREDETERMINADA)  # Garantiza una familia compatible.
        familia_editor = normalizar_fuente(familia_editor_guardada, PreferenciasAplicacion.FUENTE_EDITOR_PREDETERMINADA)  # Garantiza una familia compatible para código.
        tamano_interfaz = self.preferencias_aplicacion.tamano_fuente_interfaz()  # Recupera el tamaño global.
        tamano_editor = self.preferencias_aplicacion.tamano_fuente_editor()  # Recupera el tamaño independiente del editor.
        tema_id = self.preferencias_tema.tema()  # Recupera la variante visual confirmada.

        if familia_interfaz != familia_interfaz_guardada: self.preferencias_aplicacion.establecer_familia_fuente_interfaz(familia_interfaz)  # Corrige una preferencia global antigua o incompatible.
        if familia_editor != familia_editor_guardada: self.preferencias_aplicacion.establecer_familia_fuente_editor(familia_editor)  # Corrige también una preferencia incompatible del editor.

        fuente_aplicacion = aplicacion.font()  # Copia la fuente general utilizada actualmente.
        fuente_aplicacion.setFamily(familia_interfaz)  # Cambia únicamente su familia.
        fuente_aplicacion.setPointSize(tamano_interfaz)  # Cambia únicamente su tamaño.
        aplicacion.setFont(fuente_aplicacion)  # Actualiza la fuente predeterminada de Qt.

        self.ventana.editor_codigo.setObjectName("EditorCodigo")  # Identifica el editor para mantener su tipografía independiente.
        aplicacion.setStyleSheet(construir_estilo_aplicacion(tema_id, familia_interfaz, tamano_interfaz, familia_editor, tamano_editor))  # Aplica la estructura base más la paleta dinámica.
        self._aplicar_estilos_locales(tema_id)  # Actualiza también hojas de estilo aplicadas directamente a widgets concretos.
        self._aplicar_fuente_editor(familia_editor, tamano_editor)  # Sincroniza QFont y las métricas internas del editor.

    def _aplicar_estilos_locales(self, tema_id: str) -> None:
        aplicacion = QApplication.instance()  # Recupera QApplication para consultar todos los widgets existentes.
        if aplicacion is None: return  # Evita operar si la interfaz ya no se encuentra disponible.
        paleta = obtener_tema(tema_id)  # Recupera la paleta completa correspondiente con el tema actual.

        for widget in aplicacion.allWidgets():  # Recorre ventana principal, Configuración, popups y controles auxiliares.
            estilo_actual = widget.styleSheet()  # Consulta exclusivamente la hoja de estilos aplicada directamente al widget.
            if not estilo_actual.strip(): continue  # Omite componentes que dependen solamente del QSS global.

            estilo_base = widget.property(self.PROPIEDAD_ESTILO_BASE)  # Recupera la copia original conservada anteriormente.
            estilo_aplicado = widget.property(self.PROPIEDAD_ESTILO_APLICADO)  # Recupera la última transformación generada por el gestor.

            if not isinstance(estilo_base, str) or (isinstance(estilo_aplicado, str) and estilo_actual != estilo_aplicado):  # Detecta un control nuevo o un estilo modificado posteriormente por otro componente.
                estilo_base = estilo_actual  # Toma la versión actual como nueva referencia original.
                widget.setProperty(self.PROPIEDAD_ESTILO_BASE, estilo_base)  # Conserva esa referencia para futuros cambios de tema.

            estilo_nuevo = self._traducir_estilo_local(estilo_base, paleta)  # Sustituye la antigua paleta oscura por la variante seleccionada.
            widget.setProperty(self.PROPIEDAD_ESTILO_APLICADO, estilo_nuevo)  # Registra exactamente qué transformación pertenece al gestor.
            if estilo_actual != estilo_nuevo: widget.setStyleSheet(estilo_nuevo)  # Evita repintados innecesarios cuando el contenido no cambia.

    def _traducir_estilo_local(self, estilo: str, p: dict) -> str:
        reemplazos_especificos = (
            ("selection-color: #1e1e2e", f"selection-color: {p['texto_inverso']}"),  # Mantiene texto legible dentro de una selección.
            ("color: #1e1e2e", f"color: {p['texto_inverso']}"),  # Mantiene texto inverso sobre botones de acento.
            ("border: 1px solid #cdd6f4", f"border: 1px solid {p['borde_fuerte']}"),  # Evita convertir un borde claro en texto del tema.
            ("border: 1px solid #313244", f"border: 1px solid {p['borde']}"),  # Traduce bordes discretos.
            ("border: 1px solid #45475a", f"border: 1px solid {p['borde_fuerte']}"),  # Traduce bordes de mayor contraste.
            ("border: 1px solid #585b70", f"border: 1px solid {p['superficie_presionada']}"),  # Traduce contornos utilizados en controles.
            ("border-bottom: 1px solid #313244", f"border-bottom: 1px solid {p['borde']}"),  # Traduce separadores inferiores.
            ("border-top: 1px solid #313244", f"border-top: 1px solid {p['borde']}"),  # Traduce separadores superiores.
            ("border-right: 1px solid #313244", f"border-right: 1px solid {p['borde']}"),  # Traduce divisiones laterales.
            ("border-color: #313244", f"border-color: {p['borde']}"),  # Traduce un borde discreto declarado por propiedad.
            ("border-color: #45475a", f"border-color: {p['borde_fuerte']}"),  # Traduce un borde fuerte declarado por propiedad.
            ("border-color: #585b70", f"border-color: {p['superficie_presionada']}"),  # Traduce un borde interactivo.
            ("border-color: #89b4fa", f"border-color: {p['acento']}"),  # Traduce explícitamente el antiguo azul principal.
            ("color: #cdd6f4", f"color: {p['texto']}"),  # Traduce texto principal.
            ("color: #a6adc8", f"color: {p['texto_secundario']}"),  # Traduce texto secundario.
            ("color: #6c7086", f"color: {p['texto_deshabilitado']}"),  # Traduce texto deshabilitado.
        )  # Las reglas específicas se ejecutan antes de sustituir colores genéricos para evitar ambigüedades.

        for original, nuevo in reemplazos_especificos: estilo = estilo.replace(original, nuevo).replace(original.upper(), nuevo)  # Aplica cada traducción específica sin importar el uso histórico de mayúsculas.

        reemplazos_generales = {
            "#1e1e2e": p["fondo"],  # Traduce el antiguo fondo principal.
            "#181825": p["panel"],  # Traduce el antiguo fondo de paneles.
            "#11111b": p["editor"],  # Traduce el antiguo fondo profundo.
            "#313244": p["superficie"],  # Traduce superficies convencionales.
            "#363649": p["superficie_suave"],  # Traduce la superficie intermedia de selectores.
            "#45475a": p["superficie_hover"],  # Traduce estados hover.
            "#585b70": p["superficie_presionada"],  # Traduce estados presionados.
            "#242536": p["fondo_deshabilitado"],  # Traduce el primer fondo deshabilitado histórico.
            "#2b2d42": p["fondo_deshabilitado"],  # Traduce el segundo fondo deshabilitado histórico.
            "#3b3d56": p["borde_deshabilitado"],  # Traduce contornos deshabilitados.
            "#cdd6f4": p["texto"],  # Traduce cualquier texto principal restante.
            "#a6adc8": p["texto_secundario"],  # Traduce cualquier texto secundario restante.
            "#6c7086": p["texto_deshabilitado"],  # Traduce contenido deshabilitado restante.
            "#89b4fa": p["acento"],  # Traduce el antiguo acento azul.
            "#b4befe": p["acento_hover"],  # Traduce el antiguo hover del acento.
        }  # Los colores semánticos no aparecen aquí para que conserven su significado propio.

        for original, nuevo in reemplazos_generales.items(): estilo = estilo.replace(original, nuevo).replace(original.upper(), nuevo)  # Traduce los colores estructurales restantes.
        return estilo  # Devuelve la hoja local lista para el tema seleccionado.

    def _aplicar_fuente_editor(self, familia: str, tamano: int) -> None:
        editor = self.ventana.editor_codigo  # Recupera el editor especializado.
        espacios = self.preferencias_aplicacion.espacios_tabulacion_editor()  # Recupera el ancho configurado de Tab.
        fuente_editor = editor.font()  # Copia la fuente actual para conservar propiedades adicionales.
        fuente_editor.setFamily(familia)  # Aplica exclusivamente la familia del editor.
        fuente_editor.setPointSize(tamano)  # Aplica exclusivamente su tamaño.
        editor.setFont(fuente_editor)  # Actualiza realmente el QPlainTextEdit.
        metricas = QFontMetricsF(editor.font())  # Obtiene las medidas definitivas.
        editor.setTabStopDistance(metricas.horizontalAdvance(" ") * espacios)  # Convierte la cantidad de espacios en distancia visual.
        editor.actualizar_ancho_area_numeros_linea()  # Recalcula el margen utilizado por los números laterales.
        editor.viewport().update()  # Solicita el redibujado inmediato del código.