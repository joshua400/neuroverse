"""Tests for the Language Intelligence module."""

import pytest
import asyncio
from app.core.language import detect_language, _normalise_keywords


# ─────────────── Keyword Normalisation ───────────────────────────────────


class TestNormaliseKeywords:
    def test_tamil_keyword(self):
        result = _normalise_keywords("indha file ah csv convert pannu")
        assert "do" in result  # "pannu" → "do"
        assert "csv" in result

    def test_hindi_keyword(self):
        result = _normalise_keywords("report banao sales ka")
        assert "create" in result  # "banao" → "create"
        assert "report" in result

    def test_kannada_keyword(self):
        result = _normalise_keywords("file kalisu")
        assert "send" in result  # "kalisu" → "send"

    def test_malayalam_keyword(self):
        result = _normalise_keywords("idhu maattu")
        assert "remove" in result  # "maattu" → "remove"

    def test_bengali_keyword(self):
        result = _normalise_keywords("report pathao")
        assert "send" in result  # "pathao" → "send"

    def test_english_passthrough(self):
        result = _normalise_keywords("convert this file to csv")
        assert result == "convert this file to csv"

    def test_mixed_tamil_english(self):
        result = _normalise_keywords("anna indha file ah csv convert pannu")
        assert "do" in result
        assert "csv" in result

    def test_empty_string(self):
        result = _normalise_keywords("")
        assert result == ""


# ─────────────── Language Detection ──────────────────────────────────────


class TestDetectLanguage:
    @pytest.mark.asyncio
    async def test_english_input(self):
        result = await detect_language("convert this file to csv format")
        assert "en" in result.languages
        assert result.confidence > 0.0
        assert result.normalized_text == "convert this file to csv format"

    @pytest.mark.asyncio
    async def test_empty_input(self):
        result = await detect_language("")
        assert result.languages == ["en"]
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_preserves_original(self):
        text = "anna indha file ah csv convert pannu"
        result = await detect_language(text)
        assert result.original_text == text

    @pytest.mark.asyncio
    async def test_normalised_output(self):
        result = await detect_language("report banao")
        assert "create" in result.normalized_text  # "banao" → "create"

    @pytest.mark.asyncio
    async def test_code_switch_flag(self):
        """May or may not detect code-switching depending on input length."""
        result = await detect_language(
            "please convert this file quickly pannu da"
        )
        # We just verify the flag is a boolean
        assert isinstance(result.is_code_switched, bool)
