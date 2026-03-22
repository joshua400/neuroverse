import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
function walkDir(dir, fileList = []) {
    let files = [];
    try {
        files = readdirSync(dir);
    }
    catch {
        return fileList;
    }
    for (const file of files) {
        if (file === "node_modules" || file === ".git" || file === "dist")
            continue;
        const path = join(dir, file);
        try {
            if (statSync(path).isDirectory()) {
                walkDir(path, fileList);
            }
            else {
                if (path.endsWith(".ts") || path.endsWith(".py") || path.endsWith(".js") || path.endsWith(".md")) {
                    fileList.push(path);
                }
            }
        }
        catch { }
    }
    return fileList;
}
export function assembleContext(query, dir = process.cwd()) {
    const queryWords = query.toLowerCase().split(/\W+/).filter(w => w.length > 2);
    const allFiles = walkDir(dir);
    const scored = [];
    for (const f of allFiles) {
        try {
            const content = readFileSync(f, "utf-8");
            const lines = content.split("\n");
            for (let i = 0; i < lines.length; i += 40) {
                const chunkLines = lines.slice(i, i + 40);
                const chunk = chunkLines.join("\n");
                const chunkLower = chunk.toLowerCase();
                let score = 0;
                for (const w of queryWords) {
                    if (chunkLower.includes(w))
                        score++;
                }
                if (score > 0) {
                    scored.push({ file: `${f}:${i + 1}-${i + chunkLines.length}`, score, content: chunk });
                }
            }
        }
        catch { }
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 3);
}
//# sourceMappingURL=arachne.js.map