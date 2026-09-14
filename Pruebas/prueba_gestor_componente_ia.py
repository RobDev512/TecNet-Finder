# ============================================================
# Archivo: prueba_gestor_componente_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene las pruebas automáticas correspondientes
# con GestorComponenteIA.
#
# Comprueba las rutas utilizadas por la instalación privada,
# detección del runtime y del modelo, eliminación limitada
# exclusivamente a los archivos administrados por TecNet Finder
# y reintentos ante bloqueos temporales de Windows.
#
# Todas las operaciones utilizan directorios temporales creados
# por pytest para no modificar la instalación real del usuario.
# ============================================================

import shutil  # Permite conservar y sustituir temporalmente rmtree durante la prueba que simula un bloqueo de Windows.

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Importa el administrador encargado de las rutas y archivos físicos del componente opcional.


def prueba_componente_utiliza_rutas_administradas(tmp_path):  # Comprueba que todos los archivos de IA se mantengan dentro del espacio privado reservado por TecNet Finder.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Sustituye LocalAppData por una carpeta temporal aislada creada por pytest.
    assert componente.ruta_base == tmp_path / "TecNetFinder" / "IA"  # Confirma la ubicación raíz destinada exclusivamente al componente opcional.
    assert componente.ruta_ollama == tmp_path / "TecNetFinder" / "IA" / "Ollama"  # Comprueba que el runtime permanezca dentro de la carpeta administrada.
    assert componente.ruta_ejecutable_ollama == tmp_path / "TecNetFinder" / "IA" / "Ollama" / "ollama.exe"  # Verifica la ruta exacta esperada para el ejecutable privado.
    assert componente.ruta_modelos == tmp_path / "TecNetFinder" / "IA" / "Ollama" / "modelos"  # Confirma la ubicación donde deben mantenerse los modelos locales.


def prueba_componente_ausente_no_se_considera_instalado(tmp_path):  # Comprueba el estado de un usuario que todavía no posee ningún archivo perteneciente a IA.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Crea el administrador apuntando hacia una carpeta temporal completamente vacía.
    assert componente.instalado() is False  # Confirma que la ausencia de runtime y modelo nunca sea interpretada como una instalación válida.


def prueba_componente_detecta_runtime_y_modelo(tmp_path):  # Comprueba que una estructura completa sea reconocida como una instalación disponible.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Utiliza exclusivamente la ubicación temporal proporcionada por pytest.
    componente.ruta_modelos.mkdir(parents=True)  # Crea la carpeta que normalmente contendrá los archivos descargados del modelo.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Crea un archivo que representa el ejecutable privado requerido.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Agrega al menos un archivo real dentro de la carpeta de modelos.
    assert componente.instalado() is True  # Confirma que runtime, directorio y contenido del modelo sean suficientes para considerar instalada la IA.


def prueba_componente_desinstala_solamente_ruta_administrada(tmp_path):  # Comprueba que la desinstalación nunca elimine información ajena a TecNet Finder.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Prepara una instalación simulada dentro de una ubicación completamente aislada.
    componente.ruta_modelos.mkdir(parents=True)  # Crea la estructura privada que posteriormente deberá desaparecer.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Representa el ejecutable administrado por la aplicación.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Representa los archivos del modelo que también pertenecen a la instalación.
    archivo_ajeno = tmp_path / "archivo-ajeno.txt"  # Crea deliberadamente un archivo fuera de ruta_base para comprobar el límite de la eliminación.
    archivo_ajeno.write_text("conservar", encoding="utf-8")  # Guarda contenido que deberá permanecer intacto después de desinstalar.
    assert componente.desinstalar_archivos(intentos=1, espera_segundos=0) is True  # Ejecuta una eliminación inmediata sin pausas y confirma su éxito.
    assert not componente.ruta_base.exists()  # Comprueba que toda la carpeta administrada haya desaparecido.
    assert archivo_ajeno.is_file()  # Confirma que la operación no haya afectado ningún archivo situado fuera de su ámbito.


def prueba_componente_reintenta_si_windows_bloquea_temporalmente(tmp_path, monkeypatch):  # Comprueba la política de reintentos utilizada cuando Windows mantiene temporalmente un archivo en uso.
    componente = GestorComponenteIA(ruta_datos_locales=tmp_path)  # Crea nuevamente una instalación completamente temporal.
    componente.ruta_modelos.mkdir(parents=True)  # Prepara el directorio privado que deberá retirarse después del bloqueo simulado.
    componente.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")  # Representa un ejecutable que podría continuar ocupado brevemente.
    (componente.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")  # Representa los datos del modelo local.
    rmtree_real = shutil.rmtree  # Conserva la función original para poder ejecutar una eliminación verdadera después del primer fallo.
    llamadas = {"cantidad": 0}  # Registra cuántas veces GestorComponenteIA intenta retirar la carpeta.

    def rmtree_simulado(ruta):  # Sustituye temporalmente rmtree para provocar un bloqueo únicamente durante el primer intento.
        llamadas["cantidad"] += 1  # Incrementa el contador cada vez que producción solicita eliminar la carpeta.

        if llamadas["cantidad"] == 1:  # Comprueba si se trata exactamente del primer intento de desinstalación.
            raise PermissionError("Archivo temporalmente ocupado")  # Simula el error que Windows puede producir mientras un ejecutable todavía se encuentra en uso.

        rmtree_real(ruta)  # Permite que el segundo intento elimine realmente la carpeta temporal creada por la prueba.

    monkeypatch.setattr(shutil, "rmtree", rmtree_simulado)  # Sustituye únicamente durante esta prueba la función utilizada internamente por producción.
    resultado = componente.desinstalar_archivos(intentos=3, espera_segundos=0)  # Permite hasta tres intentos pero elimina las pausas para que la prueba sea inmediata.
    assert resultado is True  # Confirma que un bloqueo temporal no haga fracasar definitivamente la desinstalación.
    assert llamadas["cantidad"] == 2  # Comprueba que haya existido exactamente un intento fallido y uno exitoso.
    assert not componente.ruta_base.exists()  # Verifica que el componente haya desaparecido físicamente después del reintento.