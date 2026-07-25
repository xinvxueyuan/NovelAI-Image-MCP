"""Complete NovelAI HTTP client built on a shared httpx async session.

A long-lived ``httpx.AsyncClient`` is owned by the instance (or supplied by the
MCP lifespan) and used for all NovelAI API traffic. Covers generation, Director,
utility, and account business logic.
"""

from __future__ import annotations

import base64
from collections import OrderedDict
from collections.abc import AsyncIterator, Mapping
from dataclasses import replace
from hashlib import sha256
import json
from typing import Any

import httpx

from .auth import NovelAICredentials, derive_access_key, request_tracking_headers
from .constants import (
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    Endpoint,
    Model,
    is_v4_model,
)
from .exceptions import (
    NovelAIAuthenticationError,
    NovelAIError,
    NovelAIProviderError,
    NovelAIResponseError,
    NovelAITimeoutError,
    NovelAITransportError,
)
from .http import BROWSER_HEADERS, create_http_client
from .imaging import parse_image
from .models import CharacterPrompt, GenerationRequest
from .payload import build_generation_payload
from .response import (
    GenerationEvent,
    MessagePackStreamParser,
    NovelAIImage,
    check_status,
    parse_messagepack_images,
    parse_zip_images,
)

_SHARED_VIBE_CACHE: OrderedDict[str, str] = OrderedDict()


class MissingNovelAITokenError(NovelAIAuthenticationError):
    """No usable NovelAI credential is configured."""


def _content(response: httpx.Response) -> bytes:
    content = getattr(response, "content", b"")
    if isinstance(content, str):
        return content.encode()
    if isinstance(content, bytes):
        return content
    raise NovelAIResponseError("NovelAI response has no binary content")


def _json_object(content: bytes) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise NovelAIResponseError("NovelAI returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise NovelAIResponseError("NovelAI returned a non-object JSON response")
    return value


def _first_image(content: bytes, *, filename: str) -> NovelAIImage:
    if content.startswith(b"PK"):
        images = parse_zip_images(content)
        if not images:
            raise NovelAIResponseError("NovelAI returned an empty image archive")
        return replace(images[0], filename=filename)
    return NovelAIImage(filename=filename, data=content)


class NovelAIClient:
    """Project-owned client for generation, tools, utilities, and account APIs."""

    def __init__(
        self,
        credentials: NovelAICredentials,
        *,
        http_client: httpx.AsyncClient | None = None,
        image_base_url: str = "https://image.novelai.net",
        account_base_url: str = "https://api.novelai.net",
        timeout: float = 120.0,
        vibe_cache_entries: int = 64,
    ) -> None:
        self.credentials = credentials
        self.image_base_url = image_base_url.rstrip("/")
        self.account_base_url = account_base_url.rstrip("/")
        self.timeout = timeout
        self.vibe_cache_entries = vibe_cache_entries
        self._access_token: str | None = credentials.token
        self._vibe_cache = _SHARED_VIBE_CACHE
        # When no shared http_client is supplied (production paths via
        # ``server.lifespan`` and the CLI), build one with Chrome TLS +
        # header fingerprint impersonation so Cloudflare's bot WAF accepts
        # the connection. Tests inject a plain ``httpx.AsyncClient`` so
        # ``respx`` can intercept at the transport layer.
        self._http = http_client or create_http_client(self.timeout)
        self._owns_http = http_client is None

    async def aclose(self) -> None:
        """Close the underlying HTTP session when owned by this client."""
        if self._owns_http and not self._http.is_closed:
            await self._http.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        authenticated: bool = True,
        json_body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> bytes:
        # Start from the full Chrome fingerprint block so requests carry the
        # browser headers even when the caller injected a plain httpx client
        # (tests). Per-request values below override the defaults where needed.
        headers = dict(BROWSER_HEADERS)
        headers["Content-Type"] = "application/json"
        headers.update(request_tracking_headers())
        if authenticated:
            headers["Authorization"] = f"Bearer {await self.get_access_token()}"
        try:
            response = await self._http.request(
                method,
                url,
                headers=headers,
                json=dict(json_body) if json_body is not None else None,
                params=dict(params) if params is not None else None,
            )
        except TimeoutError as exc:
            raise NovelAITimeoutError("NovelAI request timed out") from exc
        except httpx.HTTPError as exc:
            raise NovelAITransportError("NovelAI request transport failed") from exc
        content = _content(response)
        check_status(response.status_code, content)
        return content

    async def get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        payload = {"key": derive_access_key(self.credentials)}
        content = await self._request(
            "POST",
            f"{self.account_base_url}{Endpoint.LOGIN}",
            authenticated=False,
            json_body=payload,
        )
        token = _json_object(content).get("accessToken")
        if not isinstance(token, str) or not token:
            raise NovelAIResponseError("NovelAI login did not return an access token")
        self._access_token = token
        return token

    async def encode_vibe(
        self,
        reference: str,
        *,
        information_extracted: float,
        model: Model,
    ) -> str:
        key = sha256(
            (
                f"{self.image_base_url}\0{reference}\0"
                f"{information_extracted}\0{model.value}"
            ).encode()
        ).hexdigest()
        cached = self._vibe_cache.get(key)
        if cached is not None:
            self._vibe_cache.move_to_end(key)
            return cached
        content = await self._request(
            "POST",
            f"{self.image_base_url}{Endpoint.ENCODE_VIBE}",
            json_body={
                "image": reference,
                "information_extracted": information_extracted,
                "model": model.value,
            },
        )
        token = base64.b64encode(content).decode("ascii")
        self._vibe_cache[key] = token
        while len(self._vibe_cache) > self.vibe_cache_entries:
            self._vibe_cache.popitem(last=False)
        return token

    async def _prepare_references(
        self, request: GenerationRequest
    ) -> GenerationRequest:
        if not is_v4_model(request.model) or not request.references:
            return request
        information = request.reference_information or tuple(
            1.0 for _ in request.references
        )
        encoded = tuple([
            await self.encode_vibe(
                reference,
                information_extracted=information[index],
                model=request.model,
            )
            for index, reference in enumerate(request.references)
        ])
        return replace(request, references=encoded, reference_information=())

    async def generate(
        self,
        request: GenerationRequest,
    ) -> tuple[NovelAIImage, ...]:
        prepared = await self._prepare_references(request)
        endpoint = (
            Endpoint.IMAGE_STREAM if is_v4_model(prepared.model) else Endpoint.IMAGE
        )
        content = await self._request(
            "POST",
            f"{self.image_base_url}{endpoint}",
            json_body=build_generation_payload(prepared),
        )
        if is_v4_model(prepared.model):
            return parse_messagepack_images(content)
        return parse_zip_images(content)

    async def stream_generation(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[GenerationEvent]:
        """Yield V4/V4.5 events as the active driver produces HTTP chunks."""
        prepared = await self._prepare_references(request)
        if not is_v4_model(prepared.model):
            raise ValueError("real-time generation requires a V4/V4.5 model")
        # Start from the Chrome fingerprint block (same as ``_request``) and
        # override Accept for the MessagePack streaming endpoint.
        headers = dict(BROWSER_HEADERS)
        headers["Accept"] = "application/x-msgpack"
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {await self.get_access_token()}"
        headers.update(request_tracking_headers())
        url = f"{self.image_base_url}{Endpoint.IMAGE_STREAM}"
        body = build_generation_payload(prepared)
        parser = MessagePackStreamParser()
        try:
            async with self._http.stream(
                "POST", url, headers=headers, json=body
            ) as response:
                if response.status_code >= 400:
                    content = await response.aread()
                    check_status(response.status_code, content)
                    return
                async for chunk in response.aiter_bytes():
                    for event in parser.feed(chunk):
                        yield event
            parser.finish()
        except NovelAIError:
            raise
        except TimeoutError as exc:
            raise NovelAITimeoutError("NovelAI streaming request timed out") from exc
        except httpx.HTTPError as exc:
            raise NovelAITransportError("NovelAI streaming transport failed") from exc

    async def director(
        self,
        tool: DirectorTool,
        image: bytes,
        *,
        prompt: str = "",
        defry: int = 0,
        emotion: Emotion | None = None,
        emotion_level: EmotionLevel = EmotionLevel.NORMAL,
    ) -> NovelAIImage:
        parsed = parse_image(image)
        if tool is DirectorTool.EMOTION:
            if emotion is None:
                raise ValueError("emotion tool requires an emotion")
            prompt = f"{emotion.value};;{prompt + ',' if prompt else ''}"
            defry = int(emotion_level)
        content = await self._request(
            "POST",
            f"{self.image_base_url}{Endpoint.DIRECTOR}",
            json_body={
                "req_type": tool.value,
                "width": parsed.width,
                "height": parsed.height,
                "image": parsed.base64,
                "prompt": prompt,
                "defry": defry,
            },
        )
        return _first_image(content, filename=f"{tool.value}.png")

    async def upscale(self, image: bytes, *, factor: int = 4) -> NovelAIImage:
        if factor not in {2, 4}:
            raise ValueError("upscale factor must be 2 or 4")
        parsed = parse_image(image)
        content = await self._request(
            "POST",
            f"{self.account_base_url}{Endpoint.UPSCALE}",
            json_body={
                "image": parsed.base64,
                "width": parsed.width,
                "height": parsed.height,
                "scale": factor,
            },
        )
        return _first_image(content, filename="upscaled.png")

    async def annotate(
        self,
        image: bytes,
        model: ControlNetModel,
    ) -> NovelAIImage:
        parsed = parse_image(image)
        content = await self._request(
            "POST",
            f"{self.account_base_url}{Endpoint.ANNOTATE}",
            json_body={"model": model.value, "parameters": {"image": parsed.base64}},
        )
        return _first_image(content, filename=f"{model.value}.png")

    async def suggest_tags(
        self,
        prompt: str,
        *,
        model: Model = Model.V4_5,
        language: str = "en",
    ) -> tuple[dict[str, Any], ...]:
        content = await self._request(
            "GET",
            f"{self.image_base_url}{Endpoint.SUGGEST_TAGS}",
            params={"model": model.value, "prompt": prompt, "lang": language},
        )
        tags = _json_object(content).get("tags", [])
        if not isinstance(tags, list) or not all(
            isinstance(item, dict) for item in tags
        ):
            raise NovelAIResponseError("NovelAI returned invalid tag suggestions")
        return tuple(tags)

    async def get_subscription(self) -> dict[str, Any]:
        content = await self._request(
            "GET",
            f"{self.account_base_url}{Endpoint.SUBSCRIPTION}",
        )
        return _json_object(content)

    async def get_user_data(self) -> dict[str, Any]:
        content = await self._request(
            "GET",
            f"{self.account_base_url}{Endpoint.USER_DATA}",
        )
        return _json_object(content)


def _process_event(event: object) -> tuple[str, bytes | None, str | None]:
    """Compatibility helper retained for existing parser tests."""
    if not isinstance(event, dict):
        return (type(event).__name__, None, None)
    event_type = str(event.get("event_type"))
    if event_type == "final":
        image = event.get("image")
        if isinstance(image, bytes):
            return (event_type, image, None)
        if isinstance(image, str):
            try:
                return (event_type, base64.b64decode(image, validate=True), None)
            except ValueError:
                return (event_type, None, "Invalid final image value")
        return (event_type, None, "Invalid final image value")
    if event_type == "error":
        return (
            event_type,
            None,
            f"NovelAI error (code={event.get('code', 'unknown')}): "
            f"{event.get('message', 'unknown error')}",
        )
    return (event_type, None, None)


def extract_final_image(content: bytes) -> bytes:
    try:
        images = parse_messagepack_images(content)
    except NovelAIProviderError as exc:
        raise NovelAIResponseError(str(exc)) from exc
    if not images:
        raise NovelAIResponseError("No final image in stream")
    return images[-1].data


def _coordinate(value: object, *, default: float = 0.5) -> float:
    if isinstance(value, int | float):
        return float(value)
    return default


async def generate_image_from_plan(
    plan: Any,
    *,
    client: NovelAIClient,
    n_samples: int = 1,
    quality: bool = True,
    uc_preset: int = 0,
    noise_schedule: str = "karras",
    cfg_rescale: float = 0.0,
    dynamic_thresholding: bool = False,
    auto_smea: bool = False,
    prefer_brownian: bool = True,
) -> bytes:
    """Generate a single image from a high-level plan (used by the sync CLI).

    The caller supplies the configured client plus the generation defaults
    (read from settings, not from a global config).
    """
    characters: list[CharacterPrompt] = []
    for raw_character in plan.character_prompts:
        center = raw_character.get("center", {})
        center_values = center if isinstance(center, dict) else {}
        characters.append(
            CharacterPrompt(
                prompt=str(raw_character.get("prompt", "")),
                negative_prompt=str(raw_character.get("uc", "")),
                x=_coordinate(center_values.get("x")),
                y=_coordinate(center_values.get("y")),
                enabled=bool(raw_character.get("enabled", True)),
            )
        )
    request = GenerationRequest(
        prompt=plan.prompt,
        base_caption=plan.base_caption,
        negative_prompt=plan.negative_prompt,
        model=Model(plan.model),
        width=plan.width,
        height=plan.height,
        steps=plan.steps,
        scale=plan.scale,
        sampler=plan.sampler,
        seed=plan.seed,
        n_samples=n_samples,
        quality=quality,
        uc_preset=uc_preset,
        noise_schedule=noise_schedule,
        cfg_rescale=cfg_rescale,
        dynamic_thresholding=dynamic_thresholding,
        auto_smea=auto_smea,
        prefer_brownian=prefer_brownian,
        character_prompts=tuple(characters),
        use_coords=plan.use_coords,
    )
    images = await client.generate(request)
    if not images:
        raise NovelAIResponseError("NovelAI returned no final images")
    return images[-1].data


__all__ = [
    "MissingNovelAITokenError",
    "NovelAIClient",
    "NovelAIError",
    "NovelAIProviderError",
    "NovelAIResponseError",
    "NovelAITimeoutError",
    "NovelAITransportError",
    "extract_final_image",
    "generate_image_from_plan",
]
