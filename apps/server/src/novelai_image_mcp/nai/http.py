"""HTTP client factory with Chrome TLS + header fingerprint impersonation.

NovelAI's API endpoints (``api.novelai.net`` and ``image.novelai.net``) sit
behind Cloudflare's bot-management WAF, which fingerprints clients at two
layers:

1. **TLS fingerprint (JA3/JA4):** Cloudflare inspects the TLS ``ClientHello``
   (cipher order, extensions, ALPN) before any HTTP header is read. Plain
   ``httpx`` uses OpenSSL, whose fingerprint differs from Chrome's BoringSSL
   and is flagged as a non-browser client — the connection is reset at the
   TLS layer, surfacing as ``NovelAITransportError``.
2. **HTTP headers:** Cloudflare and NovelAI's own backend check for a real
   browser ``User-Agent`` plus the Chromium Client Hints (``Sec-Ch-Ua*``) and
   Fetch Metadata (``Sec-Fetch-*``) header families. Missing any of these
   triggers a challenge or silent block.

This module addresses both layers:

* ``BROWSER_HEADERS`` — the full Chrome 150 header block (User-Agent, Client
  Hints, Fetch Metadata, Accept-Language, Priority).
* ``create_http_client()`` — returns an ``httpx.AsyncClient`` backed by
  ``httpx_curl_cffi.AsyncCurlTransport`` (which wraps ``curl_cffi`` /
  ``curl-impersonate``) so the TLS handshake reproduces Chrome's BoringSSL
  fingerprint. Falls back to plain ``httpx`` with browser headers if
  ``httpx-curl-cffi`` is not installed, logging a warning.
"""

from __future__ import annotations

import logging

import httpx

_logger = logging.getLogger(__name__)

# Chrome 150 stable on Windows (released 2026-07-23). The minor version is
# frozen to ``0.0.0`` per Chrome's User-Agent Reduction policy — the actual
# patch version (150.0.7871.186) is never sent in the UA string.
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)

# Chrome 150 Client Hints. ``Sec-Fetch-Site`` is ``same-site`` (not
# ``same-origin``) because ``image.novelai.net`` / ``api.novelai.net`` are
# sibling origins under ``novelai.net``.
CHROME_SEC_CH_UA = '"Chromium";v="150", "Google Chrome";v="150", "Not.A/Brand";v="99"'

# Full Chrome 150 browser fingerprint headers. These are set as default
# headers on the ``httpx.AsyncClient`` so every request — including streaming
# and any future code path — carries them automatically. Per-request headers
# (Authorization, Content-Type, x-correlation-id, x-initiated-at) override or
# extend these without conflict.
BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": CHROME_USER_AGENT,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": "https://novelai.net",
    # Trailing slash matters — the real browser always sends the path-less
    # origin with a slash, and Cloudflare's strict-mode rules check for it.
    "Referer": "https://novelai.net/",
    "Priority": "u=1, i",
    "Sec-Ch-Ua": CHROME_SEC_CH_UA,
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}


def _try_curl_transport() -> httpx.AsyncBaseTransport | None:
    """Return an ``AsyncCurlTransport`` if ``httpx-curl-cffi`` is installed.

    ``impersonate="chrome"`` selects the latest available Chrome TLS profile
    shipped by ``curl_cffi`` (cipher order, TLS extensions, ALPN, HTTP/2
    SETTINGS frame). ``default_headers=True`` lets curl-impersonate inject
    the matching HTTP/2 pseudo-header order so the wire-level fingerprint
    matches Chrome exactly.

    Returns ``None`` (and logs a warning) if the optional dependency is not
    installed — callers fall back to plain ``httpx`` with ``BROWSER_HEADERS``,
    which works against NovelAI today but is fragile if Cloudflare tightens
    JA3/JA4 enforcement.
    """
    try:
        from httpx_curl_cffi import AsyncCurlTransport
    except ImportError:
        _logger.warning(
            "httpx-curl-cffi is not installed; falling back to plain httpx "
            "without TLS fingerprint impersonation. NovelAI's Cloudflare WAF "
            "may reject requests at the TLS layer. Install with: "
            "pip install httpx-curl-cffi"
        )
        return None
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


def create_http_client(timeout: float = 120.0) -> httpx.AsyncClient:
    """Construct an ``httpx.AsyncClient`` with Chrome TLS + header fingerprint.

    Uses ``httpx_curl_cffi.AsyncCurlTransport`` (wrapping ``curl_cffi``) to
    reproduce Chrome's BoringSSL TLS fingerprint so Cloudflare's JA3/JA4
    bot detection treats the connection as browser-originated. Browser
    fingerprint headers (User-Agent, Sec-Ch-Ua*, Sec-Fetch-*, ...) are set
    as client defaults so every request carries them automatically.

    Callers that already own an ``httpx.AsyncClient`` (e.g. tests using
    ``respx``) should pass it via ``NovelAIClient(http_client=...)`` to
    bypass this factory.
    """
    transport = _try_curl_transport()
    return httpx.AsyncClient(
        timeout=timeout,
        transport=transport,
        headers=BROWSER_HEADERS,
    )


__all__ = [
    "BROWSER_HEADERS",
    "CHROME_SEC_CH_UA",
    "CHROME_USER_AGENT",
    "create_http_client",
]
