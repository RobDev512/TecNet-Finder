# ============================================================
# Archivo: ventana_advertencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene la ventana independiente utilizada para consultar
# errores y advertencias producidos por una compilación.
#
# La ventana conserva el nombre histórico del archivo y de la
# clase para no romper integraciones existentes, pero ahora
# organiza los diagnósticos en dos pestañas:
#
# - Errores.
# - Advertencias.
#
# Cuando existen ambos tipos, Errores se muestra primero.
# La ventana continúa siendo compatible con modalidad modal o
# no modal y permite navegar al código mediante doble clic.
# ============================================================

from pathlib import Path  # Permite localizar los iconos utilizados por la ventana.

from PySide6.QtCore import Qt, Signal  # Proporciona señales y banderas de interacción.
from PySide6.QtGui import QIcon  # Permite asignar un icono representativo a la ventana.
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QTabWidget, QVBoxLayout, QWidget  # Importa los controles utilizados por la ventana.

from Interfaz.apariencia.recursos_tema import ruta_icono_comun, ruta_icono_oscuro  # Permite seleccionar un icono de error o advertencia.
from Interfaz.ventanas.barra_titulo import BarraTitulo  # Reutiliza la barra personalizada oficial.
from Motor.compilacion.diagnosticos import Diagnostico  # Define la estructura recibida por cada diagnóstico.


class TarjetaDiagnosticoInteractiva(QFrame):  # Representa un error o advertencia navegable mediante doble clic.
    activada = Signal(object)  # Envía el Diagnostico original asociado con la tarjeta.

    def __init__(self, diagnostico: Diagnostico, padre=None):
        super().__init__(padre)  # Inicializa la superficie estándar de Qt.
        self.diagnostico = diagnostico  # Conserva exactamente el diagnóstico representado.
        self.es_error = diagnostico.severidad == "error"  # Distingue visualmente problemas bloqueantes y advertencias.
        self.setObjectName("TarjetaErrorIndependiente" if self.es_error else "TarjetaAdvertenciaIndependiente")  # Permite aplicar un borde específico según severidad.

        if diagnostico.linea is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que la tarjeta puede navegar al código.
            self.setToolTip("Doble clic para ir a este diagnóstico en el código.")  # Explica directamente la interacción disponible.
        else:
            self.setToolTip("Este diagnóstico no tiene una ubicación específica en el código.")  # Evita prometer navegación cuando no existe línea de origen.

    def mouseDoubleClickEvent(self, evento) -> None:
        if evento.button() == Qt.MouseButton.LeftButton and self.diagnostico.linea is not None:
            self.activada.emit(self.diagnostico)  # Entrega el diagnóstico original a la ventana superior.
            evento.accept()  # Informa a Qt que el doble clic fue procesado.
            return

        super().mouseDoubleClickEvent(evento)  # Conserva el comportamiento convencional para cualquier otra interacción.


class VentanaAdvertencias(QDialog):  # Conserva el nombre histórico, pero ahora muestra errores y advertencias.
    diagnostico_activado = Signal(object)  # Informa qué diagnóstico debe abrirse dentro del editor.
    advertencia_activada = Signal(object)  # Mantiene compatibilidad con integraciones anteriores que escuchaban esta señal.

    def __init__(self, diagnosticos: list[Diagnostico], padre=None):
        super().__init__(padre)  # Vincula la ventana con TecNet Finder sin imponer todavía modalidad.
        self.diagnosticos = list(diagnosticos)  # Conserva una copia estable de todos los diagnósticos de la compilación.
        self.errores = [diagnostico for diagnostico in self.diagnosticos if diagnostico.severidad == "error"]  # Agrupa primero problemas bloqueantes.
        self.advertencias = [
            diagnostico
            for diagnostico in self.diagnosticos
            if diagnostico.severidad in ("warning", "advertencia")
        ]  # Agrupa después avisos no bloqueantes.
        self.pestanas_diagnosticos = None  # Se inicializa durante la construcción y queda disponible para pruebas e interacción.

        self.setObjectName("VentanaAdvertencias")  # Conserva el identificador visual histórico.
        self.setWindowTitle("Diagnósticos de compilación")  # Actualiza el título visible con el nuevo alcance.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)  # Reutiliza nuestra propia barra de título.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite representar correctamente las esquinas exteriores redondeadas.
        self.setModal(False)  # Deja la modalidad definitiva en manos de ControlConfiguracion.
        self.setWindowModality(Qt.WindowModality.NonModal)  # Mantiene inicialmente comportamiento no modal.
        self.setFixedSize(760, 580)  # Reserva espacio suficiente para pestañas, tarjetas y texto.
        self.setStyleSheet("QDialog#VentanaAdvertencias { background-color: transparent; }")  # Mantiene transparente únicamente el fondo exterior del diálogo.
        self.setWindowIcon(QIcon(str(self._ruta_icono())))  # Utiliza error como prioridad visual cuando existe al menos uno.
        self._construir_interfaz()  # Construye barra, pestañas y pie.

    def _ruta_icono(self) -> Path:
        if self.errores:
            return ruta_icono_comun("Error.png")  # Da prioridad al icono de error cuando la compilación contiene problemas bloqueantes.

        return ruta_icono_oscuro("Advertencia.png")  # Utiliza el icono histórico cuando solamente existen advertencias.

    def _construir_interfaz(self) -> None:
        diseno_exterior = QVBoxLayout(self)  # Crea el margen exterior responsable de mostrar correctamente las esquinas redondeadas.
        diseno_exterior.setContentsMargins(7, 7, 7, 7)  # Separa el marco de los límites transparentes del diálogo.
        diseno_exterior.setSpacing(0)  # Mantiene unido el marco principal.

        self.marco = QFrame(self)  # Crea la superficie principal visible de la ventana.
        self.marco.setObjectName("MarcoVentanaAdvertencias")  # Conserva el identificador utilizado por el estilo existente.
        self.marco.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt pinte correctamente el fondo redondeado.

        self.marco.setStyleSheet(
            """
            QFrame#MarcoVentanaAdvertencias {
                background-color: #1e1e2e;
                border: 1px solid #cdd6f4;
                border-radius: 14px;
            }

            QFrame#TarjetaErrorIndependiente,
            QFrame#TarjetaAdvertenciaIndependiente {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 8px;
            }

            QFrame#TarjetaErrorIndependiente:hover {
                background-color: #1c1c2c;
                border-color: #f38ba8;
            }

            QFrame#TarjetaAdvertenciaIndependiente:hover {
                background-color: #1c1c2c;
                border-color: #f9e2af;
            }

            QFrame#TarjetaErrorIndependiente QLabel,
            QFrame#TarjetaAdvertenciaIndependiente QLabel {
                background-color: #1e1e2e;
                border: none;
                border-radius: 7px;
                padding: 2px 5px;
            }

            QLabel#CodigoErrorIndependiente {
                color: #f38ba8;
                font-size: 11pt;
                font-weight: bold;
            }

            QLabel#CodigoAdvertenciaIndependiente {
                color: #f9e2af;
                font-size: 11pt;
                font-weight: bold;
            }

            QLabel#UbicacionDiagnosticoIndependiente {
                color: #a6adc8;
            }

            QLabel#TituloCampoDiagnosticoIndependiente {
                color: #cdd6f4;
                font-weight: bold;
            }

            QLabel#TextoDiagnosticoIndependiente {
                color: #cdd6f4;
            }

            QScrollArea#AreaDiagnosticosIndependientes {
                background-color: #1e1e2e;
                border: none;
            }

            QScrollArea#AreaDiagnosticosIndependientes > QWidget > QWidget {
                background-color: #1e1e2e;
            }
            """
        )  # Mantiene el diseño existente y agrega una variante roja para errores.

        diseno_exterior.addWidget(self.marco)  # Coloca el marco dentro del diálogo transparente.

        diseno_general = QVBoxLayout(self.marco)  # Divide verticalmente barra, contenido y pie.
        diseno_general.setContentsMargins(1, 1, 1, 1)  # Conserva visible el borde externo del marco.
        diseno_general.setSpacing(0)  # Une todas las regiones para simular una sola ventana.

        # ====================================================
        # Barra superior
        # ====================================================

        contenedor_barra = QFrame()  # Crea una región independiente para conservar las esquinas superiores.
        contenedor_barra.setObjectName("ContenedorBarraAdvertencias")  # Conserva el identificador visual histórico.
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
        )  # Mantiene la apariencia oscura y las esquinas redondeadas superiores.

        diseno_barra = QVBoxLayout(contenedor_barra)  # Aloja exclusivamente la barra reutilizable.
        diseno_barra.setContentsMargins(0, 0, 0, 0)  # Permite que la barra ocupe toda la cabecera.
        diseno_barra.setSpacing(0)  # Evita huecos innecesarios alrededor del título.

        self.barra_titulo = BarraTitulo(
            ventana=self,
            ruta_icono=self._ruta_icono(),
            titulo="Diagnósticos de compilación",
            mostrar_configuracion=False,
            mostrar_minimizar=False,
            mostrar_pantalla_completa=False,
            mostrar_cerrar=True,
            permitir_arrastre=True,
        )  # Reutiliza la misma barra preparada para diálogos secundarios.

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
        )  # Evita recuadros internos alrededor del icono y el título.

        if self.barra_titulo.boton_cerrar is not None:
            self.barra_titulo.boton_cerrar.setObjectName("BotonCerrarAdvertencias")  # Conserva un estilo aislado para este botón.

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
        # Contenido
        # ====================================================

        contenido = QWidget()  # Crea la región principal donde viven resumen y pestañas.
        diseno_contenido = QVBoxLayout(contenido)  # Organiza título, explicación y pestañas.
        diseno_contenido.setContentsMargins(22, 18, 22, 16)  # Proporciona aire alrededor del contenido principal.
        diseno_contenido.setSpacing(12)  # Mantiene una separación uniforme entre los bloques.

        titulo = QLabel("Diagnósticos detectados")  # Identifica claramente el contenido de la ventana.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el estilo de títulos ya definido por TecNet Finder.
        diseno_contenido.addWidget(titulo)  # Coloca el título antes de la explicación.

        cantidad_errores = len(self.errores)  # Cuenta los errores bloqueantes.
        cantidad_advertencias = len(self.advertencias)  # Cuenta los avisos no bloqueantes.

        descripcion = QLabel(
            f"Errores: {cantidad_errores} | Advertencias: {cantidad_advertencias}. "
            "Haz doble clic sobre cualquier diagnóstico con ubicación para ir directamente al código."
        )  # Resume el resultado y explica la interacción disponible.

        descripcion.setObjectName("DescripcionConfiguracion")  # Mantiene una apariencia secundaria.
        descripcion.setWordWrap(True)  # Permite que el texto se adapte al ancho de la ventana.
        diseno_contenido.addWidget(descripcion)  # Sitúa la explicación encima de las pestañas.

        self.pestanas_diagnosticos = QTabWidget()  # Permite consultar errores y advertencias sin perder la Tabla VLSM de la ventana principal.
        self.pestanas_diagnosticos.setObjectName("PestanasDiagnosticosIndependientes")  # Facilita futuras personalizaciones del componente.

        if self.errores:
            self.pestana_errores = self._crear_pestana_diagnosticos(self.errores)  # Construye primero la lista de mayor prioridad.
            self.pestanas_diagnosticos.addTab(
                self.pestana_errores,
                f"Errores ({len(self.errores)})",
            )  # Coloca Errores como primera pestaña.
        else:
            self.pestana_errores = None  # Expone claramente que esta compilación no produjo errores.

        if self.advertencias:
            self.pestana_advertencias = self._crear_pestana_diagnosticos(self.advertencias)  # Construye la lista de avisos.
            self.pestanas_diagnosticos.addTab(
                self.pestana_advertencias,
                f"Advertencias ({len(self.advertencias)})",
            )  # Coloca Advertencias después de los errores.
        else:
            self.pestana_advertencias = None  # Expone claramente que esta compilación no produjo advertencias.

        if self.errores:
            self.pestanas_diagnosticos.setCurrentIndex(0)  # Garantiza que los errores tengan prioridad cuando ambos tipos existen.

        diseno_contenido.addWidget(self.pestanas_diagnosticos, 1)  # Permite que las pestañas utilicen toda la superficie vertical restante.
        diseno_general.addWidget(contenido, 1)  # Incorpora la región principal entre barra y pie.

        # ====================================================
        # Pie
        # ====================================================

        pie = QFrame()  # Crea la región inferior donde vive el botón Aceptar.
        pie.setObjectName("PieVentanaAdvertencias")  # Conserva el identificador visual histórico.
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

        self.boton_aceptar = QPushButton("Aceptar")  # Permite cerrar la consulta de diagnósticos.
        self.boton_aceptar.setObjectName("BotonPrincipal")  # Utiliza el estilo azul de acción principal.
        self.boton_aceptar.setDefault(True)  # Permite cerrar también presionando Enter.
        self.boton_aceptar.clicked.connect(self.accept)  # Cierra la ventana cuando el usuario confirma.

        diseno_pie.addWidget(self.boton_aceptar)  # Coloca la acción después del espacio flexible.
        diseno_general.addWidget(pie)  # Agrega finalmente el pie al marco.

    def _crear_pestana_diagnosticos(self, diagnosticos: list[Diagnostico]) -> QWidget:
        pagina = QWidget()  # Crea la página perteneciente a Errores o Advertencias.
        pagina.setObjectName("PaginaDiagnosticosIndependientes")  # Permite mantener transparente la superficie propia de QTabWidget.

        diseno_pagina = QVBoxLayout(pagina)  # Organiza el marco redondeado dentro de la pestaña.
        diseno_pagina.setContentsMargins(0, 0, 0, 0)  # Evita márgenes externos que separen innecesariamente la pestaña.
        diseno_pagina.setSpacing(0)  # Mantiene una única superficie visual.

        marco = QFrame()  # Crea el verdadero contenedor visible de la pestaña.
        marco.setObjectName("ContenedorDiagnosticosIndependientes")  # Permite aplicar fondo, borde y esquinas redondeadas reales.
        marco.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Obliga a Qt a pintar correctamente su superficie.

        diseno_marco = QVBoxLayout(marco)  # Aloja el scroll dentro del marco redondeado.
        diseno_marco.setContentsMargins(10, 10, 10, 10)  # Aleja contenido y scrollbar de todas las esquinas.
        diseno_marco.setSpacing(0)  # Evita espacios internos innecesarios.

        area = QScrollArea()  # Permite mostrar cualquier cantidad de diagnósticos.
        area.setObjectName("AreaDiagnosticosIndependientes")  # Identifica exclusivamente este scroll.
        area.setFrameShape(QFrame.Shape.NoFrame)  # Elimina el marco rectangular propio de QScrollArea.
        area.setWidgetResizable(True)  # Adapta el contenido al espacio disponible.
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Impide barras horizontales.
        area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Muestra desplazamiento únicamente cuando hace falta.
        area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Permite aprovechar toda la superficie interior.
        area.viewport().setAutoFillBackground(False)  # Evita que el viewport tape el fondo redondeado con un rectángulo propio.

        contenedor_lista = QWidget()  # Contiene las tarjetas dentro del scroll.
        contenedor_lista.setObjectName("ListaDiagnosticosIndependientes")  # Permite mantenerlo visualmente transparente.

        diseno_lista = QVBoxLayout(contenedor_lista)  # Organiza verticalmente todas las tarjetas.
        diseno_lista.setContentsMargins(0, 0, 0, 0)  # El margen exterior ya pertenece al marco redondeado.
        diseno_lista.setSpacing(10)  # Separa uniformemente varias tarjetas.

        cantidad_diagnosticos = len(diagnosticos)  # Permite adaptar la distribución cuando solamente existe un elemento.

        for diagnostico in diagnosticos:
            tarjeta = self._crear_tarjeta_diagnostico(diagnostico)  # Construye la tarjeta completa del diagnóstico.
            tarjeta.activada.connect(self._emitir_diagnostico)  # Mantiene la navegación mediante doble clic.

            if cantidad_diagnosticos == 1:
                tarjeta.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding,
                )  # Hace que una tarjeta única aproveche también el espacio vertical disponible.

                diseno_lista.addWidget(
                    tarjeta,
                    1,
                )  # Entrega el espacio libre a la única tarjeta.
            else:
                tarjeta.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred,
                )  # Conserva la altura natural cuando existen varios diagnósticos.

                diseno_lista.addWidget(tarjeta)  # Añade cada diagnóstico consecutivamente.

        if cantidad_diagnosticos > 1:
            diseno_lista.addStretch()  # Mantiene agrupadas arriba las tarjetas cuando existe una lista larga.

        area.setWidget(contenedor_lista)  # Introduce finalmente las tarjetas dentro del área desplazable.
        diseno_marco.addWidget(area, 1)  # Coloca el scroll dentro del marco y lejos de sus esquinas.
        diseno_pagina.addWidget(marco, 1)  # Utiliza el marco redondeado como única superficie visible de la pestaña.

        return pagina  # Devuelve la pestaña completamente preparada.
    
    def _crear_tarjeta_diagnostico(self, diagnostico: Diagnostico) -> TarjetaDiagnosticoInteractiva:
        tarjeta = TarjetaDiagnosticoInteractiva(diagnostico, self)  # Crea una superficie que conoce el diagnóstico que debe activar.

        diseno = QVBoxLayout(tarjeta)  # Organiza encabezado, mensaje y solución.
        diseno.setContentsMargins(16, 13, 16, 13)  # Separa el contenido del borde de la tarjeta.
        diseno.setSpacing(7)  # Mantiene próximos los elementos relacionados.

        fila_encabezado = QHBoxLayout()  # Coloca código y ubicación en una misma línea.
        fila_encabezado.setContentsMargins(0, 0, 0, 0)  # Evita márgenes adicionales dentro de la tarjeta.

        codigo = QLabel(f"{diagnostico.codigo} · {diagnostico.categoria}")  # Identifica código y categoría de forma compacta.
        codigo.setObjectName(
            "CodigoErrorIndependiente"
            if diagnostico.severidad == "error"
            else "CodigoAdvertenciaIndependiente"
        )  # Utiliza rojo o amarillo según severidad.

        fila_encabezado.addWidget(codigo)  # Coloca el identificador en el extremo izquierdo.
        fila_encabezado.addStretch()  # Separa visualmente el código de su ubicación.

        if diagnostico.linea is not None:
            ubicacion_texto = f"Línea {diagnostico.linea}"  # Muestra inicialmente la línea de origen.

            if diagnostico.columna is not None:
                ubicacion_texto += f", columna {diagnostico.columna}"  # Añade la columna cuando también está disponible.
        else:
            ubicacion_texto = "Ubicación no especificada"  # Informa claramente cuando el diagnóstico no puede navegarse.

        ubicacion = QLabel(ubicacion_texto)  # Crea la representación visual de la ubicación.
        ubicacion.setObjectName("UbicacionDiagnosticoIndependiente")  # Utiliza un tono secundario discreto.

        fila_encabezado.addWidget(ubicacion)  # Coloca la ubicación en el extremo derecho.
        diseno.addLayout(fila_encabezado)  # Incorpora el encabezado completo a la tarjeta.

        titulo_mensaje = QLabel("Mensaje")  # Identifica el bloque descriptivo del diagnóstico.
        titulo_mensaje.setObjectName("TituloCampoDiagnosticoIndependiente")  # Resalta el encabezado sin competir con el código.
        diseno.addWidget(titulo_mensaje)  # Coloca el título antes del mensaje.

        mensaje = QLabel(diagnostico.mensaje)  # Muestra exactamente la explicación formal producida por el compilador.
        mensaje.setObjectName("TextoDiagnosticoIndependiente")  # Utiliza el color normal de lectura.
        mensaje.setWordWrap(True)  # Ajusta textos extensos dentro del ancho disponible.
        mensaje.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite copiar información si el usuario la necesita.
        diseno.addWidget(mensaje)  # Incorpora el mensaje después de su título.

        titulo_solucion = QLabel("Solución")  # Identifica la recomendación asociada con el diagnóstico.
        titulo_solucion.setObjectName("TituloCampoDiagnosticoIndependiente")  # Utiliza el mismo formato que Mensaje.
        diseno.addWidget(titulo_solucion)  # Separa visualmente solución y explicación.

        solucion = QLabel(
            diagnostico.solucion or "No se proporcionó una solución específica."
        )  # Muestra una recomendación o un respaldo comprensible.

        solucion.setObjectName("TextoDiagnosticoIndependiente")  # Mantiene el color normal de lectura.
        solucion.setWordWrap(True)  # Permite utilizar varias líneas cuando sea necesario.
        solucion.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite copiar la solución directamente.
        diseno.addWidget(solucion)  # Completa el contenido visible de la tarjeta.

        for etiqueta in (
            codigo,
            ubicacion,
            titulo_mensaje,
            mensaje,
            titulo_solucion,
            solucion,
        ):
            etiqueta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Permite que el doble clic llegue a la tarjeta completa.

        return tarjeta  # Devuelve la tarjeta completamente preparada.

    def _emitir_diagnostico(self, diagnostico: Diagnostico) -> None:
        self.diagnostico_activado.emit(diagnostico)  # Emite la señal general utilizada por la nueva integración.

        if diagnostico.severidad in ("warning", "advertencia"):
            self.advertencia_activada.emit(diagnostico)  # Conserva compatibilidad con cualquier conexión histórica limitada a advertencias.

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

        posicion_x = max(
            area.left(),
            min(posicion_x, area.right() - self.width() + 1),
        )  # Mantiene toda la ventana dentro de la pantalla.

        posicion_y = max(
            area.top(),
            min(posicion_y, area.bottom() - self.height() + 1),
        )  # Hace lo mismo verticalmente.

        self.move(posicion_x, posicion_y)  # Coloca finalmente la ventana en la posición segura calculada.

    def showEvent(self, evento) -> None:
        super().showEvent(evento)  # Permite que Qt termine primero de preparar la ventana.
        self._centrar_en_area_disponible()  # Centra la ventana cuando sus dimensiones reales ya son conocidas.