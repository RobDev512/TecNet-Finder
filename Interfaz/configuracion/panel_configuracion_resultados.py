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
# ============================================================

from PySide6.QtCore import Qt, Signal  # Permite manejar señales y configurar el cursor de las casillas personalizadas.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Proporciona los controles utilizados por esta categoría.

from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona la interfaz utilizada para consultar y modificar estas preferencias.


class BotonCasillaConfiguracion(QPushButton):  # Representa una casilla con la misma apariencia utilizada por las demás categorías.
    def __init__(self, nombre_accesible: str, padre=None):  # Recibe una descripción accesible y un posible panel propietario.
        super().__init__(padre)  # Inicializa el botón utilizado como control de selección.
        self.setCheckable(True)  # Permite conservar los estados activado y desactivado.
        self.setFixedSize(24, 24)  # Utiliza las mismas dimensiones de las demás casillas.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el control puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Proporciona una descripción para herramientas de accesibilidad.
        self.setStyleSheet("padding: 0px; font-family: 'Segoe UI Symbol'; font-size: 12pt; font-weight: bold;")  # Mantiene centrada y claramente visible la marca.
        self.toggled.connect(self._actualizar_apariencia)  # Actualiza inmediatamente la representación visual.
        self._actualizar_apariencia(False)  # Prepara inicialmente una casilla desactivada.

    def _actualizar_apariencia(self, activado: bool) -> None:  # Sincroniza marca y estilo con el estado actual.
        self.setText("✓" if activado else "")  # Muestra la marca únicamente cuando la opción está activa.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Reutiliza los estilos azul y oscuro existentes.
        self.style().unpolish(self)  # Retira temporalmente la apariencia anterior.
        self.style().polish(self)  # Aplica nuevamente los estilos utilizando el nuevo estado.
        self.update()  # Solicita el redibujado inmediato.


class PanelConfiguracionResultados(QWidget):  # Agrupa las preferencias relacionadas con navegación y presentación de resultados.
    navegacion_errores_cambiada = Signal(bool)  # Comunica cambios efectivos en la navegación automática hacia errores.
    navegacion_vlsm_cambiada = Signal(bool)  # Comunica cambios efectivos en la navegación automática hacia Tabla VLSM.
    advertencias_vlsm_cambiadas = Signal(bool)  # Comunica cambios en la modalidad compacta de advertencias.
    advertencias_ventana_cambiadas = Signal(bool)  # Comunica cambios en la modalidad de ventana independiente.
    cerrar_ventana_al_navegar_cambiado = Signal(bool)  # Comunica qué debe ocurrir al abrir una advertencia en el editor.

    def __init__(self, preferencias_aplicacion: PreferenciasAplicacion, padre=None):  # Recibe las preferencias compartidas por la ventana general.
        super().__init__(padre)  # Vincula este panel con Configuración.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva el administrador utilizado durante esta sesión.
        self.actualizando_advertencias = False  # Distingue una decisión del usuario de una sincronización interna.
        self._construir_interfaz()  # Construye los controles reflejando los valores actuales.

    def _construir_interfaz(self) -> None:  # Construye las tres tarjetas correspondientes con navegación y advertencias.
        diseno = QVBoxLayout(self)  # Organiza verticalmente encabezado y tarjetas.
        diseno.setContentsMargins(24, 22, 24, 22)  # Utiliza los mismos márgenes exteriores de las demás categorías.
        diseno.setSpacing(14)  # Mantiene una separación uniforme entre grupos.

        titulo = QLabel("Resultados y navegación")  # Presenta el nombre de la categoría.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el estilo general de Configuración.
        titulo.setContentsMargins(4, 0, 4, 0)  # Mantiene una pequeña separación lateral.
        diseno.addWidget(titulo)  # Coloca el título como primer elemento.

        descripcion = QLabel("Personaliza qué muestra TecNet Finder después de compilar y cómo presenta e interactúa con las advertencias.")  # Resume el alcance de la categoría.
        descripcion.setObjectName("DescripcionConfiguracion")  # Utiliza el estilo secundario común.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación horizontal.
        descripcion.setWordWrap(True)  # Permite adaptar el contenido al ancho.
        diseno.addWidget(descripcion)  # Coloca la explicación debajo del título.

        # ====================================================
        # Tarjeta 1: Navegación después de compilar
        # ====================================================

        panel_navegacion = QFrame()  # Crea la tarjeta dedicada con la navegación.
        panel_navegacion.setObjectName("TarjetaConfiguracion")  # Reutiliza la apariencia común.
        diseno_navegacion = QVBoxLayout(panel_navegacion)  # Organiza título, descripción y opciones.
        diseno_navegacion.setContentsMargins(22, 16, 22, 16)  # Mantiene el padding uniforme.
        diseno_navegacion.setSpacing(9)  # Conserva próximas las opciones relacionadas.

        subtitulo_navegacion = QLabel("Navegación después de compilar")  # Identifica la primera tarjeta.
        subtitulo_navegacion.setObjectName("SubtituloConfiguracion")  # Aplica el estilo común.
        subtitulo_navegacion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación interna.
        diseno_navegacion.addWidget(subtitulo_navegacion)  # Coloca el encabezado.

        descripcion_navegacion = QLabel("Decide de forma independiente cuándo TecNet Finder debe cambiar automáticamente la vista después de una compilación.")  # Explica por qué existen dos decisiones separadas.
        descripcion_navegacion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_navegacion.setContentsMargins(4, 2, 4, 2)  # Añade una pequeña separación interior.
        descripcion_navegacion.setWordWrap(True)  # Permite varias líneas.
        diseno_navegacion.addWidget(descripcion_navegacion)  # Coloca la explicación.

        fila_errores = QHBoxLayout()  # Organiza la preferencia correspondiente con diagnósticos de error.
        fila_errores.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación de las opciones.
        fila_errores.setSpacing(9)  # Separa casilla y texto.
        self.casilla_navegacion_errores = BotonCasillaConfiguracion("Ir automáticamente a Errores / Advertencias cuando existan errores", self)  # Crea la preferencia de navegación hacia errores.
        self.etiqueta_navegacion_errores = QLabel("Ir automáticamente a Errores / Advertencias cuando existan errores")  # Presenta su descripción visible.
        self.etiqueta_navegacion_errores.setObjectName("TextoConfiguracion")  # Utiliza el estilo de opciones.
        self.etiqueta_navegacion_errores.setContentsMargins(2, 0, 2, 0)  # Mantiene una separación mínima.
        self.casilla_navegacion_errores.setChecked(self.preferencias_aplicacion.navegacion_errores_activada())  # Recupera el valor actual.
        self.casilla_navegacion_errores.toggled.connect(self._cambiar_navegacion_errores)  # Registra cualquier modificación.
        fila_errores.addWidget(self.casilla_navegacion_errores)  # Coloca la casilla.
        fila_errores.addWidget(self.etiqueta_navegacion_errores)  # Coloca después el texto.
        fila_errores.addStretch()  # Mantiene el conjunto alineado a la izquierda.
        diseno_navegacion.addLayout(fila_errores)  # Incorpora la primera preferencia.

        fila_vlsm = QHBoxLayout()  # Organiza la preferencia correspondiente con resultados VLSM.
        fila_vlsm.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación.
        fila_vlsm.setSpacing(9)  # Separa casilla y texto.
        self.casilla_navegacion_vlsm = BotonCasillaConfiguracion("Ir automáticamente a Tabla VLSM cuando se generen subredes válidas", self)  # Crea la navegación automática hacia resultados válidos.
        self.etiqueta_navegacion_vlsm = QLabel("Ir automáticamente a Tabla VLSM cuando se generen subredes válidas")  # Presenta el nombre de la opción.
        self.etiqueta_navegacion_vlsm.setObjectName("TextoConfiguracion")  # Utiliza el estilo común.
        self.etiqueta_navegacion_vlsm.setContentsMargins(2, 0, 2, 0)  # Conserva separación mínima.
        self.casilla_navegacion_vlsm.setChecked(self.preferencias_aplicacion.navegacion_vlsm_activada())  # Recupera la preferencia actual.
        self.casilla_navegacion_vlsm.toggled.connect(self._cambiar_navegacion_vlsm)  # Registra cualquier decisión nueva.
        fila_vlsm.addWidget(self.casilla_navegacion_vlsm)  # Coloca la casilla.
        fila_vlsm.addWidget(self.etiqueta_navegacion_vlsm)  # Coloca su descripción.
        fila_vlsm.addStretch()  # Mantiene la opción alineada a la izquierda.
        diseno_navegacion.addLayout(fila_vlsm)  # Incorpora la segunda preferencia.

        diseno.addWidget(panel_navegacion)  # Añade la primera tarjeta completa.

        # ====================================================
        # Tarjeta 2: Presentación de advertencias
        # ====================================================

        panel_advertencias = QFrame()  # Crea la tarjeta correspondiente con las dos modalidades de advertencia.
        panel_advertencias.setObjectName("TarjetaConfiguracion")  # Reutiliza la apariencia de las demás tarjetas.
        diseno_advertencias = QVBoxLayout(panel_advertencias)  # Organiza título, descripción y ambas modalidades.
        diseno_advertencias.setContentsMargins(22, 16, 22, 16)  # Mantiene el mismo padding.
        diseno_advertencias.setSpacing(9)  # Conserva una separación uniforme.

        subtitulo_advertencias = QLabel("Presentación de advertencias")  # Identifica la segunda tarjeta.
        subtitulo_advertencias.setObjectName("SubtituloConfiguracion")  # Aplica el estilo correspondiente.
        subtitulo_advertencias.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación interior.
        diseno_advertencias.addWidget(subtitulo_advertencias)  # Coloca el encabezado.

        descripcion_advertencias = QLabel("Elige cómo mostrar las advertencias de una compilación válida. Activar una modalidad desactiva automáticamente la otra.")  # Explica la exclusión entre las dos presentaciones.
        descripcion_advertencias.setObjectName("DescripcionConfiguracion")  # Mantiene la apariencia secundaria.
        descripcion_advertencias.setContentsMargins(4, 2, 4, 2)  # Conserva una pequeña separación.
        descripcion_advertencias.setWordWrap(True)  # Permite adaptar el contenido.
        diseno_advertencias.addWidget(descripcion_advertencias)  # Coloca la explicación.

        fila_advertencias_vlsm = QHBoxLayout()  # Organiza la modalidad compacta debajo de Tabla VLSM.
        fila_advertencias_vlsm.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación de la tarjeta.
        fila_advertencias_vlsm.setSpacing(9)  # Separa casilla y texto.
        self.casilla_advertencias = BotonCasillaConfiguracion("Mostrar advertencias debajo de Tabla VLSM", self)  # Crea el control de la modalidad compacta.
        self.etiqueta_advertencias = QLabel("Mostrar advertencias debajo de Tabla VLSM")  # Presenta la descripción visible.
        self.etiqueta_advertencias.setObjectName("TextoConfiguracion")  # Utiliza el estilo común.
        self.etiqueta_advertencias.setContentsMargins(2, 0, 2, 0)  # Mantiene una pequeña separación.
        self.casilla_advertencias.setChecked(self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Recupera el estado actual.
        self.casilla_advertencias.toggled.connect(self._cambiar_advertencias_vlsm)  # Registra las futuras decisiones.
        fila_advertencias_vlsm.addWidget(self.casilla_advertencias)  # Coloca la casilla.
        fila_advertencias_vlsm.addWidget(self.etiqueta_advertencias)  # Coloca el texto.
        fila_advertencias_vlsm.addStretch()  # Mantiene la opción alineada hacia la izquierda.
        diseno_advertencias.addLayout(fila_advertencias_vlsm)  # Incorpora la modalidad compacta.

        fila_advertencias_ventana = QHBoxLayout()  # Organiza la modalidad de ventana independiente.
        fila_advertencias_ventana.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_advertencias_ventana.setSpacing(9)  # Separa casilla y texto.
        self.casilla_advertencias_ventana = BotonCasillaConfiguracion("Mostrar advertencias en una ventana independiente", self)  # Crea el control de la segunda modalidad.
        self.etiqueta_advertencias_ventana = QLabel("Mostrar advertencias en una ventana independiente")  # Presenta su descripción visible.
        self.etiqueta_advertencias_ventana.setObjectName("TextoConfiguracion")  # Utiliza el estilo general.
        self.etiqueta_advertencias_ventana.setContentsMargins(2, 0, 2, 0)  # Mantiene separación mínima.
        self.casilla_advertencias_ventana.setChecked(self.preferencias_aplicacion.advertencias_ventana_independiente())  # Recupera el estado actual.
        self.casilla_advertencias_ventana.toggled.connect(self._cambiar_advertencias_ventana)  # Registra futuras decisiones.
        fila_advertencias_ventana.addWidget(self.casilla_advertencias_ventana)  # Coloca la casilla.
        fila_advertencias_ventana.addWidget(self.etiqueta_advertencias_ventana)  # Coloca su texto.
        fila_advertencias_ventana.addStretch()  # Mantiene el conjunto a la izquierda.
        diseno_advertencias.addLayout(fila_advertencias_ventana)  # Incorpora la segunda modalidad.

        diseno.addWidget(panel_advertencias)  # Añade la tarjeta completa.

        # ====================================================
        # Tarjeta 3: Interacción con advertencias
        # ====================================================

        panel_interaccion = QFrame()  # Crea la tarjeta correspondiente con el doble clic de la ventana independiente.
        panel_interaccion.setObjectName("TarjetaConfiguracion")  # Reutiliza la apariencia general.
        diseno_interaccion = QVBoxLayout(panel_interaccion)  # Organiza título, descripción y opción.
        diseno_interaccion.setContentsMargins(22, 16, 22, 16)  # Mantiene el mismo padding.
        diseno_interaccion.setSpacing(9)  # Conserva separación uniforme.

        subtitulo_interaccion = QLabel("Interacción con advertencias")  # Identifica la tercera tarjeta.
        subtitulo_interaccion.setObjectName("SubtituloConfiguracion")  # Aplica el estilo interno.
        subtitulo_interaccion.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación.
        diseno_interaccion.addWidget(subtitulo_interaccion)  # Coloca el encabezado.

        descripcion_interaccion = QLabel("En la ventana independiente puedes hacer doble clic sobre una advertencia para ir directamente a su ubicación en el código.")  # Explica el comportamiento de navegación.
        descripcion_interaccion.setObjectName("DescripcionConfiguracion")  # Mantiene el estilo secundario.
        descripcion_interaccion.setContentsMargins(4, 2, 4, 2)  # Conserva separación interna.
        descripcion_interaccion.setWordWrap(True)  # Permite varias líneas.
        diseno_interaccion.addWidget(descripcion_interaccion)  # Coloca la explicación.

        fila_cerrar = QHBoxLayout()  # Organiza la opción que decide si la ventana se cierra al navegar.
        fila_cerrar.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_cerrar.setSpacing(9)  # Separa casilla y texto.
        self.casilla_cerrar_ventana = BotonCasillaConfiguracion("Cerrar la ventana de advertencias al ir al código", self)  # Crea la preferencia correspondiente.
        self.etiqueta_cerrar_ventana = QLabel("Cerrar la ventana de advertencias al ir al código")  # Presenta el texto visible.
        self.etiqueta_cerrar_ventana.setObjectName("TextoConfiguracion")  # Utiliza la apariencia común.
        self.etiqueta_cerrar_ventana.setContentsMargins(2, 0, 2, 0)  # Mantiene una separación mínima.
        self.casilla_cerrar_ventana.setChecked(self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Recupera la decisión actual.
        self.casilla_cerrar_ventana.toggled.connect(self._cambiar_cerrar_ventana_al_navegar)  # Registra futuras modificaciones.
        fila_cerrar.addWidget(self.casilla_cerrar_ventana)  # Coloca la casilla.
        fila_cerrar.addWidget(self.etiqueta_cerrar_ventana)  # Coloca su descripción.
        fila_cerrar.addStretch()  # Mantiene el contenido alineado a la izquierda.
        diseno_interaccion.addLayout(fila_cerrar)  # Incorpora la opción.
        diseno.addWidget(panel_interaccion)  # Añade la tercera tarjeta.

        self._actualizar_disponibilidad_interaccion()  # Refleja si esta opción puede utilizarse con la modalidad actual.
        diseno.addStretch()  # Mantiene todo el contenido agrupado hacia arriba.

    # ========================================================
    # Navegación
    # ========================================================

    def _cambiar_navegacion_errores(self, activada: bool) -> None:  # Intenta modificar la navegación automática hacia errores.
        if self.preferencias_aplicacion.establecer_navegacion_errores_activada(activada):  # Comprueba que el valor pueda conservarse.
            self.navegacion_errores_cambiada.emit(bool(activada))  # Comunica el nuevo comportamiento después de guardarlo.
            return  # Finaliza porque no hace falta restaurar la casilla.

        self._restaurar_casilla(self.casilla_navegacion_errores, self.preferencias_aplicacion.navegacion_errores_activada())  # Recupera el estado anterior cuando la escritura falla.

    def _cambiar_navegacion_vlsm(self, activada: bool) -> None:  # Intenta modificar la navegación automática hacia Tabla VLSM.
        if self.preferencias_aplicacion.establecer_navegacion_vlsm_activada(activada):  # Comprueba que el valor pueda guardarse.
            self.navegacion_vlsm_cambiada.emit(bool(activada))  # Comunica la nueva decisión.
            return  # Finaliza después de una actualización correcta.

        self._restaurar_casilla(self.casilla_navegacion_vlsm, self.preferencias_aplicacion.navegacion_vlsm_activada())  # Recupera la preferencia que continúa almacenada.

    # ========================================================
    # Presentación de advertencias
    # ========================================================

    def _cambiar_advertencias_vlsm(self, visibles: bool) -> None:  # Modifica la modalidad compacta manteniendo exclusión con la ventana independiente.
        if self.actualizando_advertencias:  # Comprueba si el cambio fue producido internamente.
            return  # Evita interpretar una sincronización como otra decisión del usuario.

        if not self.preferencias_aplicacion.establecer_advertencias_vlsm_visibles(visibles):  # Intenta conservar la nueva decisión.
            self._restaurar_advertencias_guardadas()  # Recupera ambas casillas cuando la operación falla.
            return  # Impide emitir señales correspondientes con un cambio inexistente.

        if visibles:  # Comprueba si la modalidad compacta acaba de activarse.
            self.actualizando_advertencias = True  # Protege la sincronización visual de la modalidad contraria.
            self._establecer_casilla_sin_emitir(self.casilla_advertencias_ventana, False)  # Desactiva visualmente la ventana independiente.
            self.actualizando_advertencias = False  # Permite nuevamente interacciones normales.
            self.advertencias_ventana_cambiadas.emit(False)  # Solicita cerrar cualquier ventana independiente todavía activa.

        self.advertencias_vlsm_cambiadas.emit(bool(visibles))  # Comunica el estado efectivo de la modalidad compacta.
        self._actualizar_disponibilidad_interaccion()  # Actualiza la tercera tarjeta según la modalidad elegida.

    def _cambiar_advertencias_ventana(self, visibles: bool) -> None:  # Modifica la ventana independiente manteniendo exclusión con el panel compacto.
        if self.actualizando_advertencias:  # Comprueba si la modificación pertenece con una sincronización interna.
            return  # Evita procesarla dos veces.

        if not self.preferencias_aplicacion.establecer_advertencias_ventana_independiente(visibles):  # Intenta conservar el nuevo valor.
            self._restaurar_advertencias_guardadas()  # Recupera la representación almacenada cuando falla.
            return  # No comunica un cambio que realmente no ocurrió.

        if visibles:  # Comprueba si la ventana independiente acaba de habilitarse.
            self.actualizando_advertencias = True  # Protege la sincronización de la otra modalidad.
            self._establecer_casilla_sin_emitir(self.casilla_advertencias, False)  # Desactiva visualmente el panel compacto.
            self.actualizando_advertencias = False  # Reactiva el procesamiento normal.
            self.advertencias_vlsm_cambiadas.emit(False)  # Solicita ocultar inmediatamente cualquier panel compacto visible.

        self.advertencias_ventana_cambiadas.emit(bool(visibles))  # Comunica el estado efectivo de la ventana independiente.
        self._actualizar_disponibilidad_interaccion()  # Activa o desactiva la opción dependiente del tercer bloque.

    # ========================================================
    # Interacción con advertencias
    # ========================================================

    def _cambiar_cerrar_ventana_al_navegar(self, cerrar: bool) -> None:  # Modifica el comportamiento del doble clic sobre una advertencia.
        if self.preferencias_aplicacion.establecer_cerrar_ventana_advertencias_al_navegar(cerrar):  # Intenta conservar la nueva decisión.
            self.cerrar_ventana_al_navegar_cambiado.emit(bool(cerrar))  # Comunica el comportamiento efectivo.
            return  # Finaliza después de una actualización correcta.

        self._restaurar_casilla(self.casilla_cerrar_ventana, self.preferencias_aplicacion.cerrar_ventana_advertencias_al_navegar())  # Recupera el valor anterior si no pudo guardarse.

    def _actualizar_disponibilidad_interaccion(self) -> None:  # Habilita la tercera opción solamente cuando existe ventana independiente.
        disponible = self.casilla_advertencias_ventana.isChecked()  # Consulta directamente la modalidad actual.
        self.casilla_cerrar_ventana.setEnabled(disponible)  # Impide modificar una opción irrelevante cuando la ventana está apagada.
        self.etiqueta_cerrar_ventana.setEnabled(disponible)  # Mantiene también el texto visualmente sincronizado.

    # ========================================================
    # Utilidades visuales
    # ========================================================

    def _establecer_casilla_sin_emitir(self, casilla: BotonCasillaConfiguracion, activada: bool) -> None:  # Sincroniza una casilla sin volver a ejecutar su lógica asociada.
        casilla.blockSignals(True)  # Suspende temporalmente las señales.
        casilla.setChecked(bool(activada))  # Coloca el estado solicitado.
        casilla.blockSignals(False)  # Reactiva futuras interacciones del usuario.
        casilla._actualizar_apariencia(bool(activada))  # Actualiza manualmente la representación porque toggled estuvo bloqueada.

    def _restaurar_casilla(self, casilla: BotonCasillaConfiguracion, valor: bool) -> None:  # Recupera una preferencia que no pudo modificarse.
        self._establecer_casilla_sin_emitir(casilla, valor)  # Reutiliza la sincronización silenciosa.

    def _restaurar_advertencias_guardadas(self) -> None:  # Recupera conjuntamente las dos modalidades cuando alguna escritura falla.
        self.actualizando_advertencias = True  # Protege la restauración frente a procesamiento recursivo.
        self._establecer_casilla_sin_emitir(self.casilla_advertencias, self.preferencias_aplicacion.advertencias_vlsm_visibles())  # Recupera la modalidad compacta almacenada.
        self._establecer_casilla_sin_emitir(self.casilla_advertencias_ventana, self.preferencias_aplicacion.advertencias_ventana_independiente())  # Recupera la modalidad independiente almacenada.
        self.actualizando_advertencias = False  # Reactiva futuras decisiones normales.
        self._actualizar_disponibilidad_interaccion()  # Sincroniza finalmente la disponibilidad de la opción dependiente.