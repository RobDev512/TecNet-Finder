# ============================================================
# Archivo: resaltador_sintaxis.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo contiene el resaltador de sintaxis del editor de
# TecNet Finder.
#
# Su función es modificar únicamente la apariencia del código
# fuente para distinguir palabras reservadas, direcciones IP,
# máscaras, números y otros elementos del lenguaje.
#
# El resaltado no realiza análisis léxico ni sintáctico real.
# ============================================================

from PySide6.QtCore import QRegularExpression  # Importa las expresiones regulares utilizadas para localizar texto dentro de cada línea.
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat  # Importa las clases necesarias para colorear fragmentos del documento.


class ResaltadorSintaxis(QSyntaxHighlighter):  # Define el resaltador visual utilizado por el editor de código.
    def __init__(self, documento):  # Inicializa el resaltador sobre el documento perteneciente al editor.
        super().__init__(documento)  # Entrega el documento a QSyntaxHighlighter para que pueda procesar sus bloques.
        self.reglas = []  # Crea la lista que relacionará expresiones regulares con formatos visuales.

        formato_reservada = QTextCharFormat()  # Crea el formato utilizado para las palabras reservadas del DSL.
        formato_reservada.setForeground(QColor("#89b4fa"))  # Asigna un tono azul a IP, MASK, HOSTS y NAME.
        formato_reservada.setFontWeight(QFont.Weight.Bold)  # Muestra las palabras reservadas con mayor grosor.

        formato_ip = QTextCharFormat()  # Crea el formato visual utilizado para direcciones IPv4.
        formato_ip.setForeground(QColor("#a6e3a1"))  # Asigna un tono verde a las direcciones IP.

        formato_mascara = QTextCharFormat()  # Crea el formato utilizado para las máscaras CIDR.
        formato_mascara.setForeground(QColor("#cba6f7"))  # Asigna un tono violeta a valores como /24.

        formato_numero = QTextCharFormat()  # Crea el formato utilizado para cantidades numéricas.
        formato_numero.setForeground(QColor("#fab387"))  # Asigna un tono naranja a los números de hosts.

        formato_coma = QTextCharFormat()  # Crea el formato utilizado para las comas de HOSTS.
        formato_coma.setForeground(QColor("#f9e2af"))  # Asigna un tono amarillo al separador de cantidades.

        octeto = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"  # Define la misma forma general utilizada para reconocer octetos IPv4.
        direccion_ip = rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b"  # Construye el patrón completo de una dirección IPv4.

        self.reglas.extend([  # Registra las reglas visuales en el orden en que serán aplicadas.
            (QRegularExpression(r"\b(?:IP|MASK|HOSTS|NAME)\b"), formato_reservada),  # Resalta las palabras reservadas principales.
            (QRegularExpression(direccion_ip), formato_ip),  # Resalta las direcciones IPv4 completas.
            (QRegularExpression(r"/\d+"), formato_mascara),  # Resalta máscaras escritas en notación CIDR.
            (QRegularExpression(r"\b\d+\b"), formato_numero),  # Resalta cantidades numéricas individuales.
            (QRegularExpression(r","), formato_coma),  # Resalta las comas utilizadas dentro de HOSTS.
        ])

    def highlightBlock(self, texto: str) -> None:  # Aplica todas las reglas visuales al bloque de texto que PySide6 está procesando.
        for expresion, formato in self.reglas:  # Recorre cada expresión regular junto con su formato correspondiente.
            iterador = expresion.globalMatch(texto)  # Busca todas las coincidencias de la regla dentro de la línea actual.

            while iterador.hasNext():  # Continúa mientras todavía exista otra coincidencia de la misma expresión.
                coincidencia = iterador.next()  # Obtiene la siguiente coincidencia encontrada.
                inicio = coincidencia.capturedStart()  # Obtiene la posición donde comienza el fragmento reconocido.
                longitud = coincidencia.capturedLength()  # Obtiene cuántos caracteres ocupa el fragmento reconocido.
                self.setFormat(inicio, longitud, formato)  # Aplica el formato visual solamente al fragmento encontrado.