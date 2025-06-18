from pydantic import BaseModel


class FileToSync(BaseModel):
    filename: str
    id: int
    encoded_bts: str
    timestamp: str
    device: str
    user_email: str


class FilesToSyncResponse(BaseModel):
    file: FileToSync | None = None
