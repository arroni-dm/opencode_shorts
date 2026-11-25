import os, subprocess, sys

def _duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        text=True,
    )
    return float(out.strip())

def synthesize(narration, out_path, openai_key=None, use_openai=False, voice="alloy", model="tts-1"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if use_openai and openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            with client.audio.speech.with_streaming_response.create(
                model=model, voice=voice, input=narration
            ) as resp:
                resp.stream_to_file(out_path)
            return out_path, _duration(out_path)
        except Exception as e:
            print(f"[tts] OpenAI TTS failed, falling back to gTTS: {e}")
    # gTTS fallback
    from gtts import gTTS
    tts = gTTS(text=narration, lang="en", slow=False)
    tts.save(out_path)
    return out_path, _duration(out_path)

if __name__ == "__main__":
    d = synthesize("Hello world, this is a test.", "out.mp3")
    print(d)
