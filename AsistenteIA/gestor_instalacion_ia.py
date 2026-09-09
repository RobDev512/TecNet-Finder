# ============================================================
# Archivo: gestor_instalacion_ia.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Este archivo administra la instalación y desinstalación del
# componente opcional de inteligencia artificial local.
#
# Descarga un runtime oficial de Ollama previamente fijado,
# verifica su integridad mediante SHA-256, extrae los archivos
# de forma segura, descarga el modelo requerido y revierte una
# instalación incompleta cuando ocurre algún problema.
#
# El primer inicio del runtime dispone de un tiempo adicional
# porque Windows puede tardar en preparar y revisar binarios
# recién descargados.
# ============================================================

import hashlib  # Permite verificar que el paquete descargado coincida exactamente con el archivo oficial esperado.
import json  # Permite comunicarse con la API local de Ollama durante la descarga del modelo.
import os  # Permite comprobar que la plataforma actual sea compatible con el paquete seleccionado.
import platform  # Permite distinguir la arquitectura del procesador antes de instalar binarios.
from pathlib import Path  # Permite administrar de forma segura las rutas temporales y definitivas.
import shutil  # Permite mover instalaciones preparadas y restaurar respaldos en caso de fallo.
import tempfile  # Permite trabajar dentro de un directorio temporal que se elimina automáticamente.
from typing import Callable  # Permite recibir una función opcional utilizada para informar progreso a la interfaz.
import urllib.error  # Permite reconocer fallos de red durante las descargas.
import urllib.request  # Permite descargar archivos y comunicarse con Ollama sin agregar dependencias externas.
import zipfile  # Permite extraer el paquete independiente de Ollama para Windows.

from AsistenteIA.configuracion import MODELO_IA, URL_BASE_OLLAMA  # Importa el modelo requerido y la dirección exclusiva de la instancia privada.
from AsistenteIA.gestor_componente_ia import GestorComponenteIA  # Permite utilizar las rutas administradas del componente opcional.
from AsistenteIA.gestor_ollama import GestorOllama  # Permite iniciar el runtime temporalmente y detenerlo antes de desinstalar.


VERSION_OLLAMA = "0.33.3"  # Fija la versión probada por TecNet Finder para evitar instalar automáticamente binarios futuros no verificados.
URL_PAQUETE_OLLAMA = "https://github.com/ollama/ollama/releases/download/v0.33.3/ollama-windows-amd64.zip"  # Utiliza directamente el paquete independiente publicado por el proyecto oficial.
SHA256_PAQUETE_OLLAMA = "52cb36a62e7e501f61514f60212dec7117b6c098811357585e02fffe32d2fcd7"  # Conserva el resumen oficial del paquete Windows AMD64 utilizado por esta versión.
TIEMPO_INICIO_INSTALACION_SEGUNDOS = 30.0  # Permite un primer arranque más lento debido a extracción reciente, antivirus y carga inicial de bibliotecas.

NotificadorProgreso = Callable[[str, int | None], None]  # Define el formato utilizado para comunicar etapa y porcentaje opcional hacia la interfaz.


class ErrorInstalacionIA(Exception):  # Representa fallos controlados relacionados exclusivamente con la administración del componente.
    pass


class GestorInstalacionIA:  # Coordina la instalación completa sin mezclar esta responsabilidad con la interfaz gráfica.
    def __init__(
        self,
        componente_ia: GestorComponenteIA,
        gestor_ollama: GestorOllama,
        url_paquete: str = URL_PAQUETE_OLLAMA,
        sha256_paquete: str = SHA256_PAQUETE_OLLAMA,
        abrir_url=None,
    ):
        self.componente_ia = componente_ia  # Reutiliza exactamente las rutas administradas por TecNet Finder.
        self.gestor_ollama = gestor_ollama  # Comparte el mismo ciclo de vida de Ollama utilizado por la aplicación.
        self.url_paquete = url_paquete  # Permite sustituir el origen durante pruebas sin realizar conexiones reales.
        self.sha256_paquete = sha256_paquete.lower()  # Normaliza el resumen esperado antes de realizar comparaciones.
        self.abrir_url = abrir_url or urllib.request.urlopen  # Utiliza urllib real salvo cuando una prueba proporciona otra implementación.

    def instalar(self, notificar: NotificadorProgreso | None = None) -> tuple[bool, str]:
        if self.componente_ia.instalado():
            return False, "La asistencia de IA ya se encuentra instalada."  # Evita sobrescribir una instalación completa que actualmente funciona.

        if not self._plataforma_compatible():
            return False, "Esta versión del componente de IA requiere Windows de 64 bits sobre arquitectura AMD64."  # Impide ejecutar un paquete incompatible con el equipo.

        if self.gestor_ollama.motor.disponible() and not self.gestor_ollama.iniciado_por_aplicacion:
            return False, "Otra instancia está utilizando el servicio privado de IA. Cierra las demás instancias de TecNet Finder e inténtalo nuevamente."  # Evita reemplazar archivos utilizados por un proceso que esta ejecución no controla.

        if self.gestor_ollama.iniciado_por_aplicacion:
            self.gestor_ollama.detener()  # Limpia cualquier runtime parcial controlado por esta aplicación antes de reemplazar sus archivos.

        ruta_temporales = self.componente_ia.ruta_base.parent / "Temporal"  # Mantiene los archivos transitorios fuera del directorio definitivo del componente.

        try:
            ruta_temporales.mkdir(parents=True, exist_ok=True)  # Prepara una ubicación administrada donde descargar y verificar el paquete.
        except OSError as error:
            return False, f"No fue posible preparar los archivos temporales de instalación: {error}"  # Informa el problema sin modificar la instalación existente.

        try:
            with tempfile.TemporaryDirectory(prefix="instalacion_ia_", dir=str(ruta_temporales)) as directorio_temporal:
                ruta_temporal = Path(directorio_temporal)  # Convierte la ubicación creada automáticamente en una ruta reutilizable.
                ruta_paquete = ruta_temporal / "ollama.zip"  # Reserva el nombre utilizado para conservar la descarga antes de verificarla.
                ruta_extraida = ruta_temporal / "extraido"  # Reserva una carpeta independiente para revisar el contenido del ZIP.
                ruta_respaldo = None  # Conserva temporalmente cualquier instalación parcial sustituida.
                runtime_colocado = False  # Permite saber si un fallo requiere retirar archivos recién instalados.

                try:
                    self._descargar_paquete(ruta_paquete, notificar)  # Descarga y verifica el archivo oficial antes de extraer cualquier ejecutable.
                    ruta_runtime = self._extraer_paquete(ruta_paquete, ruta_extraida, notificar)  # Extrae únicamente rutas seguras dentro del directorio temporal.
                    ruta_respaldo = self._colocar_runtime(ruta_runtime, ruta_temporal)  # Coloca el runtime verificado en su ubicación definitiva.
                    runtime_colocado = True  # Registra que a partir de este punto un fallo necesita ejecutar rollback.

                    self._notificar(notificar, "Iniciando servicio local por primera vez...", None)  # Informa que Windows puede tardar algo más durante el primer arranque.

                    inicio_correcto = self.gestor_ollama.iniciar(
                        requerir_modelo=False,
                        tiempo_inicio_segundos=TIEMPO_INICIO_INSTALACION_SEGUNDOS,
                    )  # Concede un margen mayor al runtime recién extraído sin ralentizar los inicios normales de TecNet Finder.

                    if not inicio_correcto:
                        detalle = self.gestor_ollama.ultimo_error_inicio.strip()  # Recupera la causa concreta producida por el administrador del proceso.

                        if detalle:
                            raise ErrorInstalacionIA(
                                f"Ollama fue instalado, pero su servicio privado no pudo iniciar correctamente.\n\nDetalle: {detalle}"
                            )  # Permite distinguir timeout, proceso terminado o problema de archivos.
                        raise ErrorInstalacionIA(
                            "Ollama fue instalado, pero su servicio privado no pudo iniciar correctamente."
                        )  # Conserva un mensaje seguro cuando no existe información adicional.

                    self._descargar_modelo(notificar)  # Solicita el modelo directamente mediante la API de la instancia privada recién creada.

                    if not self.componente_ia.instalado():
                        raise ErrorInstalacionIA(
                            "La descarga terminó, pero TecNet Finder no pudo validar la instalación completa del componente."
                        )  # Impide considerar exitosa una instalación que no dejó runtime y modelo disponibles.

                    self._notificar(notificar, "Instalación completada.", 100)  # Informa a la interfaz que runtime y modelo están listos.
                    return True, "La asistencia de IA local se instaló correctamente."  # Mantiene el servicio activo para poder utilizar el autocompletado inmediatamente.
                except Exception as error:
                    self.gestor_ollama.detener()  # Retira primero cualquier proceso que pueda mantener bloqueados los archivos recién creados.

                    if runtime_colocado:
                        self._restaurar_runtime(ruta_respaldo)  # Recupera la situación existente antes de comenzar la sustitución.

                    if isinstance(error, ErrorInstalacionIA):
                        return False, str(error)  # Conserva los mensajes controlados preparados específicamente para el usuario.

                    if isinstance(error, urllib.error.URLError):
                        return False, f"No fue posible completar la descarga necesaria para la asistencia de IA: {error.reason}"  # Convierte fallos de red en una explicación directa.

                    if isinstance(error, zipfile.BadZipFile):
                        return False, "El paquete descargado no es un archivo ZIP válido."  # Evita exponer detalles internos innecesarios ante un archivo corrupto.

                    return False, f"No fue posible completar la instalación de la asistencia de IA: {error}"  # Mantiene controlado cualquier fallo inesperado de archivos o red.
        finally:
            self._retirar_directorio_vacio(ruta_temporales)  # Evita conservar la carpeta Temporal cuando ya no contiene ninguna instalación en curso.

    def desinstalar(self, notificar: NotificadorProgreso | None = None) -> tuple[bool, str]:
        if not self.componente_ia.ruta_base.exists():
            return True, "La asistencia de IA ya se encontraba desinstalada."  # Considera exitosa una solicitud cuando no existen archivos administrados que retirar.

        if self.gestor_ollama.motor.disponible() and not self.gestor_ollama.iniciado_por_aplicacion:
            return False, "El componente está siendo utilizado por otra instancia. Cierra las demás instancias de TecNet Finder antes de desinstalarlo."  # Evita terminar o borrar procesos que esta aplicación no inició.

        self._notificar(notificar, "Deteniendo el servicio local...", 25)  # Informa que primero deben liberarse ejecutables y bibliotecas cargadas.
        self.gestor_ollama.detener()  # Cierra el proceso principal y sus procesos secundarios antes de tocar los archivos físicos.

        if self.gestor_ollama.motor.disponible():
            return False, "El servicio local continúa activo y sus archivos no pueden retirarse de forma segura."  # Impide una eliminación parcial cuando el puerto privado todavía responde.

        self._notificar(notificar, "Esperando liberación de archivos...", 50)  # Informa que Windows puede tardar brevemente en liberar bibliotecas recién cerradas.
        self._notificar(notificar, "Eliminando runtime y modelo local...", 75)  # Informa la fase física de liberación de espacio.

        if not self.componente_ia.desinstalar_archivos():
            return False, "Windows no permitió eliminar completamente los archivos de la asistencia de IA después de varios intentos."  # Declara fallo únicamente después de la política de reintentos.

        self._notificar(notificar, "Desinstalación completada.", 100)  # Informa que el directorio administrado ya desapareció.
        return True, "La asistencia de IA local se desinstaló correctamente."  # Confirma que TecNet Finder puede seguir funcionando sin el componente opcional.

    def _plataforma_compatible(self) -> bool:
        arquitectura = platform.machine().lower()  # Normaliza el nombre reportado por Python para realizar una comparación estable.
        return os.name == "nt" and arquitectura in {"amd64", "x86_64"}  # Limita esta versión del instalador al paquete Windows AMD64 actualmente verificado.

    def _descargar_paquete(self, ruta_destino: Path, notificar: NotificadorProgreso | None) -> None:
        self._notificar(notificar, f"Descargando Ollama {VERSION_OLLAMA}...", 0)  # Identifica la versión exacta antes de comenzar la transferencia.

        solicitud = urllib.request.Request(
            self.url_paquete,
            headers={"User-Agent": "TecNetFinder/1.0"},
        )  # Agrega una identificación simple sin modificar la dirección oficial del paquete.

        resumen = hashlib.sha256()  # Calcula la integridad mientras los mismos bytes se escriben al disco.
        descargados = 0  # Permite calcular el avance cuando el servidor informa el tamaño total.
        tamano_bloque = 1024 * 1024  # Procesa la descarga en bloques de un MiB para evitar mantener el paquete completo en memoria.

        with self.abrir_url(solicitud, timeout=60) as respuesta:
            total_texto = respuesta.headers.get("Content-Length", "0")  # Consulta el tamaño anunciado sin asumir que siempre estará presente.

            try:
                total = int(total_texto)  # Convierte el encabezado a bytes cuando contiene un valor válido.
            except (TypeError, ValueError):
                total = 0  # Utiliza progreso indeterminado si el origen no informó una longitud válida.

            with ruta_destino.open("wb") as archivo_destino:
                while True:
                    bloque = respuesta.read(tamano_bloque)  # Obtiene solamente la siguiente porción disponible de la descarga.

                    if not bloque:
                        break  # Finaliza cuando el origen ya no proporciona más datos.

                    archivo_destino.write(bloque)  # Conserva exactamente los bytes recibidos antes de procesar el siguiente bloque.
                    resumen.update(bloque)  # Alimenta el SHA-256 con los mismos datos almacenados.
                    descargados += len(bloque)  # Actualiza la cantidad realmente recibida.

                    porcentaje = int(descargados * 100 / total) if total > 0 else None  # Calcula porcentaje solamente cuando existe un tamaño total confiable.
                    self._notificar(notificar, f"Descargando Ollama {VERSION_OLLAMA}...", porcentaje)  # Mantiene actualizada la barra de progreso durante la transferencia.

        if resumen.hexdigest().lower() != self.sha256_paquete:
            raise ErrorInstalacionIA(
                "La verificación SHA-256 del paquete de Ollama no coincidió con la versión oficial esperada."
            )  # Impide extraer o ejecutar un archivo cuya integridad no pudo confirmarse.

    def _extraer_paquete(
        self,
        ruta_paquete: Path,
        ruta_destino: Path,
        notificar: NotificadorProgreso | None,
    ) -> Path:
        self._notificar(notificar, "Verificando y extrayendo el runtime local...", 0)  # Informa que comienza la preparación de archivos ya descargados.
        ruta_destino.mkdir(parents=True, exist_ok=True)  # Crea una raíz dedicada que facilitará validar todas las rutas del ZIP.
        raiz_destino = ruta_destino.resolve()  # Obtiene la forma absoluta utilizada para impedir escapes fuera del directorio temporal.

        with zipfile.ZipFile(ruta_paquete, "r") as archivo_zip:
            miembros = archivo_zip.infolist()  # Recupera todas las entradas antes de comenzar la extracción.
            total_extraer = sum(miembro.file_size for miembro in miembros if not miembro.is_dir())  # Calcula el tamaño descomprimido total utilizado para mostrar progreso.
            extraidos = 0  # Conserva cuántos bytes descomprimidos han sido escritos hasta el momento.

            for miembro in miembros:
                ruta_relativa = Path(miembro.filename)  # Convierte el nombre almacenado en el ZIP a una ruta verificable.

                if ruta_relativa.is_absolute() or ".." in ruta_relativa.parts:
                    raise ErrorInstalacionIA(
                        "El paquete contiene una ruta no permitida y fue rechazado por seguridad."
                    )  # Bloquea entradas que intenten escribir fuera del directorio temporal.

                ruta_salida = (ruta_destino / ruta_relativa).resolve()  # Calcula la ubicación exacta antes de crear cualquier archivo.

                if not ruta_salida.is_relative_to(raiz_destino):
                    raise ErrorInstalacionIA(
                        "El paquete contiene una ruta no permitida y fue rechazado por seguridad."
                    )  # Añade una segunda barrera frente a rutas manipuladas.

                if miembro.is_dir():
                    ruta_salida.mkdir(parents=True, exist_ok=True)  # Recrea únicamente directorios que permanecen dentro de la raíz verificada.
                    continue  # Continúa con la siguiente entrada sin abrir un archivo inexistente.

                ruta_salida.parent.mkdir(parents=True, exist_ok=True)  # Prepara la carpeta propietaria del archivo validado.

                with archivo_zip.open(miembro, "r") as origen, ruta_salida.open("wb") as destino:
                    while True:
                        bloque = origen.read(1024 * 1024)  # Extrae cada archivo en bloques para evitar picos grandes de memoria.

                        if not bloque:
                            break  # Finaliza el archivo actual cuando ya se escribió todo su contenido.

                        destino.write(bloque)  # Conserva los bytes descomprimidos dentro de la ruta previamente validada.
                        extraidos += len(bloque)  # Actualiza el progreso global de extracción.

                        porcentaje = int(extraidos * 100 / total_extraer) if total_extraer > 0 else None  # Calcula avance solamente cuando existen datos que extraer.
                        self._notificar(notificar, "Verificando y extrayendo el runtime local...", porcentaje)  # Informa el avance mientras se preparan bibliotecas grandes.

        ejecutable_directo = ruta_destino / "ollama.exe"  # Comprueba primero la estructura utilizada actualmente por el paquete oficial.

        if ejecutable_directo.is_file():
            return ruta_destino  # Utiliza directamente la raíz extraída cuando allí se encuentra el runtime.

        candidatos = list(ruta_destino.rglob("ollama.exe"))  # Busca una posible carpeta contenedora si una versión futura agrega un nivel adicional.

        if len(candidatos) != 1:
            raise ErrorInstalacionIA(
                "No fue posible identificar de forma segura el ejecutable de Ollama dentro del paquete."
            )  # Evita adivinar una estructura ambigua.

        return candidatos[0].parent  # Utiliza como raíz del runtime la carpeta exacta que contiene el único ejecutable encontrado.

    def _colocar_runtime(self, ruta_runtime: Path, ruta_temporal: Path) -> Path | None:
        ruta_respaldo = None  # Conserva opcionalmente una instalación parcial existente para permitir rollback.

        if self.componente_ia.ruta_ollama.exists():
            ruta_respaldo = ruta_temporal / "respaldo_ollama"  # Mantiene el respaldo dentro del mismo ciclo temporal de la instalación.
            shutil.move(str(self.componente_ia.ruta_ollama), str(ruta_respaldo))  # Retira la instalación anterior sin destruirla todavía.

        self.componente_ia.ruta_base.mkdir(parents=True, exist_ok=True)  # Garantiza que exista el directorio administrado antes de colocar el runtime.
        shutil.move(str(ruta_runtime), str(self.componente_ia.ruta_ollama))  # Convierte la copia verificada en la instalación activa de TecNet Finder.
        return ruta_respaldo  # Permite al llamador restaurar el estado anterior si falla la siguiente fase.

    def _restaurar_runtime(self, ruta_respaldo: Path | None) -> None:
        if self.componente_ia.ruta_ollama.exists():
            shutil.rmtree(self.componente_ia.ruta_ollama, ignore_errors=True)  # Retira únicamente el runtime incompleto colocado por esta operación.

        if ruta_respaldo is not None and ruta_respaldo.exists():
            self.componente_ia.ruta_base.mkdir(parents=True, exist_ok=True)  # Recrea el directorio administrado si fue retirado durante la limpieza.
            shutil.move(str(ruta_respaldo), str(self.componente_ia.ruta_ollama))  # Recupera exactamente la instalación que existía antes del intento fallido.

    def _descargar_modelo(self, notificar: NotificadorProgreso | None) -> None:
        self._notificar(notificar, f"Descargando modelo {MODELO_IA}...", None)  # Utiliza progreso indeterminado porque Ollama divide el modelo en múltiples capas independientes.

        cuerpo = json.dumps(
            {
                "model": MODELO_IA,
                "stream": True,
            }
        ).encode("utf-8")  # Construye la solicitud oficial de descarga manteniendo el modelo definido por TecNet Finder.

        solicitud = urllib.request.Request(
            f"{URL_BASE_OLLAMA}/api/pull",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )  # Solicita el modelo exclusivamente a la instancia privada que acaba de iniciar la aplicación.

        completado = False  # Exige recibir explícitamente el estado final de éxito antes de aceptar la descarga.

        with self.abrir_url(solicitud, timeout=300) as respuesta:
            for linea in respuesta:
                if not linea.strip():
                    continue  # Ignora líneas vacías sin alterar el estado de la transferencia.

                evento = json.loads(linea.decode("utf-8"))  # Interpreta cada actualización emitida por la API de Ollama.

                if evento.get("error"):
                    raise ErrorInstalacionIA(f"Ollama no pudo descargar el modelo: {evento['error']}")  # Detiene inmediatamente la instalación ante un error reportado por el servidor.

                estado = str(evento.get("status", "")).strip()  # Recupera la descripción de la etapa actual sin depender de campos opcionales.

                if estado == "pulling manifest":
                    self._notificar(notificar, f"Preparando modelo {MODELO_IA}...", None)  # Informa la obtención de la descripción del modelo.
                elif estado.startswith("pulling "):
                    self._notificar(notificar, f"Descargando modelo {MODELO_IA}...", None)  # Mantiene una descripción sencilla mientras se reciben sus capas.
                elif estado == "verifying sha256 digest":
                    self._notificar(notificar, "Verificando integridad del modelo...", None)  # Indica que Ollama está comprobando los datos descargados.
                elif estado == "writing manifest":
                    self._notificar(notificar, "Registrando modelo local...", None)  # Informa la fase final antes de hacer disponible el modelo.
                elif estado == "success":
                    completado = True  # Registra únicamente el estado final reconocido como instalación correcta.

        if not completado:
            raise ErrorInstalacionIA(
                "Ollama terminó la conexión sin confirmar que el modelo hubiera sido instalado correctamente."
            )  # Evita aceptar una transferencia incompleta o interrumpida.

    def _retirar_directorio_vacio(self, ruta: Path) -> None:
        try:
            ruta.rmdir()  # Elimina solamente la carpeta Temporal cuando ya quedó completamente vacía.
        except OSError:
            pass  # Conserva la carpeta si todavía existe algún archivo temporal perteneciente a otra operación.

    def _notificar(
        self,
        notificar: NotificadorProgreso | None,
        etapa: str,
        porcentaje: int | None,
    ) -> None:
        if notificar is not None:
            notificar(etapa, porcentaje)  # Delega la presentación del progreso sin acoplar este gestor con PySide6.