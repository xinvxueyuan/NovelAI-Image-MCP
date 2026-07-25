"""Tests for the Chrome TLS + header fingerprint factory in ``nai.http``.

The factory's contract is: return an ``httpx.AsyncClient`` whose default
headers carry the full Chrome 150 fingerprint block, backed by
``httpx_curl_cffi.AsyncCurlTransport`` when the dependency is available
(production), and by plain httpx when it is not (tests / fallback).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx

from novelai_image_mcp.nai.http import (
    BROWSER_HEADERS,
    CHROME_USER_AGENT,
    create_http_client,
)


class TestBrowserHeaders:
    def test_user_agent_is_chrome_150(self) -> None:
        """The UA string targets Chrome 150 stable on Windows."""
        assert "Chrome/150" in CHROME_USER_AGENT
        assert "Windows NT 10.0" in CHROME_USER_AGENT

    def test_browser_headers_contain_client_hints(self) -> None:
        """Cloudflare checks for Chromium Client Hints + Fetch Metadata."""
        assert "Sec-Ch-Ua" in BROWSER_HEADERS
        assert "Sec-Ch-Ua-Mobile" in BROWSER_HEADERS
        assert "Sec-Ch-Ua-Platform" in BROWSER_HEADERS
        assert "Sec-Fetch-Dest" in BROWSER_HEADERS
        assert "Sec-Fetch-Mode" in BROWSER_HEADERS
        assert "Sec-Fetch-Site" in BROWSER_HEADERS

    def test_referer_has_trailing_slash(self) -> None:
        """The real browser always sends ``https://novelai.net/`` (with slash)."""
        assert BROWSER_HEADERS["Referer"] == "https://novelai.net/"

    def test_sec_fetch_site_is_same_site(self) -> None:
        """``image.novelai.net`` is a sibling of ``novelai.net`` (same-site)."""
        assert BROWSER_HEADERS["Sec-Fetch-Site"] == "same-site"


class TestCreateHttpClient:
    async def test_returns_httpx_async_client(self) -> None:
        """The factory returns a real ``httpx.AsyncClient`` instance."""
        client = create_http_client(timeout=30.0)
        try:
            assert isinstance(client, httpx.AsyncClient)
            assert not client.is_closed
        finally:
            await client.aclose()

    async def test_browser_headers_set_as_client_defaults(self) -> None:
        """The Chrome fingerprint headers are set as default request headers."""
        client = create_http_client(timeout=30.0)
        try:
            # ``httpx.AsyncClient.headers`` exposes the merged default headers.
            assert client.headers["User-Agent"] == CHROME_USER_AGENT
            assert client.headers["Sec-Ch-Ua-Platform"] == '"Windows"'
            assert client.headers["Sec-Fetch-Site"] == "same-site"
        finally:
            await client.aclose()

    async def test_timeout_propagated(self) -> None:
        """The timeout kwarg is forwarded to the underlying client."""
        client = create_http_client(timeout=42.0)
        try:
            assert client.timeout.read == 42.0
        finally:
            await client.aclose()

    async def test_curl_transport_used_when_available(self) -> None:
        """When ``httpx_curl_cffi`` is installed, the curl transport is used."""
        # Build a minimal fake transport that satisfies ``httpx.BaseTransport``
        # enough for ``httpx.AsyncClient`` to accept it in the constructor.
        # We never send a request, so the methods are never called.
        fake_transport = httpx.AsyncBaseTransport()
        with patch(
            "novelai_image_mcp.nai.http._try_curl_transport",
            return_value=fake_transport,
        ) as mock_try:
            client = create_http_client(timeout=10.0)
            try:
                mock_try.assert_called_once()
            finally:
                await client.aclose()

    async def test_falls_back_to_plain_httpx_without_curl_cffi(self) -> None:
        """When ``httpx_curl_cffi`` is missing, plain httpx is used (no crash)."""
        # Simulate ``httpx_curl_cffi`` not being installed by patching
        # ``_try_curl_transport`` to return ``None`` (the documented fallback).
        with patch(
            "novelai_image_mcp.nai.http._try_curl_transport",
            return_value=None,
        ):
            client = create_http_client(timeout=10.0)
            try:
                # The client is still a functional httpx.AsyncClient; the
                # transport is the default httpx transport (not curl).
                assert isinstance(client, httpx.AsyncClient)
                # Browser headers are still set even without the curl transport.
                assert client.headers["User-Agent"] == CHROME_USER_AGENT
            finally:
                await client.aclose()
