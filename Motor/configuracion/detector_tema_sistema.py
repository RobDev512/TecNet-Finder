# ============================================================
# Archivo: detector_tema_sistema.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Detecta si el sistema operativo utiliza una apariencia clara
# u oscura para que TecNet Finder pueda elegir automáticamente
# su tema inicial mientras el usuario no haya fijado uno manual.
#
# Prioridad de detección:
# 1. Qt, cuando QApplication ya se encuentra disponible.
# 2. Preferencia de aplicaciones de Windows.
# 3. Modo oscuro como respaldo seguro e histórico.
# ============================================================

import sys  # Permite identificar Windows antes de consultar su registro.
from PySide6.QtCore import Qt  # Proporciona los valores oficiales de esquema claro y oscuro de Qt.
from PySide6.QtGui import QGuiApplication  # Permite consultar el esquema reconocido por Qt cuando la aplicación ya existe.
from Motor.configuracion.catalogo_temas import MODO_CLARO, MODO_OSCURO, TEMA_CLARO_TECNET, TEMA_OSCURO_TECNET  # Proporciona modos y variantes oficiales de TecNet Finder.


def detectar_modo_sistema() -> str:
    modo_qt = _detectar_mediante_qt()  # Intenta utilizar primero la información que Qt ya obtuvo del sistema.
    if modo_qt is not None: return modo_qt  # Devuelve inmediatamente una detección concluyente.
    modo_windows = _detectar_mediante_windows()  # Consulta después la preferencia específica de aplicaciones de Windows.
    if modo_windows is not None: return modo_windows  # Devuelve el resultado cuando el registro se encuentra disponible.
    return MODO_OSCURO  # Conserva la apariencia histórica de TecNet Finder como respaldo seguro.


def tema_recomendado_sistema() -> str:
    return TEMA_CLARO_TECNET if detectar_modo_sistema() == MODO_CLARO else TEMA_OSCURO_TECNET  # Relaciona cada modo del sistema con la variante TecNet oficial correspondiente.


def _detectar_mediante_qt() -> str | None:
    aplicacion = QGuiApplication.instance()  # Recupera la aplicación gráfica únicamente cuando ya fue creada.
    if aplicacion is None: return None  # Deja que otro método realice la detección durante pruebas o inicializaciones tempranas.
    pistas = aplicacion.styleHints()  # Recupera las preferencias visuales conocidas por Qt.
    obtener_esquema = getattr(pistas, "colorScheme", None)  # Mantiene compatibilidad con versiones de Qt que todavía no expongan esta función.
    if not callable(obtener_esquema): return None  # Continúa con Windows cuando la API no está disponible.
    enum_esquema = getattr(Qt, "ColorScheme", None)  # Recupera el enum solamente cuando la versión actual de Qt lo expone.
    if enum_esquema is None: return None  # Mantiene compatibilidad con versiones anteriores de Qt.
    try: esquema = obtener_esquema()  # Consulta el esquema actualmente detectado por Qt.
    except Exception: return None  # Evita que una limitación de plataforma interrumpa el inicio de TecNet Finder.
    if esquema == enum_esquema.Light: return MODO_CLARO  # Traduce el esquema claro al identificador interno.
    if esquema == enum_esquema.Dark: return MODO_OSCURO  # Traduce el esquema oscuro al identificador interno.
    return None  # Permite utilizar un segundo método cuando Qt devuelve Unknown.


def _detectar_mediante_windows() -> str | None:
    if sys.platform != "win32": return None  # Evita importar módulos exclusivos de Windows en otras plataformas.
    try:
        import winreg  # Importa el registro únicamente cuando realmente se ejecuta sobre Windows.
        ruta = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"  # Utiliza la clave oficial donde Windows guarda el tema utilizado por aplicaciones.
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta) as clave: valor, _tipo = winreg.QueryValueEx(clave, "AppsUseLightTheme")  # Recupera 1 para claro y 0 para oscuro.
        return MODO_CLARO if int(valor) != 0 else MODO_OSCURO  # Convierte directamente la preferencia de Windows al catálogo interno.
    except (OSError, ValueError, TypeError):
        return None  # Deja que el llamador utilice el respaldo histórico si la clave no existe o contiene un valor inválido.
