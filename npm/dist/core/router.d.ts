/**
 * Marga — Multi-Model AI Router.
 *
 * Routes tasks to the best-suited LLM provider:
 *   multilingual → Sarvam AI
 *   reasoning    → Anthropic / OpenAI
 *   local        → Ollama
 *   general      → best available
 */
import { TaskType } from "../types.js";
import type { ModelRoutingDecision } from "../types.js";
interface RouterConfig {
    openaiApiKey?: string;
    anthropicApiKey?: string;
    sarvamApiKey?: string;
    ollamaBaseUrl: string;
}
export declare function configureRouter(cfg: Partial<RouterConfig>): void;
export declare function routeTask(taskType: TaskType): ModelRoutingDecision;
export declare function callLLM(prompt: string, taskType?: TaskType): Promise<string>;
export {};
//# sourceMappingURL=router.d.ts.map