r"""Geçici betik: Aşama 9 destek kontrolü denemesi 2 (çalıştırıldığı hâliyle docs/bulgular'a eklenecek).

Test 2 kayıtlarındaki 9 soruyu (asama-6-test-2-kemosentez.json: 4,
asama-6-test-2-tarih.json: 5), soru ÜRETMEDEN, doğrudan
support_check.check_support fonksiyonuna verir ve sonucu
docs/bulgular/asama-9-destek-kontrolu-2.json dosyasına kaydeder.

- Gerçek OpenAI çağrısı yapar: doğrulanmış soru sayısı kadar (bu kayıtlarda 9).
- Çıktı dosyası zaten varsa hiçbir çağrı yapmadan durur: ilk çalıştırmanın
  sonucu olduğu gibi kalır, üzerine yazılmaz.
- API anahtarı tanımlı değilse hiçbir çağrı yapmadan durur.
- İstem support-v1 değilse hiçbir çağrı yapmadan durur.
- Kayıtlardaki bir soruda beklenen alan eksikse hiçbir çağrı yapmadan durur.
- API anahtarı ekrana ya da dosyaya yazılmaz.

Eski kayıt biçimi (Test 2, record_version yok) için uyarlama:
- Kayıtlarda record_version ve quote_audit yok; bunlar okunmaz. Soru
  alanları (question, options, correct_index, explanation, source_quote,
  source_start_seconds, verified, quote_match) yeni biçimle aynıdır ve her
  soru için varlıkları çağrıdan önce denetlenir.
- Modelin özgün alıntısı (model_quote) bu kayıtlarda yok; check_support zaten
  yalnızca source_quote'u (transkriptteki hâli) kullanır, bu yüzden davranış
  değişmez. Çıktıya her soru için "model_quote_available": false yazılır.
- İki kaynak dosya okunur; her sonuç video ve kaynak dosya adıyla birlikte,
  "kemosentez S1" gibi bir anahtarla kaydedilir.

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

# (kısa ad, kaynak dosya) — sıra tablodaki sırayla aynı
SOURCES = [
    ("kemosentez", ROOT / "docs/bulgular/asama-6-test-2-kemosentez.json"),
    ("tarih", ROOT / "docs/bulgular/asama-6-test-2-tarih.json"),
]
OUTPUT = ROOT / "docs/bulgular/asama-9-destek-kontrolu-2.json"
PROMPTS = ROOT / "backend/app/prompts"
REQUIRED_FIELDS = [
    "question", "options", "correct_index", "explanation",
    "source_quote", "source_start_seconds", "verified", "quote_match",
]


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

    # 2) Kayıtlardaki soruları olduğu gibi oku (yeniden üretim yok); alanları denetle
    items = []  # (anahtar, video_id, kaynak adı, Question)
    for short, path in SOURCES:
        record = json.loads(path.read_text(encoding="utf-8"))
        response = record["response"]
        for i, q in enumerate(response["questions"], 1):
            missing = [k for k in REQUIRED_FIELDS if k not in q]
            if missing:
                print(f"DURDU: {path.name} soru {i} içinde eksik alan: {missing}. Hiçbir çağrı yapılmadı.")
                return 1
            question = Question(
                question=q["question"],
                options=q["options"],
                correct_index=q["correct_index"],
                explanation=q["explanation"],
                source_quote=q["source_quote"],
                source_start_seconds=q["source_start_seconds"],
                verified=q["verified"],
                quote_match=q["quote_match"],
            )
            items.append((f"{short} S{i}", response["video_id"], path.name, question))

    questions = [item[3] for item in items]
    expected_calls = sum(q.verified for q in questions)
    print(f"{len(questions)} soru okundu, {expected_calls} model çağrısı yapılacak (model: {settings.openai_model}).")

    # 3) Model çağrıları (her doğrulanmış soru için bir tane), tek seferde
    llm = get_llm()
    started = datetime.now().astimezone()
    results = check_support(questions, llm)
    finished = datetime.now().astimezone()

    # 4) Sonucu olduğu gibi kaydet
    git_head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    output = {
        "experiment": "asama-9-destek-kontrolu-2",
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
        "source_files": [{"name": path.name, "sha256": sha256(path)} for _, path in SOURCES],
        "results": [
            {
                "key": key,
                "video_id": video_id,
                "source_file": source_name,
                "question": q.question,
                "correct_answer": q.options[q.correct_index],
                "source_quote": q.source_quote,
                "quote_match": q.quote_match,
                "model_quote_available": False,  # eski kayıt biçimi: modelin özgün alıntısı yok
                "label": r.label,
                "reason": r.reason,
                "model_raw": r.model_raw,
            }
            for (key, video_id, source_name, q), r in zip(items, results)
        ],
    }
    # "x" kipi: arada dosya oluşmuşsa üzerine yazmaz
    with OUTPUT.open("x", encoding="utf-8") as f:
        f.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")

    print(f"Kaydedildi: {OUTPUT}")
    for row in output["results"]:
        print(f"  {row['key']}: {row['label']}  |  {row['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
