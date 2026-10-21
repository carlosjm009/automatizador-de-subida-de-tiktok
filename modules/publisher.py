import json  # Importa `json` para utilizarlo en este archivo.
import logging  # Importa `logging` para utilizarlo en este archivo.
import os  # Importa `os` para utilizarlo en este archivo.
from datetime import datetime  # Importa los nombres necesarios desde `datetime`.
from pathlib import Path  # Importa los nombres necesarios desde `pathlib`.
from typing import Optional  # Importa los nombres necesarios desde `typing`.

from googleapiclient.discovery import build  # Importa los nombres necesarios desde `googleapiclient.discovery`.
from googleapiclient.http import MediaFileUpload  # Importa los nombres necesarios desde `googleapiclient.http`.
from google.oauth2.credentials import Credentials  # Importa los nombres necesarios desde `google.oauth2.credentials`.
from google_auth_oauthlib.flow import InstalledAppFlow  # Importa los nombres necesarios desde `google_auth_oauthlib.flow`.
from google.auth.transport.requests import Request  # Importa los nombres necesarios desde `google.auth.transport.requests`.

from config import YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_TOKEN_FILE, PUBLICATION_LOG_FILE  # Importa los nombres necesarios desde `config`.

logger = logging.getLogger("reddit_bot")  # Guarda en `logger` el resultado de `logging.getLogger("reddit_bot")`.

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]  # Inicia la lista que se completa con los elementos de las lineas siguientes.


def _load_publication_log() -> list:  # Declara la funcion `_load_publication_log` y especifica sus parametros y tipo de retorno.
    if os.path.exists(PUBLICATION_LOG_FILE):  # Solo ejecuta el bloque siguiente si se cumple `os.path.exists(PUBLICATION_LOG_FILE)`.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            with open(PUBLICATION_LOG_FILE, "r", encoding="utf-8") as f:  # Abre `open(PUBLICATION_LOG_FILE, "r", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
                return json.load(f)  # Devuelve `json.load(f)` al llamador y termina esta funcion.
        except Exception:  # Captura `Exception` para gestionar el error en este bloque.
            return []  # Devuelve `[]` al llamador y termina esta funcion.
    return []  # Devuelve `[]` al llamador y termina esta funcion.


def _save_publication_record(record: dict) -> None:  # Declara la funcion `_save_publication_record` y especifica sus parametros y tipo de retorno.
    os.makedirs(PUBLICATION_LOG_FILE.parent, exist_ok=True)  # Crea la ruta de carpetas indicada.
    history = _load_publication_log()  # Guarda en `history` el resultado de `_load_publication_log()`.
    history.append(record)  # Anade el elemento indicado a la coleccion.
    with open(PUBLICATION_LOG_FILE, "w", encoding="utf-8") as f:  # Abre `open(PUBLICATION_LOG_FILE, "w", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
        json.dump(history, f, indent=4, ensure_ascii=False)  # Serializa los datos como JSON en el archivo indicado.


def _get_youtube_credentials(token_path: Path = YOUTUBE_TOKEN_FILE) -> Optional[Credentials]:  # Declara la funcion `_get_youtube_credentials` y especifica sus parametros y tipo de retorno.
    """Obtiene credenciales de YouTube desde un token guardado o inicia un flujo OAuth."""  # Ejecuta la operacion indicada por esta expresion.
    creds = None  # Guarda en `creds` el resultado de `None`.
    if token_path.exists():  # Solo ejecuta el bloque siguiente si se cumple `token_path.exists()`.
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)  # Guarda en `creds` el resultado de `Credentials.from_authorized_user_file(str(token_path), SCOPES)`.

    if not creds or not creds.valid:  # Solo ejecuta el bloque siguiente si se cumple `not creds or not creds.valid`.
        if creds and creds.expired and creds.refresh_token:  # Solo ejecuta el bloque siguiente si se cumple `creds and creds.expired and creds.refresh_token`.
            creds.refresh(Request())  # Invoca `creds.refresh` con los argumentos indicados.
        else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
            flow = InstalledAppFlow.from_client_secrets_file(  # Guarda en `flow` el resultado de `InstalledAppFlow.from_client_secrets_file(`.
                str(YOUTUBE_CLIENT_SECRETS_FILE),  # Invoca `str` con los argumentos indicados.
                SCOPES,  # Continua la expresion abierta arriba con este valor o argumento.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
            creds = flow.run_local_server(port=0)  # Guarda en `creds` el resultado de `flow.run_local_server(port=0)`.
            with open(token_path, "w", encoding="utf-8") as f:  # Abre `open(token_path, "w", encoding="utf-8") as f` y garantiza la liberacion del recurso al salir del bloque.
                f.write(creds.to_json())  # Invoca `f.write` con los argumentos indicados.

    return creds  # Devuelve `creds` al llamador y termina esta funcion.


def publish_video(video_path: str, platform: str = "local", title: str = "Historia") -> str:  # Declara la funcion `publish_video` y especifica sus parametros y tipo de retorno.
    """Sube un vídeo a YouTube Shorts si están disponibles las credenciales."""  # Ejecuta la operacion indicada por esta expresion.
    video_path = str(Path(video_path).resolve())  # Guarda en `video_path` el resultado de `str(Path(video_path).resolve())`.
    if platform == "local":  # Solo ejecuta el bloque siguiente si se cumple `platform == "local"`.
        logger.info(f"📦 Publicación local simulada: {video_path}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        return video_path  # Devuelve `video_path` al llamador y termina esta funcion.

    if platform != "youtube":  # Solo ejecuta el bloque siguiente si se cumple `platform != "youtube"`.
        logger.warning(f"⚠️ Publicación aún no implementada para {platform}.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        return video_path  # Devuelve `video_path` al llamador y termina esta funcion.

    if not os.path.exists(video_path):  # Solo ejecuta el bloque siguiente si se cumple `not os.path.exists(video_path)`.
        raise FileNotFoundError(f"No se encontró el vídeo para publicar: {video_path}")  # Lanza `FileNotFoundError` para informar de esta condicion de error.

    if not YOUTUBE_CLIENT_SECRETS_FILE.exists():  # Solo ejecuta el bloque siguiente si se cumple `not YOUTUBE_CLIENT_SECRETS_FILE.exists()`.
        logger.warning(f"⚠️ Falta {YOUTUBE_CLIENT_SECRETS_FILE} para publicar en YouTube.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        logger.warning("   Genera el archivo desde Google Cloud Console y vuelve a intentarlo.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        _save_publication_record({  # Invoca `_save_publication_record` con los argumentos indicados.
            "timestamp": datetime.now().isoformat(timespec="seconds"),  # Asocia la clave `timestamp` con el valor indicado en este diccionario.
            "video_path": video_path,  # Asocia la clave `video_path` con el valor indicado en este diccionario.
            "published_target": video_path,  # Asocia la clave `published_target` con el valor indicado en este diccionario.
            "platform": platform,  # Asocia la clave `platform` con el valor indicado en este diccionario.
            "title": title,  # Asocia la clave `title` con el valor indicado en este diccionario.
            "success": False,  # Asocia la clave `success` con el valor indicado en este diccionario.
            "error": "missing_client_secrets",  # Asocia la clave `error` con el valor indicado en este diccionario.
        })  # Cierra el diccionario o conjunto abierto anteriormente.
        return video_path  # Devuelve `video_path` al llamador y termina esta funcion.

    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        creds = _get_youtube_credentials()  # Guarda en `creds` el resultado de `_get_youtube_credentials()`.
        youtube = build("youtube", "v3", credentials=creds)  # Guarda en `youtube` el resultado de `build("youtube", "v3", credentials=creds)`.
        
        # Ajustes de SEO y publicación pública
        body = {  # Inicia el diccionario que se completa con los campos de las lineas siguientes.
            "snippet": {  # Asocia la clave `snippet` con el valor indicado en este diccionario.
                "title": title,  # Asocia la clave `title` con el valor indicado en este diccionario.
                "description": "Vídeo generado automáticamente #Shorts #Historias",  # Asocia la clave `description` con el valor indicado en este diccionario.
                "tags": ["shorts", "historias", "reddit", "narracion"],  # Asocia la clave `tags` con el valor indicado en este diccionario.
                "categoryId": "24",  # 24 = Entretenimiento
            },  # Cierra el diccionario o conjunto abierto anteriormente.
            "status": {  # Asocia la clave `status` con el valor indicado en este diccionario.
                "privacyStatus": "unlisted", # <--- CAMBIA 'public' POR 'unlisted' AQUÍ
                "selfDeclaredMadeForKids": False  # Asocia la clave `selfDeclaredMadeForKids` con el valor indicado en este diccionario.
            },  # Cierra el diccionario o conjunto abierto anteriormente.
        }  # Cierra el diccionario o conjunto abierto anteriormente.
        
        media = MediaFileUpload(video_path, resumable=True, chunksize=-1, mimetype="video/mp4")  # Guarda en `media` el resultado de `MediaFileUpload(video_path, resumable=True, chunksize=-1, mimetype="video/mp4")`.
        request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)  # Guarda en `request` el resultado de `youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)`.
        response = request.execute()  # Guarda en `response` el resultado de `request.execute()`.
        published_id = response.get("id", video_path)  # Guarda en `published_id` el resultado de `response.get("id", video_path)`.
        logger.info(f"✅ Vídeo subido a YouTube con ID: {published_id}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        _save_publication_record({  # Invoca `_save_publication_record` con los argumentos indicados.
            "timestamp": datetime.now().isoformat(timespec="seconds"),  # Asocia la clave `timestamp` con el valor indicado en este diccionario.
            "video_path": video_path,  # Asocia la clave `video_path` con el valor indicado en este diccionario.
            "published_target": published_id,  # Asocia la clave `published_target` con el valor indicado en este diccionario.
            "platform": platform,  # Asocia la clave `platform` con el valor indicado en este diccionario.
            "title": title,  # Asocia la clave `title` con el valor indicado en este diccionario.
            "success": True,  # Asocia la clave `success` con el valor indicado en este diccionario.
            "error": None,  # Asocia la clave `error` con el valor indicado en este diccionario.
        })  # Cierra el diccionario o conjunto abierto anteriormente.
        return published_id  # Devuelve `published_id` al llamador y termina esta funcion.
    except Exception as exc:  # Captura `Exception as exc` para gestionar el error en este bloque.
        logger.warning(f"⚠️ Error al publicar en YouTube: {exc}")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        _save_publication_record({  # Invoca `_save_publication_record` con los argumentos indicados.
            "timestamp": datetime.now().isoformat(timespec="seconds"),  # Asocia la clave `timestamp` con el valor indicado en este diccionario.
            "video_path": video_path,  # Asocia la clave `video_path` con el valor indicado en este diccionario.
            "published_target": video_path,  # Asocia la clave `published_target` con el valor indicado en este diccionario.
            "platform": platform,  # Asocia la clave `platform` con el valor indicado en este diccionario.
            "title": title,  # Asocia la clave `title` con el valor indicado en este diccionario.
            "success": False,  # Asocia la clave `success` con el valor indicado en este diccionario.
            "error": str(exc),  # Asocia la clave `error` con el valor indicado en este diccionario.
        })  # Cierra el diccionario o conjunto abierto anteriormente.
        return video_path  # Devuelve `video_path` al llamador y termina esta funcion.