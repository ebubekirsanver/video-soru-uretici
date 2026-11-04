"""Pilot üretim 1: 6 pilot videoda iki koşul (full / rag), questions-v3.

Bu bir İŞLERLİK ve ÖN GÖZLEM çalışmasıdır: kalite, kaynağa dayalılık ve Bloom
uyumu ölçülmez. İstekler API üzerinden FastAPI TestClient ile yapılır (çalışan
bir sunucu gerekmez); çalıştırma kayıtları backend/runs altına yazılır. Gerçek
OpenAI çağrısı yapılır; BGE-M3 yerel olarak çalışır.

Her video için: /api/topics (count 6), sonra aynı konu metinleri ve aynı
bloom_levels ile önce full, sonra rag (k=5). Bir video hata verirse hata video
dosyasına yazılır ve sonrakine geçilir; yeniden deneme yapılmaz. Video dosyası
varsa o video atlanır (üzerine yazılmaz).

Ek çalıştırma (edebiyat ve Python): tamamlanan videoların dosyaları durduğu için
yalnızca bu ikisi işlenir; özet pilot-1-ek-ozet.json dosyasına yazılır. Transkript
önbellek üzerinden alınır, böylece video başına tek YouTube isteği yapılır.

Maliyet yalnızca bu betikte, sabit liste fiyatıyla hesaplanır; kod ve kayıt
biçimi değişmez. Tam transkriptler depoya girmez: argümanla verilen klasöre
yazılır (altyazı hatası adaylarını okumak için).

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\pilot-1\\pilot-1.py <transkript-klasörü>
"""

import hashlib
import json
import random
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import runs  # noqa: E402
from app.services.bloom import seeded_mapping  # noqa: E402
from app.services.chunking import fixed_size_chunks  # noqa: E402
from app.services.embeddings import get_embedder  # noqa: E402
from app.services.metrics import scrub_secrets  # noqa: E402
from app.services.text_clean import clean_transcript  # noqa: E402
from app.services.transcript import fetch_transcript  # noqa: E402
from app.services.transcript_cache import load_transcript  # noqa: E402

VIDEOS = [
    ("biyoloji", "109kCbVtU1U"),
    ("tarih", "aaCHLYO3Fzg"),
    ("matematik", "edSvMQ77TmU"),
    ("ingilizce", "FetnCoTS9qY"),
    ("edebiyat", "fgOxbhEMnQQ"),
    ("python", "CEr_UiR4Gvk"),
]
TOPIC_COUNT = 6
K = 5
SAMPLE_COUNT = 3
PRICE_IN = 0.15  # USD / 1M token, kullanıcının verdiği liste fiyatı
PRICE_OUT = 0.60
HERE = Path(__file__).resolve().parent

client = TestClient(app)


class PilotError(Exception):
    pass


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
        raise PilotError(f"{path}: {r.status_code} {r.json().get('detail')}")
    new = sorted(run_files() - before)
    if len(new) != 1:
        raise PilotError(f"{path}: tek bir yeni kayıt bekleniyordu, {len(new)} bulundu (SAVE_RUNS açık mı?)")
    return r.json(), runs.load_run(new[0])


def oembed(url: str) -> dict:
    """Video adı ve kanal adı; alınamazsa None."""
    query = urllib.parse.urlencode({"url": url, "format": "json"})
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?{query}", timeout=30) as f:
            data = json.loads(f.read().decode("utf-8"))
        return {"title": data.get("title"), "channel": data.get("author_name")}
    except Exception as exc:  # oEmbed alınamazsa deneme durmaz
        print(f"  oEmbed alınamadı: {type(exc).__name__}")
        return {"title": None, "channel": None}


def tokens_of(calls: list[dict]) -> dict:
    t = {"prompt_tokens": sum(c.get("prompt_tokens") or 0 for c in calls),
         "completion_tokens": sum(c.get("completion_tokens") or 0 for c in calls)}
    t["total_tokens"] = t["prompt_tokens"] + t["completion_tokens"]
    t["cost_usd"] = round((t["prompt_tokens"] * PRICE_IN + t["completion_tokens"] * PRICE_OUT) / 1_000_000, 6)
    return t


def sample_order(video_id: str) -> list[tuple[str, int]]:
    """Plandaki sabit seçim sırası: 12 soru yeri, video_id'den türetilen tohumla karıştırılmış."""
    seed = int.from_bytes(hashlib.sha256(f"pilot-1-ornek:{video_id}".encode("utf-8")).digest()[:8], "big")
    slots = [("full", i) for i in range(1, 7)] + [("rag", i) for i in range(1, 7)]
    random.Random(seed).shuffle(slots)
    return slots


def run_condition(mode: str, url: str, texts: list[str], levels: list[str]) -> dict:
    body = {"url": url, "topics": texts, "bloom_levels": levels, "context_mode": mode}
    if mode == "rag":
        body["k"] = K
    response, record = post("/api/questions", body)
    tg = record["topic_generation"]
    metrics = record["metrics"]
    flags = [{"question_index": r["index"], "rule_id": f["rule_id"]}
             for r in (record.get("writing_check") or {}).get("results", []) for f in r["flags"]]
    similar = (record.get("similarity_check") or {})
    pairs = similar.get("flagged_pairs", [])
    tokens = tokens_of(metrics["llm_calls"])
    stages = metrics["stages"]

    print(f"  [{mode}] sonuçlar: " + ", ".join(t["outcome"] for t in tg["per_topic"]) + f" · {tg['outcome_counts']}")
    print(f"  [{mode}] dönen {response['returned_count']}/{response['requested_count']} · "
          f"alıntısı bulunan {response['verified_count']} · benzer çift {len(pairs)}"
          + (f" (hata: {similar['error']})" if similar.get("error") else "")
          + f" · yazım işareti {len(flags)} ({', '.join(str(f['rule_id']) for f in flags) or 'yok'})")
    line = f"  [{mode}] süre {stages['total_ms'] / 1000:.1f} sn"
    if mode == "rag":
        line += f" (dizinleme {stages.get('index_ms', 0) / 1000:.1f} sn, erişim {stages.get('retrieval_ms', 0) / 1000:.1f} sn)"
    print(line + f" · çağrı {len(metrics['llm_calls'])} · token {tokens['prompt_tokens']} girdi + "
                 f"{tokens['completion_tokens']} çıktı · maliyet {tokens['cost_usd']:.6f} USD")
    return {
        "mode": mode,
        "response": response,
        "topic_generation": tg,
        "similarity_check": similar,
        "writing_flags": flags,
        "stages": stages,
        "llm_calls": metrics["llm_calls"],
        "tokens": tokens,
        "dropped": metrics.get("dropped"),
    }


def pick_samples(video_id: str, texts: list[str], conditions: dict) -> list[dict]:
    by_topic = {mode: {q["topic"]: q for q in c["response"]["questions"]} for mode, c in conditions.items()}
    samples = []
    for mode, position in sample_order(video_id):
        q = by_topic[mode].get(texts[position - 1])
        if q is None:
            continue
        samples.append({
            "slot": f"{mode}-{position}",
            "mode": mode,
            "bloom_level": q["bloom_level"],
            "question": q["question"],
            "options": q["options"],
            "correct_answer": q["options"][q["correct_index"]],
            "source_quote": q["source_quote"],
            "source_time": mmss(q["source_start_seconds"]),
            "verified": q["verified"],
        })
        if len(samples) == SAMPLE_COUNT:
            break
    return samples


def process(name: str, video_id: str, transcript_dir: Path) -> dict | None:
    out = HERE / f"pilot-1-{name}.json"
    print(f"=== {name} ({video_id}) ===")
    if out.exists():
        print("  dosya var, atlandı")
        return None
    url = f"https://youtu.be/{video_id}"
    data = {"experiment": "pilot-1", "name": name, "video_id": video_id, "url": url,
            "run_at": datetime.now().astimezone().isoformat(timespec="seconds"), "error": None}
    try:
        data["video"] = oembed(url)
        print(f"  video: {data['video']['title']} · kanal: {data['video']['channel']}")

        raw, _ = load_transcript(video_id, get_settings().transcript_language_list, fetch_transcript)
        clean = clean_transcript(raw)
        words = sum(len(s.text.split()) for s in clean.segments)
        chunks = len(fixed_size_chunks(clean.segments, video_id))
        data["transcript"] = {"language": clean.language, "is_generated": clean.is_generated,
                              "segments": len(clean.segments), "duration_seconds": clean.duration_seconds,
                              "duration": mmss(clean.duration_seconds), "words": words, "chunks": chunks}
        print(f"  süre {mmss(clean.duration_seconds)} · dil {clean.language} · otomatik altyazı {clean.is_generated} · "
              f"kelime {words} · parça {chunks}")
        (transcript_dir / f"{name}.txt").write_text(
            "\n".join(f"[{mmss(s.start)}] {s.text}" for s in clean.segments), encoding="utf-8")

        topics_resp, topics_rec = post("/api/topics", {"url": url, "count": TOPIC_COUNT})
        topics = topics_resp["topics"]
        topics_tokens = tokens_of(topics_rec["metrics"]["llm_calls"])
        topics_ms = topics_rec["metrics"]["stages"]["total_ms"]
        data["topics"] = {"prompt_version": topics_resp["prompt_version"], "items": topics,
                          "extraction": topics_rec["topic_extraction"], "stages": topics_rec["metrics"]["stages"],
                          "tokens": topics_tokens}
        print(f"  [konu] {len(topics)} konu · süre {topics_ms / 1000:.1f} sn · token {topics_tokens['prompt_tokens']} girdi + "
              f"{topics_tokens['completion_tokens']} çıktı · maliyet {topics_tokens['cost_usd']:.6f} USD")
        if len(topics) != TOPIC_COUNT:
            raise PilotError(f"Konu çıkarma {len(topics)} konu döndürdü, {TOPIC_COUNT} gerekli; koşullar çalıştırılmadı.")
        levels = seeded_mapping(video_id, TOPIC_COUNT)
        data["bloom_levels"] = levels
        for i, (t, lv) in enumerate(zip(topics, levels), 1):
            print(f"    {i}. [{lv}] {t['title']}")

        texts = [t["text"] for t in topics]
        conditions = {}
        for mode in ("full", "rag"):
            conditions[mode] = run_condition(mode, url, texts, levels)
        data["conditions"] = conditions
        data["samples"] = pick_samples(video_id, texts, conditions)

        total_ms = topics_ms + sum(c["stages"]["total_ms"] for c in conditions.values())
        all_tokens = [topics_tokens] + [c["tokens"] for c in conditions.values()]
        data["totals"] = {
            "seconds": round(total_ms / 1000, 1),
            "prompt_tokens": sum(t["prompt_tokens"] for t in all_tokens),
            "completion_tokens": sum(t["completion_tokens"] for t in all_tokens),
            "total_tokens": sum(t["total_tokens"] for t in all_tokens),
            "cost_usd": round(sum(t["cost_usd"] for t in all_tokens), 6),
        }
        print(f"  toplam {data['totals']['seconds']} sn · {data['totals']['total_tokens']} token · "
              f"{data['totals']['cost_usd']:.6f} USD")
        print(f"  seçilen örnekler: {', '.join(s['slot'] for s in data['samples'])}")
    except Exception as exc:  # bir video hata verirse kaydedilir, sonrakine geçilir
        detail = scrub_secrets(str(exc), (get_settings().openai_api_key,)).replace(str(ROOT), "<depo>")[:300]
        data["error"] = {"type": type(exc).__name__, "detail": detail}
        print(f"  HATA: {type(exc).__name__}: {detail}")
    with out.open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def main() -> None:
    if len(sys.argv) != 2:
        print("Kullanım: pilot-1.py <transkript-klasörü>")
        sys.exit(2)
    transcript_dir = Path(sys.argv[1])
    transcript_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    get_embedder()._load()
    load_seconds = time.perf_counter() - t0
    print(f"BGE-M3 ilk yüklenme süresi: {load_seconds:.1f} sn (hiçbir videonun süresine dahil değil)")
    print()

    results = []
    for name, video_id in VIDEOS:
        data = process(name, video_id, transcript_dir)
        if data:
            results.append(data)
        print()

    print("=== Özet ===")
    print("| Video | Süre | Toplam süre (sn) | Toplam token | Maliyet (USD) |")
    print("|---|---|---|---|---|")
    done = [d for d in results if d.get("totals")]
    for d in results:
        if d.get("totals"):
            t = d["totals"]
            print(f"| {d['name']} | {d['transcript']['duration']} | {t['seconds']} | {t['total_tokens']} | {t['cost_usd']:.6f} |")
        else:
            print(f"| {d['name']} | hata | — | — | — |")
    print(f"| TOPLAM | — | {round(sum(d['totals']['seconds'] for d in done), 1)} | "
          f"{sum(d['totals']['total_tokens'] for d in done)} | {sum(d['totals']['cost_usd'] for d in done):.6f} |")
    summary = {"experiment": "pilot-1", "bge_m3_load_seconds": round(load_seconds, 1),
               "price_usd_per_1m": {"input": PRICE_IN, "output": PRICE_OUT}}
    with (HERE / "pilot-1-ek-ozet.json").open("x", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
