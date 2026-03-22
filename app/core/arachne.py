import os
import re
from typing import List, Dict

def assemble_context(query: str, directory: str = ".") -> List[Dict]:
    """Assemble code context automatically across the codebase based on BM25-like overlap."""
    query_words = [w for w in re.split(r'\W+', query.lower()) if len(w) > 2]
    scored = []
    
    for root, dirs, files in os.walk(directory):
        if ".git" in root or "node_modules" in root or "__pycache__" in root or "dist" in root or "venv" in root:
            continue
        for file in files:
            if not file.endswith((".py", ".ts", ".js", ".md")):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                lines = content.split("\n")
                for i in range(0, len(lines), 40):
                    chunk_lines = lines[i:i+40]
                    chunk = "\n".join(chunk_lines)
                    chunk_lower = chunk.lower()
                    score = sum(1 for w in query_words if w in chunk_lower)
                    if score > 0:
                        scored.append({
                            "file": f"{path}:{i+1}-{i+len(chunk_lines)}",
                            "score": score,
                            "content": chunk
                        })
            except Exception:
                pass
                
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:3]
