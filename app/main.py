#!/usr/bin/env python3
"""
India-First MCP — FastAPI Application Entry Point.

This file provides an optional REST API layer on top of the MCP tools.
It can be used for:
  • Health checks & monitoring
  • Direct HTTP access to the pipeline (for non-MCP clients)
  • Admin endpoints (agent registry, memory inspection)

For MCP clients, use ``mcp/server.py`` directly.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="India-First Multilingual MCP",
    version="0.1.0",
    description=(
        "India-first multilingual intelligence + memory + safety layer "
        "for autonomous AI agents."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────── Health ──────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok", "service": "india-first-mcp"}


# ─────────────── REST wrappers (mirror MCP tools) ────────────────────────


class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1)
    user_id: str = "anonymous"
    execute: bool = True


@app.post("/api/process")
async def api_process(req: ProcessRequest):
    """Run the full multilingual pipeline via REST."""
    from app.core.language import detect_language
    from app.core.intent import extract_intent
    from app.core.safety import check_safety
    from app.services.executor import execute_intent

    lang = await detect_language(req.text)
    intent = await extract_intent(lang.normalized_text)
    safety = await check_safety(intent, raw_text=req.text)

    result: Dict[str, Any] = {
        "language": lang.model_dump(),
        "intent": intent.model_dump(),
        "safety": safety.model_dump(),
    }
    if req.execute:
        exec_result = await execute_intent(intent, safety)
        result["execution"] = exec_result

    return result


class MemoryStoreRequest(BaseModel):
    user_id: str
    intent: str
    tier: str = "short_term"
    language: str = "en"
    data: Dict[str, Any] = {}
    importance_score: float = 0.5


@app.post("/api/memory/store")
async def api_memory_store(req: MemoryStoreRequest):
    """Store a memory record via REST."""
    from app.core.memory import store_memory
    from app.models.schemas import MemoryRecord, MemoryTier

    record = MemoryRecord(
        user_id=req.user_id,
        tier=MemoryTier(req.tier),
        intent=req.intent,
        language=req.language,
        data=req.data,
        importance_score=req.importance_score,
    )
    stored = await store_memory(record)
    return stored.model_dump()


class MemoryRecallRequest(BaseModel):
    user_id: str
    intent: str | None = None
    tier: str | None = None
    limit: int = 10


@app.post("/api/memory/recall")
async def api_memory_recall(req: MemoryRecallRequest):
    """Recall memories via REST."""
    from app.core.memory import recall_memory
    from app.models.schemas import MemoryQuery, MemoryTier

    query = MemoryQuery(
        user_id=req.user_id,
        intent=req.intent,
        tier=MemoryTier(req.tier) if req.tier else None,
        limit=req.limit,
    )
    results = await recall_memory(query)
    return [r.model_dump() for r in results]


# ─────────────── Run ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
