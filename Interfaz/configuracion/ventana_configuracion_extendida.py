# ============================================================
# Archivo: ventana_configuracion_extendida.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Amplía Configuración con el bloqueo opcional de advertencias
# y una categoría independiente para administrar preferencias.
# Mantiene la confirmación de cambios generales de Configuración
# y separa de ella la restauración explícita de valores iniciales.
# ============================================================

from PySide6.QtCore import Signal  # Comunica al controlador cambios confirmados.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout  # Construye tarjetas y opciones adicionales.

from Interfaz.configuracion.panel_configuracion_resultados import BotonCasillaConfiguracion  # Utiliza la casilla original de Configuración.
from Interfaz.configuracion.ventana_configuracion import VentanaConfiguracion  # Conserva el funcionamiento de las categorías originales.
from Interfaz.ventanas.panel_restauracion_preferencias import PanelRestauracionPreferencias, TEXTOS  # Agrega herramientas de datos sin duplicar traducciones.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Conserva la categoría anterior durante la construcción de Configuración.
from Motor.configuracion.preferencias_modalidad_advertencias import PreferenciasModalidadAdvertencias  # Guarda el bloqueo de la ventana independiente.


class VentanaConfiguracionExtendida(VentanaConfiguracion):  # Complementa Configuración sin modificar las cuatro categorías originales.
    bloquear_interaccion_advertencias_cambiado = Signal(bool)  # Notifica la elección después de guardarla.
    CLAVE_SECCION_DATOS = "datos_preferencias"  # Identifica de forma estable la nueva categoría.

    def __init__(self, *argumentos, **palabras_clave):
        preferencias = palabras_clave.get("preferencias_aplicacion") or PreferenciasAplicacion()  # Recupera el gestor real que utilizará Configuración.
        self._seccion_antes_de_abrir = preferencias._leer_preferencias().get(preferencias.CLAVE_ULTIMA_SECCION_CONFIGURACION)  # Evita perder la sección adicional durante el inicio.
        super().__init__(*argumentos, **palabras_clave)  # Construye la ventana original y las opciones ya probadas.
        self.preferencias_modalidad_advertencias = PreferenciasModalidadAdvertencias()  # Recupera el estado real del bloqueo.
        self.bloquear_interaccion_temporal = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Evita guardar antes de Aplicar.
        self._agregar_preferencia_bloqueo_advertencias()  # Mantiene el control adicional en Resultados y navegación.

        self.panel_restauracion = PanelRestauracionPreferencias(self)  # Construye la nueva sección con la casilla oficial.
        self._agregar_seccion("configuracion.seccion.datos_preferencias", self.panel_restauracion, self.CLAVE_SECCION_DATOS)  # Usa la misma navegación que el resto.
        self._aplicar_idioma_visual(self.preferencias_aplicacion.idioma_interfaz())  # Traduce la sección desde su primera aparición.
        self._recuperar_seccion_datos()  # Respeta la preferencia de recordar categoría.
        self._actualizar_estado_botones()  # Recalcula los controles después de incorporar las opciones.

    # ========================================================
    # Categoría Datos y preferencias
    # ========================================================

    def _aplicar_idioma_visual(self, idioma: str) -> bool:
        aplicado = super()._aplicar_idioma_visual(idioma)  # Conserva el comportamiento habitual de idioma.
        if not aplicado: return False  # Evita una actualización parcial.
        panel = getattr(self, "panel_restauracion", None)  # La clase base llama este método antes de crear la sección nueva.
        if panel is not None:
            panel.aplicar_idioma(idioma)  # Retraduce los textos del propio panel.
            indice = self.claves_secciones.index(self.CLAVE_SECCION_DATOS)  # Busca la sección por identificador estable.
            etiqueta = TEXTOS.get(idioma, TEXTOS["es"])["seccion"]  # Traduce su nombre sin depender de claves inexistentes.
            self.lista_secciones.item(indice).setText(etiqueta)  # Evita mostrar la clave técnica en el menú.
            self.lista_secciones.item(indice).setToolTip(etiqueta)  # Mantiene la ayuda consistente.
        return True  # Informa que se completó la actualización.

    def _recuperar_seccion_datos(self) -> None:
        if not self.preferencias_aplicacion.recordar_seccion_configuracion(): return  # Respeta la opción de no recordar la categoría.
        if self._seccion_antes_de_abrir == self.CLAVE_SECCION_DATOS:
            self.lista_secciones.setCurrentRow(self.claves_secciones.index(self.CLAVE_SECCION_DATOS))  # Reabre la nueva sección cuando fue la última utilizada.

    def _cambiar_panel(self, indice: int) -> None:
        if not hasattr(self, "panel_restauracion") or not 0 <= indice < len(self.claves_secciones):
            super()._cambiar_panel(indice)  # Conserva el funcionamiento durante la construcción inicial.
            return
        if self.claves_secciones[indice] != self.CLAVE_SECCION_DATOS:
            super()._cambiar_panel(indice)  # Mantiene la persistencia convencional de las otras cuatro secciones.
            return
        self.paneles.setCurrentIndex(indice)  # Muestra la nueva categoría mediante la pila oficial.
        if self.preferencias_aplicacion.recordar_seccion_configuracion():
            self.preferencias_aplicacion._guardar_valor(self.preferencias_aplicacion.CLAVE_ULTIMA_SECCION_CONFIGURACION, self.CLAVE_SECCION_DATOS)  # Recuerda esta categoría sin alterar los demás ajustes.

    # ========================================================
    # Bloqueo opcional de la ventana de advertencias
    # ========================================================

    def _agregar_preferencia_bloqueo_advertencias(self) -> None:
        diseno_principal = self.panel_resultados.layout()  # Recupera el panel original de Resultados y navegación.
        if diseno_principal is None: return  # Evita actuar ante una estructura inesperada.

        tarjeta = QFrame()  # Construye una tarjeta independiente.
        tarjeta.setObjectName("TarjetaConfiguracion")  # Reutiliza la apariencia del resto de Configuración.
        diseno_tarjeta = QVBoxLayout(tarjeta)  # Agrupa título, explicación y control.
        diseno_tarjeta.setContentsMargins(22, 16, 22, 16)  # Mantiene los márgenes de las tarjetas existentes.
        diseno_tarjeta.setSpacing(9)  # Separa los elementos sin desperdiciar espacio.

        titulo = QLabel("Interacción con la ventana principal")  # Identifica la función adicional.
        titulo.setObjectName("SubtituloConfiguracion")  # Aplica la tipografía oficial.
        titulo.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación interior.
        diseno_tarjeta.addWidget(titulo)  # Coloca el encabezado.

        descripcion = QLabel("Decide si la ventana independiente de advertencias debe impedir temporalmente utilizar TecNet Finder. Si se desactiva, podrás consultar las advertencias y la ventana principal al mismo tiempo.")  # Explica la modalidad.
        descripcion.setObjectName("DescripcionConfiguracion")  # Utiliza el color secundario del tema.
        descripcion.setContentsMargins(4, 2, 4, 2)  # Separa el texto del borde.
        descripcion.setWordWrap(True)  # Evita recortes al cambiar el tamaño de la ventana.
        diseno_tarjeta.addWidget(descripcion)  # Añade la aclaración.

        fila = QHBoxLayout()  # Alinea casilla y etiqueta.
        fila.setContentsMargins(4, 2, 4, 2)  # Reutiliza el margen habitual.
        fila.setSpacing(9)  # Deja espacio entre ambos controles.
        self.casilla_bloquear_interaccion = BotonCasillaConfiguracion("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta", self.panel_resultados)  # Utiliza la casilla existente.
        self.etiqueta_bloquear_interaccion = QLabel("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta")  # Explica qué activa.
        self.etiqueta_bloquear_interaccion.setObjectName("TextoConfiguracion")  # Reutiliza la apariencia común.
        self.etiqueta_bloquear_interaccion.setContentsMargins(2, 0, 2, 0)  # Evita que se pegue a la casilla.
        self.casilla_bloquear_interaccion.setChecked(self.bloquear_interaccion_temporal)  # Refleja el estado persistente.
        self.casilla_bloquear_interaccion.toggled.connect(self._cambiar_bloqueo_temporal)  # Cambia únicamente el estado temporal.
        fila.addWidget(self.casilla_bloquear_interaccion)  # Sitúa primero el control.
        fila.addWidget(self.etiqueta_bloquear_interaccion)  # Coloca después su texto.
        fila.addStretch()  # Alinea los controles a la izquierda.
        diseno_tarjeta.addLayout(fila)  # Completa la tarjeta.

        diseno_principal.insertWidget(max(0, diseno_principal.count() - 1), tarjeta)  # Inserta la opción antes del espacio final.
        self.panel_resultados.casilla_advertencias_ventana.toggled.connect(self._actualizar_disponibilidad_bloqueo)  # Sincroniza la modalidad independiente.
        self._actualizar_disponibilidad_bloqueo()  # Ajusta inmediatamente la disponibilidad.

    def _cambiar_bloqueo_temporal(self, bloquear: bool) -> None:
        self.bloquear_interaccion_temporal = bool(bloquear)  # Mantiene la elección en memoria hasta Aplicar o Aceptar.
        self._actualizar_disponibilidad_bloqueo()  # Actualiza las opciones dependientes.
        self._actualizar_estado_botones()  # Activa Aplicar cuando existe una modificación.

    def _actualizar_disponibilidad_bloqueo(self, *_argumentos) -> None:
        ventana_activa = self.panel_resultados.casilla_advertencias_ventana.isChecked()  # Comprueba si existe ventana independiente.
        bloqueo_activo = ventana_activa and self.casilla_bloquear_interaccion.isChecked()  # Consulta el estado de bloqueo.
        self.casilla_bloquear_interaccion.setEnabled(ventana_activa)  # Deshabilita una elección sin efecto.
        self.etiqueta_bloquear_interaccion.setEnabled(ventana_activa)  # Acompaña visualmente al control.
        self.panel_resultados.casilla_cerrar_ventana.setEnabled(ventana_activa and not bloqueo_activo)  # Impide opciones incompatibles.
        self.panel_resultados.etiqueta_cerrar_ventana.setEnabled(ventana_activa and not bloqueo_activo)  # Aplica la misma regla al texto.
        if bloqueo_activo:
            ayuda = "Con el bloqueo activo, la ventana debe cerrarse antes de poder navegar nuevamente por TecNet Finder."  # Explica la limitación.
            self.panel_resultados.casilla_cerrar_ventana.setToolTip(ayuda)  # Describe la razón del bloqueo.
            self.panel_resultados.etiqueta_cerrar_ventana.setToolTip(ayuda)  # Mantiene la descripción accesible.
        else:
            self.panel_resultados.casilla_cerrar_ventana.setToolTip("")  # Retira una ayuda que ya no corresponde.
            self.panel_resultados.etiqueta_cerrar_ventana.setToolTip("")  # Mantiene las dos zonas sincronizadas.

    # ========================================================
    # Aplicar / Aceptar / Cancelar
    # ========================================================

    def _obtener_cambios_generales(self) -> dict[str, list[str]]:
        cambios = super()._obtener_cambios_generales()  # Obtiene las diferencias de las cuatro categorías originales.
        if not hasattr(self, "preferencias_modalidad_advertencias"): return cambios  # Protege llamadas durante la creación de la ventana.
        valor_real = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Consulta la opción guardada.
        if self.bloquear_interaccion_temporal != valor_real:
            cambios.setdefault("Resultados y navegación", []).append("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta")  # Añade la nueva diferencia.
        return cambios  # Conserva el contrato original del resumen de cambios.

    def _aplicar_preferencias_generales(self) -> tuple[dict[str, list[str]], list[str]]:
        pendiente = self.bloquear_interaccion_temporal != self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Comprueba si se modificó el bloqueo.
        guardado = True  # Inicializa el estado cuando no hay nada nuevo que persistir.
        if pendiente:
            guardado = self.preferencias_modalidad_advertencias.establecer_bloquear_interaccion_fondo(self.bloquear_interaccion_temporal)  # Guarda la opción adicional.
        aplicados, errores = super()._aplicar_preferencias_generales()  # Aplica después la configuración convencional.
        if pendiente and guardado:
            aplicados.setdefault("Resultados y navegación", []).append("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta")  # Añade la preferencia al resumen.
            valor_confirmado = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Consulta el valor escrito.
            self.bloquear_interaccion_advertencias_cambiado.emit(valor_confirmado)  # Sincroniza la ventana de advertencias.
        if pendiente and not guardado:
            errores.append("No fue posible guardar el bloqueo de interacción de la ventana de advertencias.")  # Informa el fallo.
        return aplicados, errores  # Mantiene el contrato de la ventana original.

    def _cancelar_cambios(self) -> None:
        if hasattr(self, "preferencias_modalidad_advertencias"):
            self.bloquear_interaccion_temporal = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Descarta la elección temporal.
        super()._cancelar_cambios()  # Cierra sin guardar los cambios pendientes.
