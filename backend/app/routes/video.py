import os
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from app.models.job import Job, JobStatus, VideoRequest
from app.services import job_service
from app.services.script_generator import generate_script
from app.services.tts_service import synthesize_sections, list_voices
from app.services.media_service import fetch_section_images
from app.services.video_composer import compose_video, extract_audio_only, extract_video_only
from app.services.upload_service import get_upload_path, extract_pptx_text

router = APIRouter(prefix="/api", tags=["video"])

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")


async def run_pipeline(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        return

    temp_job_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(temp_job_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # ── Step 0: Generate Script ─────────────────────────────────────────
        job_service.update_job_status(job_id, JobStatus.generating_script)
        job_service.update_step(job_id, 0, "running", "Generating script with LLM...", 10)

        # Resolve uploaded context file (PPTX / video)
        context_text = ""
        if job.request.context_file_id:
            path = get_upload_path(job.request.context_file_id)
            if path and path.lower().endswith(".pptx"):
                context_text = extract_pptx_text(path)
            elif path:
                context_text = f"Content from file: {Path(path).name}"

        script = await generate_script(job.request, context=context_text)
        job_service.set_job_script(job_id, script)
        job_service.update_step(job_id, 0, "done", f"Script ready: {len(script.sections)} sections", 100)

        # ── Step 1: Generate Audio ──────────────────────────────────────────
        job_service.update_job_status(job_id, JobStatus.generating_audio)
        job_service.update_step(job_id, 1, "running", "Synthesizing narration...", 10)

        voice_sample_path = None
        if job.request.voice_sample_id:
            voice_sample_path = get_upload_path(job.request.voice_sample_id)

        audio_paths = await synthesize_sections(
            script.sections,
            temp_job_dir,
            job.request.language,
            job.request.voice,
            voice_sample_path=voice_sample_path,
        )
        job_service.update_step(job_id, 1, "done", f"Generated {len(audio_paths)} audio files", 100)

        # ── Step 2: Fetch Images ────────────────────────────────────────────
        job_service.update_job_status(job_id, JobStatus.fetching_images)
        job_service.update_step(job_id, 2, "running", "Fetching images...", 10)

        image_paths = await fetch_section_images(script.sections, temp_job_dir)
        total_imgs = sum(len(p) for p in image_paths)
        job_service.update_step(job_id, 2, "done", f"Fetched {total_imgs} images", 100)

        # ── Step 3: Compose Video ───────────────────────────────────────────
        job_service.update_job_status(job_id, JobStatus.composing_video)
        job_service.update_step(job_id, 3, "running", "Composing video...", 5)

        output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

        presenter_photo_path = None
        if job.request.presenter_photo_id:
            presenter_photo_path = get_upload_path(job.request.presenter_photo_id)

        def on_progress(pct: int, msg: str):
            job_service.update_step(job_id, 3, "running", msg, pct)

        await compose_video(
            script, audio_paths, image_paths, output_path,
            on_progress, presenter_photo_path=presenter_photo_path
        )

        job_service.set_job_video(job_id, output_path)

        # ── Post-processing: extract audio-only & video-only ────────────────
        try:
            audio_out = os.path.join(OUTPUT_DIR, f"{job_id}_audio.mp3")
            await extract_audio_only(output_path, audio_out)
            job_service.set_job_audio(job_id, audio_out)
        except Exception:
            pass

        try:
            video_only_out = os.path.join(OUTPUT_DIR, f"{job_id}_noaudio.mp4")
            await extract_video_only(output_path, video_only_out)
            job_service.set_job_video_only(job_id, video_only_out)
        except Exception:
            pass

        job_service.update_step(job_id, 3, "done", "Video ready!", 100)
        job_service.update_job_status(job_id, JobStatus.completed)

    except Exception as e:
        error_msg = str(e)
        job_service.update_job_status(job_id, JobStatus.failed, error_msg)
        job = job_service.get_job(job_id)
        if job:
            for i, step in enumerate(job.steps):
                if step.status == "running":
                    job_service.update_step(job_id, i, "error", f"Error: {error_msg}")
                    break

    finally:
        try:
            import shutil
            shutil.rmtree(temp_job_dir, ignore_errors=True)
        except Exception:
            pass


@router.post("/generate")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    job = Job(request=request)
    job_service.create_job(job)
    background_tasks.add_task(run_pipeline, job.id)
    return {"job_id": job.id, "status": job.status}


@router.get("/jobs")
async def get_jobs():
    return [_job_summary(j) for j in job_service.list_jobs()]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_detail(job)


@router.get("/jobs/{job_id}/download")
async def download_video(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.completed:
        raise HTTPException(400, f"Video not ready. Status: {job.status}")
    if not job.video_path or not os.path.exists(job.video_path):
        raise HTTPException(404, "Video file not found")
    filename = f"{job.script.title[:50].replace(' ', '_')}.mp4" if job.script else f"{job_id}.mp4"
    return FileResponse(job.video_path, media_type="video/mp4", filename=filename,
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/jobs/{job_id}/download/audio")
async def download_audio(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if not job.audio_path or not os.path.exists(job.audio_path):
        raise HTTPException(404, "Audio file not found")
    filename = f"{job.script.title[:50].replace(' ', '_')}_audio.mp3" if job.script else f"{job_id}_audio.mp3"
    return FileResponse(job.audio_path, media_type="audio/mpeg", filename=filename,
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/jobs/{job_id}/download/video-only")
async def download_video_only(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if not job.video_only_path or not os.path.exists(job.video_only_path):
        raise HTTPException(404, "Video-only file not found")
    filename = f"{job.script.title[:50].replace(' ', '_')}_noaudio.mp4" if job.script else f"{job_id}_noaudio.mp4"
    return FileResponse(job.video_only_path, media_type="video/mp4", filename=filename,
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/voices")
async def get_voices():
    return await list_voices()


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    for path in [job.video_path, job.audio_path, job.video_only_path]:
        if path and os.path.exists(path):
            os.remove(path)
    from app.services.job_service import _jobs
    _jobs.pop(job_id, None)
    return {"deleted": job_id}


def _job_summary(job: Job) -> dict:
    return {
        "id": job.id,
        "status": job.status,
        "topic": job.request.topic,
        "style": job.request.style,
        "duration": job.request.duration,
        "overall_progress": job.overall_progress,
        "created_at": job.created_at,
    }


def _job_detail(job: Job) -> dict:
    return {
        **_job_summary(job),
        "steps": [s.model_dump() for s in job.steps],
        "script": job.script.model_dump() if job.script else None,
        "error": job.error,
        "has_video": bool(job.video_path and os.path.exists(job.video_path)),
        "has_audio": bool(job.audio_path and os.path.exists(job.audio_path)),
        "has_video_only": bool(job.video_only_path and os.path.exists(job.video_only_path)),
    }
