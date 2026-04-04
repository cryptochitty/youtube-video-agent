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
from app.services.video_composer import compose_video

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
        # Step 0: Generate Script
        job_service.update_job_status(job_id, JobStatus.generating_script)
        job_service.update_step(job_id, 0, "running", "Generating script with LLM...", 10)

        script = await generate_script(job.request)
        job_service.set_job_script(job_id, script)
        job_service.update_step(job_id, 0, "done", f"Script ready: {len(script.sections)} sections", 100)

        # Step 1: Generate Audio
        job_service.update_job_status(job_id, JobStatus.generating_audio)
        job_service.update_step(job_id, 1, "running", "Synthesizing narration...", 10)

        audio_paths = await synthesize_sections(
            script.sections,
            temp_job_dir,
            job.request.language,
            job.request.voice
        )
        job_service.update_step(job_id, 1, "done", f"Generated {len(audio_paths)} audio files", 100)

        # Step 2: Fetch Images
        job_service.update_job_status(job_id, JobStatus.fetching_images)
        job_service.update_step(job_id, 2, "running", "Fetching images...", 10)

        image_paths = await fetch_section_images(script.sections, temp_job_dir)
        job_service.update_step(job_id, 2, "done", f"Fetched {len(image_paths)} images", 100)

        # Step 3: Compose Video
        job_service.update_job_status(job_id, JobStatus.composing_video)
        job_service.update_step(job_id, 3, "running", "Composing video...", 5)

        output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

        def on_progress(pct: int, msg: str):
            job_service.update_step(job_id, 3, "running", msg, pct)

        await compose_video(script, audio_paths, image_paths, output_path, on_progress)

        job_service.set_job_video(job_id, output_path)
        job_service.update_step(job_id, 3, "done", "Video ready!", 100)
        job_service.update_job_status(job_id, JobStatus.completed)

    except Exception as e:
        error_msg = str(e)
        job_service.update_job_status(job_id, JobStatus.failed, error_msg)
        # Mark current running step as error
        job = job_service.get_job(job_id)
        if job:
            for i, step in enumerate(job.steps):
                if step.status == "running":
                    job_service.update_step(job_id, i, "error", f"Error: {error_msg}")
                    break

    finally:
        # Clean up temp files
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
    jobs = job_service.list_jobs()
    return [_job_summary(j) for j in jobs]


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
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.completed:
        raise HTTPException(status_code=400, detail=f"Video not ready. Status: {job.status}")
    if not job.video_path or not os.path.exists(job.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    filename = f"{job.script.title[:50].replace(' ', '_')}.mp4" if job.script else f"{job_id}.mp4"
    return FileResponse(
        job.video_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/voices")
async def get_voices():
    voices = await list_voices()
    return voices


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.video_path and os.path.exists(job.video_path):
        os.remove(job.video_path)
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
    }
