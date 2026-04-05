import os
import asyncio
import logging
import uuid
from functools import partial
from typing import Optional

import httpx
from gtts import gTTS

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

LANGUAGE_MAP = {
    "en": "en", "es": "es", "fr": "fr", "de": "de",
    "it": "it", "pt": "pt", "ja": "ja", "zh": "zh-CN",
    "ko": "ko", "ar": "ar", "hi": "hi", "ru": "ru",
}


# ── gTTS fallback ──────────────────────────────────────────────────────────────

def _gtts_blocking(text: str, output_path: str, lang: str) -> str:
    gTTS(text=text, lang=lang, slow=False).save(output_path)
    return output_path


async def synthesize_text(
    text: str, output_path: str, language: str = "en",
    voice_override: Optional[str] = None, retries: int = 3
) -> str:
    lang = LANGUAGE_MAP.get(language, "en")
    loop = asyncio.get_event_loop()
    for attempt in range(retries):
        try:
            await loop.run_in_executor(None, partial(_gtts_blocking, text, output_path, lang))
            return output_path
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                logger.warning(f"gTTS attempt {attempt + 1} failed ({e}), retrying in {wait}s…")
                await asyncio.sleep(wait)
            else:
                raise


# ── ElevenLabs voice cloning ───────────────────────────────────────────────────

async def _clone_voice_elevenlabs(sample_path: str) -> Optional[str]:
    voice_name = f"cloned_{uuid.uuid4().hex[:8]}"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(sample_path, "rb") as f:
                r = await client.post(
                    f"{ELEVENLABS_BASE}/voices/add",
                    headers={"xi-api-key": ELEVENLABS_API_KEY},
                    data={"name": voice_name},
                    files={"files": (os.path.basename(sample_path), f, "audio/mpeg")},
                )
            if r.status_code == 200:
                return r.json().get("voice_id")
            logger.warning(f"ElevenLabs clone failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        logger.warning(f"ElevenLabs clone error: {e}")
    return None


async def _delete_voice_elevenlabs(voice_id: str):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.delete(
                f"{ELEVENLABS_BASE}/voices/{voice_id}",
                headers={"xi-api-key": ELEVENLABS_API_KEY},
            )
    except Exception as e:
        logger.warning(f"Failed to delete ElevenLabs voice {voice_id}: {e}")


async def _synthesize_elevenlabs(text: str, voice_id: str, output_path: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )
        r.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(r.content)
    return output_path


# ── Coqui XTTS v2 (free, local, no API key) ───────────────────────────────────

XTTS_LANGUAGE_MAP = {
    "en": "en", "es": "es", "fr": "fr", "de": "de",
    "it": "it", "pt": "pt", "ru": "ru", "ar": "ar",
    "zh": "zh-cn", "ko": "ko", "ja": "ja", "hi": "hi",
}


def _run_xtts_sync(sections, temp_dir: str, sample_path: str, language: str) -> list[str]:
    from TTS.api import TTS as CoquiTTS
    lang = XTTS_LANGUAGE_MAP.get(language, "en")
    tts = CoquiTTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    audio_paths = []
    for section in sections:
        path = os.path.join(temp_dir, f"audio_section_{section.id}.wav")
        text = f"{section.heading}. {section.narration}"
        tts.tts_to_file(text=text, speaker_wav=sample_path, language=lang, file_path=path)
        audio_paths.append(path)
    return audio_paths


async def _synthesize_with_coqui_xtts(
    sections, temp_dir: str, sample_path: str, language: str
) -> list[str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(_run_xtts_sync, sections, temp_dir, sample_path, language)
    )


# ── Main synthesis entry points ────────────────────────────────────────────────

async def synthesize_sections(
    sections,
    temp_dir: str,
    language: str = "en",
    voice_override: Optional[str] = None,
    voice_sample_path: Optional[str] = None,
) -> list[str]:

    if voice_sample_path:
        if ELEVENLABS_API_KEY:
            # ElevenLabs: best quality, uses API key
            return await _synthesize_with_elevenlabs(sections, temp_dir, voice_sample_path)
        else:
            # Coqui XTTS v2: free, local, no key required
            try:
                logger.info("Using Coqui XTTS v2 for voice cloning (first run downloads ~1.8GB model)…")
                return await _synthesize_with_coqui_xtts(sections, temp_dir, voice_sample_path, language)
            except Exception as e:
                logger.warning(f"Coqui XTTS failed: {e} — falling back to gTTS")

    # Default: gTTS
    audio_paths = []
    for section in sections:
        path = os.path.join(temp_dir, f"audio_section_{section.id}.mp3")
        full_text = f"{section.heading}. {section.narration}"
        audio_paths.append(await synthesize_text(full_text, path, language, voice_override))
    return audio_paths


async def _synthesize_with_elevenlabs(sections, temp_dir: str, sample_path: str) -> list[str]:
    voice_id = await _clone_voice_elevenlabs(sample_path)
    if not voice_id:
        logger.warning("ElevenLabs clone failed — falling back to gTTS")
        return await synthesize_sections(sections, temp_dir)

    audio_paths = []
    try:
        for section in sections:
            path = os.path.join(temp_dir, f"audio_section_{section.id}.mp3")
            text = f"{section.heading}. {section.narration}"
            try:
                await _synthesize_elevenlabs(text, voice_id, path)
            except Exception as e:
                logger.warning(f"ElevenLabs TTS section {section.id} failed: {e} — using gTTS")
                await synthesize_text(text, path)
            audio_paths.append(path)
    finally:
        await _delete_voice_elevenlabs(voice_id)

    return audio_paths


async def list_voices() -> list[dict]:
    return [{"name": lang, "gender": "N/A", "locale": lang} for lang in LANGUAGE_MAP]
