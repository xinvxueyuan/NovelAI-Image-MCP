"""Tests for ``nai.payload.build_generation_payload``."""

from __future__ import annotations

from novelai_image_mcp.nai import (
    Action,
    CharacterPrompt,
    GenerationRequest,
    Model,
    build_generation_payload,
)


def _base_request(**overrides: object) -> GenerationRequest:
    defaults: dict[str, object] = {
        "prompt": "a cat, masterpiece",
        "negative_prompt": "lowres",
        "width": 832,
        "height": 1216,
        "steps": 28,
        "scale": 5.0,
        "seed": 42,
    }
    defaults.update(overrides)
    return GenerationRequest(**defaults)  # type: ignore[arg-type]


class TestPayloadShape:
    def test_top_level_fields(self) -> None:
        request = _base_request()
        payload = build_generation_payload(request)
        assert payload["action"] == "generate"
        assert payload["input"].startswith("a cat")
        assert payload["model"] == "nai-diffusion-4-5-full"

    def test_parameters_present(self) -> None:
        request = _base_request()
        params = build_generation_payload(request)["parameters"]
        for key in ("width", "height", "steps", "scale", "sampler", "seed"):
            assert key in params
        assert params["width"] == 832
        assert params["height"] == 1216
        assert params["n_samples"] == 1

    def test_quality_toggle_propagated(self) -> None:
        request = _base_request(quality=True)
        assert build_generation_payload(request)["parameters"]["qualityToggle"] is True
        request_off = _base_request(quality=False)
        assert (
            build_generation_payload(request_off)["parameters"]["qualityToggle"]
            is False
        )


class TestV4Payload:
    def test_v4_includes_stream_and_prompt_objects(self) -> None:
        request = _base_request(model=Model.V4_5)
        params = build_generation_payload(request)["parameters"]
        assert params["stream"] == "msgpack"
        assert "v4_prompt" in params
        assert "v4_negative_prompt" in params
        assert params["v4_prompt"]["caption"]["base_caption"].startswith("a cat")

    def test_v4_character_prompts_serialize_to_wire_shape(self) -> None:
        request = _base_request(
            character_prompts=(CharacterPrompt(prompt="a girl", x=0.4, y=0.5),),
        )
        params = build_generation_payload(request)["parameters"]
        assert params["use_coords"] is True
        assert params["characterPrompts"][0]["center"] == {"x": 0.4, "y": 0.5}
        char_captions = params["v4_prompt"]["caption"]["char_captions"]
        assert len(char_captions) == 1
        assert char_captions[0]["centers"] == [{"x": 0.4, "y": 0.5}]


class TestV3Payload:
    def test_v3_omits_v4_specific_fields(self) -> None:
        request = _base_request(model=Model.V3)
        params = build_generation_payload(request)["parameters"]
        assert "v4_prompt" not in params
        assert "stream" not in params
        # V3 sm / sm_dyn default to False (not None)
        assert params["sm"] is False

    def test_v3_includes_quality_tags_in_input(self) -> None:
        request = _base_request(model=Model.V3, quality=True)
        payload = build_generation_payload(request)
        assert "best quality" in payload["input"]


class TestImg2ImgPayload:
    def test_image_strength_noise_included(self) -> None:
        request = _base_request(
            action=Action.IMG2IMG,
            image="base64-data",
            strength=0.5,
            noise=0.2,
            extra_noise_seed=12345,
        )
        params = build_generation_payload(request)["parameters"]
        assert params["image"] == "base64-data"
        assert params["strength"] == 0.5
        assert params["noise"] == 0.2
        assert params["extra_noise_seed"] == 12345


class TestReferencesPayload:
    def test_references_included_when_provided(self) -> None:
        request = _base_request(
            references=("vibe1", "vibe2"),
            reference_information=(0.7, 1.0),
        )
        params = build_generation_payload(request)["parameters"]
        assert params["reference_image_multiple"] == ["vibe1", "vibe2"]
        assert params["reference_information_extracted_multiple"] == [0.7, 1.0]


class TestV5Payload:
    def test_v5_uses_string_presets_and_params_version(self) -> None:
        request = _base_request(model=Model.V5)
        params = build_generation_payload(request)["parameters"]
        assert params["params_version"] == 4
        assert params["ucPresetId"] == "heavy"
        assert params["qualityPresetId"] == "standard"
        assert "ucPreset" not in params
        assert params["stream"] == "msgpack"
        assert "v4_prompt" in params

    def test_v5_string_preset_follows_uc_preset_index(self) -> None:
        request = _base_request(model=Model.V5, uc_preset=3)
        params = build_generation_payload(request)["parameters"]
        assert params["ucPresetId"] == "humanFocus"

    def test_v5_quality_off_maps_to_none(self) -> None:
        request = _base_request(model=Model.V5, quality=False)
        params = build_generation_payload(request)["parameters"]
        assert params["qualityPresetId"] == "none"

    def test_v5_straight_alpha_only_when_enabled(self) -> None:
        on = _base_request(model=Model.V5, straight_alpha=True)
        assert build_generation_payload(on)["parameters"]["straight_alpha"] is True
        off = _base_request(model=Model.V5)
        assert "straight_alpha" not in build_generation_payload(off)["parameters"]

    def test_v5_omits_smea_pair(self) -> None:
        request = _base_request(model=Model.V5, smea=True, smea_dynamic=True)
        params = build_generation_payload(request)["parameters"]
        assert "sm" not in params
        assert "sm_dyn" not in params

    def test_v4_5_keeps_integer_presets(self) -> None:
        request = _base_request(model=Model.V4_5)
        params = build_generation_payload(request)["parameters"]
        assert params["params_version"] == 3
        assert params["ucPreset"] == 0
        assert "ucPresetId" not in params
        assert "qualityPresetId" not in params
