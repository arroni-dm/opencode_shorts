import os, json
from datetime import datetime

STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")

def _path():
    os.makedirs(STATE_DIR, exist_ok=True)
    return os.path.join(STATE_DIR, "used_topics.json")

def load_used():
    p = _path()
    if not os.path.exists(p):
        return []
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return []

def is_used(topic, days=30):
    used = load_used()
    now = datetime.utcnow().timestamp()
    for u in used:
        if u.get("topic") == topic:
            age = now - u.get("ts", 0)
            if age < days * 86400:
                return True
    return False

def mark_used(topic, meta=None):
    used = load_used()
    used.append({"topic": topic, "ts": datetime.utcnow().timestamp(), "meta": meta or {}})
    # keep last 500
    used = used[-500:]
    with open(_path(), "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2)
