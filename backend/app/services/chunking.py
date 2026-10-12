"""Transkripti zaman damgalı bloklara ayırma.

Şimdilik özet isteminde kullanılıyor; Aşama 4'te (bölümleme) sabit boyutlu
bölütlemenin temeli olarak yeniden kullanılacak.
"""

from dataclasses import dataclass

from app.services.transcript import Segment


@dataclass
class TimeBlock:
    start: float
    end: float
    text: str


def group_into_blocks(segments: list[Segment], block_seconds: float = 30.0) -> list[TimeBlock]:
    """Segmentleri yaklaşık `block_seconds` uzunluğunda bloklara toplar.

    Bir segment, başladığı an bloğun başlangıcından `block_seconds` içindeyse
    o bloğa eklenir; değilse yeni blok açılır. Segmentler bölünmez, bu yüzden
    bloklar tam olarak değil yaklaşık 30 saniyedir.
    """
    if block_seconds <= 0:
        raise ValueError("block_seconds pozitif olmalı.")

    blocks: list[TimeBlock] = []
    current: list[Segment] = []
    for seg in segments:
        if current and seg.start - current[0].start >= block_seconds:
            blocks.append(_make_block(current))
            current = []
        current.append(seg)
    if current:
        blocks.append(_make_block(current))
    return blocks


def _make_block(segments: list[Segment]) -> TimeBlock:
    last = segments[-1]
    return TimeBlock(
        start=segments[0].start,
        end=round(last.start + last.duration, 2),
        text=" ".join(s.text for s in segments),
    )


def format_blocks(blocks: list[TimeBlock]) -> str:
    """Blokları LLM'e verilecek metne çevirir: her satır `[saniye] metin`."""
    return "\n".join(f"[{int(b.start)}] {b.text}" for b in blocks)
