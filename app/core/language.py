#!/usr/bin/env python3
"""
Language Intelligence Module — Hybrid Pipeline.

Pipeline:
  Input → Language Detect →  Code-Switch Split → Keyword Normalisation → Output

Key design decisions:
  • Uses **langdetect** for fast statistical language identification.
  • Rule-based keyword extraction preserves domain-critical tokens
    (csv, report, delete, summarise …) so the LLM intent step never misses them.
  • Does NOT fully translate — only normalises critical keywords, keeping
    the rest untouched for context. Full translation is left to the
    model router if needed.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

from app.models.schemas import LanguageDetectionResult

# Ensure deterministic results from langdetect.
DetectorFactory.seed = 0

# ─────────────── Domain-keyword dictionary (expandable) ──────────────────
# Maps non-English domain tokens → canonical English equivalents.
# Covers common Tamil, Hindi, Telugu, and Kannada task words.
KEYWORD_MAP: Dict[str, str] = {
    # Tamil
    "pannu": "do",
    "kondu": "bring",
    "maathru": "change",
    "eduthu": "take",
    "podu": "put",
    "paaru": "see",
    "anuppu": "send",
    "kaattu": "show",
    "seri": "ok",
    "azhithu": "delete",
    "seitha": "done",
    "report": "report",
    # Hindi
    "karo": "do",
    "bhejo": "send",
    "dikhao": "show",
    "hatao": "remove",
    "banao": "create",
    "badlo": "change",
    "nikalo": "extract",
    "samjhao": "explain",
    "mitao": "delete",
    # Telugu
    "cheyyi": "do",
    "pampu": "send",
    "chupinchu": "show",
    # Kannada
    "maadu": "do",
    "kalisu": "send",
    "toorisu": "show",
    "odigu": "read",
    # Malayalam
    "cheyyu": "do",
    "ayakku": "send",
    "kaanikku": "show",
    "vaayikku": "read",
    "maattu": "remove",
    # Bengali
    "koro": "do",
    "pathao": "send",
    "dekhao": "show",
    "poro": "read",
    "shorao": "remove",
    # File-format tokens (pass-through)
    "csv": "csv",
    "json": "json",
    "pdf": "pdf",
    "excel": "excel",
    "xlsx": "xlsx",
}

# ─────────────────────────── Public API ──────────────────────────────────


async def detect_language(text: str) -> LanguageDetectionResult:
    """Run the full hybrid language-intelligence pipeline on *text*.

    Returns a ``LanguageDetectionResult`` with detected languages,
    a confidence score, and a keyword-normalised version of the input.
    """
    text = text.strip()
    if not text:
        return LanguageDetectionResult(
            languages=["en"],
            confidence=0.0,
            is_code_switched=False,
            original_text=text,
            normalized_text=text,
        )

    # ── Step 1: Statistical language detection ──────────────────────
    languages, confidence = _detect_languages(text)

    # ── Step 2: Code-switch detection ───────────────────────────────
    is_code_switched = len(languages) > 1

    # ── Step 3: Keyword normalisation (rule-based) ──────────────────
    normalized_text = _normalise_keywords(text)

    return LanguageDetectionResult(
        languages=languages,
        confidence=confidence,
        is_code_switched=is_code_switched,
        original_text=text,
        normalized_text=normalized_text,
    )


# ─────────────────────── Internal helpers ────────────────────────────────


def _detect_languages(text: str) -> Tuple[List[str], float]:
    """Return (list_of_lang_codes, best_confidence)."""
    try:
        results = detect_langs(text)
        langs = [r.lang for r in results]
        best_confidence = results[0].prob if results else 0.0
        return langs, round(best_confidence, 4)
    except LangDetectException:
        return ["en"], 0.0


def _normalise_keywords(text: str) -> str:
    """Replace known non-English domain keywords with their English canonical form.

    The replacement is case-insensitive but preserves surrounding whitespace.
    """
    tokens = re.split(r"(\s+)", text)  # keep whitespace tokens
    out: list[str] = []
    for token in tokens:
        lower = token.lower()
        out.append(KEYWORD_MAP.get(lower, token))
    return "".join(out)
