import io
import uuid
from pathlib import Path

import torch
import torchaudio
from moviepy.audio.io.AudioFileClip import AudioFileClip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

MODEL_ID = "openai/whisper-large-v3"


def get_mp3_bytes(mp4_bytes: bytes):
    mp4_file = f"test_audio-{uuid.uuid4()}.mp4"
    with open(mp4_file, "wb") as f:
        f.write(mp4_bytes)
    audio = AudioFileClip(mp4_file)
    Path(mp4_file).unlink()
    out_file = f"test_audio-{uuid.uuid4()}.mp3"
    audio.write_audiofile(out_file)
    with open(out_file, "rb") as f:
        audio_bts = f.read()
    Path(out_file).unlink()
    return audio_bts


# Function to process bytes
def bts_to_np(audio_bytes: bytes):
    # Convert bytes to waveform using torchaudio
    with io.BytesIO(audio_bytes) as audio_file:
        waveform, sample_rate = torchaudio.load(audio_file)

    # Whisper expects 16kHz audio
    if sample_rate != 16000:
        waveform = torchaudio.functional.resample(
            waveform, orig_freq=sample_rate, new_freq=16000
        )

    # Convert to mono if stereo
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)

    # Convert waveform to numpy array
    waveform_np = waveform.squeeze().numpy()
    return waveform_np


def get_pipeline():
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        MODEL_ID, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(MODEL_ID)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
        return_timestamps=True,
    )
    return pipe
