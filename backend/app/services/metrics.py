"""Aşama bazlı süre, model çağrısı (token) ve hata ölçümü (Aşama 14).

Her istek için uç noktada yeni bir `RunMetrics` nesnesi oluşturulur; ölçümler
yalnızca çalıştırma kaydına yazılır, API yanıtına girmez.

Eşzamanlılık: model istemcisi istekler arasında paylaşılabilir. Bu yüzden
çağrı bilgisi istemcide değil, isteğe özel nesnede birikir. `OpenAIClient`
token bilgisini yalnızca bir `ContextVar`'a yazar (`llm.py`); her istek kendi bağlamında
(FastAPI'de ayrı iş parçacığı ve bağlam kopyası) çalıştığı için aynı anda
gelen iki istek birbirinin ölçümünü göremez.

Maliyet hesaplanmaz: kayda yalnızca model adı ve token sayıları yazılır.
Fiyat kullanıcıdan gelecek ve kayıt dışında hesaplanacak.
"""

import re
import time
from contextlib import contextmanager
from typing import Literal

from app.services.llm import TOKEN_FIELDS, LLMClient, LLMNotConfigured, last_usage, reset_usage

Purpose = Literal["summary", "questions", "support"]

# Testlerde sabit saat verilebilsin diye ayrı ad
clock = time.perf_counter


def _ms(start: float) -> float:
    return round((clock() - start) * 1000, 1)



class RunMetrics:
    """Tek bir isteğin ölçümleri."""

    def __init__(self):
        self.started = clock()
        self.stages: dict[str, float] = {}
        self.llm_calls: list[dict] = []
        self.dropped: dict[str, int] | None = None
        self.failed_stage: str | None = None

    @contextmanager
    def stage(self, name: str):
        """Bloğun süresini `<name>_ms` olarak yazar; hata olursa aşama adını saklar."""
        start = clock()
        try:
            yield
        except BaseException:
            self.failed_stage = self.failed_stage or name
            raise
        finally:
            self.stages[f"{name}_ms"] = _ms(start)

    @contextmanager
    def model_step(self, llm_stage: str, rest_stage: str, purpose: Purpose):
        """Model çağrısını içeren bir servis çağrısını ikiye böler.

        `llm_stage`: bu amaçla yapılan model çağrılarının toplam süresi.
        `rest_stage`: geri kalan süre (yanıt ayrıştırma, yapı denetimi ve
        sorularda alıntı doğrulama, seçenek karıştırma).
        Hata olursa: model yanıt verdiyse hata ayrıştırma/denetim adımındadır
        (`rest_stage`), vermediyse model çağrısındadır (`llm_stage`).
        """
        start = clock()
        try:
            yield
        except BaseException:
            self.failed_stage = self.failed_stage or (rest_stage if self.model_returned(purpose) else llm_stage)
            raise
        finally:
            total = (clock() - start) * 1000
            llm = sum(c["ms"] for c in self.llm_calls if c["purpose"] == purpose)
            self.stages[f"{llm_stage}_ms"] = round(llm, 1)
            self.stages[f"{rest_stage}_ms"] = round(max(total - llm, 0.0), 1)

    def model_returned(self, purpose: Purpose) -> bool:
        """Bu amaçla yapılan çağrılardan en az biri yanıt döndürdü mü?"""
        return any(c["purpose"] == purpose and c["ok"] for c in self.llm_calls)

    def track(self, llm: LLMClient, purpose: Purpose) -> "TrackedLLM":
        """Model istemcisini, çağrıları bu isteğe kaydeden ince bir sarmalayıcıyla döndürür."""
        return TrackedLLM(llm, self, purpose)

    def as_dict(self) -> dict:
        """Kayda yazılacak `metrics` alanı; `total_ms` istek başından bu ana kadardır."""
        data = {
            "stages": {**self.stages, "total_ms": _ms(self.started)},
            "llm_calls": self.llm_calls,
        }
        if self.dropped is not None:
            data["dropped"] = self.dropped
        return data


class TrackedLLM:
    """`LLMClient` sarmalayıcısı: her çağrının süresini ve token sayısını isteğin ölçümüne ekler.

    Dönüş tipi değişmez (`str`); servis kodu sarmalayıcıyı fark etmez.
    """

    def __init__(self, inner: LLMClient, metrics: RunMetrics, purpose: Purpose):
        self.inner, self.metrics, self.purpose = inner, metrics, purpose
        self.model = inner.model

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        reset_usage()
        start = clock()
        ok = False
        try:
            result = self.inner.complete(system=system, user=user, json_mode=json_mode)
            ok = True
            return result
        except LLMNotConfigured:
            # API anahtarı yok: çağrı hiç yapılmadı, kayda çağrı yazılmaz
            start = None
            raise
        finally:
            if start is not None:
                usage = last_usage() or {}
                self.metrics.llm_calls.append(
                    {
                        "purpose": self.purpose,
                        "ms": _ms(start),
                        "model": self.model,
                        "ok": ok,
                        **{k: usage.get(k) for k in TOKEN_FIELDS},
                    }
                )


# --- Hata kaydı ve gizli bilgi temizliği --------------------------------------------

MAX_DETAIL_CHARS = 300

_SECRET_PATTERNS = [
    # OpenAI biçimli anahtarlar (sk-..., sk-proj-...)
    (re.compile(r"sk-[A-Za-z0-9_\-*]{6,}"), "sk-***"),
    # Yetkilendirme başlığı
    (re.compile(r"(?i)\b(authorization)\s*[:=]\s*\S+(\s+\S+)?"), r"\1: ***"),
    (re.compile(r"(?i)\bbearer\s+\S+"), "Bearer ***"),
    # anahtar=değer biçimindeki gizli alanlar
    (re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|token|password|parola|secret)\s*[:=]\s*\S+"), r"\1=***"),
]


def scrub_secrets(text: str, known_secrets: tuple[str, ...] = ()) -> str:
    """Hata metninden API anahtarı, yetki başlığı ve anahtar benzeri dizgileri siler."""
    for secret in known_secrets:
        if secret:
            text = text.replace(secret, "***")
    for pattern, repl in _SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


ErrorKind = Literal["invalid_url", "transcript_unavailable", "llm_not_configured", "llm_failed", "invalid_json"]


def error_kind(status_code: int, metrics: RunMetrics, purpose: Purpose) -> ErrorKind | None:
    """Uç noktanın döndürdüğü HTTP koduna göre hata türü.

    502'de model yanıt verdiyse yanıt kullanılamadı (geçersiz JSON ya da
    beklenen yapı yok), vermediyse çağrının kendisi başarısız oldu.
    """
    if status_code == 502:
        return "invalid_json" if metrics.model_returned(purpose) else "llm_failed"
    return {422: "invalid_url", 404: "transcript_unavailable", 503: "llm_not_configured"}.get(status_code)


def error_record(status_code: int, detail: str, metrics: RunMetrics, purpose: Purpose, known_secrets=()) -> dict:
    """Kayda yazılacak `error` alanı (kısa, gizli bilgiden arındırılmış)."""
    detail = scrub_secrets(str(detail), tuple(known_secrets))
    if len(detail) > MAX_DETAIL_CHARS:
        detail = detail[: MAX_DETAIL_CHARS - 1].rstrip() + "…"
    return {
        "status_code": status_code,
        "kind": error_kind(status_code, metrics, purpose),
        "detail": detail,
        "stage": metrics.failed_stage,
    }
