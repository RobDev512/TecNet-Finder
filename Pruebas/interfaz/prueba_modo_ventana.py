# ============================================================
# Archivo: prueba_modo_ventana.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la integración básica del selector de ventana y
# las restricciones correspondientes con Modo ventana.
# ============================================================

import os  # Permite configurar Qt antes de importar sus componentes.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Evita depender de una pantalla física durante pytest.

from PySide6.QtCore import Qt  # Proporciona el atributo utilizado para comprobar transparencia real.
from PySide6.QtWidgets import QApplication  # Proporciona la instancia Qt necesaria para construir widgets.

from Interfaz.ventanas.barra_titulo import SelectorMediaPantalla  # Permite comprobar las nuevas opciones del selector.
from Interfaz.ventanas.ventana_principal import VentanaPrincipal  # Permite comprobar las restricciones reales de la ventana principal.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la única instancia Qt permitida o crea una nueva.


def prueba_selector_incluye_modo_ventana_y_maximizar():
    _aplicacion()  # Garantiza que Qt exista antes de construir el popup.
    selector = SelectorMediaPantalla()  # Construye la implementación real utilizada por la barra principal.

    assert selector.tarjeta_modo_ventana.etiqueta_titulo.text() == "Modo ventana"  # Comprueba la nueva acción solicitada.
    assert selector.tarjeta_maximizar.etiqueta_titulo.text() == "Maximizar"  # Comprueba la acción que recupera el estado maximizado.


def prueba_selector_emite_solicitud_de_modo_ventana():
    _aplicacion()  # Garantiza una instancia Qt válida.
    selector = SelectorMediaPantalla()  # Construye el selector real.
    emisiones = []  # Registra de manera sencilla cuántas solicitudes fueron emitidas.

    selector.modo_ventana_solicitado.connect(lambda: emisiones.append(True))  # Observa la señal sin modificar la ventana principal.
    selector._solicitar_modo_ventana()  # Ejecuta la misma ruta utilizada por el botón.

    assert emisiones == [True]  # Confirma que la solicitud se emita exactamente una vez.


def prueba_modo_ventana_utiliza_ancho_y_alto_fijos():
    _aplicacion()  # Garantiza que los widgets puedan construirse.
    ventana = VentanaPrincipal()  # Construye la implementación real de TecNet Finder.

    ventana.en_modo_ventana = True  # Simula el estado después de elegir Modo ventana.
    ventana.en_media_pantalla = False  # Garantiza que no exista una mitad activa.
    ventana.en_pantalla_completa = False  # Garantiza que fullscreen no altere las restricciones.
    ventana._actualizar_limites_ancho_pantalla()  # Aplica los límites correspondientes con el estado actual.

    assert ventana.minimumWidth() == ventana.maximumWidth()  # Comprueba que el ancho no pueda modificarse.
    assert ventana.minimumHeight() == ventana.maximumHeight()  # Comprueba que la altura tampoco pueda modificarse.


def prueba_modo_ventana_no_se_interpreta_como_media_pantalla():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la ventana real.

    ventana.en_modo_ventana = True  # Activa explícitamente la nueva modalidad.
    ventana.en_media_pantalla = False  # Parte sin ninguna mitad activa.
    ventana.en_pantalla_completa = False  # Evita que fullscreen interrumpa la sincronización.
    ventana._sincronizar_estado_media_pantalla()  # Ejecuta la misma sincronización utilizada después de mover o redimensionar.

    assert ventana.en_modo_ventana is True  # El modo fijo debe conservarse después de sincronizar.
    assert ventana.en_media_pantalla is False  # Su geometría nunca debe convertirse automáticamente en Snap.


def prueba_barra_permanece_arrastrable_solo_cuando_se_activa_modo_ventana():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la ventana principal.

    assert ventana.barra_titulo.permitir_arrastre is False  # El estado inicial no debe mover la ventana desde la barra personalizada.

    ventana.en_modo_ventana = True  # Representa el estado final de la modalidad fija.
    ventana.barra_titulo.permitir_arrastre = True  # Reproduce la habilitación realizada por activar_modo_ventana.

    assert ventana.barra_titulo.permitir_arrastre is True  # Confirma que la barra admite el desplazamiento requerido.


def prueba_selector_utiliza_panel_interno_redondeado_sobre_fondo_transparente():
    _aplicacion()  # Garantiza una instancia Qt válida.
    selector = SelectorMediaPantalla()  # Construye el popup real.
    assert selector.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) is True  # Comprueba que la superficie exterior pueda permanecer transparente.
    assert selector.panel_selector.objectName() == "PanelSelectorMediaPantalla"  # Comprueba que el fondo visible pertenezca a un panel interno independiente.
    assert selector.mask().isEmpty() is True  # Evita volver a utilizar una máscara poligonal que produzca esquinas visualmente cortadas.
    assert bool(selector.windowFlags() & Qt.WindowType.NoDropShadowWindowHint) is True  # Evita que Windows o Qt dibujen una sombra rectangular detrás del panel redondeado.


def prueba_preparacion_inicial_de_modo_ventana_habilita_arrastre_y_tamano_fijo():
    _aplicacion()  # Garantiza una instancia Qt válida.
    ventana = VentanaPrincipal()  # Construye la ventana principal.
    ventana.preparar_modo_ventana_inicial()  # Reproduce la ruta utilizada por principal.py al restaurar una sesión normal.

    assert ventana.en_modo_ventana is True  # El estado interno debe reconocer la modalidad desde el primer fotograma.
    assert ventana.en_media_pantalla is False  # Media pantalla continúa siendo temporal.
    assert ventana.barra_titulo.permitir_arrastre is True  # La barra debe permitir mover la ventana inmediatamente después de iniciar.
    assert ventana.minimumWidth() == ventana.maximumWidth()  # El ancho permanece fijo.
    assert ventana.minimumHeight() == ventana.maximumHeight()  # La altura permanece fija.
