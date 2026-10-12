"""Transkriptten çoktan seçmeli soru üretimi (RAG'siz taban çizgisi).

Transkriptin tamamı bağlam olarak LLM'e verilir; RAG Aşama 7'de eklenecek.
Üretimden sonra LLM'e güvenilmez, her soru kodda doğrulanır:
yapı (4 farklı seçenek, geçerli correct_index, boş alan yok), kaynak
alıntısının transkriptte geçmesi ve tekrar eden soruların atılması.
"""

import hashlib
import json
import logging
import random
import re
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ValidationError, field_validator

from app.services.llm import LLMClient, LLMError
from app.services.prompts import BLOCK_SECONDS, fill_prompt, load_prompt, transcript_context
from app.services.quotes import QuoteLocator, normalize
from app.services.transcript import Transcript

logger = logging.getLogger(__name__)

# İstem değişirse yeni dosyalar (v2) açılır; her soru hangi istemle üretildiğini taşır
PROMPT_VERSION = "questions-v1"
SYSTEM_PROMPT_FILE = "questions_v1_system.txt"
USER_PROMPT_FILE = "questions_v1_user.txt"
OPTION_COUNT = 4
# Alıntının başındaki [219] ya da [124.5] biçiminde saniye etiketi
_TIME_LABEL = re.compile(r"^\s*\[\d+(?:[.,]\d+)?\]")


@dataclass
class Question:
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    source_quote: str
    source_start_seconds: float | None  # alıntı bulunamazsa None
    verified: bool
    quote_match: Literal["exact", "trimmed"] | None  # alıntı bulunamazsa None
    # Yalnızca çalıştırma kaydı için (API yanıtına girmez): modelin yazdığı ham
    # alıntı ve kırpılan kelimeler (normalleştirilmiş)
    model_quote: str = ""
    trimmed_head: list[str] = field(default_factory=list)
    trimmed_tail: list[str] = field(default_factory=list)


# LLM'in döndürdüğü tek bir sorunun beklenen yapısı
class _QuestionModel(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    source_quote: str

    @field_validator("question", "explanation", "source_quote")
    @classmethod
    def _not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("boş olamaz")
        return value

    @field_validator("options")
    @classmethod
    def _four_distinct_options(cls, value: list[str]) -> list[str]:
        value = [o.strip() for o in value]
        if len(value) != OPTION_COUNT:
            raise ValueError(f"tam {OPTION_COUNT} seçenek olmalı")
        if any(not o for o in value):
            raise ValueError("boş seçenek olamaz")
        if len({normalize(o) for o in value}) != OPTION_COUNT:
            raise ValueError("seçenekler birbirinden farklı olmalı")
        return value

    @field_validator("correct_index")
    @classmethod
    def _index_in_range(cls, value: int) -> int:
        if not 0 <= value < OPTION_COUNT:
            raise ValueError(f"0 ile {OPTION_COUNT - 1} arasında olmalı")
        return value


def build_user_prompt(transcript: Transcript, count: int, block_seconds: float = BLOCK_SECONDS) -> str:
    """Transkriptin tamamını zaman damgalı bloklar halinde soru istemine yerleştirir."""
    return fill_prompt(
        load_prompt(USER_PROMPT_FILE),
        transcript_context(transcript, block_seconds),
        count=count,
        duration_seconds=int(transcript.duration_seconds),
    )


def parse_questions(raw: str) -> list[_QuestionModel]:
    """LLM yanıtını ayrıştırır; yapısı bozuk sorular tek tek atılır.

    Yanıtın tamamı JSON değilse ya da `questions` listesi yoksa LLMError fırlatılır.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM yanıtı geçerli JSON değil.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        raise LLMError("LLM yanıtında 'questions' listesi yok.")

    valid = []
    for i, item in enumerate(data["questions"]):
        try:
            valid.append(_QuestionModel.model_validate(item))
        except ValidationError as exc:
            logger.warning("Soru %d yapı denetiminden geçemedi, atıldı: %s", i, exc.errors()[0]["msg"])
    return valid


def drop_duplicates(questions: list[_QuestionModel]) -> list[_QuestionModel]:
    """Soru metni aynı olanlardan (harf, boşluk, noktalama farkı yok sayılarak) ilkini tutar."""
    seen: set[str] = set()
    unique = []
    for q in questions:
        key = normalize(q.question)
        if key in seen:
            logger.warning("Tekrar eden soru atıldı: %s", q.question)
            continue
        seen.add(key)
        unique.append(q)
    return unique


def strip_time_label(quote: str) -> str:
    """Alıntının başındaki `[219]` gibi saniye etiketini siler.

    İstem bunu yasaklasa da model blok etiketini alıntıya kopyalayabiliyor
    (bkz. docs/bulgular/asama-6-test-1.md, Bulgu 5).
    """
    return _TIME_LABEL.sub("", quote, count=1).strip()


def shuffle_options(question: str, options: list[str], correct_index: int) -> tuple[list[str], int]:
    """Seçenekleri karıştırır ve doğru cevabın yeni konumunu döndürür.

    Model doğru cevabı belli şıklara yığabildiği için sıra kodda belirlenir.
    Tohum soru metninden türetilir (sha256; Python'un hash() fonksiyonu her
    çalıştırmada değiştiği için kullanılmaz), böylece aynı soru her seferinde
    aynı sırayı verir ve sonuçlar tekrarlanabilir.
    """
    seed = int.from_bytes(hashlib.sha256(question.encode("utf-8")).digest()[:8], "big")
    order = list(range(len(options)))
    random.Random(seed).shuffle(order)
    return [options[i] for i in order], order.index(correct_index)


def generate_questions(
    context: Transcript,
    reference: Transcript,
    llm: LLMClient,
    count: int,
    block_seconds: float = BLOCK_SECONDS,
) -> list[Question]:
    """Soruları üretir ve doğrular.

    context: LLM'e verilen transkript (ham ya da temiz, kullanıcının seçimi).
    reference: alıntıların arandığı temizlenmiş transkript.
    """
    if not context.segments:
        raise ValueError("Soru üretilecek transkript boş.")

    raw = llm.complete(
        system=load_prompt(SYSTEM_PROMPT_FILE),
        user=build_user_prompt(context, count, block_seconds),
        json_mode=True,
    )
    candidates = drop_duplicates(parse_questions(raw))[:count]

    locator = QuoteLocator(reference.segments)
    questions = []
    for q in candidates:
        found = locator.match(q.source_quote)
        if found:
            # Doğrulanan alıntıda öğrenciye videoda gerçekten geçen metin gösterilir
            # (modelin eklediği [saniye] etiketi ve kırpılan sözcükler gitmiş olur)
            source_quote = found.text
        else:
            source_quote = strip_time_label(q.source_quote)
        options, correct_index = shuffle_options(q.question, q.options, q.correct_index)
        questions.append(
            Question(
                question=q.question,
                options=options,
                correct_index=correct_index,
                explanation=q.explanation,
                source_quote=source_quote,
                source_start_seconds=found.start_seconds if found else None,
                verified=found is not None,
                quote_match=found.match if found else None,
                model_quote=q.source_quote,
                trimmed_head=found.trimmed_head if found else [],
                trimmed_tail=found.trimmed_tail if found else [],
            )
        )
    return questions
