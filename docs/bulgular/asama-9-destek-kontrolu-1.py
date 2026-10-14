"""Geçici betik (commit'lenmez): Aşama 9 destek kontrolü denemesi 1.

asama-12d-test-1.json kaydındaki 5 soruyu, soru ÜRETMEDEN, doğrudan
support_check.check_support fonksiyonuna verir ve sonucu
docs/bulgular/asama-9-destek-kontrolu-1.json dosyasına kaydeder.

- Gerçek OpenAI çağrısı yapar: doğrulanmış soru sayısı kadar (bu kayıtta 5).
- Çıktı dosyası zaten varsa hiçbir çağrı yapmadan durur: ilk çalıştırmanın
  sonucu olduğu gibi kalır, üzerine yazılmaz.
- API anahtarı tanımlı değilse hiçbir çağrı yapmadan durur (aksi hâlde 5 soru
  "kontrol edilemedi" olur ve bu sahte bir "ilk çalıştırma" sayılırdı).
- API anahtarı ekrana ya da dosyaya yazılmaz.

Çalıştırma (backend klasöründen, .env proje kökünden okunsun diye):
    cd backend
    .\.venv\Scripts\python.exe -I -X utf8 <bu betiğin yolu>
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/Users/ASUS/Desktop/video-soru-uretici")
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.llm import get_llm  # noqa: E402
from app.services.questions import Question  # noqa: E402
from app.services.support_check import (  # noqa: E402
    SUPPORT_PROMPT_VERSION,
    SYSTEM_PROMPT_FILE,
    USER_PROMPT_FILE,
    check_support,
)

SOURCE = ROOT / "docs/bulgular/asama-12d-test-1.json"
OUTPUT = ROOT / "docs/bulgular/asama-9-destek-kontrolu-1.json"
PROMPTS = ROOT / "backend/app/prompts"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # 1) Ön kontroller: hiçbir çağrı yapılmadan önce
    if OUTPUT.exists():
        print(f"DURDU: {OUTPUT.name} zaten var. İlk çalıştırmanın sonucu değiştirilmez.")
        return 1
    settings = get_settings()
    if not settings.openai_api_key:
        print("DURDU: OPENAI_API_KEY tanımlı değil (.env). Hiçbir çağrı yapılmadı.")
        return 1
    if SUPPORT_PROMPT_VERSION != "support-v1":
        print(f"DURDU: beklenen istem support-v1, bulunan {SUPPORT_PROMPT_VERSION}.")
        return 1

    # 2) Kayıttaki soruları olduğu gibi oku (yeniden üretim yok)
    record = json.loads(SOURCE.read_text(encoding="utf-8"))
    raw_questions = record["response"]["questions"]
    questions = [
        Question(
            question=q["question"],
            options=q["options"],
            correct_index=q["correct_index"],
            explanation=q["explanation"],
            source_quote=q["source_quote"],
            source_start_seconds=q["source_start_seconds"],
            verified=q["verified"],
            quote_match=q["quote_match"],
        )
        for q in raw_questions
    ]
    expected_calls = sum(q.verified for q in questions)
    print(f"{len(questions)} soru okundu, {expected_calls} model çağrısı yapılacak (model: {settings.openai_model}).")

    # 3) Model çağrıları (her doğrulanmış soru için bir tane)
    llm = get_llm()
    started = datetime.now().astimezone()
    results = check_support(questions, llm)
    finished = datetime.now().astimezone()

    # 4) Sonucu olduğu gibi kaydet
    git_head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    output = {
        "experiment": "asama-9-destek-kontrolu-1",
        "note": "Model değerlendirmesidir, kesin doğru değildir. İlk çalıştırmanın sonucu, değiştirilmeden.",
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "model": llm.model,
        "support_prompt_version": SUPPORT_PROMPT_VERSION,
        "code_commit": git_head,
        "prompt_files_sha256": {
            SYSTEM_PROMPT_FILE: sha256(PROMPTS / SYSTEM_PROMPT_FILE),
            USER_PROMPT_FILE: sha256(PROMPTS / USER_PROMPT_FILE),
        },
        "source_file": SOURCE.name,
        "source_sha256": sha256(SOURCE),
        "results": [
            {
                "index": i,
                "question": q.question,
                "correct_answer": q.options[q.correct_index],
                "source_quote": q.source_quote,
                "label": r.label,
                "reason": r.reason,
                "model_raw": r.model_raw,
            }
            for i, (q, r) in enumerate(zip(questions, results), 1)
        ],
    }
    # "x" kipi: arada dosya oluşmuşsa üzerine yazmaz
    with OUTPUT.open("x", encoding="utf-8") as f:
        f.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")

    print(f"Kaydedildi: {OUTPUT}")
    for row in output["results"]:
        print(f"  Soru {row['index']}: {row['label']}  |  {row['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
