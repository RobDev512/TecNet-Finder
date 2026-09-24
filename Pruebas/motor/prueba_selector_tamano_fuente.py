# ============================================================
# Archivo: prueba_selector_tamano_fuente.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba el selector editable utilizado para los tamaños de
# fuente de la interfaz y del editor.
# ============================================================

from PySide6.QtWidgets import QApplication

from Interfaz.configuracion.controles_configuracion import CampoNumeroConfiguracion


def _app():
    return QApplication.instance() or QApplication([])


class _EventoRuedaFalso:
    def __init__(self):
        self.ignorado = False

    def ignore(self):
        self.ignorado = True


def prueba_selector_lista_todos_los_tamanos_de_uno_en_uno():
    _app()
    campo = CampoNumeroConfiguracion()
    campo.setRange(8, 14)

    valores = [
        campo.popup.lista.item(indice).data(256)
        for indice in range(campo.popup.lista.count())
    ]

    assert valores == [8, 9, 10, 11, 12, 13, 14]


def prueba_selector_permite_escribir_un_tamano_concreto():
    _app()
    campo = CampoNumeroConfiguracion()
    campo.setRange(8, 20)
    campo.setSuffix(" pt")
    campo.setValue(10)

    campo.lineEdit().setText("13 pt")
    campo.interpretText()

    assert campo.value() == 13


def prueba_selector_avanza_y_retrocede_de_un_punto():
    _app()
    campo = CampoNumeroConfiguracion()
    campo.setRange(8, 20)
    campo.setValue(10)

    campo.stepBy(1)
    assert campo.value() == 11

    campo.stepBy(-1)
    assert campo.value() == 10


def prueba_rueda_no_modifica_el_tamano():
    _app()
    campo = CampoNumeroConfiguracion()
    campo.setRange(8, 20)
    campo.setValue(10)

    evento = _EventoRuedaFalso()
    campo.wheelEvent(evento)

    assert evento.ignorado
    assert campo.value() == 10


def prueba_seleccion_desplegable_actualiza_el_valor():
    _app()
    campo = CampoNumeroConfiguracion()
    campo.setRange(8, 20)
    campo.setValue(10)

    campo._seleccionar_valor_popup(17)

    assert campo.value() == 17
