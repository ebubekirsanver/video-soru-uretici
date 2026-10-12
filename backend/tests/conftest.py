import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def _runs_disabled_by_default(monkeypatch):
    """Testler gerçek backend/runs/ klasörüne kayıt bırakmasın.

    Kayıt testleri kendi fixture'larıyla SAVE_RUNS'ı açıp geçici klasör verir.
    Ortam değişkeni .env dosyasından önce gelir; ayar önbelleği her testte temizlenir.
    """
    monkeypatch.setenv("SAVE_RUNS", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
