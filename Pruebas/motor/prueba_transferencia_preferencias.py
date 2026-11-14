# ============================================================
# Archivo: prueba_transferencia_preferencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Verifica exportación, importación, alcance de IA, validaciones,
# respaldos y recuperación ante fallos sin tocar el perfil real.
# ============================================================

import json  # Prepara archivos JSON controlados durante las pruebas.
from pathlib import Path  # Intercepta sustituciones para simular errores.
from zipfile import ZipFile  # Comprueba los respaldos previos a importar.

import pytest  # Comprueba fallos esperados sin modificar archivos reales.

from Motor.configuracion.transferencia_preferencias import exportar_preferencias, importar_preferencias, inspeccionar_preferencias  # Utiliza el servicio auténtico.


def _datos_validos() -> dict:  # Construye un ejemplo completamente compatible con el formato actual.
    return {"formato": "TecNetFinder.Preferencias", "version_formato": 1, "preferencias": {"aplicacion": {"idioma_interfaz": "fr", "tamano_fuente_editor": 12}, "tema": {"tema": "oscuro_oceano", "origen": "manual"}, "advertencias": {"bloquear_interaccion_fondo": False}, "ia": {"autocompletado_ia_activado": False, "diagnosticos_ia_activados": False}}}  # Permite probar ambos ámbitos.


def prueba_exportacion_copia_solo_preferencias_conocidas(tmp_path):
    raiz = tmp_path / "perfil"  # Evita usar LocalAppData real.
    raiz.mkdir()  # Crea un directorio aislado.
    (raiz / "preferencias_aplicacion.json").write_text('{"idioma_interfaz":"de","tamano_fuente_editor":14}', encoding="utf-8")  # Simula preferencias guardadas.
    (raiz / "preferencias_ia.json").write_text('{"autocompletado_ia_activado":false}', encoding="utf-8")  # Simula IA desactivada.
    (raiz / "logs").mkdir()  # Prepara un registro ajeno a la exportación.
    (raiz / "logs" / "tecnet-finder.log").write_text("contenido privado", encoding="utf-8")  # Comprueba que nunca se filtra.
    destino = tmp_path / "preferencias.json"  # Selecciona una ruta fuera del perfil.
    exportar_preferencias(destino, directorio=raiz)  # Deja IA fuera de forma predeterminada.
    datos = json.loads(destino.read_text(encoding="utf-8"))  # Inspecciona el documento portátil.
    assert set(datos["preferencias"]) == {"aplicacion", "tema", "advertencias"}  # Solo se exportan las secciones generales.
    assert datos["preferencias"]["aplicacion"]["idioma_interfaz"] == "de"  # Conserva la decisión de idioma.
    assert "contenido privado" not in destino.read_text(encoding="utf-8")  # No incluye eventos del log.
    assert not inspeccionar_preferencias(destino)  # Informa correctamente que no contiene IA.


def prueba_exportacion_importacion_con_ia_autorizada(tmp_path):
    raiz = tmp_path / "perfil"  # Aísla los archivos de origen.
    raiz.mkdir()  # Prepara el directorio de preferencias.
    (raiz / "preferencias_ia.json").write_text('{"autocompletado_ia_activado":false}', encoding="utf-8")  # Simula preferencias IA.
    archivo = tmp_path / "copia.json"  # Elige el destino externo.
    exportar_preferencias(archivo, directorio=raiz, incluir_ia=True)  # Exporta los cuatro ámbitos.
    assert inspeccionar_preferencias(archivo)  # Comprueba la inclusión de IA.
    nueva = tmp_path / "nuevo"  # Simula otra instalación.
    resultado = importar_preferencias(archivo, directorio=nueva, incluir_ia=True)  # Importa con autorización explícita.
    assert len(resultado.archivos) == 4  # Incluye IA junto con las preferencias generales.
    assert (nueva / "preferencias_ia.json").read_text(encoding="utf-8").find('"autocompletado_ia_activado": false') > 0  # Conserva la elección de IA.
    assert resultado.respaldo is None  # No inventa respaldos si aún no había preferencias.


def prueba_importacion_general_conserva_ia_y_logs(tmp_path):
    raiz = tmp_path / "perfil"  # Simula la instalación destino.
    raiz.mkdir()  # Crea el almacenamiento temporal.
    (raiz / "preferencias_aplicacion.json").write_text('{"idioma_interfaz":"en"}', encoding="utf-8")  # Valor previo distinto.
    (raiz / "preferencias_ia.json").write_text('{"autocompletado_ia_activado":true}', encoding="utf-8")  # IA que no debe cambiar.
    (raiz / "logs").mkdir()  # Registro que tampoco debe cambiar.
    (raiz / "logs" / "tecnet-finder.log").write_text("evento", encoding="utf-8")  # Registra contenido de prueba.
    origen = tmp_path / "importable.json"  # Prepara un paquete compatible.
    origen.write_text(json.dumps(_datos_validos()), encoding="utf-8")  # Incluye IA en el archivo.
    resultado = importar_preferencias(origen, directorio=raiz)  # Por defecto ignora IA del paquete.
    assert len(resultado.archivos) == 3  # Sustituye solo los tres archivos generales.
    assert '"idioma_interfaz": "fr"' in (raiz / "preferencias_aplicacion.json").read_text(encoding="utf-8")  # Aplica el idioma nuevo.
    assert (raiz / "preferencias_ia.json").read_text(encoding="utf-8") == '{"autocompletado_ia_activado":true}'  # No modifica IA.
    assert (raiz / "logs" / "tecnet-finder.log").read_text(encoding="utf-8") == "evento"  # Conserva logs.
    assert resultado.respaldo is not None and resultado.respaldo.is_file()  # Crea una copia antes de importar.
    with ZipFile(resultado.respaldo) as z:  # Revisa el respaldo.
        assert z.read("preferencias_aplicacion.json") == b'{"idioma_interfaz":"en"}'  # Guarda los bytes originales.
        assert "preferencias_ia.json" not in z.namelist()  # No captura información fuera del alcance.


def prueba_archivo_ajeno_se_rechaza_sin_cambiar_nada(tmp_path):
    raiz = tmp_path / "perfil"  # Aísla el destino.
    raiz.mkdir()  # Crea la carpeta.
    ruta = raiz / "preferencias_aplicacion.json"  # Identifica la preferencia existente.
    ruta.write_bytes(b'{"idioma_interfaz":"es"}')  # Prepara la decisión actual.
    origen = tmp_path / "ajeno.json"  # Crea un JSON que no es de TecNet Finder.
    origen.write_text('{"config":true}', encoding="utf-8")  # Mantiene sintaxis válida pero formato incompatible.
    with pytest.raises(ValueError): importar_preferencias(origen, directorio=raiz)  # Rechaza antes de escribir.
    assert ruta.read_bytes() == b'{"idioma_interfaz":"es"}'  # No modifica la preferencia existente.
    assert not (raiz / "respaldos").exists()  # Tampoco genera respaldos por una operación rechazada.


def prueba_valores_inseguros_se_rechazan_antes_de_importar(tmp_path):
    raiz = tmp_path / "perfil"  # Directorio sin preferencias anteriores.
    origen = tmp_path / "invalido.json"  # Archivo con valor incompatible.
    datos = _datos_validos()  # Parte de un paquete auténtico.
    datos["preferencias"]["aplicacion"]["tamano_fuente_editor"] = 9999  # Intenta introducir un tamaño fuera de rango.
    origen.write_text(json.dumps(datos), encoding="utf-8")  # Guarda el contenido para validar.
    with pytest.raises(ValueError): importar_preferencias(origen, directorio=raiz)  # Rechaza antes de escribir.
    assert not raiz.exists()  # No crea ni altera la carpeta del usuario.


def prueba_campo_desconocido_se_rechaza_para_evitar_filtraciones(tmp_path):
    origen = tmp_path / "desconocido.json"  # Prepara un archivo externo.
    datos = _datos_validos()  # Usa metadatos correctos.
    datos["preferencias"]["ia"]["clave_privada"] = "no importar"  # Simula una clave no declarada.
    origen.write_text(json.dumps(datos), encoding="utf-8")  # Guarda el paquete.
    with pytest.raises(ValueError): inspeccionar_preferencias(origen)  # La inspección ya debe rechazarlo.
    with pytest.raises(ValueError): importar_preferencias(origen, directorio=tmp_path / "perfil")  # Ni siquiera al excluir IA debe aceptarlo.


def prueba_no_importa_ia_si_no_existe_en_archivo(tmp_path):
    origen = tmp_path / "sin-ia.json"  # Elige un archivo sin IA.
    datos = _datos_validos()  # Parte de un documento correcto.
    datos["preferencias"].pop("ia")  # Retira explícitamente la sección opcional.
    origen.write_text(json.dumps(datos), encoding="utf-8")  # Guarda el archivo.
    with pytest.raises(ValueError): importar_preferencias(origen, directorio=tmp_path / "perfil", incluir_ia=True)  # No restaura IA vacía ni afirma haberla importado.
    assert not (tmp_path / "perfil").exists()  # Ningún archivo fue creado.


def prueba_revierte_todas_las_preferencias_ante_fallo(tmp_path, monkeypatch):
    raiz = tmp_path / "perfil"  # Crea una instalación ficticia.
    raiz.mkdir()  # Habilita el almacenamiento.
    aplicacion = raiz / "preferencias_aplicacion.json"  # Primer archivo a sustituir.
    tema = raiz / "preferencias_tema.json"  # Segundo archivo, donde se simulará el error.
    aplicacion.write_bytes(b'{"idioma_interfaz":"de"}')  # Conserva bytes originales exactos.
    tema.write_bytes(b'{"tema":"oscuro_tecnet"}')  # Conserva otra preferencia.
    archivo = tmp_path / "datos.json"  # Prepara el respaldo de importación.
    archivo.write_text(json.dumps(_datos_validos()), encoding="utf-8")  # Incluye un tema distinto.
    original = Path.replace  # Recupera el reemplazo real de Python.

    def reemplazar_con_fallo(self, destino):  # Simula permisos de Windows sobre un único destino.
        if Path(destino) == tema and self.suffix == ".tmp": raise PermissionError("tema bloqueado")  # Detiene el segundo reemplazo.
        return original(self, destino)  # Permite el resto de operaciones y la reversión.

    monkeypatch.setattr(Path, "replace", reemplazar_con_fallo)  # Intercepta solo esta prueba.
    with pytest.raises(PermissionError): importar_preferencias(archivo, directorio=raiz)  # No oculta el error.
    assert aplicacion.read_bytes() == b'{"idioma_interfaz":"de"}'  # Recupera el primer archivo sustituido.
    assert tema.read_bytes() == b'{"tema":"oscuro_tecnet"}'  # Conserva el segundo original.
    assert not list(raiz.glob(".*.tmp"))  # Limpia las copias temporales.


def prueba_rechaza_version_futura_y_archivo_demasiado_grande(tmp_path):
    origen = tmp_path / "futuro.json"  # Prepara un archivo de versión futura.
    datos = _datos_validos()  # Conserva una estructura válida.
    datos["version_formato"] = 2  # Anuncia una versión no implementada.
    origen.write_text(json.dumps(datos), encoding="utf-8")  # Guarda el archivo.
    with pytest.raises(ValueError): inspeccionar_preferencias(origen)  # Rechaza el formato.
    origen.write_text("x" * 300000, encoding="utf-8")  # Simula datos superiores al límite.
    with pytest.raises(ValueError): inspeccionar_preferencias(origen)  # No carga ni procesa el contenido enorme.
