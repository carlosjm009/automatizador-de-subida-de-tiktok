import os
import shutil
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Parche de compatibilidad para MoviePy y las nuevas versiones de Pillow
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

BASE_DIR = Path(__file__).resolve().parent
IMAGE_MAGICK_CANDIDATES = [
    Path(r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"),
    Path(r"C:\Program Files\ImageMagick\magick.exe"),
]

for candidate in IMAGE_MAGICK_CANDIDATES:
    if candidate.exists():
        os.environ["IMAGEMAGICK_BINARY"] = str(candidate)
        break

# --- Configuración de logging ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("reddit_bot")

# --- Archivos de datos ---
USED_POSTS_FILE = BASE_DIR / "data" / "used_posts.json"
STATUS_FILE = BASE_DIR / "data" / "run_status.json"


def update_run_status(status: str, stage: str, message: str, progress: float | None = None) -> None:
    """Guarda el estado actual de ejecución para que la GUI lo pueda mostrar."""
    STATUS_FILE.parent.mkdir(exist_ok=True)
    payload = {
        "status": status,
        "stage": stage,
        "message": message,
        "progress": progress,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=4, ensure_ascii=False), encoding="utf-8")


def load_used_posts() -> set:
    """Carga el set de IDs de posts ya usados desde el archivo JSON."""
    if USED_POSTS_FILE.exists():
        try:
            with open(USED_POSTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("used_ids", []))
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"No se pudo leer {USED_POSTS_FILE}: {e}. Empezando de cero.")
            return set()
    return set()


def save_used_post(post_id: str) -> None:
    """Añade un post ID al archivo de usados y lo guarda."""
    used_ids = load_used_posts()
    used_ids.add(post_id)
    os.makedirs(USED_POSTS_FILE.parent, exist_ok=True)
    with open(USED_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"used_ids": sorted(list(used_ids))}, f, indent=4, ensure_ascii=False)
    logger.info(f"📝 Post {post_id} marcado como usado.")


def check_prerequisites() -> list[str]:
    """Comprueba que las herramientas externas necesarias estén disponibles.

    Returns:
        Lista de herramientas que faltan. Si la lista está vacía, todo está bien.
    """
    missing = []

    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg")
    imagemagick_found = (
        shutil.which("magick") is not None
        or any(candidate.exists() for candidate in IMAGE_MAGICK_CANDIDATES)
    )
    if not imagemagick_found:
        missing.append("ImageMagick")

    if missing:
        logger.error("Herramientas externas no encontradas:")
        for item in missing:
            logger.error(f"   - {item}")
        logger.error("Revisa la instalación de ffmpeg/ImageMagick antes de continuar.")

    return missing


from modules.story_loader import get_next_story, mark_story_as_used
from modules.tts import text_to_speech
from modules.video_processor import get_next_background_segment
from modules.video_editor import create_final_video
from modules.downloader import ensure_gameplay_exists
from modules.publisher import publish_video
from config import (
    STORIES_DIR,
    PUBLISH_PLATFORM,
    VIDEO_TITLE_TEMPLATE,
    validate_backend_settings,
)


def main():
    load_dotenv()
    update_run_status("running", "startup", "Iniciando pipeline...", 0.0)

    missing_tools = check_prerequisites()
    if missing_tools:
        missing_text = ", ".join(missing_tools)
        update_run_status(
            "failed",
            "prerequisites",
            f"Faltan herramientas: {missing_text}.",
            0.0,
        )
        return

    config_errors = validate_backend_settings()
    if config_errors:
        error_text = " | ".join(config_errors)
        update_run_status("failed", "configuration", error_text, 0.0)
        logger.error(f"❌ Configuración de backend inválida: {error_text}")
        return

    os.makedirs("assets/audio", exist_ok=True)
    os.makedirs("assets/output", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    logger.info("=" * 60)
    logger.info("🎬 BOT DE VÍDEOS DE HISTORIAS — Iniciando pipeline")
    logger.info("=" * 60)

    # --- FASE 0: Comprobación automática de gameplays ---
    update_run_status("running", "check_gameplays", "Verificando disponibilidad de vídeos de fondo...", 0.1)
    logger.info("[0/4] Verificando disponibilidad de vídeos de fondo...")
    if not ensure_gameplay_exists():
        update_run_status("failed", "check_gameplays", "No hay gameplays disponibles. Revisa los canales configurados.", 0.1)
        logger.error("Operación detenida: Añade al menos un enlace de canal en 'data/channels.txt'.")
        return

    # --- Cargar historias ya usadas ---
    used_ids = load_used_posts()
    logger.info(f"📚 Historial cargado: {len(used_ids)} historias ya procesadas.")

    # --- FASE 1: Lectura de historia local (data/stories/*.txt) ---
    update_run_status("running", "loading_story", f"Buscando historia nueva en {STORIES_DIR}...", 0.25)
    logger.info(f"[1/4] Buscando historia nueva en {STORIES_DIR}...")
    try:
        story = get_next_story(used_ids=used_ids)

        if story is None:
            update_run_status(
                "failed",
                "loading_story",
                f"No hay historias nuevas disponibles en {STORIES_DIR}.",
                0.25,
            )
            logger.error(
                f"❌ No se encontró ninguna historia nueva en {STORIES_DIR}. "
                "Añade un .txt con una historia (o borra data/used_posts.json si quieres repetir alguna). Abortando."
            )
            return

        logger.info(f"✅ Historia encontrada: '{story.get('title')}' (archivo: {story['id']}.txt)")

    except Exception as e:
        update_run_status("failed", "loading_story", f"Error cargando historia: {e}", 0.25)
        logger.error(f"❌ Error cargando historia: {e}")
        return

    # --- FASE 2: Texto a Voz ---
    update_run_status("running", "tts", "Generando audio con edge-tts...", 0.5)
    logger.info("[2/4] Generando audio con edge-tts...")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"{story['id']}_{timestamp}.mp3"

        audio_path = text_to_speech(
            title=story["title"],
            body=story["body"],
            output_filename=audio_filename
        )
        logger.info(f"✅ Audio generado: {audio_path}")
    except Exception as e:
        update_run_status("failed", "tts", f"Error generando audio: {e}", 0.5)
        logger.error(f"❌ Error generando audio: {e}")
        return

    # --- FASE 3: Selección de Fondo con Memoria Secuencial ---
    update_run_status("running", "background", "Consultando memoria de vídeo y calculando tramo...", 0.75)
    logger.info("[3/4] Consultando memoria de vídeo y calculando tramo...")
    try:
        background_clip_path, start_time, end_time = get_next_background_segment(audio_path)
        logger.info(f"✅ Fondo seleccionado: {os.path.basename(background_clip_path)}")
    except Exception as e:
        update_run_status("failed", "background", f"Error gestionando el fondo: {e}", 0.75)
        logger.error(f"❌ Error gestionando el fondo: {e}")
        return

    # --- FASE 4: Montaje, Subtítulos y Fraccionamiento ---
    update_run_status("running", "render", "Iniciando montaje de vídeo y subtítulos (esto puede tardar)...", 0.9)
    logger.info("[4/4] Iniciando montaje de vídeo y subtítulos (esto puede tardar)...")
    try:
        rutas_generadas = create_final_video(
            audio_path=audio_path,
            background_clip_path=background_clip_path,
            start_time=start_time,
            end_time=end_time,
            story=story
        )

        logger.info("✅ ¡Vídeo completado con éxito! Se han generado las siguientes partes:")
        for ruta in rutas_generadas:
            logger.info(f"   📁 {ruta}")

        logger.info("📤 Publicando los vídeos generados según la configuración de backend...")
        published_targets = []
        for ruta in rutas_generadas:
            published_target = publish_video(
                video_path=ruta,
                platform=PUBLISH_PLATFORM,
                title=VIDEO_TITLE_TEMPLATE.format(title=story.get("title", "Historia sin título")),
            )
            published_targets.append(published_target)
            logger.info(f"   ✅ Publicado: {published_target}")

        # Marcar la historia como usada y mover su .txt a la carpeta de usadas
        save_used_post(story["id"])
        mark_story_as_used(story["id"], story.get("title", story["id"]), story.get("source_file"))
        logger.info(f"✅ Historia {story['id']} marcada como completada en el historial.")

    except Exception as e:
        update_run_status("failed", "render", f"Error crítico en el montaje del vídeo: {e}", 0.9)
        logger.error(f"❌ Error crítico en el montaje del vídeo: {e}")
        logger.warning("⚠️ La historia NO ha sido marcada como usada para poder reintentarlo.")
        return

    update_run_status("completed", "finish", "Vídeo generado correctamente.", 1.0)


if __name__ == "__main__":
    main()