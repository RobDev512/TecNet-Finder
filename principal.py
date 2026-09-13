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
# preferencias de IA, inicia el servicio compartido cuando es
# necesario e integra la configuración general.
#
# Si el usuario intenta iniciar TecNet Finder nuevamente, la
# segunda ejecución avisa a la primera, lleva su ventana al
# frente y finaliza sin crear otra copia de la aplicación.
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


NOMBRE_SERVIDOR_INSTANCIA = "TecNetFinder_Instancia_Unica"  # Define el identificador local utilizado para reconocer una ejecución existente.
MENSAJE_ACTIVAR_VENTANA = b"ACTIVAR"  # Define el mensaje enviado cuando una segunda ejecución solicita recuperar la primera.


def _avisar_instancia_existente() -> bool:  # Intenta localizar una ejecución previa y solicitar que lleve su ventana al frente.
    conexion = QLocalSocket()  # Crea una conexión temporal destinada únicamente a detectar la instancia existente.
    conexion.connectToServer(NOMBRE_SERVIDOR_INSTANCIA)  # Intenta conectarse con el servidor creado por la primera ejecución.

    if not conexion.waitForConnected(250):
        return False  # Informa que no existe actualmente otra instancia accesible.

    conexion.write(MENSAJE_ACTIVAR_VENTANA)  # Envía la solicitud que debe recuperar la ventana existente.
    conexion.flush()  # Fuerza el envío inmediato del pequeño mensaje.
    conexion.waitForBytesWritten(250)  # Da un margen breve para que el sistema entregue la solicitud.
    conexion.disconnectFromServer()  # Cierra ordenadamente la conexión temporal.
    return True  # Confirma que otra instancia fue localizada y avisada.


def iniciar_aplicacion() -> int:
    aplicacion = QApplication(sys.argv)  # Inicializa Qt utilizando los argumentos recibidos por Python.
    aplicacion.setApplicationName("TecNet Finder")  # Define el nombre general de la aplicación.
    aplicacion.setStyle("Fusion")  # Utiliza una base visual consistente para los widgets de PySide6.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia centralizada del proyecto.

    if _avisar_instancia_existente():
        return 0  # Finaliza silenciosamente porque la instancia original ya recibió la solicitud.

    QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)  # Limpia una referencia obsoleta que pudiera quedar después de un cierre inesperado.
    servidor_instancia = QLocalServer(aplicacion)  # Crea el servidor que representará exclusivamente a esta ejecución.

    if not servidor_instancia.listen(NOMBRE_SERVIDOR_INSTANCIA):
        if _avisar_instancia_existente():
            return 0  # Resuelve una posible carrera si otra instancia terminó de iniciar unos milisegundos antes.

        QMessageBox.critical(
            None,
            "TecNet Finder",
            "No fue posible reservar el identificador de instancia única de TecNet Finder.",
        )  # Informa el fallo en lugar de permitir silenciosamente varias ejecuciones.
        return 1  # Finaliza porque no puede garantizarse el comportamiento solicitado.

    componente_ia = GestorComponenteIA()  # Localiza la instalación opcional administrada fuera del código fuente.
    preferencias_ia = PreferenciasIA()  # Recupera independientemente las decisiones sobre autocompletado y diagnósticos.
    gestor_ollama = GestorOllama(componente_ia=componente_ia)  # Prepara el servidor utilizando exactamente la instalación detectada.

    asistencia_disponible = False  # Mantiene desactivadas las consultas hasta confirmar que el servicio pueda utilizarse.

    if componente_ia.instalado() and preferencias_ia.alguna_funcion_activada():
        asistencia_disponible = gestor_ollama.iniciar()  # Inicia Ollama una sola vez cuando al menos una función configurada lo necesita.

    ventana = VentanaPrincipal()  # Construye la única ventana principal permitida durante esta ejecución.
    ventana.control_configuracion = ControlConfiguracion(
        ventana=ventana,
        gestor_ollama=gestor_ollama,
        componente_ia=componente_ia,
        preferencias_ia=preferencias_ia,
        asistencia_disponible_inicial=asistencia_disponible,
    )  # Mantiene la configuración general vinculada con los componentes activos durante toda la ejecución.

    def atender_nueva_instancia() -> None:
        while servidor_instancia.hasPendingConnections():
            conexion = servidor_instancia.nextPendingConnection()  # Recupera cada ejecución secundaria que consiguió conectarse.

            if conexion is None:
                break  # Evita procesar una conexión inexistente en una situación excepcional.

            if conexion.bytesAvailable() == 0:
                conexion.waitForReadyRead(150)  # Espera brevemente cuando la conexión llegó unos instantes antes que el mensaje.

            mensaje = bytes(conexion.readAll())  # Recupera la solicitud enviada por la ejecución secundaria.

            if mensaje == MENSAJE_ACTIVAR_VENTANA:
                ventana.activar_desde_instancia_secundaria()  # Recupera la ventana original sin construir otra aplicación.

            conexion.disconnectFromServer()  # Cierra la conexión después de atender la única acción disponible.
            conexion.deleteLater()  # Permite que Qt libere posteriormente el objeto de comunicación.

    servidor_instancia.newConnection.connect(atender_nueva_instancia)  # Escucha todos los futuros intentos de abrir otra copia.

    ventana.showMaximized()  # Inicia la primera ejecución ocupando toda el área disponible del escritorio.

    try:
        return aplicacion.exec()  # Mantiene activa la interfaz hasta que el usuario cierre TecNet Finder.
    finally:
        gestor_ollama.detener()  # Cierra únicamente la instancia privada creada por esta ejecución.
        servidor_instancia.close()  # Libera el servidor utilizado para impedir ejecuciones duplicadas.
        QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)  # Elimina cualquier referencia local para permitir un inicio limpio posterior.


if __name__ == "__main__":
    sys.exit(iniciar_aplicacion())  # Ejecuta TecNet Finder y comunica su resultado al sistema operativo.