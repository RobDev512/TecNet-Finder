# ============================================================
# Archivo: boton_casilla_configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene la casilla personalizada utilizada
# dentro de la ventana general de Configuración.
#
# A diferencia de QCheckBox, este control utiliza un QPushButton
# seleccionable para representar claramente el estado mediante
# una marca de verificación.
#
# El mismo componente puede reutilizarse en cualquier categoría
# de Configuración para conservar una apariencia uniforme.
# ============================================================

from PySide6.QtCore import Qt  # Permite establecer el cursor utilizado por el control.
from PySide6.QtWidgets import QPushButton  # Proporciona el botón seleccionable utilizado como casilla.


class BotonCasillaConfiguracion(QPushButton):  # Representa una casilla reutilizable dentro de Configuración.
    def __init__(self, nombre_accesible: str, padre=None):  # Recibe la descripción accesible y un posible widget propietario.
        super().__init__(padre)  # Inicializa el comportamiento estándar proporcionado por QPushButton.
        self.setCheckable(True)  # Permite conservar internamente los estados activado y desactivado.
        self.setFixedSize(24, 24)  # Mantiene las dimensiones utilizadas por las casillas de Configuración.
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica visualmente que el control puede pulsarse.
        self.setAccessibleName(nombre_accesible)  # Conserva una descripción comprensible para herramientas de accesibilidad.
        self.setStyleSheet("padding: 0px; font-family: 'Segoe UI Symbol'; font-size: 12pt; font-weight: bold;")  # Mantiene centrada y claramente visible la marca.
        self.toggled.connect(self._actualizar_apariencia)  # Actualiza inmediatamente la representación cuando cambia el estado.
        self._actualizar_apariencia(False)  # Prepara inicialmente la apariencia correspondiente con una casilla vacía.

    def _actualizar_apariencia(self, activado: bool) -> None:  # Sincroniza texto y estilo con el estado lógico de la casilla.
        self.setText("✓" if activado else "")  # Muestra una marca solamente mientras la opción está seleccionada.
        self.setObjectName("BotonPrincipal" if activado else "CasillaIA")  # Utiliza el azul principal activa y el diseño oscuro desactivada.
        self.style().unpolish(self)  # Retira temporalmente la apariencia calculada para el estado anterior.
        self.style().polish(self)  # Aplica nuevamente la hoja de estilos utilizando el nuevo ObjectName.
        self.update()  # Solicita el redibujado inmediato del control.