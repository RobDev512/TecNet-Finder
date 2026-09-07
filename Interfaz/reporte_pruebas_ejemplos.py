# ============================================================
# Archivo: reporte_pruebas_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la ventana utilizada para presentar los
# resultados obtenidos por las pruebas automáticas de ejemplos.
#
# La ventana muestra un resumen general, conserva el reporte
# completo en texto y permite copiarlo al portapapeles sin
# modificar la entrada ni los resultados del editor principal.
# ============================================================

from pathlib import Path  # Importa Path para localizar los iconos gráficos utilizados por esta ventana.

from PySide6.QtCore import QSize  # Importa tamaños utilizados para los iconos de los botones.
from PySide6.QtGui import QIcon  # Importa la clase utilizada para mostrar los recursos PNG existentes.
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout  # Importa los componentes necesarios para construir el reporte.

from Motor.pruebas_ejemplos import ResumenPruebasEjemplos, generar_reporte_pruebas  # Importa el resumen estructurado y su representación textual.


class VentanaReportePruebas(QDialog):  # Muestra el resultado completo de una ejecución automática de ejemplos.
    def __init__(self, resumen: ResumenPruebasEjemplos, padre=None):  # Recibe el resumen ya calculado para mantener la interfaz separada de la lógica.
        super().__init__(padre)  # Inicializa la ventana secundaria utilizando el selector como propietario.
        self.resumen = resumen  # Conserva el resultado estructurado por si posteriormente se agregan más formas de presentación.
        self.reporte_texto = generar_reporte_pruebas(resumen)  # Genera una representación textual reutilizable y copiable.
        self.ruta_iconos = Path(__file__).resolve().parent.parent / "Recursos" / "Iconos"  # Localiza la carpeta oficial de recursos gráficos.

        self.setWindowTitle("Resultado de pruebas automáticas")  # Identifica claramente la finalidad de la ventana.
        self.resize(980, 650)  # Proporciona espacio suficiente para consultar múltiples casos.
        self.setMinimumSize(760, 480)  # Evita dimensiones donde el reporte resulte difícil de leer.

        ruta_icono = self.ruta_iconos / "Pruebas.png"  # Construye la ubicación del icono preparado para esta característica.

        if ruta_icono.exists():  # Comprueba que el recurso realmente se encuentre disponible.
            self.setWindowIcon(QIcon(str(ruta_icono)))  # Utiliza el mismo icono de pruebas dentro de la ventana.

        diseno = QVBoxLayout(self)  # Organiza título, resumen, reporte y acciones de forma vertical.
        diseno.setContentsMargins(12, 12, 12, 12)  # Mantiene una separación uniforme respecto a todos los bordes.
        diseno.setSpacing(10)  # Separa visualmente cada sección.

        titulo = QLabel("Resultado de pruebas automáticas")  # Crea el encabezado principal del reporte.
        titulo.setObjectName("TituloSeccion")  # Reutiliza el estilo azul utilizado por las demás secciones.
        diseno.addWidget(titulo)  # Coloca el encabezado en la parte superior.

        resumen_texto = QLabel(  # Construye una síntesis rápida antes de consultar el detalle completo.
            f"Total: {resumen.total}   |   "
            f"Correctos: {resumen.correctos}   |   "
            f"Pendientes: {resumen.pendientes}   |   "
            f"Fallidos: {resumen.fallidos}"
        )
        resumen_texto.setObjectName("SubtituloPrincipal")  # Utiliza el estilo secundario ya existente en la aplicación.
        diseno.addWidget(resumen_texto)  # Coloca las estadísticas inmediatamente debajo del título.

        alcance = QLabel(  # Explica la diferencia entre una prueba fallida y una expectativa todavía no implementada.
            "La evaluación automática utiliza únicamente las fases disponibles actualmente. "
            "Los códigos de fases futuras aparecen como pendientes y no provocan falsos fallos."
        )
        alcance.setObjectName("SubtituloPrincipal")  # Mantiene la misma apariencia utilizada por otras aclaraciones.
        alcance.setWordWrap(True)  # Permite adaptar el texto al ancho disponible de la ventana.
        diseno.addWidget(alcance)  # Coloca la explicación antes del reporte completo.

        self.texto_reporte = QPlainTextEdit()  # Crea un visor apropiado para conservar alineación, saltos de línea y detalles extensos.
        self.texto_reporte.setReadOnly(True)  # Impide modificar accidentalmente el resultado calculado.
        self.texto_reporte.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)  # Evita requerir desplazamiento horizontal para leer explicaciones largas.
        self.texto_reporte.setPlainText(self.reporte_texto)  # Coloca todo el reporte generado por Motor.
        diseno.addWidget(self.texto_reporte, 1)  # Permite que el reporte utilice la mayor parte de la ventana.

        acciones = QHBoxLayout()  # Crea la barra inferior utilizada por las acciones disponibles.
        acciones.setSpacing(10)  # Mantiene una separación uniforme entre botones.
        acciones.addStretch()  # Empuja las acciones hacia el extremo derecho.

        boton_copiar = QPushButton("Copiar reporte")  # Crea la acción utilizada para conservar el reporte en el portapapeles.
        boton_copiar.setToolTip("Copiar todo el reporte de pruebas automáticas")  # Explica la finalidad del botón.
        self._aplicar_icono(boton_copiar, "Copiar.png")  # Utiliza el recurso preparado anteriormente para copiar información.
        boton_copiar.clicked.connect(self._copiar_reporte)  # Conecta el botón con el portapapeles del sistema.
        acciones.addWidget(boton_copiar)  # Coloca la acción de copia antes del cierre.

        boton_cerrar = QPushButton("Cerrar")  # Crea la acción utilizada para regresar al selector de ejemplos.
        boton_cerrar.clicked.connect(self.accept)  # Cierra únicamente la ventana del reporte.
        acciones.addWidget(boton_cerrar)  # Coloca el cierre en el extremo derecho.

        diseno.addLayout(acciones)  # Agrega finalmente la barra de acciones.

    def _aplicar_icono(self, boton: QPushButton, nombre_archivo: str) -> None:  # Coloca un icono PNG cuando el recurso solicitado existe.
        ruta = self.ruta_iconos / nombre_archivo  # Construye la ruta completa dentro de Recursos/Iconos.

        if not ruta.exists():  # Comprueba que el archivo gráfico esté disponible.
            return  # Conserva el botón funcional aunque el recurso faltara accidentalmente.

        boton.setIcon(QIcon(str(ruta)))  # Carga el icono desde el archivo PNG.
        boton.setIconSize(QSize(18, 18))  # Mantiene una dimensión consistente con el resto de controles.

    def _copiar_reporte(self) -> None:  # Envía el reporte completo al portapapeles del sistema.
        QApplication.clipboard().setText(self.reporte_texto)  # Conserva exactamente el texto generado por Motor.