/**
 * Setu — Agent-to-Agent Router.
 *
 * Registry, discovery, and HTTP routing to downstream agents.
 */
import axios from "axios";
// ─── Agent registry ─────────────────────────────────────────────────────
const registry = new Map();
export function registerAgent(agent) {
    registry.set(agent.agentName, agent);
}
export function unregisterAgent(name) {
    return registry.delete(name);
}
export function listAgents() {
    return [...registry.values()];
}
export function getAgent(name) {
    return registry.get(name);
}
// ─── Routing ────────────────────────────────────────────────────────────
export async function routeToAgent(request) {
    const agent = getAgent(request.targetAgent);
    if (!agent) {
        return { success: false, error: `Agent '${request.targetAgent}' is not registered.`, fallback: true };
    }
    try {
        const resp = await axios.post(agent.endpoint, { task: request.task, payload: request.payload }, { headers: { "Content-Type": "application/json" }, timeout: 30000 });
        return { success: true, agent: request.targetAgent, response: resp.data };
    }
    catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return { success: false, error: `Agent unreachable: ${msg}`, fallback: true };
    }
}
//# sourceMappingURL=agent-router.js.map