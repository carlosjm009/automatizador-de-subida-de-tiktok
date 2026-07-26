import os
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_youtube_credentials(token_path: str = "data/youtube_token.json") -> Optional[Credentials]:
    """Obtiene credenciales de YouTube desde un token guardado o inicia un flujo OAuth."""
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "data/client_secrets.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

    return creds


def publish_video(video_path: str, platform: str = "local", title: str = "Reddit Story") -> str:
    """Sube un vídeo a YouTube Shorts si están disponibles las credenciales."""
    video_path = str(Path(video_path).resolve())
    if platform == "local":
        print(f"📦 Publicación local simulada: {video_path}")
        return video_path

    if platform != "youtube":
        print(f"⚠️ Publicación aún no implementada para {platform}.")
        return video_path

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"No se encontró el vídeo para publicar: {video_path}")

    if not os.path.exists("data/client_secrets.json"):
        print("⚠️ Falta data/client_secrets.json para publicar en YouTube.")
        print("   Genera el archivo desde Google Cloud Console y vuelve a intentarlo.")
        return video_path

    try:
        creds = _get_youtube_credentials()
        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": title,
                "description": "Vídeo generado automáticamente por Reddit Story Bot",
                "tags": ["shorts", "reddit", "automation"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "private"},
        }
        media = MediaFileUpload(video_path, resumable=True, chunksize=-1, mimetype="video/mp4")
        request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        response = request.execute()
        print(f"✅ Vídeo subido a YouTube con ID: {response.get('id')}")
        return response.get("id", video_path)
    except Exception as exc:
        print(f"⚠️ Error al publicar en YouTube: {exc}")
        return video_path
