import os
import asyncio
import httpx
from pathlib import Path

IMAGE_SOURCE = os.getenv("IMAGE_SOURCE", "duckduckgo")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


async def _fetch_pexels_image(query: str, index: int) -> str | None:
    if not PEXELS_API_KEY:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 5, "orientation": "landscape"}
        )
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                return photos[index % len(photos)]["src"]["large2x"]
    return None


async def _fetch_duckduckgo_image(query: str) -> str | None:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(
                query,
                max_results=5,
                type_image="photo",
                size="Large",
                color="color",
                layout="Wide"
            ))
            if results:
                return results[0]["image"]
    except Exception:
        pass
    return None


async def _download_image(url: str, dest: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=HEADERS) as client:
            r = await client.get(url)
            if r.status_code == 200 and len(r.content) > 1000:
                Path(dest).write_bytes(r.content)
                return True
    except Exception:
        pass
    return False


def _create_fallback_image(dest: str, text: str, index: int):
    """Generate a gradient placeholder image using PIL."""
    from PIL import Image, ImageDraw, ImageFont
    import math

    w, h = 1920, 1080
    palettes = [
        [(30, 30, 60), (60, 60, 120)],
        [(20, 60, 40), (40, 120, 80)],
        [(60, 30, 30), (120, 60, 60)],
        [(20, 40, 60), (40, 80, 120)],
        [(50, 30, 70), (100, 60, 140)],
    ]
    colors = palettes[index % len(palettes)]

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * t)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * t)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    img.save(dest, "JPEG", quality=90)


async def fetch_section_images(sections, temp_dir: str) -> list[str]:
    image_paths = []
    semaphore = asyncio.Semaphore(3)  # Limit concurrent requests

    async def fetch_one(section, idx):
        async with semaphore:
            dest = os.path.join(temp_dir, f"image_section_{section.id}.jpg")

            url = None
            if IMAGE_SOURCE == "pexels":
                url = await _fetch_pexels_image(section.search_query, idx)
            if not url:
                url = await _fetch_duckduckgo_image(section.search_query)

            success = False
            if url:
                success = await _download_image(url, dest)

            if not success:
                _create_fallback_image(dest, section.heading, idx)

            return dest

    tasks = [fetch_one(s, i) for i, s in enumerate(sections)]
    image_paths = await asyncio.gather(*tasks)
    return list(image_paths)
