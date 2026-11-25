# Setup Guide

## 1. Local prerequisites
- Python 3.10+, ffmpeg, fonts (DejaVu). On Windows use Git Bash or WSL.

## 2. Python env
```bash
cd yt-auto-pipeline
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 3. Environment
Copy `.env.example` to `.env` and fill:
- At least one stock media key: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `COVERR_API_KEY`, or Storyblocks keys.
- `STOCK_PROVIDER=auto` (or pexels/pixabay/coverr/storyblocks)
- Optional: `OPENAI_API_KEY` + `USE_OPENAI_TTS=true`
- Optional: `YOUTUBE_API_KEY` for niche/reference research (150-200 shortlisted videos)
- YouTube upload credentials (step 4)
- `TARGET_SECONDS=55` (50-60s window)
- `PRIVACY_STATUS=private`

## 4. YouTube OAuth (one-time, upload scope)
1. Create a Google Cloud project, enable YouTube Data API v3.
2. Create OAuth 2.0 Desktop client credentials, download JSON.
3. Save as `client_secrets.json` in project root (or set `YOUTUBE_CLIENT_SECRETS_JSON`).
4. Run `python scripts/oauth_setup.py` and complete browser consent.
5. This creates `token.json`. Store both JSONs as GitHub secrets:
   - `YOUTUBE_CLIENT_SECRETS_JSON`
   - `YOUTUBE_TOKEN_JSON`

## 5. GitHub
- Push repo to GitHub.
- Add secrets/vars as listed below.
- The workflow runs 5 times/day per `config/schedule.json`.

## 6. Local test
```bash
python src/main.py
```
Output lands in `output/`.

## Notes
- Videos are forced to `private` mode in code.
- Target duration window is 50-60s; pipeline fails if outside 48-62s.
- Captions are estimated timings (word-count based). For precise captions, add Whisper API call in `captions.py`.
- Niche research is optional and only runs if `YOUTUBE_API_KEY` is set.
- Respect stock media licenses and YouTube ToS.
