"""Aşama 7b: konu tabanlı soru üretimi, AS1'in iki koşulu (full / rag), istem questions-v2.

Sahte LLM, sahte gömme ve her testte geçici bir Chroma klasörü kullanılır;
gerçek model çağrısı ya da indirme yoktur.
"""

import hashlib
import json
import math
import re

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.embeddings import EmbeddingUnavailable
from app.services.llm import get_llm
from app.services.retrieval import TranscriptIndex, get_index_provider
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"
DIM = 64

# Her konu tek bir uzun segment (>150 kelime): her segment kendi parçası olur, örtüşme yok
TOPIC_SEGMENTS = [
    ("fotosentez klorofil", "fotosentezde bitkiler klorofil sayesinde ışık enerjisini kullanır", 0.0),
    ("hidrotermal bacalar", "hidrotermal bacalar okyanus tabanında yer alan sıcak su kaynaklarıdır", 100.0),
    ("prokaryot hücre", "kemosentetik canlıların tamamı prokaryot hücre yapısına sahiptir", 200.0),
    ("mitoz bölünme", "mitoz bölünmede kromozom sayısı yavru hücrelerde korunur", 300.0),
]


def make_transcript():
    segments = []
    for title, sentence, start in TOPIC_SEGMENTS:
        filler = " ".join([title] * 75)  # konunun kelimeleri parçada baskın olsun
        segments.append(Segment(f"{sentence} {filler}", start, 90.0))
    return Transcript(VID, "tr", True, segments)


class FakeEmbedder:
    """Deterministik sahte gömme: kelimeler md5 ile 64 kutuya sayılır, vektör normalize edilir."""

    model = "fake-embedder"

    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(list(texts))
        vectors = []
        for text in texts:
            v = [0.0] * DIM
            for word in text.lower().split():
                v[int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % DIM] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            vectors.append([x / norm for x in v])
        return vectors


class BrokenEmbedder(FakeEmbedder):
    def embed(self, texts):
        raise EmbeddingUnavailable("Gömme modeli (fake) yüklenemedi: indirme başarısız")


def question_for(topic):
    """Konunun cümlesinden alıntı yapan geçerli bir soru (konu metni soruda geçer, tekrar sayılmaz)."""
    sentence = next(s for t, s, _ in TOPIC_SEGMENTS if t == topic)
    return {
        "question": f"{topic} hakkında hangisi doğrudur?",
        "options": ["Doğru seçenek", "Yanlış bir", "Yanlış iki", "Yanlış üç"],
        "correct_index": 0,
        "explanation": "açıklama",
        "source_quote": sentence,
    }


class TopicLLM:
    """Sahte LLM: özet isteminde özet, soru isteminde konuya göre soru döndürür; çağrıları kaydeder."""

    model = "fake-model"

    def __init__(self, empty_topics=(), quotes=None, summary_topics=None):
        self.empty_topics = set(empty_topics)
        self.quotes = quotes or {}
        self.summary_topics = summary_topics or [t for t, _, _ in TOPIC_SEGMENTS]
        self.question_calls, self.summary_calls = [], []

    def complete(self, system, user, json_mode=False):
        if "özetleyen" in system:  # summary_system.txt
            self.summary_calls.append(user)
            topics = [{"title": t, "start_seconds": 0} for t in self.summary_topics]
            return json.dumps({"summary": "Özet.", "topics": topics}, ensure_ascii=False)
        self.question_calls.append((system, user))
        topic = re.search(r"^Konu: (.+)$", user, re.MULTILINE).group(1)
        if topic in self.empty_topics:
            return json.dumps({"questions": []})
        q = question_for(topic)
        if topic in self.quotes:
            q["source_quote"] = self.quotes[topic]
        return json.dumps({"questions": [q]}, ensure_ascii=False)


client = TestClient(app)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    """Kayıt geçici klasörde; transkript sahte; dizin geçici Chroma klasöründe."""
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: make_transcript())
    state = {"index": TranscriptIndex(FakeEmbedder(), path=tmp_path / "chroma")}

    def use(llm, index=None):
        if index is not None:
            state["index"] = index
        app.dependency_overrides[get_llm] = lambda: llm
        app.dependency_overrides[get_index_provider] = lambda: (lambda: state["index"])
        return llm

    use.state = state
    use.runs_dir = runs_dir
    yield use
    app.dependency_overrides.clear()


def last_record(runs_dir):
    paths = sorted(runs_dir.glob("*.json"))
    return runs.load_run(paths[-1])


def labels(user_prompt):
    """Kullanıcı istemindeki bağlam satırlarının [saniye] etiketleri, sırasıyla."""
    # İstemin açıklama cümlesinde de <bağlam> geçer; bağlam son açılış etiketinden sonradır
    context = user_prompt.split("<bağlam>\n")[-1].split("</bağlam>")[0]
    return [int(x) for x in re.findall(r"^\[(\d+)\]", context, re.MULTILINE)]


# --- Eski davranış korunur -------------------------------------------------------


def test_without_context_mode_old_behavior(setup):
    llm = setup(TopicLLM())

    class V1LLM:
        model = "fake-model"

        def complete(self, system, user, json_mode=False):
            return json.dumps({"questions": [question_for("mitoz bölünme")]}, ensure_ascii=False)

    setup(V1LLM())
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200
    body = r.json()
    assert body["prompt_version"] == "questions-v1" and "context_mode" not in body
    assert all("topic" not in q for q in body["questions"])
    record = last_record(setup.runs_dir)
    assert record["topic_generation"] is None
    assert record["request"] == {"url": VID, "count": 5, "transcript_mode": "clean", "check_support": False}
    assert "index_ms" not in record["metrics"]["stages"]
    assert llm.question_calls == []


# --- İki koşul: aynı istem, farklı bağlam ------------------------------------------


def test_same_system_prompt_and_topic_in_both_conditions(setup):
    full_llm = setup(TopicLLM())
    assert client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": ["hidrotermal bacalar"]}).status_code == 200
    rag_llm = setup(TopicLLM())
    assert client.post(
        "/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["hidrotermal bacalar"], "k": 2}
    ).status_code == 200

    (full_system, full_user), = full_llm.question_calls
    (rag_system, rag_user), = rag_llm.question_calls
    assert full_system == rag_system  # sistem istemi birebir aynı
    assert "Konu: hidrotermal bacalar" in full_user and "Konu: hidrotermal bacalar" in rag_user
    # İstem metni de bağlam dışında aynı
    strip = lambda u: u.split("<bağlam>")[0] + u.split("</bağlam>")[1]  # noqa: E731
    assert strip(full_user) == strip(rag_user)
    # full: tüm bloklar zaman sırasıyla; rag: yalnızca erişilen 2 parça, en ilgilisi (100 sn) başta
    assert labels(full_user) == [0, 100, 200, 300]
    assert len(labels(rag_user)) == 2 and labels(rag_user)[0] == 100


def test_rag_context_contains_only_retrieved_chunks(setup):
    llm = setup(TopicLLM())
    client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme"], "k": 1})
    (_, user), = llm.question_calls
    assert labels(user) == [300]
    assert "mitoz bölünmede kromozom" in user
    assert "hidrotermal bacalar okyanus" not in user


def test_rag_quote_is_searched_in_full_transcript(setup):
    # Model, erişilen parçada olmayan bir yerden alıntı yaparsa da alıntı TAM transkriptte bulunur
    other = "fotosentezde bitkiler klorofil sayesinde ışık enerjisini kullanır"
    setup(TopicLLM(quotes={"mitoz bölünme": other}))
    r = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme"], "k": 1})
    (q,) = r.json()["questions"]
    assert q["verified"] is True
    assert q["source_start_seconds"] == 0.0  # alıntının bulunduğu segmentin başlangıcı
    assert q["topic"] == "mitoz bölünme"


def test_rag_source_start_seconds_for_own_chunk(setup):
    setup(TopicLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["prokaryot hücre"]})
    (q,) = r.json()["questions"]
    assert q["verified"] is True and q["source_start_seconds"] == 200.0


# --- Konu başına çağrı, boş konu, konuların kaynağı --------------------------------


def test_one_call_per_topic_and_empty_topic_skipped(setup):
    topics = ["fotosentez klorofil", "hidrotermal bacalar", "mitoz bölünme"]
    llm = setup(TopicLLM(empty_topics={"hidrotermal bacalar"}))
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": topics})
    assert r.status_code == 200
    assert len(llm.question_calls) == 3  # konu başına tek çağrı
    body = r.json()
    assert body["returned_count"] == 2 and body["requested_count"] == 3
    assert [q["topic"] for q in body["questions"]] == ["fotosentez klorofil", "mitoz bölünme"]

    record = last_record(setup.runs_dir)
    tg = record["topic_generation"]
    assert tg["no_question_topics"] == ["hidrotermal bacalar"]
    assert [t["produced"] for t in tg["per_topic"]] == [True, False, True]
    assert [c["purpose"] for c in record["metrics"]["llm_calls"]] == ["questions"] * 3


def test_topics_from_summary_when_not_given(setup):
    llm = setup(TopicLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "count": 2})
    assert r.status_code == 200
    assert len(llm.summary_calls) == 1
    assert [q["topic"] for q in r.json()["questions"]] == ["fotosentez klorofil", "hidrotermal bacalar"]
    record = last_record(setup.runs_dir)
    assert record["topic_generation"]["topics_source"] == "summary"
    assert record["topic_generation"]["topics"] == ["fotosentez klorofil", "hidrotermal bacalar"]
    assert [c["purpose"] for c in record["metrics"]["llm_calls"]] == ["summary", "questions", "questions"]


def test_given_topics_do_not_call_summary(setup):
    llm = setup(TopicLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme"], "count": 9})
    assert r.status_code == 200
    assert llm.summary_calls == []
    assert r.json()["requested_count"] == 1  # topics verilince count yok sayılır
    assert last_record(setup.runs_dir)["topic_generation"]["topics_source"] == "request"


# --- k, dizin önbelleği ------------------------------------------------------------


def test_k_is_applied(setup):
    llm = setup(TopicLLM())
    client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme"], "k": 3})
    (_, user), = llm.question_calls
    assert len(labels(user)) == 3
    retrieved = last_record(setup.runs_dir)["topic_generation"]["per_topic"][0]["retrieved"]
    assert len(retrieved) == 3 and retrieved[0]["chunk_index"] == 3
    assert set(retrieved[0]) == {"chunk_index", "start_seconds", "end_seconds", "score"}


def test_second_rag_request_does_not_reembed(setup):
    setup(TopicLLM())
    body = {"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme"]}
    client.post("/api/questions", json=body)
    embedder = setup.state["index"].embedder
    chunk_embeds = [c for c in embedder.calls if len(c) > 1]
    client.post("/api/questions", json=body)
    assert [c for c in embedder.calls if len(c) > 1] == chunk_embeds  # parçalar bir kez gömüldü


# --- Hatalar -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "extra",
    [
        {"context_mode": "abc"},
        {"context_mode": "full", "topics": []},
        {"context_mode": "full", "topics": [f"konu {i}" for i in range(11)]},
        {"context_mode": "full", "topics": ["  "]},
        {"context_mode": "rag", "k": 0},
        {"context_mode": "rag", "k": 11},
        {"context_mode": "rag", "transcript_mode": "raw"},
        {"topics": ["mitoz bölünme"]},  # context_mode olmadan
        {"k": 3},  # context_mode olmadan
    ],
)
def test_invalid_fields_422(setup, extra):
    setup(TopicLLM())
    assert client.post("/api/questions", json={"url": VID, **extra}).status_code == 422


def test_full_with_raw_transcript_allowed(setup):
    setup(TopicLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "transcript_mode": "raw", "topics": ["mitoz bölünme"]})
    assert r.status_code == 200


def test_embedding_unavailable_503(setup, tmp_path):
    setup(TopicLLM(), index=TranscriptIndex(BrokenEmbedder(), path=tmp_path / "broken"))
    r = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme"]})
    assert r.status_code == 503
    assert "Gömme modeli" in r.json()["detail"]
    record = last_record(setup.runs_dir)
    assert record["outcome"] == "error"
    assert record["error"]["kind"] == "embedding_unavailable" and record["error"]["stage"] == "index"


def test_full_mode_does_not_open_index(setup):
    def fail():
        raise AssertionError("full koşulunda dizin açılmamalı")

    setup(TopicLLM())
    app.dependency_overrides[get_index_provider] = lambda: fail
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": ["mitoz bölünme"]})
    assert r.status_code == 200


# --- Kayıt --------------------------------------------------------------------------


def test_record_v6_rag_fields(setup):
    setup(TopicLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": ["mitoz bölünme", "hidrotermal bacalar"], "k": 2})
    body = r.json()
    assert body["context_mode"] == "rag" and body["prompt_version"] == "questions-v2"

    record = last_record(setup.runs_dir)
    assert record["record_version"] == 6
    assert record["response"] == body
    assert record["request"]["context_mode"] == "rag" and record["request"]["k"] == 2
    tg = record["topic_generation"]
    assert tg["prompt_version"] == "questions-v2" and tg["context_mode"] == "rag" and tg["k"] == 2
    assert tg["chunking"] == "fixed-150-30" and tg["embedding_model"] == "fake-embedder"
    assert tg["topics"] == ["mitoz bölünme", "hidrotermal bacalar"]
    for t in tg["per_topic"]:
        assert len(t["retrieved"]) == 2 and t["context_words"] > 0
    stages = record["metrics"]["stages"]
    assert {"index_ms", "retrieval_ms", "llm_questions_ms", "quote_verify_ms"} <= set(stages)


def test_record_full_fields(setup):
    setup(TopicLLM())
    client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": ["mitoz bölünme"]})
    tg = last_record(setup.runs_dir)["topic_generation"]
    assert tg["context_mode"] == "full"
    assert tg["k"] is None and tg["chunking"] is None and tg["embedding_model"] is None
    (t,) = tg["per_topic"]
    total_words = sum(len(s.text.split()) for s in make_transcript().segments)
    assert t["retrieved"] is None and t["context_words"] == total_words
    stages = last_record(setup.runs_dir)["metrics"]["stages"]
    assert "index_ms" not in stages and "retrieval_ms" not in stages


def test_load_run_v5_record_has_no_topic_generation(tmp_path):
    path = tmp_path / "eski.json"
    path.write_text(json.dumps({"record_version": 5, "endpoint": "/api/questions", "request": {}, "response": {}}), encoding="utf-8")
    assert runs.load_run(path)["topic_generation"] is None
