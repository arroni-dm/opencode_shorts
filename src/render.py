import os, subprocess

def render(clips, audio_path, srt_path, out_path, width=1080, height=1920):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Build concat list, repeating clips until enough
    dur = float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", audio_path],
        text=True).strip())
    # estimate clip durations
    clip_durs = []
    for c in clips:
        clip_durs.append(float(subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", c],
            text=True).strip()))
    # repeat
    concat_paths = []
    total = 0.0
    i = 0
    while total < dur + 2:
        c = clips[i % len(clips)]
        concat_paths.append(c)
        total += clip_durs[i % len(clips)]
        i += 1
    list_file = os.path.join(os.path.dirname(out_path), "concat.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for c in concat_paths:
            f.write(f"file '{os.path.abspath(c)}'\n")
    # burn subtitles
    srt_abs = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"subtitles='{srt_abs}':force_style='FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV=260'"
    )
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-i", audio_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(dur),
        "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path

if __name__ == "__main__":
    print("render module ok")
