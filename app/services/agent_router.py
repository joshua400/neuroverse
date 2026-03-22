#!/usr/bin/env python3
"""
Agent-to-Agent (A2A) Router.

Implements:
  • Standardised Protocol (REST + JSON schema)
  • Agent Registry (discover and register downstream agents)
  • Fallback to local execution if a remote agent is unreachable
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from app.models.schemas import AgentDefinition, AgentRoutingRequest

# ───────────── Agent Registry ────────────────────────────────────────────

_AGENT_REGISTRY: Dict[str, AgentDefinition] = {}


def register_agent(agent: AgentDefinition) -> None:
    """Register a downstream agent."""
    _AGENT_REGISTRY[agent.agent_name] = agent


def unregister_agent(agent_name: str) -> bool:
    """Remove an agent from the registry.  Returns True if found."""
    return _AGENT_REGISTRY.pop(agent_name, None) is not None


def list_agents() -> List[AgentDefinition]:
    """Return all registered agents."""
    return list(_AGENT_REGISTRY.values())


def get_agent(name: str) -> Optional[AgentDefinition]:
    """Retrieve a single agent definition by name."""
    return _AGENT_REGISTRY.get(name)


# ───────────── Routing ───────────────────────────────────────────────────


async def route_to_agent(request: AgentRoutingRequest) -> Dict[str, Any]:
    """Route a task to the named agent.

    If the target agent is registered and reachable, forwards the
    payload via HTTP POST and returns the response.

    Falls back to a local error result if the agent is not registered
    or the HTTP call fails.
    """
    agent = get_agent(request.target_agent)
    if agent is None:
        return {
            "success": False,
            "error": f"Agent '{request.target_agent}' is not registered.",
            "fallback": True,
        }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                agent.endpoint,
                json={
                    "task": request.task,
                    "payload": request.payload,
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            return {
                "success": True,
                "agent": request.target_agent,
                "response": resp.json(),
            }
    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "error": f"Agent returned HTTP {exc.response.status_code}",
            "fallback": True,
        }
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        return {
            "success": False,
            "error": f"Agent unreachable: {type(exc).__name__}",
            "fallback": True,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Unexpected error: {exc}",
            "fallback": True,
        }
