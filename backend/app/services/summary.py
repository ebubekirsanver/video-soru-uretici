"""Transkriptten LLM ile Türkçe özet ve zaman damgalı konu başlıkları çıkarma."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.services.chunking import format_blocks, group_into_blocks
from app.services.llm import LLMClient, LLMError
from app.services.transcript import Transcript

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
BLOCK_SECONDS = 30.0


@dataclass
class Topic:
    title: str
    start_seconds: float


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


@lru_cache
def load_prompt(name: str) -> str:
    """`app/prompts` altındaki istem dosyasını okur."""
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def build_user_prompt(transcript: Transcript, block_seconds: float = BLOCK_SECONDS) -> str:
    """Transkripti zaman damgalı bloklara ayırıp kullanıcı istemine yerleştirir."""
    text = format_blocks(group_into_blocks(transcript.segments, block_seconds))
    # Transkript içinde sınır etiketi geçerse veri bölümünün dışına taşmasın
    text = text.replace("<transkript>", "").replace("</transkript>", "")
    # str.format yerine replace: transkriptteki { } karakterleri sorun çıkarmasın
    return (
        load_prompt("summary_user.txt")
        .replace("{duration_seconds}", str(int(transcript.duration_seconds)))
        .replace("{transcript}", text)
    )


def parse_summary(raw: str, duration_seconds: float) -> Summary:
    """LLM yanıtını doğrular; başlık zamanlarını video süresine sınırlar ve sıralar."""
    try:
        data = _SummaryModel.model_validate_json(raw)
    except ValidationError as exc:
        raise LLMError("LLM yanıtı beklenen JSON biçiminde değil.") from exc

    topics = [
        Topic(title=t.title.strip(), start_seconds=min(max(t.start_seconds, 0.0), duration_seconds))
        for t in data.topics
    ]
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
    return parse_summary(raw, transcript.duration_seconds)
