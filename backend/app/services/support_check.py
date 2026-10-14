"""Alıntı cevabı destekliyor mu? (Aşama 9'un ilk adımı)

Kod tarafındaki doğrulama (`quotes.py`) yalnızca alıntının transkriptte
geçtiğini söyler; alıntının doğru cevabı desteklediğini göstermez
(bkz. docs/bulgular/asama-12d-test-1.md). Bu servis her doğrulanmış soru için
ayrı bir LLM çağrısıyla bunu sorar.

Önemli: sonuç bir **model değerlendirmesidir**, kesin doğru kabul edilmemelidir.
Model de yanılabilir; bu kontrolün ne kadar isabetli olduğu ayrıca ölçülmelidir.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Literal

from app.services.llm import LLMClient, LLMError
from app.services.prompts import load_prompt
from app.services.quotes import turkish_lower

logger = logging.getLogger(__name__)

# İstem değişirse yeni dosyalar (v2) açılır; yanıtta hangi istemin kullanıldığı yazılır
SUPPORT_PROMPT_VERSION = "support-v1"
SYSTEM_PROMPT_FILE = "support_v1_system.txt"
USER_PROMPT_FILE = "support_v1_user.txt"

# Modelin verebileceği etiketler
MODEL_LABELS = ("destekliyor", "kısmen", "desteklemiyor")
# Kodun verdiği etiketler: alıntı transkriptte bulunamadıysa çağrı yapılmaz;
# çağrı başarısız olursa ya da model geçersiz yanıt verirse sonuç bilinmez
NOT_CHECKED = "kontrol edilmedi"
CHECK_FAILED = "kontrol edilemedi"

SupportLabel = Literal["destekliyor", "kısmen", "desteklemiyor", "kontrol edilmedi", "kontrol edilemedi"]

# Gerekçe en fazla bir cümle istenir; model uzun yazarsa yanıtı şişirmesin
MAX_REASON_CHARS = 300

# Veri bölümlerini ayıran etiketler; veri içinde geçerlerse silinir
_DATA_TAGS = re.compile(r"</?\s*(soru|dogru_cevap|alinti)\s*>", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\{(question|answer|quote)\}")


@dataclass
class SupportResult:
    label: SupportLabel
    reason: str
    model_raw: str | None = None  # yalnızca çalıştırma kaydı için: modelin ham yanıtı


def _clean_data(text: str) -> str:
    return _DATA_TAGS.sub("", text).strip()


def build_user_prompt(question: str, answer: str, quote: str) -> str:
    """Soru, doğru cevap metni ve alıntıyı istem şablonuna yerleştirir.

    Tek geçişte yerleştirilir: alıntının içinde "{question}" gibi bir metin
    geçse bile yeniden işlenmez.
    """
    values = {"question": _clean_data(question), "answer": _clean_data(answer), "quote": _clean_data(quote)}
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], load_prompt(USER_PROMPT_FILE))


def parse_support(raw: str) -> SupportResult:
    """Model yanıtını doğrular. Geçersizse LLMError fırlatır."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError("Destek kontrolü yanıtı geçerli JSON değil.") from exc
    if not isinstance(data, dict):
        raise LLMError("Destek kontrolü yanıtı bir JSON nesnesi değil.")

    label = data.get("label")
    reason = data.get("reason")
    if not isinstance(label, str) or not isinstance(reason, str):
        raise LLMError("Destek kontrolü yanıtında 'label' ya da 'reason' eksik.")

    label = turkish_lower(label.strip())
    if label not in MODEL_LABELS:
        raise LLMError(f"Destek kontrolü yanıtında geçersiz etiket: {label!r}")
    reason = reason.strip()
    if len(reason) > MAX_REASON_CHARS:
        reason = reason[: MAX_REASON_CHARS - 1].rstrip() + "…"
    return SupportResult(label=label, reason=reason, model_raw=raw)


def check_one(question: str, answer: str, quote: str, llm: LLMClient) -> SupportResult:
    """Tek bir soru için modelden değerlendirme ister.

    Çağrı başarısız olursa ya da yanıt geçersizse istek bozulmaz: sonuç
    "kontrol edilemedi" olur ve neden günlüğe yazılır.
    """
    raw = None
    try:
        raw = llm.complete(
            system=load_prompt(SYSTEM_PROMPT_FILE),
            user=build_user_prompt(question, answer, quote),
            json_mode=True,
        )
        return parse_support(raw)
    except LLMError as exc:
        logger.warning("Destek kontrolü yapılamadı: %s", exc)
        return SupportResult(label=CHECK_FAILED, reason="Model değerlendirmesi alınamadı.", model_raw=raw)


def check_support(questions: list, llm: LLMClient) -> list[SupportResult]:
    """Her soru için destek kontrolü yapar; sonuçlar soru sırasıyla döner.

    Yalnızca alıntısı transkriptte bulunan (`verified`) sorular için çağrı
    yapılır, yani çağrı sayısı en çok soru sayısı kadardır. Doğrulanamayan
    sorular "kontrol edilmedi" olarak işaretlenir.
    """
    results = []
    for q in questions:
        if not q.verified:
            results.append(SupportResult(label=NOT_CHECKED, reason="Alıntı transkriptte bulunamadığı için kontrol yapılmadı."))
            continue
        answer = q.options[q.correct_index]  # harfi değil, seçeneğin metni
        results.append(check_one(q.question, answer, q.source_quote, llm))
    return results
