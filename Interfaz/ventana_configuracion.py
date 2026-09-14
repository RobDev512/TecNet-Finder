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
# - Editor.
# - Resultados y navegación.
# - Asistencia de IA.
#
# También administra Aplicar, Aceptar y Cancelar, conserva un
# registro de cambios pendientes y utiliza scrollbars propios
# coherentes con el diseño oscuro de la aplicación.
# ============================================================

from pathlib import Path  # Permite localizar el engrane utilizado por la barra personalizada.
from PySide6.QtCore import Qt, Signal  # Permite controlar la ventana y comunicar preferencias confirmadas.
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout  # Importa los componentes generales.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Comparte la instalación local de IA.
from AsistenteIA.gestor_ollama import GestorOllama  # Comparte el servidor local administrado.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Conserva las preferencias reales de IA.
from Interfaz.barra_titulo import BarraTitulo  # Reutiliza la barra personalizada.
from Interfaz.panel_configuracion_editor import PanelConfiguracionEditor  # Importa la categoría Editor.
from Interfaz.panel_configuracion_ia_diferida import PanelConfiguracionIADiferida  # Importa la variante diferida de IA.
from Interfaz.panel_configuracion_resultados import PanelConfiguracionResultados  # Importa Resultados y navegación.
from Interfaz.panel_configuracion_ventana import PanelConfiguracionVentana  # Importa Ventana y apariencia.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias realmente persistidas.
from Motor.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Administra las decisiones todavía pendientes.


class VentanaConfiguracion(QDialog):  # Representa Configuración completa.
    ajuste_linea_editor_cambiado = Signal(bool)  # Comunica el ajuste de línea confirmado.
    botones_rapidos_editor_cambiados = Signal(bool)  # Comunica la visibilidad confirmada de Pegar y Ejemplos.
    familia_fuente_editor_cambiada = Signal(str)  # Comunica la familia tipográfica confirmada.
    tamano_fuente_editor_cambiado = Signal(int)  # Comunica el tamaño de fuente confirmado.
    espacios_tabulacion_editor_cambiados = Signal(int)  # Comunica el ancho confirmado de una tabulación.
    navegacion_errores_cambiada = Signal(bool)  # Comunica la navegación confirmada hacia errores.
    navegacion_vlsm_cambiada = Signal(bool)  # Comunica la navegación confirmada hacia Tabla VLSM.
    advertencias_vlsm_cambiadas = Signal(bool)  # Comunica la modalidad compacta confirmada.
    advertencias_ventana_cambiadas = Signal(bool)  # Comunica la modalidad independiente confirmada.
    cerrar_ventana_al_navegar_cambiado = Signal(bool)  # Comunica el comportamiento confirmado del doble clic.
    autocompletado_ia_cambiado = Signal(bool)  # Comunica el estado efectivo del autocompletado.
    diagnosticos_ia_cambiados = Signal(bool)  # Comunica el estado efectivo de diagnósticos asistidos.
    servicio_ia_cambiado = Signal(bool)  # Comunica la disponibilidad real de Ollama.

    def __init__(self, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool, preferencias_aplicacion: PreferenciasAplicacion | None = None, padre=None):
        super().__init__(padre)  # Vincula Configuración con la ventana principal.
        self.operacion_en_curso = False  # Protege operaciones activas de IA.
        self.cerrar_despues_de_operacion = False  # Reserva la posibilidad de terminar Aceptar después de una transición de servicio.
        self.cierre_confirmado = False  # Distingue un cierre procesado de un clic directo sobre la X.
        self.preferencias_aplicacion = preferencias_aplicacion or PreferenciasAplicacion()  # Conserva las preferencias reales compartidas.
        self.preferencias_temporales = PreferenciasConfiguracionTemporales(self.preferencias_aplicacion)  # Crea la copia editable de esta sesión.
        self.preferencias_ia = preferencias_ia  # Conserva las preferencias persistentes de IA.
        self.claves_secciones = []  # Relaciona cada sección lateral con una clave estable.

        self.setObjectName("VentanaConfiguracion")  # Identifica este diálogo dentro de los estilos.
        self.setWindowTitle("Configuración")  # Conserva un título reconocible por Windows.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)  # Sustituye la barra nativa por BarraTitulo.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite conservar las esquinas exteriores transparentes.
        self.setFixedSize(850, 770)  # Mantiene las dimensiones acordadas.
        self.setModal(True)  # Impide abrir varias configuraciones simultáneamente.

        self.setStyleSheet("""
            QDialog#VentanaConfiguracion {
                background-color: transparent;
            }

            QFrame#TarjetaConfiguracion QLabel {
                background-color: #1e1e2e;
                border: none;
                border-radius: 7px;
                padding: 2px 5px;
            }

            QScrollBar:vertical {
                background-color: transparent;
                width: 11px;
                margin: 4px 2px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background-color: #45475a;
                min-height: 34px;
                border: none;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #585b70;
            }

            QScrollBar::handle:vertical:pressed {
                background-color: #6c7086;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background-color: transparent;
                border: none;
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background-color: transparent;
                border: none;
            }

            QScrollBar:horizontal {
                background-color: transparent;
                height: 11px;
                margin: 2px 4px;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background-color: #45475a;
                min-width: 34px;
                border: none;
                border-radius: 5px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #585b70;
            }

            QScrollBar::handle:horizontal:pressed {
                background-color: #6c7086;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                background-color: transparent;
                border: none;
                width: 0px;
            }

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background-color: transparent;
                border: none;
            }
        """)  # Redondea todos los QLabel internos de tarjetas y sustituye las barras nativas por scrollbars modernos sin flechas.

        if padre is not None:  # Comprueba si Configuración tiene una ventana propietaria.
            self.setWindowIcon(padre.windowIcon())  # Conserva el icono oficial para Windows y la barra de tareas.

        self._construir_interfaz(gestor_ollama, componente_ia, preferencias_ia, asistencia_disponible_inicial)  # Construye barra, categorías y pie.
        self._actualizar_estado_botones()  # Mantiene Aplicar desactivado mientras no existan modificaciones.

    def _ruta_icono(self) -> Path:
        return Path(__file__).resolve().parent.parent / "Recursos" / "Iconos" / "Engrane.png"  # Reutiliza exactamente el engrane blanco utilizado por el botón principal.

    def _centrar_en_area_disponible(self) -> None:
        padre = self.parentWidget()  # Recupera TecNet Finder como referencia para elegir monitor.
        pantalla = padre.windowHandle().screen() if padre is not None and padre.windowHandle() is not None else self.screen()  # Prefiere la pantalla donde se encuentra la aplicación.
        pantalla = pantalla or QApplication.primaryScreen()  # Utiliza la pantalla principal únicamente como respaldo.
        if pantalla is None:  # Comprueba que Qt haya detectado alguna pantalla.
            return  # Conserva la posición automática cuando no existe información geométrica.
        area = pantalla.availableGeometry()  # Recupera el área disponible excluyendo la barra de tareas.
        self.move(area.x() + max(0, (area.width() - self.width()) // 2), area.y() + max(0, (area.height() - self.height()) // 2))  # Centra Configuración dentro de la pantalla actual.

    def _construir_interfaz(self, gestor_ollama: GestorOllama, componente_ia: GestorComponenteIA, preferencias_ia: PreferenciasIA, asistencia_disponible_inicial: bool) -> None:
        diseno_exterior = QVBoxLayout(self)  # Organiza el marco visible dentro de la región transparente.
        diseno_exterior.setContentsMargins(7, 7, 7, 7)  # Reserva una pequeña zona para las esquinas exteriores.
        diseno_exterior.setSpacing(0)  # Evita espacios adicionales.

        self.marco_ventana = QFrame(self)  # Crea la superficie visible principal.
        self.marco_ventana.setObjectName("MarcoVentanaConfiguracion")  # Permite estilizar exclusivamente el marco.
        self.marco_ventana.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza el dibujo correcto del fondo.
        self.marco_ventana.setStyleSheet("QFrame#MarcoVentanaConfiguracion { background-color: #1e1e2e; border: 1px solid #cdd6f4; border-radius: 14px; }")  # Mantiene el borde exterior redondeado.
        diseno_exterior.addWidget(self.marco_ventana)  # Coloca la superficie dentro del diálogo.

        diseno_general = QVBoxLayout(self.marco_ventana)  # Organiza barra, área central y pie.
        diseno_general.setContentsMargins(1, 1, 1, 1)  # Mantiene visible el borde exterior.
        diseno_general.setSpacing(0)  # Une visualmente las tres regiones.

        contenedor_barra = QFrame()  # Crea el fondo de la zona superior.
        contenedor_barra.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza el dibujo de sus esquinas.
        contenedor_barra.setStyleSheet("background-color: #181825; border: none; border-top-left-radius: 13px; border-top-right-radius: 13px;")  # Conserva el tono oscuro de la barra.
        diseno_barra = QVBoxLayout(contenedor_barra)  # Aloja BarraTitulo dentro del fondo.
        diseno_barra.setContentsMargins(0, 0, 0, 0)  # Permite que ocupe toda la región.
        diseno_barra.setSpacing(0)  # Elimina separación innecesaria.

        self.barra_titulo = BarraTitulo(ventana=self, ruta_icono=self._ruta_icono(), titulo="Configuración", mostrar_configuracion=False, mostrar_minimizar=False, mostrar_pantalla_completa=False, mostrar_cerrar=True, permitir_arrastre=True)  # Construye la barra con el engrane blanco.
        self.barra_titulo.setStyleSheet("QWidget#BarraTitulo { background-color: transparent; border: none; } QLabel { background-color: transparent; border: none; } QLabel#TituloBarra { background-color: transparent; }")  # Mantiene transparente el fondo del engrane y del título.

        if self.barra_titulo.boton_cerrar is not None:  # Comprueba que esta barra realmente incluya una X.
            self.barra_titulo.boton_cerrar.setObjectName("BotonCerrarConfiguracion")  # Permite estilizar exclusivamente este botón.
            self.barra_titulo.boton_cerrar.setStyleSheet("""
                QPushButton#BotonCerrarConfiguracion { background-color: transparent; color: #cdd6f4; border: none; border-top-right-radius: 12px; padding: 0px; }
                QPushButton#BotonCerrarConfiguracion:hover { background-color: #c42b1c; color: #ffffff; border: none; border-top-right-radius: 12px; }
                QPushButton#BotonCerrarConfiguracion:pressed { background-color: #a52016; color: #ffffff; border: none; border-top-right-radius: 12px; }
                QPushButton#BotonCerrarConfiguracion:disabled { background-color: transparent; border: none; border-top-right-radius: 12px; }
            """)  # Mantiene la respuesta visual roja sin perder la esquina exterior.

        diseno_barra.addWidget(self.barra_titulo)  # Coloca BarraTitulo dentro de su región.
        diseno_general.addWidget(contenedor_barra)  # Incorpora la zona superior completa.

        separador = QFrame()  # Crea una línea entre barra y contenido.
        separador.setFixedHeight(1)  # Mantiene una división visual discreta.
        separador.setStyleSheet("background-color: #cdd6f4; border: none;")  # Utiliza el mismo tono claro del borde.
        diseno_general.addWidget(separador)  # Coloca la división debajo de la barra.

        contenido = QHBoxLayout()  # Organiza navegación lateral y categoría activa.
        contenido.setContentsMargins(0, 0, 0, 0)  # Elimina márgenes internos.
        contenido.setSpacing(0)  # Une visualmente ambas zonas.

        self.lista_secciones = QListWidget()  # Crea la navegación lateral.
        self.lista_secciones.setObjectName("ListaConfiguracion")  # Mantiene el estilo actual de la lista.
        self.lista_secciones.setFixedWidth(210)  # Conserva el ancho acordado.
        self.lista_secciones.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide desplazamiento horizontal.
        contenido.addWidget(self.lista_secciones)  # Coloca la navegación a la izquierda.

        self.paneles = QStackedWidget()  # Conserva todas las categorías registradas.
        self.paneles.setObjectName("PanelesConfiguracion")  # Permite mantener el estilo general.
        contenido.addWidget(self.paneles, 1)  # Entrega todo el espacio restante a la categoría activa.

        contenedor_contenido = QFrame()  # Agrupa navegación y panel.
        contenedor_contenido.setLayout(contenido)  # Asigna el diseño horizontal.
        diseno_general.addWidget(contenedor_contenido, 1)  # Hace que el área central ocupe todo el alto disponible.

        self.panel_ventana = PanelConfiguracionVentana(self.preferencias_temporales, self)  # Construye Ventana y apariencia utilizando valores temporales.
        self._agregar_seccion("Ventana y apariencia", self.panel_ventana, PreferenciasAplicacion.SECCION_VENTANA)  # Registra la primera categoría.
        for casilla in (self.panel_ventana.casilla_iniciar_maximizado, self.panel_ventana.casilla_recordar_estado, self.panel_ventana.casilla_recordar_seccion):  # Recorre sus tres preferencias.
            casilla.toggled.connect(self._actualizar_estado_botones)  # Actualiza Aplicar cuando alguna cambia.

        self.panel_editor = PanelConfiguracionEditor(self.preferencias_temporales, self)  # Construye la categoría Editor.
        self._agregar_seccion("Editor", self.panel_editor, PreferenciasAplicacion.SECCION_EDITOR)  # Registra Editor después de Ventana.
        self.panel_editor.configuracion_modificada.connect(self._actualizar_estado_botones)  # Detecta cualquier preferencia del editor modificada.

        self.panel_resultados = PanelConfiguracionResultados(self.preferencias_temporales, self)  # Construye Resultados y navegación.
        self._agregar_seccion("Resultados y navegación", self.panel_resultados, PreferenciasAplicacion.SECCION_RESULTADOS)  # Registra la tercera categoría.
        self.panel_resultados.navegacion_errores_cambiada.connect(self._actualizar_estado_botones)  # Detecta navegación hacia errores.
        self.panel_resultados.navegacion_vlsm_cambiada.connect(self._actualizar_estado_botones)  # Detecta navegación hacia VLSM.
        self.panel_resultados.advertencias_vlsm_cambiadas.connect(self._actualizar_estado_botones)  # Detecta cambios del panel compacto.
        self.panel_resultados.advertencias_ventana_cambiadas.connect(self._actualizar_estado_botones)  # Detecta cambios de la ventana independiente.
        self.panel_resultados.cerrar_ventana_al_navegar_cambiado.connect(self._actualizar_estado_botones)  # Detecta cambios del doble clic.

        self.panel_ia = PanelConfiguracionIADiferida(gestor_ollama, componente_ia, preferencias_ia, asistencia_disponible_inicial, self)  # Construye Asistencia de IA conservando operaciones físicas inmediatas.
        self._agregar_seccion("Asistencia de IA", self.panel_ia, PreferenciasAplicacion.SECCION_IA)  # Registra la última categoría.
        self.panel_ia.configuracion_modificada.connect(self._actualizar_estado_botones)  # Detecta preferencias de IA todavía pendientes.
        self.panel_ia.autocompletado_cambiado.connect(self.autocompletado_ia_cambiado.emit)  # Reenvía el estado efectivo de autocompletado.
        self.panel_ia.diagnosticos_ia_cambiados.connect(self.diagnosticos_ia_cambiados.emit)  # Reenvía el estado efectivo de diagnósticos.
        self.panel_ia.servicio_cambiado.connect(self.servicio_ia_cambiado.emit)  # Reenvía disponibilidad del servicio.
        self.panel_ia.operacion_cambiada.connect(self._actualizar_operacion)  # Bloquea Configuración durante operaciones críticas.

        self.lista_secciones.currentRowChanged.connect(self._cambiar_panel)  # Cambia la categoría cuando el usuario selecciona otra opción.
        self.lista_secciones.setCurrentRow(self._obtener_indice_inicial())  # Recupera la última categoría cuando corresponde.

        pie = QFrame()  # Crea la región inferior de acciones.
        pie.setObjectName("PieConfiguracion")  # Aplica únicamente al contenedor el estilo del pie definido de forma centralizada en estilos.py.
        pie.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt dibuje correctamente el fondo y las esquinas redondeadas del pie.
        diseno_pie = QHBoxLayout(pie)  # Organiza Aplicar, Aceptar y Cancelar.
        diseno_pie.setContentsMargins(16, 10, 16, 10)  # Mantiene espacio respecto con los bordes.
        diseno_pie.setSpacing(10)  # Separa uniformemente las acciones.
        diseno_pie.addStretch()  # Empuja los botones hacia el extremo derecho.

        self.boton_aplicar = QPushButton("Aplicar")  # Confirma cambios sin cerrar Configuración.
        self.boton_aplicar.clicked.connect(self._aplicar_desde_boton)  # Ejecuta el guardado y muestra el resumen.
        diseno_pie.addWidget(self.boton_aplicar)  # Añade Aplicar.

        self.boton_aceptar = QPushButton("Aceptar")  # Confirma cambios y cierra la ventana.
        self.boton_aceptar.setObjectName("BotonPrincipal")  # Destaca Aceptar como acción principal.
        self.boton_aceptar.clicked.connect(self._aceptar_cambios)  # Ejecuta el mismo guardado antes de cerrar.
        diseno_pie.addWidget(self.boton_aceptar)  # Añade Aceptar.

        self.boton_cancelar = QPushButton("Cancelar")  # Descarta únicamente los cambios todavía pendientes.
        self.boton_cancelar.clicked.connect(self._cancelar_cambios)  # Cierra Configuración sin guardar la copia temporal.
        diseno_pie.addWidget(self.boton_cancelar)  # Añade Cancelar.

        diseno_general.addWidget(pie)  # Coloca finalmente la región inferior.

    def _agregar_seccion(self, nombre: str, panel, clave: str) -> None:
        elemento = QListWidgetItem(nombre)  # Crea el elemento visible dentro de la navegación lateral.
        elemento.setToolTip(nombre)  # Permite consultar el nombre completo cuando aparezca recortado.
        self.lista_secciones.addItem(elemento)  # Añade la categoría a la lista.
        self.claves_secciones.append(clave)  # Conserva una clave estable independiente de la posición.

        area = QScrollArea()  # Crea una región desplazable para la categoría.
        area.setObjectName("AreaDesplazamientoConfiguracion")  # Permite identificar todos los scrolls del área principal.
        area.setFrameShape(QFrame.Shape.NoFrame)  # Evita introducir un borde adicional.
        area.setWidgetResizable(True)  # Adapta el contenido al ancho disponible.
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide desplazamiento horizontal.
        area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra la nueva barra vertical únicamente cuando sea necesaria.
        area.setStyleSheet("QScrollArea#AreaDesplazamientoConfiguracion { background-color: #1e1e2e; border: none; } QScrollArea#AreaDesplazamientoConfiguracion > QWidget > QWidget { background-color: #1e1e2e; }")  # Integra visualmente el área con el fondo general.
        area.setWidget(panel)  # Coloca el panel real dentro de la zona desplazable.
        self.paneles.addWidget(area)  # Registra la categoría dentro del mismo orden de la navegación.

    def _obtener_indice_inicial(self) -> int:
        if not self.preferencias_aplicacion.recordar_seccion_configuracion():  # Comprueba si debe ignorarse la última categoría.
            return 0  # Abre siempre Ventana y apariencia.
        try:  # Intenta localizar la clave almacenada dentro del orden actual.
            return self.claves_secciones.index(self.preferencias_aplicacion.ultima_seccion_configuracion())  # Devuelve la posición correspondiente.
        except ValueError:  # Protege la aplicación si una categoría desapareció.
            return 0  # Recupera la primera sección.

    def _cambiar_panel(self, indice: int) -> None:
        if not 0 <= indice < self.paneles.count():  # Comprueba que la posición corresponda con una categoría válida.
            return  # Descarta valores temporales inválidos.
        self.paneles.setCurrentIndex(indice)  # Muestra la categoría seleccionada.
        if self.preferencias_aplicacion.recordar_seccion_configuracion() and indice < len(self.claves_secciones):  # Comprueba si la navegación interna debe persistirse.
            self.preferencias_aplicacion.establecer_ultima_seccion_configuracion(self.claves_secciones[indice])  # Conserva su clave estable.

    def _obtener_cambios_generales(self) -> dict[str, list[str]]:
        cambios = {"Ventana y apariencia": [], "Editor": [], "Resultados y navegación": []}  # Prepara el registro organizado por sección.
        comparaciones = {
            "Ventana y apariencia": [
                (self.preferencias_temporales.iniciar_maximizado(), self.preferencias_aplicacion.iniciar_maximizado(), "Iniciar TecNet Finder maximizado"),
                (self.preferencias_temporales.recordar_estado_ventana(), self.preferencias_aplicacion.recordar_estado_ventana(), "Recordar el estado de la ventana al cerrar"),
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
        }  # Centraliza las comparaciones para mantener compacto el registro de cambios.

        for seccion, elementos in comparaciones.items():  # Recorre todas las categorías generales.
            for temporal, real, nombre in elementos:  # Recorre cada preferencia editable.
                if temporal != real:  # Comprueba si su copia temporal difiere de la configuración persistida.
                    cambios[seccion].append(nombre)  # Registra exactamente la preferencia modificada.

        return {seccion: elementos for seccion, elementos in cambios.items() if elementos}  # Elimina del registro las categorías que no contienen cambios.

    def _obtener_todos_los_cambios_pendientes(self) -> dict[str, list[str]]:
        cambios = self._obtener_cambios_generales()  # Recupera primero Ventana, Editor y Resultados.
        cambios_ia = self.panel_ia.obtener_cambios_pendientes()  # Recupera independientemente las preferencias de IA.
        if cambios_ia:  # Comprueba si IA tiene alguna decisión diferente.
            cambios["Asistencia de IA"] = cambios_ia  # Incorpora la sección al mismo registro.
        return cambios  # Devuelve la colección completa de modificaciones pendientes.

    def _actualizar_estado_botones(self, *_argumentos) -> None:
        if hasattr(self, "boton_aplicar"):  # Evita consultar el botón antes de construir el pie.
            self.boton_aplicar.setEnabled(bool(self._obtener_todos_los_cambios_pendientes()) and not self.operacion_en_curso)  # Habilita Aplicar únicamente cuando existe una diferencia real.

    def _aplicar_preferencias_generales(self) -> tuple[dict[str, list[str]], list[str]]:
        cambios_antes = self._obtener_cambios_generales()  # Conserva el registro exacto antes de realizar escrituras.

        self.preferencias_aplicacion.establecer_iniciar_maximizado(self.preferencias_temporales.iniciar_maximizado())  # Confirma el inicio de ventana.
        self.preferencias_aplicacion.establecer_recordar_estado_ventana(self.preferencias_temporales.recordar_estado_ventana())  # Confirma la recuperación entre sesiones.
        self.preferencias_aplicacion.establecer_recordar_seccion_configuracion(self.preferencias_temporales.recordar_seccion_configuracion())  # Confirma la recuperación de categoría.
        self.preferencias_aplicacion.establecer_ajuste_linea_editor_activado(self.preferencias_temporales.ajuste_linea_editor_activado())  # Confirma el ajuste de líneas.
        self.preferencias_aplicacion.establecer_botones_rapidos_editor_visibles(self.preferencias_temporales.botones_rapidos_editor_visibles())  # Confirma la visibilidad de Pegar y Ejemplos.
        self.preferencias_aplicacion.establecer_familia_fuente_editor(self.preferencias_temporales.familia_fuente_editor())  # Confirma la tipografía seleccionada.
        self.preferencias_aplicacion.establecer_tamano_fuente_editor(self.preferencias_temporales.tamano_fuente_editor())  # Confirma el tamaño del editor.
        self.preferencias_aplicacion.establecer_espacios_tabulacion_editor(self.preferencias_temporales.espacios_tabulacion_editor())  # Confirma el ancho de Tab.
        self.preferencias_aplicacion.establecer_navegacion_errores_activada(self.preferencias_temporales.navegacion_errores_activada())  # Confirma navegación hacia errores.
        self.preferencias_aplicacion.establecer_navegacion_vlsm_activada(self.preferencias_temporales.navegacion_vlsm_activada())  # Confirma navegación hacia VLSM.
        self.preferencias_aplicacion.establecer_cerrar_ventana_advertencias_al_navegar(self.preferencias_temporales.cerrar_ventana_advertencias_al_navegar())  # Confirma el comportamiento del doble clic.

        if self.preferencias_temporales.advertencias_vlsm_visibles():  # Comprueba si debe utilizarse el panel compacto.
            self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(True)  # Activa esta modalidad y desactiva automáticamente la otra.
        elif self.preferencias_temporales.advertencias_ventana_independiente():  # Comprueba si debe utilizarse la ventana independiente.
            self.preferencias_aplicacion.establecer_advertencias_ventana_independiente(True)  # Activa esta modalidad y desactiva el panel.
        else:  # Representa la posibilidad de mantener ambas modalidades adicionales apagadas.
            self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(False)  # Desactiva el panel compacto.
            self.preferencias_aplicacion.establecer_advertencias_ventana_independiente(False)  # Desactiva también la ventana independiente.

        cambios_despues = self._obtener_cambios_generales()  # Comprueba qué diferencias continúan después de escribir.
        aplicados = {}  # Prepara el registro de preferencias confirmadas correctamente.
        errores = []  # Prepara la colección de posibles fallos.

        for seccion, elementos in cambios_antes.items():  # Recorre las modificaciones que existían inicialmente.
            pendientes = set(cambios_despues.get(seccion, []))  # Obtiene las que continúan diferentes después de la escritura.
            confirmados = [elemento for elemento in elementos if elemento not in pendientes]  # Conserva solamente los cambios realmente aplicados.
            if confirmados:  # Comprueba si la sección tuvo al menos una confirmación.
                aplicados[seccion] = confirmados  # Añade esos cambios al resumen.

        for seccion, elementos in cambios_despues.items():  # Recorre cualquier diferencia que continúe pendiente.
            for elemento in elementos:  # Recorre sus preferencias individuales.
                if elemento in cambios_antes.get(seccion, []):  # Comprueba que se intentara aplicar en esta operación.
                    errores.append(f"No fue posible guardar: {elemento}.")  # Informa exactamente qué preferencia falló.

        if cambios_antes.get("Editor"):  # Comprueba si alguna preferencia del Editor cambió.
            self.ajuste_linea_editor_cambiado.emit(self.preferencias_aplicacion.ajuste_linea_editor_activado())  # Aplica el ajuste confirmado.
            self.botones_rapidos_editor_cambiados.emit(self.preferencias_aplicacion.botones_rapidos_editor_visibles())  # Aplica los botones confirmados.
            self.familia_fuente_editor_cambiada.emit(self.preferencias_aplicacion.familia_fuente_editor())  # Aplica la familia tipográfica confirmada.
            self.tamano_fuente_editor_cambiado.emit(self.preferencias_aplicacion.tamano_fuente_editor())  # Aplica el tamaño confirmado.
            self.espacios_tabulacion_editor_cambiados.emit(self.preferencias_aplicacion.espacios_tabulacion_editor())  # Aplica la tabulación confirmada.

        if cambios_antes.get("Resultados y navegación"):  # Comprueba si alguna preferencia de Resultados cambió.
            self.navegacion_errores_cambiada.emit(self.preferencias_aplicacion.navegacion_errores_activada())  # Sincroniza navegación hacia errores.
            self.navegacion_vlsm_cambiada.emit(self.preferencias_aplicacion.navegacion_vlsm_activada())  # Sincroniza navegación hacia VLSM.
            self.advertencias_vlsm_cambiadas.emit(self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Sincroniza el panel compacto.
            self.advertencias_ventana_cambiadas.emit(self.preferencias_aplicacion.advertencias_ventana_independiente())  # Sincroniza la ventana independiente.
            self.cerrar_ventana_al_navegar_cambiado.emit(self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Sincroniza el comportamiento del doble clic.

        if self.preferencias_aplicacion.recordar_seccion_configuracion() and 0 <= self.lista_secciones.currentRow() < len(self.claves_secciones):  # Comprueba si debe conservarse la categoría actualmente visible.
            self.preferencias_aplicacion.establecer_ultima_seccion_configuracion(self.claves_secciones[self.lista_secciones.currentRow()])  # Guarda su clave estable.

        return aplicados, errores  # Entrega la información utilizada por el resumen y posibles advertencias.

    def _aplicar_cambios(self, mostrar_resumen: bool) -> tuple[bool, bool]:
        if not self._obtener_todos_los_cambios_pendientes():  # Comprueba si realmente existe algo que confirmar.
            return True, False  # Evita escrituras y diálogos vacíos.

        aplicados, errores = self._aplicar_preferencias_generales()  # Confirma primero las preferencias generales.
        aplicados_ia, errores_ia = self.panel_ia.aplicar_cambios_pendientes()  # Confirma después las preferencias de IA.

        if aplicados_ia:  # Comprueba si IA tuvo cambios efectivos.
            aplicados["Asistencia de IA"] = aplicados_ia  # Incorpora esos cambios al resumen general.

        errores.extend(errores_ia)  # Une los posibles fallos de ambas fuentes.
        self._actualizar_estado_botones()  # Recalcula si Aplicar debe continuar habilitado.

        if mostrar_resumen and aplicados:  # Comprueba si el usuario pulsó Aplicar y hubo modificaciones confirmadas.
            self._mostrar_resumen_cambios(aplicados)  # Presenta cantidad, secciones y detalles.

        if errores:  # Comprueba si alguna preferencia no pudo persistirse.
            QMessageBox.warning(self, "Configuración", "Algunos cambios no pudieron aplicarse:\n\n" + "\n".join(f"• {error}" for error in errores))  # Mantiene abierta Configuración e informa los problemas.

        return not errores, bool(aplicados)  # Informa si todo terminó correctamente y si realmente hubo cambios.

    def _aplicar_desde_boton(self) -> None:
        self._aplicar_cambios(True)  # Confirma los cambios, muestra el resumen y mantiene abierta Configuración.

    def _aceptar_cambios(self) -> None:
        correcto, _ = self._aplicar_cambios(False)  # Confirma las preferencias pendientes sin mostrar el resumen intermedio.
        if not correcto:  # Comprueba si alguna preferencia continúa sin guardarse.
            return  # Mantiene abierta Configuración para no perder información.
        if self.operacion_en_curso:  # Comprueba si alguna transición de IA continúa activa.
            self.cerrar_despues_de_operacion = True  # Reserva el cierre hasta que termine la operación.
            return  # Evita cerrar prematuramente.
        self.cierre_confirmado = True  # Autoriza el cierre normal.
        super().accept()  # Finaliza Configuración conservando todos los valores aplicados.

    def _cancelar_cambios(self) -> None:
        if self.operacion_en_curso:  # Protege cualquier operación activa de IA.
            return  # Mantiene Configuración abierta.
        self.panel_ia.descartar_cambios_pendientes()  # Recupera las preferencias de IA ya confirmadas.
        self.cierre_confirmado = True  # Marca el cierre como procesado mediante Cancelar.
        super().reject()  # Descarta automáticamente la copia temporal de preferencias generales.

    def _mostrar_resumen_cambios(self, cambios: dict[str, list[str]]) -> None:
        cantidad = sum(len(elementos) for elementos in cambios.values())  # Cuenta todas las preferencias confirmadas.
        secciones = len(cambios)  # Cuenta únicamente las categorías afectadas.
        dialogo = QMessageBox(self)  # Crea el cuadro informativo vinculado con Configuración.
        dialogo.setWindowTitle("Cambios aplicados")  # Identifica claramente el resultado de Aplicar.
        dialogo.setIcon(QMessageBox.Icon.Information)  # Utiliza el icono convencional de información.
        dialogo.setText(f"Se aplicaron {cantidad} {'cambio' if cantidad == 1 else 'cambios'} en {secciones} {'sección' if secciones == 1 else 'secciones'}.")  # Construye el resumen numérico.
        dialogo.setInformativeText("\n\n".join(seccion + ":\n" + "\n".join(f"• {elemento}" for elemento in elementos) for seccion, elementos in cambios.items()))  # Organiza el registro por categoría.
        dialogo.setStandardButtons(QMessageBox.StandardButton.Ok)  # Mantiene una única acción de confirmación.
        boton = dialogo.button(QMessageBox.StandardButton.Ok)  # Recupera el botón generado por Qt.
        if boton is not None:  # Comprueba que exista.
            boton.setText("Aceptar")  # Mantiene el cuadro completamente en español.
            boton.setObjectName("BotonPrincipal")  # Reutiliza el azul principal.
        dialogo.exec()  # Muestra el resumen hasta que el usuario lo cierre.

    def _actualizar_operacion(self, en_curso: bool) -> None:
        self.operacion_en_curso = bool(en_curso)  # Conserva el estado actual de las operaciones de IA.
        self.lista_secciones.setEnabled(not self.operacion_en_curso)  # Bloquea la navegación lateral mientras corresponda.
        self.boton_aplicar.setEnabled(bool(self._obtener_todos_los_cambios_pendientes()) and not self.operacion_en_curso)  # Mantiene Aplicar coherente con cambios y disponibilidad.
        self.boton_aceptar.setEnabled(not self.operacion_en_curso)  # Bloquea Aceptar durante operaciones críticas.
        self.boton_cancelar.setEnabled(not self.operacion_en_curso)  # Bloquea Cancelar durante operaciones críticas.
        if self.barra_titulo.boton_cerrar is not None:  # Comprueba que exista la X personalizada.
            self.barra_titulo.boton_cerrar.setEnabled(not self.operacion_en_curso)  # Protege también el cierre superior.
        if not self.operacion_en_curso and self.cerrar_despues_de_operacion:  # Comprueba si Aceptar estaba esperando esta finalización.
            self.cerrar_despues_de_operacion = False  # Consume la solicitud pendiente.
            self.cierre_confirmado = True  # Autoriza el cierre definitivo.
            super().accept()  # Finaliza Configuración de forma segura.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt calcule primero su geometría definitiva.
        self._centrar_en_area_disponible()  # Centra posteriormente la ventana en el monitor correcto.

    def accept(self) -> None:
        self._aceptar_cambios()  # Hace que cualquier aceptación convencional respete Aplicar/Aceptar.

    def reject(self) -> None:
        self._cancelar_cambios()  # Hace que Escape tenga exactamente el mismo comportamiento que Cancelar.

    def closeEvent(self, evento) -> None:
        if self.cierre_confirmado:  # Comprueba si Aceptar o Cancelar ya procesaron correctamente el cierre.
            evento.accept()  # Permite finalmente cerrar el diálogo.
            return  # Evita procesar nuevamente la misma operación.
        if self.operacion_en_curso:  # Comprueba si todavía existe una operación protegida.
            evento.ignore()  # Impide cerrar durante la operación.
            return  # Conserva Configuración abierta.
        evento.ignore()  # Evita que la X destruya directamente la ventana.
        self._cancelar_cambios()  # Convierte la X en el mismo comportamiento de Cancelar.