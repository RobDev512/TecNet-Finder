# ============================================================
# Archivo: prueba_tipografia_interfaz.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba las preferencias relacionadas con la tipografía
# general de la interfaz de TecNet Finder.
#
# Estas pruebas verifican:
# - Valores predeterminados.
# - Persistencia de familia y tamaño.
# - Rechazo de valores inválidos.
# - Recuperación segura de archivos alterados.
# - Independencia entre interfaz y editor.
# - Funcionamiento de la copia temporal de Configuración.
#
# Se utiliza tmp_path para evitar alterar la configuración real
# almacenada dentro de LocalAppData.
# ============================================================

import json  # Permite preparar archivos de preferencias controlados durante algunas pruebas.

from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Administra las preferencias persistentes reales.
from Motor.configuracion.preferencias_configuracion_temporales import PreferenciasConfiguracionTemporales  # Proporciona la copia temporal utilizada por Configuración.


def test_tipografia_interfaz_utiliza_valores_predeterminados(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea una configuración nueva completamente aislada.

    assert (
        preferencias.familia_fuente_interfaz()
        == PreferenciasAplicacion.FUENTE_INTERFAZ_PREDETERMINADA
    )  # Comprueba que una instalación nueva mantenga la apariencia histórica.

    assert (
        preferencias.tamano_fuente_interfaz()
        == PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_PREDETERMINADO
    )  # Comprueba que el tamaño inicial continúe siendo 10 pt.


def test_tipografia_interfaz_persiste_entre_instancias(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara el administrador que escribirá los valores.

    assert preferencias.establecer_familia_fuente_interfaz("Segoe UI") is True  # Guarda una familia diferente.
    assert preferencias.establecer_tamano_fuente_interfaz(11) is True  # Guarda un tamaño diferente.

    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Fuerza una lectura nueva desde el archivo.

    assert preferencias_recargadas.familia_fuente_interfaz() == "Segoe UI"  # Confirma que la familia permanezca.
    assert preferencias_recargadas.tamano_fuente_interfaz() == 11  # Confirma que también permanezca el tamaño.


def test_tipografia_interfaz_rechaza_familia_vacia(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Utiliza una configuración inicialmente vacía.

    assert preferencias.establecer_familia_fuente_interfaz("") is False  # Rechaza una cadena completamente vacía.
    assert preferencias.establecer_familia_fuente_interfaz("   ") is False  # Rechaza también una cadena formada únicamente por espacios.

    assert (
        preferencias.familia_fuente_interfaz()
        == PreferenciasAplicacion.FUENTE_INTERFAZ_PREDETERMINADA
    )  # Comprueba que el rechazo no altere la configuración real.


def test_tipografia_interfaz_rechaza_tamanos_fuera_de_rango(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara una configuración temporal.

    assert (
        preferencias.establecer_tamano_fuente_interfaz(
            PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_MINIMO - 1
        )
        is False
    )  # Rechaza un tamaño menor al permitido.

    assert (
        preferencias.establecer_tamano_fuente_interfaz(
            PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_MAXIMO + 1
        )
        is False
    )  # Rechaza un tamaño mayor al permitido.

    assert preferencias.establecer_tamano_fuente_interfaz(True) is False  # Impide interpretar True como el entero 1.

    assert (
        preferencias.tamano_fuente_interfaz()
        == PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_PREDETERMINADO
    )  # Comprueba que continúe utilizando el valor seguro.


def test_tipografia_interfaz_recupera_valores_seguros_si_archivo_es_invalido(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara la ruta temporal de preferencias.

    preferencias.ruta_directorio.mkdir(
        parents=True,
        exist_ok=True,
    )  # Crea la carpeta necesaria para escribir manualmente el archivo.

    preferencias.ruta_archivo.write_text(
        json.dumps(
            {
                "familia_fuente_interfaz": "",
                "tamano_fuente_interfaz": 100,
            }
        ),
        encoding="utf-8",
    )  # Simula información externa válida como JSON pero inválida para estas preferencias.

    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Recupera los valores mediante una instancia nueva.

    assert (
        preferencias_recargadas.familia_fuente_interfaz()
        == PreferenciasAplicacion.FUENTE_INTERFAZ_PREDETERMINADA
    )  # Recupera la familia segura.

    assert (
        preferencias_recargadas.tamano_fuente_interfaz()
        == PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_PREDETERMINADO
    )  # Recupera el tamaño seguro.


def test_tipografia_interfaz_es_independiente_de_tipografia_editor(tmp_path):
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara una configuración inicialmente predeterminada.

    assert preferencias.establecer_familia_fuente_interfaz("Segoe UI") is True  # Cambia la interfaz.
    assert preferencias.establecer_tamano_fuente_interfaz(11) is True  # Cambia el tamaño de la interfaz.

    assert preferencias.establecer_familia_fuente_editor("Cascadia Code") is True  # Cambia independientemente el editor.
    assert preferencias.establecer_tamano_fuente_editor(13) is True  # Cambia independientemente su tamaño.

    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Obliga a recuperar todo desde disco.

    assert preferencias_recargadas.familia_fuente_interfaz() == "Segoe UI"  # Confirma la configuración general.
    assert preferencias_recargadas.tamano_fuente_interfaz() == 11  # Confirma su tamaño.

    assert preferencias_recargadas.familia_fuente_editor() == "Cascadia Code"  # Confirma que el editor mantenga otra familia.
    assert preferencias_recargadas.tamano_fuente_editor() == 13  # Confirma que también mantenga otro tamaño.


def test_copia_temporal_modifica_tipografia_sin_alterar_preferencias_reales(tmp_path):
    preferencias_reales = PreferenciasAplicacion(tmp_path)  # Crea la configuración persistente real.
    preferencias_temporales = PreferenciasConfiguracionTemporales(preferencias_reales)  # Crea la copia utilizada por Configuración.

    assert preferencias_temporales.establecer_familia_fuente_interfaz("Arial") is True  # Modifica únicamente la copia temporal.
    assert preferencias_temporales.establecer_tamano_fuente_interfaz(12) is True  # Modifica también su tamaño temporal.

    assert preferencias_temporales.familia_fuente_interfaz() == "Arial"  # Confirma el cambio dentro de Configuración.
    assert preferencias_temporales.tamano_fuente_interfaz() == 12  # Confirma el tamaño temporal.

    assert (
        preferencias_reales.familia_fuente_interfaz()
        == PreferenciasAplicacion.FUENTE_INTERFAZ_PREDETERMINADA
    )  # Comprueba que Cancelar todavía podría descartar la nueva familia.

    assert (
        preferencias_reales.tamano_fuente_interfaz()
        == PreferenciasAplicacion.TAMANO_FUENTE_INTERFAZ_PREDETERMINADO
    )  # Comprueba que tampoco se haya persistido el tamaño.


def test_copia_temporal_recarga_tipografia_confirmada(tmp_path):
    preferencias_reales = PreferenciasAplicacion(tmp_path)  # Prepara las preferencias persistentes.

    assert preferencias_reales.establecer_familia_fuente_interfaz("Segoe UI") is True  # Guarda una familia definitiva.
    assert preferencias_reales.establecer_tamano_fuente_interfaz(11) is True  # Guarda un tamaño definitivo.

    preferencias_temporales = PreferenciasConfiguracionTemporales(preferencias_reales)  # Crea Configuración a partir de esos valores.

    assert preferencias_temporales.familia_fuente_interfaz() == "Segoe UI"  # Confirma que la copia herede la familia real.
    assert preferencias_temporales.tamano_fuente_interfaz() == 11  # Confirma que también herede el tamaño.