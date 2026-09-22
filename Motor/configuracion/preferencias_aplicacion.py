# ============================================================
# Archivo: preferencias_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Administra las preferencias generales persistentes de TecNet
# Finder relacionadas con ventana, apariencia, editor,
# navegación y avisos.
#
# Los valores se almacenan dentro de LocalAppData para mantener
# estas decisiones separadas del código fuente del compilador.
# ============================================================

import json  # Permite almacenar las preferencias mediante un archivo estructurado.
import os  # Permite consultar LocalAppData proporcionado por Windows.
from pathlib import Path  # Permite construir rutas independientes del usuario.


class PreferenciasAplicacion:  # Centraliza todas las preferencias generales persistentes.

    # ========================================================
    # Claves de Ventana y apariencia
    # ========================================================

    CLAVE_INICIAR_MAXIMIZADO = "iniciar_maximizado"  # Guarda el estado utilizado durante un inicio convencional.
    CLAVE_RECORDAR_ESTADO_VENTANA = "recordar_estado_ventana"  # Guarda si debe recuperarse el estado anterior.
    CLAVE_ULTIMO_ESTADO_VENTANA = "ultimo_estado_ventana"  # Guarda exclusivamente normal o maximizada.
    CLAVE_RECORDAR_SECCION_CONFIGURACION = "recordar_seccion_configuracion"  # Guarda si Configuración recupera su categoría anterior.
    CLAVE_ULTIMA_SECCION_CONFIGURACION = "ultima_seccion_configuracion"  # Guarda la última categoría visitada.
    CLAVE_FAMILIA_FUENTE_INTERFAZ = "familia_fuente_interfaz"  # Guarda la familia tipográfica utilizada por la interfaz general.
    CLAVE_TAMANO_FUENTE_INTERFAZ = "tamano_fuente_interfaz"  # Guarda el tamaño base utilizado por la interfaz general.

    # ========================================================
    # Claves del Editor
    # ========================================================

    CLAVE_AJUSTE_LINEA_EDITOR = "ajuste_linea_editor"  # Guarda el ajuste automático de líneas.
    CLAVE_BOTONES_RAPIDOS_EDITOR = "mostrar_botones_rapidos_editor"  # Guarda la visibilidad de Ampliar y Ejemplos.
    CLAVE_FAMILIA_FUENTE_EDITOR = "familia_fuente_editor"  # Guarda la tipografía elegida para escribir código.
    CLAVE_TAMANO_FUENTE_EDITOR = "tamano_fuente_editor"  # Guarda el tamaño del texto del editor.
    CLAVE_ESPACIOS_TABULACION_EDITOR = "espacios_tabulacion_editor"  # Guarda el ancho visual de una tabulación.

    # ========================================================
    # Claves de navegación y advertencias
    # ========================================================

    CLAVE_NAVEGACION_ANTIGUA = "navegacion_automatica"  # Conserva compatibilidad con versiones anteriores.
    CLAVE_NAVEGACION_ERRORES = "navegacion_errores"  # Guarda la navegación hacia diagnósticos.
    CLAVE_NAVEGACION_VLSM = "navegacion_vlsm"  # Guarda la navegación hacia Tabla VLSM.
    CLAVE_ADVERTENCIAS_VLSM = "mostrar_advertencias_vlsm"  # Guarda la modalidad compacta de avisos.
    CLAVE_ADVERTENCIAS_VENTANA = "mostrar_advertencias_ventana"  # Guarda la modalidad independiente.
    CLAVE_CERRAR_VENTANA_AL_NAVEGAR = "cerrar_ventana_advertencias_al_navegar"  # Guarda el comportamiento del doble clic.

    # ========================================================
    # Estados de ventana
    # ========================================================

    ESTADO_VENTANA_MAXIMIZADA = "maximizada"  # Representa una sesión cerrada maximizada.
    ESTADO_VENTANA_NORMAL = "normal"  # Representa una sesión cerrada en modo ventana.

    # ========================================================
    # Categorías de Configuración
    # ========================================================

    SECCION_VENTANA = "ventana"  # Identifica Ventana y apariencia.
    SECCION_EDITOR = "editor"  # Identifica Editor.
    SECCION_RESULTADOS = "resultados"  # Identifica Resultados y navegación.
    SECCION_IA = "ia"  # Identifica Asistencia de IA.
    SECCIONES_CONFIGURACION_VALIDAS = {
        SECCION_VENTANA,
        SECCION_EDITOR,
        SECCION_RESULTADOS,
        SECCION_IA,
    }  # Limita las categorías recuperables.

    # ========================================================
    # Límites y valores predeterminados de la interfaz
    # ========================================================

    FUENTE_INTERFAZ_PREDETERMINADA = "Consolas"  # Conserva la apariencia general utilizada históricamente por TecNet Finder.
    TAMANO_FUENTE_INTERFAZ_PREDETERMINADO = 10  # Conserva el tamaño base utilizado actualmente por la interfaz.
    TAMANO_FUENTE_INTERFAZ_MINIMO = 8  # Evita una interfaz demasiado pequeña para resultar legible.
    TAMANO_FUENTE_INTERFAZ_MAXIMO = 14  # Evita que el tamaño base rompa innecesariamente la distribución de los controles.

    # ========================================================
    # Límites y valores predeterminados del editor
    # ========================================================

    FUENTE_EDITOR_PREDETERMINADA = "Consolas"  # Conserva la tipografía utilizada históricamente por el editor.
    TAMANO_FUENTE_EDITOR_PREDETERMINADO = 10  # Conserva el tamaño original del código.
    TAMANO_FUENTE_EDITOR_MINIMO = 8  # Evita tamaños excesivamente pequeños.
    TAMANO_FUENTE_EDITOR_MAXIMO = 20  # Evita tamaños poco prácticos.
    ESPACIOS_TABULACION_VALIDOS = {2, 4, 8}  # Define los anchos ofrecidos desde Configuración.

    def __init__(self, ruta_datos_locales: str | Path | None = None):
        self.ruta_datos_locales = Path(ruta_datos_locales) if ruta_datos_locales else self._obtener_ruta_datos_locales()  # Permite utilizar carpetas temporales durante pruebas.
        self.ruta_directorio = self.ruta_datos_locales / "TecNetFinder"  # Define la carpeta general de datos locales.
        self.ruta_archivo = self.ruta_directorio / "preferencias_aplicacion.json"  # Define el archivo de preferencias generales.

    # ========================================================
    # Ventana y apariencia
    # ========================================================

    def iniciar_maximizado(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_INICIAR_MAXIMIZADO, True)  # Recupera el comportamiento histórico.
        return valor if isinstance(valor, bool) else True  # Corrige información inválida.

    def establecer_iniciar_maximizado(self, activado: bool) -> bool:
        return self._guardar_valor(self.CLAVE_INICIAR_MAXIMIZADO, bool(activado))  # Persiste el valor solicitado.

    def recordar_estado_ventana(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_RECORDAR_ESTADO_VENTANA, False)  # Recupera si debe restaurarse el estado anterior.
        return valor if isinstance(valor, bool) else False  # Recupera un valor seguro ante información inválida.

    def establecer_recordar_estado_ventana(self, activado: bool) -> bool:
        return self._guardar_valor(self.CLAVE_RECORDAR_ESTADO_VENTANA, bool(activado))  # Persiste la nueva decisión.

    def ultimo_estado_ventana(self) -> str | None:
        valor = self._leer_preferencias().get(self.CLAVE_ULTIMO_ESTADO_VENTANA)  # Recupera el último estado persistente.
        return valor if valor in (self.ESTADO_VENTANA_MAXIMIZADA, self.ESTADO_VENTANA_NORMAL) else None  # Rechaza estados temporales.

    def establecer_ultimo_estado_ventana(self, estado: str) -> bool:
        if estado not in (self.ESTADO_VENTANA_MAXIMIZADA, self.ESTADO_VENTANA_NORMAL):  # Comprueba que el estado sea recuperable.
            return False  # Impide almacenar fullscreen o Media pantalla.
        return self._guardar_valor(self.CLAVE_ULTIMO_ESTADO_VENTANA, estado)  # Persiste el estado seguro.

    def recordar_seccion_configuracion(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_RECORDAR_SECCION_CONFIGURACION, True)  # Recupera la decisión relacionada con la navegación interna.
        return valor if isinstance(valor, bool) else True  # Mantiene activa esta comodidad ante información inválida.

    def establecer_recordar_seccion_configuracion(self, activado: bool) -> bool:
        return self._guardar_valor(self.CLAVE_RECORDAR_SECCION_CONFIGURACION, bool(activado))  # Persiste la selección.

    def ultima_seccion_configuracion(self) -> str:
        valor = self._leer_preferencias().get(self.CLAVE_ULTIMA_SECCION_CONFIGURACION, self.SECCION_VENTANA)  # Recupera la última categoría almacenada.
        return valor if valor in self.SECCIONES_CONFIGURACION_VALIDAS else self.SECCION_VENTANA  # Recupera una categoría segura.

    def establecer_ultima_seccion_configuracion(self, seccion: str) -> bool:
        if seccion not in self.SECCIONES_CONFIGURACION_VALIDAS:  # Comprueba que la clave pertenezca a una categoría real.
            return False  # Rechaza identificadores desconocidos.
        return self._guardar_valor(self.CLAVE_ULTIMA_SECCION_CONFIGURACION, seccion)  # Persiste la clave válida.

    def familia_fuente_interfaz(self) -> str:
        valor = self._leer_preferencias().get(self.CLAVE_FAMILIA_FUENTE_INTERFAZ, self.FUENTE_INTERFAZ_PREDETERMINADA)  # Recupera la familia tipográfica global.
        if isinstance(valor, str) and valor.strip():  # Comprueba que exista un nombre utilizable.
            return valor.strip()  # Devuelve la familia almacenada sin espacios sobrantes.
        return self.FUENTE_INTERFAZ_PREDETERMINADA  # Recupera el valor seguro ante información inválida.

    def establecer_familia_fuente_interfaz(self, familia: str) -> bool:
        if not isinstance(familia, str) or not familia.strip():  # Comprueba que se haya recibido una familia utilizable.
            return False  # Rechaza valores vacíos o incompatibles.
        return self._guardar_valor(self.CLAVE_FAMILIA_FUENTE_INTERFAZ, familia.strip())  # Persiste exactamente la familia seleccionada.

    def tamano_fuente_interfaz(self) -> int:
        valor = self._leer_preferencias().get(self.CLAVE_TAMANO_FUENTE_INTERFAZ, self.TAMANO_FUENTE_INTERFAZ_PREDETERMINADO)  # Recupera el tamaño base guardado.
        if isinstance(valor, int) and not isinstance(valor, bool) and self.TAMANO_FUENTE_INTERFAZ_MINIMO <= valor <= self.TAMANO_FUENTE_INTERFAZ_MAXIMO:  # Comprueba tipo y rango.
            return valor  # Devuelve el tamaño válido.
        return self.TAMANO_FUENTE_INTERFAZ_PREDETERMINADO  # Recupera el valor seguro ante información inválida.

    def establecer_tamano_fuente_interfaz(self, tamano: int) -> bool:
        if not isinstance(tamano, int) or isinstance(tamano, bool):  # Evita booleanos y otros tipos incompatibles.
            return False  # Rechaza el valor recibido.
        if not self.TAMANO_FUENTE_INTERFAZ_MINIMO <= tamano <= self.TAMANO_FUENTE_INTERFAZ_MAXIMO:  # Comprueba el intervalo permitido.
            return False  # Evita tamaños capaces de romper innecesariamente la interfaz.
        return self._guardar_valor(self.CLAVE_TAMANO_FUENTE_INTERFAZ, tamano)  # Persiste el tamaño base seleccionado.

    # ========================================================
    # Editor
    # ========================================================

    def ajuste_linea_editor_activado(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_AJUSTE_LINEA_EDITOR, True)  # Recupera el ajuste automático.
        return valor if isinstance(valor, bool) else True  # Utiliza ajuste como valor seguro.

    def establecer_ajuste_linea_editor_activado(self, activado: bool) -> bool:
        return self._guardar_valor(self.CLAVE_AJUSTE_LINEA_EDITOR, bool(activado))  # Persiste la nueva decisión.

    def botones_rapidos_editor_visibles(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_BOTONES_RAPIDOS_EDITOR, True)  # Recupera la visibilidad de Ampliar y Ejemplos.
        return valor if isinstance(valor, bool) else True  # Mantiene ambos visibles ante información inválida.

    def establecer_botones_rapidos_editor_visibles(self, visibles: bool) -> bool:
        return self._guardar_valor(self.CLAVE_BOTONES_RAPIDOS_EDITOR, bool(visibles))  # Persiste la nueva visibilidad.

    def familia_fuente_editor(self) -> str:
        valor = self._leer_preferencias().get(self.CLAVE_FAMILIA_FUENTE_EDITOR, self.FUENTE_EDITOR_PREDETERMINADA)  # Recupera la familia seleccionada.
        return valor.strip() if isinstance(valor, str) and valor.strip() else self.FUENTE_EDITOR_PREDETERMINADA  # Evita nombres vacíos o tipos incompatibles.

    def establecer_familia_fuente_editor(self, familia: str) -> bool:
        if not isinstance(familia, str) or not familia.strip():  # Comprueba que exista realmente un nombre de familia.
            return False  # Rechaza valores vacíos o incompatibles.
        return self._guardar_valor(self.CLAVE_FAMILIA_FUENTE_EDITOR, familia.strip())  # Persiste exactamente el nombre seleccionado.

    def tamano_fuente_editor(self) -> int:
        valor = self._leer_preferencias().get(self.CLAVE_TAMANO_FUENTE_EDITOR, self.TAMANO_FUENTE_EDITOR_PREDETERMINADO)  # Recupera el tamaño guardado.
        if isinstance(valor, int) and not isinstance(valor, bool) and self.TAMANO_FUENTE_EDITOR_MINIMO <= valor <= self.TAMANO_FUENTE_EDITOR_MAXIMO:  # Valida tipo y rango.
            return valor  # Devuelve el tamaño permitido.
        return self.TAMANO_FUENTE_EDITOR_PREDETERMINADO  # Recupera el tamaño original ante información inválida.

    def establecer_tamano_fuente_editor(self, tamano: int) -> bool:
        if not isinstance(tamano, int) or isinstance(tamano, bool):  # Evita booleanos y otros tipos.
            return False  # Rechaza valores incompatibles.
        if not self.TAMANO_FUENTE_EDITOR_MINIMO <= tamano <= self.TAMANO_FUENTE_EDITOR_MAXIMO:  # Comprueba el rango permitido.
            return False  # Rechaza tamaños poco prácticos.
        return self._guardar_valor(self.CLAVE_TAMANO_FUENTE_EDITOR, tamano)  # Persiste el tamaño válido.

    def espacios_tabulacion_editor(self) -> int:
        valor = self._leer_preferencias().get(self.CLAVE_ESPACIOS_TABULACION_EDITOR, 4)  # Recupera el ancho actual.
        return valor if valor in self.ESPACIOS_TABULACION_VALIDOS else 4  # Recupera cuatro espacios ante un valor desconocido.

    def establecer_espacios_tabulacion_editor(self, espacios: int) -> bool:
        if espacios not in self.ESPACIOS_TABULACION_VALIDOS:  # Comprueba que corresponda con una opción disponible.
            return False  # Rechaza cualquier otra cantidad.
        return self._guardar_valor(self.CLAVE_ESPACIOS_TABULACION_EDITOR, espacios)  # Persiste el valor válido.

    # ========================================================
    # Navegación
    # ========================================================

    def navegacion_errores_activada(self) -> bool:
        datos = self._leer_preferencias()  # Recupera una sola vez la configuración.
        valor = datos.get(self.CLAVE_NAVEGACION_ERRORES)  # Busca primero la nueva preferencia específica.
        if isinstance(valor, bool):  # Comprueba que el valor sea válido.
            return valor  # Respeta la decisión actual.
        valor_antiguo = datos.get(self.CLAVE_NAVEGACION_ANTIGUA)  # Consulta la antigua opción general.
        return valor_antiguo if isinstance(valor_antiguo, bool) else True  # Mantiene compatibilidad automática.

    def navegacion_vlsm_activada(self) -> bool:
        datos = self._leer_preferencias()  # Recupera la configuración una sola vez.
        valor = datos.get(self.CLAVE_NAVEGACION_VLSM)  # Consulta la preferencia específica.
        if isinstance(valor, bool):  # Comprueba que pueda utilizarse.
            return valor  # Respeta el valor persistido.
        valor_antiguo = datos.get(self.CLAVE_NAVEGACION_ANTIGUA)  # Busca la opción utilizada anteriormente.
        return valor_antiguo if isinstance(valor_antiguo, bool) else True  # Migra su comportamiento de forma transparente.

    def establecer_navegacion_errores_activada(self, activada: bool) -> bool:
        return self._guardar_valor(self.CLAVE_NAVEGACION_ERRORES, bool(activada))  # Persiste exclusivamente esta navegación.

    def establecer_navegacion_vlsm_activada(self, activada: bool) -> bool:
        return self._guardar_valor(self.CLAVE_NAVEGACION_VLSM, bool(activada))  # Persiste exclusivamente la navegación hacia VLSM.

    def navegacion_automatica_activada(self) -> bool:
        return self.navegacion_errores_activada() and self.navegacion_vlsm_activada()  # Mantiene compatibilidad con la antigua opción general.

    def establecer_navegacion_automatica_activada(self, activada: bool) -> bool:
        return self._guardar_valores({
            self.CLAVE_NAVEGACION_ERRORES: bool(activada),
            self.CLAVE_NAVEGACION_VLSM: bool(activada),
        })  # Aplica la decisión antigua a ambas opciones actuales.

    # ========================================================
    # Presentación de advertencias
    # ========================================================

    def advertencias_vlsm_visibles(self) -> bool:
        datos = self._leer_preferencias()  # Recupera ambas modalidades.
        panel = datos.get(self.CLAVE_ADVERTENCIAS_VLSM, True)  # Recupera el panel compacto.
        ventana = datos.get(self.CLAVE_ADVERTENCIAS_VENTANA, False)  # Recupera la ventana independiente.
        panel = panel if isinstance(panel, bool) else True  # Normaliza el primer valor.
        ventana = ventana if isinstance(ventana, bool) else False  # Normaliza el segundo valor.
        return True if panel and ventana else panel  # Da prioridad al panel si un archivo externo dejó ambas activadas.

    def advertencias_ventana_independiente(self) -> bool:
        datos = self._leer_preferencias()  # Recupera ambas modalidades.
        panel = datos.get(self.CLAVE_ADVERTENCIAS_VLSM, True)  # Consulta la modalidad compacta.
        ventana = datos.get(self.CLAVE_ADVERTENCIAS_VENTANA, False)  # Consulta la modalidad independiente.
        panel = panel if isinstance(panel, bool) else True  # Normaliza la primera opción.
        ventana = ventana if isinstance(ventana, bool) else False  # Normaliza la segunda opción.
        return False if panel and ventana else ventana  # Mantiene exclusividad incluso ante archivos editados externamente.

    def establecer_advertencias_vlsm_visibles(self, visibles: bool) -> bool:
        cambios = {self.CLAVE_ADVERTENCIAS_VLSM: bool(visibles)}  # Prepara la nueva modalidad compacta.
        if visibles:  # Comprueba si debe activarse.
            cambios[self.CLAVE_ADVERTENCIAS_VENTANA] = False  # Apaga automáticamente la ventana independiente.
        return self._guardar_valores(cambios)  # Persiste la combinación resultante.

    def establecer_advertencias_ventana_independiente(self, visibles: bool) -> bool:
        cambios = {self.CLAVE_ADVERTENCIAS_VENTANA: bool(visibles)}  # Prepara la modalidad independiente.
        if visibles:  # Comprueba si debe activarse.
            cambios[self.CLAVE_ADVERTENCIAS_VLSM] = False  # Apaga automáticamente el panel compacto.
        return self._guardar_valores(cambios)  # Persiste la combinación resultante.

    def cerrar_ventana_advertencias_al_navegar(self) -> bool:
        valor = self._leer_preferencias().get(self.CLAVE_CERRAR_VENTANA_AL_NAVEGAR, True)  # Recupera el comportamiento del doble clic.
        return valor if isinstance(valor, bool) else True  # Mantiene el comportamiento recomendado ante información inválida.

    def establecer_cerrar_ventana_advertencias_al_navegar(self, cerrar: bool) -> bool:
        return self._guardar_valor(self.CLAVE_CERRAR_VENTANA_AL_NAVEGAR, bool(cerrar))  # Persiste la nueva decisión.

    # ========================================================
    # Persistencia
    # ========================================================

    def _guardar_valor(self, clave: str, valor) -> bool:
        return self._guardar_valores({clave: valor})  # Reutiliza la misma escritura para una sola preferencia.

    def _guardar_valores(self, cambios: dict) -> bool:
        datos = self._leer_preferencias()  # Conserva todos los valores que no serán modificados.
        datos.update(cambios)  # Sustituye exclusivamente las claves solicitadas.

        try:  # Protege la aplicación frente a problemas del sistema de archivos.
            self.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta cuando todavía no existe.
            ruta_temporal = self.ruta_archivo.with_suffix(".tmp")  # Prepara una escritura segura mediante archivo temporal.
            ruta_temporal.write_text(
                json.dumps(datos, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )  # Guarda toda la configuración de forma legible.
            ruta_temporal.replace(self.ruta_archivo)  # Sustituye el archivo real después de completar la escritura.
            return True  # Confirma que las preferencias fueron persistidas.
        except OSError:  # Captura cualquier problema de escritura.
            return False  # Mantiene funcional la aplicación aunque no pueda guardar.

    def _leer_preferencias(self) -> dict:
        if not self.ruta_archivo.is_file():  # Comprueba si todavía no existe un archivo de preferencias.
            return {}  # Permite que todos los getters utilicen sus valores iniciales.

        try:  # Protege el inicio frente a archivos corruptos.
            datos = json.loads(self.ruta_archivo.read_text(encoding="utf-8"))  # Lee y convierte el JSON persistente.
        except (OSError, json.JSONDecodeError):  # Captura problemas de lectura o contenido inválido.
            return {}  # Recupera valores predeterminados sin bloquear TecNet Finder.

        return datos if isinstance(datos, dict) else {}  # Acepta exclusivamente un objeto JSON.

    def _obtener_ruta_datos_locales(self) -> Path:
        ruta_local = os.environ.get("LOCALAPPDATA")  # Consulta la ubicación oficial de Windows.
        return Path(ruta_local) if ruta_local else Path.home() / "AppData" / "Local"  # Mantiene una ruta alternativa segura.