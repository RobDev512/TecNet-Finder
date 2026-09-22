# ============================================================
# Archivo: panel_configuracion_ventana.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene las preferencias relacionadas con ventana y apariencia.
#
# Permite modificar:
# - Estado inicial de la ventana.
# - Recuperación del estado entre sesiones.
# - Modo visual: oscuro o claro.
# - Variante perteneciente al modo seleccionado.
# - Idioma de la interfaz.
# - Tipografía general.
# - Última categoría visitada de Configuración.
#
# El modo no se guarda independientemente. Se obtiene del tema
# seleccionado para evitar combinaciones inconsistentes.
# ============================================================

from PySide6.QtCore import Qt, Signal  # Permite configurar controles y comunicar modificaciones temporales.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget  # Proporciona los componentes visuales necesarios.
from Interfaz.configuracion.controles_configuracion import CampoNumeroConfiguracion, SelectorDesplegableConfiguracion  # Proporciona los controles personalizados generales.
from Interfaz.configuracion.selector_fuentes import SelectorFuentes  # Proporciona búsqueda especializada de familias tipográficas.
from Motor.configuracion.catalogo_idiomas import idiomas_disponibles  # Proporciona los seis idiomas admitidos y sus nombres visibles.
from Motor.configuracion.catalogo_temas import modo_del_tema, obtener_modos_disponibles, obtener_tema, obtener_temas_por_modo  # Proporciona modos y variantes visuales.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Proporciona límites y valores compartidos.


class BotonCasillaVentana(QPushButton):  # Representa una casilla coherente con las demás categorías de Configuración.
    def __init__(self, nombre_accesible: str, padre=None):
        super().__init__(padre)  # Inicializa QPushButton.
        self.setCheckable(True)  # Permite conservar un estado activado o desactivado.
        self.setFixedSize(24, 24)  # Mantiene dimensiones compactas.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Proporciona una descripción accesible.
        self.setStyleSheet("padding: 0px; font-family: 'Segoe UI Symbol'; font-size: 12pt; font-weight: bold;")  # Garantiza la representación correcta de la marca.
        self.toggled.connect(self._actualizar_apariencia)  # Sincroniza representación y estado.
        self._actualizar_apariencia(False)  # Prepara inicialmente una casilla vacía.

    def _actualizar_apariencia(self, activado: bool) -> None:
        self.setText("✓" if activado else "")  # Muestra la marca solamente cuando corresponde.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Reutiliza los estilos existentes.
        self.style().unpolish(self)  # Retira temporalmente la apariencia anterior.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos.
        self.update()  # Solicita el redibujado inmediato.


class PanelConfiguracionVentana(QWidget):  # Agrupa las preferencias de ventana, tema y tipografía general.
    configuracion_modificada = Signal()  # Informa que existe al menos una modificación temporal.

    def __init__(self, preferencias_aplicacion, preferencias_tema, padre=None):
        super().__init__(padre)  # Vincula el panel con Configuración.
        self.preferencias_aplicacion = preferencias_aplicacion  # Conserva la copia temporal de preferencias generales.
        self.preferencias_tema = preferencias_tema  # Conserva la copia temporal específica del tema.
        tema_actual = self.preferencias_tema.tema()  # Recupera la variante utilizada al abrir Configuración.
        self._ultima_variante_por_modo = {modo_del_tema(tema_actual): tema_actual}  # Recuerda la última variante visitada de cada modo durante esta sesión.
        self._construir_interfaz()  # Construye todos los controles.

    def _crear_tarjeta(self, titulo: str, descripcion: str) -> tuple[QFrame, QVBoxLayout]:
        tarjeta = QFrame()  # Crea una superficie visual reutilizable.
        tarjeta.setObjectName("TarjetaConfiguracion")  # Reutiliza el estilo común.
        diseno = QVBoxLayout(tarjeta)  # Organiza verticalmente su contenido.
        diseno.setContentsMargins(22, 16, 22, 16)  # Mantiene padding uniforme.
        diseno.setSpacing(9)  # Conserva una separación compacta.
        subtitulo = QLabel(titulo)  # Presenta el nombre de la tarjeta.
        subtitulo.setObjectName("SubtituloConfiguracion")  # Utiliza el estilo interno.
        subtitulo.setContentsMargins(4, 0, 4, 0)  # Mantiene alineación lateral.
        descripcion_widget = QLabel(descripcion)  # Presenta una breve explicación.
        descripcion_widget.setObjectName("DescripcionConfiguracion")  # Utiliza el estilo secundario.
        descripcion_widget.setContentsMargins(4, 2, 4, 2)  # Mantiene separación interior.
        descripcion_widget.setWordWrap(True)  # Permite adaptar el texto.
        diseno.addWidget(subtitulo)  # Añade primero el título.
        diseno.addWidget(descripcion_widget)  # Añade después la explicación.
        return tarjeta, diseno  # Entrega tarjeta y layout para completar su contenido.

    def _crear_fila_casilla(self, casilla: QPushButton, texto: str, ayuda: str = "") -> QHBoxLayout:
        fila = QHBoxLayout()  # Organiza horizontalmente casilla y descripción.
        fila.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación general.
        fila.setSpacing(9)  # Separa ambos elementos.
        etiqueta = QLabel(texto)  # Presenta el nombre visible de la opción.
        etiqueta.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.
        if ayuda: casilla.setToolTip(ayuda); etiqueta.setToolTip(ayuda)  # Comparte la ayuda contextual.
        fila.addWidget(casilla)  # Coloca primero la casilla.
        fila.addWidget(etiqueta)  # Coloca después la descripción.
        fila.addStretch()  # Mantiene el conjunto alineado a la izquierda.
        return fila  # Entrega la fila terminada.

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)  # Organiza toda la categoría verticalmente.
        diseno.setContentsMargins(24, 22, 24, 22)  # Mantiene los márgenes existentes.
        diseno.setSpacing(14)  # Conserva separación uniforme.

        titulo = QLabel("Ventana y apariencia")  # Presenta el nombre de la categoría.
        titulo.setObjectName("TituloConfiguracion")  # Reutiliza el encabezado principal.
        titulo.setContentsMargins(4, 0, 4, 0)  # Mantiene alineación lateral.
        descripcion = QLabel("Personaliza cómo inicia TecNet Finder, su tema visual, el idioma y la tipografía utilizada por la interfaz.")  # Resume el propósito actualizado.
        descripcion.setObjectName("DescripcionConfiguracion")  # Utiliza el estilo secundario.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Mantiene la misma alineación.
        descripcion.setWordWrap(True)  # Permite adaptar la explicación.
        diseno.addWidget(titulo)  # Añade el encabezado.
        diseno.addWidget(descripcion)  # Añade su explicación.

        tarjeta_inicio, diseno_inicio = self._crear_tarjeta("Inicio de TecNet Finder", "Define el estado utilizado al abrir TecNet Finder cuando no se está recuperando un estado anterior.")  # Construye la primera tarjeta.
        self.casilla_iniciar_maximizado = BotonCasillaVentana("Iniciar TecNet Finder maximizado", self)  # Crea la preferencia.
        self.casilla_iniciar_maximizado.setChecked(self.preferencias_aplicacion.iniciar_maximizado())  # Recupera el valor temporal.
        self.casilla_iniciar_maximizado.toggled.connect(self._cambiar_iniciar_maximizado)  # Registra modificaciones.
        diseno_inicio.addLayout(self._crear_fila_casilla(self.casilla_iniciar_maximizado, "Iniciar TecNet Finder maximizado", "Cuando no exista un estado anterior para recuperar, TecNet Finder iniciará ocupando toda el área disponible."))  # Añade la opción.
        diseno.addWidget(tarjeta_inicio)  # Incorpora la primera tarjeta.

        tarjeta_estado, diseno_estado = self._crear_tarjeta("Estado entre sesiones", "Permite recuperar si TecNet Finder estaba maximizado o en modo ventana cuando terminó la sesión anterior.")  # Construye la segunda tarjeta.
        self.casilla_recordar_estado = BotonCasillaVentana("Recordar el estado de la ventana al cerrar", self)  # Crea la preferencia.
        self.casilla_recordar_estado.setChecked(self.preferencias_aplicacion.recordar_estado_ventana())  # Recupera el valor temporal.
        self.casilla_recordar_estado.toggled.connect(self._cambiar_recordar_estado)  # Registra modificaciones.
        diseno_estado.addLayout(self._crear_fila_casilla(self.casilla_recordar_estado, "Recordar el estado de la ventana al cerrar", "Media pantalla y pantalla completa continúan siendo estados temporales y no se recuperan entre ejecuciones."))  # Añade la opción.
        diseno.addWidget(tarjeta_estado)  # Incorpora la tarjeta.

        # ====================================================
        # Tema de la aplicación
        # ====================================================

        tarjeta_tema, diseno_tema = self._crear_tarjeta("Tema de la aplicación", "Selecciona primero un modo y después una variante. Los colores de errores, advertencias y demás diagnósticos conservan siempre su significado.")  # Construye la tarjeta completa de apariencia.
        tema_actual = self.preferencias_tema.tema()  # Recupera la variante temporal actual.
        modo_actual = modo_del_tema(tema_actual)  # Obtiene automáticamente el modo correspondiente.

        fila_modo = QHBoxLayout()  # Organiza la selección de modo.
        fila_modo.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_modo.setSpacing(10)  # Separa etiqueta y selector.
        etiqueta_modo = QLabel("Modo:")  # Identifica la primera selección.
        etiqueta_modo.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.
        self.selector_modo = SelectorDesplegableConfiguracion(self)  # Utiliza el selector personalizado para una lista pequeña.
        self.selector_modo.setFixedWidth(220)  # Mantiene un ancho cómodo.
        for modo in obtener_modos_disponibles(): self.selector_modo.agregar_opcion(modo["nombre"], modo["id"])  # Añade Oscuro y Claro desde el catálogo central.
        self.selector_modo.establecer_valor(modo_actual)  # Marca el modo correspondiente con el tema actual.
        self.selector_modo.valor_cambiado.connect(self._cambiar_modo_tema)  # Reconstruye las variantes cuando cambia el modo.
        fila_modo.addWidget(etiqueta_modo)  # Coloca la etiqueta.
        fila_modo.addWidget(self.selector_modo)  # Coloca el selector.
        fila_modo.addStretch()  # Mantiene el contenido alineado.
        diseno_tema.addLayout(fila_modo)  # Añade la primera fila.

        fila_variante = QHBoxLayout()  # Organiza la selección de variante.
        fila_variante.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_variante.setSpacing(10)  # Separa etiqueta y selector.
        etiqueta_variante = QLabel("Variante:")  # Identifica la segunda selección.
        etiqueta_variante.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.
        self.selector_variante = SelectorDesplegableConfiguracion(self)  # Utiliza el mismo control reutilizable.
        self.selector_variante.setFixedWidth(260)  # Reserva espacio suficiente para nombres futuros.
        self._cargar_variantes(modo_actual, tema_actual)  # Añade solamente las variantes pertenecientes al modo inicial.
        self.selector_variante.valor_cambiado.connect(self._cambiar_variante_tema)  # Registra una selección concreta.
        fila_variante.addWidget(etiqueta_variante)  # Coloca la etiqueta.
        fila_variante.addWidget(self.selector_variante)  # Coloca el selector.
        fila_variante.addStretch()  # Mantiene el contenido alineado.
        diseno_tema.addLayout(fila_variante)  # Añade la segunda fila.

        self.etiqueta_descripcion_tema = QLabel("")  # Reserva una explicación específica para la variante actual.
        self.etiqueta_descripcion_tema.setObjectName("DescripcionConfiguracion")  # Utiliza la apariencia secundaria.
        self.etiqueta_descripcion_tema.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        self.etiqueta_descripcion_tema.setWordWrap(True)  # Permite varias líneas.
        diseno_tema.addWidget(self.etiqueta_descripcion_tema)  # Coloca la explicación debajo de los selectores.
        self._actualizar_descripcion_tema(tema_actual)  # Presenta la descripción inicial.
        diseno.addWidget(tarjeta_tema)  # Incorpora la tarjeta completa.

        # ====================================================
        # Idioma de la interfaz
        # ====================================================

        tarjeta_idioma, diseno_idioma = self._crear_tarjeta("Idioma de la interfaz", "Selecciona el idioma utilizado por los textos de TecNet Finder. Las palabras reservadas IP, MASK, HOSTS y NAME permanecen sin cambios.")  # Construye la tarjeta dedicada al idioma.
        fila_idioma = QHBoxLayout()  # Organiza etiqueta y selector.
        fila_idioma.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación de las demás preferencias.
        fila_idioma.setSpacing(10)  # Separa ambos controles.
        etiqueta_idioma = QLabel("Idioma:")  # Identifica la selección.
        etiqueta_idioma.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.
        self.selector_idioma = SelectorDesplegableConfiguracion(self)  # Utiliza el selector personalizado ya probado.
        self.selector_idioma.setFixedWidth(260)  # Reserva espacio para los nombres nativos de los seis idiomas.
        for codigo, nombre in idiomas_disponibles(): self.selector_idioma.agregar_opcion(nombre, codigo)  # Conserva un valor interno estable independiente del texto visible.
        self.selector_idioma.establecer_valor(self.preferencias_aplicacion.idioma_interfaz())  # Recupera la selección temporal actual.
        self.selector_idioma.valor_cambiado.connect(self._cambiar_idioma_interfaz)  # Registra solamente selecciones realizadas por el usuario.
        fila_idioma.addWidget(etiqueta_idioma)  # Coloca la etiqueta.
        fila_idioma.addWidget(self.selector_idioma)  # Coloca el selector.
        fila_idioma.addStretch()  # Mantiene el conjunto alineado a la izquierda.
        diseno_idioma.addLayout(fila_idioma)  # Añade la selección a la tarjeta.
        diseno.addWidget(tarjeta_idioma)  # Incorpora la preferencia de idioma dentro de Ventana y apariencia.

        # ====================================================
        # Tipografía general
        # ====================================================

        tarjeta_tipografia, diseno_tipografia = self._crear_tarjeta("Tipografía de la interfaz", "Cambia la fuente utilizada por la interfaz general. El editor conserva su propia configuración independiente.")  # Construye la tarjeta de tipografía.
        fila_familia = QHBoxLayout()  # Organiza la familia global.
        fila_familia.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_familia.setSpacing(10)  # Separa los controles.
        etiqueta_familia = QLabel("Familia de fuente:")  # Identifica la preferencia.
        etiqueta_familia.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.
        self.selector_fuente_interfaz = SelectorFuentes(self)  # Utiliza el selector buscable.
        self.selector_fuente_interfaz.setFixedWidth(300)  # Mantiene espacio suficiente para nombres largos.
        self.selector_fuente_interfaz.establecer_valor(self.preferencias_aplicacion.familia_fuente_interfaz())  # Recupera la selección temporal.
        self.selector_fuente_interfaz.valor_cambiado.connect(self._cambiar_familia_fuente_interfaz)  # Registra futuras selecciones.
        fila_familia.addWidget(etiqueta_familia)  # Coloca la etiqueta.
        fila_familia.addWidget(self.selector_fuente_interfaz)  # Coloca el selector.
        fila_familia.addStretch()  # Mantiene todo alineado.
        diseno_tipografia.addLayout(fila_familia)  # Añade la primera fila.

        fila_tamano = QHBoxLayout()  # Organiza el tamaño base.
        fila_tamano.setContentsMargins(4, 2, 4, 2)  # Mantiene la alineación.
        fila_tamano.setSpacing(10)  # Separa los controles.
        etiqueta_tamano = QLabel("Tamaño base:")  # Identifica la preferencia.
        etiqueta_tamano.setObjectName("TextoConfiguracion")  # Reutiliza el estilo común.
        self.selector_tamano_interfaz = CampoNumeroConfiguracion(self)  # Utiliza el campo numérico propio.
        self.selector_tamano_interfaz.setRange(PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_MINIMO, PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_MAXIMO)  # Limita la selección a valores seguros.
        self.selector_tamano_interfaz.setSuffix(" pt")  # Aclara la unidad.
        self.selector_tamano_interfaz.setValue(self.preferencias_aplicacion.tamano_fuente_interfaz())  # Recupera el valor temporal.
        self.selector_tamano_interfaz.setFixedWidth(130)  # Mantiene un ancho compacto.
        self.selector_tamano_interfaz.valueChanged.connect(self._cambiar_tamano_fuente_interfaz)  # Registra modificaciones.
        fila_tamano.addWidget(etiqueta_tamano)  # Coloca la etiqueta.
        fila_tamano.addWidget(self.selector_tamano_interfaz)  # Coloca el campo.
        fila_tamano.addStretch()  # Mantiene la fila alineada.
        diseno_tipografia.addLayout(fila_tamano)  # Añade la segunda fila.
        diseno.addWidget(tarjeta_tipografia)  # Incorpora la tarjeta.

        tarjeta_configuracion, diseno_configuracion = self._crear_tarjeta("Ventana de Configuración", "Permite regresar directamente a la última categoría que estabas consultando cuando vuelvas a abrir Configuración.")  # Construye la última tarjeta.
        self.casilla_recordar_seccion = BotonCasillaVentana("Abrir Configuración en la última sección visitada", self)  # Crea la preferencia.
        self.casilla_recordar_seccion.setChecked(self.preferencias_aplicacion.recordar_seccion_configuracion())  # Recupera el valor temporal.
        self.casilla_recordar_seccion.toggled.connect(self._cambiar_recordar_seccion)  # Registra modificaciones.
        diseno_configuracion.addLayout(self._crear_fila_casilla(self.casilla_recordar_seccion, "Abrir Configuración en la última sección visitada"))  # Añade la opción.
        diseno.addWidget(tarjeta_configuracion)  # Incorpora la tarjeta.
        diseno.addStretch()  # Mantiene todas las tarjetas agrupadas arriba.

    def _cargar_variantes(self, modo_id: str, tema_preferido: str | None = None) -> None:
        temas = obtener_temas_por_modo(modo_id)  # Recupera únicamente las variantes compatibles con el modo solicitado.
        self.selector_variante.limpiar_opciones()  # Elimina las opciones pertenecientes al modo anterior.
        for tema in temas: self.selector_variante.agregar_opcion(tema["nombre"], tema["id"])  # Reconstruye el selector mediante el catálogo central.
        ids = {tema["id"] for tema in temas}  # Obtiene rápidamente los identificadores disponibles.
        seleccionado = tema_preferido if tema_preferido in ids else (temas[0]["id"] if temas else None)  # Conserva una variante preferida o utiliza la primera disponible.
        if seleccionado is not None: self.selector_variante.establecer_valor(seleccionado)  # Sincroniza visualmente la variante definitiva.

    def _cambiar_modo_tema(self, modo_id) -> None:
        modo_id = str(modo_id)  # Normaliza el identificador recibido desde el selector.
        tema_preferido = self._ultima_variante_por_modo.get(modo_id)  # Intenta recuperar la última variante visitada de este modo durante la sesión.
        temas = obtener_temas_por_modo(modo_id)  # Recupera las variantes disponibles.
        if not temas: return  # Evita modificar la preferencia si un modo futuro todavía no posee variantes.
        ids = {tema["id"] for tema in temas}  # Obtiene sus identificadores.
        tema_nuevo = tema_preferido if tema_preferido in ids else temas[0]["id"]  # Recupera la variante recordada o utiliza la primera.
        self._cargar_variantes(modo_id, tema_nuevo)  # Reconstruye visualmente el segundo selector.
        if self.preferencias_tema.establecer_tema(tema_nuevo): self._ultima_variante_por_modo[modo_id] = tema_nuevo; self._actualizar_descripcion_tema(tema_nuevo); self.configuracion_modificada.emit()  # Conserva temporalmente la nueva combinación.

    def _cambiar_variante_tema(self, tema_id) -> None:
        tema_id = str(tema_id)  # Normaliza el valor recibido.
        if self.preferencias_tema.establecer_tema(tema_id):
            modo_id = modo_del_tema(tema_id)  # Recupera el modo al que pertenece la variante.
            self._ultima_variante_por_modo[modo_id] = tema_id  # Recuerda esta selección durante la sesión actual.
            self._actualizar_descripcion_tema(tema_id)  # Actualiza la explicación visible.
            self.configuracion_modificada.emit()  # Solicita reevaluar Aplicar.

    def _actualizar_descripcion_tema(self, tema_id: str) -> None:
        self.etiqueta_descripcion_tema.setText(obtener_tema(tema_id)["descripcion"])  # Presenta la descripción centralizada de la variante.

    def _cambiar_iniciar_maximizado(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_iniciar_maximizado(activado): self.configuracion_modificada.emit(); return  # Conserva temporalmente la decisión.
        self._restaurar_casilla(self.casilla_iniciar_maximizado, self.preferencias_aplicacion.iniciar_maximizado())  # Recupera el valor anterior ante un fallo.

    def _cambiar_recordar_estado(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_recordar_estado_ventana(activado): self.configuracion_modificada.emit(); return  # Conserva temporalmente la decisión.
        self._restaurar_casilla(self.casilla_recordar_estado, self.preferencias_aplicacion.recordar_estado_ventana())  # Recupera el valor anterior.

    def _cambiar_recordar_seccion(self, activado: bool) -> None:
        if self.preferencias_aplicacion.establecer_recordar_seccion_configuracion(activado): self.configuracion_modificada.emit(); return  # Conserva temporalmente la decisión.
        self._restaurar_casilla(self.casilla_recordar_seccion, self.preferencias_aplicacion.recordar_seccion_configuracion())  # Recupera el valor realmente válido.

    def _cambiar_familia_fuente_interfaz(self, familia: str) -> None:
        if self.preferencias_aplicacion.establecer_familia_fuente_interfaz(str(familia)): self.configuracion_modificada.emit()  # Conserva temporalmente la fuente seleccionada.

    def _cambiar_tamano_fuente_interfaz(self, tamano: int) -> None:
        if self.preferencias_aplicacion.establecer_tamano_fuente_interfaz(tamano): self.configuracion_modificada.emit()  # Conserva temporalmente el tamaño.

    def _cambiar_idioma_interfaz(self, idioma: str) -> None:
        if self.preferencias_aplicacion.establecer_idioma_interfaz(str(idioma)): self.configuracion_modificada.emit()  # Conserva temporalmente el idioma seleccionado hasta Aplicar o Aceptar.

    def _restaurar_casilla(self, casilla: BotonCasillaVentana, valor: bool) -> None:
        casilla.blockSignals(True)  # Evita ejecutar nuevamente la modificación mientras se restaura.
        casilla.setChecked(bool(valor))  # Recupera el valor todavía válido.
        casilla.blockSignals(False)  # Reactiva las futuras interacciones.
        casilla._actualizar_apariencia(bool(valor))  # Sincroniza manualmente la representación visual.
