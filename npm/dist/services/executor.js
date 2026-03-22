/**
 * Tool Executor — maps intents to registered tool functions with retry logic.
 */
import { MAX_RETRIES } from "../constants.js";
const TOOLS = new Map();
export function registerTool(name, fn) {
    TOOLS.set(name, fn);
}
// ─── Built-in demo tools ────────────────────────────────────────────────
registerTool("convert_format", async (params) => {
    const inputFmt = params["input_format"] ?? "json";
    const outputFmt = params["output_format"] ?? "csv";
    if (inputFmt === "json" && outputFmt === "csv") {
        return 'header1,header2\nvalue1,value2\n(demo conversion — connect real formatter)';
    }
    return `Conversion from ${inputFmt} to ${outputFmt} is not yet implemented.`;
});
registerTool("summarize", async (params) => {
    const text = params["text"] ?? "";
    if (!text)
        return "No text provided to summarize.";
    const words = text.split(/\s+/);
    if (words.length <= 30)
        return text;
    return words.slice(0, 30).join(" ") + "…";
});
registerTool("generate_report", async (params) => {
    return JSON.stringify({ report: "Sales Report", status: "generated", data: params }, null, 2);
});
registerTool("query_data", async (params) => {
    return JSON.stringify({
        query: params["query"] ?? "",
        results: [],
        note: "Demo stub — no real DB connected.",
    });
});
registerTool("explain", async (params) => {
    const topic = params["topic"] ?? "unknown";
    return `Explanation for '${topic}': This is a placeholder. In production, this routes to the LLM.`;
});
// ─── Executor ───────────────────────────────────────────────────────────
export async function executeIntent(intent, safety, extraContext) {
    if (!safety.allowed) {
        return { success: false, output: `Blocked by safety: ${safety.reason}`, tool: intent.intent };
    }
    const toolFn = TOOLS.get(intent.intent);
    if (!toolFn) {
        return { success: false, output: `No tool registered for intent '${intent.intent}'.`, tool: intent.intent };
    }
    const params = { ...intent.parameters, ...(extraContext ?? {}) };
    let lastError = "";
    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {
            const output = await toolFn(params);
            return { success: true, output, tool: intent.intent };
        }
        catch (e) {
            lastError = `Attempt ${attempt} failed: ${e instanceof Error ? e.message : String(e)}`;
        }
    }
    return { success: false, output: `All ${MAX_RETRIES} retries exhausted. Last error: ${lastError}`, tool: intent.intent };
}
//# sourceMappingURL=executor.js.map