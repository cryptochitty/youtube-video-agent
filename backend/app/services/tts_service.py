import os
import asyncio
import edge_tts
from pathlib import Path

TTS_VOICE = os.getenv("TTS_VOICE", "en-US-AriaNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")

# Language to voice map (free edge-tts voices)
LANGUAGE_VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ko": "ko-KR-SunHiNeural",
    "ar": "ar-SA-ZariyahNeural",
    "hi": "hi-IN-SwaraNeural",
    "ru": "ru-RU-SvetlanaNeural",
}


async def synthesize_text(text: str, output_path: str, language: str = "en", voice_override: str = None) -> str:
    voice = voice_override or TTS_VOICE

    # Auto-select voice based on language if using default
    if not voice_override and voice == "en-US-AriaNeural" and language != "en":
        voice = LANGUAGE_VOICE_MAP.get(language, "en-US-AriaNeural")

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=TTS_RATE,
        pitch=TTS_PITCH
    )
    await communicate.save(output_path)
    return output_path


async def synthesize_sections(sections, temp_dir: str, language: str = "en", voice_override: str = None) -> list[str]:
    audio_paths = []
    tasks = []

    for section in sections:
        path = os.path.join(temp_dir, f"audio_section_{section.id}.mp3")
        full_text = f"{section.heading}. {section.narration}"
        tasks.append(synthesize_text(full_text, path, language, voice_override))

    results = await asyncio.gather(*tasks)
    audio_paths = list(results)
    return audio_paths


async def list_voices() -> list[dict]:
    voices = await edge_tts.list_voices()
    return [{"name": v["Name"], "gender": v["Gender"], "locale": v["Locale"]} for v in voices]
