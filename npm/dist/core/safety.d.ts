/**
 * Kavach — 3-Layer Safety Engine.
 *
 * Layer 1: Rule-based blocklist (keywords + regex) — zero tokens, < 1ms
 * Layer 2: Intent risk classification (deterministic map)
 * Layer 3: Optional LLM judge (async, costs tokens)
 *
 * Action Guard:
 *   CRITICAL / HIGH → always block
 *   MEDIUM + strict mode → block
 *   LOW → always allow
 */
import { RiskLevel } from "../types.js";
import type { ExtractedIntent, SafetyVerdict, LLMCall } from "../types.js";
export declare function setStrictMode(enabled: boolean): void;
declare function checkBlocklist(rawText: string, intent: ExtractedIntent): SafetyVerdict | null;
declare function classifyRisk(intent: ExtractedIntent): RiskLevel;
/**
 * Run the full 3-layer safety pipeline.
 */
export declare function checkSafety(intent: ExtractedIntent, rawText?: string, llmCall?: LLMCall): Promise<SafetyVerdict>;
export { checkBlocklist as _checkBlocklist, classifyRisk as _classifyRisk };
//# sourceMappingURL=safety.d.ts.map