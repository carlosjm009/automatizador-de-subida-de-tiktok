"""
config.py
Configuración central del proyecto: credenciales, constantes y rutas.
Todos los módulos importan de aquí para no repetir valores "hardcodeados".
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Carga las variables desde el archivo .env (en la raíz del proyecto)


def ensure_env_template():
    """Crea un .env de ejemplo si no existe y no está configurado."""
    env_path = BASE_DIR / ".env"
    example_path = BASE_DIR / ".env.example"
    if env_path.exists():
        return
    if example_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        env_path.write_text(
            "REDDIT_CLIENT_ID=tu_client_id_aqui\n"
            "REDDIT_CLIENT_SECRET=tu_secret_aqui\n"
            "REDDIT_USER_AGENT=windows:reddit_video_bot:v1.0 (by /u/TuUsuarioDeReddit)\n",
            encoding="utf-8",
        )


BASE_DIR = Path(__file__).resolve().parent
ensure_env_template()

# --- Credenciales de Reddit (Módulo 1) ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "RedditStoryBot/1.0")

# --- Subreddits a scrapear (añade/quita los que quieras) ---
SUBREDDITS = ["AmItheAsshole", "HistoriasDeReddit", "confesiones"]

# --- Filtro de longitud del cuerpo del post (en caracteres) ---
MIN_LENGTH = 500
MAX_LENGTH = 1000

# --- Rutas del proyecto ---
ASSETS_DIR = BASE_DIR / "assets"
AUDIO_DIR = ASSETS_DIR / "audio"
GAMEPLAY_DIR = ASSETS_DIR / "gameplay"       # Aquí pones tus clips de Minecraft/GTA
OUTPUT_DIR = ASSETS_DIR / "output"           # Vídeos finales (Fase 2)
USED_POSTS_FILE = BASE_DIR / "data" / "used_posts.json"

# Crea las carpetas necesarias si no existen
for _folder in (AUDIO_DIR, GAMEPLAY_DIR, OUTPUT_DIR, USED_POSTS_FILE.parent):
    _folder.mkdir(parents=True, exist_ok=True)

# --- Configuración TTS (Módulo 2) ---
# Prueba otras voces con: python modules/tts.py --list-voices
TTS_VOICE = "es-ES-AlvaroNeural"   # Alternativas: es-ES-ElviraNeural, es-MX-DaliaNeural
TTS_RATE = "+0%"                  # Velocidad, ej. "+10%" o "-10%"
TTS_PITCH = "+0Hz"                # Tono
