/**
 * Bodhi — Intent Extraction Engine.
 *
 * Strategy:
 *   1. Try LLM extraction (if callable provided)
 *   2. Fall back to rule-based deterministic parser
 *   3. Always return a valid ExtractedIntent
 */

import type { ExtractedIntent, LLMCall } from "../types.js";

// ─── Rule patterns ──────────────────────────────────────────────────────

interface RulePattern {
  intent: string;
  keywords: string[];
  confidence: number;
}

const RULE_PATTERNS: RulePattern[] = [
  { intent: "convert_format", keywords: ["convert", "transform", "change format", "export"], confidence: 0.75 },
  { intent: "summarize", keywords: ["summarize", "summarise", "summary", "brief", "tldr"], confidence: 0.8 },
  { intent: "generate_report", keywords: ["report", "generate report", "analytics"], confidence: 0.7 },
  { intent: "delete_data", keywords: ["delete", "remove", "drop", "clean", "erase", "destroy"], confidence: 0.85 },
  { intent: "query_data", keywords: ["query", "search", "find", "fetch", "get", "lookup", "look up"], confidence: 0.7 },
  { intent: "send_message", keywords: ["send", "share", "email", "notify", "message"], confidence: 0.7 },
  { intent: "explain", keywords: ["explain", "describe", "what is", "how to", "tell me about"], confidence: 0.7 },
];

// ─── Format heuristics ──────────────────────────────────────────────────

const FORMAT_KEYWORDS = ["csv", "json", "xml", "pdf", "excel", "xlsx", "yaml", "html", "markdown", "txt"];

function detectFormats(text: string): Record<string, string> {
  const lower = text.toLowerCase();
  const params: Record<string, string> = {};
  const found = FORMAT_KEYWORDS.filter((f) => lower.includes(f));

  if (found.length >= 2) {
    params["input_format"] = found[0];
    params["output_format"] = found[1];
  } else if (found.length === 1) {
    params["output_format"] = found[0];
  }
  return params;
}

// ─── LLM prompt ─────────────────────────────────────────────────────────

const LLM_PROMPT = (text: string) =>
  `You are an intent extraction engine. Given the user input below, respond with ONLY valid JSON:
{"intent": "<canonical_intent>", "parameters": {}, "confidence": 0.0-1.0}

Canonical intents: convert_format, summarize, generate_report, delete_data, query_data, send_message, explain, unknown

User input: "${text}"`;

// ─── Public API ─────────────────────────────────────────────────────────

/**
 * Rule-based intent extraction (deterministic fallback).
 */
export function ruleBasedExtract(text: string): ExtractedIntent {
  const lower = text.toLowerCase();

  for (const rule of RULE_PATTERNS) {
    if (rule.keywords.some((kw) => lower.includes(kw))) {
      return {
        intent: rule.intent,
        parameters: detectFormats(text),
        confidence: rule.confidence,
        source: "rule",
      };
    }
  }

  return { intent: "unknown", parameters: {}, confidence: 0.1, source: "rule" };
}

/**
 * Extract intent — LLM first, rule-based fallback.
 */
export async function extractIntent(
  text: string,
  llmCall?: LLMCall
): Promise<ExtractedIntent> {
  if (!text.trim()) {
    return { intent: "unknown", parameters: {}, confidence: 0, source: "rule" };
  }

  // Try LLM
  if (llmCall) {
    try {
      const raw = await llmCall(LLM_PROMPT(text));
      const parsed = JSON.parse(raw.trim()) as {
        intent?: string;
        parameters?: Record<string, string>;
        confidence?: number;
      };

      if (parsed.intent && (parsed.confidence ?? 0) >= 0.5) {
        return {
          intent: parsed.intent.toLowerCase().replace(/\s+/g, "_"),
          parameters: { ...detectFormats(text), ...(parsed.parameters ?? {}) },
          confidence: parsed.confidence ?? 0.5,
          source: "llm",
        };
      }
    } catch {
      // LLM failed — fall through to rule-based
    }
  }

  return ruleBasedExtract(text);
}
