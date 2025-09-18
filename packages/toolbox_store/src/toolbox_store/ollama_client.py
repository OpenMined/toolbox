import json
import sys

import httpx
from packaging import version


class OllamaEmbeddingClient:
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        min_ollama_version: str | None = "0.11.10",
    ):
        self.ollama_url = ollama_url
        self.conn = httpx.Client(base_url=self.ollama_url)

        if min_ollama_version:
            self._check_min_version(min_ollama_version)

    def _check_min_version(self, min_version: str) -> bool:
        """Check if the installed Ollama version meets the minimum requirement."""
        version_info = self.version()
        version_str = version_info.get("version")
        if version_str is None:
            raise RuntimeError("Could not determine Ollama version")
        if version.parse(version_str) < version.parse(min_version):
            raise RuntimeError(
                f"Ollama version {min_version} or higher is required, found {version_str}. Please update Ollama."
            )
        return True

    def version(self) -> dict[str, any]:
        """Get the Ollama version."""
        response = self.conn.get("/api/version")
        response.raise_for_status()
        return response.json()

    def model_exists(self, model: str) -> bool:
        try:
            model_info = self.show_model(model)
            if "error" in model_info:
                return False
            return True
        except Exception:
            return False

    def show_model(self, model: str) -> dict[str, any]:
        """Get information about a specific model."""
        response = self.conn.post("/api/show", json={"model": model})
        response.raise_for_status()
        return response.json()

    def pull(self, model: str, show_updates: bool = False) -> dict[str, any]:
        """Pull a model and wait for completion."""
        last_update = None
        for update in self.pull_streaming(model):
            status = update.get("status", "error")

            if show_updates:
                last_update = self._print_pull_status(update, last_update)

            if status in ("success", "error"):
                return update
        raise RuntimeError("Unexpected end of pull stream")

    def _print_pull_status(
        self, update: dict[str, any], last_update: str | None
    ) -> str:
        """Print pull status updates and return the current update string."""
        status = update.get("status", None)
        completed = update.get("completed")
        total = update.get("total")
        completed_str = (
            "" if completed is None or total is None else f"({completed}/{total})"
        )
        new_update = f"Ollama pull status: {status} {completed_str}"
        if new_update != last_update:
            last_len = len(last_update) if last_update else 0
            padded_update = new_update.ljust(max(len(new_update), last_len))
            _end = "\n" if status in ("success", "error") else "\r"
            print(padded_update, end=_end, flush=True)
        return new_update

    def pull_streaming(self, model: str):
        """Pull a model from the Ollama library with streaming updates."""
        data = {"model": model, "stream": True}

        with self.conn.stream("POST", "/api/pull", json=data, timeout=60.0) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    def embed(self, model: str, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of documents.

        Args:
            model: The model to use for embeddings (e.g. "embeddinggemma:300m")
            documents: List of text documents to embed

        Returns:
            List of embedding vectors (one per document)
        """
        data = {"model": model, "input": documents}

        response = self.conn.post("/api/embed", json=data, timeout=60.0)
        response.raise_for_status()
        result = response.json()

        # The API returns embeddings as a list of lists
        return result.get("embeddings", [])

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    client = OllamaEmbeddingClient()
    version_info = client.version()
    print(f"Ollama version: {version_info.get('version', 'unknown')}")

    # Test embedding
    test_documents = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language",
    ]

    model_name = "embeddinggemma:300m"

    model_exists = client.model_exists(model_name)
    if model_exists:
        print(f"Model '{model_name}' is available locally.")
    else:
        print(f"\nPulling model '{model_name}'...")
        res = client.pull(model_name, show_updates=True)
        if res.get("status") == "success":
            print("Model pulled successfully.")
        else:
            print(f"Failed to pull model: {res}")
            sys.exit(1)

    print("\nGenerating embeddings for test documents...")
    try:
        embeddings = client.embed(model_name, test_documents)
        print(f"Generated {len(embeddings)} embeddings")
        for i, emb in enumerate(embeddings):
            print(f"Document {i + 1}: embedding with {len(emb)} dimensions")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
