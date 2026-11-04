import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def _runs_disabled_by_default(monkeypatch):
    """Testler gerçek backend/runs/ ve backend/transcripts/ klasörlerine dosya bırakmasın.

    Kayıt testleri kendi fixture'larıyla SAVE_RUNS'ı açıp geçici klasör verir;
    önbellek testleri de TRANSCRIPT_CACHE'i aynı biçimde açar.
    Ortam değişkeni .env dosyasından önce gelir; ayar önbelleği her testte temizlenir.
    """
    monkeypatch.setenv("SAVE_RUNS", "false")
    monkeypatch.setenv("TRANSCRIPT_CACHE", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
