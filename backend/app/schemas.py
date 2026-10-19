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
    start_seconds: float = Field(description="Konunun yaklaşık başladığı zaman (saniye); modelin verdiği değer")
    start_verified: bool = Field(
        description="true: modelin verdiği değer isteme verilen blok etiketlerinden biri. "
        "Konunun videoda gerçekten o anda başladığını göstermez."
    )


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
    check_support: bool = Field(
        default=False,
        description="true ise alıntısı transkriptte bulunan her soru için ayrı bir model çağrısıyla "
        "alıntının doğru cevabı destekleyip desteklemediği sorulur (soru sayısı kadar ek ücretli çağrı)",
    )


class SupportOut(BaseModel):
    """Alıntı-cevap destek kontrolü. Bir model değerlendirmesidir; kesin doğru kabul edilmemelidir."""

    label: Literal["destekliyor", "kısmen", "desteklemiyor", "kontrol edilmedi", "kontrol edilemedi"] = Field(
        description="destekliyor / kısmen / desteklemiyor: modelin değerlendirmesi; "
        "kontrol edilmedi: alıntı transkriptte bulunamadığı için çağrı yapılmadı; "
        "kontrol edilemedi: çağrı başarısız oldu ya da model geçersiz yanıt verdi"
    )
    reason: str = Field(description="En fazla bir cümlelik gerekçe (model ya da kod tarafından)")


class QuestionOut(BaseModel):
    question: str
    options: list[str] = Field(description="4 seçenek")
    correct_index: int = Field(description="Doğru seçeneğin sırası (0-3)")
    explanation: str
    source_quote: str = Field(
        description="Sorunun dayandığı alıntı. Doğrulandıysa transkriptteki metin; "
        "doğrulanamadıysa modelin yazdığı alıntı (baştaki [saniye] etiketi silinmiş)"
    )
    source_start_seconds: float | None = Field(
        description="Alıntının başladığı transkript segmentinin başlangıcı (saniye); doğrulanamadıysa null"
    )
    verified: bool = Field(description="Alıntı temizlenmiş transkriptte bulundu mu")
    quote_match: Literal["exact", "trimmed"] | None = Field(
        description="exact: alıntı birebir bulundu; trimmed: kenarlarından en fazla 2 kelime "
        "kırpılarak bulundu; null: bulunamadı"
    )
    # Yalnızca check_support=true iken yanıtta yer alır; kapalıyken anahtar hiç görünmez
    support: SupportOut | None = Field(
        default=None, description="Alıntı-cevap destek kontrolü (model değerlendirmesi; yalnızca check_support=true iken)"
    )


class QuestionsResponse(BaseModel):
    video_id: str
    transcript_mode: Literal["clean", "raw"]
    model: str
    prompt_version: str
    requested_count: int
    returned_count: int
    verified_count: int
    questions: list[QuestionOut]
    # Yalnızca check_support=true iken yanıtta yer alır
    support_prompt_version: str | None = Field(
        default=None, description="Destek kontrolünde kullanılan istem sürümü (yalnızca check_support=true iken)"
    )
