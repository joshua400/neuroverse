#!/usr/bin/env node
/**
 * NeuroVerse — India-First Multilingual MCP Server (npm edition).
 *
 * Exposes 6 tools via Model Context Protocol:
 *   1. neuroverse_process    — Full multilingual pipeline
 *   2. neuroverse_store      — Store memory
 *   3. neuroverse_recall     — Recall memories
 *   4. neuroverse_execute    — Safe end-to-end execution
 *   5. neuroverse_route      — Route to downstream agent
 *   6. neuroverse_model      — Query multi-model router
 *
 * Install:  npm install neuroverse
 * Run:      npx neuroverse   (or node dist/index.js)
 *
 * Built by Joshua Ragiland M — Joshuaragiland.com
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { detectLanguage } from "./core/language.js";
import { extractIntent } from "./core/intent.js";
import { checkSafety, setStrictMode } from "./core/safety.js";
import { storeMemory, recallMemory } from "./core/memory.js";
import { routeTask, callLLM, configureRouter } from "./core/router.js";
import { transcribeAudio, synthesizeSpeech } from "./core/voice.js";
import { logFeedback } from "./core/rlhf.js";
import { assembleContext } from "./core/arachne.js";
import { executeIntent } from "./services/executor.js";
import { routeToAgent } from "./services/agent-router.js";
import { TaskType } from "./types.js";
// ─── Configuration from environment ────────────────────────────────────
configureRouter({
    openaiApiKey: process.env["OPENAI_API_KEY"],
    anthropicApiKey: process.env["ANTHROPIC_API_KEY"],
    sarvamApiKey: process.env["SARVAM_API_KEY"],
    openrouterApiKey: process.env["OPENROUTER_API_KEY"],
    ollamaBaseUrl: process.env["OLLAMA_BASE_URL"] ?? "http://localhost:11434",
});
if (process.env["SAFETY_STRICT_MODE"] === "true") {
    setStrictMode(true);
}
// ─── Create MCP server ─────────────────────────────────────────────────
const server = new McpServer({
    name: "neuroverse-mcp-server",
    version: "4.1.1",
});
// ─── Tool 1: neuroverse_process ─────────────────────────────────────────
const ProcessInputSchema = z
    .object({
    text: z
        .string()
        .min(1, "Text is required")
        .max(5000, "Text must not exceed 5000 characters")
        .describe("Raw user input (may be code-switched, e.g. Tamil+English)"),
    user_id: z
        .string()
        .default("anonymous")
        .describe("Identifier for the user / agent"),
    execute: z
        .boolean()
        .default(true)
        .describe("If true, also execute the extracted intent after safety check"),
})
    .strict();
server.registerTool("neuroverse_process", {
    title: "Process Multilingual Input",
    description: `Process mixed-language input through the full NeuroVerse pipeline.

Pipeline: Language Detect → Normalise → Intent Extract → Safety Check → (optional) Execute

Supported languages: Tamil, Hindi, Telugu, Kannada + English (code-switched).

Args:
  - text (string): Raw user input, possibly code-switched
  - user_id (string): User / agent identifier (default: "anonymous")
  - execute (boolean): Whether to also execute the intent (default: true)

Returns:
  JSON with keys: language, intent, safety, execution (if execute=true)

Examples:
  - "anna indha file ah csv convert pannu" → detects Tamil+English, extracts convert_format
  - "report banao sales ka" → detects Hindi+English, extracts generate_report
  - "drop database production" → BLOCKED by safety layer`,
    inputSchema: ProcessInputSchema,
    annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
    },
}, async (params) => {
    const lang = detectLanguage(params.text);
    const intent = await extractIntent(lang.normalizedText);
    const safety = await checkSafety(intent, params.text);
    const result = {
        language: lang,
        intent,
        safety,
    };
    if (params.execute) {
        const exec = await executeIntent(intent, safety);
        result["execution"] = exec;
    }
    return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
});
// ─── Tool 2: neuroverse_store ───────────────────────────────────────────
const StoreMemorySchema = z
    .object({
    user_id: z.string().min(1).describe("Agent / user identifier"),
    intent: z.string().min(1).describe("Canonical intent this memory relates to"),
    tier: z
        .enum(["short_term", "episodic", "semantic"])
        .default("short_term")
        .describe("Memory tier"),
    language: z.string().default("en").describe("Primary language code"),
    data: z
        .record(z.unknown())
        .default({})
        .describe("Structured memory payload"),
    importance_score: z
        .number()
        .min(0)
        .max(1)
        .default(0.5)
        .describe("Importance score — only above 0.4 are persisted for episodic/semantic"),
})
    .strict();
server.registerTool("neuroverse_store", {
    title: "Store Memory",
    description: `Store a memory record in NeuroVerse's tiered memory system.

Tiers:
  - short_term: In-process, capped at 50 per user. Lost on restart.
  - episodic: Persisted to JSON file. Recent actions.
  - semantic: Persisted to JSON file. Long-term facts.

Only episodic/semantic memories with importance_score ≥ 0.4 are persisted.

Args:
  - user_id (string): Agent / user identifier
  - intent (string): Canonical intent name
  - tier (string): short_term | episodic | semantic
  - language (string): Language code (default: "en")
  - data (object): Structured payload
  - importance_score (number): 0.0–1.0

Returns:
  JSON of the stored MemoryRecord`,
    inputSchema: StoreMemorySchema,
    annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: false,
    },
}, async (params) => {
    const record = await storeMemory({
        userId: params.user_id,
        intent: params.intent,
        tier: params.tier,
        language: params.language,
        data: params.data,
        importanceScore: params.importance_score,
    });
    return {
        content: [{ type: "text", text: JSON.stringify(record, null, 2) }],
    };
});
// ─── Tool 3: neuroverse_recall ──────────────────────────────────────────
const RecallMemorySchema = z
    .object({
    user_id: z.string().min(1).describe("Agent / user identifier"),
    intent: z.string().optional().describe("Filter by intent"),
    tier: z
        .enum(["short_term", "episodic", "semantic"])
        .optional()
        .describe("Filter by tier"),
    semantic_query: z.string().optional().describe("Query for semantic retrieval reranking"),
    limit: z.number().int().min(1).max(100).default(10).describe("Max results"),
})
    .strict();
server.registerTool("neuroverse_recall", {
    title: "Recall Memory",
    description: `Retrieve memories from NeuroVerse's tiered memory system.

Args:
  - user_id (string): Agent / user identifier
  - intent (string, optional): Filter by intent
  - tier (string, optional): Filter by tier
  - semantic_query (string, optional): Search constraint for vector engine
  - limit (number): Max results (1–100, default 10)

Returns:
  JSON array of matching MemoryRecords`,
    inputSchema: RecallMemorySchema,
    annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
    },
}, async (params) => {
    const results = await recallMemory({
        userId: params.user_id,
        intent: params.intent,
        tier: params.tier,
        semanticQuery: params.semantic_query,
        limit: params.limit,
    });
    return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
    };
});
// ─── Tool 4: neuroverse_execute ─────────────────────────────────────────
const SafeExecuteSchema = z
    .object({
    text: z
        .string()
        .min(1)
        .max(5000)
        .describe("Raw user input to parse, safety-check, and execute"),
    user_id: z.string().default("anonymous").describe("User / agent ID"),
})
    .strict();
server.registerTool("neuroverse_execute", {
    title: "Safe Execute",
    description: `Parse, safety-check, and execute a user request end-to-end.

Convenience tool that chains: Language → Intent → Safety → Execute.

Args:
  - text (string): Raw user input
  - user_id (string): User / agent identifier

Returns:
  JSON with safety verdict and execution result`,
    inputSchema: SafeExecuteSchema,
    annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
    },
}, async (params) => {
    const lang = detectLanguage(params.text);
    const intent = await extractIntent(lang.normalizedText);
    const safety = await checkSafety(intent, params.text);
    const exec = await executeIntent(intent, safety);
    return {
        content: [
            {
                type: "text",
                text: JSON.stringify({ intent, safety, execution: exec }, null, 2),
            },
        ],
    };
});
// ─── Tool 5: neuroverse_route ───────────────────────────────────────────
const RouteAgentSchema = z
    .object({
    target_agent: z.string().min(1).describe("Name of the registered agent"),
    task: z.string().min(1).describe("Task description to send"),
    payload: z
        .record(z.unknown())
        .default({})
        .describe("Arbitrary payload for the target"),
})
    .strict();
server.registerTool("neuroverse_route", {
    title: "Route to Agent",
    description: `Route a task to a registered downstream agent via HTTP.

Args:
  - target_agent (string): Name of the agent
  - task (string): Task description
  - payload (object): Arbitrary payload

Returns:
  JSON with the agent's response or a fallback error`,
    inputSchema: RouteAgentSchema,
    annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
    },
}, async (params) => {
    const result = await routeToAgent({
        targetAgent: params.target_agent,
        task: params.task,
        payload: params.payload,
    });
    return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
});
// ─── Tool 6: neuroverse_model ───────────────────────────────────────────
const ModelRouteSchema = z
    .object({
    task_type: z
        .enum(["multilingual", "reasoning", "local", "general"])
        .default("general")
        .describe("Task type for routing"),
    prompt: z
        .string()
        .optional()
        .describe("Optional prompt to actually send to the routed model"),
})
    .strict();
server.registerTool("neuroverse_model", {
    title: "Model Route",
    description: `Query the multi-model AI router.

If a prompt is provided, the prompt is sent to the routed model.
Otherwise, returns only the routing decision.

Supported providers: OpenAI, Anthropic, Sarvam AI, Ollama.

Args:
  - task_type (string): multilingual | reasoning | local | general
  - prompt (string, optional): Prompt to send

Returns:
  JSON with routing decision and optional model response`,
    inputSchema: ModelRouteSchema,
    annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
    },
}, async (params) => {
    const taskType = params.task_type;
    const decision = routeTask(taskType);
    const result = { routing: decision };
    if (params.prompt) {
        try {
            const response = await callLLM(params.prompt, taskType);
            result["model_response"] = response;
        }
        catch (e) {
            result["model_response"] = `Error: ${e instanceof Error ? e.message : String(e)}`;
        }
    }
    return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
});
// ─── Tool 7: neuroverse_transcribe ──────────────────────────────────────
const TranscribeSchema = z
    .object({
    audio_path: z.string().min(1).describe("Absolute path to the audio file to transcribe"),
})
    .strict();
server.registerTool("neuroverse_transcribe", {
    title: "Transcribe Audio",
    description: `Transcribe an audio file to text using Whisper STT.

Args:
  - audio_path (string): Absolute path to the audio file

Returns:
  JSON with the transcribed text`,
    inputSchema: TranscribeSchema,
    annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
    },
}, async (params) => {
    const text = await transcribeAudio(params.audio_path);
    return {
        content: [{ type: "text", text: JSON.stringify({ text }, null, 2) }],
    };
});
// ─── Tool 8: neuroverse_synthesize ──────────────────────────────────────
const SynthesizeSchema = z
    .object({
    text: z.string().min(1).describe("Text to synthesize into speech"),
    language: z.string().default("en").describe("Language code (e.g. en, ta, hi)"),
})
    .strict();
server.registerTool("neuroverse_synthesize", {
    title: "Synthesize Speech",
    description: `Synthesize text to speech using Coqui TTS.

Args:
  - text (string): Text to synthesize
  - language (string): Language code

Returns:
  JSON with the path to the generated audio file`,
    inputSchema: SynthesizeSchema,
    annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
    },
}, async (params) => {
    const audio_path = await synthesizeSpeech(params.text, params.language);
    return {
        content: [{ type: "text", text: JSON.stringify({ audio_path }, null, 2) }],
    };
});
// ─── Tool 9: neuroverse_feedback ────────────────────────────────────────
const FeedbackSchema = z
    .object({
    intent: z.string().min(1).describe("The intent executed"),
    model: z.string().min(1).describe("The model used"),
    rating: z.number().int().min(1).max(5).describe("Rating from 1 to 5"),
    feedback_text: z.string().optional().describe("Optional human-readable feedback"),
})
    .strict();
server.registerTool("neuroverse_feedback", {
    title: "Log RLHF Feedback",
    description: "Submit Reinforcement Learning from Human Feedback (RLHF) data for agent tuning.",
    inputSchema: FeedbackSchema,
    annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: false,
    },
}, async (params) => {
    const record = logFeedback(params.intent, params.model, params.rating, params.feedback_text);
    return {
        content: [{ type: "text", text: JSON.stringify(record, null, 2) }],
    };
});
// ─── Tool 10: neuroverse_assemble_context ───────────────────────────────
const AssembleContextSchema = z
    .object({
    query: z.string().min(1).describe("Search query for context assembly"),
    dir: z.string().optional().describe("Root directory to scan (defaults to cwd)"),
})
    .strict();
server.registerTool("neuroverse_assemble_context", {
    title: "Assemble Code Context (Arachne Protocol)",
    description: "Scan the codebase and assemble the most relevant file chunks based on a query.",
    inputSchema: AssembleContextSchema,
    annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
    },
}, async (params) => {
    const chunks = assembleContext(params.query, params.dir);
    return {
        content: [{ type: "text", text: JSON.stringify(chunks, null, 2) }],
    };
});
// ─── Tool 11: neuroverse_reason ─────────────────────────────────────────
const ReasonSchema = z
    .object({
    prompt: z.string().min(1).describe("The complex prompt requiring high-performance reasoning"),
})
    .strict();
server.registerTool("neuroverse_reason", {
    title: "High-Performance Reason",
    description: "Execute a complex reasoning task using specialized high-performance models (e.g. OpenRouter Reasoning). Returns the model's analytical response.",
    inputSchema: ReasonSchema,
    annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
    },
}, async (params) => {
    try {
        const response = await callLLM(params.prompt, TaskType.REASONING);
        return {
            content: [{ type: "text", text: response }],
        };
    }
    catch (e) {
        return {
            content: [{ type: "text", text: `Error: ${e instanceof Error ? e.message : String(e)}` }],
            isError: true,
        };
    }
});
// ─── Boot ───────────────────────────────────────────────────────────────
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("🧠 NeuroVerse MCP server running via stdio");
}
main().catch((error) => {
    console.error("NeuroVerse server error:", error);
    process.exit(1);
});
//# sourceMappingURL=index.js.map