# ============================================================
# Archivo: principal.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo es el punto de entrada principal de TecNet Finder.
#
# Su única responsabilidad es crear la aplicación de PySide6,
# aplicar el estilo general, mostrar la ventana principal e
# iniciar el ciclo de eventos de la interfaz gráfica.
# ============================================================

import sys  # Importa las herramientas necesarias para recibir argumentos y finalizar correctamente el proceso.

from PySide6.QtWidgets import QApplication  # Importa el objeto principal requerido por toda aplicación desarrollada con Qt.

from Interfaz.estilos import ESTILO_APLICACION  # Importa la hoja de estilos centralizada de TecNet Finder.
from Interfaz.ventana_principal import VentanaPrincipal  # Importa la ventana que contiene todos los componentes visuales.


def iniciar_aplicacion() -> int:  # Crea y ejecuta la aplicación gráfica completa de TecNet Finder.
    aplicacion = QApplication(sys.argv)  # Inicializa Qt utilizando los argumentos recibidos por el proceso de Python.
    aplicacion.setApplicationName("TecNet Finder")  # Define el nombre de la aplicación para Qt y el sistema operativo.
    aplicacion.setStyle("Fusion")  # Utiliza un estilo base consistente entre diferentes versiones de Windows.
    aplicacion.setStyleSheet(ESTILO_APLICACION)  # Aplica la apariencia centralizada definida dentro de Interfaz.
    ventana = VentanaPrincipal()  # Construye la ventana principal junto con todos sus paneles.
    ventana.show()  # Hace visible la interfaz gráfica en pantalla.
    return aplicacion.exec()  # Inicia el ciclo de eventos y devuelve el código de salida cuando la ventana se cierre.


if __name__ == "__main__":  # Comprueba que el archivo haya sido ejecutado directamente y no solamente importado.
    sys.exit(iniciar_aplicacion())  # Ejecuta la aplicación y comunica al sistema operativo su código final.