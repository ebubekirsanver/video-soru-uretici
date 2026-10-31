"""Anlamca benzer soruları işaretleme (Aşama 9, tekrar eleme; kural sürümü similarity-v1).

`questions.drop_duplicates` yalnızca normalleştirilmiş metni birebir aynı olan
soruları atar. 7b koşul denemesinde (docs/bulgular/asama-7b-kosul-denemesi-1.md)
metni farklı ama aynı bilgiyi soran sorular listede kaldı. Bu modül her
sorunun "soru metni + doğru cevap" metnini gömer (BGE-M3) ve aynı istekteki
soru çiftlerinin kosinüs benzerliğini hesaplar; eşiği geçen çiftleri işaretler.

Yalnızca İŞARETLER, soru atılmaz (yazım kurallarındaki gibi): deneyde her
videoda 6 soru olmalı; atma kararı öğretmen onayına ve değerlendirmeye kalır.
Sonuç yalnızca çalıştırma kaydına yazılır, API yanıtına girmez.
"""

import math
from dataclasses import dataclass

from app.services.embeddings import EmbeddingClient

SIMILARITY_VERSION = "similarity-v1"
# Karar (docs/bulgular/asama-9-benzer-sorular-1.md): Eşik 0,80 (soru + doğru cevap
# skoru). Bu 16 çiftte 'farklı' etiketlilerin en yüksek skoru 0,669, 'aynı bilgi'
# etiketlilerin en düşük skoru 0,907; eşik ikisinin arasından, iki tarafa pay
# bırakacak biçimde seçildi. Eşik aynı veride seçildiği için iyimser; pilot
# videolarda yeniden bakılacak. Kod soruları yalnızca işaretler, atmaz.
SIMILARITY_THRESHOLD = 0.80


def pair_text(question: str, answer: str) -> str:
    """Gömülen metin: soru metni ve doğru cevabın metni (harf değil)."""
    return f"{question} {answer}"


@dataclass
class SimilarPair:
    a: int  # 1'den başlayan soru sırası
    b: int
    score: float  # kosinüs benzerliği


def _cosine(u: list[float], v: list[float]) -> float:
    dot = sum(x * y for x, y in zip(u, v))
    norm = math.sqrt(sum(x * x for x in u)) * math.sqrt(sum(y * y for y in v))
    return dot / norm if norm else 0.0


def pair_scores(texts: list[str], embedder: EmbeddingClient) -> list[SimilarPair]:
    """Bütün çiftlerin (i < j) kosinüs benzerliği; 2'den az metin varsa gömme yapılmaz."""
    if len(texts) < 2:
        return []
    vectors = embedder.embed(texts)
    return [
        SimilarPair(i + 1, j + 1, round(_cosine(vectors[i], vectors[j]), 6))
        for i in range(len(texts))
        for j in range(i + 1, len(texts))
    ]


def flag_similar(questions: list, embedder: EmbeddingClient, threshold: float = SIMILARITY_THRESHOLD) -> list[SimilarPair]:
    """Aynı istekteki soru çiftlerinden benzerliği eşiğe eşit ya da üstünde olanları döndürür."""
    texts = [pair_text(q.question, q.options[q.correct_index]) for q in questions]
    return [p for p in pair_scores(texts, embedder) if p.score >= threshold]


def similarity_record(questions: list, pairs: list[SimilarPair], threshold: float = SIMILARITY_THRESHOLD) -> dict:
    """Kayda yazılacak `similarity_check` alanı."""
    return {
        "rules_version": SIMILARITY_VERSION,
        "threshold": threshold,
        "text": "soru metni + doğru cevap",
        "flagged_pairs": [
            {"a": p.a, "b": p.b, "score": p.score,
             "question_a": questions[p.a - 1].question, "question_b": questions[p.b - 1].question}
            for p in pairs
        ],
    }
