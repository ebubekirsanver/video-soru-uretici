"""Transkript metin temizleme.

Ham transkript değiştirilmez; temizlenmiş kopya ayrı döndürülür. Böylece
ham ve temiz transkriptle üretilen çıktılar karşılaştırılabilir.
"""

import re
from typing import Literal

from app.services.transcript import Segment, Transcript

TranscriptMode = Literal["clean", "raw"]

# [Müzik], [Alkış], [ __ ] gibi köşeli parantez etiketleri.
# Normal parantezler (...) bilerek silinmez: konuşmanın parçası olabilirler.
_BRACKET_TAG = re.compile(r"\[[^\[\]]*\]")
_MUSIC_NOTE = re.compile(r"♪")
_WHITESPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Köşeli parantez etiketlerini ve ♪ işaretini siler, boşlukları toparlar."""
    text = _BRACKET_TAG.sub(" ", text)
    text = _MUSIC_NOTE.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()


def clean_transcript(transcript: Transcript) -> Transcript:
    """Temizlenmiş yeni bir transkript döndürür; boş kalan segmentler atılır."""
    segments = []
    for s in transcript.segments:
        text = clean_text(s.text)
        if text:
            segments.append(Segment(text=text, start=s.start, duration=s.duration))
    return Transcript(
        video_id=transcript.video_id,
        language=transcript.language,
        is_generated=transcript.is_generated,
        segments=segments,
    )


def prepare_transcript(transcript: Transcript, mode: TranscriptMode) -> Transcript:
    """Seçilen moda göre ham ya da temiz transkripti döndürür."""
    return clean_transcript(transcript) if mode == "clean" else transcript
