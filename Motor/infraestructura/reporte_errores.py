# ============================================================
# Archivo: reporte_errores.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Registra excepciones no controladas y ofrece un reporte local.
# No confunde diagnósticos normales del DSL con errores Python.
# Nunca envía informes automáticamente ni modifica preferencias.
# Los fallos de hilos secundarios se registran sin abrir Qt
# desde esos hilos, evitando operaciones gráficas inseguras.
# ============================================================

from __future__ import annotations  # Permite anotar los tipos sin forzar imports en tiempo de ejecución.

from datetime import datetime  # Agrega fecha y hora local a cada reporte.
import logging  # Registra también la excepción dentro de los logs rotativos.
from pathlib import Path  # Manipula las rutas de los reportes guardados.
import platform  # Identifica el entorno técnico para diagnosticar errores.
import sys  # Intercepta solamente excepciones no controladas de Python.
import threading  # Permite registrar errores de otros hilos sin mostrar ventanas allí.
import traceback  # Conserva la traza completa de una excepción.
from types import TracebackType  # Describe las trazas de Python.
from uuid import uuid4  # Produce identificadores distintos para cada incidencia.

from Motor.configuracion.version_aplicacion import NOMBRE_APLICACION, VERSION_VISIBLE  # Centraliza el nombre y la versión del producto.


# ============================================================
# Mensajes traducidos y advertencia de privacidad
# ============================================================

TEXTOS = {
    "es": ("Error inesperado", "TecNet Finder encontró un error inesperado. Se registró el incidente para facilitar su diagnóstico.", "Puedes copiar o guardar el reporte. Revísalo antes de compartirlo: podría contener rutas y datos personales.", "Copiar reporte", "Guardar reporte", "Cerrar", "Guardar informe de error", "Informes de texto (*.txt)", "No fue posible guardar el reporte:", "No fue posible copiar el reporte."),
    "en": ("Unexpected error", "TecNet Finder encountered an unexpected error. The incident was logged for troubleshooting.", "You can copy or save the report. Review it before sharing: it may contain file paths or personal data.", "Copy report", "Save report", "Close", "Save error report", "Text reports (*.txt)", "Could not save the report:", "Could not copy the report."),
    "pt": ("Erro inesperado", "O TecNet Finder encontrou um erro inesperado. O incidente foi registrado para diagnóstico.", "Você pode copiar ou salvar o relatório. Revise-o antes de compartilhar: ele pode conter caminhos ou dados pessoais.", "Copiar relatório", "Salvar relatório", "Fechar", "Salvar relatório de erro", "Relatórios de texto (*.txt)", "Não foi possível salvar o relatório:", "Não foi possível copiar o relatório."),
    "fr": ("Erreur inattendue", "TecNet Finder a rencontré une erreur inattendue. L'incident a été enregistré pour faciliter le diagnostic.", "Vous pouvez copier ou enregistrer le rapport. Vérifiez-le avant de le partager : il peut contenir des chemins ou des données personnelles.", "Copier le rapport", "Enregistrer le rapport", "Fermer", "Enregistrer le rapport d'erreur", "Rapports texte (*.txt)", "Impossible d'enregistrer le rapport :", "Impossible de copier le rapport."),
    "de": ("Unerwarteter Fehler", "In TecNet Finder ist ein unerwarteter Fehler aufgetreten. Das Ereignis wurde zur Diagnose protokolliert.", "Du kannst den Bericht kopieren oder speichern. Prüfe ihn vor dem Teilen: Er kann Pfade oder persönliche Daten enthalten.", "Bericht kopieren", "Bericht speichern", "Schließen", "Fehlerbericht speichern", "Textberichte (*.txt)", "Bericht konnte nicht gespeichert werden:", "Bericht konnte nicht kopiert werden."),
    "la": ("Error inopinatus", "In TecNet Finder error inopinatus accidit. Eventus ad causam explorandam notatus est.", "Relationem exscribere aut servare potes. Antequam mittas, inspice: vias tabularum et data privata continere potest.", "Relationem exscribe", "Relationem serva", "Claude", "Relationem erroris servare", "Relationes textuales (*.txt)", "Relatio servari non potuit:", "Relatio exscribi non potuit."),
}


# ============================================================
# Construcción y persistencia del reporte
# ============================================================

def crear_reporte(tipo: type[BaseException], error: BaseException, traza: TracebackType | None, *, origen: str) -> tuple[str, str]:  # Devuelve un identificador y un informe legible en UTF-8.
    fecha = datetime.now().astimezone()  # Conserva la zona horaria local para reconocer el evento.
    identificador = f"{fecha:%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"  # Evita sobreescribir reportes generados en el mismo segundo.
    detalles = "".join(traceback.format_exception(tipo, error, traza))  # Reúne el tipo, el mensaje y todas las líneas de la traza.
    reporte = (f"{NOMBRE_APLICACION} {VERSION_VISIBLE}\nID de incidente: {identificador}\nFecha: {fecha.isoformat(timespec='seconds')}\n"
               f"Origen: {origen}\nPython: {platform.python_version()}\nSistema: {platform.system()} {platform.release()}\n\n"
               f"Excepción: {tipo.__name__}\n\n--- TRAZA DE ERROR ---\n{detalles}")  # Incluye información técnica sin recoger archivos del usuario.
    return identificador, reporte  # El usuario decide si copia o guarda el texto posteriormente.


def guardar_reporte(ruta: str | Path, contenido: str) -> Path:  # Escribe solamente en la ubicación elegida por el usuario.
    destino = Path(ruta)  # Convierte la ubicación en una ruta segura de pathlib.
    destino.write_text(contenido, encoding="utf-8")  # Qt solicita permiso de sobrescritura antes de llegar aquí.
    return destino  # Permite confirmar dónde quedó el reporte guardado.


def _idioma_actual() -> str:  # Consulta el idioma real sin depender de ventanas activas.
    try:
        from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Evita cargar preferencias cuando no existe interfaz.
        idioma = PreferenciasAplicacion().idioma_interfaz()  # Recupera el idioma confirmado por el usuario.
        return idioma if idioma in TEXTOS else "es"  # Recurre a español ante un valor inesperado.
    except Exception:
        return "es"  # Un archivo de preferencias dañado no debe bloquear el reporte de error.


# ============================================================
# Ventana informativa (solo desde el hilo gráfico principal)
# ============================================================

def _mostrar_dialogo(identificador: str, reporte: str) -> bool:  # Ofrece copiar o guardar, sin transmisión automática.
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox  # Importa Qt solo si existe una aplicación gráfica.
    except ImportError:
        return False  # Permite registrar errores incluso en entornos sin PySide6.

    app = QApplication.instance()  # Evita construir controles antes de inicializar QApplication.
    if app is None or QApplication.closingDown(): return False  # No abre nuevas ventanas durante el cierre de Qt.
    texto = TEXTOS[_idioma_actual()]  # Selecciona exclusivamente los textos del idioma confirmado.
    cuadro = QMessageBox(app.activeWindow())  # Conserva la ventana principal como propietaria, cuando está disponible.
    cuadro.setIcon(QMessageBox.Icon.Critical)  # Identifica visualmente que se trata de una excepción inesperada.
    cuadro.setWindowTitle(f"{NOMBRE_APLICACION} — {texto[0]}")  # Presenta una identificación clara de la aplicación.
    cuadro.setText(texto[1])  # Explica el fallo sin mostrar de entrada una traza potencialmente sensible.
    cuadro.setInformativeText(f"{texto[2]}\n\nID: {identificador}")  # Indica la privacidad y permite localizar el incidente en el log.
    copiar = cuadro.addButton(texto[3], QMessageBox.ButtonRole.ActionRole)  # Copia el reporte completo al portapapeles.
    guardar = cuadro.addButton(texto[4], QMessageBox.ButtonRole.ActionRole)  # Guarda un archivo únicamente bajo solicitud.
    cerrar = cuadro.addButton(texto[5], QMessageBox.ButtonRole.RejectRole)  # Ofrece cerrar sin copiar ni guardar nada.
    cuadro.setDefaultButton(cerrar)  # Prioriza una salida segura sin acciones adicionales.
    cuadro.setEscapeButton(cerrar)  # Escape cierra igual que el botón explícito.
    cuadro.exec()  # Espera la selección del usuario sin iniciar un bucle global nuevo.

    if cuadro.clickedButton() is copiar:  # Distingue la opción elegida sin depender del texto de los botones.
        try: QApplication.clipboard().setText(reporte)  # Nunca envía información fuera de la aplicación.
        except Exception as fallo: QMessageBox.warning(app.activeWindow(), texto[0], f"{texto[9]}\n{fallo}")  # Explica un fallo del portapapeles.
    elif cuadro.clickedButton() is guardar:  # Solicita una ruta explícita, con el diálogo estándar del sistema.
        propuesta = f"TecNetFinder-error-{identificador}.txt"  # Sugiere un archivo distinguible de otros incidentes.
        ruta, _filtro = QFileDialog.getSaveFileName(app.activeWindow(), texto[6], propuesta, texto[7])  # Permite cancelar sin escribir nada.
        if ruta:
            try: guardar_reporte(ruta, reporte)  # Escribe únicamente después de confirmar la ubicación.
            except OSError as fallo: QMessageBox.warning(app.activeWindow(), texto[0], f"{texto[8]}\n{fallo}")  # No oculta errores de permisos.
    return True  # Confirma que se pudo presentar una interfaz al usuario.


# ============================================================
# Ganchos de excepciones no controladas
# ============================================================

class GestorReporteErrores:  # Coordina hooks instalados una sola vez durante la sesión.
    def __init__(self, logger: logging.Logger):
        self.logger = logger  # Reutiliza el mismo logger rotativo del programa.
        self.gancho_anterior = sys.excepthook  # Permite respetar el comportamiento original cuando haga falta.
        self.gancho_hilos_anterior = threading.excepthook  # Conserva el comportamiento original de los hilos.
        self.mostrando = False  # Evita cuadros de diálogo recursivos cuando ocurre otro error.

    def _registrar(self, tipo: type[BaseException], error: BaseException, traza: TracebackType | None, origen: str) -> tuple[str, str]:
        identificador, reporte = crear_reporte(tipo, error, traza, origen=origen)  # Construye un reporte independiente por evento.
        self.logger.error("Error inesperado [%s] (%s)", identificador, origen, exc_info=(tipo, error, traza))  # Conserva la traza dentro del log rotativo.
        return identificador, reporte  # Permite presentar el mismo incidente al usuario.

    def capturar_principal(self, tipo: type[BaseException], error: BaseException, traza: TracebackType | None) -> None:
        if issubclass(tipo, (KeyboardInterrupt, SystemExit)): self.gancho_anterior(tipo, error, traza); return  # No confunde interrupciones normales con errores.
        if self.mostrando: self.gancho_anterior(tipo, error, traza); return  # Evita ventanas en cascada durante otro reporte.
        self.mostrando = True  # Bloquea temporalmente una segunda captura anidada.
        try:
            identificador, reporte = self._registrar(tipo, error, traza, "Interfaz / proceso principal")  # Registra primero para no perder evidencia.
            mostrado = _mostrar_dialogo(identificador, reporte) if threading.current_thread() is threading.main_thread() else False  # Qt solo en el hilo de la interfaz.
            if not mostrado: self.gancho_anterior(tipo, error, traza)  # Conserva la salida en terminal si no se pudo mostrar el diálogo.
        except Exception:
            self.gancho_anterior(tipo, error, traza)  # No reemplaza el error original por un fallo secundario del reporte.
        finally:
            self.mostrando = False  # Libera la captura para futuros errores independientes.

    def capturar_hilo(self, argumentos) -> None:
        if issubclass(argumentos.exc_type, (KeyboardInterrupt, SystemExit)): self.gancho_hilos_anterior(argumentos); return  # Conserva excepciones de control.
        try: self._registrar(argumentos.exc_type, argumentos.exc_value, argumentos.exc_traceback, f"Hilo: {getattr(argumentos.thread, 'name', 'desconocido')}")  # Registra sin intentar abrir Qt desde otro hilo.
        except Exception: pass  # Preserva la salida original aun cuando falle el almacenamiento.
        self.gancho_hilos_anterior(argumentos)  # Mantiene también el traceback convencional de Python.


_GESTOR_ACTIVO: GestorReporteErrores | None = None  # Recuerda el capturador para evitar ganchos duplicados.


def instalar_reporte_errores(logger: logging.Logger) -> GestorReporteErrores:  # Activa una sola vez los ganchos para errores imprevistos.
    global _GESTOR_ACTIVO  # Comparte el capturador durante la ejecución.
    if _GESTOR_ACTIVO is not None:
        _GESTOR_ACTIVO.logger = logger  # Reutiliza el capturador tras una segunda inicialización sin anidar ganchos.
        return _GESTOR_ACTIVO  # Mantiene la identidad de los ganchos registrados.
    gestor = GestorReporteErrores(logger)  # Conserva los hooks anteriores antes de modificarlos.
    sys.excepthook = gestor.capturar_principal  # Intercepta excepciones Python no controladas del proceso principal.
    threading.excepthook = gestor.capturar_hilo  # Registra fallos de hilos secundarios sin manipular widgets.
    _GESTOR_ACTIVO = gestor  # Evita una instalación duplicada.
    return gestor  # Permite comprobar el capturador mediante pruebas aisladas.
