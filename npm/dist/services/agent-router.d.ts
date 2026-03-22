/**
 * Setu — Agent-to-Agent Router.
 *
 * Registry, discovery, and HTTP routing to downstream agents.
 */
import type { AgentDefinition, AgentRoutingRequest } from "../types.js";
export declare function registerAgent(agent: AgentDefinition): void;
export declare function unregisterAgent(name: string): boolean;
export declare function listAgents(): AgentDefinition[];
export declare function getAgent(name: string): AgentDefinition | undefined;
export declare function routeToAgent(request: AgentRoutingRequest): Promise<Record<string, unknown>>;
//# sourceMappingURL=agent-router.d.ts.map