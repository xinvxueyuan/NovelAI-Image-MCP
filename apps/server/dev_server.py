"""Entry point for ``mcp dev`` — imports the package's ``mcp`` server object.

``mcp dev`` uses ``importlib.util.spec_from_file_location`` to load the
file spec, which does not support relative imports. This top-level shim
imports the installed ``novelai_image_mcp`` package and re-exports its
``mcp`` server so the Inspector can launch it:

    uv run mcp dev dev_server.py:mcp --with-editable .
"""

from novelai_image_mcp.server import mcp

__all__ = ["mcp"]
