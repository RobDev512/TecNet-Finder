# ============================================================
# Archivo: version_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Centraliza la identificación y las versiones del proyecto.
#
# La versión estable corresponde a la última entrega pública,
# mientras que la versión de desarrollo identifica los cambios
# actuales antes de publicar el siguiente instalador.
# ============================================================

NOMBRE_APLICACION = "TecNet Finder"  # Identifica el producto de forma única en todas las ventanas.
VERSION_ESTABLE = "1.2.2"  # Versión a empaquetar; publicar después de validar el instalador Windows.
VERSION_DESARROLLO = "1.2.2"  # Versión preparada dentro de la rama de estabilidad.
VERSION_ACTUAL = VERSION_DESARROLLO  # Identifica los archivos que se ejecutan durante esta actualización.
VERSION_VISIBLE = f"v{VERSION_ACTUAL}"  # Presenta la versión mediante el prefijo convencional.
NOMBRE_ACTUALIZACION = "Stability & Polish"  # Conserva la denominación del roadmap.
URL_REPOSITORIO = "https://github.com/RobDev512/TecNet-Finder"  # Enlace público del proyecto.
