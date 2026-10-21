import os  # Importa `os` para utilizarlo en este archivo.
import shutil  # Importa `shutil` para utilizarlo en este archivo.
import sys  # Importa `sys` para utilizarlo en este archivo.
import json  # Importa `json` para utilizarlo en este archivo.
import logging  # Importa `logging` para utilizarlo en este archivo.
from datetime import datetime  # Importa los nombres necesarios desde `datetime`.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.
from dotenv import load_dotenv  # Importa los nombres necesarios desde `dotenv`.

# Parche de compatibilidad para MoviePy y las nuevas versiones de Pillow
import PIL.Image  # Importa `PIL.Image` para utilizarlo en este archivo.
if not hasattr(PIL.Image, 'ANTIALIAS'):  # Solo ejecuta el bloque siguiente si se cumple `not hasattr(PIL.Image, 'ANTIALIAS')`.
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS  # Guarda en `PIL.Image.ANTIALIAS` el resultado de `PIL.Image.LANCZOS`.

BASE_DIR = Path(__file__).resolve().parent  # Guarda en `BASE_DIR` el resultado de `Path(__file__).resolve().parent`.
IMAGE_MAGICK_CANDIDATES = [  # Inicia la lista que se completa con los elementos de las lineas siguientes.
    Path(r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"),  # Invoca `Path` con los argumentos indicados.
    Path(r"C:\Program Files\ImageMagick\magick.exe"),  # Invoca `Path` con los argumentos indicados.
]   # Cierra la lista o indice abierto anteriormente.

for candidate in IMAGE_MAGICK_CANDIDATES:  # Recorre `IMAGE_MAGICK_CANDIDATES` y asigna cada elemento a `candidate`.
    if candidate.exists():  # Solo ejecuta el bloque siguiente si se cumple `candidate.exists()`.
        os.environ["IMAGEMAGICK_BINARY"] = str(candidate)  # Ejecuta la operacion indicada por esta expresion.
        break  # Termina inmediatamente el bucle actual.

# --- Configuración de logging ---
LOG_DIR = BASE_DIR / "logs"  # Construye en `LOG_DIR` la ruta del archivo o carpeta indicada.
LOG_DIR.mkdir(exist_ok=True)  # Crea la carpeta indicada si todavia no existe.
LOG_FILE = LOG_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"  # Guarda en `LOG_FILE` el resultado de `LOG_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"`.

logging.basicConfig(  # Configura el nivel, formato y destinos del registro.
    level=logging.INFO,  # Guarda en `level` el resultado de `logging.INFO,`.
    format="%(asctime)s [%(levelname)s] %(message)s",  # Guarda en `format` el resultado de `"%(asctime)s [%(levelname)s] %(message)s",`.
    handlers=[  # Guarda en `handlers` el resultado de `[`.
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # Invoca `logging.FileHandler` con los argumentos indicados.
        logging.StreamHandler(sys.stdout),  # Invoca `logging.StreamHandler` con los argumentos indicados.
    ],   # Cierra la lista o indice abierto anteriormente.
)  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
logger = logging.getLogger("reddit_bot")  # Guarda en `logger` el resultado de `logging.getLogger("reddit_bot")`.

# --- Archivos de datos ---
USED_POSTS_FILE = BASE_DIR / "data" / "used_posts.json"  # Construye en `USED_POSTS_FILE` la ruta del archivo o carpeta indicada.
STATUS_FILE = BASE_DIR / "data" / "run_status.json"  # Construye en `STATUS_FILE` la ruta del archivo o carpeta indicada.


def update_run_status(status: str, stage: str, message: str, progress: float | None = None) -> None:  # Declara la funcion `update_run_status` y especifica sus parametros y tipo de retorno.
    """Guarda el estado actual de ejecución para que la GUI lo pueda mostrar."""  # Ejecuta la operacion indicada por esta expresion.
    STATUS_FILE.parent.mkdir(exist_ok=True)  # Crea la carpeta indicada si todavia no existe.
    payload = {  # Inicia el diccionario que se completa con los campos de las lineas siguientes.
        "status": status,  # Asocia la clave `status` con el valor indicado en este diccionario.
        "stage": stage,  # Asocia la clave `stage` con el valor indicado en este diccionario.
        "message": message,  # Asocia la clave `message` con el valor indicado en este diccionario.
        "progress": progress,  # Asocia la clave `progress` con el valor indicado en este diccionario.
        "updated_at": datetime.now().isoformat(timespec="seconds"),  # Asocia la clave `updated_at` con el valor indicado en este diccionario.
    }  # Cierra el diccionario o conjunto abierto anteriormente.
    STATUS_FILE.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")  # Escribe el contenido generado en el archivo indicado.


def load_used_posts() -> set:  # Declara la funcion `load_used_posts` y especifica sus parametros y tipo de retorno.
    """Carga el set de IDs de posts ya usados desde el archivo JSON."""  # Ejecuta la operacion indicada por esta expresion.
    if USED_POSTS_FILE.exists():  # Solo ejecuta el bloque siguiente si se cumple `USED_POSTS_FILE.exists()`.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            with open(USED_POSTS_FILE, "r", encoding="utf-8") as f:  # Abre `open(USED_POSTS_FILE, "r", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
                data = json.load(f)  # Guarda en `data` el resultado de `json.load(f)`.
                return set(data.get("used_ids", []))  # Devuelve `set(data.get("used_ids", []))` al llamador y termina esta funcion.
        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            logger.warning(f"No se pudo leer {USED_POSTS_FILE}: {e}. Empezando de cero.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            return set()  # Devuelve `set()` al llamador y termina esta funcion.
    return set()  # Devuelve `set()` al llamador y termina esta funcion.


def save_used_post(post_id: str) -> None:  # Declara la funcion `save_used_post` y especifica sus parametros y tipo de retorno.
    """Añade un post ID al archivo de usados y lo guarda."""  # Ejecuta la operacion indicada por esta expresion.
    used_ids = load_used_posts()  # Guarda en `used_ids` el resultado de `load_used_posts()`.
    used_ids.add(post_id)  # Anade el elemento indicado al conjunto.
    os.makedirs(USED_POSTS_FILE.parent, exist_ok=True)  # Crea la ruta de carpetas indicada.
    with open(USED_POSTS_FILE, "w", encoding="utf-8") as f:  # Abre `open(USED_POSTS_FILE, "w", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
        json.dump({"used_ids": sorted(list(used_ids))}, f, indent=4, ensure_ascii=False)  # Serializa los datos como JSON en el archivo indicado.
    logger.info(f"📝 Post {post_id} marcado como usado.")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.


def check_prerequisites() -> list[str]:  # Declara la funcion `check_prerequisites` y especifica sus parametros y tipo de retorno.
    """Comprueba que las herramientas externas necesarias estén disponibles.

    Returns:
        Lista de herramientas que faltan. Si la lista está vacía, todo está bien.
    """
    missing = []  # Inicializa `missing` como una coleccion vacia para acumular datos.

    if shutil.which("ffmpeg") is None:  # Solo ejecuta el bloque siguiente si se cumple `shutil.which("ffmpeg") is None`.
        missing.append("ffmpeg")  # Anade el elemento indicado a la coleccion.
    imagemagick_found = (  # Guarda en `imagemagick_found` el resultado de `(`.
        shutil.which("magick") is not None  # Invoca `shutil.which` con los argumentos indicados.
        or any(candidate.exists() for candidate in IMAGE_MAGICK_CANDIDATES)  # Continua la expresion abierta arriba con este valor o argumento.
    )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
    if not imagemagick_found:  # Solo ejecuta el bloque siguiente si se cumple `not imagemagick_found`.
        missing.append("ImageMagick")  # Anade el elemento indicado a la coleccion.

    if missing:  # Solo ejecuta el bloque siguiente si se cumple `missing`.
        logger.error("Herramientas externas no encontradas:")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        for item in missing:  # Recorre `missing` y asigna cada elemento a `item`.
            logger.error(f"   - {item}")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        logger.error("Revisa la instalación de ffmpeg/ImageMagick antes de continuar.")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.

    return missing  # Devuelve `missing` al llamador y termina esta funcion.


from modules.story_loader import get_next_story, mark_story_as_used  # Importa los nombres necesarios desde `modules.story_loader`.
from modules.tts import text_to_speech  # Importa los nombres necesarios desde `modules.tts`.
from modules.video_editor import create_final_video, get_next_background_segment, commit_background_progress  # Importa los nombres necesarios desde `modules.video_editor`.
from modules.downloader import ensure_gameplay_exists  # Importa los nombres necesarios desde `modules.downloader`.
from modules.publisher import publish_video  # Importa los nombres necesarios desde `modules.publisher`.
from config import (  # Importa los nombres necesarios desde `config`.
    STORIES_DIR,  # Continua la expresion abierta arriba con este valor o argumento.
    PUBLISH_PLATFORM,  # Continua la expresion abierta arriba con este valor o argumento.
    VIDEO_TITLE_TEMPLATE,  # Continua la expresion abierta arriba con este valor o argumento.
    validate_backend_settings,  # Continua la expresion abierta arriba con este valor o argumento.
)  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.


def main():  # Declara la funcion `main` y especifica sus parametros y tipo de retorno.
    load_dotenv()  # Invoca `load_dotenv` con los argumentos indicados.
    update_run_status("running", "startup", "Iniciando pipeline...", 0.0)  # Invoca `update_run_status` con los argumentos indicados.

    missing_tools = check_prerequisites()  # Guarda en `missing_tools` el resultado de `check_prerequisites()`.
    if missing_tools:  # Solo ejecuta el bloque siguiente si se cumple `missing_tools`.
        missing_text = ", ".join(missing_tools)  # Guarda en `missing_text` el resultado de `", ".join(missing_tools)`.
        update_run_status(  # Invoca `update_run_status` con los argumentos indicados.
            "failed",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            "prerequisites",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
            f"Faltan herramientas: {missing_text}.",  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
            0.0,  # Continua la expresion abierta arriba con este valor o argumento.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        return  # Termina esta funcion sin devolver un valor explicito.

    config_errors = validate_backend_settings()  # Guarda en `config_errors` el resultado de `validate_backend_settings()`.
    if config_errors:  # Solo ejecuta el bloque siguiente si se cumple `config_errors`.
        error_text = " | ".join(config_errors)  # Guarda en `error_text` el resultado de `" | ".join(config_errors)`.
        update_run_status("failed", "configuration", error_text, 0.0)  # Invoca `update_run_status` con los argumentos indicados.
        logger.error(f"❌ Configuración de backend inválida: {error_text}")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        return  # Termina esta funcion sin devolver un valor explicito.

    os.makedirs("assets/audio", exist_ok=True)  # Crea la ruta de carpetas indicada.
    os.makedirs("assets/output", exist_ok=True)  # Crea la ruta de carpetas indicada.
    os.makedirs("data", exist_ok=True)  # Crea la ruta de carpetas indicada.

    logger.info("=" * 60)  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    logger.info("🎬 BOT DE VÍDEOS DE HISTORIAS — Iniciando pipeline")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    logger.info("=" * 60)  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

    # --- FASE 0: Comprobación automática de gameplays ---
    update_run_status("running", "check_gameplays", "Verificando disponibilidad de vídeos de fondo...", 0.1)  # Invoca `update_run_status` con los argumentos indicados.
    logger.info("[0/4] Verificando disponibilidad de vídeos de fondo...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    if not ensure_gameplay_exists():  # Solo ejecuta el bloque siguiente si se cumple `not ensure_gameplay_exists()`.
        update_run_status("failed", "check_gameplays", "No hay gameplays disponibles. Revisa los canales configurados.", 0.1)  # Invoca `update_run_status` con los argumentos indicados.
        logger.error("Operación detenida: Añade al menos un enlace de canal en 'data/channels.txt'.")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        return  # Termina esta funcion sin devolver un valor explicito.

    # --- Cargar historias ya usadas ---
    used_ids = load_used_posts()  # Guarda en `used_ids` el resultado de `load_used_posts()`.
    logger.info(f"📚 Historial cargado: {len(used_ids)} historias ya procesadas.")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

    # --- FASE 1: Lectura de historia local (data/stories/*.txt) ---
    update_run_status("running", "loading_story", f"Buscando historia nueva en {STORIES_DIR}...", 0.25)  # Invoca `update_run_status` con los argumentos indicados.
    logger.info(f"[1/4] Buscando historia nueva en {STORIES_DIR}...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        story = get_next_story(used_ids=used_ids)  # Guarda en `story` el resultado de `get_next_story(used_ids=used_ids)`.

        if story is None:  # Solo ejecuta el bloque siguiente si se cumple `story is None`.
            update_run_status(  # Invoca `update_run_status` con los argumentos indicados.
                "failed",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "loading_story",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                f"No hay historias nuevas disponibles en {STORIES_DIR}.",  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
                0.25,  # Continua la expresion abierta arriba con este valor o argumento.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
            logger.error(  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
                f"❌ No se encontró ninguna historia nueva en {STORIES_DIR}. "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
                "Añade un .txt con una historia (o borra data/used_posts.json si quieres repetir alguna). Abortando."  # Ejecuta la operacion indicada por esta expresion.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
            return  # Termina esta funcion sin devolver un valor explicito.

        logger.info(f"✅ Historia encontrada: '{story.get('title')}' (archivo: {story['id']}.txt)")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        update_run_status("failed", "loading_story", f"Error cargando historia: {e}", 0.25)  # Invoca `update_run_status` con los argumentos indicados.
        logger.error(f"❌ Error cargando historia: {e}")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        return  # Termina esta funcion sin devolver un valor explicito.

    # --- FASE 2: Texto a Voz ---
    update_run_status("running", "tts", "Generando audio con edge-tts...", 0.5)  # Invoca `update_run_status` con los argumentos indicados.
    logger.info("[2/4] Generando audio con edge-tts...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Guarda en `timestamp` el resultado de `datetime.now().strftime("%Y%m%d_%H%M%S")`.
        audio_filename = f"{story['id']}_{timestamp}.mp3"  # Guarda en `audio_filename` el resultado de `f"{story['id']}_{timestamp}.mp3"`.

        audio_path = text_to_speech(  # Guarda en `audio_path` el resultado de `text_to_speech(`.
            title=story["title"],  # Guarda en `title` el resultado de `story["title"],`.
            body=story["body"],  # Guarda en `body` el resultado de `story["body"],`.
            output_filename=audio_filename  # Guarda en `output_filename` el resultado de `audio_filename`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        logger.info(f"✅ Audio generado: {audio_path}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        update_run_status("failed", "tts", f"Error generando audio: {e}", 0.5)  # Invoca `update_run_status` con los argumentos indicados.
        logger.error(f"❌ Error generando audio: {e}")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        return  # Termina esta funcion sin devolver un valor explicito.

    # --- FASE 3: Selección de Fondo con Memoria Secuencial ---
    update_run_status("running", "background", "Consultando memoria de vídeo y calculando tramo...", 0.75)  # Invoca `update_run_status` con los argumentos indicados.
    logger.info("[3/4] Consultando memoria de vídeo y calculando tramo...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        background_clip_path, start_time, end_time = get_next_background_segment(audio_path)  # Ejecuta la operacion indicada por esta expresion.
        logger.info(f"✅ Fondo seleccionado: {os.path.basename(background_clip_path)}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        update_run_status("failed", "background", f"Error gestionando el fondo: {e}", 0.75)  # Invoca `update_run_status` con los argumentos indicados.
        logger.error(f"❌ Error gestionando el fondo: {e}")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        return  # Termina esta funcion sin devolver un valor explicito.

    # --- FASE 4: Montaje, Subtítulos y Fraccionamiento ---
    update_run_status("running", "render", "Iniciando montaje de vídeo y subtítulos (esto puede tardar)...", 0.9)  # Invoca `update_run_status` con los argumentos indicados.
    logger.info("[4/4] Iniciando montaje de vídeo y subtítulos (esto puede tardar)...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        rutas_generadas = create_final_video(  # Guarda en `rutas_generadas` el resultado de `create_final_video(`.
            audio_path=audio_path,  # Guarda en `audio_path` el resultado de `audio_path,`.
            background_clip_path=background_clip_path,  # Guarda en `background_clip_path` el resultado de `background_clip_path,`.
            start_time=start_time,  # Guarda en `start_time` el resultado de `start_time,`.
            end_time=end_time,  # Guarda en `end_time` el resultado de `end_time,`.
            story=story  # Guarda en `story` el resultado de `story`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

        logger.info("✅ ¡Vídeo completado con éxito! Se han generado las siguientes partes:")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        for ruta in rutas_generadas:  # Recorre `rutas_generadas` y asigna cada elemento a `ruta`.
            logger.info(f"   📁 {ruta}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

        # Solo ahora, con el vídeo ya generado con éxito, confirmamos en disco
        # el tramo de gameplay consumido (ver modules/video_editor.py). Si el
        # pipeline falla antes de llegar aquí, el tramo NO se pierde.
        commit_background_progress(background_clip_path, end_time)  # Invoca `commit_background_progress` con los argumentos indicados.

        logger.info("📤 Publicando los vídeos generados según la configuración de backend...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        published_targets = []  # Inicializa `published_targets` como una coleccion vacia para acumular datos.
        for ruta in rutas_generadas:  # Recorre `rutas_generadas` y asigna cada elemento a `ruta`.
            published_target = publish_video(  # Guarda en `published_target` el resultado de `publish_video(`.
                video_path=ruta,  # Guarda en `video_path` el resultado de `ruta,`.
                platform=PUBLISH_PLATFORM,  # Guarda en `platform` el resultado de `PUBLISH_PLATFORM,`.
                title=VIDEO_TITLE_TEMPLATE.format(title=story.get("title", "Historia sin título")),  # Guarda en `title` el resultado de `VIDEO_TITLE_TEMPLATE.format(title=story.get("title", "Historia sin título")),`.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
            published_targets.append(published_target)  # Anade el elemento indicado a la coleccion.
            logger.info(f"   ✅ Publicado: {published_target}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

        # Marcar la historia como usada y mover su .txt a la carpeta de usadas
        save_used_post(story["id"])  # Invoca `save_used_post` con los argumentos indicados.
        mark_story_as_used(story["id"], story.get("title", story["id"]), story.get("source_file"))  # Invoca `mark_story_as_used` con los argumentos indicados.
        logger.info(f"✅ Historia {story['id']} marcada como completada en el historial.")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        update_run_status("failed", "render", f"Error crítico en el montaje del vídeo: {e}", 0.9)  # Invoca `update_run_status` con los argumentos indicados.
        logger.error(f"❌ Error crítico en el montaje del vídeo: {e}")  # Registra el mensaje de error para que aparezca en la consola o en el archivo de log.
        logger.warning("⚠️ La historia NO ha sido marcada como usada para poder reintentarlo.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        return  # Termina esta funcion sin devolver un valor explicito.

    update_run_status("completed", "finish", "Vídeo generado correctamente.", 1.0)  # Invoca `update_run_status` con los argumentos indicados.


if __name__ == "__main__":  # Solo ejecuta el bloque siguiente si se cumple `__name__ == "__main__"`.
    main()  # Invoca `main` con los argumentos indicados.