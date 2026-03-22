/**
 * NeuroVerse — TypeScript type definitions.
 */

// ─── Enums ──────────────────────────────────────────────────────────────

export enum RiskLevel {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum MemoryTier {
  SHORT_TERM = "short_term",
  EPISODIC = "episodic",
  SEMANTIC = "semantic",
}

export enum TaskType {
  MULTILINGUAL = "multilingual",
  REASONING = "reasoning",
  LOCAL = "local",
  GENERAL = "general",
}

export enum ModelProvider {
  OPENAI = "openai",
  ANTHROPIC = "anthropic",
  OLLAMA = "ollama",
  SARVAM = "sarvam",
  OPENROUTER = "openrouter",
}

// ─── Interfaces ─────────────────────────────────────────────────────────

export interface LanguageDetectionResult {
  languages: string[];
  confidence: number;
  isCodeSwitched: boolean;
  originalText: string;
  normalizedText: string;
}

export interface ExtractedIntent {
  intent: string;
  parameters: Record<string, string>;
  confidence: number;
  source: "llm" | "rule" | "test";
}

export interface MemoryRecord {
  id: string;
  userId: string;
  tier: MemoryTier;
  intent: string;
  language: string;
  data: Record<string, unknown>;
  importanceScore: number;
  vector?: number[];
  createdAt: string;
  updatedAt: string;
}

export interface MemoryQuery {
  userId: string;
  intent?: string;
  tier?: MemoryTier;
  semanticQuery?: string;
  limit: number;
}

export interface SafetyVerdict {
  allowed: boolean;
  riskLevel: RiskLevel;
  reason: string;
  blockedBy?: string;
}

export interface ModelRoutingDecision {
  provider: ModelProvider;
  modelName: string;
  reason: string;
}

export interface AgentDefinition {
  agentName: string;
  endpoint: string;
  capabilities: string[];
}

export interface AgentRoutingRequest {
  targetAgent: string;
  task: string;
  payload: Record<string, unknown>;
}

export interface ExecutionResult {
  success: boolean;
  output: string;
  tool: string;
}

/** Callable for LLM inference (prompt → response). */
export type LLMCall = (prompt: string) => Promise<string>;
