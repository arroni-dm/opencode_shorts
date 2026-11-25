import os, json
from datetime import datetime, timedelta, timezone

def research_references(api_key, max_refs=200, work_dir=None):
    if not api_key:
        return None
    try:
        from googleapiclient.discovery import build
    except Exception:
        return None
    yt = build("youtube", "v3", developerKey=api_key)
    queries = ["shorts facts", "true story shorts", "mystery shorts", "science what if shorts"]
    collected = []
    published_after = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    for q in queries:
        try:
            search = yt.search().list(
                q=q, part="snippet", type="video", order="viewCount",
                publishedAfter=published_after, maxResults=50, videoDuration="short"
            ).execute()
        except Exception as e:
            print(f"[niche] search failed for {q}: {e}")
            continue
        ids = [it["id"]["videoId"] for it in search.get("items", []) if "videoId" in it.get("id", {})]
        if not ids:
            continue
        try:
            stats = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute()
        except Exception as e:
            print(f"[niche] stats failed: {e}")
            continue
        for v in stats.get("items", []):
            sn = v.get("snippet", {})
            st = v.get("statistics", {})
            try:
                views = int(st.get("viewCount", 0))
            except Exception:
                views = 0
            pub = sn.get("publishedAt")
            try:
                pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                age_days = max(1, (datetime.now(timezone.utc) - pub_dt).days)
            except Exception:
                age_days = 14
            collected.append({
                "id": v.get("id"),
                "title": sn.get("title"),
                "channel": sn.get("channelTitle"),
                "tags": sn.get("tags", [])[:15],
                "views": views,
                "age_days": age_days,
                "velocity": round(views / age_days, 2),
                "published": pub,
            })
    # dedupe by id
    seen = set()
    uniq = []
    for c in collected:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        uniq.append(c)
    uniq.sort(key=lambda x: x["velocity"], reverse=True)
    refs = uniq[:max_refs]
    if work_dir:
        os.makedirs(work_dir, exist_ok=True)
        with open(os.path.join(work_dir, "references.json"), "w", encoding="utf-8") as f:
            json.dump({"generated_at": datetime.utcnow().isoformat(), "count": len(refs), "refs": refs}, f, indent=2)
    return refs

def summarize_patterns(refs):
    if not refs:
        return {}
    from collections import Counter
    words = Counter()
    tags = Counter()
    for r in refs:
        for t in r.get("tags", []):
            tags[t.lower()] += 1
        for w in (r.get("title") or "").lower().split():
            w = w.strip(".,!?-:;\"'()[]")
            if len(w) > 3:
                words[w] += 1
    return {
        "top_tags": [t for t, _ in tags.most_common(12)],
        "top_words": [w for w, _ in words.most_common(12)],
        "example_titles": [r["title"] for r in refs[:8]],
    }
