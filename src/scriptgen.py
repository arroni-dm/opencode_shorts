import json, os
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
    for offset in range(len(topics)):
        cand = topics[(run_index + offset) % len(topics)]
        if cand["topic"] not in used:
            return cand
    return topics[run_index % len(topics)]

FALLBACK_LINES = [
    "In 1925, a charming con man sold the Eiffel Tower to a scrap dealer.",
    "He wore a sharp suit and spoke like a government official.",
    "See, Victor Lustig had a fake title and a fake office.",
    "He invited the dealer to a very secret meeting.",
    "He showed forged papers and a confident smile.",
    "The dealer believed every single word.",
    "Victor asked for a large cash bribe.",
    "The dealer paid without asking any questions.",
    "Then Victor disappeared with all the money.",
    "The dealer was too embarrassed to report it.",
    "A month later, Victor sold the tower again.",
    "He used the exact same trick on another buyer.",
    "This time, the police finally caught him.",
    "He had conned people across two continents.",
    "The judge gave him a long prison sentence.",
    "Victor laughed and called it just business.",
    "The Eiffel Tower never belonged to anyone.",
    "It still stands in Paris today.",
    "The con became a legend.",
    "Some lies are too bold to question.",
]

def generate_script(topic_obj, openai_key=None, model="gpt-4o-mini", target_seconds=55, used_topics=None):
    topic = topic_obj["topic"]
    used_topics = used_topics or []
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            prompt = (
                "Create an original funny true-story YouTube Short in Tall Tale style. "
                "Return JSON with keys: title (<=60 chars), description (<=300 chars), "
                "tags (array of 5-8), sources (array of source strings), "
                "lines (array of exactly 20 objects with key text; each line 3-8 words). "
                "Total narration should be about 95 words and run about 55 seconds. "
                "Do not copy any existing story; make it original. "
                f"Topic: {topic}. Avoid these used topics: {used_topics}. Return only JSON."
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
            )
            text = resp.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            data.setdefault("title", f"Tall tale: {topic}"[:60])
            data.setdefault("description", f"An original tall tale about {topic}. #shorts")
            data.setdefault("tags", ["shorts", "story", "funny", "truestory", "talltale"])
            data.setdefault("sources", [f"Original story inspired by the topic: {topic}"])
            lines = data.get("lines", [])
            # normalize lines to {text}
            norm_lines = []
            for ln in lines:
                if isinstance(ln, str):
                    norm_lines.append({"text": ln})
                elif isinstance(ln, dict) and "text" in ln:
                    norm_lines.append({"text": ln["text"]})
            if len(norm_lines) != 20:
                raise ValueError(f"expected 20 lines, got {len(norm_lines)}")
            data["lines"] = norm_lines
            data.setdefault("voice", "am_michael")
            data.setdefault("speed", 1.05)
            data.setdefault("lead", 0.3)
            data.setdefault("outro", 1.2)
            data.setdefault("gap", 0.18)
            data.setdefault("music", "bounce")
            return data
        except Exception as e:
            print(f"[scriptgen] OpenAI failed, falling back: {e}")
    # Fallback tall-tale script
    return {
        "title": f"Tall tale: {topic}"[:60],
        "description": f"An original tall tale about {topic}. #shorts",
        "tags": ["shorts", "story", "funny", "truestory", "talltale"],
        "sources": [f"Fallback original tall-tale script for topic: {topic}"],
        "voice": "am_michael",
        "speed": 1.05,
        "lead": 0.3,
        "outro": 1.2,
        "gap": 0.18,
        "music": "bounce",
        "lines": [{"text": t} for t in FALLBACK_LINES],
    }

if __name__ == "__main__":
    t = pick_topic()
    print(json.dumps(generate_script(t, os.getenv("OPENAI_API_KEY")), indent=2))
