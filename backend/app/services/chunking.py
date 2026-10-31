"""Transkripti zaman damgalı bloklara ve parçalara ayırma.

- `group_into_blocks` / `format_blocks`: ~30 sn'lik bloklar; özet ve soru
  istemlerinde (tam transkript koşulu) kullanılır.
- `fixed_size_chunks`: RAG koşulu için sabit boyutlu, örtüşmeli parçalar
  (Aşama 7a). Bu parçalar gömülüp ChromaDB'de dizinlenir (`retrieval.py`).
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


# --- Sabit boyutlu parçalar (Aşama 7a, RAG koşulu) -----------------------------------
#
# Ana deneyde sabit boyutlu bölütleme kullanılır: gerçek belgelerde anlamsal
# bölütleme sabit boyutlu bölütlemeden genellikle daha iyi sonuç vermiyor
# (Qu vd., 2025). Anlamsal bölütleme ikincil deneydir (CLAUDE.md, kural 6).
# 30 sn'lik bloklar (~70 kelime) tek başına bir soru için az bağlam verdiği için
# parçalar daha büyük tutulur. 150/30 değerleri ölçülerek seçilmedi; değişirse
# sürüm adı da değişir ve dizindeki eski parçalar karışmaz.
CHUNK_WORDS = 150
CHUNK_OVERLAP_WORDS = 30
CHUNKING_VERSION = f"fixed-{CHUNK_WORDS}-{CHUNK_OVERLAP_WORDS}"


@dataclass
class Chunk:
    video_id: str
    chunk_index: int  # 0'dan başlar
    start_seconds: float  # ilk segmentin başı
    end_seconds: float  # son segmentin sonu
    text: str
    chunking: str  # parçalama sürümü, ör. "fixed-150-30"


def _word_count(segment: Segment) -> int:
    return len(segment.text.split())


def _overlap_tail(segments: list[Segment], overlap_words: int) -> list[Segment]:
    """Kapanan parçanın son segmentlerinden toplam en az `overlap_words` kelimelik kısım.

    Parçanın ilk segmenti hiçbir zaman örtüşmeye alınmaz; böylece her yeni
    parça en az bir yeni segment içerir ve döngü ilerler. Tek segmentlik
    parçada örtüşme olmaz.
    """
    tail: list[Segment] = []
    words = 0
    for seg in reversed(segments[1:]):
        tail.insert(0, seg)
        words += _word_count(seg)
        if words >= overlap_words:
            break
    return tail


def _make_chunk(video_id: str, index: int, segments: list[Segment], version: str) -> Chunk:
    last = segments[-1]
    return Chunk(
        video_id=video_id,
        chunk_index=index,
        start_seconds=segments[0].start,
        end_seconds=round(last.start + last.duration, 2),
        text=" ".join(s.text for s in segments),
        chunking=version,
    )


def fixed_size_chunks(
    segments: list[Segment],
    video_id: str,
    chunk_words: int = CHUNK_WORDS,
    overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[Chunk]:
    """Segmentleri bölmeden, örtüşmeli, yaklaşık `chunk_words` kelimelik parçalara toplar.

    Bir parça, kelime sayısı `chunk_words`'e ulaşınca kapanır (son eklenen
    segment kadar aşabilir). Sonraki parça, önceki parçanın son segmentlerinden
    toplam en az `overlap_words` kelimelik kısımla başlar. Girdi temizlenmiş
    transkriptin segmentleridir.

    Uç durumlar: boş girdi boş liste verir; `chunk_words`'ten uzun tek bir
    segment tek başına bir parça olur; son parça kısa kalabilir.
    """
    if chunk_words <= 0:
        raise ValueError("chunk_words pozitif olmalı.")
    if not 0 <= overlap_words < chunk_words:
        raise ValueError("overlap_words 0 ile chunk_words arasında olmalı.")

    version = (
        CHUNKING_VERSION
        if (chunk_words, overlap_words) == (CHUNK_WORDS, CHUNK_OVERLAP_WORDS)
        else f"fixed-{chunk_words}-{overlap_words}"
    )
    chunks: list[Chunk] = []
    current: list[Segment] = []
    words = 0
    has_new = False  # current, örtüşme dışında yeni segment içeriyor mu
    for seg in segments:
        current.append(seg)
        words += _word_count(seg)
        has_new = True
        if words >= chunk_words:
            chunks.append(_make_chunk(video_id, len(chunks), current, version))
            current = _overlap_tail(current, overlap_words)
            words = sum(_word_count(s) for s in current)
            has_new = False
    # Yalnızca örtüşmeden oluşan artık bir parça yeniden yazılmaz
    if current and has_new:
        chunks.append(_make_chunk(video_id, len(chunks), current, version))
    return chunks

