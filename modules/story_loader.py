"""
modules/story_loader.py

Fuente de historias local: en vez de conectarse a Reddit, el pipeline lee
historias que el propio usuario coloca como archivos .txt dentro de
STORIES_DIR (por defecto: data/stories/).

Formato esperado de cada archivo .txt:

    Título de la historia
    (línea en blanco, opcional)
    Resto del cuerpo de la historia, puede ocupar
    varias líneas y párrafos.

Si el archivo no tiene una línea en blanco separando título y cuerpo,
se asume que TODO el archivo es el cuerpo y se genera un título a partir
del nombre del archivo.

Cada archivo se identifica por su propio nombre (sin extensión), que se
usa como "id" único para el sistema de "historias ya usadas"
(data/used_posts.json). Si vuelves a ejecutar el bot, no se repetirá una
historia ya narrada mientras el .txt siga existiendo con el mismo nombre.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import STORIES_DIR, USED_STORIES_DIR, STORY_HISTORY_FILE

logger = logging.getLogger("reddit_bot")


def log_story_usage(story_id: str, title: str, source_file: Optional[Path | str] = None) -> None:
    """Guarda un registro de uso de la historia con fecha, título y destino."""
    STORY_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if STORY_HISTORY_FILE.exists():
        try:
            with open(STORY_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    record = {
        "id": story_id,
        "title": title,
        "used_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": str(source_file) if source_file else None,
        "status": "used",
    }
    history.append(record)

    with open(STORY_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def mark_story_as_used(story_id: str, title: str, source_file: Optional[Path | str] = None) -> None:
    """Mueve el archivo .txt de la historia a la carpeta de usadas tras completarla con éxito."""
    USED_STORIES_DIR.mkdir(parents=True, exist_ok=True)

    if source_file is None:
        source_path = STORIES_DIR / f"{story_id}.txt"
    else:
        source_path = Path(source_file)

    if not source_path.exists():
        logger.warning(f"⚠️ No se encontró el archivo de historia {source_path} para moverlo a usadas.")
    else:
        destination_path = USED_STORIES_DIR / source_path.name
        if destination_path.exists():
            destination_path.unlink()

        source_path.rename(destination_path)
        logger.info(f"📦 Historia movida a usadas: {destination_path}")

    log_story_usage(story_id, title, source_file or source_path)


def _parse_story_file(path: Path) -> dict:
    """Divide el contenido de un .txt en título + cuerpo."""
    raw = path.read_text(encoding="utf-8").strip()
    lines = raw.splitlines()

    if not lines:
        raise ValueError("el archivo está vacío")

    titulo = lines[0].strip()
    resto = lines[1:]

    # Si la línea siguiente al título está en blanco, la tratamos como
    # el separador título/cuerpo y la descartamos.
    if resto and resto[0].strip() == "":
        resto = resto[1:]

    cuerpo = "\n".join(resto).strip()

    if not cuerpo:
        # No había una segunda línea real de cuerpo: tratamos todo el
        # archivo como cuerpo y generamos un título a partir del nombre
        # del archivo (ej. "historia_01.txt" -> "Historia 01").
        cuerpo = titulo
        titulo = path.stem.replace("_", " ").replace("-", " ").strip().capitalize()

    return {"title": titulo, "body": cuerpo}


def get_next_story(used_ids: Optional[set] = None) -> Optional[dict]:
    """
    Busca en STORIES_DIR el primer archivo .txt (por orden alfabético) cuyo
    id (nombre de archivo sin extensión) no esté en used_ids.

    Args:
        used_ids: Set de IDs de historias ya usadas para evitar repetirlas.

    Returns:
        Dict con la historia lista para el resto del pipeline
        (id, title, body, texto_completo, length), o None si no hay ningún
        .txt nuevo disponible en la carpeta.
    """
    if used_ids is None:
        used_ids = set()

    STORIES_DIR.mkdir(parents=True, exist_ok=True)

    archivos = sorted(STORIES_DIR.glob("*.txt"))

    if not archivos:
        logger.warning(
            f"⚠️ No hay ningún archivo .txt en {STORIES_DIR}. "
            "Añade ahí tus historias (una por archivo) para que el bot pueda usarlas."
        )
        return None

    for archivo in archivos:
        story_id = archivo.stem

        if story_id in used_ids:
            continue

        try:
            parsed = _parse_story_file(archivo)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo leer '{archivo.name}': {e}. Se ignora y se prueba con el siguiente.")
            continue

        titulo = parsed["title"]
        cuerpo = parsed["body"]

        if not cuerpo:
            logger.warning(f"⚠️ '{archivo.name}' no tiene contenido útil, se ignora.")
            continue

        texto_completo = f"{titulo}. {cuerpo}"

        return {
            "id": story_id,
            "title": titulo,
            "body": cuerpo,
            "texto_completo": texto_completo,
            "length": len(texto_completo),
            "source_file": str(archivo),
        }

    logger.warning(f"⚠️ Todos los archivos .txt de {STORIES_DIR} ya han sido usados.")
    return None
