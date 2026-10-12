from types import SimpleNamespace

import pytest
from openai import OpenAIError

from app.services.llm import LLMError, LLMNotConfigured, OpenAIClient


class FakeCompletions:
    """OpenAI `chat.completions` taklidi; gerçek ağ çağrısı yapmaz."""

    def __init__(self, content="yanıt", error=None):
        self.content, self.error, self.calls = content, error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_client(completions):
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_complete_sends_model_and_messages():
    completions = FakeCompletions(content="merhaba")
    llm = OpenAIClient(api_key="test", model="gpt-4o-mini", client=make_client(completions))

    assert llm.complete("sistem", "kullanıcı") == "merhaba"
    call = completions.calls[0]
    assert call["model"] == "gpt-4o-mini"
    assert call["messages"] == [
        {"role": "system", "content": "sistem"},
        {"role": "user", "content": "kullanıcı"},
    ]
    assert "response_format" not in call


def test_complete_json_mode():
    completions = FakeCompletions(content="{}")
    llm = OpenAIClient(api_key="test", model="m", client=make_client(completions))
    llm.complete("s", "u", json_mode=True)
    assert completions.calls[0]["response_format"] == {"type": "json_object"}


def test_missing_api_key_raises():
    llm = OpenAIClient(api_key="", model="m")
    with pytest.raises(LLMNotConfigured):
        llm.complete("s", "u")


def test_api_error_wrapped():
    completions = FakeCompletions(error=OpenAIError("bağlantı hatası"))
    llm = OpenAIClient(api_key="test", model="m", client=make_client(completions))
    with pytest.raises(LLMError, match="bağlantı hatası"):
        llm.complete("s", "u")


def test_empty_response_raises():
    completions = FakeCompletions(content=None)
    llm = OpenAIClient(api_key="test", model="m", client=make_client(completions))
    with pytest.raises(LLMError):
        llm.complete("s", "u")
