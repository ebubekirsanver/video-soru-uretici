r"""Geçici betik: Aşama 9 destek kontrolü denemesi 3 (çalıştırıldığı hâliyle docs/bulgular'a eklenecek).

Genelleme denemesi 1'in dört kaydındaki (genelleme-1-matematik/edebiyat/
python/ingilizce.json) soruları, soru ÜRETMEDEN, doğrudan
support_check.check_support fonksiyonuna verir ve sonucu
docs/bulgular/asama-9-destek-kontrolu-3.json dosyasına kaydeder.

- Gerçek OpenAI çağrısı yapar: doğrulanmış soru sayısı kadar (bu kayıtlarda 18).
- Çıktı dosyası zaten varsa hiçbir çağrı yapmadan durur: ilk çalıştırmanın
  sonucu olduğu gibi kalır, üzerine yazılmaz.
- API anahtarı tanımlı değilse hiçbir çağrı yapmadan durur.
- İstem support-v1 değilse hiçbir çağrı yapmadan durur.
- Kayıtlardaki bir soruda beklenen alan eksikse hiçbir çağrı yapmadan durur.
- API anahtarı ekrana ya da dosyaya yazılmaz.

Yeni kayıt biçimi (record_version 3, quote_audit var) için uyarlama:
- Her kaynağın record_version'ı 3 ve quote_audit listesi olmalı; değilse
  hiçbir çağrı yapmadan durur.
- quote_audit'teki modelin özgün alıntısı (model_quote) ve kırpılan
  kelimeler (trimmed_head, trimmed_tail) her soruya index ve soru metniyle
  eşlenir; eşleşmezse hiçbir çağrı yapmadan durur. Bu bilgiler yalnızca
  çıktıya yazılır, modele gitmez: check_support yine yalnızca source_quote'u
  (transkriptteki hâli) kullanır. Çıktıda "model_quote_available": true olur.
- Kayıtlardaki 20 sorunun hepsi, uç noktadaki gibi, check_support'a verilir;
  alıntısı doğrulanamayan 2 soru için çağrı yapılmaz ("kontrol edilmedi").
  Doğrulanmış soru sayısı 18 değilse hiçbir çağrı yapmadan durur.
- Yapılan gerçek çağrı sayısı sayılır ve çıktıya "calls_made" olarak yazılır.

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
    ("matematik", ROOT / "docs/bulgular/genelleme-1-matematik.json"),
    ("edebiyat", ROOT / "docs/bulgular/genelleme-1-edebiyat.json"),
    ("python", ROOT / "docs/bulgular/genelleme-1-python.json"),
    ("ingilizce", ROOT / "docs/bulgular/genelleme-1-ingilizce.json"),
]
OUTPUT = ROOT / "docs/bulgular/asama-9-destek-kontrolu-3.json"
PROMPTS = ROOT / "backend/app/prompts"
REQUIRED_FIELDS = [
    "question", "options", "correct_index", "explanation",
    "source_quote", "source_start_seconds", "verified", "quote_match",
]
EXPECTED_CALLS = 18


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CountingLLM:
    """Gerçek istemciyi sarar; yalnızca yapılan çağrı sayısını sayar, içeriğe dokunmaz."""

    def __init__(self, inner):
        self.inner = inner
        self.model = inner.model
        self.calls = 0

    def complete(self, system, user, json_mode=False):
        self.calls += 1
        return self.inner.complete(system=system, user=user, json_mode=json_mode)


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

    # 2) Kayıtlardaki soruları olduğu gibi oku (yeniden üretim yok); biçimi ve alanları denetle
    items = []  # (anahtar, video_id, kaynak adı, Question, quote_audit satırı)
    for short, path in SOURCES:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("record_version") != 3 or not isinstance(record.get("quote_audit"), list):
            print(f"DURDU: {path.name} beklenen biçimde değil (record_version 3 ve quote_audit gerekli). Hiçbir çağrı yapılmadı.")
            return 1
        audit = {a.get("index"): a for a in record["quote_audit"]}
        response = record["response"]
        for i, q in enumerate(response["questions"], 1):
            missing = [k for k in REQUIRED_FIELDS if k not in q]
            if missing:
                print(f"DURDU: {path.name} soru {i} içinde eksik alan: {missing}. Hiçbir çağrı yapılmadı.")
                return 1
            a = audit.get(i)
            if a is None or a.get("question") != q["question"] or "model_quote" not in a:
                print(f"DURDU: {path.name} soru {i} için quote_audit satırı eşleşmedi. Hiçbir çağrı yapılmadı.")
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
            items.append((f"{short} S{i}", response["video_id"], path.name, question, a))

    questions = [item[3] for item in items]
    expected_calls = sum(q.verified for q in questions)
    if expected_calls != EXPECTED_CALLS:
        print(f"DURDU: beklenen {EXPECTED_CALLS} doğrulanmış soru, bulunan {expected_calls}. Hiçbir çağrı yapılmadı.")
        return 1
    print(f"{len(questions)} soru okundu, {expected_calls} model çağrısı yapılacak (model: {settings.openai_model}).")

    # 3) Model çağrıları (her doğrulanmış soru için bir tane), tek seferde
    llm = CountingLLM(get_llm())
    started = datetime.now().astimezone()
    results = check_support(questions, llm)
    finished = datetime.now().astimezone()

    # 4) Sonucu olduğu gibi kaydet
    git_head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    output = {
        "experiment": "asama-9-destek-kontrolu-3",
        "note": "Model değerlendirmesidir, kesin doğru değildir. İlk çalıştırmanın sonucu, değiştirilmeden.",
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "model": llm.model,
        "support_prompt_version": SUPPORT_PROMPT_VERSION,
        "code_commit": git_head,
        "calls_expected": expected_calls,
        "calls_made": llm.calls,
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
                "verified": q.verified,
                "quote_match": q.quote_match,
                "model_quote_available": True,  # yeni kayıt biçimi: quote_audit'ten
                "model_quote": a["model_quote"],
                "trimmed_head": a.get("trimmed_head", []),
                "trimmed_tail": a.get("trimmed_tail", []),
                "label": r.label,
                "reason": r.reason,
                "model_raw": r.model_raw,
            }
            for (key, video_id, source_name, q, a), r in zip(items, results)
        ],
    }
    # "x" kipi: arada dosya oluşmuşsa üzerine yazmaz
    with OUTPUT.open("x", encoding="utf-8") as f:
        f.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")

    print(f"Kaydedildi: {OUTPUT} (yapılan çağrı: {llm.calls})")
    for row in output["results"]:
        print(f"  {row['key']}: {row['label']}  |  {row['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
