# ============================================================
# Archivo: control_barrida_final.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Atiende textos residuales que permanecían fuera de la capa
# principal de internacionalización:
# - Buscador del selector de fuentes.
# - Confirmaciones, progreso y mensajes del componente de IA.
# - Errores de persistencia mostrados desde Configuración.
#
# No modifica el compilador, el DSL ni los datos internos de las
# preferencias. Solamente transforma textos en el momento de
# presentarlos al usuario.
# ============================================================

from types import MethodType

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton

from Interfaz.internacionalizacion.control_cierre_interfaz import ControlCierreInterfaz
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class ControlBarridaFinal:
    TITULOS_IA = {
        "Instalar asistencia de IA": "configuracion.ia.confirmacion.instalar.titulo",
        "Desinstalar asistencia de IA": "configuracion.ia.confirmacion.desinstalar.titulo",
        "Asistencia de IA": "configuracion.ia.dialogo.asistencia",
        "Preferencias": "configuracion.ia.dialogo.preferencias",
        "Instalación de IA": "configuracion.ia.dialogo.instalacion",
        "Desinstalación de IA": "configuracion.ia.dialogo.desinstalacion",
    }

    TEXTOS_IA_EXACTOS = {
        (
            "TecNet Finder descargará aproximadamente 2.5 GB entre el runtime local y el modelo.\n\n"
            "La instalación se guardará únicamente en los datos locales de TecNet Finder y puede tardar varios minutos.\n\n"
            "¿Deseas continuar?"
        ): "configuracion.ia.confirmacion.instalar.mensaje",
        (
            "Se eliminarán el runtime local de Ollama y el modelo utilizado por TecNet Finder.\n\n"
            "El compilador seguirá funcionando normalmente y podrás volver a instalar la asistencia más adelante.\n\n"
            "¿Deseas desinstalar el componente?"
        ): "configuracion.ia.confirmacion.desinstalar.mensaje",
        "Preparando operación...": "configuracion.ia.progreso.preparando",
        "Verificando y extrayendo el runtime local...": "configuracion.ia.progreso.extrayendo_runtime",
        "Verificando integridad del modelo...": "configuracion.ia.progreso.verificando_modelo",
        "Eliminando runtime y modelo local...": "configuracion.ia.progreso.eliminando",
        "La asistencia de IA ya se encuentra instalada.": "configuracion.ia.mensaje.ya_instalada",
        "Esta versión del componente de IA requiere Windows de 64 bits sobre arquitectura AMD64.": "configuracion.ia.mensaje.windows_amd64",
        "Otra instancia está utilizando el servicio privado de IA. Cierra las demás instancias de TecNet Finder e inténtalo nuevamente.": "configuracion.ia.mensaje.otra_instancia_servicio",
        "La asistencia de IA local se instaló correctamente.": "configuracion.ia.mensaje.instalada",
        "El paquete descargado no es un archivo ZIP válido.": "configuracion.ia.mensaje.zip_invalido",
        "La asistencia de IA ya se encontraba desinstalada.": "configuracion.ia.mensaje.ya_desinstalada",
        "El componente está siendo utilizado por otra instancia. Cierra las demás instancias de TecNet Finder antes de desinstalarlo.": "configuracion.ia.mensaje.componente_en_uso",
        "El servicio local continúa activo y sus archivos no pueden retirarse de forma segura.": "configuracion.ia.mensaje.servicio_activo",
        "Windows no permitió eliminar completamente los archivos de la asistencia de IA después de varios intentos.": "configuracion.ia.mensaje.eliminacion_windows",
        "La asistencia de IA local se desinstaló correctamente.": "configuracion.ia.mensaje.desinstalada",
        "El componente se instaló y está activo, pero no fue posible guardar todas las preferencias de IA.": "configuracion.ia.mensaje.preferencias_no_guardadas",
        "La opción cambió para esta ejecución, pero no fue posible guardar la preferencia.": "configuracion.ia.mensaje.preferencia_no_guardada",
        "No fue posible guardar Autocompletado con IA.": "configuracion.ia.error.guardar_autocompletado",
        "No fue posible guardar la mejora de soluciones de diagnósticos con IA.": "configuracion.ia.error.guardar_diagnosticos",
    }

    def __init__(self, ventana):
        self.ventana = ventana
        self.gestor = GestorTraducciones("es")
        self._ventanas_preparadas: set[int] = set()

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)

    def establecer_idioma(self, idioma: str) -> bool:
        return self.gestor.establecer_idioma(idioma)

    def preparar_configuracion(self, ventana) -> None:
        self._traducir_busqueda_fuentes(ventana)

        identificador = id(ventana)
        if identificador not in self._ventanas_preparadas:
            self._preparar_panel_ia(ventana.panel_ia)
            self._preparar_errores_configuracion(ventana)
            self._ventanas_preparadas.add(identificador)

        self.aplicar_configuracion(ventana)

    def aplicar_configuracion(self, ventana) -> None:
        self._traducir_busqueda_fuentes(ventana)

        panel = getattr(ventana, "panel_ia", None)
        if panel is not None and not panel.operacion_en_curso:
            if panel.etiqueta_progreso.text() in (
                "Preparando operación...",
                self._t("configuracion.ia.progreso.preparando"),
            ):
                panel.etiqueta_progreso.setText(
                    self._t("configuracion.ia.progreso.preparando")
                )

    def _traducir_busqueda_fuentes(self, ventana) -> None:
        selectores = []

        panel_ventana = getattr(ventana, "panel_ventana", None)
        if panel_ventana is not None:
            selector = getattr(panel_ventana, "selector_fuente_interfaz", None)
            if selector is not None:
                selectores.append(selector)

        panel_editor = getattr(ventana, "panel_editor", None)
        if panel_editor is not None:
            selector = getattr(panel_editor, "selector_fuente", None)
            if selector is not None:
                selectores.append(selector)

        for selector in selectores:
            popup = getattr(selector, "popup", None)
            campo = getattr(popup, "campo_busqueda", None)
            if campo is not None:
                campo.setPlaceholderText(self._t("configuracion.fuentes.buscar"))

    def _preparar_panel_ia(self, panel) -> None:
        if getattr(panel, "_barrida_final_i18n", False):
            return

        original_confirmacion = panel._preguntar_confirmacion
        original_progreso = panel._actualizar_progreso
        original_mostrar_progreso = panel._mostrar_progreso
        original_finalizar = panel._finalizar_operacion
        original_aplicar_pendientes = getattr(panel, "aplicar_cambios_pendientes", None)

        def preguntar_confirmacion(_panel, titulo: str, mensaje: str) -> bool:
            QTimer.singleShot(0, self._traducir_botones_modal_activo)
            return original_confirmacion(
                self._traducir_texto_ia(titulo),
                self._traducir_texto_ia(mensaje),
            )

        def actualizar_progreso(_panel, etapa: str, porcentaje) -> None:
            original_progreso(
                self._traducir_texto_ia(etapa),
                porcentaje,
            )

        def mostrar_progreso(_panel, mostrar: bool) -> None:
            original_mostrar_progreso(mostrar)
            if _panel.etiqueta_progreso.text() == "Preparando operación...":
                _panel.etiqueta_progreso.setText(
                    self._t("configuracion.ia.progreso.preparando")
                )

        def finalizar_operacion(_panel, operacion: str, resultado: bool, mensaje: str) -> None:
            QTimer.singleShot(0, self._traducir_modal_ia_activo)
            QTimer.singleShot(40, self._traducir_modal_ia_activo)
            original_finalizar(
                operacion,
                resultado,
                self._traducir_texto_ia(mensaje),
            )

        panel._preguntar_confirmacion = MethodType(preguntar_confirmacion, panel)
        panel._actualizar_progreso = MethodType(actualizar_progreso, panel)
        panel._mostrar_progreso = MethodType(mostrar_progreso, panel)
        panel._finalizar_operacion = MethodType(finalizar_operacion, panel)

        if callable(original_aplicar_pendientes):
            def aplicar_cambios_pendientes(_panel):
                aplicados, errores = original_aplicar_pendientes()
                return aplicados, [
                    self._traducir_texto_ia(error)
                    for error in errores
                ]

            panel.aplicar_cambios_pendientes = MethodType(
                aplicar_cambios_pendientes,
                panel,
            )

        panel._barrida_final_i18n = True

    def _preparar_errores_configuracion(self, ventana) -> None:
        if getattr(ventana, "_barrida_final_errores_i18n", False):
            return

        original = ventana._aplicar_preferencias_generales

        def aplicar_preferencias_generales(_ventana):
            aplicados, errores = original()
            return aplicados, [
                self._traducir_error_configuracion(error)
                for error in errores
            ]

        ventana._aplicar_preferencias_generales = MethodType(
            aplicar_preferencias_generales,
            ventana,
        )
        ventana._barrida_final_errores_i18n = True

    def _traducir_error_configuracion(self, texto: str) -> str:
        prefijo = "No fue posible guardar: "
        if texto.startswith(prefijo) and texto.endswith("."):
            elemento = texto[len(prefijo):-1]
            clave = ControlCierreInterfaz.MAPA_CAMBIOS.get(elemento)
            elemento_traducido = self._t(clave) if clave else elemento
            return self._t(
                "configuracion.error.guardar_elemento",
                elemento=elemento_traducido,
            )

        return self._traducir_texto_ia(texto)

    def _traducir_texto_ia(self, texto: str) -> str:
        if not isinstance(texto, str) or not texto:
            return texto

        clave_titulo = self.TITULOS_IA.get(texto)
        if clave_titulo:
            return self._t(clave_titulo)

        clave = self.TEXTOS_IA_EXACTOS.get(texto)
        if clave:
            return self._t(clave)

        prefijos = (
            (
                "Descargando Ollama ",
                "configuracion.ia.progreso.descargando_ollama",
                "version",
            ),
            (
                "Descargando modelo ",
                "configuracion.ia.progreso.descargando_modelo",
                "modelo",
            ),
            (
                "Preparando modelo ",
                "configuracion.ia.progreso.preparando_modelo",
                "modelo",
            ),
            (
                "No fue posible preparar los archivos temporales de instalación: ",
                "configuracion.ia.mensaje.temporales",
                "error",
            ),
            (
                "No fue posible completar la descarga necesaria para la asistencia de IA: ",
                "configuracion.ia.mensaje.descarga",
                "error",
            ),
            (
                "No fue posible completar la instalación de la asistencia de IA: ",
                "configuracion.ia.mensaje.instalacion_error",
                "error",
            ),
            (
                "No fue posible preparar la carpeta privada de modelos: ",
                "configuracion.ia.mensaje.carpeta_modelos",
                "error",
            ),
            (
                "Ollama no pudo descargar el modelo: ",
                "configuracion.ia.mensaje.modelo_error",
                "error",
            ),
        )

        for prefijo, clave_prefijo, variable in prefijos:
            if texto.startswith(prefijo):
                valor = texto[len(prefijo):].strip()
                if valor.endswith("..."):
                    valor = valor[:-3]
                return self._t(clave_prefijo, **{variable: valor})

        prefijo_proceso = "El proceso privado de Ollama terminó durante el inicio con código "
        if texto.startswith(prefijo_proceso):
            codigo = texto[len(prefijo_proceso):].rstrip(".")
            return self._t(
                "configuracion.ia.mensaje.proceso_termino",
                codigo=codigo,
            )

        prefijo_servicio = "El servicio privado de Ollama no respondió después de "
        if texto.startswith(prefijo_servicio):
            resto = texto[len(prefijo_servicio):]
            segundos = resto.split(" segundos", 1)[0]
            return self._t(
                "configuracion.ia.mensaje.servicio_no_responde",
                segundos=segundos,
            )

        return texto

    def _traducir_botones_modal_activo(self) -> None:
        modal = QApplication.activeModalWidget()
        if modal is None:
            return

        for boton in modal.findChildren(QPushButton):
            texto = boton.text().strip()
            if texto == "Sí":
                boton.setText(self._t("comun.si"))
            elif texto == "No":
                boton.setText(self._t("comun.no"))

    def _traducir_modal_ia_activo(self) -> None:
        modal = QApplication.activeModalWidget()
        if modal is None:
            return

        titulo = modal.windowTitle()
        titulo_traducido = self._traducir_texto_ia(titulo)
        if titulo_traducido != titulo:
            modal.setWindowTitle(titulo_traducido)

        if isinstance(modal, QMessageBox):
            texto = modal.text()
            texto_traducido = self._traducir_texto_ia(texto)
            if texto_traducido != texto:
                modal.setText(texto_traducido)

            informativo = modal.informativeText()
            if informativo:
                nuevo = self._traducir_texto_ia(informativo)
                if nuevo != informativo:
                    modal.setInformativeText(nuevo)

        for etiqueta in modal.findChildren(QLabel):
            texto = etiqueta.text()
            nuevo = self._traducir_texto_ia(texto)
            if nuevo != texto:
                etiqueta.setText(nuevo)

        for boton in modal.findChildren(QPushButton):
            texto = boton.text().strip()
            if texto in ("OK", "Aceptar"):
                boton.setText(self._t("comun.aceptar"))
            elif texto == "Sí":
                boton.setText(self._t("comun.si"))
            elif texto == "No":
                boton.setText(self._t("comun.no"))
