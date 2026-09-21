# ============================================================
# Archivo: prueba_panel_resultados_analisis.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que la pestaña Análisis represente las tres fases
# implementadas actualmente: léxica, sintáctica y semántica.
# ============================================================

import os  # Permite utilizar Qt en modo sin pantalla durante pytest.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Evita depender de una interfaz gráfica física.

from PySide6.QtWidgets import QApplication, QPlainTextEdit, QTabWidget  # Proporciona los componentes mínimos para construir PanelResultados.

from Interfaz.resultados.panel_resultados import PanelResultados  # Permite comprobar la pestaña y el reporte técnico reales.
from Motor.compilacion.modelos import BloqueRed, ResultadoCompilacion, ResultadoLexico, ResultadoSemantico, ResultadoSintactico, Token  # Construye resultados controlados de las tres fases.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la única instancia Qt permitida o crea una nueva.


def _crear_panel() -> PanelResultados:
    _aplicacion()  # Garantiza que Qt exista antes de construir widgets.
    editor = QPlainTextEdit()  # Proporciona el editor mínimo requerido por PanelResultados.
    panel_diagnosticos = QTabWidget()  # Proporciona las operaciones de pestañas utilizadas por la vista principal.
    return PanelResultados(
        editor_codigo=editor,
        panel_diagnosticos=panel_diagnosticos,
        accion_analizar=lambda: None,
        accion_limpiar=lambda: None,
    )  # Construye la implementación real sin ejecutar acciones externas.


def _bloque(ip: str, nombre: str, linea: int) -> BloqueRed:
    return BloqueRed(
        direccion_ip=ip,
        mascara_subred="/24",
        cantidades_hosts=[50],
        nombre=nombre,
        linea_origen=linea,
    )  # Construye un bloque sencillo con identificación inequívoca.


def prueba_pestana_analisis_utiliza_nombre_general():
    panel = _crear_panel()  # Construye la interfaz real.
    indice = panel.pestanas_salida.indexOf(panel.tab_analisis)  # Localiza la subpestaña técnica.
    assert indice >= 0
    assert panel.pestanas_salida.tabText(indice) == "Análisis"  # Evita volver al nombre limitado a léxico y sintáctico.


def prueba_analisis_muestra_las_tres_fases_y_distingue_bloques_semanticos():
    panel = _crear_panel()  # Construye la salida textual real.
    bloque_valido = _bloque("192.168.1.0", "Valida", 1)
    bloque_semanticamente_invalido = _bloque("300.1.1.0", "Invalida", 2)

    resultado = ResultadoCompilacion(
        resultado_lexico=ResultadoLexico(
            tokens=[
                Token("IP", "IP", 1, 1),
                Token("IP_ADDRESS", "192.168.1.0", 1, 4),
            ]
        ),
        resultado_sintactico=ResultadoSintactico(
            bloques=[bloque_valido, bloque_semanticamente_invalido]
        ),
        resultado_semantico=ResultadoSemantico(
            bloques_validos=[bloque_valido]
        ),
    )  # Simula dos bloques sintácticos de los cuales solamente uno supera semántica.

    panel._mostrar_analisis(resultado)  # Genera el mismo reporte utilizado por la aplicación.
    texto = panel.texto_analisis.toPlainText()

    assert "=== ANÁLISIS LÉXICO ===" in texto
    assert "=== ANÁLISIS SINTÁCTICO ===" in texto
    assert "=== ANÁLISIS SEMÁNTICO ===" in texto
    assert "Estado: Semánticamente válido" in texto
    assert "Bloques sintácticamente válidos: 2" in texto
    assert "Bloques semánticamente válidos: 1" in texto

    seccion_semantica = texto.split("=== ANÁLISIS SEMÁNTICO ===", 1)[1].split("=== RESUMEN ===", 1)[0]
    assert "Valida" in seccion_semantica
    assert "Invalida" not in seccion_semantica  # Un bloque que falló semántica no debe presentarse como aceptado por esa fase.


def prueba_analisis_indica_cuando_semantica_no_fue_ejecutada():
    panel = _crear_panel()  # Construye la salida técnica.
    resultado = ResultadoCompilacion(
        resultado_lexico=ResultadoLexico(),
        resultado_sintactico=ResultadoSintactico(),
        resultado_semantico=None,
    )  # Conserva compatibilidad con un resultado antiguo o parcial sin fase semántica.

    panel._mostrar_analisis(resultado)
    texto = panel.texto_analisis.toPlainText()

    assert "=== ANÁLISIS SEMÁNTICO ===" in texto
    assert "El análisis semántico no fue ejecutado." in texto
    assert "Bloques semánticamente válidos: 0" in texto
