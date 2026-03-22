#!/usr/bin/env python3
"""
Multi-Layer Safety Engine.

Architecture — three layers checked in order:
  Layer 1 — Rule-based blocklist (fast, deterministic)
  Layer 2 — Intent Risk Classifier (heuristic scoring)
  Layer 3 — Model-based safety check (optional LLM judge)

Action Guard:
  if risk == HIGH or CRITICAL → block execution
  if risk == MEDIUM and strict_mode → block execution

Sandbox note:
  Actual sandboxed execution is delegated to the Execution Engine;
  this module only decides *whether* to allow it.
"""

from __future__ import annotations

import re
from typing import Callable, Coroutine, Optional

from app.config import settings
from app.models.schemas import ExtractedIntent, RiskLevel, SafetyVerdict

# ───────────── Layer 1: Blocked keywords / patterns ──────────────────────

BLOCKED_KEYWORDS = [
    "delete_all_data",
    "drop_database",
    "drop_table",
    "system_shutdown",
    "format_disk",
    "rm -rf",
    "truncate",
    "shutdown",
    "reboot",
    "erase_all",
    "destroy",
]

BLOCKED_PATTERNS = [
    re.compile(r"\bdrop\s+(database|table|schema)\b", re.IGNORECASE),
    re.compile(r"\bdelete\s+from\s+\*\b", re.IGNORECASE),
    re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
    re.compile(r"\bformat\s+[a-z]:\b", re.IGNORECASE),
    re.compile(r"\brm\s+(-rf|--force)\b", re.IGNORECASE),
]

# ───────────── Layer 2: Intent risk map ──────────────────────────────────

_INTENT_RISK_MAP = {
    "delete_data": RiskLevel.HIGH,
    "drop_database": RiskLevel.CRITICAL,
    "system_shutdown": RiskLevel.CRITICAL,
    "send_message": RiskLevel.MEDIUM,
    "convert_format": RiskLevel.LOW,
    "summarize": RiskLevel.LOW,
    "generate_report": RiskLevel.LOW,
    "query_data": RiskLevel.LOW,
    "explain": RiskLevel.LOW,
    "unknown": RiskLevel.MEDIUM,
}

# ───────────── Public API ────────────────────────────────────────────────


async def check_safety(
    intent: ExtractedIntent,
    raw_text: str = "",
    *,
    llm_safety_call: Optional[
        Callable[[str], Coroutine[None, None, str]]
    ] = None,
) -> SafetyVerdict:
    """Run the full multi-layer safety pipeline.

    Parameters
    ----------
    intent:
        The extracted intent to evaluate.
    raw_text:
        Original user input (used by Layer 1 & 3).
    llm_safety_call:
        Optional async LLM callable for Layer 3 model-based check.
    """
    # ── Layer 1: Rule-based blocklist ────────────────────────────────
    verdict = _check_blocklist(raw_text, intent)
    if verdict is not None:
        return verdict

    # ── Layer 2: Intent risk classification ──────────────────────────
    risk = _classify_risk(intent)

    if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        return SafetyVerdict(
            allowed=False,
            risk_level=risk,
            reason=f"Intent '{intent.intent}' classified as {risk.value} risk.",
            blocked_by="intent_risk",
        )

    if risk == RiskLevel.MEDIUM and settings.safety_strict_mode:
        return SafetyVerdict(
            allowed=False,
            risk_level=risk,
            reason=f"Intent '{intent.intent}' is medium risk; strict mode is enabled.",
            blocked_by="intent_risk",
        )

    # ── Layer 3: Optional model-based safety check ───────────────────
    if llm_safety_call is not None:
        model_verdict = await _model_safety_check(
            intent, raw_text, llm_safety_call
        )
        if model_verdict is not None:
            return model_verdict

    # ── All clear ────────────────────────────────────────────────────
    return SafetyVerdict(
        allowed=True,
        risk_level=risk,
        reason="All safety checks passed.",
    )


# ─────────────────── Internal helpers ────────────────────────────────────


def _check_blocklist(
    raw_text: str, intent: ExtractedIntent
) -> Optional[SafetyVerdict]:
    """Layer 1 — fast keyword and regex check."""
    combined = f"{raw_text} {intent.intent}".lower()

    for kw in BLOCKED_KEYWORDS:
        if kw in combined:
            return SafetyVerdict(
                allowed=False,
                risk_level=RiskLevel.CRITICAL,
                reason=f"Blocked keyword detected: '{kw}'",
                blocked_by="rule",
            )

    for pattern in BLOCKED_PATTERNS:
        if pattern.search(combined):
            return SafetyVerdict(
                allowed=False,
                risk_level=RiskLevel.CRITICAL,
                reason=f"Blocked pattern matched: {pattern.pattern}",
                blocked_by="rule",
            )

    return None  # no match — continue to next layer


def _classify_risk(intent: ExtractedIntent) -> RiskLevel:
    """Layer 2 — map intent to risk level."""
    return _INTENT_RISK_MAP.get(intent.intent, RiskLevel.MEDIUM)


async def _model_safety_check(
    intent: ExtractedIntent,
    raw_text: str,
    llm_call,
) -> Optional[SafetyVerdict]:
    """Layer 3 — ask LLM to judge safety (optional)."""
    prompt = (
        "You are a safety classifier. Given the following user request and "
        "extracted intent, respond with ONLY a JSON object:\n"
        '{"safe": true/false, "reason": "..."}\n\n'
        f"User request: {raw_text}\n"
        f"Intent: {intent.intent}\n"
        f"Parameters: {intent.parameters}\n"
    )
    try:
        raw = await llm_call(prompt)
        import json
        result = json.loads(raw.strip())
        if not result.get("safe", True):
            return SafetyVerdict(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                reason=result.get("reason", "Model-based check flagged this action."),
                blocked_by="model",
            )
    except Exception:
        pass  # if model call fails, default to allowing (layers 1+2 already passed)

    return None
