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
// ─── Configuration ──────────────────────────────────────────────────────
let strictMode = false;
export function setStrictMode(enabled) {
    strictMode = enabled;
}
// ─── Layer 1: Blocklist ─────────────────────────────────────────────────
const BLOCKED_KEYWORDS = [
    "delete_all_data",
    "drop_database",
    "drop_table",
    "system_shutdown",
    "format_disk",
    "rm -rf",
    "truncate",
    "shutdown",
    "reboot",
    "erase_all",
    "destroy",
];
const BLOCKED_PATTERNS = [
    /\bdrop\s+(database|table|schema)\b/i,
    /\bdelete\s+from\s+\*/i,
    /\btruncate\s+table\b/i,
    /\bformat\s+[a-z]:/i,
    /\brm\s+(-rf|--force)\b/i,
];
function checkBlocklist(rawText, intent) {
    const combined = `${rawText} ${intent.intent}`.toLowerCase();
    for (const kw of BLOCKED_KEYWORDS) {
        if (combined.includes(kw)) {
            return {
                allowed: false,
                riskLevel: RiskLevel.CRITICAL,
                reason: `Blocked keyword detected: '${kw}'`,
                blockedBy: "rule",
            };
        }
    }
    for (const pattern of BLOCKED_PATTERNS) {
        if (pattern.test(combined)) {
            return {
                allowed: false,
                riskLevel: RiskLevel.CRITICAL,
                reason: `Blocked pattern matched: ${pattern.source}`,
                blockedBy: "rule",
            };
        }
    }
    return null; // no match
}
// ─── Layer 2: Intent risk map ───────────────────────────────────────────
const INTENT_RISK_MAP = {
    delete_data: RiskLevel.HIGH,
    drop_database: RiskLevel.CRITICAL,
    system_shutdown: RiskLevel.CRITICAL,
    send_message: RiskLevel.MEDIUM,
    convert_format: RiskLevel.LOW,
    summarize: RiskLevel.LOW,
    generate_report: RiskLevel.LOW,
    query_data: RiskLevel.LOW,
    explain: RiskLevel.LOW,
    unknown: RiskLevel.MEDIUM,
};
function classifyRisk(intent) {
    return INTENT_RISK_MAP[intent.intent] ?? RiskLevel.MEDIUM;
}
// ─── Layer 3: Optional LLM judge ────────────────────────────────────────
async function modelSafetyCheck(intent, rawText, llmCall) {
    const prompt = `You are a safety classifier. Given the following user request and ` +
        `extracted intent, respond with ONLY a JSON object:\n` +
        `{"safe": true/false, "reason": "..."}\n\n` +
        `User request: ${rawText}\n` +
        `Intent: ${intent.intent}\n` +
        `Parameters: ${JSON.stringify(intent.parameters)}\n`;
    try {
        const raw = await llmCall(prompt);
        const result = JSON.parse(raw.trim());
        if (!result.safe) {
            return {
                allowed: false,
                riskLevel: RiskLevel.HIGH,
                reason: result.reason ?? "Model-based check flagged this action.",
                blockedBy: "model",
            };
        }
    }
    catch {
        // If model fails, default to allowing (layers 1+2 already passed)
    }
    return null;
}
// ─── Public API ─────────────────────────────────────────────────────────
/**
 * Run the full 3-layer safety pipeline.
 */
export async function checkSafety(intent, rawText = "", llmCall) {
    // Layer 1: Blocklist
    const blocklistVerdict = checkBlocklist(rawText, intent);
    if (blocklistVerdict)
        return blocklistVerdict;
    // Layer 2: Risk classification
    const risk = classifyRisk(intent);
    if (risk === RiskLevel.HIGH || risk === RiskLevel.CRITICAL) {
        return {
            allowed: false,
            riskLevel: risk,
            reason: `Intent '${intent.intent}' classified as ${risk} risk.`,
            blockedBy: "intent_risk",
        };
    }
    if (risk === RiskLevel.MEDIUM && strictMode) {
        return {
            allowed: false,
            riskLevel: risk,
            reason: `Intent '${intent.intent}' is medium risk; strict mode is enabled.`,
            blockedBy: "intent_risk",
        };
    }
    // Layer 3: Optional model check
    if (llmCall) {
        const modelVerdict = await modelSafetyCheck(intent, rawText, llmCall);
        if (modelVerdict)
            return modelVerdict;
    }
    // All clear
    return {
        allowed: true,
        riskLevel: risk,
        reason: "All safety checks passed.",
    };
}
// Re-export helpers for testing
export { checkBlocklist as _checkBlocklist, classifyRisk as _classifyRisk };
//# sourceMappingURL=safety.js.map