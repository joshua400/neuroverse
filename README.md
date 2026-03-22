<p align="center">
  <img src="https://img.shields.io/badge/NeuroVerse-v2.0.0-blueviolet?style=for-the-badge" alt="version" />
  <img src="https://img.shields.io/badge/Node.js-18+-339933?style=for-the-badge&logo=node.js&logoColor=white" alt="node" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/License-Apache--2.0-green?style=for-the-badge" alt="license" />
  <img src="https://img.shields.io/badge/MCP-v1.0-orange?style=for-the-badge" alt="MCP" />
  <img src="https://img.shields.io/badge/Tests-40%2F40%20✅-brightgreen?style=for-the-badge" alt="tests" />
  <img src="https://img.shields.io/badge/npm-neuroverse-CB3837?style=for-the-badge&logo=npm&logoColor=white" alt="npm" />
</p>

<h1 align="center">🧠 NeuroVerse</h1>

<p align="center">
  <strong>📦 <a href="https://www.npmjs.com/package/neuroverse">Install from npm</a></strong> | <strong>🐙 <a href="https://github.com/joshua400/neuroverse">GitHub Repository</a></strong>
</p>

<p align="center">
  <strong>Your AI agent only speaks English. NeuroVerse fixes that.</strong><br/>
  <strong>Your AI agent forgets everything. NeuroVerse remembers.</strong><br/>
  <strong>Your AI agent might do something dangerous. NeuroVerse stops that.</strong><br/>
  <strong>Your AI agent is locked to one model. NeuroVerse routes to the best one.</strong>
</p>

<p align="center">
  <em>Multilingual intelligence + memory + safety + voice layer for autonomous AI agents.</em>
</p>

---

## 🚀 What's New in v2.0
- **New Indian Languages**: Added full keyword & trigram support for **Kannada**, **Malayalam**, and **Bengali**. NeuroVerse now understands 6 Indian languages + English natively.
- **Voice Layer**: Built-in support for **Whisper STT** and **Coqui TTS**. Give your agents ears and a voice with the new `neuroverse_transcribe` and `neuroverse_synthesize` tools.

---

## 🚀 What is NeuroVerse?

Every time you start a new chat with Cursor, VS Code Copilot, or any MCP-compatible AI agent, it starts from zero — no memory, no safety, no understanding of your language. NeuroVerse is an MCP server that gives your agents:

| | Feature | Description |
|---|---|---|
| 🌐 | **Multilingual Intelligence** | Understands mixed Indian languages — Tamil, Hindi, Telugu, Kannada, Malayalam, Bengali + English. Code-switching? No problem. |
| 🎙️ | **Voice Layer** | STT via Whisper and TTS via Coqui. Transcribe user audio and synthesize agent responses. |
| 🧠 | **Intent Extraction** | LLM-first structured intent extraction with deterministic rule-based fallback. Never misses a command. |
| 💾 | **Tiered Memory** | Short-term (session), Episodic (recent), Semantic (long-term facts) — all with importance scoring. |
| 🛡️ | **3-Layer Safety (Kavach)** | Keyword blocklist → Intent risk classifier → LLM judge. Blocks `DROP DATABASE` before it's too late. |
| 🤖 | **Multi-Model Router (Marga)** | OpenAI · Anthropic · Sarvam AI · Ollama — routes each task to the best model automatically. |
| 🔗 | **Agent-to-Agent (Setu)** | REST+JSON agent registry with automatic fallback. Agents calling agents calling agents. |
| ⚡ | **Async Everything** | FastAPI + asyncpg + httpx. Sub-millisecond safety checks. Zero blocking. |

> ⚡ NeuroVerse is a modular intelligence layer — not a monolith. Plug in what you need. Ignore what you don't.

---

## Table of Contents

- [Quick Start](#-quick-start)
- [Why NeuroVerse?](#-why-neuroverse)
- [How It Works](#-how-it-works)
- [Multilingual Intelligence (Vani)](#-multilingual-intelligence--vani)
- [Intent Extraction (Bodhi)](#-intent-extraction--bodhi)
- [Tiered Memory (Smriti)](#-tiered-memory--smriti)
- [Safety Layer (Kavach)](#-safety-layer--kavach)
- [Multi-Model Router (Marga)](#-multi-model-router--marga)
- [Agent-to-Agent (Setu)](#-agent-to-agent--setu)
- [MCP Tools](#-mcp-tools)
- [REST API](#-rest-api)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Architecture](#-architecture)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 🚀 Quick Start

### 1. Install

**Option A: npm (recommended) — use anywhere**
```bash
npm install neuroverse
```

**Option B: From source (Python)**
```bash
git clone https://github.com/joshua400/neuroverse.git
cd neuroverse
python -m pip install -e ".[dev]"
```

💡 **Tip:** If you installed via npm, the path is `node_modules/neuroverse/dist/index.js`. If from source, use the absolute path to your cloned directory.

### 2. Add NeuroVerse to your MCP config

NeuroVerse is a standard MCP server (stdio). Add it to your host's config:

**Cursor / VS Code Copilot / Claude Desktop (npm)**
```json
{
  "mcpServers": {
    "neuroverse": {
      "command": "npx",
      "args": ["neuroverse"]
    }
  }
}
```

**From source (Python)**
```json
{
  "mcpServers": {
    "neuroverse": {
      "command": "python",
      "args": ["mcp/server.py"],
      "cwd": "/path/to/neuroverse"
    }
  }
}
```

### 3. Tell your agent to use NeuroVerse

Add this to your agent's rules file (`.md`, `.cursorrules`, system prompt, etc.):

```markdown
## NeuroVerse Integration
- Use `neuroverse_process` to handle any user request — it auto-detects language, extracts intent, checks safety, and executes.
- Use `neuroverse_store` / `neuroverse_recall` for persistent context across sessions.
- Use `neuroverse_execute` for any potentially dangerous action — it will block destructive operations.
```

That's it. Two commands your agent needs to know:

| Command | When | What happens |
|---|---|---|
| `neuroverse_process(text, user_id)` | Any user request | Detects language, extracts intent, safety-checks, executes |
| `neuroverse_store(user_id, intent, ...)` | End of work | Saves context for next session |

Next session, your agent picks up exactly where it left off — like it never forgot.

### Requirements

- **npm edition:** Node.js 18+ (zero database deps — uses JSON files)
- **Python edition:** Python 3.10+ + PostgreSQL (for persistent memory)

---

## 🤔 Why NeuroVerse?

| Without NeuroVerse | With NeuroVerse |
|---|---|
| Agent only understands English | Agent understands Tamil, Hindi, Telugu, Kannada + English code-switching |
| `"anna file ah csv convert pannu"` → ❌ error | `"anna file ah csv convert pannu"` → ✅ converts file to CSV |
| Every session starts from zero | Agent remembers what it did — across sessions, across agents |
| `DROP DATABASE` → 💀 your data is gone | `DROP DATABASE` → 🛡️ blocked in < 1ms, zero tokens |
| Locked to one LLM provider | Routes to the best model for each task automatically |
| Two agents = chaos | Agent A hands off to Agent B seamlessly |

### Token Efficiency

NeuroVerse's safety layer runs at **zero token cost** — pure regex and rule matching, no LLM calls wasted:

| Safety Approach | Cost per Check | Latency |
|---|---|---|
| LLM-based safety | 500–2,000 tokens | 1–5 seconds |
| Embedding-based | 100–500 tokens | 200–500ms |
| **NeuroVerse Kavach** | **0 tokens** | **< 1ms** |

Over 100 tool calls per session, that's **50,000–200,000 tokens saved** compared to LLM-based safety.

---

## ⚙️ How It Works

```
User Input (any language)
        │
   ┌────┴────┐
   │  Vani   │ ← Language detection + keyword normalisation
   │ (भाषा)  │   Tamil/Hindi/Telugu → normalised internal format
   └────┬────┘
        │
   ┌────┴────┐
   │  Bodhi  │ ← LLM intent extraction + rule-based fallback
   │ (बोधि)  │   Returns structured JSON with confidence
   └────┬────┘
        │
   ┌────┴────┐
   │ Kavach  │ ← 3-layer safety: blocklist → risk → LLM judge
   │ (कवच)   │   Blocks dangerous actions at zero token cost
   └────┬────┘
        │
   ┌────┴────┐
   │  Marga  │ ← Routes to best model (OpenAI/Anthropic/Sarvam/Ollama)
   │ (मार्ग)  │   Based on task type: multilingual/reasoning/local
   └────┬────┘
        │
   ┌────┴────┐
   │ Smriti  │ ← Stores/recalls from tiered memory
   │ (स्मृति) │   Short-term + Episodic + Semantic (PostgreSQL)
   └────┬────┘
        │
   Tool Execution + Response
```

---

## 🌐 Multilingual Intelligence — Vani

**The Problem:** Every MCP server speaks only English. 70% of India code-switches daily.

```
"anna indha file ah csv convert pannu"
         ↓
"anna this file ah csv convert do"     ← keyword normalisation (not full translation)
         ↓
Intent: convert_format { output_format: "csv" }
```

### Hybrid Pipeline (Rule + LLM)

```
Input → Language Detect (langdetect) → Code-Switch Split → Keyword Normalise → Output
```

**Key insight:** Don't fully translate. Only normalise domain-critical keywords. The rest stays untouched — preserving context, tone, and nuance.

### Supported Languages

| Language | Keywords Mapped | Example |
|---|---|---|
| 🇮🇳 Tamil | `pannu` → do, `maathru` → change, `anuppu` → send | `"file ah csv convert pannu"` |
| 🇮🇳 Hindi | `karo` → do, `banao` → create, `bhejo` → send | `"report banao sales ka"` |
| 🇮🇳 Telugu | `cheyyi` → do, `pampu` → send, `chupinchu` → show | `"data chupinchu"` |
| 🇮🇳 Kannada | Support coming in v2 | — |
| 🇬🇧 English | Pass-through | `"convert json to csv"` |

### Code-Switch Detection

```json
{
  "languages": ["ta", "en"],
  "confidence": 0.92,
  "is_code_switched": true,
  "original_text": "anna indha file ah csv convert pannu",
  "normalized_text": "anna this file ah csv convert do"
}
```

---

## 🧠 Intent Extraction — Bodhi

**LLM-first. Rule-based fallback. Never fails.**

```
LLM succeeds (confidence ≥ 0.5)?
   ├─ Yes → use LLM result
   └─ No  → rule-based parser (deterministic)
```

### LLM Strategy

```python
# Prompt to LLM:
"Extract structured intent from the following input.
 Return ONLY valid JSON: {intent, parameters, confidence}"
```

### Rule-Based Fallback (7 patterns)

| Pattern | Intent | Trigger Keywords |
|---|---|---|
| Format conversion | `convert_format` | convert, csv, json, excel, pdf |
| Summarisation | `summarize` | summarise, summary, brief, tldr |
| Report generation | `generate_report` | report, generate report |
| Deletion | `delete_data` | delete, remove, drop, clean |
| Data query | `query_data` | query, search, find, fetch, get |
| Communication | `send_message` | send, share, email, notify |
| Explanation | `explain` | explain, describe, what is, how to |

### Output

```json
{
  "intent": "convert_format",
  "parameters": { "input_format": "json", "output_format": "csv" },
  "confidence": 0.87,
  "source": "rule"
}
```

The key difference: **the code decides** — not the LLM. If the LLM fails, hallucinates, or returns garbage, the rule engine takes over. Deterministic. Reliable.

---

## 💾 Tiered Memory — Smriti

**The Problem:** Raw logs are useless. Storing everything wastes resources. No relevance scoring.

**NeuroVerse's approach:** Score → Filter → Compress → Store.

### Three Tiers

| Tier | Storage | Lifetime | Use |
|---|---|---|---|
| **Short-term** | In-process dict | Current session | Active context, capped at 50 per user |
| **Episodic** | PostgreSQL | Recent actions | What the agent did recently |
| **Semantic** | PostgreSQL | Long-term facts | Persistent knowledge about users, projects, entities |

### Importance Scoring

```python
if importance_score >= 0.4:
    persist_to_database()   # worth remembering
else:
    skip()                  # noise
```

Only important memories survive. No bloat. No irrelevant recall.

### Context Compression

```
❌ Bad:  "The user asked about sales data three times in the last hour and seemed frustrated..."
✅ Good: { "intent": "sales_query", "frequency": 3, "sentiment": "frustrated" }
```

Structured JSON payloads, NOT raw text dumps. Compressed. Indexable. Queryable.

### Memory Schema (PostgreSQL)

```sql
CREATE TABLE memory_records (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    tier        TEXT NOT NULL,          -- short_term | episodic | semantic
    intent      TEXT NOT NULL,
    language    TEXT DEFAULT 'en',
    data        JSONB DEFAULT '{}',     -- compressed structured payload
    importance  REAL DEFAULT 0.5,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
-- Indexed: user_id, intent, tier
```

---

## 🛡️ Safety Layer — Kavach

<p align="center">
  <em>"The shield that never sleeps."</em>
</p>

### Three Layers — Defense in Depth

```
Agent calls tool  →  MCP Server receives request
                            │
                ┌───────────┴───────────┐
                │   Layer 1: Blocklist  │  ← regex + keywords, < 0.1ms
                └───────────┬───────────┘
                            │ pass
                ┌───────────┴───────────┐
                │  Layer 2: Risk Score  │  ← intent → risk classification
                └───────────┬───────────┘
                            │ pass
                ┌───────────┴───────────┐
                │  Layer 3: LLM Judge   │  ← optional model-based check
                └───────────┬───────────┘
                            │ pass
                     Execute handler
```

### Layer 1 — Rule-Based Blocklist (Zero Cost)

Runs inside the MCP server. Pure regex. No network. No tokens.

**Blocked keywords:**
```
delete_all_data, drop_database, drop_table, system_shutdown,
format_disk, rm -rf, truncate, shutdown, reboot, erase_all, destroy
```

**Blocked patterns (regex):**
```
DROP (DATABASE|TABLE|SCHEMA)
DELETE FROM *
TRUNCATE TABLE
FORMAT [drive]:
rm (-rf|--force)
```

### Layer 2 — Intent Risk Classification

| Risk Level | Intents | Action |
|---|---|---|
| 🟢 LOW | `convert_format`, `summarize`, `generate_report`, `query_data`, `explain` | ✅ Allow |
| 🟡 MEDIUM | `send_message`, `unknown` | ⚠️ Block if strict mode |
| 🔴 HIGH | `delete_data` | ❌ Block always |
| ⛔ CRITICAL | `drop_database`, `system_shutdown` | ❌ Block always |

### Layer 3 — LLM Safety Judge (Optional)

If Layers 1–2 pass, optionally ask an LLM: *"Is this safe?"*

```json
// LLM returns:
{ "safe": false, "reason": "This action would delete all user data." }
```

### Safety Verdict

```json
{
  "allowed": false,
  "risk_level": "critical",
  "reason": "Blocked keyword detected: 'drop_database'",
  "blocked_by": "rule"
}
```

### Token Cost: Zero

```
Most AI safety:  Agent → "rm -rf /" → Safety LLM → 2,000 tokens burned
NeuroVerse:      Agent → "rm -rf /" → regex match → BLOCKED (0 tokens, < 1ms)
```

### Strict Mode

```bash
# .env
SAFETY_STRICT_MODE=true    # Also blocks MEDIUM risk (unknown/send)
SAFETY_STRICT_MODE=false   # Only blocks HIGH and CRITICAL
```

---

## 🤖 Multi-Model Router — Marga

**The Problem:** Vendor lock-in. One model for everything. Overpaying.

**NeuroVerse's approach:** Route each task to the best model. Automatically.

### Routing Logic

```python
def route_task(task):
    if task.type == "multilingual":
        return sarvam_model        # Best for Indian languages
    elif task.type == "reasoning":
        return claude_or_openai    # Best for complex analysis
    elif task.type == "local":
        return ollama              # Free, on-device, private
    else:
        return best_available      # Fallback chain
```

### Supported Providers

| Provider | Default Model | Best For | Cost |
|---|---|---|---|
| 🇮🇳 Sarvam AI | `sarvam-2b-v0.5` | Indian languages, multilingual | Low |
| 🧠 Anthropic | `claude-sonnet-4-20250514` | Reasoning, analysis | Medium |
| 🤖 OpenAI | `gpt-4o` | General tasks, code | Medium |
| 🦙 Ollama | `llama3` | Local, private, offline | Free |

### Benefits

| | Without Marga | With Marga |
|---|---|---|
| Cost | Pay GPT-4 for everything | Use Ollama for simple tasks |
| Speed | Same latency for all tasks | Local models for fast tasks |
| Privacy | Everything goes to cloud | Sensitive data stays local |
| Vendor lock-in | Stuck with one provider | Switch anytime |

### Fallback Chain

If your preferred provider is down or unconfigured:
```
Sarvam → OpenAI → Anthropic → Ollama (local, always available)
```

---

## 🔗 Agent-to-Agent — Setu

**Agents calling agents calling agents.**

### Agent Registry

```python
register_agent({
    "agent_name": "report_agent",
    "endpoint": "http://localhost:8001/generate",
    "capabilities": ["generate_report", "sales_analysis"]
})
```

### Routing

```json
{
  "target_agent": "report_agent",
  "task": "generate_sales_report",
  "payload": { "quarter": "Q1", "year": 2026 }
}
```

### Fallback

If the target agent is unreachable:
```json
{
  "success": false,
  "error": "Agent unreachable: ConnectError",
  "fallback": true
}
```

The caller can fall back to local execution. No hard failures.

---

## 🧩 MCP Tools

NeuroVerse exposes **6 tools** via the Model Context Protocol:

| # | Tool (npm) | Tool (Python) | Description |
|---|---|---|---|
| 1 | `neuroverse_process` | `india_mcp_process_multilingual_input` | Full pipeline: detect → normalise → intent → safety → execute |
| 2 | `neuroverse_store` | `india_mcp_store_memory` | Store a memory record in the tiered system |
| 3 | `neuroverse_recall` | `india_mcp_recall_memory` | Retrieve memories by user, intent, or tier |
| 4 | `neuroverse_execute` | `india_mcp_safe_execute` | End-to-end safe execution (convenience) |
| 5 | `neuroverse_route` | `india_mcp_route_agent` | Route a task to a registered downstream agent |
| 6 | `neuroverse_model` | `india_mcp_model_route` | Query the multi-model router (optionally invoke) |
| 7 | `neuroverse_transcribe` | `india_mcp_transcribe_audio` | Transcribe audio to text via Whisper STT |
| 8 | `neuroverse_synthesize` | `india_mcp_synthesize_speech` | Synthesize speech from text via Coqui TTS |

### Real-World Example

```
── Session 1 (Agent Alpha, 2pm) ───────────────────────────
india_mcp_process_multilingual_input({
    text: "anna indha sales data ah csv convert pannu",
    user_id: "alpha",
    execute: true
})
→ Language: Tamil+English (code-switched)
→ Intent: convert_format { output_format: "csv" }
→ Safety: ✅ allowed (LOW risk)
→ Execution: ✅ success

india_mcp_store_memory({
    user_id: "alpha",
    intent: "convert_format",
    tier: "episodic",
    data: { "file": "sales_q1.json", "output": "csv" },
    importance_score: 0.8
})

── Session 2 (Agent Beta, next day) ───────────────────────
india_mcp_recall_memory({
    user_id: "alpha",
    intent: "convert_format",
    limit: 5
})
→ "Agent Alpha converted sales_q1.json to CSV yesterday"
→ Beta picks up exactly where Alpha left off
```

---

## 🌐 REST API

NeuroVerse also ships with a FastAPI REST layer — for non-MCP clients:

```bash
python app/main.py
# → http://localhost:8000/docs (Swagger UI)
```

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/process` | POST | Full multilingual pipeline |
| `/api/memory/store` | POST | Store memory |
| `/api/memory/recall` | POST | Recall memories |

---

## ⚙️ Configuration

All settings via environment variables (`.env`):

```bash
# Database (PostgreSQL required for persistent memory)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/neuroverse

# AI Model API Keys (configure the ones you have)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SARVAM_API_KEY=...

# Ollama (local, free)
OLLAMA_BASE_URL=http://localhost:11434

# Safety
SAFETY_STRICT_MODE=true     # Block MEDIUM risk actions too

# MCP Transport
MCP_TRANSPORT=stdio          # or streamable_http
MCP_PORT=8000
```

---

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

```
tests/test_intent.py     — 10 passed  (rule-based + async + mock LLM + fallback)
tests/test_language.py   — 10 passed  (keyword normalisation + detection + code-switch)
tests/test_pipeline.py   —  8 passed  (full e2e: English, Tamil, Hindi, dangerous, edges)
tests/test_safety.py     — 12 passed  (blocklist, regex, risk classification, pipeline)

============================= 40 passed in 0.87s ==============================
```

### What's Tested

| Category | Tests | Coverage |
|---|---|---|
| Language Detection | 10 | Tamil, Hindi, English, empty input, code-switch flag |
| Intent Extraction | 10 | All 7 rule patterns, LLM mock, LLM failure, empty |
| Safety Engine | 12 | Keywords, regex, risk levels, full pipeline, strict mode |
| Full Pipeline | 8 | E2E English, Tamil, Hindi, dangerous commands, edge cases |

---

## 🏗️ Architecture

### npm Edition (Node.js / TypeScript)
```
npm/
├── src/
│   ├── core/
│   │   ├── language.ts       # Vani  — Language detection (zero deps)
│   │   ├── intent.ts         # Bodhi — Intent extraction (LLM + fallback)
│   │   ├── memory.ts         # Smriti — Tiered memory (JSON files)
│   │   ├── safety.ts         # Kavach — 3-layer safety engine
│   │   └── router.ts         # Marga — Multi-model AI router
│   ├── services/
│   │   ├── executor.ts       # Tool registry + retry engine
│   │   └── agent-router.ts   # Setu — Agent-to-Agent routing
│   ├── types.ts              # TypeScript interfaces & enums
│   ├── constants.ts          # Shared constants
│   └── index.ts              # MCP Server — 6 tools (McpServer + Zod)
├── package.json              # npm publish config
├── tsconfig.json
└── LICENSE                   # Apache-2.0
```

### Python Edition
```
app/
├── core/
│   ├── language.py           # Vani  — Language detection (langdetect)
│   ├── intent.py             # Bodhi — Intent extraction (LLM + fallback)
│   ├── memory.py             # Smriti — Tiered memory (PostgreSQL)
│   ├── safety.py             # Kavach — 3-layer safety engine
│   └── router.py             # Marga — Multi-model AI router
├── models/schemas.py         # 12 Pydantic v2 models
├── services/
│   ├── executor.py           # Tool registry + retry engine
│   └── agent_router.py       # Setu — Agent-to-Agent routing
├── config.py                 # Settings from environment
└── main.py                   # FastAPI REST entry point
mcp/server.py                 # MCP Server (FastMCP) — 6 tools
tests/                        # 40 tests (pytest)
```

### Dependencies — Minimal

**npm (3 packages):**

| Package | Purpose |
|---|---|
| `@modelcontextprotocol/sdk` | MCP protocol |
| `zod` | Schema validation |
| `axios` | HTTP requests |

**Python (7 packages):**

| Package | Purpose |
|---|---|
| `mcp[cli]` | Model Context Protocol SDK |
| `fastapi` + `uvicorn` | REST API layer |
| `pydantic` | Input validation (v2) |
| `langdetect` | Statistical language identification |
| `asyncpg` + `sqlalchemy[asyncio]` | PostgreSQL async driver |
| `httpx` | Async HTTP for model APIs |

---

## 🚀 Roadmap

| Phase | Status | What |
|---|---|---|
| v1.0 | ✅ Done | Multilingual parsing + intent extraction + 5 tools |
| v1.0 | ✅ Done | Tiered memory system (PostgreSQL) |
| v1.0 | ✅ Done | 3-layer safety engine (Kavach) |
| v1.0 | ✅ Done | Multi-model router (Marga) + Agent routing (Setu) |
| v2.0 | ✅ Done | Voice layer (Whisper/Coqui) + Extended Multilingual |
| v3.0 | ✅ Done | Redis caching + Embedding-based semantic retrieval |
| v4.0 | ✅ Done | Reinforcement learning (RLHF) + Arachne contextual indexing |
| v5.0 | 🔮 Future | Agent marketplace & external system plugins |

---

## 🔐 Security

| Measure | Implementation |
|---|---|
| API key management | Environment variables only — never in code |
| Input sanitisation | Pydantic v2 with field constraints on all inputs |
| Rate limiting | Planned for v2.0 |
| Path traversal | N/A — no file system access by tools |
| SQL injection | Parameterised queries via SQLAlchemy |
| Encrypted storage | Delegated to PostgreSQL TLS |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# npm edition
git clone https://github.com/joshua400/neuroverse.git
cd neuroverse/npm
npm install
npm run build

# Python edition
cd neuroverse
python -m pip install -e ".[dev]"
python -m pytest tests/ -v    # All 40 should pass
```

---

## 📜 License

Apache-2.0

---

<p align="center">
  <em>"I built NeuroVerse because it broke my heart watching agents forget everything every session — and not understand a word of Tamil."</em>
</p>

<p align="center">
  <strong>Joshua Ragiland M</strong><br/>
  ✉️ <a href="mailto:joshuaragiland@gmail.com">joshuaragiland@gmail.com</a><br/>
  🌐 <a href="https://portfolio-joshua400s-projects.vercel.app/">Portfolio Website</a>
</p>

<p align="center">
  <sub>Built with 🧠 by Joshua — for the agents of tomorrow.</sub>
</p>
