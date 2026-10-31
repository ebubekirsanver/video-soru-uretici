from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_serializer, model_validator


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


class TopicsRequest(BaseModel):
    url: str = Field(description="YouTube video bağlantısı")
    count: int = Field(default=6, ge=1, le=10, description="İstenen konu sayısı (1-10)")


class TopicOut(BaseModel):
    title: str = Field(description="Kısa başlık")
    description: str = Field(description="Bu konuda videoda anlatılanı söyleyen tek cümle")
    text: str = Field(description='Soru üretimine ve erişime verilecek metin: "Başlık: açıklama"')


class TopicsResponse(BaseModel):
    video_id: str
    prompt_version: str = Field(description="Konu çıkarma istemi sürümü (topics-v1)")
    model: str
    topics: list[TopicOut]


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
    # --- Aşama 7b: AS1 koşulları (konu tabanlı, istem questions-v2) ---
    # context_mode verilmezse eski davranış (questions-v1, tam transkript) aynen sürer.
    context_mode: Literal["full", "rag"] | None = Field(
        default=None,
        description="Verilirse konu başına bir soru questions-v2 ile üretilir. full: transkriptin tamamı, "
        "rag: konu için erişilen parçalar. Verilmezse eski davranış (questions-v1).",
    )
    topics: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=10,
        description="Konular (1-10). Verilirse hepsi kullanılır ve count yok sayılır; verilmezse konular özet "
        "servisinden alınır (ilk count konu). Yalnızca context_mode ile.",
    )
    k: int = Field(
        default=5, ge=1, le=10, description="RAG'de konu başına erişilen parça sayısı (1-10). Yalnızca context_mode ile."
    )
    # --- Aşama 8: hedef Bloom düzeyleri (istem questions-v3) ---
    bloom_levels: list[Literal["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]] | None = Field(
        default=None,
        description="topics ile aynı sırada ve uzunlukta hedef Bloom düzeyleri. Yalnızca topics ile verilebilir. "
        "Verilmezse 6 konuya 6 düzey, video_id'den türetilen sabit tohumla eşlenir; konu sayısı 6 değilse verilmesi gerekir.",
    )

    @field_validator("topics")
    @classmethod
    def _topics_not_empty(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        value = [t.strip() for t in value]
        if any(not t for t in value):
            raise ValueError("konu boş olamaz")
        return value

    @model_validator(mode="after")
    def _check_condition_fields(self) -> "QuestionsRequest":
        if self.context_mode is None and {"topics", "k", "bloom_levels"} & self.model_fields_set:
            raise ValueError("topics, k ve bloom_levels yalnızca context_mode ile kullanılabilir")
        if self.bloom_levels is not None:
            if self.topics is None:
                raise ValueError("bloom_levels yalnızca topics ile birlikte verilebilir")
            if len(self.bloom_levels) != len(self.topics):
                raise ValueError("bloom_levels, topics ile aynı uzunlukta olmalı")
        elif self.context_mode is not None:
            # Tohumlu Bloom eşlemesi yalnızca 6 konu için yapılır (protokol; kullanıcı kararı)
            topic_count = len(self.topics) if self.topics is not None else self.count
            if topic_count != 6:
                raise ValueError(
                    "bloom_levels verilmediğinde konu sayısı 6 olmalı (topics ya da count); "
                    "başka sayıda konu için bloom_levels verilmeli"
                )
        if self.context_mode == "rag" and self.transcript_mode == "raw":
            # RAG dizini temiz transkriptten kurulur; ham/temiz karşılaştırması ikincil deneydir
            raise ValueError("context_mode=rag yalnızca transcript_mode=clean ile kullanılabilir")
        return self

    @model_serializer(mode="wrap")
    def _hide_unused_fields(self, handler):
        # Eski biçimli (context_mode'suz) isteklerin çalıştırma kaydındaki gövdesi değişmesin
        data = handler(self)
        if self.context_mode is None and isinstance(data, dict):
            for key in ("context_mode", "topics", "k", "bloom_levels"):
                data.pop(key, None)
        return data


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
    # Yalnızca context_mode verildiğinde yanıtta yer alır
    topic: str | None = Field(default=None, description="Sorunun üretildiği konu (yalnızca context_mode ile)")
    bloom_level: str | None = Field(
        default=None,
        description="Hedef Bloom düzeyi (yalnızca context_mode ile). Sorunun istemde hedeflendiği düzeydir; "
        "sorunun gerçekten bu düzeyde olduğu iddia edilmez.",
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
    # Yalnızca context_mode verildiğinde yanıtta yer alır
    context_mode: Literal["full", "rag"] | None = Field(
        default=None, description="AS1 koşulu (yalnızca context_mode verildiyse)"
    )
    # Yalnızca check_support=true iken yanıtta yer alır
    support_prompt_version: str | None = Field(
        default=None, description="Destek kontrolünde kullanılan istem sürümü (yalnızca check_support=true iken)"
    )
