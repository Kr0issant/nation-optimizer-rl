"""Root-level app.py wrapper for Hugging Face Spaces Docker runtime.

The Spaces Docker SDK expects app_file to point to a module at the repo root.
This file re-exports the FastAPI app from server.app so uvicorn can find it.
"""

from server.app import app

__all__ = ["app"]
