# ============================================================
# Archivo: prueba_editor_ampliado.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que el antiguo botón Pegar funcione ahora como
# control de enfoque para ampliar y restaurar el editor.
# ============================================================

import os  # Permite configurar Qt antes de importar widgets.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Evita depender de una pantalla física durante pytest.

from PySide6.QtWidgets import QApplication  # Proporciona la aplicación necesaria para construir la ventana real.

from Interfaz.ventanas.ventana_principal import VentanaPrincipal  # Permite comprobar la integración real del modo de editor ampliado.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la única instancia Qt permitida o crea una nueva.


def prueba_boton_pegar_se_reutiliza_como_ampliar_editor():
    _aplicacion()  # Garantiza que Qt exista.
    ventana = VentanaPrincipal()  # Construye la interfaz real.
    boton = ventana.editor_codigo.boton_pegar  # Recupera el control flotante histórico.

    assert boton.toolTip() == "Ampliar editor"  # Comprueba que la función visible ya no sea Pegar.
    assert boton.property("recurso_tema") == "Pantalla_completa.png"  # Comprueba que utilice un recurso de expansión.


def prueba_editor_ampliado_oculta_resultados_y_navegacion():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la interfaz real.

    ventana._establecer_editor_ampliado(True)  # Activa directamente el modo de enfoque.

    assert ventana.editor_ampliado is True  # Conserva el estado interno.
    assert ventana.panel_resultados.tabBar().isHidden() is True  # Oculta explícitamente la navegación principal.
    assert ventana.panel_resultados.pestanas_salida.isHidden() is True  # Oculta explícitamente las salidas.
    assert ventana.etiqueta_estado.isHidden() is True  # Oculta explícitamente el estado general.
    assert ventana.editor_codigo.boton_pegar.toolTip() == "Restaurar vista"  # El mismo botón debe ofrecer ahora la salida.


def prueba_restaurar_editor_recupera_interfaz():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la interfaz real.

    ventana._establecer_editor_ampliado(True)  # Entra al modo ampliado.
    ventana._establecer_editor_ampliado(False)  # Recupera la distribución normal.

    assert ventana.editor_ampliado is False  # Confirma la restauración.
    assert ventana.panel_resultados.tabBar().isHidden() is False  # Recupera las pestañas principales.
    assert ventana.panel_resultados.pestanas_salida.isHidden() is False  # Recupera las pestañas de salida.
    assert ventana.etiqueta_estado.isHidden() is False  # Recupera la barra informativa.
    assert ventana.editor_codigo.boton_pegar.toolTip() == "Ampliar editor"  # El botón vuelve a representar expansión.
