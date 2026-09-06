# ============================================================
# Archivo: flujo_compilacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo coordina las diferentes partes de TecNet Finder
# sin implementar directamente ninguna fase del compilador.
#
# Actualmente ejecuta el análisis léxico, el análisis sintáctico
# y el cálculo VLSM de los bloques aceptados.
#
# Conforme avance Lenguajes y Autómatas II, este mismo flujo
# incorporará análisis semántico, código intermedio,
# optimización y generación de código objeto.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa la primera fase encargada de convertir el código fuente en tokens.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa la fase que comprueba el orden gramatical de los tokens.
from Motor.modelos import ResultadoCompilacion  # Importa el modelo que reunirá todos los resultados obtenidos durante el flujo.
from Redes.calculadora_vlsm import calcular_vlsm  # Importa la función de dominio encargada de calcular las subredes VLSM.


class FlujoCompilacion:  # Coordina las fases disponibles sin colocar su lógica dentro de la interfaz gráfica.
    def analizar(self, codigo_fuente: str) -> ResultadoCompilacion:  # Ejecuta ordenadamente todas las etapas actualmente reconstruidas.
        analizador_lexico = AnalizadorLexico()  # Crea una nueva instancia del lexer para analizar el código fuente recibido.
        resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Obtiene los tokens y diagnósticos generados durante la fase léxica.

        analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Crea el parser utilizando únicamente los tokens reconocidos por el lexer.
        resultado_sintactico = analizador_sintactico.analizar()  # Obtiene bloques válidos, diagnósticos, árboles, producciones y derivación.

        subredes_vlsm = []  # Crea la lista donde se reunirán las subredes calculadas para todos los bloques sintácticamente válidos.

        for bloque in resultado_sintactico.bloques:  # Recorre únicamente las instrucciones que lograron cumplir la gramática actual.
            resultados_bloque = calcular_vlsm(  # Ejecuta el cálculo VLSM utilizando los datos almacenados en el bloque actual.
                direccion_ip=bloque.direccion_ip,  # Envía la dirección IPv4 reconocida después de IP.
                mascara_subred=bloque.mascara_subred,  # Envía la máscara CIDR reconocida después de MASK.
                cantidades_hosts=bloque.cantidades_hosts,  # Envía todas las cantidades solicitadas después de HOSTS.
                nombre_red=bloque.nombre,  # Envía el nombre opcional de la red cuando la instrucción utilizó NAME.
            )

            subredes_vlsm.extend(resultados_bloque)  # Agrega las subredes del bloque actual a la lista general del programa.

        return ResultadoCompilacion(  # Construye un único resultado que podrá utilizar posteriormente la interfaz.
            resultado_lexico=resultado_lexico,  # Conserva toda la información producida por el lexer.
            resultado_sintactico=resultado_sintactico,  # Conserva toda la información producida por el parser.
            subredes_vlsm=subredes_vlsm,  # Conserva todas las subredes calculadas para los bloques aceptados.
        )