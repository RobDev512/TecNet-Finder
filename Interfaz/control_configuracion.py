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
# - Asistencia de IA.
#
# La construcción visual del tema y las fuentes se delega al
# GestorTipografia para mantener este archivo enfocado en la
# coordinación entre componentes.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt  # Permite observar cambios geométricos, temporizar acciones y manejar posiciones.
from PySide6.QtWidgets import QPlainTextEdit, QPushButton  # Proporciona el ajuste de línea y el botón flotante.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Comparte la instalación local de IA.
from AsistenteIA.gestor_ollama import GestorOllama  # Comparte el runtime local administrado.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Comparte las preferencias persistentes de IA.
from Interfaz.gestor_tipografia import GestorTipografia  # Centraliza tema y fuentes.
from Interfaz.ventana_advertencias import VentanaAdvertencias  # Presenta avisos mediante una ventana independiente.
from Interfaz.ventana_configuracion import VentanaConfiguracion  # Importa el diálogo general de Configuración.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias generales persistentes.
from Motor.preferencias_tema import PreferenciasTema  # Administra el tema visual persistente.


class ControlConfiguracion(QObject):  # Coordina Configuración sin intervenir en las fases formales del compilador.
    def __init__(self, ventana, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool, preferencias_aplicacion: PreferenciasAplicacion | None = None):
        super().__init__(ventana)  # Vincula el controlador con la ventana principal.
        self.ventana = ventana  # Conserva acceso al editor y paneles de resultados.
        self.gestor_ollama = gestor_ollama  # Reutiliza el mismo servidor local.
        self.componente_ia = componente_ia  # Reutiliza la instalación detectada.
        self.preferencias_ia = preferencias_ia  # Conserva las decisiones específicas de IA.
        self.preferencias_aplicacion = preferencias_aplicacion or PreferenciasAplicacion()  # Reutiliza las preferencias generales compartidas.
        self.preferencias_tema = PreferenciasTema()  # Conserva una única instancia persistente para la apariencia visual.
        self.gestor_tipografia = GestorTipografia(self.ventana, self.preferencias_aplicacion, self.preferencias_tema)  # Delega tema y fuentes al componente especializado.

        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Conserva la disponibilidad efectiva de Ollama.
        self.navegar_a_errores = True  # Mantiene inicialmente el comportamiento histórico.
        self.navegar_a_vlsm = True  # Mantiene inicialmente navegación hacia VLSM.
        self.mostrar_advertencias_ventana = False  # Mantiene inicialmente desactivada la ventana independiente.
        self.cerrar_ventana_advertencias_al_navegar = True  # Conserva inicialmente el cierre automático.
        self.ventana_advertencias = None  # Conserva una posible ventana de avisos.
        self.ultimo_resultado_procesado = None  # Evita procesar dos veces la misma compilación.
        self.boton_reabrir_advertencias = None  # Reserva la acción flotante.

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(self._abrir_configuracion)  # Hace que el engrane abra Configuración.
        self.ventana.panel_resultados.establecer_navegacion_automatica(False)  # Sustituye la antigua navegación general por preferencias independientes.
        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_acciones_post_compilacion)  # Programa acciones después de compilar.
        self.ventana.editor_codigo.textChanged.connect(self._invalidar_reapertura_advertencias)  # Retira la reapertura cuando cambia el código.
        self._configurar_boton_reabrir_advertencias()  # Construye el acceso flotante.
        self._aplicar_autocompletado(self.asistencia_disponible and self.preferencias_ia.autocompletado_activado())  # Aplica el ghost text efectivo.
        self._aplicar_diagnosticos(self.asistencia_disponible and self.preferencias_ia.diagnosticos_ia_activados())  # Aplica diagnósticos asistidos.
        self._aplicar_preferencias_aplicacion()  # Recupera las preferencias visuales y generales antes de mostrar TecNet Finder.

    # ========================================================
    # Botón flotante de advertencias
    # ========================================================

    def _configurar_boton_reabrir_advertencias(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera el QTabWidget principal.
        self.contenedor_resultados = panel.parentWidget()  # Utiliza el contenedor exterior.
        self.boton_reabrir_advertencias = QPushButton(self.contenedor_resultados)  # Crea una acción libre respecto al layout.
        self.boton_reabrir_advertencias.setObjectName("BotonFlotantePanel")  # Reutiliza la apariencia compacta existente.
        self.boton_reabrir_advertencias.setFixedSize(30, 30)  # Mantiene dimensiones apropiadas.
        self.boton_reabrir_advertencias.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que puede pulsarse.
        self.boton_reabrir_advertencias.setAccessibleName("Ver advertencias de la última compilación")  # Conserva accesibilidad.
        panel._aplicar_icono(self.boton_reabrir_advertencias, "Advertencia.png", 17)  # Utiliza el icono amarillo existente.
        self.boton_reabrir_advertencias.setEnabled(False)  # Impide utilizarlo antes de una compilación válida.
        self.boton_reabrir_advertencias.hide()  # Evita mostrar una acción todavía inútil.
        self.boton_reabrir_advertencias.clicked.connect(self._reabrir_ventana_advertencias)  # Recupera avisos sin recompilar.
        panel.installEventFilter(self)  # Permite recolocar el botón cuando cambia el panel.
        panel.tabBar().installEventFilter(self)  # Permite reajustarlo cuando cambia la barra.
        panel.currentChanged.connect(self._al_cambiar_vista_resultados)  # Actualiza su estado al cambiar pestañas.
        panel.pestanas_salida.currentChanged.connect(self._al_cambiar_vista_resultados)  # Actualiza su estado en pestañas internas.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Espera a que Qt conozca la geometría definitiva.

    def eventFilter(self, objeto, evento) -> bool:
        panel = self.ventana.panel_resultados  # Recupera el panel utilizado como referencia.
        if objeto in (panel, panel.tabBar()) and evento.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Move, QEvent.Type.LayoutRequest): QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Recalcula la posición después del reajuste.
        return super().eventFilter(objeto, evento)  # Conserva el procesamiento habitual.

    def _posicionar_boton_reabrir_advertencias(self) -> None:
        if self.boton_reabrir_advertencias is None: return  # Evita calcular coordenadas antes de construir el botón.
        panel, barra = self.ventana.panel_resultados, self.ventana.panel_resultados.tabBar()  # Recupera panel y barra principal.
        contenedor = self.boton_reabrir_advertencias.parentWidget()  # Recupera el contenedor exterior.
        if contenedor is None: return  # Evita transformar coordenadas sin un padre válido.
        origen_panel = panel.mapTo(contenedor, QPoint(0, 0))  # Convierte el origen del panel al contenedor.
        origen_barra = barra.mapTo(contenedor, QPoint(0, 0))  # Obtiene la posición real de la barra.
        x = origen_panel.x() + panel.width() - self.boton_reabrir_advertencias.width() - 1  # Mantiene el botón respecto al extremo derecho.
        y = origen_barra.y() + (barra.height() - self.boton_reabrir_advertencias.height()) // 2 - 4  # Lo centra y eleva ligeramente.
        self.boton_reabrir_advertencias.move(x, y)  # Aplica las coordenadas.
        self.boton_reabrir_advertencias.raise_()  # Mantiene el botón encima del resto.

    def _al_cambiar_vista_resultados(self, _indice: int) -> None:
        self._actualizar_boton_reabrir_advertencias()  # Recalcula si la acción debe encontrarse disponible.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Reafirma la posición.

    def _viendo_pestana_errores_advertencias(self) -> bool:
        panel = self.ventana.panel_resultados  # Obtiene las dos capas de pestañas.
        return panel.currentWidget() is panel.tab_entrada_salida and panel.pestanas_salida.currentWidget() is panel.tab_errores  # Reconoce exclusivamente la vista detallada de diagnósticos.

    # ========================================================
    # Apertura de Configuración
    # ========================================================

    def _abrir_configuracion(self) -> None:
        ventana_configuracion = VentanaConfiguracion(gestor_ollama=self.gestor_ollama, componente_ia=self.componente_ia, preferencias_ia=self.preferencias_ia, preferencias_aplicacion=self.preferencias_aplicacion, preferencias_tema=self.preferencias_tema, asistencia_disponible_inicial=self.asistencia_disponible, padre=self.ventana)  # Construye Configuración utilizando exactamente las mismas instancias compartidas.

        ventana_configuracion.apariencia_cambiada.connect(self.gestor_tipografia.aplicar)  # Refresca tema y tipografía general después de Aplicar o Aceptar.
        ventana_configuracion.ajuste_linea_editor_cambiado.connect(self._aplicar_ajuste_linea_editor)  # Sincroniza el ajuste de línea.
        ventana_configuracion.botones_rapidos_editor_cambiados.connect(self._aplicar_botones_rapidos_editor)  # Sincroniza los accesos rápidos.
        ventana_configuracion.familia_fuente_editor_cambiada.connect(self.gestor_tipografia.aplicar)  # Refresca la fuente propia del editor.
        ventana_configuracion.tamano_fuente_editor_cambiado.connect(self.gestor_tipografia.aplicar)  # Refresca el tamaño propio del editor.
        ventana_configuracion.espacios_tabulacion_editor_cambiados.connect(self.gestor_tipografia.aplicar)  # Recalcula también la distancia de Tab.
        ventana_configuracion.navegacion_errores_cambiada.connect(self._aplicar_navegacion_errores)  # Sincroniza navegación hacia errores.
        ventana_configuracion.navegacion_vlsm_cambiada.connect(self._aplicar_navegacion_vlsm)  # Sincroniza navegación hacia VLSM.
        ventana_configuracion.advertencias_vlsm_cambiadas.connect(self._aplicar_visibilidad_advertencias_vlsm)  # Sincroniza el panel compacto.
        ventana_configuracion.advertencias_ventana_cambiadas.connect(self._aplicar_ventana_advertencias)  # Sincroniza la ventana independiente.
        ventana_configuracion.cerrar_ventana_al_navegar_cambiado.connect(self._aplicar_cerrar_ventana_al_navegar)  # Sincroniza el comportamiento del doble clic.
        ventana_configuracion.autocompletado_ia_cambiado.connect(self._aplicar_autocompletado)  # Sincroniza Autocompletado.
        ventana_configuracion.diagnosticos_ia_cambiados.connect(self._aplicar_diagnosticos)  # Sincroniza diagnósticos asistidos.
        ventana_configuracion.servicio_ia_cambiado.connect(self._actualizar_servicio)  # Conserva la disponibilidad del servicio.

        self.gestor_tipografia.aplicar()  # Aplica el tema actual también a los controles locales recién creados dentro de Configuración.
        ventana_configuracion.exec()  # Mantiene el diálogo modal hasta que el usuario termine.

    # ========================================================
    # Aplicación inicial de preferencias
    # ========================================================

    def _aplicar_preferencias_aplicacion(self) -> None:
        self.gestor_tipografia.aplicar()  # Recupera tema, fuente global y fuente independiente del editor.
        self._aplicar_ajuste_linea_editor(self.preferencias_aplicacion.ajuste_linea_editor_activado())  # Recupera el ajuste de línea.
        self._aplicar_botones_rapidos_editor(self.preferencias_aplicacion.botones_rapidos_editor_visibles())  # Recupera los accesos rápidos.
        self._aplicar_navegacion_errores(self.preferencias_aplicacion.navegacion_errores_activada())  # Recupera navegación hacia errores.
        self._aplicar_navegacion_vlsm(self.preferencias_aplicacion.navegacion_vlsm_activada())  # Recupera navegación hacia VLSM.
        self._aplicar_visibilidad_advertencias_vlsm(self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Recupera el panel compacto.
        self._aplicar_ventana_advertencias(self.preferencias_aplicacion.advertencias_ventana_independiente())  # Recupera la modalidad independiente.
        self._aplicar_cerrar_ventana_al_navegar(self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Recupera el comportamiento del doble clic.

    # ========================================================
    # Editor
    # ========================================================

    def _aplicar_ajuste_linea_editor(self, activado: bool) -> None:
        self.ventana.editor_codigo.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if activado else QPlainTextEdit.LineWrapMode.NoWrap)  # Aplica el modo seleccionado.

    def _aplicar_botones_rapidos_editor(self, visibles: bool) -> None:
        self.ventana.editor_codigo.boton_pegar.setVisible(bool(visibles))  # Actualiza Pegar.
        self.ventana.editor_codigo.boton_ejemplos.setVisible(bool(visibles))  # Actualiza Ejemplos.
        if visibles: self.ventana.editor_codigo._posicionar_botones_flotantes()  # Recupera correctamente su posición al mostrarlos.

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
        resultado = self.ventana.panel_resultados.resultado_actual  # Recupera la compilación más reciente.
        if resultado is None or resultado is self.ultimo_resultado_procesado: return  # Evita ausencia o procesamiento duplicado.
        self.ultimo_resultado_procesado = resultado  # Marca el resultado como atendido.
        self._navegar_segun_resultado(resultado)  # Aplica navegación configurada.
        self._mostrar_ventana_advertencias_si_corresponde(resultado)  # Actualiza advertencias independientes.

    def _navegar_segun_resultado(self, resultado) -> None:
        panel = self.ventana.panel_resultados  # Recupera el panel principal.
        if resultado.tiene_errores:
            if not self.navegar_a_errores: return  # Conserva la vista actual cuando esta navegación está desactivada.
            panel.setCurrentWidget(panel.tab_entrada_salida)  # Muestra la zona de resultados.
            panel.pestanas_salida.setCurrentWidget(panel.tab_errores)  # Abre Errores / Advertencias.
            self.ventana.panel_diagnosticos.setCurrentIndex(0)  # Mantiene Detectados como vista prioritaria.
            return  # Evita navegar también hacia VLSM.
        if resultado.subredes_vlsm and self.navegar_a_vlsm: panel.setCurrentWidget(panel.tab_entrada_salida); panel.pestanas_salida.setCurrentWidget(panel.tab_vlsm)  # Muestra Tabla VLSM cuando corresponde.

    # ========================================================
    # Advertencias
    # ========================================================

    def _aplicar_visibilidad_advertencias_vlsm(self, visibles: bool) -> None:
        self.ventana.panel_resultados.establecer_advertencias_compactas(bool(visibles))  # Actualiza la modalidad compacta.

    def _aplicar_ventana_advertencias(self, activada: bool) -> None:
        self.mostrar_advertencias_ventana = bool(activada)  # Conserva la modalidad confirmada.
        if not self.mostrar_advertencias_ventana: self._cerrar_ventana_advertencias_actual()  # Retira inmediatamente una ventana abierta.
        self._actualizar_boton_reabrir_advertencias()  # Actualiza disponibilidad de reapertura.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Reafirma su posición.

    def _obtener_advertencias_reabribles(self, resultado=None) -> list:
        resultado = resultado if resultado is not None else self.ventana.panel_resultados.resultado_actual  # Utiliza el resultado recibido o la última compilación vigente.
        if not self.mostrar_advertencias_ventana or resultado is None or resultado.tiene_errores: return []  # Reserva esta modalidad para compilaciones válidas.
        return [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Conserva únicamente recomendaciones no bloqueantes.

    def _actualizar_boton_reabrir_advertencias(self, resultado=None) -> None:
        if self.boton_reabrir_advertencias is None: return  # Evita modificar un control inexistente.
        advertencias = self._obtener_advertencias_reabribles(resultado)  # Recupera contenido reutilizable.
        disponible = bool(advertencias)  # Determina si existe información vigente.
        viendo_diagnosticos = self._viendo_pestana_errores_advertencias()  # Reconoce la vista equivalente.
        self.boton_reabrir_advertencias.setVisible(disponible)  # Oculta la acción cuando no existe contenido.
        self.boton_reabrir_advertencias.setEnabled(disponible and not viendo_diagnosticos)  # La desactiva dentro de la vista equivalente.
        if not disponible: return  # Evita preparar texto innecesario.
        cantidad = len(advertencias)  # Obtiene la cantidad vigente.
        texto = "advertencia" if cantidad == 1 else "advertencias"  # Ajusta singular o plural.
        self.boton_reabrir_advertencias.setToolTip("Ya estás consultando Errores / Advertencias" if viendo_diagnosticos else f"Ver {cantidad} {texto} de la última compilación")  # Explica el estado actual del botón.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Mantiene la posición correcta.

    def _mostrar_ventana_advertencias_si_corresponde(self, resultado) -> None:
        advertencias = self._obtener_advertencias_reabribles(resultado)  # Obtiene avisos compatibles con esta modalidad.
        self._cerrar_ventana_advertencias_actual()  # Retira cualquier ventana perteneciente a una compilación anterior.
        self._actualizar_boton_reabrir_advertencias(resultado)  # Sincroniza la acción.
        if advertencias: self._crear_ventana_advertencias(advertencias)  # Presenta automáticamente los avisos cuando existen.

    def _crear_ventana_advertencias(self, advertencias: list) -> None:
        self.ventana_advertencias = VentanaAdvertencias(advertencias=advertencias, padre=self.ventana)  # Construye la ventana utilizando avisos vigentes.
        self.ventana_advertencias.advertencia_activada.connect(self._ir_a_advertencia_independiente)  # Permite navegar mediante doble clic.
        self.ventana_advertencias.finished.connect(self._al_cerrar_ventana_advertencias)  # Conserva correctamente la referencia.
        self.ventana_advertencias.show()  # Muestra la ventana sin bloquear la principal.
        self.ventana_advertencias.raise_()  # La coloca inicialmente al frente.
        self.ventana_advertencias.activateWindow()  # Entrega el foco inicial.

    def _reabrir_ventana_advertencias(self) -> None:
        if self._viendo_pestana_errores_advertencias(): return  # Evita abrir una representación duplicada.
        advertencias = self._obtener_advertencias_reabribles()  # Recupera las advertencias vigentes.
        if not advertencias: self._actualizar_boton_reabrir_advertencias(); return  # Oculta la acción si dejó de ser válida.
        if self.ventana_advertencias is not None: self.ventana_advertencias.show(); self.ventana_advertencias.raise_(); self.ventana_advertencias.activateWindow(); return  # Recupera una ventana ya existente.
        self._crear_ventana_advertencias(advertencias)  # Reconstruye la ventana sin recompilar.

    def _cerrar_ventana_advertencias_actual(self) -> None:
        ventana_actual = self.ventana_advertencias  # Conserva temporalmente la referencia.
        self.ventana_advertencias = None  # Libera primero la referencia.
        if ventana_actual is not None: ventana_actual.close()  # Cierra solamente la representación visual.

    def _invalidar_reapertura_advertencias(self) -> None:
        self.ultimo_resultado_procesado = None  # Permite procesar normalmente la siguiente compilación.
        self._cerrar_ventana_advertencias_actual()  # Retira una ventana que dejó de corresponder con el código.
        if self.boton_reabrir_advertencias is not None: self.boton_reabrir_advertencias.setEnabled(False); self.boton_reabrir_advertencias.hide()  # Retira la acción hasta otra compilación válida.

    def _aplicar_cerrar_ventana_al_navegar(self, cerrar: bool) -> None:
        self.cerrar_ventana_advertencias_al_navegar = bool(cerrar)  # Conserva el comportamiento confirmado.

    def _ir_a_advertencia_independiente(self, diagnostico) -> None:
        if diagnostico.linea is None: return  # Evita navegación inválida sin ubicación.
        self.ventana.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Selecciona la posición relacionada.
        if self.cerrar_ventana_advertencias_al_navegar and self.ventana_advertencias is not None: self._cerrar_ventana_advertencias_actual()  # Cierra la ventana conservando su posible reapertura.
        elif self.ventana_advertencias is not None: self.ventana_advertencias.lower()  # La coloca detrás cuando debe mantenerse abierta.
        self.ventana.raise_()  # Lleva TecNet Finder al frente.
        self.ventana.activateWindow()  # Recupera el foco general.
        self.ventana.editor_codigo.setFocus()  # Deja listo el editor.

    def _al_cerrar_ventana_advertencias(self, _resultado_dialogo: int) -> None:
        ventana_cerrada = self.sender()  # Obtiene exactamente qué instancia terminó.
        if ventana_cerrada is self.ventana_advertencias: self.ventana_advertencias = None  # Libera exclusivamente la referencia vigente.

    # ========================================================
    # Asistencia de IA
    # ========================================================

    def _actualizar_servicio(self, disponible: bool) -> None:
        self.asistencia_disponible = bool(disponible)  # Conserva la disponibilidad efectiva de Ollama.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        control = self.ventana.editor_codigo.control_autocompletado  # Recupera el controlador del editor.
        control.establecer_habilitado(bool(habilitado))  # Activa o detiene nuevas sugerencias.
        if habilitado:
            actualizar = getattr(self.ventana.editor_codigo, "_actualizar_autocompletado", None)  # Recupera la operación existente de forma segura.
            if callable(actualizar): actualizar()  # Solicita una posible sugerencia inmediatamente.

    def _aplicar_diagnosticos(self, habilitado: bool) -> None:
        self.ventana.panel_diagnosticos.establecer_ia_habilitada(bool(habilitado))  # Activa o desactiva soluciones asistidas.