from fastapi import FastAPI
import uvicorn

from whisper.fastapi_server import router


if __name__ == "__main__":
    app = FastAPI()
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8006)
