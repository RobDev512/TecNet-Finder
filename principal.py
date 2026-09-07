# ============================================================
# Archivo: principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo es el punto de entrada principal de TecNet Finder.
#
# Su única responsabilidad es crear la aplicación de PySide6,
# aplicar el estilo general, mostrar la ventana principal
# maximizada e iniciar el ciclo de eventos.
# ============================================================

import sys  # Importa las herramientas necesarias para recibir argumentos y finalizar correctamente el proceso.

from PySide6.QtWidgets import QApplication  # Importa el objeto principal requerido por toda aplicación Qt.

from Interfaz.estilos import ESTILO_APLICACION  # Importa la hoja de estilos centralizada de TecNet Finder.
from Interfaz.ventana_principal import VentanaPrincipal  # Importa la ventana principal de la aplicación.


def iniciar_aplicacion() -> int:  # Crea y ejecuta la aplicación gráfica completa de TecNet Finder.
    aplicacion = QApplication(sys.argv)  # Inicializa Qt utilizando los argumentos recibidos por Python.
    aplicacion.setApplicationName("TecNet Finder")  # Define el nombre general de la aplicación.
    aplicacion.setStyle("Fusion")  # Utiliza una base visual consistente para los widgets de PySide6.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia centralizada del proyecto.

    ventana = VentanaPrincipal()  # Construye la ventana junto con su barra personalizada y componentes.
    ventana.showMaximized()  # Inicia siempre ocupando toda el área disponible del escritorio.

    return aplicacion.exec()  # Inicia el ciclo de eventos y devuelve el código final cuando la aplicación se cierra.


if __name__ == "__main__":  # Comprueba que principal.py haya sido ejecutado directamente.
    sys.exit(iniciar_aplicacion())  # Ejecuta TecNet Finder y comunica su resultado al sistema operativo.