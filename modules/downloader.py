import os
import yt_dlp
from config import GAMEPLAY_DIR

CHANNELS_FILE = "data/channels.txt"
ARCHIVE_FILE = "data/downloaded_archive.txt"  # El bloc de notas secreto para no descargar dos veces el mismo vídeo

def ensure_gameplay_exists():
    """
    Comprueba si hay vídeos disponibles. Si la carpeta está vacía,
    acude a los canales de YouTube configurados y descarga automáticamente 
    el siguiente vídeo disponible que no se haya descargado antes.
    """
    valid_extensions = (".mp4", ".mov", ".avi", ".webm")
    os.makedirs(GAMEPLAY_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Comprobar si ya hay vídeos listos para usar
    videos = [f for f in os.listdir(GAMEPLAY_DIR) if f.lower().endswith(valid_extensions)]
    
    if videos:
        print(f"✅ Se han encontrado {len(videos)} vídeos de gameplay listos en la recámara.")
        return True

    print("⚠️ La carpeta de gameplays está vacía. Activando piloto automático de descarga...")
    
    # Si no existe el archivo de canales, lo creamos con una estructura de ejemplo
    if not os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            f.write("# Pega aquí URLs de canales de YouTube (ej: https://www.youtube.com/@Canal/videos)\n")
        print(f"⚠️ Se ha creado '{CHANNELS_FILE}'. Por favor, pon ahí la URL de un canal de YouTube.")
        return False

    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print(f"❌ El archivo '{CHANNELS_FILE}' no contiene ninguna URL de canal válida.")
        return False

    # Configuración inteligente de yt-dlp con historial de descargas
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(GAMEPLAY_DIR, '%(id)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'playlistend': 1,               # Descarga solo 1 vídeo nuevo por cada comprobación
        'download_archive': ARCHIVE_FILE, # Registra los IDs descargados para ignorarlos en el futuro
        'ignoreerrors': True,
    }

    # Recorrer los canales de la lista hasta conseguir descargar uno nuevo
    for channel_url in urls:
        print(f"📥 Conectando con el canal: {channel_url}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([channel_url])
            
            # Verificar si la descarga fue efectiva y ya hay vídeos en la carpeta
            current_videos = [f for f in os.listdir(GAMEPLAY_DIR) if f.lower().endswith(valid_extensions)]
            if current_videos:
                print("✅ ¡Nuevo gameplay descargado e integrado automáticamente en el sistema!")
                return True
                
        except Exception as e:
            print(f"⚠️ Error al intentar descargar del canal {channel_url}: {e}")
            continue

    print("❌ No se pudo descargar ningún vídeo nuevo. Revisa los enlaces en 'data/channels.txt'.")
    return False