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

import os  # Importa `os` para utilizarlo en este archivo.

from moviepy import TextClip  # Importa los nombres necesarios desde `moviepy`.

from modules.video_editor import (  # Importa los nombres necesarios desde `modules.video_editor`.
    SUBTITLE_FONT,  # Continua la expresion abierta arriba con este valor o argumento.
    SUBTITLE_FONT_SIZE,  # Continua la expresion abierta arriba con este valor o argumento.
    SUBTITLE_STROKE_WIDTH,  # Continua la expresion abierta arriba con este valor o argumento.
    SUBTITLE_BOX_HEIGHT,  # Continua la expresion abierta arriba con este valor o argumento.
)  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.

OUT_DIR = "test_output"  # Guarda en `OUT_DIR` el resultado de `"test_output"`.

# Palabras elegidas a propósito: todas tienen alguna letra con descendente
# (p, y, q, g, j) y ninguna tiene mayúsculas ni tildes que "engañen" al
# cálculo antiguo dándole más altura de la que en realidad necesitaba.
TEST_WORDS = [  # Inicia la lista que se completa con los elementos de las lineas siguientes.
    "papy",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "jugoso",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "quizás",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "guapo",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "y",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "porque",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "gente",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
    "pequeño",  # Aporta este texto a la lista, llamada o mensaje construido arriba.
]   # Cierra la lista o indice abierto anteriormente.


def main():  # Declara la funcion `main` y especifica sus parametros y tipo de retorno.
    os.makedirs(OUT_DIR, exist_ok=True)  # Crea la ruta de carpetas indicada.
    print(f"Fuente usada: {SUBTITLE_FONT or '(por defecto de Pillow)'}")  # Muestra en la consola el texto o resultado indicado.
    print(f"font_size={SUBTITLE_FONT_SIZE}  stroke_width={SUBTITLE_STROKE_WIDTH}  "  # Muestra en la consola el texto o resultado indicado.
          f"box_height={SUBTITLE_BOX_HEIGHT}\n")  # Aporta esta parte del texto interpolado a la cadena o mensaje construido arriba.

    for word in TEST_WORDS:  # Recorre `TEST_WORDS` y asigna cada elemento a `word`.
        txt_clip_kwargs = dict(  # Guarda en `txt_clip_kwargs` el resultado de `dict(`.
            text=word,  # Guarda en `text` el resultado de `word,`.
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

        clip = TextClip(**txt_clip_kwargs)  # Guarda en `clip` el resultado de `TextClip(**txt_clip_kwargs)`.
        out_path = os.path.join(OUT_DIR, f"subtitle_{word}.png")  # Guarda en `out_path` el resultado de `os.path.join(OUT_DIR, f"subtitle_{word}.png")`.
        clip.save_frame(out_path, t=0)  # Invoca `clip.save_frame` con los argumentos indicados.
        print(f"  ✔ Generado: {out_path}  (tamaño imagen: {clip.size})")  # Muestra en la consola el texto o resultado indicado.

    print(f"\nListo. Abre la carpeta '{OUT_DIR}' y revisa que ninguna letra "  # Muestra en la consola el texto o resultado indicado.
          "(sobre todo la p/y/q/g de abajo) esté cortada por el borde de la imagen.")  # Aporta este texto a la lista, llamada o mensaje construido arriba.


if __name__ == "__main__":  # Solo ejecuta el bloque siguiente si se cumple `__name__ == "__main__"`.
    main()  # Invoca `main` con los argumentos indicados.
