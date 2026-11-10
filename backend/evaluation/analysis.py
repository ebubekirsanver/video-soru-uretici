"""Ortak etiketlerle AS1 ve AS2 analizi.

Koşullar "rag" ve "full"; farklar her yerde rag - full yönündedir.

Üretilemeyen konu (empty / invalid / duplicate):
- AS1 kabul edilebilirlik ve kaynağa dayalılıkta o koşulda "hayır" sayılır.
- Cevaplanabilirliği yoktur: çift Wilcoxon'dan çıkarılır, kaç çiftin çıktığı raporlanır.
- AS2'de birincil sonuç "bütün konular"dır: üretilemeyen konu hedef düzeye uyumsuz
  sayılır (kullanıcı kararı). "Yalnızca üretilen sorular" ikincil olarak verilir.

Yöntemler `evaluation/stats.py` başındadır. Eksik ya da geçersiz ortak etiket
sessizce geçilmez: raporda listelenir ve o ölçütün hesabından çıkar.

Çalıştırma (backend klasöründen):
    python -m evaluation.analysis --ortak <ortak.xlsx> --anahtar <anahtar.json> --cikti <klasör>
"""

import argparse
from collections import Counter
from pathlib import Path

from evaluation.common import (
    BLOOM_LEVELS,
    CONDITIONS,
    DEFAULT_ALPHA,
    interval,
    load_key,
    num,
    table,
    write_json,
)
from evaluation.labels import Label, read_labels
from evaluation.stats import mcnemar_exact, paired_difference, wilcoxon_signed_rank, wilson

UNPRODUCED_COLUMN = "Üretilemedi"


def build_pairs(key: dict) -> dict[str, dict]:
    """Çift kimliği -> koşul -> yuva. Yuvada `id` varsa soru üretilmiştir, None ise üretilememiştir."""
    pairs: dict[str, dict] = {}
    for item_id, info in key["questions"].items():
        pairs.setdefault(info["pair_id"], {})[info["condition"]] = {**info, "id": item_id}
    for info in key["unproduced"]:
        pairs.setdefault(info["pair_id"], {})[info["condition"]] = {**info, "id": None}
    return pairs


def _binary(slot: dict, labels: dict[str, Label], field: str) -> bool | None:
    """Üretilemeyen konu False; etiketi eksik soru None."""
    if slot["id"] is None:
        return False
    label = labels.get(slot["id"])
    return None if label is None else getattr(label, field)


def as1_binary(pairs: dict, labels: dict[str, Label], field: str, alpha: float) -> dict:
    """Kesin McNemar, koşul oranları ve oran farkı. Bir tarafı eksik olan çift çıkarılır."""
    both = rag_only = full_only = neither = excluded = 0
    for pair in pairs.values():
        if len(pair) < 2:
            continue
        rag, full = _binary(pair["rag"], labels, field), _binary(pair["full"], labels, field)
        if rag is None or full is None:
            excluded += 1
        elif rag and full:
            both += 1
        elif rag:
            rag_only += 1
        elif full:
            full_only += 1
        else:
            neither += 1
    n = both + rag_only + full_only + neither
    return {
        "pairs": n, "excluded_missing_label": excluded,
        "both": both, "rag_only": rag_only, "full_only": full_only, "neither": neither,
        "rag": wilson(both + rag_only, n, alpha), "full": wilson(both + full_only, n, alpha),
        "mcnemar": mcnemar_exact(rag_only, full_only),
        "difference": paired_difference(both, rag_only, full_only, neither, alpha),
    }


def as1_answerable(pairs: dict, labels: dict[str, Label]) -> dict:
    """Wilcoxon; üretilemeyen konulu ve etiketi eksik çiftler ayrı sayılarak çıkarılır."""
    differences, unproduced, missing = [], 0, 0
    for pair in pairs.values():
        if len(pair) < 2:
            continue
        if pair["rag"]["id"] is None or pair["full"]["id"] is None:
            unproduced += 1
            continue
        rag, full = labels.get(pair["rag"]["id"]), labels.get(pair["full"]["id"])
        if rag is None or full is None or rag.answerable is None or full.answerable is None:
            missing += 1
            continue
        differences.append(rag.answerable - full.answerable)
    return {"excluded_unproduced": unproduced, "excluded_missing_label": missing, **wilcoxon_signed_rank(differences)}


def _slots(pairs: dict) -> list[dict]:
    return [slot for pair in pairs.values() if len(pair) == 2 for slot in pair.values()]


def as2(pairs: dict, labels: dict[str, Label], alpha: float) -> dict:
    """Hedef düzeye uyum. `all_topics` (birincil): üretilemeyenler uyumsuz sayılarak; `produced` (ikincil): üretilen sorular."""
    slots = _slots(pairs)
    labelled = [s for s in slots if s["id"] is not None and s["id"] in labels and labels[s["id"]].bloom is not None]
    missing = sum(1 for s in slots if s["id"] is not None) - len(labelled)
    unproduced = [s for s in slots if s["id"] is None]

    def rates(selected_labelled, selected_unproduced):
        hits = sum(labels[s["id"]].bloom == s["bloom_target"] for s in selected_labelled)
        return {"produced": wilson(hits, len(selected_labelled), alpha),
                "all_topics": wilson(hits, len(selected_labelled) + len(selected_unproduced), alpha)}

    def where(items, key, value):
        return [s for s in items if s[key] == value]

    matrix = {t: {g: 0 for g in [*BLOOM_LEVELS, UNPRODUCED_COLUMN]} for t in BLOOM_LEVELS}
    for s in labelled:
        matrix[s["bloom_target"]][labels[s["id"]].bloom] += 1
    for s in unproduced:
        matrix[s["bloom_target"]][UNPRODUCED_COLUMN] += 1
    return {
        "primary": "all_topics",
        "excluded_missing_label": missing,
        "total": rates(labelled, unproduced),
        "by_condition": {c: rates(where(labelled, "condition", c), where(unproduced, "condition", c)) for c in CONDITIONS},
        "by_level": {lv: rates(where(labelled, "bloom_target", lv), where(unproduced, "bloom_target", lv)) for lv in BLOOM_LEVELS},
        "confusion_matrix": matrix,
    }


def descriptive(pairs: dict, labels: dict[str, Label], alpha: float) -> dict:
    """Video ve koşul bazında kabul edilebilir oranı (üretilemeyen konu paydadadır) ve üretilemeyen sayıları."""
    cells: dict[tuple, list[bool]] = {}
    missing = 0
    for slot in _slots(pairs):
        value = _binary(slot, labels, "acceptable")
        if value is None:
            missing += 1
            continue
        cells.setdefault((slot["video_id"], slot["condition"]), []).append(value)
    unproduced = [s for s in _slots(pairs) if s["id"] is None]
    return {
        "excluded_missing_label": missing,
        "acceptable_by_video": [
            {"video_id": video, "condition": condition, **wilson(sum(values), len(values), alpha)}
            for (video, condition), values in sorted(cells.items())
        ],
        "unproduced_count": len(unproduced),
        "unproduced_by_outcome": dict(sorted(Counter(s["outcome"] for s in unproduced).items())),
        "unproduced_by_condition": dict(sorted(Counter(s["condition"] for s in unproduced).items())),
        "unproduced": [{f: s[f] for f in ("video_id", "topic_index", "condition", "bloom_target", "outcome")} for s in unproduced],
    }


def analyze(key: dict, labels: dict[str, Label], alpha: float = DEFAULT_ALPHA) -> dict:
    pairs = build_pairs(key)
    return {
        "alpha": alpha,
        "pair_count": sum(1 for p in pairs.values() if len(p) == 2),
        "incomplete_pairs": sorted(p for p, slots in pairs.items() if len(slots) < 2),
        "as1": {
            "acceptable": as1_binary(pairs, labels, "acceptable", alpha),
            "grounded": as1_binary(pairs, labels, "grounded", alpha),
            "answerable": as1_answerable(pairs, labels),
        },
        "as2": as2(pairs, labels, alpha),
        "descriptive": descriptive(pairs, labels, alpha),
    }


def _rate(w: dict) -> str:
    return f"{w['k']} / {w['n']}"


def _significant(p, alpha) -> str:
    if p is None:
        return "tanımsız"
    return "evet" if p < alpha else "hayır"


def render_report(result: dict, problems: list[dict]) -> str:
    alpha = result["alpha"]
    level = round((1 - alpha) * 100)
    as1, as2_result, desc = result["as1"], result["as2"], result["descriptive"]
    lines = ["# AS1 ve AS2 analizi", "",
             f"Ortak etiketlerle hesaplandı. Anlamlılık düzeyi {num(alpha, 2)}. Tam çift: {result['pair_count']}. "
             f"Bir koşulu eksik, analize girmeyen çift: {len(result['incomplete_pairs'])}. Farklar rag - full yönündedir.", "",
             "## AS1: kabul edilebilirlik ve kaynağa dayalılık", ""]
    rows = []
    for name, r in (("Kabul edilebilir (0-1 hata)", as1["acceptable"]), ("Kaynağa dayalı", as1["grounded"])):
        d, m = r["difference"], r["mcnemar"]
        rows.append([name, r["pairs"], r["excluded_missing_label"], _rate(r["rag"]), num(r["rag"]["rate"]), _rate(r["full"]), num(r["full"]["rate"]),
                     r["both"], r["rag_only"], r["full_only"], r["neither"], num(d["difference"]), interval(d["ci_low"], d["ci_high"]),
                     num(m["p_value"], 4), _significant(m["p_value"], alpha)])
    lines += table(["Ölçüt", "Çift", "Çıkarılan", "rag", "rag oranı", "full", "full oranı", "İkisi de evet", "Yalnız rag", "Yalnız full",
                    "İkisi de hayır", "Fark", f"Fark %{level} GA", "McNemar p", f"p < {num(alpha, 2)}"], rows)
    lines += ["", "Kesin McNemar: uyumsuz çiftlerde iki yönlü binom testi. Oran farkı aralığı: Newcombe (1998) 10. yöntem. "
              "Üretilemeyen konu o koşulda \"hayır\" sayıldı.", "", "## AS1: cevaplanabilirlik", ""]
    w = as1["answerable"]
    lines += table(["Test edilen çift", "Sıfır fark", "Üretilemeyen konu nedeniyle çıkarılan", "Etiket eksikliği nedeniyle çıkarılan",
                    "W+", "W-", "Z", "p", f"p < {num(alpha, 2)}", "r", "Not"],
                   [[w["n"], w["zero_differences"], w["excluded_unproduced"], w["excluded_missing_label"], num(w["w_plus"], 1), num(w["w_minus"], 1),
                     num(w["z"]), num(w["p_value"], 4), _significant(w["p_value"], alpha), num(w["r"]), w["note"] or ""]])
    lines += ["", "Wilcoxon işaretli sıra testi: sıfır farklar çıkarıldı, bağ düzeltmeli normal yaklaşım, süreklilik düzeltmesi yok. "
              "r = Z / √N; N sıfır olmayan fark sayısı.", "", "## AS2: hedef düzeye uyum", ""]

    def rate_rows(items):
        out = []
        for name, r in items:
            p, a = r["produced"], r["all_topics"]
            out.append([name, _rate(a), num(a["rate"]), interval(a["ci_low"], a["ci_high"]), _rate(p), num(p["rate"]), interval(p["ci_low"], p["ci_high"])])
        return out

    headers = ["", "Bütün konular (birincil)", "Oran", f"%{level} Wilson GA", "Yalnızca üretilen sorular (ikincil)", "Oran", f"%{level} Wilson GA"]
    lines += ["Birincil sonuç \"bütün konular\"dır: üretilemeyen konu hedef düzeye uyumsuz sayılır. "
              "\"Yalnızca üretilen sorular\" ikincil sonuçtur.", ""]
    lines += table(headers, rate_rows([*as2_result["by_condition"].items(), ("Toplam", as2_result["total"])]))
    lines += ["", f"Bloom etiketi eksik olduğu için çıkarılan soru: {as2_result['excluded_missing_label']}.", "",
              "### Düzey bazında (keşfedici; test yok)", ""]
    lines += table(headers, rate_rows(as2_result["by_level"].items()))
    lines += ["", "### Hedef × verilen düzey karışıklık matrisi", "", "Satır hedef düzey, sütun ortak etiket.", ""]
    columns = [*BLOOM_LEVELS, UNPRODUCED_COLUMN]
    lines += table(["Hedef", *columns], [[t, *(as2_result["confusion_matrix"][t][c] for c in columns)] for t in BLOOM_LEVELS])
    lines += ["", "## Betimsel", "", "Üretilemeyen konu paydaya dahildir.", ""]
    lines += table(["Video", "Koşul", "Kabul edilebilir", "Oran", f"%{level} Wilson GA"],
                   [[v["video_id"], v["condition"], _rate(v), num(v["rate"]), interval(v["ci_low"], v["ci_high"])] for v in desc["acceptable_by_video"]])
    lines += ["", f"Üretilemeyen konu: {desc['unproduced_count']}. Sonuca göre: {desc['unproduced_by_outcome']}. Koşula göre: {desc['unproduced_by_condition']}.", ""]
    if desc["unproduced"]:
        lines += table(["Video", "Konu", "Koşul", "Hedef düzey", "Sonuç"],
                       [[u["video_id"], u["topic_index"], u["condition"], u["bloom_target"], u["outcome"]] for u in desc["unproduced"]])
        lines.append("")
    lines += ["## Eksik ya da geçersiz hücreler", ""]
    if problems:
        lines += table(["Dosya", "Kimlik", "Sütun", "Değer", "Sorun"], [[p["file"], p["id"], p["column"], p["value"], p["reason"]] for p in problems])
    else:
        lines.append("Yok.")
    return "\n".join(lines) + "\n"


def run(joint_path: Path, key_path: Path, out_dir: Path, alpha: float = DEFAULT_ALPHA) -> dict:
    key = load_key(key_path)
    labels, label_problems = read_labels(joint_path, sorted(key["questions"]))
    problems = [p.as_dict() for p in label_problems]
    result = {**analyze(key, labels, alpha), "problems": problems}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "analiz.json", result)
    (out_dir / "analiz-raporu.md").write_text(render_report(result, problems), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Ortak etiketlerle AS1 ve AS2 analizini yapar.")
    parser.add_argument("--ortak", type=Path, required=True, help="Doldurulmuş ortak etiket dosyası")
    parser.add_argument("--anahtar", type=Path, required=True)
    parser.add_argument("--cikti", type=Path, required=True)
    parser.add_argument("--alfa", type=float, default=DEFAULT_ALPHA, help="Anlamlılık düzeyi; aralıklar 1 - alfa düzeyinde")
    args = parser.parse_args()
    result = run(args.ortak, args.anahtar, args.cikti, args.alfa)
    print(f"{result['pair_count']} tam çift, {len(result['problems'])} sorunlu hücre.")


if __name__ == "__main__":
    main()
