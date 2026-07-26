import os
import json
import random
import shutil
from moviepy import VideoFileClip
from config import GAMEPLAY_DIR

PROGRESS_FILE = "data/video_progress.json"
USED_GAMEPLAY_DIR = "assets/used_gameplays"  # Carpeta a donde se moverán los vídeos terminados

def _load_progress():
    """Carga el registro de progreso de los vídeos."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_progress(progress_data):
    """Guarda el registro de progreso actualizado."""
    os.makedirs("data", exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=4)

def get_next_background_segment(audio_path: str):
    """
    Selecciona un vídeo, comprueba si le queda suficiente tiempo. 
    Si ya está exprimido (le quedan menos de 25 segundos), lo mueve a la carpeta de usados.
    Retorna: (video_path, start_time, end_time)
    """
    from moviepy import AudioFileClip
    try:
        with AudioFileClip(audio_path) as audio:
            audio_duration = audio.duration
    except Exception as e:
        raise RuntimeError(f"Error al leer el audio {audio_path}: {e}")

    # Asegurarnos de que existan las carpetas necesarias
    os.makedirs(GAMEPLAY_DIR, exist_ok=True)
    os.makedirs(USED_GAMEPLAY_DIR, exist_ok=True)

    valid_extensions = (".mp4", ".mov", ".avi", ".webm")
    videos = [f for f in os.listdir(GAMEPLAY_DIR) if f.lower().endswith(valid_extensions)]
    
    if not videos:
        raise FileNotFoundError(
            f"No se encontraron vídeos de gameplay en {GAMEPLAY_DIR}. "
            "El descargador automático se encargará de buscar uno nuevo."
        )

    progress = _load_progress()
    selected_video = None
    start_time = 0.0
    selected_video_name = None

    random.shuffle(videos)

    for video_name in videos:
        video_path = os.path.join(GAMEPLAY_DIR, video_name)
        
        try:
            with VideoFileClip(video_path) as clip:
                video_duration = clip.duration
                
            current_pos = progress.get(video_name, 0.0)
            remaining_time = video_duration - current_pos
            
            # --- UMBRAL DE AGOTAMIENTO ---
            # Si le quedan menos de 90 segundos (o menos de lo que dura el audio actual),
            # consideramos que ya no sirve para meter historias y lo archivamos.
            if remaining_time < 90 or remaining_time < audio_duration:
                print(f"🗑️ El vídeo '{video_name}' está prácticamente agotado (quedan {remaining_time:.1f}s). Moviendo a la carpeta de usados...")
                
                destination_path = os.path.join(USED_GAMEPLAY_DIR, video_name)
                
                # Si ya existiera un archivo con el mismo nombre en la carpeta de destino, lo borramos primero
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                    
                # Mover el archivo físico fuera de la carpeta activa de gameplays
                shutil.move(video_path, destination_path)
                
                # Limpiar su registro en el archivo de progreso
                if video_name in progress:
                    progress.pop(video_name)
                    _save_progress(progress)
                    
                continue # Pasamos a revisar el siguiente vídeo
            
            # Si el vídeo tiene suficiente tiempo disponible, lo seleccionamos
            selected_video = video_path
            selected_video_name = video_name
            start_time = current_pos
            break
            
        except Exception as e:
            print(f"⚠️ Error al procesar el vídeo {video_name}: {e}")
            continue

    # Si se han revisado todos los vídeos y ninguno tiene tiempo suficiente
    if not selected_video:
        raise FileNotFoundError(
            "Todos los vídeos de gameplay actuales se han agotado por completo. "
            "El sistema requerirá descargar uno nuevo desde 'channels.txt'."
        )

    end_time = start_time + audio_duration

    # Actualizar la memoria con la nueva posición avanzada
    progress[selected_video_name] = end_time
    _save_progress(progress)

    print(f"🧠 Memoria de vídeo: Usando '{selected_video_name}' desde el segundo {start_time:.1f} hasta {end_time:.1f}")
    return selected_video, start_time, end_time