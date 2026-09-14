# ============================================================
# Archivo: panel_configuracion_ventana.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las preferencias relacionadas con el
# comportamiento general de la ventana de TecNet Finder.
#
# La sección permite decidir:
#
# - Si TecNet Finder debe iniciar maximizado.
# - Si debe recordar entre ejecuciones si anteriormente estaba
#   maximizado o utilizando una ventana convencional.
# - Si Configuración debe recuperar la última categoría visitada.
#
# Estas preferencias solamente modifican la experiencia visual
# de la aplicación y no intervienen en ninguna fase del compilador.
# ============================================================

from PySide6.QtCore import Qt  # Permite configurar el cursor utilizado por las casillas personalizadas.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Proporciona los controles necesarios para construir esta categoría.

from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Centraliza las preferencias generales utilizadas por la aplicación.


class BotonCasillaVentana(QPushButton):  # Representa una casilla con la misma apariencia utilizada por las demás categorías.
    def __init__(self, nombre_accesible: str, padre=None):  # Recibe la descripción accesible y el panel propietario.
        super().__init__(padre)  # Inicializa el botón utilizado como control de selección.
        self.setCheckable(True)  # Permite conservar explícitamente los estados activado y desactivado.
        self.setFixedSize(24, 24)  # Mantiene las mismas dimensiones utilizadas por las demás casillas.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica visualmente que el usuario puede pulsar el control.
        self.setAccessibleName(nombre_accesible)  # Proporciona una descripción útil para herramientas de accesibilidad.
        self.setStyleSheet("padding: 0px; font-family: 'Segoe UI Symbol'; font-size: 12pt; font-weight: bold;")  # Mantiene centrada la marca de verificación.
        self.toggled.connect(self._actualizar_apariencia)  # Actualiza inmediatamente la apariencia cuando cambia el estado.
        self._actualizar_apariencia(False)  # Prepara inicialmente una casilla desactivada.

    def _actualizar_apariencia(self, activado: bool) -> None:  # Sincroniza la representación visual con el estado lógico.
        self.setText("✓" if activado else "")  # Muestra la marca solamente mientras la opción se encuentra activa.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Reutiliza los estilos azul y oscuro existentes.
        self.style().unpolish(self)  # Retira temporalmente la apariencia anterior.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos con el nuevo estado.
        self.update()  # Solicita el redibujado inmediato del control.


class PanelConfiguracionVentana(QWidget):  # Agrupa las preferencias correspondientes con ventana y comportamiento visual.
    def __init__(self, preferencias_aplicacion: PreferenciasAplicacion, padre=None):  # Recibe el administrador de preferencias utilizado por Configuración.
        super().__init__(padre)  # Vincula el panel con la ventana general de Configuración.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva la misma instancia compartida por esta sesión.
        self._construir_interfaz()  # Construye todos los controles representando los valores actuales.

    def _construir_interfaz(self) -> None:  # Construye encabezado y las tres tarjetas de esta categoría.
        diseno = QVBoxLayout(self)  # Organiza verticalmente título, descripción y tarjetas.
        diseno.setContentsMargins(24, 22, 24, 22)  # Utiliza los mismos márgenes exteriores de las demás categorías.
        diseno.setSpacing(14)  # Conserva una separación uniforme entre grupos.

        titulo = QLabel("Ventana y apariencia")  # Presenta el nombre de la categoría.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el estilo general de los títulos.
        titulo.setContentsMargins(4, 0, 4, 0)  # Mantiene una pequeña separación lateral.
        diseno.addWidget(titulo)  # Coloca el encabezado al principio del panel.

        descripcion = QLabel("Personaliza cómo inicia TecNet Finder y qué comportamiento de la interfaz debe conservar entre ejecuciones.")  # Resume el propósito de la categoría.
        descripcion.setObjectName("DescripcionConfiguracion")  # Utiliza el estilo secundario común.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Mantiene la misma alineación horizontal del título.
        descripcion.setWordWrap(True)  # Permite adaptar naturalmente el texto al ancho disponible.
        diseno.addWidget(descripcion)  # Coloca la explicación debajo del encabezado.

        # ====================================================
        # Tarjeta 1: Inicio de TecNet Finder
        # ====================================================

        tarjeta_inicio = QFrame()  # Crea la tarjeta relacionada con el comportamiento inicial.
        tarjeta_inicio.setObjectName("TarjetaConfiguracion")  # Reutiliza el diseño exterior común.
        diseno_inicio = QVBoxLayout(tarjeta_inicio)  # Organiza título, descripción y opción.
        diseno_inicio.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding utilizado por las demás tarjetas.
        diseno_inicio.setSpacing(9)  # Conserva próximos los elementos del mismo grupo.

        subtitulo_inicio = QLabel("Inicio de TecNet Finder")  # Identifica la primera tarjeta.
        subtitulo_inicio.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo interno de subtítulos.
        subtitulo_inicio.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación del contenido.
        diseno_inicio.addWidget(subtitulo_inicio)  # Coloca el encabezado interno.

        descripcion_inicio = QLabel("Define el estado utilizado al abrir TecNet Finder cuando no se está recuperando un estado anterior.")  # Explica cuándo se utiliza esta preferencia.
        descripcion_inicio.setObjectName("DescripcionConfiguracion")  # Mantiene la apariencia secundaria.
        descripcion_inicio.setContentsMargins(4, 2, 4, 2)  # Conserva una pequeña separación alrededor del texto.
        descripcion_inicio.setWordWrap(True)  # Permite distribuir correctamente la explicación.
        diseno_inicio.addWidget(descripcion_inicio)  # Coloca el texto antes de la opción.

        fila_inicio = QHBoxLayout()  # Organiza horizontalmente la casilla y su descripción.
        fila_inicio.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación de las demás opciones.
        fila_inicio.setSpacing(9)  # Separa casilla y texto.

        self.casilla_iniciar_maximizado = BotonCasillaVentana("Iniciar TecNet Finder maximizado", self)  # Crea la preferencia correspondiente con el estado inicial.
        self.etiqueta_iniciar_maximizado = QLabel("Iniciar TecNet Finder maximizado")  # Presenta el texto visible de la opción.
        self.etiqueta_iniciar_maximizado.setObjectName("TextoConfiguracion")  # Mantiene el estilo tipográfico general.
        self.etiqueta_iniciar_maximizado.setContentsMargins(2, 0, 2, 0)  # Conserva una pequeña separación interior.
        self.casilla_iniciar_maximizado.setChecked(self.preferencias_aplicacion.iniciar_maximizado())  # Representa el valor actual de la preferencia.

        ayuda_inicio = "Cuando no exista un estado anterior para recuperar, TecNet Finder iniciará ocupando toda el área disponible."  # Prepara una explicación compartida por casilla y texto.
        self.casilla_iniciar_maximizado.setToolTip(ayuda_inicio)  # Permite consultar la explicación desde la casilla.
        self.etiqueta_iniciar_maximizado.setToolTip(ayuda_inicio)  # Permite consultarla también desde la etiqueta.
        self.casilla_iniciar_maximizado.toggled.connect(self._cambiar_iniciar_maximizado)  # Registra cualquier decisión nueva.

        fila_inicio.addWidget(self.casilla_iniciar_maximizado)  # Coloca primero la casilla.
        fila_inicio.addWidget(self.etiqueta_iniciar_maximizado)  # Coloca después su descripción.
        fila_inicio.addStretch()  # Mantiene el conjunto alineado hacia la izquierda.
        diseno_inicio.addLayout(fila_inicio)  # Incorpora la opción dentro de la tarjeta.
        diseno.addWidget(tarjeta_inicio)  # Añade la tarjeta completa al panel.

        # ====================================================
        # Tarjeta 2: Estado entre sesiones
        # ====================================================

        tarjeta_estado = QFrame()  # Crea la tarjeta dedicada con la recuperación del estado.
        tarjeta_estado.setObjectName("TarjetaConfiguracion")  # Mantiene el mismo diseño visual.
        diseno_estado = QVBoxLayout(tarjeta_estado)  # Organiza título, descripción y opción.
        diseno_estado.setContentsMargins(22, 16, 22, 16)  # Mantiene exactamente el mismo espacio interior.
        diseno_estado.setSpacing(9)  # Conserva una separación uniforme.

        subtitulo_estado = QLabel("Estado entre sesiones")  # Identifica la persistencia del estado de ventana.
        subtitulo_estado.setObjectName("SubtituloConfiguracion")  # Utiliza el estilo de los demás subtítulos.
        subtitulo_estado.setContentsMargins(4, 0, 4, 0)  # Mantiene la misma alineación.
        diseno_estado.addWidget(subtitulo_estado)  # Coloca el encabezado interno.

        descripcion_estado = QLabel("Si se activa, TecNet Finder recordará si estaba maximizado o en modo ventana cuando se cerró y utilizará ese estado la próxima vez.")  # Explica qué estados se conservan entre sesiones.
        descripcion_estado.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_estado.setContentsMargins(4, 2, 4, 2)  # Conserva una separación discreta.
        descripcion_estado.setWordWrap(True)  # Permite mostrar completamente la explicación.
        diseno_estado.addWidget(descripcion_estado)  # Coloca la descripción debajo del subtítulo.

        fila_estado = QHBoxLayout()  # Organiza casilla y descripción sobre una misma línea.
        fila_estado.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación interior.
        fila_estado.setSpacing(9)  # Separa visualmente ambos elementos.

        self.casilla_recordar_estado = BotonCasillaVentana("Recordar el estado de la ventana al cerrar", self)  # Crea la preferencia que conserva maximizado o modo ventana.
        self.etiqueta_recordar_estado = QLabel("Recordar el estado de la ventana al cerrar")  # Presenta el texto correspondiente.
        self.etiqueta_recordar_estado.setObjectName("TextoConfiguracion")  # Reutiliza la apariencia de las opciones.
        self.etiqueta_recordar_estado.setContentsMargins(2, 0, 2, 0)  # Mantiene una separación mínima.
        self.casilla_recordar_estado.setChecked(self.preferencias_aplicacion.recordar_estado_ventana())  # Recupera el valor almacenado actualmente.

        ayuda_estado = "La aplicación recordará únicamente si estaba maximizada o en modo ventana. Media pantalla y pantalla completa continúan siendo estados temporales."  # Explica qué estados no se persisten.
        self.casilla_recordar_estado.setToolTip(ayuda_estado)  # Muestra la explicación sobre el control.
        self.etiqueta_recordar_estado.setToolTip(ayuda_estado)  # Muestra la misma explicación sobre el texto.
        self.casilla_recordar_estado.toggled.connect(self._cambiar_recordar_estado)  # Registra futuras modificaciones.

        fila_estado.addWidget(self.casilla_recordar_estado)  # Coloca la casilla.
        fila_estado.addWidget(self.etiqueta_recordar_estado)  # Coloca su descripción.
        fila_estado.addStretch()  # Mantiene el conjunto alineado a la izquierda.
        diseno_estado.addLayout(fila_estado)  # Incorpora la opción.
        diseno.addWidget(tarjeta_estado)  # Añade la tarjeta completa.

        # ====================================================
        # Tarjeta 3: Ventana de Configuración
        # ====================================================

        tarjeta_configuracion = QFrame()  # Crea una tarjeta relacionada con el propio diálogo de Configuración.
        tarjeta_configuracion.setObjectName("TarjetaConfiguracion")  # Mantiene el mismo diseño exterior.
        diseno_configuracion = QVBoxLayout(tarjeta_configuracion)  # Organiza su contenido.
        diseno_configuracion.setContentsMargins(22, 16, 22, 16)  # Mantiene el mismo padding.
        diseno_configuracion.setSpacing(9)  # Conserva la separación uniforme.

        subtitulo_configuracion = QLabel("Ventana de Configuración")  # Identifica las preferencias correspondientes con este diálogo.
        subtitulo_configuracion.setObjectName("SubtituloConfiguracion")  # Aplica la apariencia de subtítulo.
        subtitulo_configuracion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación.
        diseno_configuracion.addWidget(subtitulo_configuracion)  # Coloca el encabezado interno.

        descripcion_configuracion = QLabel("Permite regresar directamente a la última categoría que estabas consultando cuando vuelvas a abrir Configuración.")  # Explica el beneficio de conservar la sección visitada.
        descripcion_configuracion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_configuracion.setContentsMargins(4, 2, 4, 2)  # Conserva la separación interior.
        descripcion_configuracion.setWordWrap(True)  # Permite ajustar el texto al ancho del panel.
        diseno_configuracion.addWidget(descripcion_configuracion)  # Coloca la explicación.

        fila_configuracion = QHBoxLayout()  # Organiza casilla y descripción.
        fila_configuracion.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación con las demás opciones.
        fila_configuracion.setSpacing(9)  # Separa ambos elementos.

        self.casilla_recordar_seccion = BotonCasillaVentana("Abrir Configuración en la última sección visitada", self)  # Crea la preferencia de recuperación de categoría.
        self.etiqueta_recordar_seccion = QLabel("Abrir Configuración en la última sección visitada")  # Presenta el texto visible.
        self.etiqueta_recordar_seccion.setObjectName("TextoConfiguracion")  # Mantiene el estilo de opción.
        self.etiqueta_recordar_seccion.setContentsMargins(2, 0, 2, 0)  # Conserva separación mínima.
        self.casilla_recordar_seccion.setChecked(self.preferencias_aplicacion.recordar_seccion_configuracion())  # Recupera el valor actual.
        self.casilla_recordar_seccion.toggled.connect(self._cambiar_recordar_seccion)  # Registra futuras modificaciones.

        fila_configuracion.addWidget(self.casilla_recordar_seccion)  # Coloca primero la casilla.
        fila_configuracion.addWidget(self.etiqueta_recordar_seccion)  # Coloca después la descripción.
        fila_configuracion.addStretch()  # Mantiene la opción alineada hacia la izquierda.
        diseno_configuracion.addLayout(fila_configuracion)  # Añade la fila dentro de la tarjeta.
        diseno.addWidget(tarjeta_configuracion)  # Añade la tercera tarjeta completa.

        diseno.addStretch()  # Mantiene todo el contenido agrupado hacia la parte superior.

    # ========================================================
    # Persistencia de las opciones
    # ========================================================

    def _cambiar_iniciar_maximizado(self, activado: bool) -> None:  # Intenta actualizar el comportamiento inicial.
        if self.preferencias_aplicacion.establecer_iniciar_maximizado(activado):  # Comprueba que la preferencia pueda conservarse correctamente.
            return  # Mantiene el nuevo estado cuando la operación fue satisfactoria.

        self._restaurar_casilla(self.casilla_iniciar_maximizado, self.preferencias_aplicacion.iniciar_maximizado())  # Recupera el valor anterior cuando la escritura falla.

    def _cambiar_recordar_estado(self, activado: bool) -> None:  # Intenta actualizar la recuperación del estado entre sesiones.
        if self.preferencias_aplicacion.establecer_recordar_estado_ventana(activado):  # Comprueba que el nuevo valor pueda guardarse.
            return  # Conserva visualmente la decisión realizada.

        self._restaurar_casilla(self.casilla_recordar_estado, self.preferencias_aplicacion.recordar_estado_ventana())  # Recupera el valor realmente almacenado.

    def _cambiar_recordar_seccion(self, activado: bool) -> None:  # Intenta actualizar la recuperación de la última categoría visitada.
        if self.preferencias_aplicacion.establecer_recordar_seccion_configuracion(activado):  # Comprueba que la escritura haya sido satisfactoria.
            return  # Conserva el nuevo valor.

        self._restaurar_casilla(self.casilla_recordar_seccion, self.preferencias_aplicacion.recordar_seccion_configuracion())  # Recupera la preferencia que continúa almacenada.

    def _restaurar_casilla(self, casilla: BotonCasillaVentana, valor: bool) -> None:  # Recupera silenciosamente una casilla cuando no pudo persistirse un cambio.
        casilla.blockSignals(True)  # Evita volver a ejecutar la escritura mientras se restaura.
        casilla.setChecked(bool(valor))  # Recupera el valor que continúa siendo válido.
        casilla.blockSignals(False)  # Reactiva futuras interacciones del usuario.
        casilla._actualizar_apariencia(bool(valor))  # Actualiza manualmente la representación porque las señales estuvieron bloqueadas.