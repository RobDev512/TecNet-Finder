# ============================================================
# Archivo: prueba_reporte_errores.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba reportes locales, ganchos de Python y privacidad.
# No abre interfaces ni modifica los registros del usuario.
# ============================================================

import logging  # Prepara registros aislados de prueba.
from pathlib import Path  # Permite comprobar la persistencia del informe.
import sys  # Comprueba la instalación de los ganchos del proceso.
import threading  # Comprueba la captura de excepciones de otros hilos.
from types import SimpleNamespace  # Simula los argumentos de threading.excepthook.

import pytest  # Permite validar excepciones y parametrizar pruebas.
from Motor.infraestructura import reporte_errores  # Reutiliza exclusivamente la lógica real de reporte.


def _excepcion_prueba():  # Construye un error real con traceback para las pruebas.
    try: raise ValueError("mensaje de prueba")  # Genera una traza identificable sin modificar el sistema.
    except ValueError as error: return type(error), error, error.__traceback__  # Conserva sus tres componentes.


def prueba_informe_con_id_y_traza():
    tipo, error, traza = _excepcion_prueba()  # Recupera una excepción conocida.
    identificador, texto = reporte_errores.crear_reporte(tipo, error, traza, origen="Prueba")  # Construye el contenido.
    assert identificador in texto and "TecNet Finder" in texto  # Comprueba identificación y proyecto.
    assert "ValueError: mensaje de prueba" in texto and "Prueba" in texto  # Comprueba la traza y el origen.
    assert "ID de incidente:" in texto and "Python:" in texto  # Incluye contexto técnico básico.


def prueba_dos_reportes_tienen_identificadores_distintos():
    tipo, error, traza = _excepcion_prueba()  # Construye dos eventos inmediatos.
    primero, _ = reporte_errores.crear_reporte(tipo, error, traza, origen="Uno")
    segundo, _ = reporte_errores.crear_reporte(tipo, error, traza, origen="Dos")
    assert primero != segundo  # Evita sobrescrituras de reportes sucesivos.


def prueba_guardar_reporte_en_destino_elegido(tmp_path):
    ruta = tmp_path / "reporte.txt"  # Aísla la operación en la carpeta temporal de pytest.
    resultado = reporte_errores.guardar_reporte(ruta, "Descripción y traza")  # Escribe los bytes UTF-8.
    assert resultado == ruta and ruta.read_text(encoding="utf-8") == "Descripción y traza"  # Verifica contenido íntegro.
    assert not (tmp_path / "otro.txt").exists()  # No crea archivos ajenos a la ruta solicitada.


def prueba_guardar_reporte_no_crea_directorio_implicito(tmp_path):
    with pytest.raises(OSError): reporte_errores.guardar_reporte(tmp_path / "sin_crear" / "error.txt", "texto")  # Propaga fallos reales de escritura.


def prueba_idiomas_tienen_botones_y_advertencia_de_privacidad():
    assert len(reporte_errores.TEXTOS) == 6  # Conserva los seis idiomas de TecNet Finder.
    assert all(len(textos) == 10 and all(textos) for textos in reporte_errores.TEXTOS.values())  # Verifica traducciones completas.
    assert "datos personales" in reporte_errores.TEXTOS["es"][2]  # Advierte antes de compartir reportes.


def prueba_gancho_principal_registra_una_sola_vez(monkeypatch, tmp_path):
    logger = logging.getLogger("TecNetFinder.PruebaErrores")  # Evita interferir con el registro real.
    logger.setLevel(logging.ERROR)  # Captura el incidente de prueba.
    ruta = tmp_path / "errores.log"  # Guarda un log temporal aislado.
    manejador = logging.FileHandler(ruta, encoding="utf-8")  # Reutiliza el formato estándar de Python.
    logger.addHandler(manejador)
    originales = []  # Conserva la evidencia del gancho anterior.
    monkeypatch.setattr(sys, "excepthook", lambda *datos: originales.append(datos))  # Sustituye temporalmente el hook original.
    monkeypatch.setattr(threading, "excepthook", lambda _datos: None)  # Aísla también el comportamiento de hilos.
    monkeypatch.setattr(reporte_errores, "_GESTOR_ACTIVO", None)  # Instala un capturador nuevo únicamente dentro de esta prueba.
    mostrados = []
    monkeypatch.setattr(reporte_errores, "_mostrar_dialogo", lambda identificador, reporte: mostrados.append(reporte) or True)  # Simula la ventana sin PySide6.
    try:
        gestor = reporte_errores.instalar_reporte_errores(logger)  # Instala los hooks de la prueba.
        assert reporte_errores.instalar_reporte_errores(logger) is gestor  # Comprueba idempotencia.
        tipo, error, traza = _excepcion_prueba()  # Crea la excepción real.
        sys.excepthook(tipo, error, traza)  # Ejecuta el gancho instalado.
        manejador.flush()
        assert ruta.read_text(encoding="utf-8").count("Error inesperado [") == 1  # Registra el incidente una vez.
        assert "ValueError: mensaje de prueba" in ruta.read_text(encoding="utf-8")  # Conserva la traza.
        assert len(mostrados) == 1 and not originales  # Muestra una sola ventana y no invoca el fallback.
    finally: logger.removeHandler(manejador); manejador.close()  # Libera el archivo temporal.


def prueba_errores_de_hilo_no_abren_ventanas(monkeypatch, tmp_path):
    logger = logging.getLogger("TecNetFinder.PruebaHilos")  # Prepara un logger independiente.
    logger.setLevel(logging.ERROR)
    ruta = tmp_path / "hilos.log"
    manejador = logging.FileHandler(ruta, encoding="utf-8")
    logger.addHandler(manejador)
    anteriores = []
    monkeypatch.setattr(threading, "excepthook", lambda argumentos: anteriores.append(argumentos))  # Registra la llamada al hook previo.
    monkeypatch.setattr(reporte_errores, "_mostrar_dialogo", lambda *_: pytest.fail("No se debe abrir una ventana desde hilos secundarios"))  # Prohíbe Qt.
    try:
        gestor = reporte_errores.GestorReporteErrores(logger)  # No modifica sys.excepthook en esta prueba.
        tipo, error, traza = _excepcion_prueba()
        datos = SimpleNamespace(exc_type=tipo, exc_value=error, exc_traceback=traza, thread=SimpleNamespace(name="PruebaHilo"))  # Simula un error en otro hilo.
        gestor.capturar_hilo(datos)  # Comprueba el registro sin invocar Qt.
        manejador.flush()
        assert "PruebaHilo" in ruta.read_text(encoding="utf-8") and len(anteriores) == 1  # Mantiene log y hook previo.
    finally: logger.removeHandler(manejador); manejador.close()


def prueba_logger_aislado_no_cambia_ganchos(monkeypatch, tmp_path):
    from Motor.infraestructura.registro import configurar_registro  # Comprueba la compatibilidad con el sistema de registro anterior.
    anterior_principal = sys.excepthook  # Conserva los ganchos reales de pytest.
    anterior_hilos = threading.excepthook
    configurar_registro(tmp_path)  # La carpeta explícita indica que es una prueba independiente.
    assert sys.excepthook is anterior_principal and threading.excepthook is anterior_hilos  # No instala un capturador global.


def prueba_interrupcion_normal_usa_gancho_previo(monkeypatch):
    logger = logging.getLogger("TecNetFinder.InterrupcionesPrueba")  # Evita registrar una interrupción intencional.
    anteriores = []
    monkeypatch.setattr(sys, "excepthook", lambda *datos: anteriores.append(datos))
    gestor = reporte_errores.GestorReporteErrores(logger)  # Construye el gestor sin instalar sus hooks globalmente.
    error = KeyboardInterrupt()  # Simula una interrupción normal del usuario.
    gestor.capturar_principal(KeyboardInterrupt, error, None)
    assert len(anteriores) == 1 and anteriores[0][1] is error  # Respeta el hook convencional sin crear un reporte.


def prueba_sin_interfaz_se_conserva_salida_original(monkeypatch):
    logger = logging.getLogger("TecNetFinder.SinInterfazPrueba")
    logger.addHandler(logging.NullHandler())  # Evita escribir en archivos reales.
    anteriores = []
    monkeypatch.setattr(sys, "excepthook", lambda *datos: anteriores.append(datos))
    monkeypatch.setattr(reporte_errores, "_mostrar_dialogo", lambda *_: False)  # Simula un inicio sin QApplication.
    gestor = reporte_errores.GestorReporteErrores(logger)
    tipo, error, traza = _excepcion_prueba()
    gestor.capturar_principal(tipo, error, traza)
    assert len(anteriores) == 1 and anteriores[0][1] is error  # La consola conserva la traza original.
