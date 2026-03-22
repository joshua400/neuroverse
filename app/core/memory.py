#!/usr/bin/env python3
"""
Tiered Memory System.

Architecture:
  • Short-term  — in-process dict (current session)
  • Episodic    — recent actions (PostgreSQL)
  • Semantic    — long-term facts (PostgreSQL)

Key design decisions:
  • Memory is scored for importance before storing.  Only records above
    the configurable threshold are persisted to the DB.
  • Context compression: stores structured JSON payloads, NOT raw text.
  • In-memory short-term cache avoids DB round-trips for the active session.
  • SQLAlchemy async engine for PostgreSQL access.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import httpx
import os

from app.models.schemas import MemoryQuery, MemoryRecord, MemoryTier

# ─────────────────── Embeddings & Math ────────────────────────────────────

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2: return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(a * a for a in v2))
    if not mag1 or not mag2: return 0.0
    return dot / (mag1 * mag2)

async def generate_embedding(text: str) -> Optional[List[float]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not text:
        return None
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-3-small", "input": text},
                timeout=5.0
            )
            res.raise_for_status()
            data = res.json()
            return data["data"][0]["embedding"]
    except Exception:
        return None

# ─────────────────── Configuration ───────────────────────────────────────

IMPORTANCE_THRESHOLD: float = 0.4  # Minimum score to persist

# ─────────────────── In-memory short-term store ──────────────────────────

_short_term: Dict[str, List[MemoryRecord]] = defaultdict(list)

# ─────────────────── PostgreSQL Store (async) ────────────────────────────
# The actual DB engine is created lazily in `_get_engine` so the module can
# be imported without a running Postgres instance (useful in tests).

_engine = None
_TABLE_CREATED = False

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS memory_records (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    tier        TEXT NOT NULL,
    intent      TEXT NOT NULL,
    language    TEXT NOT NULL DEFAULT 'en',
    data        JSONB NOT NULL DEFAULT '{}',
    importance  REAL NOT NULL DEFAULT 0.5,
    vector      JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_records(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_intent ON memory_records(intent);
CREATE INDEX IF NOT EXISTS idx_memory_tier ON memory_records(tier);
"""


async def _get_engine():
    """Lazily create an asyncpg-backed SQLAlchemy engine."""
    global _engine, _TABLE_CREATED
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.config import settings

        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )
    if not _TABLE_CREATED:
        from sqlalchemy import text

        async with _engine.begin() as conn:
            for stmt in _CREATE_TABLE_SQL.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    await conn.execute(text(stmt))
        _TABLE_CREATED = True
    return _engine


# ─────────────────── Public API ──────────────────────────────────────────


async def store_memory(record: MemoryRecord) -> MemoryRecord:
    """Store a memory record.

    • Short-term records are kept in-process.
    • Episodic / Semantic records are written to PostgreSQL **only**
      if ``importance_score >= IMPORTANCE_THRESHOLD``.
    """
    if record.id is None:
        record.id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    record.created_at = record.created_at or now
    record.updated_at = now

    if record.tier != MemoryTier.SHORT_TERM and record.importance_score >= IMPORTANCE_THRESHOLD:
        import json
        text_to_embed = json.dumps(record.data)
        if text_to_embed and text_to_embed != "{}":
            vector = await generate_embedding(text_to_embed)
            if vector:
                record.vector = vector

    if record.tier == MemoryTier.SHORT_TERM:
        _short_term[record.user_id].append(record)
        # Cap per-user short-term entries to 50
        if len(_short_term[record.user_id]) > 50:
            _short_term[record.user_id] = _short_term[record.user_id][-50:]
        return record

    # Only persist if above threshold
    if record.importance_score < IMPORTANCE_THRESHOLD:
        return record  # silently skip

    await _insert_record(record)
    return record


async def recall_memory(query: MemoryQuery) -> List[MemoryRecord]:
    """Retrieve memories matching *query*."""
    results: List[MemoryRecord] = []

    # Always include short-term for this user
    for rec in _short_term.get(query.user_id, []):
        if query.intent and rec.intent != query.intent:
            continue
        if query.tier and rec.tier != query.tier:
            continue
        results.append(rec)

    # If requesting only short-term, return now
    if query.tier == MemoryTier.SHORT_TERM:
        return results[: query.limit]

    # Query PostgreSQL for episodic / semantic
    db_results = await _query_records(query)
    results.extend(db_results)

    # Semantic Reranking
    if query.semantic_query and len(results) > 0:
        q_vec = await generate_embedding(query.semantic_query)
        if q_vec:
            def _score(r):
                if not r.vector: return -1.0
                return cosine_similarity(q_vec, r.vector)
            results.sort(key=_score, reverse=True)
            return results[: query.limit]

    # Sort by recency and limit if no semantic query
    results.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
    return results[: query.limit]


async def clear_short_term(user_id: str) -> int:
    """Flush the short-term memory for *user_id*.  Returns count removed."""
    count = len(_short_term.pop(user_id, []))
    return count


# ─────────────────── DB helpers ──────────────────────────────────────────


async def _insert_record(record: MemoryRecord) -> None:
    import json
    from sqlalchemy import text

    engine = await _get_engine()
    sql = text("""
        INSERT INTO memory_records (id, user_id, tier, intent, language, data, importance, vector, created_at, updated_at)
        VALUES (:id, :user_id, :tier, :intent, :language, :data::jsonb, :importance, :vector::jsonb, :created_at, :updated_at)
        ON CONFLICT (id) DO UPDATE SET
            data = EXCLUDED.data,
            importance = EXCLUDED.importance,
            vector = EXCLUDED.vector,
            updated_at = EXCLUDED.updated_at
    """)
    async with engine.begin() as conn:
        await conn.execute(
            sql,
            {
                "id": record.id,
                "user_id": record.user_id,
                "tier": record.tier.value,
                "intent": record.intent,
                "language": record.language,
                "data": json.dumps(record.data),
                "importance": record.importance_score,
                "vector": json.dumps(record.vector) if record.vector else None,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            },
        )


async def _query_records(query: MemoryQuery) -> List[MemoryRecord]:
    import json
    from sqlalchemy import text

    engine = await _get_engine()
    clauses = ["user_id = :user_id"]
    params: Dict[str, Any] = {"user_id": query.user_id, "limit": query.limit}

    if query.intent:
        clauses.append("intent = :intent")
        params["intent"] = query.intent
    if query.tier:
        clauses.append("tier = :tier")
        params["tier"] = query.tier.value

    where = " AND ".join(clauses)
    sql = text(
        f"SELECT * FROM memory_records WHERE {where} ORDER BY created_at DESC LIMIT :limit"
    )

    async with engine.connect() as conn:
        result = await conn.execute(sql, params)
        rows = result.mappings().all()

    records: List[MemoryRecord] = []
    for row in rows:
        data = row["data"]
        if isinstance(data, str):
            data = json.loads(data)
        records.append(
            MemoryRecord(
                id=row["id"],
                user_id=row["user_id"],
                tier=MemoryTier(row["tier"]),
                intent=row["intent"],
                language=row["language"],
                data=data,
                importance_score=row["importance"],
                vector=json.loads(row["vector"]) if row["vector"] else None,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        )
    return records
