# ============================================================
# Archivo: prueba_preferencias_aplicacion.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo verifica la persistencia y recuperación segura de
# las preferencias generales de TecNet Finder.
#
# Comprueba opciones relacionadas con:
#
# - Ventana y apariencia.
# - Última categoría visitada en Configuración.
# - Navegación hacia errores y Tabla VLSM.
# - Presentación de advertencias.
# - Interacción con la ventana independiente.
# - Compatibilidad con configuraciones de versiones anteriores.
# - Recuperación ante archivos dañados.
#
# Todas las pruebas utilizan una carpeta temporal para no alterar
# la configuración real almacenada dentro de LocalAppData.
# ============================================================

from Motor.configuracion.preferencias_aplicacion import PreferenciasAplicacion  # Importa el administrador persistente que será comprobado mediante archivos temporales.


def test_valores_predeterminados(tmp_path):  # Comprueba todos los valores que debe utilizar una instalación que todavía no posee archivo de preferencias.
    preferencias = PreferenciasAplicacion(tmp_path)  # Sustituye LocalAppData por una carpeta temporal inicialmente vacía.
    assert preferencias.iniciar_maximizado() is True  # Confirma que TecNet Finder inicie maximizado de manera predeterminada.
    assert preferencias.recordar_estado_ventana() is False  # Comprueba que inicialmente no se restaure automáticamente el estado de la sesión anterior.
    assert preferencias.ultimo_estado_ventana() is None  # Confirma que todavía no exista ningún estado normal o maximizado almacenado.
    assert preferencias.recordar_seccion_configuracion() is True  # Comprueba que Configuración recuerde su última categoría de forma predeterminada.
    assert preferencias.ultima_seccion_configuracion() == PreferenciasAplicacion.SECCION_VENTANA  # Verifica que Ventana y apariencia sea la sección inicial cuando todavía no existe historial.
    assert preferencias.navegacion_errores_activada() is True  # Confirma que los errores provoquen navegación automática inicialmente.
    assert preferencias.navegacion_vlsm_activada() is True  # Confirma que los resultados válidos también naveguen automáticamente hacia Tabla VLSM.
    assert preferencias.advertencias_vlsm_visibles() is True  # Comprueba que la modalidad integrada de advertencias sea la predeterminada.
    assert preferencias.advertencias_ventana_independiente() is False  # Confirma que la ventana independiente permanezca desactivada inicialmente.
    assert preferencias.cerrar_ventana_advertencias_al_navegar() is True  # Comprueba que la ventana independiente se cierre después de navegar al código cuando llegue a utilizarse.


def test_guarda_preferencias_de_ventana(tmp_path):  # Comprueba que inicio, recuperación de estado y último modo puedan persistirse entre instancias.
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea el primer administrador que realizará las modificaciones.
    assert preferencias.establecer_iniciar_maximizado(False) is True  # Desactiva el inicio maximizado y confirma que la escritura pueda realizarse.
    assert preferencias.establecer_recordar_estado_ventana(True) is True  # Activa la recuperación del último estado de ventana.
    assert preferencias.establecer_ultimo_estado_ventana(PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA) is True  # Guarda un cierre simulado en estado maximizado.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Crea una segunda instancia para obligar a recuperar los valores desde el archivo.
    assert preferencias_recargadas.iniciar_maximizado() is False  # Confirma que la primera modificación permanezca después de recargar.
    assert preferencias_recargadas.recordar_estado_ventana() is True  # Comprueba que también se conserve la recuperación entre sesiones.
    assert preferencias_recargadas.ultimo_estado_ventana() == PreferenciasAplicacion.ESTADO_VENTANA_MAXIMIZADA  # Verifica que el estado maximizado almacenado pueda restaurarse correctamente.


def test_rechaza_estado_de_ventana_no_persistente(tmp_path):  # Comprueba que estados temporales como pantalla completa nunca se almacenen para el siguiente inicio.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara un administrador sobre una configuración temporal vacía.
    assert preferencias.establecer_ultimo_estado_ventana("pantalla_completa") is False  # Intenta guardar deliberadamente un modo que no pertenece a los estados persistentes permitidos.
    assert preferencias.ultimo_estado_ventana() is None  # Confirma que la operación rechazada no haya dejado ningún valor inválido almacenado.


def test_guarda_ultima_seccion_configuracion(tmp_path):  # Comprueba que Configuración pueda recordar la última categoría visitada.
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea el administrador que escribirá la preferencia.
    assert preferencias.establecer_ultima_seccion_configuracion(PreferenciasAplicacion.SECCION_IA) is True  # Simula que Asistencia de IA fue la última sección utilizada.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Recupera el archivo mediante una instancia nueva.
    assert preferencias_recargadas.ultima_seccion_configuracion() == PreferenciasAplicacion.SECCION_IA  # Confirma que Configuración pueda regresar posteriormente a esa categoría.


def test_rechaza_seccion_configuracion_inexistente(tmp_path):  # Comprueba que no pueda almacenarse un identificador de categoría desconocido.
    preferencias = PreferenciasAplicacion(tmp_path)  # Utiliza una configuración temporal sin modificaciones previas.
    assert preferencias.establecer_ultima_seccion_configuracion("seccion_inexistente") is False  # Intenta guardar deliberadamente una sección que no pertenece al catálogo permitido.
    assert preferencias.ultima_seccion_configuracion() == PreferenciasAplicacion.SECCION_VENTANA  # Confirma que el rechazo mantenga intacto el valor predeterminado seguro.


def test_guarda_navegaciones_independientemente(tmp_path):  # Comprueba que navegación hacia errores y navegación hacia VLSM sean preferencias completamente independientes.
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea el administrador encargado de guardar ambas decisiones.
    assert preferencias.establecer_navegacion_errores_activada(False) is True  # Desactiva únicamente la navegación automática correspondiente con errores.
    assert preferencias.establecer_navegacion_vlsm_activada(True) is True  # Mantiene activa de manera independiente la navegación hacia resultados VLSM.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Fuerza la lectura del archivo mediante una nueva instancia.
    assert preferencias_recargadas.navegacion_errores_activada() is False  # Confirma que la primera preferencia permanezca desactivada.
    assert preferencias_recargadas.navegacion_vlsm_activada() is True  # Comprueba que modificar errores no haya alterado la segunda navegación.


def test_preferencia_antigua_navegacion_migra_a_ambas_opciones(tmp_path):  # Comprueba la compatibilidad con el antiguo valor único navegacion_automatica.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara las rutas donde se escribirá manualmente una configuración de versión anterior.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta necesaria para simular que ya existe información persistente.
    preferencias.ruta_archivo.write_text('{"navegacion_automatica": false}', encoding="utf-8")  # Escribe únicamente la clave histórica utilizada antes de separar ambas navegaciones.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Crea una nueva instancia para obligar a interpretar el formato antiguo.
    assert preferencias_recargadas.navegacion_errores_activada() is False  # Comprueba que el antiguo valor desactivado se aplique a la nueva preferencia de errores.
    assert preferencias_recargadas.navegacion_vlsm_activada() is False  # Confirma que el mismo valor histórico también migre hacia la navegación VLSM.


def test_ventana_independiente_desactiva_panel_vlsm(tmp_path):  # Comprueba la exclusión mutua al activar la modalidad de advertencias en ventana independiente.
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea un administrador con los valores predeterminados.
    assert preferencias.advertencias_vlsm_visibles() is True  # Verifica primero que la modalidad integrada comienza activada.
    assert preferencias.establecer_advertencias_ventana_independiente(True) is True  # Activa la modalidad alternativa y confirma que pueda persistirse.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Recupera los valores efectivos desde el archivo guardado.
    assert preferencias_recargadas.advertencias_ventana_independiente() is True  # Confirma que la nueva modalidad haya quedado seleccionada.
    assert preferencias_recargadas.advertencias_vlsm_visibles() is False  # Verifica que la modalidad integrada se haya desactivado automáticamente.


def test_panel_vlsm_desactiva_ventana_independiente(tmp_path):  # Comprueba la exclusión mutua también cuando el cambio se realiza en la dirección contraria.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara una nueva configuración temporal.
    assert preferencias.establecer_advertencias_ventana_independiente(True) is True  # Activa primero la ventana independiente.
    assert preferencias.establecer_advertencias_vlsm_visibles(True) is True  # Activa después el panel integrado para obligar a desactivar la primera modalidad.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Recupera la configuración efectiva mediante una nueva instancia.
    assert preferencias_recargadas.advertencias_vlsm_visibles() is True  # Confirma que la modalidad solicitada más recientemente permanezca activa.
    assert preferencias_recargadas.advertencias_ventana_independiente() is False  # Comprueba que la modalidad contraria haya sido desactivada automáticamente.


def test_ambas_modalidades_pueden_permanecer_apagadas(tmp_path):  # Comprueba que la exclusión mutua no obligue a mantener siempre alguna modalidad activa.
    preferencias = PreferenciasAplicacion(tmp_path)  # Crea la configuración temporal utilizada por la prueba.
    assert preferencias.establecer_advertencias_vlsm_visibles(False) is True  # Desactiva explícitamente el panel integrado.
    assert preferencias.establecer_advertencias_ventana_independiente(False) is True  # Mantiene también desactivada la ventana independiente.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Recarga los valores almacenados desde disco.
    assert preferencias_recargadas.advertencias_vlsm_visibles() is False  # Confirma que el panel pueda permanecer apagado.
    assert preferencias_recargadas.advertencias_ventana_independiente() is False  # Confirma igualmente que ninguna ventana tenga que activarse por obligación.


def test_guarda_comportamiento_al_navegar_desde_advertencia(tmp_path):  # Comprueba la preferencia que controla si la ventana independiente debe cerrarse después de navegar al código.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara una configuración temporal nueva.
    assert preferencias.cerrar_ventana_advertencias_al_navegar() is True  # Comprueba primero el comportamiento predeterminado.
    assert preferencias.establecer_cerrar_ventana_advertencias_al_navegar(False) is True  # Desactiva la preferencia para conservar abierta la ventana después de navegar.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Fuerza la recuperación del valor persistido.
    assert preferencias_recargadas.cerrar_ventana_advertencias_al_navegar() is False  # Confirma que la decisión permanezca entre instancias.


def test_archivo_danado_recupera_valores_seguros(tmp_path):  # Comprueba que un JSON corrupto no impida iniciar TecNet Finder ni produzca valores impredecibles.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara las rutas donde se colocará deliberadamente una configuración inválida.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta que normalmente contendría el archivo persistente.
    preferencias.ruta_archivo.write_text("{contenido inválido", encoding="utf-8")  # Guarda un fragmento que no puede interpretarse como JSON correcto.
    assert preferencias.iniciar_maximizado() is True  # Confirma que ante el archivo dañado se recupere el valor seguro de inicio maximizado.
    assert preferencias.recordar_estado_ventana() is False  # Comprueba que no se intente restaurar un estado potencialmente corrupto.
    assert preferencias.navegacion_errores_activada() is True  # Recupera el comportamiento predeterminado correspondiente con errores.
    assert preferencias.navegacion_vlsm_activada() is True  # Recupera igualmente la navegación predeterminada hacia resultados.
    assert preferencias.advertencias_vlsm_visibles() is True  # Utiliza nuevamente la modalidad de advertencias integrada predeterminada.
    assert preferencias.advertencias_ventana_independiente() is False  # Mantiene desactivada la ventana independiente cuando no puede leerse la configuración.
    assert preferencias.cerrar_ventana_advertencias_al_navegar() is True  # Recupera también el comportamiento seguro de cierre después de navegar.


def test_clave_antigua_media_pantalla_no_afecta_resultados(tmp_path):  # Comprueba que una clave obsoleta de versiones anteriores pueda ignorarse sin alterar otras preferencias.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara la ubicación donde se simulará un archivo histórico.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta persistente necesaria.
    preferencias.ruta_archivo.write_text('{"lado_media_pantalla": "derecha"}', encoding="utf-8")  # Escribe únicamente una preferencia antigua que ya no participa en el diseño actual.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Carga el archivo mediante la versión actual del administrador.
    assert preferencias_recargadas.iniciar_maximizado() is True  # Confirma que la clave desconocida no altere el inicio predeterminado.
    assert preferencias_recargadas.recordar_estado_ventana() is False  # Comprueba que tampoco active accidentalmente la recuperación de estado.
    assert preferencias_recargadas.navegacion_errores_activada() is True  # Mantiene intacta la navegación predeterminada hacia errores.
    assert preferencias_recargadas.navegacion_vlsm_activada() is True  # Mantiene intacta también la navegación hacia VLSM.
    assert preferencias_recargadas.advertencias_vlsm_visibles() is True  # Conserva el panel integrado como modalidad predeterminada.
    assert preferencias_recargadas.advertencias_ventana_independiente() is False  # Confirma que la antigua clave no active la modalidad independiente.


def test_archivo_con_ambas_modalidades_activas_prioriza_panel_vlsm(tmp_path):  # Comprueba la recuperación segura de un archivo inconsistente donde ambas modalidades aparecen activadas simultáneamente.
    preferencias = PreferenciasAplicacion(tmp_path)  # Prepara la ruta donde se escribirá manualmente la configuración conflictiva.
    preferencias.ruta_directorio.mkdir(parents=True, exist_ok=True)  # Crea la carpeta requerida por el archivo persistente.
    preferencias.ruta_archivo.write_text('{"mostrar_advertencias_vlsm": true, "mostrar_advertencias_ventana": true}', encoding="utf-8")  # Simula un archivo externo o histórico que viola la exclusión mutua actual.
    preferencias_recargadas = PreferenciasAplicacion(tmp_path)  # Recupera la configuración para aplicar la regla de normalización definida por producción.
    assert preferencias_recargadas.advertencias_vlsm_visibles() is True  # Confirma que el panel integrado tenga prioridad ante la combinación inválida.
    assert preferencias_recargadas.advertencias_ventana_independiente() is False  # Comprueba que la modalidad independiente sea desactivada durante la lectura segura.