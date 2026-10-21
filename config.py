"""
config.py
Configuración central del proyecto: constantes y rutas.
Todos los módulos importan de aquí para no repetir valores "hardcodeados".
"""

import os  # Importa `os` para utilizarlo en este archivo.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.
from dotenv import load_dotenv  # Importa los nombres necesarios desde `dotenv`.

load_dotenv()  # Carga las variables desde el archivo .env (en la raíz del proyecto)


BASE_DIR = Path(__file__).resolve().parent  # Guarda en `BASE_DIR` el resultado de `Path(__file__).resolve().parent`.

# --- Rutas del proyecto ---
ASSETS_DIR = BASE_DIR / "assets"  # Construye en `ASSETS_DIR` la ruta del archivo o carpeta indicada.
AUDIO_DIR = ASSETS_DIR / "audio"  # Construye en `AUDIO_DIR` la ruta del archivo o carpeta indicada.
GAMEPLAY_DIR = ASSETS_DIR / "gameplay"       # Aquí pones tus clips de Minecraft/GTA
OUTPUT_DIR = ASSETS_DIR / "output"           # Vídeos finales (Fase 2)
USED_POSTS_FILE = BASE_DIR / "data" / "used_posts.json"  # Construye en `USED_POSTS_FILE` la ruta del archivo o carpeta indicada.
LOG_DIR = BASE_DIR / "logs"                  # Logs del pipeline (usado por main.py y gui.py)

# Carpeta donde el usuario coloca sus historias como archivos .txt
# (una historia por archivo). Ver modules/story_loader.py para el formato.
STORIES_DIR = BASE_DIR / "data" / "stories"  # Construye en `STORIES_DIR` la ruta del archivo o carpeta indicada.
USED_STORIES_DIR = STORIES_DIR / "usadas"  # Construye en `USED_STORIES_DIR` la ruta del archivo o carpeta indicada.

# Crea las carpetas necesarias si no existen
for _folder in (AUDIO_DIR, GAMEPLAY_DIR, OUTPUT_DIR, STORIES_DIR, USED_STORIES_DIR, USED_POSTS_FILE.parent, LOG_DIR):  # Recorre `(AUDIO_DIR, GAMEPLAY_DIR, OUTPUT_DIR, STORIES_DIR, USED_STORIES_DIR, USED_POSTS_FILE.parent, LOG_DIR)` y asigna cada elemento a `_folder`.
    _folder.mkdir(parents=True, exist_ok=True)  # Crea la carpeta indicada si todavia no existe.

# --- Configuración TTS (Módulo 2) ---
# Prueba otras voces con: python modules/tts.py --list-voices
TTS_VOICE = "es-ES-AlvaroNeural"   # Alternativas: es-ES-ElviraNeural, es-MX-DaliaNeural
TTS_RATE = "+0%"                  # Velocidad, ej. "+10%" o "-10%"
TTS_PITCH = "+0Hz"                # Tono

# --- Backend y publicación ---
PUBLISH_PLATFORM = os.getenv("PUBLISH_PLATFORM", "local").lower()  # Lee la variable de entorno indicada y guarda el resultado en `PUBLISH_PLATFORM`.
VIDEO_TITLE_TEMPLATE = os.getenv("VIDEO_TITLE_TEMPLATE", "Reddit Story: {title}")  # Lee la variable de entorno indicada y guarda el resultado en `VIDEO_TITLE_TEMPLATE`.
YOUTUBE_CLIENT_SECRETS_FILE = BASE_DIR / "data" / "client_secrets.json"  # Construye en `YOUTUBE_CLIENT_SECRETS_FILE` la ruta del archivo o carpeta indicada.
CLIENT_SECRETS_FILE = YOUTUBE_CLIENT_SECRETS_FILE  # Guarda en `CLIENT_SECRETS_FILE` el resultado de `YOUTUBE_CLIENT_SECRETS_FILE`.
YOUTUBE_TOKEN_FILE = BASE_DIR / "data" / "youtube_token.json"  # Construye en `YOUTUBE_TOKEN_FILE` la ruta del archivo o carpeta indicada.
PUBLICATION_LOG_FILE = BASE_DIR / "data" / "published_videos.json"  # Construye en `PUBLICATION_LOG_FILE` la ruta del archivo o carpeta indicada.
STORY_HISTORY_FILE = BASE_DIR / "data" / "story_history.json"  # Construye en `STORY_HISTORY_FILE` la ruta del archivo o carpeta indicada.

# --- Rutas adicionales ---
PROGRESS_FILE = BASE_DIR / "data" / "video_progress.json"  # Construye en `PROGRESS_FILE` la ruta del archivo o carpeta indicada.
USED_GAMEPLAY_DIR = ASSETS_DIR / "used_gameplays"  # Construye en `USED_GAMEPLAY_DIR` la ruta del archivo o carpeta indicada.


def validate_backend_settings() -> list[str]:  # Declara la funcion `validate_backend_settings` y especifica sus parametros y tipo de retorno.
    errors = []  # Inicializa `errors` como una coleccion vacia para acumular datos.

    if PUBLISH_PLATFORM not in {"local", "youtube"}:  # Solo ejecuta el bloque siguiente si se cumple `PUBLISH_PLATFORM not in {"local", "youtube"}`.
        errors.append(  # Anade el elemento indicado a la coleccion.
            "PUBLISH_PLATFORM debe ser 'local' o 'youtube', no '" + PUBLISH_PLATFORM + "'."  # Aporta este texto a la lista, llamada o mensaje construido arriba.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    if PUBLISH_PLATFORM == "youtube" and not YOUTUBE_CLIENT_SECRETS_FILE.exists():  # Solo ejecuta el bloque siguiente si se cumple `PUBLISH_PLATFORM == "youtube" and not YOUTUBE_CLIENT_SECRETS_FILE.exists()`.
        errors.append(  # Anade el elemento indicado a la coleccion.
            f"Falta el archivo de credenciales de YouTube: {YOUTUBE_CLIENT_SECRETS_FILE}"  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    return errors  # Devuelve `errors` al llamador y termina esta funcion.


def save_env_config(updates: dict) -> None:  # Declara la funcion `save_env_config` y especifica sus parametros y tipo de retorno.
    """
    Guarda/modifica variables en el archivo .env.
    'updates' es un dict {CLAVE: valor}.
    Si el valor es None, elimina la clave del .env.
    """
    env_path = BASE_DIR / ".env"  # Construye en `env_path` la ruta del archivo o carpeta indicada.
    lines = []  # Inicializa `lines` como una coleccion vacia para acumular datos.
    if env_path.exists():  # Solo ejecuta el bloque siguiente si se cumple `env_path.exists()`.
        lines = env_path.read_text(encoding="utf-8").splitlines()  # Guarda en `lines` el resultado de `env_path.read_text(encoding="utf-8").splitlines()`.

    # Primero actualizar líneas existentes
    modified_keys = set()  # Inicializa `modified_keys` como una coleccion vacia para acumular datos.
    new_lines = []  # Inicializa `new_lines` como una coleccion vacia para acumular datos.
    for line in lines:  # Recorre `lines` y asigna cada elemento a `line`.
        stripped = line.strip()  # Guarda en `stripped` el resultado de `line.strip()`.
        if "=" in stripped and not stripped.startswith("#"):  # Solo ejecuta el bloque siguiente si se cumple `"=" in stripped and not stripped.startswith("#")`.
            key = stripped.split("=", 1)[0].strip()  # Guarda en `key` el resultado de `stripped.split("=", 1)[0].strip()`.
            if key in updates:  # Solo ejecuta el bloque siguiente si se cumple `key in updates`.
                val = updates[key]  # Guarda en `val` el resultado de `updates[key]`.
                if val is not None:  # Solo ejecuta el bloque siguiente si se cumple `val is not None`.
                    new_lines.append(f"{key}={val}")  # Anade el elemento indicado a la coleccion.
                # Si es None, omitimos la línea (la borramos)
                modified_keys.add(key)  # Anade el elemento indicado al conjunto.
                continue  # Pasa a la siguiente iteracion del bucle actual.
        new_lines.append(line)  # Anade el elemento indicado a la coleccion.

    # Añadir claves nuevas que no existían
    for key, val in updates.items():  # Recorre `updates.items()` y asigna cada elemento a `key, val`.
        if val is not None and key not in modified_keys:  # Solo ejecuta el bloque siguiente si se cumple `val is not None and key not in modified_keys`.
            new_lines.append(f"{key}={val}")  # Anade el elemento indicado a la coleccion.

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")  # Escribe el contenido generado en el archivo indicado.
    load_dotenv(override=True)  # Recargar variables
