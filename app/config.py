#!/usr/bin/env python3
"""
Shared configuration for the India-First MCP server.

Loads environment variables via python-dotenv and exposes
typed settings through a Pydantic BaseSettings-style class.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Immutable application settings populated from environment variables."""

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:password@localhost:5432/india_mcp",
        )
    )

    # ── AI Model Keys ─────────────────────────────────────────────────
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    sarvam_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("SARVAM_API_KEY")
    )

    # ── Ollama (Local) ────────────────────────────────────────────────
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
    )

    # ── Safety ────────────────────────────────────────────────────────
    safety_strict_mode: bool = field(
        default_factory=lambda: os.getenv("SAFETY_STRICT_MODE", "true").lower()
        == "true"
    )

    # ── MCP Transport ─────────────────────────────────────────────────
    mcp_transport: str = field(
        default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio")
    )
    mcp_port: int = field(
        default_factory=lambda: int(os.getenv("MCP_PORT", "8000"))
    )


# Singleton instance — import this everywhere.
settings = Settings()
