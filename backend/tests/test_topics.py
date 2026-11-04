"""Konu çıkarma (istem topics-v1) ve POST /api/topics. Sahte LLM; gerçek model çağrısı yok."""

import json

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.llm import LLMError, OpenAIClient, get_llm
from app.services.topics import PROMPT_VERSION, Topic, extract_topics, parse_topics
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"


def topic(title, description=None):
    return {"title": title, "description": description if description is not None else f"{title} anlatılıyor."}


def six_topics():
    return [topic(f"Konu {i}") for i in range(1, 7)]


def make_transcript():
    return Transcript(VID, "tr", True, [Segment("kemosentez anlatılıyor", 0.0, 10.0), Segment("fotosentez", 40.0, 10.0)])


class FakeLLM:
    model = "fake-model"

    def __init__(self, response):
        self.response = response
        self.calls = []

    def complete(self, system, user, json_mode=False, max_tokens=None):
        self.calls.append((system, user, json_mode))
        return self.response if isinstance(self.response, str) else json.dumps(self.response, ensure_ascii=False)


# --- Servis -----------------------------------------------------------------------


def test_valid_six_topics():
    result = parse_topics(json.dumps({"topics": six_topics()}), 6)
    assert [t.title for t in result.topics] == [f"Konu {i}" for i in range(1, 7)]
    assert result.shortfall == 0
    assert result.dropped == {"empty": 0, "duplicate": 0, "extra": 0}


def test_duplicate_title_removed_first_kept():
    topics = [topic("Hidrotermal Bacalar", "ilk"), topic("hidrotermal bacalar!", "ikinci"), topic("Mitoz", "m")]
    result = parse_topics(json.dumps({"topics": topics}), 6)
    assert [(t.title, t.description) for t in result.topics] == [("Hidrotermal Bacalar", "ilk"), ("Mitoz", "m")]
    assert result.dropped["duplicate"] == 1


@pytest.mark.parametrize("bad", [topic("", "açıklama"), topic("Başlık", "  "), {"title": "Başlık"}, "metin", {"title": 3, "description": "x"}])
def test_empty_or_malformed_topic_dropped(bad):
    result = parse_topics(json.dumps({"topics": [bad, topic("Geçerli")]}), 6)
    assert [t.title for t in result.topics] == ["Geçerli"]
    assert result.dropped["empty"] == 1


def test_extra_topics_first_six_taken():
    topics = [topic(f"Konu {i}") for i in range(1, 10)]
    result = parse_topics(json.dumps({"topics": topics}), 6)
    assert [t.title for t in result.topics] == [f"Konu {i}" for i in range(1, 7)]
    assert result.dropped["extra"] == 3


def test_fewer_topics_no_error_shortfall_recorded():
    result = parse_topics(json.dumps({"topics": six_topics()[:4]}), 6)
    assert len(result.topics) == 4
    assert result.shortfall == 2
    record = result.as_record()
    assert record["requested_count"] == 6 and record["returned_count"] == 4 and record["shortfall"] == 2


@pytest.mark.parametrize("raw", ["bu JSON değil", json.dumps({"konular": []}), json.dumps(["liste"])])
def test_invalid_json_raises(raw):
    with pytest.raises(LLMError):
        parse_topics(raw, 6)


def test_topic_text_is_title_colon_description():
    assert Topic("Hidrotermal bacalar", "Okyanus tabanındaki sıcak su kaynakları.").text == (
        "Hidrotermal bacalar: Okyanus tabanındaki sıcak su kaynakları."
    )


def test_extract_topics_prompt_contains_count_and_transcript_blocks():
    llm = FakeLLM({"topics": six_topics()})
    result = extract_topics(make_transcript(), llm, count=6)
    assert len(result.topics) == 6
    (system, user, json_mode), = llm.calls
    assert json_mode is True
    assert "konu çıkaran" in system
    assert "tam 6 konu" in user
    assert "[0] kemosentez anlatılıyor" in user and "[40] fotosentez" in user


# --- API --------------------------------------------------------------------------


client = TestClient(app)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: make_transcript())

    def use(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        return llm

    use.runs_dir = runs_dir
    yield use
    app.dependency_overrides.clear()


def only_record(runs_dir):
    (path,) = sorted(runs_dir.glob("*.json"))
    return path, runs.load_run(path)


def test_api_topics_success_and_record(setup):
    setup(FakeLLM({"topics": six_topics() + [topic("Konu 7")]}))
    r = client.post("/api/topics", json={"url": VID})
    assert r.status_code == 200
    body = r.json()
    assert body["prompt_version"] == PROMPT_VERSION == "topics-v1"
    assert body["video_id"] == VID and body["model"] == "fake-model"
    assert len(body["topics"]) == 6  # varsayılan count 6
    assert body["topics"][0] == {"title": "Konu 1", "description": "Konu 1 anlatılıyor.", "text": "Konu 1: Konu 1 anlatılıyor."}

    path, record = only_record(setup.runs_dir)
    assert path.name.endswith("-topics.json")
    assert record["record_version"] == 10 and record["endpoint"] == "/api/topics"
    assert record["response"] == body
    te = record["topic_extraction"]
    assert te["requested_count"] == 6 and te["returned_count"] == 6 and te["dropped"]["extra"] == 1
    assert [c["purpose"] for c in record["metrics"]["llm_calls"]] == ["topics"]


def test_api_topics_shortfall_in_record(setup):
    setup(FakeLLM({"topics": six_topics()[:3]}))
    r = client.post("/api/topics", json={"url": VID, "count": 6})
    assert r.status_code == 200 and len(r.json()["topics"]) == 3
    _, record = only_record(setup.runs_dir)
    assert record["topic_extraction"]["shortfall"] == 3


def test_api_topics_invalid_json_502(setup):
    setup(FakeLLM("bu JSON değil"))
    assert client.post("/api/topics", json={"url": VID}).status_code == 502
    _, record = only_record(setup.runs_dir)
    assert record["outcome"] == "error"
    assert record["error"]["kind"] == "invalid_json" and record["error"]["stage"] == "topics_parse"


def test_api_topics_no_api_key_503(setup):
    setup(OpenAIClient(api_key="", model="m"))
    assert client.post("/api/topics", json={"url": VID}).status_code == 503
    _, record = only_record(setup.runs_dir)
    assert record["error"]["kind"] == "llm_not_configured"


@pytest.mark.parametrize("count", [0, 11, "altı"])
def test_api_topics_invalid_count_422(setup, count):
    setup(FakeLLM({"topics": six_topics()}))
    assert client.post("/api/topics", json={"url": VID, "count": count}).status_code == 422


def test_api_topics_transcript_unavailable_404(setup, monkeypatch):
    from app.services.transcript import TranscriptUnavailable

    def missing(video_id, languages):
        raise TranscriptUnavailable("Bu videoda altyazılar kapalı.")

    monkeypatch.setattr("app.routers.fetch_transcript", missing)
    setup(FakeLLM({"topics": six_topics()}))
    assert client.post("/api/topics", json={"url": VID}).status_code == 404


def test_load_run_v6_record_has_no_topic_extraction(tmp_path):
    path = tmp_path / "eski.json"
    path.write_text(json.dumps({"record_version": 6, "endpoint": "/api/questions", "request": {}, "response": {}}), encoding="utf-8")
    assert runs.load_run(path)["topic_extraction"] is None
