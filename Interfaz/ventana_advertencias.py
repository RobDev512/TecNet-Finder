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

from pathlib import Path  # Permite localizar el icono oficial de TecNet Finder.

from PySide6.QtCore import Qt, Signal  # Permite emitir la advertencia seleccionada y controlar diferentes opciones de Qt.
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget  # Importa los controles utilizados por la ventana.

from Interfaz.barra_titulo import BarraTitulo  # Reutiliza la barra personalizada oficial.
from Motor.diagnosticos import Diagnostico  # Define la estructura recibida por cada advertencia.


class TarjetaAdvertenciaInteractiva(QFrame):  # Representa una advertencia que puede activarse mediante doble clic.
    activada = Signal(object)  # Envía el Diagnostico original asociado con la tarjeta.

    def __init__(
        self,
        advertencia: Diagnostico,
        padre=None,
    ):
        super().__init__(padre)  # Inicializa la superficie estándar de Qt.

        self.advertencia = advertencia  # Conserva el diagnóstico exacto que representa esta tarjeta.

        self.setObjectName(
            "TarjetaAdvertenciaIndependiente"
        )  # Permite utilizar el estilo específico preparado para las advertencias.

        if advertencia.linea is not None:
            self.setCursor(
                Qt.CursorShape.PointingHandCursor
            )  # Indica que una advertencia con ubicación puede utilizarse para navegar.

            self.setToolTip(
                "Doble clic para ir a esta advertencia en el código."
            )  # Explica directamente la interacción disponible.
        else:
            self.setToolTip(
                "Esta advertencia no tiene una ubicación específica en el código."
            )  # Evita prometer navegación cuando no existe línea de origen.

    def mouseDoubleClickEvent(self, evento) -> None:
        if (
            evento.button() == Qt.MouseButton.LeftButton
            and self.advertencia.linea is not None
        ):
            self.activada.emit(
                self.advertencia
            )  # Entrega el diagnóstico original a la ventana superior.

            evento.accept()  # Informa a Qt que el doble clic fue procesado.
            return

        super().mouseDoubleClickEvent(
            evento
        )  # Conserva el comportamiento convencional para cualquier otra interacción.


class VentanaAdvertencias(QDialog):  # Representa la ventana independiente de advertencias de compilación.
    advertencia_activada = Signal(object)  # Informa qué advertencia debe abrirse dentro del editor.

    def __init__(
        self,
        advertencias: list[Diagnostico],
        padre=None,
    ):
        super().__init__(padre)  # Vincula la ventana con TecNet Finder sin volverla modal.

        self.advertencias = list(
            advertencias
        )  # Conserva una copia estable de los avisos correspondientes con esta compilación.

        self.setObjectName("VentanaAdvertencias")
        self.setWindowTitle("Advertencias de compilación")

        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )  # Reutiliza nuestra propia barra de título.

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )  # Permite representar correctamente las esquinas exteriores redondeadas.

        self.setModal(False)  # No bloquea la interacción con la ventana principal.

        self.setWindowModality(
            Qt.WindowModality.NonModal
        )  # Confirma explícitamente el comportamiento no modal.

        self.setFixedSize(
            700,
            540,
        )  # Mantiene una superficie cómoda sin cubrir toda la aplicación.

        self.setStyleSheet(
            "QDialog#VentanaAdvertencias { background-color: transparent; }"
        )

        if padre is not None:
            self.setWindowIcon(
                padre.windowIcon()
            )

        self._construir_interfaz()

    def _ruta_icono(self) -> Path:
        return (
            Path(__file__).resolve().parent.parent
            / "Recursos"
            / "LogoTNF.ico"
        )

    def _construir_interfaz(self) -> None:
        diseno_exterior = QVBoxLayout(self)
        diseno_exterior.setContentsMargins(7, 7, 7, 7)
        diseno_exterior.setSpacing(0)

        self.marco = QFrame(self)
        self.marco.setObjectName("MarcoVentanaAdvertencias")
        self.marco.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

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
                border-color: #f9e2af;
                background-color: #1c1c2c;
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
        )  # Define únicamente los elementos propios de esta ventana.

        diseno_exterior.addWidget(self.marco)

        diseno_general = QVBoxLayout(self.marco)
        diseno_general.setContentsMargins(1, 1, 1, 1)
        diseno_general.setSpacing(0)

        # ====================================================
        # Barra superior
        # ====================================================

        contenedor_barra = QFrame()
        contenedor_barra.setObjectName("ContenedorBarraAdvertencias")
        contenedor_barra.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        contenedor_barra.setStyleSheet(
            """
            QFrame#ContenedorBarraAdvertencias {
                background-color: #181825;
                border: none;
                border-top-left-radius: 13px;
                border-top-right-radius: 13px;
            }
            """
        )

        diseno_barra = QVBoxLayout(contenedor_barra)
        diseno_barra.setContentsMargins(0, 0, 0, 0)
        diseno_barra.setSpacing(0)

        self.barra_titulo = BarraTitulo(
            ventana=self,
            ruta_icono=self._ruta_icono(),
            titulo="Advertencias de compilación",
            mostrar_configuracion=False,
            mostrar_minimizar=False,
            mostrar_pantalla_completa=False,
            mostrar_cerrar=True,
            permitir_arrastre=True,
        )

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
        )

        if self.barra_titulo.boton_cerrar is not None:
            self.barra_titulo.boton_cerrar.setObjectName(
                "BotonCerrarAdvertencias"
            )

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
            )

        diseno_barra.addWidget(self.barra_titulo)
        diseno_general.addWidget(contenedor_barra)

        separador = QFrame()
        separador.setFixedHeight(1)
        separador.setStyleSheet(
            "background-color: #45475a; border: none;"
        )

        diseno_general.addWidget(separador)

        # ====================================================
        # Contenido principal
        # ====================================================

        contenido = QWidget()
        diseno_contenido = QVBoxLayout(contenido)
        diseno_contenido.setContentsMargins(22, 18, 22, 16)
        diseno_contenido.setSpacing(12)

        titulo = QLabel("Advertencias detectadas")
        titulo.setObjectName("TituloConfiguracion")
        diseno_contenido.addWidget(titulo)

        cantidad = len(self.advertencias)

        descripcion = QLabel(
            f"Se detectaron {cantidad} "
            f"{'advertencia' if cantidad == 1 else 'advertencias'}. "
            "Haz doble clic sobre una advertencia para ir directamente "
            "a su ubicación en el código."
        )  # Explica también la nueva interacción disponible.
        descripcion.setObjectName("DescripcionConfiguracion")
        descripcion.setWordWrap(True)
        diseno_contenido.addWidget(descripcion)

        self.area_desplazamiento = QScrollArea()
        self.area_desplazamiento.setObjectName("AreaAdvertenciasIndependientes")
        self.area_desplazamiento.setFrameShape(QFrame.Shape.NoFrame)
        self.area_desplazamiento.setWidgetResizable(True)

        self.area_desplazamiento.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.area_desplazamiento.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        contenedor_advertencias = QWidget()
        diseno_lista = QVBoxLayout(contenedor_advertencias)
        diseno_lista.setContentsMargins(0, 0, 6, 0)
        diseno_lista.setSpacing(10)

        for advertencia in self.advertencias:
            tarjeta = self._crear_tarjeta_advertencia(
                advertencia
            )

            tarjeta.activada.connect(
                self.advertencia_activada.emit
            )  # Reenvía el diagnóstico seleccionado hacia el controlador general.

            diseno_lista.addWidget(tarjeta)

        diseno_lista.addStretch()

        self.area_desplazamiento.setWidget(
            contenedor_advertencias
        )

        diseno_contenido.addWidget(
            self.area_desplazamiento,
            1,
        )

        diseno_general.addWidget(
            contenido,
            1,
        )

        # ====================================================
        # Pie
        # ====================================================

        pie = QFrame()
        pie.setObjectName("PieVentanaAdvertencias")
        pie.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

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
        )

        diseno_pie = QHBoxLayout(pie)
        diseno_pie.setContentsMargins(16, 10, 16, 10)
        diseno_pie.addStretch()

        self.boton_aceptar = QPushButton("Aceptar")
        self.boton_aceptar.setObjectName("BotonPrincipal")
        self.boton_aceptar.setDefault(True)
        self.boton_aceptar.clicked.connect(self.accept)

        diseno_pie.addWidget(self.boton_aceptar)
        diseno_general.addWidget(pie)

    def _crear_tarjeta_advertencia(
        self,
        advertencia: Diagnostico,
    ) -> TarjetaAdvertenciaInteractiva:
        tarjeta = TarjetaAdvertenciaInteractiva(
            advertencia,
            self,
        )  # Crea una superficie que conoce el diagnóstico que debe activar.

        diseno = QVBoxLayout(tarjeta)
        diseno.setContentsMargins(16, 13, 16, 13)
        diseno.setSpacing(7)

        fila_encabezado = QHBoxLayout()
        fila_encabezado.setContentsMargins(0, 0, 0, 0)

        codigo = QLabel(
            f"{advertencia.codigo} · {advertencia.categoria}"
        )
        codigo.setObjectName("CodigoAdvertenciaIndependiente")

        fila_encabezado.addWidget(codigo)
        fila_encabezado.addStretch()

        if advertencia.linea is not None:
            ubicacion_texto = f"Línea {advertencia.linea}"

            if advertencia.columna is not None:
                ubicacion_texto += f", columna {advertencia.columna}"
        else:
            ubicacion_texto = "Ubicación no especificada"

        ubicacion = QLabel(ubicacion_texto)
        ubicacion.setObjectName("UbicacionAdvertenciaIndependiente")

        fila_encabezado.addWidget(ubicacion)
        diseno.addLayout(fila_encabezado)

        titulo_mensaje = QLabel("Mensaje")
        titulo_mensaje.setObjectName("TituloCampoAdvertenciaIndependiente")
        diseno.addWidget(titulo_mensaje)

        mensaje = QLabel(advertencia.mensaje)
        mensaje.setObjectName("TextoAdvertenciaIndependiente")
        mensaje.setWordWrap(True)
        mensaje.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        diseno.addWidget(mensaje)

        titulo_solucion = QLabel("Solución")
        titulo_solucion.setObjectName("TituloCampoAdvertenciaIndependiente")
        diseno.addWidget(titulo_solucion)

        solucion = QLabel(
            advertencia.solucion or "No se proporcionó una solución específica."
        )
        solucion.setObjectName("TextoAdvertenciaIndependiente")
        solucion.setWordWrap(True)
        solucion.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        diseno.addWidget(solucion)

        # Los QLabel normalmente reciben los eventos del ratón.
        # Los hacemos transparentes para que el doble clic alcance
        # correctamente la tarjeta completa.
        for etiqueta in (
            codigo,
            ubicacion,
            titulo_mensaje,
            mensaje,
            titulo_solucion,
            solucion,
        ):
            etiqueta.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )

        return tarjeta

    def _centrar_en_area_disponible(self) -> None:
        pantalla = None
        padre = self.parentWidget()

        if padre is not None and padre.windowHandle() is not None:
            pantalla = padre.windowHandle().screen()

        if pantalla is None:
            pantalla = self.screen()

        if pantalla is None:
            pantalla = QApplication.primaryScreen()

        if pantalla is None:
            return

        area = pantalla.availableGeometry()

        if padre is not None:
            centro = padre.frameGeometry().center()
        else:
            centro = area.center()

        posicion_x = centro.x() - self.width() // 2
        posicion_y = centro.y() - self.height() // 2

        posicion_x = max(
            area.left(),
            min(
                posicion_x,
                area.right() - self.width() + 1,
            ),
        )

        posicion_y = max(
            area.top(),
            min(
                posicion_y,
                area.bottom() - self.height() + 1,
            ),
        )

        self.move(posicion_x, posicion_y)

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._centrar_en_area_disponible()