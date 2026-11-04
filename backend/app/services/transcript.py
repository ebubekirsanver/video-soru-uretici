from dataclasses import dataclass

from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)


class TranscriptUnavailable(Exception):
    """Videonun transkripti alınamadı (altyazı yok, kapalı, video erişilemez)."""


class TranscriptBlocked(Exception):
    """YouTube bu ağdan gelen istekleri engelledi (IP engeli ya da istek sınırı).

    Video ya da altyazı sorunu değil, erişim sorunudur; bu yüzden
    `TranscriptUnavailable` değildir ve HTTP 503'e çevrilir.
    """


@dataclass
class Segment:
    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    video_id: str
    language: str
    is_generated: bool
    segments: list[Segment]

    @property
    def duration_seconds(self) -> float:
        if not self.segments:
            return 0.0
        last = self.segments[-1]
        return round(last.start + last.duration, 2)


def fetch_transcript(video_id: str, languages: list[str], api: YouTubeTranscriptApi | None = None) -> Transcript:
    """Videonun zaman damgalı altyazısını çeker; `languages` sırayla denenir.

    Altyazı bulunamazsa ileride Whisper yedeği devreye girecek (Aşama 3).
    """
    api = api or YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=languages)
    except RequestBlocked as exc:
        # IpBlocked da RequestBlocked'tır; kütüphane HTTP 429'u da IpBlocked olarak fırlatır
        raise TranscriptBlocked(
            "YouTube bu ağdan gelen istekleri geçici olarak engelledi; bir süre sonra ya da başka bir ağdan deneyin."
        ) from exc
    except NoTranscriptFound as exc:
        raise TranscriptUnavailable(
            f"İstenen dillerde ({', '.join(languages)}) altyazı bulunamadı."
        ) from exc
    except TranscriptsDisabled as exc:
        raise TranscriptUnavailable("Bu videoda altyazılar kapalı.") from exc
    except VideoUnavailable as exc:
        raise TranscriptUnavailable("Video bulunamadı ya da erişilemiyor.") from exc
    except CouldNotRetrieveTranscript as exc:
        raise TranscriptUnavailable("Transkript YouTube'dan alınamadı.") from exc

    segments = [
        Segment(text=s.text.strip(), start=s.start, duration=s.duration)
        for s in fetched
        if s.text.strip()
    ]
    return Transcript(
        video_id=video_id,
        language=fetched.language_code,
        is_generated=fetched.is_generated,
        segments=segments,
    )
