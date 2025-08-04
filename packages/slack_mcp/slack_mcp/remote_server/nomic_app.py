from contextlib import asynccontextmanager
import os
from uuid import UUID

import torch
import uvicorn
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
from transformers import AutoModel, AutoTokenizer

router = APIRouter()

tokenizer = AutoTokenizer.from_pretrained(
    "nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True
)
model = AutoModel.from_pretrained(
    "nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True
)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

PORT = os.getenv("NOMIC_PORT", 8020)
USE_MOCK_EMBEDDINGS = os.getenv("USE_MOCK_EMBEDDINGS", "False").lower() == "true"


@router.get("/health")
async def health():
    return {"status": "ok"}


class EmbeddingRequest(BaseModel):
    chunk_id: UUID
    prompt: str


@router.post("/embeddings")
async def embeddings(request: list[EmbeddingRequest]):
    if USE_MOCK_EMBEDDINGS:
        return [
            {"chunk_id": str(x.chunk_id), "embedding": [0.0] * 768} for x in request
        ]

    inputs = tokenizer(
        [x.prompt for x in request],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        # Use the mean pooling of the last hidden state as embedding
        last_hidden = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]
        mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
        sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
        sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
        embeddings = (sum_embeddings / sum_mask).squeeze().tolist()

    return [
        {"chunk_id": str(x.chunk_id), "embedding": embedding}
        for x, embedding in zip(request, embeddings)
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    print(f"Using device: {device}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8020)
