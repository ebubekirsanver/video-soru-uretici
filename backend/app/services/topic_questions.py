"""Konu tabanlı soru üretimi: AS1'in iki koşulu (Aşama 7b, istem questions-v2).

Her konu için bir model çağrısıyla tek soru üretilir. İki koşulda da aynı
konular, aynı istem ve aynı model kullanılır; tek fark modele verilen bağlam:

- "full": transkriptin tamamı, ~30 sn'lik zaman damgalı bloklar hâlinde
  (Aşama 6'daki gibi).
- "rag": o konu için `retrieve(video_id, konu, k)` ile bulunan parçalar, en
  ilgili parça başta olacak şekilde (N. F. Liu vd., 2024: uzun bağlamda
  ortadaki bilgi gözden kaçabiliyor). Erişim sorgusu konunun başlığıdır.

Üretilen sorular v1 ile aynı doğrulamadan geçer (`questions.py`): yapı
denetimi, tekrar ayıklama, alıntının TAM temiz transkriptte aranması (RAG
koşulunda da) ve seçenek karıştırma.
"""

import json
import re
from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Callable, Literal

from app.services.llm import LLMClient
from app.services.prompts import BLOCK_SECONDS, load_prompt, transcript_context
from app.services.questions import Question, drop_duplicates, parse_questions, verify_candidates
from app.services.retrieval import RetrievedChunk, TranscriptIndex
from app.services.transcript import Transcript

# İstem değişirse yeni dosyalar (v3) açılır
PROMPT_VERSION_V2 = "questions-v2"
SYSTEM_PROMPT_FILE = "questions_v2_system.txt"
USER_PROMPT_FILE = "questions_v2_user.txt"

ContextMode = Literal["full", "rag"]

# Veri bölümünü ayıran etiket; bağlamda ya da konuda geçerse silinir
_CONTEXT_TAG = re.compile(r"</?\s*bağlam\s*>", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\{(topic|context)\}")
_TIME_LABEL = re.compile(r"^\[\d+\]\s*", re.MULTILINE)


def _clean(text: str) -> str:
    return _CONTEXT_TAG.sub("", text)


def full_context(transcript: Transcript, block_seconds: float = BLOCK_SECONDS) -> str:
    """Tam transkript koşulu: v1 ile aynı ~30 sn'lik `[saniye] metin` blokları."""
    return _clean(transcript_context(transcript, block_seconds))


def rag_context(chunks: list[RetrievedChunk]) -> str:
    """RAG koşulu: erişilen parçalar verildiği sırayla (en ilgili başta), `[başlangıç saniyesi] metin`."""
    return "\n".join(f"[{int(c.start_seconds)}] {_clean(c.text)}" for c in chunks)


def context_word_count(context: str) -> int:
    """Bağlamın kelime sayısı (satır başındaki `[saniye]` etiketleri sayılmaz)."""
    return len(_TIME_LABEL.sub("", context).split())


def build_topic_user_prompt(topic: str, context: str) -> str:
    """Konu ve bağlamı kullanıcı istemine tek geçişte yerleştirir.

    Bağlamın ya da konunun içinde "{topic}" gibi bir metin geçse bile yeniden işlenmez.
    """
    values = {"topic": _clean(topic).strip(), "context": context}
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], load_prompt(USER_PROMPT_FILE))


@dataclass
class TopicTrace:
    """Bir konu için kayda yazılan adım bilgisi."""

    topic: str
    context_words: int
    produced: bool  # model bu konu için soru döndürdü mü
    retrieved: list[dict] | None = None  # yalnızca rag: chunk_index, start/end_seconds, score


@dataclass
class TopicGeneration:
    questions: list[Question]
    traces: list[TopicTrace]
    dropped: dict = field(default_factory=dict)

    @property
    def no_question_topics(self) -> list[str]:
        return [t.topic for t in self.traces if not t.produced]


def generate_topic_questions(
    topics: list[str],
    context_mode: ContextMode,
    context_transcript: Transcript,
    reference: Transcript,
    llm: LLMClient,
    *,
    index: TranscriptIndex | None = None,
    k: int = 5,
    timer: Callable[[str], object] | None = None,
) -> TopicGeneration:
    """Her konu için bir model çağrısıyla tek soru üretir ve doğrular.

    context_transcript: "full" koşulunda modele verilen transkript (ham ya da temiz).
    reference: temizlenmiş transkriptin tamamı; alıntılar burada aranır, "rag"
        koşulunda dizin de bundan kurulur.
    index: "rag" koşulunda gerekli. Video önce dizinlenir (önbellek varsa
        yeniden gömülmez), sonra her konu için erişim yapılır.
    timer: `timer("index")` / `timer("retrieval")` bir bağlam yöneticisi
        döndürür; süreler çalıştırma kaydı için ölçülür.

    Model bir konu için soru döndürmezse (boş liste) o konu atlanır, hata
    verilmez; `no_question_topics` içinde görünür.
    """
    if context_mode not in ("full", "rag"):
        raise ValueError(f"Geçersiz context_mode: {context_mode!r}")
    timer = timer or (lambda name: nullcontext())
    video_id = reference.video_id

    if context_mode == "rag":
        if index is None:
            raise ValueError("rag koşulu için dizin gerekli.")
        with timer("index"):
            index.index_transcript(video_id, reference.segments)
        shared_context = None
    else:
        shared_context = full_context(context_transcript)

    system = load_prompt(SYSTEM_PROMPT_FILE)
    candidates, candidate_topics, traces = [], [], []
    structure_invalid = extra_ignored = 0
    for topic in topics:
        retrieved = None
        if context_mode == "rag":
            with timer("retrieval"):
                found = index.retrieve(video_id, topic, k=k)
            context = rag_context(found)
            retrieved = [
                {"chunk_index": c.chunk_index, "start_seconds": c.start_seconds,
                 "end_seconds": c.end_seconds, "score": c.score}
                for c in found
            ]
        else:
            context = shared_context

        raw = llm.complete(system=system, user=build_topic_user_prompt(topic, context), json_mode=True)
        parsed = parse_questions(raw)
        # parse_questions başarılıysa yanıt bir "questions" listesi içerir
        structure_invalid += len(json.loads(raw)["questions"]) - len(parsed)
        if parsed:
            candidates.append(parsed[0])
            candidate_topics.append(topic)
            extra_ignored += len(parsed) - 1  # istem en çok 1 soru istiyor
        traces.append(TopicTrace(topic, context_word_count(context), bool(parsed), retrieved))

    unique = drop_duplicates(candidates)
    kept = [(q, t) for q, t in zip(candidates, candidate_topics) if any(q is u for u in unique)]
    questions = verify_candidates([q for q, _ in kept], reference, [t for _, t in kept])
    dropped = {
        "structure_invalid": structure_invalid,
        "duplicate": len(candidates) - len(unique),
        "extra_ignored": extra_ignored,
    }
    return TopicGeneration(questions=questions, traces=traces, dropped=dropped)
