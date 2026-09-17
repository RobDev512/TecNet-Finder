# ============================================================
# Archivo: principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo es el punto de entrada principal de TecNet Finder.
#
# Crea la aplicación gráfica, garantiza que solamente exista
# una instancia de TecNet Finder por sesión, consulta las
# preferencias generales y de IA e integra Configuración.
#
# También aplica el estado inicial elegido para la ventana
# principal y puede recordar entre ejecuciones si TecNet Finder
# se cerró maximizado o utilizando una ventana convencional.
#
# Media pantalla y pantalla completa se consideran estados
# temporales y nunca se restauran automáticamente al iniciar.
# ============================================================

import sys  # Permite recibir los argumentos del proceso y devolver correctamente el código de salida de TecNet Finder.

from PySide6.QtNetwork import QLocalServer, QLocalSocket  # Permite detectar otra ejecución de TecNet Finder y comunicarse localmente con ella.
from PySide6.QtWidgets import QApplication, QMessageBox  # Proporciona la aplicación gráfica y el mensaje utilizado ante un fallo excepcional de instancia.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite saber si el componente opcional de inteligencia artificial está instalado.
from AsistenteIA.gestor_ollama import GestorOllama  # Administra el servidor privado utilizado por las funciones locales de IA.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Recupera las preferencias persistentes relacionadas con las funciones de asistencia.
from Interfaz.configuracion.control_configuracion import ControlConfiguracion  # Conecta la ventana de Configuración con los componentes principales de la aplicación.
from Interfaz.apariencia.estilos import ESTILO_APLICACION  # Recupera la hoja de estilos general utilizada por toda la interfaz.
from Interfaz.ventanas.ventana_principal import VentanaPrincipal  # Proporciona la ventana principal donde funciona TecNet Finder.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Recupera las preferencias generales de ventana, navegación y resultados.


NOMBRE_SERVIDOR_INSTANCIA = "TecNetFinder_Instancia_Unica"  # Identifica localmente la instancia principal para impedir que queden dos aplicaciones abiertas.
MENSAJE_ACTIVAR_VENTANA = b"ACTIVAR"  # Indica a la instancia existente que otra ejecución intentó abrir TecNet Finder.


def _avisar_instancia_existente() -> bool:  # Intenta contactar una ejecución existente antes de crear una nueva aplicación.
    conexion = QLocalSocket()  # Crea una conexión local temporal destinada únicamente a comunicarse con la primera instancia.
    conexion.connectToServer(NOMBRE_SERVIDOR_INSTANCIA)  # Busca el servidor reservado por la aplicación que ya se encuentra abierta.
    if not conexion.waitForConnected(250):
        return False  # Informa que no existe una instancia accesible y permite continuar con el inicio normal.
    conexion.write(MENSAJE_ACTIVAR_VENTANA)  # Solicita que la ventana ya existente vuelva a mostrarse o tome el foco.
    conexion.flush()  # Envía inmediatamente los datos pendientes de la conexión local.
    conexion.waitForBytesWritten(250)  # Da un margen breve para que el mensaje alcance la instancia principal.
    conexion.disconnectFromServer()  # Cierra la comunicación porque ya no será necesaria.
    return True  # Informa que sí existía otra instancia y evita crear una segunda ventana.


def _mostrar_ventana_normal_centrada(aplicacion: QApplication, ventana: VentanaPrincipal) -> None:  # Muestra TecNet Finder como ventana normal centrada en la pantalla principal.
    pantalla = aplicacion.primaryScreen()  # Utiliza el monitor principal como referencia segura durante el inicio.
    if pantalla is None:
        ventana.resize(1280, 760)  # Mantiene un tamaño convencional si Qt todavía no puede identificar ninguna pantalla.
        ventana.show()  # Muestra igualmente la aplicación para no impedir su inicio por falta temporal de información del monitor.
        return

    area = pantalla.availableGeometry()  # Recupera el espacio disponible del monitor excluyendo elementos como la barra de tareas.
    ancho = min(1280, area.width())  # Limita inicialmente el ancho para evitar superar pantallas pequeñas.
    ancho = max(min(area.width() // 2, area.width()), ancho)  # Conserva como mínimo aproximadamente media pantalla cuando existe espacio suficiente.
    alto = min(760, area.height())  # Limita la altura para impedir que la ventana sobrepase verticalmente el monitor.
    ventana.resize(ancho, alto)  # Aplica el tamaño calculado antes de centrar la ventana.

    posicion_x = area.x() + max(0, (area.width() - ancho) // 2)  # Calcula la posición horizontal necesaria para centrar TecNet Finder.
    posicion_y = area.y() + max(0, (area.height() - alto) // 2)  # Calcula la posición vertical necesaria para centrar TecNet Finder.
    ventana.move(posicion_x, posicion_y)  # Coloca la ventana dentro del área realmente utilizable del monitor.
    ventana.show()  # Inicia TecNet Finder en estado convencional y no maximizado.


def _mostrar_ventana_segun_preferencias(aplicacion: QApplication, ventana: VentanaPrincipal, preferencias: PreferenciasAplicacion) -> None:  # Decide el estado inicial utilizando las preferencias persistentes.
    estado_recordado = None  # Comienza sin asumir que existe un estado anterior que deba restaurarse.
    if preferencias.recordar_estado_ventana():
        estado_recordado = preferencias.ultimo_estado_ventana()  # Recupera solamente los estados persistentes permitidos: normal o maximizada.

    if estado_recordado == PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA:
        ventana.showMaximized()  # Restaura una sesión anterior que terminó con la ventana maximizada.
        return
    if estado_recordado == PreferenciasAplicacion.ESTADO_VENTANA_NORMAL:
        _mostrar_ventana_normal_centrada(aplicacion, ventana)  # Restaura una sesión anterior que terminó utilizando una ventana convencional.
        return
    if preferencias.iniciar_maximizado():
        ventana.showMaximized()  # Utiliza la preferencia inicial histórica cuando todavía no existe un estado anterior recordado.
        return

    _mostrar_ventana_normal_centrada(aplicacion, ventana)  # Utiliza una ventana convencional cuando el usuario desactivó el inicio maximizado.


def _guardar_estado_final_ventana(ventana: VentanaPrincipal, preferencias: PreferenciasAplicacion) -> None:  # Conserva un estado seguro que podrá restaurarse durante la siguiente ejecución.
    if not preferencias.recordar_estado_ventana():
        return  # No almacena el estado de la sesión cuando el usuario desactivó explícitamente esta preferencia.

    if ventana.en_pantalla_completa:
        estado = PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA if ventana.modo_antes_pantalla_completa == "maximizado" else PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Recupera el modo existente antes de entrar temporalmente a pantalla completa.
    elif ventana.en_media_pantalla:
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Considera Media pantalla como una disposición temporal derivada de una ventana normal.
    elif ventana.isMaximized():
        estado = PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA  # Conserva que TecNet Finder terminó la sesión en estado maximizado.
    else:
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Trata cualquier otro estado convencional como una ventana normal.

    preferencias.establecer_ultimo_estado_ventana(estado)  # Guarda únicamente un estado que pueda restaurarse de forma segura en el próximo inicio.


def iniciar_aplicacion() -> int:  # Construye todos los componentes globales y mantiene TecNet Finder activo hasta el cierre.
    aplicacion = QApplication(sys.argv)  # Crea la aplicación Qt utilizando los argumentos recibidos por el proceso.
    aplicacion.setApplicationName("TecNet Finder")  # Establece el nombre utilizado por Qt y por distintos elementos del sistema operativo.
    aplicacion.setStyle("Fusion")  # Utiliza una base visual consistente antes de aplicar los estilos personalizados.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia general definida para TecNet Finder.

    if _avisar_instancia_existente():
        return 0  # Finaliza silenciosamente esta ejecución cuando otra instancia ya recibió la solicitud de activación.

    QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)  # Elimina un identificador residual que pudiera haber quedado después de un cierre anormal.
    servidor_instancia = QLocalServer(aplicacion)  # Crea el servidor local que identificará esta ejecución como la instancia principal.

    if not servidor_instancia.listen(NOMBRE_SERVIDOR_INSTANCIA):
        if _avisar_instancia_existente():
            return 0  # Reintenta contactar otra instancia por si apareció durante la inicialización.
        QMessageBox.critical(None, "TecNet Finder", "No fue posible reservar el identificador de instancia única de TecNet Finder.")  # Informa que la protección de instancia única no pudo establecerse.
        return 1  # Finaliza con error porque continuar podría permitir ejecuciones duplicadas.

    componente_ia = GestorComponenteIA()  # Prepara el administrador encargado de localizar la instalación opcional del componente de IA.
    preferencias_ia = PreferenciasIA()  # Recupera las funciones de asistencia que el usuario decidió mantener activadas.
    preferencias_aplicacion = PreferenciasAplicacion()  # Crea una única instancia compartida para todas las preferencias generales.
    gestor_ollama = GestorOllama(componente_ia=componente_ia)  # Prepara el servidor privado utilizando el mismo componente administrado por TecNet Finder.
    asistencia_disponible = False  # Parte de un estado seguro donde ninguna función depende obligatoriamente de la IA.

    if componente_ia.instalado() and preferencias_ia.alguna_funcion_activada():
        asistencia_disponible = gestor_ollama.iniciar()  # Inicia Ollama únicamente cuando existe el componente y alguna función realmente lo necesita.

    ventana = VentanaPrincipal()  # Crea la interfaz principal después de preparar las dependencias globales.
    ventana.control_configuracion = ControlConfiguracion(
        ventana=ventana,
        gestor_ollama=gestor_ollama,
        componente_ia=componente_ia,
        preferencias_ia=preferencias_ia,
        asistencia_disponible_inicial=asistencia_disponible,
        preferencias_aplicacion=preferencias_aplicacion,
    )  # Comparte con Configuración exactamente las mismas instancias utilizadas durante el inicio.

    def atender_nueva_instancia() -> None:  # Atiende solicitudes enviadas por otras ejecuciones que intentaron abrir TecNet Finder.
        while servidor_instancia.hasPendingConnections():
            conexion = servidor_instancia.nextPendingConnection()  # Recupera la siguiente conexión pendiente recibida por el servidor local.
            if conexion is None:
                break  # Abandona el ciclo si Qt no pudo proporcionar una conexión válida.
            if conexion.bytesAvailable() == 0:
                conexion.waitForReadyRead(150)  # Espera brevemente cuando el mensaje todavía no ha llegado por completo.
            mensaje = bytes(conexion.readAll())  # Recupera el contenido enviado por la instancia secundaria.
            if mensaje == MENSAJE_ACTIVAR_VENTANA:
                ventana.activar_desde_instancia_secundaria()  # Recupera o enfoca la ventana principal en lugar de crear una segunda.
            conexion.disconnectFromServer()  # Cierra la conexión después de atender la solicitud.
            conexion.deleteLater()  # Delega a Qt la liberación segura del objeto asociado con la conexión.

    servidor_instancia.newConnection.connect(atender_nueva_instancia)  # Ejecuta el manejador cada vez que otra instancia intenta comunicarse.
    _mostrar_ventana_segun_preferencias(aplicacion, ventana, preferencias_aplicacion)  # Muestra la ventana utilizando el estado elegido en Configuración.

    try:
        resultado_aplicacion = aplicacion.exec()  # Mantiene activa la interfaz hasta que el usuario cierre TecNet Finder.
        _guardar_estado_final_ventana(ventana, preferencias_aplicacion)  # Conserva el estado final solamente después de terminar normalmente la sesión.
        return resultado_aplicacion  # Devuelve a Windows el código obtenido del ciclo principal de Qt.
    finally:
        gestor_ollama.detener()  # Detiene el servidor privado de IA aunque la aplicación termine por una ruta excepcional.
        servidor_instancia.close()  # Libera el servidor local utilizado para impedir instancias duplicadas.
        QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)  # Elimina el identificador local para permitir un inicio limpio posteriormente.


if __name__ == "__main__":
    sys.exit(iniciar_aplicacion())  # Inicia TecNet Finder solamente cuando principal.py fue ejecutado directamente.