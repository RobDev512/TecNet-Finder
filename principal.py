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

import sys  # Importa las herramientas necesarias para recibir argumentos y finalizar correctamente el proceso.

from PySide6.QtNetwork import QLocalServer, QLocalSocket  # Permite detectar otra ejecución y comunicarse localmente con ella.
from PySide6.QtWidgets import QApplication, QMessageBox  # Importa la aplicación principal y un cuadro para fallos excepcionales.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite detectar la instalación opcional administrada para el usuario.
from AsistenteIA.gestor_ollama import GestorOllama  # Importa el administrador del servidor privado utilizado por la inteligencia artificial.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Permite respetar las decisiones persistentes de las funciones de asistencia.
from Interfaz.control_configuracion import ControlConfiguracion  # Integra la ventana general de configuración con TecNet Finder.
from Interfaz.estilos import ESTILO_APLICACION  # Importa la hoja de estilos centralizada de TecNet Finder.
from Interfaz.ventana_principal import VentanaPrincipal  # Importa la ventana principal de la aplicación.
from Motor.preferencias_aplicacion import PreferenciasAplicacion  # Recupera las decisiones generales relacionadas con ventana y resultados.


NOMBRE_SERVIDOR_INSTANCIA = "TecNetFinder_Instancia_Unica"  # Define el identificador local utilizado para reconocer una ejecución existente.
MENSAJE_ACTIVAR_VENTANA = b"ACTIVAR"  # Define el mensaje enviado cuando una segunda ejecución solicita recuperar la primera.


def _avisar_instancia_existente() -> bool:
    conexion = QLocalSocket()
    conexion.connectToServer(
        NOMBRE_SERVIDOR_INSTANCIA
    )

    if not conexion.waitForConnected(250):
        return False

    conexion.write(
        MENSAJE_ACTIVAR_VENTANA
    )

    conexion.flush()
    conexion.waitForBytesWritten(250)
    conexion.disconnectFromServer()

    return True


def _mostrar_ventana_normal_centrada(
    aplicacion: QApplication,
    ventana: VentanaPrincipal,
) -> None:
    pantalla = aplicacion.primaryScreen()  # Utiliza el monitor principal como referencia segura durante un inicio normal.

    if pantalla is None:
        ventana.resize(
            1280,
            760,
        )  # Mantiene un tamaño convencional como respaldo si Qt todavía no conoce ninguna pantalla.

        ventana.show()
        return

    area = pantalla.availableGeometry()  # Recupera el espacio real disponible excluyendo la barra de tareas.

    ancho = min(
        1280,
        area.width(),
    )  # Evita superar horizontalmente pantallas menores.

    ancho = max(
        min(area.width() // 2, area.width()),
        ancho,
    )  # Respeta como mínimo aproximadamente media pantalla cuando existe espacio suficiente.

    alto = min(
        760,
        area.height(),
    )  # Mantiene un tamaño cómodo sin superar verticalmente el monitor.

    ventana.resize(
        ancho,
        alto,
    )

    posicion_x = area.x() + max(
        0,
        (area.width() - ancho) // 2,
    )

    posicion_y = area.y() + max(
        0,
        (area.height() - alto) // 2,
    )

    ventana.move(
        posicion_x,
        posicion_y,
    )  # Centra la ventana dentro del área utilizable.

    ventana.show()  # Inicia TecNet Finder en estado convencional.


def _mostrar_ventana_segun_preferencias(
    aplicacion: QApplication,
    ventana: VentanaPrincipal,
    preferencias: PreferenciasAplicacion,
) -> None:
    estado_recordado = None  # Comienza sin asumir que existe una sesión anterior utilizable.

    if preferencias.recordar_estado_ventana():
        estado_recordado = (
            preferencias.ultimo_estado_ventana()
        )  # Recupera únicamente normal o maximizada cuando el usuario solicitó recordar el estado.

    if estado_recordado == PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA:
        ventana.showMaximized()
        return

    if estado_recordado == PreferenciasAplicacion.ESTADO_VENTANA_NORMAL:
        _mostrar_ventana_normal_centrada(
            aplicacion,
            ventana,
        )
        return

    if preferencias.iniciar_maximizado():
        ventana.showMaximized()  # Conserva el comportamiento histórico cuando no existe ningún estado anterior.
        return

    _mostrar_ventana_normal_centrada(
        aplicacion,
        ventana,
    )  # Utiliza una ventana convencional cuando el usuario desactivó el inicio maximizado.


def _guardar_estado_final_ventana(
    ventana: VentanaPrincipal,
    preferencias: PreferenciasAplicacion,
) -> None:
    if not preferencias.recordar_estado_ventana():
        return  # No conserva información de la sesión cuando la opción se encuentra desactivada.

    if ventana.en_pantalla_completa:
        estado = (
            PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
            if ventana.modo_antes_pantalla_completa == "maximizado"
            else PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
        )  # Recupera el modo que existía antes de entrar temporalmente a fullscreen.
    elif ventana.en_media_pantalla:
        estado = (
            PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
        )  # Considera Media pantalla como un estado temporal derivado de una ventana normal.
    elif ventana.isMaximized():
        estado = (
            PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
        )  # Registra explícitamente una sesión cerrada mientras estaba maximizada.
    else:
        estado = (
            PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
        )  # Considera cualquier otro estado convencional como ventana normal.

    preferencias.establecer_ultimo_estado_ventana(
        estado
    )  # Conserva únicamente el estado seguro que podrá recuperarse en el siguiente inicio.


def iniciar_aplicacion() -> int:
    aplicacion = QApplication(
        sys.argv
    )

    aplicacion.setApplicationName(
        "TecNet Finder"
    )

    aplicacion.setStyle(
        "Fusion"
    )

    aplicacion.setStyleSheet(
        ESTILO_APLICACION
    )

    if _avisar_instancia_existente():
        return 0

    QLocalServer.removeServer(
        NOMBRE_SERVIDOR_INSTANCIA
    )

    servidor_instancia = QLocalServer(
        aplicacion
    )

    if not servidor_instancia.listen(
        NOMBRE_SERVIDOR_INSTANCIA
    ):
        if _avisar_instancia_existente():
            return 0

        QMessageBox.critical(
            None,
            "TecNet Finder",
            "No fue posible reservar el identificador de instancia única de TecNet Finder.",
        )

        return 1

    componente_ia = GestorComponenteIA()
    preferencias_ia = PreferenciasIA()
    preferencias_aplicacion = PreferenciasAplicacion()  # Crea una única instancia compartida para todas las preferencias generales.

    gestor_ollama = GestorOllama(
        componente_ia=componente_ia
    )

    asistencia_disponible = False

    if (
        componente_ia.instalado()
        and preferencias_ia.alguna_funcion_activada()
    ):
        asistencia_disponible = gestor_ollama.iniciar()

    ventana = VentanaPrincipal()

    ventana.control_configuracion = ControlConfiguracion(
        ventana=ventana,
        gestor_ollama=gestor_ollama,
        componente_ia=componente_ia,
        preferencias_ia=preferencias_ia,
        asistencia_disponible_inicial=asistencia_disponible,
        preferencias_aplicacion=preferencias_aplicacion,
    )  # Comparte exactamente la misma configuración utilizada durante el inicio.

    def atender_nueva_instancia() -> None:
        while servidor_instancia.hasPendingConnections():
            conexion = servidor_instancia.nextPendingConnection()

            if conexion is None:
                break

            if conexion.bytesAvailable() == 0:
                conexion.waitForReadyRead(
                    150
                )

            mensaje = bytes(
                conexion.readAll()
            )

            if mensaje == MENSAJE_ACTIVAR_VENTANA:
                ventana.activar_desde_instancia_secundaria()

            conexion.disconnectFromServer()
            conexion.deleteLater()

    servidor_instancia.newConnection.connect(
        atender_nueva_instancia
    )

    _mostrar_ventana_segun_preferencias(
        aplicacion,
        ventana,
        preferencias_aplicacion,
    )  # Sustituye el antiguo showMaximized fijo por el estado elegido en Configuración.

    try:
        resultado_aplicacion = aplicacion.exec()  # Mantiene activa la interfaz hasta que el usuario cierre TecNet Finder.

        _guardar_estado_final_ventana(
            ventana,
            preferencias_aplicacion,
        )  # Conserva el estado final solamente después de terminar normalmente la sesión.

        return resultado_aplicacion
    finally:
        gestor_ollama.detener()

        servidor_instancia.close()

        QLocalServer.removeServer(
            NOMBRE_SERVIDOR_INSTANCIA
        )


if __name__ == "__main__":
    sys.exit(
        iniciar_aplicacion()
    )