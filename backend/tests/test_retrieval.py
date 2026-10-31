"""ChromaDB dizini ve erişim (Aşama 7a). Sahte gömme; gerçek model ve ağ yok.

Her test kendi geçici klasöründe kalıcı bir Chroma istemcisi açar; testler
birbirini etkilemez.
"""

import hashlib
import math

import pytest

from app.services.chunking import CHUNKING_VERSION, Chunk
from app.services.retrieval import TranscriptIndex, chunk_id
from app.services.transcript import Segment

DIM = 64


class FakeEmbedder:
    """Deterministik sahte gömme: kelimeler md5 ile 64 kutuya sayılır, vektör normalize edilir."""

    model = "fake-embedder"

    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(list(texts))
        vectors = []
        for text in texts:
            v = [0.0] * DIM
            for word in text.lower().split():
                v[int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % DIM] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            vectors.append([x / norm for x in v])
        return vectors


TOPICS = [
    "fotosentez klorofil ışık bitki yaprak glikoz oksijen",
    "kemosentez bakteri hidrotermal baca kükürt enerji",
    "hücre zarı difüzyon osmoz geçirgenlik madde taşıma",
    "mitoz bölünme kromozom iğ ipliği çekirdek evre",
]


def make_chunks(video_id, topics=TOPICS):
    return [Chunk(video_id, i, i * 30.0, i * 30.0 + 35.0, text, CHUNKING_VERSION) for i, text in enumerate(topics)]


@pytest.fixture
def index(tmp_path):
    return TranscriptIndex(FakeEmbedder(), path=tmp_path / "chroma")


def test_second_index_does_not_reembed(index, tmp_path):
    first = index.index_chunks(make_chunks("vidA"))
    assert first.embedded is True and first.chunk_count == 4
    assert len(index.embedder.calls) == 1  # tüm parçalar tek çağrıda gömülür

    second = index.index_chunks(make_chunks("vidA"))
    assert second.embedded is False
    assert len(index.embedder.calls) == 1  # yeniden gömme yok

    # Aynı klasör yeniden açılınca (ör. sunucu yeniden başladı) da yeniden gömülmez
    reopened = TranscriptIndex(FakeEmbedder(), path=tmp_path / "chroma")
    assert reopened.index_chunks(make_chunks("vidA")).embedded is False
    assert reopened.embedder.calls == []


def test_changed_transcript_is_reindexed(index):
    index.index_chunks(make_chunks("vidA"))
    index.index_chunks(make_chunks("vidA", TOPICS[:2]))
    assert len(index.embedder.calls) == 2
    found = index.retrieve("vidA", "mitoz kromozom", k=10)
    assert sorted(c.chunk_index for c in found) == [0, 1]  # eski parçalar silindi


def test_same_count_changed_text_is_reembedded(index):
    index.index_chunks(make_chunks("vidA"))
    changed = TOPICS[:3] + ["mayoz eşey hücresi krossing over çeşitlilik"]  # parça sayısı aynı (4)
    result = index.index_chunks(make_chunks("vidA", changed))
    assert result.embedded is True
    assert len(index.embedder.calls) == 2
    found = index.retrieve("vidA", "mayoz krossing over", k=1)
    assert found[0].chunk_index == 3 and found[0].text == changed[3]
    assert index.retrieve("vidA", "mayoz", k=10)[0].text != TOPICS[3]
    assert TOPICS[3] not in [c.text for c in index.retrieve("vidA", "mitoz", k=10)]


def test_index_without_hashes_is_reembedded_once(index):
    # Özet üst verisi eklenmeden önce oluşturulmuş dizini taklit et: aynı kimlikler, özet yok
    chunks = make_chunks("vidA")
    index._collection.add(
        ids=[chunk_id("vidA", CHUNKING_VERSION, c.chunk_index) for c in chunks],
        embeddings=index.embedder.embed([c.text for c in chunks]),
        documents=[c.text for c in chunks],
        metadatas=[
            {"video_id": "vidA", "chunking": CHUNKING_VERSION, "chunk_index": c.chunk_index,
             "start_seconds": c.start_seconds, "end_seconds": c.end_seconds}
            for c in chunks
        ],
    )
    index.embedder.calls.clear()
    assert index.index_chunks(chunks).embedded is True  # özet olmadığı için bir kez yeniden gömülür
    assert index.index_chunks(chunks).embedded is False  # sonra önbellek çalışır
    assert len(index.embedder.calls) == 1


def test_retrieve_most_relevant_first(index):
    index.index_chunks(make_chunks("vidA"))
    found = index.retrieve("vidA", "hidrotermal baca kükürt bakteri", k=4)
    assert found[0].chunk_index == 1
    assert found[0].text == TOPICS[1]
    assert (found[0].start_seconds, found[0].end_seconds) == (30.0, 65.0)
    scores = [c.score for c in found]
    assert scores == sorted(scores, reverse=True)
    assert 0.0 < found[0].score <= 1.0


def test_retrieve_only_requested_video(index):
    index.index_chunks(make_chunks("vidA"))
    other = ["kemosentez bakteri hidrotermal baca kükürt enerji tekrar", "başka video başka konu"]
    index.index_chunks(make_chunks("vidB", other))
    found = index.retrieve("vidB", "kemosentez bakteri hidrotermal", k=10)
    assert len(found) == 2
    assert {c.text for c in found} == set(other)
    assert all(c.text not in TOPICS for c in found)


def test_k_is_applied(index):
    index.index_chunks(make_chunks("vidA"))
    assert len(index.retrieve("vidA", "fotosentez", k=2)) == 2
    assert len(index.retrieve("vidA", "fotosentez", k=1)) == 1
    assert len(index.retrieve("vidA", "fotosentez", k=10)) == 4  # parça sayısından fazlası istenince hepsi
    with pytest.raises(ValueError):
        index.retrieve("vidA", "fotosentez", k=0)


def test_unknown_video_returns_empty(index):
    index.index_chunks(make_chunks("vidA"))
    calls = len(index.embedder.calls)
    assert index.retrieve("yok", "fotosentez") == []
    assert len(index.embedder.calls) == calls  # parça yoksa sorgu gömülmez


def test_index_transcript_uses_fixed_chunks(index):
    segments = [Segment(" ".join(f"s{i}k{j}" for j in range(20)), i * 5.0, 5.0) for i in range(20)]
    result = index.index_transcript("vidC", segments)
    assert (result.chunk_count, result.chunking, result.embedded) == (3, CHUNKING_VERSION, True)
    found = index.retrieve("vidC", "s19k0 s19k1 s19k2", k=1)
    assert found[0].chunk_index == 2 and found[0].end_seconds == 100.0
    with pytest.raises(ValueError):
        index.index_transcript("bos", [])


def test_chunk_id_format():
    assert chunk_id("vidA", "fixed-150-30", 3) == "vidA:fixed-150-30:3"


def test_mixed_chunks_rejected(index):
    chunks = make_chunks("vidA")
    chunks[1] = Chunk("vidB", 1, 0.0, 1.0, "x", CHUNKING_VERSION)
    with pytest.raises(ValueError):
        index.index_chunks(chunks)


def test_other_embedding_model_rejected(index, tmp_path):
    index.index_chunks(make_chunks("vidA"))

    class OtherModel(FakeEmbedder):
        model = "baska-model"

    with pytest.raises(ValueError, match="başka bir dizin"):
        TranscriptIndex(OtherModel(), path=tmp_path / "chroma")
