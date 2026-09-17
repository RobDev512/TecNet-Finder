# ============================================================
# Archivo: panel_configuracion_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el panel de configuración dedicado a las
# funciones opcionales de inteligencia artificial local.
#
# Autocompletado y mejora de soluciones pueden activarse de forma
# independiente. Ollama permanece activo mientras al menos una
# función lo requiera y las operaciones pesadas continúan
# ejecutándose fuera del hilo gráfico.
#
# La barra de progreso representa el porcentaje mediante texto
# cuyo color cambia dinámicamente al ser cubierto por el avance.
# ============================================================



from PySide6.QtCore import QObject, QRect, QRunnable, QThreadPool, Qt, Signal, Slot  # Permite controlar geometría, señales y trabajos ejecutados fuera del hilo gráfico.
from PySide6.QtGui import QColor, QPainter, QPixmap  # Permite dibujar el progreso y cargar los recursos gráficos asociados con las funciones de IA.
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton, QStackedWidget, QStyle, QVBoxLayout, QWidget  # Importa los controles utilizados por el panel.

from AsistenteIA.infraestructura.configuracion import MODELO_IA  # Permite mostrar el modelo técnico utilizado actualmente.
from AsistenteIA.infraestructura.gestor_componente_ia import GestorComponenteIA  # Permite consultar la instalación opcional administrada.
from AsistenteIA.infraestructura.gestor_instalacion_ia import GestorInstalacionIA, VERSION_OLLAMA  # Permite instalar y retirar físicamente el componente opcional.
from AsistenteIA.infraestructura.gestor_ollama import GestorOllama  # Permite iniciar y detener la instancia privada.
from AsistenteIA.preferencias.preferencias_ia import PreferenciasIA  # Permite conservar independientemente las funciones solicitadas por el usuario.
from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona los indicadores gráficos iniciales utilizados por las funciones de IA.
from Motor.configuracion.catalogo_temas import TEMA_PREDETERMINADO, obtener_tema  # Permite construir botones de confirmación con los colores reales del tema activo.

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
                resultado = self.gestor_ollama.iniciar()  # Inicia el servicio porque al menos una función acaba de solicitarlo.
                mensaje = "La asistencia de IA se activó correctamente." if resultado else "No fue posible iniciar la asistencia de IA local."  # Prepara una explicación sencilla del resultado.
            elif self.operacion == "desactivar":
                self.gestor_ollama.detener()  # Cierra Ollama solamente cuando ninguna función continúa utilizándolo.
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
    def __init__(self, nombre_accesible: str, padre=None):
        super().__init__(padre)  # Inicializa el botón utilizado como control de selección.
        self.setCheckable(True)  # Permite conservar explícitamente los estados activado y desactivado.
        self.setFixedSize(24, 24)  # Mantiene una apariencia compacta similar a una casilla.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que el control puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Conserva una descripción específica para cada función disponible.
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
    autocompletado_cambiado = Signal(bool)  # Comunica al editor si puede comenzar o debe dejar de solicitar sugerencias.
    diagnosticos_ia_cambiados = Signal(bool)  # Comunica al panel de diagnósticos si debe mejorar automáticamente las soluciones.
    servicio_cambiado = Signal(bool)  # Informa si la instancia privada se encuentra realmente disponible para las funciones activas.
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
        self.autocompletado_solicitado = preferencias_ia.autocompletado_activado()  # Conserva la decisión independiente correspondiente al ghost text.
        self.diagnosticos_solicitados = preferencias_ia.diagnosticos_ia_activados()  # Conserva la decisión independiente correspondiente a las soluciones.
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
            "Administra las funciones inteligentes de TecNet Finder. "
            "El procesamiento se realiza localmente en este equipo."
        )  # Explica brevemente que ambas funciones comparten la misma infraestructura privada.
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
        self.etiqueta_modelo.setObjectName("DetalleIA")  # Permite restaurar un fondo sutil y redondeado para los datos técnicos.
        self.etiqueta_runtime = QLabel(f"Runtime local: Ollama {VERSION_OLLAMA}")  # Informa la versión fijada por TecNet Finder.
        self.etiqueta_runtime.setObjectName("DetalleIA")  # Mantiene el mismo tratamiento visual del resto de datos técnicos.
        self.etiqueta_ruta = QLabel()  # Muestra la ubicación administrada del componente.
        self.etiqueta_ruta.setObjectName("DetalleIA")  # Identifica la ruta como un dato técnico dentro de la misma tarjeta.

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

        panel_funciones = QFrame()  # Agrupa las preferencias que utilizan el mismo servicio local.
        panel_funciones.setObjectName("TarjetaConfiguracion")  # Reutiliza el diseño visual común de configuración.
        diseno_funciones = QVBoxLayout(panel_funciones)  # Organiza título y ambas funciones independientes.
        diseno_funciones.setContentsMargins(22, 16, 22, 16)  # Mantiene una separación lateral y vertical clara respecto al borde.
        diseno_funciones.setSpacing(9)  # Mantiene próximas las dos opciones relacionadas.

        subtitulo_funciones = QLabel("Funciones de IA")  # Identifica el grupo que controla el uso del modelo.
        subtitulo_funciones.setObjectName("SubtituloConfiguracion")  # Mantiene coherencia visual entre bloques.
        subtitulo_funciones.setContentsMargins(4, 0, 4, 0)  # Añade padding interior al texto del encabezado.
        diseno_funciones.addWidget(subtitulo_funciones)  # Coloca el nombre antes de los controles.

        fila_autocompletado = QHBoxLayout()  # Coloca casilla, texto y espacio restante en una sola fila.
        fila_autocompletado.setContentsMargins(4, 2, 4, 2)  # Evita que la primera opción quede pegada al límite de la zona interior.
        fila_autocompletado.setSpacing(9)  # Mantiene la marca cerca de su descripción.

        self.boton_autocompletado = BotonCasillaIA("Activar autocompletado con IA", self)  # Crea la casilla dedicada exclusivamente al ghost text.
        self.etiqueta_autocompletado = QLabel("Activar autocompletado con IA")  # Explica claramente qué controla la primera selección.
        self.etiqueta_autocompletado.setObjectName("TextoConfiguracion")  # Mantiene el aspecto normal del contenido.
        self.etiqueta_autocompletado.setContentsMargins(2, 0, 2, 0)  # Mantiene una pequeña separación interna alrededor del texto.
        self.icono_autocompletado = self._crear_etiqueta_icono("Autocompletado.png", "Indicador visual del autocompletado generado por IA")  # Identifica la misma función mediante el recurso utilizado dentro del editor.

        fila_autocompletado.addWidget(self.boton_autocompletado)  # Coloca primero el control interactivo.
        fila_autocompletado.addWidget(self.etiqueta_autocompletado)  # Coloca inmediatamente después su descripción.
        fila_autocompletado.addWidget(self.icono_autocompletado)  # Añade el icono al final del nombre sin separarlo innecesariamente hacia el borde de la tarjeta.
        fila_autocompletado.addStretch()  # Mantiene el conjunto alineado hacia la izquierda.
        diseno_funciones.addLayout(fila_autocompletado)  # Incorpora la primera función al grupo.

        fila_diagnosticos = QHBoxLayout()  # Crea una segunda fila independiente sin aumentar el ancho de la tarjeta.
        fila_diagnosticos.setContentsMargins(4, 2, 4, 2)  # Mantiene la misma alineación horizontal que el autocompletado.
        fila_diagnosticos.setSpacing(9)  # Conserva la misma distancia entre casilla y descripción.

        self.boton_diagnosticos = BotonCasillaIA("Mejorar soluciones de diagnósticos con IA", self)  # Crea la preferencia destinada a errores y advertencias detectados.
        self.etiqueta_diagnosticos = QLabel("Mejorar soluciones de diagnósticos con IA")  # Describe la generación automática que aparecerá en la columna Solución.
        self.etiqueta_diagnosticos.setObjectName("TextoConfiguracion")  # Mantiene el estilo común del resto de opciones.
        self.etiqueta_diagnosticos.setContentsMargins(2, 0, 2, 0)  # Conserva el mismo padding visual que la primera fila.
        self.icono_diagnosticos = self._crear_etiqueta_icono("Asistente_ia.png", "Indicador visual de la mejora de diagnósticos mediante IA")  # Relaciona esta preferencia con el mismo símbolo utilizado en la tabla de soluciones.

        fila_diagnosticos.addWidget(self.boton_diagnosticos)  # Coloca la segunda casilla en el mismo eje horizontal.
        fila_diagnosticos.addWidget(self.etiqueta_diagnosticos)  # Coloca su explicación inmediatamente después.
        fila_diagnosticos.addWidget(self.icono_diagnosticos)  # Añade el indicador al final del nombre de la función.
        fila_diagnosticos.addStretch()  # Mantiene la opción alineada hacia la izquierda.
        diseno_funciones.addLayout(fila_diagnosticos)  # Incorpora la mejora automática debajo del autocompletado.

        diseno.addWidget(panel_funciones)  # Incorpora la tarjeta completa de funciones.

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

        self.marco_administracion = QFrame()  # Crea un contenedor interior para recuperar el recuadro redondeado de la zona de acciones.
        self.marco_administracion.setObjectName("MarcoAdministracionIA")  # Permite tematizar esta región sin afectar el resto de la tarjeta.
        diseno_marco_administracion = QVBoxLayout(self.marco_administracion)  # Organiza la zona intercambiable dentro del mismo marco.
        diseno_marco_administracion.setContentsMargins(0, 0, 0, 0)  # Deja que el propio estilo controle completamente el padding visual.
        diseno_marco_administracion.setSpacing(0)  # Evita espacios extra entre el marco y la página activa.

        self.zona_administracion = QStackedWidget()  # Reserva una única región que alternará entre botones y progreso.
        self.zona_administracion.setObjectName("ZonaAdministracionIA")  # Identifica la región apilada que vive dentro del marco redondeado.
        self.zona_administracion.setFixedHeight(66)  # Proporciona espacio suficiente para márgenes internos sin modificar el tamaño general.
        diseno_marco_administracion.addWidget(self.zona_administracion)  # Inserta la zona intercambiable dentro del contenedor estilizado.
        diseno_componente.addWidget(self.marco_administracion)  # Incorpora finalmente la región estable de administración.

        pagina_botones = QWidget()  # Representa el estado normal de administración.
        pagina_botones.setObjectName("PaginaAdministracionIA")  # Hace transparente esta página para dejar visible el fondo redondeado de la tarjeta principal.
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
        pagina_progreso.setObjectName("PaginaAdministracionIA")  # Mantiene también transparente la página de progreso para evitar que reaparezca el rectángulo cuadrado.
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

        self.boton_autocompletado.toggled.connect(self._cambiar_autocompletado)  # Procesa únicamente la preferencia del ghost text.
        self.boton_diagnosticos.toggled.connect(self._cambiar_diagnosticos)  # Procesa únicamente la preferencia de soluciones automáticas.

    def _crear_etiqueta_icono(self, nombre_archivo: str, ayuda: str) -> QLabel:
        etiqueta = QLabel(self)  # Crea un indicador puramente informativo que no altera el comportamiento de la opción asociada.
        etiqueta.setFixedSize(20, 20)  # Reserva un espacio pequeño y uniforme junto al nombre de cada función.
        etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Mantiene el PNG centrado dentro de su propia región.
        etiqueta.setToolTip(ayuda)  # Explica por qué aparece el símbolo sin añadir texto permanente a la fila.
        etiqueta.setStyleSheet("background-color: transparent; border: none; padding: 0px;")  # Evita que el estilo general de las tarjetas dibuje un recuadro detrás del icono.
        ruta = ruta_icono_oscuro(nombre_archivo)  # Recupera el recurso inicial mediante la estructura centralizada de iconos.
        if ruta.exists():
            imagen = QPixmap(str(ruta))  # Carga el PNG original conservando su transparencia.
            etiqueta.setPixmap(imagen.scaled(17, 17, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))  # Reduce el recurso con suavizado para que acompañe al texto sin dominarlo.
        return etiqueta  # Devuelve el control listo para insertarse al final de la fila correspondiente.

    def _actualizar_estado(self) -> None:
        instalado = self.componente_ia.instalado()  # Comprueba únicamente los archivos administrados del runtime y el modelo.

        self.etiqueta_instalacion.setText(f"Estado de instalación: {'Instalada' if instalado else 'No instalada'}")  # Presenta explícitamente la situación física.
        self.etiqueta_instalacion.setObjectName("EstadoIACorrecto" if instalado else "EstadoIANeutral")  # Distingue visualmente presencia y ausencia.

        if self.asistencia_disponible and instalado:
            self.etiqueta_ejecucion.setText("Estado de ejecución: Activa")  # Representa que al menos una función dispone realmente del servicio local.
            self.etiqueta_ejecucion.setObjectName("EstadoIACorrecto")  # Utiliza la apariencia positiva.
        elif instalado and self._alguna_funcion_solicitada():
            self.etiqueta_ejecucion.setText("Estado de ejecución: No disponible")  # Indica que existe una función solicitada pero Ollama no respondió correctamente.
            self.etiqueta_ejecucion.setObjectName("EstadoIAAdvertencia")  # Utiliza un estado de atención.
        else:
            self.etiqueta_ejecucion.setText("Estado de ejecución: Inactiva")  # Representa el componente detenido o físicamente ausente.
            self.etiqueta_ejecucion.setObjectName("EstadoIANeutral")  # Utiliza una apariencia neutra.

        self.etiqueta_ruta.setText(f"Ubicación: {self.componente_ia.ruta_base}")  # Informa dónde reside el componente opcional.

        self.actualizando_controles = True  # Evita que sincronizar visualmente las casillas produzca nuevas operaciones.
        self.boton_autocompletado.setChecked(instalado and self.autocompletado_solicitado)  # Refleja la decisión específica cuando existe una instalación utilizable.
        self.boton_diagnosticos.setChecked(instalado and self.diagnosticos_solicitados)  # Refleja independientemente la decisión sobre soluciones automáticas.
        self.actualizando_controles = False  # Permite nuevamente procesar decisiones reales.

        controles_habilitados = instalado and not self.operacion_en_curso  # Impide modificar funciones cuando no existe componente o una operación todavía está activa.
        self.boton_autocompletado.setEnabled(controles_habilitados)  # Permite controlar el ghost text solamente sobre una instalación completa.
        self.boton_diagnosticos.setEnabled(controles_habilitados)  # Aplica la misma condición a la mejora de diagnósticos.
        self.boton_instalar.setEnabled(not instalado and not self.operacion_en_curso)  # Solo ofrece instalación cuando el componente todavía no existe.
        self.boton_desinstalar.setEnabled(instalado and not self.operacion_en_curso)  # Solo ofrece eliminación cuando existen archivos administrados.

        for etiqueta in (self.etiqueta_instalacion, self.etiqueta_ejecucion):
            etiqueta.style().unpolish(etiqueta)  # Retira temporalmente el estilo anterior.
            etiqueta.style().polish(etiqueta)  # Aplica la apariencia correspondiente al nuevo estado.
            etiqueta.update()  # Solicita el redibujado inmediato.

    def _cambiar_autocompletado(self, activar: bool) -> None:
        if self.actualizando_controles or self.operacion_en_curso:
            return  # Ignora sincronizaciones internas o clics mientras existe otra operación.

        self._cambiar_funcion("autocompletado", activar)  # Delega el ciclo de vida común conservando la identidad de la función.

    def _cambiar_diagnosticos(self, activar: bool) -> None:
        if self.actualizando_controles or self.operacion_en_curso:
            return  # Ignora sincronizaciones internas o clics mientras existe otra operación.

        self._cambiar_funcion("diagnosticos", activar)  # Reutiliza las mismas reglas sin vincular esta opción con el ghost text.

    def _cambiar_funcion(self, funcion: str, activar: bool) -> None:
        if funcion == "autocompletado":
            self.autocompletado_solicitado = bool(activar)  # Actualiza inmediatamente el estado utilizado durante esta ejecución.
            guardado = self.preferencias_ia.establecer_autocompletado_activado(activar)  # Conserva exclusivamente la primera función.
        else:
            self.diagnosticos_solicitados = bool(activar)  # Actualiza independientemente la mejora de diagnósticos.
            guardado = self.preferencias_ia.establecer_diagnosticos_ia_activados(activar)  # Conserva exclusivamente la segunda función.

        if not guardado:
            QMessageBox.warning(
                self,
                "Preferencias",
                "La opción cambió para esta ejecución, pero no fue posible guardar la preferencia.",
            )  # Informa un problema de persistencia sin impedir utilizar la elección actual.

        if not activar:
            self._emitir_funcion(funcion, False)  # Detiene inmediatamente nuevas solicitudes pertenecientes únicamente a la función apagada.

            if self.asistencia_disponible and not self._alguna_funcion_solicitada():
                self._iniciar_operacion("desactivar")  # Cierra Ollama únicamente cuando ninguna otra función continúa necesitándolo.
                return

            self._actualizar_estado()  # Conserva el servicio activo cuando la otra función todavía está habilitada.
            return

        if self.asistencia_disponible:
            self._emitir_funcion(funcion, True)  # Activa inmediatamente la nueva función porque el servicio compartido ya responde.
            self._actualizar_estado()  # Refleja la nueva selección sin reiniciar Ollama.
            return

        self._iniciar_operacion("activar")  # Inicia el servicio una sola vez y después habilita todas las funciones actualmente solicitadas.

    def _emitir_funcion(self, funcion: str, habilitada: bool) -> None:
        if funcion == "autocompletado":
            self.autocompletado_cambiado.emit(bool(habilitada))  # Comunica exclusivamente el estado efectivo del ghost text.
            return

        self.diagnosticos_ia_cambiados.emit(bool(habilitada))  # Comunica exclusivamente el estado efectivo de las soluciones automáticas.

    def _emitir_funciones_efectivas(self) -> None:
        instalado = self.componente_ia.instalado()  # Impide habilitar consumidores si la instalación dejó de estar completa.
        disponible = instalado and self.asistencia_disponible  # Exige simultáneamente archivos y servicio operativo.
        self.autocompletado_cambiado.emit(disponible and self.autocompletado_solicitado)  # Aplica la primera preferencia sobre el estado real.
        self.diagnosticos_ia_cambiados.emit(disponible and self.diagnosticos_solicitados)  # Aplica de forma independiente la segunda preferencia.

    def _alguna_funcion_solicitada(self) -> bool:
        return self.autocompletado_solicitado or self.diagnosticos_solicitados  # Decide el ciclo de vida de Ollama sin privilegiar una función concreta.

    def _preguntar_confirmacion(self, titulo: str, mensaje: str) -> bool:
        dialogo = QDialog(self)  # Crea una confirmación propia para evitar la apariencia nativa inconsistente de los botones estándar de QMessageBox.
        dialogo.setWindowTitle(titulo)  # Conserva el título correspondiente a instalación o desinstalación.
        dialogo.setModal(True)  # Impide interactuar con Configuración mientras la decisión siga pendiente.
        dialogo.setMinimumWidth(610)  # Mantiene espacio suficiente para el mensaje sin producir una ventana excesivamente alta.

        diseno_principal = QHBoxLayout(dialogo)  # Organiza el icono de confirmación y el contenido textual en una misma fila.
        diseno_principal.setContentsMargins(18, 16, 18, 16)  # Mantiene respiración uniforme respecto a los límites de la ventana.
        diseno_principal.setSpacing(18)  # Separa claramente el icono del bloque de contenido.

        etiqueta_icono = QLabel(dialogo)  # Reserva una zona exclusiva para el símbolo de interrogación.
        etiqueta_icono.setFixedSize(64, 64)  # Conserva una presencia visual similar a la del cuadro estándar anterior.
        etiqueta_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Mantiene el símbolo centrado.
        icono = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)  # Utiliza el icono estándar de confirmación proporcionado por Qt.
        etiqueta_icono.setPixmap(icono.pixmap(52, 52))  # Representa el símbolo con un tamaño claro sin dominar el diálogo.
        etiqueta_icono.setStyleSheet("background-color: transparent; border: none; padding: 0px;")  # Evita que los estilos generales añadan un fondo innecesario.
        diseno_principal.addWidget(etiqueta_icono, 0, Qt.AlignmentFlag.AlignTop)  # Coloca el icono alineado con el comienzo del mensaje.

        columna_contenido = QVBoxLayout()  # Agrupa mensaje y botones dentro de la zona derecha.
        columna_contenido.setContentsMargins(0, 0, 0, 0)  # Delega el margen exterior al diseño principal.
        columna_contenido.setSpacing(16)  # Separa el texto de las acciones de confirmación.

        etiqueta_mensaje = QLabel(mensaje, dialogo)  # Presenta íntegramente la explicación proporcionada por la operación.
        etiqueta_mensaje.setObjectName("TextoConfiguracion")  # Reutiliza el color de texto definido por el tema activo.
        etiqueta_mensaje.setWordWrap(True)  # Permite adaptar los párrafos cuando la ventana cambie de tamaño.
        etiqueta_mensaje.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # Permite copiar el mensaje sin convertirlo en un control editable.
        columna_contenido.addWidget(etiqueta_mensaje)  # Coloca primero la explicación completa.

        fila_botones = QHBoxLayout()  # Organiza las dos decisiones en una fila claramente reconocible.
        fila_botones.setContentsMargins(0, 0, 0, 0)  # Evita introducir márgenes adicionales dentro del bloque.
        fila_botones.setSpacing(10)  # Mantiene una separación visible entre ambas decisiones.
        fila_botones.addStretch()  # Empuja las acciones hacia la derecha, igual que un diálogo convencional.

        preferencias_tema_temporales = getattr(self.window(), "preferencias_tema_temporales", None)  # Recupera el tema que Configuración está mostrando actualmente, incluso antes de aplicarlo.
        tema_id = preferencias_tema_temporales.tema() if preferencias_tema_temporales is not None else TEMA_PREDETERMINADO  # Utiliza el tema temporal cuando existe y conserva uno seguro como respaldo.
        paleta = obtener_tema(tema_id)  # Obtiene los colores oficiales correspondientes al modo y variante actualmente visibles.

        boton_si = QPushButton("Sí", dialogo)  # Representa explícitamente la confirmación afirmativa.
        boton_si.setMinimumSize(92, 36)  # Hace evidente que se trata de un botón y no de texto aislado.
        boton_si.setCursor(Qt.CursorShape.PointingHandCursor)  # Refuerza visualmente su carácter interactivo.
        boton_si.setAutoDefault(False)  # Evita acabados adicionales del sistema.
        boton_si.setDefault(False)  # Impide que la acción destructiva sea la predeterminada.
        boton_si.setFlat(False)  # Fuerza la representación convencional del botón.
        boton_si.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {paleta["acento"]};
                color: {paleta["texto_inverso"]};
                border: 1px solid {paleta["acento"]};
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {paleta["acento_hover"]};
                color: {paleta["texto_inverso"]};
                border: 1px solid {paleta["acento_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {paleta["superficie_presionada"]};
                color: {paleta["texto"]};
                border: 1px solid {paleta["acento"]};
            }}
            """
        )  # Aplica directamente la acción principal para impedir que estilos heredados oculten fondo o borde.
        boton_si.clicked.connect(dialogo.accept)  # Cierra la ventana informando una confirmación positiva.

        boton_no = QPushButton("No", dialogo)  # Representa explícitamente la cancelación.
        boton_no.setMinimumSize(92, 36)  # Mantiene exactamente la misma presencia visual que Sí.
        boton_no.setCursor(Qt.CursorShape.PointingHandCursor)  # Conserva la respuesta visual habitual.
        boton_no.setAutoDefault(True)  # Permite utilizar esta acción como decisión segura mediante teclado.
        boton_no.setDefault(True)  # Mantiene No como opción predeterminada.
        boton_no.setFlat(False)  # Fuerza la representación completa de su superficie.
        boton_no.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {paleta["superficie"]};
                color: {paleta["texto"]};
                border: 1px solid {paleta["borde_fuerte"]};
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {paleta["superficie_hover"]};
                color: {paleta["texto"]};
                border: 1px solid {paleta["acento"]};
            }}
            QPushButton:pressed {{
                background-color: {paleta["superficie_presionada"]};
                color: {paleta["texto"]};
                border: 1px solid {paleta["acento"]};
            }}
            """
        )  # Aplica directamente la acción secundaria utilizando la misma paleta del tema visible.
        boton_no.clicked.connect(dialogo.reject)  # Cierra la ventana sin ejecutar la operación.

        fila_botones.addWidget(boton_si)  # Coloca primero la acción afirmativa.
        fila_botones.addWidget(boton_no)  # Coloca después la cancelación segura.
        columna_contenido.addLayout(fila_botones)  # Añade ambas acciones debajo del mensaje.

        diseno_principal.addLayout(columna_contenido, 1)  # Permite que el bloque textual utilice todo el ancho restante.
        boton_no.setFocus()  # Sitúa inicialmente el teclado sobre la decisión no destructiva.

        resultado = dialogo.exec()  # Muestra la confirmación modal utilizando controles completamente tematizables.
        return resultado == QDialog.DialogCode.Accepted  # Devuelve True solamente cuando el usuario pulsó Sí.
    
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
        )  # Solicita confirmación porque la operación retirará todos los archivos pesados administrados.

        if not confirmado:
            return  # Conserva completamente la instalación cuando el usuario cancela.

        self.autocompletado_solicitado = False  # Evita volver a habilitar ghost text durante o después de la eliminación física.
        self.diagnosticos_solicitados = False  # Detiene también cualquier mejora automática pendiente.
        self.preferencias_ia.establecer_autocompletado_activado(False)  # Conserva el estado seguro para próximos inicios.
        self.preferencias_ia.establecer_diagnosticos_ia_activados(False)  # Conserva también apagada la segunda función.
        self.autocompletado_cambiado.emit(False)  # Detiene inmediatamente nuevas propuestas en el editor.
        self.diagnosticos_ia_cambiados.emit(False)  # Restaura inmediatamente las soluciones oficiales en la tabla.
        self._sincronizar_casillas_desactivadas()  # Retira ambas marcas antes de iniciar la operación larga.
        self._iniciar_operacion("desinstalar")  # Realiza cierre y eliminación dentro del hilo secundario.

    def _sincronizar_casillas_desactivadas(self) -> None:
        self.actualizando_controles = True  # Impide que modificar programáticamente las casillas vuelva a iniciar otra operación.
        self.boton_autocompletado.setChecked(False)  # Retira inmediatamente la primera marca.
        self.boton_diagnosticos.setChecked(False)  # Retira también la marca correspondiente a las soluciones.
        self.actualizando_controles = False  # Recupera el procesamiento normal de decisiones del usuario.

    def _iniciar_operacion(self, operacion: str) -> None:
        self.operacion_en_curso = True  # Impide iniciar otra operación simultánea.
        self.operacion_cambiada.emit(True)  # Solicita a la ventana general impedir temporalmente su cierre.
        self.boton_autocompletado.setEnabled(False)  # Evita cambios mientras el servicio compartido se encuentra en transición.
        self.boton_diagnosticos.setEnabled(False)  # Protege también la segunda preferencia durante la misma transición.
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
            self.asistencia_disponible = bool(resultado)  # Conserva el estado real obtenido al iniciar el servicio compartido.
            self.servicio_cambiado.emit(self.asistencia_disponible)  # Sincroniza al controlador general con la disponibilidad real.
            self._emitir_funciones_efectivas()  # Habilita únicamente las funciones que el usuario mantiene seleccionadas.

            if not resultado:
                tipo_mensaje = "advertencia"  # Programa el aviso después de que el panel represente el fallo.
                titulo_mensaje = "Asistencia de IA"  # Identifica el servicio que no pudo iniciarse.
                texto_mensaje = mensaje  # Conserva la explicación producida por el gestor.

        elif operacion == "desactivar":
            self.asistencia_disponible = False  # Confirma que ninguna función mantiene vivo el servicio.
            self.servicio_cambiado.emit(False)  # Actualiza el estado compartido utilizado al reabrir Configuración.
            self.autocompletado_cambiado.emit(False)  # Garantiza que no quede un consumidor activo después del cierre.
            self.diagnosticos_ia_cambiados.emit(False)  # Garantiza también la restauración de soluciones oficiales.

            if not resultado:
                tipo_mensaje = "advertencia"  # Programa únicamente los fallos de cierre.
                titulo_mensaje = "Asistencia de IA"  # Identifica el servicio afectado.
                texto_mensaje = mensaje  # Conserva la explicación producida durante la limpieza.

        elif operacion == "instalar":
            if resultado:
                self.asistencia_disponible = True  # Aprovecha la instancia que quedó activa después de descargar el modelo.
                self.autocompletado_solicitado = True  # Habilita inicialmente el ghost text después de una instalación voluntaria.
                self.diagnosticos_solicitados = True  # Habilita también la mejora automática como segunda función del mismo componente.
                guardado_autocompletado = self.preferencias_ia.establecer_autocompletado_activado(True)  # Conserva la primera función para futuros inicios.
                guardado_diagnosticos = self.preferencias_ia.establecer_diagnosticos_ia_activados(True)  # Conserva de forma independiente la segunda.
                self.servicio_cambiado.emit(True)  # Informa que la instalación dejó un servicio utilizable.
                self._emitir_funciones_efectivas()  # Activa inmediatamente ambas funciones sin reiniciar TecNet Finder.
                tipo_mensaje = "informacion"  # Programa la confirmación para después del repintado.
                titulo_mensaje = "Asistencia de IA"  # Identifica la instalación terminada.
                texto_mensaje = mensaje  # Conserva el mensaje producido por el gestor.

                if not guardado_autocompletado or not guardado_diagnosticos:
                    tipo_mensaje = "advertencia"  # Prioriza advertir cuando alguna elección no pudo conservarse.
                    titulo_mensaje = "Preferencias"  # Identifica que el componente sí quedó instalado físicamente.
                    texto_mensaje = "El componente se instaló y está activo, pero no fue posible guardar todas las preferencias de IA."  # Explica exactamente el alcance del problema.
            else:
                self.asistencia_disponible = False  # Conserva desactivados los consumidores después de una instalación fallida.
                self.servicio_cambiado.emit(False)  # Informa que el servicio no quedó disponible.
                self.autocompletado_cambiado.emit(False)  # Mantiene detenido el autocompletado.
                self.diagnosticos_ia_cambiados.emit(False)  # Mantiene también las soluciones oficiales.
                tipo_mensaje = "advertencia"  # Programa la explicación después de restaurar visualmente los botones.
                titulo_mensaje = "Instalación de IA"  # Identifica la operación que no pudo completarse.
                texto_mensaje = mensaje  # Conserva la causa reportada por el gestor.

        elif operacion == "desinstalar":
            self.asistencia_disponible = False  # Mantiene la asistencia apagada después del intento de eliminación.
            self.servicio_cambiado.emit(False)  # El componente administrado ya no debe considerarse disponible para consumidores.
            self.autocompletado_cambiado.emit(False)  # Mantiene detenido el ghost text.
            self.diagnosticos_ia_cambiados.emit(False)  # Mantiene visible únicamente la solución oficial.
            self._sincronizar_casillas_desactivadas()  # Garantiza que ambas marcas continúen apagadas independientemente del resultado físico.

            if resultado:
                tipo_mensaje = "informacion"  # Programa la confirmación después de mostrar que el componente ya no existe.
                titulo_mensaje = "Asistencia de IA"  # Identifica la eliminación completada.
                texto_mensaje = mensaje  # Conserva el mensaje de éxito producido por el gestor.
            else:
                tipo_mensaje = "advertencia"  # Programa el fallo después de reflejar el estado real.
                titulo_mensaje = "Desinstalación de IA"  # Identifica la operación afectada.
                texto_mensaje = mensaje  # Conserva la explicación concreta del problema.

        self._mostrar_progreso(False)  # Recupera primero la página normal de botones dentro del mismo espacio reservado.
        self._actualizar_estado()  # Sincroniza completamente etiquetas, casillas y acciones antes de abrir cualquier mensaje modal.

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
