# ============================================================
# Archivo: prueba_traducciones_mantenimiento.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Comprueba que los seis idiomas incluyan los textos del
# mantenimiento y de las nuevas ayudas del visor de triplos.
# ============================================================

import json  # Permite leer los catálogos tal como se entregan junto al ejecutable.
from pathlib import Path  # Localiza los archivos sin depender del directorio de ejecución.


RAIZ = Path(__file__).resolve().parents[2]  # Obtiene la carpeta principal del proyecto.
IDIOMAS = ("es", "en", "pt", "fr", "de", "la")  # Revisa todos los idiomas oficiales de la aplicación.
CLAVES = (
    "mantenimiento.titulo", "mantenimiento.subtitulo", "mantenimiento.pestana.informacion",
    "mantenimiento.pestana.registros", "mantenimiento.cerrar", "mantenimiento.estado.titulo",
    "mantenimiento.estado.valor", "mantenimiento.estado.descripcion", "mantenimiento.version.titulo",
    "mantenimiento.actualizacion.titulo", "mantenimiento.actualizacion.descripcion", "acerca.titulo",
    "acerca.descripcion", "acerca.version_estable", "acerca.materia", "acerca.tecnologias",
    "acerca.abrir_repositorio", "acerca.copiar_version", "mantenimiento.registros.titulo",
    "mantenimiento.registros.descripcion", "mantenimiento.registros.buscar",
    "mantenimiento.registros.todos_niveles", "mantenimiento.registros.fecha",
    "mantenimiento.registros.nivel", "mantenimiento.registros.origen", "mantenimiento.registros.mensaje",
    "mantenimiento.registros.copiar_evento", "mantenimiento.registros.ruta_vacia",
    "mantenimiento.registros.error_lectura", "mantenimiento.registros.eventos",
    "mantenimiento.registros.sin_resultados", "mantenimiento.registros.error_abrir",
    "mantenimiento.registros.actualizar", "mantenimiento.registros.copiar", "mantenimiento.registros.abrir",
    "resultados.triplos.ayuda.iniciar_red", "resultados.triplos.ayuda.solicitud",
    "resultados.triplos.ayuda.asignar_vlsm", "resultados.triplos.ayuda.siguiente_cursor",
)  # Enumera las claves utilizadas por los controles nuevos y la ventana de mantenimiento.


def prueba_catalogos_mantenimiento_completos():
    for idioma in IDIOMAS:  # Examina las mismas seis traducciones cargadas por la aplicación.
        ruta = RAIZ / "Recursos" / "Idiomas" / f"{idioma}.json"  # Encuentra el catálogo correspondiente.
        catalogo = json.loads(ruta.read_text(encoding="utf-8-sig"))  # Comprueba también que el JSON sea válido.
        for clave in CLAVES:  # Evita mostrar identificadores entre corchetes en la interfaz.
            assert isinstance(catalogo.get(clave), str) and catalogo[clave].strip(), (idioma, clave)
        assert "{cantidad}" in catalogo["mantenimiento.registros.eventos"]  # Mantiene el contador de registros.
        assert "{error}" in catalogo["mantenimiento.registros.error_lectura"]  # Mantiene la descripción de errores.
        assert "pila" not in catalogo["resultados.triplos.comprobacion"].lower() if idioma == "es" else True  # Utiliza el nuevo encabezado.


def prueba_version_en_desarrollo_separada_de_la_estable():
    from Motor.configuracion.version_aplicacion import VERSION_DESARROLLO, VERSION_ESTABLE, VERSION_VISIBLE  # Consulta la identificación central.
    assert VERSION_ESTABLE == "1.2.2"  # Conserva intacta la versión pública mientras no se libere v1.3.0.
    assert VERSION_DESARROLLO == "1.3.0"  # Identifica correctamente la fase de triplos en pruebas.
    assert VERSION_VISIBLE == "v1.3.0"  # Utiliza la versión de desarrollo en la ventana de mantenimiento.
