# ============================================================
# Archivo: panel_configuracion_editor.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene la categoría Editor de Configuración.
#
# Permite modificar:
#
# - Ajuste automático de líneas.
# - Visibilidad de Ampliar y Ejemplos.
# - Familia de fuente.
# - Tamaño de fuente.
# - Ancho visual de tabulación.
#
# La selección de fuente utiliza un control especializado con
# búsqueda para facilitar la localización entre muchas familias.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Permite configurar las casillas y notificar cambios pendientes.
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)  # Importa los componentes básicos del panel.

from Interfaz.configuracion.controles_configuracion import (
    CampoNumeroConfiguracion,
    SelectorDesplegableConfiguracion,
)  # Mantiene los controles generales utilizados para números y listas pequeñas.

from Interfaz.configuracion.selector_fuentes import SelectorFuentes  # Proporciona el selector especializado con búsqueda de tipografías.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona límites y valores predeterminados del editor.


class BotonCasillaEditor(QPushButton):
    # ========================================================
    # Constructor
    # ========================================================

    def __init__(self, nombre_accesible: str, padre=None):
        super().__init__(padre)  # Inicializa el botón utilizado como casilla.
        self.setCheckable(True)  # Permite mantener un estado activado o desactivado.
        self.setFixedSize(24, 24)  # Conserva las dimensiones de las demás casillas.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Conserva una descripción para accesibilidad.

        self.setStyleSheet(
            "padding: 0px; "
            "font-family: 'Segoe UI Symbol'; "
            "font-size: 12pt; "
            "font-weight: bold;"
        )  # Centra visualmente la marca de verificación.

        self.toggled.connect(self._actualizar_apariencia)  # Actualiza el estilo cuando cambia el estado.
        self._actualizar_apariencia(False)  # Prepara inicialmente una casilla vacía.

    def _actualizar_apariencia(self, activado: bool) -> None:
        self.setText("✓" if activado else "")  # Muestra la marca únicamente cuando está activa.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Reutiliza los estilos azul y oscuro.
        self.style().unpolish(self)  # Retira la apariencia anterior.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos.
        self.update()  # Redibuja inmediatamente la casilla.


class PanelConfiguracionEditor(QWidget):
    # Informa a VentanaConfiguracion que existe una modificación temporal.
    configuracion_modificada = Signal()

    # ========================================================
    # Constructor
    # ========================================================

    def __init__(self, preferencias_aplicacion, padre=None):
        super().__init__(padre)  # Vincula el panel con Configuración.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva la copia temporal compartida.
        self._construir_interfaz()  # Construye tarjetas y controles.

    # ========================================================
    # Construcción visual
    # ========================================================

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)  # Organiza toda la categoría verticalmente.
        diseno.setContentsMargins(24, 22, 24, 22)  # Mantiene los mismos márgenes de las demás secciones.
        diseno.setSpacing(14)  # Conserva separación uniforme.

        titulo = QLabel("Editor")  # Presenta el nombre de la categoría.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el encabezado azul.
        titulo.setContentsMargins(4, 0, 4, 0)  # Conserva una pequeña separación lateral.
        diseno.addWidget(titulo)  # Añade el título.

        descripcion = QLabel(
            "Personaliza la visualización y algunos comportamientos del editor donde escribes el código fuente de TecNet Finder."
        )  # Resume el propósito de esta categoría.

        descripcion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación horizontal.
        descripcion.setWordWrap(True)  # Permite varias líneas.
        diseno.addWidget(descripcion)  # Coloca la explicación.

        # ====================================================
        # Tarjeta 1: Visualización del contenido
        # ====================================================

        tarjeta_visualizacion = QFrame()  # Crea la primera tarjeta.
        tarjeta_visualizacion.setObjectName("TarjetaConfiguracion")  # Reutiliza el marco común.

        diseno_visualizacion = QVBoxLayout(tarjeta_visualizacion)  # Organiza el contenido.
        diseno_visualizacion.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding.
        diseno_visualizacion.setSpacing(9)  # Conserva una separación compacta.

        subtitulo_visualizacion = QLabel("Visualización del contenido")  # Identifica la tarjeta.
        subtitulo_visualizacion.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo interno.
        diseno_visualizacion.addWidget(subtitulo_visualizacion)  # Coloca el subtítulo.

        descripcion_visualizacion = QLabel(
            "Controla cómo se distribuye el código dentro del área visible y qué accesos rápidos aparecen sobre el editor."
        )  # Explica ambas opciones.

        descripcion_visualizacion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_visualizacion.setWordWrap(True)  # Permite adaptar el texto.
        diseno_visualizacion.addWidget(descripcion_visualizacion)  # Añade la explicación.

        # ----------------------------------------------------
        # Ajuste de línea
        # ----------------------------------------------------

        fila_ajuste = QHBoxLayout()  # Organiza casilla y texto.
        fila_ajuste.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_ajuste.setSpacing(9)  # Separa ambos elementos.

        self.casilla_ajuste_linea = BotonCasillaEditor(
            "Ajustar automáticamente las líneas largas",
            self,
        )  # Crea la preferencia de ajuste.

        etiqueta_ajuste = QLabel("Ajustar automáticamente las líneas largas")  # Presenta el nombre visible.
        etiqueta_ajuste.setObjectName("TextoConfiguracion")  # Utiliza el estilo común.

        self.casilla_ajuste_linea.setChecked(
            self.preferencias_aplicacion.ajuste_linea_editor_activado()
        )  # Recupera el valor temporal actual.

        self.casilla_ajuste_linea.toggled.connect(
            self._cambiar_ajuste_linea
        )  # Registra cualquier modificación.

        fila_ajuste.addWidget(self.casilla_ajuste_linea)  # Coloca la casilla.
        fila_ajuste.addWidget(etiqueta_ajuste)  # Coloca la descripción.
        fila_ajuste.addStretch()  # Mantiene la opción alineada a la izquierda.

        diseno_visualizacion.addLayout(fila_ajuste)  # Añade la primera preferencia.

        # ----------------------------------------------------
        # Botones rápidos
        # ----------------------------------------------------

        fila_botones = QHBoxLayout()  # Organiza la segunda casilla.
        fila_botones.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_botones.setSpacing(9)  # Separa casilla y texto.

        self.casilla_botones_rapidos = BotonCasillaEditor(
            "Mostrar los botones rápidos Ampliar y Ejemplos",
            self,
        )  # Crea la preferencia de visibilidad.

        etiqueta_botones = QLabel("Mostrar los botones rápidos Ampliar y Ejemplos")  # Presenta el nombre.
        etiqueta_botones.setObjectName("TextoConfiguracion")  # Mantiene el estilo común.

        self.casilla_botones_rapidos.setChecked(
            self.preferencias_aplicacion.botones_rapidos_editor_visibles()
        )  # Recupera la selección temporal.

        self.casilla_botones_rapidos.toggled.connect(
            self._cambiar_botones_rapidos
        )  # Registra cualquier cambio.

        fila_botones.addWidget(self.casilla_botones_rapidos)  # Coloca la casilla.
        fila_botones.addWidget(etiqueta_botones)  # Coloca el texto.
        fila_botones.addStretch()  # Mantiene la fila alineada a la izquierda.

        diseno_visualizacion.addLayout(fila_botones)  # Añade la segunda preferencia.
        diseno.addWidget(tarjeta_visualizacion)  # Incorpora la primera tarjeta.

        # ====================================================
        # Tarjeta 2: Tipografía
        # ====================================================

        tarjeta_tipografia = QFrame()  # Crea la tarjeta destinada a la fuente.
        tarjeta_tipografia.setObjectName("TarjetaConfiguracion")  # Reutiliza el marco exterior.

        diseno_tipografia = QVBoxLayout(tarjeta_tipografia)  # Organiza sus controles.
        diseno_tipografia.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding.
        diseno_tipografia.setSpacing(9)  # Conserva separación uniforme.

        subtitulo_tipografia = QLabel("Tipografía")  # Identifica la tarjeta.
        subtitulo_tipografia.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo interno.
        diseno_tipografia.addWidget(subtitulo_tipografia)  # Coloca el subtítulo.

        descripcion_tipografia = QLabel(
            "Elige la familia y el tamaño utilizados para escribir y revisar las instrucciones del lenguaje."
        )  # Explica que estas opciones pertenecen únicamente al editor.

        descripcion_tipografia.setObjectName("DescripcionConfiguracion")  # Mantiene el aspecto secundario.
        descripcion_tipografia.setWordWrap(True)  # Permite adaptar la explicación.
        diseno_tipografia.addWidget(descripcion_tipografia)  # Coloca el texto.

        # ----------------------------------------------------
        # Familia del editor
        # ----------------------------------------------------

        fila_familia = QHBoxLayout()  # Organiza etiqueta y selector.
        fila_familia.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_familia.setSpacing(10)  # Separa ambos elementos.

        etiqueta_familia = QLabel("Familia de fuente:")  # Presenta el nombre de la preferencia.
        etiqueta_familia.setObjectName("TextoConfiguracion")  # Utiliza el estilo común.

        self.selector_fuente = SelectorFuentes(self)  # Utiliza el selector especializado con búsqueda.
        self.selector_fuente.setFixedWidth(300)  # Reserva espacio suficiente para nombres extensos.

        self.selector_fuente.establecer_valor(
            self.preferencias_aplicacion.familia_fuente_editor()
        )  # Recupera la familia temporal actual.

        self.selector_fuente.valor_cambiado.connect(
            self._cambiar_familia_fuente
        )  # Registra una nueva familia únicamente después de seleccionarla.

        fila_familia.addWidget(etiqueta_familia)  # Coloca la descripción.
        fila_familia.addWidget(self.selector_fuente)  # Coloca el selector.
        fila_familia.addStretch()  # Mantiene la fila alineada a la izquierda.

        diseno_tipografia.addLayout(fila_familia)  # Incorpora la selección.

        # ----------------------------------------------------
        # Tamaño del editor
        # ----------------------------------------------------

        fila_tamano = QHBoxLayout()  # Organiza etiqueta y campo.
        fila_tamano.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación.
        fila_tamano.setSpacing(10)  # Separa los elementos.

        etiqueta_tamano = QLabel("Tamaño de fuente:")  # Identifica el campo numérico.
        etiqueta_tamano.setObjectName("TextoConfiguracion")  # Utiliza el mismo estilo.

        self.selector_tamano_fuente = CampoNumeroConfiguracion(self)  # Utiliza el campo numérico personalizado.

        self.selector_tamano_fuente.setRange(
            PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MINIMO,
            PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MAXIMO,
        )  # Conserva los límites establecidos.

        self.selector_tamano_fuente.setSuffix(" pt")  # Aclara la unidad.
        self.selector_tamano_fuente.setValue(
            self.preferencias_aplicacion.tamano_fuente_editor()
        )  # Recupera el valor temporal.

        self.selector_tamano_fuente.setFixedWidth(130)  # Mantiene un ancho compacto.

        self.selector_tamano_fuente.valueChanged.connect(
            self._cambiar_tamano_fuente
        )  # Registra futuras modificaciones.

        fila_tamano.addWidget(etiqueta_tamano)  # Coloca la etiqueta.
        fila_tamano.addWidget(self.selector_tamano_fuente)  # Coloca el campo.
        fila_tamano.addStretch()  # Mantiene todo alineado a la izquierda.

        diseno_tipografia.addLayout(fila_tamano)  # Añade la segunda preferencia.
        diseno.addWidget(tarjeta_tipografia)  # Incorpora la tarjeta.

        # ====================================================
        # Tarjeta 3: Tabulación
        # ====================================================

        tarjeta_tabulacion = QFrame()  # Crea la tarjeta dedicada a Tab.
        tarjeta_tabulacion.setObjectName("TarjetaConfiguracion")  # Mantiene la misma apariencia.

        diseno_tabulacion = QVBoxLayout(tarjeta_tabulacion)  # Organiza sus elementos.
        diseno_tabulacion.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding.
        diseno_tabulacion.setSpacing(9)  # Conserva la separación.

        subtitulo_tabulacion = QLabel("Tabulación")  # Identifica la tarjeta.
        subtitulo_tabulacion.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo.
        diseno_tabulacion.addWidget(subtitulo_tabulacion)  # Coloca el subtítulo.

        descripcion_tabulacion = QLabel(
            "Define cuánto espacio visual representa una tabulación dentro del editor."
        )  # Explica esta preferencia.

        descripcion_tabulacion.setObjectName("DescripcionConfiguracion")  # Mantiene la apariencia secundaria.
        descripcion_tabulacion.setWordWrap(True)  # Permite adaptar el texto.
        diseno_tabulacion.addWidget(descripcion_tabulacion)  # Añade la explicación.

        fila_tabulacion = QHBoxLayout()  # Organiza etiqueta y selector.
        fila_tabulacion.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_tabulacion.setSpacing(10)  # Separa ambos controles.

        etiqueta_tabulacion = QLabel("Ancho de tabulación:")  # Presenta el nombre.
        etiqueta_tabulacion.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.

        self.selector_tabulacion = SelectorDesplegableConfiguracion(self)  # Mantiene el desplegable general para una lista pequeña.
        self.selector_tabulacion.setFixedWidth(180)  # Reserva un ancho suficiente.

        for espacios in (2, 4, 8):
            self.selector_tabulacion.agregar_opcion(
                f"{espacios} espacios",
                espacios,
            )  # Añade las tres cantidades soportadas.

        self.selector_tabulacion.establecer_valor(
            self.preferencias_aplicacion.espacios_tabulacion_editor()
        )  # Marca el valor temporal.

        self.selector_tabulacion.valor_cambiado.connect(
            self._cambiar_tabulacion
        )  # Registra una nueva selección.

        fila_tabulacion.addWidget(etiqueta_tabulacion)  # Coloca la etiqueta.
        fila_tabulacion.addWidget(self.selector_tabulacion)  # Coloca el selector.
        fila_tabulacion.addStretch()  # Mantiene el contenido alineado.

        diseno_tabulacion.addLayout(fila_tabulacion)  # Añade la opción.
        diseno.addWidget(tarjeta_tabulacion)  # Incorpora la última tarjeta.

        diseno.addStretch()  # Mantiene todo agrupado hacia la parte superior.

    # ========================================================
    # Modificaciones temporales
    # ========================================================

    def _cambiar_ajuste_linea(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_ajuste_linea_editor_activado(
            activado
        ):
            self.configuracion_modificada.emit()  # Informa que existe una modificación pendiente.

    def _cambiar_botones_rapidos(self, visibles: bool) -> None:
        if self.preferencias_aplicacion.establecer_botones_rapidos_editor_visibles(
            visibles
        ):
            self.configuracion_modificada.emit()  # Solicita reevaluar Aplicar.

    def _cambiar_familia_fuente(self, familia: str) -> None:
        if self.preferencias_aplicacion.establecer_familia_fuente_editor(
            str(familia)
        ):
            self.configuracion_modificada.emit()  # Registra la nueva familia como cambio temporal.

    def _cambiar_tamano_fuente(self, tamano: int) -> None:
        if self.preferencias_aplicacion.establecer_tamano_fuente_editor(
            tamano
        ):
            self.configuracion_modificada.emit()  # Registra el nuevo tamaño.

    def _cambiar_tabulacion(self, espacios) -> None:
        if self.preferencias_aplicacion.establecer_espacios_tabulacion_editor(
            int(espacios)
        ):
            self.configuracion_modificada.emit()  # Registra el nuevo ancho visual.