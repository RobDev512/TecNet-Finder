# ============================================================
# Archivo: flujo_compilacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo coordina las diferentes partes de TecNet Finder
# sin implementar directamente ninguna fase del compilador.
#
# Actualmente ejecuta análisis léxico, análisis sintáctico,
# advertencias no bloqueantes y cálculo VLSM.
#
# Conforme avance Lenguajes y Autómatas II, este mismo flujo
# incorporará análisis semántico, código intermedio,
# optimización y generación de código objeto.
# ============================================================

from Compilador.analizador_lexico import AnalizadorLexico  # Importa la primera fase encargada de convertir el código fuente en tokens.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa la fase que comprueba el orden gramatical de los tokens.
from Motor.advertencias import generar_advertencias  # Importa las recomendaciones no bloqueantes separadas de las fases formales.
from Motor.modelos import ResultadoCompilacion  # Importa el modelo que reunirá todos los resultados obtenidos durante el flujo.
from Redes.calculadora_vlsm import calcular_vlsm  # Importa la función de dominio encargada de calcular las subredes VLSM.


class FlujoCompilacion:  # Coordina las fases disponibles sin colocar su lógica dentro de la interfaz gráfica.
    def analizar(self, codigo_fuente: str) -> ResultadoCompilacion:  # Ejecuta ordenadamente todas las etapas actualmente reconstruidas.
        analizador_lexico = AnalizadorLexico()  # Crea una nueva instancia del lexer para analizar el código fuente recibido.
        resultado_lexico = analizador_lexico.analizar(codigo_fuente)  # Obtiene los tokens y diagnósticos generados durante la fase léxica.

        analizador_sintactico = AnalizadorSintactico(resultado_lexico.tokens)  # Crea el parser utilizando únicamente los tokens reconocidos por el lexer.
        resultado_sintactico = analizador_sintactico.analizar()  # Obtiene bloques válidos, diagnósticos, árboles, producciones y derivación.

        advertencias = generar_advertencias(  # Genera recomendaciones sin alterar la aceptación de ningún bloque.
            codigo_fuente=codigo_fuente,
            resultado_lexico=resultado_lexico,
            resultado_sintactico=resultado_sintactico,
        )

        subredes_vlsm = []  # Crea la lista donde se reunirán las subredes calculadas para todos los bloques sintácticamente válidos.

        for bloque in resultado_sintactico.bloques:  # Recorre únicamente las instrucciones que lograron cumplir la gramática actual.
            resultados_bloque = calcular_vlsm(
                direccion_ip=bloque.direccion_ip,
                mascara_subred=bloque.mascara_subred,
                cantidades_hosts=bloque.cantidades_hosts,
                nombre_red=bloque.nombre,
            )

            subredes_vlsm.extend(resultados_bloque)  # Agrega las subredes del bloque actual a la lista general del programa.

        return ResultadoCompilacion(
            resultado_lexico=resultado_lexico,
            resultado_sintactico=resultado_sintactico,
            subredes_vlsm=subredes_vlsm,
            advertencias=advertencias,
        )