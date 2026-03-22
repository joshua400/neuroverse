/**
 * Marga — Multi-Model AI Router.
 *
 * Routes tasks to the best-suited LLM provider:
 *   multilingual → Sarvam AI
 *   reasoning    → Anthropic / OpenAI
 *   local        → Ollama
 *   general      → best available
 */

import axios from "axios";
import { ModelProvider, TaskType } from "../types.js";
import type { ModelRoutingDecision, LLMCall } from "../types.js";

// ─── Configuration ──────────────────────────────────────────────────────

interface RouterConfig {
  openaiApiKey?: string;
  anthropicApiKey?: string;
  sarvamApiKey?: string;
  ollamaBaseUrl: string;
}

let config: RouterConfig = {
  ollamaBaseUrl: "http://localhost:11434",
};

export function configureRouter(cfg: Partial<RouterConfig>): void {
  config = { ...config, ...cfg };
}

// ─── Default models ─────────────────────────────────────────────────────

const DEFAULT_MODELS: Record<ModelProvider, string> = {
  [ModelProvider.OPENAI]: "gpt-4o",
  [ModelProvider.ANTHROPIC]: "claude-sonnet-4-20250514",
  [ModelProvider.OLLAMA]: "llama3",
  [ModelProvider.SARVAM]: "sarvam-2b-v0.5",
};

// ─── Routing logic ──────────────────────────────────────────────────────

export function routeTask(taskType: TaskType): ModelRoutingDecision {
  if (taskType === TaskType.MULTILINGUAL) {
    if (config.sarvamApiKey) {
      return {
        provider: ModelProvider.SARVAM,
        modelName: DEFAULT_MODELS[ModelProvider.SARVAM],
        reason: "Multilingual task — routing to Sarvam AI for Indian-language support.",
      };
    }
    return fallbackDecision("Sarvam not configured; falling back for multilingual.");
  }

  if (taskType === TaskType.REASONING) {
    if (config.anthropicApiKey) {
      return {
        provider: ModelProvider.ANTHROPIC,
        modelName: DEFAULT_MODELS[ModelProvider.ANTHROPIC],
        reason: "Reasoning task — routing to Anthropic for strong analytical capability.",
      };
    }
    if (config.openaiApiKey) {
      return {
        provider: ModelProvider.OPENAI,
        modelName: DEFAULT_MODELS[ModelProvider.OPENAI],
        reason: "Reasoning task — routing to OpenAI (Anthropic unavailable).",
      };
    }
    return fallbackDecision("No reasoning provider available.");
  }

  if (taskType === TaskType.LOCAL) {
    return {
      provider: ModelProvider.OLLAMA,
      modelName: DEFAULT_MODELS[ModelProvider.OLLAMA],
      reason: "Local task — routing to Ollama for on-device execution.",
    };
  }

  return fallbackDecision("General task — using best available provider.");
}

function fallbackDecision(reason: string): ModelRoutingDecision {
  if (config.openaiApiKey) {
    return { provider: ModelProvider.OPENAI, modelName: DEFAULT_MODELS[ModelProvider.OPENAI], reason };
  }
  if (config.anthropicApiKey) {
    return { provider: ModelProvider.ANTHROPIC, modelName: DEFAULT_MODELS[ModelProvider.ANTHROPIC], reason };
  }
  return {
    provider: ModelProvider.OLLAMA,
    modelName: DEFAULT_MODELS[ModelProvider.OLLAMA],
    reason: reason + " Falling back to Ollama (local).",
  };
}

// ─── Provider dispatch ──────────────────────────────────────────────────

export async function callLLM(prompt: string, taskType: TaskType = TaskType.GENERAL): Promise<string> {
  const decision = routeTask(taskType);
  return dispatch(prompt, decision);
}

async function dispatch(prompt: string, decision: ModelRoutingDecision): Promise<string> {
  switch (decision.provider) {
    case ModelProvider.OPENAI:
      return callOpenAI(prompt, decision.modelName);
    case ModelProvider.ANTHROPIC:
      return callAnthropic(prompt, decision.modelName);
    case ModelProvider.SARVAM:
      return callSarvam(prompt, decision.modelName);
    case ModelProvider.OLLAMA:
      return callOllama(prompt, decision.modelName);
    default:
      throw new Error(`Unknown provider: ${decision.provider}`);
  }
}

async function callOpenAI(prompt: string, model: string): Promise<string> {
  const resp = await axios.post(
    "https://api.openai.com/v1/chat/completions",
    { model, messages: [{ role: "user", content: prompt }], temperature: 0.3 },
    { headers: { Authorization: `Bearer ${config.openaiApiKey}`, "Content-Type": "application/json" }, timeout: 60000 }
  );
  return resp.data.choices[0].message.content;
}

async function callAnthropic(prompt: string, model: string): Promise<string> {
  const resp = await axios.post(
    "https://api.anthropic.com/v1/messages",
    { model, max_tokens: 2048, messages: [{ role: "user", content: prompt }] },
    {
      headers: {
        "x-api-key": config.anthropicApiKey ?? "",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
      },
      timeout: 60000,
    }
  );
  return resp.data.content[0].text;
}

async function callSarvam(prompt: string, model: string): Promise<string> {
  const resp = await axios.post(
    "https://api.sarvam.ai/v1/chat/completions",
    { model, messages: [{ role: "user", content: prompt }], temperature: 0.3 },
    { headers: { Authorization: `Bearer ${config.sarvamApiKey}`, "Content-Type": "application/json" }, timeout: 60000 }
  );
  return resp.data.choices[0].message.content;
}

async function callOllama(prompt: string, model: string): Promise<string> {
  const resp = await axios.post(
    `${config.ollamaBaseUrl}/api/generate`,
    { model, prompt, stream: false },
    { timeout: 120000 }
  );
  return resp.data.response ?? "";
}
