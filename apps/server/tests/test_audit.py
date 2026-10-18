"""Tests for the append-only audit trail."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from novelai_image_mcp.audit import (
    AUDIT_FILENAME,
    DIGEST_LENGTH,
    MAX_ARGUMENT_LENGTH,
    MAX_RECORDED_HEADER_LENGTH,
    MAX_RECORDED_HEADERS,
    append_record,
    artifact_paths,
    build_record,
    cap_headers,
    digest_text,
    resolve_audit_path,
    summarise_arguments,
)
from novelai_image_mcp.routing import RoutingContext, resolve_routing

if TYPE_CHECKING:
    from collections.abc import Mapping

_LOGGER = "novelai_image_mcp.audit"


def _routing(
    *,
    enabled: bool = True,
    route: str = "team-a",
    model: str | None = "nai-diffusion-5-full",
    agent: str | None = "agent-1",
    client: str | None = "client-1",
    session: str | None = "session-1",
    recorded_headers: Mapping[str, str] | None = None,
) -> RoutingContext:
    """A routing context with every field populated unless overridden."""
    return RoutingContext(
        enabled=enabled,
        route=route,
        model=model,
        agent=agent,
        client=client,
        session=session,
        recorded_headers=recorded_headers or {},
    )


class _TextBlock:
    """Minimal stand-in for a text content block."""

    def __init__(self, text: str) -> None:
        self.text = text


class _Result:
    """Minimal stand-in for a tool result carrying content blocks."""

    def __init__(self, content: list[object]) -> None:
        self.content = content


class TestDigestText:
    def test_reports_the_length_and_a_truncated_sha256(self) -> None:
        digest = digest_text("a cat")
        assert digest["length"] == 5
        assert digest["sha256"] == hashlib.sha256(b"a cat").hexdigest()[:DIGEST_LENGTH]
        assert len(digest["sha256"]) == DIGEST_LENGTH

    def test_never_contains_the_original_text(self) -> None:
        digest = digest_text("very secret prompt")
        assert "very secret prompt" not in json.dumps(digest)

    def test_unencodable_surrogates_do_not_raise(self) -> None:
        assert digest_text("\ud800")["length"] == 1


class TestSummariseArguments:
    def test_prompts_are_reduced_to_a_digest(self) -> None:
        summary = summarise_arguments({"prompt": "a cat", "negative_prompt": "blurry"})
        assert summary["prompt"] == digest_text("a cat")
        assert summary["negative_prompt"] == digest_text("blurry")
        assert "a cat" not in json.dumps(summary)

    def test_image_arguments_are_redacted(self) -> None:
        summary = summarise_arguments({
            "image": "aGVsbG8=",
            "mask": "aGVsbG8=",
            "references": ["vibe-token"],
            "init_image": "aGVsbG8=",
        })
        assert set(summary.values()) == {"[redacted image]"}
        assert "aGVsbG8=" not in json.dumps(summary)

    def test_an_over_long_string_is_digested_under_any_name(self) -> None:
        blob = "A" * (MAX_ARGUMENT_LENGTH + 1)
        summary = summarise_arguments({"unexpected_name": blob})
        assert summary["unexpected_name"] == digest_text(blob)
        assert blob not in json.dumps(summary)

    def test_a_short_plain_string_is_kept(self) -> None:
        assert summarise_arguments({"sampler": "k_euler"}) == {"sampler": "k_euler"}

    def test_scalars_are_kept(self) -> None:
        summary = summarise_arguments({
            "steps": 28,
            "scale": 5.0,
            "smea": False,
            "seed": None,
        })
        assert summary == {"steps": 28, "scale": 5.0, "smea": False, "seed": None}

    def test_containers_are_reduced_to_their_size(self) -> None:
        summary = summarise_arguments({
            "characterPrompts": [1, 2, 3],
            "extra": {"a": 1},
        })
        assert summary == {"characterPrompts": {"items": 3}, "extra": {"keys": 1}}

    def test_unknown_objects_are_reduced_to_their_type_name(self) -> None:
        assert summarise_arguments({"weird": object()}) == {"weird": "object"}

    def test_an_empty_mapping_yields_an_empty_summary(self) -> None:
        assert summarise_arguments(None) == {}
        assert summarise_arguments({}) == {}


class TestArtifactPaths:
    def test_extracts_png_paths_from_text_blocks(self) -> None:
        result = _Result([_TextBlock("Saved 1 image(s): ['outputs/a.png']")])
        assert artifact_paths(result) == ["outputs/a.png"]

    def test_sorts_and_deduplicates(self) -> None:
        result = _Result([
            _TextBlock("b.png and a.png and b.png"),
        ])
        assert artifact_paths(result) == ["a.png", "b.png"]

    def test_returns_nothing_without_text_blocks(self) -> None:
        assert artifact_paths(_Result([])) == []
        assert artifact_paths(_Result([object()])) == []
        assert artifact_paths(object()) == []


class TestBuildRecord:
    def test_carries_every_documented_field(self) -> None:
        record = build_record(
            routing=_routing(),
            tool="generate_image",
            duration_ms=12.3456,
            outcome="ok",
            features={"model-routing", "experimental-tools"},
            artifacts=["b.png", "a.png"],
            arguments={"prompt": "a cat"},
            unknown_keys={"nope"},
            malformed={"bad"},
        )
        assert record["route"] == "team-a"
        assert record["model"] == "nai-diffusion-5-full"
        assert record["agent"] == "agent-1"
        assert record["client"] == "client-1"
        assert record["session"] == "session-1"
        assert record["tool"] == "generate_image"
        assert record["outcome"] == "ok"
        assert record["duration_ms"] == 12.346
        assert record["features"] == ["experimental-tools", "model-routing"]
        assert record["artifacts"] == ["a.png", "b.png"]
        assert record["unknown_keys"] == ["nope"]
        assert record["malformed"] == ["bad"]
        assert record["headers"] == {}

    def test_timestamps_are_utc_iso(self) -> None:
        record = build_record(
            routing=_routing(), tool="t", duration_ms=0.0, outcome="ok"
        )
        assert record["ts"].endswith("+00:00")

    def test_the_record_never_carries_a_raw_prompt(self) -> None:
        record = build_record(
            routing=_routing(),
            tool="generate_image",
            duration_ms=1.0,
            outcome="ok",
            arguments={"prompt": "a very secret prompt", "image": "aGVsbG8="},
        )
        serialised = json.dumps(record)
        assert "a very secret prompt" not in serialised
        assert "aGVsbG8=" not in serialised

    def test_the_record_is_json_serialisable(self) -> None:
        record = build_record(
            routing=_routing(), tool="t", duration_ms=0.5, outcome="error"
        )
        assert json.loads(json.dumps(record))["outcome"] == "error"


class TestResolveAuditPath:
    def test_an_explicit_path_wins(self, tmp_path: Path) -> None:
        target = tmp_path / "custom.jsonl"
        resolved = resolve_audit_path(
            audit_log_path=str(target), output_dir=tmp_path / "outputs"
        )
        assert resolved == target

    def test_the_output_directory_is_the_default(self, tmp_path: Path) -> None:
        resolved = resolve_audit_path(audit_log_path=None, output_dir=tmp_path)
        assert resolved == tmp_path / AUDIT_FILENAME

    def test_without_any_setting_the_file_is_relative(self) -> None:
        assert resolve_audit_path(audit_log_path=None) == Path(AUDIT_FILENAME)


class TestAppendRecord:
    def test_writes_one_json_line(self, tmp_path: Path) -> None:
        target = tmp_path / "audit.jsonl"
        assert append_record({"tool": "ping"}, path=target) is True
        lines = target.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0]) == {"tool": "ping"}

    def test_appends_rather_than_truncating(self, tmp_path: Path) -> None:
        target = tmp_path / "audit.jsonl"
        append_record({"n": 1}, path=target)
        append_record({"n": 2}, path=target)
        lines = target.read_text(encoding="utf-8").splitlines()
        assert [json.loads(line)["n"] for line in lines] == [1, 2]

    def test_creates_missing_parent_directories(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "deeper" / "audit.jsonl"
        assert append_record({"tool": "ping"}, path=target) is True
        assert target.is_file()

    def test_a_multiline_value_still_produces_one_line(self, tmp_path: Path) -> None:
        target = tmp_path / "audit.jsonl"
        append_record({"note": "first\nsecond"}, path=target)
        assert len(target.read_text(encoding="utf-8").splitlines()) == 1

    def test_an_unwritable_path_returns_false_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")
        with caplog.at_level("ERROR", logger=_LOGGER):
            assert (
                append_record({"tool": "ping"}, path=blocker / "audit.jsonl") is False
            )
        assert any(record.levelname == "ERROR" for record in caplog.records)

    def test_an_unserialisable_record_returns_false_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        circular: dict[str, object] = {}
        circular["self"] = circular
        with caplog.at_level("ERROR", logger=_LOGGER):
            assert append_record(circular, path=tmp_path / "audit.jsonl") is False
        assert any(record.levelname == "ERROR" for record in caplog.records)


class TestHeaderSnapshot:
    """The record carries T1's sanitised header snapshot, capped for size."""

    def test_the_record_carries_the_sanitised_headers(self) -> None:
        routing = _routing(
            recorded_headers={"x-mcp-agent-id": "team-a", "user-agent": "pytest"}
        )
        record = build_record(routing=routing, tool="t", duration_ms=0.0, outcome="ok")
        assert record["headers"] == {
            "x-mcp-agent-id": "team-a",
            "user-agent": "pytest",
        }

    def test_credential_headers_never_reach_the_record(self) -> None:
        # Built the way the routing layer builds it, so this asserts the whole
        # T1 -> T3 chain rather than a hand-written snapshot.
        routing = resolve_routing(
            {
                "authorization": "Bearer super-secret",
                "cookie": "session=super-secret",
                "x-api-token": "super-secret",
                "x-mcp-agent-id": "team-a",
            },
            enabled=True,
            model_headers=("X-MCP-Model",),
            agent_headers=("X-MCP-Agent-ID",),
            client_headers=("X-MCP-Client",),
        )
        record = build_record(routing=routing, tool="t", duration_ms=0.0, outcome="ok")
        assert set(record["headers"]) == {"x-mcp-agent-id"}
        assert "super-secret" not in json.dumps(record)

    def test_the_header_count_is_capped(self) -> None:
        headers = {f"x-{index:03d}": "v" for index in range(40)}
        record = build_record(
            routing=_routing(recorded_headers=headers),
            tool="t",
            duration_ms=0.0,
            outcome="ok",
        )
        assert len(record["headers"]) == MAX_RECORDED_HEADERS
        expected = {f"x-{index:03d}" for index in range(MAX_RECORDED_HEADERS)}
        assert set(record["headers"]) == expected

    def test_header_values_are_truncated(self) -> None:
        routing = _routing(
            recorded_headers={"x-big": "a" * (MAX_RECORDED_HEADER_LENGTH + 50)}
        )
        record = build_record(routing=routing, tool="t", duration_ms=0.0, outcome="ok")
        assert record["headers"]["x-big"] == "a" * MAX_RECORDED_HEADER_LENGTH

    def test_the_cap_helper_handles_empty_input(self) -> None:
        assert cap_headers(None) == {}
        assert cap_headers({}) == {}

    def test_the_cap_helper_lower_cases_names(self) -> None:
        assert cap_headers({"X-MCP-Agent-ID": "team-a"}) == {"x-mcp-agent-id": "team-a"}
