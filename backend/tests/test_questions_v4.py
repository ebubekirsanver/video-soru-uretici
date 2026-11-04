"""questions-v4 ve prompt_version seçimi. Sahte LLM, sahte gömme; gerçek model çağrısı yok."""

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.embeddings import get_embedder_provider
from app.services.llm import LLMTruncated, get_llm
from app.services.prompts import load_prompt
from app.services.retrieval import TranscriptIndex, get_index_provider
from app.services.topic_questions import PROMPT_FILES, build_topic_user_prompt
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"
SENTENCE = "mitoz bölünmede kromozom sayısı yavru hücrelerde korunur ve canlı büyür"
REASON = "Konu bağlamda hiç geçmiyor."
BODY = {"url": VID, "context_mode": "full", "topics": ["mitoz"], "bloom_levels": ["Yaratma"]}

client = TestClient(app)


class FakeEmbedder:
    model = "fake-embedder"

    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


def question():
    return {
        "reasoning": "gerekçe",
        "question": "Mitoz hakkında hangisi doğrudur?",
        "options": ["Doğru seçenek", "Yanlış bir", "Yanlış iki", "Yanlış üç"],
        "correct_index": 0,
        "explanation": "açıklama",
        "source_quote": SENTENCE,
    }


class FakeLLM:
    model = "fake-model"

    def __init__(self, response):
        self.response = response
        self.calls = []

    def complete(self, system, user, json_mode=False, max_tokens=None):
        self.calls.append((system, user))
        return json.dumps(self.response, ensure_ascii=False)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()
    transcript = Transcript(VID, "tr", True, [Segment(SENTENCE, 0.0, 10.0)])
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: transcript)
    index = TranscriptIndex(FakeEmbedder(), path=tmp_path / "chroma")

    def use(response):
        llm = FakeLLM(response)
        app.dependency_overrides[get_llm] = lambda: llm
        app.dependency_overrides[get_index_provider] = lambda: (lambda: index)
        app.dependency_overrides[get_embedder_provider] = lambda: (lambda: index.embedder)
        return llm

    use.runs_dir = runs_dir
    yield use
    app.dependency_overrides.clear()


def last_record(runs_dir):
    return runs.load_run(sorted(runs_dir.glob("*.json"))[-1])


# --- İstem dosyaları ----------------------------------------------------------------


def test_v4_files_load_and_differ_from_v3_only_in_system():
    v3_system, v3_user = (load_prompt(f) for f in PROMPT_FILES["questions-v3"])
    v4_system, v4_user = (load_prompt(f) for f in PROMPT_FILES["questions-v4"])
    assert v4_user == v3_user
    assert v4_system != v3_system


@pytest.mark.parametrize(
    "text",
    [
        "Hedef düzeyin zor olması boş liste döndürme nedeni değildir.",
        "Örnek sorunun kalıbını da kopyalama",
        "Yaratma düzeyinde soru, bağlamdaki öğeleri bir amaç için bir araya getiren",
        "16. Doğru cevap ya da doğru cevabı ele veren anahtar kelime soru kökünde geçmesin.",
        "17. Soru kendi başına cevaplanabilir olsun",
        '{"questions": [], "skip_reason": "Konunun bağlamda neden geçmediği (bir cümle)"}',
    ],
)
def test_v4_system_contains_new_rules(text):
    assert text in load_prompt("questions_v4_system.txt")


def test_v4_system_has_no_leftover_old_empty_list_wording():
    # "açıkça geçmiyorsa" kalırsa Yaratma konularındaki boş liste sorunu istemde sürer
    assert "açıkça geçmiyorsa" not in load_prompt("questions_v4_system.txt")


def test_v4_user_prompt_placeholders_filled():
    user = build_topic_user_prompt("mitoz", "[0] bağlam metni", "Yaratma", "questions-v4")
    assert "Konu: mitoz" in user and "Hedef Bloom düzeyi: Yaratma" in user and "[0] bağlam metni" in user
    assert not re.search(r"\{(topic|context|bloom_level|bloom_definition|bloom_example)\}", user)


# --- prompt_version seçimi ----------------------------------------------------------


def test_default_version_is_v3(setup):
    llm = setup({"questions": [question()]})
    body = client.post("/api/questions", json=BODY).json()
    assert body["prompt_version"] == "questions-v3"
    assert llm.calls[0][0] == load_prompt("questions_v3_system.txt")
    record = last_record(setup.runs_dir)
    assert record["request"]["prompt_version"] == "questions-v3"
    assert record["topic_generation"]["prompt_version"] == "questions-v3"


@pytest.mark.parametrize("mode", ["full", "rag"])
def test_v4_used_and_recorded(setup, mode):
    llm = setup({"questions": [question()]})
    r = client.post("/api/questions", json={**BODY, "context_mode": mode, "prompt_version": "questions-v4"})
    assert r.status_code == 200 and r.json()["prompt_version"] == "questions-v4"
    assert llm.calls[0][0] == load_prompt("questions_v4_system.txt")
    record = last_record(setup.runs_dir)
    assert record["record_version"] == 10
    assert record["request"]["prompt_version"] == "questions-v4"
    assert record["response"]["prompt_version"] == "questions-v4"
    assert record["topic_generation"]["prompt_version"] == "questions-v4"


def test_prompt_version_without_context_mode_422(setup):
    setup({"questions": [question()]})
    r = client.post("/api/questions", json={"url": VID, "prompt_version": "questions-v3"})
    assert r.status_code == 422


@pytest.mark.parametrize("value", ["questions-v2", "questions-v5", None])
def test_invalid_prompt_version_422(setup, value):
    setup({"questions": [question()]})
    assert client.post("/api/questions", json={**BODY, "prompt_version": value}).status_code == 422


def test_old_request_record_has_no_prompt_version_field(setup):
    setup({"questions": [question()]})
    assert client.post("/api/questions", json={"url": VID, "count": 1}).status_code == 200
    record = last_record(setup.runs_dir)
    assert "prompt_version" not in record["request"]
    assert record["response"]["prompt_version"] == "questions-v1"


# --- skip_reason --------------------------------------------------------------------


def per_topic(setup, response, version):
    setup(response)
    r = client.post("/api/questions", json={**BODY, "prompt_version": version})
    assert r.status_code == 200
    assert "skip_reason" not in json.dumps(r.json())  # API yanıtında görünmez
    (trace,) = last_record(setup.runs_dir)["topic_generation"]["per_topic"]
    return trace


def test_v4_empty_list_reason_recorded(setup):
    trace = per_topic(setup, {"questions": [], "skip_reason": f"  {REASON} "}, "questions-v4")
    assert trace["outcome"] == "empty" and trace["skip_reason"] == REASON


def test_v4_reason_with_question_ignored(setup):
    trace = per_topic(setup, {"questions": [question()], "skip_reason": REASON}, "questions-v4")
    assert trace["outcome"] == "ok" and trace["skip_reason"] is None


def test_v4_reason_with_invalid_question_ignored(setup):
    bad = {**question(), "options": ["iki", "seçenek"]}
    trace = per_topic(setup, {"questions": [bad], "skip_reason": REASON}, "questions-v4")
    assert trace["outcome"] == "invalid" and trace["skip_reason"] is None


@pytest.mark.parametrize("response", [{"questions": []}, {"questions": [], "skip_reason": 3}, {"questions": [], "skip_reason": "  "}])
def test_v4_missing_or_bad_reason_is_null(setup, response):
    trace = per_topic(setup, response, "questions-v4")
    assert trace["outcome"] == "empty" and trace["skip_reason"] is None


def test_v3_reason_stays_null(setup):
    trace = per_topic(setup, {"questions": [], "skip_reason": REASON}, "questions-v3")
    assert trace["outcome"] == "empty" and trace["skip_reason"] is None


def test_v3_prompt_files_unchanged_in_use(setup):
    llm = setup({"questions": []})
    client.post("/api/questions", json=BODY)
    system, user = llm.calls[0]
    assert "skip_reason" not in system and "skip_reason" not in user
    assert '{"questions": []}' in system


# --- Çıktı token sınırı -------------------------------------------------------------


class TruncatingLLM(FakeLLM):
    """Adında "kesilen" geçen konuda yanıt sınıra takılır; çağrıların sınırını kaydeder."""

    def __init__(self, response):
        super().__init__(response)
        self.limits = []

    def complete(self, system, user, json_mode=False, max_tokens=None):
        self.limits.append(max_tokens)
        if "Konu: kesilen" in user:
            raise LLMTruncated("kesildi")
        return super().complete(system, user, json_mode, max_tokens)


def use_llm(llm):
    app.dependency_overrides[get_llm] = lambda: llm
    return llm


@pytest.mark.parametrize("version", ["questions-v3", "questions-v4"])
def test_truncated_topic_is_invalid_and_others_continue(setup, version):
    setup({})
    llm = use_llm(TruncatingLLM({"questions": [question()]}))
    r = client.post("/api/questions", json={
        **BODY, "topics": ["kesilen konu", "mitoz"], "bloom_levels": ["Anlama", "Yaratma"], "prompt_version": version,
    })
    assert r.status_code == 200 and r.json()["returned_count"] == 1
    assert "truncated" not in json.dumps(r.json())  # yalnızca kayıtta
    record = last_record(setup.runs_dir)
    tg = record["topic_generation"]
    first, second = tg["per_topic"]
    assert first["outcome"] == "invalid" and first["truncated"] is True and first["produced"] is False
    assert second["outcome"] == "ok" and second["truncated"] is False
    assert tg["outcome_counts"]["invalid"] == 1 and tg["max_tokens"] == 1000
    assert llm.limits == [1000, 1000]
    assert record["record_version"] == 10


def test_limit_comes_from_settings(setup, monkeypatch):
    monkeypatch.setenv("QUESTION_MAX_TOKENS", "321")
    get_settings.cache_clear()
    setup({})
    llm = use_llm(TruncatingLLM({"questions": [question()]}))
    assert client.post("/api/questions", json=BODY).status_code == 200
    assert llm.limits == [321]
    assert last_record(setup.runs_dir)["topic_generation"]["max_tokens"] == 321


def test_limit_not_applied_to_other_calls(setup):
    setup({})
    llm = use_llm(TruncatingLLM({"questions": [question()], "topics": [
        {"title": f"Konu {i}", "description": "açıklama"} for i in range(6)
    ], "label": "destekliyor", "reason": "gerekçe"}))
    # Konu çıkarma: sınır yok; sonraki 6 çağrı konu tabanlı soru üretimi: sınır var
    assert client.post("/api/questions", json={"url": VID, "context_mode": "full", "count": 6}).status_code == 200
    assert llm.limits == [None] + [1000] * 6
    # questions-v1 ve destek kontrolü: sınır yok
    llm.limits.clear()
    assert client.post("/api/questions", json={"url": VID, "count": 1, "check_support": True}).status_code == 200
    assert llm.limits == [None, None]
