import os
import shutil
import sys
import json
import logging
import random
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
    if not any(candidate.exists() for candidate in IMAGE_MAGICK_CANDIDATES):
        missing.append("ImageMagick")

    if missing:
        logger.error("Herramientas externas no encontradas:")
        for item in missing:
            logger.error(f"   - {item}")
        logger.error("Revisa la instalación de ffmpeg/ImageMagick antes de continuar.")

    return missing


from modules.scraper import get_top_story
from modules.tts import text_to_speech
from modules.video_processor import get_next_background_segment
from modules.video_editor import create_final_video
from modules.downloader import ensure_gameplay_exists
from config import SUBREDDITS, MIN_LENGTH, MAX_LENGTH


def get_next_subreddit(used_ids: set) -> str:
    """
    Selecciona un subreddit de la lista, prefiriendo aquellos de los que
    aún no hemos usado historias. Si todos tienen historias usadas, elige
    uno al azar.
    """
    # Cargar historial para ver de qué subreddits hemos sacado historias
    subreddit_history_file = BASE_DIR / "data" / "subreddit_history.json"
    subreddit_count = {}
    if subreddit_history_file.exists():
        try:
            with open(subreddit_history_file, "r", encoding="utf-8") as f:
                subreddit_count = json.load(f)
        except Exception:
            subreddit_count = {}

    # Ordenar subreddits por los que menos se han usado (ascendente)
    sorted_subreddits = sorted(SUBREDDITS, key=lambda sr: subreddit_count.get(sr, 0))
    return sorted_subreddits[0]


def update_subreddit_history(subreddit: str) -> None:
    """Incrementa el contador de uso de un subreddit."""
    subreddit_history_file = BASE_DIR / "data" / "subreddit_history.json"
    history = {}
    if subreddit_history_file.exists():
        try:
            with open(subreddit_history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {}
    history[subreddit] = history.get(subreddit, 0) + 1
    with open(subreddit_history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


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

    os.makedirs("assets/audio", exist_ok=True)
    os.makedirs("assets/output", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    logger.info("=" * 60)
    logger.info("🎬 BOT DE VÍDEOS 'REDDIT STORIES' — Iniciando pipeline")
    logger.info("=" * 60)

    # --- FASE 0: Comprobación automática de gameplays ---
    update_run_status("running", "check_gameplays", "Verificando disponibilidad de vídeos de fondo...", 0.1)
    logger.info("[0/4] Verificando disponibilidad de vídeos de fondo...")
    if not ensure_gameplay_exists():
        update_run_status("failed", "check_gameplays", "No hay gameplays disponibles. Revisa los canales configurados.", 0.1)
        logger.error("Operación detenida: Añade al menos un enlace de canal en 'data/channels.txt'.")
        return

    # --- Cargar posts ya usados ---
    used_ids = load_used_posts()
    logger.info(f"📚 Historial cargado: {len(used_ids)} posts ya procesados.")

    # --- FASE 1: Scraping con rotación de subreddits ---
    update_run_status("running", "scraping", "Buscando historia en Reddit...", 0.25)
    logger.info("[1/4] Buscando historia en Reddit...")
    try:
        # Intentar con cada subreddit hasta encontrar una historia válida
        story = None
        attempted_subreddits = []

        for _ in range(len(SUBREDDITS) * 2):  # Máximo 2 rondas completas
            subreddit = get_next_subreddit(used_ids)
            if subreddit in attempted_subreddits:
                # Si ya intentamos todos, rompemos el bucle
                if len(attempted_subreddits) >= len(SUBREDDITS):
                    break
                continue

            attempted_subreddits.append(subreddit)
            logger.info(f"🔍 Probando en r/{subreddit}...")

            story = get_top_story(
                subreddit_name=subreddit,
                limit_chars=(MIN_LENGTH, MAX_LENGTH),
                used_ids=used_ids,
            )

            if story is not None and story["id"] not in used_ids:
                logger.info(f"✅ Historia encontrada en r/{story.get('subreddit')}: {story.get('title')}")
                break
            else:
                story = None

        if story is None:
            update_run_status("failed", "scraping", "No se encontró una historia válida en ningún subreddit.", 0.25)
            logger.error("❌ No se encontró ninguna historia válida en ningún subreddit. Abortando.")
            return

    except Exception as e:
        update_run_status("failed", "scraping", f"Error en scraping: {e}", 0.25)
        logger.error(f"❌ Error en scraping: {e}")
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

        # Marcar la historia como usada y actualizar el historial de subreddits
        save_used_post(story["id"])
        update_subreddit_history(story["subreddit"])
        logger.info(f"✅ Historia {story['id']} marcada como completada en el historial.")

    except Exception as e:
        update_run_status("failed", "render", f"Error crítico en el montaje del vídeo: {e}", 0.9)
        logger.error(f"❌ Error crítico en el montaje del vídeo: {e}")
        logger.warning("⚠️ La historia NO ha sido marcada como usada para poder reintentarlo.")
        return

    update_run_status("completed", "finish", "Vídeo generado correctamente.", 1.0)


if __name__ == "__main__":
    main()