import logging  # Importa `logging` para utilizarlo en este archivo.
import os  # Importa `os` para utilizarlo en este archivo.
import yt_dlp  # Importa `yt_dlp` para utilizarlo en este archivo.
from yt_dlp.utils import MaxDownloadsReached  # Importa los nombres necesarios desde `yt_dlp.utils`.
from config import GAMEPLAY_DIR  # Importa los nombres necesarios desde `config`.

logger = logging.getLogger("reddit_bot")  # Guarda en `logger` el resultado de `logging.getLogger("reddit_bot")`.

CHANNELS_FILE = "data/channels.txt"  # Guarda en `CHANNELS_FILE` el resultado de `"data/channels.txt"`.
ARCHIVE_FILE = "data/downloaded_archive.txt"  # El bloc de notas secreto para no descargar dos veces el mismo vídeo

def ensure_gameplay_exists():  # Declara la funcion `ensure_gameplay_exists` y especifica sus parametros y tipo de retorno.
    """
    Comprueba si hay vídeos disponibles. Si la carpeta está vacía,
    acude a los canales de YouTube configurados y descarga automáticamente 
    el siguiente vídeo disponible que no se haya descargado antes.
    """
    valid_extensions = (".mp4", ".mov", ".avi", ".webm")  # Guarda en `valid_extensions` el resultado de `(".mp4", ".mov", ".avi", ".webm")`.
    os.makedirs(GAMEPLAY_DIR, exist_ok=True)  # Crea la ruta de carpetas indicada.
    os.makedirs("data", exist_ok=True)  # Crea la ruta de carpetas indicada.
    
    # Comprobar si ya hay vídeos listos para usar
    videos = [f for f in os.listdir(GAMEPLAY_DIR) if f.lower().endswith(valid_extensions)]  # Inicia la lista que se completa con los elementos de las lineas siguientes.
    
    if videos:  # Solo ejecuta el bloque siguiente si se cumple `videos`.
        logger.info(f"✅ Se han encontrado {len(videos)} vídeos de gameplay listos en la recámara.")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        return True  # Devuelve `True` al llamador y termina esta funcion.

    logger.warning("⚠️ La carpeta de gameplays está vacía. Activando piloto automático de descarga...")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
    
    # Si no existe el archivo de canales, lo creamos con una estructura de ejemplo
    if not os.path.exists(CHANNELS_FILE):  # Solo ejecuta el bloque siguiente si se cumple `not os.path.exists(CHANNELS_FILE)`.
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:  # Abre `open(CHANNELS_FILE, "w", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
            f.write("# Pega aquí URLs de canales de YouTube (ej: https://www.youtube.com/@Canal/videos)\n")  # Invoca `f.write` con los argumentos indicados.
        logger.warning(f"⚠️ Se ha creado '{CHANNELS_FILE}'. Por favor, pon ahí la URL de un canal de YouTube.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        return False  # Devuelve `False` al llamador y termina esta funcion.

    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:  # Abre `open(CHANNELS_FILE, "r", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]  # Inicia la lista que se completa con los elementos de las lineas siguientes.

    if not urls:  # Solo ejecuta el bloque siguiente si se cumple `not urls`.
        logger.error(f"❌ El archivo '{CHANNELS_FILE}' no contiene ninguna URL de canal válida.")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        return False  # Devuelve `False` al llamador y termina esta funcion.

    # Configuración inteligente de yt-dlp con historial de descargas
    ydl_opts = {  # Inicia el diccionario que se completa con los campos de las lineas siguientes.
        'format': 'bestvideo+bestaudio/best',  # Asocia la clave `format` con el valor indicado en este diccionario.
        'outtmpl': os.path.join(GAMEPLAY_DIR, '%(id)s.%(ext)s'),  # Asocia la clave `outtmpl` con el valor indicado en este diccionario.
        'merge_output_format': 'mp4',  # Asocia la clave `merge_output_format` con el valor indicado en este diccionario.
        'playlistend': 20,                # Ventana de búsqueda: mira hasta los 20 vídeos más recientes del canal
        'max_downloads': 1,               # Se detiene en cuanto descarga 1 vídeo NUEVO (los ya archivados se saltan sin contar)
        'download_archive': ARCHIVE_FILE, # Registra los IDs descargados para ignorarlos en el futuro
        'ignoreerrors': True,  # Asocia la clave `ignoreerrors` con el valor indicado en este diccionario.
    }  # Cierra el diccionario o conjunto abierto anteriormente.

    # Recorrer los canales de la lista hasta conseguir descargar uno nuevo
    for channel_url in urls:  # Recorre `urls` y asigna cada elemento a `channel_url`.
        logger.info(f"📥 Conectando con el canal: {channel_url}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # Abre `yt_dlp.YoutubeDL(ydl_opts) as ydl` y garantiza la liberacion del recurso al salir del bloque.
                ydl.download([channel_url])  # Inicia la descarga solicitada con yt-dlp.
        except MaxDownloadsReached:  # Captura `MaxDownloadsReached` para gestionar el error en este bloque.
            # yt-dlp lanza esta excepción cuando alcanza el límite de descargas.
            # Es una señal de ÉXITO (ya se descargó el vídeo), no de error.
            logger.info("✅ Límite de descarga alcanzado (1 vídeo nuevo).")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            logger.warning(f"⚠️ Error al intentar descargar del canal {channel_url}: {e}")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            continue  # Pasa a la siguiente iteracion del bucle actual.
        
        # Verificar si la descarga fue efectiva y ya hay vídeos en la carpeta
        current_videos = [f for f in os.listdir(GAMEPLAY_DIR) if f.lower().endswith(valid_extensions)]  # Inicia la lista que se completa con los elementos de las lineas siguientes.
        if current_videos:  # Solo ejecuta el bloque siguiente si se cumple `current_videos`.
            logger.info("✅ ¡Nuevo gameplay descargado e integrado automáticamente en el sistema!")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
            return True  # Devuelve `True` al llamador y termina esta funcion.

    logger.error("❌ No se pudo descargar ningún vídeo nuevo. Revisa los enlaces en 'data/channels.txt'.")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
    return False  # Devuelve `False` al llamador y termina esta funcion.
