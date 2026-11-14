# ============================================================
# Archivo: principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene el punto de entrada principal de TecNet Finder.
# Crea la interfaz gráfica, evita ejecutar varias instancias
# simultáneas y conecta las preferencias generales y de IA.
#
# Recupera únicamente los estados permitidos de la ventana,
# coordina el cierre del runtime de IA y activa el registro
# de eventos introducido en la actualización v1.2.2.
# ============================================================

import sys  # Proporciona los argumentos del proceso y permite devolver el código final de ejecución.

from PySide6.QtNetwork import QLocalServer, QLocalSocket  # Impide abrir instancias duplicadas y comunica la solicitud de activación.
from PySide6.QtWidgets import QApplication, QMessageBox  # Prepara la aplicación gráfica y los avisos importantes.

from AsistenteIA.infraestructura.gestor_componente_ia import GestorComponenteIA  # Comprueba la disponibilidad del componente local de IA.
from AsistenteIA.infraestructura.gestor_ollama import GestorOllama  # Administra el runtime local de Ollama.
from AsistenteIA.preferencias.preferencias_ia import PreferenciasIA  # Recupera las preferencias específicas de asistencia.
from Interfaz.apariencia.control_recuperacion_pantalla import ControlRecuperacionPantalla  # Reajusta la apariencia después de cambios de pantalla.
from Interfaz.apariencia.estilos import ESTILO_APLICACION  # Proporciona los estilos visuales generales.
from Interfaz.configuracion.control_configuracion_idioma import ControlConfiguracionIdioma  # Vincula Configuración y los idiomas disponibles.
from Interfaz.ventanas.ventana_principal import VentanaPrincipal  # Construye la ventana principal de TecNet Finder.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Almacena las preferencias de ventana y aplicación.
from Motor.infraestructura.registro import configurar_registro  # Inicializa el sistema de logs de v1.2.2.


# ============================================================
# Identificación de la instancia única
# ============================================================

NOMBRE_SERVIDOR_INSTANCIA = "TecNetFinder_Instancia_Unica"  # Identifica el servidor local utilizado por TecNet Finder.
MENSAJE_ACTIVAR_VENTANA = b"ACTIVAR"  # Solicita recuperar una ventana que ya se encuentra abierta.


def _avisar_instancia_existente() -> bool:  # Contacta una instancia anterior para pedirle que vuelva a mostrarse.
    conexion = QLocalSocket()  # Prepara un cliente para comunicarse con el servidor local.
    conexion.connectToServer(NOMBRE_SERVIDOR_INSTANCIA)  # Intenta localizar la instancia activa.

    if not conexion.waitForConnected(250):  # Comprueba si existe una conexión disponible en el tiempo permitido.
        return False  # Indica que no se encontró una instancia receptora.

    conexion.write(MENSAJE_ACTIVAR_VENTANA)  # Solicita que la ventana existente vuelva al frente.
    conexion.flush()  # Envía inmediatamente los datos pendientes.
    conexion.waitForBytesWritten(250)  # Da un breve margen para completar el envío.
    conexion.disconnectFromServer()  # Cierra la conexión después de notificar.
    return True  # Confirma que había otra instancia disponible.


# ============================================================
# Recuperación de la ventana principal
# ============================================================

def _mostrar_ventana_normal_centrada(aplicacion: QApplication, ventana: VentanaPrincipal) -> None:  # Prepara el Modo ventana inicial.
    pantalla = aplicacion.primaryScreen()  # Obtiene el monitor principal disponible.
    ventana.preparar_modo_ventana_inicial(pantalla)  # Aplica la geometría apropiada antes de mostrar la ventana.
    ventana.show()  # Presenta la aplicación al usuario.


def _mostrar_ventana_segun_preferencias(aplicacion: QApplication, ventana: VentanaPrincipal, preferencias: PreferenciasAplicacion) -> None:  # Recupera el estado inicial permitido.
    estado_recordado = None  # Parte de un estado sin recuperación explícita.

    if preferencias.recordar_estado_ventana():  # Comprueba si el usuario solicitó recordar el estado anterior.
        estado_recordado = preferencias.ultimo_estado_ventana()  # Recupera únicamente normal o maximizada.

    if estado_recordado == PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA:  # Da prioridad al último estado maximizado.
        ventana.showMaximized()  # Ocupa todo el espacio disponible de la pantalla.
        return  # Finaliza porque el estado ya quedó restaurado.

    if estado_recordado == PreferenciasAplicacion.ESTADO_VENTANA_NORMAL:  # Comprueba si se recordó el Modo ventana.
        _mostrar_ventana_normal_centrada(aplicacion, ventana)  # Recupera la ventana normal con geometría válida.
        return  # Evita aplicar también las preferencias de inicio convencional.

    if preferencias.iniciar_maximizado():  # Consulta la preferencia de inicio cuando no existe un estado recordado.
        ventana.showMaximized()  # Abre maximizado según la elección del usuario.
        return  # Evita mostrar la ventana una segunda vez.

    _mostrar_ventana_normal_centrada(aplicacion, ventana)  # Utiliza Modo ventana cuando no corresponde maximizar.


def _guardar_estado_final_ventana(ventana: VentanaPrincipal, preferencias: PreferenciasAplicacion) -> None:  # Conserva el estado seguro al terminar.
    if not preferencias.recordar_estado_ventana():  # Respeta la decisión de no recordar la última presentación.
        return  # Finaliza sin sobrescribir preferencias.

    if ventana.en_pantalla_completa:  # Determina el estado persistente cuando se cierra desde fullscreen.
        estado = PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA if ventana.modo_antes_pantalla_completa == "maximizado" else PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Recupera el modo anterior permitido.
    elif ventana.en_media_pantalla:  # Media pantalla es temporal y nunca debe persistirse.
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Guarda su equivalente recuperable.
    elif ventana.en_modo_ventana:  # Comprueba si ya se utilizaba la ventana fija.
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Conserva el estado normal.
    elif ventana.isMaximized():  # Comprueba la maximización convencional.
        estado = PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA  # Conserva el modo maximizado.
    else:  # Atiende cualquier presentación que no corresponda a los estados anteriores.
        estado = PreferenciasAplicacion.ESTADO_VENTANA_NORMAL  # Utiliza el respaldo más seguro.

    preferencias.establecer_ultimo_estado_ventana(estado)  # Persiste la decisión para la siguiente ejecución.


# ============================================================
# Inicio y cierre de TecNet Finder
# ============================================================

def iniciar_aplicacion() -> int:  # Construye los componentes y ejecuta el ciclo principal de Qt.
    logger = configurar_registro()  # Activa el historial local de eventos de la aplicación.
    logger.info("Iniciando TecNet Finder")  # Registra el comienzo de esta sesión.
    aplicacion = QApplication(sys.argv)  # Inicializa el entorno gráfico de PySide6.
    aplicacion.setApplicationName("TecNet Finder")  # Define el nombre reconocido por el sistema.
    aplicacion.setStyle("Fusion")  # Mantiene el estilo base utilizado por el proyecto.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia general.

    if _avisar_instancia_existente():  # Comprueba si otra instancia ya está ejecutándose.
        return 0  # Termina esta ejecución porque la anterior recibió la solicitud de activación.

    QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)  # Retira un posible identificador obsoleto.
    servidor_instancia = QLocalServer(aplicacion)  # Prepara el servidor de comunicación local.

    if not servidor_instancia.listen(NOMBRE_SERVIDOR_INSTANCIA):  # Comprueba si pudo reservarse el identificador exclusivo.
        if _avisar_instancia_existente():  # Intenta activar una instancia que pudo iniciarse al mismo tiempo.
            return 0  # Evita abrir una aplicación duplicada.

        QMessageBox.critical(None, "TecNet Finder", "No fue posible reservar el identificador de instancia única de TecNet Finder.")  # Informa que el inicio no puede continuar.
        return 1  # Señala que hubo un problema de inicialización.

    componente_ia = GestorComponenteIA()  # Detecta si está instalado el componente opcional de IA.
    preferencias_ia = PreferenciasIA()  # Consulta las decisiones relacionadas con la asistencia.
    preferencias_aplicacion = PreferenciasAplicacion()  # Recupera la configuración general de TecNet Finder.
    gestor_ollama = GestorOllama(componente_ia=componente_ia)  # Administra el runtime local cuando corresponde.
    asistencia_disponible = False  # Parte de un inicio sin asistencia activa.

    if componente_ia.instalado() and preferencias_ia.alguna_funcion_activada():  # Inicia Ollama solo cuando está disponible y el usuario lo requiere.
        asistencia_disponible = gestor_ollama.iniciar()  # Conserva el resultado efectivo del inicio.

    ventana = VentanaPrincipal()  # Construye la ventana principal y los paneles del compilador.
    ventana.control_configuracion = ControlConfiguracionIdioma(ventana=ventana, gestor_ollama=gestor_ollama, componente_ia=componente_ia, preferencias_ia=preferencias_ia, asistencia_disponible_inicial=asistencia_disponible, preferencias_aplicacion=preferencias_aplicacion)  # Integra Configuración e idiomas.

    # Mantiene la numeración del editor y restaura la apariencia después de suspensión o cambios de DPI.
    ventana.control_recuperacion_pantalla = ControlRecuperacionPantalla(aplicacion=aplicacion, ventana=ventana, gestor_tipografia=ventana.control_configuracion.gestor_tipografia)  # Activa el control de recuperación visual.

    def atender_nueva_instancia() -> None:  # Procesa las solicitudes recibidas desde otra ejecución de TecNet Finder.
        while servidor_instancia.hasPendingConnections():  # Atiende todas las conexiones que todavía están pendientes.
            conexion = servidor_instancia.nextPendingConnection()  # Obtiene la siguiente conexión disponible.

            if conexion is None:  # Comprueba si Qt no pudo entregar un socket válido.
                break  # Abandona el ciclo sin intentar utilizar un objeto inexistente.

            if conexion.bytesAvailable() == 0:  # Comprueba si todavía no ha llegado el mensaje.
                conexion.waitForReadyRead(150)  # Da un breve margen para recibir los datos.

            mensaje = bytes(conexion.readAll())  # Convierte los bytes recibidos a un valor comparable.

            if mensaje == MENSAJE_ACTIVAR_VENTANA:  # Reconoce la solicitud legítima de mostrar la instancia existente.
                ventana.activar_desde_instancia_secundaria()  # Recupera y lleva al frente la ventana principal.

            conexion.disconnectFromServer()  # Cierra la comunicación después de atenderla.
            conexion.deleteLater()  # Solicita a Qt liberar el objeto cuando corresponda.

    servidor_instancia.newConnection.connect(atender_nueva_instancia)  # Vincula las conexiones entrantes con su controlador.
    _mostrar_ventana_segun_preferencias(aplicacion, ventana, preferencias_aplicacion)  # Presenta la ventana en el modo seleccionado.

    try:  # Ejecuta el ciclo gráfico y conserva la oportunidad de guardar el último estado.
        resultado_aplicacion = aplicacion.exec()  # Mantiene TecNet Finder abierto mientras exista la aplicación.
        _guardar_estado_final_ventana(ventana, preferencias_aplicacion)  # Guarda el estado recuperable del usuario.
        return resultado_aplicacion  # Devuelve el resultado producido por Qt.
    finally:  # Libera los recursos compartidos, incluso cuando el ciclo termina con errores.
        gestor_ollama.detener()  # Detiene el runtime local administrado por TecNet Finder.
        servidor_instancia.close()  # Deja de escuchar conexiones nuevas.
        QLocalServer.removeServer(NOMBRE_SERVIDOR_INSTANCIA)  # Libera el identificador de instancia única.


# ============================================================
# Punto de ejecución directa
# ============================================================

if __name__ == "__main__":  # Evita arrancar la interfaz cuando este módulo solamente se importa.
    sys.exit(iniciar_aplicacion())  # Ejecuta el programa y comunica su resultado al sistema.
