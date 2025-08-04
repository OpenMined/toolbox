import os

import requests

OLLAMA_PORT = os.getenv("OLLAMA_PORT", 11434)
OLLAMA_URL = f"http://localhost:{OLLAMA_PORT}"


def get_embedding(query: str) -> list[float]:
    """get the embedding for a query using Ollama API v1.5"""
    import subprocess

    try:
        subprocess.run(
            ["ollama", "pull", "nomic-embed-text:v1.5"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    payload = {"model": "nomic-embed-text:v1.5", "prompt": query}
    response = requests.post(f"{OLLAMA_URL}/api/embeddings", json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    embedding = data.get("embedding")
    if embedding is None or not isinstance(embedding, list):
        raise ValueError(f"No embedding returned from Ollama: {data}")
    return embedding


def ollama_available() -> bool:
    """check if ollama is available"""
    try:
        response = requests.get(OLLAMA_URL, timeout=10)
        response.raise_for_status()
        return True
    except Exception:
        return False
