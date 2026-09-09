# ============================================================
# Archivo: panel_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el panel encargado de mostrar los
# diagnósticos detectados y el catálogo general de códigos.
#
# Las soluciones oficiales permanecen intactas internamente y
# pueden sustituirse visualmente por explicaciones generadas por
# la IA local únicamente cuando el usuario hace doble clic sobre
# la celda Solución y la función se encuentra habilitada.
#
# El contenido de las tablas se centra verticalmente para mantener
# una lectura equilibrada incluso cuando una fila crece por textos
# extensos. La navegación al código permanece disponible mediante
# doble clic sobre las demás celdas.
# ============================================================

from PySide6.QtCore import QEvent, QTimer, Qt, Signal  # Importa eventos, temporización, roles, alineaciones, cursores y navegación.
from PySide6.QtGui import QBrush, QColor  # Importa las herramientas utilizadas para colorear filas y estados.
from PySide6.QtWidgets import QApplication, QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QTabWidget  # Importa pestañas, tablas y acceso al intervalo de doble clic.

from AsistenteIA.control_diagnosticos_ia import ControlDiagnosticosIA  # Mejora soluciones en segundo plano sin intervenir en la detección formal.
from AsistenteIA.explicador_diagnosticos import ExplicadorDiagnosticos  # Permite relacionar cada resultado de IA con la identidad exacta del diagnóstico.
from Motor.diagnosticos import Diagnostico, ESTADO_DIAGNOSTICO_DISPONIBLE, obtener_catalogo_diagnosticos, texto_estado_diagnostico  # Importa el modelo y el catálogo centralizado de diagnósticos.


class PanelDiagnosticos(QTabWidget):  # Organiza diagnósticos detectados y catálogo general dentro de dos subpestañas.
    diagnostico_activado = Signal(object)  # Emite el diagnóstico asociado cuando el usuario solicita navegar hacia el código fuente.

    def __init__(self, padre=None):  # Inicializa las dos tablas manteniendo la misma interfaz pública utilizada por la ventana principal.
        super().__init__(padre)  # Inicializa el contenedor de pestañas.
        self.filas_catalogo: dict[str, int] = {}  # Relaciona cada código con su fila para localizar inmediatamente su ficha.
        self.diagnosticos_actuales: list[Diagnostico] = []  # Conserva la compilación vigente sin modificar sus soluciones oficiales.
        self.ia_habilitada = False  # Impide generar explicaciones hasta recibir el estado efectivo desde Configuración.
        self.codigo_catalogo_pendiente: str | None = None  # Retrasa el clic simple sobre Código para distinguirlo correctamente del doble clic.
        self.clave_solucion_pendiente: str | None = None  # Identifica la única solución que se encuentra esperando una respuesta de IA.
        self.tabla_detectados = QTableWidget(0, 6)  # Crea la tabla destinada únicamente a los diagnósticos obtenidos en la compilación actual.
        self.tabla_catalogo = QTableWidget(0, 6)  # Crea la tabla fija destinada a mostrar todos los códigos conocidos.
        self.control_diagnosticos_ia = ControlDiagnosticosIA(self)  # Prepara la generación automática sin bloquear la interfaz.

        self.temporizador_catalogo = QTimer(self)  # Permite esperar brevemente antes de interpretar Código como un clic simple.
        self.temporizador_catalogo.setSingleShot(True)  # Ejecuta como máximo una apertura del catálogo por interacción.
        aplicacion = QApplication.instance()  # Consulta la configuración real de doble clic utilizada por el sistema.
        intervalo_doble_clic = aplicacion.doubleClickInterval() if aplicacion is not None else 250  # Mantiene una alternativa segura durante pruebas aisladas.
        self.temporizador_catalogo.setInterval(max(150, intervalo_doble_clic))  # Espera lo suficiente para reconocer un posible segundo clic.
        self.temporizador_catalogo.timeout.connect(self._abrir_codigo_catalogo_pendiente)  # Abre la ficha solamente cuando no llegó un doble clic.

        self._configurar_tabla_detectados()  # Prepara columnas, selección y comportamiento interactivo de la primera vista.
        self._configurar_tabla_catalogo()  # Prepara la tabla utilizada como referencia general.
        self._cargar_catalogo()  # Llena la segunda vista utilizando exclusivamente los datos registrados en Motor.

        self.addTab(self.tabla_detectados, "Detectados")  # Mantiene primero la vista utilizada durante una compilación normal.
        self.addTab(self.tabla_catalogo, "Catálogo")  # Agrega la referencia completa como segunda subpestaña.

        self.tabla_detectados.cellClicked.connect(self._procesar_clic_detectado)  # Diferencia el acceso al catálogo de la navegación mediante doble clic.
        self.tabla_detectados.cellDoubleClicked.connect(self._activar_diagnostico)  # Navega desde cualquier celda de una fila hacia el código fuente.
        self.tabla_detectados.itemSelectionChanged.connect(self._sincronizar_catalogo_desde_detectados)  # Mantiene preparada en segundo plano la ficha correspondiente al diagnóstico seleccionado.
        self.control_diagnosticos_ia.soluciones_listas.connect(self._aplicar_soluciones_ia)  # Sustituye visualmente únicamente soluciones pertenecientes a la compilación vigente.

    def _configurar_tabla_detectados(self) -> None:  # Configura la tabla que muestra únicamente los diagnósticos de la compilación actual.
        self.tabla_detectados.setHorizontalHeaderLabels(
            [
                "Código",
                "Categoría",
                "Mensaje",
                "Línea",
                "Columna",
                "Solución",
            ]
        )

        self.tabla_detectados.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide modificar accidentalmente los diagnósticos.
        self.tabla_detectados.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Selecciona la fila completa al pulsar cualquiera de sus celdas.
        self.tabla_detectados.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite trabajar solamente con un diagnóstico a la vez.
        self.tabla_detectados.setAlternatingRowColors(True)  # Facilita distinguir visualmente filas consecutivas.
        self.tabla_detectados.setWordWrap(True)  # Permite que los mensajes y soluciones extensos utilicen varias líneas.
        self.tabla_detectados.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar información mediante puntos suspensivos.
        self.tabla_detectados.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_detectados.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta la altura según el contenido real.
        self.tabla_detectados.setMouseTracking(True)  # Permite conocer la celda situada debajo del cursor aunque no exista ningún clic.
        self.tabla_detectados.viewport().setMouseTracking(True)  # Activa el seguimiento directamente sobre el área donde se dibujan las celdas.
        self.tabla_detectados.viewport().installEventFilter(self)  # Permite cambiar el cursor solamente cuando se encuentra sobre la columna Código.

        encabezado = self.tabla_detectados.horizontalHeader()  # Obtiene el encabezado para configurar individualmente sus columnas.

        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Reserva únicamente el espacio necesario para Código.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Reserva únicamente el espacio necesario para Categoría.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Permite que Mensaje utilice una parte amplia del espacio restante.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Línea compacta.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Columna compacta.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución comparta el espacio principal.

    def _configurar_tabla_catalogo(self) -> None:  # Configura la tabla de referencia utilizada para consultar todos los códigos conocidos.
        self.tabla_catalogo.setHorizontalHeaderLabels(
            [
                "Código",
                "Tipo",
                "Estado",
                "Nombre",
                "Descripción",
                "Solución sugerida",
            ]
        )

        self.tabla_catalogo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Impide alterar visualmente la información central del catálogo.
        self.tabla_catalogo.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)  # Mantiene seleccionada la ficha completa del código.
        self.tabla_catalogo.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Permite consultar una sola entrada a la vez.
        self.tabla_catalogo.setAlternatingRowColors(True)  # Facilita la lectura de códigos consecutivos.
        self.tabla_catalogo.setWordWrap(True)  # Permite mostrar completamente descripciones y soluciones extensas.
        self.tabla_catalogo.setTextElideMode(Qt.TextElideMode.ElideNone)  # Evita ocultar información del catálogo.
        self.tabla_catalogo.verticalHeader().setVisible(False)  # Oculta la numeración automática de filas.
        self.tabla_catalogo.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Adapta la altura de cada ficha al texto completo.

        encabezado = self.tabla_catalogo.horizontalHeader()  # Obtiene el encabezado de la referencia general.

        encabezado.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Código compacto.
        encabezado.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene Tipo compacto.
        encabezado.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Reserva solamente el ancho requerido por el Estado.
        encabezado.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Mantiene visible el nombre completo del diagnóstico.
        encabezado.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Permite que Descripción utilice buena parte del espacio disponible.
        encabezado.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Permite que Solución sugerida comparta el espacio restante.

    def eventFilter(self, objeto, evento) -> bool:  # Cambia dinámicamente el cursor únicamente al pasar sobre un código clickeable.
        if objeto is self.tabla_detectados.viewport():  # Comprueba que el evento pertenezca al área de celdas de la tabla Detectados.
            if evento.type() == QEvent.Type.MouseMove:  # Atiende cada movimiento del mouse dentro de la tabla.
                indice = self.tabla_detectados.indexAt(evento.position().toPoint())  # Obtiene la fila y columna exactas situadas debajo del cursor.

                if indice.isValid() and indice.column() == 0:  # Comprueba que exista una celda y que corresponda específicamente a Código.
                    self.tabla_detectados.viewport().setCursor(Qt.CursorShape.PointingHandCursor)  # Muestra la manita convencional utilizada por enlaces.
                else:
                    self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Recupera la flecha convencional sobre el resto de la tabla.

            elif evento.type() == QEvent.Type.Leave:
                self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Garantiza que la manita no permanezca activa fuera de los enlaces.

        return super().eventFilter(objeto, evento)  # Permite que Qt continúe procesando normalmente selección, clics y desplazamiento.

    def establecer_ia_habilitada(self, habilitada: bool) -> None:
        nuevo_estado = bool(habilitada)  # Conserva únicamente el estado efectivo comunicado por la configuración general.

        if self.ia_habilitada == nuevo_estado:
            return  # Evita alterar la tabla cuando el estado real no cambió.

        self.ia_habilitada = nuevo_estado  # Actualiza primero la decisión utilizada por los dobles clics posteriores.
        self.control_diagnosticos_ia.establecer_habilitado(self.ia_habilitada)  # Sincroniza la capa asíncrona con la preferencia efectiva.
        self._actualizar_ayudas_solucion()  # Refleja en los tooltips si la mejora manual con IA se encuentra disponible.

        if not self.ia_habilitada:
            self.control_diagnosticos_ia.cancelar()  # Invalida cualquier solicitud iniciada antes de desactivar la función.
            self._restaurar_soluciones_oficiales()  # Recupera inmediatamente el contenido determinista cuando la IA se desactiva.

    def _color_categoria(self, categoria: str) -> QColor:  # Devuelve el color utilizado por cada familia de diagnósticos.
        if categoria == "Advertencia":
            return QColor("#f9e2af")  # Utiliza amarillo para advertencias.

        if categoria == "Léxico":
            return QColor("#f38ba8")  # Utiliza rojo rosado para diagnósticos léxicos.

        if categoria == "Sintáctico":
            return QColor("#fab387")  # Utiliza naranja para diagnósticos sintácticos.

        if categoria == "Semántico":
            return QColor("#cba6f7")  # Utiliza violeta para diagnósticos semánticos.

        return QColor("#cdd6f4")  # Utiliza el color general para diagnósticos no pertenecientes a las categorías anteriores.

    def _color_diagnostico(self, diagnostico: Diagnostico) -> QColor:  # Conserva la prioridad visual amarilla para cualquier advertencia detectada.
        if diagnostico.severidad in ("warning", "advertencia"):
            return QColor("#f9e2af")  # Fuerza el amarillo independientemente de la categoría almacenada.

        return self._color_categoria(diagnostico.categoria)  # Utiliza el color general correspondiente al resto de diagnósticos.

    def _color_estado_catalogo(self, estado: str) -> QColor:  # Diferencia visualmente funcionalidades actuales de las todavía pendientes.
        if estado == ESTADO_DIAGNOSTICO_DISPONIBLE:
            return QColor("#a6e3a1")  # Utiliza verde para los diagnósticos disponibles.

        return QColor("#f9e2af")  # Utiliza amarillo para las características que todavía deben implementarse.

    def _cargar_catalogo(self) -> None:  # Construye todas las filas directamente desde la fuente central de Motor.
        self.tabla_catalogo.setRowCount(0)  # Elimina cualquier contenido previo antes de reconstruir la referencia.
        self.filas_catalogo.clear()  # Reinicia también las posiciones utilizadas para localizar códigos rápidamente.

        for codigo, informacion in obtener_catalogo_diagnosticos():
            fila = self.tabla_catalogo.rowCount()  # Obtiene la nueva posición dentro de la tabla.
            self.tabla_catalogo.insertRow(fila)  # Crea una fila independiente para la ficha.
            self.filas_catalogo[codigo] = fila  # Registra dónde quedó ubicado el código actual.

            valores = [
                codigo,
                informacion["categoria"],
                texto_estado_diagnostico(codigo),
                informacion["nombre"],
                informacion["descripcion"],
                informacion["solucion"],
            ]

            color_categoria = self._color_categoria(informacion["categoria"])  # Obtiene el color correspondiente al tipo de diagnóstico.
            color_estado = self._color_estado_catalogo(informacion["estado"])  # Obtiene verde o amarillo según su disponibilidad.

            for columna, valor in enumerate(valores):
                elemento = QTableWidgetItem(valor)  # Crea la celda utilizando exactamente la información registrada.
                elemento.setForeground(QBrush(color_estado if columna == 2 else color_categoria))  # Colorea únicamente Estado según disponibilidad y conserva el tipo para las demás columnas.
                elemento.setToolTip(valor)  # Permite consultar también el contenido completo al dejar el cursor encima.

                if columna in (0, 1, 2, 3):
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra código, tipo, estado y nombre.
                else:
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Centra verticalmente los textos extensos sin perder su alineación izquierda.

                if columna == 0:
                    elemento.setData(Qt.ItemDataRole.UserRole, codigo)  # Conserva el código para futuras interacciones.

                self.tabla_catalogo.setItem(fila, columna, elemento)  # Inserta finalmente la celda en la tabla.

        self.tabla_catalogo.resizeRowsToContents()  # Ajusta todas las alturas después de cargar las descripciones completas.

    def mostrar_diagnosticos(self, diagnosticos: list[Diagnostico]) -> None:  # Sustituye únicamente la tabla de resultados actuales sin modificar el catálogo.
        self.control_diagnosticos_ia.cancelar()  # Invalida cualquier mejora perteneciente a una compilación anterior.
        self.clave_solucion_pendiente = None  # Descarta la relación visual con cualquier solicitud de la compilación anterior.
        self.diagnosticos_actuales = list(diagnosticos)  # Conserva una copia estable de los objetos oficiales sin alterar sus soluciones.
        self.tabla_detectados.setRowCount(0)  # Elimina los diagnósticos correspondientes a la compilación anterior.

        for diagnostico in self.diagnosticos_actuales:
            fila = self.tabla_detectados.rowCount()  # Obtiene la siguiente posición libre.
            self.tabla_detectados.insertRow(fila)  # Inserta una nueva fila para el diagnóstico.
            color = self._color_diagnostico(diagnostico)  # Obtiene el color correspondiente a su categoría o severidad.

            valores = [
                diagnostico.codigo,
                diagnostico.categoria,
                diagnostico.mensaje,
                "" if diagnostico.linea is None else str(diagnostico.linea),
                "" if diagnostico.columna is None else str(diagnostico.columna),
                diagnostico.solucion,
            ]

            for columna, valor in enumerate(valores):
                elemento = QTableWidgetItem(valor)  # Crea la celda con la información correspondiente.
                elemento.setForeground(QBrush(color))  # Aplica el color propio del diagnóstico a toda la fila.
                elemento.setToolTip(valor)  # Mantiene el texto completo disponible mediante tooltip.

                if columna in (0, 1, 3, 4):
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centra código, categoría y ubicación.
                else:
                    elemento.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Centra verticalmente Mensaje y Solución dentro de filas de altura variable.

                if columna == 0:
                    elemento.setData(Qt.ItemDataRole.UserRole, diagnostico)  # Conserva el objeto completo para navegación y sincronización.
                    fuente_codigo = elemento.font()  # Obtiene una copia de la fuente utilizada por la celda.
                    fuente_codigo.setUnderline(True)  # Subraya el código para comunicar visualmente que puede pulsarse.
                    fuente_codigo.setBold(True)  # Refuerza ligeramente el identificador para distinguirlo del resto de la fila.
                    elemento.setFont(fuente_codigo)  # Aplica el formato visual similar al de un enlace.
                    elemento.setToolTip(
                        f"{diagnostico.codigo}\n\n"
                        "Clic: abrir este código en el catálogo.\n"
                        "Doble clic: ir al fragmento correspondiente en el código fuente."
                    )  # Explica claramente las dos interacciones disponibles sobre la misma celda.

                if columna == 5:
                    elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Explica el origen de la solución y la interacción opcional con IA.

                self.tabla_detectados.setItem(fila, columna, elemento)  # Inserta finalmente la celda en su posición correspondiente.

        self.tabla_detectados.resizeRowsToContents()  # Recalcula la altura necesaria después de insertar todos los textos.

    def limpiar(self) -> None:  # Elimina únicamente los resultados de la compilación y mantiene disponible la referencia fija.
        self.control_diagnosticos_ia.cancelar()  # Descarta cualquier respuesta que todavía estuviera generándose.
        self.diagnosticos_actuales.clear()  # Elimina también la relación utilizada para validar futuras soluciones.
        self.temporizador_catalogo.stop()  # Evita abrir una ficha después de limpiar la interfaz.
        self.codigo_catalogo_pendiente = None  # Descarta cualquier clic simple todavía pendiente.
        self.clave_solucion_pendiente = None  # Descarta también cualquier solución que estuviera esperando una respuesta de IA.
        self.tabla_detectados.setRowCount(0)  # Borra únicamente los diagnósticos producidos por la compilación anterior.
        self.tabla_catalogo.clearSelection()  # Elimina cualquier ficha preseleccionada del catálogo.
        self.tabla_detectados.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # Restaura también el cursor convencional al limpiar los diagnósticos.
        self.setCurrentWidget(self.tabla_detectados)  # Regresa a Detectados para dejar el panel en su estado principal.

    def _aplicar_soluciones_ia(self, soluciones: dict) -> None:
        clave_pendiente = self.clave_solucion_pendiente  # Recupera la identidad exacta solicitada mediante doble clic.
        self.clave_solucion_pendiente = None  # Libera la interacción antes de modificar la celda correspondiente.

        if not self.ia_habilitada or not clave_pendiente:
            return  # Ignora señales tardías o resultados que ya no pertenecen a una solicitud visible.

        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            clave = ExplicadorDiagnosticos.clave_diagnostico(diagnostico)  # Obtiene la misma identidad utilizada por el explicador.

            if clave != clave_pendiente:
                continue  # Mantiene intactas todas las demás soluciones, incluidas otras mejoras ya mostradas.

            elemento = self.tabla_detectados.item(fila, 5)  # Recupera exclusivamente la celda visual solicitada.

            if elemento is None:
                return  # Finaliza si la tabla cambió mientras se generaba la respuesta.

            solucion_ia = soluciones.get(clave_pendiente) if isinstance(soluciones, dict) else None  # Busca únicamente la mejora correspondiente al diagnóstico solicitado.
            elemento.setForeground(QBrush(self._color_diagnostico(diagnostico)))  # Recupera el color normal al abandonar el estado temporal.

            if not isinstance(solucion_ia, str) or not solucion_ia.strip():
                elemento.setText(diagnostico.solucion)  # Recupera la solución oficial si la capa opcional no pudo producir una mejora válida.
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Mantiene disponible una nueva solicitud mediante doble clic.
                self.tabla_detectados.resizeRowsToContents()  # Ajusta nuevamente la fila después de retirar el estado temporal.
                return

            elemento.setText(solucion_ia)  # Sustituye únicamente la representación visible sin modificar diagnostico.solucion.
            elemento.setToolTip(
                "Solución mejorada con IA local.\n"
                "La solución oficial permanece intacta internamente.\n\n"
                f"Solución oficial:\n{diagnostico.solucion}"
            )  # Hace transparente para el usuario cuál es el origen del contenido actual.
            self.tabla_detectados.resizeRowsToContents()  # Ajusta la altura únicamente después de recibir la explicación solicitada.
            return

    def _solicitar_mejora_solucion(self, fila: int) -> None:
        if not self.ia_habilitada:
            return  # Mantiene la navegación normal cuando la función opcional se encuentra desactivada.

        if fila < 0 or fila >= len(self.diagnosticos_actuales):
            return  # Protege frente a índices que dejaron de corresponder con la compilación actual.

        diagnostico = self.diagnosticos_actuales[fila]  # Obtiene el diagnóstico oficial asociado con la celda pulsada.
        clave = ExplicadorDiagnosticos.clave_diagnostico(diagnostico)  # Calcula la identidad utilizada por la caché y por el resultado asíncrono.

        if self.clave_solucion_pendiente == clave:
            return  # Evita encolar varias veces la misma solicitud mientras todavía se está generando.

        self._restaurar_solucion_pendiente()  # Recupera cualquier celda anterior si el usuario solicita otra antes de que termine la primera.
        self.clave_solucion_pendiente = clave  # Registra qué única celda podrá aceptar la próxima respuesta de IA.

        elemento = self.tabla_detectados.item(fila, 5)  # Obtiene la celda visual sin alterar el diagnóstico interno.

        if elemento is None:
            self.clave_solucion_pendiente = None  # Evita conservar una solicitud sin representación visible.
            return

        elemento.setText("Mejorando solución con IA...")  # Muestra un estado temporal solamente después de una acción explícita del usuario.
        elemento.setToolTip("La IA local está preparando una versión más clara de esta solución.")  # Explica por qué cambió temporalmente el contenido.
        self.tabla_detectados.resizeRowsToContents()  # Adapta la fila al texto breve mostrado durante la generación.
        self.control_diagnosticos_ia.procesar([diagnostico])  # Genera únicamente la solución solicitada y reutiliza la caché si ya existe.

    def _restaurar_solucion_pendiente(self) -> None:
        clave_pendiente = self.clave_solucion_pendiente  # Conserva la identidad antes de invalidar una solicitud anterior.

        if not clave_pendiente:
            return  # Evita recorrer la tabla cuando no existe ninguna generación pendiente.

        self.control_diagnosticos_ia.cancelar()  # Hace obsoleto cualquier resultado que todavía pudiera llegar desde el hilo secundario.
        self.clave_solucion_pendiente = None  # Libera inmediatamente la interacción para aceptar otra solicitud.

        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            if ExplicadorDiagnosticos.clave_diagnostico(diagnostico) != clave_pendiente:
                continue  # Busca únicamente la celda que estaba mostrando el estado temporal.

            elemento = self.tabla_detectados.item(fila, 5)  # Recupera la celda todavía visible.

            if elemento is not None:
                elemento.setText(diagnostico.solucion)  # Restaura la recomendación oficial al cancelar esa generación.
                elemento.setForeground(QBrush(self._color_diagnostico(diagnostico)))  # Recupera el color propio de la fila.
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Recupera también la ayuda para volver a solicitar IA.

            break  # Finaliza porque cada identidad corresponde con una sola fila de la compilación actual.

        self.tabla_detectados.resizeRowsToContents()  # Recupera la altura apropiada después de cancelar la generación anterior.

    def _texto_ayuda_solucion(self, diagnostico: Diagnostico) -> str:
        texto = f"Solución oficial de TecNet Finder:\n{diagnostico.solucion}"  # Identifica siempre la recomendación determinista almacenada.

        if self.ia_habilitada:
            texto += "\n\nHaz doble clic en esta celda para mejorar la solución con IA local."  # Explica la interacción únicamente cuando el servicio está disponible para esta función.

        return texto  # Devuelve un tooltip coherente con el estado efectivo de Configuración.

    def _actualizar_ayudas_solucion(self) -> None:
        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            elemento = self.tabla_detectados.item(fila, 5)  # Recorre únicamente la columna que puede solicitar una mejora.

            if elemento is None:
                continue  # Ignora filas todavía incompletas durante una reconstrucción transitoria.

            if elemento.text() == diagnostico.solucion:
                elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Actualiza solo las celdas que todavía muestran la solución oficial.

    def _restaurar_soluciones_oficiales(self) -> None:
        self.clave_solucion_pendiente = None  # Elimina cualquier relación con una generación que dejó de ser válida.

        for fila, diagnostico in enumerate(self.diagnosticos_actuales):
            elemento = self.tabla_detectados.item(fila, 5)  # Localiza la celda que pudo haber sido reemplazada por la IA.

            if elemento is None:
                continue  # Ignora filas que dejaron de existir por una actualización simultánea.

            elemento.setText(diagnostico.solucion)  # Recupera exactamente la solución almacenada por el compilador.
            elemento.setForeground(QBrush(self._color_diagnostico(diagnostico)))  # Recupera el color normal si la celda estaba mostrando un estado temporal.
            elemento.setToolTip(self._texto_ayuda_solucion(diagnostico))  # Recupera también la ayuda coherente con el estado actual de la IA.

        self.tabla_detectados.resizeRowsToContents()  # Reduce nuevamente las filas cuando la explicación de IA era más extensa.

    def _procesar_clic_detectado(self, fila: int, columna: int) -> None:  # Retrasa únicamente Código para poder diferenciar clic simple y doble clic.
        if columna != 0:
            self.temporizador_catalogo.stop()  # Cancela cualquier apertura anterior cuando el usuario interactúa con otra celda.
            self.codigo_catalogo_pendiente = None  # Elimina la ficha pendiente porque la intención actual es diferente.
            return

        elemento = self.tabla_detectados.item(fila, 0)  # Recupera la celda donde se conserva el diagnóstico completo.

        if elemento is None:
            return  # Finaliza si no existe información asociada.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el objeto estructurado almacenado dentro del código.

        if diagnostico is None:
            return  # Evita continuar con una fila incompleta.

        self.codigo_catalogo_pendiente = diagnostico.codigo  # Conserva temporalmente la ficha que se abrirá si no aparece un segundo clic.
        self.temporizador_catalogo.start()  # Inicia la espera utilizando el intervalo de doble clic configurado por el sistema.

    def _abrir_codigo_catalogo_pendiente(self) -> None:
        codigo = self.codigo_catalogo_pendiente  # Recupera la intención almacenada por el clic simple.
        self.codigo_catalogo_pendiente = None  # Limpia el estado antes de modificar visualmente la pestaña.

        if not codigo:
            return  # Evita cualquier acción cuando un doble clic canceló previamente la navegación al catálogo.

        self._seleccionar_codigo_catalogo(codigo, cambiar_pestana=True)  # Abre finalmente la ficha únicamente después de descartar un doble clic.

    def _sincronizar_catalogo_desde_detectados(self) -> None:  # Mantiene preparada la ficha correspondiente aunque todavía no se cambie de pestaña.
        filas = self.tabla_detectados.selectionModel().selectedRows()  # Recupera la fila completa seleccionada actualmente.

        if not filas:
            return  # Evita intentar sincronizar cuando la tabla está vacía.

        fila_detectada = filas[0].row()  # Obtiene la posición del diagnóstico seleccionado.
        elemento = self.tabla_detectados.item(fila_detectada, 0)  # Recupera la celda que conserva el objeto completo.

        if elemento is None:
            return  # Finaliza si la selección todavía no posee una celda válida.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el diagnóstico estructurado.

        if diagnostico is None:
            return  # Evita intentar localizar un código inexistente.

        self._seleccionar_codigo_catalogo(
            diagnostico.codigo,
            cambiar_pestana=False,
        )  # Preselecciona silenciosamente su ficha sin apartar al usuario de Detectados.

    def _seleccionar_codigo_catalogo(self, codigo: str, cambiar_pestana: bool) -> None:  # Localiza, selecciona y centra una ficha concreta dentro del catálogo.
        fila_catalogo = self.filas_catalogo.get(codigo)  # Busca la posición registrada para el código recibido.

        if fila_catalogo is None:
            return  # Mantiene el panel sin cambios si se tratara de un código desconocido.

        self.tabla_catalogo.selectRow(fila_catalogo)  # Selecciona visualmente la ficha completa correspondiente al código.
        elemento_catalogo = self.tabla_catalogo.item(fila_catalogo, 0)  # Recupera la primera celda para poder desplazar la vista hasta ella.

        if elemento_catalogo is not None:
            self.tabla_catalogo.scrollToItem(
                elemento_catalogo,
                QAbstractItemView.ScrollHint.PositionAtCenter,
            )  # Centra la ficha dentro del espacio visible aunque se encuentre lejos en la tabla.

        if cambiar_pestana:
            self.setCurrentWidget(self.tabla_catalogo)  # Cambia automáticamente de Detectados a Catálogo mostrando la ficha encontrada.

    def _activar_diagnostico(self, fila: int, columna: int) -> None:  # Diferencia la mejora manual de Solución de la navegación normal hacia el editor.
        self.temporizador_catalogo.stop()  # Cancela inmediatamente cualquier apertura del catálogo todavía pendiente.
        self.codigo_catalogo_pendiente = None  # Confirma que la interacción actual no fue un clic simple sobre Código.

        if columna == 5 and self.ia_habilitada:
            self._solicitar_mejora_solucion(fila)  # Utiliza el doble clic sobre la solución oficial como solicitud explícita de IA.
            return  # Evita mover el foco al editor mientras la intención fue mejorar la recomendación.

        elemento = self.tabla_detectados.item(fila, 0)  # Recupera siempre el objeto completo desde la primera columna de la misma fila.

        if elemento is None:
            return  # Finaliza si la fila estuviera incompleta.

        diagnostico = elemento.data(Qt.ItemDataRole.UserRole)  # Recupera el diagnóstico estructurado almacenado internamente.

        if diagnostico is not None:
            QTimer.singleShot(
                0,
                lambda diagnostico=diagnostico: self.diagnostico_activado.emit(diagnostico),
            )  # Espera a que la tabla termine el doble clic antes de devolver el foco y la selección al editor.
