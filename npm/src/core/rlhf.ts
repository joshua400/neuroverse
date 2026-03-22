import { randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export interface FeedbackRecord {
  id: string;
  intent: string;
  model: string;
  rating: number; // 1 to 5
  feedbackText: string;
  createdAt: string;
}

let dataDir = join(process.cwd(), "data", "rlhf");

function ensureDir(): void {
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
  }
}

function persistPath(): string {
  ensureDir();
  return join(dataDir, "feedback.json");
}

export function logFeedback(intent: string, model: string, rating: number, feedbackText: string = ""): FeedbackRecord {
  const p = persistPath();
  let records: FeedbackRecord[] = [];
  if (existsSync(p)) {
    try {
      records = JSON.parse(readFileSync(p, "utf-8"));
    } catch {}
  }
  const full: FeedbackRecord = {
    id: randomUUID(), intent, model, rating, feedbackText, createdAt: new Date().toISOString()
  };
  records.push(full);
  writeFileSync(p, JSON.stringify(records, null, 2), "utf-8");
  return full;
}
