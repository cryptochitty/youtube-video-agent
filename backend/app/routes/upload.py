from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.upload_service import save_upload

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_CONTEXT = {
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "video/mp4", "video/quicktime", "video/x-msvideo", "video/webm",
}
ALLOWED_AUDIO = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp3", "audio/ogg"}
ALLOWED_IMAGE = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

CONTEXT_EXTS = {".pptx", ".mp4", ".mov", ".avi", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _check_ext(filename: str, allowed: set) -> bool:
    from pathlib import Path
    return Path(filename).suffix.lower() in allowed


@router.post("/context")
async def upload_context(file: UploadFile = File(...)):
    if not _check_ext(file.filename, CONTEXT_EXTS):
        raise HTTPException(400, "Unsupported file type. Upload a .pptx or video file.")
    result = await save_upload(file)
    return result


@router.post("/voice")
async def upload_voice(file: UploadFile = File(...)):
    if not _check_ext(file.filename, AUDIO_EXTS):
        raise HTTPException(400, "Unsupported file type. Upload an mp3 or wav file.")
    result = await save_upload(file)
    return result


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...)):
    if not _check_ext(file.filename, IMAGE_EXTS):
        raise HTTPException(400, "Unsupported file type. Upload a jpg or png file.")
    result = await save_upload(file)
    return result
