# ============================================================
# Archivo: ventana_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la ventana independiente utilizada para
# mostrar las advertencias producidas por una compilación.
#
# La ventana es no modal para permitir consultar simultáneamente
# Tabla VLSM dentro de la ventana principal.
#
# Cada advertencia se representa mediante una tarjeta interactiva.
# Un doble clic sobre la tarjeta solicita navegar directamente a
# la ubicación correspondiente dentro del código fuente.
#
# Todas las tarjetas se encuentran dentro de una zona desplazable
# para permitir visualizar cualquier cantidad de advertencias.
# ============================================================

from pathlib import Path  # Permite localizar el icono específico utilizado por la ventana de advertencias.

from PySide6.QtCore import Qt, Signal  # Permite emitir la advertencia seleccionada y controlar diferentes opciones de Qt.
from PySide6.QtGui import QIcon  # Permite asignar el icono de advertencia también a la ventana independiente.
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget  # Importa los controles utilizados por la ventana.

from Interfaz.barra_titulo import BarraTitulo  # Reutiliza la barra personalizada oficial.
from Motor.diagnosticos import Diagnostico  # Define la estructura recibida por cada advertencia.


class TarjetaAdvertenciaInteractiva(QFrame):  # Representa una advertencia que puede activarse mediante doble clic.
    activada = Signal(object)  # Envía el Diagnostico original asociado con la tarjeta.

    def __init__(self, advertencia: Diagnostico, padre=None):
        super().__init__(padre)  # Inicializa la superficie estándar de Qt.
        self.advertencia = advertencia  # Conserva el diagnóstico exacto que representa esta tarjeta.
        self.setObjectName("TarjetaAdvertenciaIndependiente")  # Permite utilizar el estilo específico preparado para las advertencias.

        if advertencia.linea is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que una advertencia con ubicación puede utilizarse para navegar.
            self.setToolTip("Doble clic para ir a esta advertencia en el código.")  # Explica directamente la interacción disponible.
        else:
            self.setToolTip("Esta advertencia no tiene una ubicación específica en el código.")  # Evita prometer navegación cuando no existe línea de origen.

    def mouseDoubleClickEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton and self.advertencia.linea is not None:
            self.activada.emit(self.advertencia)  # Entrega el diagnóstico original a la ventana superior.
            evento.accept()  # Informa a Qt que el doble clic fue procesado.
            return
        super().mouseDoubleClickEvent(evento)  # Conserva el comportamiento convencional para cualquier otra interacción.


class VentanaAdvertencias(QDialog):  # Representa la ventana independiente de advertencias de compilación.
    advertencia_activada = Signal(object)  # Informa qué advertencia debe abrirse dentro del editor.

    def __init__(self, advertencias: list[Diagnostico], padre=None):
        super().__init__(padre)  # Vincula la ventana con TecNet Finder sin volverla modal.
        self.advertencias = list(advertencias)  # Conserva una copia estable de los avisos correspondientes con esta compilación.
        self.setObjectName("VentanaAdvertencias")  # Permite identificar específicamente esta ventana mediante estilos.
        self.setWindowTitle("Advertencias de compilación")  # Define el nombre utilizado por el sistema para esta ventana.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)  # Reutiliza nuestra propia barra de título.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite representar correctamente las esquinas exteriores redondeadas.
        self.setModal(False)  # No bloquea la interacción con la ventana principal.
        self.setWindowModality(Qt.WindowModality.NonModal)  # Confirma explícitamente el comportamiento no modal.
        self.setFixedSize(700, 540)  # Mantiene una superficie cómoda sin cubrir toda la aplicación.
        self.setStyleSheet("QDialog#VentanaAdvertencias { background-color: transparent; }")  # Mantiene transparente únicamente el fondo exterior del diálogo.
        self.setWindowIcon(QIcon(str(self._ruta_icono())))  # Utiliza el mismo icono amarillo de advertencia también como icono propio de esta ventana.
        self._construir_interfaz()  # Construye la barra personalizada, tarjetas y pie después de configurar la ventana.

    def _ruta_icono(self) -> Path:
        return Path(__file__).resolve().parent.parent / "Recursos" / "Iconos" / "Advertencia.png"  # Utiliza el recurso específico de advertencia en lugar del logotipo general de TecNet Finder.

    def _construir_interfaz(self) -> None:
        diseno_exterior = QVBoxLayout(self)  # Crea el margen exterior responsable de mostrar correctamente las esquinas redondeadas.
        diseno_exterior.setContentsMargins(7, 7, 7, 7)  # Separa el marco de los límites transparentes del diálogo.
        diseno_exterior.setSpacing(0)  # Mantiene unido el marco principal.

        self.marco = QFrame(self)  # Crea la superficie principal visible de la ventana.
        self.marco.setObjectName("MarcoVentanaAdvertencias")  # Permite aplicar únicamente los estilos propios de esta ventana.
        self.marco.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt pinte correctamente el fondo redondeado.

        self.marco.setStyleSheet(
            """
            QFrame#MarcoVentanaAdvertencias {
                background-color: #1e1e2e;
                border: 1px solid #cdd6f4;
                border-radius: 14px;
            }

            QFrame#TarjetaAdvertenciaIndependiente {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 8px;
            }

            QFrame#TarjetaAdvertenciaIndependiente:hover {
                background-color: #1c1c2c;
                border-color: #f9e2af;
            }

            QFrame#TarjetaAdvertenciaIndependiente QLabel {
                background-color: #1e1e2e;
                border: none;
                border-radius: 7px;
                padding: 2px 5px;
            }

            QLabel#CodigoAdvertenciaIndependiente {
                color: #f9e2af;
                font-size: 11pt;
                font-weight: bold;
            }

            QLabel#UbicacionAdvertenciaIndependiente {
                color: #a6adc8;
            }

            QLabel#TituloCampoAdvertenciaIndependiente {
                color: #cdd6f4;
                font-weight: bold;
            }

            QLabel#TextoAdvertenciaIndependiente {
                color: #cdd6f4;
            }

            QScrollArea#AreaAdvertenciasIndependientes {
                background-color: #1e1e2e;
                border: none;
            }

            QScrollArea#AreaAdvertenciasIndependientes > QWidget > QWidget {
                background-color: #1e1e2e;
            }
            """
        )  # Mantiene fondos redondeados únicamente sobre las etiquetas internas de cada tarjeta.

        diseno_exterior.addWidget(self.marco)  # Coloca el marco dentro del diálogo transparente.

        diseno_general = QVBoxLayout(self.marco)  # Divide verticalmente barra, contenido y pie.
        diseno_general.setContentsMargins(1, 1, 1, 1)  # Conserva visible el borde externo del marco.
        diseno_general.setSpacing(0)  # Une todas las regiones para simular una sola ventana.

        # ====================================================
        # Barra superior
        # ====================================================

        contenedor_barra = QFrame()  # Crea una región independiente para conservar las esquinas superiores.
        contenedor_barra.setObjectName("ContenedorBarraAdvertencias")  # Permite aplicar únicamente el fondo correspondiente a la cabecera.
        contenedor_barra.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt dibuje el fondo personalizado.

        contenedor_barra.setStyleSheet(
            """
            QFrame#ContenedorBarraAdvertencias {
                background-color: #181825;
                border: none;
                border-top-left-radius: 13px;
                border-top-right-radius: 13px;
            }
            """
        )  # Conserva la apariencia oscura y las esquinas redondeadas superiores.

        diseno_barra = QVBoxLayout(contenedor_barra)  # Aloja exclusivamente la barra reutilizable.
        diseno_barra.setContentsMargins(0, 0, 0, 0)  # Permite que la barra ocupe toda la cabecera.
        diseno_barra.setSpacing(0)  # Evita huecos innecesarios alrededor del título.

        self.barra_titulo = BarraTitulo(
            ventana=self,
            ruta_icono=self._ruta_icono(),
            titulo="Advertencias de compilación",
            mostrar_configuracion=False,
            mostrar_minimizar=False,
            mostrar_pantalla_completa=False,
            mostrar_cerrar=True,
            permitir_arrastre=True,
        )  # Reutiliza la misma estructura visual utilizada por Configuración.

        self.barra_titulo.setStyleSheet(
            """
            QWidget#BarraTitulo {
                background-color: transparent;
                border: none;
            }

            QLabel {
                background-color: transparent;
                border: none;
            }

            QLabel#TituloBarra {
                background-color: transparent;
                border: none;
            }
            """
        )  # Replica el tratamiento utilizado por Configuración para que icono y título formen un conjunto compacto sin recuadros visibles.

        if self.barra_titulo.boton_cerrar is not None:
            self.barra_titulo.boton_cerrar.setObjectName("BotonCerrarAdvertencias")  # Identifica únicamente el botón cerrar de esta ventana.

            self.barra_titulo.boton_cerrar.setStyleSheet(
                """
                QPushButton#BotonCerrarAdvertencias {
                    background-color: transparent;
                    color: #cdd6f4;
                    border: none;
                    border-top-right-radius: 12px;
                    padding: 0px;
                }

                QPushButton#BotonCerrarAdvertencias:hover {
                    background-color: #c42b1c;
                    color: #ffffff;
                    border: none;
                    border-top-right-radius: 12px;
                }

                QPushButton#BotonCerrarAdvertencias:pressed {
                    background-color: #a52016;
                    color: #ffffff;
                    border: none;
                    border-top-right-radius: 12px;
                }
                """
            )  # Conserva el comportamiento rojo utilizado para cerrar ventanas personalizadas.

        diseno_barra.addWidget(self.barra_titulo)  # Agrega la barra completa a la región superior.
        diseno_general.addWidget(contenedor_barra)  # Incorpora finalmente la cabecera al marco.

        separador = QFrame()  # Crea una línea visual entre cabecera y contenido.
        separador.setFixedHeight(1)  # Mantiene el separador extremadamente discreto.
        separador.setStyleSheet("background-color: #45475a; border: none;")  # Utiliza el mismo tono divisorio del resto de TecNet Finder.
        diseno_general.addWidget(separador)  # Inserta la línea inmediatamente después de la barra.

        # ====================================================
        # Contenido principal
        # ====================================================

        contenido = QWidget()  # Crea la región desplazable donde aparecerán todas las advertencias.
        diseno_contenido = QVBoxLayout(contenido)  # Organiza título, descripción y lista.
        diseno_contenido.setContentsMargins(22, 18, 22, 16)  # Proporciona aire alrededor del contenido principal.
        diseno_contenido.setSpacing(12)  # Mantiene una separación uniforme entre los bloques.

        titulo = QLabel("Advertencias detectadas")  # Identifica claramente el contenido de la ventana.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el estilo de títulos ya definido por TecNet Finder.
        diseno_contenido.addWidget(titulo)  # Coloca el título antes de la explicación.

        cantidad = len(self.advertencias)  # Calcula cuántos avisos pertenecen a esta compilación.

        descripcion = QLabel(
            f"Se detectaron {cantidad} "
            f"{'advertencia' if cantidad == 1 else 'advertencias'}. "
            "Haz doble clic sobre una advertencia para ir directamente "
            "a su ubicación en el código."
        )  # Explica también la interacción disponible sobre las tarjetas.

        descripcion.setObjectName("DescripcionConfiguracion")  # Mantiene una apariencia secundaria.
        descripcion.setWordWrap(True)  # Permite que el texto se adapte al ancho de la ventana.
        diseno_contenido.addWidget(descripcion)  # Sitúa la explicación encima de las tarjetas.

        self.area_desplazamiento = QScrollArea()  # Permite mostrar cualquier cantidad de advertencias sin ampliar la ventana.
        self.area_desplazamiento.setObjectName("AreaAdvertenciasIndependientes")  # Permite aplicar el fondo específico del área.
        self.area_desplazamiento.setFrameShape(QFrame.Shape.NoFrame)  # Evita añadir otro borde dentro del marco principal.
        self.area_desplazamiento.setWidgetResizable(True)  # Adapta automáticamente el contenedor interno al ancho disponible.
        self.area_desplazamiento.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide desplazamiento lateral innecesario.
        self.area_desplazamiento.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra la barra vertical solamente cuando haga falta.

        contenedor_advertencias = QWidget()  # Aloja todas las tarjetas dentro del área desplazable.
        diseno_lista = QVBoxLayout(contenedor_advertencias)  # Organiza las advertencias una debajo de otra.
        diseno_lista.setContentsMargins(0, 0, 6, 0)  # Reserva un pequeño espacio antes de la posible scrollbar.
        diseno_lista.setSpacing(10)  # Separa claramente una advertencia de la siguiente.

        for advertencia in self.advertencias:
            tarjeta = self._crear_tarjeta_advertencia(advertencia)  # Construye una tarjeta completa para el diagnóstico actual.
            tarjeta.activada.connect(self.advertencia_activada.emit)  # Reenvía el diagnóstico seleccionado hacia el controlador general.
            diseno_lista.addWidget(tarjeta)  # Coloca la tarjeta actual en la lista.

        diseno_lista.addStretch()  # Mantiene las tarjetas agrupadas hacia la parte superior.
        self.area_desplazamiento.setWidget(contenedor_advertencias)  # Introduce la lista completa dentro del área desplazable.
        diseno_contenido.addWidget(self.area_desplazamiento, 1)  # Permite que el área utilice todo el espacio vertical restante.
        diseno_general.addWidget(contenido, 1)  # Incorpora la región principal entre barra y pie.

        # ====================================================
        # Pie
        # ====================================================

        pie = QFrame()  # Crea la región inferior donde vive el botón Aceptar.
        pie.setObjectName("PieVentanaAdvertencias")  # Permite aislar completamente el estilo del pie.
        pie.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que se dibujen sus esquinas inferiores.

        pie.setStyleSheet(
            """
            QFrame#PieVentanaAdvertencias {
                background-color: #181825;
                border: none;
                border-top: 1px solid #313244;
                border-bottom-left-radius: 13px;
                border-bottom-right-radius: 13px;
            }
            """
        )  # Mantiene el mismo tono de la cabecera y cierra visualmente la ventana.

        diseno_pie = QHBoxLayout(pie)  # Organiza horizontalmente el botón inferior.
        diseno_pie.setContentsMargins(16, 10, 16, 10)  # Mantiene una separación cómoda respecto a los bordes.
        diseno_pie.addStretch()  # Empuja la acción hacia el extremo derecho.

        self.boton_aceptar = QPushButton("Aceptar")  # Permite cerrar la consulta de advertencias.
        self.boton_aceptar.setObjectName("BotonPrincipal")  # Utiliza el estilo azul de acción principal.
        self.boton_aceptar.setDefault(True)  # Permite cerrar también presionando Enter.
        self.boton_aceptar.clicked.connect(self.accept)  # Cierra la ventana cuando el usuario confirma.

        diseno_pie.addWidget(self.boton_aceptar)  # Coloca la acción después del espacio flexible.
        diseno_general.addWidget(pie)  # Agrega finalmente el pie al marco.

    def _crear_tarjeta_advertencia(self, advertencia: Diagnostico) -> TarjetaAdvertenciaInteractiva:
        tarjeta = TarjetaAdvertenciaInteractiva(advertencia, self)  # Crea una superficie que conoce el diagnóstico que debe activar.

        diseno = QVBoxLayout(tarjeta)  # Organiza encabezado, mensaje y solución.
        diseno.setContentsMargins(16, 13, 16, 13)  # Separa el contenido del borde de la tarjeta.
        diseno.setSpacing(7)  # Mantiene próximos los elementos relacionados.

        fila_encabezado = QHBoxLayout()  # Coloca código y ubicación en una misma línea.
        fila_encabezado.setContentsMargins(0, 0, 0, 0)  # Evita márgenes adicionales dentro de la tarjeta.

        codigo = QLabel(f"{advertencia.codigo} · {advertencia.categoria}")  # Identifica código y categoría de forma compacta.
        codigo.setObjectName("CodigoAdvertenciaIndependiente")  # Utiliza el tono amarillo propio de las advertencias.

        fila_encabezado.addWidget(codigo)  # Coloca el identificador en el extremo izquierdo.
        fila_encabezado.addStretch()  # Separa visualmente el código de su ubicación.

        if advertencia.linea is not None:
            ubicacion_texto = f"Línea {advertencia.linea}"  # Muestra inicialmente la línea de origen.

            if advertencia.columna is not None:
                ubicacion_texto += f", columna {advertencia.columna}"  # Añade la columna cuando también está disponible.
        else:
            ubicacion_texto = "Ubicación no especificada"  # Informa claramente cuando el diagnóstico no puede navegarse.

        ubicacion = QLabel(ubicacion_texto)  # Crea la representación visual de la ubicación.
        ubicacion.setObjectName("UbicacionAdvertenciaIndependiente")  # Utiliza un tono secundario discreto.

        fila_encabezado.addWidget(ubicacion)  # Coloca la ubicación en el extremo derecho.
        diseno.addLayout(fila_encabezado)  # Incorpora el encabezado completo a la tarjeta.

        titulo_mensaje = QLabel("Mensaje")  # Identifica el bloque descriptivo del diagnóstico.
        titulo_mensaje.setObjectName("TituloCampoAdvertenciaIndependiente")  # Resalta el encabezado sin competir con el código.
        diseno.addWidget(titulo_mensaje)  # Coloca el título antes del mensaje.

        mensaje = QLabel(advertencia.mensaje)  # Muestra exactamente la explicación formal producida por el compilador.
        mensaje.setObjectName("TextoAdvertenciaIndependiente")  # Utiliza el color normal de lectura.
        mensaje.setWordWrap(True)  # Ajusta textos extensos dentro del ancho disponible.
        mensaje.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite copiar información si el usuario la necesita.
        diseno.addWidget(mensaje)  # Incorpora el mensaje después de su título.

        titulo_solucion = QLabel("Solución")  # Identifica la recomendación asociada con la advertencia.
        titulo_solucion.setObjectName("TituloCampoAdvertenciaIndependiente")  # Utiliza el mismo formato que Mensaje.
        diseno.addWidget(titulo_solucion)  # Separa visualmente solución y explicación.

        solucion = QLabel(advertencia.solucion or "No se proporcionó una solución específica.")  # Muestra una recomendación o un respaldo comprensible.
        solucion.setObjectName("TextoAdvertenciaIndependiente")  # Mantiene el color normal de lectura.
        solucion.setWordWrap(True)  # Permite utilizar varias líneas cuando sea necesario.
        solucion.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite copiar la solución directamente.
        diseno.addWidget(solucion)  # Completa el contenido visible de la tarjeta.

        for etiqueta in (codigo, ubicacion, titulo_mensaje, mensaje, titulo_solucion, solucion):
            etiqueta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite que el doble clic llegue a la tarjeta completa en lugar de quedarse atrapado dentro de una etiqueta.

        return tarjeta  # Devuelve la tarjeta completamente preparada.

    def _centrar_en_area_disponible(self) -> None:
        pantalla = None  # Prepara una referencia al monitor donde deberá mostrarse la ventana.
        padre = self.parentWidget()  # Obtiene la ventana principal cuando continúa disponible.

        if padre is not None and padre.windowHandle() is not None:
            pantalla = padre.windowHandle().screen()  # Prefiere el mismo monitor utilizado actualmente por TecNet Finder.

        if pantalla is None:
            pantalla = self.screen()  # Utiliza el monitor asignado por Qt como segunda opción.

        if pantalla is None:
            pantalla = QApplication.primaryScreen()  # Utiliza el monitor principal solamente cuando no existe otra referencia.

        if pantalla is None:
            return  # Evita intentar posicionar la ventana si Qt todavía no dispone de información de pantalla.

        area = pantalla.availableGeometry()  # Obtiene la región disponible excluyendo elementos del sistema como la barra de tareas.
        centro = padre.frameGeometry().center() if padre is not None else area.center()  # Prefiere centrarse respecto a TecNet Finder.
        posicion_x = centro.x() - self.width() // 2  # Calcula la coordenada horizontal centrada.
        posicion_y = centro.y() - self.height() // 2  # Calcula la coordenada vertical centrada.
        posicion_x = max(area.left(), min(posicion_x, area.right() - self.width() + 1))  # Mantiene toda la ventana dentro de la pantalla.
        posicion_y = max(area.top(), min(posicion_y, area.bottom() - self.height() + 1))  # Hace lo mismo verticalmente.

        self.move(posicion_x, posicion_y)  # Coloca finalmente la ventana en la posición segura calculada.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt termine primero de preparar la ventana.
        self._centrar_en_area_disponible()  # Centra la ventana cuando sus dimensiones reales ya son conocidas.