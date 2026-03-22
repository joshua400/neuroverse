import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
let dataDir = join(process.cwd(), "data", "rlhf");
function ensureDir() {
    if (!existsSync(dataDir)) {
        mkdirSync(dataDir, { recursive: true });
    }
}
function persistPath() {
    ensureDir();
    return join(dataDir, "feedback.json");
}
export function logFeedback(intent, model, rating, feedbackText = "") {
    const p = persistPath();
    let records = [];
    if (existsSync(p)) {
        try {
            records = JSON.parse(readFileSync(p, "utf-8"));
        }
        catch { }
    }
    const full = {
        id: randomUUID(), intent, model, rating, feedbackText, createdAt: new Date().toISOString()
    };
    records.push(full);
    writeFileSync(p, JSON.stringify(records, null, 2), "utf-8");
    return full;
}
//# sourceMappingURL=rlhf.js.map