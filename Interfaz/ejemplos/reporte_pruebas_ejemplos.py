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


from PySide6.QtCore import QSize  # Proporciona el tamaño utilizado para los iconos de los botones.
from PySide6.QtGui import QIcon  # Permite cargar los recursos PNG disponibles dentro del proyecto.
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout  # Proporciona los controles necesarios para construir la ventana.
from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona los recursos gráficos iniciales utilizados por la ventana de reporte.
from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona los recursos grÃ¡ficos iniciales utilizados por la ventana de reporte.

from Interfaz.apariencia.recursos_tema import ruta_icono_oscuro  # Proporciona los recursos iniciales utilizados por la ventana de reporte.
from Motor.pruebas_ejemplos import ResumenPruebasEjemplos, generar_reporte_pruebas  # Proporciona el resumen estructurado y su representación textual completa.


class VentanaReportePruebas(QDialog):  # Presenta visualmente el resultado de una ejecución automática de ejemplos.
    def __init__(self, resumen: ResumenPruebasEjemplos, padre=None):  # Recibe un resumen ya calculado para mantener separadas interfaz y lógica de pruebas.
        super().__init__(padre)  # Inicializa la ventana secundaria utilizando el selector de ejemplos como propietario.
        self.resumen = resumen  # Conserva el resultado estructurado por si posteriormente se requieren otras formas de presentación.
        self.reporte_texto = generar_reporte_pruebas(resumen)  # Genera una representación textual reutilizable para visor y portapapeles.

        self.setWindowTitle("Resultado de pruebas automáticas")  # Identifica claramente la finalidad de la ventana.
        self.resize(980, 650)  # Proporciona espacio suficiente para consultar varios resultados cómodamente.
        self.setMinimumSize(760, 480)  # Evita reducir la ventana hasta dimensiones donde el reporte resulte difícil de leer.

        ruta_icono = ruta_icono_oscuro("Pruebas.png")  # Obtiene el icono inicial de la ventana desde la categoría oscura.

        if ruta_icono.exists():  # Comprueba que el recurso exista antes de intentar utilizarlo.
            self.setWindowIcon(QIcon(str(ruta_icono)))  # Utiliza el icono de pruebas dentro de la barra de la ventana.

        diseno = QVBoxLayout(self)  # Organiza encabezado, resumen, reporte y acciones verticalmente.
        diseno.setContentsMargins(12, 12, 12, 12)  # Mantiene una separación uniforme respecto a todos los bordes.
        diseno.setSpacing(10)  # Conserva una distancia consistente entre las diferentes secciones.

        titulo = QLabel("Resultado de pruebas automáticas")  # Crea el encabezado principal de la ventana.
        titulo.setObjectName("TituloSeccion")  # Reutiliza el estilo azul utilizado por otras secciones de TecNet Finder.
        diseno.addWidget(titulo)  # Coloca el encabezado en la zona superior.

        resumen_texto = QLabel(
            f"Total: {resumen.total}   |   "
            f"Correctos: {resumen.correctos}   |   "
            f"Pendientes: {resumen.pendientes}   |   "
            f"Fallidos: {resumen.fallidos}"
        )  # Construye una síntesis rápida de la ejecución antes de mostrar el detalle completo.
        resumen_texto.setObjectName("SubtituloPrincipal")  # Utiliza el estilo secundario ya existente en la aplicación.
        diseno.addWidget(resumen_texto)  # Coloca las estadísticas inmediatamente debajo del título.

        alcance = QLabel(
            "La evaluación automática utiliza las fases disponibles actualmente. "
            "Una prueba marcada como inválida también se considera correcta cuando "
            "produce exactamente los diagnósticos declarados como esperados."
        )  # Explica que CORRECTO se refiere al resultado de la prueba y no necesariamente a una entrada válida.
        alcance.setObjectName("SubtituloPrincipal")  # Mantiene la misma apariencia utilizada por otras aclaraciones.
        alcance.setWordWrap(True)  # Permite adaptar el texto al ancho disponible.
        diseno.addWidget(alcance)  # Coloca la explicación antes del reporte detallado.

        self.texto_reporte = QPlainTextEdit()  # Crea un visor adecuado para contenido extenso con saltos y alineación.
        self.texto_reporte.setReadOnly(True)  # Impide modificar accidentalmente el resultado calculado.
        self.texto_reporte.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)  # Facilita leer explicaciones largas sin desplazamiento horizontal.
        self.texto_reporte.setPlainText(self.reporte_texto)  # Coloca exactamente el reporte generado por Motor.
        diseno.addWidget(self.texto_reporte, 1)  # Permite que el reporte utilice la mayor parte de la ventana.

        acciones = QHBoxLayout()  # Crea la barra inferior destinada a las acciones disponibles.
        acciones.setSpacing(10)  # Mantiene separación uniforme entre botones.
        acciones.addStretch()  # Empuja las acciones hacia el extremo derecho.

        boton_copiar = QPushButton("Copiar reporte")  # Crea la acción destinada a enviar todo el resultado al portapapeles.
        boton_copiar.setToolTip("Copiar todo el reporte de pruebas automáticas")  # Explica la función cuando el usuario mantiene el cursor encima.
        self._aplicar_icono(boton_copiar, "Copiar.png")  # Reutiliza el icono oficial de copia cuando se encuentra disponible.
        boton_copiar.clicked.connect(self._copiar_reporte)  # Conecta el botón con la operación real sobre el portapapeles.
        acciones.addWidget(boton_copiar)  # Coloca la acción de copia antes del botón de cierre.

        boton_cerrar = QPushButton("Cerrar")  # Crea la acción utilizada para regresar al selector.
        boton_cerrar.clicked.connect(self.accept)  # Cierra solamente esta ventana secundaria.
        acciones.addWidget(boton_cerrar)  # Coloca el cierre en el extremo derecho.

        diseno.addLayout(acciones)  # Incorpora finalmente la barra de acciones al diseño principal.

    def _aplicar_icono(self, boton: QPushButton, nombre_archivo: str) -> None:
        boton.setProperty("recurso_tema", nombre_archivo)  # Declara el nombre lógico para permitir que el gestor actualice posteriormente el icono según el tema.  # Coloca un icono PNG sin impedir el funcionamiento cuando el recurso falta.
        ruta = ruta_icono_oscuro(nombre_archivo)  # Recupera la variante inicial mediante el sistema centralizado de recursos.

        if not ruta.exists():  # Comprueba si el archivo realmente está disponible dentro del proyecto.
            return  # Conserva el botón completamente funcional aun cuando el icono no exista.

        boton.setIcon(QIcon(str(ruta)))  # Carga el recurso encontrado dentro del botón.
        boton.setIconSize(QSize(18, 18))  # Mantiene dimensiones coherentes con las demás acciones de TecNet Finder.

    def _copiar_reporte(self) -> None:  # Copia al portapapeles exactamente el reporte textual que se encuentra visible.
        QApplication.clipboard().setText(self.texto_reporte.toPlainText())  # Obtiene el contenido del visor como cadena en lugar de intentar copiar el propio widget.