import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm import LLMError, OpenAIClient, get_llm
from app.services.transcript import Segment, Transcript, TranscriptUnavailable

VID = "dQw4w9WgXcQ"


class FakeLLM:
    """LLMClient taklidi; gerçek API çağrısı yapmaz."""

    model = "fake-model"

    def __init__(self, response="", error=None):
        self.response, self.error, self.calls = response, error, []

    def complete(self, system, user, json_mode=False):
        self.calls.append({"system": system, "user": user, "json_mode": json_mode})
        if self.error:
            raise self.error
        return self.response


def make_transcript():
    return Transcript(
        VID,
        "tr",
        True,
        [
            Segment("[Müzik]", 0.0, 4.0),
            Segment("kabarcık sıralaması komşu elemanları karşılaştırır", 4.0, 10.0),
            Segment("en kötü durumda karmaşıklığı n kare olur", 40.0, 10.0),
        ],
    )


def llm_response():
    base = {
        "options": ["a", "b", "c", "d"],
        "correct_index": 0,
        "explanation": "açıklama",
    }
    questions = [
        {**base, "question": "Soru 1?", "source_quote": "kabarcık sıralaması komşu elemanları karşılaştırır"},
        {**base, "question": "Soru 2?", "source_quote": "videoda hiç söylenmeyen beş kelimelik alıntı"},
        {**base, "question": "Soru 3?", "options": ["a", "b", "c"], "source_quote": "x"},  # bozuk
        {**base, "question": "soru 1", "source_quote": "kabarcık sıralaması komşu elemanları karşılaştırır"},  # tekrar
        {**base, "question": "Soru 4?", "source_quote": "En kötü durumda, karmaşıklığı N kare olur."},
    ]
    return json.dumps({"questions": questions}, ensure_ascii=False)


client = TestClient(app)


@pytest.fixture
def use_llm():
    """Uç noktadaki LLM bağımlılığını verilen sahte nesneyle değiştirir."""

    def _use(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        return llm

    yield _use
    app.dependency_overrides.clear()


@pytest.fixture
def fake_transcript(monkeypatch):
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: make_transcript())


def test_endpoint_ok(use_llm, fake_transcript):
    use_llm(FakeLLM(response=llm_response()))
    r = client.post("/api/questions", json={"url": f"https://youtu.be/{VID}", "count": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["video_id"] == VID
    assert body["model"] == "fake-model" and body["prompt_version"] == "questions-v1"
    assert body["transcript_mode"] == "clean"
    # 5 aday: 1 bozuk ve 1 tekrar atıldı, 1 doğrulanamadı
    assert body["requested_count"] == 5
    assert body["returned_count"] == 3
    assert body["verified_count"] == 2

    by_text = {q["question"]: q for q in body["questions"]}
    assert set(by_text) == {"Soru 1?", "Soru 2?", "Soru 4?"}
    assert by_text["Soru 1?"]["verified"] is True and by_text["Soru 1?"]["source_start_seconds"] == 4.0
    assert by_text["Soru 1?"]["quote_match"] == "exact"
    assert by_text["Soru 2?"]["verified"] is False and by_text["Soru 2?"]["source_start_seconds"] is None
    assert by_text["Soru 2?"]["quote_match"] is None
    assert by_text["Soru 4?"]["verified"] is True and by_text["Soru 4?"]["source_start_seconds"] == 40.0
    for q in body["questions"]:
        assert len(q["options"]) == 4 and q["options"][q["correct_index"]] == "a"
        assert set(q) == {
            "question", "options", "correct_index", "explanation",
            "source_quote", "source_start_seconds", "verified", "quote_match",
        }


def test_endpoint_trimmed_quote(use_llm, fake_transcript):
    q = {
        "question": "Kabarcık sıralaması neyi karşılaştırır?",
        "options": ["a", "b", "c", "d"],
        "correct_index": 0,
        "explanation": "açıklama",
        "source_quote": "[4] Yani kabarcık sıralaması komşu elemanları karşılaştırır",
    }
    use_llm(FakeLLM(response=json.dumps({"questions": [q]}, ensure_ascii=False)))
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200
    (out,) = r.json()["questions"]
    assert out["verified"] is True and out["quote_match"] == "trimmed"
    assert out["source_quote"] == "kabarcık sıralaması komşu elemanları karşılaştırır"
    assert out["source_start_seconds"] == 4.0


def test_endpoint_default_count(use_llm, fake_transcript):
    llm = use_llm(FakeLLM(response=llm_response()))
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200
    assert r.json()["requested_count"] == 5
    assert "5 adet" in llm.calls[0]["user"]


@pytest.mark.parametrize("count", [0, 21, -1])
def test_endpoint_invalid_count(use_llm, count):
    use_llm(FakeLLM())
    r = client.post("/api/questions", json={"url": VID, "count": count})
    assert r.status_code == 422


def test_endpoint_invalid_url(use_llm):
    use_llm(FakeLLM())
    r = client.post("/api/questions", json={"url": "https://example.com"})
    assert r.status_code == 422


def test_endpoint_transcript_unavailable(use_llm, monkeypatch):
    def fake_fetch(video_id, languages):
        raise TranscriptUnavailable("Bu videoda altyazılar kapalı.")

    monkeypatch.setattr("app.routers.fetch_transcript", fake_fetch)
    llm = use_llm(FakeLLM())
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 404
    assert llm.calls == []


def test_endpoint_empty_after_cleaning(use_llm, monkeypatch):
    only_tags = Transcript(VID, "tr", True, [Segment("[Müzik]", 0.0, 5.0)])
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: only_tags)
    llm = use_llm(FakeLLM())
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 404
    assert llm.calls == []


def test_endpoint_bad_json(use_llm, fake_transcript):
    use_llm(FakeLLM(response="bu JSON değil"))
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 502


def test_endpoint_llm_error(use_llm, fake_transcript):
    use_llm(FakeLLM(error=LLMError("OpenAI çağrısı başarısız: zaman aşımı")))
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 502
    assert "zaman aşımı" in r.json()["detail"]


def test_endpoint_missing_api_key(use_llm, fake_transcript):
    use_llm(OpenAIClient(api_key="", model="gpt-4o-mini"))
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 503
    assert "OPENAI_API_KEY" in r.json()["detail"]


def test_endpoint_raw_mode(use_llm, fake_transcript):
    llm = use_llm(FakeLLM(response=llm_response()))
    r = client.post("/api/questions", json={"url": VID, "transcript_mode": "raw"})
    assert r.status_code == 200
    assert r.json()["transcript_mode"] == "raw"
    assert "[Müzik]" in llm.calls[0]["user"]
    # Ham modda da doğrulama temiz transkripte karşı yapılır
    assert r.json()["verified_count"] == 2
