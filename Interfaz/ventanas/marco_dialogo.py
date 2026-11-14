# ============================================================
# Archivo: marco_dialogo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Unifica las ventanas secundarias de TecNet Finder con la
# misma BarraTitulo empleada por Configuración y Diagnósticos.
#
# Conserva el comportamiento modal, la X de cierre, el arrastre
# nativo de Windows y los colores de los temas claro y oscuro.
# ============================================================

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt  # Controla eventos, posicionamiento y ajustes posteriores a la apertura.
from PySide6.QtGui import QColor, QPainter  # Permite resaltar directamente la opción bajo el cursor, incluso si Qt ignora el hover de QSS.
from PySide6.QtWidgets import QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QStyledItemDelegate, QVBoxLayout, QWidget  # Construye los diálogos y el selector de registros.

from Interfaz.apariencia.recursos_tema import ruta_marca  # Recupera el emblema oficial de TecNet Finder.
from Interfaz.ventanas.barra_titulo import BarraTitulo  # Reutiliza el componente de título oficial.
from Motor.configuracion.catalogo_temas import obtener_tema  # Obtiene los colores del tema seleccionado.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Consulta las preferencias de idioma actuales.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Consulta la variante visual actual.
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones  # Traduce la ayuda del cierre.


def preparar_dialogo_con_barra(dialogo: QDialog, titulo: str, *, horizontal: bool = False, margenes: tuple[int, int, int, int] = (12, 12, 12, 12)):
    # Organiza un QDialog sin barra nativa y devuelve el diseño donde colocar su contenido.
    paleta = obtener_tema(PreferenciasTema().tema())  # Mantiene la variante visual vigente, no una paleta fija.
    idioma = PreferenciasAplicacion().idioma_interfaz()  # Recupera el idioma para describir la X.
    texto_cerrar = GestorTraducciones(idioma).traducir("comun.cerrar")  # Respeta los seis idiomas de la interfaz.

    dialogo.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)  # Retira solamente los controles nativos.
    dialogo.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # Permite bordes redondeados reales.
    if not dialogo.objectName(): dialogo.setObjectName("DialogoTecNet")  # Identifica la ventana sin alterar nombres existentes.
    dialogo.setStyleSheet(f'QDialog#{dialogo.objectName()} {{ background-color: transparent; }}')  # Evita pintar esquinas rectangulares.

    exterior = QVBoxLayout(dialogo)  # Crea un marco exterior con zona para las esquinas.
    exterior.setContentsMargins(7, 7, 7, 7)  # Reserva espacio alrededor del borde redondeado.
    exterior.setSpacing(0)  # No deja huecos entre marco y ventana.

    marco = QFrame(dialogo)  # Construye la superficie visible de la ventana.
    marco.setObjectName("MarcoDialogoTecNet")  # Permite colorear únicamente el marco.
    marco.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Solicita a Qt dibujar el fondo.
    marco.setStyleSheet(f'QFrame#MarcoDialogoTecNet {{ background-color: {paleta["fondo"]}; border: 1px solid {paleta["borde_fuerte"]}; border-radius: 13px; }}')  # Adapta fondo y contorno.
    exterior.addWidget(marco)  # Sitúa el marco dentro del diálogo transparente.
    diseno_marco = QVBoxLayout(marco)  # Agrupa barra y contenido interno.
    diseno_marco.setContentsMargins(1, 1, 1, 1)  # Deja visible el contorno.
    diseno_marco.setSpacing(0)  # Une la cabecera con el cuerpo.

    cabecera = QFrame(marco)  # Crea el fondo de la barra superior.
    cabecera.setObjectName("CabeceraDialogoTecNet")  # Aísla sus esquinas.
    cabecera.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Permite ver el fondo.
    cabecera.setStyleSheet(f'QFrame#CabeceraDialogoTecNet {{ background-color: {paleta["panel"]}; border: none; border-top-left-radius: 12px; border-top-right-radius: 12px; }}')  # Conserva la paleta vigente.
    diseno_cabecera = QVBoxLayout(cabecera)  # Aloja únicamente la barra reutilizable.
    diseno_cabecera.setContentsMargins(0, 0, 0, 0)  # Elimina márgenes propios.
    diseno_cabecera.setSpacing(0)  # Mantiene la barra compacta.

    dialogo.barra_titulo = BarraTitulo(ventana=dialogo, ruta_icono=ruta_marca("LogoTNF.ico"), titulo=titulo, mostrar_configuracion=False, mostrar_minimizar=False, mostrar_pantalla_completa=False, mostrar_cerrar=True, permitir_arrastre=True)  # Reutiliza el mismo control de Configuración.
    dialogo.barra_titulo.setStyleSheet(f'QWidget#BarraTitulo {{ background-color: transparent; border: none; }} QLabel {{ background-color: transparent; border: none; }} QLabel#TituloBarra {{ color: {paleta["texto"]}; }}')  # Mantiene la cabecera sin recuadros.
    if dialogo.barra_titulo.boton_cerrar is not None:  # Comprueba que exista la acción de cierre.
        dialogo.barra_titulo.boton_cerrar.setToolTip(texto_cerrar)  # Traduce su ayuda.
        dialogo.barra_titulo.boton_cerrar.setAccessibleName(texto_cerrar)  # Traduce su nombre accesible.
    diseno_cabecera.addWidget(dialogo.barra_titulo)  # Coloca la barra dentro del marco.
    diseno_marco.addWidget(cabecera)  # Inserta la barra en la parte superior.

    cuerpo = QWidget(marco)  # Crea el área de contenido sin modificar los controles existentes.
    cuerpo.setObjectName("CuerpoDialogoTecNet")  # Permite mantener separados cuerpo y barra.
    cuerpo.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # Asegura el dibujo del fondo.
    cuerpo.setStyleSheet(f'QWidget#CuerpoDialogoTecNet {{ background-color: {paleta["fondo"]}; border: none; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }}')  # Pinta el cuerpo según el tema.
    contenido = QHBoxLayout(cuerpo) if horizontal else QVBoxLayout(cuerpo)  # Respeta la orientación requerida por cada diálogo.
    contenido.setContentsMargins(*margenes)  # Conserva márgenes del contenido original.
    contenido.setSpacing(10)  # Mantiene la distribución histórica.
    diseno_marco.addWidget(cuerpo, 1)  # Permite que el cuerpo crezca junto con la ventana.

    if dialogo.objectName() == "VentanaMantenimiento":  # Ajusta únicamente el Centro de estabilidad, sin alterar los demás diálogos.
        pantalla = dialogo.screen()  # Consulta el espacio utilizable del monitor antes de mostrar la ventana.
        area = pantalla.availableGeometry() if pantalla is not None else None  # Respeta también los monitores pequeños.
        ancho = min(1000, max(700, area.width() - 48)) if area is not None else 1000  # Evita iniciar con el ancho reducido de 830 px.
        alto = min(720, max(480, area.height() - 64)) if area is not None else 720  # Reserva espacio para la barra de tareas.
        dialogo.resize(ancho, alto)  # Establece desde el inicio el tamaño con el que debe distribuirse el contenido.
        dialogo._ajuste_mantenimiento = AjusteMantenimiento(dialogo, paleta)  # Conserva vivo el controlador visual especializado.
        dialogo.installEventFilter(dialogo._ajuste_mantenimiento)  # Espera la primera apertura real para centrar correctamente.

    return contenido  # Devuelve el layout utilizado por el diálogo existente.


# ============================================================
# Ajustes exclusivos del Centro de mantenimiento
# ============================================================

class DelegadoHoverNiveles(QStyledItemDelegate):  # Dibuja un resaltado real bajo el cursor sin depender del hover de estilos Qt.

    def __init__(self, vista, paleta: dict):  # Conserva la vista y los colores originales del tema.
        super().__init__(vista)  # Mantiene el ciclo de vida del delegado unido al QListView.
        self.paleta = paleta  # Permite usar el acento del tema sin colores fijos.
        self.fila_hover = -1  # Indica que inicialmente ninguna opción está bajo el ratón.

    def paint(self, pintor, opcion, indice) -> None:  # Aplica el resaltado solo a la fila que realmente se está apuntando.
        super().paint(pintor, opcion, indice)  # Conserva el dibujo habitual de las opciones y su selección.
        if indice.row() != self.fila_hover: return  # No altera las demás filas ni el estado del selector.
        pintor.save()  # Preserva tipografía, transformación y recorte heredados del control.
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Suaviza las esquinas redondeadas del resaltado.
        pintor.setPen(Qt.PenStyle.NoPen)  # Evita bordes añadidos alrededor de la opción.
        pintor.setBrush(QColor(self.paleta["acento"]))  # Utiliza el color de interacción vigente.
        rectangulo = opcion.rect.adjusted(4, 2, -4, -2)  # Deja un pequeño espacio entre el borde y las opciones.
        pintor.drawRoundedRect(rectangulo, 5, 5)  # Dibuja un fondo visible aun cuando QSS ignore :hover.
        pintor.setPen(QColor(self.paleta["texto_inverso"]))  # Garantiza contraste sobre el color de acento.
        pintor.setFont(opcion.font)  # Respeta la fuente configurada por el usuario.
        texto = str(indice.data(Qt.ItemDataRole.DisplayRole) or "")  # Recupera el rótulo localizado de cada nivel.
        zona_texto = rectangulo.adjusted(12, 0, -8, 0)  # Conserva la alineación y el margen horizontal.
        texto = pintor.fontMetrics().elidedText(texto, Qt.TextElideMode.ElideRight, zona_texto.width())  # Evita desbordamientos.
        pintor.drawText(zona_texto, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto)  # Escribe la opción resaltada.
        pintor.restore()  # No modifica el pintado del resto de la lista.


class AjusteMantenimiento(QObject):  # Centra el diálogo y uniforma la lista de niveles sin intervenir en otros componentes.

    def __init__(self, dialogo: QDialog, paleta: dict):  # Prepara los ajustes que requieren una ventana ya visible.
        super().__init__(dialogo)  # Vincula la vida del controlador con su diálogo.
        self.dialogo = dialogo  # Guarda el destinatario de los cambios.
        self.paleta = paleta  # Conserva los colores reales del tema activo.
        self.primera_apertura = True  # Impide recentrar la ventana después de que el usuario la mueva.
        self.selector = None  # Se localizará cuando el Centro termine de construir la pestaña Registros.
        self.vista_niveles = None  # Identifica el viewport real donde llegan los movimientos del cursor.
        self.delegado_niveles = None  # Conserva el delegado responsable del efecto hover.
        self.flecha = None  # Conserva la etiqueta que dibujará el indicador desplegable.
        self.ventana_lista = None  # Identifica el panel flotante para mantener su posición fija.
        self.ubicacion_pendiente = False  # Impide programar varias correcciones simultáneas.

    def eventFilter(self, objeto, evento) -> bool:  # Atiende solo la primera apertura y los cambios de tamaño del selector.
        if objeto is self.dialogo and evento.type() == QEvent.Type.Show and self.primera_apertura:
            self.primera_apertura = False  # Programa el centrado una sola vez por instancia del diálogo.
            QTimer.singleShot(0, self._finalizar_primera_apertura)  # Espera que Windows y Qt asignen la geometría definitiva.
        elif objeto is self.selector and evento.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self._colocar_flecha()  # Conserva el indicador alineado al cambiar el tamaño del selector.
        elif objeto is self.ventana_lista and evento.type() in (QEvent.Type.Show, QEvent.Type.Move):
            self._programar_ubicacion_lista()  # Ancla el menú debajo del selector independientemente del elemento elegido.
        elif self.vista_niveles is not None and objeto is self.vista_niveles.viewport():  # Escucha exclusivamente el ratón sobre las opciones.
            if evento.type() == QEvent.Type.MouseMove:
                indice = self.vista_niveles.indexAt(evento.position().toPoint())  # Obtiene la opción bajo el cursor sin seleccionarla.
                self._marcar_hover_lista(indice.row() if indice.isValid() else -1)  # Actualiza el fondo de la fila apuntada.
            elif evento.type() in (QEvent.Type.Leave, QEvent.Type.Hide):
                self._marcar_hover_lista(-1)  # Retira el resaltado al abandonar el menú.
        return False  # No interrumpe el funcionamiento habitual del ratón, las listas ni las ventanas.

    def _finalizar_primera_apertura(self) -> None:  # Aplica los cambios después de construir el contenido y mostrar el diálogo.
        self._centrar_en_monitor()  # Centra en el monitor completo, no en la posición de la ventana principal.
        self._preparar_selector_niveles()  # Arregla la flecha y el menú de severidades.

    def _centrar_en_monitor(self) -> None:  # Usa la zona de trabajo del monitor donde se encuentra TecNet Finder.
        padre = self.dialogo.parentWidget()  # Consulta la ventana principal que abrió Mantenimiento.
        pantalla = padre.screen() if padre is not None else self.dialogo.screen()  # Respeta también configuraciones de varios monitores.
        if pantalla is None: return  # Evita utilizar coordenadas desconocidas.
        area = pantalla.availableGeometry()  # Excluye la barra de tareas y otros elementos reservados del sistema.
        ancho, alto = self.dialogo.width(), self.dialogo.height()  # Recupera el tamaño que ya fue corregido.
        x = area.x() + (area.width() - ancho) // 2  # Centra horizontalmente según el monitor real.
        y = area.y() + (area.height() - alto) // 2  # Centra verticalmente dentro de su área utilizable.
        self.dialogo.move(x, y)  # Realiza una única colocación sin impedir arrastrar después la ventana.

    def _preparar_selector_niveles(self) -> None:  # Integra un indicador visible y un desplegable temático.
        selector = self.dialogo.findChild(QComboBox, "MantenimientoNivel")  # Ubica el filtro existente sin reconstruirlo.
        if selector is None: return  # Permite abrir la ventana aunque cambie su estructura en el futuro.
        self.selector = selector  # Conserva la referencia necesaria para recolocar la flecha.
        colores = self.paleta  # Simplifica el uso de la paleta confirmada.

        vista = selector.view()  # Recupera el QListView que Qt muestra al desplegar el selector.
        vista.setObjectName("MantenimientoListaNiveles")  # Aísla el estilo de los demás selectores del programa.
        vista.setMouseTracking(True)  # Activa el resaltado de filas sin necesidad de hacer clic.
        vista.viewport().setMouseTracking(True)  # Detecta el cursor sobre la superficie real de las opciones.
        self.vista_niveles = vista  # Vincula el visor con el controlador de eventos de la ventana.
        self.delegado_niveles = DelegadoHoverNiveles(vista, colores)  # Se ocupa de pintar el fondo al mover el cursor.
        vista.setItemDelegate(self.delegado_niveles)  # Sustituye el delegado solo en esta lista de severidades.
        vista.viewport().installEventFilter(self)  # Recibe MouseMove y Leave aunque Qt no aplique el QSS :hover.
        vista.setStyleSheet(f"""
            QAbstractItemView#MantenimientoListaNiveles {{
                background-color: {colores["panel"]}; color: {colores["texto"]};
                border: none; outline: none; padding: 4px;
                selection-background-color: {colores["superficie_hover"]};
                selection-color: {colores["texto"]};
            }}
            QAbstractItemView#MantenimientoListaNiveles::item {{
                min-height: 27px; padding: 5px 10px; margin: 1px 3px;
                border: none; border-radius: 6px;
            }}
            QAbstractItemView#MantenimientoListaNiveles::item:selected {{
                background-color: {colores["superficie_hover"]}; color: {colores["texto"]};
            }}
            QAbstractItemView#MantenimientoListaNiveles::item:hover,
            QAbstractItemView#MantenimientoListaNiveles::item:selected:hover {{
                background-color: {colores["acento"]}; color: {colores["texto_inverso"]};
            }}
        """)  # Armoniza opciones, márgenes y selección con los controles oscuros o claros.

        ventana_lista = vista.window()  # Recupera el contenedor emergente propio de QComboBox.
        self.ventana_lista = ventana_lista  # Mantiene una referencia al popup real de Qt.
        ventana_lista.setObjectName("MantenimientoPopupNiveles")  # Identifica exclusivamente su panel desplegable.
        ventana_lista.setStyleSheet(f"QFrame#MantenimientoPopupNiveles {{ background-color: {colores['panel']}; border: 1px solid {colores['borde_fuerte']}; border-radius: 8px; }}")  # Colorea el fondo y contorno del menú.
        ventana_lista.installEventFilter(self)  # Detecta cambios automáticos de posición realizados por QComboBox.

        self.flecha = QLabel("▾", selector)  # Representa la flecha sin depender de iconos inexistentes en Recursos.
        self.flecha.setObjectName("MantenimientoFlechaNivel")  # Permite identificar el indicador durante el diagnóstico.
        self.flecha.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Mantiene el carácter centrado.
        self.flecha.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Deja que el clic abra normalmente el desplegable.
        self.flecha.setStyleSheet(f"color: {colores['texto']}; background: transparent; border: none; font-family: 'Segoe UI Symbol'; font-size: 17px;")  # Adapta la flecha al tema.
        self.flecha.show()  # Presenta la indicación aunque el QSS haya ocultado la flecha predeterminada de Qt.
        self.flecha.raise_()  # Coloca el indicador delante del fondo del selector.
        selector.installEventFilter(self)  # Reubica la flecha si cambia el tamaño por idioma o resolución.
        self._colocar_flecha()  # Alinea el indicador en su primera aparición.

    def _colocar_flecha(self) -> None:  # Coloca el símbolo sin cubrir la zona de texto de las opciones.
        if self.selector is None or self.flecha is None: return  # Espera que ambos elementos estén listos.
        self.flecha.setGeometry(self.selector.width() - 31, 0, 25, self.selector.height())  # Reserva el extremo derecho a la flecha.

    def _programar_ubicacion_lista(self) -> None:  # Evita que Qt desplace el popup cuando cambia la opción activa.
        if self.ubicacion_pendiente: return  # Una única corrección por ciclo de eventos es suficiente.
        self.ubicacion_pendiente = True  # Marca la corrección pendiente hasta terminar el layout.
        QTimer.singleShot(0, self._fijar_ubicacion_lista)  # Espera el posicionamiento inicial realizado por Qt.

    def _fijar_ubicacion_lista(self) -> None:  # Mantiene el menú anclado y visible en el monitor activo.
        self.ubicacion_pendiente = False  # Permite corregir futuras aperturas o movimientos nativos.
        if self.selector is None or self.ventana_lista is None or not self.ventana_lista.isVisible(): return  # Ignora menús cerrados.
        popup = self.ventana_lista  # Recupera el contenedor flotante real.
        pantalla = self.selector.screen()  # Respeta monitores secundarios y sus escalas.
        if pantalla is None: return  # Evita trabajar sin una pantalla identificable.
        area = pantalla.availableGeometry()  # Conserva la lista dentro del área utilizable.
        objetivo = self.selector.mapToGlobal(QPoint(0, self.selector.height() + 3))  # Coloca siempre la lista debajo del campo fijo.
        x = max(area.left(), min(objetivo.x(), area.right() - popup.width() + 1))  # Previene desbordamientos laterales.
        y = objetivo.y()  # Utiliza la misma coordenada aunque se seleccione INFO u otra opción.
        if y + popup.height() > area.bottom() + 1:  # Comprueba si el menú no cabe debajo del control.
            y = self.selector.mapToGlobal(QPoint(0, -popup.height() - 3)).y()  # Lo abre arriba cuando realmente falta espacio.
        y = max(area.top(), min(y, area.bottom() - popup.height() + 1))  # Limita la posición al monitor.
        if popup.pos() != QPoint(x, y): popup.move(x, y)  # Evita movimientos innecesarios y eventos repetidos.

    def _marcar_hover_lista(self, fila: int) -> None:  # Redibuja el menú cuando el cursor entra o sale de una opción.
        if self.delegado_niveles is None or self.vista_niveles is None: return  # Ignora eventos antes de preparar el control.
        if self.delegado_niveles.fila_hover == fila: return  # Evita repintados continuos sobre una misma fila.
        self.delegado_niveles.fila_hover = fila  # Conserva únicamente la fila bajo el cursor, no la selecciona.
        self.vista_niveles.viewport().update()  # Solicita a Qt volver a dibujar el fondo y el texto con el acento.
