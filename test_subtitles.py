"""
Script de verificación rápida para el arreglo de subtítulos.

Genera imágenes PNG con las palabras que antes se recortaban (las que
tienen letras con descendente: p, y, q, g, j) usando EXACTAMENTE la misma
configuración que create_final_video() en modules/video_editor.py, pero sin
tener que pasar por Whisper ni descargar gameplay. Así puedes comprobar en
segundos, mirando las imágenes generadas en test_output/, si el recorte ya
está solucionado antes de lanzar el pipeline completo.

Uso:
    python test_subtitles.py

Salida:
    test_output/subtitle_*.png  (una imagen por palabra de prueba)
"""

import os

from moviepy import TextClip

from modules.video_editor import (
    SUBTITLE_FONT,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_STROKE_WIDTH,
    SUBTITLE_BOX_HEIGHT,
)

OUT_DIR = "test_output"

# Palabras elegidas a propósito: todas tienen alguna letra con descendente
# (p, y, q, g, j) y ninguna tiene mayúsculas ni tildes que "engañen" al
# cálculo antiguo dándole más altura de la que en realidad necesitaba.
TEST_WORDS = [
    "papy",
    "jugoso",
    "quizás",
    "guapo",
    "y",
    "porque",
    "gente",
    "pequeño",
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Fuente usada: {SUBTITLE_FONT or '(por defecto de Pillow)'}")
    print(f"font_size={SUBTITLE_FONT_SIZE}  stroke_width={SUBTITLE_STROKE_WIDTH}  "
          f"box_height={SUBTITLE_BOX_HEIGHT}\n")

    for word in TEST_WORDS:
        txt_clip_kwargs = dict(
            text=word,
            font_size=SUBTITLE_FONT_SIZE,
            color="yellow",
            stroke_color="black",
            stroke_width=SUBTITLE_STROKE_WIDTH,
            method="caption",
            size=(900, SUBTITLE_BOX_HEIGHT),
            margin=(20, 20),
            text_align="center",
            vertical_align="top",
        )
        if SUBTITLE_FONT:
            txt_clip_kwargs["font"] = SUBTITLE_FONT

        clip = TextClip(**txt_clip_kwargs)
        out_path = os.path.join(OUT_DIR, f"subtitle_{word}.png")
        clip.save_frame(out_path, t=0)
        print(f"  ✔ Generado: {out_path}  (tamaño imagen: {clip.size})")

    print(f"\nListo. Abre la carpeta '{OUT_DIR}' y revisa que ninguna letra "
          "(sobre todo la p/y/q/g de abajo) esté cortada por el borde de la imagen.")


if __name__ == "__main__":
    main()
