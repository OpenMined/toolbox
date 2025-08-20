import base64

from pydantic import BaseModel


class TranscribeRequest(BaseModel):
    token: str = "dev_key"
    audio_base64_str: str

    @classmethod
    def from_bytes(cls, audio_bytes: bytes, token=None) -> "TranscribeRequest":
        return cls(
            audio_base64_str=base64.b64encode(audio_bytes).decode("utf-8"), token=token
        )

    @property
    def audio_bytes(self) -> bytes:
        return base64.b64decode(self.audio_base64_str)
