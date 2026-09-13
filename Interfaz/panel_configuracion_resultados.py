# ============================================================
# Archivo: panel_configuracion_resultados.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las preferencias generales relacionadas
# con la ventana principal, la navegación después de compilar y
# la presentación de los resultados.
#
# Permite elegir el lado predeterminado de Media pantalla,
# activar o desactivar la navegación automática tras compilar y
# decidir si las advertencias deben mostrarse debajo de Tabla VLSM.
#
# Las decisiones se guardan mediante PreferenciasAplicacion y se
# comunican inmediatamente al controlador general de Configuración.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Permite emitir cambios hacia Configuración y controlar alineaciones generales.
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget  # Importa los controles utilizados por las preferencias generales.

from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Centraliza la persistencia de todas las opciones mostradas por este panel.


class PanelConfiguracionResultados(QWidget):  # Agrupa las preferencias relacionadas con ventana, compilación y resultados.
    lado_media_pantalla_cambiado = Signal(str)  # Informa que el usuario seleccionó otra mitad predeterminada.
    navegacion_automatica_cambiada = Signal(bool)  # Informa que cambió el comportamiento posterior a la compilación.
    advertencias_vlsm_cambiadas = Signal(bool)  # Informa que cambió la visibilidad del panel compacto de advertencias.

    def __init__(
        self,
        preferencias_aplicacion: PreferenciasAplicacion,
        padre=None,
    ):
        super().__init__(padre)  # Vincula el panel con la ventana general de Configuración.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva el administrador persistente utilizado por los controles.
        self._construir_interfaz()  # Construye todas las opciones y refleja inmediatamente los valores guardados.

    def _construir_interfaz(self) -> None:
        diseno_principal = QVBoxLayout(self)  # Organiza verticalmente encabezado, tarjetas y espacio final.
        diseno_principal.setContentsMargins(22, 20, 22, 20)  # Mantiene una separación cómoda respecto con los bordes de Configuración.
        diseno_principal.setSpacing(14)  # Separa de forma consistente las diferentes secciones.

        titulo = QLabel("Ventana y resultados")  # Identifica el grupo general de preferencias.
        titulo.setObjectName("TituloDialogoIA")  # Reutiliza el formato de encabezado grande empleado dentro de Configuración.
        diseno_principal.addWidget(titulo)  # Coloca el nombre como primer elemento visible.

        descripcion = QLabel(
            "Personaliza cómo TecNet Finder utiliza Media pantalla y qué vista muestra después de compilar."
        )  # Explica brevemente el alcance de estas opciones.
        descripcion.setObjectName("DescripcionDialogoIA")  # Utiliza el tono secundario ya definido por la aplicación.
        descripcion.setWordWrap(True)  # Permite adaptar la explicación al ancho disponible.
        diseno_principal.addWidget(descripcion)  # Coloca la explicación inmediatamente debajo del título.

        tarjeta_ventana = self._crear_tarjeta()  # Crea la primera superficie destinada a las preferencias de ventana.
        diseno_ventana = QVBoxLayout(tarjeta_ventana)  # Organiza título, descripción y selector.
        diseno_ventana.setContentsMargins(16, 14, 16, 14)  # Mantiene suficiente espacio dentro de la tarjeta.
        diseno_ventana.setSpacing(10)  # Separa claramente sus elementos.

        titulo_ventana = QLabel("Ventana y pantalla dividida")  # Identifica las opciones relacionadas con Media pantalla.
        titulo_ventana.setObjectName("TituloSeccion")  # Utiliza el formato azul reservado para subsecciones.
        diseno_ventana.addWidget(titulo_ventana)  # Coloca el nombre como encabezado de la tarjeta.

        descripcion_ventana = QLabel(
            "Elige la mitad que TecNet Finder propondrá inicialmente cuando utilices el selector de Media pantalla."
        )  # Explica que la preferencia no sustituye las dos opciones manuales del popup.
        descripcion_ventana.setWordWrap(True)  # Permite distribuir naturalmente el texto.
        descripcion_ventana.setStyleSheet("color: #a6adc8;")  # Mantiene la explicación en un tono secundario.
        diseno_ventana.addWidget(descripcion_ventana)  # Coloca la explicación debajo del encabezado.

        fila_lado = QHBoxLayout()  # Sitúa la etiqueta y el selector sobre una misma línea.
        fila_lado.setContentsMargins(0, 0, 0, 0)  # Evita agregar márgenes duplicados.
        fila_lado.setSpacing(12)  # Conserva una separación cómoda entre ambos controles.

        etiqueta_lado = QLabel("Lado predeterminado:")  # Describe qué valor controla el selector.
        fila_lado.addWidget(etiqueta_lado)  # Coloca la descripción a la izquierda.

        self.selector_lado = QComboBox()  # Permite seleccionar exclusivamente una de las dos mitades compatibles.
        self.selector_lado.addItem("Izquierda", PreferenciasAplicacion.LADO_IZQUIERDO)  # Registra la mitad izquierda con su valor interno.
        self.selector_lado.addItem("Derecha", PreferenciasAplicacion.LADO_DERECHO)  # Registra la mitad derecha con su valor interno.
        self.selector_lado.setMinimumWidth(180)  # Mantiene ambos nombres completamente visibles.
        fila_lado.addWidget(self.selector_lado)  # Coloca el selector inmediatamente después de la etiqueta.
        fila_lado.addStretch()  # Conserva los controles alineados hacia la izquierda.
        diseno_ventana.addLayout(fila_lado)  # Incorpora la fila dentro de la tarjeta.

        lado_guardado = self.preferencias_aplicacion.lado_media_pantalla()  # Recupera la mitad persistida antes de conectar señales.
        indice_lado = self.selector_lado.findData(lado_guardado)  # Localiza el elemento visual correspondiente con el valor interno.

        if indice_lado >= 0:
            self.selector_lado.setCurrentIndex(indice_lado)  # Refleja correctamente la preferencia existente.

        self.selector_lado.currentIndexChanged.connect(
            self._cambiar_lado_media_pantalla
        )  # Guarda y comunica cualquier modificación realizada por el usuario.

        diseno_principal.addWidget(tarjeta_ventana)  # Coloca la tarjeta de ventana dentro del panel principal.

        tarjeta_compilacion = self._crear_tarjeta()  # Crea la superficie destinada al comportamiento posterior a la compilación.
        diseno_compilacion = QVBoxLayout(tarjeta_compilacion)  # Organiza sus opciones verticalmente.
        diseno_compilacion.setContentsMargins(16, 14, 16, 14)  # Mantiene espacio interior uniforme.
        diseno_compilacion.setSpacing(10)  # Separa sus controles de forma clara.

        titulo_compilacion = QLabel("Compilación y navegación")  # Identifica el segundo grupo de preferencias.
        titulo_compilacion.setObjectName("TituloSeccion")  # Utiliza el mismo formato visual de las demás subsecciones.
        diseno_compilacion.addWidget(titulo_compilacion)  # Coloca el encabezado dentro de la tarjeta.

        self.casilla_navegacion = QCheckBox(
            "Abrir automáticamente el resultado más importante después de compilar"
        )  # Permite conservar o desactivar la navegación automática actual.
        self.casilla_navegacion.setChecked(
            self.preferencias_aplicacion.navegacion_automatica_activada()
        )  # Refleja el estado persistido antes de conectar la señal.
        self.casilla_navegacion.setToolTip(
            "Con esta opción activa, los errores abren Diagnósticos y las compilaciones válidas abren Tabla VLSM."
        )  # Explica concretamente qué significa la navegación automática.
        self.casilla_navegacion.toggled.connect(
            self._cambiar_navegacion_automatica
        )  # Guarda inmediatamente cualquier modificación.
        diseno_compilacion.addWidget(self.casilla_navegacion)  # Agrega la primera preferencia de compilación.

        self.casilla_advertencias = QCheckBox(
            "Mostrar advertencias debajo de Tabla VLSM"
        )  # Permite controlar independientemente el panel compacto implementado.
        self.casilla_advertencias.setChecked(
            self.preferencias_aplicacion.advertencias_vlsm_visibles()
        )  # Refleja el estado persistido antes de conectar la señal.
        self.casilla_advertencias.setToolTip(
            "Las advertencias completas continúan disponibles en Errores / Advertencias aunque este panel compacto se oculte."
        )  # Aclara que la preferencia solamente afecta la representación resumida.
        self.casilla_advertencias.toggled.connect(
            self._cambiar_advertencias_vlsm
        )  # Guarda inmediatamente la decisión del usuario.
        diseno_compilacion.addWidget(self.casilla_advertencias)  # Agrega la segunda preferencia de compilación.

        diseno_principal.addWidget(tarjeta_compilacion)  # Coloca la tarjeta de compilación debajo de las opciones de ventana.
        diseno_principal.addStretch()  # Mantiene las preferencias agrupadas en la zona superior.

    def _crear_tarjeta(self) -> QFrame:
        tarjeta = QFrame(self)  # Crea una superficie independiente dentro de Configuración.
        tarjeta.setObjectName("PanelConfiguracionResultados")  # Permite aplicar exclusivamente el estilo de estas tarjetas.
        tarjeta.setStyleSheet(
            """
            QFrame#PanelConfiguracionResultados {
                background-color: #181825;
                border: 1px solid #45475a;
                border-radius: 8px;
            }

            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #585b70;
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 22px;
            }

            QComboBox:hover {
                border: 1px solid #89b4fa;
            }

            QComboBox QAbstractItemView {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #45475a;
                selection-background-color: #45475a;
            }

            QCheckBox {
                color: #cdd6f4;
                spacing: 8px;
                padding: 4px 0px;
            }
            """
        )  # Integra tarjetas, selector y casillas con la apariencia oscura general.
        return tarjeta  # Devuelve la superficie preparada para recibir contenido.

    def _cambiar_lado_media_pantalla(self, indice: int) -> None:
        lado = self.selector_lado.itemData(indice)  # Recupera el valor interno correspondiente con la opción seleccionada.

        if lado not in (
            PreferenciasAplicacion.LADO_IZQUIERDO,
            PreferenciasAplicacion.LADO_DERECHO,
        ):
            return  # Ignora cualquier elemento inesperado que no represente una mitad válida.

        if self.preferencias_aplicacion.establecer_lado_media_pantalla(lado):
            self.lado_media_pantalla_cambiado.emit(lado)  # Comunica el cambio únicamente después de guardar correctamente la preferencia.
            return

        self._restaurar_lado_guardado()  # Recupera visualmente el valor persistido cuando la escritura falla.

    def _cambiar_navegacion_automatica(self, activada: bool) -> None:
        if self.preferencias_aplicacion.establecer_navegacion_automatica_activada(activada):
            self.navegacion_automatica_cambiada.emit(bool(activada))  # Comunica inmediatamente el nuevo comportamiento efectivo.
            return

        self.casilla_navegacion.blockSignals(True)  # Evita volver a ejecutar la escritura mientras se restaura la opción.
        self.casilla_navegacion.setChecked(
            self.preferencias_aplicacion.navegacion_automatica_activada()
        )  # Recupera el valor que realmente permanece guardado.
        self.casilla_navegacion.blockSignals(False)  # Reactiva futuras modificaciones realizadas por el usuario.

    def _cambiar_advertencias_vlsm(self, visibles: bool) -> None:
        if self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(visibles):
            self.advertencias_vlsm_cambiadas.emit(bool(visibles))  # Comunica inmediatamente la nueva visibilidad efectiva.
            return

        self.casilla_advertencias.blockSignals(True)  # Evita ejecutar otra escritura durante la restauración.
        self.casilla_advertencias.setChecked(
            self.preferencias_aplicacion.advertencias_vlsm_visibles()
        )  # Recupera la decisión que continúa persistida.
        self.casilla_advertencias.blockSignals(False)  # Reactiva futuras modificaciones normales.

    def _restaurar_lado_guardado(self) -> None:
        lado_guardado = self.preferencias_aplicacion.lado_media_pantalla()  # Recupera la mitad que realmente continúa almacenada.
        indice = self.selector_lado.findData(lado_guardado)  # Localiza nuevamente su representación visual.

        if indice < 0:
            return  # Mantiene el selector intacto ante una situación inesperada.

        self.selector_lado.blockSignals(True)  # Evita guardar otra vez mientras únicamente se corrige la interfaz.
        self.selector_lado.setCurrentIndex(indice)  # Recupera visualmente el valor persistido.
        self.selector_lado.blockSignals(False)  # Reactiva la interacción normal.