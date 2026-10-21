"""
modules/tts.py
Módulo 2: Texto a Voz (TTS).

Convierte el título + cuerpo de la historia en un único archivo MP3
usando edge-tts (voces neuronales gratuitas de Microsoft Edge, sin API key).
"""

import asyncio  # Importa `asyncio` para utilizarlo en este archivo.
import logging  # Importa `logging` para utilizarlo en este archivo.
from typing import List  # Importa los nombres necesarios desde `typing`.

import edge_tts  # Importa `edge_tts` para utilizarlo en este archivo.

from config import AUDIO_DIR, TTS_PITCH, TTS_RATE, TTS_VOICE  # Importa los nombres necesarios desde `config`.

logger = logging.getLogger("reddit_bot")  # Guarda en `logger` el resultado de `logging.getLogger("reddit_bot")`.


async def _generate_audio(text: str, output_path: str, voice: str, rate: str, pitch: str) -> None:  # Declara la funcion `_generate_audio` y especifica sus parametros y tipo de retorno.
    """Llamada async real a edge-tts. edge-tts SOLO funciona de forma asíncrona."""  # Ejecuta la operacion indicada por esta expresion.
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)  # Guarda en `communicate` el resultado de `edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)`.
    await communicate.save(output_path)  # Ejecuta la operacion indicada por esta expresion.


def text_to_speech(  # Declara la funcion `text_to_speech` y especifica sus parametros y tipo de retorno.
    title: str,  # Define el valor del argumento o campo title en la estructura anterior.
    body: str,  # Define el valor del argumento o campo body en la estructura anterior.
    output_filename: str,  # Define el valor del argumento o campo output_filename en la estructura anterior.
    voice: str = TTS_VOICE,  # Define el valor del argumento o campo voice en la estructura anterior.
    rate: str = TTS_RATE,  # Define el valor del argumento o campo rate en la estructura anterior.
    pitch: str = TTS_PITCH,  # Define el valor del argumento o campo pitch en la estructura anterior.
) -> str:  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
    """
    Genera un MP3 narrando "título + pausa + cuerpo".

    Args:
        title: título del post de Reddit.
        body: cuerpo del post de Reddit.
        output_filename: nombre del archivo, ej. "abc123.mp3".

    Returns:
        Ruta absoluta del archivo de audio generado (dentro de AUDIO_DIR).
    """
    # Los "..." generan una pausa natural entre el título y el cuerpo.
    # Para pausas más controladas se podría migrar a SSML, pero esto
    # es suficiente para un primer flujo funcional.
    script_text = f"{title.strip()}. ... {body.strip()}"  # Guarda en `script_text` el resultado de `f"{title.strip()}. ... {body.strip()}"`.

    output_path = str(AUDIO_DIR / output_filename)  # Guarda en `output_path` el resultado de `str(AUDIO_DIR / output_filename)`.
    asyncio.run(_generate_audio(script_text, output_path, voice, rate, pitch))  # Ejecuta el proceso o funcion indicado.

    logger.info(f"[tts] Audio generado en: {output_path}")  # Registra el mensaje de informacion para que aparezca en la consola o en el archivo de log.
    return output_path  # Devuelve `output_path` al llamador y termina esta funcion.


async def _list_spanish_voices() -> List[dict]:  # Declara la funcion `_list_spanish_voices` y especifica sus parametros y tipo de retorno.
    """Devuelve solo las voces en español disponibles en edge-tts."""  # Ejecuta la operacion indicada por esta expresion.
    voices = await edge_tts.list_voices()  # Guarda en `voices` el resultado de `await edge_tts.list_voices()`.
    return [v for v in voices if v["Locale"].startswith("es-")]  # Devuelve `[v for v in voices if v["Locale"].startswith("es-")]` al llamador y termina esta funcion.


def list_spanish_voices() -> None:  # Declara la funcion `list_spanish_voices` y especifica sus parametros y tipo de retorno.
    """Utilidad de consola para ver qué voces en español puedes usar."""  # Ejecuta la operacion indicada por esta expresion.
    voices = asyncio.run(_list_spanish_voices())  # Guarda en `voices` el resultado de `asyncio.run(_list_spanish_voices())`.
    for v in voices:  # Recorre `voices` y asigna cada elemento a `v`.
        print(f"{v['ShortName']:<25} {v['Gender']:<8} {v['Locale']}")  # Muestra en la consola el texto o resultado indicado.


if __name__ == "__main__":  # Solo ejecuta el bloque siguiente si se cumple `__name__ == "__main__"`.
    import sys  # Importa `sys` para utilizarlo en este archivo.

    if "--list-voices" in sys.argv:  # Solo ejecuta el bloque siguiente si se cumple `"--list-voices" in sys.argv`.
        list_spanish_voices()  # Invoca `list_spanish_voices` con los argumentos indicados.
    else:  # Ejecuta este bloque cuando no se cumple la condicion o rama anterior.
        # Prueba rápida y aislada del módulo: python modules/tts.py
        ruta = text_to_speech(  # Guarda en `ruta` el resultado de `text_to_speech(`.
            title="Título de prueba",  # Guarda en `title` el resultado de `"Título de prueba",`.
            body=(  # Guarda en `body` el resultado de `(`.
                "Este es un cuerpo de historia de prueba para comprobar que "  # Ejecuta la operacion indicada por esta expresion.
                "la voz en español funciona correctamente antes de conectarlo "  # Ejecuta la operacion indicada por esta expresion.
                "con el scraper."  # Ejecuta la operacion indicada por esta expresion.
            ),  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
            output_filename="test_audio.mp3",  # Guarda en `output_filename` el resultado de `"test_audio.mp3",`.
        )  # Cierra la llamada o agrupacion de argumentos abierta anteriormente.
        print(f"Archivo de prueba creado en: {ruta}")  # Muestra en la consola el texto o resultado indicado.
