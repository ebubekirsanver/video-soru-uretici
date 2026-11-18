"""Alan öğretmeni alt kümesi: seçim (evaluation/subset.py) ve uyum analizi (evaluation/validity.py).

Sahte anahtar ve sahte etiketler; YouTube'a ve OpenAI'a gidilmez.
"""

import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from app.config import get_settings
from app.services.transcript import Segment, Transcript
from app.services.transcript_cache import write_cached
from evaluation import common, subset, validity
from evaluation import export as export_module
from evaluation.common import (
    BLOOM_LEVELS,
    COL_ANSWERABLE,
    COL_ASR,
    COL_BLOOM,
    COL_ERRORS,
    COL_FLAWS,
    COL_GROUNDED,
    COL_ID,
    COL_NOTE,
    DATA_START_ROW,
    FILL_COLUMNS,
    SHEET_FLAWS,
    SHEET_GUIDE,
    SHEET_QUESTIONS,
)
from evaluation.export import export
from evaluation.stats import kappa

FIELDS = ["biyoloji", "edebiyat", "ingilizce", "matematik", "python", "tarih"]
# Alan başına iki video; kimlikler bilerek alan sırasıyla aynı sırada değil
VIDEOS = {field: [f"{field[:3]}Zvideo{n}"[:11].ljust(11, "x") for n in (2, 1)] for field in FIELDS}


def make_key(drop=()):
    """6 alan × 2 video × 2 koşul × 6 düzey = 144 soru. `drop`: (video, koşul, düzey) üçlüleri anahtara girmez."""
    questions, n = {}, 0
    for field in FIELDS:
        for video in VIDEOS[field]:
            for condition in ("full", "rag"):
                for index, level in enumerate(BLOOM_LEVELS, 1):
                    if (video, condition, level) in drop:
                        continue
                    n += 1
                    questions[f"S{n:03d}"] = {"video_id": video, "topic_index": index, "topic": f"Konu {index}: açıklama",
                                              "condition": condition, "prompt_version": "questions-v3", "bloom_target": level,
                                              "pair_id": f"P{field}{video}{index}", "source": "x.json"}
    videos = {v: {"alan": f, "altyazi_turu": "otomatik", "iki_dilli": f == "ingilizce"} for f in FIELDS for v in VIDEOS[f]}
    return {"seed": 7, "prompt_version": "questions-v3", "videos": videos, "question_count": len(questions),
            "questions": questions, "unproduced": [], "incomplete_pairs": []}


def key_file(tmp_path, key=None, name="anahtar.json"):
    path = tmp_path / name
    path.write_text(json.dumps(key or make_key(), ensure_ascii=False), encoding="utf-8")
    return path


def select(tmp_path, key=None, out="disari"):
    result, path, _ = subset.run(key_file(tmp_path, key), tmp_path / out)
    return result, path


def expected_plan():
    """Kuralın adımları, betikten bağımsız olarak."""
    rng = random.Random("20261118-alt-kume")
    rows = sorted(FIELDS)
    rng.shuffle(rows)
    columns = ["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]
    rng.shuffle(columns)
    table = {rows[i]: {columns[j]: ("rag" if (i + j) % 2 == 0 else "full") for j in range(6)} for i in range(6)}
    levels = ["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]
    assignment = {}
    for field in sorted(FIELDS):
        first, second = sorted(VIDEOS[field])
        chosen = set(rng.sample(levels, 3))
        assignment[field] = {first: chosen, second: set(levels) - chosen}
    return table, assignment


def picked(result):
    return [c for c in result["hucreler"] if c["soru_kimligi"]]


# --- Seçim -------------------------------------------------------------------------------


def test_selects_36_balanced(tmp_path):
    result, _ = select(tmp_path)
    key = make_key()
    cells = picked(result)
    assert len(cells) == 36 and len({c["soru_kimligi"] for c in cells}) == 36
    info = {i: key["questions"][i] for i in (c["soru_kimligi"] for c in cells)}
    field_of = {v: f for f in FIELDS for v in VIDEOS[f]}
    by_field = Counter(field_of[q["video_id"]] for q in info.values())
    assert by_field == {f: 6 for f in FIELDS}
    for field in FIELDS:
        qs = [q for q in info.values() if field_of[q["video_id"]] == field]
        assert sorted(q["bloom_target"] for q in qs) == sorted(BLOOM_LEVELS)  # 6 farklı düzey
        assert Counter(q["condition"] for q in qs) == {"rag": 3, "full": 3}
        assert Counter(q["video_id"] for q in qs) == {v: 3 for v in VIDEOS[field]}
    for level in BLOOM_LEVELS:
        assert Counter(q["condition"] for q in info.values() if q["bloom_target"] == level) == {"rag": 3, "full": 3}
    assert all(c["durum"] == "secildi" for c in result["hucreler"])
    assert result["ozet"] == {"soru": 36, "secildi": 36, "oteki_video": 0, "bos": 0}


def test_cell_question_matches_cell_fields(tmp_path):
    result, _ = select(tmp_path)
    key = make_key()
    for cell in result["hucreler"]:
        q = key["questions"][cell["soru_kimligi"]]
        assert (q["video_id"], q["condition"], q["bloom_target"]) == (cell["istenen_video"], cell["kosul"], cell["bloom_duzeyi"])


def test_condition_table_and_video_assignment_follow_rule(tmp_path):
    result, _ = select(tmp_path)
    table, assignment = expected_plan()
    assert result["kosul_tablosu"] == table
    assert {f: {v: set(levels) for v, levels in a.items()} for f, a in result["video_atamasi"].items()} == assignment
    assert result["tohum"] == "20261118-alt-kume"
    for field in FIELDS:
        assert Counter(result["kosul_tablosu"][field].values()) == {"rag": 3, "full": 3}


def test_same_key_same_bytes(tmp_path):
    _, first = select(tmp_path, out="bir")
    _, second = select(tmp_path, out="iki")
    assert first.read_bytes() == second.read_bytes()
    assert b"\r\n" not in first.read_bytes()  # özet değeri işletim sisteminden bağımsız
    assert json.loads(first.read_text(encoding="utf-8"))["anahtar_sha256"] == subset.sha256_file(tmp_path / "anahtar.json")


def test_existing_file_kept_if_same_and_refused_if_different(tmp_path):
    key = key_file(tmp_path)
    _, path, created = subset.run(key, tmp_path / "disari")
    assert created
    before = path.read_bytes()
    _, _, created = subset.run(key, tmp_path / "disari")
    assert not created and path.read_bytes() == before
    changed = make_key()
    changed["seed"] = 8  # anahtar değişti -> özet değeri değişir -> farklı seçim dosyası
    with pytest.raises(subset.SubsetError, match="üzerine yazılmaz"):
        subset.run(key_file(tmp_path, changed, "anahtar2.json"), tmp_path / "disari")
    assert path.read_bytes() == before


def first_cell(result, field="biyoloji"):
    return next(c for c in result["hucreler"] if c["alan"] == field)


def test_missing_question_taken_from_other_video(tmp_path):
    base, _ = select(tmp_path, out="once")
    cell = first_cell(base)
    drop = {(cell["istenen_video"], cell["kosul"], cell["bloom_duzeyi"])}
    result, _ = select(tmp_path, make_key(drop), out="sonra")
    changed = first_cell(result)
    other = next(v for v in VIDEOS["biyoloji"] if v != cell["istenen_video"])
    assert changed["durum"] == "oteki_video" and changed["secilen_video"] == other
    assert changed["istenen_video"] == cell["istenen_video"]
    assert result["ozet"] == {"soru": 36, "secildi": 35, "oteki_video": 1, "bos": 0}


def test_missing_in_both_videos_leaves_cell_empty(tmp_path):
    base, _ = select(tmp_path, out="once")
    cell = first_cell(base)
    drop = {(v, cell["kosul"], cell["bloom_duzeyi"]) for v in VIDEOS["biyoloji"]}
    result, _ = select(tmp_path, make_key(drop), out="sonra")
    empty = first_cell(result)
    assert empty["durum"] == "bos" and empty["soru_kimligi"] is None and empty["secilen_video"] is None
    assert len(picked(result)) == 35 and result["ozet"]["bos"] == 1


@pytest.mark.parametrize("folder", ["backend/alt-kume-deneme", "docs/bulgular/alt-kume-deneme", "frontend/x", "."])
def test_output_inside_repo_refused(tmp_path, folder):
    target = subset.REPO_ROOT / folder
    with pytest.raises(subset.SubsetError, match="depo içinde"):
        subset.run(key_file(tmp_path), target)
    assert not (target / "alt-kume.json").exists()
    assert subset.main(["--anahtar", str(tmp_path / "anahtar.json"), "--cikti", str(target)]) == 1


def test_screen_output_has_no_ids_or_conditions(tmp_path, capsys):
    base, _ = select(tmp_path, out="once")
    cell = first_cell(base)
    key = key_file(tmp_path, make_key({(cell["istenen_video"], cell["kosul"], cell["bloom_duzeyi"])}), "eksik.json")
    assert subset.main(["--anahtar", str(key), "--cikti", str(tmp_path / "ekran")]) == 0
    out = capsys.readouterr().out
    assert "Seçilen soru: 36 / 36" in out and "Öbür videodan alınan hücre: 1" in out and "SHA-256:" in out
    assert not any(i in out for i in make_key()["questions"])
    assert "rag" not in out and "full" not in out
    assert subset.sha256_file(tmp_path / "ekran" / "alt-kume.json") in out


def test_key_without_rule_fields_refused(tmp_path):
    key = make_key()
    key["videos"][VIDEOS["tarih"][0]]["alan"] = "Tarih"
    with pytest.raises(subset.SubsetError, match="altı alan"):
        select(tmp_path, key)
    key = make_key()
    del key["videos"]
    with pytest.raises(subset.SubsetError, match="videos"):
        select(tmp_path, key)


# --- Alan öğretmeni dosyası ------------------------------------------------------------------


def run_file(tmp_path, video):
    """pilot-2 biçiminde iki koşullu çalıştırma dosyası."""
    parts = {}
    for mode in ("full", "rag"):
        traces, questions = [], []
        for i, level in enumerate(BLOOM_LEVELS, 1):
            topic = f"Konu {i}: açıklama"
            traces.append({"topic": topic, "bloom_level": level, "outcome": "ok"})
            questions.append({"question": f"{video} {i} {mode} sorusu nedir?", "options": ["Bir", "İki", "Üç", "Dört"],
                              "correct_index": i % 4, "explanation": "a", "source_quote": "q", "source_start_seconds": 1.0,
                              "verified": True, "quote_match": "exact", "topic": topic, "bloom_level": level})
        parts[mode] = {"response": {"video_id": video, "questions": questions},
                       "topic_generation": {"prompt_version": "questions-v3", "context_mode": mode, "per_topic": traces}}
    path = tmp_path / f"girdi-{video}.json"
    path.write_text(json.dumps({"runs": parts}, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    """Önbellekte transkriptler, 12 girdi dosyası ve video bilgi dosyası (hepsi tmp_path içinde)."""
    monkeypatch.setenv("TRANSCRIPT_CACHE_DIR", str(tmp_path / "transcripts"))
    get_settings.cache_clear()
    languages = get_settings().transcript_language_list
    inputs = []
    for field in FIELDS:
        for video in VIDEOS[field]:
            write_cached(Transcript(video, "tr", True, [Segment("merhaba arkadaşlar", 5.0, 3.0)]), languages)
            inputs.append(run_file(tmp_path, video))
    info = tmp_path / "video-bilgisi.json"
    info.write_text(json.dumps({"videos": make_key()["videos"]}, ensure_ascii=False), encoding="utf-8")
    yield tmp_path, inputs, info
    get_settings.cache_clear()


@pytest.fixture
def exported(prepared):
    tmp_path, inputs, info = prepared
    export(inputs, 11, tmp_path / "dagitim", tmp_path / "gizli", info, "questions-v3")
    return tmp_path, inputs


def test_teacher_file_same_format_only_subset_shuffled(exported):
    tmp_path, inputs = exported
    key_path = tmp_path / "gizli" / "anahtar.json"
    teacher = tmp_path / "ogretmen.xlsx"
    code = subset.main(["--anahtar", str(key_path), "--cikti", str(tmp_path / "gizli"), "--ogretmen-dosyasi", str(teacher),
                        "--tohum", "5", "--girdi", *map(str, inputs)])
    assert code == 0
    chosen = json.loads((tmp_path / "gizli" / "alt-kume.json").read_text(encoding="utf-8"))
    ids = sorted(c["soru_kimligi"] for c in chosen["hucreler"])
    rater = load_workbook(tmp_path / "dagitim" / "degerlendirici-A.xlsx")
    book = load_workbook(teacher)
    sheet, rater_sheet = book[SHEET_QUESTIONS], rater[SHEET_QUESTIONS]
    assert [c.value for c in sheet[1]] == [c.value for c in rater_sheet[1]]  # aynı sütunlar
    assert [c.value for c in sheet[2]] == [c.value for c in rater_sheet[2]]  # açıklama satırı
    rows = [[c.value for c in r] for r in sheet.iter_rows(min_row=DATA_START_ROW)]
    order = [r[0] for r in rows]
    expected = list(ids)
    random.Random(5).shuffle(expected)
    assert order == expected  # yalnızca alt küme, tohumla karıştırılmış
    rater_rows = {r[0].value: [c.value for c in r] for r in rater_sheet.iter_rows(min_row=DATA_START_ROW)}
    assert all(row == rater_rows[row[0]] for row in rows)  # soru metni ve seçenekler aynı
    assert SHEET_GUIDE in book.sheetnames and SHEET_FLAWS in book.sheetnames
    assert len(sheet.data_validations.dataValidation) == len(rater_sheet.data_validations.dataValidation) == 5
    videos = {r[1].rsplit("/", 1)[1] for r in rows}
    assert {s for s in book.sheetnames if s.startswith("T-")} == {f"T-{v}" for v in videos}


def test_teacher_file_refuses_inputs_not_matching_key(exported):
    tmp_path, inputs = exported
    key_path = tmp_path / "gizli" / "anahtar.json"
    key = json.loads(key_path.read_text(encoding="utf-8"))
    key["seed"] = 12  # başka tohum: kimlikler tutmaz
    other = tmp_path / "gizli2" / "anahtar.json"
    other.parent.mkdir()
    other.write_text(json.dumps(key, ensure_ascii=False), encoding="utf-8")
    result, _, _ = subset.run(other, tmp_path / "gizli2")
    with pytest.raises(subset.SubsetError, match="uyuşmuyor"):
        subset.write_teacher_file(tmp_path / "x.xlsx", key, result, inputs, 5)
    assert not (tmp_path / "x.xlsx").exists()


def test_teacher_file_needs_seed_and_inputs(tmp_path):
    with pytest.raises(SystemExit):
        subset.main(["--anahtar", str(key_file(tmp_path)), "--cikti", str(tmp_path / "d"), "--ogretmen-dosyasi", "x.xlsx"])


# --- Uyum analizi ------------------------------------------------------------------------------


IDS = ["S001", "S002", "S003", "S004", "S005", "S006"]
SUBSET = IDS[:4]
TEACHER = {
    "S001": ("Hatırlama", 0, "", "evet", 5, "hayır"),
    "S002": ("Anlama", 2, "4, 6", "hayır", 2, "evet"),
    "S003": ("Anlama", 1, "4", "evet", 4, "hayır"),
    "S004": ("Uygulama", 3, "1, 2, 3", "evet", 3, None),  # tanıma hatası boş
}
JOINT = {
    "S001": ("Hatırlama", 0, "", "evet", 4, "hayır"),
    "S002": ("Anlama", 1, "6", "hayır", 2, "hayır"),
    "S003": ("Uygulama", 1, "4", "evet", 4, "hayır"),
    "S004": ("Uygulama", 3, "1, 2, 3", "hayır", 3, "hayır"),
    "S005": (None, None, "", None, None, None),  # alt küme dışında; sorunu sayılmaz
    "S006": ("Yaratma", 0, "", "evet", 5, "hayır"),
}


def label_book(path, rows):
    wb = Workbook()
    sheet = wb.active
    sheet.title = SHEET_QUESTIONS
    sheet.append([COL_ID, *FILL_COLUMNS])
    for item_id, (bloom, errors, flaws, grounded, answerable, asr) in rows.items():
        values = {COL_BLOOM: bloom, COL_ERRORS: errors, COL_FLAWS: flaws, COL_GROUNDED: grounded,
                  COL_ANSWERABLE: answerable, COL_ASR: asr, COL_NOTE: None}
        sheet.append([item_id, *[values[c] for c in FILL_COLUMNS]])
    wb.save(path)
    return path


@pytest.fixture
def validity_files(tmp_path):
    key = {"questions": {i: {"video_id": "v", "condition": "rag", "bloom_target": "Anlama"} for i in IDS}}
    key_path = key_file(tmp_path, key)
    alt = tmp_path / "alt-kume.json"
    alt.write_text(json.dumps({"anahtar_sha256": subset.sha256_file(key_path),
                               "hucreler": [{"soru_kimligi": i, "durum": "secildi"} for i in SUBSET]
                               + [{"soru_kimligi": None, "durum": "bos"}]}), encoding="utf-8")
    return tmp_path, key_path, alt, label_book(tmp_path / "ogretmen.xlsx", TEACHER), label_book(tmp_path / "ortak.xlsx", JOINT)


def column(rows, index):
    return [rows[i][index] for i in SUBSET]


def test_validity_raw_agreement_kappa_and_distributions(validity_files):
    tmp_path, key_path, alt, teacher, joint = validity_files
    result = validity.run(teacher, joint, alt, key_path, tmp_path / "rapor")
    rows = {r["name"]: r for r in result["kappas"]}
    bloom = rows["Bloom düzeyi"]
    assert bloom["n"] == 4 and bloom["excluded"] == 0
    assert bloom["raw"]["k"] == 3 and bloom["raw"]["rate"] == pytest.approx(0.75)
    expected = kappa(column(TEACHER, 0), column(JOINT, 0), BLOOM_LEVELS)
    assert bloom["kappa"] == pytest.approx(expected["kappa"]) and bloom["ci_low"] == pytest.approx(expected["ci_low"])
    weighted = kappa(column(TEACHER, 0), column(JOINT, 0), BLOOM_LEVELS, weighted=True)
    assert rows["Bloom düzeyi (doğrusal ağırlıklı)"]["kappa"] == pytest.approx(weighted["kappa"])
    # Kabul edilebilirlik hata sayısından: öğretmen T F T F, ortak T T T F
    acceptable = rows["Kabul edilebilirlik (0-1 hata)"]
    assert acceptable["raw"]["k"] == 3
    assert acceptable["kappa"] == pytest.approx(kappa([True, False, True, False], [True, True, True, False], [True, False])["kappa"])
    answer = kappa(column(TEACHER, 4), column(JOINT, 4), [1, 2, 3, 4, 5])
    assert rows["Cevaplanabilirlik"]["kappa"] == pytest.approx(answer["kappa"])
    assert rows["Cevaplanabilirlik"]["weighted"] is False
    assert rows["Cevaplanabilirlik (doğrusal ağırlıklı)"]["kappa"] == pytest.approx(
        kappa(column(TEACHER, 4), column(JOINT, 4), [1, 2, 3, 4, 5], weighted=True)["kappa"])
    asr = rows["Tanıma hatası kaynaklı"]
    assert asr["n"] == 3 and asr["excluded"] == 1  # öğretmenin boş bıraktığı hücre
    assert asr["kappa"] == pytest.approx(kappa([False, True, False], [False, False, False], [True, False])["kappa"])
    dist = {d["field"]: d for d in result["distributions"]}
    assert [(c["category"], c["teacher"], c["joint"]) for c in dist["bloom"]["categories"]][:3] == [
        ("Hatırlama", 1, 1), ("Anlama", 2, 1), ("Uygulama", 1, 2)]
    assert [(c["category"], c["teacher"], c["joint"]) for c in dist["grounded"]["categories"]] == [(True, 3, 2), (False, 1, 2)]
    assert dist["asr_error"]["n"] == 3
    assert result["problems"] == {"teacher": 1, "joint": 0}  # alt küme dışındaki boş satır sayılmaz
    assert result["subset_size"] == 4


def test_validity_report_note_and_no_ids(validity_files):
    tmp_path, key_path, alt, teacher, joint = validity_files
    validity.run(teacher, joint, alt, key_path, tmp_path / "rapor", a_path=joint, b_path=teacher)
    report = (tmp_path / "rapor" / "alan-ogretmeni-uyumu.md").read_text(encoding="utf-8")
    assert validity.NOTE in report.split("## Uyum")[0]
    assert not any(i in report for i in IDS)
    assert "rag" not in report and "full" not in report  # koşul yazılmaz
    assert "## Ek bilgi: tartışma öncesi etiketlerle" in report and "Kappa (A)" in report and "Kappa (B)" in report
    data = json.loads((tmp_path / "rapor" / "alan-ogretmeni-uyumu.json").read_text(encoding="utf-8"))
    assert not any(i in json.dumps(data) for i in IDS)


def test_validity_pre_discussion_kappas(validity_files):
    tmp_path, key_path, alt, teacher, joint = validity_files
    result = validity.run(teacher, joint, alt, key_path, tmp_path / "rapor", a_path=joint, b_path=teacher)
    main_rows, a_rows, b_rows = result["kappas"], result["raters"]["A"], result["raters"]["B"]
    assert [r["kappa"] for r in a_rows] == [r["kappa"] for r in main_rows]  # A = ortak dosya: ana sonuçla aynı
    assert next(r for r in b_rows if r["name"] == "Bloom düzeyi")["kappa"] == pytest.approx(1.0)


def test_validity_refuses_other_key(validity_files):
    tmp_path, key_path, alt, teacher, joint = validity_files
    other = key_file(tmp_path, {"questions": {i: {} for i in IDS}, "x": 1}, "baska.json")
    with pytest.raises(validity.ValidityError, match="SHA-256"):
        validity.run(teacher, joint, alt, other, tmp_path / "rapor")


# --- Depo içine yazma denetimi (anahtar, değerlendirici ve alan öğretmeni dosyaları) ----------------


def repo_target(*parts):
    """Depo içinde, var olmayan bir yol; test sonunda da oluşmamış olmalı."""
    path = common.REPO_ROOT.joinpath(*parts)
    assert not path.exists()
    return path


def export_args(inputs, info, out, key_dir):
    return ["--girdi", *map(str, inputs), "--video-bilgisi", str(info), "--tohum", "11",
            "--cikti", str(out), "--anahtar-cikti", str(key_dir), "--istem-surumu", "questions-v3"]


def test_export_key_dir_inside_repo_refused(prepared, capsys):
    tmp_path, inputs, info = prepared
    key_dir = repo_target("docs", "bulgular", "depo-ici-anahtar-denemesi")
    code = export_module.main(export_args(inputs, info, tmp_path / "dagitim", key_dir))
    assert code == 1
    out = capsys.readouterr().out
    assert "depo içinde olamaz" in out and "anahtar dosyası koşul bilgisi taşır" in out
    assert not key_dir.exists() and not (tmp_path / "dagitim").exists()  # hiçbir dosya oluşmadı


def test_export_rater_dir_inside_repo_refused(prepared, capsys):
    tmp_path, inputs, info = prepared
    out_dir = repo_target("backend", "depo-ici-degerlendirici-denemesi")
    code = export_module.main(export_args(inputs, info, out_dir, tmp_path / "gizli"))
    assert code == 1
    assert "değerlendirici dosyaları tam transkript içerir" in capsys.readouterr().out
    assert not out_dir.exists() and not (tmp_path / "gizli").exists()
    with pytest.raises(export_module.ExportError, match="depo içinde"):  # fonksiyon da reddeder
        export(inputs, 11, out_dir, tmp_path / "gizli", info, "questions-v3")
    assert not out_dir.exists()


def test_export_outside_repo_works_as_before(prepared):
    tmp_path, inputs, info = prepared
    assert export_module.main(export_args(inputs, info, tmp_path / "dagitim", tmp_path / "gizli")) == 0
    assert (tmp_path / "dagitim" / "degerlendirici-A.xlsx").exists() and (tmp_path / "gizli" / "anahtar.json").exists()


def test_teacher_file_inside_repo_refused_before_anything(exported, capsys):
    tmp_path, inputs = exported
    teacher = repo_target("docs", "bulgular", "alan-ogretmeni-deneme.xlsx")
    out_dir = tmp_path / "secim"
    code = subset.main(["--anahtar", str(tmp_path / "gizli" / "anahtar.json"), "--cikti", str(out_dir),
                        "--ogretmen-dosyasi", str(teacher), "--tohum", "5", "--girdi", *map(str, inputs)])
    assert code == 1
    assert "alan öğretmeni dosyası tam transkript içerir" in capsys.readouterr().out
    assert not teacher.exists() and not out_dir.exists()  # alt-kume.json da yazılmadı
    with pytest.raises(subset.SubsetError, match="depo içinde"):
        subset.write_teacher_file(teacher, {}, {}, inputs, 5)


def test_inside_repo_cases(monkeypatch):
    root = common.REPO_ROOT
    assert common.inside_repo(root)  # kökün kendisi
    assert common.inside_repo(root / "backend" / "evaluation")  # alt klasör
    assert common.inside_repo(root / "yok" / "olmayan.json")  # henüz var olmayan yol
    assert not common.inside_repo(root.parent / (root.name + "-kardes"))  # kardeş klasör (aynı önekle)
    assert not common.inside_repo(root.parent)
    assert common.inside_repo(root / "backend" / ".." / "docs")  # .. içeren
    assert not common.inside_repo(root / "backend" / ".." / ".." / "baska")
    monkeypatch.chdir(root / "backend")
    assert common.inside_repo(Path("../docs/bulgular"))  # göreli yol
    assert not common.inside_repo(Path("../../baska-klasor"))


@pytest.mark.skipif(sys.platform != "win32", reason="büyük-küçük harf yalnızca Windows'ta gözetilmez")
def test_inside_repo_ignores_case_on_windows():
    assert common.inside_repo(Path(str(common.REPO_ROOT).upper()) / "docs")


def test_check_outside_repo_message():
    with pytest.raises(common.InsideRepoError) as exc:
        common.check_outside_repo(common.REPO_ROOT / "x", "Bir dosya", "çünkü gizli")
    assert str(exc.value) == "Bir dosya depo içinde olamaz: çünkü gizli."
    common.check_outside_repo(common.REPO_ROOT.parent / (common.REPO_ROOT.name + "-disari"), "Bir dosya", "gerekçe")
