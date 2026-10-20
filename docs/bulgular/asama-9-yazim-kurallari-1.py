"""Aşama 9 · Yazım kuralları değerlendirmesi 1: commit'li sorular üzerinde writing_check.

Model çağrısı yapmaz. docs/bulgular altındaki JSON dosyalarından soru listesi
içerenleri (`response.questions` ya da en üstte `questions`) okur; deney
sonucu dosyaları (ör. destek kontrolü) soru listesi içermediği için atlanır.
Aynı soru metni (normalize sonrası) bir kez sayılır: dosya adı sırasına göre
ilk görülen tutulur. Sorular kayıttaki son hâlleriyle (karıştırılmış seçenekler
ve correct_index) kontrol edilir.

Çıktı "x" kipiyle yazılır: dosya varsa hata verir, sonuç üzerine yazılmaz.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-9-yazim-kurallari-1.py
"""

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.quotes import normalize  # noqa: E402
from app.services.writing_check import RULE_NAMES, RULES_VERSION, check_question  # noqa: E402

BULGULAR = ROOT / "docs" / "bulgular"
OUTPUT = BULGULAR / "asama-9-yazim-kurallari-1.json"


def question_set(data: dict) -> tuple[str | None, list] | None:
    """Dosya bir soru listesi içeriyorsa (video_id, sorular) döndürür."""
    body = data.get("response", data)
    if not isinstance(body, dict) or not isinstance(body.get("questions"), list):
        return None
    return body.get("video_id"), body["questions"]


def main() -> None:
    sources, results, seen = [], [], set()
    duplicates = 0
    for path in sorted(BULGULAR.glob("*.json")):
        if path == OUTPUT:
            continue
        raw = path.read_bytes()
        found = question_set(json.loads(raw.decode("utf-8")))
        if found is None:
            continue
        video_id, questions = found
        sources.append(
            {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "questions_in_file": len(questions)}
        )
        for i, q in enumerate(questions, 1):
            key = normalize(q["question"])
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            flags = check_question(q["question"], q["options"], q["correct_index"])
            results.append(
                {
                    "file": path.name,
                    "video_id": video_id,
                    "index_in_file": i,
                    "question": q["question"],
                    "options": q["options"],
                    "correct_index": q["correct_index"],
                    "correct_option": q["options"][q["correct_index"]],
                    "flags": [{"rule_id": f.rule_id, "rule_name": f.rule_name, "detail": f.detail} for f in flags],
                }
            )

    counts = Counter(f["rule_id"] for r in results for f in r["flags"])
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    output = {
        "experiment": "asama-9-yazim-kurallari-1",
        "note": "Yalnızca kodla yapılan kontrol; model çağrısı yok. Etiketler .md dosyasında elle verilecek.",
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rules_version": RULES_VERSION,
        "code_commit": commit,
        "source_files": sources,
        "unique_questions": len(results),
        "duplicates_skipped": duplicates,
        "flag_counts": {str(rule_id): counts.get(rule_id, 0) for rule_id in sorted(RULE_NAMES)},
        "flagged_questions": sum(1 for r in results if r["flags"]),
        "results": results,
    }
    with OUTPUT.open("x", encoding="utf-8") as f:
        f.write(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"{len(results)} benzersiz soru, {duplicates} tekrar atlandı, {output['flagged_questions']} işaretli soru")
    print("Kural başına işaret:", output["flag_counts"])


if __name__ == "__main__":
    main()
