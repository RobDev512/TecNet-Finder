# ============================================================
# Archivo: panel_configuracion_resultados.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las preferencias relacionadas con la
# navegación posterior a la compilación y con la presentación
# de las advertencias dentro de TecNet Finder.
#
# La categoría se organiza en tres grupos:
#
# - Navegación después de compilar.
# - Presentación de advertencias.
# - Interacción con advertencias.
#
# Las dos modalidades de presentación de advertencias son
# mutuamente excluyentes, aunque ambas pueden permanecer apagadas.
#
# Las opciones utilizan el mismo diseño de casilla personalizada
# empleado dentro de Asistencia de IA.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Permite manejar señales y configurar el cursor de las casillas personalizadas.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Importa los controles utilizados para construir esta categoría.

from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Centraliza la persistencia de las preferencias generales.


class BotonCasillaConfiguracion(QPushButton):  # Representa una casilla con la misma apariencia utilizada por Asistencia de IA.
    def __init__(self, nombre_accesible: str, padre=None):
        super().__init__(padre)  # Inicializa el botón que funcionará como control de selección.

        self.setCheckable(True)  # Permite conservar explícitamente los estados activado y desactivado.
        self.setFixedSize(24, 24)  # Utiliza exactamente el mismo tamaño de las casillas de IA.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el control puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Proporciona una descripción para herramientas de accesibilidad.

        self.setStyleSheet(
            "padding: 0px; "
            "font-family: 'Segoe UI Symbol'; "
            "font-size: 12pt; "
            "font-weight: bold;"
        )  # Mantiene centrada y claramente visible la marca.

        self.toggled.connect(
            self._actualizar_apariencia
        )  # Actualiza inmediatamente la representación visual.

        self._actualizar_apariencia(False)  # Prepara inicialmente una casilla desactivada.

    def _actualizar_apariencia(self, activado: bool) -> None:
        self.setText(
            "✓" if activado else ""
        )  # Muestra la marca únicamente cuando la opción se encuentra activa.

        self.setObjectName(
            "BotonPrincipal" if activado else "CasillaIA"
        )  # Reutiliza los mismos estilos empleados por las casillas de IA.

        self.style().unpolish(self)  # Retira temporalmente la apariencia anterior.
        self.style().polish(self)  # Aplica nuevamente los estilos utilizando el nuevo estado.
        self.update()  # Solicita el redibujado inmediato.


class PanelConfiguracionResultados(QWidget):  # Agrupa las preferencias relacionadas con navegación y presentación de resultados.
    navegacion_errores_cambiada = Signal(bool)  # Informa que cambió la navegación automática hacia errores.
    navegacion_vlsm_cambiada = Signal(bool)  # Informa que cambió la navegación automática hacia Tabla VLSM.

    advertencias_vlsm_cambiadas = Signal(bool)  # Informa que cambió la visibilidad del panel compacto.
    advertencias_ventana_cambiadas = Signal(bool)  # Informa que cambió la modalidad de ventana independiente.

    cerrar_ventana_al_navegar_cambiado = Signal(bool)  # Informa qué debe suceder al abrir una advertencia en el editor.

    def __init__(
        self,
        preferencias_aplicacion: PreferenciasAplicacion,
        padre=None,
    ):
        super().__init__(padre)  # Vincula el panel con la ventana general de Configuración.

        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva el administrador persistente compartido.
        self.actualizando_advertencias = False  # Evita interpretar sincronizaciones internas como decisiones nuevas.

        self._construir_interfaz()  # Construye todos los controles y refleja las preferencias guardadas.

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)  # Organiza verticalmente encabezado y tarjetas igual que Asistencia de IA.
        diseno.setContentsMargins(24, 22, 24, 22)  # Utiliza los mismos márgenes exteriores del panel de IA.
        diseno.setSpacing(14)  # Mantiene una separación uniforme entre grupos.

        titulo = QLabel("Resultados y navegación")  # Presenta el nombre de la categoría.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el estilo general de Configuración.
        titulo.setContentsMargins(4, 0, 4, 0)  # Separa visualmente el texto de los límites.
        diseno.addWidget(titulo)  # Coloca el título al principio.

        descripcion = QLabel(
            "Personaliza qué muestra TecNet Finder después de compilar "
            "y cómo presenta e interactúa con las advertencias."
        )  # Resume el alcance de esta categoría.
        descripcion.setObjectName("DescripcionConfiguracion")  # Utiliza el estilo secundario común.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Mantiene respiración lateral.
        descripcion.setWordWrap(True)  # Adapta el contenido al ancho disponible.
        diseno.addWidget(descripcion)  # Coloca la explicación debajo del título.

        # ====================================================
        # Tarjeta 1: Navegación después de compilar
        # ====================================================

        panel_navegacion = QFrame()  # Crea la tarjeta dedicada con la navegación.
        panel_navegacion.setObjectName("TarjetaConfiguracion")  # Reutiliza la apariencia común.

        diseno_navegacion = QVBoxLayout(panel_navegacion)  # Organiza título, descripción y opciones.
        diseno_navegacion.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding uniforme.
        diseno_navegacion.setSpacing(9)  # Conserva las opciones relacionadas próximas.

        subtitulo_navegacion = QLabel("Navegación después de compilar")  # Identifica la primera tarjeta.
        subtitulo_navegacion.setObjectName("SubtituloConfiguracion")  # Aplica el estilo común.
        subtitulo_navegacion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación.
        diseno_navegacion.addWidget(subtitulo_navegacion)  # Coloca el encabezado.

        descripcion_navegacion = QLabel(
            "Decide de forma independiente cuándo TecNet Finder debe cambiar "
            "automáticamente la vista después de una compilación."
        )  # Explica por qué existen dos decisiones separadas.
        descripcion_navegacion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_navegacion.setContentsMargins(4, 2, 4, 2)  # Añade respiración interior.
        descripcion_navegacion.setWordWrap(True)  # Permite varias líneas.
        diseno_navegacion.addWidget(descripcion_navegacion)  # Coloca la explicación.

        # ----------------------------------------------------
        # Navegación hacia errores
        # ----------------------------------------------------

        fila_errores = QHBoxLayout()  # Organiza casilla y texto.
        fila_errores.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación utilizada por IA.
        fila_errores.setSpacing(9)  # Conserva una separación uniforme.

        self.casilla_navegacion_errores = BotonCasillaConfiguracion(
            "Ir automáticamente a Errores / Advertencias cuando existan errores",
            self,
        )  # Crea la preferencia dedicada con los resultados incorrectos.

        self.etiqueta_navegacion_errores = QLabel(
            "Ir automáticamente a Errores / Advertencias cuando existan errores"
        )  # Presenta el texto independiente de la casilla.
        self.etiqueta_navegacion_errores.setObjectName("TextoConfiguracion")
        self.etiqueta_navegacion_errores.setContentsMargins(2, 0, 2, 0)

        self.casilla_navegacion_errores.setChecked(
            self.preferencias_aplicacion.navegacion_errores_activada()
        )  # Recupera la preferencia persistente.

        self.casilla_navegacion_errores.toggled.connect(
            self._cambiar_navegacion_errores
        )  # Guarda cualquier cambio realizado por el usuario.

        fila_errores.addWidget(self.casilla_navegacion_errores)
        fila_errores.addWidget(self.etiqueta_navegacion_errores)
        fila_errores.addStretch()

        diseno_navegacion.addLayout(fila_errores)

        # ----------------------------------------------------
        # Navegación hacia VLSM
        # ----------------------------------------------------

        fila_vlsm = QHBoxLayout()  # Organiza la segunda preferencia.
        fila_vlsm.setContentsMargins(4, 2, 4, 2)
        fila_vlsm.setSpacing(9)

        self.casilla_navegacion_vlsm = BotonCasillaConfiguracion(
            "Ir automáticamente a Tabla VLSM cuando se generen subredes válidas",
            self,
        )  # Crea la preferencia dedicada con una compilación válida.

        self.etiqueta_navegacion_vlsm = QLabel(
            "Ir automáticamente a Tabla VLSM cuando se generen subredes válidas"
        )
        self.etiqueta_navegacion_vlsm.setObjectName("TextoConfiguracion")
        self.etiqueta_navegacion_vlsm.setContentsMargins(2, 0, 2, 0)

        self.casilla_navegacion_vlsm.setChecked(
            self.preferencias_aplicacion.navegacion_vlsm_activada()
        )  # Recupera la preferencia persistente.

        self.casilla_navegacion_vlsm.toggled.connect(
            self._cambiar_navegacion_vlsm
        )  # Guarda cualquier decisión nueva.

        fila_vlsm.addWidget(self.casilla_navegacion_vlsm)
        fila_vlsm.addWidget(self.etiqueta_navegacion_vlsm)
        fila_vlsm.addStretch()

        diseno_navegacion.addLayout(fila_vlsm)

        diseno.addWidget(panel_navegacion)

        # ====================================================
        # Tarjeta 2: Presentación de advertencias
        # ====================================================

        panel_advertencias = QFrame()
        panel_advertencias.setObjectName("TarjetaConfiguracion")

        diseno_advertencias = QVBoxLayout(panel_advertencias)
        diseno_advertencias.setContentsMargins(22, 16, 22, 16)
        diseno_advertencias.setSpacing(9)

        subtitulo_advertencias = QLabel("Presentación de advertencias")
        subtitulo_advertencias.setObjectName("SubtituloConfiguracion")
        subtitulo_advertencias.setContentsMargins(4, 0, 4, 0)
        diseno_advertencias.addWidget(subtitulo_advertencias)

        descripcion_advertencias = QLabel(
            "Elige cómo mostrar las advertencias de una compilación válida. "
            "Activar una modalidad desactiva automáticamente la otra."
        )
        descripcion_advertencias.setObjectName("DescripcionConfiguracion")
        descripcion_advertencias.setContentsMargins(4, 2, 4, 2)
        descripcion_advertencias.setWordWrap(True)
        diseno_advertencias.addWidget(descripcion_advertencias)

        # ----------------------------------------------------
        # Panel debajo de Tabla VLSM
        # ----------------------------------------------------

        fila_advertencias_vlsm = QHBoxLayout()
        fila_advertencias_vlsm.setContentsMargins(4, 2, 4, 2)
        fila_advertencias_vlsm.setSpacing(9)

        self.casilla_advertencias = BotonCasillaConfiguracion(
            "Mostrar advertencias debajo de Tabla VLSM",
            self,
        )

        self.etiqueta_advertencias = QLabel(
            "Mostrar advertencias debajo de Tabla VLSM"
        )
        self.etiqueta_advertencias.setObjectName("TextoConfiguracion")
        self.etiqueta_advertencias.setContentsMargins(2, 0, 2, 0)

        self.casilla_advertencias.setChecked(
            self.preferencias_aplicacion.advertencias_vlsm_visibles()
        )

        self.casilla_advertencias.toggled.connect(
            self._cambiar_advertencias_vlsm
        )

        fila_advertencias_vlsm.addWidget(self.casilla_advertencias)
        fila_advertencias_vlsm.addWidget(self.etiqueta_advertencias)
        fila_advertencias_vlsm.addStretch()

        diseno_advertencias.addLayout(fila_advertencias_vlsm)

        # ----------------------------------------------------
        # Ventana independiente
        # ----------------------------------------------------

        fila_advertencias_ventana = QHBoxLayout()
        fila_advertencias_ventana.setContentsMargins(4, 2, 4, 2)
        fila_advertencias_ventana.setSpacing(9)

        self.casilla_advertencias_ventana = BotonCasillaConfiguracion(
            "Mostrar advertencias en una ventana independiente",
            self,
        )

        self.etiqueta_advertencias_ventana = QLabel(
            "Mostrar advertencias en una ventana independiente"
        )
        self.etiqueta_advertencias_ventana.setObjectName("TextoConfiguracion")
        self.etiqueta_advertencias_ventana.setContentsMargins(2, 0, 2, 0)

        self.casilla_advertencias_ventana.setChecked(
            self.preferencias_aplicacion.advertencias_ventana_independiente()
        )

        self.casilla_advertencias_ventana.toggled.connect(
            self._cambiar_advertencias_ventana
        )

        fila_advertencias_ventana.addWidget(self.casilla_advertencias_ventana)
        fila_advertencias_ventana.addWidget(self.etiqueta_advertencias_ventana)
        fila_advertencias_ventana.addStretch()

        diseno_advertencias.addLayout(fila_advertencias_ventana)

        diseno.addWidget(panel_advertencias)

        # ====================================================
        # Tarjeta 3: Interacción con advertencias
        # ====================================================

        panel_interaccion = QFrame()
        panel_interaccion.setObjectName("TarjetaConfiguracion")

        diseno_interaccion = QVBoxLayout(panel_interaccion)
        diseno_interaccion.setContentsMargins(22, 16, 22, 16)
        diseno_interaccion.setSpacing(9)

        subtitulo_interaccion = QLabel("Interacción con advertencias")
        subtitulo_interaccion.setObjectName("SubtituloConfiguracion")
        subtitulo_interaccion.setContentsMargins(4, 0, 4, 0)
        diseno_interaccion.addWidget(subtitulo_interaccion)

        descripcion_interaccion = QLabel(
            "En la ventana independiente puedes hacer doble clic sobre una "
            "advertencia para ir directamente a su ubicación en el código."
        )
        descripcion_interaccion.setObjectName("DescripcionConfiguracion")
        descripcion_interaccion.setContentsMargins(4, 2, 4, 2)
        descripcion_interaccion.setWordWrap(True)
        diseno_interaccion.addWidget(descripcion_interaccion)

        fila_cerrar = QHBoxLayout()
        fila_cerrar.setContentsMargins(4, 2, 4, 2)
        fila_cerrar.setSpacing(9)

        self.casilla_cerrar_ventana = BotonCasillaConfiguracion(
            "Cerrar la ventana de advertencias al ir al código",
            self,
        )

        self.etiqueta_cerrar_ventana = QLabel(
            "Cerrar la ventana de advertencias al ir al código"
        )
        self.etiqueta_cerrar_ventana.setObjectName("TextoConfiguracion")
        self.etiqueta_cerrar_ventana.setContentsMargins(2, 0, 2, 0)

        self.casilla_cerrar_ventana.setChecked(
            self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar()
        )

        self.casilla_cerrar_ventana.toggled.connect(
            self._cambiar_cerrar_ventana_al_navegar
        )

        fila_cerrar.addWidget(self.casilla_cerrar_ventana)
        fila_cerrar.addWidget(self.etiqueta_cerrar_ventana)
        fila_cerrar.addStretch()

        diseno_interaccion.addLayout(fila_cerrar)

        diseno.addWidget(panel_interaccion)

        self._actualizar_disponibilidad_interaccion()  # Refleja si esta configuración puede utilizarse actualmente.
        diseno.addStretch()  # Mantiene todo el contenido agrupado hacia arriba.

    # ========================================================
    # Navegación
    # ========================================================

    def _cambiar_navegacion_errores(self, activada: bool) -> None:
        if self.preferencias_aplicacion.establecer_navegacion_errores_activada(
            activada
        ):
            self.navegacion_errores_cambiada.emit(
                bool(activada)
            )  # Comunica el nuevo comportamiento después de guardarlo.

            return

        self._restaurar_casilla(
            self.casilla_navegacion_errores,
            self.preferencias_aplicacion.navegacion_errores_activada(),
        )  # Recupera el estado persistido cuando la escritura falla.

    def _cambiar_navegacion_vlsm(self, activada: bool) -> None:
        if self.preferencias_aplicacion.establecer_navegacion_vlsm_activada(
            activada
        ):
            self.navegacion_vlsm_cambiada.emit(
                bool(activada)
            )

            return

        self._restaurar_casilla(
            self.casilla_navegacion_vlsm,
            self.preferencias_aplicacion.navegacion_vlsm_activada(),
        )

    # ========================================================
    # Presentación de advertencias
    # ========================================================

    def _cambiar_advertencias_vlsm(self, visibles: bool) -> None:
        if self.actualizando_advertencias:
            return  # Ignora las sincronizaciones internas.

        if not self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(
            visibles
        ):
            self._restaurar_advertencias_guardadas()
            return

        if visibles:
            self.actualizando_advertencias = True

            self._establecer_casilla_sin_emitir(
                self.casilla_advertencias_ventana,
                False,
            )  # Desactiva visualmente la otra modalidad.

            self.actualizando_advertencias = False

            self.advertencias_ventana_cambiadas.emit(
                False
            )  # Solicita cerrar cualquier ventana independiente activa.

        self.advertencias_vlsm_cambiadas.emit(
            bool(visibles)
        )

        self._actualizar_disponibilidad_interaccion()  # Actualiza el tercer bloque según la modalidad actual.

    def _cambiar_advertencias_ventana(self, visibles: bool) -> None:
        if self.actualizando_advertencias:
            return

        if not self.preferencias_aplicacion.establecer_advertencias_ventana_independiente(
            visibles
        ):
            self._restaurar_advertencias_guardadas()
            return

        if visibles:
            self.actualizando_advertencias = True

            self._establecer_casilla_sin_emitir(
                self.casilla_advertencias,
                False,
            )  # Desactiva visualmente el panel inferior de VLSM.

            self.actualizando_advertencias = False

            self.advertencias_vlsm_cambiadas.emit(
                False
            )  # Oculta inmediatamente cualquier panel compacto visible.

        self.advertencias_ventana_cambiadas.emit(
            bool(visibles)
        )

        self._actualizar_disponibilidad_interaccion()  # Activa o desactiva visualmente la tercera configuración.

    # ========================================================
    # Interacción con advertencias
    # ========================================================

    def _cambiar_cerrar_ventana_al_navegar(self, cerrar: bool) -> None:
        if self.preferencias_aplicacion.establecer_cerrar_ventana_advertencias_al_navegar(
            cerrar
        ):
            self.cerrar_ventana_al_navegar_cambiado.emit(
                bool(cerrar)
            )

            return

        self._restaurar_casilla(
            self.casilla_cerrar_ventana,
            self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar(),
        )

    def _actualizar_disponibilidad_interaccion(self) -> None:
        disponible = self.casilla_advertencias_ventana.isChecked()  # Esta decisión solamente tiene sentido con la ventana independiente habilitada.

        self.casilla_cerrar_ventana.setEnabled(
            disponible
        )  # Impide modificar una preferencia temporalmente irrelevante.

        self.etiqueta_cerrar_ventana.setEnabled(
            disponible
        )  # Mantiene el texto visualmente sincronizado.

    # ========================================================
    # Utilidades visuales
    # ========================================================

    def _establecer_casilla_sin_emitir(
        self,
        casilla: BotonCasillaConfiguracion,
        activada: bool,
    ) -> None:
        casilla.blockSignals(True)
        casilla.setChecked(bool(activada))
        casilla.blockSignals(False)

        casilla._actualizar_apariencia(
            bool(activada)
        )  # Actualiza manualmente la apariencia porque las señales permanecieron bloqueadas.

    def _restaurar_casilla(
        self,
        casilla: BotonCasillaConfiguracion,
        valor: bool,
    ) -> None:
        self._establecer_casilla_sin_emitir(
            casilla,
            valor,
        )  # Reutiliza la sincronización silenciosa.

    def _restaurar_advertencias_guardadas(self) -> None:
        self.actualizando_advertencias = True

        self._establecer_casilla_sin_emitir(
            self.casilla_advertencias,
            self.preferencias_aplicacion.advertencias_vlsm_visibles(),
        )

        self._establecer_casilla_sin_emitir(
            self.casilla_advertencias_ventana,
            self.preferencias_aplicacion.advertencias_ventana_independiente(),
        )

        self.actualizando_advertencias = False

        self._actualizar_disponibilidad_interaccion()