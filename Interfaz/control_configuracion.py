# ============================================================
# Archivo: control_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Conecta Configuración con la ventana principal de TecNet Finder.
#
# Aplica preferencias del editor, navegación, advertencias e IA
# solamente después de ser confirmadas mediante Aplicar o Aceptar.
#
# También administra la ventana independiente de advertencias y
# permite volver a abrir los avisos pertenecientes a la última
# compilación válida sin ejecutar nuevamente el compilador.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt  # Permite observar cambios de tamaño, convertir posiciones entre widgets y temporizar acciones.
from PySide6.QtGui import QFontMetricsF  # Permite calcular el ancho visual real utilizado por las tabulaciones.
from PySide6.QtWidgets import QPlainTextEdit, QPushButton  # Proporciona el modo de ajuste del editor y el botón de reapertura.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Comparte la instalación local de IA.
from AsistenteIA.gestor_ollama import GestorOllama  # Comparte el runtime local administrado.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Comparte las preferencias persistentes de IA.
from Interfaz.ventana_advertencias import VentanaAdvertencias  # Presenta avisos mediante la modalidad independiente.
from Interfaz.ventana_configuracion import VentanaConfiguracion  # Importa la ventana general de Configuración.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias generales persistentes.


class ControlConfiguracion(QObject):  # Coordina Configuración sin modificar las fases formales del compilador.
    def __init__(self, ventana, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool, preferencias_aplicacion: PreferenciasAplicacion | None = None):
        super().__init__(ventana)  # Vincula el controlador con la ventana principal.
        self.ventana = ventana  # Conserva acceso al editor y paneles de resultados.
        self.gestor_ollama = gestor_ollama  # Reutiliza el mismo servidor local.
        self.componente_ia = componente_ia  # Reutiliza la instalación detectada al iniciar.
        self.preferencias_ia = preferencias_ia  # Conserva las decisiones específicas de IA.
        self.preferencias_aplicacion = preferencias_aplicacion or PreferenciasAplicacion()  # Reutiliza la configuración general compartida.
        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Conserva el estado efectivo de Ollama.
        self.navegar_a_errores = True  # Mantiene inicialmente el comportamiento histórico.
        self.navegar_a_vlsm = True  # Mantiene inicialmente navegación hacia VLSM.
        self.mostrar_advertencias_ventana = False  # Mantiene inicialmente desactivada la ventana independiente.
        self.cerrar_ventana_advertencias_al_navegar = True  # Conserva inicialmente el cierre automático.
        self.ventana_advertencias = None  # Conserva una posible ventana de avisos abierta.
        self.ultimo_resultado_procesado = None  # Evita procesar dos veces una misma compilación.
        self.boton_reabrir_advertencias = None  # Reserva la acción flotante situada en la barra principal de pestañas.

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(self._abrir_configuracion)  # Hace que el engrane abra Configuración.
        self.ventana.panel_resultados.establecer_navegacion_automatica(False)  # Sustituye la antigua navegación general por preferencias independientes.
        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_acciones_post_compilacion)  # Programa las acciones después de compilar.
        self.ventana.editor_codigo.textChanged.connect(self._invalidar_reapertura_advertencias)  # Retira la reapertura en cuanto el código deja de corresponder con la compilación.
        self._configurar_boton_reabrir_advertencias()  # Construye el acceso flotante para recuperar advertencias sin recompilar.

        self._aplicar_autocompletado(self.asistencia_disponible and self.preferencias_ia.autocompletado_activado())  # Aplica el ghost text efectivo.
        self._aplicar_diagnosticos(self.asistencia_disponible and self.preferencias_ia.diagnosticos_ia_activados())  # Aplica la mejora efectiva de diagnósticos.
        self._aplicar_preferencias_aplicacion()  # Recupera todas las preferencias generales al iniciar.

    def _configurar_boton_reabrir_advertencias(self) -> None:
        panel = self.ventana.panel_resultados  # Recupera el QTabWidget principal de resultados.
        self.contenedor_resultados = panel.parentWidget()  # Utiliza el contenedor exterior para permitir que el botón pueda subir ligeramente por encima del límite del QTabWidget.
        self.boton_reabrir_advertencias = QPushButton(self.contenedor_resultados)  # Hace que la acción pueda colocarse libremente alrededor de la barra superior de pestañas.
        self.boton_reabrir_advertencias.setObjectName("BotonFlotantePanel")  # Reutiliza la misma apariencia compacta utilizada por otras acciones.
        self.boton_reabrir_advertencias.setFixedSize(30, 30)  # Mantiene dimensiones apropiadas para la barra superior.
        self.boton_reabrir_advertencias.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el elemento es interactivo.
        self.boton_reabrir_advertencias.setAccessibleName("Ver advertencias de la última compilación")  # Conserva una descripción aunque el control solo muestre un icono.
        panel._aplicar_icono(self.boton_reabrir_advertencias, "Advertencia.png", 17)  # Utiliza el mismo recurso amarillo de la ventana independiente.
        self.boton_reabrir_advertencias.setEnabled(False)  # Impide utilizarlo antes de disponer de una compilación apropiada.
        self.boton_reabrir_advertencias.hide()  # Evita mostrar una acción todavía inútil.
        self.boton_reabrir_advertencias.clicked.connect(self._reabrir_ventana_advertencias)  # Recupera la ventana sin ejecutar nuevamente el compilador.

        panel.installEventFilter(self)  # Permite recolocar el botón cuando cambia el tamaño general del panel.
        panel.tabBar().installEventFilter(self)  # Permite reajustarlo cuando Qt modifica la geometría de la barra de pestañas.
        panel.currentChanged.connect(self._al_cambiar_vista_resultados)  # Actualiza su estado al cambiar entre las pestañas principales.
        panel.pestanas_salida.currentChanged.connect(self._al_cambiar_vista_resultados)  # Actualiza también su estado entre Resumen, VLSM y Errores / Advertencias.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Espera a que Qt conozca las dimensiones definitivas antes de colocarlo.

    def eventFilter(self, objeto, evento) -> bool:
        panel = self.ventana.panel_resultados  # Recupera el panel utilizado como referencia para la posición.
        if objeto in (panel, panel.tabBar()) and evento.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Move, QEvent.Type.LayoutRequest):
            QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Recalcula la posición después de que Qt complete su reajuste.
        return super().eventFilter(objeto, evento)  # Conserva el procesamiento habitual del resto de eventos.

    def _posicionar_boton_reabrir_advertencias(self) -> None:
        if self.boton_reabrir_advertencias is None:
            return  # Evita calcular coordenadas antes de construir el botón.

        panel = self.ventana.panel_resultados  # Recupera el panel completo de resultados.
        barra = panel.tabBar()  # Obtiene la barra Entrada / Salida, Tablas, Sintaxis y Fases posteriores.
        contenedor = self.boton_reabrir_advertencias.parentWidget()  # Recupera el contenedor exterior donde ahora vive el botón.

        if contenedor is None:
            return  # Evita intentar transformar coordenadas sin un widget padre válido.

        origen_panel = panel.mapTo(contenedor, QPoint(0, 0))  # Convierte el origen del QTabWidget al sistema de coordenadas de su contenedor exterior.
        origen_barra = barra.mapTo(contenedor, QPoint(0, 0))  # Obtiene la posición real de la barra dentro del mismo contenedor.

        margen_derecho = 1  # Conserva el ajuste horizontal que ya confirmaste visualmente.
        desplazamiento_vertical = -4  # Eleva realmente el botón porque ahora ya no está limitado por el borde superior del QTabWidget.

        x = origen_panel.x() + panel.width() - self.boton_reabrir_advertencias.width() - margen_derecho  # Mantiene la posición horizontal respecto al extremo derecho del panel.
        y = origen_barra.y() + (barra.height() - self.boton_reabrir_advertencias.height()) // 2 + desplazamiento_vertical  # Centra respecto a la barra y después permite subir físicamente varios píxeles.

        self.boton_reabrir_advertencias.move(x, y)  # Aplica directamente las coordenadas porque el nuevo padre permite utilizar la zona situada encima del panel.
        self.boton_reabrir_advertencias.raise_()  # Mantiene el botón por encima del resto de componentes visuales.

    def _al_cambiar_vista_resultados(self, _indice: int) -> None:
        self._actualizar_boton_reabrir_advertencias()  # Recalcula si la acción debe estar disponible en la nueva vista.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Reafirma su posición después de cualquier cambio de pestaña.

    def _viendo_pestana_errores_advertencias(self) -> bool:
        panel = self.ventana.panel_resultados  # Obtiene las dos capas necesarias para conocer la vista exacta.
        return panel.currentWidget() is panel.tab_entrada_salida and panel.pestanas_salida.currentWidget() is panel.tab_errores  # Solo devuelve verdadero dentro de Entrada / Salida > Errores / Advertencias.

    def _abrir_configuracion(self) -> None:
        ventana_configuracion = VentanaConfiguracion(gestor_ollama=self.gestor_ollama, componente_ia=self.componente_ia, preferencias_ia=self.preferencias_ia, preferencias_aplicacion=self.preferencias_aplicacion, asistencia_disponible_inicial=self.asistencia_disponible, padre=self.ventana)  # Construye Configuración con las mismas instancias compartidas.
        ventana_configuracion.ajuste_linea_editor_cambiado.connect(self._aplicar_ajuste_linea_editor)  # Sincroniza el ajuste confirmado.
        ventana_configuracion.botones_rapidos_editor_cambiados.connect(self._aplicar_botones_rapidos_editor)  # Sincroniza la visibilidad confirmada.
        ventana_configuracion.familia_fuente_editor_cambiada.connect(self._aplicar_familia_fuente_editor)  # Sincroniza la nueva tipografía confirmada.
        ventana_configuracion.tamano_fuente_editor_cambiado.connect(self._aplicar_tamano_fuente_editor)  # Sincroniza el nuevo tamaño.
        ventana_configuracion.espacios_tabulacion_editor_cambiados.connect(self._aplicar_espacios_tabulacion_editor)  # Sincroniza Tab.
        ventana_configuracion.navegacion_errores_cambiada.connect(self._aplicar_navegacion_errores)  # Sincroniza navegación hacia errores.
        ventana_configuracion.navegacion_vlsm_cambiada.connect(self._aplicar_navegacion_vlsm)  # Sincroniza navegación hacia VLSM.
        ventana_configuracion.advertencias_vlsm_cambiadas.connect(self._aplicar_visibilidad_advertencias_vlsm)  # Sincroniza el panel compacto.
        ventana_configuracion.advertencias_ventana_cambiadas.connect(self._aplicar_ventana_advertencias)  # Sincroniza la ventana independiente.
        ventana_configuracion.cerrar_ventana_al_navegar_cambiado.connect(self._aplicar_cerrar_ventana_al_navegar)  # Sincroniza el comportamiento del doble clic.
        ventana_configuracion.autocompletado_ia_cambiado.connect(self._aplicar_autocompletado)  # Sincroniza Autocompletado.
        ventana_configuracion.diagnosticos_ia_cambiados.connect(self._aplicar_diagnosticos)  # Sincroniza soluciones mediante IA.
        ventana_configuracion.servicio_ia_cambiado.connect(self._actualizar_servicio)  # Conserva la disponibilidad del servicio.
        ventana_configuracion.exec()  # Mantiene la ventana modal hasta que el usuario termine.

    def _aplicar_preferencias_aplicacion(self) -> None:
        self._aplicar_ajuste_linea_editor(self.preferencias_aplicacion.ajuste_linea_editor_activado())  # Recupera el ajuste de línea.
        self._aplicar_botones_rapidos_editor(self.preferencias_aplicacion.botones_rapidos_editor_visibles())  # Recupera los accesos rápidos.
        self._aplicar_familia_fuente_editor(self.preferencias_aplicacion.familia_fuente_editor())  # Recupera primero la familia de fuente.
        self._aplicar_tamano_fuente_editor(self.preferencias_aplicacion.tamano_fuente_editor())  # Aplica después su tamaño.
        self._aplicar_espacios_tabulacion_editor(self.preferencias_aplicacion.espacios_tabulacion_editor())  # Calcula Tab utilizando la fuente definitiva.
        self._aplicar_navegacion_errores(self.preferencias_aplicacion.navegacion_errores_activada())  # Recupera navegación hacia errores.
        self._aplicar_navegacion_vlsm(self.preferencias_aplicacion.navegacion_vlsm_activada())  # Recupera navegación hacia VLSM.
        self._aplicar_visibilidad_advertencias_vlsm(self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Recupera el panel compacto.
        self._aplicar_ventana_advertencias(self.preferencias_aplicacion.advertencias_ventana_independiente())  # Recupera la modalidad independiente.
        self._aplicar_cerrar_ventana_al_navegar(self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Recupera el comportamiento del doble clic.

    def _aplicar_ajuste_linea_editor(self, activado: bool) -> None:
        modo = QPlainTextEdit.LineWrapMode.WidgetWidth if activado else QPlainTextEdit.LineWrapMode.NoWrap  # Selecciona el modo correspondiente.
        self.ventana.editor_codigo.setLineWrapMode(modo)  # Aplica el ajuste al editor.

    def _aplicar_botones_rapidos_editor(self, visibles: bool) -> None:
        self.ventana.editor_codigo.boton_pegar.setVisible(bool(visibles))  # Actualiza Pegar.
        self.ventana.editor_codigo.boton_ejemplos.setVisible(bool(visibles))  # Actualiza Ejemplos.
        if visibles:
            self.ventana.editor_codigo._posicionar_botones_flotantes()  # Recupera su posición correcta.

    def _aplicar_familia_fuente_editor(self, familia: str) -> None:
        fuente = self.ventana.editor_codigo.font()  # Copia la fuente actual para conservar tamaño y otras propiedades.
        fuente.setFamily(str(familia))  # Sustituye solamente la familia tipográfica.
        self.ventana.editor_codigo.setFont(fuente)  # Aplica la nueva tipografía al código.
        self.ventana.editor_codigo.actualizar_ancho_area_numeros_linea()  # Recalcula el margen izquierdo según la nueva fuente.
        self._aplicar_espacios_tabulacion_editor(self.preferencias_aplicacion.espacios_tabulacion_editor())  # Recalcula Tab porque su ancho depende de la tipografía.
        self.ventana.editor_codigo.viewport().update()  # Redibuja inmediatamente el editor.

    def _aplicar_tamano_fuente_editor(self, tamano: int) -> None:
        tamano = max(PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MINIMO, min(int(tamano), PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MAXIMO))  # Protege frente a valores externos.
        fuente = self.ventana.editor_codigo.font()  # Copia la fuente aplicada actualmente.
        fuente.setPointSize(tamano)  # Modifica exclusivamente el tamaño.
        self.ventana.editor_codigo.setFont(fuente)  # Aplica el nuevo tamaño.
        self.ventana.editor_codigo.actualizar_ancho_area_numeros_linea()  # Recalcula el área lateral.
        self._aplicar_espacios_tabulacion_editor(self.preferencias_aplicacion.espacios_tabulacion_editor())  # Recalcula la distancia de Tab.
        self.ventana.editor_codigo.viewport().update()  # Actualiza visualmente el contenido.

    def _aplicar_espacios_tabulacion_editor(self, espacios: int) -> None:
        espacios = espacios if espacios in PreferenciasAplicacion.ESPACIOS_TABULACION_VALIDOS else 4  # Corrige cualquier valor inesperado.
        metricas = QFontMetricsF(self.ventana.editor_codigo.font())  # Obtiene las medidas de la fuente actual.
        self.ventana.editor_codigo.setTabStopDistance(metricas.horizontalAdvance(" ") * espacios)  # Convierte la cantidad de espacios en distancia visual.

    def _aplicar_navegacion_errores(self, activada: bool) -> None:
        self.navegar_a_errores = bool(activada)  # Conserva la navegación confirmada.

    def _aplicar_navegacion_vlsm(self, activada: bool) -> None:
        self.navegar_a_vlsm = bool(activada)  # Conserva la navegación confirmada hacia VLSM.

    def _programar_acciones_post_compilacion(self, _comprobado: bool = False) -> None:
        QTimer.singleShot(0, self._procesar_resultado_actual)  # Espera a que PanelResultados termine de actualizarse.

    def _procesar_resultado_actual(self) -> None:
        resultado = self.ventana.panel_resultados.resultado_actual  # Recupera la compilación más reciente.
        if resultado is None or resultado is self.ultimo_resultado_procesado:
            return  # Evita ausencia o procesamiento duplicado.
        self.ultimo_resultado_procesado = resultado  # Marca el resultado como atendido.
        self._navegar_segun_resultado(resultado)  # Aplica la navegación configurada.
        self._mostrar_ventana_advertencias_si_corresponde(resultado)  # Actualiza la ventana independiente y la posibilidad de reabrirla.

    def _navegar_segun_resultado(self, resultado) -> None:
        panel = self.ventana.panel_resultados  # Obtiene el panel principal de resultados.

        if resultado.tiene_errores:
            if not self.navegar_a_errores:
                return  # Conserva la vista actual cuando se desactivó esta navegación.
            panel.setCurrentWidget(panel.tab_entrada_salida)  # Muestra la zona de resultados.
            panel.pestanas_salida.setCurrentWidget(panel.tab_errores)  # Abre Errores / Advertencias.
            self.ventana.panel_diagnosticos.setCurrentIndex(0)  # Mantiene Detectados como vista prioritaria.
            return  # Evita navegar también hacia VLSM.

        if resultado.subredes_vlsm and self.navegar_a_vlsm:
            panel.setCurrentWidget(panel.tab_entrada_salida)  # Muestra la región principal.
            panel.pestanas_salida.setCurrentWidget(panel.tab_vlsm)  # Abre Tabla VLSM.

    def _aplicar_visibilidad_advertencias_vlsm(self, visibles: bool) -> None:
        self.ventana.panel_resultados.establecer_advertencias_compactas(bool(visibles))  # Actualiza la modalidad compacta.

    def _aplicar_ventana_advertencias(self, activada: bool) -> None:
        self.mostrar_advertencias_ventana = bool(activada)  # Conserva la modalidad confirmada.

        if not self.mostrar_advertencias_ventana:
            self._cerrar_ventana_advertencias_actual()  # Retira inmediatamente cualquier ventana cuando la modalidad deja de estar activa.

        self._actualizar_boton_reabrir_advertencias()  # Actualiza la disponibilidad utilizando el resultado vigente.
        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Reafirma la ubicación después del cambio.

    def _obtener_advertencias_reabribles(self, resultado=None) -> list:
        resultado = resultado if resultado is not None else self.ventana.panel_resultados.resultado_actual  # Utiliza el resultado recibido o la última compilación todavía vigente.

        if not self.mostrar_advertencias_ventana or resultado is None or resultado.tiene_errores:
            return []  # Reserva la ventana independiente para compilaciones válidas cuya modalidad se encuentre habilitada.

        return [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Conserva solamente recomendaciones no bloqueantes.

    def _actualizar_boton_reabrir_advertencias(self, resultado=None) -> None:
        if self.boton_reabrir_advertencias is None:
            return  # Evita modificar un control todavía inexistente.

        advertencias = self._obtener_advertencias_reabribles(resultado)  # Comprueba si existe contenido vigente que pueda recuperarse.
        disponible = bool(advertencias)  # Determina si realmente existen advertencias pertenecientes a la última compilación.
        viendo_diagnosticos = self._viendo_pestana_errores_advertencias()  # Reconoce si el usuario ya se encuentra en la vista detallada equivalente.

        self.boton_reabrir_advertencias.setVisible(disponible)  # Oculta completamente la acción mientras no exista información reutilizable.
        self.boton_reabrir_advertencias.setEnabled(disponible and not viendo_diagnosticos)  # La mantiene visible pero desactivada dentro de Errores / Advertencias.

        if not disponible:
            return  # Evita preparar texto para una acción que actualmente no se muestra.

        cantidad = len(advertencias)  # Obtiene la cantidad vigente.
        texto = "advertencia" if cantidad == 1 else "advertencias"  # Ajusta singular o plural.

        if viendo_diagnosticos:
            self.boton_reabrir_advertencias.setToolTip("Ya estás consultando Errores / Advertencias")  # Explica por qué la acción se encuentra desactivada.
        else:
            self.boton_reabrir_advertencias.setToolTip(f"Ver {cantidad} {texto} de la última compilación")  # Explica exactamente qué puede recuperarse.

        QTimer.singleShot(0, self._posicionar_boton_reabrir_advertencias)  # Mantiene el botón anclado correctamente después de aparecer.

    def _mostrar_ventana_advertencias_si_corresponde(self, resultado) -> None:
        advertencias = self._obtener_advertencias_reabribles(resultado)  # Obtiene únicamente los avisos compatibles con la modalidad independiente.
        self._cerrar_ventana_advertencias_actual()  # Retira cualquier ventana perteneciente a una compilación anterior.
        self._actualizar_boton_reabrir_advertencias(resultado)  # Sincroniza la acción con el nuevo resultado.

        if not advertencias:
            return  # Evita crear una ventana cuando la nueva compilación no posee avisos válidos.

        self._crear_ventana_advertencias(advertencias)  # Presenta automáticamente los avisos correspondientes con la compilación recién terminada.

    def _crear_ventana_advertencias(self, advertencias: list) -> None:
        self.ventana_advertencias = VentanaAdvertencias(advertencias=advertencias, padre=self.ventana)  # Construye una ventana utilizando únicamente los avisos vigentes.
        self.ventana_advertencias.advertencia_activada.connect(self._ir_a_advertencia_independiente)  # Permite navegar mediante doble clic.
        self.ventana_advertencias.finished.connect(self._al_cerrar_ventana_advertencias)  # Conserva correctamente la referencia mientras esta instancia siga abierta.
        self.ventana_advertencias.show()  # Muestra la ventana sin bloquear la interfaz principal.
        self.ventana_advertencias.raise_()  # Coloca inicialmente la ventana encima de TecNet Finder.
        self.ventana_advertencias.activateWindow()  # Entrega el foco inicial a los avisos.

    def _reabrir_ventana_advertencias(self) -> None:
        if self._viendo_pestana_errores_advertencias():
            return  # Evita abrir la ventana si el usuario ya consulta la vista completa equivalente.

        advertencias = self._obtener_advertencias_reabribles()  # Recupera las advertencias pertenecientes a la última compilación todavía válida.

        if not advertencias:
            self._actualizar_boton_reabrir_advertencias()  # Oculta la acción si los resultados dejaron de ser reutilizables.
            return

        if self.ventana_advertencias is not None:
            self.ventana_advertencias.show()  # Recupera una ventana que únicamente hubiera quedado detrás de la principal.
            self.ventana_advertencias.raise_()  # Lleva nuevamente los avisos al frente.
            self.ventana_advertencias.activateWindow()  # Devuelve el foco a la ventana ya existente.
            return

        self._crear_ventana_advertencias(advertencias)  # Reconstruye la ventana sin volver a ejecutar ninguna fase del compilador.

    def _cerrar_ventana_advertencias_actual(self) -> None:
        ventana_actual = self.ventana_advertencias  # Conserva temporalmente la referencia para cerrar exactamente esa instancia.
        self.ventana_advertencias = None  # Libera primero la referencia para impedir que un finished tardío afecte a una ventana nueva.

        if ventana_actual is not None:
            ventana_actual.close()  # Cierra únicamente la representación visual; los diagnósticos permanecen en el último resultado.

    def _invalidar_reapertura_advertencias(self) -> None:
        self.ultimo_resultado_procesado = None  # Permite procesar normalmente la siguiente compilación después de cualquier edición.
        self._cerrar_ventana_advertencias_actual()  # Retira una ventana cuyos diagnósticos dejaron de corresponder con el código actual.

        if self.boton_reabrir_advertencias is not None:
            self.boton_reabrir_advertencias.setEnabled(False)  # Impide recuperar información perteneciente a una entrada anterior.
            self.boton_reabrir_advertencias.hide()  # Retira visualmente la acción hasta disponer de otra compilación válida.

    def _aplicar_cerrar_ventana_al_navegar(self, cerrar: bool) -> None:
        self.cerrar_ventana_advertencias_al_navegar = bool(cerrar)  # Conserva el comportamiento confirmado.

    def _ir_a_advertencia_independiente(self, diagnostico) -> None:
        if diagnostico.linea is None:
            return  # Evita una navegación inválida cuando el diagnóstico no posee ubicación.

        self.ventana.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Selecciona la posición relacionada.

        if self.cerrar_ventana_advertencias_al_navegar and self.ventana_advertencias is not None:
            self._cerrar_ventana_advertencias_actual()  # Cierra la ventana pero conserva habilitada su reapertura fuera de la vista detallada.
        elif self.ventana_advertencias is not None:
            self.ventana_advertencias.lower()  # La coloca detrás del editor cuando Configuración solicita conservarla.

        self.ventana.raise_()  # Lleva TecNet Finder al frente.
        self.ventana.activateWindow()  # Recupera el foco general.
        self.ventana.editor_codigo.setFocus()  # Deja listo el editor.

    def _al_cerrar_ventana_advertencias(self, _resultado_dialogo: int) -> None:
        ventana_cerrada = self.sender()  # Obtiene exactamente qué instancia acaba de finalizar.

        if ventana_cerrada is self.ventana_advertencias:
            self.ventana_advertencias = None  # Libera la referencia solamente cuando sigue correspondiendo con la ventana vigente.

    def _actualizar_servicio(self, disponible: bool) -> None:
        self.asistencia_disponible = bool(disponible)  # Conserva la disponibilidad efectiva de Ollama.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        control = self.ventana.editor_codigo.control_autocompletado  # Recupera el controlador del editor.
        control.establecer_habilitado(bool(habilitado))  # Activa o detiene nuevas sugerencias.

        if habilitado:
            actualizar = getattr(self.ventana.editor_codigo, "_actualizar_autocompletado", None)  # Recupera la operación existente de forma segura.

            if callable(actualizar):
                actualizar()  # Solicita una posible sugerencia inmediatamente.

    def _aplicar_diagnosticos(self, habilitado: bool) -> None:
        self.ventana.panel_diagnosticos.establecer_ia_habilitada(bool(habilitado))  # Activa o desactiva las soluciones asistidas.