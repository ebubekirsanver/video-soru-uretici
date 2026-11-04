"""Anlamca benzer soruları işaretleme (similarity-v1). Sahte gömme; gerçek model yüklenmez."""

import json
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.embeddings import EmbeddingUnavailable, get_embedder_provider
from app.services.llm import get_llm
from app.services.similarity import (
    SIMILARITY_THRESHOLD,
    SIMILARITY_VERSION,
    flag_similar,
    pair_scores,
    pair_text,
    similarity_record,
)
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"


class KeywordEmbedder:
    """Metinde geçen anahtar kelimeye göre vektör verir: aynı anahtar kelime → aynı yön."""

    model = "keyword-embedder"
    KEYS = ("enerji", "prokaryot", "baca", "fotosentez")

    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(list(texts))
        return [[1.0 if k in t.lower() else 0.0 for k in self.KEYS] + [0.01] for t in texts]


def q(question, answer):
    return SimpleNamespace(question=question, options=[answer, "b", "c", "d"], correct_index=0)


# --- Servis -----------------------------------------------------------------------


def test_similar_pair_flagged_different_not():
    questions = [
        q("Kemosentez yapan canlılar hangi enerji kaynağını kullanır?", "Kimyasal enerji"),
        q("Kemosentetik canlılar hangi enerji kaynağıyla besin üretir?", "Kimyasal enerji"),
        q("Kemosentez yapan canlıların hücre yapısı nedir?", "Prokaryot"),
    ]
    pairs = flag_similar(questions, KeywordEmbedder(), threshold=0.9)
    assert [(p.a, p.b) for p in pairs] == [(1, 2)]
    assert pairs[0].score == pytest.approx(1.0)


def test_single_or_no_question_has_no_pairs_and_no_embedding():
    embedder = KeywordEmbedder()
    assert flag_similar([q("Tek soru enerji?", "a")], embedder) == []
    assert flag_similar([], embedder) == []
    assert embedder.calls == []


def test_embedded_text_is_question_plus_correct_answer():
    embedder = KeywordEmbedder()
    question = SimpleNamespace(question="Soru metni?", options=["a", "Doğru cevap", "c", "d"], correct_index=1)
    flag_similar([question, q("İkinci soru?", "x")], embedder)
    assert embedder.calls[0][0] == pair_text("Soru metni?", "Doğru cevap") == "Soru metni? Doğru cevap"


def test_pair_scores_lists_every_pair():
    scores = pair_scores(["enerji", "enerji", "prokaryot"], KeywordEmbedder())
    assert [(p.a, p.b) for p in scores] == [(1, 2), (1, 3), (2, 3)]


def test_record_fields():
    questions = [q("A enerji?", "x"), q("B enerji?", "y")]
    pairs = flag_similar(questions, KeywordEmbedder(), threshold=0.9)
    record = similarity_record(questions, pairs, threshold=0.9)
    assert record["rules_version"] == SIMILARITY_VERSION == "similarity-v1"
    assert record["threshold"] == 0.9 and "threshold_provisional" not in record
    assert record["flagged_pairs"] == [
        {"a": 1, "b": 2, "score": pytest.approx(1.0), "question_a": "A enerji?", "question_b": "B enerji?"}
    ]


# --- API ----------------------------------------------------------------------------

QUESTIONS = {
    "Enerji kaynağı": ("Kemosentez yapan canlılar hangi enerji kaynağını kullanır?", "Kimyasal enerji",
                       "kemosentez yapan canlılar kimyasal enerji kullanır"),
    "Enerji tekrar": ("Kemosentetik canlılar hangi enerji kaynağıyla besin üretir?", "Kimyasal enerji",
                      "kemosentez yapan canlılar kimyasal enerji kullanır"),
    "Hücre yapısı": ("Kemosentez yapan canlıların hücre yapısı nedir?", "Prokaryot",
                     "bu canlıların tamamı prokaryot hücre yapısına sahiptir"),
}


class TopicLLM:
    model = "fake-model"

    def complete(self, system, user, json_mode=False, max_tokens=None):
        topic = re.search(r"^Konu: (.+)$", user, re.MULTILINE).group(1)
        question, answer, quote = QUESTIONS[topic]
        item = {"question": question, "options": [answer, "Işık enerjisi", "Isı", "Ses"],
                "correct_index": 0, "explanation": "açıklama", "source_quote": quote}
        return json.dumps({"questions": [item]}, ensure_ascii=False)


class V1LLM:
    model = "fake-model"

    def complete(self, system, user, json_mode=False, max_tokens=None):
        items = [
            {"question": question, "options": [answer, "Işık enerjisi", "Isı", "Ses"], "correct_index": 0,
             "explanation": "açıklama", "source_quote": quote}
            for question, answer, quote in QUESTIONS.values()
        ]
        return json.dumps({"questions": items}, ensure_ascii=False)


class BloomDefaultClient(TestClient):
    """Aşama 8'den beri context_mode isteklerinde konu sayısı 6 değilse bloom_levels gerekiyor.

    Bu dosyadaki testler düzeyden bağımsız davranışı (koşullar, kayıt, doğrulama)
    denetlediği için, context_mode ve topics olup bloom_levels olmayan isteklere
    her konu için "Hatırlama" eklenir. Bloom davranışı tests/test_bloom.py'de denetlenir.
    """

    def post(self, url, *args, json=None, **kwargs):
        if (
            url == "/api/questions"
            and isinstance(json, dict)
            and json.get("context_mode")
            and isinstance(json.get("topics"), list)
            and "bloom_levels" not in json
        ):
            json = {**json, "bloom_levels": ["Hatırlama"] * len(json["topics"])}
        return super().post(url, *args, json=json, **kwargs)


client = BloomDefaultClient(app)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()
    transcript = Transcript(VID, "tr", True, [
        Segment("kemosentez yapan canlılar kimyasal enerji kullanır", 0.0, 10.0),
        Segment("bu canlıların tamamı prokaryot hücre yapısına sahiptir", 10.0, 10.0),
    ])
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: transcript)
    embedder = KeywordEmbedder()

    def use(llm, embedder_provider=None):
        app.dependency_overrides[get_llm] = lambda: llm
        app.dependency_overrides[get_embedder_provider] = lambda: (embedder_provider or (lambda: embedder))
        return embedder

    use.runs_dir = runs_dir
    yield use
    app.dependency_overrides.clear()


def last_record(runs_dir):
    return runs.load_run(sorted(runs_dir.glob("*.json"))[-1])


def test_api_similar_pair_flagged_questions_not_dropped(setup):
    setup(TopicLLM())
    topics = list(QUESTIONS)
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": topics})
    assert r.status_code == 200
    body = r.json()
    assert body["returned_count"] == 3  # işaretlenen çift atılmadı
    assert "similarity" not in r.text  # API yanıtı değişmedi

    record = last_record(setup.runs_dir)
    assert record["record_version"] == 10
    sc = record["similarity_check"]
    assert sc["rules_version"] == "similarity-v1"
    assert sc["threshold"] == SIMILARITY_THRESHOLD == 0.80 and "threshold_provisional" not in sc
    assert [(p["a"], p["b"]) for p in sc["flagged_pairs"]] == [(1, 2)]
    assert sc["flagged_pairs"][0]["question_a"] == QUESTIONS["Enerji kaynağı"][0]
    assert "similarity_check_ms" in record["metrics"]["stages"]


def test_api_single_question_no_pairs(setup):
    embedder = setup(TopicLLM())
    client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": ["Hücre yapısı"]})
    assert last_record(setup.runs_dir)["similarity_check"]["flagged_pairs"] == []
    assert embedder.calls == []


def test_api_v1_path_unaffected(setup):
    def fail():
        raise AssertionError("v1 yolunda gömme kullanılmamalı")

    setup(V1LLM(), embedder_provider=fail)
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200 and r.json()["returned_count"] == 3
    record = last_record(setup.runs_dir)
    assert record["similarity_check"] is None
    assert "similarity_check" not in json.loads(sorted(setup.runs_dir.glob("*.json"))[-1].read_text(encoding="utf-8"))
    assert "similarity_check_ms" not in record["metrics"]["stages"]


def test_api_embedding_unavailable_does_not_break_request(setup):
    class Broken:
        model = "broken"

        def embed(self, texts):
            raise EmbeddingUnavailable("Gömme modeli yüklenemedi")

    setup(TopicLLM(), embedder_provider=lambda: Broken())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": list(QUESTIONS)})
    assert r.status_code == 200 and r.json()["returned_count"] == 3
    sc = last_record(setup.runs_dir)["similarity_check"]
    assert sc["rules_version"] == "similarity-v1" and "yüklenemedi" in sc["error"]


def test_load_run_without_similarity_check(tmp_path):
    path = tmp_path / "eski.json"
    path.write_text(json.dumps({"record_version": 7, "endpoint": "/api/questions", "request": {}, "response": {}}), encoding="utf-8")
    assert runs.load_run(path)["similarity_check"] is None
