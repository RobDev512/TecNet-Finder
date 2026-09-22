# ============================================================
# Archivo: __init__.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Expone la infraestructura de internacionalización utilizada
# por TecNet Finder.
# ============================================================

from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones  # Ofrece el punto de acceso principal al sistema de traducciones.

__all__ = ["GestorTraducciones"]  # Limita la interfaz pública inicial del paquete.
