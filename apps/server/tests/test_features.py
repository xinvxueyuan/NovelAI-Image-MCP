"""Tests for the insiders feature registry and its resolution rules."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from novelai_image_mcp.features import (
    EXPERIMENTAL_TOOLS,
    INSIDERS_FEATURES,
    MODEL_ROUTING,
    FeatureSpec,
    resolve_features,
)
from novelai_image_mcp.insiders import InsidersConfig, parse_insiders


class TestRegistry:
    def test_constants_use_the_canonical_spelling(self) -> None:
        assert MODEL_ROUTING == "model-routing"
        assert EXPERIMENTAL_TOOLS == "experimental-tools"

    def test_registry_holds_exactly_the_two_planned_features(self) -> None:
        assert set(INSIDERS_FEATURES) == {MODEL_ROUTING, EXPERIMENTAL_TOOLS}

    @pytest.mark.parametrize("name", [MODEL_ROUTING, EXPERIMENTAL_TOOLS])
    def test_every_spec_is_consistent_with_its_key(self, name: str) -> None:
        spec = INSIDERS_FEATURES[name]
        assert isinstance(spec, FeatureSpec)
        assert spec.name == name
        assert spec.default_enabled is True
        assert spec.summary.strip()

    def test_specs_are_frozen(self) -> None:
        spec = INSIDERS_FEATURES[MODEL_ROUTING]
        with pytest.raises(FrozenInstanceError):
            # Assign through the normal attribute protocol: ``object.__setattr__``
            # would bypass the frozen guard and silently mutate the shared registry.
            spec.default_enabled = False  # pyright: ignore[reportAttributeAccessIssue]


class TestResolveFeatures:
    def test_a_disabled_header_yields_no_features(self) -> None:
        assert resolve_features(InsidersConfig.disabled()) == frozenset()
        assert resolve_features(parse_insiders("false")) == frozenset()
        assert resolve_features(parse_insiders(None)) == frozenset()

    def test_an_enabled_header_yields_every_default(self) -> None:
        assert resolve_features(InsidersConfig(enabled=True)) == frozenset(
            {MODEL_ROUTING, EXPERIMENTAL_TOOLS},
        )
        assert resolve_features(parse_insiders("true")) == frozenset(
            {MODEL_ROUTING, EXPERIMENTAL_TOOLS},
        )

    def test_an_override_turns_a_default_off(self) -> None:
        config = InsidersConfig(enabled=True, features={MODEL_ROUTING: False})
        assert resolve_features(config) == frozenset({EXPERIMENTAL_TOOLS})

    def test_an_override_turns_a_disabled_default_on(self) -> None:
        # Both registered features default to True; the override must still be
        # the value that decides, not the default.
        config = InsidersConfig(enabled=True, features={MODEL_ROUTING: True})
        assert MODEL_ROUTING in resolve_features(config)

    def test_force_disabled_wins_over_an_explicit_enable(self) -> None:
        config = InsidersConfig(enabled=True, features={MODEL_ROUTING: True})
        assert resolve_features(config, force_disabled=[MODEL_ROUTING]) == frozenset(
            {EXPERIMENTAL_TOOLS},
        )

    def test_force_disabled_matches_any_spelling(self) -> None:
        config = InsidersConfig(enabled=True)
        assert resolve_features(config, force_disabled=["MODEL_ROUTING"]) == frozenset(
            {EXPERIMENTAL_TOOLS},
        )
        assert resolve_features(
            config, force_disabled=["Experimental_Tools"]
        ) == frozenset({MODEL_ROUTING})

    def test_force_disabled_can_turn_everything_off(self) -> None:
        config = InsidersConfig(enabled=True)
        assert resolve_features(config, force_disabled=INSIDERS_FEATURES) == frozenset()
        assert (
            resolve_features(
                config, force_disabled=["model-routing", "experimental-tools"]
            )
            == frozenset()
        )

    def test_force_disabled_is_ignored_for_unknown_names(self) -> None:
        config = InsidersConfig(enabled=True)
        assert resolve_features(config, force_disabled=["not-a-feature"]) == frozenset(
            {MODEL_ROUTING, EXPERIMENTAL_TOOLS},
        )

    def test_unregistered_keys_never_take_effect(self) -> None:
        config = InsidersConfig(
            enabled=True,
            features={"not-a-feature": True, EXPERIMENTAL_TOOLS: False},
        )
        active = resolve_features(config)
        assert active == frozenset({MODEL_ROUTING})
        assert "not-a-feature" not in active

    def test_unregistered_keys_from_the_header_never_take_effect(self) -> None:
        config = parse_insiders("not-a-feature=true")
        assert config.unknown_keys == frozenset({"not-a-feature"})
        assert resolve_features(config) == frozenset(
            {MODEL_ROUTING, EXPERIMENTAL_TOOLS},
        )

    def test_parsed_header_drives_resolution(self) -> None:
        config = parse_insiders("experimental-tools=false")
        assert resolve_features(config) == frozenset({MODEL_ROUTING})
        assert (
            resolve_features(
                parse_insiders("model-routing=false, experimental-tools=false"),
            )
            == frozenset()
        )

    def test_resolution_is_deterministic(self) -> None:
        config = parse_insiders("model-routing=false")
        assert resolve_features(config) == resolve_features(config)
