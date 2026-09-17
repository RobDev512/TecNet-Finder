# ============================================================
# Archivo: control_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Conecta Configuración con la ventana principal de TecNet Finder.
#
# Coordina:
# - Apariencia y tema.
# - Tipografía.
# - Editor.
# - Navegación.
# - Advertencias.
# - Modalidad de la ventana independiente de advertencias.
# - Asistencia de IA.
#
# Configuración se prepara anticipadamente en segundo plano para
# evitar reconstruir todos sus controles al pulsar el engrane.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt  # Permite observar cambios, temporizar acciones y manejar geometría.
from PySide6.QtWidgets import QPlainTextEdit, QPushButton  # Proporciona el ajuste de línea y el botón flotante.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Comparte la instalación local de IA.
from AsistenteIA.gestor_ollama import GestorOllama  # Comparte el runtime local administrado.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Comparte las preferencias persistentes de IA.
from Interfaz.apariencia.gestor_tipografia import GestorTipografia  # Centraliza tema y fuentes.
from Interfaz.ventanas.ventana_advertencias import VentanaAdvertencias  # Presenta avisos mediante una ventana independiente.
from Interfaz.configuracion.ventana_configuracion_extendida import VentanaConfiguracionExtendida  # Añade preferencias especializadas sin aumentar VentanaConfiguracion.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias generales persistentes.
from Motor.preferencias_modalidad_advertencias import PreferenciasModalidadAdvertencias  # Administra exclusivamente el comportamiento modal de Advertencias.
from Motor.preferencias_tema import PreferenciasTema  # Administra el tema visual persistente.


class ControlConfiguracion(QObject):  # Coordina Configuración sin intervenir en las fases formales del compilador.
    def __init__(self, ventana, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool, preferencias_aplicacion: PreferenciasAplicacion | None = None):
        super().__init__(ventana)  # Vincula el controlador con la ventana principal.
        self.ventana = ventana  # Conserva acceso al editor y paneles.
        self.gestor_ollama = gestor_ollama  # Reutiliza el servidor local.
        self.componente_ia = componente_ia  # Reutiliza la instalación detectada.
        self.preferencias_ia = preferencias_ia  # Conserva las decisiones de IA.
        self.preferencias_aplicacion = preferencias_aplicacion or PreferenciasAplicacion()  # Reutiliza las preferencias generales.
        self.preferencias_tema = PreferenciasTema()  # Conserva la configuración visual persistente.
        self.preferencias_modalidad_advertencias = PreferenciasModalidadAdvertencias()  # Conserva independientemente el bloqueo de interacción.
        self.gestor_tipografia = GestorTipografia(self.ventana, self.preferencias_aplicacion, self.preferencias_tema)  # Delega apariencia y tipografía.

        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Conserva disponibilidad efectiva de Ollama.
        self.navegar_a_errores = True  # Mantiene inicialmente el comportamiento histórico.
        self.navegar_a_vlsm = True  # Mantiene navegación hacia VLSM.
        self.mostrar_advertencias_ventana = False  # Mantiene inicialmente desactivada la ventana independiente.
        self.cerrar_ventana_advertencias_al_navegar = True  # Conserva inicialmente el cierre automático.
        self.bloquear_interaccion_ventana_advertencias = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Recupera la nueva modalidad persistente.
        self.ventana_advertencias = None  # Conserva una posible ventana de avisos.
        self.ventana_configuracion_preparada = None  # Conserva la siguiente Configuración ya construida.
        self.ultimo_resultado_procesado = None  # Evita procesar dos veces una compilación.
        self.boton_reabrir_advertencias = None  # Reserva la acción flotante.

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(self._abrir_configuracion)  # Hace que el engrane abra Configuración.
        self.ventana.panel_resultados.establecer_navegacion_automatica(False)  # Sustituye la navegación general por preferencias independientes.
        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_acciones_post_compilacion)  # Programa acciones posteriores.
        self.ventana.editor_codigo.textChanged.connect(self._invalidar_reapertura_advertencias)  # Retira reapertura cuando cambia el código.
        self._configurar_boton_reabrir_advertencias()  # Construye el acceso flotante.
        self._aplicar_autocompletado(self.asistencia_disponible and self.preferencias_ia.autocompletado_activado())  # Aplica ghost text.
        self._aplicar_diagnosticos(self.asistencia_disponible and self.preferencias_ia.diagnosticos_ia_activados())  # Aplica diagnósticos IA.
        self._aplicar_preferencias_aplicacion()  # Recupera todas las preferencias antes de mostrar TecNet Finder.
        QTimer.singleShot(350, self._preparar_ventana_configuracion)  # Construye Configuración después del inicio para acelerar aperturas posteriores.

    # ========================================================
    # Botón flotante de advertencias
    # ========================================================

    def _configurar_boton_reabrir_advertencias(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera el QTabWidget principal.
        self.contenedor_resultados = panel.parentWidget()  # Utiliza el contenedor exterior.
        self.boton_reabrir_advertencias = QPushButton(self.contenedor_resultados)  # Crea una acción libre respecto al layout.
        self.boton_reabrir_advertencias.setObjectName("BotonFlotantePanel")  # Reutiliza la apariencia compacta.
        self.boton_reabrir_advertencias.setProperty("recurso_tema", "Advertencia.png")  # Declara el recurso para seleccionar Advertencia_Claro automáticamente.
        self.boton_reabrir_advertencias.setFixedSize(30, 30)  # Mantiene dimensiones compactas.
        self.boton_reabrir_advertencias.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica interacción.
        self.boton_reabrir_advertencias.setAccessibleName("Ver advertencias de la última compilación")  # Conserva accesibilidad.
        panel._aplicar_icono(self.boton_reabrir_advertencias, "Advertencia.png", 17)  # Coloca inicialmente el recurso histórico.
        self.boton_reabrir_advertencias.setEnabled(False)  # Impide utilizarlo sin compilación.
        self.boton_reabrir_advertencias.hide()  # Evita mostrar una acción todavía inútil.
        self.boton_reabrir_advertencias.clicked.connect(self._reabrir_ventana_advertencias)  # Recupera avisos sin recompilar.
        panel.installEventFilter(self)  # Permite recolocar el botón.
        panel.tabBar().installEventFilter(self)  # Permite reajustarlo con la barra.
        panel.currentChanged.connect(self._al_cambiar_vista_resultados)  # Actualiza su disponibilidad.
        panel.pestanas_salida.currentChanged.connect(self._al_cambiar_vista_resultados)  # Atiende también subpestañas.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Espera la geometría definitiva.

    def eventFilter(self, objeto, evento) -> bool:
        panel = self.ventana.panel_resultados  # Recupera el panel de referencia.
        if objeto in (panel, panel.tabBar()) and evento.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Move, QEvent.Type.LayoutRequest): QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Recalcula la posición.
        return super().eventFilter(objeto, evento)  # Conserva los demás eventos.

    def _posicionar_boton_reabrir_advertencias(self) -> None:
        if self.boton_reabrir_advertencias is None: return  # Evita trabajar antes de construirlo.
        panel, barra = self.ventana.panel_resultados, self.ventana.panel_resultados.tabBar()  # Recupera panel y barra.
        contenedor = self.boton_reabrir_advertencias.parentWidget()  # Recupera la superficie exterior.
        if contenedor is None: return  # Evita transformar coordenadas sin padre.
        origen_panel = panel.mapTo(contenedor, QPoint(0, 0))  # Convierte el origen del panel.
        origen_barra = barra.mapTo(contenedor, QPoint(0, 0))  # Convierte el origen de la barra.
        x = origen_panel.x() + panel.width() - self.boton_reabrir_advertencias.width() - 1  # Lo ancla al extremo derecho.
        y = origen_barra.y() + (barra.height() - self.boton_reabrir_advertencias.height()) // 2 - 4  # Lo centra verticalmente.
        self.boton_reabrir_advertencias.move(x, y)  # Aplica las coordenadas.
        self.boton_reabrir_advertencias.raise_()  # Mantiene el control encima.

    def _al_cambiar_vista_resultados(self, _indice: int) -> None:
        self._actualizar_boton_reabrir_advertencias()  # Recalcula disponibilidad.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Reafirma la posición.

    def _viendo_pestana_errores_advertencias(self) -> bool:
        panel = self.ventana.panel_resultados  # Recupera ambas capas de pestañas.
        return panel.currentWidget() is panel.tab_entrada_salida and panel.pestanas_salida.currentWidget() is panel.tab_errores  # Reconoce exclusivamente Diagnósticos.

    # ========================================================
    # Configuración preparada anticipadamente
    # ========================================================

    def _crear_ventana_configuracion(self) -> VentanaConfiguracionExtendida:
        ventana = VentanaConfiguracionExtendida(gestor_ollama=self.gestor_ollama, componente_ia=self.componente_ia, preferencias_ia=self.preferencias_ia, preferencias_aplicacion=self.preferencias_aplicacion, preferencias_tema=self.preferencias_tema, asistencia_disponible_inicial=self.asistencia_disponible, padre=self.ventana)  # Construye una sesión nueva con la extensión especializada.
        ventana.apariencia_cambiada.connect(self.gestor_tipografia.aplicar)  # Refresca apariencia global.
        ventana.ajuste_linea_editor_cambiado.connect(self._aplicar_ajuste_linea_editor)  # Sincroniza ajuste de línea.
        ventana.botones_rapidos_editor_cambiados.connect(self._aplicar_botones_rapidos_editor)  # Sincroniza accesos rápidos.
        ventana.familia_fuente_editor_cambiada.connect(self.gestor_tipografia.aplicar)  # Refresca familia del editor.
        ventana.tamano_fuente_editor_cambiado.connect(self.gestor_tipografia.aplicar)  # Refresca tamaño del editor.
        ventana.espacios_tabulacion_editor_cambiados.connect(self.gestor_tipografia.aplicar)  # Recalcula Tab.
        ventana.navegacion_errores_cambiada.connect(self._aplicar_navegacion_errores)  # Sincroniza navegación a errores.
        ventana.navegacion_vlsm_cambiada.connect(self._aplicar_navegacion_vlsm)  # Sincroniza navegación a VLSM.
        ventana.advertencias_vlsm_cambiadas.connect(self._aplicar_visibilidad_advertencias_vlsm)  # Sincroniza panel compacto.
        ventana.advertencias_ventana_cambiadas.connect(self._aplicar_ventana_advertencias)  # Sincroniza ventana independiente.
        ventana.cerrar_ventana_al_navegar_cambiado.connect(self._aplicar_cerrar_ventana_al_navegar)  # Sincroniza comportamiento del doble clic.
        ventana.bloquear_interaccion_advertencias_cambiado.connect(self._aplicar_bloqueo_interaccion_advertencias)  # Sincroniza la nueva modalidad modal o no modal.
        ventana.autocompletado_ia_cambiado.connect(self._aplicar_autocompletado)  # Sincroniza autocompletado.
        ventana.diagnosticos_ia_cambiados.connect(self._aplicar_diagnosticos)  # Sincroniza diagnósticos IA.
        ventana.servicio_ia_cambiado.connect(self._actualizar_servicio)  # Conserva disponibilidad de Ollama.
        self.gestor_tipografia.preparar_ventana(ventana)  # Tematiza la ventana mientras permanece invisible.
        return ventana  # Entrega Configuración completamente preparada.

    def _preparar_ventana_configuracion(self) -> None:
        if self.ventana_configuracion_preparada is not None: return  # Evita construir dos sesiones ocultas.
        self.ventana_configuracion_preparada = self._crear_ventana_configuracion()  # Construye anticipadamente la siguiente sesión.

    def _abrir_configuracion(self) -> None:
        if self.ventana_configuracion_preparada is None: self._preparar_ventana_configuracion()  # Construye inmediatamente solamente cuando se abre demasiado pronto.
        ventana = self.ventana_configuracion_preparada  # Recupera la sesión ya preparada.
        self.ventana_configuracion_preparada = None  # La retira del caché mientras está abierta.
        if ventana is None: return  # Protege un fallo excepcional.
        self.gestor_tipografia.preparar_ventana(ventana)  # Reafirma el tema vigente sin recorrer toda la aplicación.
        ventana.exec()  # Mantiene Configuración modal hasta terminar la sesión.
        ventana.deleteLater()  # Destruye la copia utilizada para que Cancelar descarte todos sus temporales.
        QTimer.singleShot(180, self._preparar_ventana_configuracion)  # Prepara otra sesión nueva después de cerrar.

    # ========================================================
    # Aplicación inicial de preferencias
    # ========================================================

    def _aplicar_preferencias_aplicacion(self) -> None:
        self.gestor_tipografia.aplicar()  # Recupera tema y tipografías.
        self._aplicar_ajuste_linea_editor(self.preferencias_aplicacion.ajuste_linea_editor_activado())  # Recupera ajuste de línea.
        self._aplicar_botones_rapidos_editor(self.preferencias_aplicacion.botones_rapidos_editor_visibles())  # Recupera accesos rápidos.
        self._aplicar_navegacion_errores(self.preferencias_aplicacion.navegacion_errores_activada())  # Recupera navegación a errores.
        self._aplicar_navegacion_vlsm(self.preferencias_aplicacion.navegacion_vlsm_activada())  # Recupera navegación a VLSM.
        self._aplicar_visibilidad_advertencias_vlsm(self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Recupera panel compacto.
        self._aplicar_ventana_advertencias(self.preferencias_aplicacion.advertencias_ventana_independiente())  # Recupera ventana independiente.
        self._aplicar_cerrar_ventana_al_navegar(self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Recupera navegación desde Advertencias.
        self._aplicar_bloqueo_interaccion_advertencias(self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo())  # Recupera la nueva modalidad.

    # ========================================================
    # Editor
    # ========================================================

    def _aplicar_ajuste_linea_editor(self, activado: bool) -> None:
        self.ventana.editor_codigo.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if activado else QPlainTextEdit.LineWrapMode.NoWrap)  # Aplica el modo seleccionado.

    def _aplicar_botones_rapidos_editor(self, visibles: bool) -> None:
        self.ventana.editor_codigo.boton_pegar.setVisible(bool(visibles))  # Actualiza Pegar.
        self.ventana.editor_codigo.boton_ejemplos.setVisible(bool(visibles))  # Actualiza Ejemplos.
        if visibles: self.ventana.editor_codigo._posicionar_botones_flotantes()  # Recupera correctamente sus posiciones.

    # ========================================================
    # Navegación posterior a la compilación
    # ========================================================

    def _aplicar_navegacion_errores(self, activada: bool) -> None:
        self.navegar_a_errores = bool(activada)  # Conserva la navegación confirmada.

    def _aplicar_navegacion_vlsm(self, activada: bool) -> None:
        self.navegar_a_vlsm = bool(activada)  # Conserva navegación hacia VLSM.

    def _programar_acciones_post_compilacion(self, _comprobado: bool = False) -> None:
        QTimer.singleShot(0, self._procesar_resultado_actual)  # Espera a que PanelResultados termine de actualizarse.

    def _procesar_resultado_actual(self) -> None:
        resultado = self.ventana.panel_resultados.resultado_actual  # Recupera la compilación reciente.
        if resultado is None or resultado is self.ultimo_resultado_procesado: return  # Evita ausencia o procesamiento duplicado.
        self.ultimo_resultado_procesado = resultado  # Marca el resultado como atendido.
        self._navegar_segun_resultado(resultado)  # Aplica navegación configurada.
        self._mostrar_ventana_advertencias_si_corresponde(resultado)  # Actualiza la ventana independiente.

    def _navegar_segun_resultado(self, resultado) -> None:
        panel = self.ventana.panel_resultados  # Recupera el panel principal.

        if resultado.tiene_errores:
            if not self.navegar_a_errores: return  # Conserva la vista cuando esta navegación está apagada.
            panel.setCurrentWidget(panel.tab_entrada_salida)  # Muestra la zona de resultados.
            panel.pestanas_salida.setCurrentWidget(panel.tab_errores)  # Abre Diagnósticos.
            self.ventana.panel_diagnosticos.setCurrentIndex(0)  # Mantiene Detectados como prioridad.
            return  # Evita navegar también hacia VLSM.

        if resultado.subredes_vlsm and self.navegar_a_vlsm: panel.setCurrentWidget(panel.tab_entrada_salida); panel.pestanas_salida.setCurrentWidget(panel.tab_vlsm)  # Abre Tabla VLSM cuando corresponde.

    # ========================================================
    # Advertencias
    # ========================================================

    def _aplicar_visibilidad_advertencias_vlsm(self, visibles: bool) -> None:
        self.ventana.panel_resultados.establecer_advertencias_compactas(bool(visibles))  # Actualiza la modalidad compacta.

    def _aplicar_ventana_advertencias(self, activada: bool) -> None:
        self.mostrar_advertencias_ventana = bool(activada)  # Conserva la modalidad confirmada.
        if not self.mostrar_advertencias_ventana: self._cerrar_ventana_advertencias_actual()  # Retira una ventana abierta.
        self._actualizar_boton_reabrir_advertencias()  # Actualiza disponibilidad.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Reafirma su posición.

    def _aplicar_cerrar_ventana_al_navegar(self, cerrar: bool) -> None:
        self.cerrar_ventana_advertencias_al_navegar = bool(cerrar)  # Conserva la preferencia existente.

    def _aplicar_bloqueo_interaccion_advertencias(self, bloquear: bool) -> None:
        nuevo_valor = bool(bloquear)  # Normaliza una sola vez la decisión.
        cambio = nuevo_valor != self.bloquear_interaccion_ventana_advertencias  # Comprueba si realmente cambió la modalidad.
        self.bloquear_interaccion_ventana_advertencias = nuevo_valor  # Conserva inmediatamente la nueva decisión.

        if cambio and self.ventana_advertencias is not None:
            self._cerrar_ventana_advertencias_actual()  # Cierra una ventana ya visible para evitar conservar una modalidad híbrida que Qt no permite cambiar correctamente en caliente.
            self._actualizar_boton_reabrir_advertencias()  # Mantiene disponible el botón para reabrirla inmediatamente bajo la nueva modalidad.

    def _configurar_modalidad_ventana_advertencias(self, ventana: VentanaAdvertencias) -> None:
        if self.bloquear_interaccion_ventana_advertencias:
            ventana.setModal(True)  # Convierte Advertencias en diálogo modal.
            ventana.setWindowModality(Qt.WindowModality.WindowModal)  # Bloquea solamente TecNet Finder y no otras aplicaciones de Windows.
        else:
            ventana.setModal(False)  # Permite utilizar simultáneamente la ventana principal.
            ventana.setWindowModality(Qt.WindowModality.NonModal)  # Confirma explícitamente el comportamiento no modal.

    def _obtener_advertencias_reabribles(self, resultado=None) -> list:
        resultado = resultado if resultado is not None else self.ventana.panel_resultados.resultado_actual  # Utiliza el resultado recibido o la última compilación.
        if not self.mostrar_advertencias_ventana or resultado is None or resultado.tiene_errores: return []  # Reserva esta modalidad para compilaciones válidas.
        return [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Conserva únicamente recomendaciones.

    def _actualizar_boton_reabrir_advertencias(self, resultado=None) -> None:
        if self.boton_reabrir_advertencias is None: return  # Evita modificar un control inexistente.
        panel = self.ventana.panel_resultados  # Recupera la capa superior de pestañas.
        advertencias = self._obtener_advertencias_reabribles(resultado)  # Recupera contenido reutilizable.
        disponible = bool(advertencias)  # Determina si existe información vigente.
        en_pestana_principal = panel.currentWidget() is panel.tab_entrada_salida  # Permite mostrar la acción únicamente dentro de Entrada / Salida.
        visible = disponible and en_pestana_principal  # Ignora deliberadamente las subpestañas inferiores según el comportamiento solicitado.
        self.boton_reabrir_advertencias.setVisible(visible)  # Oculta la acción al entrar en Tablas, Sintaxis o Fases posteriores.
        self.boton_reabrir_advertencias.setEnabled(visible)  # Mantiene la acción disponible en cualquier subpestaña de Entrada / Salida.
        if not visible: return  # Evita preparar texto o posición cuando el botón no debe mostrarse.
        cantidad = len(advertencias)  # Obtiene la cantidad vigente.
        texto = "advertencia" if cantidad == 1 else "advertencias"  # Ajusta singular o plural.
        self.boton_reabrir_advertencias.setToolTip(f"Ver {cantidad} {texto} de la última compilación")  # Mantiene un mensaje estable independientemente de la subpestaña inferior.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Mantiene su posición.

    def _mostrar_ventana_advertencias_si_corresponde(self, resultado) -> None:
        advertencias = self._obtener_advertencias_reabribles(resultado)  # Obtiene avisos compatibles.
        self._cerrar_ventana_advertencias_actual()  # Retira una ventana anterior.
        self._actualizar_boton_reabrir_advertencias(resultado)  # Sincroniza la acción.
        if advertencias: self._crear_ventana_advertencias(advertencias)  # Presenta los avisos disponibles.

    def _crear_ventana_advertencias(self, advertencias: list) -> None:
        ventana = VentanaAdvertencias(advertencias=advertencias, padre=self.ventana)  # Construye la ventana todavía invisible.
        self._configurar_modalidad_ventana_advertencias(ventana)  # Decide antes de mostrarla si debe bloquear TecNet Finder.
        ventana.advertencia_activada.connect(self._ir_a_advertencia_independiente)  # Permite navegar mediante doble clic.
        ventana.finished.connect(self._al_cerrar_ventana_advertencias)  # Conserva correctamente la referencia.
        self.gestor_tipografia.preparar_ventana(ventana)  # Aplica tema e iconos antes del primer fotograma visible.
        self.ventana_advertencias = ventana  # Publica la referencia solamente después de prepararla.
        ventana.show()  # Muestra ya tematizada la ventana.
        ventana.raise_()  # La mantiene inicialmente al frente.
        ventana.activateWindow()  # Entrega el foco inicial.

    def _reabrir_ventana_advertencias(self) -> None:
        advertencias = self._obtener_advertencias_reabribles()  # Recupera advertencias vigentes sin depender de la subpestaña inferior seleccionada.

        if not advertencias:
            self._actualizar_boton_reabrir_advertencias()  # Oculta la acción si dejó de ser válida.
            return

        if self.ventana_advertencias is not None:
            self.gestor_tipografia.preparar_ventana(self.ventana_advertencias)  # Reafirma la apariencia antes de mostrarla.
            self.ventana_advertencias.show()  # Recupera la ventana existente.
            self.ventana_advertencias.raise_()  # La mantiene al frente.
            self.ventana_advertencias.activateWindow()  # Recupera el foco.
            return

        self._crear_ventana_advertencias(advertencias)  # Reconstruye la ventana sin recompilar.

    def _cerrar_ventana_advertencias_actual(self) -> None:
        ventana_actual = self.ventana_advertencias  # Conserva temporalmente la referencia.
        self.ventana_advertencias = None  # Libera primero la referencia.
        if ventana_actual is not None: ventana_actual.close()  # Cierra únicamente la representación visual.

    def _invalidar_reapertura_advertencias(self) -> None:
        self.ultimo_resultado_procesado = None  # Permite procesar normalmente la siguiente compilación.
        self._cerrar_ventana_advertencias_actual()  # Retira una ventana que ya no corresponde con el código.

        if self.boton_reabrir_advertencias is not None:
            self.boton_reabrir_advertencias.setEnabled(False)  # Desactiva la acción.
            self.boton_reabrir_advertencias.hide()  # La oculta hasta otra compilación válida.

    def _ir_a_advertencia_independiente(self, diagnostico) -> None:
        if diagnostico.linea is None: return  # Evita navegación inválida.

        ventana_modal = self.ventana_advertencias is not None and self.bloquear_interaccion_ventana_advertencias  # Comprueba si la ventana está bloqueando TecNet Finder.
        if ventana_modal: self._cerrar_ventana_advertencias_actual()  # Una ventana modal debe cerrarse antes de devolver interacción al editor.

        self.ventana.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Selecciona la ubicación relacionada.

        if not ventana_modal:
            if self.cerrar_ventana_advertencias_al_navegar and self.ventana_advertencias is not None: self._cerrar_ventana_advertencias_actual()  # Respeta la preferencia histórica en modalidad no modal.
            elif self.ventana_advertencias is not None: self.ventana_advertencias.lower()  # Mantiene la ventana disponible cuando así se solicitó.

        self.ventana.raise_()  # Lleva TecNet Finder al frente.
        self.ventana.activateWindow()  # Recupera el foco general.
        self.ventana.editor_codigo.setFocus()  # Deja listo el editor.

    def _al_cerrar_ventana_advertencias(self, _resultado_dialogo: int) -> None:
        ventana_cerrada = self.sender()  # Obtiene exactamente qué instancia terminó.
        if ventana_cerrada is self.ventana_advertencias: self.ventana_advertencias = None  # Libera solamente la referencia vigente.

    # ========================================================
    # Asistencia de IA
    # ========================================================

    def _actualizar_servicio(self, disponible: bool) -> None:
        self.asistencia_disponible = bool(disponible)  # Conserva la disponibilidad efectiva de Ollama.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        control = self.ventana.editor_codigo.control_autocompletado  # Recupera el controlador del editor.
        control.establecer_habilitado(bool(habilitado))  # Activa o detiene nuevas sugerencias.
        if habilitado:
            actualizar = getattr(self.ventana.editor_codigo, "_actualizar_autocompletado", None)  # Recupera la operación existente.
            if callable(actualizar): actualizar()  # Solicita una posible sugerencia inmediatamente.

    def _aplicar_diagnosticos(self, habilitado: bool) -> None:
        self.ventana.panel_diagnosticos.establecer_ia_habilitada(bool(habilitado))  # Activa o desactiva soluciones asistidas.