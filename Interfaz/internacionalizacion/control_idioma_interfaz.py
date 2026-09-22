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

from PySide6.QtWidgets import QLabel, QPushButton, QTabWidget  # Permite localizar y actualizar controles ya construidos.

from Interfaz.internacionalizacion.traductor_diagnosticos import TraductorDiagnosticos  # Traduce únicamente la representación visual de diagnósticos.
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones  # Resuelve las claves del idioma activo.


class ControlIdiomaInterfaz:
    def __init__(self, ventana):
        self.ventana = ventana  # Conserva la ventana principal cuyos textos serán actualizados.
        self.gestor = GestorTraducciones("es")  # Parte de un estado seguro y después recibe la preferencia confirmada.
        self.traductor_diagnosticos = TraductorDiagnosticos(self.gestor)  # Comparte el mismo idioma activo sin modificar los objetos formales del compilador.
        self.etiqueta_entrada = self._buscar_etiqueta_entrada()  # Conserva una referencia estable antes de que su texto deje de estar en español.
        self.etiqueta_titulo_resumen = None  # Conserva el encabezado principal del resumen.
        self.titulos_tarjetas_resumen = {}  # Relaciona cada métrica con su etiqueta visible.
        self.pestanas_tablas = None  # Conserva Tabla de tokens y Tabla de palabras reservadas.
        self.pestanas_sintaxis = None  # Conserva Producciones, Derivación y Árboles.
        self.pestanas_fases = None  # Conserva las tres fases posteriores.
        self._localizar_controles_internos()  # Localiza una sola vez los widgets estáticos creados por PanelResultados.

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)  # Abrevia la resolución de textos y variables nombradas.

    def _buscar_etiqueta_entrada(self):
        panel = self.ventana.panel_resultados  # Recupera la zona donde se construyó la etiqueta Entrada.
        for etiqueta in panel.findChildren(QLabel, "TituloSeccion"):
            if etiqueta.text() == "Entrada":
                return etiqueta  # Conserva exactamente el título del editor y no otros encabezados internos.
        return None  # Mantiene el sistema funcional si una versión futura reorganiza el panel.

    def _pestana_directa(self, contenedor):
        for pestanas in contenedor.findChildren(QTabWidget):
            if pestanas.parentWidget() is contenedor:
                return pestanas  # Devuelve únicamente el QTabWidget perteneciente directamente a la sección.
        return None  # Evita confundirlo con pestañas anidadas como las del visor de árboles.

    def _localizar_controles_internos(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera las vistas internas existentes.

        for etiqueta in panel.tab_resumen.findChildren(QLabel):
            if etiqueta.objectName() == "TituloResumen":
                self.etiqueta_titulo_resumen = etiqueta  # Conserva el encabezado único del resumen.
            elif etiqueta.objectName() == "TituloTarjeta":
                mapa = {
                    "Tokens reconocidos": "tokens",
                    "Bloques sintácticos": "bloques_sintacticos",
                    "Bloques semánticos": "bloques_semanticos",
                    "Subredes generadas": "subredes",
                    "Errores léxicos": "errores_lexicos",
                    "Errores sintácticos": "errores_sintacticos",
                    "Errores semánticos": "errores_semanticos",
                    "Advertencias": "advertencias",
                }
                clave = mapa.get(etiqueta.text())
                if clave is not None:
                    self.titulos_tarjetas_resumen[clave] = etiqueta  # Guarda referencias estables antes de la primera traducción.

        self.pestanas_tablas = self._pestana_directa(panel.tab_tablas)  # Localiza las dos tablas del análisis léxico.
        self.pestanas_sintaxis = self._pestana_directa(panel.tab_sintaxis)  # Localiza las tres vistas del parser.
        self.pestanas_fases = self._pestana_directa(panel.tab_fases_posteriores)  # Localiza las fases reservadas para unidades futuras.

    def aplicar(self, idioma: str) -> bool:
        if not self.gestor.establecer_idioma(idioma):
            return False  # Conserva intacta la interfaz ante un código no admitido.

        self._aplicar_encabezado_y_estado()  # Traduce la zona superior y el estado actual.
        self._aplicar_barra_titulo()  # Traduce controles y selector de ventana.
        self._aplicar_editor()  # Traduce ayudas de los botones flotantes.
        self._aplicar_panel_resultados()  # Traduce navegación, acciones y tablas principales.
        self._aplicar_resultados_internos()  # Traduce resumen, análisis, tablas, sintaxis y fases futuras.
        self._aplicar_panel_diagnosticos()  # Traduce pestañas y encabezados estructurados.
        return True  # Confirma que el idioma pudo aplicarse.

    def _resultado_visible(self):
        panel = self.ventana.panel_resultados  # Recupera la salida asociada con la interfaz.
        return panel.resultado_actual or self.ventana.ultimo_resultado  # Conserva resultados visibles aun cuando una edición haya invalidado solamente la exportación.

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

        self._establecer_ayuda(panel.boton_copiar_analisis, "resultados.copiar_analisis")
        self._establecer_ayuda(panel.boton_copiar_diagnosticos, "resultados.copiar_diagnosticos")
        self._aplicar_advertencias_compactas()  # Traduce Mensaje y Solución sin mover ni modificar el panel compacto de VLSM.

    def _aplicar_advertencias_compactas(self) -> None:
        panel = self.ventana.panel_resultados
        for fila, diagnostico in enumerate(panel.advertencias_compactas_actuales):
            if fila >= panel.tabla_advertencias_vlsm.rowCount():
                break
            mensaje = panel.tabla_advertencias_vlsm.item(fila, 1)
            solucion = panel.tabla_advertencias_vlsm.item(fila, 2)
            if mensaje is not None:
                texto = self.traductor_diagnosticos.mensaje(diagnostico)
                mensaje.setText(texto)
                mensaje.setToolTip(texto)
            if solucion is not None:
                texto = self.traductor_diagnosticos.solucion_diagnostico(diagnostico)
                solucion.setText(texto)
                solucion.setToolTip(texto)

    def _aplicar_resultados_internos(self) -> None:
        self._aplicar_resumen()  # Traduce título, tarjetas y estado de la vista Resumen.
        self._aplicar_analisis_textual()  # Reconstruye la salida técnica en el idioma vigente.
        self._aplicar_tablas_lexicas()  # Traduce encabezados, pestañas y agrupaciones de tokens.
        self._aplicar_sintaxis()  # Traduce navegación del parser y ayudas del visor de árboles.
        self._aplicar_fases_posteriores()  # Traduce las tres fases reservadas para unidades futuras.
        self._aplicar_grupos_vlsm()  # Traduce las franjas que identifican cada red VLSM.

    def _aplicar_resumen(self) -> None:
        panel = self.ventana.panel_resultados

        if self.etiqueta_titulo_resumen is not None:
            self.etiqueta_titulo_resumen.setText(self._t("resultados.resumen.titulo"))

        claves_tarjetas = {
            "tokens": "resultados.resumen.tokens",
            "bloques_sintacticos": "resultados.resumen.bloques_sintacticos",
            "bloques_semanticos": "resultados.resumen.bloques_semanticos",
            "subredes": "resultados.resumen.subredes",
            "errores_lexicos": "resultados.resumen.errores_lexicos",
            "errores_sintacticos": "resultados.resumen.errores_sintacticos",
            "errores_semanticos": "resultados.resumen.errores_semanticos",
            "advertencias": "resultados.resumen.advertencias",
        }

        for clave_metrica, clave_texto in claves_tarjetas.items():
            etiqueta = self.titulos_tarjetas_resumen.get(clave_metrica)
            if etiqueta is not None:
                etiqueta.setText(self._t(clave_texto))

        resultado = self._resultado_visible()
        if resultado is None:
            panel.estado_resumen.setText(self._t("principal.estado.neutral"))
            return

        diagnosticos = resultado.diagnosticos
        bloques_sintacticos = len(resultado.resultado_sintactico.bloques)
        bloques_semanticos = len(resultado.resultado_semantico.bloques_validos) if resultado.resultado_semantico is not None else 0
        cantidad_errores = sum(1 for diagnostico in diagnosticos if diagnostico.severidad == "error")
        cantidad_advertencias = sum(1 for diagnostico in diagnosticos if diagnostico.severidad in ("warning", "advertencia"))
        cantidad_subredes = len(resultado.subredes_vlsm)

        if cantidad_errores > 0:
            texto = self._t("resultados.resumen.estado.errores", errores=cantidad_errores, advertencias=cantidad_advertencias, subredes=cantidad_subredes)
        elif cantidad_advertencias > 0:
            texto = self._t("resultados.resumen.estado.advertencias", advertencias=cantidad_advertencias, subredes=cantidad_subredes)
        else:
            texto = self._t("resultados.resumen.estado.correcto", sintacticos=bloques_sintacticos, semanticos=bloques_semanticos, subredes=cantidad_subredes)

        panel.estado_resumen.setText(texto)

    def _aplicar_analisis_textual(self) -> None:
        panel = self.ventana.panel_resultados
        resultado = self._resultado_visible()

        if resultado is None or not panel.texto_analisis.toPlainText():
            return  # Conserva vacío el visor cuando todavía no existe una salida técnica visible.

        lineas = [self._t("resultados.analisis.lexico.titulo"), ""]

        if resultado.resultado_lexico.tokens:
            for token in resultado.resultado_lexico.tokens:
                lineas.append(
                    f"{self._t('resultados.analisis.token')}: {token.tipo:<12} "
                    f"{self._t('resultados.analisis.valor')}: {token.valor:<18} "
                    f"({self._t('resultados.analisis.linea')} {token.linea}, "
                    f"{self._t('resultados.analisis.posicion')} {token.columna})"
                )
        else:
            lineas.append(self._t("resultados.analisis.sin_tokens"))

        lineas.extend(["", self._t("resultados.analisis.sintactico.titulo"), ""])

        if resultado.resultado_sintactico.bloques:
            for indice, bloque in enumerate(resultado.resultado_sintactico.bloques, start=1):
                nombre = bloque.nombre or self._t("resultados.analisis.sin_nombre")
                lineas.append(self._t("resultados.analisis.red_indice", indice=indice))
                lineas.append(f"  IP: {bloque.direccion_ip}")
                lineas.append(f"  {self._t('resultados.analisis.mascara')}: {bloque.mascara_subred}")
                lineas.append(f"  {self._t('resultados.analisis.hosts_requeridos')}: {bloque.cantidades_hosts}")
                lineas.append(f"  {self._t('resultados.analisis.nombre')}: {nombre}")
                lineas.append("")
        else:
            lineas.append(self._t("resultados.analisis.sin_bloques_sintacticos"))

        lineas.extend(["", self._t("resultados.analisis.semantico.titulo"), ""])
        resultado_semantico = resultado.resultado_semantico

        if resultado_semantico is None:
            lineas.append(self._t("resultados.analisis.semantico.no_ejecutado"))
        elif resultado_semantico.bloques_validos:
            for indice, bloque in enumerate(resultado_semantico.bloques_validos, start=1):
                nombre = bloque.nombre or self._t("resultados.analisis.sin_nombre")
                lineas.append(self._t("resultados.analisis.red_indice", indice=indice))
                lineas.append(f"  IP: {bloque.direccion_ip}")
                lineas.append(f"  {self._t('resultados.analisis.mascara')}: {bloque.mascara_subred}")
                lineas.append(f"  {self._t('resultados.analisis.hosts_requeridos')}: {bloque.cantidades_hosts}")
                lineas.append(f"  {self._t('resultados.analisis.nombre')}: {nombre}")
                lineas.append(f"  {self._t('resultados.analisis.estado')}: {self._t('resultados.analisis.semanticamente_valido')}")
                lineas.append("")
        else:
            lineas.append(self._t("resultados.analisis.sin_bloques_semanticos"))

        diagnosticos = resultado.diagnosticos
        cantidad_errores = sum(1 for diagnostico in diagnosticos if diagnostico.severidad == "error")
        cantidad_advertencias = sum(1 for diagnostico in diagnosticos if diagnostico.severidad in ("warning", "advertencia"))
        errores_lexicos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Léxico" and diagnostico.severidad == "error")
        errores_sintacticos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Sintáctico" and diagnostico.severidad == "error")
        errores_semanticos = sum(1 for diagnostico in diagnosticos if diagnostico.categoria == "Semántico" and diagnostico.severidad == "error")
        bloques_semanticos = len(resultado_semantico.bloques_validos) if resultado_semantico is not None else 0

        lineas.extend(["", self._t("resultados.analisis.resumen.titulo")])
        lineas.append(f"{self._t('resultados.resumen.tokens')}: {len(resultado.resultado_lexico.tokens)}")
        lineas.append(f"{self._t('resultados.analisis.bloques_sintacticos_validos')}: {len(resultado.resultado_sintactico.bloques)}")
        lineas.append(f"{self._t('resultados.analisis.bloques_semanticos_validos')}: {bloques_semanticos}")
        lineas.append(f"{self._t('resultados.resumen.subredes')}: {len(resultado.subredes_vlsm)}")
        lineas.append(f"{self._t('resultados.resumen.errores_lexicos')}: {errores_lexicos}")
        lineas.append(f"{self._t('resultados.resumen.errores_sintacticos')}: {errores_sintacticos}")
        lineas.append(f"{self._t('resultados.resumen.errores_semanticos')}: {errores_semanticos}")
        lineas.append(f"{self._t('resultados.analisis.errores_encontrados')}: {cantidad_errores}")
        lineas.append(f"{self._t('resultados.analisis.advertencias_encontradas')}: {cantidad_advertencias}")
        lineas.append(f"{self._t('resultados.analisis.diagnosticos_totales')}: {len(diagnosticos)}")

        panel.texto_analisis.setPlainText("\n".join(lineas))

    def _aplicar_tablas_lexicas(self) -> None:
        panel = self.ventana.panel_resultados
        panel.tabla_tokens.setHorizontalHeaderLabels([self._t("resultados.tablas.tipo"), self._t("resultados.tablas.valor"), self._t("diagnosticos.linea"), self._t("resultados.tablas.posicion")])
        panel.tabla_reservadas.setHorizontalHeaderLabels([self._t("resultados.tablas.palabra_reservada"), self._t("resultados.tablas.cantidad")])

        if self.pestanas_tablas is not None and self.pestanas_tablas.count() >= 2:
            self.pestanas_tablas.setTabText(0, self._t("resultados.tablas.tokens"))
            self.pestanas_tablas.setTabText(1, self._t("resultados.tablas.reservadas"))

        self._aplicar_grupos_tokens()

    def _aplicar_grupos_tokens(self) -> None:
        panel = self.ventana.panel_resultados
        resultado = self._resultado_visible()
        if resultado is None:
            return

        grupos = panel._agrupar_tokens_por_red(resultado)
        filas_grupo = [fila for fila in range(panel.tabla_tokens.rowCount()) if panel.tabla_tokens.columnSpan(fila, 0) == panel.tabla_tokens.columnCount()]
        bloques_por_linea = {bloque.linea_origen: bloque for bloque in resultado.bloques_validos}

        for fila, (_titulo_original, tokens) in zip(filas_grupo, grupos):
            if not tokens:
                continue
            primer_token = tokens[0]
            linea = primer_token.linea
            bloque = bloques_por_linea.get(linea)

            if bloque is not None:
                nombre = bloque.nombre or bloque.direccion_ip
                texto = self._t("resultados.grupo.red_linea", nombre=nombre, ip=bloque.direccion_ip, linea=linea)
            elif primer_token.tipo == "IP":
                direccion = next((token.valor for token in tokens if token.tipo == "IP_ADDRESS"), self._t("resultados.grupo.no_identificada"))
                nombre = panel._buscar_nombre_en_tokens(tokens)
                identificador = nombre or direccion
                texto = self._t("resultados.grupo.red_linea", nombre=identificador, ip=direccion, linea=linea)
            else:
                texto = self._t("resultados.grupo.sin_red", linea=linea)

            item = panel.tabla_tokens.item(fila, 0)
            if item is not None:
                item.setText(texto)

    def _aplicar_grupos_vlsm(self) -> None:
        panel = self.ventana.panel_resultados
        resultado = self._resultado_visible()
        if resultado is None or not resultado.subredes_vlsm:
            return

        grupos = []
        anterior = None
        for subred in resultado.subredes_vlsm:
            actual = (subred.nombre_red, subred.ip_base)
            if actual != anterior:
                grupos.append(actual)
                anterior = actual

        filas_grupo = [fila for fila in range(panel.tabla_vlsm.rowCount()) if panel.tabla_vlsm.columnSpan(fila, 0) == panel.tabla_vlsm.columnCount()]
        for fila, (nombre, ip_base) in zip(filas_grupo, grupos):
            item = panel.tabla_vlsm.item(fila, 0)
            if item is not None:
                item.setText(self._t("resultados.grupo.red", nombre=nombre, ip=ip_base))

    def _aplicar_sintaxis(self) -> None:
        panel = self.ventana.panel_resultados

        if self.pestanas_sintaxis is not None and self.pestanas_sintaxis.count() >= 3:
            self.pestanas_sintaxis.setTabText(0, self._t("resultados.sintaxis.producciones"))
            self.pestanas_sintaxis.setTabText(1, self._t("resultados.sintaxis.derivacion"))
            self.pestanas_sintaxis.setTabText(2, self._t("resultados.sintaxis.arboles"))

        visor = panel.visor_arbol
        if visor.pestanas_vista.count() >= 2:
            visor.pestanas_vista.setTabText(0, self._t("resultados.arbol.textual"))
            visor.pestanas_vista.setTabText(1, self._t("resultados.arbol.grafico"))

        for etiqueta in visor.contenedor_grafico.findChildren(QLabel):
            if etiqueta.objectName() == "SubtituloPrincipal":
                etiqueta.setText(self._t("resultados.arbol.ayuda"))

        resultado = self._resultado_visible()
        arboles = resultado.resultado_sintactico.arboles if resultado is not None else []

        if not arboles and visor.pestanas_arboles.count() == 1:
            visor.pestanas_arboles.setTabText(0, self._t("resultados.arbol.sin_arbol"))
            widget = visor.pestanas_arboles.widget(0)
            if widget is not None:
                etiquetas = widget.findChildren(QLabel)
                if etiquetas:
                    etiquetas[0].setText(self._t("resultados.arbol.sin_validos"))
            visor.texto_arbol.setPlainText(self._t("resultados.arbol.sin_validos_textual"))
        elif arboles:
            for indice, arbol in enumerate(arboles, start=1):
                posicion = indice - 1
                if posicion >= visor.pestanas_arboles.count():
                    break
                if arbol.etiqueta.startswith("BloqueRed:"):
                    nombre = arbol.etiqueta.split(":", 1)[1].strip()
                else:
                    nombre = ""
                if not nombre:
                    visor.pestanas_arboles.setTabText(posicion, self._t("resultados.arbol.indice", indice=indice))

        for boton in visor.findChildren(QPushButton, "BotonGuardarArbol"):
            self._establecer_ayuda(boton, "resultados.arbol.guardar_png")

    def _aplicar_fases_posteriores(self) -> None:
        if self.pestanas_fases is None or self.pestanas_fases.count() < 3:
            return

        claves_pestanas = ("resultados.fases.codigo_intermedio", "resultados.fases.optimizacion", "resultados.fases.codigo_objeto")
        claves_textos = ("resultados.fases.unidad2", "resultados.fases.unidad3", "resultados.fases.unidad4")

        for indice, (clave_pestana, clave_texto) in enumerate(zip(claves_pestanas, claves_textos)):
            self.pestanas_fases.setTabText(indice, self._t(clave_pestana))
            visor = self.pestanas_fases.widget(indice)
            if visor is not None and hasattr(visor, "setPlainText"):
                visor.setPlainText(self._t(clave_texto))

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

        # Detectados: los objetos oficiales permanecen intactos; solo cambia lo visible.
        for fila, diagnostico in enumerate(panel.diagnosticos_actuales):
            if fila >= panel.tabla_detectados.rowCount():
                break

            categoria = panel.tabla_detectados.item(fila, 1)
            mensaje = panel.tabla_detectados.item(fila, 2)
            solucion = panel.tabla_detectados.item(fila, 5)
            codigo = panel.tabla_detectados.item(fila, 0)

            if categoria is not None:
                texto_categoria = self.traductor_diagnosticos.categoria(diagnostico.categoria)
                categoria.setText(texto_categoria)
                categoria.setToolTip(texto_categoria)

            if mensaje is not None:
                texto_mensaje = self.traductor_diagnosticos.mensaje(diagnostico)
                mensaje.setText(texto_mensaje)
                mensaje.setToolTip(texto_mensaje)

            if solucion is not None:
                texto_solucion = self.traductor_diagnosticos.solucion_diagnostico(diagnostico)
                solucion.setText(texto_solucion)
                solucion.setToolTip(self._t("diagnosticos.solucion_oficial_ayuda", solucion=texto_solucion))

            if codigo is not None:
                codigo.setToolTip(
                    self._t(
                        "diagnosticos.codigo.ayuda",
                        codigo=diagnostico.codigo,
                    )
                )

        panel.tabla_detectados.resizeRowsToContents()

        # Catálogo: código y colores siguen siendo los oficiales; nombre, estado,
        # descripción y solución se resuelven según el idioma de interfaz.
        for fila in range(panel.tabla_catalogo.rowCount()):
            elemento_codigo = panel.tabla_catalogo.item(fila, 0)
            if elemento_codigo is None:
                continue
            codigo = elemento_codigo.text().strip()
            informacion = __import__("Motor.compilacion.diagnosticos", fromlist=["obtener_informacion_diagnostico"]).obtener_informacion_diagnostico(codigo)
            valores = [
                codigo,
                self.traductor_diagnosticos.categoria(informacion["categoria"]),
                self.traductor_diagnosticos.estado(codigo),
                self.traductor_diagnosticos.nombre(codigo),
                self.traductor_diagnosticos.descripcion(codigo),
                self.traductor_diagnosticos.solucion(codigo),
            ]
            for columna, valor in enumerate(valores):
                elemento = panel.tabla_catalogo.item(fila, columna)
                if elemento is not None:
                    elemento.setText(valor)
                    elemento.setToolTip(valor)

        panel.tabla_catalogo.resizeRowsToContents()

    def aplicar_ventana_diagnosticos(self, ventana) -> None:
        # Traduce una VentanaAdvertencias ya construida. Se evita modificar la
        # clase histórica para mantener compatibilidad con todas sus integraciones.
        from Interfaz.ventanas.ventana_advertencias import TarjetaDiagnosticoInteractiva

        titulo_ventana = self._t("diagnosticos.ventana.titulo")
        ventana.setWindowTitle(titulo_ventana)
        ventana.barra_titulo.etiqueta_titulo.setText(titulo_ventana)

        if ventana.barra_titulo.boton_cerrar is not None:
            ventana.barra_titulo.boton_cerrar.setToolTip(self._t("comun.cerrar"))
            ventana.barra_titulo.boton_cerrar.setAccessibleName(self._t("comun.cerrar"))

        titulos = ventana.findChildren(QLabel, "TituloConfiguracion")
        if titulos:
            titulos[0].setText(self._t("diagnosticos.ventana.detectados"))

        descripciones = ventana.findChildren(QLabel, "DescripcionConfiguracion")
        if descripciones:
            descripciones[0].setText(
                self._t(
                    "diagnosticos.ventana.descripcion",
                    errores=len(ventana.errores),
                    advertencias=len(ventana.advertencias),
                )
            )

        if ventana.pestana_errores is not None:
            indice = ventana.pestanas_diagnosticos.indexOf(ventana.pestana_errores)
            if indice >= 0:
                ventana.pestanas_diagnosticos.setTabText(
                    indice,
                    self._t("diagnosticos.ventana.errores", cantidad=len(ventana.errores)),
                )

        if ventana.pestana_advertencias is not None:
            indice = ventana.pestanas_diagnosticos.indexOf(ventana.pestana_advertencias)
            if indice >= 0:
                ventana.pestanas_diagnosticos.setTabText(
                    indice,
                    self._t("diagnosticos.ventana.advertencias", cantidad=len(ventana.advertencias)),
                )

        ventana.boton_aceptar.setText(self._t("comun.aceptar"))

        for tarjeta in ventana.findChildren(TarjetaDiagnosticoInteractiva):
            diagnostico = tarjeta.diagnostico
            if diagnostico.linea is not None:
                tarjeta.setToolTip(self._t("diagnosticos.ventana.doble_clic"))
            else:
                tarjeta.setToolTip(self._t("diagnosticos.ventana.sin_ubicacion_ayuda"))

            codigos = [
                etiqueta
                for etiqueta in tarjeta.findChildren(QLabel)
                if etiqueta.objectName() in ("CodigoErrorIndependiente", "CodigoAdvertenciaIndependiente")
            ]
            if codigos:
                codigos[0].setText(
                    f"{diagnostico.codigo} · {self.traductor_diagnosticos.categoria(diagnostico.categoria)}"
                )

            ubicaciones = tarjeta.findChildren(QLabel, "UbicacionDiagnosticoIndependiente")
            if ubicaciones:
                if diagnostico.linea is None:
                    texto_ubicacion = self._t("diagnosticos.ubicacion.no_especificada")
                elif diagnostico.columna is None:
                    texto_ubicacion = self._t("diagnosticos.ubicacion.linea", linea=diagnostico.linea)
                else:
                    texto_ubicacion = self._t(
                        "diagnosticos.ubicacion.linea_columna",
                        linea=diagnostico.linea,
                        columna=diagnostico.columna,
                    )
                ubicaciones[0].setText(texto_ubicacion)

            encabezados = tarjeta.findChildren(QLabel, "TituloCampoDiagnosticoIndependiente")
            if len(encabezados) >= 2:
                encabezados[0].setText(self._t("diagnosticos.mensaje"))
                encabezados[1].setText(self._t("diagnosticos.solucion"))

            textos = tarjeta.findChildren(QLabel, "TextoDiagnosticoIndependiente")
            if len(textos) >= 2:
                textos[0].setText(self.traductor_diagnosticos.mensaje(diagnostico))
                textos[1].setText(self.traductor_diagnosticos.solucion_diagnostico(diagnostico))

    def aplicar_boton_reabrir_diagnosticos(self, boton, diagnosticos: list) -> None:
        if boton is None:
            return

        boton.setAccessibleName(self._t("diagnosticos.reabrir"))
        if not diagnosticos:
            boton.setToolTip(self._t("diagnosticos.reabrir"))
            return

        errores = sum(1 for diagnostico in diagnosticos if diagnostico.severidad == "error")
        advertencias = sum(
            1
            for diagnostico in diagnosticos
            if diagnostico.severidad in ("warning", "advertencia")
        )
        boton.setToolTip(
            self._t(
                "diagnosticos.reabrir.resumen",
                errores=errores,
                advertencias=advertencias,
            )
        )
