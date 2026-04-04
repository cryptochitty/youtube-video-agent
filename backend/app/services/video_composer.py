import os
import asyncio
import textwrap
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", 1920))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", 1080))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", 24))

FONT_PATH = None  # Will auto-detect system font


def _get_font(size: int):
    from PIL import ImageFont
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Windows/Fonts/arial.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _get_font_regular(size: int):
    from PIL import ImageFont
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Windows/Fonts/arial.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _create_title_card(title: str, hook: str) -> np.ndarray:
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), color=(10, 10, 20))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(VIDEO_HEIGHT):
        t = y / VIDEO_HEIGHT
        r = int(10 + 30 * t)
        g = int(10 + 20 * t)
        b = int(20 + 60 * t)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))

    # Accent bar
    draw.rectangle([0, VIDEO_HEIGHT // 2 - 3, VIDEO_WIDTH, VIDEO_HEIGHT // 2 + 3], fill=(100, 150, 255))

    # Title text
    font_title = _get_font(80)
    font_hook = _get_font_regular(44)

    # Wrap title
    wrapped = textwrap.fill(title, width=35)
    lines = wrapped.split("\n")
    total_h = len(lines) * 90
    start_y = VIDEO_HEIGHT // 2 - total_h // 2 - 80

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        y = start_y + i * 90
        # Shadow
        draw.text((x + 3, y + 3), line, font=font_title, fill=(0, 0, 0, 180))
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255))

    # Hook text
    wrapped_hook = textwrap.fill(hook, width=60)
    hook_lines = wrapped_hook.split("\n")
    hook_y = VIDEO_HEIGHT // 2 + 30
    for i, line in enumerate(hook_lines):
        bbox = draw.textbbox((0, 0), line, font=font_hook)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        draw.text((x, hook_y + i * 52), line, font=font_hook, fill=(200, 210, 255))

    return np.array(img)


def _create_end_card(cta: str) -> np.ndarray:
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), color=(10, 10, 20))
    draw = ImageDraw.Draw(img)

    for y in range(VIDEO_HEIGHT):
        t = y / VIDEO_HEIGHT
        r = int(20 + 10 * t)
        g = int(10 + 10 * t)
        b = int(40 + 40 * t)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b))

    font_big = _get_font(90)
    font_cta = _get_font_regular(50)

    # Thanks message
    thanks = "Thank You for Watching!"
    bbox = draw.textbbox((0, 0), thanks, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2 + 3, VIDEO_HEIGHT // 2 - 120 + 3), thanks, font=font_big, fill=(0, 0, 0))
    draw.text(((VIDEO_WIDTH - tw) // 2, VIDEO_HEIGHT // 2 - 120), thanks, font=font_big, fill=(255, 220, 50))

    # CTA
    wrapped = textwrap.fill(cta, width=50)
    cta_lines = wrapped.split("\n")
    for i, line in enumerate(cta_lines):
        bbox = draw.textbbox((0, 0), line, font=font_cta)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        draw.text((x, VIDEO_HEIGHT // 2 + 30 + i * 60), line, font=font_cta, fill=(200, 220, 255))

    # Subscribe reminder
    sub_font = _get_font(60)
    sub_text = "Like  |  Subscribe  |  Share"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2, VIDEO_HEIGHT - 180), sub_text, font=sub_font, fill=(100, 200, 100))

    return np.array(img)


def _resize_and_crop(img: Image.Image) -> Image.Image:
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
    iw, ih = img.size
    img_ratio = iw / ih

    if img_ratio > target_ratio:
        new_h = ih
        new_w = int(ih * target_ratio)
    else:
        new_w = iw
        new_h = int(iw / target_ratio)

    left = (iw - new_w) // 2
    top = (ih - new_h) // 2
    img = img.crop((left, top, left + new_w, top + new_h))
    return img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS)


def _add_text_overlay(frame: np.ndarray, heading: str) -> np.ndarray:
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    font = _get_font(52)

    # Bottom bar overlay
    bar_h = 100
    overlay = Image.new("RGBA", (VIDEO_WIDTH, bar_h), (0, 0, 0, 160))
    img = img.convert("RGBA")
    img.paste(overlay, (0, VIDEO_HEIGHT - bar_h), overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent line
    draw.rectangle([0, VIDEO_HEIGHT - bar_h, VIDEO_WIDTH, VIDEO_HEIGHT - bar_h + 4], fill=(100, 150, 255))

    wrapped = textwrap.fill(heading, width=55)
    bbox = draw.textbbox((0, 0), wrapped.split("\n")[0], font=font)
    tw = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - min(tw, VIDEO_WIDTH - 40)) // 2
    draw.text((x, VIDEO_HEIGHT - bar_h + 18), wrapped.split("\n")[0], font=font, fill=(255, 255, 255))

    return np.array(img)


def _load_image(path: str) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return _resize_and_crop(img)


def _ken_burns_frames(img: Image.Image, num_frames: int, zoom_in: bool = True) -> list[np.ndarray]:
    """Generate Ken Burns effect frames (slow zoom)."""
    frames = []
    iw, ih = img.size
    zoom_start = 1.0
    zoom_end = 1.08

    if not zoom_in:
        zoom_start, zoom_end = zoom_end, zoom_start

    for i in range(num_frames):
        t = i / max(num_frames - 1, 1)
        zoom = zoom_start + (zoom_end - zoom_start) * t

        nw = int(iw / zoom)
        nh = int(ih / zoom)
        x_offset = (iw - nw) // 2
        y_offset = (ih - nh) // 2

        cropped = img.crop((x_offset, y_offset, x_offset + nw, y_offset + nh))
        resized = cropped.resize((iw, ih), Image.LANCZOS)
        frames.append(np.array(resized))

    return frames


def _static_frames(frame: np.ndarray, num_frames: int) -> list[np.ndarray]:
    return [frame] * num_frames


def _seconds_to_frames(seconds: float) -> int:
    return max(1, int(seconds * VIDEO_FPS))


async def compose_video(
    script,
    audio_paths: list[str],
    image_paths: list[str],
    output_path: str,
    progress_callback: Callable[[int, str], None] = None
) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _compose_video_sync, script, audio_paths, image_paths, output_path, progress_callback)


def _compose_video_sync(script, audio_paths, image_paths, output_path, progress_callback):
    from moviepy.editor import (
        ImageClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip, ImageSequenceClip
    )
    import moviepy.editor as mpe

    clips = []
    title_duration = 3
    end_duration = 4

    if progress_callback:
        progress_callback(5, "Creating title card...")

    # Title card
    title_frame = _create_title_card(script.title, script.hook)
    title_frames = _static_frames(title_frame, _seconds_to_frames(title_duration))
    title_clip = ImageSequenceClip(title_frames, fps=VIDEO_FPS)
    clips.append(title_clip)

    total_sections = len(script.sections)
    for i, section in enumerate(script.sections):
        if progress_callback:
            pct = 10 + int(i / total_sections * 70)
            progress_callback(pct, f"Processing section {i + 1}/{total_sections}: {section.heading}")

        # Load audio
        audio_path = audio_paths[i] if i < len(audio_paths) else None
        audio_duration = section.duration_seconds

        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration
            except Exception:
                audio_clip = None
                audio_duration = section.duration_seconds
        else:
            audio_clip = None

        num_frames = _seconds_to_frames(audio_duration)

        # Load and process image
        img_path = image_paths[i] if i < len(image_paths) else None
        if img_path and os.path.exists(img_path):
            try:
                img = _load_image(img_path)
                zoom_in = (i % 2 == 0)
                frames = _ken_burns_frames(img, num_frames, zoom_in)
            except Exception:
                fallback = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
                frames = _static_frames(fallback, num_frames)
        else:
            fallback = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
            frames = _static_frames(fallback, num_frames)

        # Add text overlay to each frame
        frames = [_add_text_overlay(f, section.heading) for f in frames]

        section_clip = ImageSequenceClip(frames, fps=VIDEO_FPS)
        if audio_clip:
            section_clip = section_clip.set_audio(audio_clip)
        clips.append(section_clip)

    if progress_callback:
        progress_callback(85, "Creating end card...")

    # End card
    end_frame = _create_end_card(script.call_to_action)
    end_frames = _static_frames(end_frame, _seconds_to_frames(end_duration))
    end_clip = ImageSequenceClip(end_frames, fps=VIDEO_FPS)
    clips.append(end_clip)

    if progress_callback:
        progress_callback(90, "Rendering final video...")

    final = concatenate_videoclips(clips, method="compose")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.write_videofile(
        output_path,
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=output_path.replace(".mp4", "_temp_audio.m4a"),
        remove_temp=True,
        verbose=False,
        logger=None
    )

    if progress_callback:
        progress_callback(100, "Done!")

    return output_path
