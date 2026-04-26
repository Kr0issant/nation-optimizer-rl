# --- STAGE 1: Build the React Visualizer ---
FROM node:20-slim AS frontend-builder
WORKDIR /build
COPY visualizer/package*.json ./
RUN npm install
COPY visualizer/ ./
RUN npm run build

# --- STAGE 2: Python Runtime ---
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000

WORKDIR /app

# Install deps from pyproject only. (Do not require uv.lock in the build context —
# some hosts e.g. HF Spaces can omit it; lock is generated during `uv lock`.)
COPY pyproject.toml README.md ./
RUN uv lock && uv sync --frozen --no-dev

# Copy the game engine and server code
COPY agents ./agents
COPY core ./core
COPY evaluation ./evaluation
COPY schemas ./schemas
COPY server ./server
COPY telemetry ./telemetry
COPY training ./training
COPY client.py openenv.yaml ./

# Copy the compiled React assets from Stage 1
COPY --from=frontend-builder /build/dist ./visualizer/dist

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
