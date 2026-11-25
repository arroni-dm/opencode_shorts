import os, shutil, subprocess, sys, json
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(BASE, "templates", "tall-tale")
FACELESS = os.path.join(BASE, "faceless")

def prepare_project(work_dir):
    dst = os.path.join(work_dir, "project")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(TEMPLATE, dst)
    # remove generated artifacts
    for rel in ["data/narration.wav", "data/mix.wav", "data/lines.json", "data/words.json", "data/cues.json"]:
        p = os.path.join(dst, rel)
        if os.path.exists(p):
            os.remove(p)
    os.makedirs(os.path.join(dst, "renders"), exist_ok=True)
    os.makedirs(os.path.join(dst, "review"), exist_ok=True)
    return dst

def write_script(project_dir, script):
    with open(os.path.join(project_dir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2)

def run(cmd, cwd=None):
    print(">", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)

def render_project(project_dir):
    py = sys.executable
    run([py, os.path.join(FACELESS, "voice.py"), "."], cwd=project_dir)
    run([py, os.path.join(FACELESS, "words.py"), "."], cwd=project_dir)
    run(["node", "tools/capture.mjs", "check"], cwd=project_dir)
    run(["node", "tools/capture.mjs", "cues"], cwd=project_dir)
    run([py, "tools/mix.py", "."], cwd=project_dir)
    out_name = "tall-tale.mp4"
    out_path = os.path.join(project_dir, "renders", out_name)
    run(["node", "tools/capture.mjs", "video", os.path.join("renders", out_name)], cwd=project_dir)
    return out_path

if __name__ == "__main__":
    print("talltale module ok")
