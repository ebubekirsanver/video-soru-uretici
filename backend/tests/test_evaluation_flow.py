"""Dışa aktarma, etiket okuma, uyum ve analiz. Sentetik veri; ağ yok, gerçek etiket yok."""

import json

import pytest
from openpyxl import load_workbook

from app.config import get_settings
from app.services.transcript import Segment, Transcript
from app.services.transcript_cache import write_cached
from evaluation import agreement, analysis
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
    COLUMN_DESCRIPTIONS,
    DATA_START_ROW,
    DESCRIPTION_LABEL,
    FILL_COLUMNS,
    GUIDE_PLACEHOLDER,
    SHEET_FLAWS,
    SHEET_GUIDE,
    SHEET_QUESTIONS,
    VISIBLE_COLUMNS,
    load_key,
)
from evaluation.export import ExportError, collect, export, find_secrets, read_flaws, read_runs, read_video_info
from evaluation.labels import Label, LabelError, read_labels

VIDEOS = ["aaaaaaaaaaa", "bbbbbbbbbbb"]
QUOTE = "gizli alıntı metni transkriptte olmayan cümle"
SECRET_REASONING = "gizli gerekçe metni"
VIDEO_INFO = {
    VIDEOS[0]: {"alan": "biyoloji", "altyazi_turu": "elle", "iki_dilli": False},
    VIDEOS[1]: {"alan": "ingilizce", "altyazi_turu": "otomatik", "iki_dilli": True},
    "ccccccccccc": {"alan": "tarih", "altyazi_turu": "otomatik", "iki_dilli": False},
}


def info_file(tmp_path, videos=None):
    path = tmp_path / "video-bilgisi.json"
    path.write_text(json.dumps({"videos": videos or VIDEO_INFO}, ensure_ascii=False), encoding="utf-8")
    return path


def trace(topic, level, outcome="ok"):
    return {"topic": topic, "bloom_level": level, "outcome": outcome, "context_words": 10, "produced": outcome == "ok",
            "retrieved": None, "skip_reason": None, "truncated": False}


def question(video, index, mode, topic, level, text=None):
    return {"question": text or f"{video} {index} {mode} sorusu nedir?", "options": ["Birinci", "İkinci", "Üçüncü", "= 10"],
            "correct_index": index % 4, "explanation": "açıklama", "source_quote": QUOTE, "source_start_seconds": 12.0,
            "verified": True, "quote_match": "exact", "topic": topic, "bloom_level": level}


def run_part(video, mode, version="questions-v3", outcomes=None):
    outcomes = outcomes or {}
    traces, questions = [], []
    for i, level in enumerate(BLOOM_LEVELS, 1):
        topic = f"Konu {i}: açıklama"
        outcome = outcomes.get(i, "ok")
        traces.append(trace(topic, level, outcome))
        if outcome == "ok":
            questions.append(question(video, i, mode, topic, level))
    return {
        "response": {"video_id": video, "questions": questions, "prompt_version": version},
        "topic_generation": {"prompt_version": version, "context_mode": mode, "topics": [t["topic"] for t in traces], "per_topic": traces,
                             "questions_reasoning": [{"reasoning": SECRET_REASONING}]},
    }


def pilot_file(tmp_path, video, outcomes=None):
    """pilot-2 biçimi: v3 ve v4 çalıştırmaları bir arada."""
    outcomes = outcomes or {}
    path = tmp_path / f"pilot-2-{video}.json"
    runs = {f"{v}-{m}": run_part(video, m, f"questions-{v}", outcomes.get(m)) for v in ("v3", "v4") for m in ("full", "rag")}
    path.write_text(json.dumps({"experiment": "pilot-2", "runs": runs}, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("TRANSCRIPT_CACHE_DIR", str(tmp_path / "transcripts"))
    get_settings.cache_clear()
    languages = get_settings().transcript_language_list
    for video in VIDEOS:
        write_cached(Transcript(video, "tr", True, [Segment("merhaba [Müzik] arkadaşlar", 65.0, 3.0)]), languages)
    return tmp_path


def do_export(workspace, seed=42, outcomes=None, name="cikti"):
    paths = [pilot_file(workspace, VIDEOS[0], outcomes), pilot_file(workspace, VIDEOS[1])]
    out, key_dir = workspace / name, workspace / f"{name}-anahtar"
    export(paths, seed, out, key_dir, info_file(workspace), "questions-v3")
    return out / "degerlendirici-A.xlsx", out / "degerlendirici-B.xlsx", key_dir / "anahtar.json"


def sheet_rows(path, sheet=SHEET_QUESTIONS):
    return [list(r) for r in load_workbook(path)[sheet].iter_rows(values_only=True)]


def ids_of(path):
    return [r[0] for r in sheet_rows(path)[DATA_START_ROW - 1:]]


def fill(path, target, values, skip=()):
    """Dosyayı doldurur. `values(id)`: sütun -> değer sözlüğü."""
    wb = load_workbook(path)
    sheet = wb[SHEET_QUESTIONS]
    header = [c.value for c in sheet[1]]
    for row in range(DATA_START_ROW, sheet.max_row + 1):
        item_id = sheet.cell(row, 1).value
        for column, value in values(item_id).items():
            if (item_id, column) not in skip:
                sheet.cell(row, header.index(column) + 1).value = value
    wb.save(target)
    return target


def perfect(item_id):
    return {COL_BLOOM: "Anlama", COL_ERRORS: 1, COL_FLAWS: "4", COL_GROUNDED: "evet", COL_ANSWERABLE: 4, COL_ASR: "hayır"}


# --- Dışa aktarma -------------------------------------------------------------------


def test_reads_three_input_shapes(tmp_path):
    part = run_part(VIDEOS[0], "full")
    record = tmp_path / "20261104-120000-x-questions.json"
    record.write_text(json.dumps({"outcome": "ok", **part}), encoding="utf-8")
    pilot1 = tmp_path / "pilot-1-x.json"
    pilot1.write_text(json.dumps({"conditions": {"full": part}}), encoding="utf-8")
    pilot2 = tmp_path / "pilot-2-x.json"
    pilot2.write_text(json.dumps({"runs": {"v3-full": part}}), encoding="utf-8")
    assert read_runs(record)[0].source == record.name
    assert read_runs(pilot1)[0].source == "pilot-1-x.json#full"
    assert read_runs(pilot2)[0].source == "pilot-2-x.json#v3-full"


def test_unknown_or_failed_input_rejected(tmp_path):
    path = tmp_path / "x.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ExportError):
        read_runs(path)
    path.write_text(json.dumps({"outcome": "error", "topic_generation": None, "response": None}), encoding="utf-8")
    with pytest.raises(ExportError):
        read_runs(path)


def test_mixed_versions_need_selection(tmp_path):
    runs = read_runs(pilot_file(tmp_path, VIDEOS[0]))
    with pytest.raises(ExportError, match="birden çok istem sürümü"):
        collect(runs, None)
    questions, _, version = collect(runs, "questions-v4")
    assert version == "questions-v4" and len(questions) == 12


def test_rater_files_identical_and_columns(workspace):
    a, b, _ = do_export(workspace)
    assert sheet_rows(a)[0] == VISIBLE_COLUMNS + FILL_COLUMNS
    assert sheet_rows(a) == sheet_rows(b)
    assert len(sheet_rows(a)) == 2 + 24  # başlık + açıklama + 2 video × 2 koşul × 6 konu
    assert ids_of(a)[:2] == ["S001", "S002"]
    assert all(v is None for row in sheet_rows(a)[DATA_START_ROW - 1:] for v in row[len(VISIBLE_COLUMNS):])


def test_description_row_explains_asr_column(workspace):
    a, _, _ = do_export(workspace)
    header, description = sheet_rows(a)[:2]
    assert description[0] == DESCRIPTION_LABEL
    assert description[header.index(COL_ASR)] == COLUMN_DESCRIPTIONS[COL_ASR]
    assert COLUMN_DESCRIPTIONS[COL_ASR].startswith("Sorudaki hata (yanlış bilgi, anlamsız ifade, yanlış doğru cevap)")
    assert load_workbook(a)[SHEET_QUESTIONS].freeze_panes == f"A{DATA_START_ROW}"


def test_hidden_fields_not_in_any_cell(workspace):
    a, _, key_path = do_export(workspace)
    wb = load_workbook(a)
    cells = [c.value for ws in wb for row in ws.iter_rows() for c in row if isinstance(c.value, str)]
    assert not any(QUOTE in c or SECRET_REASONING in c for c in cells)
    exact = {"full", "rag", "questions-v3", "questions-v4", *BLOOM_LEVELS}
    question_cells = [c.value for row in wb[SHEET_QUESTIONS].iter_rows() for c in row if isinstance(c.value, str)]
    # "Bloom düzeyi" sütun adı kalır; hedef düzey, koşul ve sürüm hücre olarak geçmez
    assert not exact & set(question_cells)
    assert not any("questions-v" in c or "12" == c or "0:12" == c for c in question_cells)
    assert not any("Konu 1" in c for c in cells)  # konu metni de koşulu/hedefi açmasın
    assert wb.properties.creator in (None, "")
    assert [ws.sheet_state for ws in wb] == ["visible"] * len(wb.sheetnames)
    assert not wb.defined_names


def test_condition_and_level_only_in_key(workspace):
    a, _, key_path = do_export(workspace)
    key = load_key(key_path)
    info = key["questions"]["S001"]
    assert set(info) == {"video_id", "topic_index", "topic", "condition", "prompt_version", "bloom_target", "pair_id", "source"}
    assert info["bloom_target"] in BLOOM_LEVELS and info["condition"] in ("full", "rag")
    assert "#v3-" in info["source"] and key["seed"] == 42 and key["question_count"] == 24
    assert key["videos"] == {v: VIDEO_INFO[v] for v in VIDEOS}  # yalnızca kullanılan videolar
    assert "tmp" not in key_path.read_text(encoding="utf-8").lower().replace("_tmp", "")


def test_pair_ids_join_two_conditions(workspace):
    _, _, key_path = do_export(workspace)
    key = load_key(key_path)
    pairs = {}
    for info in key["questions"].values():
        pairs.setdefault(info["pair_id"], []).append(info)
    assert len(pairs) == 12 and key["incomplete_pairs"] == []
    for items in pairs.values():
        assert sorted(i["condition"] for i in items) == ["full", "rag"]
        assert len({(i["video_id"], i["topic_index"], i["bloom_target"]) for i in items}) == 1


def test_same_seed_same_order_other_seed_differs(workspace):
    first = load_key(do_export(workspace, 42, name="a")[2])["questions"]
    same = load_key(do_export(workspace, 42, name="b")[2])["questions"]
    other = load_key(do_export(workspace, 43, name="c")[2])["questions"]
    assert first == same
    assert first != other


def test_unproduced_go_to_key_not_to_rater_file(workspace):
    outcomes = {"rag": {2: "empty", 3: "duplicate"}, "full": {5: "invalid"}}
    a, _, key_path = do_export(workspace, outcomes=outcomes)
    key = load_key(key_path)
    assert key["question_count"] == 21 and len(ids_of(a)) == 21
    assert sorted((u["condition"], u["topic_index"], u["outcome"]) for u in key["unproduced"]) == [
        ("full", 5, "invalid"), ("rag", 2, "empty"), ("rag", 3, "duplicate")]


def test_sheets_transcript_guide_and_flaws(workspace):
    a, _, _ = do_export(workspace)
    wb = load_workbook(a)
    assert wb.sheetnames == [SHEET_QUESTIONS, SHEET_GUIDE, SHEET_FLAWS, f"T-{VIDEOS[0]}", f"T-{VIDEOS[1]}"]
    assert wb[SHEET_GUIDE]["A1"].value == GUIDE_PLACEHOLDER and wb[SHEET_GUIDE].max_row == 1
    assert wb[f"T-{VIDEOS[0]}"]["A2"].value == "1:05"
    assert wb[f"T-{VIDEOS[0]}"]["B2"].value == "merhaba arkadaşlar"  # temiz transkript
    assert [wb[SHEET_FLAWS].cell(r, 1).value for r in range(2, 21)] == list(range(1, 20))
    assert wb[SHEET_FLAWS]["B2"].value == "Ambiguous or unclear information"
    assert len(read_flaws()) == 19


def test_dropdowns_present(workspace):
    a, _, _ = do_export(workspace)
    rules = {str(r.sqref): r.formula1 for r in load_workbook(a)[SHEET_QUESTIONS].data_validations.dataValidation}
    assert rules["J3:J26"] == '"' + ",".join(BLOOM_LEVELS) + '"'
    assert rules["K3:K26"].startswith('"0,1,2') and rules["K3:K26"].endswith('19"')
    assert rules["M3:M26"] == '"evet,hayır"'
    assert rules["N3:N26"] == '"1,2,3,4,5"'
    assert rules["O3:O26"] == '"evet,hayır"'  # tanıma hatası kaynaklı mı
    assert len(rules) == 5  # hatalı maddeler ve not serbest


def test_option_starting_with_equals_stays_text(workspace):
    a, _, _ = do_export(workspace)
    wb = load_workbook(a)
    cell = wb[SHEET_QUESTIONS][f"H{DATA_START_ROW}"]  # Seçenek D
    assert cell.value == "= 10" and cell.data_type == "s"


def test_missing_transcript_stops_without_youtube(workspace):
    path = pilot_file(workspace, "ccccccccccc")
    with pytest.raises(ExportError, match="önbellekte yok"):
        export([path], 1, workspace / "o", workspace / "k", info_file(workspace), "questions-v3")


def test_video_missing_from_info_file_stops(workspace):
    path = pilot_file(workspace, VIDEOS[0])
    with pytest.raises(ExportError, match="Video bilgi dosyasında olmayan video"):
        export([path], 1, workspace / "o", workspace / "k", info_file(workspace, {VIDEOS[1]: VIDEO_INFO[VIDEOS[1]]}), "questions-v3")


@pytest.mark.parametrize(
    "item,message",
    [
        ({"altyazi_turu": "otomatik", "iki_dilli": False}, "alan yok"),
        ({"alan": "tarih", "altyazi_turu": "yarı", "iki_dilli": False}, "elle ya da otomatik"),
        ({"alan": "tarih", "altyazi_turu": "elle", "iki_dilli": "evet"}, "true ya da false"),
    ],
)
def test_invalid_video_info_rejected(tmp_path, item, message):
    with pytest.raises(ExportError, match=message):
        read_video_info(info_file(tmp_path, {"x": item}))


def test_secret_in_output_removes_files(workspace):
    path = pilot_file(workspace, VIDEOS[0])
    data = json.loads(path.read_text(encoding="utf-8"))
    for run in data["runs"].values():
        run["response"]["questions"][0]["question"] = "Adres https://youtu.be/x?si=abc nedir?"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ExportError, match="paylaşım kodu"):
        export([path], 1, workspace / "o", workspace / "k", info_file(workspace), "questions-v3")
    assert not (workspace / "o" / "degerlendirici-A.xlsx").exists()
    assert not (workspace / "k" / "anahtar.json").exists()


def test_find_secrets_clean_text():
    assert find_secrets(["https://youtu.be/abc", "Token sayısı ve risk-analizi"]) == []
    assert find_secrets([r"C:\Users\kisi\x"]) == ["yerel yol"]


# --- Etiket okuma -------------------------------------------------------------------


def test_read_valid_labels(workspace):
    a, _, key_path = do_export(workspace)
    ids = sorted(load_key(key_path)["questions"])
    labels, problems = read_labels(fill(a, workspace / "dolu.xlsx", perfect), ids)
    assert problems == [] and len(labels) == 24
    label = labels["S001"]
    assert (label.bloom, label.errors, label.flaws, label.grounded, label.answerable) == ("Anlama", 1, (4,), True, 4)
    assert label.acceptable is True


@pytest.mark.parametrize("errors,acceptable", [(0, True), (1, True), (2, False), (19, False)])
def test_acceptable_threshold(errors, acceptable):
    assert Label(errors=errors).acceptable is acceptable


def test_empty_cell_reported_with_id_and_column(workspace):
    a, _, key_path = do_export(workspace)
    ids = sorted(load_key(key_path)["questions"])
    path = fill(a, workspace / "dolu.xlsx", perfect, skip={("S003", COL_ANSWERABLE)})
    labels, problems = read_labels(path, ids)
    assert [(p.id, p.column, p.reason) for p in problems] == [("S003", COL_ANSWERABLE, "boş")]
    assert labels["S003"].answerable is None and labels["S003"].bloom == "Anlama"


@pytest.mark.parametrize(
    "column,value,reason",
    [
        (COL_BLOOM, "Analiz", "geçerli Bloom"),
        (COL_ERRORS, 20, "tam sayı değil"),
        (COL_ERRORS, 1.5, "tam sayı değil"),
        (COL_GROUNDED, "belki", "evet ya da hayır"),
        (COL_ANSWERABLE, 6, "tam sayı değil"),
        (COL_FLAWS, "20", "tekrarsız"),
        (COL_FLAWS, "4, 4", "tekrarsız"),
        (COL_FLAWS, "dört", "tekrarsız"),
        (COL_FLAWS, "4, 12", "uyuşmuyor"),
        (COL_ASR, "belki", "evet ya da hayır"),
    ],
)
def test_invalid_cell_reported(workspace, column, value, reason):
    a, _, key_path = do_export(workspace)
    ids = sorted(load_key(key_path)["questions"])

    def values(item_id):
        return {**perfect(item_id), **({column: value} if item_id == "S002" else {})}

    _, problems = read_labels(fill(a, workspace / "dolu.xlsx", values), ids)
    assert len(problems) == 1 and problems[0].id == "S002" and problems[0].column == column and reason in problems[0].reason


def test_values_as_text_accepted(workspace):
    a, _, key_path = do_export(workspace)
    ids = sorted(load_key(key_path)["questions"])

    def values(item_id):
        return {COL_BLOOM: " Anlama ", COL_ERRORS: "2", COL_FLAWS: "4; 12", COL_GROUNDED: "HAYIR", COL_ANSWERABLE: 3.0, COL_ASR: "Evet"}

    labels, problems = read_labels(fill(a, workspace / "dolu.xlsx", values), ids)
    assert problems == []
    assert labels["S001"].flaws == (4, 12) and labels["S001"].grounded is False and labels["S001"].answerable == 3
    assert labels["S001"].asr_error is True


def test_id_problems_reported(workspace):
    a, _, key_path = do_export(workspace)
    ids = sorted(load_key(key_path)["questions"])
    wb = load_workbook(fill(a, workspace / "dolu.xlsx", perfect))
    sheet = wb[SHEET_QUESTIONS]
    sheet[f"A{DATA_START_ROW}"] = "S999"
    sheet[f"A{DATA_START_ROW + 1}"] = sheet[f"A{DATA_START_ROW + 2}"].value
    wb.save(workspace / "bozuk.xlsx")
    _, problems = read_labels(workspace / "bozuk.xlsx", ids)
    reasons = {p.reason for p in problems}
    assert reasons == {"kimlik anahtarda yok", "kimlik birden çok kez geçiyor", "kimlik dosyada yok"}


def test_missing_column_stops(workspace):
    a, _, _ = do_export(workspace)
    wb = load_workbook(a)
    wb[SHEET_QUESTIONS]["J1"] = "Başka"
    wb.save(workspace / "bozuk.xlsx")
    with pytest.raises(LabelError, match=COL_BLOOM):
        read_labels(workspace / "bozuk.xlsx", ["S001"])


# --- Uyum ---------------------------------------------------------------------------


def test_agreement_outputs_and_disagreements(workspace):
    a, b, key_path = do_export(workspace)
    filled_a = fill(a, workspace / "A.xlsx", perfect)

    def rater_b(item_id):
        values = perfect(item_id)
        if item_id == "S001":
            values.update({COL_BLOOM: "Yaratma", COL_ERRORS: 2, COL_FLAWS: "4, 12"})
        return values

    filled_b = fill(b, workspace / "B.xlsx", rater_b)
    out = workspace / "uyum"
    result = agreement.run(filled_a, filled_b, key_path, out)

    fields = sorted(r["field"] for r in result["disagreements"])
    assert fields == sorted([COL_BLOOM, COL_ERRORS, "Kabul edilebilirlik (0-1 hata)", COL_FLAWS])
    assert {r["id"] for r in result["disagreements"]} == {"S001"}
    by_name = {k["name"]: k for k in result["kappas"]}
    assert by_name["Kaynağa dayalılık"]["kappa"] is None and "tanımsız" in by_name["Kaynağa dayalılık"]["note"]
    report = (out / "uyum-raporu.md").read_text(encoding="utf-8")
    assert "Fleiss, Cohen ve Everitt" in report and "tanımsız" in report

    rows = sheet_rows(out / "anlasmazliklar.xlsx", "Anlaşmazlıklar")
    assert rows[0][0] == COL_ID and len(rows) == 5
    texts = [str(c) for row in rows for c in row if c is not None]
    key = load_key(key_path)["questions"]["S001"]
    assert key["condition"] not in texts and key["bloom_target"] not in set(texts) - {"Yaratma", "Anlama"}
    assert not any("questions-v" in t for t in texts)


def test_agreement_excludes_missing_and_reports(workspace):
    a, b, key_path = do_export(workspace)
    filled_a = fill(a, workspace / "A.xlsx", perfect, skip={("S005", COL_BLOOM)})
    filled_b = fill(b, workspace / "B.xlsx", perfect)
    result = agreement.run(filled_a, filled_b, key_path, workspace / "uyum")
    bloom = result["kappas"][0]
    assert bloom["n"] == 23 and bloom["excluded"] == 1
    assert [(p["id"], p["column"]) for p in result["problems"]] == [("S005", COL_BLOOM)]
    assert "S005" in (workspace / "uyum" / "uyum-raporu.md").read_text(encoding="utf-8")


def test_joint_template_same_format_and_blank(workspace):
    a, b, key_path = do_export(workspace)
    filled = fill(a, workspace / "A.xlsx", lambda i: {**perfect(i), COL_NOTE: "özel not"})
    agreement.run(filled, fill(b, workspace / "B.xlsx", perfect), key_path, workspace / "uyum")
    template = workspace / "uyum" / "ortak-etiket-sablonu.xlsx"
    rows = sheet_rows(template)
    assert rows[0] == VISIBLE_COLUMNS + FILL_COLUMNS
    assert [r[:len(VISIBLE_COLUMNS)] for r in rows] == [r[:len(VISIBLE_COLUMNS)] for r in sheet_rows(a)]
    assert all(v is None for r in rows[DATA_START_ROW - 1:] for v in r[len(VISIBLE_COLUMNS):])
    assert rows[1] == sheet_rows(a)[1]  # açıklama satırı korunur
    assert len(load_workbook(template)[SHEET_QUESTIONS].data_validations.dataValidation) == 5


def test_agreement_has_asr_kappa_and_disagreement(workspace):
    a, b, key_path = do_export(workspace)
    filled_a = fill(a, workspace / "A.xlsx", lambda i: {**perfect(i), COL_ASR: "evet" if i in ("S001", "S002") else "hayır"})
    filled_b = fill(b, workspace / "B.xlsx", lambda i: {**perfect(i), COL_ASR: "evet" if i == "S001" else "hayır"})
    result = agreement.run(filled_a, filled_b, key_path, workspace / "uyum")
    asr = next(k for k in result["kappas"] if k["field"] == "asr_error")
    assert asr["name"] == "Tanıma hatası kaynaklı" and asr["n"] == 24
    # 24 sorunun 23'ünde uyum; A 2 evet, B 1 evet
    assert asr["agreement"] == pytest.approx(23 / 24)
    assert [(r["id"], r["field"], r["a"], r["b"]) for r in result["disagreements"]] == [("S002", COL_ASR, "evet", "hayır")]


# --- Analiz -------------------------------------------------------------------------


def make_key():
    """4 çift, 1 video. P4'te rag üretilemedi."""
    questions, unproduced = {}, []
    for i, level in enumerate(BLOOM_LEVELS[:4], 1):
        for j, mode in enumerate(("full", "rag")):
            info = {"video_id": "v", "topic_index": i, "topic": f"k{i}", "condition": mode, "prompt_version": "questions-v3",
                    "bloom_target": level, "pair_id": f"P{i}", "source": "x"}
            if i == 4 and mode == "rag":
                unproduced.append({**info, "outcome": "empty"})
            else:
                questions[f"S{i}{j}"] = info
    return {"questions": questions, "unproduced": unproduced, "incomplete_pairs": [],
            "videos": {"v": {"alan": "biyoloji", "altyazi_turu": "otomatik", "iki_dilli": False}}}


def lab(errors=0, grounded=True, answerable=4, bloom="Hatırlama", asr_error=False):
    return Label(bloom=bloom, errors=errors, flaws=(), grounded=grounded, answerable=answerable, asr_error=asr_error)


def base_labels():
    return {
        "S10": lab(errors=3, grounded=False, answerable=2, bloom="Hatırlama"),  # P1 full
        "S11": lab(errors=0, grounded=True, answerable=5, bloom="Hatırlama"),  # P1 rag
        "S20": lab(errors=0, answerable=3, bloom="Hatırlama"),  # P2 full (hedef Anlama, uyumsuz)
        "S21": lab(errors=1, answerable=4, bloom="Anlama"),  # P2 rag
        "S30": lab(errors=0, answerable=4, bloom="Uygulama"),  # P3 full
        "S31": lab(errors=2, answerable=4, bloom="Uygulama"),  # P3 rag
        "S40": lab(errors=0, answerable=5, bloom="Çözümleme"),  # P4 full; rag üretilemedi
    }


def test_unproduced_counts_as_not_acceptable_and_not_grounded():
    result = analysis.analyze(make_key(), base_labels())
    acceptable = result["as1"]["acceptable"]
    # P1 yalnız rag, P2 ikisi, P3 yalnız full, P4 yalnız full (rag üretilemedi)
    assert (acceptable["both"], acceptable["rag_only"], acceptable["full_only"], acceptable["neither"]) == (1, 1, 2, 0)
    assert acceptable["pairs"] == 4
    assert acceptable["rag"]["k"] == 2 and acceptable["full"]["k"] == 3
    assert acceptable["mcnemar"]["discordant"] == 3 and acceptable["mcnemar"]["p_value"] == pytest.approx(1.0)
    assert acceptable["difference"]["difference"] == pytest.approx(-0.25)
    grounded = result["as1"]["grounded"]
    assert (grounded["both"], grounded["rag_only"], grounded["full_only"], grounded["neither"]) == (2, 1, 1, 0)


def test_unproduced_pair_removed_from_wilcoxon_and_counted():
    w = analysis.analyze(make_key(), base_labels())["as1"]["answerable"]
    # Farklar rag - full: P1 +3, P2 +1, P3 0; P4 çıkarıldı
    assert w["excluded_unproduced"] == 1 and w["pairs"] == 3 and w["zero_differences"] == 1 and w["n"] == 2
    assert w["w_plus"] == 3.0 and w["w_minus"] == 0.0


def test_both_conditions_unproduced_pair_stays_in_mcnemar():
    key = make_key()
    key["unproduced"].append({**key["questions"].pop("S40"), "outcome": "invalid"})
    labels = base_labels()
    del labels["S40"]
    result = analysis.analyze(key, labels)
    assert result["as1"]["acceptable"]["neither"] == 1 and result["as1"]["acceptable"]["pairs"] == 4
    assert result["as1"]["answerable"]["excluded_unproduced"] == 1


def test_missing_label_excluded_from_that_measure_only():
    labels = base_labels()
    labels["S11"].errors = None
    result = analysis.analyze(make_key(), labels)
    assert result["as1"]["acceptable"]["pairs"] == 3 and result["as1"]["acceptable"]["excluded_missing_label"] == 1
    assert result["as1"]["grounded"]["pairs"] == 4
    assert result["descriptive"]["excluded_missing_label"] == 1


def test_no_discordant_pairs_in_analysis():
    key = make_key()
    labels = {i: lab() for i in key["questions"]}
    key["questions"]["S41"] = {**key["unproduced"].pop(), "pair_id": "P4"}
    key["questions"]["S41"].pop("outcome")
    labels["S41"] = lab()
    result = analysis.analyze(key, labels)
    assert result["as1"]["acceptable"]["mcnemar"]["p_value"] == 1.0
    assert result["as1"]["acceptable"]["difference"]["difference"] == 0
    assert result["as1"]["answerable"]["note"] == "bütün farklar sıfır; test uygulanamadı"


def test_as2_rates_and_matrix():
    a = analysis.analyze(make_key(), base_labels())["as2"]
    # Üretilen 7 soruda uyum: S10, S11 (Hatırlama), S21 (Anlama), S30, S31 (Uygulama), S40 (Çözümleme) = 6
    assert a["total"]["produced"]["k"] == 6 and a["total"]["produced"]["n"] == 7
    assert a["total"]["all_topics"]["k"] == 6 and a["total"]["all_topics"]["n"] == 8
    assert a["by_condition"]["rag"]["produced"]["n"] == 3 and a["by_condition"]["rag"]["all_topics"]["n"] == 4
    assert a["by_level"]["Anlama"]["produced"]["k"] == 1 and a["by_level"]["Anlama"]["produced"]["n"] == 2
    assert a["by_level"]["Yaratma"]["produced"]["rate"] is None
    assert a["confusion_matrix"]["Anlama"]["Hatırlama"] == 1
    assert a["confusion_matrix"]["Çözümleme"][analysis.UNPRODUCED_COLUMN] == 1


def test_as2_primary_is_all_topics_and_stated_in_report():
    result = analysis.analyze(make_key(), base_labels())
    assert result["as2"]["primary"] == "all_topics"
    report = analysis.render_report(result, [])
    assert "Birincil sonuç \"bütün konular\"dır" in report
    header = next(line for line in report.splitlines() if "Bütün konular (birincil)" in line)
    assert header.index("Bütün konular (birincil)") < header.index("Yalnızca üretilen sorular (ikincil)")
    total = next(line for line in report.splitlines() if line.startswith("| Toplam |"))
    assert total.index("6 / 8") < total.index("6 / 7")


def test_descriptive_includes_unproduced_in_denominator():
    d = analysis.analyze(make_key(), base_labels())["descriptive"]
    rag = next(v for v in d["acceptable_by_video"] if v["condition"] == "rag")
    assert (rag["k"], rag["n"]) == (2, 4)
    assert d["unproduced_count"] == 1 and d["unproduced_by_outcome"] == {"empty": 1} and d["unproduced_by_condition"] == {"rag": 1}


def test_incomplete_pair_left_out_and_reported():
    key = make_key()
    del key["questions"]["S10"]
    labels = base_labels()
    result = analysis.analyze(key, labels)
    assert result["incomplete_pairs"] == ["P1"] and result["pair_count"] == 3
    assert result["as1"]["acceptable"]["pairs"] == 3


def test_full_flow_report_and_json(workspace):
    a, _, key_path = do_export(workspace, outcomes={"rag": {6: "empty"}})
    joint = fill(a, workspace / "ortak.xlsx", perfect)
    out = workspace / "analiz"
    result = analysis.run(joint, key_path, out, alpha=0.01)
    assert result["alpha"] == 0.01 and result["pair_count"] == 12 and result["problems"] == []
    assert result["descriptive"]["unproduced_count"] == 1
    saved = json.loads((out / "analiz.json").read_text(encoding="utf-8"))
    assert saved["as1"]["answerable"]["excluded_unproduced"] == 1
    report = (out / "analiz-raporu.md").read_text(encoding="utf-8")
    for text in ("Kesin McNemar", "Newcombe", "keşfedici", "Wilson", "karışıklık matrisi", "Üretilemeyen konu: 1", "%99",
                 "Tanıma hatası kaynaklı sorular hariç", "İki dilli videolar hariç", "Altyazı türüne göre (betimsel; test yok)",
                 "Bu bölümdekiler birincil sonuç değildir"):
        assert text in report


# --- Hafta-3: tanıma hatası, iki dilli videolar, altyazı türü ---------------------------


def two_video_key():
    """make_key'deki 4 çift "v" videosunda; aynı yapı "w" videosu için P5-P8 olarak eklenir."""
    key = make_key()
    for item_id, info in list(key["questions"].items()):
        key["questions"]["W" + item_id[1:]] = {**info, "video_id": "w", "pair_id": "Q" + info["pair_id"][1:]}
    for info in list(key["unproduced"]):
        key["unproduced"].append({**info, "video_id": "w", "pair_id": "Q" + info["pair_id"][1:]})
    key["videos"] = {"v": {"alan": "biyoloji", "altyazi_turu": "elle", "iki_dilli": False},
                     "w": {"alan": "ingilizce", "altyazi_turu": "otomatik", "iki_dilli": True}}
    return key


def two_video_labels():
    labels = base_labels()
    labels.update({"W" + item_id[1:]: lab(errors=label.errors, grounded=label.grounded, answerable=label.answerable, bloom=label.bloom)
                   for item_id, label in base_labels().items()})
    return labels


def test_asr_count_by_condition():
    labels = base_labels()
    labels["S11"].asr_error = True  # P1 rag
    labels["S20"].asr_error = True  # P2 full
    labels["S30"].asr_error = None  # işaret eksik
    result = analysis.analyze(make_key(), labels)
    assert result["asr_by_condition"] == {"flagged": {"full": 1, "rag": 1}, "missing": 1, "questions": {"full": 4, "rag": 3}}


def test_without_asr_drops_pair_and_keeps_primary():
    labels = base_labels()
    primary = analysis.analyze(make_key(), labels)
    labels["S11"].asr_error = True  # P1'in rag sorusu işaretli: P1 çifti AS1'den çıkar
    result = analysis.analyze(make_key(), labels)
    assert result["as1"] == primary["as1"] and result["as2"] == primary["as2"]  # birincil sonuç değişmez
    s = result["sensitivity"]["without_asr"]
    assert s["excluded_pairs"] == 1 and s["excluded_pairs_missing_flag"] == 0
    assert s["as1"]["acceptable"]["pairs"] == 3  # P2, P3, P4
    # AS2'de yalnızca işaretli soru çıkar; P1'in full sorusu kalır
    assert s["excluded_questions"] == 1
    assert s["as2"]["total"]["all_topics"]["n"] == primary["as2"]["total"]["all_topics"]["n"] - 1


def test_without_asr_missing_flag_counted_separately():
    labels = base_labels()
    labels["S20"].asr_error = None
    s = analysis.analyze(make_key(), labels)["sensitivity"]["without_asr"]
    assert s["excluded_pairs"] == 0 and s["excluded_pairs_missing_flag"] == 1
    assert s["excluded_questions"] == 0 and s["excluded_questions_missing_flag"] == 1


def test_unproduced_topic_is_not_an_asr_flag():
    # P4'te rag üretilemedi; işaret olmadığı için çift duyarlılık analizinde kalır
    s = analysis.analyze(make_key(), base_labels())["sensitivity"]["without_asr"]
    assert s["as1"]["acceptable"]["pairs"] == 4 and s["excluded_pairs"] == 0


def test_without_bilingual_videos():
    key, labels = two_video_key(), two_video_labels()
    result = analysis.analyze(key, labels)
    b = result["sensitivity"]["without_bilingual"]
    assert b["excluded_videos"] == ["w"] and b["excluded_pairs"] == 4
    assert result["as1"]["acceptable"]["pairs"] == 8 and b["as1"]["acceptable"]["pairs"] == 4
    assert b["as1"]["acceptable"] == analysis.analyze(make_key() | {"videos": key["videos"]}, base_labels())["as1"]["acceptable"]
    assert b["as2"]["total"]["all_topics"]["n"] == 8


def test_by_subtitle_type_descriptive():
    sub = analysis.analyze(two_video_key(), two_video_labels())["by_subtitle_type"]
    assert sub["elle"]["videos"] == ["v"] and sub["otomatik"]["videos"] == ["w"]
    # Her videoda 8 yuva, kabul edilebilir: S11, S20, S21, S30, S40 = 5 (rag P4 üretilemedi)
    assert (sub["elle"]["acceptable"]["k"], sub["elle"]["acceptable"]["n"]) == (5, 8)
    assert sub["elle"]["as2"]["all_topics"]["n"] == 8 and sub["elle"]["as2"]["all_topics"]["k"] == 6
    assert "p_value" not in json.dumps(sub)  # test yok


def test_analysis_requires_video_info():
    key = make_key()
    del key["videos"]
    with pytest.raises(ValueError, match="video bilgisi"):
        analysis.analyze(key, base_labels())
