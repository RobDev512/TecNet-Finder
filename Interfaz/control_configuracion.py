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
# ============================================================

from PySide6.QtCore import QObject, QTimer  # Permite integrar el controlador con Qt y ejecutar acciones posteriores a la compilación.
from PySide6.QtGui import QFontMetricsF  # Permite calcular el ancho visual de las tabulaciones.
from PySide6.QtWidgets import QPlainTextEdit  # Proporciona los modos oficiales de ajuste de línea.
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

        self.ventana.barra_titulo.boton_configuracion.clicked.connect(self._abrir_configuracion)  # Hace que el engrane abra Configuración.
        self.ventana.panel_resultados.establecer_navegacion_automatica(False)  # Sustituye la antigua navegación general por preferencias independientes.
        self.ventana.panel_resultados.boton_analizar.clicked.connect(self._programar_acciones_post_compilacion)  # Programa las acciones después de compilar.

        self._aplicar_autocompletado(self.asistencia_disponible and self.preferencias_ia.autocompletado_activado())  # Aplica el ghost text efectivo.
        self._aplicar_diagnosticos(self.asistencia_disponible and self.preferencias_ia.diagnosticos_ia_activados())  # Aplica la mejora efectiva de diagnósticos.
        self._aplicar_preferencias_aplicacion()  # Recupera todas las preferencias generales al iniciar.

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
        if visibles:  # Comprueba si deben reaparecer.
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
        if resultado is None or resultado is self.ultimo_resultado_procesado:  # Evita ausencia o duplicados.
            return  # No realiza acciones innecesarias.
        self.ultimo_resultado_procesado = resultado  # Marca el resultado como atendido.
        self._navegar_segun_resultado(resultado)  # Aplica la navegación configurada.
        self._mostrar_ventana_advertencias_si_corresponde(resultado)  # Presenta avisos independientes cuando corresponde.

    def _navegar_segun_resultado(self, resultado) -> None:
        panel = self.ventana.panel_resultados  # Obtiene el panel principal de resultados.
        if resultado.tiene_errores:  # Da prioridad absoluta a errores bloqueantes.
            if not self.navegar_a_errores:  # Comprueba si la navegación fue desactivada.
                return  # Conserva la vista actual.
            panel.setCurrentWidget(panel.tab_entrada_salida)  # Muestra la zona de resultados.
            panel.pestanas_salida.setCurrentWidget(panel.tab_errores)  # Abre Errores / Advertencias.
            self.ventana.panel_diagnosticos.setCurrentIndex(0)  # Mantiene Detectados como vista prioritaria.
            return  # Evita navegar también hacia VLSM.
        if resultado.subredes_vlsm and self.navegar_a_vlsm:  # Comprueba que la compilación válida produzca subredes.
            panel.setCurrentWidget(panel.tab_entrada_salida)  # Muestra la región principal.
            panel.pestanas_salida.setCurrentWidget(panel.tab_vlsm)  # Abre Tabla VLSM.

    def _aplicar_visibilidad_advertencias_vlsm(self, visibles: bool) -> None:
        self.ventana.panel_resultados.establecer_advertencias_compactas(bool(visibles))  # Actualiza la modalidad compacta.

    def _aplicar_ventana_advertencias(self, activada: bool) -> None:
        self.mostrar_advertencias_ventana = bool(activada)  # Conserva la modalidad confirmada.
        if not self.mostrar_advertencias_ventana and self.ventana_advertencias is not None:  # Comprueba si debe cerrarse una ventana existente.
            self.ventana_advertencias.close()  # Retira la ventana.
            self.ventana_advertencias = None  # Elimina su referencia.

    def _mostrar_ventana_advertencias_si_corresponde(self, resultado) -> None:
        if not self.mostrar_advertencias_ventana or resultado.tiene_errores:  # Evita mostrarla cuando está desactivada o existen errores.
            return  # Conserva errores como prioridad.
        advertencias = [diagnostico for diagnostico in resultado.diagnosticos if diagnostico.severidad in ("warning", "advertencia")]  # Conserva únicamente avisos.
        if not advertencias:  # Comprueba si realmente existen advertencias.
            return  # Evita una ventana vacía.
        if self.ventana_advertencias is not None:  # Comprueba si permanece una ventana anterior.
            self.ventana_advertencias.close()  # Retira la versión anterior.
        self.ventana_advertencias = VentanaAdvertencias(advertencias=advertencias, padre=self.ventana)  # Crea la nueva ventana.
        self.ventana_advertencias.advertencia_activada.connect(self._ir_a_advertencia_independiente)  # Permite navegar mediante doble clic.
        self.ventana_advertencias.finished.connect(self._al_cerrar_ventana_advertencias)  # Libera la referencia al terminar.
        self.ventana_advertencias.show()  # Muestra la ventana sin bloquear.
        self.ventana_advertencias.raise_()  # La coloca encima inicialmente.
        self.ventana_advertencias.activateWindow()  # Le entrega el foco inicial.

    def _aplicar_cerrar_ventana_al_navegar(self, cerrar: bool) -> None:
        self.cerrar_ventana_advertencias_al_navegar = bool(cerrar)  # Conserva el comportamiento confirmado.

    def _ir_a_advertencia_independiente(self, diagnostico) -> None:
        if diagnostico.linea is None:  # Comprueba que el aviso pueda localizarse en código.
            return  # Evita una navegación inválida.
        self.ventana.editor_codigo.ir_a_posicion(diagnostico.linea, diagnostico.columna, diagnostico.longitud)  # Selecciona la posición relacionada.
        if self.cerrar_ventana_advertencias_al_navegar and self.ventana_advertencias is not None:  # Comprueba si debe cerrarse.
            self.ventana_advertencias.close()  # Cierra la ventana independiente.
            self.ventana_advertencias = None  # Descarta su referencia.
        elif self.ventana_advertencias is not None:  # Mantiene la ventana cuando así se configuró.
            self.ventana_advertencias.lower()  # La coloca detrás del editor.
        self.ventana.raise_()  # Lleva TecNet Finder al frente.
        self.ventana.activateWindow()  # Recupera el foco general.
        self.ventana.editor_codigo.setFocus()  # Deja listo el editor.

    def _al_cerrar_ventana_advertencias(self, _resultado_dialogo: int) -> None:
        self.ventana_advertencias = None  # Permite crear una nueva ventana posteriormente.

    def _actualizar_servicio(self, disponible: bool) -> None:
        self.asistencia_disponible = bool(disponible)  # Conserva la disponibilidad efectiva de Ollama.

    def _aplicar_autocompletado(self, habilitado: bool) -> None:
        control = self.ventana.editor_codigo.control_autocompletado  # Recupera el controlador del editor.
        control.establecer_habilitado(bool(habilitado))  # Activa o detiene nuevas sugerencias.
        if habilitado:  # Comprueba si debe actualizar la posición actual.
            actualizar = getattr(self.ventana.editor_codigo, "_actualizar_autocompletado", None)  # Recupera la operación existente de forma segura.
            if callable(actualizar):  # Comprueba que siga disponible.
                actualizar()  # Solicita una posible sugerencia inmediatamente.

    def _aplicar_diagnosticos(self, habilitado: bool) -> None:
        self.ventana.panel_diagnosticos.establecer_ia_habilitada(bool(habilitado))  # Activa o desactiva las soluciones asistidas.