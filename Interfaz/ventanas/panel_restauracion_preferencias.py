# ============================================================
# Archivo: panel_restauracion_preferencias.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Presenta la restauración dentro de Configuración, sección
# Datos y preferencias, utilizando la casilla oficial del tema.
# Conserva los seis idiomas, confirmación y respaldos existentes.
# ============================================================

from pathlib import Path  # Construye rutas para los diálogos de importación y exportación.
from PySide6.QtCore import Qt  # Proporciona el cursor interactivo para el botón de restauración.
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget  # Construye el panel con controles de Configuración.

from Interfaz.configuracion.boton_casilla_configuracion import BotonCasillaConfiguracion  # Reutiliza el diseño de casillas de Configuración.
from Motor.configuracion.catalogo_temas import obtener_tema  # Recupera los colores de cada tema para el botón de restauración.
from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Recupera el idioma del usuario.
from Motor.configuracion.preferencias_tema import PreferenciasTema  # Consulta el tema confirmado de TecNet Finder.
from Motor.configuracion.restaurador_preferencias import restaurar_preferencias  # Reutiliza la restauración probada.
from Motor.configuracion.transferencia_preferencias import exportar_preferencias, importar_preferencias, inspeccionar_preferencias  # Exporta e importa datos validados sin modificar registros.


TEXTOS = {  # Mantiene disponibles los seis idiomas sin alterar las palabras reservadas del DSL.
    "es": {
        "titulo": "Restaurar valores predeterminados", "descripcion": "Restablece apariencia, editor, ventanas y advertencias. No borra registros, ejemplos ni modelos de IA.",
        "incluir": "Incluir preferencias de IA", "boton": "Restaurar predeterminados",
        "confirmar": "¿Restaurar las preferencias generales, visuales y de advertencias? Se guardará un respaldo. Todos los cambios se aplicarán al reiniciar TecNet Finder.",
        "confirmar_ia": "¿Restaurar también las preferencias de IA? La IA volverá a sus valores iniciales y podría activarse al reiniciar. Se guardará un respaldo.",
        "correcto": "Preferencias restauradas. Cierra y vuelve a abrir TecNet Finder para aplicar completamente los valores predeterminados.",
        "respaldo": "Respaldo guardado en:", "fallo": "No fue posible completar la restauración. No se continuó con los cambios:\n",
    },
    "en": {
        "titulo": "Restore default settings", "descripcion": "Resets appearance, editor, windows and warnings. Logs, examples and AI models are preserved.",
        "incluir": "Include AI preferences", "boton": "Restore defaults",
        "confirmar": "Restore general, visual and warning settings? A backup will be created. All changes will take effect after restarting TecNet Finder.",
        "confirmar_ia": "Also reset AI preferences? AI will return to its initial settings and may become enabled on restart. A backup will be created.",
        "correcto": "Settings restored. Close and reopen TecNet Finder to fully apply the defaults.",
        "respaldo": "Backup saved at:", "fallo": "Could not restore settings. The changes were not completed:\n",
    },
    "pt": {
        "titulo": "Restaurar configurações padrão", "descripcion": "Restaura aparência, editor, janelas e avisos. Preserva registros, exemplos e modelos de IA.",
        "incluir": "Incluir preferências de IA", "boton": "Restaurar padrões",
        "confirmar": "Restaurar as preferências gerais, visuais e de avisos? Será criado um backup. Reinicie o TecNet Finder para aplicar todas as alterações.",
        "confirmar_ia": "Restaurar também as preferências de IA? A IA voltará às configurações iniciais e poderá ser ativada ao reiniciar. Será criado um backup.",
        "correcto": "Preferências restauradas. Feche e abra novamente o TecNet Finder para aplicar os padrões.",
        "respaldo": "Backup salvo em:", "fallo": "Não foi possível restaurar as preferências:\n",
    },
    "fr": {
        "titulo": "Rétablir les paramètres par défaut", "descripcion": "Réinitialise l’apparence, l’éditeur, les fenêtres et les avertissements. Les journaux, exemples et modèles d’IA sont conservés.",
        "incluir": "Inclure les préférences d’IA", "boton": "Rétablir les paramètres",
        "confirmar": "Rétablir les préférences générales, visuelles et d’avertissement ? Une sauvegarde sera créée. Redémarrez TecNet Finder pour appliquer tous les changements.",
        "confirmar_ia": "Rétablir aussi les préférences d’IA ? L’IA retrouvera ses valeurs initiales et pourra être activée au redémarrage. Une sauvegarde sera créée.",
        "correcto": "Préférences rétablies. Fermez et rouvrez TecNet Finder pour appliquer les valeurs par défaut.",
        "respaldo": "Sauvegarde enregistrée dans :", "fallo": "Impossible de rétablir les préférences :\n",
    },
    "de": {
        "titulo": "Standardeinstellungen wiederherstellen", "descripcion": "Setzt Darstellung, Editor, Fenster und Warnungen zurück. Protokolle, Beispiele und KI-Modelle bleiben erhalten.",
        "incluir": "KI-Einstellungen einbeziehen", "boton": "Standards wiederherstellen",
        "confirmar": "Allgemeine, visuelle und Warnungseinstellungen zurücksetzen? Eine Sicherung wird erstellt. Starten Sie TecNet Finder anschließend neu.",
        "confirmar_ia": "Auch KI-Einstellungen zurücksetzen? Die KI kehrt zu den Anfangswerten zurück und kann nach einem Neustart aktiv sein. Eine Sicherung wird erstellt.",
        "correcto": "Einstellungen zurückgesetzt. Schließen und öffnen Sie TecNet Finder erneut, damit alle Änderungen gelten.",
        "respaldo": "Sicherung gespeichert unter:", "fallo": "Einstellungen konnten nicht zurückgesetzt werden:\n",
    },
    "la": {
        "titulo": "Praeferentias pristinas restitue", "descripcion": "Speciem, editorem, fenestras et monita restituit. Acta, exempla et exemplaria IA servantur.",
        "incluir": "Praeferentias IA includere", "boton": "Praeferentias restitue",
        "confirmar": "Visne praeferentias generales, aspectus et monita restituere? Exemplar servabitur. TecNet Finder denuo aperiendum erit.",
        "confirmar_ia": "Visne etiam praeferentias IA restituere? IA ad statum initialem redibit et post initium activari poterit. Exemplar servabitur.",
        "correcto": "Praeferentiae restitutae sunt. TecNet Finder claude ac rursus aperi ut mutationes perficiantur.",
        "respaldo": "Exemplar servatum est in:", "fallo": "Praeferentiae restitui non potuerunt:\n",
    },
}


# ============================================================
# Confirmaciones localizadas (Sí / No)
# ============================================================

ETIQUETAS_CONFIRMACION = {  # Evita que Qt muestre Yes y No cuando Windows usa otra configuración regional.
    "es": ("Sí", "No"),  # Mantiene las confirmaciones en español.
    "en": ("Yes", "No"),  # Conserva los textos ingleses al seleccionar inglés.
    "pt": ("Sim", "Não"),  # Traduce ambos botones al portugués.
    "fr": ("Oui", "Non"),  # Utiliza las acciones francesas.
    "de": ("Ja", "Nein"),  # Utiliza las acciones alemanas.
    "la": ("Ita", "Non"),  # Presenta las respuestas en latín.
}


# ============================================================
# Textos específicos de Datos y preferencias
# ============================================================

SECCION_DATOS = {
    "es": ("Datos y preferencias", "Administra la configuración personal de TecNet Finder.", "La restauración es una acción independiente de Aplicar y Aceptar.", "Se descartarán los cambios de Configuración que todavía no hayas aplicado."),
    "en": ("Data and preferences", "Manage your TecNet Finder personal settings.", "Restore is independent of Apply and OK.", "Any pending settings changes will be discarded."),
    "pt": ("Dados e preferências", "Gerencie as configurações pessoais do TecNet Finder.", "A restauração é independente de Aplicar e Aceitar.", "As alterações pendentes serão descartadas."),
    "fr": ("Données et préférences", "Gérez les paramètres personnels de TecNet Finder.", "La restauration est indépendante des boutons Appliquer et Valider.", "Les modifications non enregistrées seront abandonnées."),
    "de": ("Daten und Einstellungen", "Verwalten Sie Ihre persönlichen TecNet-Finder-Einstellungen.", "Die Wiederherstellung funktioniert unabhängig von Übernehmen und OK.", "Nicht gespeicherte Änderungen werden verworfen."),
    "la": ("Data et praeferentiae", "Praeferentias personales TecNet Finder administra.", "Restitutio a confirmatione mutationum separata est.", "Mutationes nondum confirmatae omittentur."),
}

for codigo, (seccion, explicacion, nota, pendientes) in SECCION_DATOS.items():  # Extiende los textos existentes sin alterar sus mensajes de respaldo.
    TEXTOS[codigo].update({"seccion": seccion, "explicacion": explicacion, "nota": nota, "pendientes": pendientes})  # Mantiene los seis idiomas sincronizados.


# ============================================================
# Textos de exportación e importación
# ============================================================

TEXTOS_TRANSFERENCIA = {
    "es": {"titulo_exportar": "Exportar preferencias", "descripcion_exportar": "Guarda la configuración actual en un archivo JSON que podrás usar en otra instalación. Solo se incluyen los cambios ya aplicados.", "ia_exportar": "Incluir preferencias de IA en el archivo", "boton_exportar": "Exportar preferencias", "archivo_exportar": "Guardar preferencias de TecNet Finder", "exito_exportar": "Preferencias exportadas correctamente en:", "titulo_importar": "Importar preferencias", "descripcion_importar": "Recupera preferencias desde un archivo compatible. Se comprobará su contenido y se respaldará tu configuración actual antes de sustituirla.", "ia_importar": "Importar también preferencias de IA", "boton_importar": "Importar preferencias", "archivo_importar": "Seleccionar archivo de preferencias", "confirmar_importar": "¿Importar las preferencias del archivo seleccionado?\n\nSe reemplazarán apariencia, editor, ventanas y advertencias. Se guardará un respaldo de los valores anteriores. Es necesario reiniciar TecNet Finder.", "confirmar_ia": "También se reemplazarán las preferencias de IA.", "falta_ia": "Este archivo no contiene preferencias de IA. Desmarca esa opción para importar solamente los ajustes generales.", "exito_importar": "Preferencias importadas correctamente. Cierra y vuelve a abrir TecNet Finder para aplicarlas por completo.", "fallo_exportar": "No fue posible exportar las preferencias:\n", "fallo_importar": "No fue posible importar las preferencias:\n"},
    "en": {"titulo_exportar": "Export preferences", "descripcion_exportar": "Save your current settings as a JSON file to use in another installation. Only previously applied changes are included.", "ia_exportar": "Include AI preferences in file", "boton_exportar": "Export preferences", "archivo_exportar": "Save TecNet Finder preferences", "exito_exportar": "Preferences exported successfully to:", "titulo_importar": "Import preferences", "descripcion_importar": "Restore settings from a compatible file. The data will be checked and your current settings backed up before replacement.", "ia_importar": "Also import AI preferences", "boton_importar": "Import preferences", "archivo_importar": "Choose preferences file", "confirmar_importar": "Import preferences from the selected file?\n\nAppearance, editor, window and warning settings will be replaced. A backup will be created. Restart TecNet Finder to apply the changes.", "confirmar_ia": "AI preferences will also be replaced.", "falta_ia": "This file does not contain AI preferences. Uncheck that option to import general settings only.", "exito_importar": "Preferences imported successfully. Close and reopen TecNet Finder to apply the changes fully.", "fallo_exportar": "Could not export preferences:\n", "fallo_importar": "Could not import preferences:\n"},
    "pt": {"titulo_exportar": "Exportar preferências", "descripcion_exportar": "Salva as configurações atuais em um arquivo JSON para outra instalação. Apenas alterações já aplicadas são incluídas.", "ia_exportar": "Incluir preferências de IA no arquivo", "boton_exportar": "Exportar preferências", "archivo_exportar": "Salvar preferências do TecNet Finder", "exito_exportar": "Preferências exportadas para:", "titulo_importar": "Importar preferências", "descripcion_importar": "Recupera configurações de um arquivo compatível, validando os dados e salvando uma cópia dos valores atuais.", "ia_importar": "Importar também preferências de IA", "boton_importar": "Importar preferências", "archivo_importar": "Selecionar arquivo de preferências", "confirmar_importar": "Importar as preferências do arquivo selecionado?\n\nAparência, editor, janelas e avisos serão substituídos. Será criado um backup. Reinicie o TecNet Finder.", "confirmar_ia": "As preferências de IA também serão substituídas.", "falta_ia": "Este arquivo não contém preferências de IA. Desmarque a opção para importar apenas os ajustes gerais.", "exito_importar": "Preferências importadas. Reinicie o TecNet Finder para aplicá-las completamente.", "fallo_exportar": "Não foi possível exportar:\n", "fallo_importar": "Não foi possível importar:\n"},
    "fr": {"titulo_exportar": "Exporter les préférences", "descripcion_exportar": "Enregistre les paramètres dans un fichier JSON réutilisable. Seules les modifications déjà appliquées sont incluses.", "ia_exportar": "Inclure les préférences d’IA", "boton_exportar": "Exporter les préférences", "archivo_exportar": "Enregistrer les préférences TecNet Finder", "exito_exportar": "Préférences exportées vers :", "titulo_importar": "Importer les préférences", "descripcion_importar": "Récupère les réglages d’un fichier compatible après vérification et sauvegarde de la configuration actuelle.", "ia_importar": "Importer également les préférences d’IA", "boton_importar": "Importer les préférences", "archivo_importar": "Choisir le fichier de préférences", "confirmar_importar": "Importer les préférences de ce fichier ?\n\nL’apparence, l’éditeur, les fenêtres et les avertissements seront remplacés. Une sauvegarde sera créée. Redémarrez TecNet Finder.", "confirmar_ia": "Les préférences d’IA seront aussi remplacées.", "falta_ia": "Ce fichier ne contient pas de préférences d’IA. Décochez cette option pour continuer.", "exito_importar": "Préférences importées. Redémarrez TecNet Finder pour appliquer les changements.", "fallo_exportar": "Impossible d’exporter les préférences :\n", "fallo_importar": "Impossible d’importer les préférences :\n"},
    "de": {"titulo_exportar": "Einstellungen exportieren", "descripcion_exportar": "Speichert die Einstellungen als JSON-Datei für andere Installationen. Nur bereits übernommene Änderungen werden berücksichtigt.", "ia_exportar": "KI-Einstellungen in die Datei aufnehmen", "boton_exportar": "Einstellungen exportieren", "archivo_exportar": "TecNet-Finder-Einstellungen speichern", "exito_exportar": "Einstellungen exportiert nach:", "titulo_importar": "Einstellungen importieren", "descripcion_importar": "Stellt Einstellungen aus einer kompatiblen Datei wieder her. Die Daten werden geprüft und die aktuellen Einstellungen gesichert.", "ia_importar": "Auch KI-Einstellungen importieren", "boton_importar": "Einstellungen importieren", "archivo_importar": "Einstellungsdatei auswählen", "confirmar_importar": "Einstellungen aus dieser Datei importieren?\n\nDarstellung, Editor, Fenster und Warnungen werden ersetzt. Eine Sicherung wird erstellt. Starten Sie TecNet Finder neu.", "confirmar_ia": "Auch KI-Einstellungen werden ersetzt.", "falta_ia": "Die Datei enthält keine KI-Einstellungen. Deaktivieren Sie diese Option, um fortzufahren.", "exito_importar": "Einstellungen importiert. Starten Sie TecNet Finder neu, um alle Änderungen anzuwenden.", "fallo_exportar": "Export fehlgeschlagen:\n", "fallo_importar": "Import fehlgeschlagen:\n"},
    "la": {"titulo_exportar": "Praeferentias exportare", "descripcion_exportar": "Praeferentias in tabulam JSON servat, ut alibi adhibeantur. Mutationes iam confirmatae tantum includuntur.", "ia_exportar": "Praeferentias IA in tabula includere", "boton_exportar": "Praeferentias exportare", "archivo_exportar": "Praeferentias TecNet Finder servare", "exito_exportar": "Praeferentiae servatae in:", "titulo_importar": "Praeferentias importare", "descripcion_importar": "Praeferentias ex tabula probata restituit, exemplar praesentium ante mutationem servans.", "ia_importar": "Praeferentias IA quoque importare", "boton_importar": "Praeferentias importare", "archivo_importar": "Tabulam praeferentiarum eligere", "confirmar_importar": "Visne praeferentias ex hac tabula importare?\n\nSpecies, editor, fenestrae atque monita mutabuntur. Exemplar servabitur. TecNet Finder rursus aperi.", "confirmar_ia": "Praeferentiae IA quoque mutabuntur.", "falta_ia": "Haec tabula praeferentias IA non continet. Optionem omitte.", "exito_importar": "Praeferentiae importatae. TecNet Finder rursus aperi ut mutationes fiant.", "fallo_exportar": "Exportatio non potuit fieri:\n", "fallo_importar": "Importatio non potuit fieri:\n"},
}


class PanelRestauracionPreferencias(QWidget):  # Proporciona una categoría completa en la navegación de Configuración.
    def __init__(self, padre=None):
        super().__init__(padre)  # Conserva el ciclo de vida asociado a Configuración.
        self.setObjectName("ContenidoSeccionConfiguracion")  # Permite al gestor de temas aplicar el fondo correcto.
        self.idioma = PreferenciasAplicacion().idioma_interfaz()  # Consulta el idioma actual sin alterar preferencias.
        self.textos = TEXTOS.get(self.idioma, TEXTOS["es"])  # Usa español como respaldo.
        diseno = QVBoxLayout(self)  # Construye una sección equivalente al resto de Configuración.
        diseno.setContentsMargins(24, 22, 24, 22)  # Iguala los márgenes laterales de Configuración.
        diseno.setSpacing(12)  # Mantiene separación entre títulos y tarjetas.

        self.titulo_categoria = QLabel()  # Presenta la categoría completa.
        self.titulo_categoria.setObjectName("TituloConfiguracion")  # Utiliza la jerarquía tipográfica oficial.
        self.titulo_categoria.setContentsMargins(4, 0, 4, 0)  # Conserva alineación con las tarjetas.
        diseno.addWidget(self.titulo_categoria)  # Coloca el título sobre la tarjeta.

        self.descripcion_categoria = QLabel()  # Explica el alcance de la sección.
        self.descripcion_categoria.setObjectName("DescripcionConfiguracion")  # Usa el color secundario del tema.
        self.descripcion_categoria.setWordWrap(True)  # Permite traducciones más largas.
        self.descripcion_categoria.setContentsMargins(4, 0, 4, 0)  # Separa el texto del borde.
        diseno.addWidget(self.descripcion_categoria)  # Coloca la descripción general.

        tarjeta = QFrame()  # Agrupa la restauración como herramienta independiente.
        tarjeta.setObjectName("TarjetaConfiguracion")  # Reutiliza el diseño de Resultados y navegación.
        contenedor = QVBoxLayout(tarjeta)  # Organiza los controles sin añadir un fondo a la fila de selección.
        contenedor.setContentsMargins(22, 16, 22, 16)  # Repite las proporciones de las tarjetas originales.
        contenedor.setSpacing(11)  # Separa título, descripción y acciones.

        self.titulo_restauracion = QLabel()  # Identifica la operación disponible.
        self.titulo_restauracion.setObjectName("SubtituloConfiguracion")  # Aplica el estilo del resto de tarjetas.
        self.titulo_restauracion.setContentsMargins(4, 0, 4, 0)  # Mantiene el título alineado.
        contenedor.addWidget(self.titulo_restauracion)  # Inserta el encabezado.

        self.descripcion_restauracion = QLabel()  # Explica qué datos se restablecen y cuáles se conservan.
        self.descripcion_restauracion.setObjectName("DescripcionConfiguracion")  # Mantiene el color informativo.
        self.descripcion_restauracion.setContentsMargins(4, 0, 4, 0)  # Conserva el margen de la tarjeta.
        self.descripcion_restauracion.setWordWrap(True)  # Evita recortes por idioma.
        contenedor.addWidget(self.descripcion_restauracion)  # Añade la explicación.

        fila_ia = QHBoxLayout()  # Presenta la opción sin un QCheckBox ni la franja oscura que éste generaba.
        fila_ia.setContentsMargins(4, 3, 4, 3)  # Mantiene la misma alineación de las demás opciones.
        fila_ia.setSpacing(9)  # Separa control y texto.
        self.opcion_ia = BotonCasillaConfiguracion("Incluir preferencias de IA", self)  # Reutiliza exactamente el control empleado en Configuración.
        self.opcion_ia.setChecked(False)  # No modifica las preferencias de IA salvo solicitud explícita.
        self.etiqueta_ia = QLabel()  # Separa el texto de la casilla para evitar estilos de fondo de QCheckBox.
        self.etiqueta_ia.setObjectName("TextoConfiguracion")  # Emplea la tipografía normal de opciones.
        self.etiqueta_ia.setWordWrap(True)  # Mantiene legibilidad en cualquiera de los seis idiomas.
        self.etiqueta_ia.setStyleSheet("background-color: transparent; border: none;")  # Impide la franja oscura señalada por el usuario.
        fila_ia.addWidget(self.opcion_ia)  # Sitúa la casilla al principio.
        fila_ia.addWidget(self.etiqueta_ia, 1)  # Alinea su texto con las demás etiquetas.
        contenedor.addLayout(fila_ia)  # Añade la fila a la tarjeta.

        fila_boton = QHBoxLayout()  # Mantiene la acción principal separada de la casilla.
        fila_boton.setContentsMargins(4, 2, 4, 0)  # Conserva el espaciado del panel.
        self.boton = QPushButton()  # Permite restaurar después de confirmar el alcance.
        self.boton.setObjectName("BotonRestaurarPreferencias")  # Limita su apariencia a esta acción sin afectar otras categorías.
        self.boton.setCursor(Qt.CursorShape.PointingHandCursor)  # Indica que la restauración está disponible para pulsarse.
        self._aplicar_estilo_boton()  # Utiliza el mismo fondo, borde y estados de los botones normales de Configuración.
        self.boton.clicked.connect(self._confirmar_y_restaurar)  # Protege la operación con una confirmación explícita.
        fila_boton.addWidget(self.boton)  # Alinea la acción a la izquierda.
        fila_boton.addStretch()  # No estira el botón a toda la tarjeta.
        contenedor.addLayout(fila_boton)  # Finaliza las acciones.

        self.nota = QLabel()  # Aclara que el botón no es un ajuste sujeto a Aplicar.
        self.nota.setObjectName("DescripcionConfiguracion")  # Usa una presentación informativa discreta.
        self.nota.setWordWrap(True)  # Evita recortes en traducciones largas.
        self.nota.setContentsMargins(4, 0, 4, 0)  # Alinea la observación con la tarjeta.
        contenedor.addWidget(self.nota)  # Muestra la aclaración bajo el botón.

        diseno.addWidget(tarjeta)  # Inserta la herramienta dentro de la sección propia.
        # ====================================================
        # Exportar preferencias
        # ====================================================

        self.tarjeta_exportar = QFrame()  # Separa la copia portátil de la restauración de fábrica.
        self.tarjeta_exportar.setObjectName("TarjetaConfiguracion")  # Reutiliza el contorno de las demás tarjetas.
        diseno_exportar = QVBoxLayout(self.tarjeta_exportar)  # Organiza la tarjeta según el patrón de Configuración.
        diseno_exportar.setContentsMargins(22, 16, 22, 16)  # Conserva el espaciado oficial.
        diseno_exportar.setSpacing(10)  # Evita controles amontonados.
        self.titulo_exportar = QLabel()  # Encabeza la copia de preferencias.
        self.titulo_exportar.setObjectName("SubtituloConfiguracion")  # Emplea la misma jerarquía visual.
        self.descripcion_exportar = QLabel()  # Indica que solo se guardan cambios ya confirmados.
        self.descripcion_exportar.setObjectName("DescripcionConfiguracion")  # Reutiliza el color de descripción.
        self.descripcion_exportar.setWordWrap(True)  # Permite textos extensos en los seis idiomas.
        diseno_exportar.addWidget(self.titulo_exportar)  # Muestra el título.
        diseno_exportar.addWidget(self.descripcion_exportar)  # Muestra la explicación.
        fila_exportar_ia = QHBoxLayout()  # Mantiene el control sin QCheckBox ni fondos rectangulares.
        fila_exportar_ia.setSpacing(9)  # Iguala la separación de otras casillas.
        self.opcion_ia_exportar = BotonCasillaConfiguracion("Incluir preferencias de IA", self)  # Reutiliza la casilla oficial.
        self.etiqueta_ia_exportar = QLabel()  # Explica su alcance sin controlar otras opciones.
        self.etiqueta_ia_exportar.setObjectName("TextoConfiguracion")  # Aplica la tipografía normal.
        self.etiqueta_ia_exportar.setStyleSheet("background-color: transparent; border: none;")  # Impide la franja oscura ya corregida en Restaurar.
        fila_exportar_ia.addWidget(self.opcion_ia_exportar)  # Sitúa la casilla.
        fila_exportar_ia.addWidget(self.etiqueta_ia_exportar)  # Coloca su etiqueta.
        fila_exportar_ia.addStretch()  # Mantiene los elementos a la izquierda.
        diseno_exportar.addLayout(fila_exportar_ia)  # Inserta la opción de IA.
        fila_exportar = QHBoxLayout()  # Evita un botón excesivamente ancho.
        self.boton_exportar = QPushButton()  # Abre un diálogo para elegir el destino.
        self.boton_exportar.setObjectName("BotonPreferenciasArchivo")  # Permite aplicar los colores actuales del tema.
        self.boton_exportar.setCursor(Qt.CursorShape.PointingHandCursor)  # Refuerza la disponibilidad.
        self.boton_exportar.clicked.connect(self._exportar)  # Ejecuta la copia solamente al pulsar.
        fila_exportar.addWidget(self.boton_exportar)  # Añade la acción.
        fila_exportar.addStretch()  # Mantiene la alineación.
        diseno_exportar.addLayout(fila_exportar)  # Completa la tarjeta.
        diseno.addWidget(self.tarjeta_exportar)  # Añade Exportar debajo de Restaurar.

        # ====================================================
        # Importar preferencias
        # ====================================================

        self.tarjeta_importar = QFrame()  # Separa la acción que sustituye valores existentes.
        self.tarjeta_importar.setObjectName("TarjetaConfiguracion")  # Conserva el mismo estilo de tarjeta.
        diseno_importar = QVBoxLayout(self.tarjeta_importar)  # Mantiene el orden de título, explicación y controles.
        diseno_importar.setContentsMargins(22, 16, 22, 16)  # Evita diferencias de márgenes.
        diseno_importar.setSpacing(10)  # Conserva la densidad visual.
        self.titulo_importar = QLabel()  # Describe la operación de importación.
        self.titulo_importar.setObjectName("SubtituloConfiguracion")  # Reutiliza el encabezado conocido.
        self.descripcion_importar = QLabel()  # Explica validación y respaldo previo.
        self.descripcion_importar.setObjectName("DescripcionConfiguracion")  # Utiliza el color secundario.
        self.descripcion_importar.setWordWrap(True)  # Evita cortar traducciones.
        diseno_importar.addWidget(self.titulo_importar)  # Agrega título.
        diseno_importar.addWidget(self.descripcion_importar)  # Agrega descripción.
        fila_importar_ia = QHBoxLayout()  # Mantiene explícita la autorización para importar IA.
        fila_importar_ia.setSpacing(9)  # Conserva espacio entre casilla y texto.
        self.opcion_ia_importar = BotonCasillaConfiguracion("Importar preferencias de IA", self)  # Por defecto queda desmarcada.
        self.etiqueta_ia_importar = QLabel()  # Explica la opción.
        self.etiqueta_ia_importar.setObjectName("TextoConfiguracion")  # Reutiliza el estilo de Configuración.
        self.etiqueta_ia_importar.setStyleSheet("background-color: transparent; border: none;")  # Mantiene el fondo de la tarjeta sin recuadros.
        fila_importar_ia.addWidget(self.opcion_ia_importar)  # Sitúa la opción.
        fila_importar_ia.addWidget(self.etiqueta_ia_importar)  # Sitúa el texto.
        fila_importar_ia.addStretch()  # Alinea a la izquierda.
        diseno_importar.addLayout(fila_importar_ia)  # Inserta la fila.
        fila_importar = QHBoxLayout()  # Mantiene el botón compacto.
        self.boton_importar = QPushButton()  # Abre el selector de archivos.
        self.boton_importar.setObjectName("BotonPreferenciasArchivo")  # Usa el estilo temático de exportación.
        self.boton_importar.setCursor(Qt.CursorShape.PointingHandCursor)  # Refuerza que funciona.
        self.boton_importar.clicked.connect(self._importar)  # Confirma y valida antes de modificar el perfil.
        fila_importar.addWidget(self.boton_importar)  # Añade el botón.
        fila_importar.addStretch()  # Evita ocupar todo el ancho.
        diseno_importar.addLayout(fila_importar)  # Completa la tarjeta.
        diseno.addWidget(self.tarjeta_importar)  # Añade Importar debajo de Exportar.

        diseno.addStretch()  # Mantiene el contenido arriba.
        self.aplicar_idioma(self.idioma)  # Completa los rótulos según la configuración actual.
        self._aplicar_estilo_boton()  # Sincroniza los nuevos botones con la paleta inicial.

    # ========================================================
    # Apariencia del botón de restauración
    # ========================================================

    def _aplicar_estilo_boton(self) -> None:  # Recupera el contraste y los estados utilizados por los botones de Configuración.
        p = obtener_tema(PreferenciasTema().tema())  # Respeta cualquier tema claro u oscuro confirmado.
        self.boton.setStyleSheet(f"""
            QPushButton#BotonRestaurarPreferencias {{ background-color: {p["superficie"]}; color: {p["texto"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 7px; padding: 8px 14px; font-weight: bold; }}
            QPushButton#BotonRestaurarPreferencias:hover {{ background-color: {p["superficie_hover"]}; color: {p["texto"]}; border-color: {p["acento"]}; }}
            QPushButton#BotonRestaurarPreferencias:pressed {{ background-color: {p["superficie_presionada"]}; color: {p["texto"]}; border-color: {p["acento"]}; }}
            QPushButton#BotonRestaurarPreferencias:disabled {{ background-color: {p["fondo_deshabilitado"]}; color: {p["texto_deshabilitado"]}; border-color: {p["borde_deshabilitado"]}; }}
        """)  # Conserva un borde visible en reposo, cambio de color al pasar el cursor y estado deshabilitado inequívoco.
        for boton in (getattr(self, "boton_exportar", None), getattr(self, "boton_importar", None)):  # Reutiliza los estados de los botones normales de Configuración.
            if boton is None: continue  # Permite la llamada previa a construir la tarjeta.
            boton.setStyleSheet(f"""
                QPushButton#BotonPreferenciasArchivo {{ background-color: {p["superficie"]}; color: {p["texto"]}; border: 1px solid {p["borde_fuerte"]}; border-radius: 7px; padding: 8px 14px; font-weight: bold; }}
                QPushButton#BotonPreferenciasArchivo:hover {{ background-color: {p["superficie_hover"]}; color: {p["texto"]}; border-color: {p["acento"]}; }}
                QPushButton#BotonPreferenciasArchivo:pressed {{ background-color: {p["superficie_presionada"]}; color: {p["texto"]}; border-color: {p["acento"]}; }}
                QPushButton#BotonPreferenciasArchivo:disabled {{ background-color: {p["fondo_deshabilitado"]}; color: {p["texto_deshabilitado"]}; border-color: {p["borde_deshabilitado"]}; }}
            """)  # Conserva la apariencia usada por el botón Restaurar.

    def showEvent(self, evento) -> None:  # Actualiza el color si se confirmó otro tema mientras esta categoría estaba oculta.
        super().showEvent(evento)  # Mantiene el ciclo normal de Qt para mostrar el panel.
        self._aplicar_estilo_boton()  # Sincroniza el botón con la paleta vigente antes de interactuar.

    def aplicar_idioma(self, idioma: str) -> None:  # Actualiza los textos cuando se cambia el idioma desde Configuración.
        self.idioma = idioma if idioma in TEXTOS else "es"  # Garantiza que exista un catálogo completo.
        self.textos = TEXTOS[self.idioma]  # Conserva el mismo diccionario para las confirmaciones.
        t = self.textos  # Reduce repeticiones de acceso.
        self.titulo_categoria.setText(t["seccion"])  # Retraduce la categoría.
        self.descripcion_categoria.setText(t["explicacion"])  # Actualiza la explicación general.
        self.titulo_restauracion.setText(t["titulo"])  # Traduce el título de la tarjeta.
        self.descripcion_restauracion.setText(t["descripcion"])  # Mantiene el alcance legible.
        self.etiqueta_ia.setText(t["incluir"])  # Traduce la opción de IA.
        self.opcion_ia.setAccessibleName(t["incluir"])  # Mantiene la descripción accesible.
        self.boton.setText(t["boton"])  # Traduce la acción.
        self.nota.setText(t["nota"])  # Explica su independencia de Aplicar.
        tt = TEXTOS_TRANSFERENCIA[self.idioma]  # Recupera los textos de importación y exportación para el mismo idioma.
        self.titulo_exportar.setText(tt["titulo_exportar"])  # Traduce la primera herramienta nueva.
        self.descripcion_exportar.setText(tt["descripcion_exportar"])  # Traduce su descripción.
        self.etiqueta_ia_exportar.setText(tt["ia_exportar"])  # Explica la opción de exportar IA.
        self.opcion_ia_exportar.setAccessibleName(tt["ia_exportar"])  # Mantiene accesibilidad.
        self.boton_exportar.setText(tt["boton_exportar"])  # Traduce la acción Exportar.
        self.titulo_importar.setText(tt["titulo_importar"])  # Traduce la segunda herramienta nueva.
        self.descripcion_importar.setText(tt["descripcion_importar"])  # Traduce su descripción.
        self.etiqueta_ia_importar.setText(tt["ia_importar"])  # Explica la opción independiente de IA.
        self.opcion_ia_importar.setAccessibleName(tt["ia_importar"])  # Mantiene accesibilidad.
        self.boton_importar.setText(tt["boton_importar"])  # Traduce la acción Importar.

    # ========================================================
    # Diálogo de confirmación según el idioma de la interfaz
    # ========================================================

    def _preguntar_confirmacion(self, titulo: str, mensaje: str) -> bool:  # Presenta Sí/No en el idioma elegido sin alterar la decisión predeterminada.
        dialogo = QMessageBox(self)  # Construye el mensaje con los mismos estilos generales de TecNet Finder.
        dialogo.setWindowTitle(titulo)  # Conserva el título traducido de la operación.
        dialogo.setIcon(QMessageBox.Icon.Question)  # Representa visualmente que se solicita una decisión.
        dialogo.setText(mensaje)  # Presenta la explicación específica de restauración o importación.
        dialogo.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)  # Conserva la semántica estándar de ambos botones.
        dialogo.setDefaultButton(QMessageBox.StandardButton.No)  # Evita confirmar accidentalmente al pulsar Enter.
        dialogo.setEscapeButton(QMessageBox.StandardButton.No)  # Escape siempre cancela la operación.
        afirmativo, negativo = ETIQUETAS_CONFIRMACION.get(self.idioma, ETIQUETAS_CONFIRMACION["es"])  # Usa español si el código de idioma es desconocido.
        boton_si = dialogo.button(QMessageBox.StandardButton.Yes)  # Recupera el botón de aceptación sin crear otro distinto.
        boton_no = dialogo.button(QMessageBox.StandardButton.No)  # Recupera el botón que cancela.
        if boton_si is not None: boton_si.setText(afirmativo)  # Sustituye Yes por la traducción visible.
        if boton_no is not None: boton_no.setText(negativo)  # Sustituye No por el equivalente del idioma activo.
        return dialogo.exec() == QMessageBox.StandardButton.Yes  # Solo permite continuar tras una confirmación explícita.

    def _confirmar_y_restaurar(self) -> None:  # Solicita autorización antes de reemplazar preferencias guardadas.
        t = self.textos  # Consulta los textos de la sesión.
        ventana = self.window()  # Recupera el diálogo de Configuración que contiene esta sección.
        if getattr(ventana, "operacion_en_curso", False): return  # No interrumpe una operación importante de IA.
        incluir_ia = self.opcion_ia.isChecked()  # Respeta la elección explícita del usuario.
        pregunta = t["confirmar_ia"] if incluir_ia else t["confirmar"]  # Advierte que los valores se aplican al reiniciar.
        if hasattr(ventana, "_obtener_todos_los_cambios_pendientes") and ventana._obtener_todos_los_cambios_pendientes():
            pregunta += "\n\n" + t["pendientes"]  # Evita perder cambios temporales sin aviso.
        if not self._preguntar_confirmacion(t["titulo"], pregunta): return  # Solo restaura cuando el usuario confirma con Sí.
        try:
            resultado = restaurar_preferencias(incluir_ia=incluir_ia)  # Conserva respaldo y reversión ante fallos.
        except (OSError, ValueError, RuntimeError) as error:
            QMessageBox.warning(self, t["titulo"], t["fallo"] + str(error))  # Muestra la causa sin afirmar éxito.
            return
        mensaje = t["correcto"]  # Indica que se deben cargar los valores iniciales en un nuevo inicio.
        if resultado.respaldo is not None: mensaje += f"\n\n{t['respaldo']}\n{resultado.respaldo}"  # Comunica la ubicación de recuperación.
        QMessageBox.information(self, t["titulo"], mensaje)  # Confirma solo cuando la restauración termina.
        self.boton.setEnabled(False)  # Impide un segundo restablecimiento en la misma sesión.
        if hasattr(ventana, "_cancelar_cambios"): ventana._cancelar_cambios()  # Cierra Configuración sin reescribir los valores restaurados.

    # ========================================================
    # Exportación e importación de preferencias
    # ========================================================

    def _exportar(self) -> None:  # Guarda una copia de los ajustes confirmados sin cambiarlos.
        t = TEXTOS_TRANSFERENCIA[self.idioma]  # Consulta los mensajes vigentes.
        destino, _filtro = QFileDialog.getSaveFileName(self, t["archivo_exportar"], str(Path.home() / "TecNetFinder-preferencias.json"), "JSON (*.json)")  # Solicita una ubicación elegida por el usuario.
        if not destino: return  # No crea archivos si se cancela el diálogo.
        if not destino.lower().endswith(".json"): destino += ".json"  # Mantiene la extensión reconocida por la importación.
        try: ruta = exportar_preferencias(destino, incluir_ia=self.opcion_ia_exportar.isChecked())  # Solo exporta archivos de preferencias conocidos.
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, t["titulo_exportar"], t["fallo_exportar"] + str(error))  # No informa éxito cuando falla.
            return
        QMessageBox.information(self, t["titulo_exportar"], f"{t['exito_exportar']}\n{ruta}")  # Confirma la ruta escrita.

    def _importar(self) -> None:  # Valida y solicita confirmación antes de sustituir preferencias.
        t = TEXTOS_TRANSFERENCIA[self.idioma]  # Consulta los textos vigentes.
        ventana = self.window()  # Recupera la sesión de Configuración.
        if getattr(ventana, "operacion_en_curso", False): return  # Respeta operaciones activas de IA.
        origen, _filtro = QFileDialog.getOpenFileName(self, t["archivo_importar"], str(Path.home()), "JSON (*.json)")  # Permite elegir un archivo externo.
        if not origen: return  # Evita cambios ante cancelación.
        try: contiene_ia = inspeccionar_preferencias(origen)  # Comprueba el paquete completo antes de mostrar el diálogo.
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, t["titulo_importar"], t["fallo_importar"] + str(error))  # Rechaza archivos inválidos.
            return
        incluir_ia = self.opcion_ia_importar.isChecked()  # Requiere consentimiento explícito para sustituir IA.
        if incluir_ia and not contiene_ia:
            QMessageBox.warning(self, t["titulo_importar"], t["falta_ia"])  # No crea una configuración vacía cuando no existe IA.
            return
        pregunta = t["confirmar_importar"] + ("\n\n" + t["confirmar_ia"] if incluir_ia else "")  # Explica qué ámbitos serán reemplazados.
        if hasattr(ventana, "_obtener_todos_los_cambios_pendientes") and ventana._obtener_todos_los_cambios_pendientes():
            pregunta += "\n\n" + self.textos["pendientes"]  # Advierte que los valores sin aplicar no se exportan ni guardan.
        if not self._preguntar_confirmacion(t["titulo_importar"], pregunta): return  # Solo importa tras aceptar explícitamente.
        try: resultado = importar_preferencias(origen, incluir_ia=incluir_ia)  # Revalida y realiza una importación respaldada y reversible.
        except (OSError, ValueError, RuntimeError) as error:
            QMessageBox.warning(self, t["titulo_importar"], t["fallo_importar"] + str(error))  # Mantiene Configuración abierta ante fallos.
            return
        mensaje = t["exito_importar"]  # Recuerda que la aplicación debe reiniciarse.
        if resultado.respaldo is not None: mensaje += f"\n\n{self.textos['respaldo']}\n{resultado.respaldo}"  # Informa la ruta de la copia anterior.
        QMessageBox.information(self, t["titulo_importar"], mensaje)  # Confirma solo cuando ya se completó la operación.
        self.boton_importar.setEnabled(False)  # Evita ejecutar otra importación durante la misma sesión.
        if hasattr(ventana, "_cancelar_cambios"): ventana._cancelar_cambios()  # Cierra sin volver a guardar ajustes temporales antiguos.
