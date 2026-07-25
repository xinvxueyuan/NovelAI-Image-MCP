"""Tests for the value objects in ``nai.models``."""

from __future__ import annotations

import pytest

from novelai_image_mcp.nai import (
    Action,
    CharacterPrompt,
    GenerationRequest,
    Model,
)


class TestGenerationRequest:
    @pytest.mark.parametrize(
        ("width", "height"),
        [(832, 1216), (1024, 1024), (512, 512), (768, 768)],
    )
    def test_dimensions_rounded_up_to_64(self, width: int, height: int) -> None:
        request = GenerationRequest(
            prompt="test",
            width=width,
            height=height,
        )
        assert request.width % 64 == 0
        assert request.height % 64 == 0

    def test_default_model_is_v4_5(self) -> None:
        request = GenerationRequest(prompt="test")
        assert request.model is Model.V4_5

    def test_default_action_is_generate(self) -> None:
        request = GenerationRequest(prompt="test")
        assert request.action is Action.GENERATE

    def test_empty_prompt_rejected(self) -> None:
        with pytest.raises(ValueError, match="prompt must not be empty"):
            GenerationRequest(prompt="   ")

    @pytest.mark.parametrize("seed", [-1, 2**32])
    def test_invalid_seed_rejected(self, seed: int) -> None:
        with pytest.raises(ValueError, match="seed must be"):
            GenerationRequest(prompt="test", seed=seed)

    @pytest.mark.parametrize("n_samples", [0, 9])
    def test_invalid_n_samples_rejected(self, n_samples: int) -> None:
        with pytest.raises(ValueError, match="n_samples must be"):
            GenerationRequest(prompt="test", n_samples=n_samples)

    @pytest.mark.parametrize("steps", [0, 51])
    def test_invalid_steps_rejected(self, steps: int) -> None:
        with pytest.raises(ValueError, match="steps must be"):
            GenerationRequest(prompt="test", steps=steps)

    def test_img2img_requires_image(self) -> None:
        with pytest.raises(ValueError, match="image-conditioned actions require"):
            GenerationRequest(prompt="test", action=Action.IMG2IMG)

    def test_inpaint_requires_mask(self) -> None:
        with pytest.raises(ValueError, match="inpainting requires a mask"):
            GenerationRequest(
                prompt="test",
                action=Action.INPAINT,
                image="base64",
                model=Model.V4_5_INPAINT,
            )

    def test_inpaint_requires_inpaint_model(self) -> None:
        with pytest.raises(ValueError, match="inpainting requires an inpainting"):
            GenerationRequest(
                prompt="test",
                action=Action.INPAINT,
                image="base64",
                mask="base64",
                model=Model.V4_5,
            )

    def test_img2img_auto_fills_strength_and_noise(self) -> None:
        request = GenerationRequest(
            prompt="test",
            action=Action.IMG2IMG,
            image="base64",
        )
        assert request.strength == 0.3
        assert request.noise == 0.0
        assert request.extra_noise_seed is not None

    @pytest.mark.parametrize("strength", [0.0, 1.0])
    def test_invalid_strength_rejected(self, strength: float) -> None:
        with pytest.raises(ValueError, match="strength must be"):
            GenerationRequest(
                prompt="test",
                action=Action.IMG2IMG,
                image="base64",
                strength=strength,
            )

    def test_high_resolution_rejected(self) -> None:
        # 49152 × 64 = exactly the per-side max but the product exceeds the
        # 3_047_424 total-resolution cap.
        with pytest.raises(ValueError, match="total resolution exceeds"):
            GenerationRequest(prompt="test", width=49_152, height=64)


class TestEffectivePrompts:
    def test_quality_toggle_appends_quality_tags(self) -> None:
        request = GenerationRequest(prompt="a cat", quality=True)
        assert "very aesthetic" in request.effective_prompt
        assert "masterpiece" in request.effective_prompt

    def test_quality_toggle_off_passes_through(self) -> None:
        request = GenerationRequest(prompt="a cat", quality=False)
        assert request.effective_prompt == "a cat"

    def test_negative_prompt_merges_uc_preset(self) -> None:
        request = GenerationRequest(
            prompt="a cat",
            negative_prompt="bad hands",
            uc_preset=0,
        )
        assert "nsfw" in request.effective_negative_prompt
        assert "bad hands" in request.effective_negative_prompt


class TestMaxSamples:
    @pytest.mark.parametrize(
        ("width", "height", "expected"),
        # Bands: <=512*704 → 8; <=640*640 → 6; <=1_310_720 → 4;
        # <=1_572_864 → 2; else → 1.
        [
            (512, 704, 8),
            (640, 640, 6),
            (832, 1216, 4),
            (1024, 1024, 4),
            (1216, 1216, 2),
        ],
    )
    def test_max_samples_by_resolution(
        self, width: int, height: int, expected: int
    ) -> None:
        request = GenerationRequest(prompt="test", width=width, height=height)
        assert request.max_samples == expected


class TestEstimateAnlasCost:
    def test_opus_free_sample_at_normal_resolution(self) -> None:
        request = GenerationRequest(prompt="test", width=832, height=1216, steps=28)
        cost = request.estimate_anlas_cost(opus=True)
        assert cost == 0  # within opus free-sample limits

    def test_non_opus_costs_anlas(self) -> None:
        request = GenerationRequest(prompt="test", width=832, height=1216, steps=28)
        cost = request.estimate_anlas_cost(opus=False)
        assert cost > 0

    def test_smea_multiplies_cost(self) -> None:
        base = GenerationRequest(prompt="test", width=832, height=1216)
        smea = GenerationRequest(prompt="test", width=832, height=1216, smea=True)
        # Only applies when autoSmea is off and model is V4.x — V4_5 + smea=True
        # takes the smea=True branch (factor 1.2).
        assert smea.estimate_anlas_cost() >= base.estimate_anlas_cost()

    def test_img2img_strength_scales_cost(self) -> None:
        full = GenerationRequest(
            prompt="test",
            action=Action.IMG2IMG,
            image="base64",
            strength=0.99,
        )
        partial = GenerationRequest(
            prompt="test",
            action=Action.IMG2IMG,
            image="base64",
            strength=0.1,
        )
        assert full.estimate_anlas_cost() >= partial.estimate_anlas_cost()


class TestCharacterPrompt:
    def test_default_center(self) -> None:
        cp = CharacterPrompt(prompt="a girl")
        assert cp.x == 0.5
        assert cp.y == 0.5

    def test_empty_prompt_rejected(self) -> None:
        with pytest.raises(ValueError, match="character prompt must not be empty"):
            CharacterPrompt(prompt="   ")

    @pytest.mark.parametrize(
        ("x", "y"),
        [(0.0, 0.5), (1.0, 0.5), (0.5, 0.0), (0.5, 1.0)],
    )
    def test_out_of_range_coords_rejected(self, x: float, y: float) -> None:
        with pytest.raises(ValueError, match="character coordinates"):
            CharacterPrompt(prompt="a girl", x=x, y=y)
