"""Transkript önbelleği.

Başarıyla çekilen transkript yerel bir klasöre JSON olarak yazılır; aynı video
ve aynı dil listesi için sonraki istekler YouTube'a gitmez. İki gerekçe:

- Tekrarlanabilirlik: deneyde iki koşul (full / rag) ve konu çıkarma aynı
  transkripti kullanır; altyazı çalıştırmalar arasında değişse bile koşullar
  aynı metinle karşılaştırılır.
- YouTube istek sınırı: Pilot 1'de her video için transkript defalarca çekildi
  ve YouTube bu bilgisayarın IP'sini engelledi (docs/bulgular/pilot-1/pilot-1.md).

Önbellek ham (temizlenmemiş) transkripti tutar; temizleme her istekte yapılır.
Yalnızca başarılı çekimler yazılır. Bozuk ya da okunamayan dosya isteği bozmaz:
yok sayılır, uyarı günlüğe düşer ve transkript yeniden çekilir. Yazma hatası da
isteği bozmaz. Ayar: TRANSCRIPT_CACHE (varsayılan açık), TRANSCRIPT_CACHE_DIR.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

from app.config import get_settings
from app.services.transcript import Segment, Transcript

logger = logging.getLogger(__name__)

TranscriptSource = Literal["cache", "youtube"]
_UNSAFE = re.compile(r"[^A-Za-z0-9_-]")


def cache_path(video_id: str, languages: list[str]) -> Path:
    """Dosya adı video_id ve dil listesinden (sırası önemli) türer."""
    safe_id = _UNSAFE.sub("_", video_id)
    safe_languages = "-".join(_UNSAFE.sub("_", lang) for lang in languages)
    return Path(get_settings().transcript_cache_dir) / f"{safe_id}__{safe_languages}.json"


def read_cached(video_id: str, languages: list[str]) -> Transcript | None:
    """Önbellekteki transkripti döndürür; yoksa ya da bozuksa None."""
    path = cache_path(video_id, languages)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["video_id"] != video_id:
            raise ValueError("video_id uyuşmuyor")
        segments = [Segment(text=str(s["text"]), start=float(s["start"]), duration=float(s["duration"]))
                    for s in data["segments"]]
        return Transcript(
            video_id=video_id,
            language=str(data["language"]),
            is_generated=bool(data["is_generated"]),
            segments=segments,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logger.warning("Transkript önbelleği okunamadı, yeniden çekilecek (%s): %s", path.name, type(exc).__name__)
        return None


def write_cached(transcript: Transcript, languages: list[str]) -> None:
    """Transkripti önbelleğe yazar; yazma hatası isteği bozmaz."""
    path = cache_path(transcript.video_id, languages)
    data = {
        "video_id": transcript.video_id,
        "languages": languages,
        "language": transcript.language,
        "is_generated": transcript.is_generated,
        "fetched_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "segments": [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript.segments],
    }
    temp = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Önce geçici dosyaya: yarıda kesilen yazma bozuk önbellek bırakmasın
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, path)
    except OSError as exc:
        logger.warning("Transkript önbelleğe yazılamadı (%s): %s", path.name, type(exc).__name__)


def load_transcript(
    video_id: str,
    languages: list[str],
    fetch: Callable[[str, list[str]], Transcript],
) -> tuple[Transcript, TranscriptSource]:
    """Önce önbelleğe bakar, yoksa `fetch` ile çeker ve yazar; transkripti ve kaynağını döndürür.

    `fetch` hata fırlatırsa hata olduğu gibi yükselir ve önbelleğe bir şey yazılmaz.
    """
    if not get_settings().transcript_cache:
        return fetch(video_id, languages), "youtube"
    cached = read_cached(video_id, languages)
    if cached is not None:
        return cached, "cache"
    transcript = fetch(video_id, languages)
    write_cached(transcript, languages)
    return transcript, "youtube"
