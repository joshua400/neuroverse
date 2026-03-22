"""Integration tests — full pipeline from raw input to execution."""

import pytest
from app.core.language import detect_language
from app.core.intent import extract_intent
from app.core.safety import check_safety
from app.services.executor import execute_intent


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_english_convert_csv(self):
        """English input requesting format conversion."""
        lang = await detect_language("convert this json to csv")
        intent = await extract_intent(lang.normalized_text)
        safety = await check_safety(intent, raw_text="convert this json to csv")
        result = await execute_intent(intent, safety)

        assert intent.intent == "convert_format"
        assert safety.allowed is True
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_tamil_mixed_input(self):
        """Tamil-English code-switched input."""
        raw = "indha file ah csv convert pannu"
        lang = await detect_language(raw)
        # Should normalise keywords
        assert "do" in lang.normalized_text or "csv" in lang.normalized_text

        intent = await extract_intent(lang.normalized_text)
        assert intent.intent == "convert_format"

    @pytest.mark.asyncio
    async def test_hindi_mixed_input(self):
        """Hindi-English code-switched input."""
        raw = "report banao sales ka"
        lang = await detect_language(raw)
        assert "create" in lang.normalized_text

    @pytest.mark.asyncio
    async def test_dangerous_command_blocked(self):
        """Dangerous input should be blocked by safety."""
        raw = "drop database production"
        lang = await detect_language(raw)
        intent = await extract_intent(lang.normalized_text)
        safety = await check_safety(intent, raw_text=raw)
        result = await execute_intent(intent, safety)

        assert safety.allowed is False
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_summarize_pipeline(self):
        """Summarise intent through full pipeline."""
        raw = "summarize this long report for me"
        lang = await detect_language(raw)
        intent = await extract_intent(lang.normalized_text)
        safety = await check_safety(intent, raw_text=raw)
        result = await execute_intent(intent, safety)

        assert intent.intent == "summarize"
        assert safety.allowed is True
        assert result["success"] is True


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_input(self):
        lang = await detect_language("")
        intent = await extract_intent(lang.normalized_text)
        assert intent.intent == "unknown"

    @pytest.mark.asyncio
    async def test_incomplete_command(self):
        """Partial / ambiguous input."""
        lang = await detect_language("do it")
        intent = await extract_intent(lang.normalized_text)
        # Should gracefully handle
        assert intent.intent is not None

    @pytest.mark.asyncio
    async def test_mixed_slang(self):
        """Mixed slang input."""
        lang = await detect_language("bro file csv mein change karo yaar")
        intent = await extract_intent(lang.normalized_text)
        # Should pick up "csv" and "change" keywords
        assert intent.intent in ("convert_format", "unknown", "query_data")
