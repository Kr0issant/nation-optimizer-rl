"""Convenience launcher for the visualizer SSE server.

Reads ``HF_TOKEN`` / ``HF_MODEL_ID`` from ``.env`` if present, then starts
:mod:`server.visualizer_server` with uvicorn on ``localhost:8001``.

Usage::

    python -m scripts.run_visualizer_server
    python -m scripts.run_visualizer_server --port 8001 --host 0.0.0.0
"""

from __future__ import annotations

import argparse
import logging

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload on source changes (development only).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper())

    import uvicorn

    uvicorn.run(
        "server.visualizer_server:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
