# ============================================================
# Archivo: prueba_restaurador_preferencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba alcance, respaldo y repetibilidad del restablecimiento.
# Las pruebas no utilizan el directorio real del usuario.
# ============================================================

from zipfile import ZipFile  # Permite verificar el contenido exacto de los respaldos.

from Motor.configuracion.restaurador_preferencias import restaurar_preferencias  # Utiliza el servicio real sin mostrar ventanas.


def prueba_restaura_generales_sin_tocar_ia_ni_logs(tmp_path):  # Confirma que el restablecimiento ordinario conserva otros datos.
    raiz = tmp_path / "TecNetFinder"  # Aísla las pruebas del perfil de Windows.
    raiz.mkdir()  # Prepara la carpeta de preferencias temporales.
    (raiz / "preferencias_aplicacion.json").write_text('{"idioma_interfaz":"en"}', encoding="utf-8")  # Simula una personalización real.
    (raiz / "preferencias_tema.json").write_text('{"tema":"oscuro"}', encoding="utf-8")  # Conserva una segunda preferencia distinta.
    (raiz / "preferencias_ia.json").write_text('{"autocompletado_ia_activado":false}', encoding="utf-8")  # Simula IA desactivada.
    (raiz / "logs").mkdir()  # Crea un directorio de eventos ajeno a la operación.
    (raiz / "logs" / "tecnet-finder.log").write_text("evento", encoding="utf-8")  # Conserva un registro de prueba.

    resultado = restaurar_preferencias(directorio=raiz)  # Ejecuta el restablecimiento sin incluir IA.
    assert set(resultado.archivos) == {"preferencias_aplicacion.json", "preferencias_tema.json", "preferencias_modalidad_advertencias.json"}  # Comprueba el alcance correcto.
    assert (raiz / "preferencias_aplicacion.json").read_text(encoding="utf-8").strip() == "{}"  # Comprueba los valores por defecto.
    assert (raiz / "preferencias_tema.json").read_text(encoding="utf-8").strip() == "{}"  # Recupera el modo de tema automático.
    assert (raiz / "preferencias_ia.json").read_text(encoding="utf-8") == '{"autocompletado_ia_activado":false}'  # Nunca cambia IA sin autorización.
    assert (raiz / "logs" / "tecnet-finder.log").read_text(encoding="utf-8") == "evento"  # Conserva el historial de la aplicación.
    assert resultado.respaldo is not None and resultado.respaldo.is_file()  # Comprueba la existencia del respaldo.
    with ZipFile(resultado.respaldo) as respaldo:
        assert respaldo.read("preferencias_aplicacion.json") == b'{"idioma_interfaz":"en"}'  # Conserva los bytes exactos del idioma anterior.
        assert respaldo.read("preferencias_tema.json") == b'{"tema":"oscuro"}'  # También conserva el tema previo.
        assert "preferencias_ia.json" not in respaldo.namelist()  # Evita incluir archivos fuera de la operación.


def prueba_ia_se_restaura_unicamente_con_autorizacion(tmp_path):  # Comprueba el alcance opcional de la IA.
    raiz = tmp_path / "TecNetFinder"  # Trabaja exclusivamente en un directorio aislado.
    raiz.mkdir()  # Prepara el espacio temporal de los archivos.
    (raiz / "preferencias_ia.json").write_text('{"autocompletado_ia_activado":false}', encoding="utf-8")  # Simula una decisión previa.
    resultado = restaurar_preferencias(directorio=raiz, incluir_ia=True)  # Restablece incluyendo las preferencias de IA.
    assert "preferencias_ia.json" in resultado.archivos  # Confirma que se incluyó el archivo correcto.
    assert (raiz / "preferencias_ia.json").read_text(encoding="utf-8").strip() == "{}"  # Reactiva los valores iniciales del gestor.
    with ZipFile(resultado.respaldo) as respaldo:
        assert respaldo.read("preferencias_ia.json") == b'{"autocompletado_ia_activado":false}'  # Conserva la configuración anterior.


def prueba_primera_instalacion_no_necesita_respaldo(tmp_path):  # Asegura que también funciona sin preferencias previas.
    resultado = restaurar_preferencias(directorio=tmp_path)  # No requiere que existan archivos originales.
    assert resultado.respaldo is None  # Evita respaldos vacíos.
    assert all((tmp_path / nombre).read_text(encoding="utf-8").strip() == "{}" for nombre in resultado.archivos)  # Crea valores predeterminados válidos.


def prueba_revierte_si_falla_una_sustitucion(tmp_path, monkeypatch):  # Evita que una restauración interrumpida deje preferencias mezcladas.
    raiz = tmp_path / "TecNetFinder"  # Aísla el fallo de los archivos verdaderos del usuario.
    raiz.mkdir()  # Permite preparar dos preferencias reales.
    aplicacion = raiz / "preferencias_aplicacion.json"  # Define el primer archivo afectado.
    tema = raiz / "preferencias_tema.json"  # Define el segundo archivo, donde simularemos el error.
    aplicacion.write_bytes(b'{"idioma_interfaz":"fr"}')  # Prepara una elección de idioma anterior.
    tema.write_bytes(b'{"tema":"oceano"}')  # Conserva un tema anterior que debe recuperarse.

    from pathlib import Path  # Permite interceptar únicamente las operaciones de cambio de nombre.
    original = Path.replace  # Conserva la implementación real utilizada por el servicio.

    def reemplazar_con_fallo(self, destino):
        if Path(destino) == tema and self.suffix == ".tmp": raise PermissionError("archivo bloqueado")  # Simula que Windows impide sustituir el tema.
        return original(self, destino)  # Deja funcionar el resto y la reversión del primer archivo.

    monkeypatch.setattr(Path, "replace", reemplazar_con_fallo)  # Activa el fallo solamente durante esta prueba.
    import pytest  # Verifica explícitamente que el servicio informe la interrupción.
    with pytest.raises(PermissionError): restaurar_preferencias(directorio=raiz)  # No oculta el problema de escritura.
    assert aplicacion.read_bytes() == b'{"idioma_interfaz":"fr"}'  # Revierte el primer archivo ya sustituido.
    assert tema.read_bytes() == b'{"tema":"oceano"}'  # Conserva el archivo que no se pudo tocar.
    assert not list(raiz.glob(".*.tmp"))  # Elimina los archivos temporales de la operación fallida.


def prueba_respaldo_nuevo_no_reemplaza_el_anterior(tmp_path):  # Garantiza que dos restablecimientos no eliminen respaldos existentes.
    raiz = tmp_path / "TecNetFinder"  # Mantiene el historial fuera del directorio real.
    raiz.mkdir()  # Crea la carpeta de preferencias de prueba.
    archivo = raiz / "preferencias_aplicacion.json"  # Utiliza un archivo conocido por el servicio.
    archivo.write_text('{"idioma_interfaz":"de"}', encoding="utf-8")  # Simula el primer valor personalizado.
    primer = restaurar_preferencias(directorio=raiz)  # Guarda una primera copia de seguridad.
    archivo.write_text('{"idioma_interfaz":"pt"}', encoding="utf-8")  # Simula otra preferencia del usuario.
    segundo = restaurar_preferencias(directorio=raiz)  # Ejecuta una segunda restauración.
    assert primer.respaldo != segundo.respaldo  # Comprueba que ninguno de los nombres se repitió.
    assert primer.respaldo.is_file() and segundo.respaldo.is_file()  # Ambos respaldos deben continuar disponibles.
    with ZipFile(primer.respaldo) as respaldo: assert respaldo.read("preferencias_aplicacion.json") == b'{"idioma_interfaz":"de"}'  # Verifica la primera copia.
    with ZipFile(segundo.respaldo) as respaldo: assert respaldo.read("preferencias_aplicacion.json") == b'{"idioma_interfaz":"pt"}'  # Verifica la segunda copia.
