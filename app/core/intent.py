#!/usr/bin/env python3
"""
Intent Extraction Engine — LLM + Rule-based Fallback.

Pipeline:
  Normalised Input → LLM Extraction → Validation → (fallback) Rule Parser → ExtractedIntent

Key design decisions:
  • Primary: asks the configured LLM to return a JSON intent.
  • Fallback: if the LLM call fails or returns low-confidence output,
    a deterministic rule-based parser takes over, matching known
    keyword patterns to canonical intents.
  • Pydantic validation ensures the output is always well-typed.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import ExtractedIntent

# ───────────────── Rule-based intent patterns ────────────────────────────
# Each tuple: (list_of_trigger_keywords, canonical_intent, default_params)

_RULE_PATTERNS: List[Tuple[List[str], str, Dict[str, Any]]] = [
    # Format conversion
    (["convert", "csv", "json", "excel", "xlsx", "pdf", "format"],
     "convert_format", {}),
    # Summarisation
    (["summarise", "summarize", "summary", "brief", "tldr"],
     "summarize", {}),
    # Report generation
    (["report", "generate report", "sales report"],
     "generate_report", {}),
    # Deletion / cleanup
    (["delete", "remove", "drop", "clean"],
     "delete_data", {}),
    # Data query
    (["query", "search", "find", "look up", "fetch", "get"],
     "query_data", {}),
    # Send / share
    (["send", "share", "email", "notify"],
     "send_message", {}),
    # Explanation
    (["explain", "describe", "what is", "how to"],
     "explain", {}),
]


# ───────────────── Public API ────────────────────────────────────────────


async def extract_intent(
    text: str,
    *,
    llm_call=None,
) -> ExtractedIntent:
    """Extract a structured intent from *text*.

    Parameters
    ----------
    text:
        The (preferably normalised) user input.
    llm_call:
        An optional async callable ``async (prompt: str) -> str`` that
        invokes the LLM.  When *None*, the rule-based parser is used
        directly.

    Returns
    -------
    ExtractedIntent
        Always returns a valid Pydantic model.
    """
    text = text.strip()
    if not text:
        return _empty_intent()

    # ── Try LLM first ────────────────────────────────────────────────
    if llm_call is not None:
        try:
            intent = await _llm_extract(text, llm_call)
            if intent is not None and intent.confidence >= 0.5:
                return intent
        except Exception:
            pass  # fall through to rule-based

    # ── Fallback: rule-based parser ──────────────────────────────────
    return _rule_based_extract(text)


# ─────────────────────── LLM extraction ──────────────────────────────────

_LLM_PROMPT_TEMPLATE = """\
Extract structured intent from the following user input.

Return ONLY valid JSON with these fields:
- "intent": a short snake_case intent name
- "parameters": a dict of relevant key-value pairs
- "confidence": a float 0-1

Input: {user_input}
"""


async def _llm_extract(
    text: str, llm_call
) -> Optional[ExtractedIntent]:
    prompt = _LLM_PROMPT_TEMPLATE.format(user_input=text)
    raw = await llm_call(prompt)
    raw = raw.strip()

    # Try to parse JSON from the LLM response
    parsed = _parse_json(raw)
    if parsed is None:
        return None

    return ExtractedIntent(
        intent=parsed.get("intent", "unknown"),
        parameters=parsed.get("parameters", {}),
        confidence=float(parsed.get("confidence", 0.0)),
        source="llm",
    )


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Robustly extract the first JSON object from *text*."""
    # Strip markdown code fences if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object within the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
        return None


# ────────────────── Rule-based fallback ──────────────────────────────────


def _rule_based_extract(text: str) -> ExtractedIntent:
    """Deterministic keyword-matching intent extractor."""
    lower = text.lower()
    best_score = 0
    best_intent = "unknown"
    best_params: Dict[str, Any] = {}

    for keywords, intent_name, default_params in _RULE_PATTERNS:
        hits = sum(1 for kw in keywords if kw in lower)
        if hits > best_score:
            best_score = hits
            best_intent = intent_name
            best_params = dict(default_params)

    # Confidence is proportional to how many keywords matched
    confidence = min(best_score / 3.0, 1.0) if best_score > 0 else 0.1

    # Try to extract format hints from text
    _enrich_format_params(lower, best_params)

    return ExtractedIntent(
        intent=best_intent,
        parameters=best_params,
        confidence=round(confidence, 2),
        source="rule",
    )


def _enrich_format_params(lower: str, params: Dict[str, Any]) -> None:
    """Heuristically add input_format / output_format if detectable."""
    formats = ["csv", "json", "pdf", "excel", "xlsx", "xml", "yaml"]
    found = [f for f in formats if f in lower]
    if len(found) >= 2:
        params["input_format"] = found[0]
        params["output_format"] = found[1]
    elif len(found) == 1:
        params["output_format"] = found[0]


def _empty_intent() -> ExtractedIntent:
    return ExtractedIntent(
        intent="unknown",
        parameters={},
        confidence=0.0,
        source="rule",
    )
