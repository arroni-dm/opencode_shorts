# Automated YouTube Shorts/Video Pipeline

Fully programmatic, cloud-friendly pipeline that produces and uploads a YouTube video on a 5-slot daily schedule (every ~4.8 h). No local faceless engine required.

## What it does
1. Picks/rotates a topic.
2. Generates a script + title/description/tags (OpenAI, or template fallback).
3. Synthesizes voiceover (OpenAI TTS or gTTS).
4. Builds word-timed captions (SRT).
5. Fetches portrait stock clips (Pexels).
6. Renders a 1080×1920 MP4 with FFmpeg (concat + crop/scale + burned-in captions + audio).
7. Uploads to YouTube via Data API v3.

## Schedule
GitHub Actions cron (UTC): 00:00, 04:48, 09:36, 14:24, 19:12.

## Setup
See `docs/SETUP.md` (create after). Quick:
- Copy `.env.example` to `.env` and fill keys.
- `pip install -r requirements.txt`
- `python scripts/oauth_setup.py` once to create `token.json` (store as GitHub secret).
- Add secrets to GitHub: OPENAI_API_KEY, PEXELS_API_KEY, YOUTUBE_CLIENT_SECRETS, YOUTUBE_TOKEN_JSON.
- Enable workflow.

## Run locally
`python src/main.py`

## Cost notes
- gTTS + Pexels are free. OpenAI TTS/LLM are optional and billed.
- YouTube upload is free within quota.
