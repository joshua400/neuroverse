import os
import json
import uuid
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.getcwd(), "data", "rlhf")

def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def log_feedback(intent: str, model: str, rating: int, feedback_text: str = "") -> dict:
    """"Log user feedback (RLHF) to a persistent store."""
    _ensure_dir()
    path = os.path.join(DATA_DIR, "feedback.json")
    records = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                pass
    record = {
        "id": str(uuid.uuid4()),
        "intent": intent,
        "model": model,
        "rating": rating,
        "feedback_text": feedback_text,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    records.append(record)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    return record
