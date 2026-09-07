# ============================================================
# Archivo: prueba_gestor_ejemplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo comprueba la lectura e interpretación de los
# archivos utilizados por el selector de ejemplos.
#
# Las pruebas verifican las cantidades actuales, los casos con
# varias instrucciones y la exclusión de plantillas genéricas.
# ============================================================

from Motor.gestor_ejemplos import GestorEjemplos  # Importa el componente real utilizado por la interfaz para leer los casos.


def prueba_carga_los_doce_ejemplos_validos():  # Comprueba que el archivo válido actual se interprete completamente.
    gestor = GestorEjemplos()  # Utiliza directamente la carpeta Ejemplos perteneciente al proyecto.
    validos, _invalidos = gestor.cargar_ejemplos()  # Recupera ambas categorías aunque solamente se verificará la primera.

    assert len(validos) == 12  # Comprueba que los doce casos actuales hayan sido reconocidos.
    assert validos[0].titulo.startswith("CASO V1")  # Verifica que el primer título se conserve correctamente.
    assert validos[0].comando == "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Comprueba que el código no haya sido alterado.


def prueba_carga_los_veinte_ejemplos_invalidos():  # Comprueba que todos los casos incorrectos actuales permanezcan disponibles.
    gestor = GestorEjemplos()  # Crea una nueva instancia independiente del lector.
    _validos, invalidos = gestor.cargar_ejemplos()  # Obtiene específicamente los casos del segundo archivo.

    assert len(invalidos) == 20  # Comprueba que ninguna entrada inválida se pierda durante el análisis del texto.
    assert invalidos[0].titulo.startswith("CASO I1")  # Verifica el comienzo de la colección.
    assert invalidos[-1].titulo.startswith("CASO I20")  # Verifica también que el último caso haya sido recuperado.


def prueba_conserva_varias_instrucciones_dentro_del_mismo_caso():  # Comprueba que un ejemplo multilinea no se divida accidentalmente en casos independientes.
    gestor = GestorEjemplos()  # Utiliza el lector real de los archivos actuales.
    validos, invalidos = gestor.cargar_ejemplos()  # Recupera ambas categorías para comprobar ejemplos multilinea.

    caso_valido = next(ejemplo for ejemplo in validos if ejemplo.titulo.startswith("CASO V4"))  # Localiza el caso válido que contiene dos redes.
    caso_invalido = next(ejemplo for ejemplo in invalidos if ejemplo.titulo.startswith("CASO I11"))  # Localiza el caso incorrecto formado por dos instrucciones.

    assert len(caso_valido.comando.splitlines()) == 2  # Verifica que las dos instrucciones válidas permanezcan agrupadas.
    assert len(caso_invalido.comando.splitlines()) == 2  # Verifica que el caso de procesamiento parcial conserve también ambas líneas.


def prueba_ignora_plantillas_con_marcadores_genericos():  # Comprueba que expresiones explicativas con símbolos menor y mayor no se inserten como código real.
    gestor = GestorEjemplos()  # Crea un gestor que utilizará directamente el analizador de texto.
    texto = (  # Construye un contenido mínimo que mezcla una plantilla y una instrucción ejecutable.
        "# CASO 1\n"
        "IP <IP_ADDRESS> MASK <SUBNET_MASK> HOSTS <NUMBER>\n"
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "Salida esperada: caso válido.\n"
    )

    ejemplos = gestor.analizar_texto(texto, "Válida")  # Interpreta el texto mediante la misma lógica utilizada por los archivos reales.

    assert len(ejemplos) == 1  # Comprueba que solamente se haya generado un registro real.
    assert ejemplos[0].comando == "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"  # Verifica que la plantilla genérica haya sido descartada.