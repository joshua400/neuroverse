#!/usr/bin/env python3
"""
India-First Multilingual MCP Server.

Exposes the following tools via Model Context Protocol (FastMCP):
  1. india_mcp_process_multilingual_input
  2. india_mcp_store_memory
  3. india_mcp_recall_memory
  4. india_mcp_safe_execute
  5. india_mcp_route_agent
  6. india_mcp_model_route
  7. india_mcp_transcribe_audio
  8. india_mcp_synthesize_speech
  9. india_mcp_feedback
  10. india_mcp_assemble_context

Following mcp-builder skill best practices:
  • Pydantic v2 input models with Field() constraints
  • Async/await throughout
  • Tool annotations (readOnlyHint, destructiveHint, etc.)
  • Comprehensive docstrings with schema descriptions
  • Consistent error handling
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from mcp.server.fastmcp import FastMCP

# ─────────────── Initialise MCP Server ───────────────────────────────────

mcp = FastMCP("india_mcp")

# ─────────────── Input Models ────────────────────────────────────────────


class ProcessMultilingualInput(BaseModel):
    """Input for the multilingual processing pipeline."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(
        ...,
        description="Raw user input (may be code-switched, e.g. Tamil+English)",
        min_length=1,
        max_length=5000,
    )
    user_id: str = Field(
        default="anonymous",
        description="Identifier for the user / agent (used for memory context)",
    )
    execute: bool = Field(
        default=True,
        description="If true, also execute the extracted intent after safety check",
    )


class StoreMemoryInput(BaseModel):
    """Input for storing a memory record."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_id: str = Field(..., description="Agent / user identifier")
    intent: str = Field(..., description="Canonical intent this memory relates to")
    tier: str = Field(
        default="short_term",
        description="Memory tier: short_term | episodic | semantic",
    )
    language: str = Field(default="en", description="Primary language code")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Structured memory payload"
    )
    importance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score — only episodic/semantic memories above 0.4 are persisted",
    )


class RecallMemoryInput(BaseModel):
    """Input for recalling memories."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    user_id: str = Field(..., description="Agent / user identifier")
    intent: Optional[str] = Field(default=None, description="Filter by intent")
    tier: Optional[str] = Field(default=None, description="Filter by tier")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")


class SafeExecuteInput(BaseModel):
    """Input for the safe-execution pipeline."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(
        ...,
        description="Raw user input to parse, safety-check, and execute",
        min_length=1,
        max_length=5000,
    )
    user_id: str = Field(default="anonymous", description="User / agent ID")


class RouteAgentInput(BaseModel):
    """Input for routing a task to another agent."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    target_agent: str = Field(..., description="Name of the registered agent")
    task: str = Field(..., description="Task description to send")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary payload for the target"
    )


class ModelRouteInput(BaseModel):
    """Input for querying the model router."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    task_type: str = Field(
        default="general",
        description="Task type: multilingual | reasoning | local | general",
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Optional prompt to actually send to the routed model",
    )


class TranscribeInput(BaseModel):
    """Input for transcribing audio."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    audio_path: str = Field(..., description="Absolute path to the audio file to transcribe")


class SynthesizeInput(BaseModel):
    """Input for synthesizing speech."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(..., description="Text to synthesize into speech")
    language: str = Field(default="en", description="Language code (e.g. en, ta, hi)")


class FeedbackInput(BaseModel):
    """Input for RLHF feedback logging."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    intent: str = Field(..., description="The intent executed")
    model: str = Field(..., description="The model used")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    feedback_text: str = Field(default="", description="Optional human-readable feedback")


class AssembleContextInput(BaseModel):
    """Input for assembling code context."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(..., description="Search query for context assembly")
    dir: str = Field(default=".", description="Root directory to scan (defaults to cwd)")


# ─────────────── Tool Implementations ────────────────────────────────────


@mcp.tool(
    name="india_mcp_process_multilingual_input",
    annotations={
        "title": "Process Multilingual Input",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def process_multilingual_input(params: ProcessMultilingualInput) -> str:
    """Process mixed-language input through the full India-First pipeline.

    Pipeline: Language Detect → Normalise → Intent Extract → Safety Check → (optional) Execute

    Args:
        params (ProcessMultilingualInput): Validated input containing:
            - text (str): Raw user input, possibly code-switched
            - user_id (str): User / agent identifier (default: "anonymous")
            - execute (bool): Whether to also execute the intent (default: True)

    Returns:
        str: JSON with keys: language, intent, safety, execution (if execute=True)
    """
    from app.core.language import detect_language
    from app.core.intent import extract_intent
    from app.core.safety import check_safety
    from app.services.executor import execute_intent

    # Step 1: Language detection + normalisation
    lang_result = await detect_language(params.text)

    # Step 2: Intent extraction (rule-based fallback, no LLM by default)
    intent = await extract_intent(lang_result.normalized_text)

    # Step 3: Safety check
    safety = await check_safety(intent, raw_text=params.text)

    result: Dict[str, Any] = {
        "language": lang_result.model_dump(),
        "intent": intent.model_dump(),
        "safety": safety.model_dump(),
    }

    # Step 4: (optional) Execution
    if params.execute:
        exec_result = await execute_intent(intent, safety)
        result["execution"] = exec_result

    return json.dumps(result, indent=2, default=str)


@mcp.tool(
    name="india_mcp_store_memory",
    annotations={
        "title": "Store Memory",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def store_memory(params: StoreMemoryInput) -> str:
    """Store a memory record in the tiered memory system.

    Args:
        params (StoreMemoryInput): Validated input containing:
            - user_id (str): Agent / user identifier
            - intent (str): Canonical intent name
            - tier (str): short_term | episodic | semantic
            - language (str): Language code
            - data (dict): Structured payload
            - importance_score (float): 0.0–1.0; must be ≥0.4 for episodic/semantic to persist

    Returns:
        str: JSON of the stored MemoryRecord
    """
    from app.core.memory import store_memory as _store
    from app.models.schemas import MemoryRecord, MemoryTier

    record = MemoryRecord(
        user_id=params.user_id,
        tier=MemoryTier(params.tier),
        intent=params.intent,
        language=params.language,
        data=params.data,
        importance_score=params.importance_score,
    )
    stored = await _store(record)
    return json.dumps(stored.model_dump(), indent=2, default=str)


@mcp.tool(
    name="india_mcp_recall_memory",
    annotations={
        "title": "Recall Memory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def recall_memory(params: RecallMemoryInput) -> str:
    """Retrieve memories from the tiered memory system.

    Args:
        params (RecallMemoryInput): Validated input containing:
            - user_id (str): Agent / user identifier
            - intent (str, optional): Filter by intent
            - tier (str, optional): Filter by tier
            - limit (int): Max results (1–100, default 10)

    Returns:
        str: JSON array of matching MemoryRecords
    """
    from app.core.memory import recall_memory as _recall
    from app.models.schemas import MemoryQuery, MemoryTier

    query = MemoryQuery(
        user_id=params.user_id,
        intent=params.intent,
        tier=MemoryTier(params.tier) if params.tier else None,
        limit=params.limit,
    )
    results = await _recall(query)
    return json.dumps(
        [r.model_dump() for r in results], indent=2, default=str
    )


@mcp.tool(
    name="india_mcp_safe_execute",
    annotations={
        "title": "Safe Execute",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def safe_execute(params: SafeExecuteInput) -> str:
    """Parse, safety-check, and execute a user request end-to-end.

    This is a convenience tool that chains:
      Language → Intent → Safety → Execute

    Args:
        params (SafeExecuteInput): Validated input containing:
            - text (str): Raw user input
            - user_id (str): User / agent identifier

    Returns:
        str: JSON with safety verdict and execution result
    """
    from app.core.language import detect_language
    from app.core.intent import extract_intent
    from app.core.safety import check_safety
    from app.services.executor import execute_intent

    lang = await detect_language(params.text)
    intent = await extract_intent(lang.normalized_text)
    safety = await check_safety(intent, raw_text=params.text)
    exec_result = await execute_intent(intent, safety)

    return json.dumps(
        {
            "intent": intent.model_dump(),
            "safety": safety.model_dump(),
            "execution": exec_result,
        },
        indent=2,
        default=str,
    )


@mcp.tool(
    name="india_mcp_route_agent",
    annotations={
        "title": "Route to Agent",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def route_agent(params: RouteAgentInput) -> str:
    """Route a task to a registered downstream agent.

    Args:
        params (RouteAgentInput): Validated input containing:
            - target_agent (str): Name of the agent to route to
            - task (str): Task description
            - payload (dict): Arbitrary payload

    Returns:
        str: JSON with the agent's response or a fallback error
    """
    from app.services.agent_router import route_to_agent
    from app.models.schemas import AgentRoutingRequest

    request = AgentRoutingRequest(
        target_agent=params.target_agent,
        task=params.task,
        payload=params.payload,
    )
    result = await route_to_agent(request)
    return json.dumps(result, indent=2, default=str)


@mcp.tool(
    name="india_mcp_model_route",
    annotations={
        "title": "Model Route",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def model_route(params: ModelRouteInput) -> str:
    """Query the multi-model AI router.

    If a prompt is provided, the prompt is actually sent to the routed model.
    Otherwise, returns the routing decision only.

    Args:
        params (ModelRouteInput): Validated input containing:
            - task_type (str): multilingual | reasoning | local | general
            - prompt (str, optional): Prompt to send to the chosen model

    Returns:
        str: JSON with routing decision and optional model response
    """
    from app.core.router import route_task, call_llm
    from app.models.schemas import TaskType

    task_type = TaskType(params.task_type)
    decision = route_task(task_type)

    result: Dict[str, Any] = {"routing": decision.model_dump()}

    if params.prompt:
        try:
            response = await call_llm(params.prompt, task_type)
            result["model_response"] = response
        except Exception as exc:
            result["model_response"] = f"Error: {exc}"

    return json.dumps(result, indent=2, default=str)


@mcp.tool(
    name="india_mcp_transcribe_audio",
    annotations={
        "title": "Transcribe Audio",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def transcribe_audio(params: TranscribeInput) -> str:
    """Transcribe an audio file to text using Whisper STT.

    Args:
        params: Validated input containing the audio_path.

    Returns:
        str: JSON with the transcribed text.
    """
    from app.core.voice import voice_service
    text = await voice_service.transcribe_audio(params.audio_path)
    return json.dumps({"text": text}, indent=2, default=str)


@mcp.tool(
    name="india_mcp_synthesize_speech",
    annotations={
        "title": "Synthesize Speech",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def synthesize_speech(params: SynthesizeInput) -> str:
    """Synthesize text to speech using Coqui TTS.

    Args:
        params: Validated input containing text and language.

    Returns:
        str: JSON with the path to the generated audio file.
    """
    from app.core.voice import voice_service
    audio_path = await voice_service.synthesize_speech(params.text, params.language)
    return json.dumps({"audio_path": audio_path}, indent=2, default=str)


@mcp.tool(
    name="india_mcp_feedback",
    annotations={
        "title": "Log RLHF Feedback",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def log_feedback_tool(params: FeedbackInput) -> str:
    """Submit Reinforcement Learning from Human Feedback (RLHF) data for agent tuning."""
    from app.core.rlhf import log_feedback
    record = log_feedback(params.intent, params.model, params.rating, params.feedback_text)
    return json.dumps(record, indent=2, default=str)


@mcp.tool(
    name="india_mcp_assemble_context",
    annotations={
        "title": "Assemble Code Context (Arachne Protocol)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def assemble_context_tool(params: AssembleContextInput) -> str:
    """Scan the codebase and assemble the most relevant file chunks based on a query."""
    from app.core.arachne import assemble_context
    chunks = assemble_context(params.query, params.dir)
    return json.dumps(chunks, indent=2, default=str)


# ─────────────── Entry Point ─────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
