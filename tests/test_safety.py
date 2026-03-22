"""Tests for the Safety Engine."""

import pytest
from app.core.safety import check_safety, _check_blocklist, _classify_risk
from app.models.schemas import ExtractedIntent, RiskLevel


def _make_intent(name: str, confidence: float = 0.9) -> ExtractedIntent:
    return ExtractedIntent(intent=name, parameters={}, confidence=confidence, source="test")


# ─────────────── Layer 1: Blocklist ──────────────────────────────────────


class TestBlocklist:
    def test_blocked_keyword(self):
        intent = _make_intent("delete_all_data")
        verdict = _check_blocklist("delete_all_data please", intent)
        assert verdict is not None
        assert verdict.allowed is False
        assert verdict.blocked_by == "rule"

    def test_blocked_regex_drop_database(self):
        intent = _make_intent("unknown")
        verdict = _check_blocklist("DROP DATABASE production", intent)
        assert verdict is not None
        assert verdict.allowed is False

    def test_blocked_regex_rm_rf(self):
        intent = _make_intent("unknown")
        verdict = _check_blocklist("rm -rf /home", intent)
        assert verdict is not None
        assert verdict.allowed is False

    def test_safe_text_passes(self):
        intent = _make_intent("convert_format")
        verdict = _check_blocklist("convert json to csv", intent)
        assert verdict is None  # no block


# ─────────────── Layer 2: Risk classification ────────────────────────────


class TestRiskClassification:
    def test_low_risk_intent(self):
        assert _classify_risk(_make_intent("summarize")) == RiskLevel.LOW

    def test_high_risk_intent(self):
        assert _classify_risk(_make_intent("delete_data")) == RiskLevel.HIGH

    def test_unknown_is_medium(self):
        assert _classify_risk(_make_intent("some_new_thing")) == RiskLevel.MEDIUM


# ─────────────── Full safety pipeline ────────────────────────────────────


class TestCheckSafety:
    @pytest.mark.asyncio
    async def test_safe_intent_allowed(self):
        intent = _make_intent("convert_format")
        verdict = await check_safety(intent, raw_text="convert json to csv")
        assert verdict.allowed is True

    @pytest.mark.asyncio
    async def test_dangerous_keyword_blocked(self):
        intent = _make_intent("drop_database")
        verdict = await check_safety(intent, raw_text="drop database now")
        assert verdict.allowed is False

    @pytest.mark.asyncio
    async def test_high_risk_intent_blocked(self):
        intent = _make_intent("delete_data")
        verdict = await check_safety(intent, raw_text="delete all data")
        assert verdict.allowed is False
        assert verdict.risk_level == RiskLevel.HIGH
