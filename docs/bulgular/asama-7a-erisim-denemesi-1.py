"""Aşama 7a · Erişim denemesi 1: BGE-M3 + ChromaDB ile ilk gerçek erişim.

Kemosentez videosunun (109kCbVtU1U) temiz transkripti sabit boyutlu parçalara
bölünür (fixed-150-30), BGE-M3 ile gömülüp backend/chroma dizinine yazılır ve
üç sorgu için retrieve(k=3) çalıştırılır. OpenAI çağrısı yapılmaz; YouTube'dan
transkript çekilir, BGE-M3 ilk kullanımda Hugging Face'ten indirilir.

Sorgular ve beklenen zamanlar betik çalıştırılmadan önce .md dosyasına yazıldı.
Çıktıda yerel dosya yolu yazdırılmaz.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-7a-erisim-denemesi-1.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.chunking import CHUNKING_VERSION  # noqa: E402
from app.services.embeddings import SentenceTransformerClient  # noqa: E402
from app.services.retrieval import TranscriptIndex  # noqa: E402
from app.services.text_clean import clean_transcript  # noqa: E402
from app.services.transcript import fetch_transcript  # noqa: E402

VIDEO_ID = "109kCbVtU1U"
K = 3
# (etiket, sorgu, beklenen saniye ya da None)
QUERIES = [
    ("a", "Hidrotermal bacalar nerede bulunur?", 124),
    ("b", "Kemosentetik canlıların hücre yapısı nasıldır, prokaryot mudur?", 435),
    ("c", "Kemosentez nedir ve fotosentezden farkı nedir?", None),
]


def mmss(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def main() -> None:
    settings = get_settings()
    transcript = clean_transcript(fetch_transcript(VIDEO_ID, settings.transcript_language_list))
    print(f"Video: {VIDEO_ID} · dil: {transcript.language} · segment: {len(transcript.segments)} "
          f"· süre: {transcript.duration_seconds} sn ({mmss(transcript.duration_seconds)})")

    embedder = SentenceTransformerClient(settings.embedding_model)
    t0 = time.perf_counter()
    embedder._load()  # ilk model yükleme (indirme dahil olabilir)
    load_seconds = time.perf_counter() - t0
    print(f"Gömme modeli: {embedder.model} · ilk yükleme süresi: {load_seconds:.1f} sn")

    index = TranscriptIndex(embedder, path=settings.chroma_dir)
    t0 = time.perf_counter()
    result = index.index_transcript(VIDEO_ID, transcript.segments)
    index_seconds = time.perf_counter() - t0
    print(f"Parçalama: {CHUNKING_VERSION} · toplam parça: {result.chunk_count} "
          f"· dizinleme süresi: {index_seconds:.1f} sn · yeni gömme yapıldı: {result.embedded}")

    for label, query, expected in QUERIES:
        print()
        print(f"Sorgu {label}) {query}")
        found = index.retrieve(VIDEO_ID, query, k=K)
        for rank, c in enumerate(found, 1):
            snippet = c.text[:200].replace("\n", " ")
            print(f"  {rank}. chunk_index={c.chunk_index} · {c.start_seconds:.2f}–{c.end_seconds:.2f} sn "
                  f"({mmss(c.start_seconds)}–{mmss(c.end_seconds)}) · skor={c.score:.4f}")
            print(f"     {snippet}")
        if expected is None:
            print("  Ölçüt: kullanıcı değerlendirecek")
            continue
        inside = [c.start_seconds <= expected <= c.end_seconds for c in found]
        first = "evet" if inside and inside[0] else "hayır"
        line = f"  Ölçüt: beklenen {expected} sn ilk sıradaki parçanın aralığında mı: {first}"
        if first == "hayır":
            rank = next((i for i, ok in enumerate(inside, 1) if ok), None)
            line += f" · ilk {K} içinde mi: " + (f"evet ({rank}. sırada)" if rank else "hayır")
        print(line)


if __name__ == "__main__":
    main()
