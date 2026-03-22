/**
 * Smriti — Tiered Memory System.
 *
 * Tiers:
 *   short_term — in-process Map, capped at MAX_SHORT_TERM per user
 *   episodic   — persistent (JSON file on disk)
 *   semantic   — persistent (JSON file on disk)
 *
 * Node.js version uses JSON files instead of PostgreSQL for zero-dep operation.
 * For production, swap in a real database adapter.
 */
import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import axios from "axios";
import { MAX_SHORT_TERM, IMPORTANCE_THRESHOLD } from "../constants.js";
// ─── Embeddings & Math ──────────────────────────────────────────────────
function cosineSimilarity(v1, v2) {
    let dot = 0, mag1 = 0, mag2 = 0;
    for (let i = 0; i < v1.length; i++) {
        dot += v1[i] * v2[i];
        mag1 += v1[i] * v1[i];
        mag2 += v2[i] * v2[i];
    }
    if (!mag1 || !mag2)
        return 0;
    return dot / (Math.sqrt(mag1) * Math.sqrt(mag2));
}
async function generateEmbedding(text) {
    const apiKey = process.env["OPENAI_API_KEY"];
    if (!apiKey || !text)
        return undefined;
    try {
        const res = await axios.post("https://api.openai.com/v1/embeddings", {
            model: "text-embedding-3-small",
            input: text
        }, {
            headers: { Authorization: `Bearer ${apiKey}` }
        });
        return res.data.data[0].embedding;
    }
    catch (e) {
        console.warn("Embedding generation failed, skipping semantic search");
        return undefined;
    }
}
// ─── In-process short-term store ────────────────────────────────────────
const shortTerm = new Map();
// ─── Data directory ─────────────────────────────────────────────────────
let dataDir = join(process.cwd(), "data", "memory");
export function setDataDir(dir) {
    dataDir = dir;
}
function ensureDir() {
    if (!existsSync(dataDir)) {
        mkdirSync(dataDir, { recursive: true });
    }
}
function persistPath() {
    ensureDir();
    return join(dataDir, "persistent.json");
}
function loadPersistent() {
    const p = persistPath();
    if (!existsSync(p))
        return [];
    try {
        return JSON.parse(readFileSync(p, "utf-8"));
    }
    catch {
        return [];
    }
}
function savePersistent(records) {
    writeFileSync(persistPath(), JSON.stringify(records, null, 2), "utf-8");
}
// ─── Public API ─────────────────────────────────────────────────────────
/**
 * Store a memory record in the appropriate tier.
 */
export async function storeMemory(record) {
    const now = new Date().toISOString();
    let vector;
    if (record.tier && record.tier !== "short_term" && record.importanceScore !== undefined && record.importanceScore >= IMPORTANCE_THRESHOLD) {
        const textToEmbed = JSON.stringify(record.data);
        if (textToEmbed && textToEmbed !== "{}") {
            vector = await generateEmbedding(textToEmbed);
        }
    }
    const full = {
        id: record.id ?? randomUUID(),
        userId: record.userId,
        tier: (record.tier ?? "short_term"),
        intent: record.intent,
        language: record.language ?? "en",
        data: record.data ?? {},
        importanceScore: record.importanceScore ?? 0.5,
        vector,
        createdAt: record.createdAt ?? now,
        updatedAt: now,
    };
    if (full.tier === "short_term") {
        const existing = shortTerm.get(full.userId) ?? [];
        existing.push(full);
        // Cap
        if (existing.length > MAX_SHORT_TERM) {
            existing.shift();
        }
        shortTerm.set(full.userId, existing);
    }
    else {
        // Episodic / Semantic — persist only above threshold
        if (full.importanceScore >= IMPORTANCE_THRESHOLD) {
            const records = loadPersistent();
            records.push(full);
            savePersistent(records);
        }
    }
    return full;
}
/**
 * Retrieve memory records matching the query.
 */
export async function recallMemory(query) {
    const results = [];
    // Check short-term
    const stRecords = shortTerm.get(query.userId) ?? [];
    for (const r of stRecords) {
        if (query.tier && r.tier !== query.tier)
            continue;
        if (query.intent && r.intent !== query.intent)
            continue;
        results.push(r);
    }
    // Check persistent
    if (!query.tier || query.tier !== "short_term") {
        const persistent = loadPersistent();
        for (const r of persistent) {
            if (r.userId !== query.userId)
                continue;
            if (query.tier && r.tier !== query.tier)
                continue;
            if (query.intent && r.intent !== query.intent)
                continue;
            results.push(r);
        }
    }
    // Apply Semantic Search if requested
    if (query.semanticQuery && results.length > 0) {
        const qVector = await generateEmbedding(query.semanticQuery);
        if (qVector) {
            results.sort((a, b) => {
                const simA = a.vector ? cosineSimilarity(qVector, a.vector) : -1;
                const simB = b.vector ? cosineSimilarity(qVector, b.vector) : -1;
                return simB - simA; // DESC
            });
            return results.slice(0, query.limit);
        }
    }
    // Sort by createdAt descending, apply limit
    results.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
    return results.slice(0, query.limit);
}
/**
 * Clear short-term memory for a user.
 */
export function clearShortTerm(userId) {
    shortTerm.delete(userId);
}
//# sourceMappingURL=memory.js.map