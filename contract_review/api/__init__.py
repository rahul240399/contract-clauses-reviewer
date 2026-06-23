"""HTTP delivery adapter (FastAPI) over the same core the CLI uses."""

from .app import create_app

__all__ = ["create_app"]
