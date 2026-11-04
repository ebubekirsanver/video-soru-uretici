from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Ortam değişkenlerinden okunan ayarlar (.env desteklenir)."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Video Soru Üretici"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Konu tabanlı soru üretiminde (questions-v3/v4) bir yanıtın en çok çıktı token sayısı
    question_max_tokens: int = 1000
    # Virgülle ayrılmış dil kodları, sırayla denenir
    transcript_languages: str = "tr,en"
    # Başarılı özet/soru yanıtları yerelde dosyaya kaydedilsin mi
    save_runs: bool = True
    # Kayıt klasörü; varsayılan backend/runs (sunucunun başlatıldığı klasörden bağımsız)
    runs_dir: Path = BACKEND_DIR / "runs"
    # Başarılı transkriptler yerelde saklansın mı (varsayılan backend/transcripts, git dışında)
    transcript_cache: bool = True
    transcript_cache_dir: Path = BACKEND_DIR / "transcripts"
    # RAG (Aşama 7a): gömme modeli ve kalıcı ChromaDB dizini (varsayılan backend/chroma, git dışında)
    embedding_model: str = "BAAI/bge-m3"
    chroma_dir: Path = BACKEND_DIR / "chroma"

    @property
    def transcript_language_list(self) -> list[str]:
        return [d.strip() for d in self.transcript_languages.split(",") if d.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
