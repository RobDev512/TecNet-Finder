# ============================================================
# Archivo: ventana_configuracion_extendida.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Extiende la ventana general de Configuración con preferencias
# especializadas que no justifican aumentar todavía más la clase
# VentanaConfiguracion original.
#
# Actualmente añade:
# - Bloqueo opcional de la ventana principal mientras se muestran
#   advertencias en una ventana independiente.
#
# Conserva exactamente el sistema Aplicar / Aceptar / Cancelar
# utilizado por el resto de Configuración.
# ============================================================

from PySide6.QtCore import Signal  # Permite comunicar al controlador una preferencia ya confirmada.
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout  # Proporciona los controles utilizados por la nueva tarjeta.
from Interfaz.configuracion.panel_configuracion_resultados import BotonCasillaConfiguracion  # Reutiliza la misma casilla utilizada actualmente por Resultados y navegación.
from Interfaz.configuracion.ventana_configuracion import VentanaConfiguracion  # Extiende la ventana estable sin duplicar sus cientos de líneas.
from Motor.preferencias_modalidad_advertencias import PreferenciasModalidadAdvertencias  # Administra exclusivamente la nueva decisión persistente.


class VentanaConfiguracionExtendida(VentanaConfiguracion):  # Añade preferencias especializadas conservando íntegramente la ventana principal.
    bloquear_interaccion_advertencias_cambiado = Signal(bool)  # Comunica el valor solamente después de Aplicar o Aceptar.

    def __init__(self, *argumentos, **palabras_clave):
        super().__init__(*argumentos, **palabras_clave)  # Construye primero toda la Configuración convencional ya probada.
        self.preferencias_modalidad_advertencias = PreferenciasModalidadAdvertencias()  # Recupera la preferencia real independiente.
        self.bloquear_interaccion_temporal = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Crea la copia temporal utilizada durante esta sesión.
        self._agregar_preferencia_bloqueo_advertencias()  # Añade visualmente la nueva opción dentro de Resultados y navegación.
        self._actualizar_estado_botones()  # Recalcula Aplicar después de incorporar la nueva preferencia.

    # ========================================================
    # Construcción de la preferencia adicional
    # ========================================================

    def _agregar_preferencia_bloqueo_advertencias(self) -> None:
        diseno_principal = self.panel_resultados.layout()  # Recupera el layout existente sin modificar PanelConfiguracionResultados.
        if diseno_principal is None: return  # Evita continuar ante una estructura inesperada.

        tarjeta = QFrame()  # Crea una tarjeta independiente para mantener clara la diferencia entre navegación y modalidad.
        tarjeta.setObjectName("TarjetaConfiguracion")  # Reutiliza exactamente la apariencia general de las demás tarjetas.
        diseno_tarjeta = QVBoxLayout(tarjeta)  # Organiza título, explicación y casilla.
        diseno_tarjeta.setContentsMargins(22, 16, 22, 16)  # Mantiene el mismo padding utilizado en Resultados y navegación.
        diseno_tarjeta.setSpacing(9)  # Conserva la misma densidad visual de las otras tarjetas.

        titulo = QLabel("Interacción con la ventana principal")  # Identifica claramente qué controla esta preferencia.
        titulo.setObjectName("SubtituloConfiguracion")  # Reutiliza el estilo de subtítulos.
        titulo.setContentsMargins(4, 0, 4, 0)  # Mantiene la alineación interior.
        diseno_tarjeta.addWidget(titulo)  # Añade primero el encabezado.

        descripcion = QLabel("Decide si la ventana independiente de advertencias debe impedir temporalmente utilizar TecNet Finder. Si se desactiva, podrás consultar las advertencias y la ventana principal al mismo tiempo.")  # Explica la diferencia entre modalidad modal y no modal.
        descripcion.setObjectName("DescripcionConfiguracion")  # Reutiliza la apariencia secundaria.
        descripcion.setContentsMargins(4, 2, 4, 2)  # Mantiene una pequeña respiración lateral.
        descripcion.setWordWrap(True)  # Permite adaptar la explicación al ancho disponible.
        diseno_tarjeta.addWidget(descripcion)  # Coloca la explicación debajo del título.

        fila = QHBoxLayout()  # Organiza casilla y texto en una sola línea.
        fila.setContentsMargins(4, 2, 4, 2)  # Conserva la alineación de las otras opciones.
        fila.setSpacing(9)  # Mantiene una separación cómoda entre control y descripción.
        self.casilla_bloquear_interaccion = BotonCasillaConfiguracion("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta", self.panel_resultados)  # Reutiliza la casilla ya existente.
        self.etiqueta_bloquear_interaccion = QLabel("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta")  # Presenta la preferencia mediante un texto directo.
        self.etiqueta_bloquear_interaccion.setObjectName("TextoConfiguracion")  # Reutiliza la apariencia común de opciones.
        self.etiqueta_bloquear_interaccion.setContentsMargins(2, 0, 2, 0)  # Mantiene una separación mínima.
        self.casilla_bloquear_interaccion.setChecked(self.bloquear_interaccion_temporal)  # Representa la preferencia real al abrir Configuración.
        self.casilla_bloquear_interaccion.toggled.connect(self._cambiar_bloqueo_temporal)  # Modifica solamente la copia en memoria.
        fila.addWidget(self.casilla_bloquear_interaccion)  # Coloca primero la casilla.
        fila.addWidget(self.etiqueta_bloquear_interaccion)  # Coloca después su texto.
        fila.addStretch()  # Mantiene todo alineado hacia la izquierda.
        diseno_tarjeta.addLayout(fila)  # Incorpora finalmente la opción.

        indice_insercion = max(0, diseno_principal.count() - 1)  # Localiza la posición inmediatamente anterior al stretch final existente.
        diseno_principal.insertWidget(indice_insercion, tarjeta)  # Añade la nueva tarjeta sin alterar las tres originales.

        self.panel_resultados.casilla_advertencias_ventana.toggled.connect(self._actualizar_disponibilidad_bloqueo)  # Recalcula las opciones cuando se activa o desactiva la ventana independiente.
        self._actualizar_disponibilidad_bloqueo()  # Sincroniza inmediatamente el estado inicial.

    # ========================================================
    # Estado temporal
    # ========================================================

    def _cambiar_bloqueo_temporal(self, bloquear: bool) -> None:
        self.bloquear_interaccion_temporal = bool(bloquear)  # Conserva solamente la decisión temporal hasta Aplicar o Aceptar.
        self._actualizar_disponibilidad_bloqueo()  # Sincroniza la opción de cerrar al navegar.
        self._actualizar_estado_botones()  # Hace que Aplicar reconozca también esta nueva diferencia.

    def _actualizar_disponibilidad_bloqueo(self, *_argumentos) -> None:
        ventana_activa = self.panel_resultados.casilla_advertencias_ventana.isChecked()  # Comprueba si la modalidad independiente se encuentra seleccionada.
        bloqueo_activo = ventana_activa and self.casilla_bloquear_interaccion.isChecked()  # Determina si además se utilizará comportamiento modal.

        self.casilla_bloquear_interaccion.setEnabled(ventana_activa)  # Evita modificar una opción irrelevante cuando la ventana independiente está apagada.
        self.etiqueta_bloquear_interaccion.setEnabled(ventana_activa)  # Mantiene también su etiqueta visualmente sincronizada.

        self.panel_resultados.casilla_cerrar_ventana.setEnabled(ventana_activa and not bloqueo_activo)  # La opción de conservar abierta la ventana carece de sentido cuando la ventana es modal.
        self.panel_resultados.etiqueta_cerrar_ventana.setEnabled(ventana_activa and not bloqueo_activo)  # Expresa visualmente la misma dependencia.

        if bloqueo_activo:
            ayuda = "Con el bloqueo activo, la ventana debe cerrarse antes de poder navegar nuevamente por TecNet Finder."  # Explica por qué la opción anterior queda temporalmente deshabilitada.
            self.panel_resultados.casilla_cerrar_ventana.setToolTip(ayuda)  # Añade la explicación al control.
            self.panel_resultados.etiqueta_cerrar_ventana.setToolTip(ayuda)  # Añade la misma explicación al texto.
        else:
            self.panel_resultados.casilla_cerrar_ventana.setToolTip("")  # Retira la explicación cuando la opción vuelve a estar disponible.
            self.panel_resultados.etiqueta_cerrar_ventana.setToolTip("")  # Mantiene ambos componentes sincronizados.

    # ========================================================
    # Integración con Aplicar / Aceptar / Cancelar
    # ========================================================

    def _obtener_cambios_generales(self) -> dict[str, list[str]]:
        cambios = super()._obtener_cambios_generales()  # Recupera todas las diferencias administradas por la clase base.
        if not hasattr(self, "preferencias_modalidad_advertencias"): return cambios  # Protege la llamada realizada durante la construcción de la clase base.

        valor_real = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Recupera el valor confirmado actualmente.
        if self.bloquear_interaccion_temporal != valor_real: cambios.setdefault("Resultados y navegación", []).append("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta")  # Integra la nueva diferencia al mismo resumen.
        return cambios  # Devuelve una colección completamente compatible con la clase original.

    def _aplicar_preferencias_generales(self) -> tuple[dict[str, list[str]], list[str]]:
        pendiente = self.bloquear_interaccion_temporal != self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Comprueba la nueva diferencia antes de aplicar la clase base.
        guardado = True  # Considera correcto el estado mientras no exista nada nuevo que persistir.

        if pendiente: guardado = self.preferencias_modalidad_advertencias.establecer_bloquear_interaccion_fondo(self.bloquear_interaccion_temporal)  # Persiste primero la preferencia adicional para que la clase base ya no la considere pendiente.
        aplicados, errores = super()._aplicar_preferencias_generales()  # Deja que la ventana original confirme después todas sus preferencias habituales.

        if pendiente and guardado:
            aplicados.setdefault("Resultados y navegación", []).append("Bloquear TecNet Finder mientras la ventana de advertencias esté abierta")  # Añade la preferencia al resumen convencional de cambios aplicados.
            valor_confirmado = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Recupera el valor realmente escrito.
            self.bloquear_interaccion_advertencias_cambiado.emit(valor_confirmado)  # Comunica el nuevo comportamiento al controlador general.

        if pendiente and not guardado: errores.append("No fue posible guardar el bloqueo de interacción de la ventana de advertencias.")  # Informa un fallo de persistencia mediante el mismo mecanismo existente.
        return aplicados, errores  # Mantiene exactamente el contrato esperado por VentanaConfiguracion.

    def _cancelar_cambios(self) -> None:
        if hasattr(self, "preferencias_modalidad_advertencias"): self.bloquear_interaccion_temporal = self.preferencias_modalidad_advertencias.bloquear_interaccion_fondo()  # Descarta la copia adicional antes de cerrar.
        super()._cancelar_cambios()  # Deja que la clase base descarte después el resto de preferencias temporales.