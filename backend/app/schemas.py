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
