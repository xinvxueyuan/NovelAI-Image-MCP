"""Tests for the `novelai://...` resources."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pytest

from novelai_image_mcp.nai import Model


class TestCatalogResources:
    async def test_models_resource_lists_every_model(self, mcp_client: Any) -> None:
        contents = await mcp_client.read_resource("novelai://models")
        payload = json.loads(contents[0].text)
        assert {entry["id"] for entry in payload["models"]} == {
            model.value for model in Model
        }

    async def test_models_resource_flags_capabilities(self, mcp_client: Any) -> None:
        contents = await mcp_client.read_resource("novelai://models")
        by_id = {entry["id"]: entry for entry in json.loads(contents[0].text)["models"]}
        v45 = by_id[Model.V4_5.value]
        assert v45["vibe_transfer"] is True
        assert v45["v5"] is False
        v5 = by_id[Model.V5.value]
        assert v5["vibe_transfer"] is False
        assert v5["v5"] is True
        assert by_id[Model.V4_5_INPAINT.value]["inpainting"] is True

    async def test_samplers_resource(self, mcp_client: Any) -> None:
        contents = await mcp_client.read_resource("novelai://samplers")
        payload = json.loads(contents[0].text)
        assert "k_euler_ancestral" in payload["samplers"]
        assert "karras" in payload["noise_schedules"]
        assert payload["uc_presets"] == [0, 1, 2, 3]

    async def test_defaults_resource_mirrors_settings(
        self, mcp_client: Any, settings: Any
    ) -> None:
        contents = await mcp_client.read_resource("novelai://defaults")
        payload = json.loads(contents[0].text)
        assert payload["model"] == settings.default_model
        assert payload["width"] == settings.default_width
        assert payload["steps"] == settings.default_steps
        # Credentials and endpoints must never leak through a resource.
        assert not {"token", "password", "image_base_url"} & payload.keys()


class TestOutputResource:
    async def test_reads_a_generated_png(
        self, mcp_client: Any, settings: Any, png_bytes: bytes
    ) -> None:
        from mcp_types import BlobResourceContents

        name = "generate-20260101T000000Z-abcdef.png"
        (Path(settings.output_dir) / name).write_bytes(png_bytes)
        contents = await mcp_client.read_resource(f"novelai://outputs/{name}")
        block = contents[0]
        assert isinstance(block, BlobResourceContents)
        assert block.mime_type == "image/png"
        # Resources carry bytes base64-encoded, so decode before comparing.
        assert base64.b64decode(block.blob) == png_bytes

    async def test_missing_image_is_reported(self, mcp_client: Any) -> None:
        from mcp.shared.exceptions import MCPError

        with pytest.raises(MCPError):
            await mcp_client.read_resource("novelai://outputs/absent.png")


class TestResolveOutputPath:
    """The template handler validates the name before touching the disk."""

    def test_accepts_a_plain_png_name(self, settings: Any, png_bytes: bytes) -> None:
        from novelai_image_mcp.output import resolve_output_path

        (Path(settings.output_dir) / "shot.png").write_bytes(png_bytes)
        resolved = resolve_output_path("shot.png", output_dir=settings.output_dir)
        assert resolved.name == "shot.png"

    @pytest.mark.parametrize(
        "name",
        ["../escape.png", "nested/shot.png", "/etc/passwd.png", "shot.jpg", ".png"],
    )
    def test_rejects_everything_but_plain_png_names(
        self, settings: Any, name: str
    ) -> None:
        from novelai_image_mcp.output import resolve_output_path

        with pytest.raises(ValueError, match="invalid image name"):
            resolve_output_path(name, output_dir=settings.output_dir)

    def test_reports_a_missing_file(self, settings: Any) -> None:
        from novelai_image_mcp.output import resolve_output_path

        with pytest.raises(FileNotFoundError):
            resolve_output_path("absent.png", output_dir=settings.output_dir)
