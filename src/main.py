import os, sys, json
from datetime import datetime
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))

load_dotenv(os.path.join(BASE, ".env"))

from scriptgen import pick_topic, generate_script, load_topics
from tts import synthesize
from captions import make_srt
from media import fetch_clips
from render import render
from upload import upload
from history import load_used, is_used, mark_used
from niche import research_references, summarize_patterns

def main():
    openai_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    use_tts = os.getenv("USE_OPENAI_TTS", "false").lower() == "true"
    tts_voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
    width = int(os.getenv("VIDEO_WIDTH", "1080"))
    height = int(os.getenv("VIDEO_HEIGHT", "1920"))
    target = int(os.getenv("TARGET_SECONDS", "55"))
    max_clips = int(os.getenv("MAX_CLIPS", "6"))
    privacy = os.getenv("PRIVACY_STATUS", "private")
    provider = os.getenv("STOCK_PROVIDER", "auto")
    yt_api_key = os.getenv("YOUTUBE_API_KEY")

    work = os.path.join(BASE, "work", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(work, exist_ok=True)

    # duplicate-topic avoidance
    used = [u.get("topic") for u in load_used()]
    topic_obj = pick_topic(used=used)
    if is_used(topic_obj["topic"]):
        # find next unused
        topics = load_topics()
        for t in topics:
            if t["topic"] not in used:
                topic_obj = t
                break
    print("Topic:", topic_obj["topic"])

    # optional niche/reference research
    patterns = {}
    refs = research_references(yt_api_key, max_refs=200, work_dir=work)
    if refs:
        patterns = summarize_patterns(refs)
        print(f"Reference videos shortlisted: {len(refs)}")

    script = generate_script(
        topic_obj, openai_key=openai_key, model=model,
        target_seconds=target, patterns=patterns, used_topics=used,
    )
    print("Title:", script["title"])

    audio_path = os.path.join(work, "voice.mp3")
    audio_path, duration = synthesize(
        script["narration"], audio_path,
        openai_key=openai_key, use_openai=use_tts, voice=tts_voice,
    )
    print(f"Audio: {duration:.2f}s")
    if duration < 48 or duration > 62:
        raise RuntimeError(f"Audio duration {duration:.2f}s outside 50-60s window")

    srt_path = os.path.join(work, "captions.srt")
    make_srt(script["narration"], duration, srt_path)

    clips_dir = os.path.join(work, "clips")
    keys = {
        "pexels": os.getenv("PEXELS_API_KEY"),
        "pixabay": os.getenv("PIXABAY_API_KEY"),
        "coverr": os.getenv("COVERR_API_KEY"),
        "storyblocks_public": os.getenv("STORYBLOCKS_PUBLIC_KEY"),
        "storyblocks_private": os.getenv("STORYBLOCKS_PRIVATE_KEY"),
    }
    clips = fetch_clips(
        script.get("keywords", topic_obj.get("keywords", [])),
        clips_dir, max_clips=max_clips, provider=provider, keys=keys,
    )

    out_path = os.path.join(BASE, "output", f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    render(clips, audio_path, srt_path, out_path, width=width, height=height)
    print("Rendered:", out_path)

    if privacy != "private":
        print("WARNING: privacy_status is not private; forcing private per requirement")
        privacy = "private"
    vid = upload(out_path, script["title"], script["description"],
                 script.get("tags", []), privacy_status=privacy)
    print("YouTube video id:", vid)

    mark_used(topic_obj["topic"], meta={"title": script["title"], "video_id": vid})

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PIPELINE FAILED: {e}")
        raise
