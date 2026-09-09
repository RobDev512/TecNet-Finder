# ============================================================
# Archivo: prueba_gestor_componente_ia.py
# Proyecto: TecNet Finder
#
# Descripción:
# Este archivo comprueba la ubicación y el estado del componente
# opcional de inteligencia artificial sin utilizar la instalación
# real del usuario.
# ============================================================

from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Importa el administrador de archivos del componente opcional.


def prueba_componente_utiliza_estructura_administrada(tmp_path):
    gestor = GestorComponenteIA(ruta_datos_locales=tmp_path)

    assert gestor.ruta_base == tmp_path / "TecNetFinder" / "IA"
    assert gestor.ruta_ollama == tmp_path / "TecNetFinder" / "IA" / "Ollama"
    assert gestor.ruta_modelos == tmp_path / "TecNetFinder" / "IA" / "Ollama" / "modelos"


def prueba_componente_no_instalado_sin_runtime(tmp_path):
    gestor = GestorComponenteIA(ruta_datos_locales=tmp_path)

    assert gestor.instalado() is False


def prueba_componente_detecta_instalacion_completa(tmp_path):
    gestor = GestorComponenteIA(ruta_datos_locales=tmp_path)
    gestor.ruta_modelos.mkdir(parents=True)
    gestor.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")
    (gestor.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")

    assert gestor.instalado() is True


def prueba_componente_desinstala_solamente_directorio_administrado(tmp_path):
    gestor = GestorComponenteIA(ruta_datos_locales=tmp_path)
    gestor.ruta_modelos.mkdir(parents=True)
    gestor.ruta_ejecutable_ollama.write_bytes(b"runtime simulado")
    (gestor.ruta_modelos / "modelo.bin").write_bytes(b"modelo simulado")

    assert gestor.desinstalar_archivos() is True
    assert not gestor.ruta_base.exists()
    assert tmp_path.exists()