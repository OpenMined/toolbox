from pydantic import BaseModel

from notes_mcp.models.audio import AudioChunk


class Meeting(BaseModel):
    filename: str
    chunks_ids: list[int]
    
    chunks: list[AudioChunk] | None = None
    
    def show_text(self):
        return "\n".join([chunk.transcription for chunk in self.chunks])
    