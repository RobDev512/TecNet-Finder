# ============================================================
# Archivo: prueba_integracion_selector_mantenimiento.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Evita que el controlador del diálogo reemplace el delegado
# del selector compartido con el visor de triplos.
# ============================================================

import os  # Permite ejecutar las pruebas de Qt sin ventanas físicas.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Prepara la plataforma antes de importar PySide6.

from PySide6.QtWidgets import QApplication  # Mantiene una instancia válida para construir los controles.

from Interfaz.ventanas.selector_niveles_registros import SelectorNivelesRegistros  # Recupera el selector ya instalado.
from Interfaz.ventanas.ventana_mantenimiento import VentanaMantenimiento  # Comprueba el diálogo completo del proyecto.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza Qt durante toda la sesión de pruebas.


def prueba_mantenimiento_no_sustituye_delegado_del_selector():
    _aplicacion()  # Inicializa los controles de PySide6.
    ventana = VentanaMantenimiento()  # Construye la ventana con sus filtros de niveles.
    selector = ventana.selector_nivel  # Recupera el selector de Registros.
    assert isinstance(selector, SelectorNivelesRegistros)  # Comprueba que sigue instalado el componente visual aprobado.
    delegado = selector.delegado_opciones  # Conserva el delegado que pinta las opciones redondeadas.
    ventana._ajuste_mantenimiento._preparar_selector_niveles()  # Simula el controlador que antes sobrescribía el estilo.
    assert selector.view().itemDelegate() is delegado  # Impide que vuelva a instalarse el delegado rectangular anterior.
    assert selector.view().objectName() == "OpcionesInstruccionTriplo"  # Mantiene la lista heredada del visor de triplos.
    assert ventana._ajuste_mantenimiento.flecha is None  # Impide superponer la flecha antigua sobre la personalizada.
    ventana.close()  # Libera el diálogo de prueba.


def prueba_apertura_real_conserva_el_estilo_del_selector():
    app = _aplicacion()  # Recupera la aplicación antes de mostrar la ventana.
    ventana = VentanaMantenimiento()  # Construye el mismo diálogo que abre el usuario.
    selector = ventana.selector_nivel  # Conserva la referencia a su filtro.
    delegado = selector.delegado_opciones  # Identifica la implementación visual antes de mostrarlo.
    ventana.show()  # Activa la apertura que anteriormente reinstalaba el delegado antiguo.
    app.processEvents()  # Ejecuta las tareas de distribución y la primera apertura.
    app.processEvents()  # Permite completar la actualización diferida del Centro de mantenimiento.
    assert selector.view().itemDelegate() is delegado  # Comprueba que la apertura no reemplaza las opciones redondeadas.
    assert selector.count() >= 1 and selector.itemData(0) == ""  # Conserva los valores del filtro de registros.
    ventana.close()  # Finaliza la prueba sin alterar los archivos de registro.
