import os

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException

from whisper.models import TranscribeRequest
from whisper.settings import settings
from whisper.whisper_model import bts_to_np, get_mp3_bytes, get_pipeline

router = APIRouter()
pipe = get_pipeline()


@router.post("/health")
def health_check():
    return {"status": "healthy", "service": "whisper-api"}


# Root endpoint
@router.post("/transcribe")
def transcribe(request: TranscribeRequest) -> dict:
    if request.token != settings.whisper_secret_key:
        raise HTTPException(status_code=401, detail="Invalid token")
    audio_bts = get_mp3_bytes(request.audio_bytes)
    waveform_np = bts_to_np(audio_bts)
    result = pipe(waveform_np)
    transcription = result["text"].strip()
    return {"status": "success", "transcription": transcription}


# Main entry point
if __name__ == "__main__":
    app = FastAPI()
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8006)
