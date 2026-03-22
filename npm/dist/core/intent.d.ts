/**
 * Bodhi — Intent Extraction Engine.
 *
 * Strategy:
 *   1. Try LLM extraction (if callable provided)
 *   2. Fall back to rule-based deterministic parser
 *   3. Always return a valid ExtractedIntent
 */
import type { ExtractedIntent, LLMCall } from "../types.js";
/**
 * Rule-based intent extraction (deterministic fallback).
 */
export declare function ruleBasedExtract(text: string): ExtractedIntent;
/**
 * Extract intent — LLM first, rule-based fallback.
 */
export declare function extractIntent(text: string, llmCall?: LLMCall): Promise<ExtractedIntent>;
//# sourceMappingURL=intent.d.ts.map