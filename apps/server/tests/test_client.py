"""Tests for ``nai.client.NovelAIClient`` HTTP behavior (respx-mocked)."""

from __future__ import annotations

import io
import struct
from typing import cast
import zipfile

from _helpers import PNG_BYTES
import httpx
import msgpack
import pytest
import respx

from novelai_image_mcp.nai import (
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    GenerationRequest,
    Model,
    NovelAIAuthenticationError,
    NovelAIClient,
    NovelAIConcurrencyError,
    NovelAICredentials,
    NovelAIInsufficientCreditsError,
    NovelAIResponseError,
    NovelAIValidationError,
)


def _png_zip() -> bytes:
    """Build a ZIP archive containing a single PNG entry (V3 generate shape)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("image_0.png", PNG_BYTES)
    return buffer.getvalue()


def _msgpack_final_frame(image: bytes = PNG_BYTES) -> bytes:
    """Build a single ``final`` event as a length-prefixed msgpack frame."""
    # ``msgpack.packb`` is untyped in the shipped stubs; cast to ``bytes`` so
    # the ``len(payload)`` / concatenation below type-checks without ambiguity.
    payload = cast(
        "bytes",
        msgpack.packb(
            {
                "event_type": "final",
                "samp_ix": 0,
                "step_ix": 28,
                "gen_id": "g1",
                "image": image,
            },
        ),
    )
    return struct.pack(">I", len(payload)) + payload


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    """A real ``httpx.AsyncClient`` shared with the client under test."""
    return httpx.AsyncClient()


@pytest.fixture
def nai_client(http_client: httpx.AsyncClient) -> NovelAIClient:
    """A NovelAIClient backed by ``http_client`` (respx intercepts its calls)."""
    return NovelAIClient(
        NovelAICredentials(token="pst-test-token"),
        http_client=http_client,
    )


@pytest.fixture
def login_client(http_client: httpx.AsyncClient) -> NovelAIClient:
    """A NovelAIClient without a cached token — forces the login flow."""
    return NovelAIClient(
        NovelAICredentials(username="alice", password="secret"),
        http_client=http_client,
    )


class TestLogin:
    @respx.mock
    async def test_get_access_token_caches_after_login(
        self, login_client: NovelAIClient
    ) -> None:
        login = respx.post("https://image.novelai.net/user/login").mock(
            return_value=httpx.Response(200, json={"accessToken": "abc"})
        )
        token = await login_client.get_access_token()
        assert token == "abc"
        assert login.call_count == 1
        # Second call should hit the cache (no new HTTP request).
        assert await login_client.get_access_token() == "abc"
        assert login.call_count == 1

    @respx.mock
    async def test_login_missing_token_raises(
        self, login_client: NovelAIClient
    ) -> None:
        respx.post("https://image.novelai.net/user/login").mock(
            return_value=httpx.Response(200, json={})
        )
        with pytest.raises(NovelAIResponseError, match="access token"):
            await login_client.get_access_token()


class TestGenerate:
    @respx.mock
    async def test_generate_v3_parses_zip(self, nai_client: NovelAIClient) -> None:
        route = respx.post("https://image.novelai.net/ai/generate-image").mock(
            return_value=httpx.Response(200, content=_png_zip())
        )
        images = await nai_client.generate(
            GenerationRequest(prompt="a cat", model=Model.V3)
        )
        assert route.called
        assert len(images) == 1
        assert images[0].data == PNG_BYTES

    @respx.mock
    async def test_generate_v4_parses_msgpack_stream(
        self, nai_client: NovelAIClient
    ) -> None:
        route = respx.post("https://image.novelai.net/ai/generate-image-stream").mock(
            return_value=httpx.Response(200, content=_msgpack_final_frame())
        )
        images = await nai_client.generate(
            GenerationRequest(prompt="a cat", model=Model.V4_5)
        )
        assert route.called
        assert len(images) == 1
        assert images[0].data == PNG_BYTES


class TestUpscaleDirectorAnnotate:
    @respx.mock
    async def test_upscale_returns_image(self, nai_client: NovelAIClient) -> None:
        respx.post("https://image.novelai.net/ai/upscale").mock(
            return_value=httpx.Response(200, content=PNG_BYTES)
        )
        result = await nai_client.upscale(PNG_BYTES, factor=4)
        assert result.data == PNG_BYTES
        assert result.filename == "upscaled.png"

    @respx.mock
    async def test_upscale_invalid_factor_rejected(
        self, nai_client: NovelAIClient
    ) -> None:
        with pytest.raises(ValueError, match="upscale factor"):
            await nai_client.upscale(PNG_BYTES, factor=3)

    @respx.mock
    async def test_director_emotion_requires_emotion(
        self, nai_client: NovelAIClient
    ) -> None:
        with pytest.raises(ValueError, match="emotion tool requires"):
            await nai_client.director(DirectorTool.EMOTION, PNG_BYTES)

    @respx.mock
    async def test_director_emotion_builds_prompt(
        self, nai_client: NovelAIClient
    ) -> None:
        route = respx.post("https://image.novelai.net/ai/augment-image").mock(
            return_value=httpx.Response(200, content=PNG_BYTES)
        )
        await nai_client.director(
            DirectorTool.EMOTION,
            PNG_BYTES,
            emotion=Emotion.HAPPY,
            emotion_level=EmotionLevel.NORMAL,
        )
        body = route.calls.last.request.read()
        assert b"happy;;" in body

    @respx.mock
    async def test_annotate_returns_image(self, nai_client: NovelAIClient) -> None:
        respx.post("https://image.novelai.net/ai/annotate-image").mock(
            return_value=httpx.Response(200, content=PNG_BYTES)
        )
        result = await nai_client.annotate(PNG_BYTES, ControlNetModel.PALETTE_SWAP)
        assert result.data == PNG_BYTES


class TestTagsAndAccount:
    @respx.mock
    async def test_suggest_tags_returns_list(self, nai_client: NovelAIClient) -> None:
        respx.get("https://image.novelai.net/ai/generate-image/suggest-tags").mock(
            return_value=httpx.Response(
                200, json={"tags": [{"text": "cat", "count": 10}]}
            )
        )
        tags = await nai_client.suggest_tags("ca")
        assert tags == ({"text": "cat", "count": 10},)

    @respx.mock
    async def test_get_subscription(self, nai_client: NovelAIClient) -> None:
        respx.get("https://image.novelai.net/user/subscription").mock(
            return_value=httpx.Response(200, json={"tier": 1})
        )
        assert await nai_client.get_subscription() == {"tier": 1}

    @respx.mock
    async def test_get_user_data(self, nai_client: NovelAIClient) -> None:
        respx.get("https://image.novelai.net/user/data").mock(
            return_value=httpx.Response(200, json={"email": "a@b.com"})
        )
        assert await nai_client.get_user_data() == {"email": "a@b.com"}


class TestEncodeVibe:
    @respx.mock
    async def test_encode_vibe_caches(self, nai_client: NovelAIClient) -> None:
        route = respx.post("https://image.novelai.net/ai/encode-vibe").mock(
            return_value=httpx.Response(200, content=b"\x01\x02\x03")
        )
        token1 = await nai_client.encode_vibe(
            "base64-ref", information_extracted=1.0, model=Model.V4_5
        )
        token2 = await nai_client.encode_vibe(
            "base64-ref", information_extracted=1.0, model=Model.V4_5
        )
        assert token1 == token2
        assert route.call_count == 1


class TestErrorHandling:
    @respx.mock
    @pytest.mark.parametrize(
        ("status", "exception"),
        [
            (400, NovelAIValidationError),
            (401, NovelAIAuthenticationError),
            (402, NovelAIInsufficientCreditsError),
            (429, NovelAIConcurrencyError),
        ],
    )
    async def test_status_codes_raise_typed_errors(
        self,
        nai_client: NovelAIClient,
        status: int,
        exception: type[Exception],
    ) -> None:
        respx.get("https://image.novelai.net/user/subscription").mock(
            return_value=httpx.Response(status, json={"detail": "nope"})
        )
        with pytest.raises(exception):
            await nai_client.get_subscription()


class TestCredentials:
    def test_token_only_accepted(self) -> None:
        client = NovelAIClient(NovelAICredentials(token="tok"))
        assert client._access_token == "tok"

    def test_missing_credentials_raises(self) -> None:
        with pytest.raises(ValueError, match="provide a token"):
            NovelAICredentials()

    def test_partial_pair_raises(self) -> None:
        with pytest.raises(ValueError, match="provide a token"):
            NovelAICredentials(username="alice")
