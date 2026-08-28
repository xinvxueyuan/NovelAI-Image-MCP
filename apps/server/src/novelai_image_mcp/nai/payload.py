"""NovelAI V4+ / V5 wire payload mapping."""

from typing import Any

from .constants import Model, is_v4_model, is_v5_model, params_version_for
from .models import GenerationRequest, NovelAIGenerationPlan

# V5 replaced the integer ``ucPreset`` (0-3) with a string enum.
_UC_PRESET_IDS = ("heavy", "light", "furryFocus", "humanFocus")


def _caption(
    text: str,
    *,
    char_captions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {"caption": {"base_caption": text, "char_captions": char_captions or []}}


def build_payload(
    plan: NovelAIGenerationPlan,
    *,
    model: str,
) -> dict[str, Any]:
    """Map an already-resolved plan to NovelAI's V4.5/V5 request shape."""
    payload: dict[str, Any] = {
        "action": "generate",
        "input": plan.prompt,
        "model": model,
        "parameters": {
            "width": plan.width,
            "height": plan.height,
            "steps": plan.steps,
            "scale": plan.scale,
            "sampler": plan.sampler,
            "seed": plan.seed,
            "n_samples": 1,
            "negative_prompt": plan.negative_prompt,
            "qualityToggle": True,
            "params_version": params_version_for(Model(model)),
            "stream": "msgpack",
            "v4_prompt": _caption(
                plan.base_caption,
                char_captions=list(plan.char_captions),
            )
            | {"use_coords": plan.use_coords, "use_order": True},
            "v4_negative_prompt": _caption(plan.negative_prompt) | {"legacy_uc": False},
            "characterPrompts": list(plan.character_prompts),
            "add_original_image": True,
            "autoSmea": False,
            "cfg_rescale": 0,
            "controlnet_strength": 1,
            "dynamic_thresholding": False,
            "image_format": "png",
            "legacy": False,
            "legacy_uc": False,
            "legacy_v3_extend": False,
            "noise_schedule": "karras",
            "normalize_reference_strength_multiple": True,
            "prefer_brownian": True,
            "use_coords": plan.use_coords,
        },
    }
    if is_v5_model(Model(model)):
        payload["parameters"]["ucPresetId"] = "heavy"
        payload["parameters"]["qualityPresetId"] = "standard"
    else:
        payload["parameters"]["ucPreset"] = 0
    return payload


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def build_generation_payload(request: GenerationRequest) -> dict[str, Any]:
    """Serialize every supported generation and conditioning option."""
    prompt = request.effective_prompt
    negative_prompt = request.effective_negative_prompt
    characters = [
        {
            "prompt": item.prompt,
            "uc": item.negative_prompt,
            "center": {"x": item.x, "y": item.y},
            "enabled": item.enabled,
        }
        for item in request.character_prompts
    ]
    char_captions = [
        {
            "char_caption": item.prompt,
            "centers": [{"x": item.x, "y": item.y}],
        }
        for item in request.character_prompts
        if item.enabled
    ]
    negative_char_captions = [
        {
            "char_caption": item.negative_prompt,
            "centers": [{"x": item.x, "y": item.y}],
        }
        for item in request.character_prompts
        if item.enabled and item.negative_prompt
    ]
    parameters: dict[str, Any] = {
        "width": request.width,
        "height": request.height,
        "n_samples": request.n_samples,
        "steps": request.steps,
        "scale": request.scale,
        "sampler": _enum_value(request.sampler),
        "seed": request.seed,
        "negative_prompt": negative_prompt,
        "qualityToggle": request.quality,
        "params_version": params_version_for(request.model),
        "dynamic_thresholding": request.dynamic_thresholding,
        "cfg_rescale": request.cfg_rescale,
        "noise_schedule": _enum_value(request.noise_schedule),
        "add_original_image": request.add_original_image,
        "controlnet_strength": request.controlnet_strength,
        "characterPrompts": characters,
        "skip_cfg_above_sigma": request.skip_cfg_above_sigma,
        "legacy": request.legacy,
        "legacy_v3_extend": request.legacy_v3_extend,
    }
    if is_v5_model(request.model):
        # V5 uses string enums where older generations used ints/bools.
        parameters["ucPresetId"] = _UC_PRESET_IDS[request.uc_preset]
        parameters["qualityPresetId"] = "standard" if request.quality else "none"
        if request.straight_alpha:
            parameters["straight_alpha"] = True
    else:
        parameters["ucPreset"] = request.uc_preset
    optional: dict[str, Any] = {
        "extra_noise_seed": request.extra_noise_seed,
        "image": request.image,
        "mask": request.mask,
        "strength": request.strength,
        "noise": request.noise,
        "controlnet_condition": request.controlnet_condition,
        "controlnet_model": request.controlnet_model,
    }
    if not is_v5_model(request.model):
        # V5 clients do not send the SMEA ``sm``/``sm_dyn`` pair — autoSmea is
        # the only SMEA control (emitted in the ``is_v4_model`` block below).
        optional["sm"] = request.smea
        optional["sm_dyn"] = request.smea_dynamic
    parameters.update({
        key: value for key, value in optional.items() if value is not None
    })
    if request.references:
        parameters["reference_image_multiple"] = list(request.references)
        if request.reference_information:
            parameters["reference_information_extracted_multiple"] = list(
                request.reference_information
            )
        if request.reference_strengths:
            parameters["reference_strength_multiple"] = list(
                request.reference_strengths
            )
    if is_v4_model(request.model):
        parameters.update({
            "autoSmea": request.auto_smea,
            "normalize_reference_strength_multiple": (
                request.normalize_reference_strengths
            ),
            "deliberate_euler_ancestral_bug": (request.deliberate_euler_ancestral_bug),
            "prefer_brownian": request.prefer_brownian,
            "use_coords": request.use_coords or bool(characters),
            "legacy_uc": request.legacy_uc,
            "stream": "msgpack",
        })
        if request.inpaint_img2img_strength is not None:
            parameters["inpaintImg2ImgStrength"] = request.inpaint_img2img_strength
        parameters["v4_prompt"] = {
            "caption": {
                "base_caption": request.effective_base_caption,
                "char_captions": char_captions,
            },
            "use_coords": parameters["use_coords"],
            "use_order": request.use_order,
        }
        parameters["v4_negative_prompt"] = {
            "caption": {
                "base_caption": negative_prompt,
                "char_captions": negative_char_captions,
            },
            "legacy_uc": request.legacy_uc,
        }
    else:
        parameters["sm"] = request.smea or False
        parameters["sm_dyn"] = request.smea_dynamic or False
    return {
        "action": request.action.value,
        "input": prompt,
        "model": request.model.value,
        "parameters": parameters,
    }
