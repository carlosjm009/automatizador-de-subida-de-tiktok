import json
import logging
import os
import shutil
import subprocess
import uuid  # Genera identificadores únicos de archivos temporales

import whisper
from moviepy import AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip
from moviepy.config import FFMPEG_BINARY

from config import GAMEPLAY_DIR, OUTPUT_DIR, PROGRESS_FILE, USED_GAMEPLAY_DIR

logger = logging.getLogger("reddit_bot")

# --- Resolución de fuente para los subtítulos ---
# MoviePy 2.x necesita la ruta a un archivo de fuente (.ttf/.otf) real, no
# un nombre de familia como "Impact" (que era válido en MoviePy 1.x/ImageMagick).
# Probamos varias rutas típicas de Windows; si no se encuentra ninguna,
# TextClip usará su fuente por defecto (Pillow) en vez de fallar.
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\Impact.ttf",
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\Arialbd.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]

_VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".webm")


def _resolve_subtitle_font():
    for candidate in _FONT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    logger.warning(
        "No se encontró ninguna fuente TTF para los subtítulos (se probaron: %s). "
        "Se usará la fuente por defecto de MoviePy.",
        ", ".join(_FONT_CANDIDATES),
    )
    return None


SUBTITLE_FONT = _resolve_subtitle_font()


def split_video_into_parts(input_path: str, max_duration: int = 55) -> list:
    """
    Divide un vídeo largo en partes de máximo `max_duration` segundos
    para subirlos como Shorts/TikToks por partes de forma automatizada.

    Se usa ffmpeg directamente (en lugar de MoviePy) para evitar el bug de
    MoviePy que pierde el proceso interno de ffmpeg al escribir varios
    subclips del mismo clip padre en bucle ('NoneType' object has no
    attribute 'stdout').
    """
    parts_paths = []
    with VideoFileClip(input_path) as video:
        total_duration = video.duration

        # Si el vídeo dura menos del límite, no hace falta trocearlo
        if total_duration <= max_duration + 5:
            return [input_path]

        start = 0
        part_num = 1

        base_dir = os.path.dirname(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        base_name = base_name.replace("_final", "").replace("_master", "")

        logger.info(f"✂️ La historia dura {total_duration:.1f}s. Fraccionando en partes para Shorts/TikTok...")

        while start < total_duration:
            end = min(start + max_duration, total_duration)

            # Evitar trozos finales absurdamente cortos (menos de 5 segundos)
            if total_duration - end < 5 and part_num > 1:
                end = total_duration

            part_duration = end - start
            part_filename = f"{base_name}_part{part_num}.mp4"
            part_path = os.path.join(base_dir, part_filename)

            logger.info(f"   🔹 Generando parte {part_num} ({start:.1f}s a {end:.1f}s)...")

            # --- Fraccionamiento con ffmpeg directo ---
            # -ss ANTES de -i = búsqueda rápida por keyframes.
            # -t = duración exacta del segmento a partir del punto de inicio.
            cmd = [
                FFMPEG_BINARY,
                "-y",
                "-ss", f"{start:.3f}",
                "-i", input_path,
                "-t", f"{part_duration:.3f}",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                part_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Mostramos la traza de ffmpeg para depurar si falla
                stderr_tail = result.stderr.strip()[-2000:]
                raise RuntimeError(
                    f"ffmpeg no pudo generar la parte {part_num} "
                    f"({start:.1f}s a {end:.1f}s):\n{stderr_tail}"
                )

            parts_paths.append(part_path)
            start = end
            part_num += 1
            if start >= total_duration:
                break

    return parts_paths


def _archive_exhausted_video(video_path) -> None:
    """
    Mueve un vídeo de gameplay ya agotado (sin tramos libres) a
    used_gameplays/, para que ensure_gameplay_exists() detecte
    correctamente que hace falta descargar contenido nuevo. Antes de este
    cambio, un vídeo agotado se quedaba para siempre en assets/gameplay,
    así que la comprobación de "carpeta no vacía" nunca disparaba una
    nueva descarga y el pipeline fallaba en bucle en la Fase 3.
    """
    try:
        USED_GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)
        destination = USED_GAMEPLAY_DIR / video_path.name
        if destination.exists():
            destination = USED_GAMEPLAY_DIR / f"{video_path.stem}_{uuid.uuid4().hex[:8]}{video_path.suffix}"
        shutil.move(str(video_path), str(destination))
        logger.info(f"   📦 '{video_path.name}' archivado en {USED_GAMEPLAY_DIR.name}/ (agotado, sin tramos libres).")
    except OSError as e:
        logger.warning(f"⚠️ No se pudo archivar el vídeo agotado '{video_path.name}': {e}")


def commit_background_progress(video_path: str, end_time: float) -> None:
    """
    Confirma en disco el nuevo punto de memoria secuencial para un vídeo de
    fondo. IMPORTANTE: solo se debe llamar cuando el vídeo final se ha
    generado con éxito. Si se guardara al elegir el tramo (como se hacía
    antes), una ejecución que falla más adelante en el pipeline "quema"
    igualmente ese tramo de gameplay sin haber producido ningún vídeo.
    """
    progress = {}
    if PROGRESS_FILE.exists():
        try:
            progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"⚠️ No se pudo leer {PROGRESS_FILE}: {e}. Se empieza de cero.")
            progress = {}

    video_name = os.path.basename(video_path)
    progress[video_name] = end_time
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")
    logger.info(f"   💾 Progreso de '{video_name}' confirmado en memoria: hasta {end_time:.1f}s")


def get_next_background_segment(audio_path: str):
    """
    Selecciona el siguiente tramo disponible del siguiente vídeo de gameplay
    usando memoria secuencial persistida en data/video_progress.json.

    Devuelve una tupla (ruta_del_vídeo, start_time, end_time):
      - ruta_del_vídeo: path al clip de fondo elegido.
      - start_time: segundo de inicio del tramo (donde se quedó la memoria).
      - end_time: segundo de fin del tramo (inicio + duración del audio,
        limitado por la duración total del vídeo).
    """
    # 1. Cargar el progreso de memoria secuencial
    progress = {}
    if PROGRESS_FILE.exists():
        try:
            progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"⚠️ No se pudo leer {PROGRESS_FILE}: {e}. Se empieza de cero.")
            progress = {}

    # 2. Duración del audio (cuánto tramo necesitamos)
    with AudioFileClip(audio_path) as audio:
        needed_duration = audio.duration

    if needed_duration <= 0:
        raise ValueError(f"El audio '{audio_path}' no tiene duración válida ({needed_duration}).")

    # 3. Buscar el siguiente vídeo con espacio sin usar
    videos = sorted(
        (p for p in GAMEPLAY_DIR.iterdir() if p.suffix.lower() in _VALID_VIDEO_EXTENSIONS),
        key=lambda p: p.name.lower(),
    )

    for video_path in videos:
        current_progress = float(progress.get(video_path.name, 0.0))

        with VideoFileClip(str(video_path)) as video:
            video_duration = video.duration

        # Si este vídeo ya está agotado, archivarlo y probar con el siguiente
        if current_progress >= video_duration - 1:
            logger.info(f"   ➡️ '{video_path.name}' ya está completamente usado. Probando siguiente...")
            _archive_exhausted_video(video_path)
            continue

        start_time = current_progress
        end_time = min(start_time + needed_duration, video_duration)

        # NOTA: la memoria NO se guarda aquí. Se confirma con
        # commit_background_progress() solo si el vídeo final se genera
        # con éxito, para no perder tramos de gameplay en ejecuciones
        # fallidas (ver create_final_video / main.py).
        logger.info(f"   🎬 Tramo seleccionado: '{video_path.name}' [{start_time:.1f}s → {end_time:.1f}s]")
        return str(video_path), start_time, end_time

    raise RuntimeError(
        f"No hay ningún gameplay con tramos sin usar en {GAMEPLAY_DIR}. "
        "Añade más vídeos o restablece data/video_progress.json."
    )


def create_final_video(audio_path: str, background_clip_path: str, start_time: float, end_time: float, story: dict = None) -> list:
    """
    Monta el vídeo final usando el tramo secuencial de la memoria, lo renderiza
    como vídeo maestro y lo fracciona automáticamente si supera los 55 segundos.
    """
    # 1. Cargar el audio y el modelo de Whisper
    logger.info("   [4.1] Cargando Whisper y transcribiendo audio...")
    audio = AudioFileClip(audio_path)
    model = whisper.load_model("base")

    # word_timestamps=True es vital para el estilo "karaoke"
    transcription = model.transcribe(audio_path, word_timestamps=True, language="es")

    # 2. Cargar y preparar el clip de vídeo de fondo usando el tramo de la memoria
    logger.info("   [4.2] Preparando y reencuadrando vídeo de fondo (9:16)...")
    bg_clip = VideoFileClip(background_clip_path)

    # USAMOS EL TRAMO EXACTO QUE DICTA LA MEMORIA
    bg_clip = bg_clip.subclipped(start_time, end_time)

    # Recortar a relación de aspecto 9:16 (vertical) centrado
    w, h = bg_clip.size
    target_ratio = 9 / 16
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        bg_clip = bg_clip.cropped(x1=(w - new_w) / 2, x2=(w + new_w) / 2, y1=0, y2=h)
    else:
        new_h = int(w / target_ratio)
        bg_clip = bg_clip.cropped(x1=0, x2=w, y1=(h - new_h) / 2, y2=(h + new_h) / 2)

    # Escalar a 1080x1920 exactos para estándar de TikTok/Shorts
    bg_clip = bg_clip.resized(new_size=(1080, 1920))
    bg_clip = bg_clip.with_audio(audio)

    # 3. Generar los clips de texto (Subtítulos con estilo Impact / Amarillo)
    logger.info("   [4.3] Generando subtítulos sincronizados...")
    text_clips = []

    for segment in transcription.get("segments", []):
        for word_info in segment.get("words", []):
            word_text = word_info["word"].strip()
            start = word_info["start"]
            end = word_info["end"]

            if not word_text:
                continue

            txt_clip_kwargs = dict(
                text=word_text,
                font_size=110,
                color="yellow",
                stroke_color="black",
                stroke_width=5.5,
                method="caption",
                size=(900, None),
                text_align="center",
            )
            if SUBTITLE_FONT:
                txt_clip_kwargs["font"] = SUBTITLE_FONT

            txt_clip = TextClip(**txt_clip_kwargs)

            txt_clip = (
                txt_clip.with_start(start)
                .with_end(end)
                .with_position(("center", "center"))
            )

            text_clips.append(txt_clip)

    # 4. Componer y Renderizar el vídeo maestro
    logger.info("   [4.4] Renderizando vídeo maestro...")
    final_video = CompositeVideoClip([bg_clip] + text_clips)

    story_id = story.get("id", "output") if story else "output"
    master_filename = f"{story_id}_master.mp4"
    master_path = str(OUTPUT_DIR / master_filename)

    # Generar nombres únicos irrepetibles para evitar bloqueos de Windows
    unique_temp_audio = f"temp_audio_{uuid.uuid4().hex}.m4a"
    retry_temp_audio = f"temp_audio_retry_{uuid.uuid4().hex}.m4a"

    try:
        final_video.write_videofile(
            master_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=unique_temp_audio,
            remove_temp=True,
            logger=None,
            threads=4  # Acelera el proceso usando múltiples hilos
        )
    except Exception as e:
        logger.warning(f"⚠️ Fallo al renderizar el vídeo maestro con el encoder habitual: {e}")
        try:
            final_video.write_videofile(
                master_path,
                fps=30,
                codec="mpeg4",
                audio_codec="aac",
                temp_audiofile=retry_temp_audio,
                remove_temp=True,
                logger=None
            )
        except Exception as retry_e:
            raise RuntimeError(f"Error crítico en el reintento del renderizado: {retry_e}") from e
    finally:
        # Bloque de limpieza forzada: destruye cualquier archivo temporal huérfano
        for temp_file in [unique_temp_audio, retry_temp_audio]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    # 5. Limpieza de memoria del vídeo maestro
    audio.close()
    bg_clip.close()
    final_video.close()

    # 6. Fraccionar el vídeo maestro si excede los 55 segundos
    final_parts = split_video_into_parts(master_path, max_duration=55)

    # Borrar el archivo maestro pesado y conservar solo las partes finales
    if len(final_parts) > 1 and os.path.exists(master_path):
        os.remove(master_path)

    return final_parts