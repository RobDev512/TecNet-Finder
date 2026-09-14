# ============================================================
# Archivo: panel_configuracion_editor.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene la categoría Editor de Configuración.
#
# Permite modificar:
# - Ajuste automático de líneas.
# - Visibilidad de Pegar y Ejemplos.
# - Familia de fuente.
# - Tamaño de fuente.
# - Ancho visual de tabulación.
#
# Utiliza controles personalizados para evitar la apariencia nativa
# de QSpinBox y QComboBox y conservar el diseño de TecNet Finder.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Permite configurar las casillas y notificar cambios pendientes.
from PySide6.QtGui import QFontDatabase  # Permite obtener directamente las tipografías instaladas en Windows.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Importa los componentes básicos del panel.
from Interfaz.controles_configuracion import CampoNumeroConfiguracion, SelectorDesplegableConfiguracion  # Importa los controles visuales propios.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona límites y valores predeterminados del editor.


class BotonCasillaEditor(QPushButton):  # Mantiene la misma casilla visual utilizada en las demás categorías.
    def __init__(self, nombre_accesible: str, padre=None):
        super().__init__(padre)  # Inicializa el botón utilizado como casilla.
        self.setCheckable(True)  # Permite mantener un estado activado o desactivado.
        self.setFixedSize(24, 24)  # Conserva las dimensiones de las casillas actuales.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Conserva una descripción para accesibilidad.
        self.setStyleSheet("padding: 0px; font-family: 'Segoe UI Symbol'; font-size: 12pt; font-weight: bold;")  # Centra visualmente la palomita.
        self.toggled.connect(self._actualizar_apariencia)  # Actualiza el estilo cuando cambia su estado.
        self._actualizar_apariencia(False)  # Prepara inicialmente una casilla vacía.

    def _actualizar_apariencia(self, activado: bool) -> None:
        self.setText("✓" if activado else "")  # Muestra la marca únicamente cuando está activa.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Reutiliza los estilos azul y oscuro existentes.
        self.style().unpolish(self)  # Retira el estilo correspondiente con el estado anterior.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos.
        self.update()  # Redibuja inmediatamente la casilla.


class PanelConfiguracionEditor(QWidget):  # Representa toda la categoría Editor.
    configuracion_modificada = Signal()  # Informa que existe al menos una preferencia temporal diferente.

    def __init__(self, preferencias_aplicacion, padre=None):
        super().__init__(padre)  # Vincula el panel con Configuración.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva la copia temporal compartida.
        self._construir_interfaz()  # Construye las tarjetas y controles.

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)  # Organiza toda la categoría verticalmente.
        diseno.setContentsMargins(24, 22, 24, 22)  # Mantiene los mismos márgenes de las demás secciones.
        diseno.setSpacing(14)  # Conserva una separación uniforme.

        titulo = QLabel("Editor")  # Presenta el nombre de la categoría.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el encabezado azul existente.
        titulo.setContentsMargins(4, 0, 4, 0)  # Conserva una pequeña separación lateral.
        diseno.addWidget(titulo)  # Coloca el título como primer elemento.

        descripcion = QLabel("Personaliza la visualización y algunos comportamientos del editor donde escribes el código fuente de TecNet Finder.")  # Resume el propósito de esta sección.
        descripcion.setObjectName("DescripcionConfiguracion")  # Mantiene el mismo estilo secundario.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación horizontal.
        descripcion.setWordWrap(True)  # Permite varias líneas cuando sea necesario.
        diseno.addWidget(descripcion)  # Coloca la descripción debajo del título.

        tarjeta_visualizacion = QFrame()  # Crea la tarjeta de comportamiento visual.
        tarjeta_visualizacion.setObjectName("TarjetaConfiguracion")  # Reutiliza el diseño exterior común.
        diseno_visualizacion = QVBoxLayout(tarjeta_visualizacion)  # Organiza título, explicación y casillas.
        diseno_visualizacion.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding de las demás tarjetas.
        diseno_visualizacion.setSpacing(9)  # Conserva una separación compacta.
        subtitulo_visualizacion = QLabel("Visualización del contenido")  # Identifica la primera tarjeta.
        subtitulo_visualizacion.setObjectName("SubtituloConfiguracion")  # Reutiliza el encabezado interno.
        diseno_visualizacion.addWidget(subtitulo_visualizacion)  # Coloca el subtítulo.
        descripcion_visualizacion = QLabel("Controla cómo se distribuye el código dentro del área visible y qué accesos rápidos aparecen sobre el editor.")  # Explica ambas configuraciones.
        descripcion_visualizacion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_visualizacion.setWordWrap(True)  # Permite adaptar el texto.
        diseno_visualizacion.addWidget(descripcion_visualizacion)  # Coloca la explicación.

        fila_ajuste = QHBoxLayout()  # Organiza la primera casilla.
        fila_ajuste.setContentsMargins(4, 2, 4, 2)  # Mantiene su alineación.
        fila_ajuste.setSpacing(9)  # Separa casilla y texto.
        self.casilla_ajuste_linea = BotonCasillaEditor("Ajustar automáticamente las líneas largas", self)  # Crea la opción de ajuste.
        etiqueta_ajuste = QLabel("Ajustar automáticamente las líneas largas")  # Presenta su nombre visible.
        etiqueta_ajuste.setObjectName("TextoConfiguracion")  # Utiliza el estilo de opciones.
        self.casilla_ajuste_linea.setChecked(self.preferencias_aplicacion.ajuste_linea_editor_activado())  # Recupera el valor temporal.
        self.casilla_ajuste_linea.toggled.connect(self._cambiar_ajuste_linea)  # Registra cualquier modificación.
        fila_ajuste.addWidget(self.casilla_ajuste_linea)  # Coloca primero la casilla.
        fila_ajuste.addWidget(etiqueta_ajuste)  # Coloca después el texto.
        fila_ajuste.addStretch()  # Mantiene el conjunto alineado a la izquierda.
        diseno_visualizacion.addLayout(fila_ajuste)  # Incorpora la primera opción.

        fila_botones = QHBoxLayout()  # Organiza la visibilidad de los botones rápidos.
        fila_botones.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación.
        fila_botones.setSpacing(9)  # Separa casilla y descripción.
        self.casilla_botones_rapidos = BotonCasillaEditor("Mostrar los botones rápidos Pegar y Ejemplos", self)  # Crea la segunda opción.
        etiqueta_botones = QLabel("Mostrar los botones rápidos Pegar y Ejemplos")  # Presenta su nombre.
        etiqueta_botones.setObjectName("TextoConfiguracion")  # Mantiene el estilo común.
        self.casilla_botones_rapidos.setChecked(self.preferencias_aplicacion.botones_rapidos_editor_visibles())  # Recupera la selección temporal.
        self.casilla_botones_rapidos.toggled.connect(self._cambiar_botones_rapidos)  # Registra cualquier cambio.
        fila_botones.addWidget(self.casilla_botones_rapidos)  # Coloca la casilla.
        fila_botones.addWidget(etiqueta_botones)  # Coloca su texto.
        fila_botones.addStretch()  # Mantiene ambos elementos alineados.
        diseno_visualizacion.addLayout(fila_botones)  # Incorpora la segunda opción.
        diseno.addWidget(tarjeta_visualizacion)  # Añade la primera tarjeta completa.

        tarjeta_tipografia = QFrame()  # Crea la tarjeta dedicada con la fuente.
        tarjeta_tipografia.setObjectName("TarjetaConfiguracion")  # Utiliza el mismo marco exterior.
        diseno_tipografia = QVBoxLayout(tarjeta_tipografia)  # Organiza sus controles.
        diseno_tipografia.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding.
        diseno_tipografia.setSpacing(9)  # Mantiene separación uniforme.
        subtitulo_tipografia = QLabel("Tipografía")  # Identifica la tarjeta.
        subtitulo_tipografia.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo de títulos.
        diseno_tipografia.addWidget(subtitulo_tipografia)  # Coloca el subtítulo.
        descripcion_tipografia = QLabel("Elige la familia y el tamaño utilizados para escribir y revisar las instrucciones del lenguaje.")  # Explica ahora las dos opciones disponibles.
        descripcion_tipografia.setObjectName("DescripcionConfiguracion")  # Mantiene la apariencia secundaria.
        descripcion_tipografia.setWordWrap(True)  # Permite adaptar la explicación.
        diseno_tipografia.addWidget(descripcion_tipografia)  # Coloca el texto explicativo.

        fila_familia = QHBoxLayout()  # Organiza la nueva selección de tipografía.
        fila_familia.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación con las demás opciones.
        fila_familia.setSpacing(10)  # Separa etiqueta y selector.
        etiqueta_familia = QLabel("Familia de fuente:")  # Presenta el nombre de la preferencia.
        etiqueta_familia.setObjectName("TextoConfiguracion")  # Utiliza el mismo fondo redondeado.
        self.selector_fuente = SelectorDesplegableConfiguracion(self)  # Utiliza el nuevo desplegable completamente personalizado.
        self.selector_fuente.setFixedWidth(300)  # Deja espacio suficiente para nombres largos de fuentes.
        familias = sorted(QFontDatabase.families(), key=str.casefold)  # Obtiene y ordena todas las tipografías disponibles realmente en el equipo.
        familia_actual = self.preferencias_aplicacion.familia_fuente_editor()  # Recupera la tipografía seleccionada actualmente.
        if familia_actual not in familias:  # Comprueba si la preferencia ya no existe dentro de Windows.
            familias.insert(0, familia_actual)  # Conserva temporalmente la selección para no perderla silenciosamente.
        for familia in familias:  # Recorre las fuentes disponibles.
            self.selector_fuente.agregar_opcion(familia, familia)  # Presenta el nombre y utiliza el mismo texto como dato interno.
        self.selector_fuente.establecer_valor(familia_actual)  # Marca la fuente actualmente seleccionada.
        self.selector_fuente.valor_cambiado.connect(self._cambiar_familia_fuente)  # Registra cualquier nueva elección.
        fila_familia.addWidget(etiqueta_familia)  # Coloca primero la descripción.
        fila_familia.addWidget(self.selector_fuente)  # Coloca después el selector.
        fila_familia.addStretch()  # Mantiene el conjunto alineado a la izquierda.
        diseno_tipografia.addLayout(fila_familia)  # Añade la nueva preferencia.

        fila_tamano = QHBoxLayout()  # Organiza el campo numérico de tamaño.
        fila_tamano.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación.
        fila_tamano.setSpacing(10)  # Separa etiqueta y campo.
        etiqueta_tamano = QLabel("Tamaño de fuente:")  # Identifica el valor numérico.
        etiqueta_tamano.setObjectName("TextoConfiguracion")  # Utiliza el mismo estilo de texto.
        self.selector_tamano_fuente = CampoNumeroConfiguracion(self)  # Utiliza el nuevo campo plano sin flechas nativas.
        self.selector_tamano_fuente.setRange(PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MINIMO, PreferenciasAplicacion.TAMANO_FUENTE_EDITOR_MAXIMO)  # Conserva los límites establecidos.
        self.selector_tamano_fuente.setSuffix(" pt")  # Aclara que el valor se expresa en puntos.
        self.selector_tamano_fuente.setValue(self.preferencias_aplicacion.tamano_fuente_editor())  # Recupera el tamaño temporal actual.
        self.selector_tamano_fuente.setFixedWidth(130)  # Mantiene un ancho compacto parecido al ejemplo de VS Code.
        self.selector_tamano_fuente.valueChanged.connect(self._cambiar_tamano_fuente)  # Registra cualquier modificación.
        fila_tamano.addWidget(etiqueta_tamano)  # Coloca primero la etiqueta.
        fila_tamano.addWidget(self.selector_tamano_fuente)  # Coloca después el campo limpio.
        fila_tamano.addStretch()  # Mantiene ambos controles alineados a la izquierda.
        diseno_tipografia.addLayout(fila_tamano)  # Añade la segunda preferencia.
        diseno.addWidget(tarjeta_tipografia)  # Incorpora la tarjeta completa.

        tarjeta_tabulacion = QFrame()  # Crea la tarjeta dedicada con Tab.
        tarjeta_tabulacion.setObjectName("TarjetaConfiguracion")  # Mantiene la misma apariencia exterior.
        diseno_tabulacion = QVBoxLayout(tarjeta_tabulacion)  # Organiza su contenido.
        diseno_tabulacion.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding.
        diseno_tabulacion.setSpacing(9)  # Conserva la separación.
        subtitulo_tabulacion = QLabel("Tabulación")  # Identifica la tarjeta.
        subtitulo_tabulacion.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo interno.
        diseno_tabulacion.addWidget(subtitulo_tabulacion)  # Coloca el subtítulo.
        descripcion_tabulacion = QLabel("Define cuánto espacio visual representa una tabulación dentro del editor.")  # Explica la configuración.
        descripcion_tabulacion.setObjectName("DescripcionConfiguracion")  # Mantiene la apariencia secundaria.
        descripcion_tabulacion.setWordWrap(True)  # Permite adaptar el texto.
        diseno_tabulacion.addWidget(descripcion_tabulacion)  # Coloca la descripción.

        fila_tabulacion = QHBoxLayout()  # Organiza etiqueta y selector.
        fila_tabulacion.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_tabulacion.setSpacing(10)  # Separa ambos elementos.
        etiqueta_tabulacion = QLabel("Ancho de tabulación:")  # Presenta el nombre de la preferencia.
        etiqueta_tabulacion.setObjectName("TextoConfiguracion")  # Reutiliza el estilo existente.
        self.selector_tabulacion = SelectorDesplegableConfiguracion(self)  # Sustituye por completo el antiguo QComboBox.
        self.selector_tabulacion.setFixedWidth(180)  # Reserva un ancho cómodo para las tres opciones.
        for espacios in (2, 4, 8):  # Recorre los valores soportados.
            self.selector_tabulacion.agregar_opcion(f"{espacios} espacios", espacios)  # Presenta un texto claro y conserva el número real.
        self.selector_tabulacion.establecer_valor(self.preferencias_aplicacion.espacios_tabulacion_editor())  # Marca la configuración temporal actual.
        self.selector_tabulacion.valor_cambiado.connect(self._cambiar_tabulacion)  # Registra cualquier selección nueva.
        fila_tabulacion.addWidget(etiqueta_tabulacion)  # Coloca la etiqueta.
        fila_tabulacion.addWidget(self.selector_tabulacion)  # Coloca el selector personalizado.
        fila_tabulacion.addStretch()  # Mantiene todo alineado a la izquierda.
        diseno_tabulacion.addLayout(fila_tabulacion)  # Añade la preferencia.
        diseno.addWidget(tarjeta_tabulacion)  # Incorpora la última tarjeta.
        diseno.addStretch()  # Mantiene todas las tarjetas agrupadas en la zona superior.

    def _cambiar_ajuste_linea(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_ajuste_linea_editor_activado(activado):  # Conserva temporalmente la decisión.
            self.configuracion_modificada.emit()  # Solicita reevaluar el botón Aplicar.

    def _cambiar_botones_rapidos(self, visibles: bool) -> None:
        if self.preferencias_aplicacion.establecer_botones_rapidos_editor_visibles(visibles):  # Conserva temporalmente la visibilidad.
            self.configuracion_modificada.emit()  # Informa que existe una modificación pendiente.

    def _cambiar_familia_fuente(self, familia) -> None:
        if self.preferencias_aplicacion.establecer_familia_fuente_editor(str(familia)):  # Conserva temporalmente la nueva tipografía.
            self.configuracion_modificada.emit()  # Solicita habilitar Aplicar.

    def _cambiar_tamano_fuente(self, tamano: int) -> None:
        if self.preferencias_aplicacion.establecer_tamano_fuente_editor(tamano):  # Valida y conserva el tamaño temporal.
            self.configuracion_modificada.emit()  # Informa que existe una modificación pendiente.

    def _cambiar_tabulacion(self, espacios) -> None:
        if self.preferencias_aplicacion.establecer_espacios_tabulacion_editor(int(espacios)):  # Conserva temporalmente la opción seleccionada.
            self.configuracion_modificada.emit()  # Solicita actualizar Aplicar.