"""Pilot 2: questions-v3 ile questions-v4'ün aynı konu ve düzeylerle karşılaştırılması.

Bu bir ÖN GÖZLEM çalışmasıdır: kalite ve Bloom uyumu ölçülmez. İstekler API
üzerinden FastAPI TestClient ile yapılır (çalışan bir sunucu gerekmez);
çalıştırma kayıtları backend/runs altına yazılır. Gerçek OpenAI çağrısı yapılır;
BGE-M3 yerel olarak çalışır.

Her video için konular ve Bloom düzeyleri pilot 1 JSON'undan AYNEN alınır; konu
çıkarma çalıştırılmaz. 4 çalıştırma: v3-full, v3-rag, v4-full, v4-rag. Yeniden
deneme yapılmaz. Transkript önbellekten gelir; önbellekte yoksa video başına tek
YouTube isteği yapılır, alınamazsa video atlanır ve hiç OpenAI çağrısı yapılmaz.
Video dosyası varsa o video atlanır (üzerine yazılmaz). Bir çalıştırma hata
verirse biten çalıştırmalar ve hata video dosyasına yazılır, sonrakine geçilir.

Betik, pilot-2.md içindeki RAPOR_ISARETI satırının altını video dosyalarından
yeniden yazar; satırın üstündeki plana dokunmaz.

Maliyet yalnızca bu betikte, sabit liste fiyatıyla hesaplanır.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\pilot-2\\pilot-2.py

Bir videonun eksik çalıştırmalarını tamamlamak için (biten çalıştırmalar yeniden
çalıştırılmaz, video dosyası güncellenir):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\pilot-2\\pilot-2.py --eksik <alan>
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import runs  # noqa: E402
from app.services.embeddings import get_embedder  # noqa: E402
from app.services.metrics import scrub_secrets  # noqa: E402
from app.services.transcript import TranscriptBlocked, TranscriptUnavailable, fetch_transcript  # noqa: E402
from app.services.transcript_cache import load_transcript  # noqa: E402

VIDEOS = [
    ("biyoloji", "109kCbVtU1U"),
    ("tarih", "aaCHLYO3Fzg"),
    ("matematik", "edSvMQ77TmU"),
    ("ingilizce", "FetnCoTS9qY"),
    ("edebiyat", "fgOxbhEMnQQ"),
    ("python", "CEr_UiR4Gvk"),
]
RUNS = [
    ("v3-full", "questions-v3", "full"),
    ("v3-rag", "questions-v3", "rag"),
    ("v4-full", "questions-v4", "full"),
    ("v4-rag", "questions-v4", "rag"),
]
K = 5
FIRST_LOAD_SECONDS = 27.2  # ilk çalıştırmadaki BGE-M3 yüklenme süresi; rapor --eksik ile yeniden yazılınca korunur
PRICE_IN = 0.15  # USD / 1M token, pilot 1 ile aynı liste fiyatı
PRICE_OUT = 0.60
# bloom_levels.json örneklerine özgü sözcükler. Konu gerçekten bunlarla ilgiliyse yanlış işaret olabilir.
EXAMPLE_WORDS = ["Ali", "Ayşe", "iki öğrenci", "basınç", "rüzgâr", "fırıldak", "mum", "termometre", "balon"]
OUTCOMES = ("ok", "empty", "invalid", "duplicate")
REPORT_MARK = "<!-- RAPOR_ISARETI: bu satırın altını pilot-2.py yazar -->"
SECRET_PATTERNS = {
    "API anahtarı": r"sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY",
    "yetki başlığı": r"(?i)authorization|bearer\s+\S",
    "parola/token": r"(?i)password\s*[=:]|parola\s*[=:]|\btoken\s*=",
    ".env": r"\.env\b",
    "e-posta": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "yerel yol": r"[A-Za-z]:[\\/]+Users|/c/Users",
    "paylaşım kodu": r"[?&]si=",
}
HERE = Path(__file__).resolve().parent
PILOT_1 = HERE.parent / "pilot-1"

client = TestClient(app)


class PilotError(Exception):
    pass


def mmss(seconds) -> str:
    if seconds is None:
        return "yok"
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


# --- Otomatik işaretler ---------------------------------------------------------------


def fold(text: str) -> str:
    """Türkçe küçük harfe çevirir, şapkalı harfleri düzleştirir."""
    text = text.replace("I", "ı").replace("İ", "i").lower()
    return text.replace("â", "a").replace("î", "i").replace("û", "u")


def plain(text: str) -> str:
    """Küçük harf, noktalamasız, tek boşluklu metin."""
    return " ".join(re.sub(r"[^\w\s]", "", fold(text)).split())


def answer_in_stem(stem: str, correct: str) -> bool:
    """"Olası cevap kökte": kaba işaret; doğru cevabın kökte geçtiğini kanıtlamaz.

    Doğru seçenek kökte geçiyorsa ya da seçenekteki 4 harften uzun kelimelerin
    yarısından fazlası kökte geçiyorsa işaretlenir. Geçme, metin içinde aramadır:
    "savaşı", "savaşından" içinde bulunur.
    """
    stem, correct = plain(stem), plain(correct)
    if correct and correct in stem:
        return True
    words = [w for w in correct.split() if len(w) > 4]
    return bool(words) and 2 * sum(w in stem for w in words) > len(words)


def example_leak(question: str, options: list[str]) -> list[str]:
    """Soru kökü ya da seçeneklerde geçen örnek sözcükleri.

    Özel adlar (Ali, Ayşe) büyük harfle ve tam kelime olarak aranır; diğerleri
    kelime başından, ek alabilir ("balonun"). "umumi" içindeki "mum" sayılmaz.
    """
    text = " ".join([question, *options])
    found = []
    for word in EXAMPLE_WORDS:
        if word[0].isupper():
            hit = re.search(rf"(?<!\w){word}(?!\w)", text)
        else:
            hit = re.search(rf"(?<!\w){re.escape(fold(word))}", fold(text))
        if hit:
            found.append(word)
    return found


# --- Çalıştırma -----------------------------------------------------------------------


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


def tokens_of(calls: list[dict]) -> dict:
    t = {"prompt_tokens": sum(c.get("prompt_tokens") or 0 for c in calls),
         "completion_tokens": sum(c.get("completion_tokens") or 0 for c in calls)}
    t["total_tokens"] = t["prompt_tokens"] + t["completion_tokens"]
    t["cost_usd"] = round((t["prompt_tokens"] * PRICE_IN + t["completion_tokens"] * PRICE_OUT) / 1_000_000, 6)
    return t


def question_flags(response: dict, record: dict) -> list[dict]:
    """Soru başına işaretler; sıra yanıttaki soru sırasıdır (index 1'den başlar)."""
    similar = (record.get("similarity_check") or {}).get("flagged_pairs", [])
    writing = {r["index"]: [f["rule_id"] for f in r["flags"]] for r in (record.get("writing_check") or {}).get("results", [])}
    flags = []
    for i, q in enumerate(response["questions"], 1):
        flags.append({
            "index": i,
            "answer_in_stem": answer_in_stem(q["question"], q["options"][q["correct_index"]]),
            "example_leak": example_leak(q["question"], q["options"]),
            "writing_rules": writing.get(i, []),
            "similar_to": [p["b"] if p["a"] == i else p["a"] for p in similar if i in (p["a"], p["b"])],
        })
    return flags


def run_one(label: str, version: str, mode: str, url: str, texts: list[str], levels: list[str]) -> dict:
    body = {"url": url, "topics": texts, "bloom_levels": levels, "context_mode": mode, "prompt_version": version}
    if mode == "rag":
        body["k"] = K
    response, record = post("/api/questions", body)
    tg = record["topic_generation"]
    if not response["prompt_version"] == tg["prompt_version"] == version:
        raise PilotError(f"{label}: kayıtta beklenmeyen istem sürümü: {tg['prompt_version']}")
    metrics = record["metrics"]
    flags = question_flags(response, record)
    similar = record.get("similarity_check") or {}
    tokens = tokens_of(metrics["llm_calls"])
    summary = {
        "outcome_counts": tg["outcome_counts"],
        "returned": response["returned_count"],
        "verified": response["verified_count"],
        "answer_in_stem": sum(f["answer_in_stem"] for f in flags),
        "example_leak": sum(bool(f["example_leak"]) for f in flags),
        "writing_flags": sum(len(f["writing_rules"]) for f in flags),
        "similar_pairs": len(similar.get("flagged_pairs", [])),
        "seconds": round(metrics["stages"]["total_ms"] / 1000, 1),
    }
    print(f"  [{label}] sonuçlar: " + ", ".join(t["outcome"] for t in tg["per_topic"]))
    print(f"  [{label}] dönen {summary['returned']}/{response['requested_count']} · alıntısı bulunan {summary['verified']} · "
          f"olası cevap kökte {summary['answer_in_stem']} · örnek sızıntısı {summary['example_leak']} · "
          f"yazım işareti {summary['writing_flags']} · benzer çift {summary['similar_pairs']}"
          + (f" (hata: {similar['error']})" if similar.get("error") else ""))
    print(f"  [{label}] süre {summary['seconds']} sn · çağrı {len(metrics['llm_calls'])} · token {tokens['prompt_tokens']} girdi + "
          f"{tokens['completion_tokens']} çıktı · maliyet {tokens['cost_usd']:.6f} USD · kaynak {metrics.get('transcript_source')}")
    return {
        "label": label, "prompt_version": version, "mode": mode, "model": response["model"],
        "transcript_source": metrics.get("transcript_source"),
        "response": response, "topic_generation": tg, "similarity_check": similar,
        "question_flags": flags, "summary": summary, "stages": metrics["stages"],
        "llm_calls": metrics["llm_calls"], "tokens": tokens, "dropped": metrics.get("dropped"),
    }


def pilot_1_inputs(name: str) -> tuple[list[dict], list[str]] | None:
    """Pilot 1 JSON'undaki konular ve düzeyler; video pilot 1'de tamamlanmadıysa None."""
    path = PILOT_1 / f"pilot-1-{name}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("error") or "conditions" not in data:
        return None
    return data["topics"]["items"], data["bloom_levels"]


def fetch_once(video_id: str) -> tuple[str | None, dict | None]:
    """Transkripti önbelleğe alır: (kaynak, None) ya da alınamadıysa (None, hata). Tek deneme."""
    try:
        _, source = load_transcript(video_id, get_settings().transcript_language_list, fetch_transcript)
        return source, None
    except (TranscriptBlocked, TranscriptUnavailable) as exc:
        return None, {"type": type(exc).__name__, "detail": str(exc)}


def write_once(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


def new_data(name: str, video_id: str, topics: list[dict], levels: list[str]) -> dict:
    return {"experiment": "pilot-2", "name": name, "video_id": video_id, "url": f"https://youtu.be/{video_id}",
            "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "topics": topics, "bloom_levels": levels, "skipped": None, "error": None, "failed_runs": [], "runs": {}}


def failed_run(label: str, before: set[Path]) -> dict | None:
    """Hatalı çalıştırmanın harcaması: yanıt olmasa da -error kaydındaki model çağrıları ücretlidir."""
    errors = sorted(p for p in run_files() - before if p.stem.endswith("-error"))
    if not errors:
        return None
    metrics = runs.load_run(errors[-1])["metrics"]
    return {"label": label, "llm_calls": metrics["llm_calls"], "tokens": tokens_of(metrics["llm_calls"])}


def overwrite(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def process(data: dict, save=write_once) -> None:
    print(f"=== {data['name']} ({data['video_id']}) ===")
    texts = [t["text"] for t in data["topics"]]
    before = run_files()
    try:
        for label, version, mode in RUNS:
            if label in data["runs"]:
                continue
            data["runs"][label] = run_one(label, version, mode, data["url"], texts, data["bloom_levels"])
    except Exception as exc:  # biten çalıştırmalar korunur, sonraki videoya geçilir
        detail = scrub_secrets(str(exc), (get_settings().openai_api_key,)).replace(str(ROOT), "<depo>")[:300]
        data["error"] = {"type": type(exc).__name__, "detail": detail}
        failed = failed_run(label, before)
        if failed:
            data.setdefault("failed_runs", []).append({**failed, **data["error"]})
        print(f"  HATA: {type(exc).__name__}: {detail}")
    save(HERE / f"pilot-2-{data['name']}.json", data)
    print()


# --- Rapor ----------------------------------------------------------------------------


def num(value) -> str:
    return str(value).replace(".", ",")


def cell(text) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def load_results() -> list[dict]:
    paths = [HERE / f"pilot-2-{name}.json" for name, _ in VIDEOS]
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths if p.exists()]


def run_cost(run: dict) -> float:
    return run["tokens"]["cost_usd"]


def summary_section(results: list[dict]) -> list[str]:
    lines = ["## Video × sürüm × koşul özeti", "",
             "| Video | Sürüm | Koşul | ok | empty | invalid | duplicate | Alıntısı bulunan | Olası cevap kökte | "
             "Örnek sızıntısı | Yazım işareti | Benzer çift | Süre (sn) | Girdi token | Çıktı token | Maliyet (USD) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    done = [r for d in results for r in d["runs"].values()]
    # Toplamlar yalnızca dört çalıştırması da tamam olan videolardan: sürümler aynı videolarla karşılaştırılsın
    complete = [d for d in results if len(d["runs"]) == len(RUNS)]
    failed = [f for d in results for f in d.get("failed_runs", [])]
    for d in results:
        for run in d["runs"].values():
            s, t = run["summary"], run["tokens"]
            counts = [s["outcome_counts"][o] for o in OUTCOMES]
            row = [d["name"], run["prompt_version"].removeprefix("questions-"), run["mode"], *counts, s["verified"],
                   s["answer_in_stem"], s["example_leak"], s["writing_flags"], s["similar_pairs"], num(s["seconds"]),
                   t["prompt_tokens"], t["completion_tokens"], num(f"{t['cost_usd']:.6f}")]
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
    for version in ("questions-v3", "questions-v4"):
        for mode in ("full", "rag"):
            group = [r for d in complete for r in d["runs"].values() if r["prompt_version"] == version and r["mode"] == mode]
            s = [r["summary"] for r in group]
            counts = [sum(x["outcome_counts"][o] for x in s) for o in OUTCOMES]
            row = [f"**Toplam ({len(complete)} video)**", version.removeprefix("questions-"), mode, *counts,
                   *(sum(x[key] for x in s) for key in ("verified", "answer_in_stem", "example_leak", "writing_flags", "similar_pairs")),
                   num(round(sum(x["seconds"] for x in s), 1)), sum(r["tokens"]["prompt_tokens"] for r in group),
                   sum(r["tokens"]["completion_tokens"] for r in group), num(f"{sum(r['tokens']['cost_usd'] for r in group):.6f}")]
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
    total = sum(r["tokens"]["cost_usd"] for r in done) + sum(f["tokens"]["cost_usd"] for f in failed)
    calls = sum(len(r["llm_calls"]) for r in done) + sum(len(f["llm_calls"]) for f in failed)
    names = ", ".join(d["name"] for d in complete)
    lines += ["", f"Toplam satırları dört çalıştırması da tamam olan videolardan hesaplandı: {names}.", "",
              f"Harcama, hatalı çalıştırmalar dahil: {calls} OpenAI çağrısı, {num(f'{total:.6f}')} USD (liste fiyatıyla tahmin).", ""]
    lines += ["\"Olası cevap kökte\" kaba bir işarettir. \"Örnek sızıntısı\" sayısı, konu gerçekten bu sözcüklerle "
              "ilgiliyse yanlış işaret olabilir.", ""]
    missing = [d for d in results if d["skipped"] or d["error"]]
    if missing:
        lines += ["**Atlanan ya da yarım kalan videolar**", ""]
        for d in missing:
            problem = d["skipped"] or d["error"]
            lines.append(f"- {d['name']}: {problem['type']}: {problem['detail']} (biten çalıştırma: {len(d['runs'])} / {len(RUNS)})")
        lines.append("")
    if failed:
        lines += ["**Hatalı çalıştırmalar** (harcamaya dahil, tablolara dahil değil)", ""]
        for d in results:
            for run in d.get("failed_runs", []):
                longest = max(run["llm_calls"], key=lambda c: c.get("completion_tokens") or 0)
                lines.append(f"- {d['name']} {run['label']}: {run['detail']} {len(run['llm_calls'])} çağrı, "
                             f"{run['tokens']['prompt_tokens']} girdi + {run['tokens']['completion_tokens']} çıktı token, "
                             f"{num(f'{run_cost(run):.6f}')} USD. En uzun çağrı: {longest['completion_tokens']} çıktı token, "
                             f"{num(round(longest['ms'] / 1000, 1))} sn.")
        lines.append("")
    return lines


def topic_result(run: dict | None, index: int) -> str:
    if run is None:
        return "çalıştırılmadı"
    trace = run["topic_generation"]["per_topic"][index]
    if trace.get("truncated"):
        return trace["outcome"] + " (token sınırında kesildi)"
    return trace["outcome"] + (f": {cell(trace['skip_reason'])}" if trace.get("skip_reason") else "")


def create_section(results: list[dict]) -> list[str]:
    labels = [label for label, _, _ in RUNS]
    lines = ["## Yaratma düzeyindeki konular", "", "| Video | Konu | " + " | ".join(labels) + " |",
             "|---|---|" + "---|" * len(labels)]
    for d in results:
        for i, (topic, level) in enumerate(zip(d["topics"], d["bloom_levels"])):
            if level == "Yaratma":
                cells = [topic_result(d["runs"].get(label), i) for label in labels]
                lines.append(f"| {d['name']} | {cell(topic['title'])} | " + " | ".join(cells) + " |")
    return lines + [""]


def flags_text(flag: dict, topic_numbers: list[int]) -> str:
    """topic_numbers: yanıttaki soru sırasına göre konu numaraları (benzer sorular konu numarasıyla yazılır)."""
    parts = []
    if flag["answer_in_stem"]:
        parts.append("olası cevap kökte")
    if flag["example_leak"]:
        parts.append("örnek sızıntısı (" + ", ".join(flag["example_leak"]) + ")")
    if flag["writing_rules"]:
        parts.append("yazım kuralı " + ", ".join(str(r) for r in flag["writing_rules"]))
    if flag["similar_to"]:
        parts.append("benzer soru: konu " + ", ".join(str(topic_numbers[i - 1]) for i in flag["similar_to"]))
    return "; ".join(parts) or "yok"


def question_rows(run: dict | None, topic_text: str, index: int) -> dict:
    """Bir çalıştırmanın o konudaki hücreleri."""
    rows = {"Sonuç": topic_result(run, index)}
    if run is None:
        return rows
    topics = run["topic_generation"]["topics"]
    numbers = [topics.index(q["topic"]) + 1 for q in run["response"]["questions"]]
    for position, q in enumerate(run["response"]["questions"]):
        if q["topic"] == topic_text:
            rows["Soru"] = cell(q["question"])
            rows["Seçenekler"] = "<br>".join(cell(o) for o in q["options"])
            rows["Doğru cevap"] = cell(q["options"][q["correct_index"]])
            rows["Kaynak alıntısı"] = cell(q["source_quote"])
            rows["Kaynak zamanı"] = mmss(q["source_start_seconds"]) + (" · alıntı bulundu" if q["verified"] else " · alıntı bulunamadı")
            rows["İşaretler"] = flags_text(run["question_flags"][position], numbers)
    return rows


def questions_section(results: list[dict]) -> list[str]:
    fields = ["Sonuç", "Soru", "Seçenekler", "Doğru cevap", "Kaynak alıntısı", "Kaynak zamanı", "İşaretler"]
    lines = ["## Bütün sorular", ""]
    for d in results:
        if not d["runs"]:
            continue
        lines += [f"### {d['name']}", ""]
        for i, (topic, level) in enumerate(zip(d["topics"], d["bloom_levels"])):
            lines += [f"#### Konu {i + 1} · hedef düzey {level} · {topic['title']}", ""]
            for mode in ("full", "rag"):
                v3 = question_rows(d["runs"].get(f"v3-{mode}"), topic["text"], i)
                v4 = question_rows(d["runs"].get(f"v4-{mode}"), topic["text"], i)
                lines += [f"| {mode} | v3 | v4 |", "|---|---|---|"]
                lines += [f"| {f} | {v3.get(f, '—')} | {v4.get(f, '—')} |" for f in fields if f in v3 or f in v4]
                lines.append("")
    return lines


def scan(texts: dict[str, str]) -> list[str]:
    """Gizli bilgi taraması; eşleşmeleri `dosya: tür` olarak döndürür (eşleşen metin yazılmaz)."""
    return [f"{name}: {kind}" for name, text in texts.items() for kind, pattern in SECRET_PATTERNS.items()
            if re.search(pattern, text)]


def write_report(results: list[dict], load_seconds: float | None) -> None:
    lines = ["## Çalıştırma", "", f"- BGE-M3 yüklenme süresi: {num(round(load_seconds, 1)) + ' sn' if load_seconds is not None else 'yüklenmedi'}."]
    for d in results:
        sources = sorted({r["transcript_source"] or "bilinmiyor" for r in d["runs"].values()})
        models = sorted({r["model"] for r in d["runs"].values()})
        lines.append(f"- {d['name']}: {len(d['runs'])} / {len(RUNS)} çalıştırma · transkript kaynağı {', '.join(sources) or 'yok'}"
                     f" · model {', '.join(models) or 'yok'}.")
    lines.append("")
    lines += summary_section(results) + create_section(results) + questions_section(results)
    report = "\n".join(lines)

    texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(HERE.glob("pilot-2-*.json"))}
    texts["rapor"] = report
    hits = scan(texts)
    print("Gizli bilgi taraması: " + ("; ".join(hits) if hits else "eşleşme yok"))
    report += "\n## Gizli bilgi taraması\n\n" + (
        "Eşleşmeler: " + "; ".join(hits) if hits else
        "Video JSON dosyaları ve bu rapor tarandı (API anahtarı, yetki başlığı, parola/token, `.env`, e-posta, yerel yol, paylaşım kodu); eşleşme yok."
    ) + "\n"

    path = HERE / "pilot-2.md"
    plan = path.read_bytes().decode("utf-8").split(REPORT_MARK)[0]
    path.write_bytes(f"{plan}{REPORT_MARK}\n\n{report}".encode("utf-8"))


def complete_missing(name: str) -> None:
    """Video dosyasındaki eksik çalıştırmaları bir kez çalıştırır ve raporu yeniden yazar."""
    path = HERE / f"pilot-2-{name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["error"] or data["skipped"]:
        sys.exit(f"{name}: dosyada error ya da skipped var; önce temizlenmeli.")
    data["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.perf_counter()
    get_embedder()._load()
    print(f"BGE-M3 yüklenme süresi: {time.perf_counter() - t0:.1f} sn (hiçbir çalıştırmanın süresine dahil değil)")
    process(data, save=overwrite)
    write_report(load_results(), FIRST_LOAD_SECONDS)


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--eksik":
        complete_missing(sys.argv[2])
        return
    if REPORT_MARK not in (HERE / "pilot-2.md").read_text(encoding="utf-8"):
        sys.exit("pilot-2.md içinde rapor işareti yok.")
    if not get_settings().transcript_cache:
        sys.exit("TRANSCRIPT_CACHE kapalı; pilot 2 önbellekle çalışır.")

    # Önce transkriptler: alınamayan video için hiç OpenAI çağrısı yapılmaz
    ready = []
    for name, video_id in VIDEOS:
        if (HERE / f"pilot-2-{name}.json").exists():
            print(f"{name}: dosya var, atlandı")
            continue
        inputs = pilot_1_inputs(name)
        if inputs is None:
            print(f"{name}: pilot 1'de tamamlanmadı, atlandı")
            data = new_data(name, video_id, [], [])
            data["skipped"] = {"type": "PilotBirEksik", "detail": "Pilot 1'de tamamlanmadığı için konu ve düzey yok."}
            write_once(HERE / f"pilot-2-{name}.json", data)
            continue
        data = new_data(name, video_id, *inputs)
        source, problem = fetch_once(video_id)
        print(f"{name}: transkript " + (source if source else f"alınamadı ({problem['type']})"))
        if problem:
            data["skipped"] = problem
            write_once(HERE / f"pilot-2-{name}.json", data)
        else:
            ready.append(data)
    print()

    load_seconds = None
    if ready:
        t0 = time.perf_counter()
        get_embedder()._load()
        load_seconds = time.perf_counter() - t0
        print(f"BGE-M3 ilk yüklenme süresi: {load_seconds:.1f} sn (hiçbir çalıştırmanın süresine dahil değil)")
        print()
    for data in ready:
        process(data)

    write_report(load_results(), load_seconds)


if __name__ == "__main__":
    main()
