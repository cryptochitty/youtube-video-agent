import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes.video import router

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.getenv("TEMP_DIR", "./temp"), exist_ok=True)

app = FastAPI(
    title="YouTube Video Generator",
    description="AI-powered YouTube video generation using free local models",
    version="1.0.0"
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve generated videos statically for preview
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")


@app.get("/health")
async def health():
    llm = os.getenv("LLM_PROVIDER", "ollama")
    return {
        "status": "ok",
        "llm_provider": llm,
        "tts_voice": os.getenv("TTS_VOICE", "en-US-AriaNeural"),
        "image_source": os.getenv("IMAGE_SOURCE", "duckduckgo"),
    }
