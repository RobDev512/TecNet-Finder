# ============================================================
# Archivo: resaltador_sintaxis.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Contiene el resaltador visual del editor de TecNet Finder.
#
# Recupera la identidad cromática de TecNet Finder OG:
# - IP: azul.
# - MASK: verde.
# - HOSTS y NUMBER: naranja.
# - NAME: amarillo/dorado.
# - IP_ADDRESS: turquesa.
# - SUBNET_MASK: violeta.
# - COMMA: rosa/rojo.
#
# En temas claros utiliza equivalentes más oscuros para conservar
# contraste sin perder el significado visual original.
# ============================================================

from PySide6.QtCore import QRegularExpression  # Proporciona las expresiones regulares utilizadas exclusivamente para localizar fragmentos visuales.
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat  # Proporciona formatos y resaltado del documento.
from Motor.configuracion.catalogo_temas import MODO_CLARO, TEMA_PREDETERMINADO, modo_del_tema  # Permite conservar la identidad OG con contraste apropiado para cada modo.


class ResaltadorSintaxis(QSyntaxHighlighter):  # Define el resaltador visual asociado con el documento del editor.
    COLORES_OSCUROS = {"IP": "#89b4fa", "MASK": "#a6e3a1", "HOSTS": "#fab387", "NAME": "#f9e2af", "IP_ADDRESS": "#94e2d5", "SUBNET_MASK": "#cba6f7", "NUMBER": "#fab387", "COMMA": "#f38ba8"}  # Recupera exactamente la identidad cromática de TecNet Finder OG.
    COLORES_CLAROS = {"IP": "#2563eb", "MASK": "#287a3d", "HOSTS": "#b45309", "NAME": "#946200", "IP_ADDRESS": "#0f766e", "SUBNET_MASK": "#7c3aed", "NUMBER": "#b45309", "COMMA": "#c42b1c"}  # Mantiene los mismos roles mediante tonos legibles sobre fondos claros.

    def __init__(self, documento):
        super().__init__(documento)  # Entrega el documento a QSyntaxHighlighter.
        self.reglas: list[tuple[QRegularExpression, QTextCharFormat]] = []  # Conserva las reglas visuales vigentes.
        octeto = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"  # Define la forma admitida para cada octeto IPv4.
        self.expresion_ip = QRegularExpression(rf"\b{octeto}\.{octeto}\.{octeto}\.{octeto}\b")  # Construye una dirección IPv4 completa.
        self.aplicar_tema(TEMA_PREDETERMINADO)  # Inicializa el resaltado antes de que el gestor aplique la preferencia real.

    def _crear_formato(self, color: str, negrita: bool = False) -> QTextCharFormat:
        formato = QTextCharFormat()  # Crea un formato independiente para evitar compartir estados entre reglas.
        formato.setForeground(QColor(color))  # Aplica el tono correspondiente con el token.
        if negrita: formato.setFontWeight(QFont.Weight.Bold)  # Refuerza únicamente los elementos que TecNet Finder OG mostraba en negrita.
        return formato  # Entrega el formato completamente preparado.

    def aplicar_tema(self, tema_id: str) -> None:
        colores = self.COLORES_CLAROS if modo_del_tema(tema_id) == MODO_CLARO else self.COLORES_OSCUROS  # Conserva la identidad original adaptando solamente el contraste del modo claro.
        self.reglas = [
            (QRegularExpression(r","), self._crear_formato(colores["COMMA"], True)),  # Aplica primero la regla general de las comas, igual que TecNet Finder OG.
            (QRegularExpression(r"\b\d+\b"), self._crear_formato(colores["NUMBER"])),  # Aplica después NUMBER para cantidades de hosts.
            (self.expresion_ip, self._crear_formato(colores["IP_ADDRESS"], True)),  # Sobrescribe NUMBER cuando los números forman una dirección IPv4 completa.
            (QRegularExpression(r"/\d+"), self._crear_formato(colores["SUBNET_MASK"], True)),  # Sobrescribe NUMBER dentro de máscaras CIDR como /24.
            (QRegularExpression(r"\bIP(?=\s|\d|$)"), self._crear_formato(colores["IP"], True)),  # Recupera el azul histórico de la palabra reservada IP.
            (QRegularExpression(r"\bMASK(?=\s|/|$)"), self._crear_formato(colores["MASK"], True)),  # Recupera el verde histórico de MASK.
            (QRegularExpression(r"\bHOSTS(?=\s|\d|,|$)"), self._crear_formato(colores["HOSTS"], True)),  # Recupera el naranja histórico de HOSTS.
            (QRegularExpression(r"\bNAME\b"), self._crear_formato(colores["NAME"], True)),  # Recupera el amarillo/dorado histórico de NAME.
        ]  # Mantiene las reglas específicas después de las generales para que puedan sobrescribirlas visualmente.
        self.rehighlight()  # Vuelve a colorear inmediatamente el documento ya escrito.

    def highlightBlock(self, texto: str) -> None:
        for expresion, formato in self.reglas:  # Recorre las reglas respetando el orden de precedencia visual.
            iterador = expresion.globalMatch(texto)  # Busca todas las coincidencias dentro de la línea actual.
            while iterador.hasNext():
                coincidencia = iterador.next()  # Recupera la coincidencia siguiente.
                inicio, longitud = coincidencia.capturedStart(), coincidencia.capturedLength()  # Obtiene posición y longitud del fragmento.
                if inicio >= 0 and longitud > 0: self.setFormat(inicio, longitud, formato)  # Aplica el formato solamente cuando la coincidencia es válida.
