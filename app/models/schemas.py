#!/usr/bin/env python3
"""
Pydantic models used throughout the India-First MCP.

Covers:
  • Language detection results
  • Structured intents
  • Memory records
  • Safety verdicts
  • Model routing decisions
  • Agent routing definitions
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ───────────────────────────────── Enums ──────────────────────────────────


class RiskLevel(str, Enum):
    """Risk classification for a user action."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryTier(str, Enum):
    """Tier in the tiered-memory architecture."""
    SHORT_TERM = "short_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    SARVAM = "sarvam"


class TaskType(str, Enum):
    """High-level classification of an incoming task."""
    MULTILINGUAL = "multilingual"
    REASONING = "reasoning"
    LOCAL = "local"
    GENERAL = "general"


# ────────────────────────── Language Models ───────────────────────────────


class LanguageDetectionResult(BaseModel):
    """Result of the language-detection step."""
    model_config = ConfigDict(str_strip_whitespace=True)

    languages: List[str] = Field(
        ..., description="ISO 639-1 codes detected (e.g. ['ta', 'en'])"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall detection confidence"
    )
    is_code_switched: bool = Field(
        default=False, description="True when multiple languages are mixed"
    )
    original_text: str = Field(..., description="Raw input text")
    normalized_text: str = Field(
        ..., description="Internally normalised English representation"
    )


# ─────────────────────────── Intent Models ───────────────────────────────


class ExtractedIntent(BaseModel):
    """Structured intent extracted from user input."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    intent: str = Field(
        ...,
        description="Canonical intent name, e.g. 'convert_format'",
        min_length=1,
        max_length=120,
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Key-value parameters for the intent"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence of extraction"
    )
    source: str = Field(
        default="llm",
        description="'llm' or 'rule' — which extraction engine produced this",
    )

    @field_validator("intent")
    @classmethod
    def normalise_intent(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")


# ─────────────────────────── Memory Models ───────────────────────────────


class MemoryRecord(BaseModel):
    """A single memory entry in the tiered store."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = Field(default=None, description="UUID primary key")
    user_id: str = Field(..., description="ID of the owning agent / user")
    tier: MemoryTier = Field(..., description="Which memory tier this belongs to")
    intent: str = Field(..., description="Canonical intent this relates to")
    language: str = Field(default="en", description="Primary language")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload")
    importance_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Importance score — only stored if > threshold",
    )
    vector: Optional[List[float]] = Field(default=None, description="Memory embedding vector")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class MemoryQuery(BaseModel):
    """Query parameters for memory recall."""
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(..., description="Agent / user identifier")
    intent: Optional[str] = Field(default=None, description="Filter by intent")
    tier: Optional[MemoryTier] = Field(default=None, description="Filter by tier")
    semantic_query: Optional[str] = Field(default=None, description="Query for semantic retrieval")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")


# ─────────────────────────── Safety Models ───────────────────────────────


class SafetyVerdict(BaseModel):
    """Result of the multi-layer safety check."""
    allowed: bool = Field(..., description="Whether the action is permitted")
    risk_level: RiskLevel = Field(
        ..., description="Risk classification of the action"
    )
    reason: str = Field(
        default="", description="Human-readable explanation"
    )
    blocked_by: Optional[str] = Field(
        default=None,
        description="Which safety layer blocked: 'rule' | 'intent_risk' | 'model'",
    )


# ──────────────────────── Router / Agent Models ──────────────────────────


class ModelRoutingDecision(BaseModel):
    """Describes which model provider should handle the task."""
    provider: ModelProvider
    model_name: str = Field(..., description="Specific model identifier")
    reason: str = Field(default="", description="Why this model was chosen")


class AgentDefinition(BaseModel):
    """Describes a registered downstream agent."""
    agent_name: str = Field(..., description="Human-readable agent name")
    endpoint: str = Field(..., description="URL endpoint of the agent")
    capabilities: List[str] = Field(
        default_factory=list, description="List of supported intents / capabilities"
    )


class AgentRoutingRequest(BaseModel):
    """Request to route a task to another agent."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    target_agent: str = Field(..., description="Agent name to route to")
    task: str = Field(..., description="Task description")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary payload for the target"
    )
