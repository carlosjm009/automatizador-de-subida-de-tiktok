import logging
import os

import whisper
from moviepy import AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip

from config import OUTPUT_DIR

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

            subclip = video.subclipped(start, end)
            part_filename = f"{base_name}_part{part_num}.mp4"
            part_path = os.path.join(base_dir, part_filename)

            logger.info(f"   🔹 Generando parte {part_num} ({start:.1f}s a {end:.1f}s)...")
            subclip.write_videofile(
                part_path,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            subclip.close()
            parts_paths.append(part_path)

            start = end
            part_num += 1
            if start >= total_duration:
                break

    return parts_paths


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
                method="label",
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

    try:
        final_video.write_videofile(
            master_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
    except Exception as e:
        logger.warning(f"⚠️ Fallo al renderizar el vídeo maestro con el encoder habitual: {e}")
        final_video.write_videofile(
            master_path,
            fps=30,
            codec="mpeg4",
            audio_codec="aac",
            logger=None,
        )

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
