"""Tests for the Intent Extraction module."""

import pytest
from app.core.intent import extract_intent, _rule_based_extract


# ─────────────── Rule-based extraction ───────────────────────────────────


class TestRuleBasedExtract:
    def test_convert_intent(self):
        result = _rule_based_extract("convert this json to csv")
        assert result.intent == "convert_format"
        assert result.source == "rule"
        assert result.confidence > 0.0
        # Should detect format params
        assert "output_format" in result.parameters or "input_format" in result.parameters

    def test_summarize_intent(self):
        result = _rule_based_extract("summarize this report for me")
        assert result.intent == "summarize"

    def test_delete_intent(self):
        result = _rule_based_extract("delete all old records")
        assert result.intent == "delete_data"

    def test_query_intent(self):
        result = _rule_based_extract("search for users named John")
        assert result.intent == "query_data"

    def test_send_intent(self):
        result = _rule_based_extract("send this report via email")
        assert result.intent == "send_message"

    def test_explain_intent(self):
        result = _rule_based_extract("explain how to use this system")
        assert result.intent == "explain"

    def test_unknown_intent(self):
        result = _rule_based_extract("hello world")
        assert result.intent == "unknown"
        assert result.confidence <= 0.1

    def test_empty_string(self):
        result = _rule_based_extract("")
        assert result.intent == "unknown"


# ─────────────── Full extraction (async, no LLM) ────────────────────────


class TestExtractIntent:
    @pytest.mark.asyncio
    async def test_without_llm(self):
        """Without an LLM callable, falls back to rule-based."""
        result = await extract_intent("convert json to csv")
        assert result.intent == "convert_format"
        assert result.source == "rule"

    @pytest.mark.asyncio
    async def test_empty_input(self):
        result = await extract_intent("")
        assert result.intent == "unknown"

    @pytest.mark.asyncio
    async def test_with_mock_llm(self):
        """With a mock LLM that returns valid JSON."""
        async def mock_llm(prompt: str) -> str:
            return '{"intent": "generate_report", "parameters": {"type": "sales"}, "confidence": 0.95}'

        result = await extract_intent("generate a sales report", llm_call=mock_llm)
        assert result.intent == "generate_report"
        assert result.source == "llm"
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_with_failing_llm(self):
        """If LLM raises, should fall back to rule-based."""
        async def failing_llm(prompt: str) -> str:
            raise RuntimeError("LLM down")

        result = await extract_intent("convert json to csv", llm_call=failing_llm)
        assert result.intent == "convert_format"
        assert result.source == "rule"
