from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import uuid
import time


class VideoStyle(str, Enum):
    educational = "educational"
    entertainment = "entertainment"
    motivational = "motivational"
    news = "news"
    tutorial = "tutorial"
    documentary = "documentary"


class VideoDuration(str, Enum):
    short = "60"       # ~1 min
    medium = "180"     # ~3 min
    long = "300"       # ~5 min


class JobStatus(str, Enum):
    queued = "queued"
    generating_script = "generating_script"
    generating_audio = "generating_audio"
    fetching_images = "fetching_images"
    composing_video = "composing_video"
    completed = "completed"
    failed = "failed"


class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="Video topic or title idea")
    style: VideoStyle = VideoStyle.educational
    duration: VideoDuration = VideoDuration.medium
    language: str = Field(default="en", description="Language code e.g. en, es, fr, de")
    voice: Optional[str] = Field(default=None, description="Override TTS voice")
    extra_instructions: Optional[str] = Field(default=None, max_length=500)
    context_file_id: Optional[str] = Field(default=None, description="Uploaded PPTX or video file ID")
    voice_sample_id: Optional[str] = Field(default=None, description="Uploaded voice sample file ID")
    presenter_photo_id: Optional[str] = Field(default=None, description="Uploaded presenter photo file ID")


class ScriptSection(BaseModel):
    id: int
    heading: str
    narration: str
    visual_description: str
    search_query: str
    duration_seconds: int


class VideoScript(BaseModel):
    title: str
    description: str
    tags: List[str]
    hook: str
    sections: List[ScriptSection]
    call_to_action: str
    total_duration_seconds: int


class JobStep(BaseModel):
    name: str
    status: str = "pending"  # pending | running | done | error
    message: Optional[str] = None
    progress: int = 0  # 0-100


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.queued
    request: VideoRequest
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    steps: List[JobStep] = Field(default_factory=lambda: [
        JobStep(name="Script Generation"),
        JobStep(name="Audio Narration"),
        JobStep(name="Image Fetching"),
        JobStep(name="Video Composition"),
    ])
    script: Optional[VideoScript] = None
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    video_only_path: Optional[str] = None
    error: Optional[str] = None
    overall_progress: int = 0
