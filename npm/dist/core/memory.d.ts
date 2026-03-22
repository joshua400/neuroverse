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
import type { MemoryRecord, MemoryQuery } from "../types.js";
export declare function setDataDir(dir: string): void;
/**
 * Store a memory record in the appropriate tier.
 */
export declare function storeMemory(record: Partial<MemoryRecord> & {
    userId: string;
    intent: string;
}): Promise<MemoryRecord>;
/**
 * Retrieve memory records matching the query.
 */
export declare function recallMemory(query: MemoryQuery): Promise<MemoryRecord[]>;
/**
 * Clear short-term memory for a user.
 */
export declare function clearShortTerm(userId: string): void;
//# sourceMappingURL=memory.d.ts.map