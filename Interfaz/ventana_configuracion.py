# ============================================================
# Archivo: ventana_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la ventana general de configuración de
# TecNet Finder.
#
# Utiliza la barra de título personalizada de la aplicación,
# mantiene un tamaño fijo, presenta bordes exteriores redondeados
# y organiza sus categorías mediante una navegación lateral con
# paneles intercambiables.
#
# Cada categoría utiliza desplazamiento vertical únicamente
# cuando su contenido no cabe dentro del tamaño fijo acordado.
#
# La ventana se centra horizontal y verticalmente dentro del área
# útil del monitor donde se encuentra TecNet Finder, excluyendo
# espacios ocupados por elementos del sistema como la barra de
# tareas de Windows.
# ============================================================

from pathlib import Path  # Permite localizar el icono oficial utilizado por la barra personalizada.

from PySide6.QtCore import Qt, Signal  # Permite controlar apariencia, navegación y señales emitidas por los paneles.
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout  # Importa los componentes utilizados por la configuración.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite compartir la instalación opcional con el panel correspondiente.
from AsistenteIA.gestor_ollama import GestorOllama  # Permite compartir el servicio activo de inteligencia artificial.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Permite compartir las preferencias persistentes del usuario.
from Interfaz.barra_titulo import BarraTitulo  # Reutiliza la misma barra personalizada utilizada por la ventana principal.
from Interfaz.panel_configuracion_ia import PanelConfiguracionIA  # Importa la primera sección disponible dentro de Configuración.


class VentanaConfiguracion(QDialog):  # Representa la configuración general y permite cambiar entre diferentes categorías.
    autocompletado_ia_cambiado = Signal(bool)  # Reenvía el estado efectivo de la función de ghost text.
    diagnosticos_ia_cambiados = Signal(bool)  # Reenvía independientemente la mejora automática de soluciones.
    servicio_ia_cambiado = Signal(bool)  # Informa al controlador principal si Ollama se encuentra realmente disponible.

    def __init__(
        self,
        gestor_ollama: GestorOllama,
        componente_ia: GestorComponenteIA,
        preferencias_ia: PreferenciasIA,
        asistencia_disponible_inicial: bool,
        padre=None,
    ):
        super().__init__(padre)  # Mantiene la configuración vinculada con la ventana principal.
        self.operacion_en_curso = False  # Evita cerrar la ventana mientras algún componente todavía está cambiando de estado.

        self.setObjectName("VentanaConfiguracion")  # Permite distinguir este diálogo frameless del resto de las ventanas.
        self.setWindowTitle("Configuración")  # Conserva un nombre identificable para Windows y herramientas de accesibilidad.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)  # Sustituye completamente la barra estándar de Windows por la barra propia.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite que las zonas exteriores a las esquinas redondeadas sean realmente transparentes.
        self.setFixedSize(850, 770)  # Mantiene exactamente el tamaño acordado sin permitir agrandar ni reducir la ventana.
        self.setModal(True)  # Evita abrir varias ventanas de configuración simultáneamente.
        self.setStyleSheet("QDialog#VentanaConfiguracion { background-color: transparent; }")  # Impide que el estilo global pinte un rectángulo oscuro detrás de las esquinas redondeadas.

        if padre is not None:
            self.setWindowIcon(padre.windowIcon())  # Conserva el icono oficial de TecNet Finder dentro del sistema operativo.

        self._construir_interfaz(
            gestor_ollama,
            componente_ia,
            preferencias_ia,
            asistencia_disponible_inicial,
        )  # Construye marco, barra personalizada, navegación y paneles utilizando los componentes compartidos.

    def _ruta_icono(self) -> Path:
        return Path(__file__).resolve().parent.parent / "Recursos" / "LogoTNF.ico"  # Localiza el mismo recurso utilizado por la ventana principal.

    def _centrar_en_area_disponible(self) -> None:
        pantalla = None  # Comienza sin asumir qué monitor debe utilizarse como referencia.
        padre = self.parentWidget()  # Obtiene la ventana principal asociada con Configuración.

        if padre is not None and padre.windowHandle() is not None:
            pantalla = padre.windowHandle().screen()  # Prefiere el monitor donde actualmente se encuentra TecNet Finder.

        if pantalla is None:
            pantalla = self.screen()  # Utiliza la pantalla asignada al propio diálogo cuando el padre no permite determinarla.

        if pantalla is None:
            pantalla = QApplication.primaryScreen()  # Utiliza el monitor principal únicamente como último respaldo.

        if pantalla is None:
            return  # Mantiene la posición administrada por Qt si el sistema no proporcionara información de pantallas.

        area_disponible = pantalla.availableGeometry()  # Obtiene el área útil del monitor excluyendo la barra de tareas y otras zonas reservadas por el sistema.

        desplazamiento_x = max(0, (area_disponible.width() - self.width()) // 2)  # Calcula el espacio horizontal necesario para centrar la ventana.
        desplazamiento_y = max(0, (area_disponible.height() - self.height()) // 2)  # Calcula el espacio vertical necesario para centrarla sin contar la barra de tareas.

        posicion_x = area_disponible.x() + desplazamiento_x  # Respeta también el origen real del monitor cuando existen varias pantallas.
        posicion_y = area_disponible.y() + desplazamiento_y  # Respeta cualquier zona superior reservada por el sistema operativo.

        self.move(posicion_x, posicion_y)  # Sitúa Configuración exactamente en el centro del área de trabajo disponible.

    def _construir_interfaz(
        self,
        gestor_ollama: GestorOllama,
        componente_ia: GestorComponenteIA,
        preferencias_ia: PreferenciasIA,
        asistencia_disponible_inicial: bool,
    ) -> None:
        diseno_exterior = QVBoxLayout(self)  # Reserva el diálogo transparente para colocar dentro la ventana visual real.
        diseno_exterior.setContentsMargins(7, 7, 7, 7)  # Deja espacio transparente alrededor para que las curvas exteriores puedan apreciarse correctamente.
        diseno_exterior.setSpacing(0)  # Evita introducir separaciones adicionales alrededor del marco.

        self.marco_ventana = QFrame(self)  # Crea el contenedor visible que representa realmente la superficie de Configuración.
        self.marco_ventana.setObjectName("MarcoVentanaConfiguracion")  # Permite aplicar exclusivamente el estilo exterior de esta ventana.
        self.marco_ventana.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt represente correctamente fondo, borde y radios definidos mediante QSS.
        self.marco_ventana.setStyleSheet(
            """
            QFrame#MarcoVentanaConfiguracion {
                background-color: #1e1e2e;
                border: 1px solid #cdd6f4;
                border-radius: 14px;
            }
            """
        )  # Dibuja un contorno claro y redondea las cuatro esquinas exteriores del cuadro principal.
        diseno_exterior.addWidget(self.marco_ventana)  # Coloca la superficie redondeada dentro del área transparente exterior.

        diseno_general = QVBoxLayout(self.marco_ventana)  # Organiza barra, contenido y pie dentro del marco redondeado.
        diseno_general.setContentsMargins(1, 1, 1, 1)  # Reserva únicamente el espacio necesario para que el borde exterior permanezca visible.
        diseno_general.setSpacing(0)  # Mantiene unidas visualmente las regiones internas de la ventana.

        contenedor_barra = QFrame()  # Crea una superficie propia para las esquinas superiores de la ventana.
        contenedor_barra.setObjectName("ContenedorBarraConfiguracion")  # Permite diferenciar esta región de la barra utilizada en la ventana principal.
        contenedor_barra.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que el fondo redondeado superior sea representado correctamente.
        contenedor_barra.setStyleSheet(
            """
            QFrame#ContenedorBarraConfiguracion {
                background-color: #181825;
                border: none;
                border-top-left-radius: 13px;
                border-top-right-radius: 13px;
            }
            """
        )  # Conserva el color de la barra principal y redondea únicamente sus esquinas superiores.

        diseno_barra = QVBoxLayout(contenedor_barra)  # Permite colocar la barra reutilizable dentro de la superficie redondeada.
        diseno_barra.setContentsMargins(0, 0, 0, 0)  # Hace que la barra ocupe completamente su contenedor.
        diseno_barra.setSpacing(0)  # Evita cualquier separación entre la barra y su fondo.

        self.barra_titulo = BarraTitulo(
            ventana=self,
            ruta_icono=self._ruta_icono(),
            titulo="Configuración",
            mostrar_configuracion=False,
            mostrar_minimizar=False,
            mostrar_pantalla_completa=False,
            mostrar_cerrar=True,
            permitir_arrastre=True,
        )  # Reutiliza la barra oficial mostrando solamente nombre, logotipo y botón de cierre.

        self.barra_titulo.setStyleSheet(
            """
            QWidget#BarraTitulo {
                background-color: transparent;
                border: none;
            }

            QLabel#TituloBarra {
                background-color: transparent;
            }
            """
        )  # Hace transparente únicamente esta instancia para que el contenedor redondeado controle correctamente sus esquinas.

        if self.barra_titulo.boton_cerrar is not None:
            self.barra_titulo.boton_cerrar.setObjectName("BotonCerrarConfiguracion")  # Distingue esta X de la correspondiente a la ventana principal.
            self.barra_titulo.boton_cerrar.setStyleSheet(
                """
                QPushButton#BotonCerrarConfiguracion {
                    background-color: transparent;
                    color: #cdd6f4;
                    border: none;
                    border-top-right-radius: 12px;
                    padding: 0px;
                }

                QPushButton#BotonCerrarConfiguracion:hover {
                    background-color: #c42b1c;
                    color: #ffffff;
                    border: none;
                    border-top-right-radius: 12px;
                }

                QPushButton#BotonCerrarConfiguracion:pressed {
                    background-color: #a52016;
                    color: #ffffff;
                    border: none;
                    border-top-right-radius: 12px;
                }

                QPushButton#BotonCerrarConfiguracion:disabled {
                    background-color: transparent;
                    border: none;
                    border-top-right-radius: 12px;
                }
                """
            )  # Hace que todos los fondos temporales del botón respeten físicamente la curva exterior de Configuración.

        diseno_barra.addWidget(self.barra_titulo)  # Coloca la barra reutilizable sobre el fondo superior redondeado.
        diseno_general.addWidget(contenedor_barra)  # Incorpora la región completa como primera parte de la ventana.

        contenedor_separador = QFrame()  # Reserva una pequeña región independiente para separar barra y contenido.
        contenedor_separador.setObjectName("ContenedorSeparadorConfiguracion")  # Permite mantener el fondo alineado con la interfaz.
        contenedor_separador.setStyleSheet(
            """
            QFrame#ContenedorSeparadorConfiguracion {
                background-color: #181825;
                border: none;
            }
            """
        )  # Conserva el mismo fondo inmediatamente debajo de la barra personalizada.

        diseno_separador = QHBoxLayout(contenedor_separador)  # Permite dar un pequeño margen lateral a la línea clara.
        diseno_separador.setContentsMargins(8, 0, 8, 0)  # Evita que la línea choque visualmente contra el borde exterior.
        diseno_separador.setSpacing(0)  # Mantiene la línea como único elemento del separador.

        separador_barra = QFrame()  # Crea la línea que divide visualmente la barra del resto de Configuración.
        separador_barra.setFixedHeight(1)  # Mantiene la delimitación discreta y consistente con el borde exterior.
        separador_barra.setStyleSheet("background-color: #cdd6f4; border: none;")  # Utiliza el mismo tono claro empleado alrededor de la ventana.
        diseno_separador.addWidget(separador_barra)  # Coloca la línea dentro del margen lateral definido.

        diseno_general.addWidget(contenedor_separador)  # Inserta la separación inmediatamente debajo de la barra.

        contenido = QHBoxLayout()  # Organiza navegación lateral y panel seleccionado.
        contenido.setContentsMargins(0, 0, 0, 0)  # Evita separaciones externas innecesarias.
        contenido.setSpacing(0)  # Une visualmente ambas áreas de configuración.

        self.lista_secciones = QListWidget()  # Crea la navegación lateral utilizada para seleccionar categorías.
        self.lista_secciones.setObjectName("ListaConfiguracion")  # Permite aplicar el estilo general destinado a la navegación.
        self.lista_secciones.setFixedWidth(210)  # Reserva un ancho constante similar a configuraciones modernas.
        self.lista_secciones.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide mostrar desplazamiento horizontal en nombres breves.
        contenido.addWidget(self.lista_secciones)  # Coloca la navegación lateral en el lado izquierdo.

        self.paneles = QStackedWidget()  # Conserva todos los paneles registrados y muestra solamente el seleccionado.
        self.paneles.setObjectName("PanelesConfiguracion")  # Permite aplicar la apariencia general del área principal.
        contenido.addWidget(self.paneles, 1)  # Permite que el panel activo utilice todo el ancho restante.

        contenedor_contenido = QFrame()  # Agrupa navegación y paneles dentro de una única región central.
        contenedor_contenido.setObjectName("ContenidoVentanaConfiguracion")  # Permite identificar el contenido situado entre barra y pie.
        contenedor_contenido.setLayout(contenido)  # Asigna navegación y paneles al contenedor central.
        diseno_general.addWidget(contenedor_contenido, 1)  # Hace que esta región aproveche todo el espacio vertical disponible.

        self.panel_ia = PanelConfiguracionIA(
            gestor_ollama=gestor_ollama,
            componente_ia=componente_ia,
            preferencias_ia=preferencias_ia,
            asistencia_disponible_inicial=asistencia_disponible_inicial,
            padre=self,
        )  # Construye la primera categoría real de configuración utilizando los mismos componentes activos de TecNet Finder.

        self._agregar_seccion("Asistencia de IA", self.panel_ia)  # Registra la sección dentro de un área desplazable reutilizable.

        self.panel_ia.autocompletado_cambiado.connect(self.autocompletado_ia_cambiado.emit)  # Reenvía únicamente los cambios efectivos del ghost text.
        self.panel_ia.diagnosticos_ia_cambiados.connect(self.diagnosticos_ia_cambiados.emit)  # Reenvía independientemente la mejora de diagnósticos.
        self.panel_ia.servicio_cambiado.connect(self.servicio_ia_cambiado.emit)  # Mantiene sincronizado el estado compartido de Ollama.
        self.panel_ia.operacion_cambiada.connect(self._actualizar_operacion)  # Impide cerrar Configuración mientras el servicio local cambia de estado.

        self.lista_secciones.currentRowChanged.connect(self._cambiar_panel)  # Cambia el contenido cuando el usuario selecciona otra categoría.
        self.lista_secciones.setCurrentRow(0)  # Muestra inicialmente la primera categoría disponible.

        pie = QFrame()  # Crea la región inferior que contendrá el botón general de cierre.
        pie.setObjectName("PieConfiguracionRedondeado")  # Permite controlar específicamente las esquinas inferiores.
        pie.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt represente correctamente su fondo y sus radios.
        pie.setStyleSheet(
            """
            QFrame#PieConfiguracionRedondeado {
                background-color: #181825;
                border: none;
                border-top: 1px solid #313244;
                border-bottom-left-radius: 13px;
                border-bottom-right-radius: 13px;
            }
            """
        )  # Mantiene el aspecto del pie existente pero evita que vuelva cuadradas las esquinas inferiores.

        diseno_pie = QHBoxLayout(pie)  # Organiza el botón general de cierre dentro de la región inferior.
        diseno_pie.setContentsMargins(16, 10, 16, 10)  # Mantiene espacio suficiente respecto a los bordes.
        diseno_pie.addStretch()  # Empuja el botón hacia el extremo derecho.

        self.boton_cerrar = QPushButton("Cerrar")  # Permite abandonar Configuración sin cerrar TecNet Finder.
        self.boton_cerrar.clicked.connect(self.accept)  # Solicita cerrar únicamente esta ventana secundaria.
        diseno_pie.addWidget(self.boton_cerrar)  # Coloca la acción al final de la región inferior.

        diseno_general.addWidget(pie)  # Incorpora el pie redondeado como última región de Configuración.

    def _agregar_seccion(self, nombre: str, panel) -> None:
        elemento = QListWidgetItem(nombre)  # Crea la entrada visible correspondiente a una categoría.
        elemento.setToolTip(nombre)  # Conserva el nombre completo como ayuda para futuras etiquetas largas.
        self.lista_secciones.addItem(elemento)  # Incorpora la categoría a la navegación lateral.

        desplazamiento = QScrollArea()  # Mantiene el tamaño fijo de Configuración aunque una categoría crezca posteriormente.
        desplazamiento.setObjectName("AreaDesplazamientoConfiguracion")  # Permite diferenciar esta superficie del resto de widgets.
        desplazamiento.setFrameShape(QFrame.Shape.NoFrame)  # Evita agregar un segundo borde alrededor del panel.
        desplazamiento.setWidgetResizable(True)  # Adapta horizontalmente el contenido al espacio disponible.
        desplazamiento.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide desplazamiento lateral porque los paneles deben ajustarse al ancho.
        desplazamiento.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra la barra vertical únicamente cuando el contenido supera la altura disponible.
        desplazamiento.setStyleSheet(
            """
            QScrollArea#AreaDesplazamientoConfiguracion {
                background-color: #1e1e2e;
                border: none;
            }

            QScrollArea#AreaDesplazamientoConfiguracion > QWidget > QWidget {
                background-color: #1e1e2e;
            }
            """
        )  # Integra la superficie desplazable con el mismo fondo del área principal.
        desplazamiento.setWidget(panel)  # Convierte el panel real en el contenido desplazable sin modificar su lógica.
        self.paneles.addWidget(desplazamiento)  # Registra la categoría completa en la misma posición que su elemento lateral.

    def _cambiar_panel(self, indice: int) -> None:
        if 0 <= indice < self.paneles.count():
            self.paneles.setCurrentIndex(indice)  # Muestra exclusivamente el panel relacionado con la categoría seleccionada.

    def _actualizar_operacion(self, en_curso: bool) -> None:
        self.operacion_en_curso = bool(en_curso)  # Conserva si algún panel está ejecutando una operación que exige mantener abierta la ventana.
        self.boton_cerrar.setEnabled(not self.operacion_en_curso)  # Impide abandonar Configuración mientras Ollama inicia o termina.
        self.lista_secciones.setEnabled(not self.operacion_en_curso)  # Evita cambiar de categoría durante una operación que todavía no ha terminado.

        if self.barra_titulo.boton_cerrar is not None:
            self.barra_titulo.boton_cerrar.setEnabled(not self.operacion_en_curso)  # Protege también la X personalizada mientras existe un trabajo pendiente.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt prepare completamente la geometría y los controles antes de reposicionar el diálogo.
        self._centrar_en_area_disponible()  # Centra Configuración cada vez que se muestra utilizando únicamente el área útil del monitor.

    def accept(self) -> None:
        if self.operacion_en_curso:
            return  # Mantiene viva la ventana mientras algún panel espera una respuesta del servicio.

        super().accept()  # Cierra normalmente Configuración cuando todos sus componentes se encuentran estables.

    def reject(self) -> None:
        if self.operacion_en_curso:
            return  # Evita cerrar mediante Escape mientras existe una operación pendiente.

        super().reject()  # Conserva el comportamiento normal cuando no hay operaciones activas.

    def closeEvent(self, evento) -> None:
        if self.operacion_en_curso:
            evento.ignore()  # Impide que la X personalizada destruya la ventana mientras Ollama cambia de estado.
            return  # Mantiene Configuración abierta hasta recibir el resultado pendiente.

        evento.accept()  # Permite el cierre inmediato cuando la ventana se encuentra completamente estable.