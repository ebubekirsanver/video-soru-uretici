"""Uzman ile iki değerlendiricinin ortak etiketleri arasındaki uyum (docs/alt-kume-secim-kurali.md, Analiz).

Puanlayıcı 2026-11-25'ten beri ölçme ve değerlendirme alanından bir uzmandır (kural,
"Değişiklikler"); kodda ve dosya adlarında "alan öğretmeni / ogretmen" adı geçmişle
uyum için korunmuştur. Uzmanın etiketleri ana analize (AS1, AS2) katılmaz; geçerlilik
göstergesidir. Her ölçüt için ham uyum (Wilson aralığıyla), Cohen's kappa (büyük
örneklem ve yüzdelik bootstrap aralığıyla), iki tarafın kategori dağılımı ve hesaba
girmeyen soru sayısı verilir. --a ve --b verilirse uzman ile her değerlendiricinin
tartışma öncesi etiketleri arasındaki kappa da verilir (yalnızca büyük örneklem aralığı).

Bootstrap (2026-11-25, danışman önerisi): o ölçütte hesaba giren soru çiftlerinden aynı
sayıda çift yerine koyarak çekilir, kappa B kez (varsayılan 2000) yeniden hesaplanır;
aralık alfa/2 ve 1 - alfa/2 yüzdelikleridir. Tek üreteç random.Random(20261125) ölçütleri
rapordaki sırayla dolaşır; aynı girdi aynı aralığı verir. Kappanın hesaplanamadığı
örneklemler atlanır ve sayılır; B'nin %5'inden fazlaysa aralık verilmez.

Raporda soru kimlikleri ve koşullar listelenmez; yalnızca toplam sayılar yazılır.

Çalıştırma (backend klasöründen):
    python -m evaluation.validity --ogretmen <xlsx> --ortak <ortak.xlsx> --alt-kume <alt-kume.json> \\
        --anahtar <anahtar.json> --cikti <klasör> [--a <A.xlsx> --b <B.xlsx>] [--bootstrap 2000]
"""

import argparse
import json
import random
from pathlib import Path

from evaluation.agreement import KAPPAS, METHOD_NOTE, compute_kappas
from evaluation.common import DEFAULT_ALPHA, interval, load_key, num, table, write_json
from evaluation.labels import Label, read_labels
from evaluation.stats import bootstrap_kappa, kappa, wilson
from evaluation.subset import sha256_file

REPORT_FILE = "alan-ogretmeni-uyumu.md"
JSON_FILE = "alan-ogretmeni-uyumu.json"
NOTE = ("Ölçme ve değerlendirme uzmanının etiketleri ana analize katılmaz; geçerlilik göstergesidir. "
        "36 soru kappa için küçük bir örneklemdir.")
BOOTSTRAP_REPLICATES = 2000
BOOTSTRAP_SEED = 20261125
BOOTSTRAP_MAX_SKIPPED = 0.05  # atlanan örneklem B'nin bu oranını aşarsa aralık verilmez
BOOTSTRAP_NOTE = ("Bootstrap güven aralığı yüzdelik yöntemiyle, soru çiftleri yerine koyarak yeniden örneklenerek "
                  "hesaplanır; küçük örneklemde büyük örneklem yaklaşımından daha güvenilirdir.")
# Kural cevaplanabilirlik için ağırlıksız kappayı da istiyor; agreement.KAPPAS'ta yalnızca
# doğrusal ağırlıklısı var. Bu satır aynı biçimde burada eklenir (agreement.py değişmez).
EXTRA_KAPPAS = [("Cevaplanabilirlik", "answerable", [1, 2, 3, 4, 5], False)]
# Kategori dağılımı ölçüt başına bir kez verilir (rapor adı, alan, kategoriler)
CRITERIA = [
    ("Bloom düzeyi", "bloom"),
    ("Kabul edilebilirlik (0-1 hata)", "acceptable"),
    ("Kaynağa dayalılık", "grounded"),
    ("Cevaplanabilirlik", "answerable"),
    ("Tanıma hatası kaynaklı", "asr_error"),
    ("Anahtar yanlış (A)", "key_wrong"),  # 2026-11-25; kappa satırı agreement.KAPPAS'tan gelir
]


class ValidityError(Exception):
    """Girdiler birbiriyle uyuşmuyor."""


def _categories(field: str) -> list:
    return next(c for _, f, c, _ in KAPPAS + EXTRA_KAPPAS if f == field)


def _used(x: dict[str, Label], y: dict[str, Label], ids: list[str], field: str) -> list[tuple]:
    pairs = [(getattr(x[i], field), getattr(y[i], field)) for i in ids if i in x and i in y]
    return [(a, b) for a, b in pairs if a is not None and b is not None]


def _extra_kappas(x: dict[str, Label], y: dict[str, Label], ids: list[str], alpha: float) -> list[dict]:
    """agreement.compute_kappas ile aynı biçimde, EXTRA_KAPPAS için."""
    results = []
    for name, field, categories, weighted in EXTRA_KAPPAS:
        used = _used(x, y, ids, field)
        result = kappa([a for a, _ in used], [b for _, b in used], categories, weighted, alpha)
        results.append({"name": name, "field": field, "weighted": weighted, "excluded": len(ids) - len(used), **result})
    return results


def all_kappas(x: dict[str, Label], y: dict[str, Label], ids: list[str], alpha: float) -> list[dict]:
    """agreement.KAPPAS sırası; ağırlıksız cevaplanabilirlik ağırlıklısının hemen önüne konur."""
    rows = compute_kappas(x, y, ids, alpha)
    extra = _extra_kappas(x, y, ids, alpha)
    position = next(i for i, r in enumerate(rows) if r["field"] == "answerable")
    return rows[:position] + extra + rows[position:]


def with_raw_agreement(rows: list[dict], x: dict[str, Label], y: dict[str, Label], ids: list[str], alpha: float) -> list[dict]:
    """Her satıra ham uyum (aynı kategori) ve Wilson aralığı eklenir."""
    out = []
    for row in rows:
        used = _used(x, y, ids, row["field"])
        same = sum(a == b for a, b in used)
        out.append({**row, "raw": wilson(same, len(used), alpha)})
    return out


def with_bootstrap(rows: list[dict], x: dict[str, Label], y: dict[str, Label], ids: list[str], alpha: float,
                   replicates: int) -> list[dict]:
    """Her kappa satırına yüzdelik bootstrap aralığı. Tek üreteç, satırlar sabit (rapordaki) sırayla."""
    if replicates <= 0:
        return rows
    rng = random.Random(BOOTSTRAP_SEED)
    out = []
    for row in rows:
        used = _used(x, y, ids, row["field"])
        result = bootstrap_kappa([a for a, _ in used], [b for _, b in used], _categories(row["field"]), row["weighted"],
                                 replicates, rng, alpha, BOOTSTRAP_MAX_SKIPPED)
        out.append({**row, "bootstrap": {**result, "seed": BOOTSTRAP_SEED}})
    return out


def distributions(x: dict[str, Label], y: dict[str, Label], ids: list[str]) -> list[dict]:
    """Ölçüt başına iki tarafın kategori dağılımı; yalnızca iki tarafta da geçerli etiketi olan sorular."""
    result = []
    for name, field in CRITERIA:
        used = _used(x, y, ids, field)
        categories = _categories(field)
        result.append({"name": name, "field": field, "n": len(used),
                       "categories": [{"category": c, "teacher": sum(a == c for a, _ in used),
                                       "joint": sum(b == c for _, b in used)} for c in categories]})
    return result


def subset_ids(subset: dict, key: dict, key_path: Path) -> list[str]:
    if subset.get("anahtar_sha256") != sha256_file(key_path):
        raise ValidityError("Alt küme dosyası bu anahtar dosyasıyla üretilmemiş (anahtar SHA-256 değeri farklı).")
    ids = sorted(c["soru_kimligi"] for c in subset.get("hucreler", []) if c.get("soru_kimligi"))
    missing = [i for i in ids if i not in key["questions"]]
    if missing:
        raise ValidityError(f"Alt kümedeki {len(missing)} soru anahtarda yok.")
    if len(set(ids)) != len(ids):
        raise ValidityError("Alt kümede aynı soru birden çok kez geçiyor.")
    return ids


def _show(category) -> str:
    if isinstance(category, bool):
        return "evet" if category else "hayır"
    return str(category)


def _bootstrap_cell(row: dict) -> str:
    boot = row["bootstrap"]
    if boot["ci_low"] is None:
        return boot["note"] or "hesaplanamadı"
    text = interval(boot["ci_low"], boot["ci_high"])
    return f"{text} ({boot['skipped']} atlanan)" if boot["skipped"] else text


def render(result: dict) -> str:
    level = round((1 - result["alpha"]) * 100)
    replicates = result["bootstrap_replicates"]
    lines = ["# Ölçme ve değerlendirme uzmanıyla uyum", "", f"**Yöntem notu:** {NOTE}", "",
             "Karşılaştırma: ölçme ve değerlendirme uzmanının etiketleri ile iki değerlendiricinin tartışmadan sonraki "
             "ortak etiketleri (docs/alt-kume-secim-kurali.md, Analiz; puanlayıcı değişikliği: kuralın "
             "\"Değişiklikler\" bölümü, 2026-11-25).", "",
             f"Alt kümedeki soru: {result['subset_size']}. Sorunlu hücre: uzman dosyasında "
             f"{result['problems']['teacher']}, ortak etiket dosyasında {result['problems']['joint']} "
             "(yalnızca alt kümedeki sorular sayıldı).", "",
             "## Uyum", ""]
    if replicates:
        headers = ["Ölçüt", "n", "Hesaba girmeyen", "Ham uyum", f"%{level} GA (Wilson)", "Kappa",
                   f"Büyük örneklem %{level} GA", f"Bootstrap %{level} GA (B = {replicates}, tohum {BOOTSTRAP_SEED})", "Not"]
        rows = [[r["name"], r["n"], r["excluded"], num(r["raw"]["rate"]), interval(r["raw"]["ci_low"], r["raw"]["ci_high"]),
                 num(r["kappa"]), interval(r["ci_low"], r["ci_high"]), _bootstrap_cell(r), r["note"] or ""]
                for r in result["kappas"]]
    else:
        headers = ["Ölçüt", "n", "Hesaba girmeyen", "Ham uyum", f"%{level} GA (Wilson)", "Kappa", f"%{level} GA", "Not"]
        rows = [[r["name"], r["n"], r["excluded"], num(r["raw"]["rate"]), interval(r["raw"]["ci_low"], r["raw"]["ci_high"]),
                 num(r["kappa"]), interval(r["ci_low"], r["ci_high"]), r["note"] or ""] for r in result["kappas"]]
    lines += table(headers, rows)
    lines += ["", "Ham uyum: iki tarafın aynı kategoriyi verdiği soruların oranı (ağırlıklı satırlarda da ağırlıksız).",
              METHOD_NOTE]
    if replicates:
        lines.append(f"{BOOTSTRAP_NOTE} B = {replicates}, tohum {BOOTSTRAP_SEED}; aralık sınırları alfa/2 ve 1 - alfa/2 "
                     "yüzdelikleri. Kappanın hesaplanamadığı örneklemler (iki taraf da aynı tek kategoriye düştüğünde) "
                     f"atlanır ve sayılır; atlananlar B'nin %{round(BOOTSTRAP_MAX_SKIPPED * 100)}'inden fazlaysa aralık "
                     "verilmez.")
    lines += ["", "## Kategori dağılımı", "",
              "Kategoriler dengesiz dağıldığında kappa ham uyuma göre düşük çıkabilir (Artstein ve Poesio, 2008; "
              "Sim ve Wright, 2005). Sayılar iki tarafta da geçerli etiketi olan sorulardır.", ""]
    for block in result["distributions"]:
        lines += [f"### {block['name']} (n = {block['n']})", ""]
        lines += table(["Kategori", "Uzman", "Ortak etiket"],
                       [[_show(c["category"]), c["teacher"], c["joint"]] for c in block["categories"]])
        lines.append("")
    if result["raters"]:
        lines += ["## Ek bilgi: tartışma öncesi etiketlerle", "",
                  "Uzman ile her değerlendiricinin tartışmadan önceki etiketleri arasındaki kappa (büyük örneklem aralığı).", ""]
        names = list(result["raters"])
        rows = []
        for i, base in enumerate(result["kappas"]):
            row = [base["name"]]
            for rater in names:
                r = result["raters"][rater][i]
                row += [r["n"], num(r["kappa"]), interval(r["ci_low"], r["ci_high"])]
            rows.append(row)
        headers = ["Ölçüt"] + [h for rater in names for h in (f"n ({rater})", f"Kappa ({rater})", f"%{level} GA ({rater})")]
        lines += table(headers, rows)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def run(teacher_path: Path, joint_path: Path, subset_path: Path, key_path: Path, out_dir: Path,
        a_path: Path | None = None, b_path: Path | None = None, alpha: float = DEFAULT_ALPHA,
        bootstrap: int = BOOTSTRAP_REPLICATES) -> dict:
    key = load_key(key_path)
    subset = json.loads(Path(subset_path).read_text(encoding="utf-8"))
    ids = subset_ids(subset, key, key_path)
    all_ids = sorted(key["questions"])
    teacher, teacher_problems = read_labels(teacher_path, ids)
    # Ortak etiket ve değerlendirici dosyaları 144 sorunun hepsini taşır; yalnızca alt küme kullanılır
    joint, joint_problems = read_labels(joint_path, all_ids)
    wanted = set(ids)
    rows = with_raw_agreement(all_kappas(teacher, joint, ids, alpha), teacher, joint, ids, alpha)
    rows = with_bootstrap(rows, teacher, joint, ids, alpha, bootstrap)
    raters = {}
    for name, path in (("A", a_path), ("B", b_path)):
        if path:
            labels, _ = read_labels(path, all_ids)
            raters[name] = all_kappas(teacher, labels, ids, alpha)
    result = {
        "alpha": alpha,
        "note": NOTE,
        "subset_size": len(ids),
        "bootstrap_replicates": max(bootstrap, 0),
        "problems": {"teacher": len(teacher_problems), "joint": sum(p.id in wanted for p in joint_problems)},
        "kappas": rows,
        "distributions": distributions(teacher, joint, ids),
        "raters": raters,
    }
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # JSON'da kategoriler metin olarak (evet/hayır); soru kimliği yok
    printable = {**result, "distributions": [{**d, "categories": [{**c, "category": _show(c["category"])} for c in d["categories"]]}
                                             for d in result["distributions"]]}
    write_json(out_dir / JSON_FILE, printable)
    (out_dir / REPORT_FILE).write_text(render(result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ölçme ve değerlendirme uzmanı ile ortak etiketler arasındaki uyumu hesaplar.")
    parser.add_argument("--ogretmen", type=Path, required=True,
                        help="Uzmanın doldurduğu dosya (seçenek adı geçmişle uyum için 'ogretmen')")
    parser.add_argument("--ortak", type=Path, required=True, help="Tartışmadan sonraki ortak etiket dosyası")
    parser.add_argument("--alt-kume", type=Path, required=True, help="subset.py'nin alt-kume.json dosyası")
    parser.add_argument("--anahtar", type=Path, required=True)
    parser.add_argument("--cikti", type=Path, required=True)
    parser.add_argument("--a", type=Path, help="Değerlendirici A (tartışma öncesi)")
    parser.add_argument("--b", type=Path, help="Değerlendirici B (tartışma öncesi)")
    parser.add_argument("--alfa", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_REPLICATES, metavar="B",
                        help=f"Bootstrap tekrar sayısı (varsayılan {BOOTSTRAP_REPLICATES}); 0 verilirse bootstrap yapılmaz")
    args = parser.parse_args(argv)
    if args.bootstrap < 0:
        parser.error("--bootstrap 0 ya da pozitif olmalı.")
    try:
        result = run(args.ogretmen, args.ortak, args.alt_kume, args.anahtar, args.cikti, args.a, args.b, args.alfa,
                     args.bootstrap)
    except ValidityError as exc:
        print(f"Hata: {exc}")
        return 1
    print(f"Rapor yazıldı: {Path(args.cikti) / REPORT_FILE} ({result['subset_size']} soru).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
