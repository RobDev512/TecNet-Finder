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
# Las opciones utilizan el mismo diseño visual de tarjetas,
# descripciones y casillas utilizado por las demás categorías
# existentes dentro de Configuración.
#
# Estas preferencias solamente modifican la experiencia visual
# de la aplicación y no intervienen en ninguna fase del compilador.
# ============================================================

from PySide6.QtCore import Qt  # Permite configurar el cursor utilizado por las casillas personalizadas.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Importa los controles necesarios para construir esta categoría.

from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Centraliza el almacenamiento persistente de las preferencias generales.


class BotonCasillaVentana(QPushButton):  # Representa una casilla con la misma apariencia utilizada por las demás categorías.
    def __init__(self, nombre_accesible: str, padre=None):
        super().__init__(padre)  # Inicializa el botón que funcionará como control de selección.

        self.setCheckable(
            True
        )  # Permite conservar explícitamente los estados activado y desactivado.

        self.setFixedSize(
            24,
            24,
        )  # Mantiene exactamente las mismas dimensiones utilizadas por las casillas existentes.

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )  # Indica visualmente que el usuario puede pulsar el control.

        self.setAccessibleName(
            nombre_accesible
        )  # Proporciona una descripción útil para herramientas de accesibilidad.

        self.setStyleSheet(
            "padding: 0px; "
            "font-family: 'Segoe UI Symbol'; "
            "font-size: 12pt; "
            "font-weight: bold;"
        )  # Mantiene centrada y claramente visible la marca de verificación.

        self.toggled.connect(
            self._actualizar_apariencia
        )  # Actualiza inmediatamente la apariencia cuando cambia el estado.

        self._actualizar_apariencia(
            False
        )  # Prepara inicialmente la apariencia correspondiente con una casilla desactivada.

    def _actualizar_apariencia(self, activado: bool) -> None:
        self.setText(
            "✓" if activado else ""
        )  # Muestra la marca solamente mientras la opción se encuentra activa.

        self.setObjectName(
            "BotonPrincipal" if activado else "CasillaIA"
        )  # Reutiliza exactamente los estilos azul y oscuro existentes.

        self.style().unpolish(
            self
        )  # Retira temporalmente la apariencia correspondiente con el estado anterior.

        self.style().polish(
            self
        )  # Aplica nuevamente la hoja de estilos utilizando el nuevo estado.

        self.update()  # Solicita el redibujado inmediato del control.


class PanelConfiguracionVentana(QWidget):  # Agrupa las preferencias correspondientes con ventana y comportamiento visual.
    def __init__(
        self,
        preferencias_aplicacion: PreferenciasAplicacion,
        padre=None,
    ):
        super().__init__(padre)  # Vincula el panel con la ventana general de Configuración.

        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva la misma instancia persistente utilizada por toda la aplicación.

        self._construir_interfaz()  # Construye todos los controles y representa los valores actualmente guardados.

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(
            self
        )  # Organiza título, descripción y tarjetas siguiendo exactamente el patrón de las demás categorías.

        diseno.setContentsMargins(
            24,
            22,
            24,
            22,
        )  # Utiliza los mismos márgenes exteriores empleados por Asistencia de IA y Resultados.

        diseno.setSpacing(
            14
        )  # Conserva una separación uniforme entre los distintos grupos.

        # ====================================================
        # Encabezado
        # ====================================================

        titulo = QLabel(
            "Ventana y apariencia"
        )  # Presenta el nombre de la nueva categoría.

        titulo.setObjectName(
            "TituloConfiguracion"
        )  # Reutiliza exactamente el estilo de los demás títulos de Configuración.

        titulo.setContentsMargins(
            4,
            0,
            4,
            0,
        )  # Mantiene una pequeña separación lateral respecto con el área disponible.

        diseno.addWidget(
            titulo
        )  # Coloca el encabezado al principio de la categoría.

        descripcion = QLabel(
            "Personaliza cómo inicia TecNet Finder y qué comportamiento "
            "de la interfaz debe conservar entre ejecuciones."
        )  # Resume el propósito de la categoría sin mezclar preferencias del compilador.

        descripcion.setObjectName(
            "DescripcionConfiguracion"
        )  # Utiliza el mismo estilo secundario de las demás categorías.

        descripcion.setContentsMargins(
            4,
            0,
            4,
            0,
        )  # Mantiene la misma alineación horizontal que el título.

        descripcion.setWordWrap(
            True
        )  # Permite adaptar naturalmente el texto al ancho disponible.

        diseno.addWidget(
            descripcion
        )  # Coloca la explicación debajo del título.

        # ====================================================
        # Tarjeta 1: Inicio de TecNet Finder
        # ====================================================

        tarjeta_inicio = QFrame()  # Crea la superficie correspondiente con el comportamiento inicial.
        tarjeta_inicio.setObjectName(
            "TarjetaConfiguracion"
        )  # Reutiliza exactamente el diseño de las tarjetas existentes.

        diseno_inicio = QVBoxLayout(
            tarjeta_inicio
        )  # Organiza título, descripción y preferencia.

        diseno_inicio.setContentsMargins(
            22,
            16,
            22,
            16,
        )  # Mantiene un espacio interior equivalente al utilizado en Resultados.

        diseno_inicio.setSpacing(
            9
        )  # Conserva próximos todos los elementos pertenecientes con el mismo grupo.

        subtitulo_inicio = QLabel(
            "Inicio de TecNet Finder"
        )  # Identifica la preferencia correspondiente con el primer arranque visual.

        subtitulo_inicio.setObjectName(
            "SubtituloConfiguracion"
        )  # Reutiliza el mismo estilo de subtítulos de Configuración.

        subtitulo_inicio.setContentsMargins(
            4,
            0,
            4,
            0,
        )  # Mantiene la misma alineación horizontal.

        diseno_inicio.addWidget(
            subtitulo_inicio
        )  # Coloca el encabezado interno antes de la descripción.

        descripcion_inicio = QLabel(
            "Define el estado utilizado al abrir TecNet Finder cuando no se "
            "está recuperando un estado anterior."
        )  # Explica cuándo interviene esta preferencia.

        descripcion_inicio.setObjectName(
            "DescripcionConfiguracion"
        )  # Mantiene el estilo secundario común.

        descripcion_inicio.setContentsMargins(
            4,
            2,
            4,
            2,
        )  # Conserva una separación discreta alrededor del texto.

        descripcion_inicio.setWordWrap(
            True
        )  # Permite distribuir correctamente el contenido.

        diseno_inicio.addWidget(
            descripcion_inicio
        )  # Coloca la explicación antes de la opción interactiva.

        fila_inicio = QHBoxLayout()  # Organiza casilla y texto sobre una misma línea.

        fila_inicio.setContentsMargins(
            4,
            2,
            4,
            2,
        )  # Mantiene la misma alineación interior utilizada por las demás opciones.

        fila_inicio.setSpacing(
            9
        )  # Conserva la misma distancia entre casilla y texto utilizada en IA.

        self.casilla_iniciar_maximizado = BotonCasillaVentana(
            "Iniciar TecNet Finder maximizado",
            self,
        )  # Crea la preferencia correspondiente con el estado inicial.

        self.etiqueta_iniciar_maximizado = QLabel(
            "Iniciar TecNet Finder maximizado"
        )  # Presenta independientemente el texto correspondiente con la preferencia.

        self.etiqueta_iniciar_maximizado.setObjectName(
            "TextoConfiguracion"
        )  # Mantiene el estilo tipográfico de las demás opciones.

        self.etiqueta_iniciar_maximizado.setContentsMargins(
            2,
            0,
            2,
            0,
        )  # Conserva una pequeña separación interior.

        self.casilla_iniciar_maximizado.setChecked(
            self.preferencias_aplicacion.iniciar_maximizado()
        )  # Representa inmediatamente la decisión persistente actual.

        ayuda_inicio = (
            "Cuando no exista un estado anterior para recuperar, "
            "TecNet Finder iniciará ocupando toda el área disponible."
        )  # Prepara una explicación común para el control y su etiqueta.

        self.casilla_iniciar_maximizado.setToolTip(
            ayuda_inicio
        )  # Muestra la explicación al señalar directamente la casilla.

        self.etiqueta_iniciar_maximizado.setToolTip(
            ayuda_inicio
        )  # Permite consultar la misma explicación desde el texto.

        self.casilla_iniciar_maximizado.toggled.connect(
            self._cambiar_iniciar_maximizado
        )  # Persiste inmediatamente cualquier modificación realizada por el usuario.

        fila_inicio.addWidget(
            self.casilla_iniciar_maximizado
        )  # Coloca primero la casilla visual.

        fila_inicio.addWidget(
            self.etiqueta_iniciar_maximizado
        )  # Coloca inmediatamente después su descripción.

        fila_inicio.addStretch()  # Mantiene el conjunto completo alineado hacia la izquierda.

        diseno_inicio.addLayout(
            fila_inicio
        )  # Incorpora la preferencia dentro de la tarjeta.

        diseno.addWidget(
            tarjeta_inicio
        )  # Añade la primera tarjeta completa al panel.

        # ====================================================
        # Tarjeta 2: Estado entre sesiones
        # ====================================================

        tarjeta_estado = QFrame()  # Crea la superficie dedicada con la recuperación del estado.
        tarjeta_estado.setObjectName(
            "TarjetaConfiguracion"
        )  # Mantiene el mismo diseño visual general.

        diseno_estado = QVBoxLayout(
            tarjeta_estado
        )  # Organiza título, descripción y opción.

        diseno_estado.setContentsMargins(
            22,
            16,
            22,
            16,
        )  # Mantiene exactamente el mismo espacio interior de la tarjeta anterior.

        diseno_estado.setSpacing(
            9
        )  # Conserva una separación visual uniforme.

        subtitulo_estado = QLabel(
            "Estado entre sesiones"
        )  # Identifica la persistencia del estado maximizado o normal.

        subtitulo_estado.setObjectName(
            "SubtituloConfiguracion"
        )  # Utiliza el mismo estilo del resto de subtítulos.

        subtitulo_estado.setContentsMargins(
            4,
            0,
            4,
            0,
        )

        diseno_estado.addWidget(
            subtitulo_estado
        )

        descripcion_estado = QLabel(
            "Si se activa, TecNet Finder recordará si estaba maximizado o "
            "en modo ventana cuando se cerró y utilizará ese estado la próxima vez."
        )  # Explica claramente que Media pantalla y fullscreen no se conservan como modos iniciales.

        descripcion_estado.setObjectName(
            "DescripcionConfiguracion"
        )

        descripcion_estado.setContentsMargins(
            4,
            2,
            4,
            2,
        )

        descripcion_estado.setWordWrap(
            True
        )

        diseno_estado.addWidget(
            descripcion_estado
        )

        fila_estado = QHBoxLayout()
        fila_estado.setContentsMargins(
            4,
            2,
            4,
            2,
        )
        fila_estado.setSpacing(
            9
        )

        self.casilla_recordar_estado = BotonCasillaVentana(
            "Recordar el estado de la ventana al cerrar",
            self,
        )  # Crea la preferencia encargada de conservar maximizado o modo ventana.

        self.etiqueta_recordar_estado = QLabel(
            "Recordar el estado de la ventana al cerrar"
        )

        self.etiqueta_recordar_estado.setObjectName(
            "TextoConfiguracion"
        )

        self.etiqueta_recordar_estado.setContentsMargins(
            2,
            0,
            2,
            0,
        )

        self.casilla_recordar_estado.setChecked(
            self.preferencias_aplicacion.recordar_estado_ventana()
        )  # Recupera el estado almacenado actualmente.

        ayuda_estado = (
            "La aplicación recordará únicamente si estaba maximizada o en modo ventana. "
            "Media pantalla y pantalla completa continúan siendo estados temporales."
        )

        self.casilla_recordar_estado.setToolTip(
            ayuda_estado
        )

        self.etiqueta_recordar_estado.setToolTip(
            ayuda_estado
        )

        self.casilla_recordar_estado.toggled.connect(
            self._cambiar_recordar_estado
        )

        fila_estado.addWidget(
            self.casilla_recordar_estado
        )

        fila_estado.addWidget(
            self.etiqueta_recordar_estado
        )

        fila_estado.addStretch()

        diseno_estado.addLayout(
            fila_estado
        )

        diseno.addWidget(
            tarjeta_estado
        )

        # ====================================================
        # Tarjeta 3: Configuración
        # ====================================================

        tarjeta_configuracion = QFrame()  # Crea una tercera tarjeta relacionada con la propia ventana de Configuración.
        tarjeta_configuracion.setObjectName(
            "TarjetaConfiguracion"
        )

        diseno_configuracion = QVBoxLayout(
            tarjeta_configuracion
        )

        diseno_configuracion.setContentsMargins(
            22,
            16,
            22,
            16,
        )

        diseno_configuracion.setSpacing(
            9
        )

        subtitulo_configuracion = QLabel(
            "Ventana de Configuración"
        )  # Identifica las preferencias correspondientes con este diálogo.

        subtitulo_configuracion.setObjectName(
            "SubtituloConfiguracion"
        )

        subtitulo_configuracion.setContentsMargins(
            4,
            0,
            4,
            0,
        )

        diseno_configuracion.addWidget(
            subtitulo_configuracion
        )

        descripcion_configuracion = QLabel(
            "Permite regresar directamente a la última categoría que estabas "
            "consultando cuando vuelvas a abrir Configuración."
        )  # Explica el beneficio de conservar la categoría visitada.

        descripcion_configuracion.setObjectName(
            "DescripcionConfiguracion"
        )

        descripcion_configuracion.setContentsMargins(
            4,
            2,
            4,
            2,
        )

        descripcion_configuracion.setWordWrap(
            True
        )

        diseno_configuracion.addWidget(
            descripcion_configuracion
        )

        fila_configuracion = QHBoxLayout()
        fila_configuracion.setContentsMargins(
            4,
            2,
            4,
            2,
        )
        fila_configuracion.setSpacing(
            9
        )

        self.casilla_recordar_seccion = BotonCasillaVentana(
            "Abrir Configuración en la última sección visitada",
            self,
        )

        self.etiqueta_recordar_seccion = QLabel(
            "Abrir Configuración en la última sección visitada"
        )

        self.etiqueta_recordar_seccion.setObjectName(
            "TextoConfiguracion"
        )

        self.etiqueta_recordar_seccion.setContentsMargins(
            2,
            0,
            2,
            0,
        )

        self.casilla_recordar_seccion.setChecked(
            self.preferencias_aplicacion.recordar_seccion_configuracion()
        )

        self.casilla_recordar_seccion.toggled.connect(
            self._cambiar_recordar_seccion
        )

        fila_configuracion.addWidget(
            self.casilla_recordar_seccion
        )

        fila_configuracion.addWidget(
            self.etiqueta_recordar_seccion
        )

        fila_configuracion.addStretch()

        diseno_configuracion.addLayout(
            fila_configuracion
        )

        diseno.addWidget(
            tarjeta_configuracion
        )

        diseno.addStretch()  # Mantiene todas las tarjetas agrupadas hacia la zona superior.

    # ========================================================
    # Persistencia de las opciones
    # ========================================================

    def _cambiar_iniciar_maximizado(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_iniciar_maximizado(
            activado
        ):
            return  # Mantiene el nuevo estado cuando pudo guardarse correctamente.

        self._restaurar_casilla(
            self.casilla_iniciar_maximizado,
            self.preferencias_aplicacion.iniciar_maximizado(),
        )  # Recupera visualmente la decisión almacenada si la escritura falla.

    def _cambiar_recordar_estado(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_recordar_estado_ventana(
            activado
        ):
            return  # Conserva la decisión cuando pudo persistirse correctamente.

        self._restaurar_casilla(
            self.casilla_recordar_estado,
            self.preferencias_aplicacion.recordar_estado_ventana(),
        )

    def _cambiar_recordar_seccion(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_recordar_seccion_configuracion(
            activado
        ):
            return

        self._restaurar_casilla(
            self.casilla_recordar_seccion,
            self.preferencias_aplicacion.recordar_seccion_configuracion(),
        )

    def _restaurar_casilla(
        self,
        casilla: BotonCasillaVentana,
        valor: bool,
    ) -> None:
        casilla.blockSignals(
            True
        )  # Evita volver a ejecutar la escritura al recuperar el estado persistido.

        casilla.setChecked(
            bool(valor)
        )  # Recupera el valor que realmente continúa almacenado.

        casilla.blockSignals(
            False
        )  # Reactiva las futuras decisiones realizadas por el usuario.

        casilla._actualizar_apariencia(
            bool(valor)
        )  # Actualiza manualmente la marca porque las señales permanecieron bloqueadas.