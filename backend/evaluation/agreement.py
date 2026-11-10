"""İki değerlendiricinin tartışmadan önceki etiketleriyle uyum hesabı.

Çıktılar: uyum raporu (md ve JSON), tartışma toplantısı için anlaşmazlık listesi
ve ortak etiket şablonu. Anlaşmazlık listesi ve şablon kimlikleri taşır, koşul
ve hedef düzey bilgisi taşımaz: toplantı da kör yapılır.

Çalıştırma (backend klasöründen):
    python -m evaluation.agreement --a <A.xlsx> --b <B.xlsx> --anahtar <anahtar.json> --cikti <klasör>
"""

import argparse
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font

from evaluation.common import (
    BLOOM_LEVELS,
    COL_ANSWERABLE,
    COL_BLOOM,
    COL_ERRORS,
    COL_FLAWS,
    COL_GROUNDED,
    COL_ID,
    COL_QUESTION,
    COL_VIDEO,
    DEFAULT_ALPHA,
    FILL_COLUMNS,
    SHEET_QUESTIONS,
    interval,
    load_key,
    num,
    table,
    write_json,
)
from evaluation.labels import Label, read_labels
from evaluation.stats import kappa

METHOD_NOTE = ("Güven aralığı: Fleiss, Cohen ve Everitt (1969) büyük örneklem varyansı, κ ± z·SE, [-1; 1] içine kırpılır. "
               "Doğrusal ağırlık: 1 - |i-j| / (k-1). Bir alanı eksik ya da geçersiz olan soru o alanın hesabına girmez.")
# (rapor adı, alan, kategoriler, doğrusal ağırlıklı mı)
KAPPAS = [
    ("Bloom düzeyi", "bloom", BLOOM_LEVELS, False),
    ("Bloom düzeyi (doğrusal ağırlıklı)", "bloom", BLOOM_LEVELS, True),
    ("Kabul edilebilirlik (0-1 hata)", "acceptable", [True, False], False),
    ("Kaynağa dayalılık", "grounded", [True, False], False),
    ("Cevaplanabilirlik (doğrusal ağırlıklı)", "answerable", [1, 2, 3, 4, 5], True),
]
# Anlaşmazlık listesindeki alanlar; kabul edilebilirlik hata sayısından türer
DISAGREEMENT_FIELDS = [
    (COL_BLOOM, "bloom"),
    (COL_ERRORS, "errors"),
    ("Kabul edilebilirlik (0-1 hata)", "acceptable"),
    (COL_FLAWS, "flaws"),
    (COL_GROUNDED, "grounded"),
    (COL_ANSWERABLE, "answerable"),
]


def compute_kappas(a: dict[str, Label], b: dict[str, Label], ids: list[str], alpha: float = DEFAULT_ALPHA) -> list[dict]:
    results = []
    for name, field, categories, weighted in KAPPAS:
        pairs = [(getattr(a[i], field), getattr(b[i], field)) for i in ids if i in a and i in b]
        used = [(x, y) for x, y in pairs if x is not None and y is not None]
        result = kappa([x for x, _ in used], [y for _, y in used], categories, weighted, alpha)
        results.append({"name": name, "field": field, "weighted": weighted, "excluded": len(ids) - len(used), **result})
    return results


def _show(value) -> str:
    if isinstance(value, bool):
        return "evet" if value else "hayır"
    if isinstance(value, tuple):
        return ", ".join(str(v) for v in value) or "(boş)"
    return str(value)


def disagreements(a: dict[str, Label], b: dict[str, Label], ids: list[str]) -> list[dict]:
    """İki değerlendiricinin de etiketlediği ama farklı değer verdiği sorular ve alanlar."""
    rows = []
    for item_id in ids:
        if item_id not in a or item_id not in b:
            continue
        for column, field in DISAGREEMENT_FIELDS:
            x, y = getattr(a[item_id], field), getattr(b[item_id], field)
            if field == "flaws" and x is not None and y is not None:
                x, y = tuple(sorted(x)), tuple(sorted(y))
            if x is not None and y is not None and x != y:
                rows.append({"id": item_id, "field": column, "a": _show(x), "b": _show(y)})
    return rows


def _questions_by_id(path: Path) -> dict[str, tuple[str, str]]:
    rows = load_workbook(path, data_only=True)[SHEET_QUESTIONS].iter_rows(values_only=True)
    header = list(next(rows))
    i, v, q = header.index(COL_ID), header.index(COL_VIDEO), header.index(COL_QUESTION)
    return {r[i]: (r[v], r[q]) for r in rows if r[i]}


def write_disagreements(path: Path, rows: list[dict], source: Path) -> None:
    wb = Workbook()
    wb.properties.creator = ""
    sheet = wb.active
    sheet.title = "Anlaşmazlıklar"
    sheet.append([COL_ID, COL_VIDEO, COL_QUESTION, "Alan", "Değerlendirici A", "Değerlendirici B", "Ortak karar"])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    texts = _questions_by_id(source)
    for row in rows:
        video, question = texts.get(row["id"], ("", ""))
        sheet.append([row["id"], video, None, row["field"], None, None, None])
        last = sheet.max_row
        for column, value in ((3, question), (5, row["a"]), (6, row["b"])):
            sheet.cell(last, column).value = value
            sheet.cell(last, column).data_type = "s"
            sheet.cell(last, column).alignment = Alignment(wrap_text=True, vertical="top")
    sheet.column_dimensions["B"].width = 28
    sheet.column_dimensions["C"].width = 60
    sheet.column_dimensions["D"].width = 28
    sheet.freeze_panes = "A2"
    wb.save(path)


def write_joint_template(path: Path, source: Path) -> None:
    """Değerlendirici dosyasının kopyası; doldurulan sütunlar boşaltılır, açılır listeler korunur."""
    wb = load_workbook(source)
    sheet = wb[SHEET_QUESTIONS]
    header = [c.value for c in sheet[1]]
    for column in FILL_COLUMNS:
        index = header.index(column) + 1
        for row in range(2, sheet.max_row + 1):
            sheet.cell(row, index).value = None
    wb.save(path)


def render_report(kappas: list[dict], problems: list[dict], rows: list[dict], alpha: float) -> str:
    level = round((1 - alpha) * 100)
    lines = ["# Değerlendiriciler arası uyum", "", "Tartışmadan önceki etiketlerle hesaplandı.", ""]
    lines += table(["Alan", "n", "Çıkarılan", "Oransal uyum", "Kappa", "SE", f"%{level} GA", "Not"],
                   [[k["name"], k["n"], k["excluded"], num(k["agreement"]), num(k["kappa"]), num(k["se"]),
                     interval(k["ci_low"], k["ci_high"]), k["note"] or ""] for k in kappas])
    lines += ["", METHOD_NOTE, "", f"Anlaşmazlık satırı: {len(rows)}.", "", "## Eksik ya da geçersiz hücreler", ""]
    if problems:
        lines += table(["Dosya", "Kimlik", "Sütun", "Değer", "Sorun"],
                       [[p["file"], p["id"], p["column"], p["value"], p["reason"]] for p in problems])
    else:
        lines.append("Yok.")
    return "\n".join(lines) + "\n"


def run(a_path: Path, b_path: Path, key_path: Path, out_dir: Path, alpha: float = DEFAULT_ALPHA) -> dict:
    ids = sorted(load_key(key_path)["questions"])
    a, problems_a = read_labels(a_path, ids)
    b, problems_b = read_labels(b_path, ids)
    problems = [p.as_dict() for p in problems_a + problems_b]
    kappas = compute_kappas(a, b, ids, alpha)
    rows = disagreements(a, b, ids)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"alpha": alpha, "method": METHOD_NOTE, "kappas": kappas, "problems": problems, "disagreements": rows}
    write_json(out_dir / "uyum.json", result)
    (out_dir / "uyum-raporu.md").write_text(render_report(kappas, problems, rows, alpha), encoding="utf-8")
    write_disagreements(out_dir / "anlasmazliklar.xlsx", rows, a_path)
    write_joint_template(out_dir / "ortak-etiket-sablonu.xlsx", a_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Değerlendiriciler arası uyumu hesaplar.")
    parser.add_argument("--a", type=Path, required=True, help="Değerlendirici A dosyası")
    parser.add_argument("--b", type=Path, required=True, help="Değerlendirici B dosyası")
    parser.add_argument("--anahtar", type=Path, required=True)
    parser.add_argument("--cikti", type=Path, required=True)
    parser.add_argument("--alfa", type=float, default=DEFAULT_ALPHA, help="Anlamlılık düzeyi; aralıklar 1 - alfa düzeyinde")
    args = parser.parse_args()
    result = run(args.a, args.b, args.anahtar, args.cikti, args.alfa)
    print(f"{len(result['disagreements'])} anlaşmazlık satırı, {len(result['problems'])} sorunlu hücre.")


if __name__ == "__main__":
    main()
