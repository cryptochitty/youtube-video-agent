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


async def _fetch_unsplash_image(query: str) -> str | None:
    """Use Unsplash source API — free, no key, returns relevant photo."""
    try:
        slug = query.replace(" ", ",")
        url = f"https://source.unsplash.com/1920x1080/?{slug}"
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as client:
            r = await client.get(url)
            if r.status_code == 200 and len(r.content) > 5000:
                return str(r.url)
    except Exception:
        pass
    return None


async def _fetch_duckduckgo_image(query: str) -> str | None:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5))
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
    """Generate a visually rich gradient placeholder with centered heading text."""
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    w, h = 1920, 1080
    palettes = [
        [(15, 25, 60), (40, 70, 140)],
        [(10, 45, 30), (30, 100, 70)],
        [(50, 15, 20), (110, 40, 50)],
        [(10, 30, 55), (30, 70, 120)],
        [(40, 15, 60), (90, 40, 130)],
    ]
    c0, c1 = palettes[index % len(palettes)]

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(c0[0] + (c1[0] - c0[0]) * t)
        g = int(c0[1] + (c1[1] - c0[1]) * t)
        b = int(c0[2] + (c1[2] - c0[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Accent lines
    draw.rectangle([0, h // 2 - 2, w, h // 2 + 2], fill=(255, 255, 255, 80))
    draw.rectangle([80, h // 2 - 80, 84, h // 2 + 80], fill=(100, 180, 255))

    # Centered heading text
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 72)
        font_sub = ImageFont.truetype(font_path, 38)
    except Exception:
        font = ImageFont.load_default()
        font_sub = font

    wrapped = textwrap.fill(text, width=30)
    lines = wrapped.split("\n")
    line_h = 90
    total_h = len(lines) * line_h
    start_y = h // 2 - total_h // 2 - 20

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x + 2, start_y + i * line_h + 2), line, font=font, fill=(0, 0, 0, 120))
        draw.text((x, start_y + i * line_h), line, font=font, fill=(255, 255, 255))

    img.save(dest, "JPEG", quality=90)


IMAGES_PER_SECTION = 2  # fetch multiple images per section for variety


async def fetch_section_images(sections, temp_dir: str) -> list[list[str]]:
    """Returns a list of image path lists — multiple images per section."""
    semaphore = asyncio.Semaphore(4)

    async def fetch_one(section, idx, img_idx) -> str:
        async with semaphore:
            dest = os.path.join(temp_dir, f"image_section_{section.id}_{img_idx}.jpg")

            # Vary the query slightly for the second image
            query = section.search_query if img_idx == 0 else f"{section.search_query} background"

            url = None
            if IMAGE_SOURCE == "pexels":
                url = await _fetch_pexels_image(query, idx + img_idx)
            if not url:
                url = await _fetch_unsplash_image(query)
            if not url:
                url = await _fetch_duckduckgo_image(query)

            if url and await _download_image(url, dest):
                return dest

            _create_fallback_image(dest, section.heading, idx + img_idx)
            return dest

    tasks = []
    for i, s in enumerate(sections):
        for j in range(IMAGES_PER_SECTION):
            tasks.append((s, i, j))

    results = await asyncio.gather(*[fetch_one(s, i, j) for s, i, j in tasks])

    # Group back into per-section lists
    n = IMAGES_PER_SECTION
    return [list(results[i * n:(i + 1) * n]) for i in range(len(sections))]
