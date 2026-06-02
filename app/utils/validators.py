import re
from urllib.parse import parse_qs, urlparse

YOUTUBE_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
        "music.youtube.com",
    }
)

YOUTUBE_VIDEO_PATTERNS = [
    re.compile(r"^https?://(?:www\.)?youtube\.com/watch\?", re.IGNORECASE),
    re.compile(r"^https?://(?:www\.)?youtube\.com/shorts/", re.IGNORECASE),
    re.compile(r"^https?://(?:www\.)?youtube\.com/live/", re.IGNORECASE),
    re.compile(r"^https?://youtu\.be/", re.IGNORECASE),
    re.compile(r"^https?://(?:www\.)?youtube\.com/embed/", re.IGNORECASE),
]


def is_youtube_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not any(p.match(url) for p in YOUTUBE_VIDEO_PATTERNS):
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if host not in {h.removeprefix("www.") for h in YOUTUBE_HOSTS}:
        return False
    if "list=" in url.lower():
        return False
    if "/playlist" in parsed.path.lower():
        return False
    return _has_video_id(url, parsed)


def _has_video_id(url: str, parsed) -> bool:
    if "youtu.be" in (parsed.hostname or "").lower():
        return bool(parsed.path.strip("/"))
    query = parse_qs(parsed.query)
    return bool(query.get("v", [None])[0])


def normalize_youtube_url(url: str) -> str:
    """Return a canonical watch URL for caching and yt-dlp."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if "youtu.be" in host:
        video_id = parsed.path.strip("/").split("/")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    query = parse_qs(parsed.query)
    video_id = query.get("v", [None])[0]
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url.strip()
