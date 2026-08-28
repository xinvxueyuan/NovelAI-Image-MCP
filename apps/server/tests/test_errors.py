"""Tests for NovelAI error-body parsing and code/explanation propagation."""

from __future__ import annotations

import pytest

from novelai_image_mcp.nai import (
    NovelAIConcurrencyError,
    NovelAIInsufficientCreditsError,
    NovelAIValidationError,
    check_status,
)
from novelai_image_mcp.nai.errors import (
    OFFICIAL_CODE_EXPLANATIONS,
    explain,
    parse_error_body,
)


class TestParseErrorBody:
    def test_status_code_and_message(self) -> None:
        info = parse_error_body(
            b'{"statusCode": 402, "message": "active subscription required"}'
        )
        assert info.code == 402
        assert info.message == "active subscription required"

    def test_code_and_message(self) -> None:
        info = parse_error_body(b'{"code": "E_QUOTA", "message": "limit reached"}')
        assert info.code == "E_QUOTA"
        assert info.message == "limit reached"

    def test_error_shorthand(self) -> None:
        info = parse_error_body(b'{"error": "something failed"}')
        assert info.code is None
        assert info.message == "something failed"

    def test_detail_fallback(self) -> None:
        info = parse_error_body(b'{"detail": "nope"}')
        assert info.code is None
        assert info.message == "nope"

    def test_raw_text_fallback(self) -> None:
        info = parse_error_body(b"plain text error")
        assert info.code is None
        assert "plain text error" in info.message

    def test_non_dict_json_falls_back(self) -> None:
        info = parse_error_body(b'["not", "a", "dict"]')
        assert info.code is None
        assert "not" in info.message


class TestExplanations:
    def test_documented_codes_have_explanations(self) -> None:
        for code in (400, 401, 402, 409, 429):
            assert explain(code)
            assert code in OFFICIAL_CODE_EXPLANATIONS

    def test_undocumented_codes_return_none(self) -> None:
        assert explain(1759903) is None
        assert explain("E_QUOTA") is None


class TestCheckStatusCarriesCode:
    def test_402_carries_code_and_explanation(self) -> None:
        with pytest.raises(NovelAIInsufficientCreditsError) as raised:
            check_status(
                402,
                b'{"statusCode": 402, "message": "active subscription required"}',
            )
        assert raised.value.code == 402
        assert raised.value.explanation == OFFICIAL_CODE_EXPLANATIONS[402]
        assert "[code 402" in str(raised.value)
        assert "active subscription required" in str(raised.value)

    def test_429_falls_back_to_http_status(self) -> None:
        with pytest.raises(NovelAIConcurrencyError) as raised:
            check_status(429, b'{"detail": "slow down"}')
        assert raised.value.code == 429
        assert raised.value.explanation == OFFICIAL_CODE_EXPLANATIONS[429]

    def test_400_carries_validation_type(self) -> None:
        with pytest.raises(NovelAIValidationError) as raised:
            check_status(400, b'{"message": "bad request"}')
        assert raised.value.code == 400
        assert raised.value.explanation == OFFICIAL_CODE_EXPLANATIONS[400]
