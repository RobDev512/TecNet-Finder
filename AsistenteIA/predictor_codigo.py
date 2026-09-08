# ============================================================
# Archivo: predictor_codigo.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo convierte una línea incompleta de TecNet Finder
# en una petición especializada de autocompletado para la IA.
#
# El modelo solamente propone una línea completa. Antes de aceptar
# cualquier propuesta, el lexer y parser reales comprueban que
# pertenezca al lenguaje formal actualmente implementado.
# ============================================================

from AsistenteIA.motor_local import MotorLocalOllama  # Importa el componente responsable de obtener propuestas del modelo local.
from Compilador.analizador_lexico import AnalizadorLexico  # Importa el lexer formal para impedir que la IA introduzca elementos fuera del lenguaje.
from Compilador.analizador_sintactico import AnalizadorSintactico  # Importa el parser formal encargado de validar la estructura propuesta.


class PredictorCodigo:  # Genera sugerencias sin otorgar ninguna autoridad formal al modelo de IA.
    def __init__(self, motor: MotorLocalOllama | None = None):  # Permite inyectar un motor alternativo durante pruebas automatizadas.
        self.motor = motor or MotorLocalOllama()  # Utiliza el Ollama privado cuando no se suministra otra implementación.

    def sugerir(self, prefijo: str) -> str | None:  # Devuelve únicamente el texto faltante que podría mostrarse como ghost text.
        prefijo = prefijo.rstrip("\r\n")  # Conserva espacios significativos pero elimina únicamente saltos de línea externos.

        if not prefijo.strip():
            return None  # Evita solicitar sugerencias cuando todavía no existe ninguna entrada útil.

        prompt = self._construir_prompt(prefijo)  # Proporciona al modelo gramática, ejemplos y la línea exacta escrita por el usuario.
        respuesta = self.motor.generar(prompt, maximo_tokens=48)  # Solicita una propuesta breve para minimizar latencia.

        if respuesta is None:
            return None  # Mantiene el autocompletado silenciosamente inactivo si el motor no está disponible.

        linea_completa = self._extraer_linea(respuesta)  # Elimina formatos conversacionales que el modelo pudiera agregar.

        if not linea_completa.startswith(prefijo):
            return None  # Rechaza cualquier respuesta que modifique lo que el usuario ya escribió.

        sugerencia = linea_completa[len(prefijo):]  # Conserva exclusivamente la continuación todavía no escrita.

        if not sugerencia:
            return None  # Evita mostrar un ghost text vacío.

        if not self._linea_valida(linea_completa):
            return None  # Impide mostrar propuestas que los analizadores formales rechacen.

        return sugerencia  # Devuelve únicamente texto previamente comprobado por lexer y parser.

    def _construir_prompt(self, prefijo: str) -> str:  # Describe el pequeño DSL mediante reglas y ejemplos suficientes para orientar un modelo compacto.
        return (
            "Eres el motor de autocompletado de un lenguaje llamado TecNet Finder.\n"
            "Debes devolver UNA SOLA LINEA COMPLETA y nada más.\n"
            "No uses Markdown, explicaciones, comillas ni comentarios.\n"
            "Debes conservar EXACTAMENTE el texto ya escrito al inicio.\n\n"
            "GRAMATICA:\n"
            "IP <IPv4> MASK /<CIDR> HOSTS <numero>[,<numero>...] [NAME <identificador>]\n\n"
            "REGLAS:\n"
            "- Las palabras reservadas son exactamente IP, MASK, HOSTS y NAME.\n"
            "- IPv4 tiene cuatro octetos entre 0 y 255.\n"
            "- CIDR se escribe con diagonal, por ejemplo /24.\n"
            "- HOSTS contiene uno o más números enteros separados por comas.\n"
            "- NAME es opcional y recibe un identificador sin espacios.\n\n"
            "EJEMPLOS:\n"
            "Entrada: IP 192.168.1.0 MASK /24 HOSTS\n"
            "Salida: IP 192.168.1.0 MASK /24 HOSTS 50 NAME Oficina\n"
            "Entrada: IP 10.0.0.0 MASK\n"
            "Salida: IP 10.0.0.0 MASK /24 HOSTS 20 NAME Laboratorio\n"
            "Entrada: IP 172.16.0.0 MASK /24 HOSTS 100,50 NAME\n"
            "Salida: IP 172.16.0.0 MASK /24 HOSTS 100,50 NAME Sucursal\n"
            "Entrada: IP 192.168.10.0 MAS\n"
            "Salida: IP 192.168.10.0 MASK /24 HOSTS 30 NAME Oficina\n\n"
            f"Entrada: {prefijo}\n"
            "Salida:"
        )  # Utiliza ejemplos del propio lenguaje para reducir respuestas genéricas de redes como la observada durante la primera prueba.

    def _extraer_linea(self, respuesta: str) -> str:  # Reduce una respuesta potencialmente conversacional a la primera línea candidata.
        texto = respuesta.strip()  # Elimina espacios externos producidos por el modelo.

        if texto.startswith("```"):
            lineas = texto.splitlines()  # Divide un posible bloque Markdown para retirar sus delimitadores.

            if lineas and lineas[0].startswith("```"):
                lineas = lineas[1:]

            if lineas and lineas[-1].strip() == "```":
                lineas = lineas[:-1]

            texto = "\n".join(lineas).strip()

        if texto.lower().startswith("salida:"):
            texto = texto.split(":", 1)[1].strip()  # Tolera que el modelo repita accidentalmente la etiqueta del ejemplo.

        return texto.splitlines()[0].strip() if texto else ""  # Mantiene solamente una instrucción porque el ghost text actual operará por línea.

    def _linea_valida(self, linea: str) -> bool:  # Confirma la propuesta utilizando exclusivamente las fases formales existentes.
        resultado_lexico = AnalizadorLexico().analizar(linea)  # Convierte la propuesta en tokens mediante el lexer real del proyecto.

        if resultado_lexico.tiene_errores:
            return False  # Rechaza inmediatamente cualquier símbolo o palabra que no pertenezca al lenguaje.

        resultado_sintactico = AnalizadorSintactico(resultado_lexico.tokens).analizar()  # Comprueba el orden completo utilizando la gramática oficial actual.

        if resultado_sintactico.tiene_errores:
            return False  # Impide que una generación gramaticalmente incorrecta llegue a la interfaz.

        return len(resultado_sintactico.bloques) == 1  # Exige exactamente una instrucción válida para el autocompletado de una línea.