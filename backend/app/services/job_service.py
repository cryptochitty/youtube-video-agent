import time
from typing import Dict, Optional
from app.models.job import Job, JobStatus, JobStep


_jobs: Dict[str, Job] = {}


def create_job(job: Job) -> Job:
    _jobs[job.id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def list_jobs() -> list[Job]:
    return sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)


def update_job_status(job_id: str, status: JobStatus, error: str = None):
    job = _jobs.get(job_id)
    if job:
        job.status = status
        job.updated_at = time.time()
        if error:
            job.error = error


def update_step(job_id: str, step_index: int, status: str, message: str = None, progress: int = None):
    job = _jobs.get(job_id)
    if job and 0 <= step_index < len(job.steps):
        step = job.steps[step_index]
        step.status = status
        if message:
            step.message = message
        if progress is not None:
            step.progress = progress
        # Recalculate overall progress
        total = len(job.steps) * 100
        done = sum(
            100 if s.status == "done" else (s.progress if s.status == "running" else 0)
            for s in job.steps
        )
        job.overall_progress = int(done / total * 100) if total else 0
        job.updated_at = time.time()


def set_job_script(job_id: str, script):
    job = _jobs.get(job_id)
    if job:
        job.script = script
        job.updated_at = time.time()


def set_job_video(job_id: str, path: str):
    job = _jobs.get(job_id)
    if job:
        job.video_path = path
        job.updated_at = time.time()
