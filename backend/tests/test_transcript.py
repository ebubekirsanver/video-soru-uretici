from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

from app.main import app
from app.services import transcript as transcript_service
from app.services.transcript import TranscriptUnavailable, fetch_transcript

VID = "dQw4w9WgXcQ"


class FakeFetched(list):
    language_code = "tr"
    is_generated = True


def make_fetched():
    items = [
        SimpleNamespace(text="Merhaba arkadaşlar", start=0.0, duration=2.5),
        SimpleNamespace(text="   ", start=2.5, duration=1.0),  # boş, atlanmalı
        SimpleNamespace(text="bugün sıralama algoritmalarına bakacağız", start=3.5, duration=4.0),
    ]
    return FakeFetched(items)


class FakeApi:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    def fetch(self, video_id, languages=("en",)):
        self.calls.append((video_id, list(languages)))
        if self.error:
            raise self.error
        return self.result


def test_fetch_transcript_ok():
    api = FakeApi(result=make_fetched())
    t = fetch_transcript(VID, ["tr", "en"], api=api)
    assert api.calls == [(VID, ["tr", "en"])]
    assert t.language == "tr" and t.is_generated is True
    assert [s.text for s in t.segments] == ["Merhaba arkadaşlar", "bugün sıralama algoritmalarına bakacağız"]
    assert t.duration_seconds == 7.5


def test_fetch_transcript_disabled():
    api = FakeApi(error=TranscriptsDisabled(VID))
    with pytest.raises(TranscriptUnavailable):
        fetch_transcript(VID, ["tr"], api=api)


def test_fetch_transcript_not_found():
    api = FakeApi(error=NoTranscriptFound(VID, ["tr"], None))
    with pytest.raises(TranscriptUnavailable):
        fetch_transcript(VID, ["tr"], api=api)


client = TestClient(app)


def test_endpoint_ok(monkeypatch):
    def fake_fetch(video_id, languages, api=None):
        return transcript_service.Transcript(
            video_id=video_id,
            language="tr",
            is_generated=True,
            segments=[transcript_service.Segment("merhaba", 0.0, 2.0)],
        )

    monkeypatch.setattr("app.routers.fetch_transcript", fake_fetch)
    r = client.post("/api/transcript", json={"url": f"https://youtu.be/{VID}"})
    assert r.status_code == 200
    body = r.json()
    assert body["video_id"] == VID and body["segment_count"] == 1
    assert body["segments"][0] == {"text": "merhaba", "start": 0.0, "duration": 2.0}


def test_endpoint_invalid_url():
    r = client.post("/api/transcript", json={"url": "https://example.com"})
    assert r.status_code == 422


def test_endpoint_unavailable(monkeypatch):
    def fake_fetch(video_id, languages, api=None):
        raise TranscriptUnavailable("Bu videoda altyazılar kapalı.")

    monkeypatch.setattr("app.routers.fetch_transcript", fake_fetch)
    r = client.post("/api/transcript", json={"url": VID})
    assert r.status_code == 404
    assert "kapalı" in r.json()["detail"]
