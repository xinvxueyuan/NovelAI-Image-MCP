"""Sync CLI (typer) for direct invocation outside an MCP host.

The CLI is a thin wrapper around the async ``NovelAIClient``. Each subcommand
constructs a short-lived ``httpx.AsyncClient`` + ``NovelAIClient`` (no shared
session across invocations), runs the requested operation, prints the result,
and tears the clients down. For long-lived multi-tool use, prefer the MCP
server (``serve``) which owns a pooled session via its lifespan.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from enum import StrEnum
import json
from pathlib import Path
from typing import Annotated

import httpx
import typer

from .nai import (
    Action,
    ControlNetModel,
    DirectorTool,
    Emotion,
    EmotionLevel,
    GenerationRequest,
    Model,
    NovelAIClient,
    NovelAIError,
    create_http_client,
    create_novelai_client,
)
from .output import save_image
from .settings import NovelAISettings, get_novelai_settings


class Transport(StrEnum):
    """Selectable MCP transport on the ``serve`` subcommand."""

    STDIO = "stdio"
    HTTP = "streamable-http"


app = typer.Typer(
    name="novelai-image-mcp",
    help="NovelAI image generation — MCP server + sync CLI.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


def _build_client(settings: NovelAISettings) -> tuple[NovelAIClient, httpx.AsyncClient]:
    """Construct an owned httpx session + NovelAIClient for one CLI invocation."""
    if not settings.has_credentials():
        typer.echo(
            "NovelAI credentials are not configured: set NOVELAI_TOKEN or "
            "NOVELAI_USERNAME + NOVELAI_PASSWORD (see .env.example).",
            err=True,
        )
        raise typer.Exit(code=2)
    # ``create_http_client`` returns an ``httpx.AsyncClient`` backed by
    # ``curl_cffi`` (Chrome TLS fingerprint) with browser headers — required
    # for Cloudflare's bot WAF to accept the connection to NovelAI.
    http_client = create_http_client(timeout=settings.timeout)
    client = create_novelai_client(settings, http_client=http_client)
    return client, http_client


def _run(awaitable: Awaitable[object]) -> None:
    """Run an async coroutine to completion on a fresh event loop.

    NovelAI errors are printed to stderr (their message carries the error code
    and official explanation) and exit with a non-zero status instead of a raw
    traceback.
    """

    async def _wrapper() -> None:
        try:
            await awaitable
        except NovelAIError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

    asyncio.run(_wrapper())


def _parse_model(value: str | None, settings: NovelAISettings) -> Model:
    """Resolve a model string against the configured default."""
    resolved = value or settings.default_model
    try:
        return Model(resolved)
    except ValueError as exc:
        raise typer.BadParameter(
            f"unknown model '{resolved}'; expected one of: "
            f"{', '.join(m.value for m in Model)}"
        ) from exc


def _read_image_file(path: Path) -> bytes:
    """Read an image file from disk, raising a CLI error on failure."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise typer.BadParameter(f"cannot read image file {path}: {exc}") from exc


@app.command()
def serve(
    transport: Annotated[
        Transport,
        typer.Option(
            "--transport",
            "-t",
            help="MCP transport (overrides MCP_TRANSPORT env var).",
            case_sensitive=False,
        ),
    ] = Transport.STDIO,
    host: Annotated[
        str,
        typer.Option(help="Bind host for streamable-http (overrides MCP_HOST)."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(help="Bind port for streamable-http (overrides MCP_PORT)."),
    ] = 8000,
) -> None:
    """Run the MCP server (stdio by default, or streamable-http)."""
    # Defer the import so `novelai-image-mcp generate` does not pay the MCP SDK
    # import cost (and so credential errors surface only when actually serving).
    from . import server as server_module

    if transport is Transport.HTTP:
        server_module.mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
        )
    else:
        server_module.mcp.run(transport="stdio")


@app.command()
def generate(
    prompt: Annotated[str, typer.Option("--prompt", "-p", help="Text prompt.")],
    negative_prompt: Annotated[
        str, typer.Option("--negative", "-n", help="Negative prompt.")
    ] = "",
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="NovelAI model id."),
    ] = None,
    width: Annotated[
        int | None, typer.Option("--width", help="Image width (px, multiple of 64).")
    ] = None,
    height: Annotated[
        int | None, typer.Option("--height", help="Image height (px, multiple of 64).")
    ] = None,
    steps: Annotated[int | None, typer.Option("--steps")] = None,
    scale: Annotated[float | None, typer.Option("--scale")] = None,
    sampler: Annotated[str | None, typer.Option("--sampler")] = None,
    seed: Annotated[int, typer.Option("--seed", help="RNG seed (0 = random).")] = 0,
    n_samples: Annotated[
        int, typer.Option("--n-samples", help="Number of images (1–8).")
    ] = 1,
    output_dir: Annotated[
        str | None,
        typer.Option("--output-dir", "-o", help="Override NOVELAI_OUTPUT_DIR."),
    ] = None,
) -> None:
    """Generate one or more images from a text prompt (text-to-image)."""
    settings = get_novelai_settings()
    client, http_client = _build_client(settings)
    request = GenerationRequest(
        prompt=prompt,
        action=Action.GENERATE,
        negative_prompt=negative_prompt,
        model=_parse_model(model, settings),
        width=width or settings.default_width,
        height=height or settings.default_height,
        steps=steps or settings.default_steps,
        scale=scale or settings.default_scale,
        sampler=sampler or settings.default_sampler,
        seed=seed,
        n_samples=n_samples,
    )
    target_dir = output_dir or settings.output_dir

    async def _do() -> None:
        try:
            images = await client.generate(request)
            for image in images:
                path = save_image(image.data, name="generate", output_dir=target_dir)
                typer.echo(str(path))
        finally:
            await client.aclose()
            if not http_client.is_closed:
                await http_client.aclose()

    _run(_do())


@app.command()
def upscale(
    image: Annotated[Path, typer.Argument(help="Path to the PNG/JPEG to upscale.")],
    factor: Annotated[
        int,
        typer.Option("--factor", "-f", help="Upscale factor (2 or 4)."),
    ] = 4,
    output_dir: Annotated[str | None, typer.Option("--output-dir", "-o")] = None,
) -> None:
    """Upscale an image by 2× or 4×."""
    settings = get_novelai_settings()
    client, http_client = _build_client(settings)
    raw = _read_image_file(image)
    target_dir = output_dir or settings.output_dir

    async def _do() -> None:
        try:
            result = await client.upscale(raw, factor=factor)
            path = save_image(result.data, name="upscale", output_dir=target_dir)
            typer.echo(str(path))
        finally:
            await client.aclose()
            if not http_client.is_closed:
                await http_client.aclose()

    _run(_do())


@app.command(name="director")
def director_cmd(
    tool: Annotated[
        str,
        typer.Argument(help="Director tool: lineart, sketch, bg-removal, ..."),
    ],
    image: Annotated[Path, typer.Argument(help="Path to the input image.")],
    prompt: Annotated[str, typer.Option("--prompt", "-p")] = "",
    defry: Annotated[
        int, typer.Option("--defry", help="Line-art sharpening (0–10).")
    ] = 0,
    emotion: Annotated[
        str | None,
        typer.Option("--emotion", help="Emotion name (emotion tool only)."),
    ] = None,
    emotion_level: Annotated[
        int, typer.Option("--emotion-level", help="Emotion intensity 0–5.")
    ] = 0,
    output_dir: Annotated[str | None, typer.Option("--output-dir", "-o")] = None,
) -> None:
    """Apply a NovelAI Director tool to an image."""
    settings = get_novelai_settings()
    client, http_client = _build_client(settings)
    try:
        director = DirectorTool(tool)
    except ValueError as exc:
        raise typer.BadParameter(
            f"unknown director tool '{tool}'; expected one of: "
            f"{', '.join(t.value for t in DirectorTool)}"
        ) from exc
    raw = _read_image_file(image)
    emotion_enum: Emotion | None = None
    if director is DirectorTool.EMOTION:
        if not emotion:
            raise typer.BadParameter("emotion tool requires --emotion")
        try:
            emotion_enum = Emotion(emotion)
        except ValueError as exc:
            raise typer.BadParameter(
                f"unknown emotion '{emotion}'; expected one of: "
                f"{', '.join(e.value for e in Emotion)}"
            ) from exc
    try:
        level = EmotionLevel(emotion_level)
    except ValueError as exc:
        raise typer.BadParameter(
            f"emotion_level must be between {EmotionLevel.NORMAL} and "
            f"{max(EmotionLevel)}"
        ) from exc
    target_dir = output_dir or settings.output_dir

    async def _do() -> None:
        try:
            result = await client.director(
                director,
                raw,
                prompt=prompt,
                defry=defry,
                emotion=emotion_enum,
                emotion_level=level,
            )
            path = save_image(
                result.data,
                name=f"director-{director.value}",
                output_dir=target_dir,
            )
            typer.echo(str(path))
        finally:
            await client.aclose()
            if not http_client.is_closed:
                await http_client.aclose()

    _run(_do())


@app.command()
def annotate(
    image: Annotated[Path, typer.Argument(help="Path to the input image.")],
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="ControlNet model: hed, midas, fake_scribble, mlsd, uniformer.",
        ),
    ],
    output_dir: Annotated[str | None, typer.Option("--output-dir", "-o")] = None,
) -> None:
    """Annotate an image with a ControlNet preprocessor."""
    settings = get_novelai_settings()
    client, http_client = _build_client(settings)
    try:
        controlnet = ControlNetModel(model)
    except ValueError as exc:
        raise typer.BadParameter(
            f"unknown controlnet model '{model}'; expected one of: "
            f"{', '.join(m.value for m in ControlNetModel)}"
        ) from exc
    raw = _read_image_file(image)
    target_dir = output_dir or settings.output_dir

    async def _do() -> None:
        try:
            result = await client.annotate(raw, controlnet)
            path = save_image(
                result.data,
                name=f"annotate-{controlnet.value}",
                output_dir=target_dir,
            )
            typer.echo(str(path))
        finally:
            await client.aclose()
            if not http_client.is_closed:
                await http_client.aclose()

    _run(_do())


@app.command()
def info() -> None:
    """Print the account subscription and Anlas balance as JSON."""
    settings = get_novelai_settings()
    client, http_client = _build_client(settings)

    async def _do() -> None:
        try:
            subscription = await client.get_subscription()
            typer.echo(json.dumps(subscription, ensure_ascii=False, indent=2))
        finally:
            await client.aclose()
            if not http_client.is_closed:
                await http_client.aclose()

    _run(_do())


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()


__all__ = ["app", "main"]
