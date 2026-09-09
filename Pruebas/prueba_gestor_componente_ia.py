# ============================================================
# Archivo: prueba_gestor_componente_ia.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba las rutas, detección y eliminación del
# componente opcional de inteligencia artificial.
#
# Todas las operaciones utilizan directorios temporales para no
# modificar la instalación real utilizada por TecNet Finder.
# ============================================================

import shutil  # Permite sustituir temporalmente la eliminación real durante la prueba de reintentos.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Importa el administrador de rutas y archivos que debe comprobarse.


def prueba_componente_utiliza_rutas_administradas(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Sustituye LocalAppData por una ubicación aislada creada por pytest.

    assert componente.ruta_base == tmp_path / "TecNetFinder" / "IA"
    assert componente.ruta_ollama == tmp_path / "TecNetFinder" / "IA" / "Ollama"
    assert componente.ruta_ejecutable_ollama == tmp_path / "TecNetFinder" / "IA" / "Ollama" / "ollama.exe"
    assert componente.ruta_modelos == tmp_path / "TecNetFinder" / "IA" / "Ollama" / "modelos"


def prueba_componente_ausente_no_se_considera_instalado(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Representa un usuario que nunca instaló la asistencia.

    assert componente.instalado() is False


def prueba_componente_detecta_runtime_y_modelo(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza una instalación completamente temporal.
    componente.ruta_modelos.mkdir(parents=True)  # Prepara la estructura correspondiente al runtime y sus modelos.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Representa la presencia del ejecutable privado.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Representa al menos un archivo perteneciente al modelo.

    assert componente.instalado() is True


def prueba_componente_desinstala_solamente_ruta_administrada(tmp_path):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Prepara una instalación aislada.
    componente.ruta_modelos.mkdir(parents=True)  # Crea la estructura física que posteriormente deberá eliminarse.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Representa el runtime instalado.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Representa el modelo instalado.

    archivo_ajeno = tmp_path / "archivo-ajeno.txt"  # Coloca información fuera de la carpeta administrada por TecNet Finder.
    archivo_ajeno.write_text("conservar", encoding="utf-8")  # Permite verificar que la desinstalación no exceda su ámbito.

    assert componente.desinstalar_archivos(intentos=1, espera_segundos=0) is True
    assert not componente.ruta_base.exists()
    assert archivo_ajeno.is_file()


def prueba_componente_reintenta_si_windows_bloquea_temporalmente(tmp_path, monkeypatch):
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Prepara una instalación temporal equivalente a la real.
    componente.ruta_modelos.mkdir(parents=True)  # Crea la estructura que deberá ser retirada después del bloqueo simulado.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Representa un ejecutable que Windows podría mantener abierto brevemente.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Representa los datos privados del modelo.

    rmtree_real = shutil.rmtree  # Conserva la implementación original para utilizarla después del primer fallo.
    llamadas = {"cantidad": 0}  # Registra cuántas veces el administrador intentó realizar la eliminación.

    def rmtree_simulado(ruta):
        llamadas["cantidad"] += 1  # Registra cada intento equivalente a una llamada realizada sobre Windows.

        if llamadas["cantidad"] == 1:
            raise PermissionError("Archivo temporalmente ocupado")  # Simula exactamente el bloqueo transitorio que observamos durante la prueba real.

        rmtree_real(ruta)  # Permite eliminar normalmente los archivos a partir del segundo intento.

    monkeypatch.setattr(shutil, "rmtree", rmtree_simulado)  # Sustituye únicamente durante esta prueba la operación utilizada por producción.

    resultado = componente.desinstalar_archivos(intentos=3, espera_segundos=0)  # Evita esperas reales mientras comprueba la política de reintentos.

    assert resultado is True
    assert llamadas["cantidad"] == 2
    assert not componente.ruta_base.exists()