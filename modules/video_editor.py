import json  # Importa `json` para utilizarlo en este archivo.
import logging  # Importa `logging` para utilizarlo en este archivo.
import os  # Importa `os` para utilizarlo en este archivo.
import shutil  # Importa `shutil` para utilizarlo en este archivo.
import subprocess  # Importa `subprocess` para utilizarlo en este archivo.
import uuid  # Genera identificadores únicos de archivos temporales

import whisper  # Importa `whisper` para utilizarlo en este archivo.
from moviepy import AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip, vfx  # Importa los nombres necesarios desde `moviepy`.
from moviepy.config import FFMPEG_BINARY  # Importa los nombres necesarios desde `moviepy.config`.
from PIL import ImageFont  # Importa los nombres necesarios desde `PIL`.

from config import GAMEPLAY_DIR, OUTPUT_DIR, PROGRESS_FILE, USED_GAMEPLAY_DIR  # Importa los nombres necesarios desde `config`.

logger = logging.getLogger("reddit_bot")  # Guarda en `logger` el resultado de `logging.getLogger("reddit_bot")`.

# --- Resolución de fuente para los subtítulos ---
# MoviePy 2.x necesita la ruta a un archivo de fuente (.ttf/.otf) real, no
# un nombre de familia como "Impact" (que era válido en MoviePy 1.x/ImageMagick).
# Probamos varias rutas típicas de Windows; si no se encuentra ninguna,
# TextClip usará su fuente por defecto (Pillow) en vez de fallar.
_FONT_CANDIDATES = [  # Inicia la lista que se completa con los elementos de las lineas siguientes.
    r"C:\Windows\Fonts\Impact.ttf",  # Continua la expresion abierta arriba con este valor o argumento.
    r"C:\Windows\Fonts\impact.ttf",  # Continua la expresion abierta arriba con este valor o argumento.
    r"C:\Windows\Fonts\Arialbd.ttf",  # Continua la expresion abierta arriba con este valor o argumento.
    r"C:\Windows\Fonts\arialbd.ttf",  # Continua la expresion abierta arriba con este valor o argumento.
]   # Cierra la lista o indice abierto anteriormente.

_VALID_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".webm")  # Guarda en `_VALID_VIDEO_EXTENSIONS` el resultado de `(".mp4", ".mov", ".avi", ".webm")`.


def _resolve_subtitle_font():  # Declara la funcion `_resolve_subtitle_font` y especifica sus parametros y tipo de retorno.
    for candidate in _FONT_CANDIDATES:  # Recorre `_FONT_CANDIDATES` y asigna cada elemento a `candidate`.
        if os.path.exists(candidate):  # Solo ejecuta el bloque siguiente si se cumple `os.path.exists(candidate)`.
            return candidate  # Devuelve `candidate` al llamador y termina esta funcion.
    logger.warning(  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        "No se encontró ninguna fuente TTF para los subtítulos (se probaron: %s). "  # Ejecuta la operacion indicada por esta expresion.
        "Se usará la fuente por defecto de MoviePy.",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
        ", ".join(_FONT_CANDIDATES),  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
    return None  # Devuelve `None` al llamador y termina esta funcion.


SUBTITLE_FONT = _resolve_subtitle_font()  # Guarda en `SUBTITLE_FONT` el resultado de `_resolve_subtitle_font()`.

# Tamaño de fuente y grosor de contorno usados para los subtítulos karaoke.
# Se definen aquí (en lugar de dejarlos sueltos como "magic numbers" dentro
# de create_final_video) porque también los necesita _resolve_subtitle_box_height().
SUBTITLE_FONT_SIZE = 110  # Guarda en `SUBTITLE_FONT_SIZE` el resultado de `110`.
SUBTITLE_STROKE_WIDTH = 5.5  # Guarda en `SUBTITLE_STROKE_WIDTH` el resultado de `5.5`.


def _resolve_subtitle_box_height(font_path, font_size, stroke_width, extra_padding=12):  # Declara la funcion `_resolve_subtitle_box_height` y especifica sus parametros y tipo de retorno.
    """
    Calcula una altura FIJA (en px) para la caja de cada palabra del subtítulo,
    en vez de dejar que MoviePy la auto-calcule palabra por palabra (size=(900, None)).

    Motivo del arreglo (bug real de MoviePy 2.x + Pillow >= 10):
    En modo method="caption" con altura None, MoviePy ajusta la altura de la
    imagen al bounding box EXACTO de cada palabra concreta (distinto para
    cada palabra), pero luego coloca el texto usando el ascenso GENÉRICO de
    la fuente (pil_font.getmetrics()), que es un valor fijo e igual para
    todas las palabras. Como la mayoría de palabras (las que no tienen
    mayúsculas ni tildes) no alcanzan ese ascenso máximo, el texto se dibuja
    más abajo de lo que la caja "ajustada" había previsto, y la parte baja de
    las letras con descendente (p, y, q, g, j) se sale del lienzo y queda
    recortada.

    Al fijar la altura de la caja al tamaño real de la fuente (ascenso +
    descenso, iguales para cualquier palabra) el hueco por debajo de la
    línea base es siempre el mismo y siempre suficiente, así que ninguna
    palabra se recorta.
    """
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        pil_font = (  # Guarda en `pil_font` el resultado de `(`.
            ImageFont.truetype(font_path, font_size)  # Invoca `ImageFont.truetype` con los argumentos indicados.
            if font_path  # Solo ejecuta el bloque siguiente si se cumple `font_path`.
            else ImageFont.load_default(font_size)  # Continua la expresion abierta arriba con este valor o argumento.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        ascent, descent = pil_font.getmetrics()  # Ejecuta la operacion indicada por esta expresion.
    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        logger.warning(  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            f"⚠️ No se pudieron leer las métricas de la fuente de subtítulos ({e}). "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
            "Se usará una altura de caja de seguridad."  # Ejecuta la operacion indicada por esta expresion.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        ascent, descent = int(font_size * 0.9), int(font_size * 0.3)  # Ejecuta la operacion indicada por esta expresion.

    return ascent + descent + int(stroke_width * 2) + extra_padding  # Devuelve `ascent + descent + int(stroke_width * 2) + extra_padding` al llamador y termina esta funcion.


SUBTITLE_BOX_HEIGHT = _resolve_subtitle_box_height(  # Guarda en `SUBTITLE_BOX_HEIGHT` el resultado de `_resolve_subtitle_box_height(`.
    SUBTITLE_FONT, SUBTITLE_FONT_SIZE, SUBTITLE_STROKE_WIDTH  # Continua la expresion abierta arriba con este valor o argumento.
)  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.


def split_video_into_parts(input_path: str, max_duration: int = 55) -> list:  # Declara la funcion `split_video_into_parts` y especifica sus parametros y tipo de retorno.
    """
    Divide un vídeo largo en partes de máximo `max_duration` segundos
    para subirlos como Shorts/TikToks por partes de forma automatizada.

    Se usa ffmpeg directamente (en lugar de MoviePy) para evitar el bug de
    MoviePy que pierde el proceso interno de ffmpeg al escribir varios
    subclips del mismo clip padre en bucle ('NoneType' object has no
    attribute 'stdout').
    """
    parts_paths = []  # Inicializa `parts_paths` como una coleccion vacia para acumular datos.
    with VideoFileClip(input_path) as video:  # Abre `VideoFileClip(input_path) as video` y garantiza la liberacion del recurso al salir del bloque.
        total_duration = video.duration  # Guarda en `total_duration` el resultado de `video.duration`.

        # Si el vídeo dura menos del límite, no hace falta trocearlo
        if total_duration <= max_duration + 5:  # Solo ejecuta el bloque siguiente si se cumple `total_duration <= max_duration + 5`.
            return [input_path]  # Devuelve `[input_path]` al llamador y termina esta funcion.

        start = 0  # Guarda en `start` el resultado de `0`.
        part_num = 1  # Guarda en `part_num` el resultado de `1`.

        base_dir = os.path.dirname(input_path)  # Guarda en `base_dir` el resultado de `os.path.dirname(input_path)`.
        base_name = os.path.splitext(os.path.basename(input_path))[0]  # Guarda en `base_name` el resultado de `os.path.splitext(os.path.basename(input_path))[0]`.
        base_name = base_name.replace("_final", "").replace("_master", "")  # Guarda en `base_name` el resultado de `base_name.replace("_final", "").replace("_master", "")`.

        logger.info(f"✂️ La historia dura {total_duration:.1f}s. Fraccionando en partes para Shorts/TikTok...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

        while start < total_duration:  # Repite el bloque mientras se cumpla `start < total_duration`.
            end = min(start + max_duration, total_duration)  # Guarda en `end` el resultado de `min(start + max_duration, total_duration)`.

            # Evitar trozos finales absurdamente cortos (menos de 5 segundos)
            if total_duration - end < 5 and part_num > 1:  # Solo ejecuta el bloque siguiente si se cumple `total_duration - end < 5 and part_num > 1`.
                end = total_duration  # Guarda en `end` el resultado de `total_duration`.

            part_duration = end - start  # Guarda en `part_duration` el resultado de `end - start`.
            part_filename = f"{base_name}_part{part_num}.mp4"  # Guarda en `part_filename` el resultado de `f"{base_name}_part{part_num}.mp4"`.
            part_path = os.path.join(base_dir, part_filename)  # Guarda en `part_path` el resultado de `os.path.join(base_dir, part_filename)`.

            logger.info(f"   🔹 Generando parte {part_num} ({start:.1f}s a {end:.1f}s)...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.

            # --- Fraccionamiento con ffmpeg directo ---
            # -ss ANTES de -i = búsqueda rápida por keyframes.
            # -t = duración exacta del segmento a partir del punto de inicio.
            cmd = [  # Inicia la lista que se completa con los elementos de las lineas siguientes.
                FFMPEG_BINARY,  # Continua la expresion abierta arriba con este valor o argumento.
                "-y",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-ss", f"{start:.3f}",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-i", input_path,  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-t", f"{part_duration:.3f}",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-c:v", "libx264",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-preset", "medium",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-crf", "18",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-c:a", "aac",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-b:a", "192k",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-pix_fmt", "yuv420p",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                "-movflags", "+faststart",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
                part_path,  # Continua la expresion abierta arriba con este valor o argumento.
            ]   # Cierra la lista o indice abierto anteriormente.

            result = subprocess.run(cmd, capture_output=True, text=True)  # Guarda en `result` el resultado de `subprocess.run(cmd, capture_output=True, text=True)`.
            if result.returncode != 0:  # Solo ejecuta el bloque siguiente si se cumple `result.returncode != 0`.
                # Mostramos la traza de ffmpeg para depurar si falla
                stderr_tail = result.stderr.strip()[-2000:]  # Guarda en `stderr_tail` el resultado de `result.stderr.strip()[-2000:]`.
                raise RuntimeError(  # Lanza `RuntimeError` para informar de esta condicion de error.
                    f"ffmpeg no pudo generar la parte {part_num} "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
                    f"({start:.1f}s a {end:.1f}s):\n{stderr_tail}"  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
                )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

            parts_paths.append(part_path)  # Anade el elemento indicado a la coleccion.
            start = end  # Guarda en `start` el resultado de `end`.
            part_num += 1  # Actualiza `part_num`: acumula su valor con `1`.
            if start >= total_duration:  # Solo ejecuta el bloque siguiente si se cumple `start >= total_duration`.
                break  # Termina inmediatamente el bucle actual.

    return parts_paths  # Devuelve `parts_paths` al llamador y termina esta funcion.


def _archive_exhausted_video(video_path) -> None:  # Declara la funcion `_archive_exhausted_video` y especifica sus parametros y tipo de retorno.
    """
    Mueve un vídeo de gameplay ya agotado (sin tramos libres) a
    used_gameplays/, para que ensure_gameplay_exists() detecte
    correctamente que hace falta descargar contenido nuevo. Antes de este
    cambio, un vídeo agotado se quedaba para siempre en assets/gameplay,
    así que la comprobación de "carpeta no vacía" nunca disparaba una
    nueva descarga y el pipeline fallaba en bucle en la Fase 3.
    """
    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        USED_GAMEPLAY_DIR.mkdir(parents=True, exist_ok=True)  # Crea la carpeta indicada si todavia no existe.
        destination = USED_GAMEPLAY_DIR / video_path.name  # Guarda en `destination` el resultado de `USED_GAMEPLAY_DIR / video_path.name`.
        if destination.exists():  # Solo ejecuta el bloque siguiente si se cumple `destination.exists()`.
            destination = USED_GAMEPLAY_DIR / f"{video_path.stem}_{uuid.uuid4().hex[:8]}{video_path.suffix}"  # Guarda en `destination` el resultado de `USED_GAMEPLAY_DIR / f"{video_path.stem}_{uuid.uuid4().hex[:8]}{video_path.suffix}"`.
        shutil.move(str(video_path), str(destination))  # Mueve el archivo a la ruta de destino.
        logger.info(f"   '{video_path.name}' archivado en {USED_GAMEPLAY_DIR.name}/ (agotado, sin tramos libres).")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    except OSError as e:  # Captura `OSError as e` para gestionar el error en este bloque.
        logger.warning(f" No se pudo archivar el vídeo agotado '{video_path.name}': {e}")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.


def commit_background_progress(video_path: str, end_time: float) -> None:  # Declara la funcion `commit_background_progress` y especifica sus parametros y tipo de retorno.
    """
    Confirma en disco el nuevo punto de memoria secuencial para un vídeo de
    fondo. IMPORTANTE: solo se debe llamar cuando el vídeo final se ha
    generado con éxito. Si se guardara al elegir el tramo (como se hacía
    antes), una ejecución que falla más adelante en el pipeline "quema"
    igualmente ese tramo de gameplay sin haber producido ningún vídeo.
    """
    progress = {}  # Inicializa `progress` como una coleccion vacia para acumular datos.
    if PROGRESS_FILE.exists():  # Solo ejecuta el bloque siguiente si se cumple `PROGRESS_FILE.exists()`.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))  # Guarda en `progress` el resultado de `json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))`.
        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            logger.warning(f"⚠️ No se pudo leer {PROGRESS_FILE}: {e}. Se empieza de cero.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            progress = {}  # Inicializa `progress` como una coleccion vacia para acumular datos.

    video_name = os.path.basename(video_path)  # Guarda en `video_name` el resultado de `os.path.basename(video_path)`.
    progress[video_name] = end_time  # Ejecuta la operacion indicada por esta expresion.
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)  # Crea la carpeta indicada si todavia no existe.
    PROGRESS_FILE.write_text(json.dumps(progress, indent=4, ensure_ascii=False), encoding="utf-8")  # Escribe el contenido generado en el archivo indicado.
    logger.info(f"Progreso de '{video_name}' confirmado en memoria: hasta {end_time:.1f}s")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.


def get_next_background_segment(audio_path: str):  # Declara la funcion `get_next_background_segment` y especifica sus parametros y tipo de retorno.
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
    progress = {}  # Inicializa `progress` como una coleccion vacia para acumular datos.
    if PROGRESS_FILE.exists():  # Solo ejecuta el bloque siguiente si se cumple `PROGRESS_FILE.exists()`.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))  # Guarda en `progress` el resultado de `json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))`.
        except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
            logger.warning(f"⚠️ No se pudo leer {PROGRESS_FILE}: {e}. Se empieza de cero.")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            progress = {}  # Inicializa `progress` como una coleccion vacia para acumular datos.

    # 2. Duración del audio (cuánto tramo necesitamos)
    with AudioFileClip(audio_path) as audio:  # Abre `AudioFileClip(audio_path) as audio` y garantiza la liberacion del recurso al salir del bloque.
        needed_duration = audio.duration  # Guarda en `needed_duration` el resultado de `audio.duration`.

    if needed_duration <= 0:  # Solo ejecuta el bloque siguiente si se cumple `needed_duration <= 0`.
        raise ValueError(f"El audio '{audio_path}' no tiene duración válida ({needed_duration}).")  # Lanza `ValueError` para informar de esta condicion de error.

    # 3. Buscar el siguiente vídeo con espacio sin usar
    videos = sorted(  # Guarda en `videos` el resultado de `sorted(`.
        (p for p in GAMEPLAY_DIR.iterdir() if p.suffix.lower() in _VALID_VIDEO_EXTENSIONS),  # Abre la agrupacion, lista o diccionario que se completa en las lineas siguientes.
        key=lambda p: p.name.lower(),  # Guarda en `key` el resultado de `lambda p: p.name.lower(),`.
    )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

    for video_path in videos:  # Recorre `videos` y asigna cada elemento a `video_path`.
        current_progress = float(progress.get(video_path.name, 0.0))  # Guarda en `current_progress` el resultado de `float(progress.get(video_path.name, 0.0))`.

        with VideoFileClip(str(video_path)) as video:  # Abre `VideoFileClip(str(video_path)) as video` y garantiza la liberacion del recurso al salir del bloque.
            video_duration = video.duration  # Guarda en `video_duration` el resultado de `video.duration`.

        # Si este vídeo ya está agotado, archivarlo y probar con el siguiente
        if current_progress >= video_duration - 1:  # Solo ejecuta el bloque siguiente si se cumple `current_progress >= video_duration - 1`.
            logger.info(f"   ➡️ '{video_path.name}' ya está completamente usado. Probando siguiente...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
            _archive_exhausted_video(video_path)  # Invoca `_archive_exhausted_video` con los argumentos indicados.
            continue  # Pasa a la siguiente iteracion del bucle actual.

        start_time = current_progress  # Guarda en `start_time` el resultado de `current_progress`.
        end_time = min(start_time + needed_duration, video_duration)  # Guarda en `end_time` el resultado de `min(start_time + needed_duration, video_duration)`.

        # NOTA: la memoria NO se guarda aquí. Se confirma con
        # commit_background_progress() solo si el vídeo final se genera
        # con éxito, para no perder tramos de gameplay en ejecuciones
        # fallidas (ver create_final_video / main.py).
        logger.info(f"   🎬 Tramo seleccionado: '{video_path.name}' [{start_time:.1f}s → {end_time:.1f}s]")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
        return str(video_path), start_time, end_time  # Devuelve `str(video_path), start_time, end_time` al llamador y termina esta funcion.

    raise RuntimeError(  # Lanza `RuntimeError` para informar de esta condicion de error.
        f"No hay ningún gameplay con tramos sin usar en {GAMEPLAY_DIR}. "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
        "Añade más vídeos o restablece data/video_progress.json."  # Ejecuta la operacion indicada por esta expresion.
    )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.


def create_final_video(audio_path: str, background_clip_path: str, start_time: float, end_time: float, story: dict = None) -> list:  # Declara la funcion `create_final_video` y especifica sus parametros y tipo de retorno.
    """
    Monta el vídeo final usando el tramo secuencial de la memoria, lo renderiza
    como vídeo maestro y lo fracciona automáticamente si supera los 55 segundos.
    """
    # 1. Cargar el audio y el modelo de Whisper
    logger.info("   [4.1] Cargando Whisper y transcribiendo audio...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    audio = AudioFileClip(audio_path)  # Guarda en `audio` el resultado de `AudioFileClip(audio_path)`.
    model = whisper.load_model("base")  # Guarda en `model` el resultado de `whisper.load_model("base")`.

    # word_timestamps=True es vital para el estilo "karaoke"
    transcription = model.transcribe(audio_path, word_timestamps=True, language="es")  # Guarda en `transcription` el resultado de `model.transcribe(audio_path, word_timestamps=True, language="es")`.

    # 2. Cargar y preparar el clip de vídeo de fondo usando el tramo de la memoria
    logger.info("   [4.2] Preparando y reencuadrando vídeo de fondo (9:16)...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    bg_clip = VideoFileClip(background_clip_path)  # Guarda en `bg_clip` el resultado de `VideoFileClip(background_clip_path)`.

    # USAMOS EL TRAMO EXACTO QUE DICTA LA MEMORIA
    bg_clip = bg_clip.subclipped(start_time, end_time)  # Guarda en `bg_clip` el resultado de `bg_clip.subclipped(start_time, end_time)`.

    # Si el tramo de fondo elegido es más corto que el audio (típicamente
    # porque el vídeo de gameplay se estaba quedando sin metraje al final),
    # lo repetimos en bucle para que la pantalla NUNCA se quede sin
    # gameplay mientras dure la narración.
    if bg_clip.duration < audio.duration:  # Solo ejecuta el bloque siguiente si se cumple `bg_clip.duration < audio.duration`.
        logger.warning(  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
            f"   ⚠️ El tramo de fondo dura {bg_clip.duration:.1f}s pero el audio "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
            f"dura {audio.duration:.1f}s. Repitiendo el fondo en bucle para no "  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.
            "dejar la pantalla sin gameplay."  # Ejecuta la operacion indicada por esta expresion.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        bg_clip = bg_clip.with_effects([vfx.Loop(duration=audio.duration)])  # Guarda en `bg_clip` el resultado de `bg_clip.with_effects([vfx.Loop(duration=audio.duration)])`.

    # Recortar a relación de aspecto 9:16 (vertical) centrado
    w, h = bg_clip.size  # Ejecuta la operacion indicada por esta expresion.
    target_ratio = 9 / 16  # Guarda en `target_ratio` el resultado de `9 / 16`.
    current_ratio = w / h  # Guarda en `current_ratio` el resultado de `w / h`.

    if current_ratio > target_ratio:  # Solo ejecuta el bloque siguiente si se cumple `current_ratio > target_ratio`.
        new_w = int(h * target_ratio)  # Guarda en `new_w` el resultado de `int(h * target_ratio)`.
        bg_clip = bg_clip.cropped(x1=(w - new_w) / 2, x2=(w + new_w) / 2, y1=0, y2=h)  # Guarda en `bg_clip` el resultado de `bg_clip.cropped(x1=(w - new_w) / 2, x2=(w + new_w) / 2, y1=0, y2=h)`.
    else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
        new_h = int(w / target_ratio)  # Guarda en `new_h` el resultado de `int(w / target_ratio)`.
        bg_clip = bg_clip.cropped(x1=0, x2=w, y1=(h - new_h) / 2, y2=(h + new_h) / 2)  # Guarda en `bg_clip` el resultado de `bg_clip.cropped(x1=0, x2=w, y1=(h - new_h) / 2, y2=(h + new_h) / 2)`.

    # Escalar a 1080x1920 exactos para estándar de TikTok/Shorts
    bg_clip = bg_clip.resized(new_size=(1080, 1920))  # Guarda en `bg_clip` el resultado de `bg_clip.resized(new_size=(1080, 1920))`.
    bg_clip = bg_clip.with_audio(audio)  # Guarda en `bg_clip` el resultado de `bg_clip.with_audio(audio)`.

    # 3. Generar los clips de texto (Subtítulos con estilo Impact / Amarillo)
    logger.info("   [4.3] Generando subtítulos sincronizados...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    text_clips = []  # Inicializa `text_clips` como una coleccion vacia para acumular datos.

    for segment in transcription.get("segments", []):  # Recorre `transcription.get("segments", [])` y asigna cada elemento a `segment`.
        for word_info in segment.get("words", []):  # Recorre `segment.get("words", [])` y asigna cada elemento a `word_info`.
            word_text = word_info["word"].strip()  # Guarda en `word_text` el resultado de `word_info["word"].strip()`.
            start = word_info["start"]  # Guarda en `start` el resultado de `word_info["start"]`.
            end = word_info["end"]  # Guarda en `end` el resultado de `word_info["end"]`.

            if not word_text:  # Solo ejecuta el bloque siguiente si se cumple `not word_text`.
                continue  # Pasa a la siguiente iteracion del bucle actual.

            txt_clip_kwargs = dict(  # Guarda en `txt_clip_kwargs` el resultado de `dict(`.
                text=word_text,  # Guarda en `text` el resultado de `word_text,`.
                font_size=SUBTITLE_FONT_SIZE,  # Guarda en `font_size` el resultado de `SUBTITLE_FONT_SIZE,`.
                color="yellow",  # Guarda en `color` el resultado de `"yellow",`.
                stroke_color="black",  # Guarda en `stroke_color` el resultado de `"black",`.
                stroke_width=SUBTITLE_STROKE_WIDTH,  # Guarda en `stroke_width` el resultado de `SUBTITLE_STROKE_WIDTH,`.
                method="caption",  # Guarda en `method` el resultado de `"caption",`.
                size=(900, SUBTITLE_BOX_HEIGHT),  # Guarda en `size` el resultado de `(900, SUBTITLE_BOX_HEIGHT),`.
                margin=(20, 20),  # Guarda en `margin` el resultado de `(20, 20),`.
                text_align="center",  # Guarda en `text_align` el resultado de `"center",`.
                vertical_align="top",  # Guarda en `vertical_align` el resultado de `"top",`.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
            if SUBTITLE_FONT:  # Solo ejecuta el bloque siguiente si se cumple `SUBTITLE_FONT`.
                txt_clip_kwargs["font"] = SUBTITLE_FONT  # Ejecuta la operacion indicada por esta expresion.

            txt_clip = TextClip(**txt_clip_kwargs)  # Guarda en `txt_clip` el resultado de `TextClip(**txt_clip_kwargs)`.

            txt_clip = (  # Guarda en `txt_clip` el resultado de `(`.
                txt_clip.with_start(start)  # Define el instante de inicio del subtitulo.
                .with_end(end)  # Continua la expresion abierta arriba con este valor o argumento.
                .with_position(("center", "center"))  # Continua la expresion abierta arriba con este valor o argumento.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

            text_clips.append(txt_clip)  # Anade el elemento indicado a la coleccion.

    # 4. Componer y Renderizar el vídeo maestro
    logger.info("   [4.4] Renderizando vídeo maestro...")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    final_video = CompositeVideoClip([bg_clip] + text_clips)  # Guarda en `final_video` el resultado de `CompositeVideoClip([bg_clip] + text_clips)`.

    story_id = story.get("id", "output") if story else "output"  # Guarda en `story_id` el resultado de `story.get("id", "output") if story else "output"`.
    master_filename = f"{story_id}_master.mp4"  # Guarda en `master_filename` el resultado de `f"{story_id}_master.mp4"`.
    master_path = str(OUTPUT_DIR / master_filename)  # Guarda en `master_path` el resultado de `str(OUTPUT_DIR / master_filename)`.

    # Generar nombres únicos irrepetibles para evitar bloqueos de Windows
    unique_temp_audio = f"temp_audio_{uuid.uuid4().hex}.m4a"  # Guarda en `unique_temp_audio` el resultado de `f"temp_audio_{uuid.uuid4().hex}.m4a"`.
    retry_temp_audio = f"temp_audio_retry_{uuid.uuid4().hex}.m4a"  # Guarda en `retry_temp_audio` el resultado de `f"temp_audio_retry_{uuid.uuid4().hex}.m4a"`.

    try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
        final_video.write_videofile(  # Renderiza el montaje de video con las opciones indicadas.
            master_path,  # Continua la expresion abierta arriba con este valor o argumento.
            fps=30,  # Guarda en `fps` el resultado de `30,`.
            codec="libx264",  # Guarda en `codec` el resultado de `"libx264",`.
            audio_codec="aac",  # Guarda en `audio_codec` el resultado de `"aac",`.
            temp_audiofile=unique_temp_audio,  # Guarda en `temp_audiofile` el resultado de `unique_temp_audio,`.
            remove_temp=True,  # Guarda en `remove_temp` el resultado de `True,`.
            logger=None,  # Guarda en `logger` el resultado de `None,`.
            threads=4  # Acelera el proceso usando múltiples hilos
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
    except Exception as e:  # Captura `Exception as e` para gestionar el error en este bloque.
        logger.warning(f"⚠️ Fallo al renderizar el vídeo maestro con el encoder habitual: {e}")  # Registra el mensaje de advertencia para que aparezca en la consola o en el archivo de log.
        try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
            final_video.write_videofile(  # Renderiza el montaje de video con las opciones indicadas.
                master_path,  # Continua la expresion abierta arriba con este valor o argumento.
                fps=30,  # Guarda en `fps` el resultado de `30,`.
                codec="mpeg4",  # Guarda en `codec` el resultado de `"mpeg4",`.
                audio_codec="aac",  # Guarda en `audio_codec` el resultado de `"aac",`.
                temp_audiofile=retry_temp_audio,  # Guarda en `temp_audiofile` el resultado de `retry_temp_audio,`.
                remove_temp=True,  # Guarda en `remove_temp` el resultado de `True,`.
                logger=None  # Guarda en `logger` el resultado de `None`.
            )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        except Exception as retry_e:  # Captura `Exception as retry_e` para gestionar el error en este bloque.
            raise RuntimeError(f"Error crítico en el reintento del renderizado: {retry_e}") from e  # Lanza `RuntimeError` para informar de esta condicion de error.
    finally:   # Ejecuta la limpieza incluso si falla el bloque anterior.
        # Bloque de limpieza forzada: destruye cualquier archivo temporal huérfano
        for temp_file in [unique_temp_audio, retry_temp_audio]:  # Recorre `[unique_temp_audio, retry_temp_audio]` y asigna cada elemento a `temp_file`.
            if os.path.exists(temp_file):  # Solo ejecuta el bloque siguiente si se cumple `os.path.exists(temp_file)`.
                try:   # Inicia un bloque cuyo error puede gestionarse en una clausula except.
                    os.remove(temp_file)  # Invoca `os.remove` con los argumentos indicados.
                except OSError:  # Captura `OSError` para gestionar el error en este bloque.
                    pass  # No realiza ninguna operacion en esta rama; sirve como bloque vacio.

    # 5. Limpieza de memoria del vídeo maestro
    audio.close()  # Cierra el recurso para liberar sus recursos.
    bg_clip.close()  # Cierra el recurso para liberar sus recursos.
    final_video.close()  # Cierra el recurso para liberar sus recursos.

    # 6. Fraccionar el vídeo maestro si excede los 55 segundos
    final_parts = split_video_into_parts(master_path, max_duration=55)  # Guarda en `final_parts` el resultado de `split_video_into_parts(master_path, max_duration=55)`.

    # Borrar el archivo maestro pesado y conservar solo las partes finales
    if len(final_parts) > 1 and os.path.exists(master_path):  # Solo ejecuta el bloque siguiente si se cumple `len(final_parts) > 1 and os.path.exists(master_path)`.
        os.remove(master_path)  # Invoca `os.remove` con los argumentos indicados.

    return final_parts  # Devuelve `final_parts` al llamador y termina esta funcion.