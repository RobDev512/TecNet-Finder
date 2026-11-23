# ============================================================
# Archivo: prueba_cierre_redondeado_mantenimiento.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Verifica que el botón X del Centro de mantenimiento conserve
# su esquina superior derecha redondeada en todos los estados,
# sin cambiar el estilo de los demás diálogos.
# ============================================================

import os  # Permite crear ventanas durante las pruebas sin abrir la interfaz física.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Inicializa Qt en modo de pruebas automatizadas.

from PySide6.QtCore import QEvent  # Permite simular eventos recibidos durante la liberación de un diálogo.
from PySide6.QtWidgets import QApplication, QDialog  # Construye diálogos reales para inspeccionar su estilo.

from Interfaz.ventanas.marco_dialogo import preparar_dialogo_con_barra  # Aplica el encabezado compartido de TecNet Finder.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Conserva Qt activo mientras se comprueban los controles.


def prueba_boton_cerrar_mantenimiento_redondea_todos_sus_estados():
    _aplicacion()  # Garantiza que exista una aplicación Qt.
    ventana = QDialog()  # Crea un diálogo con el mismo identificador que mantenimiento.
    ventana.setObjectName("VentanaMantenimiento")  # Activa únicamente el tratamiento visual de esta ventana.
    preparar_dialogo_con_barra(ventana, "Centro de mantenimiento")  # Construye la barra y su botón cerrar.
    boton = ventana.barra_titulo.boton_cerrar  # Recupera el botón original y evita sustituirlo por otro.
    estilo = boton.styleSheet()  # Obtiene las reglas locales que prevalecen sobre el tema general.
    assert estilo.count("border-top-right-radius: 12px") == 4  # Verifica normal, hover, presionado y deshabilitado.
    assert "QPushButton#BotonCerrar:hover" in estilo  # Mantiene el fondo rojo al acercar el cursor.
    assert "QPushButton#BotonCerrar:pressed" in estilo  # Mantiene el fondo rojo oscuro al presionar.
    assert boton.objectName() == "BotonCerrar"  # Conserva el identificador compartido y sus iconos.
    ventana.close()  # Libera la ventana después de comprobar el estilo.


def prueba_redondeado_no_modifica_otros_dialogos():
    _aplicacion()  # Prepara los widgets de la segunda comprobación.
    ventana = QDialog()  # Construye un diálogo diferente al Centro de mantenimiento.
    ventana.setObjectName("DialogoPruebaTecNet")  # Evita activar la excepción de mantenimiento.
    preparar_dialogo_con_barra(ventana, "Otro diálogo")  # Reutiliza la barra compartida sin alterar su comportamiento.
    assert not ventana.barra_titulo.boton_cerrar.styleSheet()  # Garantiza que la regla local no afecte a otras ventanas.
    ventana.close()  # Finaliza la prueba sin dejar controles abiertos.


def prueba_filtro_mantenimiento_ignora_eventos_durante_liberacion():
    _aplicacion()  # Inicializa Qt antes de preparar el controlador del diálogo.
    ventana = QDialog()  # Construye el diálogo que actúa como propietario del filtro.
    from Interfaz.ventanas.marco_dialogo import AjusteMantenimiento  # Recupera la clase que recibe los eventos.
    ajuste = AjusteMantenimiento(ventana, {})  # Crea el filtro sin instalarlo en una ventana real.
    del ajuste.dialogo  # Simula la pérdida de atributos durante el proceso de destrucción de Qt.
    evento = QEvent(QEvent.Type.Show)  # Genera el evento que provocaba el fallo intermitente.
    assert ajuste.eventFilter(ventana, evento) is False  # Comprueba que no se intenta acceder a un atributo inexistente.
    ventana.close()  # Termina la comprobación sin dejar ventanas abiertas.
