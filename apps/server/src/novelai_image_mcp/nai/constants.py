"""NovelAI protocol constants and model capability helpers."""

from enum import IntEnum, StrEnum


class Endpoint(StrEnum):
    """NovelAI API path constants.

    Most paths are rooted at ``https://image.novelai.net`` (the consolidated
    third-party host). Two exceptions — ``UPSCALE`` and ``ANNOTATE`` — were not
    migrated to ``image.novelai.net`` and remain on the Primary API at
    ``https://api.novelai.net``. The Primary API's docs
    (https://api.novelai.net/docs/) state that third-party users may use its
    ``/ai/`` routes. See ``NovelAIClient.legacy_image_base_url``.

    The ``/ai/generate-image`` family is split by model generation:

    * ``IMAGE`` (``/ai/generate-image``) — used by V3 / Furry legacy models.
      Returns a ZIP archive (``application/zip``) with HTTP 201.
    * ``IMAGE_STREAM`` (``/ai/generate-image-stream``) — used by V4 / V4.5 /
      V5 new models. Returns a MessagePack stream (``stream: "msgpack"``) with
      HTTP 200. The selection is driven by ``is_v4_model`` in ``client.py``.
    """

    LOGIN = "/user/login"
    USER_DATA = "/user/data"
    SUBSCRIPTION = "/user/subscription"
    IMAGE = "/ai/generate-image"
    IMAGE_STREAM = "/ai/generate-image-stream"
    DIRECTOR = "/ai/augment-image"
    ENCODE_VIBE = "/ai/encode-vibe"
    UPSCALE = "/ai/upscale"
    ANNOTATE = "/ai/annotate-image"
    SUGGEST_TAGS = "/ai/generate-image/suggest-tags"


class Model(StrEnum):
    V3 = "nai-diffusion-3"
    V3_INPAINT = "nai-diffusion-3-inpainting"
    FURRY = "nai-diffusion-furry-3"
    FURRY_INPAINT = "nai-diffusion-furry-3-inpainting"
    V4 = "nai-diffusion-4-full"
    V4_INPAINT = "nai-diffusion-4-full-inpainting"
    V4_CURATED = "nai-diffusion-4-curated-preview"
    V4_CURATED_INPAINT = "nai-diffusion-4-curated-inpainting"
    V4_5 = "nai-diffusion-4-5-full"
    V4_5_INPAINT = "nai-diffusion-4-5-full-inpainting"
    V4_5_CURATED = "nai-diffusion-4-5-curated"
    V4_5_CURATED_INPAINT = "nai-diffusion-4-5-curated-inpainting"
    V5 = "nai-diffusion-5-full"
    V5_CURATED = "nai-diffusion-5-curated"
    V5_INPAINT = "nai-diffusion-5-full-inpainting"


class Action(StrEnum):
    GENERATE = "generate"
    IMG2IMG = "img2img"
    INPAINT = "infill"


class Sampler(StrEnum):
    EULER = "k_euler"
    EULER_ANCESTRAL = "k_euler_ancestral"
    DPM_2S_ANCESTRAL = "k_dpmpp_2s_ancestral"
    DPM_2M = "k_dpmpp_2m"
    DPM_2M_SDE = "k_dpmpp_2m_sde"
    DPM_SDE = "k_dpmpp_sde"
    DDIM = "ddim_v3"


class NoiseSchedule(StrEnum):
    NATIVE = "native"
    KARRAS = "karras"
    EXPONENTIAL = "exponential"
    POLYEXPONENTIAL = "polyexponential"


class ControlNetModel(StrEnum):
    PALETTE_SWAP = "hed"
    FORM_LOCK = "midas"
    SCRIBBLER = "fake_scribble"
    BUILDING_CONTROL = "mlsd"
    LANDSCAPER = "uniformer"


class DirectorTool(StrEnum):
    LINE_ART = "lineart"
    SKETCH = "sketch"
    BACKGROUND_REMOVAL = "bg-removal"
    DECLUTTER = "declutter"
    COLORIZE = "colorize"
    EMOTION = "emotion"


class Emotion(StrEnum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SCARED = "scared"
    SURPRISED = "surprised"
    TIRED = "tired"
    EXCITED = "excited"
    NERVOUS = "nervous"
    THINKING = "thinking"
    CONFUSED = "confused"
    SHY = "shy"
    DISGUSTED = "disgusted"
    SMUG = "smug"
    BORED = "bored"
    LAUGHING = "laughing"
    IRRITATED = "irritated"
    AROUSED = "aroused"
    EMBARRASSED = "embarrassed"
    WORRIED = "worried"
    LOVE = "love"
    DETERMINED = "determined"
    HURT = "hurt"
    PLAYFUL = "playful"


class EmotionLevel(IntEnum):
    NORMAL = 0
    SLIGHTLY_WEAK = 1
    WEAK = 2
    EVEN_WEAKER = 3
    VERY_WEAK = 4
    WEAKEST = 5


_V4_MODELS = frozenset({
    Model.V4,
    Model.V4_INPAINT,
    Model.V4_CURATED,
    Model.V4_CURATED_INPAINT,
    Model.V4_5,
    Model.V4_5_INPAINT,
    Model.V4_5_CURATED,
    Model.V4_5_CURATED_INPAINT,
    Model.V5,
    Model.V5_CURATED,
    Model.V5_INPAINT,
})
_V5_MODELS = frozenset({
    Model.V5,
    Model.V5_CURATED,
    Model.V5_INPAINT,
})
_INPAINT_MODELS = frozenset({
    Model.V3_INPAINT,
    Model.FURRY_INPAINT,
    Model.V4_INPAINT,
    Model.V4_CURATED_INPAINT,
    Model.V4_5_INPAINT,
    Model.V4_5_CURATED_INPAINT,
    Model.V5_INPAINT,
})


def is_v4_model(model: Model) -> bool:
    """True for structured-prompt (V4+) models: V4 / V4.5 / V5 families.

    These use the ``/ai/generate-image-stream`` endpoint (MessagePack) and the
    ``v4_prompt`` / ``v4_negative_prompt`` caption payload shape. The name is
    retained for backward compatibility (public ``nai`` API).
    """
    return model in _V4_MODELS


def is_v5_model(model: Model) -> bool:
    """True for NovelAI Diffusion V5 models (Full / Curated / Inpainting)."""
    return model in _V5_MODELS


def supports_vibe(model: Model) -> bool:
    """True when vibe transfer (reference images) works for this model.

    Vibe transfer is available on V4 / V4.5 only — V3 / Furry and V5 (feature
    not yet released for V5 per the official announcement) return False.
    """
    return model in _V4_MODELS and not is_v5_model(model)


def is_inpaint_model(model: Model) -> bool:
    return model in _INPAINT_MODELS


def params_version_for(model: Model) -> int:
    """Return the NovelAI ``params_version`` for a model.

    V5 clients ship both ``3`` (Marinara-Engine) and ``4`` (Auto-NovelAI,
    SDlab) and the API tolerates either; this project sends ``4`` for V5 (the
    value used by the most recent third-party implementations) and ``3`` for
    older generations, pending live verification.
    """
    return 4 if is_v5_model(model) else 3


QUALITY_TAGS: dict[Model, str] = {
    # V5 quality tags reuse the V4.5 baseline for now — early community
    # reports say V4.5 tags do not transfer perfectly to V5 (paler, more
    # painterly); tune after live tests (TODO-live-tune).
    Model.V5: "very aesthetic, masterpiece, no text",
    Model.V5_INPAINT: "very aesthetic, masterpiece, no text",
    Model.V5_CURATED: "location, masterpiece, no text, -0.8::feet::, rating:general",
    Model.V4_5: "very aesthetic, masterpiece, no text",
    Model.V4_5_INPAINT: "very aesthetic, masterpiece, no text",
    Model.V4_5_CURATED: "location, masterpiece, no text, -0.8::feet::, rating:general",
    Model.V4_5_CURATED_INPAINT: (
        "location, masterpiece, no text, -0.8::feet::, rating:general"
    ),
    Model.V4: "no text, best quality, very aesthetic, absurdres",
    Model.V4_INPAINT: "no text, best quality, very aesthetic, absurdres",
    Model.V4_CURATED: "rating:general, amazing quality, very aesthetic, absurdres",
    Model.V4_CURATED_INPAINT: (
        "rating:general, amazing quality, very aesthetic, absurdres"
    ),
    Model.V3: "best quality, amazing quality, very aesthetic, absurdres",
    Model.V3_INPAINT: "best quality, amazing quality, very aesthetic, absurdres",
    Model.FURRY: "{best quality}, {amazing quality}",
    Model.FURRY_INPAINT: "{best quality}, {amazing quality}",
}

_V45_HEAVY = (
    "nsfw, lowres, artistic error, film grain, scan artifacts, worst quality, "
    "bad quality, jpeg artifacts, very displeasing, chromatic aberration, "
    "dithering, halftone, screentone, multiple views, logo, too many watermarks, "
    "negative space, blank page"
)
_V45_LIGHT = (
    "nsfw, lowres, artistic error, scan artifacts, worst quality, bad quality, "
    "jpeg artifacts, multiple views, very displeasing, too many watermarks, "
    "negative space, blank page"
)
_V45_FURRY = (
    "nsfw, {worst quality}, distracting watermark, unfinished, bad quality, "
    "{widescreen}, upscale, {sequence}, {{grandfathered content}}, blurred "
    "foreground, chromatic aberration, sketch, everyone, [sketch background], "
    "simple, [flat colors], ych (character), outline, multiple scenes, "
    "[[horror (theme)]], comic"
)
_V45_HUMAN = _V45_HEAVY + ", @_@, mismatched pupils, glowing eyes, bad anatomy"
_V45_CURATED_HEAVY = (
    "blurry, lowres, upscaled, artistic error, film grain, scan artifacts, worst "
    "quality, bad quality, jpeg artifacts, very displeasing, chromatic aberration, "
    "halftone, multiple views, logo, too many watermarks, negative space, blank page"
)
_V45_CURATED_LIGHT = (
    "blurry, lowres, upscaled, artistic error, scan artifacts, jpeg artifacts, "
    "logo, too many watermarks, negative space, blank page"
)
_V45_CURATED_FOCUS = (
    "blurry, lowres, upscaled, artistic error, film grain, scan artifacts, bad "
    "anatomy, bad hands, worst quality, bad quality, jpeg artifacts, very "
    "displeasing, chromatic aberration, halftone, multiple views, logo, too many "
    "watermarks, @_@, mismatched pupils, glowing eyes, negative space, blank page"
)
_V4_HEAVY = (
    "blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, "
    "jpeg artifacts, very displeasing, chromatic aberration, multiple views, logo, "
    "too many watermarks"
)
_V4_LIGHT = (
    "blurry, lowres, error, worst quality, bad quality, jpeg artifacts, very "
    "displeasing"
)
_V4_CURATED_HEAVY = (
    "blurry, lowres, error, film grain, scan artifacts, worst quality, bad quality, "
    "jpeg artifacts, very displeasing, chromatic aberration, logo, dated, signature, "
    "multiple views, gigantic breasts"
)
_V4_CURATED_LIGHT = (
    "blurry, lowres, error, worst quality, bad quality, jpeg artifacts, very "
    "displeasing, logo, dated, signature"
)
_V3_HEAVY = (
    "lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, "
    "bad quality, watermark, unfinished, displeasing, chromatic aberration, "
    "signature, extra digits, artistic error, username, scan, [abstract]"
)
_V3_LIGHT = "lowres, jpeg artifacts, worst quality, watermark, blurry, very displeasing"
_V3_HUMAN = (
    _V3_HEAVY
    + ", bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, "
    "glowing eyes"
)
_FURRY_HEAVY = (
    "{{worst quality}}, [displeasing], {unusual pupils}, guide lines, "
    "{{unfinished}}, {bad}, url, artist name, {{tall image}}, mosaic, {sketch "
    "page}, comic panel, impact (font), [dated], {logo}, ych, {what}, {where is "
    "your god now}, {distorted text}, repeated text, {floating head}, {1994}, "
    "{widescreen}, absolutely everyone, sequence, {compression artifacts}, hard "
    "translated, {cropped}, {commissioner name}, unknown text, high contrast"
)
_FURRY_LIGHT = (
    "{worst quality}, guide lines, unfinished, bad, url, tall image, widescreen, "
    "compression artifacts, unknown text"
)

UC_PRESETS: dict[Model, tuple[str, str, str, str]] = {
    # V5 UC presets reuse the V4.5 texts as a tuning baseline (TODO-live-tune).
    Model.V5: (_V45_HEAVY, _V45_LIGHT, _V45_FURRY, _V45_HUMAN),
    Model.V5_INPAINT: (_V45_HEAVY, _V45_LIGHT, _V45_FURRY, _V45_HUMAN),
    Model.V5_CURATED: (
        _V45_CURATED_HEAVY,
        _V45_CURATED_LIGHT,
        _V45_CURATED_FOCUS,
        "",
    ),
    Model.V4_5: (_V45_HEAVY, _V45_LIGHT, _V45_FURRY, _V45_HUMAN),
    Model.V4_5_INPAINT: (_V45_HEAVY, _V45_LIGHT, _V45_FURRY, _V45_HUMAN),
    Model.V4_5_CURATED: (
        _V45_CURATED_HEAVY,
        _V45_CURATED_LIGHT,
        _V45_CURATED_FOCUS,
        "",
    ),
    Model.V4_5_CURATED_INPAINT: (
        _V45_CURATED_HEAVY,
        _V45_CURATED_LIGHT,
        _V45_CURATED_FOCUS,
        "",
    ),
    Model.V4: (_V4_HEAVY, _V4_LIGHT, "", ""),
    Model.V4_INPAINT: (_V4_HEAVY, _V4_LIGHT, "", ""),
    Model.V4_CURATED: (_V4_CURATED_HEAVY, _V4_CURATED_LIGHT, "", ""),
    Model.V4_CURATED_INPAINT: (_V4_CURATED_HEAVY, _V4_CURATED_LIGHT, "", ""),
    Model.V3: (_V3_HEAVY, _V3_LIGHT, _V3_HUMAN, ""),
    Model.V3_INPAINT: (_V3_HEAVY, _V3_LIGHT, _V3_HUMAN, ""),
    Model.FURRY: (_FURRY_HEAVY, _FURRY_LIGHT, "", ""),
    Model.FURRY_INPAINT: (_FURRY_HEAVY, _FURRY_LIGHT, "", ""),
}
