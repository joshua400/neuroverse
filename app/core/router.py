#!/usr/bin/env python3
"""
Multi-Model AI Router.

Routes tasks to the best-suited LLM provider based on task type:
  • multilingual → Sarvam AI
  • reasoning    → OpenAI / Anthropic
  • local        → Ollama
  • general      → best available

Benefits:  cost reduction · speed · no vendor lock-in.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, Optional

import httpx

from app.config import settings
from app.models.schemas import ModelProvider, ModelRoutingDecision, TaskType

# ─────────────── Default model names per provider ────────────────────────

DEFAULT_MODELS: Dict[ModelProvider, str] = {
    ModelProvider.OPENAI: "gpt-4o",
    ModelProvider.ANTHROPIC: "claude-sonnet-4-20250514",
    ModelProvider.OLLAMA: "llama3",
    ModelProvider.SARVAM: "sarvam-2b-v0.5",
}

# ─────────────── Routing logic ───────────────────────────────────────────


def route_task(task_type: TaskType) -> ModelRoutingDecision:
    """Determine which provider + model should handle a given task type."""
    if task_type == TaskType.MULTILINGUAL:
        if settings.sarvam_api_key:
            return ModelRoutingDecision(
                provider=ModelProvider.SARVAM,
                model_name=DEFAULT_MODELS[ModelProvider.SARVAM],
                reason="Multilingual task — routing to Sarvam AI for best Indian-language support.",
            )
        # Fall back to OpenAI if Sarvam not configured
        return _fallback_decision("Sarvam not configured; falling back for multilingual.")

    if task_type == TaskType.REASONING:
        if settings.anthropic_api_key:
            return ModelRoutingDecision(
                provider=ModelProvider.ANTHROPIC,
                model_name=DEFAULT_MODELS[ModelProvider.ANTHROPIC],
                reason="Reasoning task — routing to Anthropic for strong analytical capability.",
            )
        if settings.openai_api_key:
            return ModelRoutingDecision(
                provider=ModelProvider.OPENAI,
                model_name=DEFAULT_MODELS[ModelProvider.OPENAI],
                reason="Reasoning task — routing to OpenAI (Anthropic unavailable).",
            )
        return _fallback_decision("No reasoning provider available.")

    if task_type == TaskType.LOCAL:
        return ModelRoutingDecision(
            provider=ModelProvider.OLLAMA,
            model_name=DEFAULT_MODELS[ModelProvider.OLLAMA],
            reason="Local task — routing to Ollama for on-device execution.",
        )

    # General / unknown
    return _fallback_decision("General task — using best available provider.")


def _fallback_decision(reason: str) -> ModelRoutingDecision:
    """Pick first available provider in priority order."""
    if settings.openai_api_key:
        return ModelRoutingDecision(
            provider=ModelProvider.OPENAI,
            model_name=DEFAULT_MODELS[ModelProvider.OPENAI],
            reason=reason,
        )
    if settings.anthropic_api_key:
        return ModelRoutingDecision(
            provider=ModelProvider.ANTHROPIC,
            model_name=DEFAULT_MODELS[ModelProvider.ANTHROPIC],
            reason=reason,
        )
    return ModelRoutingDecision(
        provider=ModelProvider.OLLAMA,
        model_name=DEFAULT_MODELS[ModelProvider.OLLAMA],
        reason=reason + " Falling back to Ollama (local).",
    )


# ─────────────── LLM call dispatching ────────────────────────────────────


async def call_llm(prompt: str, task_type: TaskType = TaskType.GENERAL) -> str:
    """Route *prompt* to the appropriate LLM and return the text response."""
    decision = route_task(task_type)
    return await _dispatch(prompt, decision)


async def _dispatch(prompt: str, decision: ModelRoutingDecision) -> str:
    """Actually call the right provider."""
    if decision.provider == ModelProvider.OPENAI:
        return await _call_openai(prompt, decision.model_name)
    if decision.provider == ModelProvider.ANTHROPIC:
        return await _call_anthropic(prompt, decision.model_name)
    if decision.provider == ModelProvider.SARVAM:
        return await _call_sarvam(prompt, decision.model_name)
    if decision.provider == ModelProvider.OLLAMA:
        return await _call_ollama(prompt, decision.model_name)
    raise ValueError(f"Unknown provider: {decision.provider}")


# ────────────────── Provider implementations ─────────────────────────────


async def _call_openai(prompt: str, model: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(prompt: str, model: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key or "",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _call_sarvam(prompt: str, model: str) -> str:
    """Call Sarvam AI API for Indian-language optimised inference."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.sarvam.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.sarvam_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_ollama(prompt: str, model: str) -> str:
    """Call local Ollama instance."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
