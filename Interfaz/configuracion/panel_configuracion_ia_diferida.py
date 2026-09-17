# ============================================================
# Archivo: panel_configuracion_ia_diferida.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo adapta PanelConfiguracionIA al sistema general
# Aplicar / Aceptar / Cancelar de la ventana de Configuración.
#
# El panel original continúa administrando instalación,
# desinstalación, Ollama, progreso y estados visuales.
#
# Esta variante modifica únicamente las preferencias de
# Autocompletado y Diagnósticos para que:
#
# - Pulsar una casilla solamente prepare un cambio.
# - Aplicar confirme y persista esos cambios.
# - Cancelar restaure los valores ya guardados.
#
# Instalar y Desinstalar continúan siendo operaciones inmediatas
# porque modifican físicamente el componente de IA.
# ============================================================

from PySide6.QtCore import Signal, Slot  # Proporciona la señal de cambios pendientes y conserva el slot utilizado al finalizar operaciones.

from Interfaz.configuracion.panel_configuracion_ia import PanelConfiguracionIA  # Reutiliza toda la implementación estable encargada del componente de inteligencia artificial.


class PanelConfiguracionIADiferida(PanelConfiguracionIA):  # Añade preferencias diferidas sin duplicar la administración completa del panel original.
    configuracion_modificada = Signal()  # Informa a Configuración que debe volver a evaluar si existen cambios pendientes.

    def _cambiar_funcion(self, funcion: str, activar: bool) -> None:  # Cambia solamente el valor temporal solicitado por el usuario.
        if funcion == "autocompletado":  # Comprueba si la modificación corresponde con las sugerencias de código.
            self.autocompletado_solicitado = bool(activar)  # Conserva temporalmente la decisión sin escribir todavía la preferencia.
        else:  # Atiende la segunda función configurable del asistente.
            self.diagnosticos_solicitados = bool(activar)  # Conserva temporalmente la decisión relacionada con soluciones mejoradas.

        self._actualizar_estado()  # Representa inmediatamente las selecciones pendientes dentro de las casillas y etiquetas.
        self.configuracion_modificada.emit()  # Solicita recalcular el estado del botón Aplicar sin confirmar todavía ningún cambio.

    def _alguna_funcion_solicitada(self) -> bool:  # Indica si las preferencias realmente aplicadas requieren mantener activo el servicio.
        return self.preferencias_ia.autocompletado_activado() or self.preferencias_ia.diagnosticos_ia_activados()  # Consulta únicamente valores persistidos y no selecciones todavía pendientes.

    def _emitir_funciones_efectivas(self) -> None:  # Comunica qué funciones pueden utilizar realmente la IA en este momento.
        instalado = self.componente_ia.instalado()  # Comprueba que runtime y modelo continúen físicamente disponibles.
        disponible = instalado and self.asistencia_disponible  # Exige simultáneamente instalación válida y servicio local disponible.
        autocompletado_aplicado = self.preferencias_ia.autocompletado_activado()  # Recupera la decisión persistida correspondiente con ghost text.
        diagnosticos_aplicados = self.preferencias_ia.diagnosticos_ia_activados()  # Recupera independientemente la decisión persistida para diagnósticos.
        self.autocompletado_cambiado.emit(disponible and autocompletado_aplicado)  # Habilita autocompletado únicamente cuando preferencia y servicio son efectivos.
        self.diagnosticos_ia_cambiados.emit(disponible and diagnosticos_aplicados)  # Hace la misma comprobación para las soluciones mejoradas.

    def obtener_cambios_pendientes(self) -> list[str]:  # Construye el resumen utilizado por la ventana general de Configuración.
        cambios = []  # Reunirá solamente preferencias cuyo valor temporal difiere del persistido.

        if self.autocompletado_solicitado != self.preferencias_ia.autocompletado_activado():  # Comprueba si la primera casilla fue modificada sin aplicar.
            cambios.append("Autocompletado con IA")  # Registra un nombre comprensible que podrá mostrarse en el resumen de cambios.

        if self.diagnosticos_solicitados != self.preferencias_ia.diagnosticos_ia_activados():  # Comprueba independientemente la segunda preferencia.
            cambios.append("Mejora de soluciones de diagnósticos con IA")  # Registra la modificación pendiente correspondiente con diagnósticos.

        return cambios  # Entrega exclusivamente los valores que todavía requieren Aplicar o Aceptar.

    def aplicar_cambios_pendientes(self) -> tuple[list[str], list[str]]:  # Persiste las selecciones temporales y sincroniza posteriormente Ollama.
        cambios_aplicados = []  # Conserva los nombres de preferencias que pudieron guardarse correctamente.
        errores = []  # Conserva explicaciones para cualquier preferencia que no pudo persistirse.
        autocompletado_anterior = self.preferencias_ia.autocompletado_activado()  # Recupera el valor real existente antes de comenzar la escritura.
        diagnosticos_anteriores = self.preferencias_ia.diagnosticos_ia_activados()  # Recupera independientemente la segunda preferencia persistida.

        if self.autocompletado_solicitado != autocompletado_anterior:  # Evita escribir el archivo cuando la primera preferencia realmente no cambió.
            guardado = self.preferencias_ia.establecer_autocompletado_activado(self.autocompletado_solicitado)  # Intenta persistir la nueva decisión del usuario.

            if guardado:  # Comprueba que la escritura haya terminado correctamente.
                cambios_aplicados.append("Autocompletado con IA")  # Registra la preferencia dentro del resumen de cambios exitosos.
            else:  # Atiende un posible problema de escritura en el almacenamiento persistente.
                errores.append("No fue posible guardar Autocompletado con IA.")  # Conserva un mensaje que podrá presentar Configuración.

        if self.diagnosticos_solicitados != diagnosticos_anteriores:  # Comprueba de forma independiente la segunda selección.
            guardado = self.preferencias_ia.establecer_diagnosticos_ia_activados(self.diagnosticos_solicitados)  # Intenta persistir la nueva decisión relacionada con diagnósticos.

            if guardado:  # Comprueba que la segunda preferencia haya podido escribirse.
                cambios_aplicados.append("Mejora de soluciones de diagnósticos con IA")  # Registra la modificación aplicada correctamente.
            else:  # Atiende un fallo de persistencia sin afectar la otra preferencia.
                errores.append("No fue posible guardar la mejora de soluciones de diagnósticos con IA.")  # Informa cuál opción no pudo conservarse.

        self._sincronizar_servicio_con_preferencias_aplicadas()  # Inicia o detiene Ollama según las preferencias que realmente quedaron persistidas.
        self._actualizar_estado()  # Actualiza visualmente las casillas después del intento de aplicación.
        self.configuracion_modificada.emit()  # Solicita recalcular si todavía quedó alguna diferencia pendiente.
        return cambios_aplicados, errores  # Permite a Configuración construir su resumen general de aplicación.

    def descartar_cambios_pendientes(self) -> None:  # Recupera las preferencias reales cuando el usuario pulsa Cancelar.
        self.autocompletado_solicitado = self.preferencias_ia.autocompletado_activado()  # Restaura la selección temporal del autocompletado.
        self.diagnosticos_solicitados = self.preferencias_ia.diagnosticos_ia_activados()  # Restaura también la selección temporal de diagnósticos.
        self._actualizar_estado()  # Retira visualmente cualquier cambio que nunca llegó a aplicarse.
        self.configuracion_modificada.emit()  # Informa que debe recalcularse el registro de modificaciones pendientes.

    def _sincronizar_servicio_con_preferencias_aplicadas(self) -> None:  # Ajusta el estado real de Ollama después de confirmar las preferencias.
        instalado = self.componente_ia.instalado()  # Comprueba primero si existe un componente físicamente utilizable.
        autocompletado_aplicado = self.preferencias_ia.autocompletado_activado()  # Recupera el valor definitivo de la primera función.
        diagnosticos_aplicados = self.preferencias_ia.diagnosticos_ia_activados()  # Recupera el valor definitivo de la segunda función.
        alguna_funcion_aplicada = autocompletado_aplicado or diagnosticos_aplicados  # Determina si alguna característica necesita mantener disponible el modelo local.

        if not instalado:  # Atiende el caso donde las preferencias existen pero el componente físico no está disponible.
            self.asistencia_disponible = False  # Mantiene el estado interno consistente con la ausencia del componente.
            self.servicio_cambiado.emit(False)  # Informa a otros componentes que no existe un servicio utilizable.
            self.autocompletado_cambiado.emit(False)  # Impide cualquier solicitud posterior de ghost text.
            self.diagnosticos_ia_cambiados.emit(False)  # Mantiene solamente las soluciones oficiales del compilador.
            self._actualizar_estado()  # Representa la indisponibilidad dentro de los controles del panel.
            return  # Finaliza porque ninguna preferencia puede activar IA sin una instalación existente.

        if alguna_funcion_aplicada:  # Comprueba si al menos una preferencia persistida necesita utilizar Ollama.
            if self.asistencia_disponible:  # Comprueba si el servicio requerido ya se encuentra ejecutándose.
                self._emitir_funciones_efectivas()  # Reutiliza la instancia activa y comunica qué consumidores deben quedar habilitados.
                self._actualizar_estado()  # Refleja que servicio y preferencias ya están sincronizados.
                return  # Evita iniciar una segunda operación innecesaria.

            self._iniciar_operacion("activar")  # Inicia Ollama únicamente después de aplicar una preferencia que realmente lo necesita.
            return  # Deja que el mecanismo asíncrono finalice posteriormente la actualización del panel.

        self.autocompletado_cambiado.emit(False)  # Deshabilita inmediatamente el consumidor de autocompletado cuando ninguna función quedó activa.
        self.diagnosticos_ia_cambiados.emit(False)  # Deshabilita también la capa opcional de explicaciones de diagnósticos.

        if self.asistencia_disponible:  # Comprueba si Ollama permanece activo aunque ninguna preferencia aplicada lo necesite.
            self._iniciar_operacion("desactivar")  # Solicita detener el servicio únicamente después de haber aplicado la desactivación.
            return  # Espera que la operación asíncrona actualice posteriormente el estado restante.

        self._actualizar_estado()  # Representa directamente el estado inactivo cuando el servicio ya se encontraba detenido.

    @Slot(str, bool, str)  # Declara la firma Qt utilizada para recibir la finalización de las operaciones asíncronas.
    def _finalizar_operacion(self, operacion: str, resultado: bool, mensaje: str) -> None:  # Extiende el cierre normal de operaciones realizado por PanelConfiguracionIA.
        super()._finalizar_operacion(operacion, resultado, mensaje)  # Conserva íntegramente instalación, desinstalación, activación y actualización visual del panel original.
        self.configuracion_modificada.emit()  # Recalcula Aplicar porque una operación inmediata puede haber modificado también preferencias relacionadas.