import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.schemas import SummaryRequest, SummaryResponse
from app.services import runs
from app.services.llm import get_llm
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"
FAKE_KEY = "sk-test-gizli-anahtar-12345"
FILE_NAME = re.compile(r"^\d{8}-\d{6}-" + VID + r"-(summary|questions)(-\d+)?\.json$")


class FakeLLM:
    """LLMClient taklidi; gerçek API çağrısı yapmaz."""

    model = "fake-model"

    def __init__(self, response):
        self.response = response

    def complete(self, system, user, json_mode=False):
        return self.response


SUMMARY_JSON = json.dumps(
    {"summary": "Kabarcık sıralaması anlatılıyor.", "topics": [{"title": "Giriş", "start_seconds": 0}]},
    ensure_ascii=False,
)
QUESTIONS_JSON = json.dumps(
    {
        "questions": [
            {
                "question": "Kabarcık sıralaması neyi karşılaştırır?",
                "options": ["Komşu elemanları", "İlk ve son elemanı", "Rastgele iki elemanı", "Hiçbirini"],
                "correct_index": 0,
                "explanation": "Komşu elemanlar karşılaştırılır.",
                "source_quote": "kabarcık sıralaması komşu elemanları karşılaştırır",
            }
        ]
    },
    ensure_ascii=False,
)

client = TestClient(app)


@pytest.fixture
def fake_transcript(monkeypatch):
    t = Transcript(VID, "tr", True, [Segment("kabarcık sıralaması komşu elemanları karşılaştırır", 4.0, 6.0)])
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: t)


@pytest.fixture
def use_llm():
    def _use(response):
        app.dependency_overrides[get_llm] = lambda: FakeLLM(response)

    yield _use
    app.dependency_overrides.clear()


@pytest.fixture
def runs_enabled(monkeypatch, tmp_path):
    """Kaydı açar ve geçici klasöre yönlendirir; ortamda sahte bir API anahtarı tanımlar."""
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    get_settings.cache_clear()
    return runs_dir


def saved_files(runs_dir):
    return sorted(runs_dir.glob("*.json")) if runs_dir.exists() else []


def test_summary_run_is_saved(runs_enabled, use_llm, fake_transcript):
    use_llm(SUMMARY_JSON)
    r = client.post("/api/summary", json={"url": f"https://youtu.be/{VID}", "transcript_mode": "raw"})
    assert r.status_code == 200

    (path,) = saved_files(runs_enabled)
    assert FILE_NAME.match(path.name) and path.name.endswith("-summary.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["endpoint"] == "/api/summary"
    assert record["request"] == {"url": f"https://youtu.be/{VID}", "transcript_mode": "raw"}
    assert record["response"] == r.json()  # yanıtın tamamı
    datetime.fromisoformat(record["saved_at"])  # geçerli zaman damgası


def test_questions_run_is_saved(runs_enabled, use_llm, fake_transcript):
    use_llm(QUESTIONS_JSON)
    r = client.post("/api/questions", json={"url": VID, "count": 3})
    assert r.status_code == 200

    (path,) = saved_files(runs_enabled)
    assert FILE_NAME.match(path.name) and path.name.endswith("-questions.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["request"] == {"url": VID, "count": 3, "transcript_mode": "clean", "check_support": False}
    assert record["response"] == r.json()
    # Türkçe karakterler kaçış dizisine çevrilmeden yazılır
    assert "Kabarcık sıralaması" in path.read_text(encoding="utf-8")


def mixed_questions_json():
    """Biri exact (etiketli), biri trimmed, biri doğrulanamayan üç soru."""
    base = {"options": ["a", "b", "c", "d"], "correct_index": 0, "explanation": "açıklama"}
    return json.dumps(
        {
            "questions": [
                {**base, "question": "Exact soru?",
                 "source_quote": "[4] Kabarcık sıralaması, komşu elemanları karşılaştırır."},
                {**base, "question": "Trimmed soru?",
                 "source_quote": "[4] Yani kabarcık sıralaması komşu elemanları karşılaştırır tamam"},
                {**base, "question": "Doğrulanamayan soru?",
                 "source_quote": "[90] Bu cümle videoda hiç geçmiyor aslında"},
            ]
        },
        ensure_ascii=False,
    )


def test_quote_audit_in_record(runs_enabled, use_llm, fake_transcript):
    use_llm(mixed_questions_json())
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200

    (path,) = saved_files(runs_enabled)
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["record_version"] == 5  # Aşama 9 (b): kayda writing_check eklendiği için sürüm 5
    assert record["response"] == r.json()  # yanıt kayıtta değiştirilmeden durur

    exact, trimmed, unverified = record["quote_audit"]
    assert exact == {
        "index": 1,
        "question": "Exact soru?",
        "model_quote": "[4] Kabarcık sıralaması, komşu elemanları karşılaştırır.",
        "source_quote": "kabarcık sıralaması komşu elemanları karşılaştırır",
        "quote_match": "exact",
        "trimmed_head": [],
        "trimmed_tail": [],
    }
    assert trimmed["model_quote"] == "[4] Yani kabarcık sıralaması komşu elemanları karşılaştırır tamam"
    assert trimmed["source_quote"] == "kabarcık sıralaması komşu elemanları karşılaştırır"
    assert trimmed["quote_match"] == "trimmed"
    assert trimmed["trimmed_head"] == ["yani"] and trimmed["trimmed_tail"] == ["tamam"]
    assert unverified["model_quote"] == "[90] Bu cümle videoda hiç geçmiyor aslında"
    assert unverified["source_quote"] == "Bu cümle videoda hiç geçmiyor aslında"
    assert unverified["quote_match"] is None


def test_response_has_no_model_quote(runs_enabled, use_llm, fake_transcript):
    use_llm(mixed_questions_json())
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200
    for q in r.json()["questions"]:
        assert not {"model_quote", "trimmed_head", "trimmed_tail"} & set(q)
    assert "model_quote" not in r.text and "quote_audit" not in r.text


def test_summary_record_has_no_quote_audit(runs_enabled, use_llm, fake_transcript):
    use_llm(SUMMARY_JSON)
    client.post("/api/summary", json={"url": VID})
    (path,) = saved_files(runs_enabled)
    record = json.loads(path.read_text(encoding="utf-8"))
    # Aşama 9 (b): kayda writing_check eklendiği için sürüm 5
    assert record["record_version"] == 5 and "quote_audit" not in record and "support_check" not in record


def test_load_run_reads_old_format_record():
    # Sürüm 1 biçiminde gerçek bir kayıt (record_version ve quote_audit yok)
    old = Path(__file__).resolve().parents[2] / "docs" / "bulgular" / "asama-6-test-2-tarih.json"
    record = runs.load_run(old)
    assert record["record_version"] == 1
    assert record["quote_audit"] == []
    assert record["support_check"] is None
    assert record["response"]["video_id"] == "aaCHLYO3Fzg"


def test_load_run_reads_new_format_record(runs_enabled, use_llm, fake_transcript):
    use_llm(mixed_questions_json())
    client.post("/api/questions", json={"url": VID})
    (path,) = saved_files(runs_enabled)
    record = runs.load_run(path)
    # Aşama 9 (b): kayda writing_check eklendiği için sürüm 5
    assert record["record_version"] == 5 and len(record["quote_audit"]) == 3 and record["support_check"] is None


def test_saved_run_contains_no_api_key(runs_enabled, use_llm, fake_transcript):
    use_llm(mixed_questions_json())  # quote_audit içeren kayıt da denetlensin
    client.post("/api/questions", json={"url": VID})
    use_llm(SUMMARY_JSON)
    client.post("/api/summary", json={"url": VID})

    files = saved_files(runs_enabled)
    assert len(files) == 2
    for path in files:
        content = path.read_text(encoding="utf-8")
        assert FAKE_KEY not in content
        assert "openai_api_key" not in content.lower()


def test_no_file_when_save_runs_false(monkeypatch, tmp_path, use_llm, fake_transcript):
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "false")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()

    use_llm(SUMMARY_JSON)
    assert client.post("/api/summary", json={"url": VID}).status_code == 200
    use_llm(QUESTIONS_JSON)
    assert client.post("/api/questions", json={"url": VID}).status_code == 200
    assert not runs_dir.exists()


def test_no_file_on_error_response(runs_enabled, use_llm, fake_transcript):
    # Aşama 14'ten beri hatalı istek de kaydedilir, ama yalnızca -error son ekli hata kaydı olarak
    use_llm("bu JSON değil")
    assert client.post("/api/questions", json={"url": VID}).status_code == 502
    (path,) = saved_files(runs_enabled)
    assert path.name.endswith("-questions-error.json")
    assert json.loads(path.read_text(encoding="utf-8"))["outcome"] == "error"


def test_write_error_does_not_break_response(monkeypatch, tmp_path, use_llm, fake_transcript, caplog):
    # Kayıt klasörü yolunda bir dosya var: klasör oluşturulamaz, yazma başarısız olur
    blocker = tmp_path / "dosya"
    blocker.write_text("engel", encoding="utf-8")
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(blocker))
    get_settings.cache_clear()

    use_llm(SUMMARY_JSON)
    with caplog.at_level(logging.ERROR, logger="app.services.runs"):
        r = client.post("/api/summary", json={"url": VID})
    assert r.status_code == 200
    assert r.json()["summary"] == "Kabarcık sıralaması anlatılıyor."
    assert any("kaydı yazılamadı" in rec.getMessage() for rec in caplog.records)


def test_same_second_does_not_overwrite(runs_enabled, monkeypatch):
    fixed = datetime(2026, 10, 12, 18, 30, 5, tzinfo=timezone(timedelta(hours=3)))
    monkeypatch.setattr(runs, "_now", lambda: fixed)
    request = SummaryRequest(url=VID)
    response = SummaryResponse(
        video_id=VID, language="tr", transcript_mode="clean", model="m", summary="özet", topics=[]
    )

    first = runs.save_run("summary", VID, request, response)
    second = runs.save_run("summary", VID, request, response)
    assert first.name == f"20261012-183005-{VID}-summary.json"
    assert second.name == f"20261012-183005-{VID}-summary-2.json"
    assert json.loads(first.read_text(encoding="utf-8"))["saved_at"] == "2026-10-12T18:30:05+03:00"
