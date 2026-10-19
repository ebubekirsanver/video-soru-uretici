"""Transkriptten LLM ile Türkçe özet ve zaman damgalı konu başlıkları çıkarma."""

from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationError

from app.services.chunking import group_into_blocks
from app.services.llm import LLMClient, LLMError
from app.services.prompts import BLOCK_SECONDS, fill_prompt, load_prompt, transcript_context
from app.services.transcript import Transcript


@dataclass
class Topic:
    title: str
    start_seconds: float
    # True: modelin verdiği değer isteme verilen blok etiketlerinden biri.
    # Konunun videoda gerçekten o anda başladığını göstermez.
    start_verified: bool = False


@dataclass
class Summary:
    summary: str
    topics: list[Topic]


# LLM'in döndürmesi beklenen JSON yapısı
class _TopicModel(BaseModel):
    title: str = Field(min_length=1)
    start_seconds: float


class _SummaryModel(BaseModel):
    summary: str = Field(min_length=1)
    topics: list[_TopicModel]


def build_user_prompt(transcript: Transcript, block_seconds: float = BLOCK_SECONDS) -> str:
    """Transkripti zaman damgalı bloklara ayırıp kullanıcı istemine yerleştirir."""
    return fill_prompt(
        load_prompt("summary_user.txt"),
        transcript_context(transcript, block_seconds),
        duration_seconds=int(transcript.duration_seconds),
    )


def block_labels(transcript: Transcript, block_seconds: float = BLOCK_SECONDS) -> set[int]:
    """İsteme `[saniye]` olarak verilen blok etiketleri (chunking.format_blocks ile aynı: int(b.start))."""
    return {int(b.start) for b in group_into_blocks(transcript.segments, block_seconds)}


def _is_label(value: float, labels: set[int]) -> bool:
    """Değer tam sayıya eşitse (ör. 354.0) ve etiketlerden biriyse True."""
    return float(value).is_integer() and int(value) in labels


def parse_summary(raw: str, duration_seconds: float, labels: set[int] | None = None) -> Summary:
    """LLM yanıtını doğrular; başlık zamanlarını video süresine sınırlar ve sıralar.

    `labels` verilirse her başlık için modelin verdiği özgün değerin bir blok
    etiketi olup olmadığı `start_verified` olarak işaretlenir. Değer
    değiştirilmez (yakın etikete çekilmez). Süre sınırına sıkıştırılan değer
    modelin verdiği değer olmadığı için hiçbir zaman doğrulanmış sayılmaz.
    """
    try:
        data = _SummaryModel.model_validate_json(raw)
    except ValidationError as exc:
        raise LLMError("LLM yanıtı beklenen JSON biçiminde değil.") from exc

    labels = labels or set()
    topics = []
    for t in data.topics:
        clamped = min(max(t.start_seconds, 0.0), duration_seconds)
        verified = clamped == t.start_seconds and _is_label(t.start_seconds, labels)
        topics.append(Topic(title=t.title.strip(), start_seconds=clamped, start_verified=verified))
    topics.sort(key=lambda t: t.start_seconds)
    return Summary(summary=data.summary.strip(), topics=topics)


def summarize(transcript: Transcript, llm: LLMClient, block_seconds: float = BLOCK_SECONDS) -> Summary:
    """Transkriptin Türkçe özetini ve konu başlıklarını üretir."""
    if not transcript.segments:
        raise ValueError("Özetlenecek transkript boş.")
    raw = llm.complete(
        system=load_prompt("summary_system.txt"),
        user=build_user_prompt(transcript, block_seconds),
        json_mode=True,
    )
    return parse_summary(raw, transcript.duration_seconds, block_labels(transcript, block_seconds))
