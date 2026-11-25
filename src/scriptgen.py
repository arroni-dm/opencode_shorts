import json, os, random
from datetime import datetime

TOPICS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "topics.json")

def load_topics():
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_topic(run_index=None, used=None):
    topics = load_topics()
    used = used or []
    if run_index is None:
        run_index = int(datetime.utcnow().timestamp()) // 3600
    # try to find a topic not used recently
    for offset in range(len(topics)):
        cand = topics[(run_index + offset) % len(topics)]
        if cand["topic"] not in used:
            return cand
    return topics[run_index % len(topics)]

def generate_script(topic_obj, openai_key=None, model="gpt-4o-mini", target_seconds=55, patterns=None, used_topics=None):
    topic = topic_obj["topic"]
    keywords = topic_obj.get("keywords", [])
    used_topics = used_topics or []
    patterns = patterns or {}
    words_target = int(target_seconds * 2.1)  # ~2.1 words/sec
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            prompt = (
                f"Create a {target_seconds}-second YouTube Shorts script as JSON with keys: "
                "title (<=60 chars), description (<=300 chars), tags (array of 5-8), "
                "keywords (array of 3 search terms for stock video), "
                f"narration (a single paragraph, about {words_target} words, spoken naturally). "
                "Make it 100% original; do not copy titles, scripts, or shots from reference videos. "
                "Use only the patterns/keywords as inspiration. "
                f"Topic: {topic}. Patterns: {json.dumps(patterns)}. "
                f"Avoid these already-used topics: {used_topics}. Return only JSON."
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            text = resp.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            data.setdefault("keywords", keywords)
            return data
        except Exception as e:
            print(f"[scriptgen] OpenAI failed, falling back: {e}")
    narration = (
        f"Here is a quick story about {topic}. "
        "It starts small, then gets strange, then flips at the end. "
        "Pay attention to the one detail everyone misses. "
        "By the time you notice it, the story is already over. "
        "And that is why people still talk about it today."
    )
    return {
        "title": f"Quick story: {topic}"[:60],
        "description": f"A short true-style story about {topic}. #shorts",
        "tags": ["shorts", "story", "facts", "history", "viral"],
        "keywords": keywords or ["city", "people", "dramatic"],
        "narration": narration,
    }

if __name__ == "__main__":
    t = pick_topic()
    print(json.dumps(generate_script(t, os.getenv("OPENAI_API_KEY")), indent=2))
