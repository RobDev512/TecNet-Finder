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
# varias instrucciones, las entradas deliberadamente mal
# ordenadas y la exclusión de plantillas genéricas.
# ============================================================

from Motor.ejemplos.gestor_ejemplos import GestorEjemplos  # Importa el componente real utilizado por la interfaz para leer los casos.


def prueba_carga_los_catorce_ejemplos_validos():  # Comprueba que los catorce ejemplos válidos actuales se interpreten completamente.
    gestor = GestorEjemplos()  # Utiliza directamente la carpeta Ejemplos perteneciente al proyecto.
    validos, _invalidos = gestor.cargar_ejemplos()  # Recupera ambas categorías aunque solamente se verificará la primera.

    assert len(validos) == 14  # Comprueba que los catorce casos válidos actuales hayan sido reconocidos.
    assert validos[0].titulo.startswith("CASO V1")  # Verifica que el primer título se conserve correctamente.
    assert validos[-1].titulo.startswith("CASO V14")  # Verifica que también se conserve el último caso válido agregado.
    assert validos[0].comando == "IP 192.168.1.0 MASK /24 HOSTS 50,30,10 NAME Oficina"  # Comprueba que el código original del primer caso no haya sido alterado.


def prueba_carga_los_veinticinco_ejemplos_invalidos():  # Comprueba que los veinticinco ejemplos incorrectos actuales permanezcan disponibles.
    gestor = GestorEjemplos()  # Crea una nueva instancia independiente del lector.
    _validos, invalidos = gestor.cargar_ejemplos()  # Obtiene específicamente los casos del segundo archivo.

    assert len(invalidos) == 25  # Comprueba que ninguno de los casos inválidos se pierda durante la interpretación del archivo.
    assert invalidos[0].titulo.startswith("CASO I1")  # Verifica el comienzo de la colección.
    assert invalidos[-1].titulo.startswith("CASO I25")  # Verifica que también se recupere correctamente el último caso agregado.


def prueba_conserva_varias_instrucciones_dentro_del_mismo_caso():  # Comprueba que los ejemplos multilínea no se dividan accidentalmente.
    gestor = GestorEjemplos()  # Utiliza el lector real de los archivos actuales.
    validos, invalidos = gestor.cargar_ejemplos()  # Recupera ambas categorías para comprobar ejemplos con varias líneas.

    caso_valido = next(ejemplo for ejemplo in validos if ejemplo.titulo.startswith("CASO V4"))  # Localiza el caso válido que contiene dos redes.
    caso_invalido = next(ejemplo for ejemplo in invalidos if ejemplo.titulo.startswith("CASO I11"))  # Localiza el caso inválido de recuperación parcial.

    assert len(caso_valido.comando.splitlines()) == 2  # Verifica que las dos instrucciones válidas permanezcan agrupadas.
    assert len(caso_invalido.comando.splitlines()) == 2  # Verifica que las dos instrucciones del caso inválido también permanezcan juntas.


def prueba_conserva_codigo_invalido_que_no_comienza_con_ip():  # Comprueba que los ejemplos con tokens fuera de orden lleguen realmente hasta el analizador sintáctico.
    gestor = GestorEjemplos()  # Utiliza el mismo lector empleado por la interfaz para cargar los archivos de ejemplos.
    _validos, invalidos = gestor.cargar_ejemplos()  # Recupera los casos inválidos donde se encuentra el ejemplo de recuperación sintáctica.

    caso = next(ejemplo for ejemplo in invalidos if ejemplo.titulo.startswith("CASO I24"))  # Localiza específicamente el caso que comienza incorrectamente con MASK.
    lineas = caso.comando.splitlines()  # Separa sus dos líneas para comprobar que ninguna haya sido descartada.

    assert len(lineas) == 2  # Confirma que tanto la línea incorrecta como el bloque válido posterior formen parte del mismo ejemplo.
    assert lineas[0] == "MASK /24 HOSTS 50"  # Garantiza que la línea destinada a producir SIN-008 llegue intacta al compilador.
    assert lineas[1] == "IP 10.0.0.0 MASK /24 HOSTS 20 NAME Segunda"  # Garantiza que también se conserve la instrucción posterior utilizada para comprobar recuperación.


def prueba_ignora_plantillas_con_marcadores_genericos():  # Comprueba que las expresiones explicativas no se inserten como código real.
    gestor = GestorEjemplos()  # Crea un gestor que utilizará directamente el analizador de texto.

    texto = (
        "# CASO 1\n"
        "IP <IP_ADDRESS> MASK <SUBNET_MASK> HOSTS <NUMBER>\n"
        "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
        "Salida esperada: caso válido.\n"
    )  # Construye un contenido mínimo que mezcla una plantilla y una instrucción ejecutable.

    ejemplos = gestor.analizar_texto(texto, "Válida")  # Interpreta el contenido con la misma lógica utilizada por los archivos reales.

    assert len(ejemplos) == 1  # Comprueba que solamente se haya generado un ejemplo real.
    assert ejemplos[0].comando == "IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina"  # Comprueba que la plantilla genérica haya sido descartada.