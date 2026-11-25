import os, sys, json, shutil
from datetime import datetime
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))

load_dotenv(os.path.join(BASE, ".env"))

from scriptgen import pick_topic, generate_script, load_topics
from talltale import prepare_project, write_script, render_project
from history import load_used, mark_used
from niche import research_references, summarize_patterns
from upload import upload

def main():
    openai_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    yt_api_key = os.getenv("YOUTUBE_API_KEY")
    privacy = os.getenv("PRIVACY_STATUS") or "private"

    work = os.path.join(BASE, "work", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(work, exist_ok=True)

    used = [u.get("topic") for u in load_used()]
    topic_obj = pick_topic(used=used)
    print("Topic:", topic_obj["topic"])

    patterns = {}
    refs = research_references(yt_api_key, max_refs=200, work_dir=work)
    if refs:
        patterns = summarize_patterns(refs)
        print(f"Reference videos shortlisted: {len(refs)}")

    script = generate_script(topic_obj, openai_key=openai_key, model=model, used_topics=used)
    # attach niche patterns into description? keep title
    print("Title:", script["title"])

    project_dir = prepare_project(work)
    write_script(project_dir, script)

    out_path = render_project(project_dir)
    print("Rendered:", out_path)

    # copy final to output/
    final_dir = os.path.join(BASE, "output")
    os.makedirs(final_dir, exist_ok=True)
    final_path = os.path.join(final_dir, os.path.basename(out_path))
    shutil.copy2(out_path, final_path)

    vid = upload(final_path, script["title"], script["description"],
                 script.get("tags", []), privacy_status="private")
    print("YouTube video id:", vid)

    mark_used(topic_obj["topic"], meta={"title": script["title"], "video_id": vid})

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PIPELINE FAILED: {e}")
        raise
