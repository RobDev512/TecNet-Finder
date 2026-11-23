# ============================================================
# Archivo: prueba_selector_niveles_registros.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Valida que mantenimiento reutiliza el selector visual
# del visor de triplos sin alterar los filtros del registro.
# ============================================================

import os  # Permite ejecutar las pruebas de interfaz sin abrir una ventana visible.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Prepara Qt antes de importar sus controles.

from PySide6.QtWidgets import QApplication  # Crea la aplicación necesaria para las pruebas gráficas.

from Interfaz.resultados.visor_triplos import SelectorInstruccionTriplos  # Recupera la implementación visual que ya funciona.
from Interfaz.ventanas.selector_niveles_registros import SelectorNivelesRegistros  # Verifica la adaptación para mantenimiento.
from Interfaz.ventanas.ventana_mantenimiento import VentanaMantenimiento  # Comprueba la integración con la ventana existente.
from Motor.configuracion.catalogo_temas import TEMA_PREDETERMINADO, obtener_tema  # Proporciona una paleta real para comprobar los estados.


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la instancia de Qt sin duplicar aplicaciones.


def prueba_mantenimiento_utiliza_selector_actualizado():
    _app()  # Inicializa Qt antes de crear el diálogo.
    ventana = VentanaMantenimiento()  # Construye el Centro de mantenimiento real.
    assert isinstance(ventana.selector_nivel, SelectorNivelesRegistros)  # Mantiene la integración creada anteriormente.
    assert ventana.selector_nivel.count() >= 1  # Conserva las opciones de niveles.
    assert ventana.selector_nivel.itemData(0) == ""  # No altera el valor especial de Todos los niveles.
    ventana.close()  # Libera el diálogo después de la prueba.


def prueba_selector_reutiliza_clase_del_visor_de_triplos():
    _app()  # Inicializa Qt antes de construir los controles.
    selector = SelectorNivelesRegistros()  # Crea el selector de registros.
    assert isinstance(selector, SelectorInstruccionTriplos)  # Confirma que se heredan el dibujo, la flecha y la posición del menú.
    assert selector.vista_opciones.objectName() == "OpcionesInstruccionTriplo"  # Comparte la misma lista aprobada.
    selector.close()  # Evita dejar controles abiertos al terminar.


def prueba_seleccion_y_hover_son_colores_distintos():
    _app()  # Inicializa los controles de Qt.
    selector = SelectorNivelesRegistros()  # Reutiliza el componente original.
    for opcion in ("Todos", "ERROR", "INFO"): selector.addItem(opcion)  # Crea las mismas tres opciones del mantenimiento.
    selector.aplicar_tema(obtener_tema(TEMA_PREDETERMINADO))  # Configura los tres estados a partir del tema activo.
    selector.setCurrentIndex(0)  # Conserva seleccionada la primera opción.
    selector.vista_opciones.fila_hover = 1  # Coloca el cursor sobre una opción diferente.
    seleccionado, _ = selector.delegado_opciones.colores_fila(0)  # Obtiene el color de la selección confirmada.
    hover, _ = selector.delegado_opciones.colores_fila(1)  # Obtiene el azul del cursor.
    normal, _ = selector.delegado_opciones.colores_fila(2)  # Obtiene el fondo sin interacción.
    assert len({seleccionado.name(), hover.name(), normal.name()}) == 3  # Comprueba que los estados son distintos.
    assert selector.currentIndex() == 0  # El hover no altera el nivel del filtro.
    selector.close()  # Libera el componente temporal.


def prueba_menu_se_abre_debajo_si_hay_espacio():
    app = _app()  # Inicializa Qt para comprobar la posición global.
    selector = SelectorNivelesRegistros()  # Prepara el desplegable heredado.
    for opcion in ("Todos", "ERROR", "INFO"): selector.addItem(opcion)  # Crea un menú con tres opciones.
    selector.aplicar_tema(obtener_tema(TEMA_PREDETERMINADO))  # Aplica el tema antes de mostrarlo.
    selector.resize(250, 42)  # Reserva el ancho del control y la flecha.
    selector.move(10, 10)  # Mantiene espacio debajo del selector en pruebas.
    selector.show()  # Inicializa la geometría visible.
    app.processEvents()  # Completa los cambios pendientes de posición.
    selector.showPopup()  # Abre el menú con la implementación original de triplos.
    app.processEvents()  # Refresca las coordenadas del popup.
    ventana = selector.view().window()  # Recupera el menú flotante.
    assert ventana.isVisible()  # Comprueba que el menú está abierto.
    assert ventana.y() >= selector.mapToGlobal(selector.rect().bottomLeft()).y()  # Comprueba que no tapa el cuadro si hay espacio.
    selector.hidePopup()  # Cierra el menú antes de terminar.
    selector.close()  # Libera el control.
