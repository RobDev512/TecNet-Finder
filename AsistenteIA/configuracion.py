# ============================================================
# Archivo: configuracion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo centraliza la configuración utilizada por el
# asistente local de inteligencia artificial de TecNet Finder.
#
# Mantener estos valores separados permite cambiar modelo,
# dirección o tiempos sin modificar el resto de la integración.
# ============================================================

MODELO_IA = "qwen2.5-coder:1.5b"  # Identifica el modelo local elegido para autocompletado y futuras explicaciones.
HOST_OLLAMA = "127.0.0.1"  # Mantiene el servidor privado limitado exclusivamente al equipo local.
PUERTO_OLLAMA = 11435  # Separa el Ollama propio de TecNet Finder del puerto convencional 11434.
URL_BASE_OLLAMA = f"http://{HOST_OLLAMA}:{PUERTO_OLLAMA}"  # Construye la dirección común utilizada por todas las peticiones locales.
TIEMPO_ESPERA_SEGUNDOS = 3.0  # Evita que una petición de IA pueda bloquear indefinidamente una operación.