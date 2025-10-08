from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for your website or all origins for testing
origins = [
    "*",  # For testing; replace with ["https://yourwebsite.com"] in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # who can access
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, etc.
    allow_headers=["*"],  # headers your site can send
)


@app.get("/status")
async def status():
    return {"status": "ok", "message": "Hello from localhost!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=12345)
