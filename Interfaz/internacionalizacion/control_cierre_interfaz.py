# ============================================================
# Archivo: control_cierre_interfaz.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Cierra las partes visuales de internacionalización que no
# pertenecen al compilador formal:
# - Salidas sintácticas extensas.
# - Etiqueta raíz de los árboles.
# - Opciones y descripciones de temas.
# - Paneles Editor, Resultados y Asistencia de IA.
# - Reanclaje del botón Guardar PNG durante zoom y desplazamiento.
# - Diálogos principales de análisis, exportación y guardado.
# - Resumen de cambios de Configuración.
#
# No modifica IP, MASK, HOSTS, NAME, los tipos de token ni los
# objetos estructurados generados por el compilador.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QRectF, QTimer
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton

from AsistenteIA.infraestructura.configuracion import MODELO_IA
from AsistenteIA.infraestructura.gestor_instalacion_ia import VERSION_OLLAMA
from Interfaz.resultados.visor_arbol_sintactico import VistaArbol
from Interfaz.internacionalizacion.traductor_sintaxis import TraductorSintaxis
from Motor.configuracion.catalogo_temas import (
    MODO_CLARO,
    MODO_OSCURO,
    modo_del_tema,
    obtener_tema,
    obtener_temas_por_modo,
)
from Motor.exportacion.exportador_resultados import exportar_reporte_txt, exportar_vlsm_excel
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class ControlCierreInterfaz(QObject):
    MAPA_EDITOR = {
        "Editor": "configuracion.editor.titulo",
        "Personaliza la visualización y algunos comportamientos del editor donde escribes el código fuente de TecNet Finder.": "configuracion.editor.descripcion",
        "Visualización del contenido": "configuracion.editor.visualizacion.titulo",
        "Controla cómo se distribuye el código dentro del área visible y qué accesos rápidos aparecen sobre el editor.": "configuracion.editor.visualizacion.descripcion",
        "Ajustar automáticamente las líneas largas": "configuracion.editor.ajuste_linea",
        "Mostrar los botones rápidos Ampliar y Ejemplos": "configuracion.editor.botones_rapidos",
        "Tipografía": "configuracion.editor.tipografia.titulo",
        "Elige la familia y el tamaño utilizados para escribir y revisar las instrucciones del lenguaje.": "configuracion.editor.tipografia.descripcion",
        "Familia de fuente:": "configuracion.editor.familia",
        "Tamaño de fuente:": "configuracion.editor.tamano",
        "Tabulación": "configuracion.editor.tabulacion.titulo",
        "Define cuánto espacio visual representa una tabulación dentro del editor.": "configuracion.editor.tabulacion.descripcion",
        "Ancho de tabulación:": "configuracion.editor.tabulacion.ancho",
    }

    MAPA_RESULTADOS = {
        "Resultados y navegación": "configuracion.resultados.titulo",
        "Personaliza qué muestra TecNet Finder después de compilar y cómo presenta e interactúa con las advertencias.": "configuracion.resultados.descripcion",
        "Navegación después de compilar": "configuracion.resultados.navegacion.titulo",
        "Decide de forma independiente cuándo TecNet Finder debe cambiar automáticamente la vista después de una compilación.": "configuracion.resultados.navegacion.descripcion",
        "Ir automáticamente a Errores / Advertencias cuando existan errores": "configuracion.resultados.navegacion.errores",
        "Ir automáticamente a Tabla VLSM cuando se generen subredes válidas": "configuracion.resultados.navegacion.vlsm",
        "Presentación de advertencias": "configuracion.resultados.advertencias.titulo",
        "Elige cómo mostrar las advertencias de una compilación válida. Activar una modalidad desactiva automáticamente la otra.": "configuracion.resultados.advertencias.descripcion",
        "Mostrar advertencias debajo de Tabla VLSM": "configuracion.resultados.advertencias.compactas",
        "Mostrar advertencias en una ventana independiente": "configuracion.resultados.advertencias.ventana",
        "Interacción con advertencias": "configuracion.resultados.interaccion.titulo",
        "En la ventana independiente puedes hacer doble clic sobre una advertencia para ir directamente a su ubicación en el código.": "configuracion.resultados.interaccion.descripcion",
        "Cerrar la ventana de advertencias al ir al código": "configuracion.resultados.interaccion.cerrar",
        "Interacción con la ventana principal": "configuracion.resultados.ventana_principal.titulo",
        "Decide si la ventana independiente de advertencias debe impedir temporalmente utilizar TecNet Finder. Si se desactiva, podrás consultar las advertencias y la ventana principal al mismo tiempo.": "configuracion.resultados.ventana_principal.descripcion",
        "Bloquear TecNet Finder mientras la ventana de advertencias esté abierta": "configuracion.resultados.ventana_principal.bloquear",
    }

    MAPA_IA = {
        "Asistencia de IA": "configuracion.ia.titulo",
        "Administra las funciones inteligentes de TecNet Finder. El procesamiento se realiza localmente en este equipo.": "configuracion.ia.descripcion",
        "Estado del componente": "configuracion.ia.estado.titulo",
        "Funciones de IA": "configuracion.ia.funciones.titulo",
        "Activar autocompletado con IA": "configuracion.ia.autocompletado",
        "Mejorar soluciones de diagnósticos con IA": "configuracion.ia.diagnosticos",
        "Administración del componente": "configuracion.ia.administracion.titulo",
        "Instala o elimina el runtime y el modelo utilizados exclusivamente por TecNet Finder. El compilador principal funciona aunque este componente no se encuentre instalado.": "configuracion.ia.administracion.descripcion",
        "Instalar componente": "configuracion.ia.instalar",
        "Desinstalar componente": "configuracion.ia.desinstalar",
        "Preparando operación...": "configuracion.ia.preparando",
    }

    MAPA_SECCIONES_CAMBIOS = {
        "Ventana y apariencia": "configuracion.seccion.ventana",
        "Editor": "configuracion.seccion.editor",
        "Resultados y navegación": "configuracion.seccion.resultados",
        "Asistencia de IA": "configuracion.seccion.ia",
    }

    MAPA_CAMBIOS = {
        "Iniciar TecNet Finder maximizado": "configuracion.cambio.iniciar_maximizado",
        "Recordar el estado de la ventana al cerrar": "configuracion.cambio.recordar_estado_ventana",
        "Tema de la aplicación": "configuracion.cambio.tema",
        "Familia de fuente de la interfaz": "configuracion.cambio.fuente_interfaz",
        "Tamaño base de la interfaz": "configuracion.cambio.tamano_interfaz",
        "Idioma de la interfaz": "configuracion.cambio.idioma",
        "Abrir Configuración en la última sección visitada": "configuracion.cambio.recordar_seccion",
        "Ajuste automático de líneas largas": "configuracion.cambio.ajuste_linea",
        "Botones rápidos Ampliar y Ejemplos": "configuracion.cambio.botones_rapidos",
        "Familia de fuente del editor": "configuracion.cambio.fuente_editor",
        "Tamaño de fuente del editor": "configuracion.cambio.tamano_editor",
        "Ancho de tabulación": "configuracion.cambio.tabulacion",
        "Navegación automática hacia Errores / Advertencias": "configuracion.cambio.navegacion_errores",
        "Navegación automática hacia Tabla VLSM": "configuracion.cambio.navegacion_vlsm",
        "Mostrar advertencias debajo de Tabla VLSM": "configuracion.cambio.advertencias_compactas",
        "Mostrar advertencias en una ventana independiente": "configuracion.cambio.advertencias_ventana",
        "Cerrar la ventana de advertencias al ir al código": "configuracion.cambio.cerrar_advertencias",
        "Bloquear TecNet Finder mientras la ventana de advertencias esté abierta": "configuracion.cambio.bloquear_advertencias",
        "Autocompletado con IA": "configuracion.cambio.ia_autocompletado",
        "Mejora de soluciones de diagnósticos con IA": "configuracion.cambio.ia_diagnosticos",
    }

    def __init__(self, ventana_principal):
        super().__init__(ventana_principal)
        self.ventana = ventana_principal
        self.gestor = GestorTraducciones("es")
        self.traductor_sintaxis = TraductorSintaxis(self.gestor)
        self._registros_configuracion: dict[int, list[tuple[object, str, str]]] = {}
        self._vistas_arbol: list[VistaArbol] = []
        self._dialogos_principales_preparados = False
        self._preparar_dialogos_principales()

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)

    def establecer_idioma(self, idioma: str) -> bool:
        if not self.gestor.establecer_idioma(idioma):
            return False

        self.aplicar_principal()
        return True

    # ========================================================
    # Diálogos principales
    # ========================================================

    def _preparar_dialogos_principales(self) -> None:
        if self._dialogos_principales_preparados:
            return

        panel = self.ventana.panel_resultados

        # En este punto los botones conservan únicamente las conexiones creadas
        # por VentanaPrincipal/PanelResultados. Se sustituyen por equivalentes
        # que mantienen la lógica estable y resuelven el texto con el idioma activo.
        for boton, accion in (
            (panel.boton_analizar, self._analizar_codigo),
            (panel.boton_exportar_excel, self._exportar_excel),
            (panel.boton_exportar_reporte, self._exportar_reporte),
        ):
            try:
                boton.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            boton.clicked.connect(accion)

        self._dialogos_principales_preparados = True

    def _analizar_codigo(self, *_argumentos) -> None:
        codigo_fuente = self.ventana.editor_codigo.toPlainText()

        if not codigo_fuente.strip():
            QMessageBox.warning(
                self.ventana,
                self._t("dialogos.entrada_vacia.titulo"),
                self._t("dialogos.entrada_vacia.mensaje"),
            )
            return

        try:
            resultado = self.ventana.flujo.analizar(codigo_fuente)
        except Exception as error:
            self.ventana._limpiar_resultados_conservando_entrada()
            self.ventana._mostrar_estado_error_interno()
            QMessageBox.critical(
                self.ventana,
                self._t("dialogos.error_interno.titulo"),
                self._t("dialogos.error_interno.mensaje", error=error),
            )
            return

        self.ventana.ultimo_resultado = resultado
        self.ventana.panel_diagnosticos.mostrar_diagnosticos(resultado.diagnosticos)
        self.ventana.editor_codigo.mostrar_diagnosticos(resultado.diagnosticos)
        self.ventana.panel_resultados.mostrar_resultado(resultado)
        self.ventana._actualizar_estado(resultado)

    def _exportar_excel(self, *_argumentos) -> None:
        panel = self.ventana.panel_resultados

        if panel.resultado_actual is None or not panel.resultado_actual.subredes_vlsm:
            panel._mostrar_mensaje(
                self._t("dialogos.exportar_excel.titulo"),
                self._t("dialogos.exportar_excel.sin_datos"),
                "Advertencia.png",
            )
            return

        ruta, _filtro = QFileDialog.getSaveFileName(
            panel,
            self._t("dialogos.exportar_excel.guardar_titulo"),
            "TecNetFinder_VLSM.xlsx",
            self._t("dialogos.exportar_excel.filtro"),
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"

        try:
            ruta_guardada = exportar_vlsm_excel(panel.resultado_actual, ruta)
        except Exception as error:
            panel._mostrar_mensaje(
                self._t("dialogos.exportacion.error_titulo"),
                self._t("dialogos.exportar_excel.error", error=error),
                "Error.png",
            )
            return

        panel._mostrar_mensaje(
            self._t("dialogos.exportacion.completada_titulo"),
            self._t("dialogos.exportar_excel.completada", ruta=ruta_guardada),
            "Correcto.png",
        )

    def _exportar_reporte(self, *_argumentos) -> None:
        panel = self.ventana.panel_resultados

        if panel.resultado_actual is None:
            panel._mostrar_mensaje(
                self._t("dialogos.exportar_reporte.titulo"),
                self._t("dialogos.exportar_reporte.sin_datos"),
                "Advertencia.png",
            )
            return

        ruta, _filtro = QFileDialog.getSaveFileName(
            panel,
            self._t("dialogos.exportar_reporte.guardar_titulo"),
            "TecNetFinder_Reporte.txt",
            self._t("dialogos.exportar_reporte.filtro"),
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".txt"):
            ruta += ".txt"

        try:
            ruta_guardada = exportar_reporte_txt(
                panel.codigo_fuente_resultado,
                panel.resultado_actual,
                ruta,
            )
        except Exception as error:
            panel._mostrar_mensaje(
                self._t("dialogos.exportacion.error_titulo"),
                self._t("dialogos.exportar_reporte.error", error=error),
                "Error.png",
            )
            return

        panel._mostrar_mensaje(
            self._t("dialogos.exportacion.completada_titulo"),
            self._t("dialogos.exportar_reporte.completada", ruta=ruta_guardada),
            "Correcto.png",
        )

    # ========================================================
    # Ventana principal
    # ========================================================

    def aplicar_principal(self) -> None:
        self._aplicar_sintaxis_visible()
        self._preparar_arboles_graficos()

    def _aplicar_sintaxis_visible(self) -> None:
        panel = self.ventana.panel_resultados
        resultado = panel.resultado_actual or self.ventana.ultimo_resultado

        if resultado is None:
            return

        sintactico = resultado.resultado_sintactico
        panel.texto_producciones.setPlainText(
            self.traductor_sintaxis.producciones(sintactico.bloques)
        )
        panel.texto_derivacion.setPlainText(
            self.traductor_sintaxis.derivacion(sintactico.bloques)
        )
        panel.visor_arbol.texto_arbol.setPlainText(
            self.traductor_sintaxis.arbol_textual(sintactico.arboles)
        )

    def _preparar_arboles_graficos(self) -> None:
        visor = self.ventana.panel_resultados.visor_arbol

        for vista in visor.findChildren(VistaArbol):
            self._preparar_reanclaje(vista)
            self._traducir_raiz_escena(vista)

    def _preparar_reanclaje(self, vista: VistaArbol) -> None:
        if not any(vista_registrada is vista for vista_registrada in self._vistas_arbol):
            self._vistas_arbol.append(vista)
            vista.installEventFilter(self)
            vista.viewport().installEventFilter(self)

            for barra in (vista.horizontalScrollBar(), vista.verticalScrollBar()):
                barra.rangeChanged.connect(
                    lambda *_argumentos, v=vista: self._programar_reanclaje(v)
                )
                barra.valueChanged.connect(
                    lambda *_argumentos, v=vista: self._programar_reanclaje(v)
                )

        self._preparar_guardado_arbol(vista)
        self._programar_reanclaje(vista)

    def _preparar_guardado_arbol(self, vista: VistaArbol) -> None:
        boton = vista.boton_superpuesto

        if boton is None:
            return

        boton.setToolTip(self._t("resultados.arbol.guardar_png"))
        boton.setAccessibleName(self._t("resultados.arbol.guardar_png"))

        if boton.property("i18n_guardado_reconectado"):
            return

        try:
            boton.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass

        boton.clicked.connect(
            lambda _marcado=False, v=vista: self._guardar_arbol_png(v)
        )
        boton.setProperty("i18n_guardado_reconectado", True)

    def _guardar_arbol_png(self, vista: VistaArbol) -> None:
        try:
            escena = vista.scene()
        except RuntimeError:
            self._descartar_vista(vista)
            return

        if escena is None:
            return

        nombre = "1"
        for item in escena.items():
            if not hasattr(item, "data"):
                continue

            etiqueta_formal = item.data(1)
            if isinstance(etiqueta_formal, str) and etiqueta_formal.startswith("BloqueRed:"):
                candidato = etiqueta_formal.split(":", 1)[1].strip()
                if candidato:
                    nombre = candidato
                    break

        ruta, _filtro = QFileDialog.getSaveFileName(
            self.ventana,
            self._t("dialogos.arbol.guardar_titulo"),
            self._t("dialogos.arbol.nombre_archivo", nombre=nombre),
            self._t("dialogos.arbol.filtro"),
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".png"):
            ruta += ".png"

        limites = escena.itemsBoundingRect().adjusted(-30, -30, 30, 30)
        ancho = max(int(limites.width()), 1)
        alto = max(int(limites.height()), 1)
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        color_fondo = escena.backgroundBrush().color()
        imagen.fill(
            color_fondo
            if color_fondo.isValid()
            else QColor("#181825")
        )
        pintor = QPainter(imagen)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        escena.render(pintor, QRectF(0, 0, ancho, alto), limites)
        pintor.end()
        imagen.save(ruta, "PNG")

    def _descartar_vista(self, vista: VistaArbol) -> None:
        self._vistas_arbol = [
            vista_registrada
            for vista_registrada in self._vistas_arbol
            if vista_registrada is not vista
        ]

    def _programar_reanclaje(self, vista: VistaArbol) -> None:
        QTimer.singleShot(0, lambda v=vista: self._reanclar_boton_arbol(v))

    def _reanclar_boton_arbol(self, vista: VistaArbol) -> None:
        if vista is None or vista.boton_superpuesto is None:
            return

        try:
            vista._posicionar_boton_superpuesto()
            vista.boton_superpuesto.raise_()
        except RuntimeError:
            self._descartar_vista(vista)  # Descarta vistas que Qt ya destruyó al reemplazar una compilación anterior.

    def eventFilter(self, objeto, evento):
        if evento.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.Move,
            QEvent.Type.LayoutRequest,
            QEvent.Type.Wheel,
        ):
            for vista in tuple(self._vistas_arbol):
                try:
                    coincide = objeto is vista or objeto is vista.viewport()
                except RuntimeError:
                    self._descartar_vista(vista)
                    continue

                if coincide:
                    self._programar_reanclaje(vista)
                    break

        return super().eventFilter(objeto, evento)

    def _traducir_raiz_escena(self, vista: VistaArbol) -> None:
        escena = vista.scene()
        if escena is None:
            return

        for item in escena.items():
            if not hasattr(item, "toPlainText") or not hasattr(item, "setPlainText"):
                continue

            etiqueta_formal = item.data(1)
            texto = item.toPlainText()

            if item.data(0) != "raiz_sintactica":
                if texto == "BloqueRed" or texto.startswith("BloqueRed:"):
                    item.setData(0, "raiz_sintactica")
                    item.setData(1, texto)  # Conserva la etiqueta formal para futuros cambios de idioma.
                    etiqueta_formal = texto
                else:
                    continue

            if not isinstance(etiqueta_formal, str):
                continue

            nombre = ""
            if etiqueta_formal.startswith("BloqueRed:"):
                nombre = etiqueta_formal.split(":", 1)[1].strip()

            rectangulo_anterior = item.boundingRect()
            centro_x = item.pos().x() + rectangulo_anterior.width() / 2.0
            nuevo_texto = (
                self._t("sintaxis.arbol.raiz_nombre", nombre=nombre)
                if nombre
                else self._t("sintaxis.arbol.raiz")
            )
            item.setPlainText(nuevo_texto)
            rectangulo_nuevo = item.boundingRect()
            item.setPos(
                centro_x - rectangulo_nuevo.width() / 2.0,
                item.pos().y(),
            )
            break

    # ========================================================
    # Configuración
    # ========================================================

    def preparar_configuracion(self, ventana) -> None:
        identificador = id(ventana)

        if not getattr(ventana, "_resumen_cambios_i18n_instalado", False):
            ventana._mostrar_resumen_cambios = (
                lambda cambios, v=ventana: self._mostrar_resumen_cambios_traducido(v, cambios)
            )
            ventana._resumen_cambios_i18n_instalado = True

        if identificador not in self._registros_configuracion:
            registros: list[tuple[object, str, str]] = []
            self._registrar_panel(
                ventana.panel_editor,
                self.MAPA_EDITOR,
                registros,
            )
            self._registrar_panel(
                ventana.panel_resultados,
                self.MAPA_RESULTADOS,
                registros,
            )
            self._registrar_panel(
                ventana.panel_ia,
                self.MAPA_IA,
                registros,
            )
            self._registros_configuracion[identificador] = registros

            panel_tema = ventana.panel_ventana
            panel_tema.selector_modo.valor_cambiado.connect(
                lambda *_args, v=ventana: QTimer.singleShot(
                    0,
                    lambda: self.aplicar_configuracion(v),
                )
            )
            panel_tema.selector_variante.valor_cambiado.connect(
                lambda *_args, v=ventana: QTimer.singleShot(
                    0,
                    lambda: self.aplicar_configuracion(v),
                )
            )

            ventana.panel_ia.operacion_cambiada.connect(
                lambda *_args, v=ventana: QTimer.singleShot(
                    0,
                    lambda: self.aplicar_configuracion(v),
                )
            )
            ventana.panel_ia.servicio_cambiado.connect(
                lambda *_args, v=ventana: QTimer.singleShot(
                    0,
                    lambda: self.aplicar_configuracion(v),
                )
            )
            ventana.panel_ia.configuracion_modificada.connect(
                lambda *_args, v=ventana: QTimer.singleShot(
                    0,
                    lambda: self.aplicar_configuracion(v),
                )
            )

        self.aplicar_configuracion(ventana)

    def _mostrar_resumen_cambios_traducido(self, ventana, cambios: dict[str, list[str]]) -> None:
        gestor = getattr(ventana, "gestor_traducciones", self.gestor)

        def traducir(clave: str, **variables) -> str:
            return gestor.traducir(clave, **variables)

        cantidad = sum(len(elementos) for elementos in cambios.values())
        secciones = len(cambios)
        bloques = []

        for seccion, elementos in cambios.items():
            clave_seccion = self.MAPA_SECCIONES_CAMBIOS.get(seccion)
            nombre_seccion = traducir(clave_seccion) if clave_seccion else seccion
            nombres_elementos = []

            for elemento in elementos:
                clave_elemento = self.MAPA_CAMBIOS.get(elemento)
                nombres_elementos.append(
                    traducir(clave_elemento) if clave_elemento else elemento
                )

            bloques.append(
                nombre_seccion
                + ":\n"
                + "\n".join(f"• {elemento}" for elemento in nombres_elementos)
            )

        dialogo = QMessageBox(ventana)
        dialogo.setWindowTitle(traducir("configuracion.resumen.titulo"))
        dialogo.setIcon(QMessageBox.Icon.Information)
        dialogo.setText(
            traducir(
                "configuracion.resumen.texto",
                cantidad=cantidad,
                secciones=secciones,
            )
        )
        dialogo.setInformativeText("\n\n".join(bloques))
        dialogo.setStandardButtons(QMessageBox.StandardButton.Ok)
        boton = dialogo.button(QMessageBox.StandardButton.Ok)

        if boton is not None:
            boton.setText(traducir("comun.aceptar"))
            boton.setObjectName("BotonPrincipal")

        dialogo.exec()

    def _registrar_panel(self, panel, mapa: dict[str, str], registros: list) -> None:
        for etiqueta in panel.findChildren(QLabel):
            texto = " ".join(etiqueta.text().split())
            clave = mapa.get(texto)
            if clave is not None:
                registros.append((etiqueta, clave, "text"))

        for boton in panel.findChildren(QPushButton):
            texto = " ".join(boton.text().split())
            clave = mapa.get(texto)
            if clave is not None:
                registros.append((boton, clave, "text"))

            accesible = " ".join(boton.accessibleName().split())
            clave_accesible = mapa.get(accesible)
            if clave_accesible is not None:
                registros.append((boton, clave_accesible, "accessible"))

    def aplicar_configuracion(self, ventana) -> None:
        registros = self._registros_configuracion.get(id(ventana), [])

        for widget, clave, atributo in registros:
            texto = self._t(clave)

            if atributo == "text":
                widget.setText(texto)
            elif atributo == "accessible":
                widget.setAccessibleName(texto)

        self._aplicar_tema_configuracion(ventana)
        self._aplicar_estado_ia(ventana)

    def _aplicar_tema_configuracion(self, ventana) -> None:
        panel = ventana.panel_ventana
        tema_id = ventana.preferencias_tema_temporales.tema()
        modo_id = modo_del_tema(tema_id)

        panel.selector_modo.limpiar_opciones()
        panel.selector_modo.agregar_opcion(
            self._t("configuracion.tema.modo.oscuro"),
            MODO_OSCURO,
        )
        panel.selector_modo.agregar_opcion(
            self._t("configuracion.tema.modo.claro"),
            MODO_CLARO,
        )
        panel.selector_modo.establecer_valor(modo_id, emitir=False)

        panel.selector_variante.limpiar_opciones()
        for tema in obtener_temas_por_modo(modo_id):
            panel.selector_variante.agregar_opcion(
                self._t(f"configuracion.tema.{tema['id']}.nombre"),
                tema["id"],
            )
        panel.selector_variante.establecer_valor(tema_id, emitir=False)
        panel.etiqueta_descripcion_tema.setText(
            self._t(f"configuracion.tema.{tema_id}.descripcion")
        )

    def _aplicar_estado_ia(self, ventana) -> None:
        panel = ventana.panel_ia
        instalado = panel.componente_ia.instalado()

        estado_instalacion = (
            self._t("configuracion.ia.estado.instalada")
            if instalado
            else self._t("configuracion.ia.estado.no_instalada")
        )
        panel.etiqueta_instalacion.setText(
            self._t(
                "configuracion.ia.estado.instalacion",
                estado=estado_instalacion,
            )
        )

        texto_actual = panel.etiqueta_ejecucion.text()
        transitorios = {
            "Estado de ejecución: Activando...": "configuracion.ia.estado.activando",
            "Estado de ejecución: Desactivando...": "configuracion.ia.estado.desactivando",
            "Estado de ejecución: Instalando componente...": "configuracion.ia.estado.instalando",
            "Estado de ejecución: Desinstalando componente...": "configuracion.ia.estado.desinstalando",
        }

        if texto_actual in transitorios:
            estado_ejecucion = self._t(transitorios[texto_actual])
        elif panel.operacion_en_curso:
            estado_ejecucion = self._t("configuracion.ia.estado.procesando")
        elif panel.asistencia_disponible and instalado:
            estado_ejecucion = self._t("configuracion.ia.estado.activa")
        elif instalado and panel._alguna_funcion_solicitada():
            estado_ejecucion = self._t("configuracion.ia.estado.no_disponible")
        else:
            estado_ejecucion = self._t("configuracion.ia.estado.inactiva")

        panel.etiqueta_ejecucion.setText(
            self._t(
                "configuracion.ia.estado.ejecucion",
                estado=estado_ejecucion,
            )
        )
        panel.etiqueta_modelo.setText(
            self._t("configuracion.ia.modelo", modelo=MODELO_IA)
        )
        panel.etiqueta_runtime.setText(
            self._t(
                "configuracion.ia.runtime",
                version=VERSION_OLLAMA,
            )
        )
        panel.etiqueta_ruta.setText(
            self._t(
                "configuracion.ia.ubicacion",
                ruta=panel.componente_ia.ruta_base,
            )
        )

        if not panel.operacion_en_curso:
            panel.etiqueta_progreso.setText(
                self._t("configuracion.ia.preparando")
            )
