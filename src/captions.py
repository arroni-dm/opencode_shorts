import os

def make_srt(narration, duration, out_path, words_per_chunk=8):
    words = narration.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i:i+words_per_chunk]))
    # allocate time by word count
    total_words = len(words)
    t = 0.0
    lines = []
    idx = 1
    wi = 0
    for c in chunks:
        cw = len(c.split())
        seg = duration * (cw / total_words) if total_words else duration / len(chunks)
        start = t
        end = min(duration, t + seg)
        lines.append(f"{idx}\n{_ts(start)} --> {_ts(end)}\n{c}\n")
        t = end
        idx += 1
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path

def _ts(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

if __name__ == "__main__":
    make_srt("Hello world this is a test caption.", 5.0, "test.srt")
    print("ok")
