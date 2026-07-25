# License

NovelAI Image MCP is licensed under the **MIT License** — see
[`LICENSE`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/LICENSE)
for the full text.

## Per-file SPDX annotations

In addition to the canonical `LICENSE` file, every source file carries an
SPDX `copyright` / `license` header declared via
[`REUSE.toml`](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/REUSE.toml).
The license per file type is:

| File type | License |
|---|---|
| Software code (`*.py`, `conf.py`) | MIT |
| Documentation (`*.md`, `*.mdx`) | MIT |
| Visual elements (`*.png`, `*.svg`, `*.jpg`, …) | CC0-1.0 |
| Infrastructure / config (`*.toml`, `*.yml`, `*.json`, `Dockerfile`, …) | CC0-1.0 |
| Build artifacts (`*.pyc`, `node_modules/`, caches) | CC0-1.0 |

CC0-1.0 (public domain dedication) is used for non-creative content
(configs, infrastructure, generated artifacts) so they impose no
attribution requirements on downstream users.

## Verifying compliance

The repository is [REUSE 3.0](https://reuse.software/)-compliant. Run:

```bash
uv run reuse lint
```

The CI workflow runs the same check on every PR.

## Third-party licenses

The project depends on:

| Dependency | License |
|---|---|
| [mcp](https://pypi.org/project/mcp/) | MIT |
| [httpx](https://www.python-httpx.org/) | BSD-3-Clause |
| [pydantic](https://docs.pydantic.dev/) | MIT |
| [pydantic-settings](https://docs.pydantic.dev/latest/usage/settings/) | MIT |
| [typer](https://typer.tiangolo.com/) | MIT |
| [argon2-cffi](https://argon2-cffi.readthedocs.io/) | MIT |
| [msgpack](https://msgpack-python.readthedocs.io/) | Apache-2.0 |
| [Sphinx](https://www.sphinx-doc.org/) | BSD-2-Clause |
| [Furo](https://pradyunsg.me/furo/) | MIT |
| [MyST Parser](https://myst-parser.readthedocs.io/) | MIT |

Run `uv tree` to see the full dependency tree, including transitive
dependencies.

## See also

- [Full license text](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/LICENSE)
- [REUSE.toml](https://github.com/novelai-image-mcp/NovelAI-Image-MCP/blob/main/REUSE.toml)
- [FSFE REUSE specification](https://reuse.software/spec/)
