# ============================================================
# Archivo: prueba_registro.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Verifica el funcionamiento básico del sistema de logs.
# Comprueba la escritura del archivo, la ausencia de manejadores
# duplicados y el registro de excepciones inesperadas.
#
# Todas las pruebas utilizan carpetas temporales de pytest.
# ============================================================

import logging  # Permite seleccionar el nivel de detalle utilizado durante una prueba.

from Motor.infraestructura.registro import configurar_registro, obtener_ruta_log  # Reutiliza la configuración y consulta de los registros reales.


# ============================================================
# Prueba de creación y escritura de eventos
# ============================================================

def prueba_crea_archivo(tmp_path):  # Confirma que se cree un archivo legible en la carpeta indicada.
    logger = configurar_registro(tmp_path)  # Prepara el registro dentro de un directorio temporal.
    logger.info("evento de prueba")  # Escribe un mensaje identificable.

    for manejador in logger.handlers:  # Recorre los manejadores configurados.
        manejador.flush()  # Garantiza que los mensajes pendientes lleguen al archivo.

    archivo = obtener_ruta_log(logger)  # Obtiene la ubicación realmente utilizada.
    assert archivo == tmp_path / "tecnet-finder.log"  # Comprueba que no se haya utilizado otra carpeta.
    assert "evento de prueba" in archivo.read_text(encoding="utf-8")  # Verifica que el mensaje quedó guardado.


# ============================================================
# Prueba de configuración repetida
# ============================================================

def prueba_no_duplica_manejadores(tmp_path):  # Impide que inicializar dos veces genere eventos repetidos.
    configurar_registro(tmp_path)  # Ejecuta una primera configuración.
    logger = configurar_registro(tmp_path)  # Vuelve a configurar el mismo logger.
    manejadores = [h for h in logger.handlers if getattr(h, "_tecnet_logger", False)]  # Filtra únicamente los manejadores propios.

    assert len(manejadores) == 1  # Debe quedar un solo manejador de archivo.
    assert logger.propagate is False  # La propagación hacia el logger raíz debe permanecer desactivada.


# ============================================================
# Prueba de excepciones registradas
# ============================================================

def prueba_registra_excepciones(tmp_path):  # Verifica que se conserve la información de una excepción.
    logger = configurar_registro(tmp_path, nivel=logging.DEBUG)  # Prepara registros con información detallada.

    try:  # Genera una excepción controlada para probar el mecanismo.
        raise ValueError("prueba controlada")  # Representa un fallo conocido de prueba.
    except ValueError:  # Recupera la excepción sin interrumpir el conjunto de pruebas.
        logger.exception("Fallo inesperado")  # Guarda el mensaje y la traza de error.

    for manejador in logger.handlers:  # Recorre los archivos asociados con el registro.
        manejador.flush()  # Completa las escrituras pendientes.

    contenido = (tmp_path / "tecnet-finder.log").read_text(encoding="utf-8")  # Recupera el archivo resultante.
    assert "Fallo inesperado" in contenido  # Comprueba el mensaje descriptivo del fallo.
    assert "ValueError: prueba controlada" in contenido  # Confirma que también se guardó el tipo de excepción.
