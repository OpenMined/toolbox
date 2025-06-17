from datetime import datetime
import os
import random
from notes_mcp import db
import requests
DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]

# file_path = HOME / ".screenpipe" / "data" / "MacBook Pro Microphone (input)_2025-06-03_14-30-45.mp4"
# FILE_PATH = 'path/to/your/audio.wav'  # Local WAV file (16kHz sample rate)


def add_transcription_to_db(conn, bts, audio_chunk_id: int, device: str, timestamp: datetime):
    transcript = transcribe(bts)
    text_length = len(transcript)
    # TODO: FIX
    # start_time and end_time are not set
    # offset_index is not set
    # speaker_id is not set
    # timestamp is not set
    transcription_id = random.randint(0, 1000000)   
    db.insert_transcription(conn,
                            transcription_id=transcription_id,
                            audio_chunk_id=audio_chunk_id,
                            offset_index=0,
                            timestamp=timestamp,
                            transcription=transcript,
                            device=device,
                            is_input_device=True,
                            speaker_id=0,
                            transcription_engine="deepgram",
                            start_time=0,
                            end_time=0,
                            text_length=text_length)
    

def transcribe(bytes_data: bytes):    
    response = requests.post(
        'https://api.deepgram.com/v1/listen',
        headers={
            'Authorization': f'Token {DEEPGRAM_API_KEY}',
            'Content-Type': 'audio/wav'
        },
        params={
            'model': 'nova-2',
            'smart_format': 'true',
            'sample_rate': '16000'
        },
        data=bytes_data
    )
    res = response.json()
    transcript = res["results"]["channels"][0]["alternatives"][0]["transcript"]
    return transcript