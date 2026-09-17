# ============================================================
# Archivo: ventana_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene la ventana general de Configuración de TecNet Finder.
#
# Administra:
# - Ventana y apariencia.
# - Tema visual.
# - Editor.
# - Resultados y navegación.
# - Asistencia de IA.
#
# Aplicar y Aceptar trasladan las copias temporales hacia las
# preferencias reales. Cancelar descarta cualquier cambio que
# todavía no hubiera sido confirmado.
# ============================================================

from pathlib import Path  # Permite localizar los recursos gráficos utilizados por la barra.
from PySide6.QtCore import Qt, Signal  # Proporciona opciones de ventana y señales.
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout  # Proporciona los componentes generales.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Comparte la instalación local de IA.
from AsistenteIA.gestor_ollama import GestorOllama  # Comparte el servidor local administrado.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Conserva las preferencias persistentes de IA.
from Interfaz.ventanas.barra_titulo import BarraTitulo  # Reutiliza la barra personalizada.
from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona el engrane inicial utilizado por la ventana de Configuración.
from Interfaz.configuracion.panel_configuracion_editor import PanelConfiguracionEditor  # Importa la categoría Editor.
from Interfaz.configuracion.panel_configuracion_ia_diferida import PanelConfiguracionIADiferida  # Importa la categoría de IA.
from Interfaz.configuracion.panel_configuracion_resultados import PanelConfiguracionResultados  # Importa Resultados y navegación.
from Interfaz.configuracion.panel_configuracion_ventana import PanelConfiguracionVentana  # Importa Ventana y apariencia.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias generales reales.
from Motor.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Mantiene una copia temporal de las preferencias generales.
from Motor.preferencias_tema import PreferenciasTema  # Administra la selección real del tema.
from Motor.preferencias_tema_temporales import PreferenciasTemaTemporales  # Mantiene una copia temporal del tema.


class VentanaConfiguracion(QDialog):  # Representa el diálogo general de Configuración.
    apariencia_cambiada = Signal()  # Solicita reaplicar tema y tipografía después de confirmar cualquiera de ellos.
    ajuste_linea_editor_cambiado = Signal(bool)  # Comunica el ajuste de línea confirmado.
    botones_rapidos_editor_cambiados = Signal(bool)  # Comunica la visibilidad de Pegar y Ejemplos.
    familia_fuente_editor_cambiada = Signal(str)  # Comunica la familia tipográfica confirmada del editor.
    tamano_fuente_editor_cambiado = Signal(int)  # Comunica el tamaño confirmado del editor.
    espacios_tabulacion_editor_cambiados = Signal(int)  # Comunica el ancho visual confirmado de Tab.
    navegacion_errores_cambiada = Signal(bool)  # Comunica la navegación hacia errores.
    navegacion_vlsm_cambiada = Signal(bool)  # Comunica la navegación hacia VLSM.
    advertencias_vlsm_cambiadas = Signal(bool)  # Comunica la modalidad compacta de advertencias.
    advertencias_ventana_cambiadas = Signal(bool)  # Comunica la modalidad independiente de advertencias.
    cerrar_ventana_al_navegar_cambiado = Signal(bool)  # Comunica el comportamiento del doble clic.
    autocompletado_ia_cambiado = Signal(bool)  # Comunica el estado efectivo del autocompletado.
    diagnosticos_ia_cambiados = Signal(bool)  # Comunica el estado efectivo de diagnósticos asistidos.
    servicio_ia_cambiado = Signal(bool)  # Comunica la disponibilidad real de Ollama.

    def __init__(self, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool, preferencias_aplicacion: PreferenciasAplicacion | None = None, preferencias_tema: PreferenciasTema | None = None, padre=None):
        super().__init__(padre)  # Vincula Configuración con la ventana principal.
        self.operacion_en_curso = False  # Protege las operaciones activas de IA.
        self.cerrar_despues_de_operacion = False  # Reserva un cierre solicitado durante una operación.
        self.cierre_confirmado = False  # Distingue cierres procesados mediante botones de un cierre directo.
        self.preferencias_aplicacion = preferencias_aplicacion or PreferenciasAplicacion()  # Conserva las preferencias generales reales.
        self.preferencias_temporales = PreferenciasConfiguracionTemporales(self.preferencias_aplicacion)  # Crea la copia general utilizada por esta sesión.
        self.preferencias_tema = preferencias_tema or PreferenciasTema()  # Conserva la configuración real de tema.
        self.preferencias_tema_temporales = PreferenciasTemaTemporales(self.preferencias_tema)  # Crea la copia temporal específica del tema.
        self.preferencias_ia = preferencias_ia  # Conserva las preferencias reales de IA.
        self.claves_secciones = []  # Relaciona cada sección lateral con una clave estable.

        self.setObjectName("VentanaConfiguracion")  # Identifica el diálogo dentro de los estilos.
        self.setWindowTitle("Configuración")  # Conserva un título reconocible por Windows.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)  # Sustituye la barra nativa por BarraTitulo.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite mantener esquinas exteriores transparentes.
        self.setFixedSize(850, 770)  # Conserva las dimensiones actuales.
        self.setModal(True)  # Impide utilizar simultáneamente varias configuraciones.

        self.setStyleSheet("""
            QDialog#VentanaConfiguracion { background-color: transparent; }
            QFrame#TarjetaConfiguracion QLabel { background-color: #1e1e2e; border: none; border-radius: 7px; padding: 2px 5px; }
            QScrollBar:vertical { background-color: transparent; width: 11px; margin: 4px 2px; border: none; }
            QScrollBar::handle:vertical { background-color: #45475a; min-height: 34px; border: none; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background-color: #585b70; }
            QScrollBar::handle:vertical:pressed { background-color: #6c7086; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background-color: transparent; border: none; height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background-color: transparent; border: none; }
            QScrollBar:horizontal { background-color: transparent; height: 11px; margin: 2px 4px; border: none; }
            QScrollBar::handle:horizontal { background-color: #45475a; min-width: 34px; border: none; border-radius: 5px; }
            QScrollBar::handle:horizontal:hover { background-color: #585b70; }
            QScrollBar::handle:horizontal:pressed { background-color: #6c7086; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background-color: transparent; border: none; width: 0px; }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background-color: transparent; border: none; }
        """)  # Conserva los ajustes particulares de Configuración.

        if padre is not None: self.setWindowIcon(padre.windowIcon())  # Reutiliza el icono oficial de TecNet Finder.
        self._construir_interfaz(gestor_ollama, componente_ia, preferencias_ia, asistencia_disponible_inicial)  # Construye todas las secciones.
        self._actualizar_estado_botones()  # Mantiene Aplicar desactivado inicialmente.

    def _ruta_icono(self) -> Path:
        return ruta_icono_oscuro("Engrane.png")  # Recupera el engrane inicial desde la nueva categoría de iconos oscuros.

    def _centrar_en_area_disponible(self) -> None:
        padre = self.parentWidget()  # Recupera la ventana principal como referencia.
        pantalla = padre.windowHandle().screen() if padre is not None and padre.windowHandle() is not None else self.screen()  # Prefiere el monitor donde se encuentra TecNet Finder.
        pantalla = pantalla or QApplication.primaryScreen()  # Utiliza la pantalla principal únicamente como respaldo.
        if pantalla is None: return  # Mantiene la posición automática si Qt todavía no conoce ningún monitor.
        area = pantalla.availableGeometry()  # Recupera el área útil excluyendo la barra de tareas.
        self.move(area.x() + max(0, (area.width() - self.width()) // 2), area.y() + max(0, (area.height() - self.height()) // 2))  # Centra Configuración en el monitor actual.

    def _construir_interfaz(self, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool) -> None:
        diseno_exterior = QVBoxLayout(self)  # Organiza el marco dentro del área transparente.
        diseno_exterior.setContentsMargins(7, 7, 7, 7)  # Reserva espacio para las esquinas.
        diseno_exterior.setSpacing(0)  # Evita separaciones adicionales.

        self.marco_ventana = QFrame(self)  # Crea la superficie principal visible.
        self.marco_ventana.setObjectName("MarcoVentanaConfiguracion")  # Permite identificar su estilo.
        self.marco_ventana.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza el dibujo del fondo.
        self.marco_ventana.setStyleSheet("QFrame#MarcoVentanaConfiguracion { background-color: #1e1e2e; border: 1px solid #cdd6f4; border-radius: 14px; }")  # Conserva borde y esquinas actuales.
        diseno_exterior.addWidget(self.marco_ventana)  # Añade el marco visible.

        diseno_general = QVBoxLayout(self.marco_ventana)  # Organiza barra, contenido y pie.
        diseno_general.setContentsMargins(1, 1, 1, 1)  # Mantiene visible el borde exterior.
        diseno_general.setSpacing(0)  # Une visualmente las regiones.

        contenedor_barra = QFrame()  # Crea la zona superior.
        contenedor_barra.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza el dibujo.
        contenedor_barra.setStyleSheet("background-color: #181825; border: none; border-top-left-radius: 13px; border-top-right-radius: 13px;")  # Conserva la barra oscura.
        diseno_barra = QVBoxLayout(contenedor_barra)  # Aloja BarraTitulo.
        diseno_barra.setContentsMargins(0, 0, 0, 0)  # Permite ocupar toda la región.
        diseno_barra.setSpacing(0)  # Elimina separación.
        self.barra_titulo = BarraTitulo(ventana=self, ruta_icono=self._ruta_icono(), titulo="Configuración", mostrar_configuracion=False, mostrar_minimizar=False, mostrar_pantalla_completa=False, mostrar_cerrar=True, permitir_arrastre=True)  # Construye la barra personalizada.
        self.barra_titulo.setStyleSheet("QWidget#BarraTitulo { background-color: transparent; border: none; } QLabel { background-color: transparent; border: none; } QLabel#TituloBarra { background-color: transparent; }")  # Mantiene transparente el contenido interno.
        if self.barra_titulo.boton_cerrar is not None:
            self.barra_titulo.boton_cerrar.setObjectName("BotonCerrarConfiguracion")  # Identifica la X propia de este diálogo.
            self.barra_titulo.boton_cerrar.setStyleSheet("""
                QPushButton#BotonCerrarConfiguracion { background-color: transparent; color: #cdd6f4; border: none; border-top-right-radius: 12px; padding: 0px; }
                QPushButton#BotonCerrarConfiguracion:hover { background-color: #c42b1c; color: #ffffff; border: none; border-top-right-radius: 12px; }
                QPushButton#BotonCerrarConfiguracion:pressed { background-color: #a52016; color: #ffffff; border: none; border-top-right-radius: 12px; }
                QPushButton#BotonCerrarConfiguracion:disabled { background-color: transparent; border: none; border-top-right-radius: 12px; }
            """)  # Conserva rojo únicamente para la acción destructiva de cierre.
        diseno_barra.addWidget(self.barra_titulo)  # Añade la barra personalizada.
        diseno_general.addWidget(contenedor_barra)  # Añade toda la región superior.

        separador = QFrame()  # Crea una línea entre barra y contenido.
        separador.setFixedHeight(1)  # Mantiene una división discreta.
        separador.setStyleSheet("background-color: #cdd6f4; border: none;")  # Conserva el tono claro actual.
        diseno_general.addWidget(separador)  # Añade la división.

        contenido = QHBoxLayout()  # Organiza navegación lateral y panel activo.
        contenido.setContentsMargins(0, 0, 0, 0)  # Elimina márgenes adicionales.
        contenido.setSpacing(0)  # Une visualmente ambas zonas.
        self.lista_secciones = QListWidget()  # Crea la navegación lateral.
        self.lista_secciones.setObjectName("ListaConfiguracion")  # Permite aplicar el estilo centralizado.
        self.lista_secciones.setFixedWidth(210)  # Conserva el ancho actual.
        self.lista_secciones.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide desplazamiento horizontal.
        contenido.addWidget(self.lista_secciones)  # Coloca la navegación a la izquierda.
        self.paneles = QStackedWidget()  # Conserva todas las categorías.
        self.paneles.setObjectName("PanelesConfiguracion")  # Permite aplicar el fondo correspondiente.
        contenido.addWidget(self.paneles, 1)  # Entrega el espacio restante a las categorías.
        contenedor_contenido = QFrame()  # Agrupa ambas regiones.
        contenedor_contenido.setLayout(contenido)  # Asigna el diseño horizontal.
        diseno_general.addWidget(contenedor_contenido, 1)  # Hace que el contenido ocupe el espacio restante.

        self.panel_ventana = PanelConfiguracionVentana(self.preferencias_temporales, self.preferencias_tema_temporales, self)  # Construye Ventana y apariencia con ambas copias temporales.
        self._agregar_seccion("Ventana y apariencia", self.panel_ventana, PreferenciasAplicacion.SECCION_VENTANA)  # Registra la primera categoría.
        self.panel_ventana.configuracion_modificada.connect(self._actualizar_estado_botones)  # Detecta cualquier modificación pendiente.

        self.panel_editor = PanelConfiguracionEditor(self.preferencias_temporales, self)  # Construye la categoría Editor.
        self._agregar_seccion("Editor", self.panel_editor, PreferenciasAplicacion.SECCION_EDITOR)  # Registra la segunda categoría.
        self.panel_editor.configuracion_modificada.connect(self._actualizar_estado_botones)  # Detecta modificaciones de editor.

        self.panel_resultados = PanelConfiguracionResultados(self.preferencias_temporales, self)  # Construye Resultados y navegación.
        self._agregar_seccion("Resultados y navegación", self.panel_resultados, PreferenciasAplicacion.SECCION_RESULTADOS)  # Registra la tercera categoría.
        self.panel_resultados.navegacion_errores_cambiada.connect(self._actualizar_estado_botones)  # Detecta cambios de navegación.
        self.panel_resultados.navegacion_vlsm_cambiada.connect(self._actualizar_estado_botones)  # Detecta cambios hacia VLSM.
        self.panel_resultados.advertencias_vlsm_cambiadas.connect(self._actualizar_estado_botones)  # Detecta cambios de avisos compactos.
        self.panel_resultados.advertencias_ventana_cambiadas.connect(self._actualizar_estado_botones)  # Detecta cambios de ventana independiente.
        self.panel_resultados.cerrar_ventana_al_navegar_cambiado.connect(self._actualizar_estado_botones)  # Detecta cambios del doble clic.

        self.panel_ia = PanelConfiguracionIADiferida(gestor_ollama, componente_ia, preferencias_ia, asistencia_disponible_inicial, self)  # Construye Asistencia de IA.
        self._agregar_seccion("Asistencia de IA", self.panel_ia, PreferenciasAplicacion.SECCION_IA)  # Registra la última categoría.
        self.panel_ia.configuracion_modificada.connect(self._actualizar_estado_botones)  # Detecta preferencias pendientes de IA.
        self.panel_ia.autocompletado_cambiado.connect(self.autocompletado_ia_cambiado.emit)  # Reenvía el estado efectivo de autocompletado.
        self.panel_ia.diagnosticos_ia_cambiados.connect(self.diagnosticos_ia_cambiados.emit)  # Reenvía el estado efectivo de diagnósticos.
        self.panel_ia.servicio_cambiado.connect(self.servicio_ia_cambiado.emit)  # Reenvía disponibilidad de Ollama.
        self.panel_ia.operacion_cambiada.connect(self._actualizar_operacion)  # Protege operaciones críticas.

        self.lista_secciones.currentRowChanged.connect(self._cambiar_panel)  # Cambia la categoría visible.
        self.lista_secciones.setCurrentRow(self._obtener_indice_inicial())  # Recupera la categoría inicial.

        pie = QFrame()  # Crea la región inferior de acciones.
        pie.setObjectName("PieConfiguracion")  # Utiliza el estilo centralizado.
        pie.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza el dibujo del fondo.
        diseno_pie = QHBoxLayout(pie)  # Organiza los botones.
        diseno_pie.setContentsMargins(16, 10, 16, 10)  # Mantiene separación exterior.
        diseno_pie.setSpacing(10)  # Separa las acciones.
        diseno_pie.addStretch()  # Empuja las acciones hacia la derecha.
        self.boton_aplicar = QPushButton("Aplicar")  # Confirma sin cerrar.
        self.boton_aplicar.clicked.connect(self._aplicar_desde_boton)  # Ejecuta el guardado.
        diseno_pie.addWidget(self.boton_aplicar)  # Añade Aplicar.
        self.boton_aceptar = QPushButton("Aceptar")  # Confirma y cierra.
        self.boton_aceptar.setObjectName("BotonPrincipal")  # Mantiene Aceptar como acción principal.
        self.boton_aceptar.clicked.connect(self._aceptar_cambios)  # Ejecuta el guardado antes de cerrar.
        diseno_pie.addWidget(self.boton_aceptar)  # Añade Aceptar.
        self.boton_cancelar = QPushButton("Cancelar")  # Descarta los cambios pendientes.
        self.boton_cancelar.clicked.connect(self._cancelar_cambios)  # Cierra sin persistir las copias.
        diseno_pie.addWidget(self.boton_cancelar)  # Añade Cancelar.
        diseno_general.addWidget(pie)  # Coloca finalmente el pie.

    def _agregar_seccion(self, nombre: str, panel, clave: str) -> None:
        elemento = QListWidgetItem(nombre)  # Crea el elemento visible dentro de la navegación.
        elemento.setToolTip(nombre)  # Permite consultar el texto completo.
        self.lista_secciones.addItem(elemento)  # Añade la categoría.
        self.claves_secciones.append(clave)  # Conserva su identificador estable.
        area = QScrollArea()  # Crea una región desplazable.
        area.setObjectName("AreaDesplazamientoConfiguracion")  # Permite identificarla en estilos.
        area.setFrameShape(QFrame.Shape.NoFrame)  # Evita un borde adicional.
        area.setWidgetResizable(True)  # Ajusta el contenido al ancho disponible.
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Evita desplazamiento lateral.
        area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra desplazamiento vertical solamente cuando se necesita.
        area.setStyleSheet("QScrollArea#AreaDesplazamientoConfiguracion { background-color: #1e1e2e; border: none; } QScrollArea#AreaDesplazamientoConfiguracion > QWidget > QWidget { background-color: #1e1e2e; }")  # Integra visualmente el área.
        area.setWidget(panel)  # Coloca la categoría real dentro del scroll.
        self.paneles.addWidget(area)  # Registra el panel siguiendo el mismo orden.

    def _obtener_indice_inicial(self) -> int:
        if not self.preferencias_aplicacion.recordar_seccion_configuracion(): return 0  # Abre siempre la primera categoría cuando esta comodidad está desactivada.
        try: return self.claves_secciones.index(self.preferencias_aplicacion.ultima_seccion_configuracion())  # Busca la categoría persistida.
        except ValueError: return 0  # Recupera la primera sección si la clave ya no existe.

    def _cambiar_panel(self, indice: int) -> None:
        if not 0 <= indice < self.paneles.count(): return  # Descarta posiciones temporales inválidas.
        self.paneles.setCurrentIndex(indice)  # Muestra la categoría seleccionada.
        if self.preferencias_aplicacion.recordar_seccion_configuracion() and indice < len(self.claves_secciones): self.preferencias_aplicacion.establecer_ultima_seccion_configuracion(self.claves_secciones[indice])  # Conserva inmediatamente la sección visitada.

    def _obtener_cambios_generales(self) -> dict[str, list[str]]:
        cambios = {"Ventana y apariencia": [], "Editor": [], "Resultados y navegación": []}  # Prepara el registro de diferencias.
        comparaciones = {
            "Ventana y apariencia": [
                (self.preferencias_temporales.iniciar_maximizado(), self.preferencias_aplicacion.iniciar_maximizado(), "Iniciar TecNet Finder maximizado"),
                (self.preferencias_temporales.recordar_estado_ventana(), self.preferencias_aplicacion.recordar_estado_ventana(), "Recordar el estado de la ventana al cerrar"),
                (self.preferencias_tema_temporales.tema(), self.preferencias_tema.tema(), "Tema de la aplicación"),
                (self.preferencias_temporales.familia_fuente_interfaz(), self.preferencias_aplicacion.familia_fuente_interfaz(), "Familia de fuente de la interfaz"),
                (self.preferencias_temporales.tamano_fuente_interfaz(), self.preferencias_aplicacion.tamano_fuente_interfaz(), "Tamaño base de la interfaz"),
                (self.preferencias_temporales.recordar_seccion_configuracion(), self.preferencias_aplicacion.recordar_seccion_configuracion(), "Abrir Configuración en la última sección visitada"),
            ],
            "Editor": [
                (self.preferencias_temporales.ajuste_linea_editor_activado(), self.preferencias_aplicacion.ajuste_linea_editor_activado(), "Ajuste automático de líneas largas"),
                (self.preferencias_temporales.botones_rapidos_editor_visibles(), self.preferencias_aplicacion.botones_rapidos_editor_visibles(), "Botones rápidos Pegar y Ejemplos"),
                (self.preferencias_temporales.familia_fuente_editor(), self.preferencias_aplicacion.familia_fuente_editor(), "Familia de fuente del editor"),
                (self.preferencias_temporales.tamano_fuente_editor(), self.preferencias_aplicacion.tamano_fuente_editor(), "Tamaño de fuente del editor"),
                (self.preferencias_temporales.espacios_tabulacion_editor(), self.preferencias_aplicacion.espacios_tabulacion_editor(), "Ancho de tabulación"),
            ],
            "Resultados y navegación": [
                (self.preferencias_temporales.navegacion_errores_activada(), self.preferencias_aplicacion.navegacion_errores_activada(), "Navegación automática hacia Errores / Advertencias"),
                (self.preferencias_temporales.navegacion_vlsm_activada(), self.preferencias_aplicacion.navegacion_vlsm_activada(), "Navegación automática hacia Tabla VLSM"),
                (self.preferencias_temporales.advertencias_vlsm_visibles(), self.preferencias_aplicacion.advertencias_vlsm_visibles(), "Mostrar advertencias debajo de Tabla VLSM"),
                (self.preferencias_temporales.advertencias_ventana_independiente(), self.preferencias_aplicacion.advertencias_ventana_independiente(), "Mostrar advertencias en una ventana independiente"),
                (self.preferencias_temporales.cerrar_ventana_advertencias_al_navegar(), self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar(), "Cerrar la ventana de advertencias al ir al código"),
            ],
        }  # Mantiene todas las comparaciones declaradas en un único lugar.
        for seccion, elementos in comparaciones.items():
            for temporal, real, nombre in elementos:
                if temporal != real: cambios[seccion].append(nombre)  # Registra solamente diferencias reales.
        return {seccion: elementos for seccion, elementos in cambios.items() if elementos}  # Elimina categorías vacías.

    def _obtener_todos_los_cambios_pendientes(self) -> dict[str, list[str]]:
        cambios = self._obtener_cambios_generales()  # Recupera las preferencias generales.
        cambios_ia = self.panel_ia.obtener_cambios_pendientes()  # Recupera independientemente la configuración de IA.
        if cambios_ia: cambios["Asistencia de IA"] = cambios_ia  # Integra IA al mismo resumen.
        return cambios  # Devuelve todas las diferencias.

    def _actualizar_estado_botones(self, *_argumentos) -> None:
        if hasattr(self, "boton_aplicar"): self.boton_aplicar.setEnabled(bool(self._obtener_todos_los_cambios_pendientes()) and not self.operacion_en_curso)  # Habilita Aplicar solamente cuando existen diferencias.

    def _aplicar_preferencias_generales(self) -> tuple[dict[str, list[str]], list[str]]:
        cambios_antes = self._obtener_cambios_generales()  # Conserva las diferencias previas para comprobar qué pudo persistirse.

        self.preferencias_aplicacion.establecer_iniciar_maximizado(self.preferencias_temporales.iniciar_maximizado())  # Confirma el estado inicial.
        self.preferencias_aplicacion.establecer_recordar_estado_ventana(self.preferencias_temporales.recordar_estado_ventana())  # Confirma la recuperación entre sesiones.
        self.preferencias_tema.establecer_tema(self.preferencias_tema_temporales.tema())  # Confirma el tema seleccionado.
        self.preferencias_aplicacion.establecer_familia_fuente_interfaz(self.preferencias_temporales.familia_fuente_interfaz())  # Confirma la familia general.
        self.preferencias_aplicacion.establecer_tamano_fuente_interfaz(self.preferencias_temporales.tamano_fuente_interfaz())  # Confirma el tamaño general.
        self.preferencias_aplicacion.establecer_recordar_seccion_configuracion(self.preferencias_temporales.recordar_seccion_configuracion())  # Confirma la recuperación de categoría.
        self.preferencias_aplicacion.establecer_ajuste_linea_editor_activado(self.preferencias_temporales.ajuste_linea_editor_activado())  # Confirma el ajuste de línea.
        self.preferencias_aplicacion.establecer_botones_rapidos_editor_visibles(self.preferencias_temporales.botones_rapidos_editor_visibles())  # Confirma los accesos rápidos.
        self.preferencias_aplicacion.establecer_familia_fuente_editor(self.preferencias_temporales.familia_fuente_editor())  # Confirma la familia del editor.
        self.preferencias_aplicacion.establecer_tamano_fuente_editor(self.preferencias_temporales.tamano_fuente_editor())  # Confirma el tamaño del editor.
        self.preferencias_aplicacion.establecer_espacios_tabulacion_editor(self.preferencias_temporales.espacios_tabulacion_editor())  # Confirma la tabulación.
        self.preferencias_aplicacion.establecer_navegacion_errores_activada(self.preferencias_temporales.navegacion_errores_activada())  # Confirma navegación a errores.
        self.preferencias_aplicacion.establecer_navegacion_vlsm_activada(self.preferencias_temporales.navegacion_vlsm_activada())  # Confirma navegación a VLSM.
        self.preferencias_aplicacion.establecer_cerrar_ventana_advertencias_al_navegar(self.preferencias_temporales.cerrar_ventana_advertencias_al_navegar())  # Confirma el doble clic.
        if self.preferencias_temporales.advertencias_vlsm_visibles(): self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(True)  # Activa la modalidad compacta.
        elif self.preferencias_temporales.advertencias_ventana_independiente(): self.preferencias_aplicacion.establecer_advertencias_ventana_independiente(True)  # Activa la ventana independiente.
        else: self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(False); self.preferencias_aplicacion.establecer_advertencias_ventana_independiente(False)  # Desactiva ambas modalidades.

        cambios_despues = self._obtener_cambios_generales()  # Comprueba las diferencias que continúan después de escribir.
        aplicados, errores = {}, []  # Prepara resumen de éxito y posibles fallos.
        for seccion, elementos in cambios_antes.items():
            pendientes = set(cambios_despues.get(seccion, []))  # Recupera los cambios que todavía continúan pendientes.
            confirmados = [elemento for elemento in elementos if elemento not in pendientes]  # Conserva exclusivamente los valores aplicados.
            if confirmados: aplicados[seccion] = confirmados  # Añade la categoría al resumen solamente cuando contiene cambios satisfactorios.
        for seccion, elementos in cambios_despues.items():
            for elemento in elementos:
                if elemento in cambios_antes.get(seccion, []): errores.append(f"No fue posible guardar: {elemento}.")  # Registra cada preferencia que no pudo persistirse.

        cambios_apariencia = aplicados.get("Ventana y apariencia", [])  # Recupera exclusivamente las preferencias visuales confirmadas.
        if any(nombre in cambios_apariencia for nombre in ("Tema de la aplicación", "Familia de fuente de la interfaz", "Tamaño base de la interfaz")): self.apariencia_cambiada.emit()  # Solicita una actualización global cuando cambia tema o tipografía.

        if cambios_antes.get("Editor"):  # Comprueba si existía alguna modificación relacionada con el editor.
            self.ajuste_linea_editor_cambiado.emit(self.preferencias_aplicacion.ajuste_linea_editor_activado())  # Sincroniza ajuste de línea.
            self.botones_rapidos_editor_cambiados.emit(self.preferencias_aplicacion.botones_rapidos_editor_visibles())  # Sincroniza accesos rápidos.
            self.familia_fuente_editor_cambiada.emit(self.preferencias_aplicacion.familia_fuente_editor())  # Sincroniza familia.
            self.tamano_fuente_editor_cambiado.emit(self.preferencias_aplicacion.tamano_fuente_editor())  # Sincroniza tamaño.
            self.espacios_tabulacion_editor_cambiados.emit(self.preferencias_aplicacion.espacios_tabulacion_editor())  # Sincroniza Tab.

        if cambios_antes.get("Resultados y navegación"):  # Comprueba si debe sincronizar resultados.
            self.navegacion_errores_cambiada.emit(self.preferencias_aplicacion.navegacion_errores_activada())  # Sincroniza navegación a errores.
            self.navegacion_vlsm_cambiada.emit(self.preferencias_aplicacion.navegacion_vlsm_activada())  # Sincroniza navegación a VLSM.
            self.advertencias_vlsm_cambiadas.emit(self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Sincroniza panel compacto.
            self.advertencias_ventana_cambiadas.emit(self.preferencias_aplicacion.advertencias_ventana_independiente())  # Sincroniza ventana independiente.
            self.cerrar_ventana_al_navegar_cambiado.emit(self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Sincroniza comportamiento de navegación.

        if self.preferencias_aplicacion.recordar_seccion_configuracion() and 0 <= self.lista_secciones.currentRow() < len(self.claves_secciones): self.preferencias_aplicacion.establecer_ultima_seccion_configuracion(self.claves_secciones[self.lista_secciones.currentRow()])  # Conserva la categoría actualmente visible.
        return aplicados, errores  # Entrega el resultado de la operación.

    def _aplicar_cambios(self, mostrar_resumen: bool) -> tuple[bool, bool]:
        if not self._obtener_todos_los_cambios_pendientes(): return True, False  # Evita escrituras y diálogos vacíos.
        aplicados, errores = self._aplicar_preferencias_generales()  # Confirma primero las preferencias generales.
        aplicados_ia, errores_ia = self.panel_ia.aplicar_cambios_pendientes()  # Confirma posteriormente las preferencias de IA.
        if aplicados_ia: aplicados["Asistencia de IA"] = aplicados_ia  # Integra IA dentro del mismo resumen.
        errores.extend(errores_ia)  # Une todos los posibles fallos.
        self._actualizar_estado_botones()  # Recalcula Aplicar.
        if mostrar_resumen and aplicados: self._mostrar_resumen_cambios(aplicados)  # Presenta los cambios confirmados.
        if errores: QMessageBox.warning(self, "Configuración", "Algunos cambios no pudieron aplicarse:\n\n" + "\n".join(f"• {error}" for error in errores))  # Informa cualquier fallo.
        return not errores, bool(aplicados)  # Informa el resultado global.

    def _aplicar_desde_boton(self) -> None:
        self._aplicar_cambios(True)  # Confirma los cambios y conserva Configuración abierta.

    def _aceptar_cambios(self) -> None:
        correcto, _ = self._aplicar_cambios(False)  # Confirma preferencias sin mostrar un resumen intermedio.
        if not correcto: return  # Mantiene Configuración abierta ante cualquier fallo.
        if self.operacion_en_curso: self.cerrar_despues_de_operacion = True; return  # Reserva el cierre durante una operación crítica.
        self.cierre_confirmado = True  # Autoriza el cierre convencional.
        super().accept()  # Finaliza el diálogo.

    def _cancelar_cambios(self) -> None:
        if self.operacion_en_curso: return  # Evita cerrar durante una operación crítica.
        self.panel_ia.descartar_cambios_pendientes()  # Recupera las preferencias de IA ya confirmadas.
        self.cierre_confirmado = True  # Marca el cierre como procesado.
        super().reject()  # Descarta automáticamente ambas copias temporales al destruir la ventana.

    def _mostrar_resumen_cambios(self, cambios: dict[str, list[str]]) -> None:
        cantidad = sum(len(elementos) for elementos in cambios.values())  # Cuenta todas las preferencias confirmadas.
        secciones = len(cambios)  # Cuenta las categorías afectadas.
        dialogo = QMessageBox(self)  # Crea el cuadro informativo.
        dialogo.setWindowTitle("Cambios aplicados")  # Identifica el resultado.
        dialogo.setIcon(QMessageBox.Icon.Information)  # Utiliza el icono convencional.
        dialogo.setText(f"Se aplicaron {cantidad} {'cambio' if cantidad == 1 else 'cambios'} en {secciones} {'sección' if secciones == 1 else 'secciones'}.")  # Construye el resumen numérico.
        dialogo.setInformativeText("\n\n".join(seccion + ":\n" + "\n".join(f"• {elemento}" for elemento in elementos) for seccion, elementos in cambios.items()))  # Organiza los detalles por categoría.
        dialogo.setStandardButtons(QMessageBox.StandardButton.Ok)  # Mantiene una única acción.
        boton = dialogo.button(QMessageBox.StandardButton.Ok)  # Recupera el botón generado.
        if boton is not None: boton.setText("Aceptar"); boton.setObjectName("BotonPrincipal")  # Mantiene el cuadro completamente en español y con la acción principal.
        dialogo.exec()  # Presenta el resumen.

    def _actualizar_operacion(self, en_curso: bool) -> None:
        self.operacion_en_curso = bool(en_curso)  # Conserva el estado actual de operaciones de IA.
        self.lista_secciones.setEnabled(not self.operacion_en_curso)  # Bloquea navegación durante operaciones críticas.
        self.boton_aplicar.setEnabled(bool(self._obtener_todos_los_cambios_pendientes()) and not self.operacion_en_curso)  # Mantiene Aplicar coherente.
        self.boton_aceptar.setEnabled(not self.operacion_en_curso)  # Bloquea Aceptar cuando corresponde.
        self.boton_cancelar.setEnabled(not self.operacion_en_curso)  # Bloquea Cancelar cuando corresponde.
        if self.barra_titulo.boton_cerrar is not None: self.barra_titulo.boton_cerrar.setEnabled(not self.operacion_en_curso)  # Protege también la X.
        if not self.operacion_en_curso and self.cerrar_despues_de_operacion: self.cerrar_despues_de_operacion = False; self.cierre_confirmado = True; super().accept()  # Ejecuta un cierre reservado.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt calcule primero la geometría definitiva.
        self._centrar_en_area_disponible()  # Centra después el diálogo.

    def accept(self) -> None:
        self._aceptar_cambios()  # Hace que cualquier aceptación utilice el mismo flujo.

    def reject(self) -> None:
        self._cancelar_cambios()  # Hace que Escape se comporte exactamente como Cancelar.

    def closeEvent(self, evento) -> None:
        if self.cierre_confirmado: evento.accept(); return  # Permite un cierre previamente procesado.
        if self.operacion_en_curso: evento.ignore(); return  # Impide cerrar durante una operación crítica.
        evento.ignore()  # Evita destruir directamente la ventana.
        self._cancelar_cambios()  # Convierte la X en el mismo comportamiento de Cancelar.