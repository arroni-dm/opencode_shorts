import os, requests

def _download(url, out):
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(out, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

def _pexels(keywords, out_dir, max_clips, api_key):
    query = " ".join(keywords[:3])
    headers = {"Authorization": api_key}
    params = {"query": query, "orientation": "portrait", "per_page": max_clips, "size": "medium"}
    r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=60)
    r.raise_for_status()
    videos = r.json().get("videos", [])
    paths = []
    for i, v in enumerate(videos[:max_clips]):
        files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"]
        if not files:
            continue
        files.sort(key=lambda f: f.get("width", 0))
        url = files[len(files)//2]["link"] if len(files) > 1 else files[0]["link"]
        out = os.path.join(out_dir, f"clip_{i:02d}.mp4")
        _download(url, out)
        paths.append(out)
    if not paths:
        raise RuntimeError("Pexels returned no clips")
    return paths

def _pixabay(keywords, out_dir, max_clips, api_key):
    query = " ".join(keywords[:3])
    params = {"key": api_key, "q": query, "video_type": "all", "orientation": "vertical", "per_page": max_clips}
    r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=60)
    r.raise_for_status()
    hits = r.json().get("hits", [])
    paths = []
    for i, h in enumerate(hits[:max_clips]):
        vids = h.get("videos", {})
        # prefer medium/large
        cand = vids.get("medium") or vids.get("large") or vids.get("small") or vids.get("tiny")
        if not cand or "url" not in cand:
            continue
        out = os.path.join(out_dir, f"clip_{i:02d}.mp4")
        _download(cand["url"], out)
        paths.append(out)
    if not paths:
        raise RuntimeError("Pixabay returned no clips")
    return paths

def _coverr(keywords, out_dir, max_clips, api_key):
    query = " ".join(keywords[:3])
    params = {"api_key": api_key, "query": query, "page_size": max_clips}
    r = requests.get("https://api.coverr.co/videos", params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    hits = data.get("hits") or data.get("videos") or []
    paths = []
    for i, h in enumerate(hits[:max_clips]):
        url = None
        if isinstance(h, dict):
            if "urls" in h and isinstance(h["urls"], dict):
                url = h["urls"].get("mp4") or h["urls"].get("hd") or h["urls"].get("sd")
            elif "url" in h:
                url = h["url"]
            elif "video_files" in h:
                url = h["video_files"][0].get("link")
        if not url:
            continue
        out = os.path.join(out_dir, f"clip_{i:02d}.mp4")
        _download(url, out)
        paths.append(out)
    if not paths:
        raise RuntimeError("Coverr returned no clips")
    return paths

def _storyblocks(keywords, out_dir, max_clips, public_key, private_key):
    raise RuntimeError("Storyblocks requires signed requests; use Pexels/Pixabay/Coverr or implement Storyblocks signing")

def fetch_clips(keywords, out_dir, max_clips=6, api_key=None, provider="auto", keys=None):
    os.makedirs(out_dir, exist_ok=True)
    keys = keys or {}
    pex = keys.get("pexels") or os.getenv("PEXELS_API_KEY")
    pix = keys.get("pixabay") or os.getenv("PIXABAY_API_KEY")
    cov = keys.get("coverr") or os.getenv("COVERR_API_KEY")
    sb_pub = keys.get("storyblocks_public") or os.getenv("STORYBLOCKS_PUBLIC_KEY")
    sb_priv = keys.get("storyblocks_private") or os.getenv("STORYBLOCKS_PRIVATE_KEY")

    if provider == "auto":
        if pex: provider = "pexels"
        elif pix: provider = "pixabay"
        elif cov: provider = "coverr"
        elif sb_pub and sb_priv: provider = "storyblocks"
        else: raise RuntimeError("No stock media API key found (PEXELS/PIXABAY/COVERR/STORYBLOCKS)")

    if provider == "pexels":
        if not pex: raise RuntimeError("PEXELS_API_KEY missing")
        return _pexels(keywords, out_dir, max_clips, pex)
    if provider == "pixabay":
        if not pix: raise RuntimeError("PIXABAY_API_KEY missing")
        return _pixabay(keywords, out_dir, max_clips, pix)
    if provider == "coverr":
        if not cov: raise RuntimeError("COVERR_API_KEY missing")
        return _coverr(keywords, out_dir, max_clips, cov)
    if provider == "storyblocks":
        if not (sb_pub and sb_priv): raise RuntimeError("STORYBLOCKS keys missing")
        return _storyblocks(keywords, out_dir, max_clips, sb_pub, sb_priv)
    raise RuntimeError(f"Unknown stock provider: {provider}")
