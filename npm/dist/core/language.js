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
// ─── Keyword maps (Indian language → English canonical) ─────────────────
const KEYWORD_MAP = {
    // Tamil
    pannu: "do",
    maathru: "change",
    anuppu: "send",
    kaattu: "show",
    padi: "read",
    edhu: "this",
    adhu: "that",
    indha: "this",
    // Hindi
    karo: "do",
    banao: "create",
    bhejo: "send",
    dikhao: "show",
    padho: "read",
    hatao: "remove",
    nikalo: "extract",
    batao: "tell",
    // Telugu
    cheyyi: "do",
    pampu: "send",
    chupinchu: "show",
    chaduvvu: "read",
    teeyandi: "remove",
    // Kannada
    maadu: "do",
    kalisu: "send",
    toorisu: "show",
    odigu: "read",
    // Malayalam
    cheyyu: "do",
    ayakku: "send",
    kaanikku: "show",
    vaayikku: "read",
    maattu: "remove",
    // Bengali (banao shared with Hindi)
    koro: "do",
    pathao: "send",
    dekhao: "show",
    poro: "read",
    shorao: "remove",
};
// ─── Common Indian-language trigrams for detection ──────────────────────
const LANGUAGE_TRIGRAMS = {
    ta: ["anna", "indha", "pannu", "maathru", "anuppu", "kaattu", "romba", "naan"],
    hi: ["karo", "banao", "bhejo", "dikhao", "yaar", "bhai", "mujhe", "kaise", "mein"],
    te: ["cheyyi", "pampu", "chupinchu", "andi", "meeru", "nenu"],
    kn: ["maadu", "kalisu", "toorisu", "guru", "nodu", "hege"],
    ml: ["cheyyu", "ayakku", "kaanikku", "enth", "ethu", "njan"],
    bn: ["koro", "pathao", "dekhao", "poro", "ami", "tumi", "kemon"],
};
// ─── Public API ─────────────────────────────────────────────────────────
/**
 * Normalise domain-critical keywords while preserving the rest.
 * NOT full translation — only maps action keywords.
 */
export function normaliseKeywords(text) {
    if (!text)
        return "";
    const words = text.split(/\s+/);
    return words.map((w) => KEYWORD_MAP[w.toLowerCase()] ?? w).join(" ");
}
/**
 * Detect language(s) from the input text.
 *
 * Uses a simple trigram-hit heuristic — no external dependencies.
 * For production, swap in a proper detector (franc, cld3, etc.).
 */
export function detectLanguage(text) {
    if (!text.trim()) {
        return {
            languages: ["en"],
            confidence: 0,
            isCodeSwitched: false,
            originalText: text,
            normalizedText: "",
        };
    }
    const lower = text.toLowerCase();
    const words = lower.split(/\s+/);
    const detected = new Map();
    // Check each word against trigram lists
    for (const word of words) {
        for (const [lang, trigrams] of Object.entries(LANGUAGE_TRIGRAMS)) {
            if (trigrams.includes(word)) {
                detected.set(lang, (detected.get(lang) ?? 0) + 1);
            }
        }
    }
    const languages = [];
    let confidence = 0.5;
    if (detected.size === 0) {
        // Assume English
        languages.push("en");
        confidence = 0.7;
    }
    else {
        // Sort by hit count descending
        const sorted = [...detected.entries()].sort((a, b) => b[1] - a[1]);
        for (const [lang] of sorted) {
            languages.push(lang);
        }
        // If there are English words too, add English
        const hasEnglish = words.some((w) => !Object.values(LANGUAGE_TRIGRAMS).flat().includes(w) &&
            !Object.keys(KEYWORD_MAP).includes(w) &&
            w.length > 2);
        if (hasEnglish && !languages.includes("en")) {
            languages.push("en");
        }
        confidence = Math.min(0.95, 0.5 + sorted[0][1] * 0.15);
    }
    const isCodeSwitched = languages.length > 1;
    const normalizedText = normaliseKeywords(text);
    return {
        languages,
        confidence,
        isCodeSwitched,
        originalText: text,
        normalizedText,
    };
}
//# sourceMappingURL=language.js.map