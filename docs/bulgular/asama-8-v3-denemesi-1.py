"""Aşama 8 · questions-v3 denemesi 1: konu çıkarma + Bloom eşlemesi + benzerlik işareti, iki koşulda.

Bu bir İŞLERLİK denemesidir: soru kalitesi ve Bloom uyumu ölçülmez. İstekler
API üzerinden FastAPI TestClient ile yapılır (çalışan bir sunucu gerekmez);
çalıştırma kayıtları her zamanki gibi backend/runs altına yazılır. Gerçek
OpenAI çağrısı yapılır; BGE-M3 yerel olarak çalışır.

İki adım, ayrı ayrı çalıştırılır:
    konular   /api/topics bir kez çağrılır (count 6); konular ve tohumlu düzey
              eşlemesi asama-8-v3-denemesi-1-konular.json dosyasına yazılır.
    kosullar  Aynı 6 konu (text) ve aynı bloom_levels ile /api/questions önce
              full, sonra rag (k=5) çağrılır; sonuçlar yazdırılır ve
              asama-8-v3-denemesi-1.json dosyasına yazılır.

Çıktı dosyaları "x" kipiyle yazılır: dosya varsa hata verir, üzerine yazılmaz.
Yerel dosya yolu ve API anahtarı yazdırılmaz.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-8-v3-denemesi-1.py konular
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\asama-8-v3-denemesi-1.py kosullar
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
from app.services.bloom import seeded_mapping  # noqa: E402

VIDEO_ID = "109kCbVtU1U"
TOPIC_COUNT = 6
K = 5
HERE = Path(__file__).resolve().parent
TOPICS_FILE = HERE / "asama-8-v3-denemesi-1-konular.json"
RESULTS_FILE = HERE / "asama-8-v3-denemesi-1.json"

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


def step_topics() -> None:
    response, record = post("/api/topics", {"url": VIDEO_ID, "count": TOPIC_COUNT})
    topics = response["topics"]
    extraction = record["topic_extraction"]
    print(f"Konu çıkarma: {response['prompt_version']} · model: {response['model']} · "
          f"istenen {extraction['requested_count']} · dönen {extraction['returned_count']} · "
          f"eksik {extraction['shortfall']} · atılan {extraction['dropped']}")
    levels = seeded_mapping(VIDEO_ID, len(topics)) if len(topics) == TOPIC_COUNT else None
    for i, t in enumerate(topics):
        level = levels[i] if levels else "—"
        print(f"  {i + 1}. [{level}] {t['title']} — {t['description']}")
    if levels is None:
        print(f"Tohumlu eşleme yapılamadı: {len(topics)} konu döndü, {TOPIC_COUNT} gerekli.")
    calls = record["metrics"]["llm_calls"]
    print(f"Model çağrısı: {len(calls)} · token: {sum(c.get('total_tokens') or 0 for c in calls)}")
    data = {
        "experiment": "asama-8-v3-denemesi-1",
        "step": "konular",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video_id": VIDEO_ID,
        "topics_prompt_version": response["prompt_version"],
        "model": response["model"],
        "topics": topics,
        "bloom_levels": levels,
        "bloom_mapping_source": "seeded" if levels else None,
        "topic_extraction": extraction,
    }
    with TOPICS_FILE.open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


def condition_report(mode: str, response: dict, record: dict) -> dict:
    tg = record["topic_generation"]
    metrics = record["metrics"]
    calls = metrics["llm_calls"]
    by_topic = {q["topic"]: q for q in response["questions"]}
    reasons = {r["topic"]: r["reasoning"] for r in tg["questions_reasoning"]}
    flags = [(r["index"], f["rule_id"]) for r in (record.get("writing_check") or {}).get("results", []) for f in r["flags"]]
    sim = record.get("similarity_check") or {}

    print(f"=== Koşul: {mode} ===")
    print(f"İstem: {response['prompt_version']} · model: {response['model']} · k: {tg['k']} "
          f"· parçalama: {tg['chunking']} · gömme: {tg['embedding_model']} · eşleme: {tg['bloom_mapping_source']}")
    for n, t in enumerate(tg["per_topic"], 1):
        q = by_topic.get(t["topic"])
        print(f"- Konu {n} [{t['bloom_level']}] {t['outcome']} · bağlam {t['context_words']} kelime")
        print(f"    konu: {t['topic']}")
        if q:
            answer = q["options"][q["correct_index"]]
            print(f"    soru: {q['question']}")
            print(f"    doğru cevap: {answer} · kaynak: {mmss(q['source_start_seconds'])} · "
                  f"alıntı bulundu: {'evet' if q['verified'] else 'hayır'}")
            print(f"    reasoning: {reasons.get(t['topic'], '')}")
        for c in t["retrieved"] or []:
            print(f"    parça {c['chunk_index']} · {c['start_seconds']:.2f}–{c['end_seconds']:.2f} sn "
                  f"({mmss(c['start_seconds'])}–{mmss(c['end_seconds'])}) · skor {c['score']:.4f}")
    print(f"Sonuç sayıları: {tg['outcome_counts']} · dönen soru: {response['returned_count']} / "
          f"{response['requested_count']} · alıntısı bulunan: {response['verified_count']}")
    pairs = sim.get("flagged_pairs", [])
    print(f"Benzerlik ({sim.get('rules_version')}, eşik {sim.get('threshold')}): işaretli çift {len(pairs)}"
          + (f" · hata: {sim['error']}" if sim.get("error") else ""))
    for p in pairs:
        print(f"    S{p['a']}–S{p['b']} · skor {p['score']:.4f}")
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
        "similarity_check": sim,
        "writing_flags": [{"question_index": i, "rule_id": rule} for i, rule in flags],
        "stages": metrics["stages"],
        "llm_calls": calls,
        "tokens": tokens,
        "dropped": metrics.get("dropped"),
    }


def side_by_side(texts: list[str], levels: list[str], titles: list[str], full: dict, rag: dict) -> None:
    f = {q["topic"]: q for q in full["questions"]}
    r = {q["topic"]: q for q in rag["questions"]}
    esc = lambda s: s.replace("|", "\\|")  # noqa: E731
    cell = lambda q: esc(q["question"]) if q else "—"  # noqa: E731
    ans = lambda q: esc(q["options"][q["correct_index"]]) if q else "—"  # noqa: E731
    print("=== Aynı konuda iki koşulun soruları ===")
    print("| Konu | Hedef düzey | full sorusu | full doğru cevap | rag sorusu | rag doğru cevap |")
    print("|---|---|---|---|---|---|")
    for text, level, title in zip(texts, levels, titles):
        print(f"| {esc(title)} | {level} | {cell(f.get(text))} | {ans(f.get(text))} | {cell(r.get(text))} | {ans(r.get(text))} |")


def step_conditions() -> None:
    data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    if not data["bloom_levels"]:
        print("HATA: konu dosyasında düzey eşlemesi yok (6 konu dönmemiş).")
        sys.exit(1)
    texts = [t["text"] for t in data["topics"]]
    titles = [t["title"] for t in data["topics"]]
    levels = data["bloom_levels"]
    print(f"Video: {VIDEO_ID} · {len(texts)} konu · düzeyler: {', '.join(levels)}")
    print()
    base = {"url": VIDEO_ID, "topics": texts, "bloom_levels": levels}
    full_resp, full_rec = post("/api/questions", {**base, "context_mode": "full"})
    full = condition_report("full", full_resp, full_rec)
    rag_resp, rag_rec = post("/api/questions", {**base, "context_mode": "rag", "k": K})
    rag = condition_report("rag", rag_resp, rag_rec)
    side_by_side(texts, levels, titles, full_resp, rag_resp)
    out = {
        "experiment": "asama-8-v3-denemesi-1",
        "step": "kosullar",
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video_id": VIDEO_ID,
        "topics": texts,
        "bloom_levels": levels,
        "conditions": [full, rag],
    }
    with RESULTS_FILE.open("x", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    steps = {"konular": step_topics, "kosullar": step_conditions}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        print("Kullanım: asama-8-v3-denemesi-1.py konular | kosullar")
        sys.exit(2)
    steps[sys.argv[1]]()
