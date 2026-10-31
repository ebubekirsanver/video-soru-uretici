"""ChromaDB dizini ve erişim (Aşama 7a, RAG koşulu).

Bir videonun temizlenmiş transkripti sabit boyutlu parçalara bölünür
(`chunking.fixed_size_chunks`), parçalar gömülür ve tek bir koleksiyonda
kosinüs benzerliğiyle dizinlenir. `retrieve` yalnızca istenen videonun
parçaları içinde arar ve en ilgiliden başlayarak döndürür.

Önbellek: aynı video aynı parçalama sürümüyle zaten dizindeyse ve parça
metinleri değişmemişse yeniden gömülmez (planın risk bölümündeki "gömmeler
önbellekte tutulur" kararı). Metin değişikliği her parçanın sha256 özetiyle
(`text_sha256`) anlaşılır.
Bir koleksiyon tek bir gömme modeline aittir; model adı koleksiyonun üst
verisinde tutulur. Farklı bir modelle (farklı vektör boyutu) aynı dizin
açılırsa hata verilir: başka model için başka bir dizin klasörü kullanılmalı.

Bu adımda soru üretimine bağlı değildir (bağlama Aşama 7b'de).
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.services.chunking import CHUNKING_VERSION, Chunk, fixed_size_chunks
from app.services.embeddings import EmbeddingClient
from app.services.transcript import Segment

COLLECTION_NAME = "transcript_chunks"


@dataclass
class RetrievedChunk:
    chunk_index: int
    start_seconds: float
    end_seconds: float
    text: str
    score: float  # kosinüs benzerliği (1 - kosinüs uzaklığı); büyük olan daha ilgili


@dataclass
class IndexResult:
    video_id: str
    chunking: str
    chunk_count: int
    embedded: bool  # False: parçalar zaten dizindeydi, gömme yapılmadı


def text_sha256(text: str) -> str:
    """Parça metninin sha256 özeti; metin değişince yeniden gömmek için."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_id(video_id: str, chunking: str, index: int) -> str:
    """Parça kimliği: video_id + parçalama sürümü + chunk_index."""
    return f"{video_id}:{chunking}:{index}"


class TranscriptIndex:
    """Transkript parçalarının kalıcı ChromaDB dizini."""

    def __init__(self, embedder: EmbeddingClient, path: str | Path | None = None, client=None):
        """`client` verilmezse `path` klasöründe kalıcı bir Chroma istemcisi açılır."""
        if client is None:
            if path is None:
                raise ValueError("path ya da client verilmeli.")
            client = chromadb.PersistentClient(
                path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
            )
        self.embedder = embedder
        # Gömmeleri her zaman kendimiz veriyoruz; Chroma'nın kendi gömme fonksiyonu kullanılmaz
        self._collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": embedder.model},
            embedding_function=None,
        )
        stored_model = (self._collection.metadata or {}).get("embedding_model")
        if stored_model != embedder.model:
            raise ValueError(
                f"Bu dizin {stored_model!r} modeliyle oluşturulmuş; {embedder.model!r} için "
                "başka bir dizin klasörü kullanın."
            )

    @staticmethod
    def _where(video_id: str, chunking: str) -> dict:
        return {"$and": [{"video_id": video_id}, {"chunking": chunking}]}

    def _existing_ids(self, video_id: str, chunking: str) -> list[str]:
        return self._collection.get(where=self._where(video_id, chunking), include=[])["ids"]

    def _existing_hashes(self, video_id: str, chunking: str) -> dict[str, str | None]:
        """Dizindeki parça kimliği → metin özeti (özet yoksa None)."""
        found = self._collection.get(where=self._where(video_id, chunking), include=["metadatas"])
        return {i: (m or {}).get("text_sha256") for i, m in zip(found["ids"], found["metadatas"])}

    def index_chunks(self, chunks: list[Chunk]) -> IndexResult:
        """Bir videonun parçalarını gömüp dizine ekler; zaten dizindeyse yeniden gömmez.

        Parçaların hepsi aynı videoya ve aynı parçalama sürümüne ait olmalı.
        Gömme yalnızca dizindeki parça kimlikleri yeni parçalarla birebir aynı
        VE her parçanın metin özeti (`text_sha256`) aynıysa atlanır. Değilse
        (ör. transkript değişmiş, parça sayısı aynı kalsa bile) o videonun bu
        sürümdeki eski parçaları silinip yenileri yazılır.

        Not: Özet üst verisi eklenmeden önce oluşturulmuş bir dizinde parçaların
        özeti yoktur; bu yüzden böyle bir dizindeki her video bir kez yeniden
        gömülür.
        """
        if not chunks:
            raise ValueError("Dizinlenecek parça yok.")
        video_id, chunking = chunks[0].video_id, chunks[0].chunking
        if any(c.video_id != video_id or c.chunking != chunking for c in chunks):
            raise ValueError("Parçalar aynı videoya ve aynı parçalama sürümüne ait olmalı.")

        ids = [chunk_id(video_id, chunking, c.chunk_index) for c in chunks]
        wanted = {i: text_sha256(c.text) for i, c in zip(ids, chunks)}
        existing = self._existing_hashes(video_id, chunking)
        if existing == wanted:
            return IndexResult(video_id, chunking, len(chunks), embedded=False)
        if existing:
            self._collection.delete(ids=list(existing))

        vectors = self.embedder.embed([c.text for c in chunks])
        self._collection.add(
            ids=ids,
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "video_id": c.video_id,
                    "chunking": c.chunking,
                    "chunk_index": c.chunk_index,
                    "start_seconds": c.start_seconds,
                    "end_seconds": c.end_seconds,
                    "embedding_model": self.embedder.model,
                    "text_sha256": wanted[i],
                }
                for i, c in zip(ids, chunks)
            ],
        )
        return IndexResult(video_id, chunking, len(chunks), embedded=True)

    def index_transcript(self, video_id: str, segments: list[Segment]) -> IndexResult:
        """Temizlenmiş transkript segmentlerini sabit boyutlu parçalara bölüp dizinler."""
        chunks = fixed_size_chunks(segments, video_id)
        if not chunks:
            raise ValueError("Transkript boş; dizinlenecek parça yok.")
        return self.index_chunks(chunks)

    def retrieve(
        self, video_id: str, query: str, k: int = 5, chunking: str = CHUNKING_VERSION
    ) -> list[RetrievedChunk]:
        """Yalnızca `video_id` videosunun parçaları içinde arar; en ilgiliden başlayarak en çok `k` parça döner."""
        if k < 1:
            raise ValueError("k en az 1 olmalı.")
        available = len(self._existing_ids(video_id, chunking))
        if available == 0:
            return []
        query_vector = self.embedder.embed([query])[0]
        result = self._collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, available),
            where=self._where(video_id, chunking),
            include=["documents", "metadatas", "distances"],
        )
        found = [
            RetrievedChunk(
                chunk_index=int(meta["chunk_index"]),
                start_seconds=float(meta["start_seconds"]),
                end_seconds=float(meta["end_seconds"]),
                text=doc,
                score=round(1.0 - float(dist), 6),
            )
            for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
        ]
        # Chroma uzaklığa göre sıralı döndürür; yine de skora göre açıkça sıralanır
        return sorted(found, key=lambda c: c.score, reverse=True)
