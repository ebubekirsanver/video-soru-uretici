from types import SimpleNamespace

import pytest
from openai import OpenAIError

from app.services.llm import LLMError, LLMNotConfigured, LLMTruncated, OpenAIClient, last_usage, reset_usage


class FakeCompletions:
    """OpenAI `chat.completions` taklidi; gerçek ağ çağrısı yapmaz."""

    def __init__(self, content="yanıt", error=None, finish_reason="stop", usage=None):
        self.content, self.error, self.calls = content, error, []
        self.finish_reason, self.usage = finish_reason, usage

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.content)
        choice = SimpleNamespace(message=message, finish_reason=self.finish_reason)
        return SimpleNamespace(choices=[choice], usage=self.usage)


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


def test_max_tokens_sent_only_when_given():
    completions = FakeCompletions()
    llm = OpenAIClient(api_key="test", model="m", client=make_client(completions))
    llm.complete("s", "u")
    llm.complete("s", "u", max_tokens=1000)
    assert "max_tokens" not in completions.calls[0]
    assert completions.calls[1]["max_tokens"] == 1000


def test_length_finish_with_limit_raises_truncated_and_keeps_usage():
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=1000, total_tokens=1010)
    completions = FakeCompletions(content='{"questions": [', finish_reason="length", usage=usage)
    llm = OpenAIClient(api_key="test", model="m", client=make_client(completions))
    reset_usage()
    with pytest.raises(LLMTruncated):
        llm.complete("s", "u", json_mode=True, max_tokens=1000)
    assert last_usage()["completion_tokens"] == 1000  # kesilen yanıtın maliyeti de ölçülür


def test_length_finish_without_limit_keeps_old_behavior():
    completions = FakeCompletions(content="kesik", finish_reason="length")
    llm = OpenAIClient(api_key="test", model="m", client=make_client(completions))
    assert llm.complete("s", "u") == "kesik"
