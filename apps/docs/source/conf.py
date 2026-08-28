"""Sphinx configuration for the NovelAI Image MCP documentation site.

The site is rendered with the Furo theme and parses MyST Markdown. API
reference pages use ``sphinx.ext.autodoc`` to introspect the
``novelai_image_mcp`` package from the shared uv workspace virtualenv.

Conventions:
    * MyST Markdown for all pages (``*.md``); reStructuredText is unused.
    * Napoleon renders Google-style docstrings (the project's pydocstyle
      convention) into readable API docs.
    * ``nitpicky = True`` keeps cross-references honest; unavoidable
      warnings from third-party stubs are listed in ``nitpick_ignore``.
    * Build with ``-W --keep-going`` in CI so warnings fail the build but
      every warning is reported in a single pass.

Run::
    uv run --package novelai-image-mcp-docs sphinx-build -b html source _build/html
"""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import Any

# ─── Project metadata ─────────────────────────────────────────────────────────
# Resolve the version from the workspace-installed ``novelai_image_mcp`` package
# so the docs site reports the same version as the shipped wheel.
try:
    release: str | None = importlib.metadata.version("novelai-image-mcp")
except importlib.metadata.PackageNotFoundError:  # pragma: no cover - dev-only fallback
    release = None

if release is None:
    # Fall back to the in-tree package __version__ when autodoc hasn't installed
    # the metadata (e.g. running sphinx-build directly against a source checkout
    # without `uv sync --package novelai-image-mcp-docs`).
    try:
        from novelai_image_mcp import __version__ as release  # type: ignore[no-redef]
    except Exception:  # noqa: BLE001 - last-resort fallback
        release = "0.0.0"

project = "NovelAI Image MCP"
author = "NovelAI Image MCP contributors"
copyright = "2026, NovelAI Image MCP contributors"  # noqa: A001 — Sphinx configures this name
version = ".".join((release or "0.0.0").split(".")[:2])

# ─── General Sphinx options ──────────────────────────────────────────────────
extensions = [
    # MyST Markdown parser — primary authoring format
    "myst_parser",
    # UX extensions
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
    "sphinxcontrib.mermaid",
    # API reference (introspects novelai_image_mcp)
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]
# Furo is the HTML theme — set via html_theme below, NOT in extensions (Furo
# raises a ConfigError if listed in extensions because it does not work with
# non-HTML builders).

# ─── sphinx-copybutton ───────────────────────────────────────────────────────
# Explicitly set every copybutton_* option. sphinx-copybutton 0.5.2 (the
# current PyPI release) renders its generated JS with empty slots for unset
# options, producing an INVALID script:
#
#     return formatCopyText(text, Undefined, , , , , Undefined, Undefined)
#            ^^^^ SyntaxError: Unexpected token ','
#
# The whole _static/copybutton.js then fails to parse on every page and the
# copy buttons never attach. Setting the options (even to their defaults)
# emits valid boolean literals.
copybutton_prompt_text = ""
copybutton_prompt_is_regexp = False
copybutton_only_copy_prompt_lines = False
copybutton_remove_prompts = False
copybutton_copy_empty_lines = True

# MyST Markdown — https://myst-parser.readthedocs.io/en/latest/configuration.html
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]
myst_url_schemes = {
    "http": None,
    "https": None,
    "mailto": None,
    "ftp": None,
    # Custom: ``novelai:path`` → https://novelai.net/<path>
    "novelai": "https://novelai.net/{{path}}",
}
myst_heading_anchors = 4
myst_substitutions = {
    "project": project,
    "version": str(release),
}
# Suppress the "unknown directive" warning for badges we render via sub-plugin.
myst_fence_as_directive = {"mermaid"}

# Templates + static assets
templates_path = ["_templates"]
html_static_path = ["_static"]
exclude_patterns: list[str] = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/.pytest_cache",
    # Per-language source trees (``zh/``, ``ja/``) are built independently
    # against this shared ``conf.py`` (each with its own source root). They
    # must be excluded from the English build so Sphinx doesn't pick up the
    # translated ``index.md`` files and warn that they're not in any toctree.
    # The patterns are relative to the active source directory, so they only
    # match when building from the English root (``apps/docs/source/``); under
    # ``apps/docs/source/zh/`` there is no nested ``zh/`` so the pattern is a
    # no-op there.
    "zh",
    "ja",
]

# Localization / warnings
#
# ``language`` is the default source language (English). It is overridable
# per-build via ``-D language=zh`` (or ``ja``) on the ``sphinx-build`` CLI;
# no Python change is required for that. Each language lives in its own
# source subdirectory (``zh/``, ``ja/``) and is built independently against
# this shared ``conf.py`` (see ``.github/workflows/docs.yml``).
#
# ``AVAILABLE_LANGUAGES`` is consumed by the language-switcher template
# (``_templates/sidebar/language-switcher.html``) via ``html_context``.
# Each tuple is ``(code, label, base_path)`` where ``base_path`` is the
# subdirectory the language deploys under (``""`` for English at the root).
AVAILABLE_LANGUAGES: list[tuple[str, str, str]] = [
    ("en", "English", ""),
    ("zh", "中文", "zh"),
    ("ja", "日本語", "ja"),
]
language = "en"
# ``current_language`` mirrors the active ``language`` so templates can
# read it without touching the Sphinx config value directly. Note: when
# Sphinx applies a ``-D language=...`` override, it does so AFTER conf.py
# is executed, so this module-level value (and everything derived from it
# — ``html_title``, ``html_context``) is stale for non-English builds. The
# ``_on_config_inited`` hook in ``setup()`` refreshes those values from
# the final ``config.language`` before building.
current_language = language


def _base_path_for(code: str) -> str:
    """Return the deploy subdirectory (``base_path``) for a language code.

    ``""`` for English (root), ``"zh"`` / ``"ja"`` for the translations.
    Used by ``_on_config_inited`` to populate ``current_base_path`` in
    ``html_context`` so the language-switcher template can compute relative
    cross-language URLs without ``pathto`` (which resolves against the
    current build's source tree, not the deployed URL structure).
    """
    for c, _, bp in AVAILABLE_LANGUAGES:
        if c == code:
            return bp
    return ""


# Localised label for the language-switcher sidebar block (the template reads
# ``switcher_label`` from ``html_context``; it used to be hardcoded English).
_SWITCHER_LABELS: dict[str, str] = {
    "en": "Language",
    "zh": "语言",
    "ja": "言語",
}


def _switcher_label_for(code: str) -> str:
    return _SWITCHER_LABELS.get(code, _SWITCHER_LABELS["en"])


def _translated_pages() -> set[str]:
    """Derive which page basenames exist in the English root AND every
    non-English language tree.

    Previously a hardcoded set; forgetting to update it silently degraded the
    language switcher (linking to a language's index instead of the newly
    translated page). ``conf.py`` always lives in ``apps/docs/source`` even
    when a per-language build points ``srcdir`` at ``apps/docs/source/<code>``,
    so ``Path(__file__).parent`` resolves the English root for every build.
    """
    root = Path(__file__).parent

    def page_names(d: Path) -> set[str]:
        return {p.stem for p in d.glob("*.md")} if d.is_dir() else set()

    translated = page_names(root)
    for code, _, base_path in AVAILABLE_LANGUAGES:
        if base_path:  # non-English languages
            translated &= page_names(root / base_path)
    return translated


# Page basenames that have translations in EVERY non-English language —
# derived from the filesystem at build time (see ``_translated_pages()``).
# The language switcher uses this set to decide whether to link to the same
# page in the target language or fall back to the target language's index
# page (per the spec: "falling back to the language's index page if the
# translated page does not exist"). English has all pages, so the fallback
# only applies when linking TO a non-English language from an English-only
# page (e.g., clicking "中文" on ``/tools/generate`` → ``/zh/``).
TRANSLATED_PAGES: set[str] = _translated_pages()
nitpicky = True
nitpick_ignore: list[tuple[str, str]] = [
    # pydantic internals surface cross-reference misses for typing generics.
    ("py:class", "pydantic._internal._model_construction.ModelMetaclass"),
    ("py:class", "pydantic._internal._fields.PydanticMetadata"),
    # httpx async client types are shadowed by their ABCs in the stubs.
    ("py:class", "httpx._client.AsyncClient"),
    # ``Any`` is imported as a name in payload.py / response.py for protocol
    # typing; Sphinx then resolves the bare ``Any`` cross-reference to
    # multiple targets (typing.Any vs the local imports). Ignore the bare
    # name so autodoc doesn't warn on every ``Any`` annotation.
    ("py:class", "Any"),
    # pydantic-settings ships its types through the pydantic inventory
    # (or doesn't expose them at all in intersphinx). These show up as
    # ``model_config`` keys on SettingsModel subclasses.
    ("py:class", "SettingsConfigDict"),
    ("py:class", "EnvPrefixTarget"),
    ("py:class", "DotenvType"),
    ("py:class", "CliSettingsSource"),
    ("py:class", "PathType"),
    ("py:class", "PydanticBaseSettingsSource"),
    # fastmcp (the server framework) is documented with Mintlify (no
    # objects.inv), so its public classes surfaced by autodoc are not in any
    # intersphinx inventory. Suppress the ones that appear on the API pages.
    ("py:class", "FastMCP"),
    ("py:class", "fastmcp.FastMCP"),
    ("py:class", "fastmcp.server.server.FastMCP"),
    # httpx is documented with MkDocs (no objects.inv); the public alias
    # ``httpx.AsyncClient`` resolves to ``httpx._client.AsyncClient`` in
    # the stubs but autodoc emits the public name. Suppress both forms.
    ("py:class", "httpx.AsyncClient"),
    ("py:class", "httpx.Client"),
    ("py:class", "httpx._client.AsyncClient"),
    ("py:class", "httpx._client.Client"),
    # fastmcp ``Context`` and ``Image`` helpers — intersphinx does not cover
    # the fastmcp package, so these bare names from tool signatures unroll.
    ("py:class", "Context"),
    ("py:class", "fastmcp.server.context.Context"),
    ("py:class", "Image"),
    ("py:class", "fastmcp.utilities.types.Image"),
    ("py:class", "Tool"),
    ("py:class", "mcp.shared.exceptions.McpError"),
]
nitpick_ignore_regex: list[tuple[str, str]] = []

# ─── autodoc ─────────────────────────────────────────────────────────────────
# Auto-generate entries for every public member; order source-by-source so the
# API reference mirrors the in-tree layout. Render typehints in the description
# (cleaner than inline annotations for heavily-typed MCP tool signatures).
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
    "imported-members": False,
    # Exclude common imported names that autodoc would otherwise pick up
    # as module attributes (creating duplicate object descriptions across
    # modules that import them). ``imported-members: False`` skips the
    # docstring lookup but the names still appear in the module namespace,
    # so we exclude them explicitly.
    "exclude-members": ",".join(
        [
            # typing helpers used as type annotations
            "Any",
            "cast",
            "Optional",
            "Union",
            "Callable",
            "Awaitable",
            "Coroutine",
            "TYPE_CHECKING",
            "annotations",
            # stdlib modules imported for side effects / use
            "json",
            "io",
            "struct",
            "zipfile",
            "base64",
            "pathlib",
            "dataclasses",
            "enum",
            "asyncio",
            # third-party libraries (documented in their own API pages)
            "msgpack",
            "httpx",
            "pydantic",
            "typer",
            "mcp",
        ]
    ),
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_member_order = "bysource"
autodoc_class_signature = "mixed"
autodoc_preserve_defaults = True

# Napoleon — render Google-style docstrings (matches ruff pydocstyle convention).
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_attr_annotations = True

# ─── intersphinx ──────────────────────────────────────────────────────────────
# Cross-reference Python and pydantic so type annotations in API docs link
# back to upstream documentation.
#
# Only libraries that publish a Sphinx ``objects.inv`` inventory are listed
# here. ``httpx`` (https://www.python-httpx.org/) and the MCP SDK
# (https://modelcontextprotocol.io/) are documented with MkDocs / Material
# for MkDocs and do not expose an ``objects.inv`` file — fetching their
# inventories 404s and fails the build under ``-W``. Types from those
# libraries are suppressed individually in ``nitpick_ignore`` above.
#
# Sphinx 8.x enforces unique target URIs across intersphinx entries —
# pydantic-settings ships its types through the pydantic inventory (same docs
# site), so we keep a single ``pydantic`` entry rather than aliasing.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# ─── HTML output (Furo theme) ─────────────────────────────────────────────────
html_theme = "furo"
# Per-language ``html_title`` — branched on the active ``language`` so each
# build's browser-tab title is localised (e.g. "NovelAI Image MCP 文档" for
# ``zh``). Falls back to the English title for any unrecognised language.
_HTML_TITLES: dict[str, str] = {
    "en": f"{project} v{release}",
    "zh": f"{project} 文档 v{release}",
    "ja": f"{project} ドキュメント v{release}",
}
html_title = _HTML_TITLES.get(language, _HTML_TITLES["en"])
html_last_updated_fmt = "%Y-%m-%d"
html_use_index = True
html_domain_indices = True
html_file_suffix = ".html"
html_link_suffix = ".html"

# Brand assets
html_logo = "_static/logo.svg"
html_favicon = "_static/favicon.svg"

# Custom CSS — overrides Furo's brand color to the project palette.
html_css_files = [
    "custom.css",
]

# ``html_context`` exposes the available languages and the active language to
# the language-switcher template (``_templates/sidebar/language-switcher.html``)
# so it can render the pill list and mark the current language active.
#
# ``current_base_path`` is the deploy subdirectory of the active language
# (``""`` for English, ``"zh"`` / ``"ja"`` for translations); the template
# uses it to compute relative cross-language URLs (e.g. from ``zh/`` to the
# English root: ``../index.html``). ``translated_pages`` lists the page names
# that have translations in every non-English language; the template falls
# back to the target language's ``index.html`` for any page not in this set
# (e.g. English-only ``tools/generate`` → ``zh/index.html``).
html_context = {
    "available_languages": AVAILABLE_LANGUAGES,
    "current_language": current_language,
    "current_base_path": _base_path_for(current_language),
    "translated_pages": TRANSLATED_PAGES,
    "switcher_label": _switcher_label_for(current_language),
}

# ``html_sidebars`` reproduces Furo's default sidebar section list (see
# ``furo/theme/furo/theme.conf``). The language switcher is placed between
# the search box and the scroll wrapper (``sidebar/scroll-start.html`` …
# ``sidebar/scroll-end.html``), i.e. in the sidebar's fixed header zone, so
# it stays visible without scrolling even when the navigation tree is long
# (previously it sat inside the scroll wrapper and was hidden under the
# menu). Overriding the list is the officially supported Furo customisation
# path — see https://pradyunsg.me/furo/customisation/sidebar/.
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/language-switcher.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ],
}

# Theme options — Furo
html_theme_options: dict[str, Any] = {
    "light_css_variables": {
        "color-brand-primary": "#7c3aed",  # violet-600
        "color-brand-content": "#6d28d9",  # violet-700
        "color-brand-secondary": "#db2777",  # pink-600
        "color-link": "#7c3aed",
        "color-link--hover": "#6d28d9",
        "color-sidebar-link": "#4b5563",  # gray-600
        "color-sidebar-link--hover": "#7c3aed",
    },
    "dark_css_variables": {
        "color-brand-primary": "#a78bfa",  # violet-400
        "color-brand-content": "#c4b5fd",  # violet-300
        "color-brand-secondary": "#f472b6",  # pink-400
        "color-link": "#a78bfa",
        "color-link--hover": "#c4b5fd",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/xinvxueyuan/NovelAI-Image-MCP",
    "source_branch": "main",
    "source_directory": "apps/docs/source/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/xinvxueyuan/NovelAI-Image-MCP",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 '
                "3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 "
                "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 "
                "1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
                "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 "
                "0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 "
                "0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 "
                '8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
            ),
            "class": "",
        },
    ],
}

# ─── linkcheck ─────────────────────────────────────────────────────────────────
# Some endpoints are flaky or reject HEAD requests; skip them.
linkcheck_ignore = [
    r"https://novelai\.net/.*",  # behind auth, may 403 HEAD
    r"https://image\.novelai\.net/.*",  # API endpoint, requires auth
    r"https://api\.novelai\.net/.*",
    r"https://github\.com/xinvxueyuan/NovelAI-Image-MCP/(pull|issues)/\d+",
    r"^mailto:",
]
linkcheck_timeout = 10
linkcheck_workers = 5
linkcheck_anchors = True
linkcheck_anchors_ignore = [
    r"^L\d+-L\d+$",  # GitHub line-range anchors
    r"^!?$",
]
linkcheck_retries = 2

# ─── Source-side hooks ─────────────────────────────────────────────────────────
# Skip building source documents that import optional dependencies that aren't
# present in the docs environment (none currently, but the hook is in place).


def _on_config_inited(app: Any, config: Any) -> None:
    """Refresh language-dependent config after ``-D`` overrides are applied.

    Sphinx applies ``-D language=zh`` (or ``ja``) AFTER ``conf.py`` is
    executed, so values derived from ``language`` at module load time —
    ``html_title`` and ``html_context`` (which carries ``current_language``,
    ``current_base_path``, ``translated_pages`` for the language-switcher
    template) — are stale for non-English builds. This hook recomputes them
    from the final ``config.language`` so each build gets its localised
    title and the switcher marks the correct language active.
    """
    lang = config.language
    config.html_title = _HTML_TITLES.get(lang, _HTML_TITLES["en"])
    # UPDATE (not replace) html_context: extensions such as sphinx-copybutton
    # inject their own keys here during ``config-inited`` (e.g.
    # ``copybutton_prompt_text``, rendered into the generated copybutton.js).
    # Assigning a fresh dict would wipe those keys and sphinx-copybutton's
    # template would render undefined values, producing INVALID JS
    # (``formatCopyText(text, Undefined, , , , , Undefined, Undefined)``).
    config.html_context.update(
        {
            "available_languages": AVAILABLE_LANGUAGES,
            "current_language": lang,
            "current_base_path": _base_path_for(lang),
            "translated_pages": TRANSLATED_PAGES,
            "switcher_label": _switcher_label_for(lang),
        }
    )


def setup(app: Any) -> dict[str, Any]:  # pragma: no cover - Sphinx hook
    """Register custom directives / additional assets if needed."""
    # _static directory must exist for Sphinx to copy custom.css; create it
    # lazily so first-time builds don't fail when the directory is empty.
    static_dir = Path(__file__).parent / "_static"
    static_dir.mkdir(exist_ok=True)
    app.connect("config-inited", _on_config_inited)
    return {
        "version": str(release),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
