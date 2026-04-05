import json
import os
import httpx
from app.models.job import VideoRequest, VideoScript, ScriptSection

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _build_prompt(request: VideoRequest, context: str = "") -> str:
    duration = int(request.duration.value)
    num_sections = max(3, duration // 45)
    context_line = ("- Reference content from uploaded file:\n" + context) if context else ""

    return f"""You are a professional YouTube content creator and scriptwriter.

Create a complete YouTube video script for the following:
- Topic: {request.topic}
- Style: {request.style.value}
- Target duration: ~{duration} seconds
- Language: {request.language}
{f'- Extra instructions: {request.extra_instructions}' if request.extra_instructions else ''}
{context_line}

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "title": "Compelling YouTube video title (under 70 chars)",
  "description": "YouTube description (150-300 words, with timestamps and hashtags)",
  "tags": ["tag1", "tag2", "tag3", ...],
  "hook": "Opening hook sentence to grab attention in first 5 seconds",
  "sections": [
    {{
      "id": 1,
      "heading": "Section title shown on screen",
      "narration": "Full narration text for this section (will be spoken by TTS)",
      "visual_description": "Description of what visuals to show",
      "search_query": "Short Pexels/image search query (2-4 words)",
      "duration_seconds": 30
    }}
  ],
  "call_to_action": "End call to action text (like and subscribe message)",
  "total_duration_seconds": {duration}
}}

Requirements:
- Create exactly {num_sections} sections
- Each section's narration should be natural spoken language
- search_query must be simple English even if language is not English
- Sections durations should add up to approximately {duration - 10} seconds (leave room for intro/outro)
- Make content engaging, informative and suitable for YouTube
"""


async def _call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7}
            }
        )
        response.raise_for_status()
        return response.json()["response"]


async def _call_groq(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def _parse_script(raw: str, request: VideoRequest) -> VideoScript:
    # Extract JSON from response (handle markdown code blocks)
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    # Find JSON object boundaries
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]

    data = json.loads(raw)
    sections = [ScriptSection(**s) for s in data["sections"]]
    return VideoScript(
        title=data["title"],
        description=data["description"],
        tags=data.get("tags", []),
        hook=data.get("hook", ""),
        sections=sections,
        call_to_action=data.get("call_to_action", "Like and subscribe for more!"),
        total_duration_seconds=data.get("total_duration_seconds", int(request.duration.value))
    )


async def generate_script(request: VideoRequest, context: str = "") -> VideoScript:
    prompt = _build_prompt(request, context)

    if LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Set it in .env or switch to LLM_PROVIDER=ollama")
        raw = await _call_groq(prompt)
    else:
        raw = await _call_ollama(prompt)

    return _parse_script(raw, request)
