"""Shared test constants and helpers (importable from any test module).

`tests/conftest.py` inserts this directory into `sys.path` so test files
can do `from _helpers import PNG_BYTES` without making `tests` a package
(preserving pytest's importlib-mode rootdir semantics).
"""

from __future__ import annotations

import base64

# Minimal 1×1 PNG (transparent black). Used everywhere a small valid PNG is
# needed; the tools under test never inspect its contents.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)

__all__ = ["PNG_BYTES"]
