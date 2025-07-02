import requests
from whisper.models import TranscribeRequest
import os

fpath = "/Users/koen/test_audio.mp4"
deployed_url = "4.151.234.109:8006"
with open(fpath, "rb") as f:
    audio_bytes = f.read()

token = os.getenv("WHISPER_SECRET_KEY", "dev_key")

request = TranscribeRequest.from_bytes(audio_bytes, token=token)

payload = request.model_dump()

response = requests.post(
    f"http://{deployed_url}/transcribe",
    json=payload,
)

print(response.json()["transcription"])
