"""Gömme (embedding) katmanı (Aşama 7a).

Uygulamanın geri kalanı yalnızca `EmbeddingClient` arayüzünü tanır (LLM
katmanındaki `LLMClient` gibi). Ana deneyde çok dilli BGE-M3 kullanılır;
farklı gömme modelleri ikincil deneydir (CLAUDE.md, kural 6).

Model ilk kullanımda yüklenir, import sırasında değil: `sentence_transformers`
de ancak o anda içe aktarılır. Testlerde gerçek model yüklenmez; sahte bir
gömme sınıfı kullanılır.
"""

from functools import lru_cache
from typing import Protocol

from app.config import get_settings


class EmbeddingUnavailable(Exception):
    """Gömme modeli yüklenemedi (paket kurulu değil, indirme başarısız vb.)."""


class EmbeddingClient(Protocol):
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Her metin için bir vektör döndürür (metin sırasıyla)."""
        ...


class SentenceTransformerClient:
    """`EmbeddingClient` arayüzünün sentence-transformers uygulaması (varsayılan: BAAI/bge-m3).

    Vektörler normalize edilir (uzunluk 1), böylece kosinüs benzerliği
    doğrudan karşılaştırılabilir. Model ilk `embed` çağrısında bir kez
    yüklenir ve sonraki çağrılarda aynı nesne kullanılır. İlk yüklemede model
    Hugging Face'ten indirilir.
    """

    def __init__(self, model: str = "BAAI/bge-m3"):
        self.model = model
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model)
            except Exception as exc:  # paket yok, indirme ya da yükleme hatası
                raise EmbeddingUnavailable(f"Gömme modeli ({self.model}) yüklenemedi: {exc}") from exc
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._load().encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]


@lru_cache
def get_embedder() -> EmbeddingClient:
    """Ayarlardaki modelle tek bir gömme istemcisi (model bir kez yüklensin diye önbellekli)."""
    return SentenceTransformerClient(get_settings().embedding_model)


def get_embedder_provider():
    """FastAPI bağımlılığı: gömme istemcisini döndüren bir fonksiyon.

    İstemci yalnızca gerektiğinde (ör. benzer soru işaretlemede) alınır; eski
    (v1) isteklerde hiç kullanılmaz. Testlerde sahte gömmeyle değiştirilir.
    """
    return get_embedder
