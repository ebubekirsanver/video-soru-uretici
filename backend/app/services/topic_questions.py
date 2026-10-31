"""Konu tabanlı soru üretimi: AS1'in iki koşulu (Aşama 7b) ve Bloom yönlendirmesi (Aşama 8, istem questions-v3).

Her konu için bir model çağrısıyla tek soru üretilir. İki koşulda da aynı
konular, aynı istem ve aynı model kullanılır; tek fark modele verilen bağlam:

- "full": transkriptin tamamı, ~30 sn'lik zaman damgalı bloklar hâlinde
  (Aşama 6'daki gibi).
- "rag": o konu için `retrieve(video_id, konu, k)` ile bulunan parçalar, en
  ilgili parça başta olacak şekilde (N. F. Liu vd., 2024: uzun bağlamda
  ortadaki bilgi gözden kaçabiliyor). Erişim sorgusu konunun başlığıdır.

Aşama 8'den beri istem questions-v3: her konuya bir hedef Bloom düzeyi eşlenir;
isteme yalnızca o düzeyin tanımı ve örneği konur (`bloom.py`). Model önce
"reasoning" alanında sorunun neden hedef düzeyde olduğunu yazar (düşünce
zinciri); bu metin yalnızca çalıştırma kaydına girer. questions-v2 dosyaları
geçmiş kaydı olarak duruyor, kullanılmıyor.

Üretilen sorular v1 ile aynı doğrulamadan geçer (`questions.py`): yapı
denetimi, tekrar ayıklama, alıntının TAM temiz transkriptte aranması (RAG
koşulunda da) ve seçenek karıştırma.
"""

import json
import re
from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Callable, Literal

from app.services.bloom import example_text, get_level
from app.services.llm import LLMClient
from app.services.prompts import BLOCK_SECONDS, load_prompt, transcript_context
from app.services.questions import Question, drop_duplicates, parse_questions, verify_candidates
from app.services.retrieval import RetrievedChunk, TranscriptIndex
from app.services.transcript import Transcript

# İstem değişirse yeni dosyalar (v4) açılır. questions-v2 dosyaları geçmiş kaydı olarak duruyor.
PROMPT_VERSION_V3 = "questions-v3"
SYSTEM_PROMPT_FILE = "questions_v3_system.txt"
USER_PROMPT_FILE = "questions_v3_user.txt"

ContextMode = Literal["full", "rag"]

# Konu başına sonuç (AS1 analizinde ayrı sayılır):
# ok: geçerli soru üretildi ve son listede
# empty: model boş liste döndürdü (konu bağlamda yok dedi)
# invalid: model soru döndürdü ama hiçbiri yapı denetiminden geçmedi
# duplicate: geçerli soru üretildi ama başka bir konunun sorusunun tekrarı olarak atıldı
TopicOutcome = Literal["ok", "empty", "invalid", "duplicate"]

# Veri bölümünü ayıran etiket; bağlamda ya da konuda geçerse silinir
_CONTEXT_TAG = re.compile(r"</?\s*bağlam\s*>", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\{(topic|context|bloom_level|bloom_definition|bloom_example)\}")
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


def build_topic_user_prompt(topic: str, context: str, bloom_level: str) -> str:
    """Konu, bağlam ve hedef Bloom düzeyini (yalnızca o düzeyin tanımı ve örneği) kullanıcı istemine yerleştirir.

    Tek geçişte yerleştirilir: bağlamın ya da konunun içinde "{topic}" gibi bir
    metin geçse bile yeniden işlenmez. İki koşulda yalnızca bu alanlar değişir.
    """
    level = get_level(bloom_level)
    values = {
        "topic": _clean(topic).strip(),
        "context": context,
        "bloom_level": level.name,
        "bloom_definition": level.definition,
        "bloom_example": example_text(level),
    }
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], load_prompt(USER_PROMPT_FILE))


@dataclass
class TopicTrace:
    """Bir konu için kayda yazılan adım bilgisi."""

    topic: str
    context_words: int
    # Geriye dönük uyumluluk için duruyor: model bu konu için yapı denetiminden
    # geçen bir soru döndürdü mü (ok ve duplicate için True)
    produced: bool
    retrieved: list[dict] | None = None  # yalnızca rag: chunk_index, start/end_seconds, score
    outcome: TopicOutcome = "ok"
    bloom_level: str | None = None  # hedef düzey


@dataclass
class TopicGeneration:
    questions: list[Question]
    traces: list[TopicTrace]
    dropped: dict = field(default_factory=dict)

    @property
    def no_question_topics(self) -> list[str]:
        """Geriye dönük uyumlu: yapı denetiminden geçen soru gelmeyen konular (empty + invalid).

        Ayrımı için konu başına `outcome` alanına bakılır.
        """
        return [t.topic for t in self.traces if t.outcome in ("empty", "invalid")]

    @property
    def outcome_counts(self) -> dict[str, int]:
        counts = {"ok": 0, "empty": 0, "invalid": 0, "duplicate": 0}
        for t in self.traces:
            counts[t.outcome] += 1
        return counts


def generate_topic_questions(
    topics: list[str],
    context_mode: ContextMode,
    context_transcript: Transcript,
    reference: Transcript,
    llm: LLMClient,
    *,
    bloom_levels: list[str],
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
    bloom_levels: konularla aynı sırada ve uzunlukta hedef Bloom düzeyleri.

    Model bir konu için soru döndürmezse (boş liste) o konu atlanır, hata
    verilmez. Her konunun sonucu (`ok` / `empty` / `invalid` / `duplicate`)
    `TopicTrace.outcome` alanında tutulur.
    """
    if context_mode not in ("full", "rag"):
        raise ValueError(f"Geçersiz context_mode: {context_mode!r}")
    if len(bloom_levels) != len(topics):
        raise ValueError("bloom_levels konularla aynı uzunlukta olmalı.")
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
    candidates, candidate_topics, candidate_levels, candidate_traces, traces = [], [], [], [], []
    structure_invalid = extra_ignored = 0
    for topic, bloom_level in zip(topics, bloom_levels):
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

        raw = llm.complete(system=system, user=build_topic_user_prompt(topic, context, bloom_level), json_mode=True)
        parsed = parse_questions(raw)
        # parse_questions başarılıysa yanıt bir "questions" listesi içerir
        returned = len(json.loads(raw)["questions"])
        structure_invalid += returned - len(parsed)
        if parsed:
            outcome = "ok"  # tekrar olarak atılırsa aşağıda "duplicate" olur
            candidates.append(parsed[0])
            candidate_topics.append(topic)
            candidate_levels.append(bloom_level)
            candidate_traces.append(len(traces))
            extra_ignored += len(parsed) - 1  # istem en çok 1 soru istiyor
        else:
            outcome = "empty" if returned == 0 else "invalid"
        traces.append(TopicTrace(topic, context_word_count(context), bool(parsed), retrieved, outcome, bloom_level))

    unique = drop_duplicates(candidates)
    for q, trace_index in zip(candidates, candidate_traces):
        if not any(q is u for u in unique):
            traces[trace_index].outcome = "duplicate"
    kept = [(q, t, lv) for q, t, lv in zip(candidates, candidate_topics, candidate_levels) if any(q is u for u in unique)]
    questions = verify_candidates([q for q, _, _ in kept], reference, [t for _, t, _ in kept], [lv for _, _, lv in kept])
    dropped = {
        "structure_invalid": structure_invalid,
        "duplicate": len(candidates) - len(unique),
        "extra_ignored": extra_ignored,
    }
    return TopicGeneration(questions=questions, traces=traces, dropped=dropped)
