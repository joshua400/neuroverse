/**
 * NeuroVerse — TypeScript type definitions.
 */
// ─── Enums ──────────────────────────────────────────────────────────────
export var RiskLevel;
(function (RiskLevel) {
    RiskLevel["LOW"] = "low";
    RiskLevel["MEDIUM"] = "medium";
    RiskLevel["HIGH"] = "high";
    RiskLevel["CRITICAL"] = "critical";
})(RiskLevel || (RiskLevel = {}));
export var MemoryTier;
(function (MemoryTier) {
    MemoryTier["SHORT_TERM"] = "short_term";
    MemoryTier["EPISODIC"] = "episodic";
    MemoryTier["SEMANTIC"] = "semantic";
})(MemoryTier || (MemoryTier = {}));
export var TaskType;
(function (TaskType) {
    TaskType["MULTILINGUAL"] = "multilingual";
    TaskType["REASONING"] = "reasoning";
    TaskType["LOCAL"] = "local";
    TaskType["GENERAL"] = "general";
})(TaskType || (TaskType = {}));
export var ModelProvider;
(function (ModelProvider) {
    ModelProvider["OPENAI"] = "openai";
    ModelProvider["ANTHROPIC"] = "anthropic";
    ModelProvider["OLLAMA"] = "ollama";
    ModelProvider["SARVAM"] = "sarvam";
    ModelProvider["OPENROUTER"] = "openrouter";
})(ModelProvider || (ModelProvider = {}));
//# sourceMappingURL=types.js.map