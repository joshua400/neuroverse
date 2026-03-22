#!/usr/bin/env python3
"""
Tool Executor — maps intents to registered tool functions with retry logic.

Tool Registry pattern:
  TOOLS = {
      "convert_format": convert_tool,
      "summarize":      summarize_tool,
      ...
  }

Retry Strategy:
  On failure, retry up to MAX_RETRIES times with the same or modified input.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Coroutine, Dict, Optional

from app.models.schemas import ExtractedIntent, SafetyVerdict

MAX_RETRIES = 2

# ───────────── Tool Registry ────────────────────────────────────────────

ToolFunc = Callable[..., Coroutine[None, None, Any]]

TOOLS: Dict[str, ToolFunc] = {}


def register_tool(name: str):
    """Decorator to register a tool function."""
    def wrapper(func: ToolFunc) -> ToolFunc:
        TOOLS[name] = func
        return func
    return wrapper


# ───────────── Built-in demo tools ───────────────────────────────────────


@register_tool("convert_format")
async def convert_format_tool(
    input_data: str = "",
    input_format: str = "json",
    output_format: str = "csv",
    **kwargs,
) -> str:
    """Demo: Convert data between formats (JSON→CSV stub)."""
    if input_format == "json" and output_format == "csv":
        try:
            data = json.loads(input_data) if input_data else [{"example": "value"}]
            if isinstance(data, list) and data:
                headers = list(data[0].keys())
                lines = [",".join(headers)]
                for row in data:
                    lines.append(",".join(str(row.get(h, "")) for h in headers))
                return "\n".join(lines)
        except Exception as exc:
            return f"Conversion error: {exc}"
    return f"Conversion from {input_format} to {output_format} is not yet implemented."


@register_tool("summarize")
async def summarize_tool(text: str = "", **kwargs) -> str:
    """Demo: Summarise the given text (stub — returns truncated)."""
    if not text:
        return "No text provided to summarize."
    words = text.split()
    if len(words) <= 30:
        return text
    return " ".join(words[:30]) + "…"


@register_tool("generate_report")
async def generate_report_tool(**kwargs) -> str:
    """Demo: Generate a simple report stub."""
    return json.dumps(
        {
            "report": "Sales Report",
            "status": "generated",
            "data": kwargs or {"note": "No data provided — demo stub"},
        },
        indent=2,
    )


@register_tool("query_data")
async def query_data_tool(query: str = "", **kwargs) -> str:
    """Demo: Query data (stub)."""
    return json.dumps({"query": query, "results": [], "note": "Demo stub — no real DB connected."})


@register_tool("explain")
async def explain_tool(topic: str = "", **kwargs) -> str:
    """Demo: Explain a topic (stub)."""
    return f"Explanation for '{topic}': This is a placeholder. In production, this routes to the LLM."


# ───────────── Executor ──────────────────────────────────────────────────


async def execute_intent(
    intent: ExtractedIntent,
    safety: SafetyVerdict,
    *,
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute the tool mapped to *intent*, respecting *safety*.

    Returns a result dict with ``success``, ``output``, and ``tool``.
    """
    if not safety.allowed:
        return {
            "success": False,
            "output": f"Blocked by safety: {safety.reason}",
            "tool": intent.intent,
        }

    tool_func = TOOLS.get(intent.intent)
    if tool_func is None:
        return {
            "success": False,
            "output": f"No tool registered for intent '{intent.intent}'.",
            "tool": intent.intent,
        }

    params = dict(intent.parameters)
    if extra_context:
        params.update(extra_context)

    last_error: Optional[str] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = await tool_func(**params)
            return {"success": True, "output": result, "tool": intent.intent}
        except Exception as exc:
            last_error = f"Attempt {attempt} failed: {exc}"

    return {
        "success": False,
        "output": f"All {MAX_RETRIES} retries exhausted. Last error: {last_error}",
        "tool": intent.intent,
    }
