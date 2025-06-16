import sqlite3
from anthropic import Anthropic



def get_all_meeting_notes(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.cursor()
    # Query the audio_transcriptions table
    cursor.execute("SELECT * FROM audio_transcriptions")
    rows = [dict(x) for x in cursor.fetchall()]
    fragments = []

    for row in rows:
        speaker_id = row["speaker_id"]
        transcription = row["transcription"]
        
        fragment = f"Speaker {speaker_id}:   {transcription}"
        fragments.append(fragment)

    full_transcription = "\n".join(fragments)
    return [full_transcription]

def get_todos(client: Anthropic, transcription: str) -> str:
    prompt = f"""Please analyze this transcription and convert it into a list of actionable todo items. Only respond with the todo items, no other text.
Format each todo item as a bullet point starting with '- '.

Transcription:
{transcription}

Todo items:"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    return response.content[0].text

