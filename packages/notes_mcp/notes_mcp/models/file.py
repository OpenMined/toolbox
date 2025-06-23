from pydantic import BaseModel


# TODO: this is defined twice now, fix
class FileToSync(BaseModel):
    filename: str
    chunk_id: int
    encoded_bts: str
    timestamp: str
    device: str
    user_email: str


class FilesToSyncResponse(BaseModel):
    file: FileToSync | None = None
