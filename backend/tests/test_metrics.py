"""Aşama 14: aşama süreleri, model çağrıları (token), hata kaydı.

Model çağrıları gerçek `OpenAIClient` üzerinden yapılır ama içine ağa çıkmayan
sahte bir `chat.completions` verilir; hiçbir testte OpenAI'ye istek gitmez.
"""

import json
import threading
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from app.config import get_settings
from app.main import app
from app.services import metrics, runs
from app.services.llm import OpenAIClient, get_llm
from app.services.metrics import scrub_secrets
from app.services.transcript import Segment, Transcript, TranscriptUnavailable

VID = "dQw4w9WgXcQ"
FAKE_KEY = "sk-test-gizli-anahtar-12345"
ENV_KEY = "ortam-anahtari-987654"  # sk- ile başlamayan, ayarlardan gelen anahtar

SUMMARY_JSON = json.dumps(
    {"summary": "Kabarcık sıralaması anlatılıyor.", "topics": [{"title": "Giriş", "start_seconds": 0}]},
    ensure_ascii=False,
)
SUPPORT_JSON = json.dumps({"label": "destekliyor", "reason": "Gerekçe."}, ensure_ascii=False)


def question(text, quote):
    return {
        "question": text,
        "options": ["Komşu elemanları", "b", "c", "d"],
        "correct_index": 0,
        "explanation": "açıklama",
        "source_quote": quote,
    }


# İki doğrulanan, bir doğrulanamayan, bir tekrar, bir yapısı bozuk soru
QUESTIONS_JSON = json.dumps(
    {
        "questions": [
            question("Soru 1?", "kabarcık sıralaması komşu elemanları karşılaştırır"),
            question("Soru 2?", "videoda hiç söylenmeyen beş kelimelik alıntı"),
            question("Soru 3?", "en kötü durumda karmaşıklığı n kare olur"),
            question("soru 1", "kabarcık sıralaması komşu elemanları karşılaştırır"),
            {"question": "Bozuk?", "options": ["a", "b"], "correct_index": 0, "explanation": "x", "source_quote": "y"},
        ]
    },
    ensure_ascii=False,
)


def usage(prompt, completion):
    return SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion, total_tokens=prompt + completion)


def completion(content, usage_obj=None):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    if usage_obj is not None:
        response.usage = usage_obj
    return response


class FakeCompletions:
    """`chat.completions` taklidi: sistem istemine göre yanıt verir, ağa çıkmaz."""

    def __init__(self, questions=QUESTIONS_JSON, summary=SUMMARY_JSON, with_usage=True, error=None):
        self.questions, self.summary, self.with_usage, self.error = questions, summary, with_usage, error

    def create(self, **kwargs):
        if self.error:
            raise self.error
        system = kwargs["messages"][0]["content"]
        if "değerlendiricisin" in system:  # support_v1_system.txt
            return completion(SUPPORT_JSON, usage(50, 10) if self.with_usage else None)
        if "özetleyen" in system:  # summary_system.txt
            return completion(self.summary, usage(1000, 200) if self.with_usage else None)
        return completion(self.questions, usage(1500, 400) if self.with_usage else None)


def make_llm(completions, api_key="test"):
    return OpenAIClient(api_key=api_key, model="gpt-test", client=SimpleNamespace(chat=SimpleNamespace(completions=completions)))


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


client = TestClient(app)


@pytest.fixture
def runs_dir(monkeypatch, tmp_path):
    d = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(d))
    monkeypatch.setenv("OPENAI_API_KEY", ENV_KEY)
    get_settings.cache_clear()
    return d


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: make_transcript())

    def _use(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        return llm

    yield _use
    app.dependency_overrides.clear()


def only_record(runs_dir):
    (path,) = sorted(runs_dir.glob("*.json"))
    return path, runs.load_run(path)


class FakeClock:
    """Her çağrıda 10 ms ilerleyen saat."""

    def __init__(self):
        self.n = 0

    def __call__(self):
        value = self.n * 0.01
        self.n += 1
        return value


# --- Token sayıları -------------------------------------------------------------


def test_summary_tokens_recorded(setup, runs_dir):
    setup(make_llm(FakeCompletions()))
    r = client.post("/api/summary", json={"url": VID})
    assert r.status_code == 200

    _, record = only_record(runs_dir)
    assert record["outcome"] == "ok" and record["error"] is None
    (call,) = record["metrics"]["llm_calls"]
    assert call["purpose"] == "summary" and call["model"] == "gpt-test" and call["ok"] is True
    assert (call["prompt_tokens"], call["completion_tokens"], call["total_tokens"]) == (1000, 200, 1200)
    assert isinstance(call["ms"], float)
    # API yanıtı değişmedi: ölçümler yalnızca kayıtta
    assert record["response"] == r.json()
    assert "metrics" not in r.text and "llm_calls" not in r.text


def test_tokens_null_without_usage(setup, runs_dir):
    setup(make_llm(FakeCompletions(with_usage=False)))
    assert client.post("/api/questions", json={"url": VID}).status_code == 200
    _, record = only_record(runs_dir)
    (call,) = record["metrics"]["llm_calls"]
    assert call["purpose"] == "questions"
    assert call["prompt_tokens"] is None and call["completion_tokens"] is None and call["total_tokens"] is None


def test_dropped_counts_recorded(setup, runs_dir):
    setup(make_llm(FakeCompletions()))
    r = client.post("/api/questions", json={"url": VID})
    assert r.json()["returned_count"] == 3
    _, record = only_record(runs_dir)
    assert record["metrics"]["dropped"] == {"structure_invalid": 1, "duplicate": 1}


# --- Süreler (sabit saat) ---------------------------------------------------------


def test_summary_stage_times_with_fixed_clock(setup, runs_dir, monkeypatch):
    monkeypatch.setattr(metrics, "clock", FakeClock())
    setup(make_llm(FakeCompletions()))
    client.post("/api/summary", json={"url": VID})
    _, record = only_record(runs_dir)
    # Saat sırası: başlangıç 0; fetch 10-20; clean 30-40; model adımı 50-80 (çağrı 60-70); toplam 90
    assert record["metrics"]["stages"] == {
        "transcript_fetch_ms": 10.0,
        "clean_ms": 10.0,
        "llm_summary_ms": 10.0,
        "summary_parse_ms": 20.0,
        "total_ms": 90.0,
    }
    assert record["metrics"]["llm_calls"][0]["ms"] == 10.0
    assert "dropped" not in record["metrics"]


def test_questions_stage_times_with_support_check(setup, runs_dir, monkeypatch):
    monkeypatch.setattr(metrics, "clock", FakeClock())
    setup(make_llm(FakeCompletions()))
    client.post("/api/questions", json={"url": VID, "check_support": True})
    _, record = only_record(runs_dir)
    # Saat: 0 başlangıç; fetch 10-20; clean 30-40; model adımı 50-80 (çağrı 60-70);
    # yazım kuralları 90-100 (Aşama 9, b'de eklendi); destek kontrolü 110-160
    # (iki çağrı 120-130, 140-150); toplam 170
    assert record["metrics"]["stages"] == {
        "transcript_fetch_ms": 10.0,
        "clean_ms": 10.0,
        "llm_questions_ms": 10.0,
        "quote_verify_ms": 20.0,
        "writing_check_ms": 10.0,
        "support_check_ms": 50.0,
        "total_ms": 170.0,
    }


def test_no_support_stage_when_check_off(setup, runs_dir):
    setup(make_llm(FakeCompletions()))
    client.post("/api/questions", json={"url": VID})
    _, record = only_record(runs_dir)
    # writing_check_ms Aşama 9 (b)'de eklendi
    assert set(record["metrics"]["stages"]) == {
        "transcript_fetch_ms", "clean_ms", "llm_questions_ms", "quote_verify_ms", "writing_check_ms", "total_ms"
    }


def test_support_call_count(setup, runs_dir):
    setup(make_llm(FakeCompletions()))
    r = client.post("/api/questions", json={"url": VID, "check_support": True})
    verified = r.json()["verified_count"]
    assert verified == 2
    _, record = only_record(runs_dir)
    purposes = [c["purpose"] for c in record["metrics"]["llm_calls"]]
    assert purposes == ["questions"] + ["support"] * verified
    assert [c["total_tokens"] for c in record["metrics"]["llm_calls"]] == [1900, 60, 60]


# --- Hata kayıtları ---------------------------------------------------------------


def error_record(runs_dir):
    path, record = only_record(runs_dir)
    assert path.name.endswith("-error.json")
    assert record["outcome"] == "error" and record["response"] is None
    return path, record


def test_invalid_url_error_record(setup, runs_dir):
    setup(make_llm(FakeCompletions()))
    assert client.post("/api/summary", json={"url": "https://example.com/video"}).status_code == 422
    path, record = error_record(runs_dir)
    assert path.name.endswith("-unknown-summary-error.json")
    assert record["error"]["status_code"] == 422
    assert record["error"]["kind"] == "invalid_url" and record["error"]["stage"] == "transcript_fetch"
    assert record["metrics"]["llm_calls"] == []
    assert set(record["metrics"]["stages"]) == {"transcript_fetch_ms", "total_ms"}


def test_transcript_unavailable_error_record(setup, runs_dir, monkeypatch):
    setup(make_llm(FakeCompletions()))

    def no_transcript(video_id, languages):
        raise TranscriptUnavailable("Bu videoda altyazılar kapalı.")

    monkeypatch.setattr("app.routers.fetch_transcript", no_transcript)
    assert client.post("/api/questions", json={"url": VID}).status_code == 404
    path, record = error_record(runs_dir)
    assert path.name.endswith(f"-{VID}-questions-error.json")
    assert record["error"] == {
        "status_code": 404,
        "kind": "transcript_unavailable",
        "detail": "Bu videoda altyazılar kapalı.",
        "stage": "transcript_fetch",
    }


def test_empty_after_clean_error_record(setup, runs_dir, monkeypatch):
    setup(make_llm(FakeCompletions()))
    only_tags = Transcript(VID, "tr", True, [Segment("[Müzik]", 0.0, 5.0)])
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: only_tags)
    assert client.post("/api/summary", json={"url": VID}).status_code == 404
    _, record = error_record(runs_dir)
    assert record["error"]["kind"] == "transcript_unavailable" and record["error"]["stage"] == "clean"


def test_llm_not_configured_error_record(setup, runs_dir):
    # Anahtarsız gerçek istemci: _get_client çağrı yapmadan LLMNotConfigured fırlatır
    setup(OpenAIClient(api_key="", model="gpt-test"))
    assert client.post("/api/questions", json={"url": VID}).status_code == 503
    _, record = error_record(runs_dir)
    assert record["error"]["kind"] == "llm_not_configured" and record["error"]["stage"] == "llm_questions"
    assert record["metrics"]["llm_calls"] == []  # çağrı yapılmadı


def test_llm_failed_error_record_has_no_secrets(setup, runs_dir):
    message = (
        f"Incorrect API key provided: {FAKE_KEY}. Authorization: Bearer {FAKE_KEY} "
        f"api_key=abc123secret ortam={ENV_KEY}"
    )
    setup(make_llm(FakeCompletions(error=OpenAIError(message))))
    assert client.post("/api/summary", json={"url": VID}).status_code == 502
    path, record = error_record(runs_dir)
    assert record["error"]["kind"] == "llm_failed" and record["error"]["stage"] == "llm_summary"
    (call,) = record["metrics"]["llm_calls"]
    assert call["ok"] is False and call["total_tokens"] is None

    content = path.read_text(encoding="utf-8")
    for secret in (FAKE_KEY, "abc123secret", ENV_KEY, "Bearer sk"):
        assert secret not in content
    assert "openai_api_key" not in content.lower()
    assert "OpenAI çağrısı başarısız" in record["error"]["detail"]


def test_invalid_json_error_record(setup, runs_dir):
    setup(make_llm(FakeCompletions(questions="bu JSON değil")))
    assert client.post("/api/questions", json={"url": VID}).status_code == 502
    _, record = error_record(runs_dir)
    # Model yanıt verdi ama yanıt kullanılamadı: hata model çağrısından sonraki adımda
    assert record["error"]["kind"] == "invalid_json" and record["error"]["stage"] == "quote_verify"
    (call,) = record["metrics"]["llm_calls"]
    assert call["ok"] is True and call["total_tokens"] == 1900


def test_summary_invalid_json_stage(setup, runs_dir):
    setup(make_llm(FakeCompletions(summary="{}")))
    assert client.post("/api/summary", json={"url": VID}).status_code == 502
    _, record = error_record(runs_dir)
    assert record["error"]["kind"] == "invalid_json" and record["error"]["stage"] == "summary_parse"


def test_no_error_record_when_save_runs_false(setup, monkeypatch, tmp_path):
    d = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "false")
    monkeypatch.setenv("RUNS_DIR", str(d))
    get_settings.cache_clear()
    setup(make_llm(FakeCompletions(questions="bu JSON değil")))
    assert client.post("/api/questions", json={"url": VID}).status_code == 502
    assert client.post("/api/summary", json={"url": "geçersiz"}).status_code == 422
    assert not d.exists()


def test_error_record_write_failure_keeps_http_error(setup, monkeypatch, tmp_path):
    blocker = tmp_path / "dosya"
    blocker.write_text("engel", encoding="utf-8")
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(blocker))
    get_settings.cache_clear()
    setup(make_llm(FakeCompletions(questions="bu JSON değil")))
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 502 and "JSON" in r.json()["detail"]


# --- Paylaşım kodu ve gizli bilgi temizliği ---------------------------------------


def test_share_code_removed_from_record(setup, runs_dir):
    setup(make_llm(FakeCompletions()))
    url = f"https://www.youtube.com/watch?v={VID}&si=GIZLIPAYLASIM&t=42"
    assert client.post("/api/summary", json={"url": url}).status_code == 200
    _, record = only_record(runs_dir)
    assert record["request"]["url"] == f"https://www.youtube.com/watch?v={VID}&t=42"


def test_strip_share_code_variants():
    assert runs.strip_share_code(f"https://youtu.be/{VID}?si=abc") == f"https://youtu.be/{VID}"
    assert runs.strip_share_code(VID) == VID
    assert runs.strip_share_code(f"youtube.com/watch?v={VID}&si=x") == f"youtube.com/watch?v={VID}"


def test_scrub_secrets():
    text = "anahtar sk-proj-AbC123_xyz-987 Authorization: Bearer tok123 token=qwe password: p4ss"
    cleaned = scrub_secrets(text, known_secrets=("p4ss",))
    for secret in ("AbC123_xyz-987", "tok123", "qwe", "p4ss"):
        assert secret not in cleaned


# --- Eşzamanlılık ----------------------------------------------------------------


class InterleavingCompletions:
    """İlk isteğin yanıtı, token bilgisi kaydedildikten sonra ikinci istek bitene kadar bekletilir.

    Ölçümler paylaşılan bir yerde (istemcide ya da genel bir değişkende)
    tutulsaydı ilk istek ikinci isteğin çağrısını ya da token sayısını görürdü.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.count = 0
        self.first_waiting = threading.Event()
        self.release = threading.Event()

    def create(self, **kwargs):
        with self.lock:
            self.count += 1
            n = self.count
        message = SimpleNamespace(message=SimpleNamespace(content=SUMMARY_JSON))
        if n == 1:
            outer = self

            class Blocking:
                # llm.py önce usage'ı kaydeder, sonra choices'ı okur: bekleme tam arada olur
                usage = SimpleNamespace(prompt_tokens=111, completion_tokens=1, total_tokens=112)

                @property
                def choices(self):
                    outer.first_waiting.set()
                    assert outer.release.wait(10)
                    return [message]

            return Blocking()
        return SimpleNamespace(
            choices=[message], usage=SimpleNamespace(prompt_tokens=222, completion_tokens=2, total_tokens=224)
        )


def test_interleaved_requests_do_not_mix_metrics(setup, runs_dir):
    # İki istek aynı (paylaşılan) istemci nesnesini kullanır
    completions = InterleavingCompletions()
    setup(make_llm(completions))

    results = {}
    first = threading.Thread(
        target=lambda: results.setdefault("a", client.post("/api/summary", json={"url": VID, "transcript_mode": "raw"}))
    )
    first.start()
    assert completions.first_waiting.wait(10)
    # İlk istek model yanıtının ortasında beklerken ikinci istek baştan sona çalışır
    results["b"] = client.post("/api/summary", json={"url": VID, "transcript_mode": "clean"})
    completions.release.set()
    first.join(10)
    assert results["a"].status_code == 200 and results["b"].status_code == 200

    records = {r["request"]["transcript_mode"]: r for r in map(runs.load_run, runs_dir.glob("*.json"))}
    (call_a,) = records["raw"]["metrics"]["llm_calls"]
    (call_b,) = records["clean"]["metrics"]["llm_calls"]
    assert call_a["prompt_tokens"] == 111 and call_a["total_tokens"] == 112
    assert call_b["prompt_tokens"] == 222 and call_b["total_tokens"] == 224


# --- Eski kayıtlar ---------------------------------------------------------------


def test_load_run_v3_record_defaults(tmp_path):
    path = tmp_path / "eski.json"
    path.write_text(
        json.dumps(
            {
                "record_version": 3,
                "saved_at": "2026-10-15T10:00:00+03:00",
                "endpoint": "/api/summary",
                "request": {"url": VID, "transcript_mode": "clean"},
                "response": {"video_id": VID},
            }
        ),
        encoding="utf-8",
    )
    record = runs.load_run(path)
    assert record["record_version"] == 3
    assert record["outcome"] == "ok" and record["metrics"] is None and record["error"] is None
    assert record["support_check"] is None and record["quote_audit"] == []


def test_load_run_v1_record_defaults():
    from pathlib import Path

    old = Path(__file__).resolve().parents[2] / "docs" / "bulgular" / "asama-6-test-2-tarih.json"
    record = runs.load_run(old)
    assert record["outcome"] == "ok" and record["metrics"] is None and record["error"] is None
