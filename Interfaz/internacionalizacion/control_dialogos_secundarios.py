# ============================================================
# Archivo: control_dialogos_secundarios.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Internacionaliza los diálogos secundarios del editor sin
# modificar el DSL ni la lógica formal del compilador.
#
# Este controlador cubre:
# - Selector de ejemplos.
# - Vista previa de ejemplos.
# - Confirmación de inserción en el editor.
# - Reporte de pruebas automáticas.
# - Tooltip de diagnósticos dibujados sobre el editor.
#
# Los archivos TXT originales se conservan como fuente canónica
# para las pruebas automáticas. La representación visible y los
# comandos insertados se localizan según el idioma de interfaz.
# ============================================================

from textwrap import fill

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
)

from Interfaz.ejemplos.reporte_pruebas_ejemplos import VentanaReportePruebas
from Interfaz.ejemplos.selector_ejemplos import SelectorEjemplos, TablaEjemplos
from Interfaz.internacionalizacion.traductor_diagnosticos import TraductorDiagnosticos
from Interfaz.internacionalizacion.traductor_ejemplos import TraductorEjemplos, identificador_caso
from Motor.compilacion.diagnosticos import (
    obtener_codigos_diagnosticos_disponibles,
    obtener_codigos_diagnosticos_pendientes,
)
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion
from Motor.ejemplos.gestor_ejemplos import EjemploCodigo
from Motor.ejemplos.pruebas_ejemplos import (
    ESTADO_CORRECTO,
    ESTADO_FALLIDO,
    ESTADO_PENDIENTE,
    ResumenPruebasEjemplos,
)
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


def _texto_codigos(codigos: list[str], gestor: GestorTraducciones, clave_vacio: str = "secundarios.reporte.ninguno") -> str:
    if codigos:
        return ", ".join(codigos)
    return gestor.traducir(clave_vacio)


def _nombre_estado(estado: str, gestor: GestorTraducciones) -> str:
    claves = {
        ESTADO_CORRECTO: "secundarios.reporte.estado.correcto",
        ESTADO_PENDIENTE: "secundarios.reporte.estado.pendiente",
        ESTADO_FALLIDO: "secundarios.reporte.estado.fallido",
    }
    return gestor.traducir(claves.get(estado, "secundarios.reporte.estado.fallido"))


def _tipo_ejemplo(tipo: str, gestor: GestorTraducciones) -> str:
    if tipo == "Válida":
        return gestor.traducir("secundarios.ejemplos.tipo.valida")
    if tipo == "Inválida":
        return gestor.traducir("secundarios.ejemplos.tipo.invalida")
    return tipo


def _traducir_motivo(motivo: str, gestor: GestorTraducciones) -> str:
    prefijos = (
        (
            "Se produjo un error interno durante la prueba: ",
            "secundarios.reporte.motivo.error_interno",
            "error",
        ),
        (
            "El caso está declarado como válido, pero produjo errores actuales: ",
            "secundarios.reporte.motivo.valido_con_errores",
            "codigos",
        ),
        (
            "El caso está reservado para una característica futura, pero produjo errores actuales inesperados: ",
            "secundarios.reporte.motivo.futuro_con_errores",
            "codigos",
        ),
        (
            "No aparecieron los códigos evaluables esperados: ",
            "secundarios.reporte.motivo.codigos_faltantes",
            "codigos",
        ),
    )

    for prefijo, clave, variable in prefijos:
        if motivo.startswith(prefijo):
            valor = motivo[len(prefijo):].strip()
            if valor.endswith("."):
                valor = valor[:-1]
            return gestor.traducir(clave, **{variable: valor})

    exactos = {
        "El caso está declarado como válido, pero no produjo bloques válidos después de las fases actuales.": "secundarios.reporte.motivo.valido_sin_bloques",
        "El caso produjo bloques válidos, pero no generó ninguna subred VLSM.": "secundarios.reporte.motivo.sin_vlsm",
        "El caso debería producir un error en las fases actuales, pero no se obtuvo ninguno.": "secundarios.reporte.motivo.error_esperado_ausente",
        "El caso está declarado como inválido, pero no produjo ningún error en las fases actuales.": "secundarios.reporte.motivo.invalido_sin_error",
    }
    clave = exactos.get(motivo)
    return gestor.traducir(clave) if clave is not None else motivo


def generar_reporte_pruebas_traducido(resumen: ResumenPruebasEjemplos, gestor: GestorTraducciones) -> str:
    lineas: list[str] = []
    disponibles = obtener_codigos_diagnosticos_disponibles()
    pendientes = obtener_codigos_diagnosticos_pendientes()

    lineas.append(gestor.traducir("secundarios.reporte.encabezado"))
    lineas.append("")
    lineas.append(gestor.traducir("secundarios.reporte.alcance"))
    lineas.append(
        gestor.traducir(
            "secundarios.reporte.diagnosticos_evaluables",
            codigos=", ".join(disponibles) if disponibles else gestor.traducir("secundarios.reporte.ninguno"),
        )
    )
    lineas.append(
        gestor.traducir(
            "secundarios.reporte.diagnosticos_pendientes",
            codigos=", ".join(pendientes) if pendientes else gestor.traducir("secundarios.reporte.ninguno"),
        )
    )
    lineas.append("")
    lineas.append(gestor.traducir("secundarios.reporte.total", cantidad=resumen.total))
    lineas.append(gestor.traducir("secundarios.reporte.correctos", cantidad=resumen.correctos))
    lineas.append(gestor.traducir("secundarios.reporte.pendientes", cantidad=resumen.pendientes))
    lineas.append(gestor.traducir("secundarios.reporte.fallidos", cantidad=resumen.fallidos))
    lineas.append(
        gestor.traducir(
            "secundarios.reporte.expectativas_pendientes",
            cantidad=resumen.con_expectativas_pendientes,
        )
    )
    lineas.append("")

    if resumen.fallidos:
        lineas.append(gestor.traducir("secundarios.reporte.resultado.fallidos"))
    elif resumen.pendientes:
        lineas.append(gestor.traducir("secundarios.reporte.resultado.pendientes"))
    else:
        lineas.append(gestor.traducir("secundarios.reporte.resultado.correcto"))

    lineas.extend(["", "-" * 72, ""])

    for indice, resultado in enumerate(resumen.resultados, start=1):
        ejemplo = resultado.ejemplo
        lineas.append(f"{indice}. [{_nombre_estado(resultado.estado, gestor)}] {ejemplo.titulo}")
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.tipo_declarado",
                tipo=_tipo_ejemplo(ejemplo.tipo, gestor),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.codigos_esperados",
                codigos=_texto_codigos(
                    resultado.codigos_esperados,
                    gestor,
                    "secundarios.reporte.no_especificados",
                ),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.codigos_evaluables_ahora",
                codigos=_texto_codigos(resultado.codigos_evaluables, gestor),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.expectativas_pendientes_detalle",
                codigos=_texto_codigos(resultado.codigos_pendientes, gestor),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.codigos_obtenidos",
                codigos=_texto_codigos(resultado.codigos_obtenidos, gestor),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.errores_obtenidos",
                codigos=_texto_codigos(resultado.codigos_error, gestor),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.advertencias_obtenidas",
                codigos=_texto_codigos(resultado.codigos_advertencia, gestor),
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.tokens",
                cantidad=resultado.tokens_reconocidos,
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.bloques",
                cantidad=resultado.bloques_validos,
            )
        )
        lineas.append(
            gestor.traducir(
                "secundarios.reporte.subredes",
                cantidad=resultado.subredes_generadas,
            )
        )

        if resultado.motivos:
            lineas.append(gestor.traducir("secundarios.reporte.motivos"))
            for motivo in resultado.motivos:
                lineas.append(f"   - {_traducir_motivo(motivo, gestor)}")
        elif resultado.estado == ESTADO_PENDIENTE:
            lineas.append(gestor.traducir("secundarios.reporte.motivo.pendiente"))
        elif resultado.codigos_pendientes:
            lineas.append(gestor.traducir("secundarios.reporte.nota.pendientes"))

        lineas.append("")

    return "\n".join(lineas).rstrip() + "\n"


class VentanaReportePruebasTraducida(VentanaReportePruebas):
    def __init__(self, resumen: ResumenPruebasEjemplos, gestor: GestorTraducciones, padre=None):
        self.gestor_traducciones = gestor
        super().__init__(resumen, padre)
        self._aplicar_idioma()

    def _t(self, clave: str, **variables) -> str:
        return self.gestor_traducciones.traducir(clave, **variables)

    def _aplicar_idioma(self) -> None:
        self.setWindowTitle(self._t("secundarios.reporte.titulo"))

        self.reporte_texto = generar_reporte_pruebas_traducido(
            self.resumen,
            self.gestor_traducciones,
        )
        self.texto_reporte.setPlainText(self.reporte_texto)

        for etiqueta in self.findChildren(QLabel):
            texto = etiqueta.text()
            if etiqueta.objectName() == "TituloSeccion":
                etiqueta.setText(self._t("secundarios.reporte.titulo"))
            elif texto.startswith("Total:"):
                etiqueta.setText(
                    self._t(
                        "secundarios.reporte.resumen",
                        total=self.resumen.total,
                        correctos=self.resumen.correctos,
                        pendientes=self.resumen.pendientes,
                        fallidos=self.resumen.fallidos,
                    )
                )
            elif texto.startswith("La evaluación automática"):
                etiqueta.setText(self._t("secundarios.reporte.explicacion"))

        for boton in self.findChildren(QPushButton):
            if boton.text() == "Copiar reporte":
                boton.setText(self._t("secundarios.reporte.copiar"))
                boton.setToolTip(self._t("secundarios.reporte.copiar_ayuda"))
            elif boton.text() == "Cerrar":
                boton.setText(self._t("comun.cerrar"))


class SelectorEjemplosTraducido(SelectorEjemplos):
    def __init__(
        self,
        ejemplos_validos,
        ejemplos_invalidos,
        gestor: GestorTraducciones,
        padre=None,
        originales_validos=None,
        originales_invalidos=None,
    ):
        self.gestor_traducciones = gestor
        originales = [*(originales_validos or []), *(originales_invalidos or [])]
        localizados = [*ejemplos_validos, *ejemplos_invalidos]
        self._original_por_codigo = {
            identificador_caso(ejemplo.titulo): ejemplo
            for ejemplo in originales
            if identificador_caso(ejemplo.titulo) is not None
        }
        self._localizado_por_codigo = {
            identificador_caso(ejemplo.titulo): ejemplo
            for ejemplo in localizados
            if identificador_caso(ejemplo.titulo) is not None
        }
        super().__init__(ejemplos_validos, ejemplos_invalidos, padre)
        self._aplicar_idioma()

    def _t(self, clave: str, **variables) -> str:
        return self.gestor_traducciones.traducir(clave, **variables)

    def _aplicar_idioma(self) -> None:
        self.setWindowTitle(self._t("secundarios.ejemplos.titulo"))

        for etiqueta in self.findChildren(QLabel):
            texto = etiqueta.text()
            if texto == "Selecciona uno o varios ejemplos para insertarlos o probarlos automáticamente.":
                etiqueta.setText(self._t("secundarios.ejemplos.instruccion"))
            elif texto.startswith("Las pruebas automáticas utilizan las fases actualmente disponibles"):
                etiqueta.setText(self._t("secundarios.ejemplos.aviso"))
            elif texto == "No se encontraron ejemplos para esta categoría.":
                etiqueta.setText(self._t("secundarios.ejemplos.sin_categoria"))

        if self.pestanas.count() >= 2:
            self.pestanas.setTabText(0, self._t("secundarios.ejemplos.validas"))
            self.pestanas.setTabText(1, self._t("secundarios.ejemplos.invalidas"))

        textos_botones = {
            "Seleccionar todo": "secundarios.ejemplos.seleccionar_todo",
            "Quitar selección": "secundarios.ejemplos.quitar_seleccion",
            "Probar seleccionados": "secundarios.ejemplos.probar_seleccionados",
            "Probar todos": "secundarios.ejemplos.probar_todos",
            "Cerrar": "comun.cerrar",
            "Insertar seleccionados": "secundarios.ejemplos.insertar_seleccionados",
        }

        for boton in self.findChildren(QPushButton):
            clave = textos_botones.get(boton.text())
            if clave is not None:
                boton.setText(self._t(clave))

            if boton.toolTip() == "Ejecutar únicamente los ejemplos marcados":
                boton.setToolTip(self._t("secundarios.ejemplos.probar_seleccionados_ayuda"))
            elif boton.toolTip() == "Ejecutar todos los ejemplos disponibles":
                boton.setToolTip(self._t("secundarios.ejemplos.probar_todos_ayuda"))

        for tabla in self.findChildren(TablaEjemplos):
            tabla.setHorizontalHeaderLabels(
                [
                    self._t("secundarios.ejemplos.columna.seleccion"),
                    self._t("secundarios.ejemplos.columna.caso"),
                    self._t("secundarios.ejemplos.columna.comando"),
                    self._t("secundarios.ejemplos.columna.salida"),
                ]
            )
            for fila in range(tabla.rowCount()):
                item = tabla.item(fila, 3)
                if item is not None and item.text() == "Sin salida esperada registrada.":
                    item.setText(self._t("secundarios.ejemplos.sin_salida"))
                    item.setToolTip(item.text())

    def _probar_seleccionados(self) -> None:
        seleccionados = self._obtener_seleccionados()
        if not seleccionados:
            QMessageBox.warning(
                self,
                self._t("secundarios.ejemplos.pruebas_titulo"),
                self._t("secundarios.ejemplos.selecciona_para_probar"),
            )
            return
        self._ejecutar_pruebas(seleccionados)

    def _probar_todos(self) -> None:
        ejemplos = [*self.ejemplos_validos, *self.ejemplos_invalidos]
        if not ejemplos:
            QMessageBox.warning(
                self,
                self._t("secundarios.ejemplos.pruebas_titulo"),
                self._t("secundarios.ejemplos.sin_ejemplos"),
            )
            return
        self._ejecutar_pruebas(ejemplos)

    def _ejecutar_pruebas(self, ejemplos) -> None:
        # Ejecuta exactamente el comando localizado que el usuario ve y puede
        # insertar, pero conserva la salida esperada canónica en español para
        # que el evaluador histórico extraiga los códigos sin cambiar su contrato.
        ejemplos_prueba = []
        for ejemplo in ejemplos:
            codigo = identificador_caso(ejemplo.titulo)
            original = self._original_por_codigo.get(codigo)

            if original is None:
                ejemplos_prueba.append(ejemplo)
                continue

            ejemplos_prueba.append(
                EjemploCodigo(
                    tipo=original.tipo,
                    titulo=original.titulo,
                    comando=ejemplo.comando,
                    salida_esperada=original.salida_esperada,
                )
            )

        resumen = self.ejecutor_pruebas.ejecutar(ejemplos_prueba)

        # El reporte vuelve a mostrar la variante localizada sin alterar códigos,
        # contadores ni la clasificación obtenida por el flujo real.
        for resultado in resumen.resultados:
            codigo = identificador_caso(resultado.ejemplo.titulo)
            localizado = self._localizado_por_codigo.get(codigo)
            if localizado is not None:
                resultado.ejemplo = localizado

        ventana_reporte = VentanaReportePruebasTraducida(
            resumen,
            self.gestor_traducciones,
            self,
        )
        ventana_reporte.exec()

    def _aceptar_seleccion(self) -> None:
        seleccionados = self._obtener_seleccionados()
        if not seleccionados:
            QMessageBox.warning(
                self,
                self._t("secundarios.ejemplos.insertar_titulo"),
                self._t("secundarios.ejemplos.selecciona_uno"),
            )
            return
        self.seleccion_final = seleccionados
        self.accept()

    def _mostrar_vista_previa(self, ejemplo) -> None:
        vista = QDialog(self)
        vista.setWindowTitle(self._t("secundarios.ejemplos.vista_previa"))
        vista.resize(780, 440)
        vista.setMinimumSize(620, 360)

        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

        diseno = QVBoxLayout(vista)
        diseno.setContentsMargins(10, 10, 10, 10)

        texto = QPlainTextEdit()
        texto.setReadOnly(True)
        texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        texto.setPlainText(
            self._t("secundarios.ejemplos.preview.tipo", tipo=_tipo_ejemplo(ejemplo.tipo, self.gestor_traducciones))
            + "\n"
            + self._t("secundarios.ejemplos.preview.caso", caso=ejemplo.titulo)
            + "\n\n"
            + self._t("secundarios.ejemplos.preview.comandos")
            + "\n"
            + ejemplo.comando
            + "\n\n"
            + self._t("secundarios.ejemplos.preview.salida")
            + "\n"
            + (ejemplo.salida_esperada or self._t("secundarios.ejemplos.sin_salida"))
        )
        diseno.addWidget(texto, 1)

        acciones = QHBoxLayout()
        acciones.addStretch()
        boton_cerrar = QPushButton(self._t("comun.cerrar"))
        boton_cerrar.clicked.connect(vista.accept)
        acciones.addWidget(boton_cerrar)
        diseno.addLayout(acciones)
        vista.exec()


class ControlDialogosSecundarios:
    def __init__(
        self,
        ventana,
        preferencias_aplicacion: PreferenciasAplicacion,
    ):
        self.ventana = ventana
        self.preferencias_aplicacion = preferencias_aplicacion
        self.gestor = GestorTraducciones(preferencias_aplicacion.idioma_interfaz())
        self.traductor_diagnosticos = TraductorDiagnosticos(self.gestor)
        self.traductor_ejemplos = TraductorEjemplos(preferencias_aplicacion.idioma_interfaz())
        self.editor = self.ventana.editor_codigo

        try:
            self.editor.boton_ejemplos.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass

        self.editor.boton_ejemplos.clicked.connect(self._abrir_selector_ejemplos)
        self.editor._texto_tooltip = self._texto_tooltip_editor

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)

    def establecer_idioma(self, idioma: str) -> bool:
        actualizado = self.gestor.establecer_idioma(idioma)
        actualizado_ejemplos = self.traductor_ejemplos.establecer_idioma(idioma)
        return actualizado and actualizado_ejemplos

    def _abrir_selector_ejemplos(self) -> None:
        originales_validos, originales_invalidos = self.editor.gestor_ejemplos.cargar_ejemplos()

        if not originales_validos and not originales_invalidos:
            QMessageBox.warning(
                self.editor,
                self._t("secundarios.ejemplos.titulo_corto"),
                self._t("secundarios.ejemplos.carpeta_vacia"),
            )
            return

        ejemplos_validos = self.traductor_ejemplos.traducir_coleccion(originales_validos)
        ejemplos_invalidos = self.traductor_ejemplos.traducir_coleccion(originales_invalidos)

        selector = SelectorEjemplosTraducido(
            ejemplos_validos,
            ejemplos_invalidos,
            self.gestor,
            self.editor.window(),
            originales_validos=originales_validos,
            originales_invalidos=originales_invalidos,
        )

        if selector.exec() != QDialog.DialogCode.Accepted:
            self.editor.setFocus()
            return

        texto_ejemplos = selector.obtener_texto_seleccionado()
        if not texto_ejemplos:
            self.editor.setFocus()
            return

        modo = self._consultar_modo_insercion()
        if modo is None:
            self.editor.setFocus()
            return

        if modo == "reemplazar":
            self.editor.setPlainText(texto_ejemplos)
        else:
            texto_actual = self.editor.toPlainText().rstrip()
            texto_completo = f"{texto_actual}\n{texto_ejemplos}" if texto_actual else texto_ejemplos
            self.editor.setPlainText(texto_completo)

        cursor = self.editor.textCursor()
        from PySide6.QtGui import QTextCursor
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)
        self.editor.ejemplos_insertados.emit()
        self.editor.setFocus()

    def _consultar_modo_insercion(self) -> str | None:
        if not self.editor.toPlainText().strip():
            return "reemplazar"

        mensaje = QMessageBox(self.editor)
        mensaje.setWindowTitle(self._t("secundarios.ejemplos.insertar_titulo"))
        mensaje.setText(self._t("secundarios.ejemplos.confirmar_insercion"))

        boton_reemplazar = mensaje.addButton(
            self._t("secundarios.ejemplos.reemplazar"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        boton_agregar = mensaje.addButton(
            self._t("secundarios.ejemplos.agregar_final"),
            QMessageBox.ButtonRole.ActionRole,
        )
        boton_cancelar = mensaje.addButton(
            self._t("comun.cancelar"),
            QMessageBox.ButtonRole.RejectRole,
        )

        mensaje.exec()
        boton_pulsado = mensaje.clickedButton()

        if boton_pulsado is boton_reemplazar:
            return "reemplazar"
        if boton_pulsado is boton_agregar:
            return "agregar"
        if boton_pulsado is boton_cancelar:
            return None
        return None

    def _texto_tooltip_editor(self, diagnosticos) -> str:
        bloques = []

        for diagnostico in diagnosticos:
            categoria = self.traductor_diagnosticos.categoria(diagnostico.categoria)
            mensaje = fill(
                self.traductor_diagnosticos.mensaje(diagnostico),
                width=72,
            )
            solucion_original = self.traductor_diagnosticos.solucion_diagnostico(diagnostico)
            solucion = fill(
                solucion_original or self._t("secundarios.editor.sin_solucion"),
                width=72,
            )

            bloques.append(
                f"{diagnostico.codigo} · {categoria}\n"
                f"{mensaje}\n\n"
                f"{self._t('diagnosticos.solucion')}:\n{solucion}"
            )

        return "\n\n────────────────────────\n\n".join(bloques)
