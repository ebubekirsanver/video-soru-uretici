"""Gömme katmanı (Aşama 7a): gerçek model yüklenmez, indirme yapılmaz."""

import sys
from types import ModuleType

from app.config import get_settings
from app.services import embeddings
from app.services.embeddings import SentenceTransformerClient, get_embedder


class FakeSentenceTransformer:
    loads = 0

    def __init__(self, name):
        FakeSentenceTransformer.loads += 1
        self.name = name
        self.calls = []

    def encode(self, texts, normalize_embeddings=False):
        self.calls.append((list(texts), normalize_embeddings))
        return [[0.6, 0.8] for _ in texts]


def install_fake_module(monkeypatch):
    module = ModuleType("sentence_transformers")
    module.SentenceTransformer = FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    FakeSentenceTransformer.loads = 0


def test_model_not_loaded_until_first_embed(monkeypatch):
    install_fake_module(monkeypatch)
    client = SentenceTransformerClient("BAAI/bge-m3")
    assert client.model == "BAAI/bge-m3"
    assert FakeSentenceTransformer.loads == 0
    assert client.embed([]) == []  # boş girdi modeli yüklemez
    assert FakeSentenceTransformer.loads == 0


def test_model_loaded_once_and_vectors_normalized(monkeypatch):
    install_fake_module(monkeypatch)
    client = SentenceTransformerClient("BAAI/bge-m3")
    assert client.embed(["bir", "iki"]) == [[0.6, 0.8], [0.6, 0.8]]
    client.embed(["üç"])
    assert FakeSentenceTransformer.loads == 1  # sonraki çağrılar aynı nesneyi kullanır
    model = client._model
    assert model.name == "BAAI/bge-m3"
    assert all(normalize for _, normalize in model.calls)


def test_get_embedder_uses_settings_and_is_cached(monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODEL", "test/model")
    get_settings.cache_clear()
    get_embedder.cache_clear()
    try:
        first = get_embedder()
        assert first.model == "test/model"
        assert get_embedder() is first
        assert first._model is None  # model henüz yüklenmedi
    finally:
        get_embedder.cache_clear()


def test_default_embedding_model_is_bge_m3(monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    get_settings.cache_clear()
    assert get_settings().embedding_model == "BAAI/bge-m3"


def test_importing_module_does_not_import_sentence_transformers():
    # Modülün en üst düzey içe aktarmalarında sentence_transformers yok (yalnızca ilk embed çağrısında)
    with open(embeddings.__file__, encoding="utf-8") as f:
        top_level = [line for line in f if line.startswith(("import ", "from "))]
    assert not any("sentence_transformers" in line for line in top_level)
