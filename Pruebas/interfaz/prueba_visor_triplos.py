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

from PySide6.QtCore import QPoint  # Permite inspeccionar si las esquinas de la tabla realmente están recortadas.
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QTabWidget  # Proporciona el entorno mínimo de la interfaz.

from Interfaz.resultados.panel_resultados import PanelResultados  # Comprueba la integración real con las fases posteriores.
from Interfaz.resultados.visor_triplos import SelectorInstruccionTriplos, VisorTriplos, comprobacion_html  # Comprueba el visor y el formato matemático.
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
    assert visor.tabla.rowCount() == 16  # Muestra quince operaciones y un encabezado de la red.
    assert visor.tabla.item(1, 0).text() == "(0)"  # Conserva el índice real tras el encabezado.
    assert visor.tabla.item(2, 1).text() == "(+, 50, 2)"  # Mantiene el orden de mayor a menor de VLSM.
    assert "(1) = 52" in visor.tabla.item(2, 2).text()  # Muestra el resultado asociado a la referencia.
    assert "HOSTS posición 2" in visor.tabla.item(2, 2).toolTip()  # Conserva la posición original del host reordenado.
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
    assert visor.tabla.item(2, 2).toolTip() == "Line 1 · Block 1 · HOSTS position 2"  # Traduce la procedencia original.
    assert visor.contador.text() == "Triples: 15"  # Traduce el contador sin cambiar su valor.
    assert visor.boton_copiar.text() == ""  # Conserva el botón compacto aunque cambie el idioma.
    assert visor.boton_copiar.toolTip() == "Copy table"  # Mantiene disponible la descripción localizada.
    assert visor.tabla.rowCount() == 16  # Conserva quince resultados y su separador de red.
    assert visor.tabla.item(2, 2).text().endswith("(1) = 52")  # No altera las comprobaciones ni las referencias.


def prueba_panel_actualiza_visor_al_compilar():
    app = _app()  # Inicializa Qt antes de crear el panel real.
    editor = QPlainTextEdit()  # Prepara una entrada mínima.
    diagnosticos = QTabWidget()  # Prepara el panel de diagnósticos usado por el coordinador gráfico.
    panel = PanelResultados(editor, diagnosticos, lambda: None, lambda: None)  # Construye la pestaña existente sin crear otra nueva.
    panel.mostrar_resultado(_resultado())  # Ejecuta la actualización real de todas las tablas.
    assert panel.visor_triplos.cantidad_visible == 15  # La fase posterior recibe los quince triplos reales.
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


def _codigo_dos_redes() -> str:
    return "IP 192.168.50.0 MASK /24 HOSTS 50 NAME Oficina\nIP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina2"  # Reproduce dos instrucciones independientes del mismo archivo fuente.


def prueba_selector_separa_instrucciones_sin_renumerar():
    app = _app()  # Prepara la sesión de Qt para mostrar dos redes en la misma compilación.
    codigo = _codigo_dos_redes()  # Conserva las dos líneas que se utilizarán como referencia visual.
    visor = VisorTriplos()  # Construye el visor real con sus controles de filtrado.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Presenta los 16 triplos generados para dos redes.
    assert visor.selector_instruccion.count() == 3  # Incluye vista general y una opción para cada instrucción.
    assert visor.tabla.rowCount() == 18  # Dos encabezados separan las dieciséis operaciones reales.
    assert "Oficina2" in visor.selector_instruccion.itemText(2)  # Utiliza NAME para identificar la segunda red.
    visor.selector_instruccion.setCurrentIndex(2)  # Filtra únicamente la segunda instrucción.
    assert visor.tabla.rowCount() == 8  # La red con una solicitud genera sus ocho operaciones.
    assert visor.tabla.item(0, 0).text() == "(8)"  # No reinicia la numeración cuando oculta la primera red.
    assert visor.tabla.item(7, 0).text() == "(15)"  # Mantiene la última referencia real de la secuencia completa.
    assert visor.campo_fuente.text() == codigo.splitlines()[1]  # Muestra exactamente la instrucción de la línea seleccionada.
    assert visor.contador.text() == "Triplos: 8 de 16"  # Diferencia operaciones visibles y totales.
    visor.selector_instruccion.setCurrentIndex(0)  # Recupera la vista de todas las instrucciones.
    assert visor.tabla.rowCount() == 18  # Restituye operaciones y separadores sin volver a compilar.


def prueba_selector_copia_solo_los_triplos_visibles():
    app = _app()  # Habilita el portapapeles de Qt para comprobar la copia filtrada.
    codigo = _codigo_dos_redes()  # Utiliza dos instrucciones con índices separados.
    visor = VisorTriplos()  # Prepara la tabla de código intermedio.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Genera los resultados originales.
    visor.selector_instruccion.setCurrentIndex(2)  # Muestra solamente la segunda línea.
    visor.copiar_tabla()  # Copia la tabla actual tal como está visible.
    copiado = QApplication.clipboard().text()  # Recupera el contenido del portapapeles.
    assert "(8)\t(INICIAR_RED, 10.10.0.0, /25)" in copiado  # Incluye la instrucción seleccionada.
    assert "(0)\t(INICIAR_RED" not in copiado  # No incluye la instrucción oculta por el filtro.
    assert len(copiado.splitlines()) == 9  # Cuenta encabezado y ocho triplos visibles.


def prueba_selector_muestra_origen_de_fila_sin_filtrar():
    app = _app()  # Inicializa Qt para comprobar la interacción con las filas.
    codigo = _codigo_dos_redes()  # Establece las dos expresiones de origen.
    visor = VisorTriplos()  # Crea la vista sin filtros aplicados.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Conserva todos los triplos en pantalla.
    visor.tabla.selectRow(11)  # Selecciona una operación de la segunda red, después de los dos encabezados.
    assert visor.selector_instruccion.currentIndex() == 0  # No cambia el filtro general al seleccionar una fila.
    assert visor.campo_fuente.text() == codigo.splitlines()[1]  # La expresión superior corresponde a la fila seleccionada.
    visor.limpiar()  # Simula una edición del código fuente.
    assert not visor.selector_instruccion.isEnabled()  # Impide consultar instrucciones obsoletas.
    assert visor.tabla.rowCount() == 0  # Descarta también todas las operaciones visibles.
    assert visor.campo_fuente.text() == ""  # Elimina la expresión anterior del encabezado.


def prueba_selector_traduce_sin_perder_la_seleccion():
    app = _app()  # Prepara el visor para comprobar cambios de idioma.
    codigo = _codigo_dos_redes()  # Genera datos de dos redes independientes.
    visor = VisorTriplos()  # Crea el mismo control utilizado por la aplicación.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Carga la secuencia original.
    visor.selector_instruccion.setCurrentIndex(2)  # Selecciona una instrucción antes de traducir la interfaz.
    visor.establecer_textos(
        encabezado="Verification", copiar="Copy table", vacio="Compile a valid instruction.",
        sin_bloques="No valid blocks.", no_disponible="Intermediate code unavailable.",
        contador="Triples: {cantidad}", origen="Line {linea} · Block {bloque}",
        host="HOSTS position {posicion}", todas="All instructions", linea="Line {linea}",
        fuente="Select an instruction to view its source code.", contador_filtrado="Triples: {visibles} of {total}",
    )  # Traduce los controles sin cambiar la secuencia de operaciones.
    assert visor.selector_instruccion.currentIndex() == 2  # Conserva la selección de la segunda instrucción.
    assert visor.selector_instruccion.itemText(0) == "All instructions"  # Traduce la vista general.
    assert visor.selector_instruccion.itemText(2).startswith("Line 2")  # Traduce también la línea original.
    assert visor.contador.text() == "Triples: 8 of 16"  # Traduce el contador parcial sin modificar su valor.
    assert visor.campo_fuente.text() == codigo.splitlines()[1]  # Conserva la expresión exacta en el campo superior.


def prueba_selector_se_invalida_al_editar_codigo():
    app = _app()  # Habilita el entorno gráfico de pruebas del panel completo.
    codigo = _codigo_dos_redes()  # Identifica dos redes antes de cambiar el editor.
    editor = QPlainTextEdit()  # Representa el mismo componente de entrada de TecNet Finder.
    editor.setPlainText(codigo)  # Proporciona el código que se va a compilar.
    panel = PanelResultados(editor, QTabWidget(), lambda: None, lambda: None)  # Integra resultados y código fuente del editor.
    panel.mostrar_resultado(FlujoCompilacion().analizar(codigo))  # Relaciona automáticamente los triplos con las líneas escritas.
    assert panel.visor_triplos.selector_instruccion.count() == 3  # El panel recibe ambas instrucciones.
    panel.visor_triplos.selector_instruccion.setCurrentIndex(2)  # Consulta la expresión de la segunda red.
    assert panel.visor_triplos.campo_fuente.text() == codigo.splitlines()[1]  # Confirma la conexión real con el editor.
    editor.setPlainText("IP 10.0.0.0 MASK /24 HOSTS 10")  # Modifica el código y anula sus resultados anteriores.
    assert panel.visor_triplos.tabla.rowCount() == 0  # Descarta los triplos que ya no corresponden al editor.
    assert not panel.visor_triplos.selector_instruccion.isEnabled()  # Inhabilita el filtro anterior.
    assert panel.visor_triplos.campo_fuente.text() == ""  # Borra la instrucción que dejó de estar vigente.


def prueba_selector_conserva_linea_real_tras_un_bloque_invalido():
    app = _app()  # Prepara una entrada con recuperación semántica.
    codigo = "IP 192.168.1.0 MASK /31 HOSTS 1\nIP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina2"  # Incluye una línea rechazada antes de una válida.
    visor = VisorTriplos()  # Construye el visor de la secuencia aceptada.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Genera triplos solamente para las redes válidas.
    assert visor.selector_instruccion.count() == 2  # Omite la instrucción rechazada sin inventar operaciones.
    assert visor.selector_instruccion.itemText(1).startswith("Línea 2")  # Conserva la línea física de la segunda instrucción.
    assert visor.tabla.item(1, 0).text() == "(0)"  # Usa el índice de la secuencia realmente generada.
    visor.selector_instruccion.setCurrentIndex(1)  # Muestra únicamente la instrucción semánticamente aceptada.
    assert visor.campo_fuente.text() == codigo.splitlines()[1]  # Obtiene la expresión de la línea correcta.


def prueba_vista_general_muestra_separadores_por_red():
    app = _app()  # Reutiliza Qt para comprobar la tabla de dos instrucciones.
    codigo = _codigo_dos_redes()  # Utiliza nombres, IP y líneas diferentes.
    visor = VisorTriplos()  # Crea el visor que se utiliza en la aplicación.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Genera dieciséis operaciones reales.
    assert visor.filas_grupo == {0, 9}  # Inserta un encabezado antes de cada secuencia de ocho triplos.
    assert visor.tabla.rowCount() == 18  # Cuenta las dos filas decorativas además de las operaciones.
    assert visor.cantidad_visible == 16  # El contador interno excluye los dos encabezados.
    assert visor.contador.text() == "Triplos: 16"  # El contador visible conserva el total real.
    assert visor.tabla.columnCount() == 3  # Los títulos ocupan las columnas existentes.
    assert visor.tabla.columnSpan(0, 0) == 3  # El encabezado de la primera red cubre las tres columnas.
    assert visor.tabla.columnSpan(9, 0) == 3  # El segundo encabezado comparte el mismo formato.
    assert "Red: Oficina" in visor.tabla.item(0, 0).text()  # Presenta el nombre de la primera red.
    assert "192.168.50.0" in visor.tabla.item(0, 0).text()  # Indica la IP base de la primera red.
    assert "Línea: 1" in visor.tabla.item(0, 0).text()  # Conserva la línea real de la primera instrucción.
    assert "Red: Oficina2" in visor.tabla.item(9, 0).text()  # Presenta el nombre de la segunda red.
    assert "Línea: 2" in visor.tabla.item(9, 0).text()  # Conserva la segunda ubicación.
    assert visor.tabla.item(1, 0).text() == "(0)"  # No renumera el primer triplo por el encabezado.
    assert visor.tabla.item(10, 0).text() == "(8)"  # No renumera la segunda red.


def prueba_separadores_desaparecen_al_filtrar_y_regresan_en_todas():
    app = _app()  # Proporciona el entorno para cambiar la selección de red.
    codigo = _codigo_dos_redes()  # Genera grupos diferentes dentro de la misma compilación.
    visor = VisorTriplos()  # Mantiene la tabla interactiva real.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Presenta ambas redes con títulos.
    visor.selector_instruccion.setCurrentIndex(2)  # Selecciona únicamente Oficina2.
    assert visor.filas_grupo == set()  # No repite el título de una red ya identificada por el selector.
    assert visor.tabla.rowCount() == 8  # Quedan únicamente sus ocho operaciones.
    assert visor.tabla.item(0, 0).text() == "(8)"  # Respeta los índices reales al filtrar.
    visor.selector_instruccion.setCurrentIndex(0)  # Recupera la vista general.
    assert visor.filas_grupo == {0, 9}  # Restituye los dos encabezados visuales.
    assert visor.tabla.item(10, 0).text() == "(8)"  # Conserva la referencia original del segundo bloque.


def prueba_copia_general_conserva_redes_y_triplos():
    app = _app()  # Permite consultar el contenido del portapapeles.
    codigo = _codigo_dos_redes()  # Prepara dos redes diferentes.
    visor = VisorTriplos()  # Utiliza el botón de copia del visor real.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Presenta títulos y operaciones.
    visor.copiar_tabla()  # Copia exactamente la vista general actual.
    lineas = QApplication.clipboard().text().splitlines()  # Separa los registros tabulados.
    assert len(lineas) == 19  # Un encabezado de columnas, dos redes y dieciséis triplos.
    assert "Red: Oficina" in lineas[1]  # Coloca la primera red antes de sus operaciones.
    assert lineas[2].startswith("(0)\t")  # Conserva los índices tras el separador.
    assert "Red: Oficina2" in lineas[10]  # Coloca la segunda red antes de su secuencia.
    assert lineas[11].startswith("(8)\t")  # Mantiene los datos de la segunda red.


def prueba_encabezados_cambian_de_idioma_sin_recalcular():
    app = _app()  # Permite probar el idioma sin reconstruir la ventana principal.
    codigo = _codigo_dos_redes()  # Conserva dos redes independientes.
    visor = VisorTriplos()  # Crea la vista con sus encabezados originales.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Genera las dieciséis operaciones.
    visor.establecer_textos(
        encabezado="Verification", copiar="Copy table", vacio="Compile a valid instruction.",
        sin_bloques="No valid blocks.", no_disponible="Intermediate code unavailable.",
        contador="Triples: {cantidad}", origen="Line {linea} · Block {bloque}",
        host="HOSTS position {posicion}", todas="All instructions", linea="Line {linea}",
        fuente="Select an instruction to view its source code.", contador_filtrado="Triples: {visibles} of {total}",
        grupo="Network: {nombre}    |    Base IP: {ip}    |    Line: {linea}",
    )  # Traduce el encabezado sin cambiar las comprobaciones matemáticas.
    assert "Network: Oficina" in visor.tabla.item(0, 0).text()  # Traduce el primer separador.
    assert "Base IP: 10.10.0.0" in visor.tabla.item(9, 0).text()  # Traduce los datos de la segunda red.
    assert visor.tabla.item(10, 0).text() == "(8)"  # No cambia los índices originales.
    assert visor.contador.text() == "Triples: 16"  # Traduce el conteo sin contabilizar títulos.


def prueba_marco_y_campos_redondeados_sin_afectar_tabla():
    app = _app()  # Inicializa Qt para consultar los estilos reales del visor.
    visor = VisorTriplos()  # Crea sus tres controles visuales y el marco exterior.
    assert visor.marco_tabla.objectName() == "MarcoTablaTriplos"  # Usa un contenedor independiente para redondear la tabla.
    assert "border-radius: 11px" in visor.marco_tabla.styleSheet()  # Comprueba la curvatura del marco.
    assert visor.marco_selector.objectName() == "MarcoSelectorTriplos"  # Conserva el borde exterior como en MantenimientoMarcoNivel.
    assert "border-radius: 8px" in visor.marco_selector.styleSheet()  # Comprueba el mismo radio que el filtro de registros.
    assert "background: transparent" in visor.marco_selector.styleSheet()  # Evita que el desplegable tape el marco.
    assert "border-radius: 9px" in visor.campo_fuente.styleSheet()  # Comprueba el campo de texto.
    assert visor.tabla.columnCount() == 3  # El redondeado no modifica la estructura del triplo.


def prueba_linea_invalida_no_agrega_encabezado_falso():
    app = _app()  # Inicializa Qt para probar recuperación semántica.
    codigo = "IP 192.168.1.0 MASK /31 HOSTS 1\nIP 10.10.0.0 MASK /25 HOSTS 100 NAME Oficina2"  # Una instrucción inválida y otra aceptada.
    visor = VisorTriplos()  # Visualiza el resultado del compilador sin reinterpretarlo.
    visor.mostrar_resultado(FlujoCompilacion().analizar(codigo), codigo)  # Produce operaciones solo para la línea válida.
    assert visor.filas_grupo == {0}  # Crea un separador solo para la red aceptada.
    assert "Oficina2" in visor.tabla.item(0, 0).text()  # Identifica la línea verdadera.
    assert "Línea: 2" in visor.tabla.item(0, 0).text()  # No reinicia la línea física del código fuente.
    assert visor.tabla.item(1, 0).text() == "(0)"  # Mantiene el primer triplo efectivamente generado.
    assert visor.contador.text() == "Triplos: 8"  # Omite la instrucción inválida del contador.


def prueba_selector_utiliza_marco_exacto_de_mantenimiento():
    app = _app()  # Prepara Qt para inspeccionar el marco del filtro.
    visor = VisorTriplos()  # Recupera el selector real de triplos.
    assert visor.selector_instruccion.parent() is visor.marco_selector  # El combo debe ir dentro del marco, no superpuesto.
    margen = visor.marco_selector.layout().contentsMargins()  # Consulta la separación real del contenedor.
    assert (margen.left(), margen.top(), margen.right(), margen.bottom()) == (1, 1, 1, 1)  # Replica el margen del Centro de mantenimiento.
    estilo = visor.marco_selector.styleSheet()  # Comprueba las reglas aplicadas al conjunto.
    assert 'background-color: ' in estilo and 'border-radius: 8px' in estilo  # El marco pinta su propio fondo y borde curvo.
    assert 'QComboBox#SelectorInstruccionTriplo { background: transparent;' in estilo  # El combo no oculta las esquinas.
    assert 'border-top-right-radius: 7px' in estilo  # La flecha conserva las esquinas del selector original.
    assert 'QAbstractItemView' in estilo  # El menú desplegable mantiene la selección y el contraste del tema.


def prueba_tabla_recorta_realmente_sus_cuatro_esquinas():
    app = _app()  # Prepara el widget real de tres columnas.
    visor = VisorTriplos()  # Construye una tabla dentro del marco redondeado.
    visor.resize(900, 600)  # Proporciona una geometría estable para la tabla interior.
    visor.show()  # Fuerza que Qt procese su primera apertura y el redondeado de encabezados.
    app.processEvents()  # Espera a que los tamaños reales del layout queden disponibles.
    region = visor.tabla.mask()  # Obtiene la región de recorte del widget completo.
    ancho = visor.tabla.width()  # Recupera las dimensiones reales, sin asumir píxeles fijos.
    alto = visor.tabla.height()  # Permite probar también plataformas con distinto escalado.
    assert not region.isEmpty()  # Una simple regla CSS no bastaría para pasar esta prueba.
    assert not region.contains(QPoint(0, 0))  # El encabezado no debe pintar la esquina superior izquierda.
    assert not region.contains(QPoint(ancho - 1, 0))  # El desplazamiento no debe pintar la esquina superior derecha.
    assert not region.contains(QPoint(0, alto - 1))  # Las celdas no deben pintar la esquina inferior izquierda.
    assert not region.contains(QPoint(ancho - 1, alto - 1))  # La barra de desplazamiento no debe pintar la esquina inferior derecha.
    assert region.contains(QPoint(ancho // 2, alto // 2))  # El centro permanece visible y operativo.
    visor.resize(750, 520)  # Comprueba que el recorte se adapte al tamaño del panel.
    app.processEvents()  # Deja que Qt recalcule el viewport y la máscara.
    assert visor.tabla.mask().contains(QPoint(visor.tabla.width() // 2, visor.tabla.height() // 2))  # La tabla conserva contenido al redimensionarse.
    visor.close()  # Evita dejar visible el widget de prueba al finalizar.


def prueba_selector_presenta_flecha_visible_y_vista_propia():
    app = _app()  # Inicializa Qt para revisar los controles dibujados en el visor.
    visor = VisorTriplos()  # Crea el selector y el marco sin depender del panel principal.
    assert isinstance(visor.selector_instruccion, SelectorInstruccionTriplos)  # El control dibuja su propia flecha en todos los temas.
    assert visor.selector_instruccion.view() is visor.selector_instruccion.vista_opciones  # La lista emergente es configurable directamente.
    assert visor.selector_instruccion.vista_opciones.objectName() == "OpcionesInstruccionTriplo"  # Evita que el diseño afecte otros combos.
    assert visor.selector_instruccion.color_flecha.isValid()  # El icono posee un color obtenido de la paleta vigente.
    assert "padding: 7px 30px 7px 9px" in visor.marco_selector.styleSheet()  # El texto no debe superponerse con la flecha.


def prueba_menu_de_triplos_reproduce_resaltado_redondeado():
    app = _app()  # Prepara la paleta real del tema seleccionado.
    visor = VisorTriplos()  # Recupera el desplegable sin abrir ventanas adicionales.
    estilo = visor.selector_instruccion.vista_opciones.styleSheet()  # Examina las reglas aplicadas a la lista real del menú.
    assert "QListView#OpcionesInstruccionTriplo::item:selected" in estilo  # La opción activa tiene un estilo propio.
    assert "border-radius: 7px" in estilo  # Se redondean tanto el fondo como las filas seleccionadas.
    assert "padding: 7px" in estilo  # El menú separa sus opciones del borde como Mantenimiento.
    assert "selection-background-color:" in visor.marco_selector.styleSheet()  # Conserva un respaldo en el estilo de QComboBox.
    assert visor.selector_instruccion.vista_opciones.window().objectName() == "MarcoOpcionesTriplo"  # Se aplica el borde al popup real.


def prueba_menu_abre_debajo_del_selector():
    app = _app()  # Prepara el entorno gráfico para abrir el menú real.
    visor = VisorTriplos()  # Construye el selector integrado en su contenedor.
    visor.resize(850, 520)  # Deja espacio suficiente para el listado desplegable.
    visor.move(10, 10)  # Acerca la ventana al borde superior para facilitar la apertura hacia abajo.
    visor.show()  # Calcula la posición global del selector.
    visor.mostrar_resultado(FlujoCompilacion().analizar(_codigo_dos_redes()), _codigo_dos_redes())  # Presenta tres opciones disponibles.
    app.processEvents()  # Completa la colocación inicial de los controles.
    combo = visor.selector_instruccion  # Recupera el selector de redes.
    combo.showPopup()  # Abre el popup mediante el mismo método que usa el usuario.
    app.processEvents()  # Aplica su geometría antes de consultar la posición.
    ventana = combo.view().window()  # Recupera la ventana emergente efectiva.
    posicion_minima = combo.mapToGlobal(QPoint(0, combo.height())).y()  # Calcula el borde inferior del cuadro de selección.
    assert ventana.isVisible()  # Confirma que se abrió el desplegable.
    assert ventana.pos().y() >= posicion_minima  # Evita que el menú cubra el cuadro cuando hay espacio abajo.
    combo.hidePopup()  # Cierra las opciones para no afectar las pruebas siguientes.
    visor.close()  # Libera la ventana usada para verificar el posicionamiento.


def prueba_seleccion_y_hover_tienen_azules_distintos():
    app = _app()  # Inicializa el tema del selector.
    visor = VisorTriplos()  # Recupera la lista y su delegado visual.
    visor.mostrar_resultado(FlujoCompilacion().analizar(_codigo_dos_redes()), _codigo_dos_redes())  # Crea varias opciones para comparar.
    combo = visor.selector_instruccion  # Consulta la opción confirmada del menú.
    combo.setCurrentIndex(0)  # Mantiene seleccionada la vista con todas las instrucciones.
    combo.vista_opciones.fila_hover = 1  # Simula el cursor sobre otra opción sin hacer clic.
    delegado = combo.delegado_opciones  # Recupera los colores usados realmente por el dibujado.
    seleccionado, texto_seleccion = delegado.colores_fila(0)  # El azul fuerte corresponde a la opción activa.
    hover, texto_hover = delegado.colores_fila(1)  # El azul tenue corresponde a la opción apuntada.
    normal, _ = delegado.colores_fila(2)  # Una tercera opción debe mantener el fondo original.
    assert seleccionado.name() != hover.name()  # La selección no se confunde con el hover.
    assert hover.name() != normal.name()  # El desplazamiento del cursor sí produce un resaltado visible.
    assert texto_seleccion.isValid() and texto_hover.isValid()  # Ambos fondos tienen texto legible.
    assert combo.currentIndex() == 0  # El hover no modifica la red realmente seleccionada.
