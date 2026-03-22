/**
 * Tool Executor — maps intents to registered tool functions with retry logic.
 */
import type { ExtractedIntent, SafetyVerdict, ExecutionResult } from "../types.js";
type ToolFunc = (params: Record<string, string>) => Promise<string>;
export declare function registerTool(name: string, fn: ToolFunc): void;
export declare function executeIntent(intent: ExtractedIntent, safety: SafetyVerdict, extraContext?: Record<string, string>): Promise<ExecutionResult>;
export {};
//# sourceMappingURL=executor.d.ts.map