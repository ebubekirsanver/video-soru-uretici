"""Transkript önbelleği ve YouTube engeli hatası. Sahte YouTube; gerçek istek yok."""

import json
import logging
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from youtube_transcript_api import IpBlocked, RequestBlocked

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.llm import get_llm
from app.services.transcript import (
    Segment,
    Transcript,
    TranscriptBlocked,
    TranscriptUnavailable,
    fetch_transcript,
)
from app.services.transcript_cache import cache_path, load_transcript, read_cached

VID = "dQw4w9WgXcQ"
LANGS = ["tr", "en"]
BLOCKED_TEXT = "YouTube bu ağdan gelen istekleri geçici olarak engelledi; bir süre sonra ya da başka bir ağdan deneyin."


def make_transcript():
    return Transcript(VID, "tr", True, [Segment("merhaba arkadaşlar", 0.0, 2.5), Segment("[Müzik] konu", 2.5, 3.0)])


class FakeYouTube:
    """fetch_transcript yerine geçer; kaç kez çağrıldığını sayar."""

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def __call__(self, video_id, languages):
        self.calls.append((video_id, list(languages)))
        if self.error:
            raise self.error
        return make_transcript()


@pytest.fixture
def cache_dir(monkeypatch, tmp_path):
    """Önbelleği açar ve geçici klasöre yönlendirir (conftest testlerde kapalı tutuyor)."""
    d = tmp_path / "transcripts"
    monkeypatch.setenv("TRANSCRIPT_CACHE", "true")
    monkeypatch.setenv("TRANSCRIPT_CACHE_DIR", str(d))
    get_settings.cache_clear()
    return d


# --- Önbellek -----------------------------------------------------------------------


def test_first_request_fetches_and_writes(cache_dir):
    yt = FakeYouTube()
    transcript, source = load_transcript(VID, LANGS, yt)
    assert source == "youtube" and len(yt.calls) == 1
    assert transcript == make_transcript()

    data = json.loads(cache_path(VID, LANGS).read_text(encoding="utf-8"))
    assert data["video_id"] == VID and data["language"] == "tr" and data["is_generated"] is True
    assert data["languages"] == LANGS and data["fetched_at"]
    assert data["segments"][0] == {"text": "merhaba arkadaşlar", "start": 0.0, "duration": 2.5}


def test_second_request_does_not_call_youtube(cache_dir):
    yt = FakeYouTube()
    first, _ = load_transcript(VID, LANGS, yt)
    second, source = load_transcript(VID, LANGS, yt)
    assert source == "cache" and len(yt.calls) == 1
    assert second == first  # ham transkript aynen geri gelir


def test_other_language_list_is_separate_entry(cache_dir):
    yt = FakeYouTube()
    load_transcript(VID, ["tr", "en"], yt)
    _, source = load_transcript(VID, ["en"], yt)
    assert source == "youtube" and len(yt.calls) == 2


@pytest.mark.parametrize(
    "content",
    ["bu JSON değil", "{}", '{"video_id": "baska", "segments": []}', '{"video_id": "dQw4w9WgXcQ", "segments": [{"text": "x"}]}'],
)
def test_corrupt_cache_refetches_and_logs(cache_dir, caplog, content):
    path = cache_path(VID, LANGS)
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    yt = FakeYouTube()
    with caplog.at_level(logging.WARNING, logger="app.services.transcript_cache"):
        transcript, source = load_transcript(VID, LANGS, yt)
    assert source == "youtube" and len(yt.calls) == 1 and transcript == make_transcript()
    assert any("okunamadı" in r.getMessage() for r in caplog.records)
    assert read_cached(VID, LANGS) == make_transcript()  # sağlam hâliyle yeniden yazıldı


def test_cache_off_fetches_every_time(cache_dir, monkeypatch):
    monkeypatch.setenv("TRANSCRIPT_CACHE", "false")
    get_settings.cache_clear()
    yt = FakeYouTube()
    assert load_transcript(VID, LANGS, yt)[1] == "youtube"
    assert load_transcript(VID, LANGS, yt)[1] == "youtube"
    assert len(yt.calls) == 2
    assert not cache_dir.exists()


@pytest.mark.parametrize("error", [TranscriptUnavailable("yok"), TranscriptBlocked("engel")])
def test_error_is_not_cached(cache_dir, error):
    yt = FakeYouTube(error=error)
    with pytest.raises(type(error)):
        load_transcript(VID, LANGS, yt)
    assert not cache_path(VID, LANGS).exists()


def test_write_failure_does_not_break_request(monkeypatch, tmp_path, caplog):
    blocker = tmp_path / "dosya"
    blocker.write_text("engel", encoding="utf-8")
    monkeypatch.setenv("TRANSCRIPT_CACHE", "true")
    monkeypatch.setenv("TRANSCRIPT_CACHE_DIR", str(blocker))
    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING, logger="app.services.transcript_cache"):
        transcript, source = load_transcript(VID, LANGS, FakeYouTube())
    assert source == "youtube" and transcript == make_transcript()
    assert any("yazılamadı" in r.getMessage() for r in caplog.records)


# --- Engel hatası (kütüphane sınıfları) -----------------------------------------------


def fake_api(error):
    def fetch(video_id, languages=("en",)):
        raise error

    return SimpleNamespace(fetch=fetch)


@pytest.mark.parametrize("error", [IpBlocked(VID), RequestBlocked(VID)])
def test_fetch_transcript_maps_block_errors(error):
    with pytest.raises(TranscriptBlocked) as exc:
        fetch_transcript(VID, LANGS, api=fake_api(error))
    assert str(exc.value) == BLOCKED_TEXT
    assert not isinstance(exc.value, TranscriptUnavailable)  # video sorunu değil


# --- API ve kayıt ---------------------------------------------------------------------


client = TestClient(app)


class SummaryLLM:
    model = "fake-model"

    def complete(self, system, user, json_mode=False, max_tokens=None):
        return json.dumps({"summary": "Özet.", "topics": [{"title": "Giriş", "start_seconds": 0}]}, ensure_ascii=False)


@pytest.fixture
def api(cache_dir, monkeypatch, tmp_path):
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()
    app.dependency_overrides[get_llm] = lambda: SummaryLLM()

    def use(yt):
        monkeypatch.setattr("app.routers.fetch_transcript", yt)
        return yt

    use.runs_dir = runs_dir
    yield use
    app.dependency_overrides.clear()


def records(runs_dir):
    return [runs.load_run(p) for p in sorted(runs_dir.glob("*.json"))]


def test_api_second_request_uses_cache_and_records_source(api):
    yt = api(FakeYouTube())
    assert client.post("/api/summary", json={"url": VID}).status_code == 200
    assert client.post("/api/summary", json={"url": VID}).status_code == 200
    assert len(yt.calls) == 1
    sources = sorted(r["metrics"]["transcript_source"] for r in records(api.runs_dir))
    assert sources == ["cache", "youtube"]
    assert all(r["record_version"] == 10 for r in records(api.runs_dir))


def test_api_transcript_endpoint_also_uses_cache(api):
    yt = api(FakeYouTube())
    first = client.post("/api/transcript", json={"url": VID})
    second = client.post("/api/transcript", json={"url": VID})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(yt.calls) == 1


def block_via_library(video_id, languages):
    return fetch_transcript(video_id, languages, api=fake_api(IpBlocked(video_id)))


def test_api_ip_block_503_with_own_message_and_kind(api):
    api(block_via_library)
    r = client.post("/api/summary", json={"url": VID})
    assert r.status_code == 503
    assert r.json()["detail"] == BLOCKED_TEXT
    (record,) = records(api.runs_dir)
    assert record["outcome"] == "error"
    assert record["error"]["kind"] == "youtube_blocked" and record["error"]["stage"] == "transcript_fetch"
    assert not cache_path(VID, LANGS).exists()


def test_api_block_with_cached_transcript_still_works(api):
    # Önbellekteki video engel sırasında da çalışır
    api(FakeYouTube())
    assert client.post("/api/summary", json={"url": VID}).status_code == 200
    api(block_via_library)
    assert client.post("/api/summary", json={"url": VID}).status_code == 200


def test_api_transcript_unavailable_stays_404(api):
    api(FakeYouTube(error=TranscriptUnavailable("Bu videoda altyazılar kapalı.")))
    r = client.post("/api/summary", json={"url": VID})
    assert r.status_code == 404
    (record,) = records(api.runs_dir)
    assert record["error"]["kind"] == "transcript_unavailable"
    assert "transcript_source" not in record["metrics"]


def test_load_run_v7_record_reads_without_source(tmp_path):
    path = tmp_path / "eski.json"
    path.write_text(json.dumps({"record_version": 7, "endpoint": "/api/summary", "request": {}, "response": {},
                                "metrics": {"stages": {"total_ms": 1.0}, "llm_calls": []}}), encoding="utf-8")
    record = runs.load_run(path)
    assert record["record_version"] == 7 and "transcript_source" not in record["metrics"]
