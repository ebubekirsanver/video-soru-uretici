from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ortam değişkenlerinden okunan ayarlar (.env desteklenir)."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Video Soru Üretici"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Virgülle ayrılmış dil kodları, sırayla denenir
    transcript_languages: str = "tr,en"

    @property
    def transcript_language_list(self) -> list[str]:
        return [d.strip() for d in self.transcript_languages.split(",") if d.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
