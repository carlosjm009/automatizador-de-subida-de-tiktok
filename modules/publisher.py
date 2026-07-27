import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from config import YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_TOKEN_FILE, PUBLICATION_LOG_FILE

logger = logging.getLogger("reddit_bot")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _load_publication_log() -> list:
    if os.path.exists(PUBLICATION_LOG_FILE):
        try:
            with open(PUBLICATION_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_publication_record(record: dict) -> None:
    os.makedirs(PUBLICATION_LOG_FILE.parent, exist_ok=True)
    history = _load_publication_log()
    history.append(record)
    with open(PUBLICATION_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def _get_youtube_credentials(token_path: Path = YOUTUBE_TOKEN_FILE) -> Optional[Credentials]:
    """Obtiene credenciales de YouTube desde un token guardado o inicia un flujo OAuth."""
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(YOUTUBE_CLIENT_SECRETS_FILE),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

    return creds


def publish_video(video_path: str, platform: str = "local", title: str = "Historia") -> str:
    """Sube un vídeo a YouTube Shorts si están disponibles las credenciales."""
    video_path = str(Path(video_path).resolve())
    if platform == "local":
        logger.info(f"📦 Publicación local simulada: {video_path}")
        return video_path

    if platform != "youtube":
        logger.warning(f"⚠️ Publicación aún no implementada para {platform}.")
        return video_path

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"No se encontró el vídeo para publicar: {video_path}")

    if not YOUTUBE_CLIENT_SECRETS_FILE.exists():
        logger.warning(f"⚠️ Falta {YOUTUBE_CLIENT_SECRETS_FILE} para publicar en YouTube.")
        logger.warning("   Genera el archivo desde Google Cloud Console y vuelve a intentarlo.")
        _save_publication_record({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "video_path": video_path,
            "published_target": video_path,
            "platform": platform,
            "title": title,
            "success": False,
            "error": "missing_client_secrets",
        })
        return video_path

    try:
        creds = _get_youtube_credentials()
        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": title,
                "description": "Vídeo generado automáticamente",
                "tags": ["shorts", "historias", "automation"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "private"},
        }
        media = MediaFileUpload(video_path, resumable=True, chunksize=-1, mimetype="video/mp4")
        request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        response = request.execute()
        published_id = response.get("id", video_path)
        logger.info(f"✅ Vídeo subido a YouTube con ID: {published_id}")
        _save_publication_record({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "video_path": video_path,
            "published_target": published_id,
            "platform": platform,
            "title": title,
            "success": True,
            "error": None,
        })
        return published_id
    except Exception as exc:
        logger.warning(f"⚠️ Error al publicar en YouTube: {exc}")
        _save_publication_record({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "video_path": video_path,
            "published_target": video_path,
            "platform": platform,
            "title": title,
            "success": False,
            "error": str(exc),
        })
        return video_path
