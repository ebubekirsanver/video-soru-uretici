import re
from urllib.parse import parse_qs, urlparse

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
_PATH_PREFIXES = ("embed", "shorts", "live", "v")


class InvalidYouTubeUrl(ValueError):
    """Verilen metin geçerli bir YouTube video bağlantısı değil."""


def extract_video_id(url: str) -> str:
    """YouTube bağlantısından 11 karakterlik video kimliğini çıkarır.

    Desteklenen biçimler: watch?v=, youtu.be/, /embed/, /shorts/, /live/
    ve çıplak 11 karakterlik kimlik.
    """
    text = (url or "").strip()
    if not text:
        raise InvalidYouTubeUrl("Bağlantı boş.")

    if _VIDEO_ID_RE.match(text):
        return text

    if "://" not in text:
        text = "https://" + text
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()

    candidate: str | None = None
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif host in _YOUTUBE_HOSTS:
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [None])[0]
        else:
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in _PATH_PREFIXES:
                candidate = parts[1]

    if not candidate or not _VIDEO_ID_RE.match(candidate):
        raise InvalidYouTubeUrl("Geçerli bir YouTube video bağlantısı bulunamadı.")
    return candidate
