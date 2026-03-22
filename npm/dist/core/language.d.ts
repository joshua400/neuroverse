/**
 * Vani — Multilingual Language Intelligence.
 *
 * Hybrid pipeline:
 *   1. Rule-based keyword normalisation (Tamil, Hindi, Telugu, Kannada)
 *   2. Heuristic language detection (trigram analysis)
 *   3. Code-switch detection
 *
 * No external dependencies — pure TypeScript.
 */
import type { LanguageDetectionResult } from "../types.js";
/**
 * Normalise domain-critical keywords while preserving the rest.
 * NOT full translation — only maps action keywords.
 */
export declare function normaliseKeywords(text: string): string;
/**
 * Detect language(s) from the input text.
 *
 * Uses a simple trigram-hit heuristic — no external dependencies.
 * For production, swap in a proper detector (franc, cld3, etc.).
 */
export declare function detectLanguage(text: string): LanguageDetectionResult;
//# sourceMappingURL=language.d.ts.map