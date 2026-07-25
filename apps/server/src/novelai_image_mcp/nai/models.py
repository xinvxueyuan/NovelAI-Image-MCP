"""Pure value objects shared by the NovelAI generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
import secrets

from .constants import (
    QUALITY_TAGS,
    UC_PRESETS,
    Action,
    Model,
    NoiseSchedule,
    Sampler,
    is_inpaint_model,
)

_MIN_COORD = 0.1
_MAX_COORD = 0.9
_MAX_SEED = 2**32 - 1
_NEGATIVE_SEPARATOR = re.compile(r"[,\n]+")


def _as_tuple[T](values: tuple[T, ...]) -> tuple[T, ...]:
    return tuple(values)


def normalize_tags(values: tuple[str, ...]) -> tuple[str, ...]:
    """Trim tags and remove case-insensitive duplicates while preserving order."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return tuple(result)


def normalize_negative_prompt(value: str | None) -> tuple[str, ...]:
    """Split comma/newline negative prompt text into normalized tags."""
    if not value:
        return ()
    return normalize_tags(tuple(_NEGATIVE_SEPARATOR.split(value)))


def _validate_seed(seed: int | None) -> None:
    if seed is not None and not 0 <= seed <= _MAX_SEED:
        raise ValueError("seed must be an unsigned 32-bit integer")


@dataclass(frozen=True, slots=True)
class PositionCoord:
    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", max(_MIN_COORD, min(_MAX_COORD, self.x)))
        object.__setattr__(self, "y", max(_MIN_COORD, min(_MAX_COORD, self.y)))


@dataclass(frozen=True, slots=True)
class CharacterIntent:
    description: str
    tags: tuple[str, ...]
    negative_tags: tuple[str, ...]
    center: PositionCoord

    def __post_init__(self) -> None:
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "tags", normalize_tags(tuple(self.tags)))
        object.__setattr__(
            self,
            "negative_tags",
            normalize_tags(tuple(self.negative_tags)),
        )


@dataclass(frozen=True, slots=True)
class GenerationHints:
    width: int | None = None
    height: int | None = None
    steps: int | None = None
    scale: float | None = None
    sampler: str | None = None
    seed: int | None = None
    negative_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "negative_tags",
            normalize_tags(tuple(self.negative_tags)),
        )


@dataclass(frozen=True, slots=True)
class PromptIntent:
    source_language: str
    english_description: str
    base_tags: tuple[str, ...]
    generation: GenerationHints
    characters: tuple[CharacterIntent, ...]
    search_required: bool
    search_query: str | None
    search_reason: str | None

    def __post_init__(self) -> None:
        description = self.english_description.strip()
        if not description:
            raise ValueError("english_description must not be empty")
        object.__setattr__(self, "source_language", self.source_language.strip())
        object.__setattr__(self, "english_description", description)
        object.__setattr__(self, "base_tags", normalize_tags(tuple(self.base_tags)))
        object.__setattr__(self, "characters", tuple(self.characters))


@dataclass(frozen=True, slots=True)
class VisualResearch:
    facts: tuple[str, ...]
    sources: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "facts", normalize_tags(tuple(self.facts)))
        object.__setattr__(self, "sources", normalize_tags(tuple(self.sources)))


@dataclass(frozen=True, slots=True)
class TipoRequest:
    description: str
    tags: tuple[str, ...]
    visual_facts: tuple[str, ...]
    seed: int

    def __post_init__(self) -> None:
        _validate_seed(self.seed)
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "tags", normalize_tags(tuple(self.tags)))
        object.__setattr__(
            self,
            "visual_facts",
            normalize_tags(tuple(self.visual_facts)),
        )


@dataclass(frozen=True, slots=True)
class TipoPrompt:
    natural_language: str
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "natural_language", self.natural_language.strip())
        object.__setattr__(self, "tags", normalize_tags(tuple(self.tags)))


@dataclass(frozen=True, slots=True)
class GenerationOverrides:
    width: int | None = None
    height: int | None = None
    steps: int | None = None
    scale: float | None = None
    sampler: str | None = None
    seed: int | None = None
    negative_prompt: str | None = None


@dataclass(frozen=True, slots=True)
class NovelAIGenerationPlan:
    prompt: str
    negative_prompt: str
    width: int
    height: int
    steps: int
    scale: float
    sampler: str
    seed: int
    base_caption: str
    char_captions: tuple[dict[str, object], ...]
    character_prompts: tuple[dict[str, object], ...]
    use_coords: bool

    def __post_init__(self) -> None:
        _validate_seed(self.seed)
        object.__setattr__(self, "char_captions", _as_tuple(self.char_captions))
        object.__setattr__(
            self,
            "character_prompts",
            _as_tuple(self.character_prompts),
        )


@dataclass(frozen=True, slots=True)
class CharacterPrompt:
    prompt: str
    negative_prompt: str = ""
    x: float = 0.5
    y: float = 0.5
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("character prompt must not be empty")
        if not 0.1 <= self.x <= 0.9 or not 0.1 <= self.y <= 0.9:
            raise ValueError("character coordinates must be between 0.1 and 0.9")


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Complete NovelAI generation request independent of the chat planner."""

    prompt: str
    base_caption: str | None = None
    model: Model = Model.V4_5
    action: Action = Action.GENERATE
    negative_prompt: str = ""
    width: int = 832
    height: int = 1216
    n_samples: int = 1
    steps: int = 28
    scale: float = 5.0
    sampler: Sampler | str = Sampler.EULER_ANCESTRAL
    seed: int = 0
    extra_noise_seed: int | None = None
    noise_schedule: NoiseSchedule | str = NoiseSchedule.KARRAS
    quality: bool = True
    uc_preset: int = 0
    dynamic_thresholding: bool = False
    cfg_rescale: float = 0.0
    smea: bool | None = None
    smea_dynamic: bool | None = None
    auto_smea: bool = False
    image: str | None = None
    mask: str | None = None
    strength: float | None = None
    noise: float | None = None
    add_original_image: bool = True
    controlnet_strength: float = 1.0
    controlnet_condition: str | None = None
    controlnet_model: str | None = None
    references: tuple[str, ...] = ()
    reference_information: tuple[float, ...] = ()
    reference_strengths: tuple[float, ...] = ()
    character_prompts: tuple[CharacterPrompt, ...] = ()
    use_coords: bool = False
    use_order: bool = True
    legacy_uc: bool = False
    normalize_reference_strengths: bool = True
    deliberate_euler_ancestral_bug: bool = False
    prefer_brownian: bool = True
    skip_cfg_above_sigma: int | None = None
    legacy: bool = False
    legacy_v3_extend: bool = False
    inpaint_img2img_strength: int | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.base_caption is not None and not self.base_caption.strip():
            raise ValueError("base_caption must not be empty when provided")
        _validate_seed(self.seed)
        if not 1 <= self.n_samples <= 8:
            raise ValueError("n_samples must be between 1 and 8")
        if not 1 <= self.steps <= 50:
            raise ValueError("steps must be between 1 and 50")
        if not 0 <= self.uc_preset <= 3:
            raise ValueError("uc_preset must be between 0 and 3")
        if not 64 <= self.width <= 49_152 or not 64 <= self.height <= 49_152:
            raise ValueError("image dimensions must be between 64 and 49152")
        object.__setattr__(self, "width", (self.width + 63) // 64 * 64)
        object.__setattr__(self, "height", (self.height + 63) // 64 * 64)
        if self.width * self.height > 3_047_424:
            raise ValueError("total resolution exceeds NovelAI's limit")
        if self.n_samples > self.max_samples:
            raise ValueError("n_samples exceeds the resolution-specific limit")
        if self.action in {Action.IMG2IMG, Action.INPAINT} and not self.image:
            raise ValueError("image-conditioned actions require an image")
        if self.action in {Action.IMG2IMG, Action.INPAINT}:
            if self.strength is None:
                object.__setattr__(self, "strength", 0.3)
            if self.noise is None:
                object.__setattr__(self, "noise", 0.0)
            if self.extra_noise_seed is None:
                object.__setattr__(
                    self, "extra_noise_seed", secrets.randbelow(2**32 - 7)
                )
        if (
            self.model in {Model.V4_5, Model.V4_5_INPAINT}
            and self.inpaint_img2img_strength is None
        ):
            object.__setattr__(self, "inpaint_img2img_strength", 1)
        if self.action is Action.INPAINT:
            if not self.mask:
                raise ValueError("inpainting requires a mask")
            if not is_inpaint_model(self.model):
                raise ValueError("inpainting requires an inpainting model")
        if self.strength is not None and not 0.01 <= self.strength <= 0.99:
            raise ValueError("strength must be between 0.01 and 0.99")
        if self.noise is not None and not 0 <= self.noise <= 0.99:
            raise ValueError("noise must be between 0 and 0.99")
        if not 0.1 <= self.controlnet_strength <= 2:
            raise ValueError("controlnet_strength must be between 0.1 and 2")
        if not 0 <= self.cfg_rescale <= 1:
            raise ValueError("cfg_rescale must be between 0 and 1")
        if self.reference_strengths and len(self.reference_strengths) != len(
            self.references
        ):
            raise ValueError("reference strengths must match references")
        if self.reference_information and len(self.reference_information) != len(
            self.references
        ):
            raise ValueError("reference information must match references")
        if any(not 0.01 <= value <= 1 for value in self.reference_strengths):
            raise ValueError("reference strengths must be between 0.01 and 1")
        if any(not 0.01 <= value <= 1 for value in self.reference_information):
            raise ValueError("reference information must be between 0.01 and 1")

    @property
    def effective_prompt(self) -> str:
        if not self.quality:
            return self.prompt
        return _merge_csv(self.prompt, QUALITY_TAGS[self.model])

    @property
    def effective_base_caption(self) -> str:
        base = self.base_caption or self.prompt
        if not self.quality:
            return base
        return _merge_csv(base, QUALITY_TAGS[self.model])

    @property
    def effective_negative_prompt(self) -> str:
        preset = UC_PRESETS[self.model][self.uc_preset]
        return _merge_csv(preset, self.negative_prompt)

    @property
    def max_samples(self) -> int:
        resolution = self.width * self.height
        if resolution <= 512 * 704:
            return 8
        if resolution <= 640 * 640:
            return 6
        if resolution <= 1_024 * 3_072:
            if resolution <= 1_310_720:
                return 4
            if resolution <= 1_572_864:
                return 2
            return 1
        return 0

    def estimate_anlas_cost(self, *, opus: bool = False) -> int:
        """Estimate provider Anlas cost using the public web-client formula."""
        resolution = max(self.width * self.height, 65_536)
        normal_portrait = 832 * 1_216
        normal_square = 1_024 * 1_024
        if normal_portrait < resolution <= normal_square:
            resolution = normal_portrait
        smea_factor = 1.0
        if self.model.value.startswith("nai-diffusion-4") and self.auto_smea:
            smea_factor = 1.2
        elif self.smea_dynamic:
            smea_factor = 1.4
        elif self.smea:
            smea_factor = 1.2
        strength = (
            self.strength
            if self.action is Action.IMG2IMG and self.strength is not None
            else 1.0
        )
        per_sample = math.ceil(
            math.ceil(
                2.951823174884865e-6 * resolution
                + 5.753298233447344e-7 * resolution * self.steps
            )
            * smea_factor
            * strength
        )
        per_sample = max(per_sample, 2)
        free_sample = opus and self.steps <= 28 and resolution <= normal_square
        return per_sample * (self.n_samples - int(free_sample))


def _merge_csv(*values: str) -> str:
    tags: list[str] = []
    seen: set[str] = set()
    for value in values:
        for raw_tag in value.split(","):
            tag = raw_tag.strip()
            key = tag.casefold()
            if tag and key not in seen:
                tags.append(tag)
                seen.add(key)
    return ", ".join(tags)
