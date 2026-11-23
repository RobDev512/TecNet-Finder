# ============================================================
# Archivo: version_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Centraliza la identificación y las versiones del proyecto.
#
# Identifica la candidata estable v1.3.0 para el instalador final.
# El número de desarrollo se conserva como alias compatible;
# la release pública se anunciará después de verificar el instalador.
# ============================================================

NOMBRE_APLICACION = "TecNet Finder"  # Identifica el producto de forma única en todas las ventanas.
VERSION_ESTABLE = "1.3.0"  # Identifica la candidata estable cuya instalación ya se comprobó en Windows.
VERSION_DESARROLLO = VERSION_ESTABLE  # Conserva la constante anterior para compatibilidad con otros componentes.
VERSION_ACTUAL = VERSION_ESTABLE  # Muestra la versión estable en la aplicación y en el Centro de mantenimiento.
VERSION_VISIBLE = f"v{VERSION_ACTUAL}"  # Presenta el identificador público con su prefijo convencional.
NOMBRE_ACTUALIZACION = "Código intermedio y triplos"  # Describe la función principal incluida en v1.3.0.
URL_REPOSITORIO = "https://github.com/RobDev512/TecNet-Finder"  # Conserva el enlace público del proyecto.
