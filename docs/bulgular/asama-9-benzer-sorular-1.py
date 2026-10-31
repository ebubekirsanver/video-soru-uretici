"""Aşama 9 · Benzer sorular 1: elle etiketlenmiş 16 çift için gerçek BGE-M3 benzerlik skorları.

Çiftler asama-7b-kosul-denemesi-1.json'daki soruların her koşul içindeki
bütün çiftleridir (Adım 1'deki tabloyla aynı sıra). Etiketler commit'li
asama-9-benzer-sorular-1.md tablosundan okunur. İki skor hesaplanır:
    (a) soru metni + doğru cevap (similarity-v1'in gömdüğü metin, `pair_text`)
    (b) yalnızca soru metni
Model (OpenAI) çağrısı yapılmaz; BGE-M3 yerelde çalışır. Eşik önerilmez.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-9-benzer-sorular-1.py
"""

import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.embeddings import SentenceTransformerClient  # noqa: E402
from app.services.similarity import pair_scores, pair_text  # noqa: E402

HERE = Path(__file__).resolve().parent
QUESTIONS_FILE = HERE / "asama-7b-kosul-denemesi-1.json"
LABELS_FILE = HERE / "asama-9-benzer-sorular-1.md"


def read_labels() -> dict[int, str]:
    labels = {}
    for line in LABELS_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (\d+) \| (?:full|rag) \|.*\| (aynı bilgi|farklı) \|$", line.strip())
        if m:
            labels[int(m.group(1))] = m.group(2)
    return labels


def main() -> None:
    data = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    labels = read_labels()
    embedder = SentenceTransformerClient(get_settings().embedding_model)
    print(f"Gömme modeli: {embedder.model} · etiketli çift: {len(labels)}")
    print()
    print("| Çift | Koşul | Sorular | (a) soru + doğru cevap | (b) yalnızca soru | Kullanıcı etiketi |")
    print("|---|---|---|---|---|---|")

    rows, n = [], 0
    for cond in data["conditions"]:
        qs = cond["response"]["questions"]
        with_answer = pair_scores([pair_text(q["question"], q["options"][q["correct_index"]]) for q in qs], embedder)
        question_only = pair_scores([q["question"] for q in qs], embedder)
        score_a = {(p.a, p.b): p.score for p in with_answer}
        score_b = {(p.a, p.b): p.score for p in question_only}
        for i, j in itertools.combinations(range(1, len(qs) + 1), 2):
            n += 1
            label = labels[n]
            rows.append((n, label, score_a[(i, j)], score_b[(i, j)]))
            print(f"| {n} | {cond['mode']} | S{i}–S{j} | {score_a[(i, j)]:.4f} | {score_b[(i, j)]:.4f} | {label} |")

    print()
    for key, name in ((2, "(a) soru + doğru cevap"), (3, "(b) yalnızca soru")):
        same = [r[key] for r in rows if r[1] == "aynı bilgi"]
        diff = [r[key] for r in rows if r[1] == "farklı"]
        separated = "evet" if min(same) > max(diff) else "hayır"
        print(f"{name}: 'aynı bilgi' en düşük = {min(same):.4f} ({len(same)} çift) · "
              f"'farklı' en yüksek = {max(diff):.4f} ({len(diff)} çift) · ayrışıyor mu: {separated}")


if __name__ == "__main__":
    main()
