# ============================================================
# Archivo: prueba_ventana_diagnosticos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la ampliación de la ventana independiente que antes
# mostraba únicamente advertencias.
#
# Las pruebas verifican:
# - Errores y advertencias se separan en pestañas.
# - Errores reciben prioridad visual.
# - La ventana independiente conserva ambos tipos de diagnóstico.
# - Una compilación parcial con VLSM mantiene Tabla VLSM visible
#   cuando la modalidad independiente está activa.
# ============================================================

import os  # Permite ejecutar Qt sin depender de una pantalla física durante la suite.
from types import SimpleNamespace  # Facilita construir dobles mínimos para navegación.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Activa el backend apropiado para pruebas automatizadas.

from PySide6.QtWidgets import QApplication  # Proporciona la aplicación mínima necesaria para construir la ventana.

from Interfaz.configuracion.control_configuracion import ControlConfiguracion  # Permite comprobar la navegación posterior a la compilación.
from Interfaz.ventanas.ventana_advertencias import VentanaAdvertencias  # Proporciona la ventana independiente ampliada.
from Motor.compilacion.diagnosticos import Diagnostico  # Permite construir errores y advertencias controlados.


def _aplicacion() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la única instancia Qt permitida o la crea cuando todavía no existe.


def _diagnostico_error() -> Diagnostico:
    return Diagnostico(
        codigo="SEM-007",
        categoria="Semántico",
        severidad="error",
        mensaje="La dirección IPv4 contiene un octeto fuera del rango permitido.",
        linea=2,
        columna=3,
        longitud=11,
        fragmento="300.1.1.0",
        solucion="Utiliza valores entre 0 y 255 en cada octeto.",
    )  # Representa un error semántico navegable.


def _diagnostico_advertencia() -> Diagnostico:
    return Diagnostico(
        codigo="ADV-009",
        categoria="Advertencia",
        severidad="advertencia",
        mensaje="La red coincide con un rango IPv4 de uso especial.",
        linea=1,
        columna=3,
        longitud=12,
        fragmento="169.254.10.0",
        solucion="Verifica que el rango especial corresponda con el propósito de la red.",
    )  # Representa una advertencia navegable.


class PestanasSalidaSimuladas:
    def __init__(self):
        self.actual = None  # Conserva qué subpestaña fue seleccionada por el controlador.

    def setCurrentWidget(self, widget) -> None:
        self.actual = widget  # Registra la selección sin necesitar una interfaz completa.


class PanelResultadosSimulado:
    def __init__(self):
        self.tab_entrada_salida = object()  # Representa la pestaña principal Entrada / Salida.
        self.tab_vlsm = object()  # Representa Tabla VLSM.
        self.tab_errores = object()  # Representa la vista interna de diagnósticos.
        self.pestanas_salida = PestanasSalidaSimuladas()  # Recibe la navegación inferior.
        self.actual = None  # Conserva qué pestaña principal fue seleccionada.

    def setCurrentWidget(self, widget) -> None:
        self.actual = widget  # Registra la navegación principal solicitada.


class PanelDiagnosticosSimulado:
    def __init__(self):
        self.indice = None  # Permite saber si ControlConfiguracion abrió Detectados.

    def setCurrentIndex(self, indice: int) -> None:
        self.indice = indice  # Conserva el índice solicitado.


def _control_navegacion(
    mostrar_ventana: bool,
) -> tuple[SimpleNamespace, PanelResultadosSimulado, PanelDiagnosticosSimulado]:
    control = SimpleNamespace()  # Construye únicamente los atributos consultados por la lógica de navegación.
    panel_resultados = PanelResultadosSimulado()  # Crea el doble mínimo requerido por el método.
    panel_diagnosticos = PanelDiagnosticosSimulado()  # Crea la vista interna simulada.

    control.ventana = SimpleNamespace(
        panel_resultados=panel_resultados,
        panel_diagnosticos=panel_diagnosticos,
    )  # Proporciona exactamente los componentes consultados por _navegar_segun_resultado.

    control.mostrar_advertencias_ventana = mostrar_ventana  # Activa o desactiva la modalidad independiente.
    control.navegar_a_vlsm = True  # Mantiene habilitada la navegación automática hacia subredes.
    control.navegar_a_errores = True  # Mantiene habilitada la navegación histórica hacia errores.

    return control, panel_resultados, panel_diagnosticos  # Devuelve todos los objetos necesarios para las aserciones.


def prueba_ventana_independiente_separa_errores_y_advertencias_y_prioriza_errores():
    aplicacion = _aplicacion()  # Mantiene viva la instancia Qt durante toda la prueba.

    ventana = VentanaAdvertencias(
        diagnosticos=[
            _diagnostico_advertencia(),
            _diagnostico_error(),
        ]
    )  # Entrega deliberadamente la advertencia antes del error para comprobar la prioridad interna.

    assert len(ventana.errores) == 1
    assert len(ventana.advertencias) == 1
    assert ventana.pestanas_diagnosticos.count() == 2
    assert ventana.pestanas_diagnosticos.tabText(0) == "Errores (1)"
    assert ventana.pestanas_diagnosticos.tabText(1) == "Advertencias (1)"
    assert ventana.pestanas_diagnosticos.currentIndex() == 0  # Errores debe abrirse primero cuando ambos tipos existen.

    ventana.close()  # Libera la ventana después de comprobar su estructura.
    assert aplicacion is QApplication.instance()  # Mantiene una referencia explícita hasta terminar la prueba.


def prueba_ventana_independiente_con_solo_advertencias_muestra_una_unica_pestana():
    aplicacion = _aplicacion()  # Garantiza el contexto gráfico requerido por QDialog.

    ventana = VentanaAdvertencias(
        diagnosticos=[_diagnostico_advertencia()]
    )  # Simula una compilación válida con un único aviso.

    assert len(ventana.errores) == 0
    assert len(ventana.advertencias) == 1
    assert ventana.pestanas_diagnosticos.count() == 1
    assert ventana.pestanas_diagnosticos.tabText(0) == "Advertencias (1)"

    ventana.close()  # Libera la ventana al finalizar.
    assert aplicacion is QApplication.instance()  # Conserva la instancia Qt durante toda la prueba.


def prueba_control_conserva_todos_los_diagnosticos_para_la_ventana_independiente():
    control, _panel_resultados, _panel_diagnosticos = _control_navegacion(
        mostrar_ventana=True
    )  # Activa la modalidad independiente.

    error = _diagnostico_error()
    advertencia = _diagnostico_advertencia()

    resultado = SimpleNamespace(
        diagnosticos=[error, advertencia]
    )  # Simula un resultado con ambas severidades.

    obtenidos = ControlConfiguracion._obtener_diagnosticos_reabribles(
        control,
        resultado,
    )  # Ejecuta la lógica real utilizando el doble mínimo.

    assert obtenidos == [
        error,
        advertencia,
    ]  # Ningún error debe hacer desaparecer las advertencias ni viceversa.


def prueba_resultado_parcial_con_ventana_independiente_prioriza_vlsm_en_la_ventana_principal():
    control, panel_resultados, panel_diagnosticos = _control_navegacion(
        mostrar_ventana=True
    )  # Activa la modalidad que presentará los errores por separado.

    resultado = SimpleNamespace(
        tiene_errores=True,
        subredes_vlsm=[object()],
    )  # Simula una compilación donde una instrucción produjo VLSM y otra produjo un error.

    ControlConfiguracion._navegar_segun_resultado(
        control,
        resultado,
    )  # Ejecuta la decisión real posterior a la compilación.

    assert panel_resultados.actual is panel_resultados.tab_entrada_salida
    assert panel_resultados.pestanas_salida.actual is panel_resultados.tab_vlsm  # La tabla parcial debe permanecer como salida principal.
    assert panel_diagnosticos.indice is None  # La vista interna no debe sustituir a la ventana independiente.


def prueba_resultado_con_error_sin_ventana_independiente_conserva_navegacion_historica():
    control, panel_resultados, panel_diagnosticos = _control_navegacion(
        mostrar_ventana=False
    )  # Desactiva la modalidad independiente.

    resultado = SimpleNamespace(
        tiene_errores=True,
        subredes_vlsm=[object()],
    )  # Mantiene la misma combinación de salida parcial y error.

    ControlConfiguracion._navegar_segun_resultado(
        control,
        resultado,
    )  # Ejecuta la ruta de respaldo mediante la implementación real.

    assert panel_resultados.actual is panel_resultados.tab_entrada_salida
    assert panel_resultados.pestanas_salida.actual is panel_resultados.tab_errores  # Sin ventana independiente, los errores continúan abriendo la vista interna.
    assert panel_diagnosticos.indice == 0  # Detectados continúa siendo la subpestaña prioritaria.