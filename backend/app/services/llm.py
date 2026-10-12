"""LLM soyut katmanı.

Uygulamanın geri kalanı yalnızca `LLMClient` arayüzünü tanır. Sağlayıcı
değişirse (başka bir model ya da yerel LLM) yeni bir sınıf yazıp `get_llm`
içinde onu döndürmek yeterlidir.
"""

from typing import Protocol

from openai import OpenAI, OpenAIError

from app.config import get_settings


class LLMError(Exception):
    """LLM çağrısı başarısız oldu ya da yanıt kullanılamaz."""


class LLMNotConfigured(LLMError):
    """LLM için gerekli ayar (örneğin API anahtarı) tanımlı değil."""


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        """Sistem ve kullanıcı mesajını gönderir, modelin metin yanıtını döndürür."""
        ...


class OpenAIClient:
    """`LLMClient` arayüzünün OpenAI uygulaması (varsayılan: GPT-4o-mini)."""

    def __init__(self, api_key: str, model: str, temperature: float = 0.2, client=None):
        self.model = model
        self.temperature = temperature
        self._api_key = api_key
        # Testlerde sahte istemci verilir; gerçek istemci ilk çağrıda kurulur
        self._client = client

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise LLMNotConfigured("OPENAI_API_KEY tanımlı değil (.env dosyasını kontrol et).")
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        client = self._get_client()
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self.temperature,
                **kwargs,
            )
        except OpenAIError as exc:
            raise LLMError(f"OpenAI çağrısı başarısız: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("LLM boş yanıt döndürdü.")
        return content


def get_llm() -> LLMClient:
    """Ayarlara göre LLM istemcisini döndürür (FastAPI bağımlılığı olarak kullanılır)."""
    settings = get_settings()
    return OpenAIClient(api_key=settings.openai_api_key, model=settings.openai_model)
