# ============================================================
# Archivo: principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo es el punto de entrada principal de TecNet Finder.
#
# Crea la aplicación gráfica, prepara silenciosamente el servicio
# local de inteligencia artificial, muestra la ventana principal
# maximizada y garantiza la limpieza del proceso privado de Ollama
# cuando la aplicación termina.
# ============================================================

import sys  # Importa las herramientas necesarias para recibir argumentos y finalizar correctamente el proceso.

from PySide6.QtWidgets import QApplication  # Importa el objeto principal requerido por toda aplicación Qt.

from AsistenteIA.gestor_ollama import GestorOllama  # Importa el administrador del servidor privado utilizado por la inteligencia artificial.
from Interfaz.estilos import ESTILO_APLICACION  # Importa la hoja de estilos centralizada de TecNet Finder.
from Interfaz.ventana_principal import VentanaPrincipal  # Importa la ventana principal de la aplicación.


def iniciar_aplicacion() -> int:
    aplicacion = QApplication(sys.argv)  # Inicializa Qt utilizando los argumentos recibidos por Python.
    aplicacion.setApplicationName("TecNet Finder")  # Define el nombre general de la aplicación.
    aplicacion.setStyle("Fusion")  # Utiliza una base visual consistente para los widgets de PySide6.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia centralizada del proyecto.

    gestor_ollama = GestorOllama()  # Prepara el control independiente del asistente local.
    gestor_ollama.iniciar()  # Intenta disponer de IA sin convertir su funcionamiento en requisito para abrir el compilador.

    ventana = VentanaPrincipal()  # Construye la ventana junto con su barra personalizada y componentes.
    ventana.showMaximized()  # Inicia siempre ocupando toda el área disponible del escritorio.

    try:
        return aplicacion.exec()  # Mantiene activa la interfaz hasta que el usuario cierre TecNet Finder.
    finally:
        gestor_ollama.detener()  # Cierra únicamente el Ollama que esta ejecución haya iniciado por su cuenta.


if __name__ == "__main__":
    sys.exit(iniciar_aplicacion())  # Ejecuta TecNet Finder y comunica su resultado al sistema operativo.