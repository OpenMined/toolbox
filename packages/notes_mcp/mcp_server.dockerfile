FROM ghcr.io/astral-sh/uv:debian-slim

WORKDIR /app
COPY . /app

RUN uv python install 3.12
RUN uv venv
RUN uv pip install -e .

ENV REPO_PATH=/app


# Expose port
EXPOSE 8000

# Run the server
CMD ["uv", "run", "/app/agentic_syftbox/server.py"]
