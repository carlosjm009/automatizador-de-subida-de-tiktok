"""
config.py
Configuración central del proyecto: constantes y rutas.
Todos los módulos importan de aquí para no repetir valores "hardcodeados".
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Carga las variables desde el archivo .env (en la raíz del proyecto)


BASE_DIR = Path(__file__).resolve().parent

# --- Rutas del proyecto ---
ASSETS_DIR = BASE_DIR / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"
GAMEPLAY_DIR = ASSETS_DIR / "gameplay"       # Aquí pones tus clips de Minecraft/GTA
OUTPUT_DIR = ASSETS_DIR / "output"           # Vídeos finales (Fase 2)
USED_POSTS_FILE = BASE_DIR / "data" / "used_posts.json"
LOG_DIR = BASE_DIR / "logs"                  # Logs del pipeline (usado por main.py y gui.py)

# Carpeta donde el usuario coloca sus historias como archivos .txt
# (una historia por archivo). Ver modules/story_loader.py para el formato.
STORIES_DIR = BASE_DIR / "data" / "stories"
USED_STORIES_DIR = STORIES_DIR / "usadas"

# Crea las carpetas necesarias si no existen
for _folder in (AUDIO_DIR, GAMEPLAY_DIR, OUTPUT_DIR, STORIES_DIR, USED_STORIES_DIR, USED_POSTS_FILE.parent, LOG_DIR):
    _folder.mkdir(parents=True, exist_ok=True)

# --- Configuración TTS (Módulo 2) ---
# Prueba otras voces con: python modules/tts.py --list-voices
TTS_VOICE = "es-ES-AlvaroNeural"   # Alternativas: es-ES-ElviraNeural, es-MX-DaliaNeural
TTS_RATE = "+0%"                  # Velocidad, ej. "+10%" o "-10%"
TTS_PITCH = "+0Hz"                # Tono

# --- Backend y publicación ---
PUBLISH_PLATFORM = os.getenv("PUBLISH_PLATFORM", "local").lower()
VIDEO_TITLE_TEMPLATE = os.getenv("VIDEO_TITLE_TEMPLATE", "Reddit Story: {title}")
YOUTUBE_CLIENT_SECRETS_FILE = BASE_DIR / "data" / "client_secrets.json"
CLIENT_SECRETS_FILE = YOUTUBE_CLIENT_SECRETS_FILE
YOUTUBE_TOKEN_FILE = BASE_DIR / "data" / "youtube_token.json"
PUBLICATION_LOG_FILE = BASE_DIR / "data" / "published_videos.json"
STORY_HISTORY_FILE = BASE_DIR / "data" / "story_history.json"

# --- Rutas adicionales ---
PROGRESS_FILE = BASE_DIR / "data" / "video_progress.json"
USED_GAMEPLAY_DIR = ASSETS_DIR / "used_gameplays"


def validate_backend_settings() -> list[str]:
    errors = []

    if PUBLISH_PLATFORM not in {"local", "youtube"}:
        errors.append(
            "PUBLISH_PLATFORM debe ser 'local' o 'youtube', no '" + PUBLISH_PLATFORM + "'."
        )

    if PUBLISH_PLATFORM == "youtube" and not YOUTUBE_CLIENT_SECRETS_FILE.exists():
        errors.append(
            f"Falta el archivo de credenciales de YouTube: {YOUTUBE_CLIENT_SECRETS_FILE}"
        )

    return errors


def save_env_config(updates: dict) -> None:
    """
    Guarda/modifica variables en el archivo .env.
    'updates' es un dict {CLAVE: valor}.
    Si el valor es None, elimina la clave del .env.
    """
    env_path = BASE_DIR / ".env"
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    # Primero actualizar líneas existentes
    modified_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                val = updates[key]
                if val is not None:
                    new_lines.append(f"{key}={val}")
                # Si es None, omitimos la línea (la borramos)
                modified_keys.add(key)
                continue
        new_lines.append(line)

    # Añadir claves nuevas que no existían
    for key, val in updates.items():
        if val is not None and key not in modified_keys:
            new_lines.append(f"{key}={val}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    load_dotenv(override=True)  # Recargar variables
