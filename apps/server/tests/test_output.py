"""Tests for ``output.save_image``."""

from __future__ import annotations

from pathlib import Path

from _helpers import PNG_BYTES

from novelai_image_mcp.output import save_image


class TestSaveImage:
    def test_writes_png_file(self, tmp_path: Path) -> None:
        path = save_image(PNG_BYTES, name="gen", output_dir=tmp_path)
        assert path.exists()
        assert path.suffix == ".png"
        assert path.read_bytes() == PNG_BYTES

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "deeper" / "outputs"
        path = save_image(PNG_BYTES, output_dir=target)
        assert target.exists()
        assert path.parent == target

    def test_repeated_calls_never_collide(self, tmp_path: Path) -> None:
        paths = {save_image(PNG_BYTES, output_dir=tmp_path) for _ in range(20)}
        assert len(paths) == 20

    def test_filename_includes_name_prefix(self, tmp_path: Path) -> None:
        path = save_image(PNG_BYTES, name="upscale", output_dir=tmp_path)
        assert path.name.startswith("upscale-")
