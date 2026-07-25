"""``python -m novelai_image_mcp`` entry — delegates to the typer CLI."""

from __future__ import annotations

from .cli import app

if __name__ == "__main__":
    app()
