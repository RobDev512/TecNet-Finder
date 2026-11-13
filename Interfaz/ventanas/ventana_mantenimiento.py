# ============================================================
# Archivo: ventana_mantenimiento.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Presenta el Centro de estabilidad y mantenimiento de v1.2.2.
#
# Consulta la versión en desarrollo, los registros de ejecución
# y la carpeta donde se almacenan. Adapta automáticamente su
# idioma y apariencia a las preferencias actuales del usuario.
#
# No modifica las fases internas del compilador.
# ============================================================

import re  # Reconoce el formato estructurado de los registros de ejecución.

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt, QTimer, QUrl  # Proporciona animación, eventos y rutas locales.
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPalette, QPixmap  # Gestiona iconos y colores de los controles.
from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget  # Construye controles y tabla de registros.

from Interfaz.ventanas.marco_dialogo import preparar_dialogo_con_barra  # Integra la misma barra oficial utilizada por Diagnósticos.
from Interfaz.apariencia.recursos_tema import ruta_marca  # Localiza los logotipos oficiales.
from Motor.configuracion.catalogo_temas import obtener_tema  # Recupera los colores de la variante visual activa.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Consulta el idioma confirmado del usuario.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Consulta el tema visual confirmado.
from Motor.configuracion.version_aplicacion import NOMBRE_ACTUALIZACION, NOMBRE_APLICACION, URL_REPOSITORIO, VERSION_ESTABLE, VERSION_VISIBLE  # Reutiliza los metadatos oficiales centralizados.
from Motor.infraestructura.registro import obtener_ruta_log  # Recupera la ubicación del registro de eventos.
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones  # Traduce los textos mediante Recursos/Idiomas.


PATRON_REGISTRO = re.compile(r"^(?P<fecha>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(?P<nivel>[A-Z]+)\s*\|\s*(?P<origen>.*?)\s*\|\s*(?P<mensaje>.*)$")  # Reconoce las cuatro columnas generadas por registro.py.


class DesplazamientoSuave(QObject):  # Anima la rueda del mouse sin interferir con el desplazamiento táctil o manual.

    def __init__(self, area):  # Prepara una animación vertical para una tabla o área desplazable.
        super().__init__(area)  # Vincula su duración con el widget desplazable.
        self.area = area  # Conserva la referencia al control que recibe la rueda.
        self.animacion = QPropertyAnimation(area.verticalScrollBar(), b"value", self)  # Anima el desplazamiento real del contenido.
        self.animacion.setDuration(185)  # Utiliza una transición corta y perceptible.
        self.animacion.setEasingCurve(QEasingCurve.Type.OutCubic)  # Evita el salto brusco de la rueda tradicional.
        self.objetivo = 0  # Acumula movimientos consecutivos sin perder desplazamiento.
        area.viewport().installEventFilter(self)  # Intercepta solo la rueda sobre el contenido.

    def eventFilter(self, objeto, evento):  # Conserva el comportamiento nativo de touchpads y teclas modificadoras.
        if objeto is self.area.viewport() and evento.type() == QEvent.Type.Wheel:
            if evento.modifiers() or not evento.pixelDelta().isNull(): return super().eventFilter(objeto, evento)  # Respeta zoom, Shift y desplazamiento preciso.
            pasos = evento.angleDelta().y() / 120  # Convierte la rueda convencional en pasos independientes de la plataforma.
            barra = self.area.verticalScrollBar()  # Obtiene el desplazamiento actual.
            if not pasos or barra.maximum() <= barra.minimum(): return super().eventFilter(objeto, evento)  # No bloquea áreas sin desplazamiento.
            if self.animacion.state() != QAbstractAnimation.State.Running: self.objetivo = barra.value()  # Reinicia el objetivo al terminar la animación anterior.
            avance = max(75, min(130, barra.singleStep() * 3))  # Avanza una distancia estable aun con tamaños variables de fila.
            self.objetivo = max(barra.minimum(), min(barra.maximum(), round(self.objetivo - pasos * avance)))  # Mantiene los límites válidos.
            self.animacion.stop()  # Interrumpe de forma segura la transición previa.
            self.animacion.setStartValue(barra.value())  # Continúa suavemente desde la posición realmente visible.
            self.animacion.setEndValue(self.objetivo)  # Desplaza el contenido hasta la nueva posición.
            self.animacion.start()  # Inicia la transición sin bloquear la interfaz.
            evento.accept()  # Impide que Qt ejecute otro salto encima de la animación.
            return True  # Informa que la rueda fue atendida.
        return super().eventFilter(objeto, evento)  # Conserva los demás eventos de Qt.


class VentanaMantenimiento(QDialog):  # Presenta información de estabilidad sin modificar el compilador.

    def __init__(self, padre=None):  # Construye el diálogo con el idioma y tema guardados.
        super().__init__(padre)  # Conserva la ventana principal como propietaria.
        self.traducciones = GestorTraducciones(PreferenciasAplicacion().idioma_interfaz())  # Recupera el idioma actualmente seleccionado.
        self.colores = obtener_tema(PreferenciasTema().tema())  # Consulta la paleta del tema confirmado.
        self.registros = []  # Conserva los eventos interpretados para poder filtrar sin releer el archivo.
        self.setObjectName("VentanaMantenimiento")  # Permite aplicar exclusivamente sus estilos.
        self.setWindowTitle(self._t("mantenimiento.titulo"))  # Traduce también el título de Windows.
        self.setMinimumSize(700, 480)  # Conserva una distribución utilizable en pantallas pequeñas.
        self.resize(830, 570)  # Utiliza un tamaño cómodo para el visor de eventos.

        ruta_icono = ruta_marca("LogoTNF.ico")  # Localiza el icono oficial.
        if ruta_icono.is_file(): self.setWindowIcon(QIcon(str(ruta_icono)))  # Lo aplica solo si existe.

        self._construir_interfaz()  # Crea las tarjetas, pestañas y botones.
        self._aplicar_estilos()  # Utiliza la paleta real de la interfaz.
        self.actualizar_registros()  # Presenta los eventos generados al arrancar.

    def showEvent(self, evento) -> None:  # Espera a que el gestor de apariencia termine la preparación inicial de Qt.
        super().showEvent(evento)  # Conserva el comportamiento habitual de aparición.
        QTimer.singleShot(0, self._finalizar_apertura)  # Programa una corrección visual sin bloquear la ventana.

    def _finalizar_apertura(self) -> None:  # Conserva la reaplicación temática anterior y estabiliza la tabla.
        self._aplicar_estilos()  # Mantiene los colores correctos después del gestor global de temas.
        QTimer.singleShot(0, self._ajustar_tabla_inicial)  # Recalcula la geometría después del cambio de estilos.

    def _ajustar_tabla_inicial(self) -> None:  # Repinta encabezados y contenido después de que finaliza el primer layout.
        self.tabla_registros.horizontalHeader().viewport().update()  # Redibuja los encabezados completos.
        self.tabla_registros.viewport().update()  # Actualiza las filas sin requerir mover la ventana.
        self.tabla_registros.updateGeometry()  # Comunica a Qt que la geometría ya está estabilizada.

    def _t(self, clave: str, **variables) -> str:  # Centraliza los textos traducibles de esta ventana.
        return self.traducciones.traducir(clave, **variables)  # Conserva el respaldo español del proyecto.

    # ========================================================
    # Construcción de la interfaz
    # ========================================================

    def _construir_interfaz(self) -> None:  # Organiza un encabezado y dos áreas de mantenimiento.
        diseno = preparar_dialogo_con_barra(self, self.windowTitle(), margenes=(18, 18, 18, 18))  # Coloca la barra superior oficial antes del contenido.
        diseno.setContentsMargins(18, 18, 18, 18)  # Conserva márgenes proporcionados.
        diseno.setSpacing(12)  # Separa los bloques visuales.

        cabecera = QFrame()  # Destaca la identidad del Centro de mantenimiento.
        cabecera.setObjectName("MantenimientoCabecera")  # Identifica su superficie visual.
        fila_cabecera = QHBoxLayout(cabecera)  # Organiza logotipo, título y versión.
        fila_cabecera.setContentsMargins(16, 14, 16, 14)  # Conserva espacio interior.

        ruta_logo = ruta_marca("LogoTNF.png")  # Consulta la imagen principal de TecNet Finder.
        if ruta_logo.is_file():  # Evita depender de que exista el recurso.
            logo = QLabel()  # Reserva un espacio para el emblema.
            logo.setPixmap(QPixmap(str(ruta_logo)).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))  # Escala sin distorsionar.
            fila_cabecera.addWidget(logo)  # Coloca el emblema a la izquierda.

        textos_cabecera = QVBoxLayout()  # Agrupa título y descripción.
        titulo = QLabel(self._t("mantenimiento.titulo"))  # Muestra el nombre traducido.
        titulo.setObjectName("MantenimientoTitulo")  # Utiliza tipografía destacada.
        subtitulo = QLabel(self._t("mantenimiento.subtitulo"))  # Explica el propósito de la herramienta.
        subtitulo.setObjectName("MantenimientoTextoSecundario")  # Mantiene una jerarquía visual discreta.
        subtitulo.setWordWrap(True)  # Evita recortes cuando el texto traducido es largo.
        textos_cabecera.addWidget(titulo)  # Añade el encabezado.
        textos_cabecera.addWidget(subtitulo)  # Añade la explicación.
        fila_cabecera.addLayout(textos_cabecera, 1)  # Reserva la mayor parte del ancho al texto.

        insignia = QLabel(VERSION_VISIBLE)  # Identifica la actualización sin depender del idioma.
        insignia.setObjectName("MantenimientoInsignia")  # Aplica apariencia de etiqueta.
        fila_cabecera.addWidget(insignia)  # Sitúa la versión a la derecha.
        diseno.addWidget(cabecera)  # Inserta el encabezado en la ventana.

        pestanas = QTabWidget()  # Separa la información de los registros.
        pestanas.setObjectName("MantenimientoPestanas")  # Permite tematizar únicamente este control.
        pestanas.currentChanged.connect(lambda _indice: QTimer.singleShot(0, self._ajustar_tabla_inicial))  # Corrige la primera distribución al cambiar de pestaña.
        pestanas.addTab(self._construir_informacion(), self._t("mantenimiento.pestana.informacion"))  # Crea la primera pestaña.
        pestanas.addTab(self._construir_registros(), self._t("mantenimiento.pestana.registros"))  # Crea la segunda pestaña.
        diseno.addWidget(pestanas, 1)  # Entrega el espacio restante a las pestañas.

        acciones = QHBoxLayout()  # Separa el cierre del contenido.
        acciones.addStretch()  # Alinea el botón a la derecha.
        boton_cerrar = QPushButton(self._t("mantenimiento.cerrar"))  # Crea la acción de salida.
        boton_cerrar.setObjectName("MantenimientoCerrar")  # Utiliza el acento del tema actual.
        boton_cerrar.clicked.connect(self.accept)  # Cierra únicamente este diálogo.
        acciones.addWidget(boton_cerrar)  # Inserta el botón en la fila.
        diseno.addLayout(acciones)  # Completa el pie de la ventana.

    def _crear_tarjeta(self, titulo: str, valor: str, descripcion: str, estado: bool = False) -> QFrame:  # Reutiliza una tarjeta de información.
        tarjeta = QFrame()  # Construye una superficie individual.
        tarjeta.setObjectName("MantenimientoTarjeta")  # Aplica borde y fondo del tema.
        diseno = QVBoxLayout(tarjeta)  # Organiza contenido en columna.
        diseno.setContentsMargins(17, 15, 17, 15)  # Mantiene espacio interior uniforme.
        diseno.setSpacing(8)  # Separa los tres niveles de información.

        etiqueta_titulo = QLabel(titulo)  # Presenta el tipo de dato.
        etiqueta_titulo.setObjectName("MantenimientoTextoSecundario")  # Utiliza una jerarquía secundaria.
        etiqueta_valor = QLabel(valor)  # Destaca el valor principal.
        etiqueta_valor.setObjectName("MantenimientoValorEstado" if estado else "MantenimientoValor")  # Distingue el estado positivo.
        etiqueta_valor.setWordWrap(True)  # Admite traducciones extensas.
        etiqueta_descripcion = QLabel(descripcion)  # Complementa el dato destacado.
        etiqueta_descripcion.setObjectName("MantenimientoTextoSecundario")  # Conserva una apariencia discreta.
        etiqueta_descripcion.setWordWrap(True)  # Evita cortar la explicación.

        diseno.addWidget(etiqueta_titulo)  # Inserta el encabezado.
        diseno.addWidget(etiqueta_valor)  # Inserta el dato destacado.
        diseno.addWidget(etiqueta_descripcion)  # Inserta la explicación.
        diseno.addStretch()  # Mantiene el contenido alineado arriba.
        return tarjeta  # Entrega un componente reutilizable.

    def _construir_informacion(self) -> QWidget:  # Fusiona Información y Acerca de dentro de una sola pestaña.
        pagina = QFrame()  # Proporciona una superficie real con las cuatro esquinas redondeadas.
        pagina.setObjectName("MantenimientoPagina")  # Reutiliza el mismo contenedor de Registros.
        pagina.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Obliga a Qt a dibujar el contorno redondeado.
        diseno_pagina = QVBoxLayout(pagina)  # Separa el área desplazable de las esquinas.
        diseno_pagina.setContentsMargins(10, 10, 10, 10)  # Impide que el scroll tape los bordes curvos.
        self.area_informacion = QScrollArea()  # Conserva la navegación cuando el contenido es largo.
        self.area_informacion.setObjectName("MantenimientoInfoScroll")  # Identifica el área desplazable para aplicar el tema.
        self.area_informacion.setWidgetResizable(True)  # Adapta el contenido al ancho disponible.
        self.area_informacion.setFrameShape(QFrame.Shape.NoFrame)  # Evita el borde rectangular nativo.
        self.area_informacion.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Evita la barra horizontal.
        self.area_informacion.viewport().setAutoFillBackground(False)  # Mantiene visible el panel en las esquinas.
        diseno_pagina.addWidget(self.area_informacion)  # Coloca el scroll dentro del marco redondeado.

        contenido = QWidget()  # Agrupa toda la información en un único panel.
        contenido.setObjectName("MantenimientoInfoContenido")  # Identifica el fondo interno de la pestaña.
        diseno = QVBoxLayout(contenido)  # Organiza tarjetas y datos del proyecto verticalmente.
        diseno.setContentsMargins(14, 16, 14, 16)  # Conserva los márgenes de la pestaña Registros.
        diseno.setSpacing(12)  # Separa cada grupo de información.

        estado = self._crear_tarjeta(self._t("mantenimiento.estado.titulo"), self._t("mantenimiento.estado.valor"), self._t("mantenimiento.estado.descripcion"), estado=True)  # Conserva el resumen del registro de eventos.
        diseno.addWidget(estado)  # Presenta primero el estado del sistema.

        fila_datos = QHBoxLayout()  # Agrupa las dos tarjetas de versión.
        fila_datos.setSpacing(12)  # Mantiene una separación uniforme.
        fila_datos.addWidget(self._crear_tarjeta(self._t("mantenimiento.version.titulo"), VERSION_VISIBLE, NOMBRE_APLICACION), 1)  # Muestra la versión en desarrollo.
        fila_datos.addWidget(self._crear_tarjeta(self._t("mantenimiento.actualizacion.titulo"), NOMBRE_ACTUALIZACION, self._t("mantenimiento.actualizacion.descripcion")), 1)  # Presenta el objetivo del release.
        diseno.addLayout(fila_datos)  # Inserta ambas tarjetas.

        acerca = QFrame()  # Reúne todos los detalles antes alojados en el diálogo Acerca de.
        acerca.setObjectName("MantenimientoTarjeta")  # Reutiliza los bordes y colores del Centro de mantenimiento.
        datos = QVBoxLayout(acerca)  # Organiza la presentación y sus acciones.
        datos.setContentsMargins(17, 15, 17, 15)  # Conserva el espacio interior de las tarjetas.
        datos.setSpacing(10)  # Separa el texto y cada dato técnico.

        titulo = QLabel(self._t("acerca.titulo"))  # Muestra el encabezado traducido del proyecto.
        titulo.setObjectName("MantenimientoSubtitulo")  # Destaca el apartado de información general.
        datos.addWidget(titulo)  # Inserta el encabezado directamente en Información.

        descripcion = QLabel(self._t("acerca.descripcion"))  # Explica la finalidad del compilador.
        descripcion.setObjectName("MantenimientoTextoSecundario")  # Presenta una descripción discreta y legible.
        descripcion.setWordWrap(True)  # Admite traducciones de distinta longitud.
        datos.addWidget(descripcion)  # Añade el contexto del proyecto.

        self._agregar_dato_informacion(datos, self._t("acerca.version_estable"), f"v{VERSION_ESTABLE}")  # Identifica la última versión publicada.
        self._agregar_dato_informacion(datos, self._t("acerca.materia"), "Lenguajes y Autómatas II")  # Conserva el contexto académico.
        self._agregar_dato_informacion(datos, self._t("acerca.tecnologias"), "Python · PySide6 · VLSM · Ollama")  # Enumera las tecnologías principales.

        acciones = QHBoxLayout()  # Coloca las funciones informativas en una misma fila.
        boton_repositorio = QPushButton(self._t("acerca.abrir_repositorio"))  # Abre el repositorio público para consulta.
        boton_repositorio.clicked.connect(self._abrir_repositorio)  # Utiliza el enlace centralizado del proyecto.
        acciones.addWidget(boton_repositorio)  # Inserta el acceso a GitHub.
        boton_copiar = QPushButton(self._t("acerca.copiar_version"))  # Permite copiar la identificación de esta versión.
        boton_copiar.clicked.connect(self._copiar_version)  # Envía los metadatos al portapapeles.
        acciones.addWidget(boton_copiar)  # Inserta la segunda acción.
        acciones.addStretch()  # Mantiene ambas acciones alineadas a la izquierda.
        datos.addLayout(acciones)  # Completa el panel informativo.

        diseno.addWidget(acerca)  # Añade los detalles del producto a la pestaña Información.
        diseno.addStretch()  # Mantiene el contenido agrupado en la parte superior.
        self.area_informacion.setWidget(contenido)  # Activa el desplazamiento únicamente cuando se necesite.
        self.desplazamiento_informacion = DesplazamientoSuave(self.area_informacion)  # Suaviza la rueda tradicional dentro de Información.
        return pagina  # Entrega la pestaña completa sin abrir ventanas adicionales.

    def _agregar_dato_informacion(self, diseno: QVBoxLayout, etiqueta: str, valor: str) -> None:  # Presenta una fila informativa reutilizable.
        fila = QHBoxLayout()  # Separa etiqueta y contenido.
        nombre = QLabel(etiqueta)  # Identifica el campo correspondiente.
        nombre.setObjectName("MantenimientoTextoSecundario")  # Reutiliza la tipografía secundaria.
        nombre.setMinimumWidth(160)  # Conserva una alineación consistente entre filas.
        valor_etiqueta = QLabel(valor)  # Muestra el dato real del proyecto.
        valor_etiqueta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite copiar el texto manualmente.
        valor_etiqueta.setWordWrap(True)  # Evita recortes en ventanas estrechas.
        fila.addWidget(nombre)  # Inserta el nombre del campo.
        fila.addWidget(valor_etiqueta, 1)  # Reserva el espacio flexible al valor.
        diseno.addLayout(fila)  # Coloca la fila en la tarjeta Acerca de.

    def _construir_registros(self) -> QWidget:  # Presenta un evento por fila y permite filtrar los registros.
        pagina = QFrame()  # Proporciona el mismo contenedor redondeado utilizado en Información.
        pagina.setObjectName("MantenimientoPagina")  # Dibuja las cuatro esquinas con la paleta activa.
        pagina.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Evita que el viewport tape el marco.
        diseno = QVBoxLayout(pagina)  # Organiza encabezado, filtros, tabla y acciones.
        diseno.setContentsMargins(14, 16, 14, 16)  # Mantiene los márgenes del resto de la ventana.
        diseno.setSpacing(11)  # Separa los controles de manera uniforme.

        titulo = QLabel(self._t("mantenimiento.registros.titulo"))  # Identifica el historial de eventos.
        titulo.setObjectName("MantenimientoSubtitulo")  # Aplica el estilo de subtítulo.
        descripcion = QLabel(self._t("mantenimiento.registros.descripcion"))  # Explica el contenido de la tabla.
        descripcion.setObjectName("MantenimientoTextoSecundario")  # Mantiene un texto explicativo discreto.
        descripcion.setWordWrap(True)  # Admite textos extensos en cualquiera de los seis idiomas.
        diseno.addWidget(titulo)  # Coloca el encabezado.
        diseno.addWidget(descripcion)  # Coloca la explicación.

        self.etiqueta_ruta = QLabel()  # Muestra la ubicación del archivo de registro activo.
        self.etiqueta_ruta.setObjectName("MantenimientoRuta")  # Utiliza el formato de ruta destacado.
        self.etiqueta_ruta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite seleccionar la ruta.
        self.etiqueta_ruta.setWordWrap(True)  # Muestra rutas de Windows extensas.
        diseno.addWidget(self.etiqueta_ruta)  # Inserta el bloque de ubicación.

        filtros = QHBoxLayout()  # Organiza el buscador y el selector de severidad.
        self.buscador_registros = QLineEdit()  # Permite localizar textos dentro de cualquier columna.
        self.buscador_registros.setObjectName("MantenimientoBuscar")  # Identifica el campo en el estilo visual.
        self.buscador_registros.setPlaceholderText(self._t("mantenimiento.registros.buscar"))  # Traduce la indicación de búsqueda.
        self.buscador_registros.textChanged.connect(self._filtrar_registros)  # Filtra sin alterar el archivo de logs.
        filtros.addWidget(self.buscador_registros, 1)  # Da prioridad de espacio al buscador.

        marco_nivel = QFrame()  # Dibuja un borde uniforme alrededor de todo el selector, incluida su flecha.
        marco_nivel.setObjectName("MantenimientoMarcoNivel")  # Unifica el redondeado de ambos extremos.
        marco_nivel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza que Qt dibuje las esquinas.
        diseno_nivel = QHBoxLayout(marco_nivel)  # Aloja el selector sin que cubra el borde curvo.
        diseno_nivel.setContentsMargins(1, 1, 1, 1)  # Deja visible el contorno exterior.
        self.selector_nivel = QComboBox()  # Permite visualizar un nivel de registro específico.
        self.selector_nivel.setObjectName("MantenimientoNivel")  # Mantiene el nombre utilizado por los temas.
        self.selector_nivel.setMinimumWidth(152)  # Evita que el texto y la flecha se recorten.
        self.selector_nivel.addItem(self._t("mantenimiento.registros.todos_niveles"), "")  # Incluye inicialmente todos los niveles.
        self.selector_nivel.currentIndexChanged.connect(self._filtrar_registros)  # Vuelve a mostrar solamente los niveles seleccionados.
        diseno_nivel.addWidget(self.selector_nivel)  # Mantiene fondo y flecha dentro del marco redondeado.
        filtros.addWidget(marco_nivel)  # Inserta el selector a la derecha del buscador.
        diseno.addLayout(filtros)  # Coloca los filtros antes de la tabla.

        self.tabla_registros = QTableWidget(0, 4)  # Divide cada evento en cuatro columnas estructuradas.
        self.tabla_registros.setObjectName("MantenimientoTabla")  # Limita los estilos únicamente al visor de eventos.
        self.tabla_registros.setHorizontalHeaderLabels([self._t("mantenimiento.registros.fecha"), self._t("mantenimiento.registros.nivel"), self._t("mantenimiento.registros.origen"), self._t("mantenimiento.registros.mensaje")])  # Traduce cada encabezado.
        self.tabla_registros.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide editar los registros originales.
        self.tabla_registros.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Permite seleccionar eventos completos.
        self.tabla_registros.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Conserva una selección sencilla.
        self.tabla_registros.setShowGrid(False)  # Evita divisiones visuales innecesarias.
        self.tabla_registros.setAlternatingRowColors(True)  # Alterna según la posición visual, incluso después de ordenar y filtrar.
        self.tabla_registros.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Permite movimiento de contenido pixel a pixel.
        self.tabla_registros.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)  # Mantiene también el desplazamiento horizontal gradual.
        self.tabla_registros.setWordWrap(False)  # Mantiene filas compactas incluso si existe un traceback.
        self.tabla_registros.verticalHeader().hide()  # Oculta números de fila redundantes.
        self.tabla_registros.verticalHeader().setDefaultSectionSize(34)  # Mantiene un alto consistente por evento.
        encabezado = self.tabla_registros.horizontalHeader()  # Recupera los encabezados de columna.
        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Evita cambios de anchura durante la primera aparición.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Mantiene estable la columna del nivel.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Permite ampliar manualmente el nombre del componente.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Utiliza todo el espacio restante para el mensaje.
        encabezado.resizeSection(0, 160)  # Reserva suficiente espacio para fecha y hora.
        encabezado.resizeSection(1, 88)  # Evita recortes de WARNING y CRITICAL.
        encabezado.resizeSection(2, 125)  # Equilibra el ancho del origen y del mensaje.
        self.tabla_registros.itemSelectionChanged.connect(self._actualizar_copia_evento)  # Activa copiar cuando existe una fila seleccionada.
        marco_tabla = QFrame()  # Aísla la tabla y sus encabezados dentro de un contenedor con esquinas reales.
        marco_tabla.setObjectName("MantenimientoMarcoTabla")  # Reutiliza el borde redondeado de las demás tarjetas.
        marco_tabla.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Garantiza el pintado completo del contorno.
        diseno_tabla = QVBoxLayout(marco_tabla)  # Evita superponer el encabezado cuadrado sobre las esquinas.
        diseno_tabla.setContentsMargins(7, 7, 7, 7)  # Mantiene separado el viewport de los cuatro bordes curvos.
        diseno_tabla.setSpacing(0)  # Impide huecos dentro del visor.
        diseno_tabla.addWidget(self.tabla_registros)  # Coloca el contenido editable solamente en lectura.
        diseno.addWidget(marco_tabla, 1)  # La tabla ocupa el espacio flexible disponible.
        self.desplazamiento_tabla = DesplazamientoSuave(self.tabla_registros)  # Suaviza la rueda del mouse sin cambiar la selección.

        fila_acciones = QHBoxLayout()  # Agrupa contador y herramientas del registro.
        self.etiqueta_cantidad = QLabel("")  # Informa cuántos eventos coinciden con los filtros.
        self.etiqueta_cantidad.setObjectName("MantenimientoTextoSecundario")  # Mantiene un estilo secundario.
        fila_acciones.addWidget(self.etiqueta_cantidad)  # Coloca el contador a la izquierda.
        fila_acciones.addStretch()  # Separa contador y botones.

        self.boton_copiar_evento = QPushButton(self._t("mantenimiento.registros.copiar_evento"))  # Copia el evento completo, incluido un posible traceback.
        self.boton_copiar_evento.setEnabled(False)  # Permite copiar solamente después de seleccionar un evento.
        self.boton_copiar_evento.clicked.connect(self._copiar_evento)  # Envía el evento seleccionado al portapapeles.
        fila_acciones.addWidget(self.boton_copiar_evento)  # Inserta el acceso a la copia.

        for clave, accion in (("mantenimiento.registros.actualizar", self.actualizar_registros), ("mantenimiento.registros.copiar", self.copiar_ruta), ("mantenimiento.registros.abrir", self.abrir_carpeta)):
            boton = QPushButton(self._t(clave))  # Crea una acción con su traducción vigente.
            boton.clicked.connect(accion)  # Vincula el comportamiento correspondiente.
            fila_acciones.addWidget(boton)  # Mantiene las herramientas en una misma fila.

        diseno.addLayout(fila_acciones)  # Completa el panel de registros.
        return pagina  # Devuelve la segunda pestaña.

    # ========================================================
    # Acciones de información general
    # ========================================================

    def _abrir_repositorio(self) -> None:  # Abre GitHub sin realizar modificaciones al proyecto.
        QDesktopServices.openUrl(QUrl(URL_REPOSITORIO))  # Utiliza el navegador predeterminado del usuario.

    def _copiar_version(self) -> None:  # Copia la versión y denominación oficial de la actualización.
        QApplication.clipboard().setText(f"{NOMBRE_APLICACION} {VERSION_VISIBLE} — {NOMBRE_ACTUALIZACION}")  # Reutiliza la información centralizada.

    # ========================================================
    # Apariencia y operaciones de mantenimiento
    # ========================================================

    def _aplicar_estilos(self) -> None:  # Aplica la paleta activa a tarjetas, filtros y a cada celda de la tabla.
        c = self.colores  # Abrevia el catálogo de colores del tema elegido.
        self.setStyleSheet(f"""
            QDialog#VentanaMantenimiento {{ background-color: transparent; }}
            QLabel {{ background: transparent; color: {c["texto"]}; }}
            QFrame#MantenimientoCabecera, QFrame#MantenimientoTarjeta {{ background-color: {c["panel"]}; border: 1px solid {c["borde"]}; border-radius: 11px; }}
            QLabel#MantenimientoTitulo {{ font-size: 19px; font-weight: bold; color: {c["texto"]}; }}
            QLabel#MantenimientoSubtitulo {{ font-size: 15px; font-weight: bold; color: {c["texto"]}; }}
            QLabel#MantenimientoTextoSecundario {{ color: {c["texto_secundario"]}; }}
            QLabel#MantenimientoValor {{ font-size: 19px; font-weight: bold; color: {c["acento"]}; }}
            QLabel#MantenimientoValorEstado {{ font-size: 19px; font-weight: bold; color: {c["exito"]}; }}
            QLabel#MantenimientoInsignia {{ background-color: {c["superficie"]}; color: {c["acento"]}; border: 1px solid {c["borde_fuerte"]}; border-radius: 8px; padding: 7px 10px; font-weight: bold; }}
            QLabel#MantenimientoRuta {{ background-color: {c["superficie"]}; border: 1px solid {c["borde"]}; border-radius: 7px; padding: 10px; color: {c["texto"]}; }}
            QTabWidget#MantenimientoPestanas::pane {{ background: transparent; border: none; }}
            QFrame#MantenimientoPagina {{ background-color: {c["panel"]}; border: 1px solid {c["borde_fuerte"]}; border-radius: 12px; }}
            QScrollArea#MantenimientoInfoScroll, QWidget#MantenimientoInfoContenido {{ background: transparent; border: none; }}
            QScrollArea#MantenimientoInfoScroll > QWidget {{ background: transparent; border: none; }}
            QTabBar::tab {{ background-color: {c["superficie"]}; color: {c["texto"]}; border: 1px solid {c["borde"]}; padding: 9px 19px; min-width: 100px; }}
            QTabBar::tab:selected {{ background-color: {c["panel"]}; border-bottom: 2px solid {c["acento"]}; font-weight: bold; }}
            QTabBar::tab:hover {{ background-color: {c["superficie_hover"]}; }}
            QLineEdit#MantenimientoBuscar {{ background-color: {c["editor"]}; color: {c["texto"]}; border: 1px solid {c["borde_fuerte"]}; border-radius: 8px; padding: 7px 10px; }}
            QLineEdit#MantenimientoBuscar:focus {{ border-color: {c["acento"]}; }}
            QFrame#MantenimientoMarcoNivel {{ background-color: {c["editor"]}; border: 1px solid {c["borde_fuerte"]}; border-radius: 8px; }}
            QComboBox#MantenimientoNivel {{ background: transparent; color: {c["texto"]}; border: none; border-radius: 7px; padding: 7px 9px; }}
            QComboBox#MantenimientoNivel::drop-down {{ background: transparent; border: none; border-top-right-radius: 7px; border-bottom-right-radius: 7px; width: 25px; }}
            QComboBox#MantenimientoNivel QAbstractItemView {{ background-color: {c["panel"]}; color: {c["texto"]}; selection-background-color: {c["superficie_hover"]}; selection-color: {c["texto"]}; }}
            QFrame#MantenimientoMarcoTabla {{ background-color: {c["editor"]}; border: 1px solid {c["borde_fuerte"]}; border-radius: 11px; }}
            QTableWidget#MantenimientoTabla {{ background-color: {c["editor"]}; color: {c["texto"]}; alternate-background-color: {c["panel"]}; border: none; border-radius: 4px; selection-background-color: {c["superficie_hover"]}; selection-color: {c["texto"]}; }}
            QTableWidget#MantenimientoTabla::item {{ padding: 4px 7px; }}
            QTableWidget#MantenimientoTabla::item:selected {{ background-color: {c["superficie_hover"]}; color: {c["texto"]}; }}
            QHeaderView::section {{ background-color: {c["superficie"]}; color: {c["texto"]}; border: none; border-bottom: 1px solid {c["borde_fuerte"]}; padding: 8px; font-weight: bold; }}
            QWidget#CuerpoDialogoTecNet QPushButton {{ background-color: {c["superficie"]}; color: {c["texto"]}; border: 1px solid {c["borde_fuerte"]}; border-radius: 7px; padding: 9px 12px; font-weight: bold; }}
            QWidget#CuerpoDialogoTecNet QPushButton:hover {{ background-color: {c["superficie_hover"]}; border-color: {c["acento"]}; }}
            QWidget#CuerpoDialogoTecNet QPushButton:pressed {{ background-color: {c["superficie_presionada"]}; }}
            QWidget#CuerpoDialogoTecNet QPushButton:disabled {{ color: {c["texto_deshabilitado"]}; border-color: {c["borde"]}; }}
            QPushButton#MantenimientoCerrar {{ background-color: {c["acento"]}; color: {c["texto_inverso"]}; border-color: {c["acento"]}; min-width: 95px; }}
            QPushButton#MantenimientoCerrar:hover {{ background-color: {c["acento_hover"]}; color: {c["texto_inverso"]}; }}
        """)  # Evita colores fijos y mantiene todos los temas compatibles.

        paleta = self.tabla_registros.palette()  # Recupera la paleta real del visor estructurado.
        paleta.setColor(QPalette.ColorRole.Base, QColor(c["editor"]))  # Impone un fondo claro en temas claros y oscuro en los demás.
        paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(c["panel"]))  # Mantiene una variante legible en filas alternas.
        paleta.setColor(QPalette.ColorRole.Text, QColor(c["texto"]))  # Evita letras oscuras sobre fondos oscuros.
        paleta.setColor(QPalette.ColorRole.Highlight, QColor(c["superficie_hover"]))  # Resalta filas seleccionadas sin perder contraste.
        paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(c["texto"]))  # Conserva texto visible al seleccionar.
        self.tabla_registros.setPalette(paleta)  # Aplica la paleta al propio QTableWidget.

        for fila in range(self.tabla_registros.rowCount()):  # Refuerza los colores de las filas ya cargadas.
            for columna in range(self.tabla_registros.columnCount()):  # Recorre todas las celdas visibles.
                item = self.tabla_registros.item(fila, columna)  # Recupera la celda correspondiente.
                if item is not None: self._establecer_colores_item(item, fila, columna)  # Evita que el tema global oculte los datos.

    def _establecer_colores_item(self, item: QTableWidgetItem, fila: int, columna: int) -> None:  # Define un contraste explícito por celda.
        c = self.colores  # Recupera los colores vigentes.
        nivel = self.tabla_registros.item(fila, 1) if columna == 1 else None  # Consulta el nivel solamente cuando corresponde.
        color = c["texto"]  # Utiliza el color de lectura general como respaldo.
        if nivel is not None:  # Distingue niveles con la paleta semántica existente.
            nombre = nivel.text().upper()  # Normaliza el identificador del nivel.
            if nombre in ("ERROR", "CRITICAL"): color = c["error"]  # Destaca fallos.
            elif nombre == "WARNING": color = c["advertencia"]  # Destaca advertencias.
            elif nombre == "INFO": color = c["exito"]  # Destaca mensajes informativos.
            elif nombre == "DEBUG": color = c["acento"]  # Distingue la depuración.
        item.setForeground(QColor(color))  # Fuerza texto visible incluso cuando el estilo global cambia.
        # Los fondos no se guardan en cada item: QTableWidget alterna por fila visible incluso después de ordenar.

    def actualizar_registros(self) -> None:  # Relee el archivo de eventos y reconstruye la tabla.
        ruta = obtener_ruta_log()  # Recupera el archivo utilizado por el sistema de registro.
        if ruta is None or not ruta.is_file():  # Comprueba que el archivo esté disponible.
            self.etiqueta_ruta.setText(self._t("mantenimiento.registros.ruta_vacia"))  # Informa la ausencia de registros.
            self.registros = []  # Limpia cualquier lectura anterior.
            self._actualizar_niveles()  # Restablece las opciones de filtrado.
            self._filtrar_registros()  # Vacía la tabla.
            return  # Evita intentar leer una ruta inexistente.

        self.etiqueta_ruta.setText(str(ruta))  # Presenta la ruta completa para consulta.
        try:  # Evita que un error de lectura cierre la ventana.
            contenido = ruta.read_text(encoding="utf-8", errors="replace")[-250000:]  # Limita la memoria y conserva los eventos más recientes.
            self.registros = self._interpretar_registros(contenido)  # Agrupa las líneas en eventos estructurados.
            self._actualizar_niveles()  # Reconstruye el selector utilizando los niveles realmente encontrados.
            self._filtrar_registros()  # Actualiza filas, colores y contador.
        except OSError as error:  # Maneja archivos bloqueados o inaccesibles.
            self.registros = []  # Evita mostrar eventos desactualizados.
            self._actualizar_niveles()  # Limpia los filtros de severidad.
            self._filtrar_registros()  # Limpia la tabla anterior.
            self.etiqueta_cantidad.setText(self._t("mantenimiento.registros.error_lectura", error=str(error)))  # Comunica la causa del fallo.

    @staticmethod
    def _interpretar_registros(contenido: str) -> list[dict[str, str]]:  # Convierte el archivo plano en filas sin perder los tracebacks.
        eventos = []  # Acumula los eventos en el orden original del registro.
        for linea in contenido.splitlines():  # Analiza cada línea del archivo.
            encontrado = PATRON_REGISTRO.match(linea)  # Detecta el inicio de un evento con cuatro columnas.
            if encontrado:  # Empieza una nueva entrada estructurada.
                eventos.append({clave: encontrado.group(clave).strip() for clave in ("fecha", "nivel", "origen", "mensaje")})  # Conserva fecha, nivel, origen y mensaje.
            elif eventos:  # Las líneas sin cabecera pertenecen al evento anterior, como un traceback.
                eventos[-1]["mensaje"] += "\n" + linea  # Mantiene el contexto completo de excepciones.
            elif linea.strip():  # Conserva contenido no estándar al principio del archivo.
                eventos.append({"fecha": "", "nivel": "—", "origen": "—", "mensaje": linea})  # Evita perder entradas antiguas o incompletas.
        return eventos  # Entrega una fila por evento detectado.

    def _actualizar_niveles(self) -> None:  # Construye las opciones del filtro de acuerdo con el archivo real.
        anterior = self.selector_nivel.currentData()  # Conserva el filtro si sigue disponible.
        niveles = sorted({evento["nivel"] for evento in self.registros if evento["nivel"] not in ("", "—")})  # Obtiene únicamente niveles encontrados.
        self.selector_nivel.blockSignals(True)  # Evita filtrar mientras se reconstruye el selector.
        self.selector_nivel.clear()  # Elimina opciones que ya no aparecen en los logs.
        self.selector_nivel.addItem(self._t("mantenimiento.registros.todos_niveles"), "")  # Permite mostrar todos los niveles.
        for nivel in niveles: self.selector_nivel.addItem(nivel, nivel)  # Conserva los nombres técnicos de logging.
        indice = self.selector_nivel.findData(anterior)  # Recupera una selección válida anterior.
        self.selector_nivel.setCurrentIndex(max(0, indice))  # Restablece el filtro si todavía existe.
        self.selector_nivel.blockSignals(False)  # Permite nuevamente aplicar filtros interactivos.

    def _filtrar_registros(self, *_argumentos) -> None:  # Actualiza la tabla según el texto y nivel seleccionados.
        texto = self.buscador_registros.text().strip().casefold()  # Permite búsqueda sin distinguir mayúsculas.
        nivel = self.selector_nivel.currentData() or ""  # Obtiene el nivel solicitado, o todos por defecto.
        filtrados = [evento for evento in self.registros if (not nivel or evento["nivel"] == nivel) and (not texto or texto in " ".join(evento.values()).casefold())]  # Combina ambos criterios.
        tabla = self.tabla_registros  # Utiliza un alias corto para actualizar los eventos.
        tabla.setSortingEnabled(False)  # Impide que Qt reordene filas durante la inserción.
        tabla.setRowCount(len(filtrados))  # Adapta el número de filas a la cantidad real de eventos.

        for fila, evento in enumerate(filtrados):  # Crea una fila por evento que cumpla los filtros.
            mensaje_completo = evento["mensaje"]  # Conserva también las líneas de traceback.
            mensaje_corto = mensaje_completo.splitlines()[0] if mensaje_completo.splitlines() else ""  # Mantiene compacta la columna de mensajes.
            valores = (evento["fecha"], evento["nivel"], evento["origen"], mensaje_corto)  # Determina el orden de las columnas.
            for columna, valor in enumerate(valores):  # Recorre los cuatro campos estructurados.
                item = QTableWidgetItem(valor)  # Construye una celda de solo lectura.
                if columna == 3: item.setData(Qt.ItemDataRole.UserRole, mensaje_completo)  # Conserva el contenido completo para copiarlo.
                if columna == 3: item.setToolTip(mensaje_completo)  # Permite consultar el mensaje íntegro al pasar el cursor.
                tabla.setItem(fila, columna, item)  # Inserta la celda en su columna.
                self._establecer_colores_item(item, fila, columna)  # Aplica colores explícitos para evitar el problema del modo claro.

        tabla.setSortingEnabled(True)  # Permite ordenar manualmente al pulsar los encabezados.
        self.etiqueta_cantidad.setText(self._t("mantenimiento.registros.eventos", cantidad=len(filtrados)))  # Actualiza el contador visible.
        if not filtrados and self.registros: self.etiqueta_cantidad.setText(self._t("mantenimiento.registros.sin_resultados"))  # Explica una búsqueda sin coincidencias.
        self._actualizar_copia_evento()  # Deshabilita la copia cuando no hay un evento seleccionado.

    def _actualizar_copia_evento(self) -> None:  # Controla la disponibilidad de Copiar evento.
        self.boton_copiar_evento.setEnabled(self.tabla_registros.currentRow() >= 0)  # Solo se habilita cuando existe selección.

    def _copiar_evento(self) -> None:  # Copia el evento seleccionado incluyendo sus líneas adicionales.
        fila = self.tabla_registros.currentRow()  # Obtiene la fila seleccionada, considerando la ordenación vigente.
        if fila < 0: return  # Evita copiar cuando todavía no hay selección.
        campos = [self.tabla_registros.item(fila, columna).text() for columna in range(3)]  # Recupera fecha, nivel y origen.
        mensaje = self.tabla_registros.item(fila, 3).data(Qt.ItemDataRole.UserRole)  # Recupera el texto completo y sus tracebacks.
        QApplication.clipboard().setText(" | ".join(campos + [mensaje or ""]))  # Envía el evento íntegro al portapapeles.

    def copiar_ruta(self) -> None:  # Copia la ubicación actual del registro al portapapeles.
        ruta = obtener_ruta_log()  # Recupera el destino real.
        if ruta is not None: QApplication.clipboard().setText(str(ruta))  # Copia la ubicación únicamente cuando existe.

    def abrir_carpeta(self) -> None:  # Abre la carpeta de registros en el explorador del sistema.
        ruta = obtener_ruta_log()  # Recupera la ubicación del archivo principal.
        if ruta is None:  # Evita intentar abrir una ruta desconocida.
            QMessageBox.warning(self, self._t("mantenimiento.titulo"), self._t("mantenimiento.registros.ruta_vacia"))  # Explica el problema.
            return  # Mantiene intacta la ventana.

        correcto = QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta.parent)))  # Abre la carpeta que contiene el archivo.
        if not correcto: QMessageBox.warning(self, self._t("mantenimiento.titulo"), self._t("mantenimiento.registros.error_abrir"))  # Informa si Windows rechazó la operación.
