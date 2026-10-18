"""Tests for the `novelai://...` resources."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pytest

from novelai_image_mcp.nai import Model
from novelai_image_mcp.routing import RoutingContext


def _routed(route: str) -> RoutingContext:
    """An active routing context for `route` (which may be hostile)."""
    return RoutingContext(enabled=True, route=route, transport="http")


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
        # Only the V5 line supports the standalone 4x upscaler (live-verified).
        assert v5["standalone_upscale"] is True
        assert v45["standalone_upscale"] is False

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


class TestRouteScopedOutputResource:
    """The outputs resource resolves inside the request's route scope."""

    NAME = "generate-20260101T000000Z-abcdef.png"

    @staticmethod
    def _write(directory: Path, data: bytes) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / TestRouteScopedOutputResource.NAME).write_bytes(data)

    def test_reads_from_the_route_subdirectory(
        self, fake_app: Any, png_bytes: bytes
    ) -> None:
        from novelai_image_mcp.resources import read_output_image

        self._write(Path(fake_app.settings.output_dir) / "alpha", png_bytes)
        data = read_output_image(
            self.NAME,
            app=fake_app,
            routing=_routed("alpha"),
            route_scoped_output=True,
        )
        assert data == png_bytes

    def test_route_scope_hides_images_outside_it(
        self, fake_app: Any, png_bytes: bytes
    ) -> None:
        from fastmcp.exceptions import ResourceError

        from novelai_image_mcp.resources import read_output_image

        # The image exists, but in the flat directory: a scoped request must not
        # see it, which is what makes the scope a real boundary.
        self._write(Path(fake_app.settings.output_dir), png_bytes)
        with pytest.raises(ResourceError):
            read_output_image(
                self.NAME,
                app=fake_app,
                routing=_routed("alpha"),
                route_scoped_output=True,
            )

    def test_routing_disabled_reads_the_flat_directory(
        self, fake_app: Any, png_bytes: bytes
    ) -> None:
        from novelai_image_mcp.resources import read_output_image

        self._write(Path(fake_app.settings.output_dir), png_bytes)
        data = read_output_image(
            self.NAME,
            app=fake_app,
            routing=RoutingContext.disabled(),
            route_scoped_output=True,
        )
        assert data == png_bytes

    def test_route_scoping_off_reads_the_flat_directory(
        self, fake_app: Any, png_bytes: bytes
    ) -> None:
        from novelai_image_mcp.resources import read_output_image

        self._write(Path(fake_app.settings.output_dir), png_bytes)
        data = read_output_image(
            self.NAME,
            app=fake_app,
            routing=_routed("alpha"),
            route_scoped_output=False,
        )
        assert data == png_bytes

    @pytest.mark.parametrize(
        "name", ["../escape.png", "nested/shot.png", "/etc/passwd.png", "shot.jpg"]
    )
    def test_escape_attempts_are_still_rejected(self, fake_app: Any, name: str) -> None:
        from fastmcp.exceptions import ResourceError

        from novelai_image_mcp.resources import read_output_image

        with pytest.raises(ResourceError, match="invalid image name"):
            read_output_image(
                name,
                app=fake_app,
                routing=_routed("alpha"),
                route_scoped_output=True,
            )

    def test_unusable_route_stays_inside_the_output_directory(
        self, fake_app: Any, png_bytes: bytes
    ) -> None:
        from novelai_image_mcp.resources import read_output_image

        # A hostile route sanitises to "unknown", so it cannot climb out of the
        # configured output directory even though routing is active.
        self._write(Path(fake_app.settings.output_dir) / "unknown", png_bytes)
        data = read_output_image(
            self.NAME,
            app=fake_app,
            routing=_routed("../../escape"),
            route_scoped_output=True,
        )
        assert data == png_bytes
