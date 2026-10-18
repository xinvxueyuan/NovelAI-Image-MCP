"""Tests for the experimental ``X-MCP-Insiders`` header parser."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from novelai_image_mcp.insiders import (
    INSIDERS_HEADER,
    InsidersConfig,
    parse_insiders,
)


class TestDisabledHeader:
    def test_header_name_constant(self) -> None:
        assert INSIDERS_HEADER == "X-MCP-Insiders"

    def test_missing_header_is_disabled(self) -> None:
        config = parse_insiders(None)
        assert config.enabled is False
        assert config.features == {}
        assert config.unknown_keys == frozenset()
        assert config.malformed == frozenset()

    @pytest.mark.parametrize(
        "raw",
        ["", "   ", "false", "FALSE", "False", "0", "off", "OFF", "no", "No"],
    )
    def test_falsy_header_is_disabled(self, raw: str) -> None:
        config = parse_insiders(raw)
        assert config.enabled is False
        assert config.features == {}
        assert config.unknown_keys == frozenset()
        assert config.malformed == frozenset()

    def test_a_bare_falsy_entry_disables_the_whole_header(self) -> None:
        # Order-independent: any bare falsy token switches the surface off,
        # even when another entry tried to switch it on.
        assert parse_insiders("model-routing=true, false").enabled is False
        assert parse_insiders("false, model-routing=true").enabled is False

    def test_separators_without_entries_do_not_enable(self) -> None:
        assert parse_insiders(",,,").enabled is False
        assert parse_insiders(" , , ").enabled is False

    def test_disabled_classmethod_matches_a_missing_header(self) -> None:
        assert InsidersConfig.disabled() == parse_insiders(None)
        assert InsidersConfig.disabled() == parse_insiders("off")

    def test_config_is_frozen(self) -> None:
        config = InsidersConfig.disabled()
        with pytest.raises(FrozenInstanceError):
            # Assign through the normal attribute protocol: ``object.__setattr__``
            # would bypass the frozen guard entirely.
            config.enabled = True  # pyright: ignore[reportAttributeAccessIssue]


class TestEnabledHeader:
    @pytest.mark.parametrize(
        "raw",
        ["true", "TRUE", "True", "1", "on", "ON", "yes", "Yes", "  true  "],
    )
    def test_bare_truthy_enables_with_defaults(self, raw: str) -> None:
        config = parse_insiders(raw)
        assert config.enabled is True
        assert config.features == {}
        assert config.unknown_keys == frozenset()
        assert config.malformed == frozenset()

    @pytest.mark.parametrize("value", ["true", "TRUE", "1", "on", "yes"])
    def test_key_value_true_overrides_to_true(self, value: str) -> None:
        config = parse_insiders(f"model-routing={value}")
        assert config.enabled is True
        assert config.features == {"model-routing": True}

    @pytest.mark.parametrize("value", ["false", "FALSE", "0", "off", "no"])
    def test_key_value_false_overrides_to_false(self, value: str) -> None:
        config = parse_insiders(f"model-routing={value}")
        assert config.enabled is True
        assert config.features == {"model-routing": False}

    def test_bare_key_overrides_to_true(self) -> None:
        config = parse_insiders("model-routing")
        assert config.enabled is True
        assert config.features == {"model-routing": True}

    def test_bare_key_keeps_the_other_defaults(self) -> None:
        config = parse_insiders("model-routing")
        assert "experimental-tools" not in config.features

    def test_keys_are_case_insensitive_and_separator_agnostic(self) -> None:
        assert parse_insiders("MODEL_ROUTING=FALSE").features == {
            "model-routing": False,
        }
        assert parse_insiders("Model-Routing=Off").features == {
            "model-routing": False,
        }
        assert parse_insiders("Model_Routing").features == {"model-routing": True}

    def test_multiple_entries_are_applied_individually(self) -> None:
        config = parse_insiders("model-routing=false, experimental-tools=false")
        assert config.enabled is True
        assert config.features == {
            "model-routing": False,
            "experimental-tools": False,
        }

    def test_extra_separators_and_empty_items_are_skipped(self) -> None:
        config = parse_insiders(" , model-routing=false ,, experimental-tools=1 , ")
        assert config.enabled is True
        assert config.features == {
            "model-routing": False,
            "experimental-tools": True,
        }
        assert config.malformed == frozenset()

    def test_the_last_override_wins(self) -> None:
        config = parse_insiders("model-routing=true, model-routing=false")
        assert config.features == {"model-routing": False}


class TestDiagnostics:
    def test_unknown_key_is_reported_and_ignored(self) -> None:
        config = parse_insiders("nope=true")
        assert config.enabled is True
        assert config.unknown_keys == frozenset({"nope"})
        assert config.features == {}

    def test_unknown_bare_key_is_reported_and_ignored(self) -> None:
        config = parse_insiders("nope")
        assert config.enabled is True
        assert config.unknown_keys == frozenset({"nope"})
        assert config.features == {}

    def test_unknown_keys_are_normalised(self) -> None:
        assert parse_insiders("No_Pe=1").unknown_keys == frozenset({"no-pe"})

    def test_an_unknown_key_never_hides_a_known_one(self) -> None:
        config = parse_insiders("bogus=1, model-routing=false")
        assert config.features == {"model-routing": False}
        assert config.unknown_keys == frozenset({"bogus"})
        assert config.malformed == frozenset()

    @pytest.mark.parametrize(
        "raw",
        ["model-routing=maybe", "model-routing=", "=true", "model-routing=2"],
    )
    def test_malformed_entry_is_reported_and_ignored(self, raw: str) -> None:
        config = parse_insiders(raw)
        assert config.malformed == frozenset({raw})
        assert config.features == {}
        assert config.unknown_keys == frozenset()

    def test_a_malformed_entry_does_not_switch_off_the_header(self) -> None:
        # A typo drops that override; it must not disable a surface the client
        # asked for, and it must never raise.
        config = parse_insiders("model-routing=maybe")
        assert config.enabled is True
        assert config.features == {}

    def test_a_malformed_entry_does_not_disturb_a_valid_one(self) -> None:
        config = parse_insiders("true, model-routing=maybe")
        assert config.enabled is True
        assert config.features == {}
        assert config.malformed == frozenset({"model-routing=maybe"})


class TestLengthLimit:
    def test_over_long_header_is_disabled_and_recorded(self) -> None:
        raw = "model-routing=false," + "x" * 4096
        config = parse_insiders(raw)
        assert config.enabled is False
        assert config.features == {}
        assert config.malformed == frozenset({"header-too-long"})

    def test_the_limit_is_inclusive(self) -> None:
        assert parse_insiders("true", max_length=4).enabled is True
        assert parse_insiders("true", max_length=3).enabled is False
        assert parse_insiders("true", max_length=3).malformed == frozenset(
            {"header-too-long"},
        )

    def test_the_limit_counts_the_raw_header(self) -> None:
        assert parse_insiders("  true  ", max_length=8).enabled is True
        assert parse_insiders("  true  ", max_length=7).enabled is False


class TestPureLogic:
    def test_parsing_never_raises_on_hostile_input(self) -> None:
        for raw in [
            "\x00",
            "=" * 10,
            "model-routing=" + "\u00e9" * 100,
            ",,,,,",
            "a" * 100_000,
        ]:
            assert isinstance(parse_insiders(raw), InsidersConfig)

    def test_result_is_stable_for_repeated_calls(self) -> None:
        first = parse_insiders("model-routing=false")
        second = parse_insiders("model-routing=false")
        assert first == second
        assert first.features == second.features
