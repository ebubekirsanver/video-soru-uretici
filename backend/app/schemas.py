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


class QuestionsRequest(BaseModel):
    url: str = Field(description="YouTube video bağlantısı")
    count: int = Field(default=5, ge=1, le=20, description="İstenen soru sayısı (1-20)")
    transcript_mode: Literal["clean", "raw"] = Field(
        default="clean", description="LLM'e verilecek transkript: clean (temiz) ya da raw (ham)"
    )


class QuestionOut(BaseModel):
    question: str
    options: list[str] = Field(description="4 seçenek")
    correct_index: int = Field(description="Doğru seçeneğin sırası (0-3)")
    explanation: str
    source_quote: str = Field(description="Sorunun dayandığı transkript alıntısı")
    source_start_seconds: float | None = Field(
        description="Alıntının geçtiği bloğun başlangıcı (saniye); doğrulanamadıysa null"
    )
    verified: bool = Field(description="Alıntı temizlenmiş transkriptte bulundu mu")


class QuestionsResponse(BaseModel):
    video_id: str
    transcript_mode: Literal["clean", "raw"]
    model: str
    prompt_version: str
    requested_count: int
    returned_count: int
    verified_count: int
    questions: list[QuestionOut]
