# ============================================================
# Archivo: gestor_tipografia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra la apariencia dinámica general de TecNet Finder.
#
# Responsabilidades:
# - Tema visual.
# - Fuente general.
# - Fuente independiente del editor.
# - Estilos locales heredados.
# - Iconos dependientes del modo.
# - Resaltado de sintaxis.
# - Componentes con dibujo especial.
#
# Las ventanas dinámicas pueden prepararse antes de mostrarse,
# evitando destellos del tema oscuro al utilizar un tema claro.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QTimer  # Permite observar ventanas y cambios de estado.
from PySide6.QtGui import QColor, QFontMetricsF, QIcon, QPalette  # Proporciona fuentes, colores, iconos y paletas.
from PySide6.QtWidgets import QApplication, QPushButton, QWidget  # Permite administrar QApplication y recursos declarados.
from Interfaz.aplicador_tema_componentes import AplicadorTemaComponentes  # Atiende componentes que no dependen exclusivamente del QSS.
from Interfaz.estilos_temas import construir_estilo_aplicacion  # Construye el stylesheet general del tema.
from Interfaz.recursos_tema import resolver_icono_tema, tema_utiliza_iconos_claros  # Resuelve recursos gráficos claros u oscuros.
from Motor.catalogo_fuentes import normalizar_fuente  # Garantiza familias compatibles con Qt.
from Motor.catalogo_temas import obtener_tema  # Proporciona la paleta utilizada para adaptar estilos locales.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona las preferencias persistentes de tipografía.
from Motor.preferencias_tema import PreferenciasTema  # Proporciona la variante visual persistente.


class GestorTipografia(QObject):  # Centraliza apariencia y recursos visuales.
    PROPIEDAD_ESTILO_BASE = "_tecnet_estilo_base"  # Conserva el stylesheet local original.
    PROPIEDAD_ESTILO_APLICADO = "_tecnet_estilo_aplicado"  # Conserva la última traducción generada.
    PROPIEDAD_TEMA_PREPARADO = "_tecnet_tema_preparado"  # Registra qué tema recibió una ventana antes de mostrarse.

    def __init__(self, ventana, preferencias_aplicacion: PreferenciasAplicacion, preferencias_tema: PreferenciasTema):
        super().__init__(ventana)  # Vincula el gestor con la ventana principal.
        self.ventana = ventana  # Conserva acceso a editor, barra y resultados.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva las preferencias generales.
        self.preferencias_tema = preferencias_tema  # Conserva las preferencias visuales.
        self.aplicador_componentes = AplicadorTemaComponentes(self.ventana)  # Centraliza excepciones visuales.

        self._firma_estilo = None  # Registra la última combinación utilizada por el QSS.
        self._firma_fuente_interfaz = None  # Registra la fuente general.
        self._firma_editor = None  # Registra tipografía y tabulación del editor.
        self._tema_aplicado = None  # Conserva la variante actualmente representada.

        self.ventana.installEventFilter(self)  # Permite corregir iconos después de fullscreen.
        aplicacion = QApplication.instance()  # Recupera QApplication.
        if aplicacion is not None: aplicacion.installEventFilter(self)  # Permite atender ventanas dinámicas como respaldo.

    # ========================================================
    # Aplicación global
    # ========================================================

    def aplicar(self, *_argumentos) -> None:
        aplicacion = QApplication.instance()  # Recupera la aplicación gráfica activa.
        if aplicacion is None: return  # Evita trabajar antes de inicializar Qt.

        familia_interfaz_guardada = self.preferencias_aplicacion.familia_fuente_interfaz()  # Recupera la fuente global guardada.
        familia_editor_guardada = self.preferencias_aplicacion.familia_fuente_editor()  # Recupera la fuente independiente del editor.
        familia_interfaz = normalizar_fuente(familia_interfaz_guardada, PreferenciasAplicacion.FUENTE_INTERFAZ_PREDETERMINADA)  # Garantiza una familia compatible.
        familia_editor = normalizar_fuente(familia_editor_guardada, PreferenciasAplicacion.FUENTE_EDITOR_PREDETERMINADA)  # Garantiza una familia compatible para código.
        tamano_interfaz = self.preferencias_aplicacion.tamano_fuente_interfaz()  # Recupera el tamaño global.
        tamano_editor = self.preferencias_aplicacion.tamano_fuente_editor()  # Recupera el tamaño del editor.
        espacios_tab = self.preferencias_aplicacion.espacios_tabulacion_editor()  # Recupera el ancho de Tab.
        tema_id = self.preferencias_tema.tema()  # Recupera la variante confirmada.

        if familia_interfaz != familia_interfaz_guardada: self.preferencias_aplicacion.establecer_familia_fuente_interfaz(familia_interfaz)  # Corrige una preferencia incompatible.
        if familia_editor != familia_editor_guardada: self.preferencias_aplicacion.establecer_familia_fuente_editor(familia_editor)  # Corrige también la del editor.

        firma_fuente_interfaz = (familia_interfaz, tamano_interfaz)  # Determina cuándo QApplication.font necesita cambiar.
        firma_estilo = (tema_id, familia_interfaz, tamano_interfaz, familia_editor, tamano_editor)  # Determina cuándo debe reconstruirse el QSS.
        firma_editor = (familia_editor, tamano_editor, espacios_tab)  # Determina cuándo deben recalcularse métricas.
        cambio_tema = tema_id != self._tema_aplicado  # Detecta una variante realmente diferente.
        cambio_estilo = firma_estilo != self._firma_estilo  # Detecta cualquier cambio visual global.

        if firma_fuente_interfaz != self._firma_fuente_interfaz:
            fuente_aplicacion = aplicacion.font()  # Copia la fuente vigente.
            fuente_aplicacion.setFamily(familia_interfaz)  # Aplica la familia seleccionada.
            fuente_aplicacion.setPointSize(tamano_interfaz)  # Aplica el tamaño seleccionado.
            aplicacion.setFont(fuente_aplicacion)  # Actualiza QApplication.
            self._firma_fuente_interfaz = firma_fuente_interfaz  # Conserva la configuración aplicada.

        self.ventana.editor_codigo.setObjectName("EditorCodigo")  # Mantiene una identificación estable para el editor.

        if cambio_estilo:
            aplicacion.setStyleSheet(construir_estilo_aplicacion(tema_id, familia_interfaz, tamano_interfaz, familia_editor, tamano_editor))  # Reconstruye el QSS únicamente cuando cambia algo real.
            self._firma_estilo = firma_estilo  # Registra la combinación aplicada.
            self._aplicar_estilos_locales(tema_id, solo_nuevos=False)  # Traduce todos los estilos locales.
        else:
            self._aplicar_estilos_locales(tema_id, solo_nuevos=True)  # Atiende solamente widgets nuevos.

        if firma_editor != self._firma_editor:
            self._aplicar_fuente_editor(familia_editor, tamano_editor, espacios_tab)  # Recalcula la geometría del editor.
            self._firma_editor = firma_editor  # Conserva la configuración aplicada.

        self._aplicar_apariencia_editor(tema_id, cambio_tema)  # Sincroniza placeholder y resaltador.
        self._aplicar_iconos_tema(tema_id)  # Sincroniza todos los recursos gráficos conocidos.
        self.aplicador_componentes.aplicar(tema_id)  # Atiende gutter, tablas, diagnósticos, árbol y ventanas auxiliares.
        self._tema_aplicado = tema_id  # Registra finalmente la variante vigente.

    # ========================================================
    # Preparación de ventanas antes de mostrarlas
    # ========================================================

    def preparar_ventana(self, ventana: QWidget) -> None:
        tema_id = self._tema_aplicado or self.preferencias_tema.tema()  # Utiliza el tema ya aplicado o recupera la preferencia persistente.
        self._aplicar_estilos_subarbol(ventana, tema_id)  # Traduce únicamente los estilos internos de esta ventana.
        self.aplicador_componentes.aplicar_ventana_dinamica(ventana, tema_id)  # Aplica reglas explícitas antes de que el usuario vea la ventana.

        barra = getattr(ventana, "barra_titulo", None)  # Recupera una barra personalizada si existe.
        if barra is not None: self._aplicar_iconos_barra(barra, tema_id, bool(getattr(ventana, "en_pantalla_completa", False)))  # Sincroniza sus iconos antes de mostrarla.

        self._aplicar_recursos_declarados(ventana, tema_id)  # Atiende botones que hayan declarado un nombre de recurso.
        ventana.setProperty(self.PROPIEDAD_TEMA_PREPARADO, tema_id)  # Informa al eventFilter que no debe volver a tematizarla durante Show.

    # ========================================================
    # Estilos locales
    # ========================================================

    def _aplicar_estilos_locales(self, tema_id: str, solo_nuevos: bool) -> None:
        aplicacion = QApplication.instance()  # Recupera todos los widgets existentes.
        if aplicacion is None: return  # Evita trabajar durante el cierre.
        paleta = obtener_tema(tema_id)  # Recupera la paleta vigente.
        for widget in aplicacion.allWidgets(): self._aplicar_estilo_local_widget(widget, paleta, solo_nuevos)  # Atiende cada hoja local.

    def _aplicar_estilos_subarbol(self, raiz: QWidget, tema_id: str) -> None:
        paleta = obtener_tema(tema_id)  # Recupera la paleta utilizada por esta ventana.
        widgets = [raiz, *raiz.findChildren(QWidget)]  # Incluye raíz y todos sus descendientes.
        for widget in widgets: self._aplicar_estilo_local_widget(widget, paleta, solo_nuevos=False)  # Traduce únicamente este subárbol.

    def _aplicar_estilo_local_widget(self, widget: QWidget, paleta: dict, solo_nuevos: bool) -> None:
        estilo_actual = widget.styleSheet()  # Consulta el stylesheet aplicado directamente al componente.
        if not estilo_actual.strip(): return  # Omite controles dependientes solo del QSS global.

        estilo_base = widget.property(self.PROPIEDAD_ESTILO_BASE)  # Recupera la referencia original.
        estilo_aplicado = widget.property(self.PROPIEDAD_ESTILO_APLICADO)  # Recupera la última traducción.

        if solo_nuevos and isinstance(estilo_base, str) and isinstance(estilo_aplicado, str) and estilo_actual == estilo_aplicado: return  # Omite componentes ya procesados.
        if not isinstance(estilo_base, str) or (isinstance(estilo_aplicado, str) and estilo_actual != estilo_aplicado):
            estilo_base = estilo_actual  # Considera una hoja nueva o modificada como referencia original.
            widget.setProperty(self.PROPIEDAD_ESTILO_BASE, estilo_base)  # Conserva esa referencia.

        estilo_nuevo = self._traducir_estilo_local(estilo_base, paleta)  # Adapta colores estructurales históricos.
        widget.setProperty(self.PROPIEDAD_ESTILO_APLICADO, estilo_nuevo)  # Conserva la transformación producida.
        if estilo_actual != estilo_nuevo: widget.setStyleSheet(estilo_nuevo)  # Evita repintados innecesarios.

    def _traducir_estilo_local(self, estilo: str, p: dict) -> str:
        reemplazos_especificos = (
            ("selection-color: #1e1e2e", f"selection-color: {p['texto_inverso']}"),
            ("color: #1e1e2e", f"color: {p['texto_inverso']}"),
            ("color: #ffffff", f"color: {p['texto']}"),
            ("border: 1px solid #cdd6f4", f"border: 1px solid {p['borde_fuerte']}"),
            ("border: 1px solid #313244", f"border: 1px solid {p['borde']}"),
            ("border: 1px solid #45475a", f"border: 1px solid {p['borde_fuerte']}"),
            ("border: 1px solid #585b70", f"border: 1px solid {p['superficie_presionada']}"),
            ("border-bottom: 1px solid #313244", f"border-bottom: 1px solid {p['borde']}"),
            ("border-top: 1px solid #313244", f"border-top: 1px solid {p['borde']}"),
            ("border-right: 1px solid #313244", f"border-right: 1px solid {p['borde']}"),
            ("border-color: #313244", f"border-color: {p['borde']}"),
            ("border-color: #45475a", f"border-color: {p['borde_fuerte']}"),
            ("border-color: #585b70", f"border-color: {p['superficie_presionada']}"),
            ("border-color: #89b4fa", f"border-color: {p['acento']}"),
            ("background-color: #6c7086", f"background-color: {p['superficie_presionada']}"),
            ("color: #cdd6f4", f"color: {p['texto']}"),
            ("color: #a6adc8", f"color: {p['texto_secundario']}"),
            ("color: #6c7086", f"color: {p['texto_deshabilitado']}"),
        )  # Ejecuta primero sustituciones dependientes de la propiedad CSS.

        for original, nuevo in reemplazos_especificos: estilo = estilo.replace(original, nuevo).replace(original.upper(), nuevo)  # Aplica traducciones contextuales.

        reemplazos_generales = {
            "#1e1e2e": p["fondo"],
            "#181825": p["panel"],
            "#11111b": p["editor"],
            "#1c1c2c": p["superficie_suave"],
            "#313244": p["superficie"],
            "#363649": p["superficie_suave"],
            "#242438": p["superficie_suave"],
            "#45475a": p["superficie_hover"],
            "#585b70": p["superficie_presionada"],
            "#242536": p["fondo_deshabilitado"],
            "#2b2d42": p["fondo_deshabilitado"],
            "#3b3d56": p["borde_deshabilitado"],
            "#cdd6f4": p["texto"],
            "#a6adc8": p["texto_secundario"],
            "#6c7086": p["texto_deshabilitado"],
            "#89b4fa": p["acento"],
            "#b4befe": p["acento_hover"],
        }  # Mantiene fuera los colores semánticos, administrados por el aplicador especializado.

        for original, nuevo in reemplazos_generales.items(): estilo = estilo.replace(original, nuevo).replace(original.upper(), nuevo)  # Traduce los colores estructurales restantes.
        return estilo  # Devuelve la hoja adaptada.

    # ========================================================
    # Editor
    # ========================================================

    def _aplicar_fuente_editor(self, familia: str, tamano: int, espacios: int) -> None:
        editor = self.ventana.editor_codigo  # Recupera el editor.
        fuente_editor = editor.font()  # Copia la fuente vigente.
        fuente_editor.setFamily(familia)  # Aplica la familia independiente.
        fuente_editor.setPointSize(tamano)  # Aplica su tamaño.
        editor.setFont(fuente_editor)  # Actualiza QPlainTextEdit.
        metricas = QFontMetricsF(editor.font())  # Obtiene dimensiones definitivas.
        editor.setTabStopDistance(metricas.horizontalAdvance(" ") * espacios)  # Calcula la distancia visual de Tab.
        editor.actualizar_ancho_area_numeros_linea()  # Recalcula el gutter.
        editor.viewport().update()  # Solicita el redibujado.

    def _aplicar_apariencia_editor(self, tema_id: str, cambio_tema: bool) -> None:
        editor = self.ventana.editor_codigo  # Recupera el editor principal.
        paleta = obtener_tema(tema_id)  # Recupera sus colores.
        editor.COLOR_SUGERENCIA_IA = paleta["texto_deshabilitado"]  # Adapta el ghost text.
        editor.COLOR_PLACEHOLDER = paleta["texto_secundario"]  # Adapta el placeholder.

        paleta_editor = editor.palette()  # Recupera la QPalette actual.
        paleta_editor.setColor(QPalette.ColorRole.PlaceholderText, QColor(paleta["texto_secundario"]))  # Modifica exclusivamente PlaceholderText.
        editor.setPalette(paleta_editor)  # Aplica la paleta actualizada.

        resaltador = getattr(self.ventana, "resaltador_sintaxis", None)  # Recupera el resaltador.
        if cambio_tema and resaltador is not None and hasattr(resaltador, "aplicar_tema"): resaltador.aplicar_tema(tema_id)  # Recolorea el documento cuando cambia de tema.

        editor.area_numeros_linea.update()  # Redibuja el gutter.
        editor.viewport().update()  # Actualiza código y ghost text.

    # ========================================================
    # Iconos
    # ========================================================

    def _aplicar_iconos_tema(self, tema_id: str) -> None:
        aplicacion = QApplication.instance()  # Recupera ventanas superiores.
        if aplicacion is None: return  # Evita operar durante el cierre.

        for ventana in aplicacion.topLevelWidgets():
            barra = getattr(ventana, "barra_titulo", None)  # Recupera BarraTitulo cuando exista.
            if barra is not None: self._aplicar_iconos_barra(barra, tema_id, bool(getattr(ventana, "en_pantalla_completa", False)))  # Sincroniza sus recursos.

        editor = self.ventana.editor_codigo  # Recupera botones rápidos.
        self._establecer_icono_simple(editor.boton_pegar, editor.ruta_iconos, "Pegar.png", tema_id)  # Utiliza Pegar_Claro.
        self._establecer_icono_simple(editor.boton_ejemplos, editor.ruta_iconos, "Ejemplos.png", tema_id)  # Utiliza Ejemplos_Claro.
        self._aplicar_recursos_declarados(self.ventana, tema_id)  # Atiende botones auxiliares como Advertencia.

    def _aplicar_recursos_declarados(self, raiz: QWidget, tema_id: str) -> None:
        botones = [raiz] if isinstance(raiz, QPushButton) else []  # Incluye la propia raíz cuando fuera un botón.
        botones.extend(raiz.findChildren(QPushButton))  # Añade todos los botones descendientes.

        for boton in botones:
            nombre = boton.property("recurso_tema")  # Consulta si el control declaró un archivo dependiente del tema.
            if not isinstance(nombre, str) or not nombre: continue  # Omite controles convencionales.
            ruta_iconos = getattr(self.ventana.panel_resultados, "ruta_iconos", None)  # Recupera la carpeta oficial de recursos.
            if ruta_iconos is None: continue  # Protege versiones futuras sin esa propiedad.
            ruta = resolver_icono_tema(ruta_iconos, nombre, tema_id)  # Resuelve automáticamente la variante.
            if ruta.exists(): boton.setIcon(QIcon(str(ruta)))  # Sustituye únicamente el icono.

    def _establecer_icono_simple(self, boton, ruta_iconos, nombre_archivo: str, tema_id: str) -> None:
        ruta = resolver_icono_tema(ruta_iconos, nombre_archivo, tema_id)  # Resuelve la variante apropiada.
        if ruta.exists(): boton.setIcon(QIcon(str(ruta)))  # Sustituye exclusivamente el recurso.

    def _aplicar_iconos_barra(self, barra, tema_id: str, pantalla_completa: bool) -> None:
        ruta_iconos = barra.ruta_iconos  # Recupera la carpeta oficial.
        modo_claro = tema_utiliza_iconos_claros(tema_id)  # Determina si se utilizan recursos oscuros.

        def normal(nombre: str):
            return resolver_icono_tema(ruta_iconos, nombre, tema_id)  # Busca una variante clara automáticamente.

        def hover(nombre_normal: str, nombre_hover: str):
            return normal(nombre_normal) if modo_claro else ruta_iconos / nombre_hover  # En modo claro reutiliza el icono oscuro sobre un fondo hover también claro.

        if barra.boton_configuracion is not None: barra.boton_configuracion.establecer_iconos(normal("Engrane.png"), hover("Engrane.png", "Engrane_Hover.png"), hover("Engrane.png", "Engrane_Hover.png"))
        if barra.boton_minimizar is not None: barra.boton_minimizar.establecer_iconos(normal("Minimizar.png"), hover("Minimizar.png", "Minimizar_hover.png"), hover("Minimizar.png", "Minimizar_hover.png"))
        if barra.boton_media_pantalla is not None: barra.boton_media_pantalla.establecer_iconos(normal("Pantalla_Dividida.png"), hover("Pantalla_Dividida.png", "Pantalla_Dividida_hover.png"), hover("Pantalla_Dividida.png", "Pantalla_Dividida_hover.png"))

        if barra.boton_pantalla_completa is not None:
            nombre_normal = "Salir_pantalla_completa.png" if pantalla_completa else "Pantalla_completa.png"  # Determina la operación disponible.
            nombre_hover = "Salir_pantalla_completa_hover.png" if pantalla_completa else "Pantalla_completa_hover.png"  # Recupera la variante oscura histórica.
            barra.boton_pantalla_completa.establecer_iconos(normal(nombre_normal), hover(nombre_normal, nombre_hover), hover(nombre_normal, nombre_hover))  # Sincroniza fullscreen.

        if barra.boton_cerrar is not None: barra.boton_cerrar.establecer_iconos(normal("Cerrar.png"), ruta_iconos / "Cerrar_activo.png", ruta_iconos / "Cerrar_activo.png")  # Conserva blanco sobre rojo durante hover.

    # ========================================================
    # Ventanas creadas posteriormente
    # ========================================================

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.ventana and evento.type() in (QEvent.Type.WindowStateChange, QEvent.Type.Show): QTimer.singleShot(0, self._refrescar_iconos_actuales)  # Corrige fullscreen o restauraciones.

        if self._tema_aplicado is not None and isinstance(objeto, QWidget) and objeto.isWindow() and evento.type() == QEvent.Type.Show:
            if objeto.property(self.PROPIEDAD_TEMA_PREPARADO) != self._tema_aplicado: QTimer.singleShot(0, lambda ventana=objeto: self._tematizar_ventana_nueva(ventana))  # Mantiene un respaldo para ventanas que no utilizaron preparar_ventana().

        return super().eventFilter(objeto, evento)  # Conserva el procesamiento habitual de Qt.

    def _tematizar_ventana_nueva(self, ventana: QWidget) -> None:
        if self._tema_aplicado is None: return  # Evita trabajar antes de aplicar la primera preferencia.
        self.preparar_ventana(ventana)  # Utiliza exactamente el mismo flujo centralizado.

    def _refrescar_iconos_actuales(self) -> None:
        if self._tema_aplicado is not None: self._aplicar_iconos_tema(self._tema_aplicado)  # Reaplica exclusivamente recursos gráficos.