import copy
import json
import os
import random
import uuid
from datetime import datetime

import requests

TOPICS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "topics.json")

REG_LINES = [
    "In 1964, a broke athlete in London mailed himself to Australia.",
    "He squeezed into a wooden crate.",
    "He packed a flashlight and canned food.",
    "See, Reg Spiers had no money for a plane ticket home.",
    "So he built a box five feet long.",
    "His friend nailed the lid shut.",
    "They wrote live cargo on the side.",
    "They shipped it by air freight across the world.",
    "It took sixty-three hours.",
    "No bathroom, no window, no mercy.",
    "When the crate landed in Perth,",
    "Reg popped out",
    "in front of the customs man.",
    "The officer had no form for this.",
    "Reg walked free.",
    "The airline sent him the bill.",
    "He never flew commercial again.",
    "The story got bigger every year.",
    "People still cannot believe it.",
    "Some trips are cheaper the hard way.",
]

EIFFEL_LINES = [
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

MAPLE_LINES = [
    "In 2012, thieves stole six million pounds of maple syrup from a Quebec warehouse.",
    "They did not take gold or cash.",
    "They took breakfast.",
    "The syrup was stored in unmarked barrels in a rural facility.",
    "The gang rented a second warehouse nearby.",
    "They siphoned syrup into their own barrels over several months.",
    "They refilled the original barrels with water.",
    "Nobody checked the weight for a very long time.",
    "The theft was worth about eighteen million dollars.",
    "Police followed sticky clues across multiple provinces.",
    "Some syrup was already sold in New England.",
    "The trail led to New Brunswick and Vermont.",
    "Officers seized trucks, money, and paperwork.",
    "Seventeen people were eventually arrested.",
    "The ringleader got eight years in prison.",
    "The stolen syrup was mostly recovered.",
    "The warehouse added better locks and cameras.",
    "The case became a sweet legend.",
    "It proved breakfast can be a crime scene.",
    "Some heists are stickier than others.",
]

FALLBACKS = [
    ("The Man Who Mailed Himself", REG_LINES),
    ("The Eiffel Tower Con", EIFFEL_LINES),
    ("The Great Maple Syrup Heist", MAPLE_LINES),
]

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

def _normalize_script(data, topic, fallback_title=None):
    data.setdefault("title", (fallback_title or f"Tall tale: {topic}")[:60])
    data.setdefault("description", f"An original tall tale about {topic}. #shorts")
    data.setdefault("tags", ["shorts", "story", "funny", "truestory", "talltale"])
    data.setdefault("sources", [f"Original story inspired by the topic: {topic}"])
    lines = data.get("lines", [])
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

def _call_gemini(api_key, prompt, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.95,
            "responseMimeType": "application/json",
        },
    }
    resp = requests.post(url, params={"key": api_key}, json=payload, timeout=90)
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts or "text" not in parts[0]:
        raise ValueError("Gemini returned no text")
    return parts[0]["text"]

def _call_openai(api_key, prompt, model):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return resp.choices[0].message.content.strip()

def _make_prompt(topic, used_topics, variation_seed):
    return (
        "Create an original funny true-story YouTube Short in Tall Tale style. "
        "Return only JSON with keys: title (<=60 chars), description (<=300 chars), "
        "tags (array of 5-8), sources (array of source strings), "
        "lines (array of exactly 20 objects, each with key text; each line 4-9 words). "
        "Total narration must be about 150 words and run about 55 seconds. "
        "The story must be fresh and distinct from recent runs. "
        "Do not copy any existing story, title, or wording. "
        f"Topic: {topic}. "
        f"Avoid these recently used topics: {used_topics}. "
        f"Variation seed: {variation_seed}."
    )

def _fallback_script(topic, used_topics):
    idx = (len(used_topics) + hash(topic)) % len(FALLBACKS)
    title, lines = FALLBACKS[idx]
    return {
        "title": title[:60],
        "description": f"An original tall tale about {topic}. #shorts",
        "tags": ["shorts", "story", "funny", "truestory", "talltale"],
        "sources": [f"Fallback tall-tale script: {title}"],
        "voice": "am_michael",
        "speed": 1.05,
        "lead": 0.3,
        "outro": 1.2,
        "gap": 0.18,
        "music": "bounce",
        "lines": [{"text": t} for t in lines],
    }

def generate_script(topic_obj, openai_key=None, openai_model="gpt-4o-mini",
                    gemini_key=None, gemini_model="gemini-2.0-flash",
                    target_seconds=55, used_topics=None):
    topic = topic_obj["topic"]
    used_topics = used_topics or []
    variation_seed = uuid.uuid4().hex
    prompt = _make_prompt(topic, used_topics, variation_seed)

    # Gemini first when available, then OpenAI, then varied local fallback.
    if gemini_key:
        try:
            text = _call_gemini(gemini_key, prompt, gemini_model)
            if text.startswith("```"):
                text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            return _normalize_script(data, topic)
        except Exception as e:
            print(f"[scriptgen] Gemini failed, trying next provider: {e}")

    if openai_key:
        try:
            text = _call_openai(openai_key, prompt, openai_model)
            if text.startswith("```"):
                text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            return _normalize_script(data, topic)
        except Exception as e:
            print(f"[scriptgen] OpenAI failed, using local fallback: {e}")

    return _fallback_script(topic, used_topics)

if __name__ == "__main__":
    t = pick_topic()
    print(json.dumps(generate_script(t, openai_key=os.getenv("OPENAI_API_KEY"),
                                    gemini_key=os.getenv("GEMINI_API_KEY")), indent=2))
