# ============================================================
# Archivo: panel_configuracion_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el panel de configuración dedicado a la
# asistencia opcional de inteligencia artificial local.
#
# Permite activar, desactivar, instalar y desinstalar el
# componente sin bloquear la interfaz y mantiene sincronizado
# el estado efectivo del autocompletado con TecNet Finder.
#
# Las acciones normales y el progreso utilizan la misma región
# visual. La barra de progreso representa el porcentaje mediante
# texto cuyo color cambia dinámicamente al ser cubierto por el
# avance de la operación.
# ============================================================

from PySide6.QtCore import QObject, QRect, QRunnable, QThreadPool, Qt, Signal, Slot  # Permite controlar geometría, señales y trabajos ejecutados fuera del hilo gráfico.
from PySide6.QtGui import QColor, QPainter  # Permite dibujar manualmente el porcentaje dinámico sobre la barra de progreso.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton, QStackedWidget, QVBoxLayout, QWidget  # Importa los controles utilizados por el panel.

from AsistenteIA.configuracion import MODELO_IA  # Permite mostrar el modelo técnico utilizado actualmente.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite consultar la instalación opcional administrada.
from AsistenteIA.gestor_instalacion_ia import GestorInstalacionIA, VERSION_OLLAMA  # Permite instalar y retirar físicamente el componente opcional.
from AsistenteIA.gestor_ollama import GestorOllama  # Permite iniciar y detener la instancia privada.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Permite conservar la elección del usuario entre ejecuciones.


class SenalesOperacionIA(QObject):  # Define el canal seguro utilizado para regresar desde los trabajos de administración.
    terminada = Signal(str, bool, str)  # Informa operación, resultado y mensaje final al hilo principal.
    progreso = Signal(str, object)  # Informa descripción y porcentaje opcional durante instalaciones largas.


class TrabajoOperacionIA(QRunnable):  # Ejecuta las operaciones de IA fuera del hilo gráfico.
    def __init__(
        self,
        operacion: str,
        gestor_ollama: GestorOllama,
        gestor_instalacion: GestorInstalacionIA,
    ):
        super().__init__()  # Inicializa el trabajo administrado por QThreadPool.
        self.operacion = operacion  # Conserva qué acción debe ejecutar el trabajo.
        self.gestor_ollama = gestor_ollama  # Reutiliza exactamente el servicio activo de TecNet Finder.
        self.gestor_instalacion = gestor_instalacion  # Reutiliza la administración física asociada con las mismas rutas.
        self.senales = SenalesOperacionIA()  # Crea los canales utilizados para progreso y resultado.

    @Slot()
    def run(self) -> None:
        resultado = False  # Considera fallida la operación hasta completarla explícitamente.
        mensaje = "La operación no pudo completarse."  # Conserva un mensaje seguro ante una ruta inesperada.

        try:
            if self.operacion == "activar":
                resultado = self.gestor_ollama.iniciar()  # Inicia el servicio fuera del hilo de la interfaz.
                mensaje = "La asistencia de IA se activó correctamente." if resultado else "No fue posible iniciar la asistencia de IA local."  # Prepara una explicación sencilla del resultado.
            elif self.operacion == "desactivar":
                self.gestor_ollama.detener()  # Cierra Ollama y sus procesos secundarios sin congelar Configuración.
                resultado = True  # Considera completada la desactivación cuando el gestor termina su limpieza.
                mensaje = "La asistencia de IA se desactivó correctamente."  # Conserva una confirmación reutilizable.
            elif self.operacion == "instalar":
                resultado, mensaje = self.gestor_instalacion.instalar(self._informar_progreso)  # Ejecuta descarga, verificación, extracción y modelo dentro del hilo secundario.
            elif self.operacion == "desinstalar":
                resultado, mensaje = self.gestor_instalacion.desinstalar(self._informar_progreso)  # Detiene el servicio y elimina únicamente la carpeta administrada del componente.
        except Exception as error:
            resultado = False  # Convierte cualquier excepción inesperada en un resultado controlado.
            mensaje = f"No fue posible completar la operación de asistencia de IA: {error}"  # Conserva información suficiente para diagnosticar el problema.

        self.senales.terminada.emit(self.operacion, resultado, mensaje)  # Devuelve el resultado al hilo principal sin modificar widgets directamente.

    def _informar_progreso(self, etapa: str, porcentaje: int | None) -> None:
        self.senales.progreso.emit(etapa, porcentaje)  # Transfiere las actualizaciones del gestor hacia la interfaz de forma segura.


class BotonCasillaIA(QPushButton):  # Representa una casilla que muestra claramente su estado mediante una marca.
    def __init__(self, padre=None):
        super().__init__(padre)  # Inicializa el botón utilizado como control de selección.
        self.setCheckable(True)  # Permite conservar explícitamente los estados activado y desactivado.
        self.setFixedSize(24, 24)  # Mantiene una apariencia compacta similar a una casilla.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el control puede pulsarse.
        self.setAccessibleName("Activar autocompletado con IA")  # Conserva una descripción accesible del control.
        self.setStyleSheet("padding: 0px; font-family: 'Segoe UI Symbol'; font-size: 12pt; font-weight: bold;")  # Mantiene centrada y legible la marca.
        self.toggled.connect(self._actualizar_apariencia)  # Actualiza inmediatamente el contenido visual.
        self._actualizar_apariencia(False)  # Prepara inicialmente el estado desactivado.

    def _actualizar_apariencia(self, activado: bool) -> None:
        self.setText("✓" if activado else "")  # Muestra una marca inequívoca mientras la opción se encuentra activa.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Utiliza el azul principal únicamente para el estado seleccionado.
        self.style().unpolish(self)  # Retira la apariencia anterior.
        self.style().polish(self)  # Aplica el nuevo estado visual.
        self.update()  # Solicita el redibujado inmediato.


class BarraProgresoIA(QProgressBar):  # Representa una barra cuyo porcentaje adapta su color según la región cubierta por el avance.
    def __init__(self, padre=None):
        super().__init__(padre)  # Conserva todo el funcionamiento normal de QProgressBar.
        self.color_texto_libre = QColor("#cdd6f4")  # Utiliza texto claro sobre la parte oscura todavía no recorrida.
        self.color_texto_cubierto = QColor("#11111b")  # Utiliza texto oscuro cuando el relleno azul alcanza cada región del porcentaje.
        self.setTextVisible(False)  # Evita que Qt dibuje un segundo porcentaje debajo del texto personalizado.

    def paintEvent(self, evento) -> None:
        super().paintEvent(evento)  # Permite que Qt dibuje primero fondo, borde y relleno utilizando el estilo configurado.

        minimo = self.minimum()  # Obtiene el límite inferior de la operación representada.
        maximo = self.maximum()  # Obtiene el límite superior de la operación representada.

        if minimo == 0 and maximo == 0:
            return  # Mantiene solamente la animación indeterminada cuando todavía no existe un porcentaje confiable.

        if maximo <= minimo:
            return  # Evita divisiones inválidas ante un rango incorrecto.

        proporcion = (self.value() - minimo) / (maximo - minimo)  # Convierte el valor actual a una proporción entre cero y uno.
        proporcion = max(0.0, min(proporcion, 1.0))  # Mantiene el cálculo dentro de los límites visibles de la barra.
        porcentaje = int(round(proporcion * 100))  # Obtiene el mismo porcentaje entero que espera ver el usuario.
        texto = f"{porcentaje}%"  # Construye el contenido centrado que será dibujado en dos colores.

        pintor = QPainter(self)  # Crea un pintor adicional sobre la barra ya representada por Qt.
        pintor.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)  # Mantiene los caracteres suaves durante el cambio de color.
        pintor.setFont(self.font())  # Conserva la misma tipografía utilizada por el resto de TecNet Finder.

        pintor.setPen(self.color_texto_libre)  # Prepara primero el color utilizado sobre el fondo oscuro.
        pintor.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, texto)  # Dibuja el porcentaje completo con el color correspondiente a la región libre.

        area_interior = self.rect().adjusted(1, 1, -1, -1)  # Descuenta el borde visual para aproximarse exactamente a la región utilizada por el relleno.
        ancho_cubierto = int(round(area_interior.width() * proporcion))  # Calcula hasta qué píxel ha llegado actualmente la parte azul.

        if ancho_cubierto <= 0:
            return  # Conserva todo el texto claro mientras el relleno todavía no alcanza ninguna región.

        zona_cubierta = QRect(
            area_interior.left(),
            area_interior.top(),
            ancho_cubierto,
            area_interior.height(),
        )  # Construye una región de recorte que coincide con la parte actualmente cubierta por el relleno.

        pintor.save()  # Conserva el estado utilizado para el texto claro antes de aplicar un recorte.
        pintor.setClipRect(zona_cubierta)  # Limita el siguiente dibujo únicamente a la región azul ya recorrida.
        pintor.setPen(self.color_texto_cubierto)  # Cambia a un tono oscuro que contrasta correctamente sobre el azul.
        pintor.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, texto)  # Redibuja solamente la parte del porcentaje alcanzada por el relleno.
        pintor.restore()  # Recupera el estado original del pintor después del dibujo recortado.


class PanelConfiguracionIA(QWidget):  # Representa la sección de IA dentro de la ventana general de configuración.
    activacion_cambiada = Signal(bool)  # Comunica al editor si puede comenzar o debe dejar de solicitar sugerencias.
    operacion_cambiada = Signal(bool)  # Informa a la ventana general si debe impedir temporalmente su cierre.

    def __init__(
        self,
        gestor_ollama: GestorOllama,
        componente_ia: GestorComponenteIA,
        preferencias_ia: PreferenciasIA,
        asistencia_disponible_inicial: bool,
        padre=None,
    ):
        super().__init__(padre)  # Vincula el panel con la ventana de configuración.
        self.gestor_ollama = gestor_ollama  # Reutiliza exactamente la instancia administrada por la aplicación.
        self.componente_ia = componente_ia  # Consulta la misma ubicación instalada utilizada por Ollama.
        self.preferencias_ia = preferencias_ia  # Conserva la configuración persistente del usuario.
        self.gestor_instalacion = GestorInstalacionIA(componente_ia, gestor_ollama)  # Prepara la administración física utilizando exactamente los mismos componentes.
        self.asistencia_disponible = bool(asistencia_disponible_inicial)  # Utiliza el estado conocido sin realizar consultas HTTP adicionales.
        self.actualizando_controles = False  # Evita interpretar sincronizaciones visuales como decisiones nuevas.
        self.operacion_en_curso = False  # Permite impedir acciones simultáneas durante inicio, cierre o instalación.
        self.trabajo_actual = None  # Conserva el trabajo activo hasta recibir su resultado.

        self.hilos = QThreadPool(self)  # Mantiene todas las operaciones lentas fuera del hilo gráfico.
        self.hilos.setMaxThreadCount(1)  # Evita modificar el mismo componente mediante varias acciones simultáneas.

        self._construir_interfaz()  # Crea los controles visuales de esta sección.
        self._actualizar_estado()  # Representa inmediatamente la situación actual.

    def _construir_interfaz(self) -> None:
        diseno = QVBoxLayout(self)  # Organiza verticalmente la información y acciones del panel.
        diseno.setContentsMargins(24, 22, 24, 22)  # Mantiene espacio suficiente respecto a los bordes de la sección.
        diseno.setSpacing(14)  # Separa claramente los diferentes grupos.

        titulo = QLabel("Asistencia de IA")  # Presenta el nombre de la sección actual.
        titulo.setObjectName("TituloConfiguracion")  # Permite destacar el encabezado mediante estilos.py.
        titulo.setContentsMargins(4, 0, 4, 0)  # Evita que el texto quede visualmente pegado a los límites internos de su etiqueta.
        diseno.addWidget(titulo)  # Coloca el encabezado al principio de la sección.

        descripcion = QLabel(
            "Administra el autocompletado inteligente de TecNet Finder. "
            "El procesamiento se realiza localmente en este equipo."
        )  # Explica brevemente la finalidad de la sección.
        descripcion.setObjectName("DescripcionConfiguracion")  # Mantiene un estilo secundario.
        descripcion.setContentsMargins(4, 0, 4, 0)  # Añade respiración lateral al texto dentro de su región.
        descripcion.setWordWrap(True)  # Permite adaptar el texto al ancho disponible.
        diseno.addWidget(descripcion)  # Coloca la descripción debajo del título.

        panel_estado = QFrame()  # Agrupa la información general del componente.
        panel_estado.setObjectName("TarjetaConfiguracion")  # Permite mostrar los datos dentro de una tarjeta diferenciada.
        diseno_estado = QVBoxLayout(panel_estado)  # Organiza verticalmente los detalles técnicos.
        diseno_estado.setContentsMargins(22, 18, 22, 18)  # Mantiene un padding uniforme entre el borde de la tarjeta y todos sus elementos.
        diseno_estado.setSpacing(8)  # Mantiene compactos los datos para respetar el tamaño fijo de Configuración.

        subtitulo_estado = QLabel("Estado del componente")  # Identifica el bloque informativo.
        subtitulo_estado.setObjectName("SubtituloConfiguracion")  # Aplica el estilo correspondiente a subtítulos.
        subtitulo_estado.setContentsMargins(4, 0, 4, 0)  # Separa el título de los límites de su propia etiqueta.
        diseno_estado.addWidget(subtitulo_estado)  # Coloca el nombre del bloque antes de sus datos.

        self.etiqueta_instalacion = QLabel()  # Muestra si la asistencia se encuentra físicamente instalada.
        self.etiqueta_ejecucion = QLabel()  # Muestra si la instancia local se encuentra actualmente activa.
        self.etiqueta_modelo = QLabel(f"Modelo: {MODELO_IA}")  # Informa el modelo utilizado actualmente.
        self.etiqueta_runtime = QLabel(f"Runtime local: Ollama {VERSION_OLLAMA}")  # Informa la versión fijada por TecNet Finder.
        self.etiqueta_ruta = QLabel()  # Muestra la ubicación administrada del componente.

        for etiqueta in (
            self.etiqueta_instalacion,
            self.etiqueta_ejecucion,
            self.etiqueta_modelo,
            self.etiqueta_runtime,
            self.etiqueta_ruta,
        ):
            etiqueta.setContentsMargins(4, 0, 4, 0)  # Mantiene el texto separado de los bordes interiores de cada etiqueta.

        self.etiqueta_ruta.setWordWrap(True)  # Evita ampliar la ventana por rutas extensas.

        diseno_estado.addWidget(self.etiqueta_instalacion)  # Agrega el estado físico.
        diseno_estado.addWidget(self.etiqueta_ejecucion)  # Agrega el estado actual de ejecución.
        diseno_estado.addWidget(self.etiqueta_modelo)  # Agrega el modelo configurado.
        diseno_estado.addWidget(self.etiqueta_runtime)  # Agrega la versión del motor cuya integridad está fijada.
        diseno_estado.addWidget(self.etiqueta_ruta)  # Agrega la ubicación local.
        diseno.addWidget(panel_estado)  # Incorpora la tarjeta informativa a la sección.

        panel_autocompletado = QFrame()  # Agrupa específicamente la preferencia relacionada con ghost text.
        panel_autocompletado.setObjectName("TarjetaConfiguracion")  # Reutiliza el diseño visual común de configuración.
        diseno_autocompletado = QVBoxLayout(panel_autocompletado)  # Organiza título y opción principal.
        diseno_autocompletado.setContentsMargins(22, 16, 22, 16)  # Mantiene una separación lateral y vertical clara respecto al borde.
        diseno_autocompletado.setSpacing(8)  # Mantiene próximos título y control.

        subtitulo_autocompletado = QLabel("Autocompletado")  # Identifica la opción que controla el ghost text.
        subtitulo_autocompletado.setObjectName("SubtituloConfiguracion")  # Mantiene coherencia visual entre bloques.
        subtitulo_autocompletado.setContentsMargins(4, 0, 4, 0)  # Añade padding interior al texto del encabezado.
        diseno_autocompletado.addWidget(subtitulo_autocompletado)  # Coloca el nombre antes del control.

        fila_activacion = QHBoxLayout()  # Coloca casilla, texto y espacio restante en una sola fila.
        fila_activacion.setContentsMargins(4, 2, 4, 2)  # Evita que casilla y texto queden pegados al límite de la zona interior.
        fila_activacion.setSpacing(9)  # Mantiene la marca cerca de su descripción.

        self.boton_activar = BotonCasillaIA(self)  # Crea la casilla personalizada con marca visible.
        self.etiqueta_activar = QLabel("Activar autocompletado con IA")  # Explica claramente qué controla la selección.
        self.etiqueta_activar.setObjectName("TextoConfiguracion")  # Mantiene el aspecto normal del contenido.
        self.etiqueta_activar.setContentsMargins(2, 0, 2, 0)  # Mantiene una pequeña separación interna alrededor del texto.

        fila_activacion.addWidget(self.boton_activar)  # Coloca primero el control interactivo.
        fila_activacion.addWidget(self.etiqueta_activar)  # Coloca inmediatamente después su descripción.
        fila_activacion.addStretch()  # Mantiene el conjunto alineado hacia la izquierda.

        diseno_autocompletado.addLayout(fila_activacion)  # Incorpora la opción de activación.
        diseno.addWidget(panel_autocompletado)  # Incorpora la segunda tarjeta completa.

        panel_componente = QFrame()  # Agrupa las operaciones relacionadas con los archivos físicos de la IA.
        panel_componente.setObjectName("TarjetaConfiguracion")  # Mantiene la misma composición visual de las otras secciones.
        diseno_componente = QVBoxLayout(panel_componente)  # Organiza descripción y zona intercambiable de administración.
        diseno_componente.setContentsMargins(22, 16, 22, 16)  # Proporciona padding real alrededor de todo el contenido de administración.
        diseno_componente.setSpacing(8)  # Mantiene una separación uniforme entre sus elementos.

        subtitulo_componente = QLabel("Administración del componente")  # Identifica las operaciones de instalación física.
        subtitulo_componente.setObjectName("SubtituloConfiguracion")  # Mantiene el estilo utilizado por los otros bloques.
        subtitulo_componente.setContentsMargins(4, 0, 4, 0)  # Separa el texto de los límites interiores de su etiqueta.
        diseno_componente.addWidget(subtitulo_componente)  # Coloca el nombre antes del texto explicativo.

        descripcion_componente = QLabel(
            "Instala o elimina el runtime y el modelo utilizados exclusivamente por TecNet Finder. "
            "El compilador principal funciona aunque este componente no se encuentre instalado."
        )  # Explica que la IA continúa siendo completamente opcional.
        descripcion_componente.setObjectName("DescripcionConfiguracion")  # Aplica el estilo secundario.
        descripcion_componente.setContentsMargins(4, 2, 4, 2)  # Mantiene el párrafo separado de los bordes de su región.
        descripcion_componente.setWordWrap(True)  # Permite mostrar la explicación en varias líneas.
        diseno_componente.addWidget(descripcion_componente)  # Coloca la explicación encima de las acciones.

        self.zona_administracion = QStackedWidget()  # Reserva una única región que alternará entre botones y progreso.
        self.zona_administracion.setFixedHeight(66)  # Proporciona espacio suficiente para márgenes internos sin modificar el tamaño general.
        diseno_componente.addWidget(self.zona_administracion)  # Incorpora una sola región estable al diseño de la tarjeta.

        pagina_botones = QWidget()  # Representa el estado normal de administración.
        diseno_botones = QHBoxLayout(pagina_botones)  # Organiza horizontalmente instalación y desinstalación.
        diseno_botones.setContentsMargins(8, 8, 8, 8)  # Aleja botones de todos los límites de la página interior.
        diseno_botones.setSpacing(12)  # Mantiene una separación visual clara entre las acciones.

        self.boton_instalar = QPushButton("Instalar componente")  # Permite obtener runtime y modelo cuando todavía no existen.
        self.boton_instalar.setObjectName("BotonPrincipal")  # Destaca la instalación como acción principal cuando se encuentre disponible.
        self.boton_desinstalar = QPushButton("Desinstalar componente")  # Permite liberar completamente el espacio ocupado por la IA.

        self.boton_instalar.clicked.connect(self._solicitar_instalacion)  # Solicita confirmación antes de iniciar una descarga de varios gigabytes.
        self.boton_desinstalar.clicked.connect(self._solicitar_desinstalacion)  # Solicita confirmación antes de eliminar runtime y modelo.

        diseno_botones.addWidget(self.boton_instalar)  # Coloca la instalación como primera acción.
        diseno_botones.addWidget(self.boton_desinstalar)  # Coloca la desinstalación inmediatamente después.
        diseno_botones.addStretch()  # Mantiene ambas acciones alineadas hacia la izquierda.

        pagina_progreso = QWidget()  # Representa el mismo espacio durante instalaciones y desinstalaciones.
        diseno_progreso = QVBoxLayout(pagina_progreso)  # Organiza descripción y barra dentro de la zona ya reservada.
        diseno_progreso.setContentsMargins(8, 5, 8, 5)  # Separa texto y barra de los cuatro límites del contenedor interior.
        diseno_progreso.setSpacing(6)  # Mantiene próxima la etapa actual a su barra correspondiente.

        self.etiqueta_progreso = QLabel("Preparando operación...")  # Muestra la fase específica que se está ejecutando.
        self.etiqueta_progreso.setObjectName("DescripcionConfiguracion")  # Mantiene la apariencia secundaria del panel.
        self.etiqueta_progreso.setContentsMargins(4, 0, 4, 0)  # Evita que la descripción comience pegada al límite izquierdo.
        self.etiqueta_progreso.setWordWrap(False)  # Conserva una sola línea dentro del espacio fijo reservado.
        diseno_progreso.addWidget(self.etiqueta_progreso)  # Coloca la descripción antes de la barra.

        self.barra_progreso = BarraProgresoIA()  # Utiliza la variante capaz de colorear dinámicamente el porcentaje según el avance.
        self.barra_progreso.setRange(0, 100)  # Utiliza inicialmente progreso determinado.
        self.barra_progreso.setValue(0)  # Comienza desde cero antes de cualquier instalación.
        self.barra_progreso.setFixedHeight(18)  # Mantiene la barra compacta dentro del espacio reservado.
        self.barra_progreso.setStyleSheet(
            """
            QProgressBar {
                background-color: #11111b;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 0px;
            }

            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 5px;
            }
            """
        )  # Mantiene la apariencia actual mientras el porcentaje personalizado se dibuja por encima.
        diseno_progreso.addWidget(self.barra_progreso)  # Coloca la barra debajo de la descripción de la etapa.

        self.zona_administracion.addWidget(pagina_botones)  # Registra como primera página las acciones utilizadas normalmente.
        self.zona_administracion.addWidget(pagina_progreso)  # Registra como segunda página la información utilizada durante operaciones largas.
        self.zona_administracion.setCurrentIndex(0)  # Muestra inicialmente los botones sin alterar la geometría.

        diseno.addWidget(panel_componente)  # Incorpora la tarjeta de administración.
        diseno.addStretch()  # Mantiene el contenido agrupado hacia la parte superior del panel.

        self.boton_activar.toggled.connect(self._cambiar_activacion)  # Procesa las decisiones después de actualizar visualmente la marca.

    def _actualizar_estado(self) -> None:
        instalado = self.componente_ia.instalado()  # Comprueba únicamente los archivos administrados del runtime y el modelo.

        self.etiqueta_instalacion.setText(f"Estado de instalación: {'Instalada' if instalado else 'No instalada'}")  # Presenta explícitamente la situación física.
        self.etiqueta_instalacion.setObjectName("EstadoIACorrecto" if instalado else "EstadoIANeutral")  # Distingue visualmente presencia y ausencia.

        if self.asistencia_disponible and instalado:
            self.etiqueta_ejecucion.setText("Estado de ejecución: Activa")  # Representa el estado conocido por la aplicación.
            self.etiqueta_ejecucion.setObjectName("EstadoIACorrecto")  # Utiliza la apariencia positiva.
        elif instalado and self.preferencias_ia.asistencia_activada():
            self.etiqueta_ejecucion.setText("Estado de ejecución: No disponible")  # Indica que se deseaba utilizar pero el servicio no se encuentra operativo.
            self.etiqueta_ejecucion.setObjectName("EstadoIAAdvertencia")  # Utiliza un estado de atención.
        else:
            self.etiqueta_ejecucion.setText("Estado de ejecución: Inactiva")  # Representa la característica detenida o físicamente ausente.
            self.etiqueta_ejecucion.setObjectName("EstadoIANeutral")  # Utiliza una apariencia neutra.

        self.etiqueta_ruta.setText(f"Ubicación: {self.componente_ia.ruta_base}")  # Informa dónde reside el componente opcional.

        self.actualizando_controles = True  # Evita que sincronizar visualmente el control produzca otra operación.
        self.boton_activar.setChecked(instalado and self.asistencia_disponible)  # Refleja el estado efectivo conocido de esta ejecución.
        self.actualizando_controles = False  # Permite nuevamente procesar decisiones reales.

        controles_habilitados = not self.operacion_en_curso  # Impide cualquier administración simultánea mientras existe un trabajo pendiente.
        self.boton_activar.setEnabled(instalado and controles_habilitados)  # Solo permite encender o apagar una instalación completa.
        self.boton_instalar.setEnabled(not instalado and controles_habilitados)  # Solo ofrece instalación cuando el componente todavía no existe.
        self.boton_desinstalar.setEnabled(instalado and controles_habilitados)  # Solo ofrece eliminación cuando existen archivos administrados.

        for etiqueta in (self.etiqueta_instalacion, self.etiqueta_ejecucion):
            etiqueta.style().unpolish(etiqueta)  # Retira temporalmente el estilo anterior.
            etiqueta.style().polish(etiqueta)  # Aplica la apariencia correspondiente al nuevo estado.
            etiqueta.update()  # Solicita el redibujado inmediato.

    def _cambiar_activacion(self, activar: bool) -> None:
        if self.actualizando_controles or self.operacion_en_curso:
            return  # Ignora cambios internos o clics durante una operación ya iniciada.

        if activar:
            self._iniciar_operacion("activar")  # Inicia el servicio en segundo plano mientras la marca ya se encuentra visible.
            return  # Evita ejecutar también la ruta correspondiente a la desactivación.

        guardado = self.preferencias_ia.establecer_asistencia_activada(False)  # Conserva inmediatamente la decisión de dejar de utilizar IA.
        self.asistencia_disponible = False  # Desactiva lógicamente la característica sin esperar al cierre del proceso.
        self.activacion_cambiada.emit(False)  # Detiene inmediatamente nuevas solicitudes desde el editor.

        if not guardado:
            QMessageBox.warning(
                self,
                "Preferencias",
                "La asistencia se desactivó para esta ejecución, pero no fue posible guardar la preferencia.",
            )  # Informa únicamente un problema de persistencia.

        self._iniciar_operacion("desactivar")  # Cierra los procesos en otro hilo sin congelar la interfaz.

    def _preguntar_confirmacion(self, titulo: str, mensaje: str) -> bool:
        dialogo = QMessageBox(self)  # Crea un cuadro controlado para poder personalizar los textos de sus botones.
        dialogo.setWindowTitle(titulo)  # Conserva el mismo título utilizado anteriormente por QMessageBox.question.
        dialogo.setIcon(QMessageBox.Icon.Question)  # Mantiene el icono de interrogación propio de una confirmación.
        dialogo.setText(mensaje)  # Coloca el contenido correspondiente a instalar o desinstalar.
        dialogo.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)  # Conserva semánticamente los botones estándar de confirmación.
        dialogo.setDefaultButton(QMessageBox.StandardButton.No)  # Mantiene No como decisión predeterminada para evitar operaciones accidentales.

        boton_si = dialogo.button(QMessageBox.StandardButton.Yes)  # Obtiene el botón afirmativo creado por Qt.
        boton_no = dialogo.button(QMessageBox.StandardButton.No)  # Obtiene el botón negativo creado por Qt.

        if boton_si is not None:
            boton_si.setText("Sí")  # Traduce explícitamente la acción afirmativa al español.

        if boton_no is not None:
            boton_no.setText("No")  # Mantiene explícitamente la acción negativa en español.

        dialogo.exec()  # Muestra la confirmación de forma modal igual que la implementación anterior.

        return dialogo.standardButton(dialogo.clickedButton()) == QMessageBox.StandardButton.Yes  # Considera aceptada la operación solamente cuando se seleccionó Sí.

    def _solicitar_instalacion(self) -> None:
        if self.operacion_en_curso or self.componente_ia.instalado():
            return  # Evita iniciar otra descarga cuando no corresponde.

        confirmado = self._preguntar_confirmacion(
            "Instalar asistencia de IA",
            "TecNet Finder descargará aproximadamente 2.5 GB entre el runtime local y el modelo.\n\n"
            "La instalación se guardará únicamente en los datos locales de TecNet Finder y puede tardar varios minutos.\n\n"
            "¿Deseas continuar?",
        )  # Solicita una decisión explícita con botones traducidos completamente al español.

        if not confirmado:
            return  # Abandona completamente la operación cuando el usuario decidió no instalar.

        self._iniciar_operacion("instalar")  # Entrega descarga, verificación y modelo al hilo secundario.

    def _solicitar_desinstalacion(self) -> None:
        if self.operacion_en_curso or not self.componente_ia.instalado():
            return  # Evita eliminar durante otra operación o cuando no existe componente.

        confirmado = self._preguntar_confirmacion(
            "Desinstalar asistencia de IA",
            "Se eliminarán el runtime local de Ollama y el modelo utilizado por TecNet Finder.\n\n"
            "El compilador seguirá funcionando normalmente y podrás volver a instalar la asistencia más adelante.\n\n"
            "¿Deseas desinstalar el componente?",
        )  # Solicita confirmación utilizando Sí y No sin depender del idioma configurado por Qt.

        if not confirmado:
            return  # Conserva completamente la instalación cuando el usuario cancela.

        self.preferencias_ia.establecer_asistencia_activada(False)  # Evita volver a iniciar automáticamente un componente que está a punto de desaparecer.
        self.asistencia_disponible = False  # Desactiva lógicamente las sugerencias antes de comenzar la eliminación física.
        self.activacion_cambiada.emit(False)  # Detiene inmediatamente cualquier nueva solicitud desde el editor.
        self._sincronizar_casilla_desactivada()  # Retira la marca visual antes de iniciar la operación larga.
        self._iniciar_operacion("desinstalar")  # Realiza cierre y eliminación dentro del hilo secundario.

    def _sincronizar_casilla_desactivada(self) -> None:
        self.actualizando_controles = True  # Impide que modificar programáticamente la casilla vuelva a iniciar otra operación.
        self.boton_activar.setChecked(False)  # Retira inmediatamente la marca porque el autocompletado ya fue desactivado lógicamente.
        self.actualizando_controles = False  # Recupera el procesamiento normal de decisiones del usuario.

    def _iniciar_operacion(self, operacion: str) -> None:
        self.operacion_en_curso = True  # Impide iniciar otra operación simultánea.
        self.operacion_cambiada.emit(True)  # Solicita a la ventana general impedir temporalmente su cierre.
        self.boton_activar.setEnabled(False)  # Evita clics repetidos durante cualquier transición.
        self.boton_instalar.setEnabled(False)  # Evita comenzar una instalación adicional.
        self.boton_desinstalar.setEnabled(False)  # Evita eliminar mientras existe otra modificación pendiente.

        if operacion == "activar":
            self.etiqueta_ejecucion.setText("Estado de ejecución: Activando...")  # Proporciona retroalimentación mientras Ollama inicia.
        elif operacion == "desactivar":
            self.etiqueta_ejecucion.setText("Estado de ejecución: Desactivando...")  # Informa que los procesos están cerrándose.
        elif operacion == "instalar":
            self.etiqueta_ejecucion.setText("Estado de ejecución: Instalando componente...")  # Indica que todavía no puede utilizarse la IA.
            self._mostrar_progreso(True)  # Sustituye temporalmente los botones por la zona de progreso.
        elif operacion == "desinstalar":
            self.etiqueta_ejecucion.setText("Estado de ejecución: Desinstalando componente...")  # Indica que la asistencia está siendo retirada.
            self._mostrar_progreso(True)  # Sustituye temporalmente los botones por la zona de progreso.

        self.etiqueta_ejecucion.setObjectName("EstadoIAAdvertencia")  # Utiliza un color intermedio durante cualquier transición.
        self.etiqueta_ejecucion.style().unpolish(self.etiqueta_ejecucion)  # Retira la apariencia anterior.
        self.etiqueta_ejecucion.style().polish(self.etiqueta_ejecucion)  # Aplica el estado visual temporal.
        self.etiqueta_ejecucion.update()  # Redibuja antes de iniciar el trabajo.

        trabajo = TrabajoOperacionIA(
            operacion,
            self.gestor_ollama,
            self.gestor_instalacion,
        )  # Prepara una única operación utilizando los gestores compartidos.

        trabajo.senales.progreso.connect(self._actualizar_progreso)  # Mantiene visible el avance de descargas y extracción.
        trabajo.senales.terminada.connect(self._finalizar_operacion)  # Regresa al panel cuando finaliza el trabajo.
        self.trabajo_actual = trabajo  # Conserva una referencia explícita durante toda la ejecución.
        self.hilos.start(trabajo)  # Entrega la operación al hilo secundario.

    @Slot(str, object)
    def _actualizar_progreso(self, etapa: str, porcentaje) -> None:
        self.etiqueta_progreso.setText(etapa)  # Muestra la fase actual utilizando un texto comprensible para el usuario.

        if porcentaje is None:
            self.barra_progreso.setRange(0, 0)  # Utiliza animación indeterminada cuando la etapa no ofrece un porcentaje confiable.
            return  # Evita asignar un valor inexistente durante esta fase.

        self.barra_progreso.setRange(0, 100)  # Recupera el modo determinado cuando existe avance cuantificable.
        self.barra_progreso.setValue(max(0, min(int(porcentaje), 100)))  # Limita cualquier valor recibido al rango representable.

    @Slot(str, bool, str)
    def _finalizar_operacion(self, operacion: str, resultado: bool, mensaje: str) -> None:
        self.operacion_en_curso = False  # Permite nuevamente utilizar los controles.
        self.operacion_cambiada.emit(False)  # Permite nuevamente cerrar la ventana general.
        self.trabajo_actual = None  # Libera la referencia al trabajo terminado.

        tipo_mensaje = None  # Permite actualizar primero toda la interfaz antes de mostrar un diálogo modal.
        titulo_mensaje = ""  # Conserva el título correspondiente al resultado definitivo.
        texto_mensaje = ""  # Conserva el texto que se mostrará después de repintar el panel.

        if operacion == "activar":
            if resultado:
                self.asistencia_disponible = True  # Registra que Ollama respondió correctamente.
                guardado = self.preferencias_ia.establecer_asistencia_activada(True)  # Conserva la elección para próximos inicios.
                self.activacion_cambiada.emit(True)  # Permite que el editor vuelva a utilizar ghost text.

                if not guardado:
                    tipo_mensaje = "advertencia"  # Programa una advertencia sin interrumpir todavía la actualización visual.
                    titulo_mensaje = "Preferencias"  # Identifica que solamente falló la persistencia de la elección.
                    texto_mensaje = "La asistencia se activó para esta ejecución, pero no fue posible guardar la preferencia."  # Explica que la función actual sí continúa operativa.
            else:
                self.asistencia_disponible = False  # Conserva desactivada la característica cuando Ollama no pudo iniciar.
                self.preferencias_ia.establecer_asistencia_activada(False)  # Evita intentarlo automáticamente la próxima vez.
                self.activacion_cambiada.emit(False)  # Mantiene detenido también el autocompletado.
                tipo_mensaje = "advertencia"  # Programa el aviso después de que el panel refleje el fallo.
                titulo_mensaje = "Asistencia de IA"  # Identifica la función que no pudo iniciarse.
                texto_mensaje = mensaje  # Conserva la explicación producida por el trabajo.

        elif operacion == "desactivar":
            self.asistencia_disponible = False  # Mantiene lógicamente apagada la asistencia.

            if not resultado:
                tipo_mensaje = "advertencia"  # Programa únicamente los fallos de cierre.
                titulo_mensaje = "Asistencia de IA"  # Identifica el servicio afectado.
                texto_mensaje = mensaje  # Conserva la explicación producida durante la limpieza.

        elif operacion == "instalar":
            if resultado:
                self.asistencia_disponible = True  # Aprovecha la instancia que quedó activa después de descargar el modelo.
                guardado = self.preferencias_ia.establecer_asistencia_activada(True)  # Hace que la nueva instalación permanezca habilitada en futuros inicios.
                self.activacion_cambiada.emit(True)  # Activa inmediatamente el ghost text sin reiniciar TecNet Finder.
                tipo_mensaje = "informacion"  # Programa la confirmación para después del repintado.
                titulo_mensaje = "Asistencia de IA"  # Identifica la instalación terminada.
                texto_mensaje = mensaje  # Conserva el mensaje producido por el gestor.

                if not guardado:
                    tipo_mensaje = "advertencia"  # Prioriza advertir que la nueva instalación no pudo conservar su preferencia.
                    titulo_mensaje = "Preferencias"  # Identifica que el componente sí quedó instalado físicamente.
                    texto_mensaje = "El componente se instaló, pero no fue posible guardar que la asistencia debe iniciar automáticamente."  # Explica exactamente qué parte quedó pendiente.
            else:
                self.asistencia_disponible = False  # Conserva desactivado el editor después de una instalación fallida.
                self.preferencias_ia.establecer_asistencia_activada(False)  # Evita intentos automáticos sobre un componente incompleto.
                self.activacion_cambiada.emit(False)  # Mantiene detenido el autocompletado.
                tipo_mensaje = "advertencia"  # Programa la explicación después de restaurar visualmente los botones.
                titulo_mensaje = "Instalación de IA"  # Identifica la operación que no pudo completarse.
                texto_mensaje = mensaje  # Conserva la causa reportada por el gestor.

        elif operacion == "desinstalar":
            self.asistencia_disponible = False  # Mantiene la asistencia apagada después del intento de eliminación.
            self.preferencias_ia.establecer_asistencia_activada(False)  # Conserva el comportamiento seguro incluso si Windows impidió borrar algún archivo.
            self.activacion_cambiada.emit(False)  # Mantiene detenido el autocompletado.
            self._sincronizar_casilla_desactivada()  # Garantiza que la marca continúe apagada independientemente del resultado físico.

            if resultado:
                tipo_mensaje = "informacion"  # Programa la confirmación después de mostrar que el componente ya no existe.
                titulo_mensaje = "Asistencia de IA"  # Identifica la eliminación completada.
                texto_mensaje = mensaje  # Conserva el mensaje de éxito producido por el gestor.
            else:
                tipo_mensaje = "advertencia"  # Programa el fallo después de reflejar el estado real que todavía permanece instalado.
                titulo_mensaje = "Desinstalación de IA"  # Identifica la operación afectada.
                texto_mensaje = mensaje  # Conserva la explicación concreta del problema.

        self._mostrar_progreso(False)  # Recupera primero la página normal de botones dentro del mismo espacio reservado.
        self._actualizar_estado()  # Sincroniza completamente etiquetas, casilla y acciones antes de abrir cualquier mensaje modal.

        if tipo_mensaje == "informacion":
            QMessageBox.information(self, titulo_mensaje, texto_mensaje)  # Muestra el éxito solamente cuando la interfaz ya representa el resultado definitivo.
        elif tipo_mensaje == "advertencia":
            QMessageBox.warning(self, titulo_mensaje, texto_mensaje)  # Muestra el problema solamente después de actualizar visualmente el panel.

    def _mostrar_progreso(self, mostrar: bool) -> None:
        if mostrar:
            self.etiqueta_progreso.setText("Preparando operación...")  # Proporciona retroalimentación incluso antes de la primera actualización del hilo.
            self.barra_progreso.setRange(0, 0)  # Comienza en modo indeterminado hasta conocer la primera fase cuantificable.
            self.zona_administracion.setCurrentIndex(1)  # Sustituye los botones por el progreso dentro del mismo espacio físico.
            return  # Conserva la zona de progreso hasta que termine la operación.

        self.zona_administracion.setCurrentIndex(0)  # Recupera los botones sin modificar la geometría de la tarjeta.
        self.etiqueta_progreso.setText("Preparando operación...")  # Deja lista una descripción inicial para el siguiente trabajo.
        self.barra_progreso.setRange(0, 100)  # Recupera la configuración determinada para futuras transferencias.
        self.barra_progreso.setValue(0)  # Reinicia completamente cualquier avance perteneciente al trabajo anterior.