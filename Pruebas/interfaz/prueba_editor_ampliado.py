# ============================================================
# Archivo: prueba_editor_ampliado.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que el botón Ampliar funcione como control de
# enfoque para ampliar y restaurar el editor.
# ============================================================

import os  # Permite configurar Qt antes de importar widgets.
from types import SimpleNamespace  # Permite construir un controlador mínimo para comprobar los accesos rápidos sin iniciar toda Configuración.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Evita depender de una pantalla física durante pytest.

from PySide6.QtWidgets import QApplication  # Proporciona la aplicación necesaria para construir la ventana real.

from Interfaz.configuracion.control_configuracion import ControlConfiguracion  # Permite comprobar que Configuración utilice el nombre definitivo del botón Ampliar.
from Interfaz.ventanas.ventana_principal import VentanaPrincipal  # Permite comprobar la integración real del modo de editor ampliado.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la única instancia Qt permitida o crea una nueva.


def prueba_boton_ampliar_controla_el_modo_de_enfoque():
    _aplicacion()  # Garantiza que Qt exista.
    ventana = VentanaPrincipal()  # Construye la interfaz real.
    boton = ventana.editor_codigo.boton_ampliar  # Recupera el control flotante de ampliación.

    assert boton.toolTip() == "Ampliar editor"  # Comprueba que la función visible corresponda con el modo de enfoque.
    assert boton.property("recurso_tema") == "Pantalla_completa.png"  # Comprueba que utilice un recurso de expansión.


def prueba_editor_ampliado_oculta_resultados_y_navegacion():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la interfaz real.

    ventana._establecer_editor_ampliado(True)  # Activa directamente el modo de enfoque.

    assert ventana.editor_ampliado is True  # Conserva el estado interno.
    assert ventana.panel_resultados.tabBar().isHidden() is True  # Oculta explícitamente la navegación principal.
    assert ventana.panel_resultados.pestanas_salida.isHidden() is True  # Oculta explícitamente las salidas.
    assert ventana.etiqueta_estado.isHidden() is True  # Oculta explícitamente el estado general.
    assert ventana.editor_codigo.boton_ampliar.toolTip() == "Restaurar vista"  # El mismo botón debe ofrecer ahora la salida.


def prueba_restaurar_editor_recupera_interfaz():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la interfaz real.

    ventana._establecer_editor_ampliado(True)  # Entra al modo ampliado.
    ventana._establecer_editor_ampliado(False)  # Recupera la distribución normal.

    assert ventana.editor_ampliado is False  # Confirma la restauración.
    assert ventana.panel_resultados.tabBar().isHidden() is False  # Recupera las pestañas principales.
    assert ventana.panel_resultados.pestanas_salida.isHidden() is False  # Recupera las pestañas de salida.
    assert ventana.etiqueta_estado.isHidden() is False  # Recupera la barra informativa.
    assert ventana.editor_codigo.boton_ampliar.toolTip() == "Ampliar editor"  # El botón vuelve a representar expansión.



class _BotonFalso:
    def __init__(self):
        self.visible = None  # Conserva el último estado solicitado por Configuración.

    def setVisible(self, visible: bool) -> None:
        self.visible = bool(visible)  # Imita únicamente la operación utilizada por el controlador real.


class _EditorFalso:
    def __init__(self):
        self.boton_ampliar = _BotonFalso()  # Representa el acceso rápido definitivo del editor.
        self.boton_ejemplos = _BotonFalso()  # Representa el segundo acceso rápido existente.
        self.reposicionamientos = 0  # Cuenta cuántas veces Configuración solicita recolocar ambos controles.

    def _posicionar_botones_flotantes(self) -> None:
        self.reposicionamientos += 1  # Imita el reajuste utilizado cuando los botones vuelven a mostrarse.


def prueba_configuracion_controla_ampliar_y_ejemplos_con_nombres_definitivos():
    editor = _EditorFalso()  # Construye únicamente la parte del editor necesaria para este comportamiento.
    controlador = SimpleNamespace(ventana=SimpleNamespace(editor_codigo=editor))  # Evita inicializar servicios ajenos a esta prueba.

    ControlConfiguracion._aplicar_botones_rapidos_editor(controlador, False)  # Apaga ambos accesos rápidos mediante el método real.

    assert editor.boton_ampliar.visible is False  # Comprueba que Configuración conozca el nombre definitivo del control.
    assert editor.boton_ejemplos.visible is False  # Comprueba que Ejemplos conserve el mismo comportamiento.
    assert editor.reposicionamientos == 0  # No debe recolocar controles mientras permanecen ocultos.

    ControlConfiguracion._aplicar_botones_rapidos_editor(controlador, True)  # Vuelve a mostrar ambos accesos rápidos.

    assert editor.boton_ampliar.visible is True  # Comprueba que Ampliar vuelva a mostrarse.
    assert editor.boton_ejemplos.visible is True  # Comprueba que Ejemplos vuelva a mostrarse.
    assert editor.reposicionamientos == 1  # Confirma que el controlador recupere sus posiciones al reaparecer.
