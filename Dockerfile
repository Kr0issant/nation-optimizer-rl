FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY agents ./agents
COPY core ./core
COPY evaluation ./evaluation
COPY schemas ./schemas
COPY server ./server
COPY telemetry ./telemetry
COPY training ./training
COPY client.py openenv.yaml ./

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
