/**
 * Setu — Agent-to-Agent Router.
 *
 * Registry, discovery, and HTTP routing to downstream agents.
 */

import axios from "axios";
import type { AgentDefinition, AgentRoutingRequest } from "../types.js";

// ─── Agent registry ─────────────────────────────────────────────────────

const registry = new Map<string, AgentDefinition>();

export function registerAgent(agent: AgentDefinition): void {
  registry.set(agent.agentName, agent);
}

export function unregisterAgent(name: string): boolean {
  return registry.delete(name);
}

export function listAgents(): AgentDefinition[] {
  return [...registry.values()];
}

export function getAgent(name: string): AgentDefinition | undefined {
  return registry.get(name);
}

// ─── Routing ────────────────────────────────────────────────────────────

export async function routeToAgent(
  request: AgentRoutingRequest
): Promise<Record<string, unknown>> {
  const agent = getAgent(request.targetAgent);
  if (!agent) {
    return { success: false, error: `Agent '${request.targetAgent}' is not registered.`, fallback: true };
  }

  try {
    const resp = await axios.post(
      agent.endpoint,
      { task: request.task, payload: request.payload },
      { headers: { "Content-Type": "application/json" }, timeout: 30000 }
    );
    return { success: true, agent: request.targetAgent, response: resp.data };
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return { success: false, error: `Agent unreachable: ${msg}`, fallback: true };
  }
}
