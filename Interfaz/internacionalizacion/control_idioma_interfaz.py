# ============================================================
# Archivo: control_idioma_interfaz.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Aplica el idioma confirmado sobre la ventana principal sin
# modificar las palabras reservadas del DSL.
#
# Este bloque internacionaliza principalmente:
# - Encabezado y estado general.
# - Pestañas principales y de salida.
# - Acciones del área de entrada.
# - Encabezados VLSM y diagnósticos.
# - Controles de ventana y acciones flotantes del editor.
#
# IP, MASK, HOSTS y NAME permanecen intactos.
# ============================================================

from PySide6.QtWidgets import QLabel  # Permite localizar la etiqueta Entrada creada por PanelResultados.

from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones  # Resuelve las claves del idioma activo.


class ControlIdiomaInterfaz:
    def __init__(self, ventana):
        self.ventana = ventana  # Conserva la ventana principal cuyos textos serán actualizados.
        self.gestor = GestorTraducciones("es")  # Parte de un estado seguro y después recibe la preferencia confirmada.
        self.etiqueta_entrada = self._buscar_etiqueta_entrada()  # Conserva una referencia estable antes de que su texto deje de estar en español.

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)  # Abrevia la resolución de textos y variables nombradas.

    def _buscar_etiqueta_entrada(self):
        panel = self.ventana.panel_resultados  # Recupera la zona donde se construyó la etiqueta Entrada.
        for etiqueta in panel.findChildren(QLabel, "TituloSeccion"):
            if etiqueta.text() == "Entrada":
                return etiqueta  # Conserva exactamente el título del editor y no otros encabezados internos.
        return None  # Mantiene el sistema funcional si una versión futura reorganiza el panel.

    def aplicar(self, idioma: str) -> bool:
        if not self.gestor.establecer_idioma(idioma):
            return False  # Conserva intacta la interfaz ante un código no admitido.

        self._aplicar_encabezado_y_estado()  # Traduce la zona superior y el estado actual.
        self._aplicar_barra_titulo()  # Traduce controles y selector de ventana.
        self._aplicar_editor()  # Traduce ayudas de los botones flotantes.
        self._aplicar_panel_resultados()  # Traduce navegación, acciones y tablas principales.
        self._aplicar_panel_diagnosticos()  # Traduce pestañas y encabezados estructurados.
        return True  # Confirma que el idioma pudo aplicarse.

    def _aplicar_encabezado_y_estado(self) -> None:
        self.ventana.subtitulo_principal.setText(self._t("principal.subtitulo"))  # Traduce la descripción visible bajo TecNet Finder.
        self.actualizar_estado()  # Reconstruye el resumen con el idioma vigente y los datos actuales.

    def actualizar_estado(self) -> None:
        resultado = self.ventana.ultimo_resultado  # Recupera la última compilación, si existe.

        if resultado is None:
            clave = "principal.estado.error_interno" if self.ventana.etiqueta_estado.objectName() == "EstadoError" else "principal.estado.neutral"
            self.ventana.etiqueta_estado.setText(self._t(clave))  # Conserva correctamente estado neutral o fallo interno.
            return

        cantidad_errores = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad == "error")
        cantidad_advertencias = sum(1 for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia"))
        cantidad_subredes = len(resultado.subredes_vlsm)
        cantidad_bloques = len(resultado.bloques_validos)

        if cantidad_errores > 0:
            texto = self._t(
                "principal.estado.errores",
                errores=cantidad_errores,
                advertencias=cantidad_advertencias,
                subredes=cantidad_subredes,
            )
        elif cantidad_advertencias > 0:
            texto = self._t(
                "principal.estado.advertencias",
                advertencias=cantidad_advertencias,
                bloques=cantidad_bloques,
                subredes=cantidad_subredes,
            )
        else:
            texto = self._t(
                "principal.estado.correcto",
                bloques=cantidad_bloques,
                subredes=cantidad_subredes,
            )

        self.ventana.etiqueta_estado.setText(texto)  # Sustituye únicamente el texto y conserva el color calculado por VentanaPrincipal.

    def _establecer_ayuda(self, boton, clave: str) -> None:
        if boton is None:
            return
        texto = self._t(clave)
        boton.setToolTip(texto)
        boton.setAccessibleName(texto)  # Mantiene tooltip y accesibilidad sincronizados.

    def _aplicar_barra_titulo(self) -> None:
        barra = self.ventana.barra_titulo  # Recupera la barra personalizada ya construida.

        self._establecer_ayuda(barra.boton_configuracion, "principal.barra.configuracion")
        self._establecer_ayuda(barra.boton_minimizar, "principal.barra.minimizar")
        self._establecer_ayuda(barra.boton_cerrar, "comun.cerrar")

        if barra.boton_pantalla_completa is not None:
            clave = "principal.barra.salir_pantalla_completa" if self.ventana.en_pantalla_completa else "principal.barra.pantalla_completa"
            self._establecer_ayuda(barra.boton_pantalla_completa, clave)

        if barra.boton_media_pantalla is not None:
            if self.ventana.en_modo_ventana:
                texto = self._t("principal.barra.modo_ventana_activo")
            elif self.ventana.en_media_pantalla:
                lado = self._t("principal.selector.izquierda") if self.ventana.lado_media_pantalla == "izquierda" else self._t("principal.selector.derecha")
                texto = self._t("principal.barra.media_pantalla_activa", lado=lado)
            else:
                texto = self._t("principal.barra.elegir_modo")

            barra.boton_media_pantalla.setToolTip(texto)
            barra.boton_media_pantalla.setAccessibleName(self._t("principal.barra.elegir_modo"))

        selector = barra.selector_media_pantalla
        if selector is not None:
            selector.tarjeta_izquierda.etiqueta_titulo.setText(self._t("principal.selector.izquierda"))
            selector.tarjeta_derecha.etiqueta_titulo.setText(self._t("principal.selector.derecha"))
            selector.tarjeta_modo_ventana.etiqueta_titulo.setText(self._t("principal.selector.modo_ventana"))
            selector.tarjeta_maximizar.etiqueta_titulo.setText(self._t("principal.selector.maximizar"))

    def _aplicar_editor(self) -> None:
        editor = self.ventana.editor_codigo  # Recupera los dos controles flotantes del área de escritura.
        clave_ampliar = "principal.editor.restaurar" if self.ventana.editor_ampliado else "principal.editor.ampliar"
        self._establecer_ayuda(editor.boton_ampliar, clave_ampliar)
        self._establecer_ayuda(editor.boton_ejemplos, "principal.editor.ejemplos")
        # El placeholder conserva deliberadamente IP, MASK, HOSTS y NAME porque pertenece al DSL.

    def _aplicar_panel_resultados(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera pestañas, acciones y tablas de la ventana principal.

        pestanas_principales = (
            "principal.pestana.entrada_salida",
            "principal.pestana.tablas",
            "principal.pestana.sintaxis",
            "principal.pestana.fases_posteriores",
        )
        for indice, clave in enumerate(pestanas_principales):
            if indice < panel.count():
                panel.setTabText(indice, self._t(clave))

        pestanas_salida = (
            "principal.salida.resumen",
            "principal.salida.analisis",
            "principal.salida.vlsm",
            "principal.salida.errores_advertencias",
        )
        for indice, clave in enumerate(pestanas_salida):
            if indice < panel.pestanas_salida.count():
                panel.pestanas_salida.setTabText(indice, self._t(clave))

        if self.etiqueta_entrada is not None:
            self.etiqueta_entrada.setText(self._t("principal.entrada.titulo"))

        panel.boton_analizar.setText(self._t("principal.accion.compilar"))
        panel.boton_exportar_excel.setText(self._t("principal.accion.exportar_excel"))
        panel.boton_exportar_excel.setToolTip(self._t("principal.accion.exportar_excel.ayuda"))
        panel.boton_exportar_reporte.setText(self._t("principal.accion.exportar_reporte"))
        panel.boton_exportar_reporte.setToolTip(self._t("principal.accion.exportar_reporte.ayuda"))
        panel.boton_limpiar.setText(self._t("principal.accion.limpiar"))

        panel.tabla_vlsm.setHorizontalHeaderLabels(
            [
                self._t("principal.vlsm.red"),
                self._t("principal.vlsm.hosts_solicitados"),
                self._t("principal.vlsm.hosts_disponibles"),
                self._t("principal.vlsm.direccion_red"),
                "CIDR",
                self._t("principal.vlsm.mascara"),
                self._t("principal.vlsm.primera_ip"),
                self._t("principal.vlsm.ultima_ip"),
                "Broadcast",
            ]
        )  # CIDR, IP y Broadcast se conservan como términos técnicos.

        panel.titulo_advertencias_vlsm.setText(self._t("principal.vlsm.advertencias"))
        panel.tabla_advertencias_vlsm.setHorizontalHeaderLabels(
            [
                self._t("diagnosticos.codigo"),
                self._t("diagnosticos.mensaje"),
                self._t("diagnosticos.solucion"),
            ]
        )

    def _aplicar_panel_diagnosticos(self) -> None:
        panel = self.ventana.panel_diagnosticos  # Recupera las dos vistas de diagnósticos estructurados.
        if panel.count() >= 2:
            panel.setTabText(0, self._t("diagnosticos.detectados"))
            panel.setTabText(1, self._t("diagnosticos.catalogo"))

        panel.tabla_detectados.setHorizontalHeaderLabels(
            [
                self._t("diagnosticos.codigo"),
                self._t("diagnosticos.categoria"),
                self._t("diagnosticos.mensaje"),
                self._t("diagnosticos.linea"),
                self._t("diagnosticos.columna"),
                self._t("diagnosticos.solucion"),
            ]
        )
        panel.tabla_catalogo.setHorizontalHeaderLabels(
            [
                self._t("diagnosticos.codigo"),
                self._t("diagnosticos.tipo"),
                self._t("diagnosticos.estado"),
                self._t("diagnosticos.nombre"),
                self._t("diagnosticos.descripcion"),
                self._t("diagnosticos.solucion_sugerida"),
            ]
        )
