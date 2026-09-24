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
# se cerró maximizado o utilizando Modo ventana.
#
# Media pantalla y pantalla completa se consideran estados
# temporales y nunca se restauran automáticamente al iniciar.
# ============================================================

import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from AsistenteIA.infraestructura.gestor_componente_ia import GestorComponenteIA
from AsistenteIA.infraestructura.gestor_ollama import GestorOllama
from AsistenteIA.preferencias.preferencias_ia import PreferenciasIA
from Interfaz.apariencia.control_recuperacion_pantalla import ControlRecuperacionPantalla
from Interfaz.apariencia.estilos import ESTILO_APLICACION
from Interfaz.configuracion.control_configuracion_idioma import ControlConfiguracionIdioma
from Interfaz.ventanas.ventana_principal import VentanaPrincipal
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion


NOMBRE_SERVIDOR_INSTANCIA = "TecNetFinder_Instancia_Unica"
MENSAJE_ACTIVAR_VENTANA = b"ACTIVAR"


def _avisar_instancia_existente() -> bool:
    conexion = QLocalSocket()
    conexion.connectToServer(NOMBRE_SERVIDOR_INSTANCIA)

    if not conexion.waitForConnected(250):
        return False

    conexion.write(MENSAJE_ACTIVAR_VENTANA)
    conexion.flush()
    conexion.waitForBytesWritten(250)
    conexion.disconnectFromServer()
    return True


def _mostrar_ventana_normal_centrada(
    aplicacion: QApplication,
    ventana: VentanaPrincipal,
) -> None:
    pantalla = aplicacion.primaryScreen()
    ventana.preparar_modo_ventana_inicial(pantalla)
    ventana.show()


def _mostrar_ventana_segun_preferencias(
    aplicacion: QApplication,
    ventana: VentanaPrincipal,
    preferencias: PreferenciasAplicacion,
) -> None:
    estado_recordado = None

    if preferencias.recordar_estado_ventana():
        estado_recordado = preferencias.ultimo_estado_ventana()

    if (
        estado_recordado
        == PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
    ):
        ventana.showMaximized()
        return

    if (
        estado_recordado
        == PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
    ):
        _mostrar_ventana_normal_centrada(aplicacion, ventana)
        return

    if preferencias.iniciar_maximizado():
        ventana.showMaximized()
        return

    _mostrar_ventana_normal_centrada(aplicacion, ventana)


def _guardar_estado_final_ventana(
    ventana: VentanaPrincipal,
    preferencias: PreferenciasAplicacion,
) -> None:
    if not preferencias.recordar_estado_ventana():
        return

    if ventana.en_pantalla_completa:
        estado = (
            PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
            if ventana.modo_antes_pantalla_completa == "maximizado"
            else PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
        )
    elif ventana.en_media_pantalla:
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
    elif ventana.en_modo_ventana:
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL
    elif ventana.isMaximized():
        estado = PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA
    else:
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL

    preferencias.establecer_ultimo_estado_ventana(estado)


def iniciar_aplicacion() -> int:
    aplicacion = QApplication(sys.argv)
    aplicacion.setApplicationName("TecNet Finder")
    aplicacion.setStyle("Fusion")
    aplicacion.setStyleSheet(ESTILO_APLICACION)

    if _avisar_instancia_existente():
        return 0

    QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)
    servidor_instancia = QLocalServer(aplicacion)

    if not servidor_instancia.listen(NOMBRE_SERVIDOR_INSTANCIA):
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
    preferencias_aplicacion = PreferenciasAplicacion()
    gestor_ollama = GestorOllama(componente_ia=componente_ia)
    asistencia_disponible = False

    if (
        componente_ia.instalado()
        and preferencias_ia.alguna_funcion_activada()
    ):
        asistencia_disponible = gestor_ollama.iniciar()

    ventana = VentanaPrincipal()
    ventana.control_configuracion = ControlConfiguracionIdioma(
        ventana=ventana,
        gestor_ollama=gestor_ollama,
        componente_ia=componente_ia,
        preferencias_ia=preferencias_ia,
        asistencia_disponible_inicial=asistencia_disponible,
        preferencias_aplicacion=preferencias_aplicacion,
    )

    # Mantiene los números de línea sincronizados con la fuente del editor
    # y recupera automáticamente la apariencia después de suspensión/DPI.
    ventana.control_recuperacion_pantalla = ControlRecuperacionPantalla(
        aplicacion=aplicacion,
        ventana=ventana,
        gestor_tipografia=ventana.control_configuracion.gestor_tipografia,
    )

    def atender_nueva_instancia() -> None:
        while servidor_instancia.hasPendingConnections():
            conexion = servidor_instancia.nextPendingConnection()

            if conexion is None:
                break

            if conexion.bytesAvailable() == 0:
                conexion.waitForReadyRead(150)

            mensaje = bytes(conexion.readAll())

            if mensaje == MENSAJE_ACTIVAR_VENTANA:
                ventana.activar_desde_instancia_secundaria()

            conexion.disconnectFromServer()
            conexion.deleteLater()

    servidor_instancia.newConnection.connect(atender_nueva_instancia)
    _mostrar_ventana_segun_preferencias(
        aplicacion,
        ventana,
        preferencias_aplicacion,
    )

    try:
        resultado_aplicacion = aplicacion.exec()
        _guardar_estado_final_ventana(
            ventana,
            preferencias_aplicacion,
        )
        return resultado_aplicacion
    finally:
        gestor_ollama.detener()
        servidor_instancia.close()
        QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)


if __name__ == "__main__":
    sys.exit(iniciar_aplicacion())
