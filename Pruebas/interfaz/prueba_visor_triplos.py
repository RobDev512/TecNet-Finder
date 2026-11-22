# ============================================================
# Archivo: prueba_visor_triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba la tabla de código intermedio, el formato
# matemático, el copiado y la actualización de resultados.
# ============================================================

import os  # Permite probar Qt sin mostrar ventanas físicas.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # Activa el controlador gráfico de pruebas.

from PySide6.QtWidgets import QApplication, QPlainTextEdit, QTabWidget  # Proporciona el entorno mínimo de la interfaz.

from Interfaz.resultados.panel_resultados import PanelResultados  # Comprueba la integración real con las fases posteriores.
from Interfaz.resultados.visor_triplos import VisorTriplos, comprobacion_html  # Comprueba el visor y el formato matemático.
from Motor.compilacion.flujo_compilacion import FlujoCompilacion  # Produce código intermedio a partir del DSL real.


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])  # Reutiliza la única aplicación Qt de la sesión.


def _resultado():
    return FlujoCompilacion().analizar("IP 192.168.1.0 MASK /24 HOSTS 10,50 NAME Oficina")  # Compila una red con solicitudes desordenadas.


def prueba_formato_matematico_seguro():
    html = comprobacion_html("log2((1)) -> log2(52) ≈ 5.7004 -> (2) ≈ 5.7004")  # Convierte el logaritmo en notación visual sin perder referencias.
    assert "log<sub>2</sub>((1))" in html  # Comprueba el subíndice sin depender de capturas.
    assert "→" in html  # Comprueba la flecha de sustitución.
    assert "⌈(2)⌉" in comprobacion_html("ceil((2)) -> ceil(5.7004) = 6")  # Comprueba el símbolo de redondeo.
    assert "<sup>6</sup>" in comprobacion_html("2 ^ (3) -> 2 ^ 6 = 64")  # Comprueba que el exponente tenga formato real.
    assert "&lt;script&gt;" in comprobacion_html("<script>")  # Evita interpretar HTML que venga de la entrada.


def prueba_visor_muestra_triplos_y_origen():
    app = _app()  # Crea Qt antes de cualquier widget.
    visor = VisorTriplos()  # Construye la vista de tres columnas.
    visor.mostrar_resultado(_resultado())  # Muestra los triplos generados por el flujo principal.
    assert visor.tabla.columnCount() == 3  # Conserva exactamente el formato acordado.
    assert visor.tabla.rowCount() == 15  # Presenta una operación por cada triplo real.
    assert visor.tabla.item(0, 0).text() == "(0)"  # Mantiene el índice original.
    assert visor.tabla.item(1, 1).text() == "(+, 50, 2)"  # Mantiene el orden de mayor a menor de VLSM.
    assert "(1) = 52" in visor.tabla.item(1, 2).text()  # Muestra el resultado asociado a la referencia.
    assert "HOSTS posición 2" in visor.tabla.item(1, 2).toolTip()  # Conserva la posición original del host reordenado.
    assert visor.boton_copiar.isEnabled()  # Activa la exportación textual cuando hay resultados.


def prueba_visor_copia_triplos_y_limpia():
    app = _app()  # Prepara el portapapeles de Qt.
    visor = VisorTriplos()  # Construye un visor independiente.
    visor.mostrar_resultado(_resultado())  # Llena las filas con resultados válidos.
    visor.copiar_tabla()  # Ejecuta la misma acción vinculada al botón de copiar.
    texto = QApplication.clipboard().text()  # Recupera el texto realmente copiado.
    assert "(0)\t(INICIAR_RED, 192.168.1.0, /24)" in texto  # Comprueba que la copia incluya la operación inicial.
    assert "(14)\t(SIGUIENTE_CURSOR, (13), —)" in texto  # Comprueba que la copia incluya la última operación.
    visor.limpiar()  # Invalida las operaciones después de cambiar la fuente.
    assert visor.tabla.rowCount() == 0  # Elimina los resultados anteriores.
    assert not visor.boton_copiar.isEnabled()  # Impide copiar resultados antiguos.


def prueba_visor_respeta_bloques_invalidos():
    app = _app()  # Garantiza que Qt esté disponible.
    visor = VisorTriplos()  # Prepara una instancia para resultados inválidos.
    resultado = FlujoCompilacion().analizar("IP 192.168.1.0 MASK /31 HOSTS 1")  # Genera un bloque semánticamente rechazado.
    visor.mostrar_resultado(resultado)  # No debe inventar operaciones para el bloque inválido.
    assert visor.tabla.rowCount() == 0  # Confirma que el visor permanezca vacío.
    assert "bloques" in visor.etiqueta_estado.text().lower()  # Explica por qué no se generan triplos.


def prueba_panel_conserva_pestana_y_limpieza():
    app = _app()  # Inicializa Qt antes de construir PanelResultados.
    editor = QPlainTextEdit()  # Simula la entrada de código utilizada en el panel real.
    diagnosticos = QTabWidget()  # Prepara un panel mínimo para construir los controles.
    panel = PanelResultados(editor, diagnosticos, lambda: None, lambda: None)  # Construye la interfaz con su árbol de pestañas original.
    fases = panel.tab_fases_posteriores.findChildren(QTabWidget)  # Identifica el contenedor de fases futuras.
    assert any(pestanas.indexOf(panel.visor_triplos) == 0 for pestanas in fases)  # Garantiza que utiliza la pestaña reservada.
    panel.visor_triplos.mostrar_resultado(_resultado())  # Comprueba que el visor se llene dentro del panel.
    panel._invalidar_resultado_exportable()  # Sin resultado_actual la invalidación debe conservar el visor.
    panel.resultado_actual = _resultado()  # Simula una compilación vigente antes de editar código.
    panel._invalidar_resultado_exportable()  # Invalida la compilación y el visor al cambiar la fuente.
    assert panel.visor_triplos.tabla.rowCount() == 0  # Impide presentar resultados que ya no corresponden al editor.


def prueba_visor_traduce_ayudas_sin_perder_los_triplos():
    app = _app()  # Reutiliza la sesión gráfica para comprobar el cambio de idioma.
    visor = VisorTriplos()  # Construye la misma vista que utiliza TecNet Finder.
    visor.mostrar_resultado(_resultado())  # Conserva las solicitudes VLSM reordenadas.
    visor.establecer_textos(
        encabezado="Verification", copiar="Copy table",
        vacio="Compile a valid instruction.", sin_bloques="No valid blocks.",
        no_disponible="Intermediate code unavailable.", contador="Triples: {cantidad}",
        origen="Line {linea} · Block {bloque}", host="HOSTS position {posicion}",
    )  # Actualiza los textos sin volver a compilar.
    assert visor.tabla.item(1, 2).toolTip() == "Line 1 · Block 1 · HOSTS position 2"  # Traduce la procedencia original.
    assert visor.contador.text() == "Triples: 15"  # Traduce el contador sin cambiar su valor.
    assert visor.boton_copiar.text() == ""  # Conserva el botón compacto aunque cambie el idioma.
    assert visor.boton_copiar.toolTip() == "Copy table"  # Mantiene disponible la descripción localizada.
    assert visor.tabla.rowCount() == 15  # Conserva todos los resultados ya calculados.
    assert visor.tabla.item(1, 2).text().endswith("(1) = 52")  # No altera las comprobaciones ni las referencias.


def prueba_panel_actualiza_visor_al_compilar():
    app = _app()  # Inicializa Qt antes de crear el panel real.
    editor = QPlainTextEdit()  # Prepara una entrada mínima.
    diagnosticos = QTabWidget()  # Prepara el panel de diagnósticos usado por el coordinador gráfico.
    panel = PanelResultados(editor, diagnosticos, lambda: None, lambda: None)  # Construye la pestaña existente sin crear otra nueva.
    panel.mostrar_resultado(_resultado())  # Ejecuta la actualización real de todas las tablas.
    assert panel.visor_triplos.tabla.rowCount() == 15  # La fase posterior recibe todos los triplos del compilador.
    editor.setPlainText("IP 10.0.0.0 MASK /24 HOSTS 20")  # Simula que el usuario modifica el código original.
    assert panel.visor_triplos.tabla.rowCount() == 0  # Elimina automáticamente los resultados obsoletos.
    assert not panel.visor_triplos.boton_copiar.isEnabled()  # No permite copiar una compilación desactualizada.


def prueba_visor_copia_con_icono_oficial():
    app = _app()  # Inicializa Qt para consultar el icono del botón de copiado.
    editor = QPlainTextEdit()  # Prepara un editor mínimo para el panel completo.
    diagnosticos = QTabWidget()  # Proporciona el contenedor de diagnósticos requerido.
    panel = PanelResultados(editor, diagnosticos, lambda: None, lambda: None)  # Construye el visor dentro de la interfaz.
    boton = panel.visor_triplos.boton_copiar  # Recupera el mismo botón visible en la pestaña de triplos.
    assert boton.text() == ""  # Impide regresar al botón ancho con texto.
    assert boton.width() == boton.height() == 32  # Conserva la forma cuadrada del control.
    assert boton.property("recurso_tema") == "Copiar.png"  # Permite que el tema seleccione su icono.
    assert not boton.icon().isNull()  # Confirma que se haya cargado el recurso real de copiado.
