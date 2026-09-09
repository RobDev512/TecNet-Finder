# ============================================================
# Archivo: principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo es el punto de entrada principal de TecNet Finder.
#
# Crea la aplicación gráfica, consulta las preferencias de la
# asistencia local, inicia su servicio solamente cuando corresponde,
# integra la configuración general y garantiza la limpieza del
# proceso privado cuando la aplicación termina.
# ============================================================

import sys  # Importa las herramientas necesarias para recibir argumentos y finalizar correctamente el proceso.

from PySide6.QtWidgets import QApplication  # Importa el objeto principal requerido por toda aplicación Qt.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite detectar la instalación opcional administrada para el usuario.
from AsistenteIA.gestor_ollama import GestorOllama  # Importa el administrador del servidor privado utilizado por la inteligencia artificial.
from AsistenteIA.preferencias_ia import PreferenciasIA  # Permite respetar la decisión persistente de activar o desactivar la asistencia.
from Interfaz.control_configuracion import ControlConfiguracion  # Integra la ventana general de configuración con TecNet Finder.
from Interfaz.estilos import ESTILO_APLICACION  # Importa la hoja de estilos centralizada de TecNet Finder.
from Interfaz.ventana_principal import VentanaPrincipal  # Importa la ventana principal de la aplicación.


def iniciar_aplicacion() -> int:
    aplicacion = QApplication(sys.argv)  # Inicializa Qt utilizando los argumentos recibidos por Python.
    aplicacion.setApplicationName("TecNet Finder")  # Define el nombre general de la aplicación.
    aplicacion.setStyle("Fusion")  # Utiliza una base visual consistente para los widgets de PySide6.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia centralizada del proyecto.

    componente_ia = GestorComponenteIA()  # Localiza la instalación opcional administrada fuera del código fuente.
    preferencias_ia = PreferenciasIA()  # Recupera la decisión persistente del usuario sobre el autocompletado.
    gestor_ollama = GestorOllama(componente_ia=componente_ia)  # Prepara el servidor utilizando exactamente la instalación detectada.

    asistencia_disponible = False  # Mantiene desactivadas las consultas hasta confirmar que el servicio pueda utilizarse.

    if componente_ia.instalado() and preferencias_ia.asistencia_activada():
        asistencia_disponible = gestor_ollama.iniciar()  # Inicia Ollama únicamente cuando existe el componente y el usuario desea utilizarlo.

    ventana = VentanaPrincipal()  # Construye la ventana principal y sus componentes.
    ventana.control_configuracion = ControlConfiguracion(
        ventana=ventana,
        gestor_ollama=gestor_ollama,
        componente_ia=componente_ia,
        preferencias_ia=preferencias_ia,
        asistencia_disponible_inicial=asistencia_disponible,
    )  # Mantiene la configuración general vinculada con los componentes activos durante toda la ejecución.

    ventana.showMaximized()  # Inicia siempre ocupando toda el área disponible del escritorio.

    try:
        return aplicacion.exec()  # Mantiene activa la interfaz hasta que el usuario cierre TecNet Finder.
    finally:
        gestor_ollama.detener()  # Cierra únicamente la instancia privada creada por esta ejecución.


if __name__ == "__main__":
    sys.exit(iniciar_aplicacion())  # Ejecuta TecNet Finder y comunica su resultado al sistema operativo.