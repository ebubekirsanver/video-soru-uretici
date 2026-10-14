import json

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.llm import get_llm
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"
OLD_QUESTION_KEYS = {
    "question", "options", "correct_index", "explanation",
    "source_quote", "source_start_seconds", "verified", "quote_match",
}
OLD_TOP_KEYS = {
    "video_id", "transcript_mode", "model", "prompt_version",
    "requested_count", "returned_count", "verified_count", "questions",
}


class RoutingLLM:
    """LLMClient taklidi: sistem istemine göre soru üretimi ya da destek kontrolü yanıtı verir."""

    model = "fake-model"

    def __init__(self, questions_json, verdicts):
        self.questions_json, self.verdicts = questions_json, list(verdicts)
        self.question_calls, self.support_calls = [], []

    def complete(self, system, user, json_mode=False):
        if "değerlendiricisin" in system:  # support_v1_system.txt
            self.support_calls.append(user)
            return self.verdicts.pop(0)
        self.question_calls.append(user)
        return self.questions_json


def make_transcript():
    return Transcript(
        VID,
        "tr",
        True,
        [
            Segment("kabarcık sıralaması komşu elemanları karşılaştırır", 4.0, 10.0),
            Segment("en kötü durumda karmaşıklığı n kare olur", 40.0, 10.0),
        ],
    )


def questions_json():
    base = {"options": ["Komşu elemanları", "b", "c", "d"], "correct_index": 0, "explanation": "açıklama"}
    return json.dumps(
        {
            "questions": [
                {**base, "question": "Soru 1?", "source_quote": "kabarcık sıralaması komşu elemanları karşılaştırır"},
                {**base, "question": "Soru 2?", "source_quote": "videoda hiç söylenmeyen beş kelimelik alıntı"},
                {**base, "question": "Soru 3?", "source_quote": "en kötü durumda karmaşıklığı n kare olur"},
            ]
        },
        ensure_ascii=False,
    )


def verdict(label, reason="Gerekçe."):
    return json.dumps({"label": label, "reason": reason}, ensure_ascii=False)


client = TestClient(app)


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: make_transcript())

    def _use(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        return llm

    yield _use
    app.dependency_overrides.clear()


# --- Kapalıyken eski davranış ------------------------------------------------


@pytest.mark.parametrize("body", [{"url": VID}, {"url": VID, "check_support": False}])
def test_off_by_default_keeps_old_response(setup, body):
    llm = setup(RoutingLLM(questions_json(), verdicts=[]))
    r = client.post("/api/questions", json=body)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == OLD_TOP_KEYS  # support_prompt_version yok
    for q in data["questions"]:
        assert set(q) == OLD_QUESTION_KEYS  # support yok, null olarak da yok
    assert len(llm.question_calls) == 1 and llm.support_calls == []  # ek çağrı yapılmadı


def test_invalid_check_support_value(setup):
    setup(RoutingLLM(questions_json(), verdicts=[]))
    r = client.post("/api/questions", json={"url": VID, "check_support": "belki"})
    assert r.status_code == 422


# --- Açıkken ------------------------------------------------------------------


def test_on_adds_support_to_each_question(setup):
    llm = setup(RoutingLLM(questions_json(), verdicts=[verdict("destekliyor", "Alıntı cevabı söylüyor."), verdict("kısmen")]))
    r = client.post("/api/questions", json={"url": VID, "check_support": True})
    assert r.status_code == 200
    data = r.json()
    assert data["support_prompt_version"] == "support-v1"

    by_text = {q["question"]: q for q in data["questions"]}
    assert by_text["Soru 1?"]["support"] == {"label": "destekliyor", "reason": "Alıntı cevabı söylüyor."}
    assert by_text["Soru 3?"]["support"]["label"] == "kısmen"
    # Doğrulanamayan soruda çağrı yapılmaz
    assert by_text["Soru 2?"]["verified"] is False
    assert by_text["Soru 2?"]["support"]["label"] == "kontrol edilmedi"
    # Çağrı sayısı: 1 soru üretimi + doğrulanmış soru sayısı (2)
    assert len(llm.question_calls) == 1 and len(llm.support_calls) == 2
    # Modele doğru cevabın metni gider
    assert all("<dogru_cevap>\nKomşu elemanları\n</dogru_cevap>" in u for u in llm.support_calls)


def test_on_invalid_model_output_does_not_break_request(setup):
    setup(RoutingLLM(questions_json(), verdicts=["bozuk", verdict("desteklemiyor")]))
    r = client.post("/api/questions", json={"url": VID, "check_support": True})
    assert r.status_code == 200
    labels = [q["support"]["label"] for q in r.json()["questions"]]
    assert sorted(labels) == sorted(["kontrol edilemedi", "kontrol edilmedi", "desteklemiyor"])


# --- Çalıştırma kaydı -----------------------------------------------------------


@pytest.fixture
def runs_dir(monkeypatch, tmp_path):
    d = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(d))
    get_settings.cache_clear()
    return d


def test_on_record_has_support_check(setup, runs_dir):
    setup(RoutingLLM(questions_json(), verdicts=[verdict("destekliyor"), "bozuk"]))
    r = client.post("/api/questions", json={"url": VID, "check_support": True})
    (path,) = runs_dir.glob("*.json")
    record = runs.load_run(path)
    assert record["record_version"] == 3
    assert record["request"]["check_support"] is True
    assert record["response"] == r.json()
    sc = record["support_check"]
    assert sc["prompt_version"] == "support-v1"
    assert [x["label"] for x in sc["results"]] == ["destekliyor", "kontrol edilmedi", "kontrol edilemedi"]
    assert sc["results"][0]["model_raw"] == verdict("destekliyor")
    assert sc["results"][1]["model_raw"] is None  # çağrı yapılmadı
    assert sc["results"][2]["model_raw"] == "bozuk"  # geçersiz yanıt denetim için saklanır


def test_off_record_has_no_support_check(setup, runs_dir):
    setup(RoutingLLM(questions_json(), verdicts=[]))
    r = client.post("/api/questions", json={"url": VID})
    (path,) = runs_dir.glob("*.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert "support_check" not in raw
    assert raw["response"] == r.json()
    assert all("support" not in q for q in raw["response"]["questions"])
