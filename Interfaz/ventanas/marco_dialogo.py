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

from PySide6.QtCore import Qt  # Permite controlar el borde y el arrastre de la ventana.
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QVBoxLayout, QWidget  # Construye el marco compartido y su área interior.

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
    return contenido  # Devuelve el layout utilizado por el diálogo existente.
