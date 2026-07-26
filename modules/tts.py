"""
modules/tts.py
Módulo 2: Texto a Voz (TTS).

Convierte el título + cuerpo de la historia en un único archivo MP3
usando edge-tts (voces neuronales gratuitas de Microsoft Edge, sin API key).
"""

import asyncio
from typing import List

import edge_tts

from config import AUDIO_DIR, TTS_PITCH, TTS_RATE, TTS_VOICE


async def _generate_audio(text: str, output_path: str, voice: str, rate: str, pitch: str) -> None:
    """Llamada async real a edge-tts. edge-tts SOLO funciona de forma asíncrona."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)


def text_to_speech(
    title: str,
    body: str,
    output_filename: str,
    voice: str = TTS_VOICE,
    rate: str = TTS_RATE,
    pitch: str = TTS_PITCH,
) -> str:
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
    script_text = f"{title.strip()}. ... {body.strip()}"

    output_path = str(AUDIO_DIR / output_filename)
    asyncio.run(_generate_audio(script_text, output_path, voice, rate, pitch))

    print(f"[tts] Audio generado en: {output_path}")
    return output_path


async def _list_spanish_voices() -> List[dict]:
    """Devuelve solo las voces en español disponibles en edge-tts."""
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith("es-")]


def list_spanish_voices() -> None:
    """Utilidad de consola para ver qué voces en español puedes usar."""
    voices = asyncio.run(_list_spanish_voices())
    for v in voices:
        print(f"{v['ShortName']:<25} {v['Gender']:<8} {v['Locale']}")


if __name__ == "__main__":
    import sys

    if "--list-voices" in sys.argv:
        list_spanish_voices()
    else:
        # Prueba rápida y aislada del módulo: python modules/tts.py
        ruta = text_to_speech(
            title="Título de prueba",
            body=(
                "Este es un cuerpo de historia de prueba para comprobar que "
                "la voz en español funciona correctamente antes de conectarlo "
                "con el scraper."
            ),
            output_filename="test_audio.mp3",
        )
        print(f"Archivo de prueba creado en: {ruta}")
