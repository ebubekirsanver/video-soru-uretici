"""Aşama 7b · Koşul denemesi 1: iki koşulun (full / rag) gerçek videoda işlerlik denemesi.

Bu bir İŞLERLİK denemesidir, AS1 değerlendirmesi değildir: soru kalitesi
ölçülmez. İstekler API üzerinden FastAPI TestClient ile yapılır (çalışan bir
sunucu gerekmez); çalıştırma kayıtları her zamanki gibi backend/runs altına
yazılır. Gerçek OpenAI çağrısı yapılır; BGE-M3 yerel olarak çalışır.

İki adım, ayrı ayrı çalıştırılır:
    ozet      /api/summary bir kez çağrılır; dönen konuların ilk 6'sı
              asama-7b-kosul-denemesi-1-konular.json dosyasına yazılır.
    kosullar  Aynı konularla /api/questions iki kez çağrılır (full, rag) ve
              sonuçlar yazdırılır; yanıtlar ve kayıttan seçilen alanlar
              asama-7b-kosul-denemesi-1.json dosyasına yazılır.

Çıktı dosyaları "x" kipiyle yazılır: dosya varsa hata verir, üzerine yazılmaz.
Yerel dosya yolu, API anahtarı ya da istek ayrıntısı yazdırılmaz.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-7b-kosul-denemesi-1.py ozet
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-7b-kosul-denemesi-1.py kosullar
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import runs  # noqa: E402

VIDEO_ID = "109kCbVtU1U"
MAX_TOPICS = 6
K = 5
HERE = Path(__file__).resolve().parent
TOPICS_FILE = HERE / "asama-7b-kosul-denemesi-1-konular.json"
RESULTS_FILE = HERE / "asama-7b-kosul-denemesi-1.json"

client = TestClient(app)


def mmss(seconds) -> str:
    if seconds is None:
        return "yok"
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def run_files() -> set[Path]:
    return set(Path(get_settings().runs_dir).glob("*.json"))


def post(path: str, body: dict) -> tuple[dict, dict]:
    """İsteği yapar; yanıtı ve bu istekle yazılan çalıştırma kaydını döndürür."""
    before = run_files()
    r = client.post(path, json=body)
    if r.status_code != 200:
        print(f"HATA {path}: {r.status_code} {r.json().get('detail')}")
        sys.exit(1)
    new = sorted(run_files() - before)
    if len(new) != 1:
        print(f"HATA: {path} için tek bir yeni kayıt bekleniyordu, {len(new)} bulundu (SAVE_RUNS açık mı?)")
        sys.exit(1)
    return r.json(), runs.load_run(new[0])


def step_summary() -> None:
    response, record = post("/api/summary", {"url": VIDEO_ID, "transcript_mode": "clean"})
    titles = [t["title"] for t in response["topics"]]
    selected = titles[:MAX_TOPICS]
    data = {
        "experiment": "asama-7b-kosul-denemesi-1",
        "step": "ozet",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video_id": VIDEO_ID,
        "summary_model": response["model"],
        "summary_topics_all": titles,
        "topics": selected,
        "summary_tokens": sum(c.get("total_tokens") or 0 for c in record["metrics"]["llm_calls"]),
    }
    with TOPICS_FILE.open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Özetten dönen konu sayısı: {len(titles)} · kullanılacak: {len(selected)}")
    for i, t in enumerate(selected, 1):
        print(f"  {i}. {t}")
    if len(titles) > MAX_TOPICS:
        print("Kullanılmayan konular: " + "; ".join(titles[MAX_TOPICS:]))


def condition_report(mode: str, response: dict, record: dict) -> dict:
    tg = record["topic_generation"]
    metrics = record["metrics"]
    calls = metrics["llm_calls"]
    flags = [
        (r["index"], f["rule_id"]) for r in (record.get("writing_check") or {}).get("results", []) for f in r["flags"]
    ]
    print(f"=== Koşul: {mode} ===")
    print(f"İstem: {response['prompt_version']} · model: {response['model']} · k: {tg['k']} "
          f"· parçalama: {tg['chunking']} · gömme: {tg['embedding_model']}")
    print("Konu başına sonuç:")
    for t in tg["per_topic"]:
        line = f"  - {t['topic']}: {t['outcome']} · bağlam {t['context_words']} kelime"
        print(line)
        for c in t["retrieved"] or []:
            print(f"      chunk {c['chunk_index']} · {c['start_seconds']:.2f}–{c['end_seconds']:.2f} sn "
                  f"({mmss(c['start_seconds'])}–{mmss(c['end_seconds'])}) · skor {c['score']:.4f}")
    print(f"Sonuç sayıları: {tg['outcome_counts']}")
    print(f"Dönen soru: {response['returned_count']} / {response['requested_count']} · "
          f"alıntısı transkriptte bulunan: {response['verified_count']}")
    print(f"Yazım kuralı işaretleri: {len(flags)} · " + (
        ", ".join(f"soru {i}: kural {rule}" for i, rule in flags) if flags else "yok"))
    tokens = {k: sum(c.get(k) or 0 for c in calls) for k in ("prompt_tokens", "completion_tokens", "total_tokens")}
    print(f"Toplam süre: {metrics['stages']['total_ms']:.1f} ms · model çağrısı: {len(calls)} · "
          f"token: {tokens['prompt_tokens']} giriş + {tokens['completion_tokens']} çıkış = {tokens['total_tokens']}")
    print("Aşama süreleri (ms): " + ", ".join(f"{k}={v}" for k, v in metrics["stages"].items()))
    print()
    return {
        "mode": mode,
        "response": response,
        "topic_generation": tg,
        "writing_flags": [{"question_index": i, "rule_id": rule} for i, rule in flags],
        "stages": metrics["stages"],
        "llm_calls": calls,
        "tokens": tokens,
        "dropped": metrics.get("dropped"),
    }


def side_by_side(topics: list[str], full: dict, rag: dict) -> None:
    def by_topic(resp):
        return {q["topic"]: q for q in resp["questions"]}

    f, r = by_topic(full), by_topic(rag)
    print("=== Aynı konuda iki koşulun soruları ===")
    print("| Konu | full sorusu | full doğru cevap | rag sorusu | rag doğru cevap | full kaynak | rag kaynak |")
    print("|---|---|---|---|---|---|---|")
    for t in topics:
        fq, rq = f.get(t), r.get(t)
        cell = lambda q, key: (q[key] if q else "—").replace("|", "\\|")  # noqa: E731
        answer = lambda q: q["options"][q["correct_index"]].replace("|", "\\|") if q else "—"  # noqa: E731
        src = lambda q: mmss(q["source_start_seconds"]) if q else "—"  # noqa: E731
        print(f"| {t} | {cell(fq, 'question')} | {answer(fq)} | {cell(rq, 'question')} | {answer(rq)} | {src(fq)} | {src(rq)} |")


def step_conditions() -> None:
    topics_data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    topics = topics_data["topics"]
    print(f"Video: {VIDEO_ID} · konular ({len(topics)}): " + "; ".join(topics))
    print()
    full_resp, full_rec = post("/api/questions", {"url": VIDEO_ID, "context_mode": "full", "topics": topics})
    full = condition_report("full", full_resp, full_rec)
    rag_resp, rag_rec = post("/api/questions", {"url": VIDEO_ID, "context_mode": "rag", "topics": topics, "k": K})
    rag = condition_report("rag", rag_resp, rag_rec)
    side_by_side(topics, full_resp, rag_resp)
    data = {
        "experiment": "asama-7b-kosul-denemesi-1",
        "step": "kosullar",
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video_id": VIDEO_ID,
        "topics": topics,
        "conditions": [full, rag],
    }
    with RESULTS_FILE.open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    steps = {"ozet": step_summary, "kosullar": step_conditions}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        print("Kullanım: asama-7b-kosul-denemesi-1.py ozet | kosullar")
        sys.exit(2)
    steps[sys.argv[1]]()
