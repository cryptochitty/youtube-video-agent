import os
import asyncio
import textwrap
from typing import Callable

from PIL import Image, ImageDraw, ImageFont
import numpy as np

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", 1920))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", 1080))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", 24))
CROSSFADE = 0.5  # seconds


def _fc_match(pattern: str) -> str | None:
    """Use fc-match to find a font path dynamically."""
    try:
        import subprocess
        result = subprocess.run(
            ["fc-match", "--format=%{file}", pattern],
            capture_output=True, text=True, timeout=3
        )
        path = result.stdout.strip()
        if result.returncode == 0 and path and os.path.exists(path):
            return path
    except Exception:
        pass
    return None


def _get_font(size: int):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Windows/Fonts/arial.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    path = _fc_match("sans:bold")
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _get_font_regular(size: int):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Windows/Fonts/arial.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    path = _fc_match("sans")
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _draw_gradient_bg(draw, w, h, c0, c1):
    for y in range(0, h, 3):
        t = y / h
        r = int(c0[0] + (c1[0] - c0[0]) * t)
        g = int(c0[1] + (c1[1] - c0[1]) * t)
        b = int(c0[2] + (c1[2] - c0[2]) * t)
        draw.rectangle([(0, y), (w, y + 2)], fill=(r, g, b))


def _create_title_card(title: str, hook: str) -> np.ndarray:
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    _draw_gradient_bg(draw, VIDEO_WIDTH, VIDEO_HEIGHT, (8, 12, 35), (25, 40, 90))

    draw.rectangle([0, VIDEO_HEIGHT // 2 - 3, VIDEO_WIDTH, VIDEO_HEIGHT // 2 + 3], fill=(80, 130, 255))
    draw.rectangle([VIDEO_WIDTH // 2 - 3, 0, VIDEO_WIDTH // 2 + 3, VIDEO_HEIGHT], fill=(80, 130, 255, 40))

    font_title = _get_font(80)
    font_hook = _get_font_regular(44)

    wrapped = textwrap.fill(title, width=35)
    lines = wrapped.split("\n")
    total_h = len(lines) * 92
    start_y = VIDEO_HEIGHT // 2 - total_h // 2 - 80
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        y = start_y + i * 92
        draw.text((x + 3, y + 3), line, font=font_title, fill=(0, 0, 0))
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255))

    wrapped_hook = textwrap.fill(hook, width=60)
    hook_y = VIDEO_HEIGHT // 2 + 30
    for i, line in enumerate(wrapped_hook.split("\n")):
        bbox = draw.textbbox((0, 0), line, font=font_hook)
        tw = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - tw) // 2, hook_y + i * 52), line, font=font_hook, fill=(190, 210, 255))

    return np.array(img)


def _create_end_card(cta: str) -> np.ndarray:
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    _draw_gradient_bg(draw, VIDEO_WIDTH, VIDEO_HEIGHT, (15, 8, 35), (45, 20, 90))

    font_big = _get_font(90)
    font_cta = _get_font_regular(50)
    font_sub = _get_font(58)

    thanks = "Thank You for Watching!"
    bbox = draw.textbbox((0, 0), thanks, font=font_big)
    tw = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - tw) // 2
    draw.text((x + 3, VIDEO_HEIGHT // 2 - 130 + 3), thanks, font=font_big, fill=(0, 0, 0))
    draw.text((x, VIDEO_HEIGHT // 2 - 130), thanks, font=font_big, fill=(255, 215, 40))

    # Divider
    draw.rectangle([VIDEO_WIDTH // 4, VIDEO_HEIGHT // 2 - 10, 3 * VIDEO_WIDTH // 4, VIDEO_HEIGHT // 2 - 7], fill=(255, 215, 40, 120))

    for i, line in enumerate(textwrap.fill(cta, width=50).split("\n")):
        bbox = draw.textbbox((0, 0), line, font=font_cta)
        tw = bbox[2] - bbox[0]
        draw.text(((VIDEO_WIDTH - tw) // 2, VIDEO_HEIGHT // 2 + 20 + i * 60), line, font=font_cta, fill=(200, 220, 255))

    sub_text = "Like  |  Subscribe  |  Share"
    bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_WIDTH - tw) // 2, VIDEO_HEIGHT - 170), sub_text, font=font_sub, fill=(100, 220, 120))

    return np.array(img)


def _resize_and_crop(img: Image.Image) -> Image.Image:
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
    iw, ih = img.size
    img_ratio = iw / ih
    if img_ratio > target_ratio:
        new_w = int(ih * target_ratio)
        new_h = ih
    else:
        new_w = iw
        new_h = int(iw / target_ratio)
    left = (iw - new_w) // 2
    top = (ih - new_h) // 2
    return img.crop((left, top, left + new_w, top + new_h)).resize(
        (VIDEO_WIDTH, VIDEO_HEIGHT), Image.LANCZOS
    )


def _add_presenter_overlay(frame: np.ndarray, presenter: "Image.Image", bar_h: int = 110) -> np.ndarray:
    """Paste circular presenter photo above the text bar, bottom-right."""
    img = Image.fromarray(frame).convert("RGBA")
    pw, ph = presenter.size
    x = VIDEO_WIDTH - pw - 20
    y = VIDEO_HEIGHT - bar_h - ph - 10
    img.paste(presenter, (x, y), presenter)
    return np.array(img.convert("RGB"))


def _add_text_overlay(frame: np.ndarray, heading: str, t: float, duration: float) -> np.ndarray:
    """Bottom bar with text that fades in over first 0.4s."""
    img = Image.fromarray(frame)
    font = _get_font(52)
    bar_h = 110

    # Fade-in alpha for text bar
    alpha = min(1.0, t / 0.4)
    bar_alpha = int(170 * alpha)

    overlay = Image.new("RGBA", (VIDEO_WIDTH, bar_h), (0, 0, 0, bar_alpha))
    img_rgba = img.convert("RGBA")
    img_rgba.paste(overlay, (0, VIDEO_HEIGHT - bar_h), overlay)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent bar
    draw.rectangle(
        [0, VIDEO_HEIGHT - bar_h, int(VIDEO_WIDTH * min(1.0, t / 0.8)), VIDEO_HEIGHT - bar_h + 5],
        fill=(80, 150, 255)
    )

    line = textwrap.fill(heading, width=55).split("\n")[0]
    bbox = draw.textbbox((0, 0), line, font=font)
    tw = bbox[2] - bbox[0]
    x = (VIDEO_WIDTH - min(tw, VIDEO_WIDTH - 40)) // 2
    text_alpha = int(255 * alpha)
    draw.text((x, VIDEO_HEIGHT - bar_h + 20), line, font=font,
              fill=(255, 255, 255, text_alpha))

    return np.array(img)


# Motion styles: (zoom_in, pan_direction)
_MOTION_STYLES = [
    (True,  "center"),
    (False, "left"),
    (True,  "right"),
    (False, "center"),
    (True,  "left"),
    (False, "right"),
]


def _make_motion_frame(img: Image.Image, t: float, duration: float, style_idx: int) -> np.ndarray:
    """Ken Burns with pan variation — no pre-built frame list."""
    zoom_in, pan = _MOTION_STYLES[style_idx % len(_MOTION_STYLES)]
    iw, ih = img.size
    zoom_start, zoom_end = (1.0, 1.10) if zoom_in else (1.10, 1.0)
    progress = t / max(duration, 0.001)
    zoom = zoom_start + (zoom_end - zoom_start) * progress

    nw = int(iw / zoom)
    nh = int(ih / zoom)

    if pan == "center":
        x_offset = (iw - nw) // 2
    elif pan == "left":
        # pan right-to-left: start right, end left
        x_offset = int((iw - nw) * (1.0 - progress))
    else:  # right
        x_offset = int((iw - nw) * progress)

    y_offset = (ih - nh) // 2
    cropped = img.crop((x_offset, y_offset, x_offset + nw, y_offset + nh))
    return np.array(cropped.resize((iw, ih), Image.BILINEAR))


async def compose_video(
    script,
    audio_paths: list[str],
    image_paths: list,
    output_path: str,
    progress_callback: Callable[[int, str], None] = None,
    presenter_photo_path: str = None,
) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _compose_video_sync, script, audio_paths, image_paths,
        output_path, progress_callback, presenter_photo_path
    )


async def extract_audio_only(video_path: str, audio_output: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_audio_sync, video_path, audio_output)


async def extract_video_only(video_path: str, video_output: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_video_only_sync, video_path, video_output)


def _extract_audio_sync(video_path: str, audio_output: str) -> str:
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(video_path)
    if clip.audio:
        clip.audio.write_audiofile(audio_output, verbose=False, logger=None)
    clip.close()
    return audio_output


def _extract_video_only_sync(video_path: str, video_output: str) -> str:
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(video_path).without_audio()
    clip.write_videofile(
        video_output, codec="libx264", verbose=False, logger=None,
        temp_audiofile=video_output.replace(".mp4", "_tmp.m4a"),
    )
    clip.close()
    return video_output


def _prepare_presenter_overlay(photo_path: str, size: int = 180):
    """Pre-process presenter photo into a ready-to-paste RGBA PIL Image."""
    try:
        img = Image.open(photo_path).convert("RGB")
        img = img.resize((size, size), Image.LANCZOS)

        # Circular mask
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)

        # White border ring
        ring_size = size + 8
        ring = Image.new("RGBA", (ring_size, ring_size), (255, 255, 255, 220))
        ring_mask = Image.new("L", (ring_size, ring_size), 0)
        ImageDraw.Draw(ring_mask).ellipse([0, 0, ring_size, ring_size], fill=255)
        ring.putalpha(ring_mask)

        presenter_rgba = img.convert("RGBA")
        presenter_rgba.putalpha(mask)
        ring.paste(presenter_rgba, (4, 4), presenter_rgba)
        return ring
    except Exception:
        return None


def _compose_video_sync(script, audio_paths, image_paths, output_path, progress_callback, presenter_photo_path=None):
    from moviepy.editor import (
        ImageClip, AudioFileClip, concatenate_videoclips, VideoClip,
    )

    # Pre-process presenter photo once (expensive — do NOT do this inside make_frame)
    presenter_overlay = None
    if presenter_photo_path and os.path.exists(presenter_photo_path):
        presenter_overlay = _prepare_presenter_overlay(presenter_photo_path)

    clips = []
    title_duration = 3
    end_duration = 5

    if progress_callback:
        progress_callback(5, "Creating title card...")

    title_clip = ImageClip(_create_title_card(script.title, script.hook), duration=title_duration)
    clips.append(title_clip.crossfadeout(CROSSFADE))

    total_sections = len(script.sections)
    for i, section in enumerate(script.sections):
        if progress_callback:
            pct = 10 + int(i / total_sections * 70)
            progress_callback(pct, f"Processing section {i + 1}/{total_sections}: {section.heading}")

        # Audio
        audio_clip = None
        audio_duration = float(section.duration_seconds)
        audio_path = audio_paths[i] if i < len(audio_paths) else None
        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration
            except Exception:
                pass

        # Load images for this section (may be a list or a single path for backward compat)
        section_imgs_raw = image_paths[i] if i < len(image_paths) else []
        if isinstance(section_imgs_raw, str):
            section_imgs_raw = [section_imgs_raw]

        pil_imgs = []
        for p in section_imgs_raw:
            if p and os.path.exists(p):
                try:
                    pil_imgs.append(_resize_and_crop(Image.open(p).convert("RGB")))
                except Exception:
                    pass

        if not pil_imgs:
            pil_imgs = [Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 15, 30))]

        num_imgs = len(pil_imgs)
        heading = section.heading
        style_base = i * 2  # each section uses 2 motion styles across its images

        if num_imgs == 1:
            # Single image — full section
            img_ref = pil_imgs[0]

            def make_frame(t, _img=img_ref, _dur=audio_duration, _si=style_base, _h=heading, _po=presenter_overlay):
                frame = _make_motion_frame(_img, t, _dur, _si)
                frame = _add_text_overlay(frame, _h, t, _dur)
                if _po is not None:
                    frame = _add_presenter_overlay(frame, _po)
                return frame

            section_clip = VideoClip(make_frame, duration=audio_duration)
        else:
            # Multiple images: split duration evenly, crossfade between sub-clips
            sub_dur = audio_duration / num_imgs
            sub_clips = []
            for j, pil_img in enumerate(pil_imgs):
                img_ref = pil_img
                si = style_base + j

                def make_sub_frame(t, _img=img_ref, _dur=sub_dur, _si=si, _h=heading, _po=presenter_overlay):
                    frame = _make_motion_frame(_img, t, _dur, _si)
                    frame = _add_text_overlay(frame, _h, t, _dur)
                    if _po is not None:
                        frame = _add_presenter_overlay(frame, _po)
                    return frame

                sc = VideoClip(make_sub_frame, duration=sub_dur)
                if j > 0:
                    sc = sc.crossfadein(CROSSFADE)
                if j < num_imgs - 1:
                    sc = sc.crossfadeout(CROSSFADE)
                sub_clips.append(sc)

            section_clip = concatenate_videoclips(sub_clips, method="compose", padding=-CROSSFADE)

        if audio_clip:
            section_clip = section_clip.set_audio(audio_clip)

        section_clip = section_clip.crossfadein(CROSSFADE).crossfadeout(CROSSFADE)
        clips.append(section_clip)

    if progress_callback:
        progress_callback(85, "Creating end card...")

    end_clip = ImageClip(_create_end_card(script.call_to_action), duration=end_duration)
    end_clip = end_clip.crossfadein(CROSSFADE)
    clips.append(end_clip)

    if progress_callback:
        progress_callback(90, "Rendering final video...")

    final = concatenate_videoclips(clips, method="compose", padding=-CROSSFADE)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    final.write_videofile(
        output_path,
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=output_path.replace(".mp4", "_temp_audio.m4a"),
        remove_temp=True,
        verbose=False,
        logger=None,
    )

    if progress_callback:
        progress_callback(100, "Done!")

    return output_path
