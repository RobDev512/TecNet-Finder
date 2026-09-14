# ============================================================
# Archivo: panel_configuracion_ia_diferida.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo adapta PanelConfiguracionIA para utilizar el sistema
# Aplicar / Aceptar / Cancelar de la ventana de Configuración.
#
# La clase original continúa encargándose de:
#
# - La apariencia de Asistencia de IA.
# - Instalación y desinstalación del componente.
# - Barra de progreso.
# - Inicio y cierre de Ollama.
# - Actualización de los estados visuales.
#
# Esta variante cambia únicamente el comportamiento de las casillas
# de Autocompletado y Diagnósticos:
#
# - Pulsarlas solamente prepara cambios pendientes.
# - Aplicar confirma esos cambios y sincroniza Ollama.
# - Cancelar restaura las decisiones ya persistidas.
#
# Instalar y Desinstalar componente siguen siendo operaciones
# inmediatas porque modifican archivos físicos y no pueden tratarse
# como una preferencia reversible.
# ============================================================

from PySide6.QtCore import Signal, Slot  # Permite informar a Configuración sobre cambios pendientes y conservar el slot de finalización.

from Interfaz.panel_configuracion_ia import PanelConfiguracionIA  # Reutiliza íntegramente la implementación estable del panel de IA.


class PanelConfiguracionIADiferida(PanelConfiguracionIA):  # Añade confirmación diferida sin duplicar la administración completa del componente.
    configuracion_modificada = Signal()  # Informa que alguna preferencia pendiente cambió y debe reevaluarse el botón Aplicar.

    def _cambiar_funcion(
        self,
        funcion: str,
        activar: bool,
    ) -> None:
        if funcion == "autocompletado":
            self.autocompletado_solicitado = bool(
                activar
            )  # Conserva temporalmente la nueva decisión del ghost text.
        else:
            self.diagnosticos_solicitados = bool(
                activar
            )  # Conserva temporalmente la nueva decisión sobre soluciones con IA.

        self._actualizar_estado()  # Mantiene las casillas y etiquetas correctamente representadas.

        self.configuracion_modificada.emit()  # Solicita actualizar el registro de cambios sin aplicar todavía ninguna preferencia.

    def _alguna_funcion_solicitada(self) -> bool:
        return (
            self.preferencias_ia.autocompletado_activado()
            or self.preferencias_ia.diagnosticos_ia_activados()
        )  # Para el estado real de ejecución utiliza únicamente las preferencias ya confirmadas.

    def _emitir_funciones_efectivas(self) -> None:
        instalado = self.componente_ia.instalado()  # Comprueba que todavía exista una instalación completa.

        disponible = (
            instalado and self.asistencia_disponible
        )  # Exige archivos y servicio antes de habilitar consumidores.

        autocompletado_aplicado = (
            self.preferencias_ia.autocompletado_activado()
        )  # Recupera la decisión ya confirmada, no la selección pendiente.

        diagnosticos_aplicados = (
            self.preferencias_ia.diagnosticos_ia_activados()
        )  # Recupera independientemente la segunda preferencia aplicada.

        self.autocompletado_cambiado.emit(
            disponible and autocompletado_aplicado
        )  # Habilita ghost text únicamente cuando preferencia y servicio son efectivos.

        self.diagnosticos_ia_cambiados.emit(
            disponible and diagnosticos_aplicados
        )  # Hace lo mismo con la mejora de soluciones.

    def obtener_cambios_pendientes(self) -> list[str]:
        cambios = []  # Acumula únicamente preferencias cuyo valor pendiente difiere del persistido.

        if (
            self.autocompletado_solicitado
            != self.preferencias_ia.autocompletado_activado()
        ):
            cambios.append(
                "Autocompletado con IA"
            )  # Registra la primera función cuando todavía no ha sido confirmada.

        if (
            self.diagnosticos_solicitados
            != self.preferencias_ia.diagnosticos_ia_activados()
        ):
            cambios.append(
                "Mejora de soluciones de diagnósticos con IA"
            )  # Registra independientemente la segunda función.

        return cambios  # Entrega a VentanaConfiguracion el registro actual.

    def aplicar_cambios_pendientes(
        self,
    ) -> tuple[list[str], list[str]]:
        cambios_aplicados = []  # Conserva los nombres confirmados correctamente.
        errores = []  # Conserva cualquier preferencia que no pudo persistirse.

        autocompletado_anterior = (
            self.preferencias_ia.autocompletado_activado()
        )  # Recupera el estado real antes de escribir cambios.

        diagnosticos_anteriores = (
            self.preferencias_ia.diagnosticos_ia_activados()
        )  # Recupera de forma independiente la segunda preferencia real.

        if self.autocompletado_solicitado != autocompletado_anterior:
            guardado = (
                self.preferencias_ia.establecer_autocompletado_activado(
                    self.autocompletado_solicitado
                )
            )  # Persiste solamente la primera función cuando realmente cambió.

            if guardado:
                cambios_aplicados.append(
                    "Autocompletado con IA"
                )
            else:
                errores.append(
                    "No fue posible guardar Autocompletado con IA."
                )

        if self.diagnosticos_solicitados != diagnosticos_anteriores:
            guardado = (
                self.preferencias_ia.establecer_diagnosticos_ia_activados(
                    self.diagnosticos_solicitados
                )
            )  # Persiste únicamente la segunda función cuando su estado difiere.

            if guardado:
                cambios_aplicados.append(
                    "Mejora de soluciones de diagnósticos con IA"
                )
            else:
                errores.append(
                    "No fue posible guardar la mejora de soluciones de diagnósticos con IA."
                )

        self._sincronizar_servicio_con_preferencias_aplicadas()  # Ajusta el estado real de Ollama después de confirmar las preferencias.

        self._actualizar_estado()  # Representa inmediatamente los valores que permanecen pendientes o aplicados.

        self.configuracion_modificada.emit()  # Solicita recalcular Aplicar después del intento.

        return cambios_aplicados, errores  # Permite construir el resumen general de Configuración.

    def descartar_cambios_pendientes(self) -> None:
        self.autocompletado_solicitado = (
            self.preferencias_ia.autocompletado_activado()
        )  # Recupera la primera preferencia confirmada.

        self.diagnosticos_solicitados = (
            self.preferencias_ia.diagnosticos_ia_activados()
        )  # Recupera también la segunda preferencia persistida.

        self._actualizar_estado()  # Retira visualmente cualquier selección que no hubiera sido aplicada.

        self.configuracion_modificada.emit()  # Informa que el registro pendiente debe quedar vacío.

    def _sincronizar_servicio_con_preferencias_aplicadas(self) -> None:
        instalado = self.componente_ia.instalado()  # Comprueba primero si existe un runtime utilizable.

        autocompletado_aplicado = (
            self.preferencias_ia.autocompletado_activado()
        )  # Recupera el estado definitivo de la primera función.

        diagnosticos_aplicados = (
            self.preferencias_ia.diagnosticos_ia_activados()
        )  # Recupera el estado definitivo de la segunda función.

        alguna_funcion_aplicada = (
            autocompletado_aplicado
            or diagnosticos_aplicados
        )  # Decide si Ollama debe mantenerse disponible.

        if not instalado:
            self.asistencia_disponible = False  # Mantiene un estado realista cuando el componente no existe.

            self.servicio_cambiado.emit(
                False
            )  # Informa al controlador que no existe servicio utilizable.

            self.autocompletado_cambiado.emit(
                False
            )  # Impide cualquier solicitud de ghost text.

            self.diagnosticos_ia_cambiados.emit(
                False
            )  # Mantiene únicamente las soluciones oficiales.

            self._actualizar_estado()

            return

        if alguna_funcion_aplicada:
            if self.asistencia_disponible:
                self._emitir_funciones_efectivas()  # Aprovecha la instancia que ya se encuentra ejecutándose.

                self._actualizar_estado()

                return

            self._iniciar_operacion(
                "activar"
            )  # Inicia Ollama únicamente después de confirmar una función que lo necesita.

            return

        self.autocompletado_cambiado.emit(
            False
        )  # Detiene inmediatamente cualquier consumidor del ghost text.

        self.diagnosticos_ia_cambiados.emit(
            False
        )  # Restaura inmediatamente las soluciones oficiales.

        if self.asistencia_disponible:
            self._iniciar_operacion(
                "desactivar"
            )  # Cierra Ollama solamente después de confirmar que ninguna función lo utiliza.

            return

        self._actualizar_estado()  # Representa el estado inactivo cuando el servicio ya estaba detenido.

    @Slot(str, bool, str)
    def _finalizar_operacion(
        self,
        operacion: str,
        resultado: bool,
        mensaje: str,
    ) -> None:
        super()._finalizar_operacion(
            operacion,
            resultado,
            mensaje,
        )  # Conserva íntegramente instalación, desinstalación y administración del panel original.

        self.configuracion_modificada.emit()  # Actualiza Aplicar por si una acción inmediata modificó preferencias de IA.