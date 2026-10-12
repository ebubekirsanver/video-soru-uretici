from typing import Literal

from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    url: str = Field(description="YouTube video bağlantısı")


class TranscriptSegment(BaseModel):
    text: str
    start: float = Field(description="Başlangıç zamanı (saniye)")
    duration: float = Field(description="Süre (saniye)")


class TranscriptResponse(BaseModel):
    video_id: str
    language: str
    is_generated: bool = Field(description="True ise YouTube otomatik altyazısı")
    segment_count: int
    duration_seconds: float
    segments: list[TranscriptSegment]


class SummaryRequest(BaseModel):
    url: str = Field(description="YouTube video bağlantısı")
    transcript_mode: Literal["clean", "raw"] = Field(
        default="clean", description="clean: etiketler temizlenir, raw: ham transkript"
    )


class SummaryTopic(BaseModel):
    title: str
    start_seconds: float = Field(description="Konunun yaklaşık başladığı zaman (saniye)")


class SummaryResponse(BaseModel):
    video_id: str
    language: str
    transcript_mode: Literal["clean", "raw"]
    model: str = Field(description="Özeti üreten LLM modeli")
    summary: str = Field(description="Türkçe özet")
    topics: list[SummaryTopic]
