"""Üretilen sorulardan kör değerlendirme dosyalarını ve anahtar dosyasını hazırlar.

Girdi: çalıştırma kaydı (backend/runs), pilot 1 ya da pilot 2 JSON'u. Değerlendirici
dosyalarında koşul, istem sürümü, hedef düzey, reasoning, alıntı ve otomatik
işaretler bulunmaz: değerlendirici modelin alıntısına güvenip transkripti
kontrol etmeyi atlamasın, koşulu ve hedef düzeyi tahmin edemesin. Bu bilgiler
yalnızca değerlendiricilere verilmeyen anahtar dosyasındadır.

Transkriptler yalnızca yerel önbellekten okunur; bu betik YouTube'a gitmez.

Çalıştırma (backend klasöründen):
    python -m evaluation.export --girdi <dosya...> --tohum 42 --cikti <klasör> --anahtar-cikti <klasör>
"""

import argparse
import glob
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from app.config import get_settings
from app.services.text_clean import clean_transcript
from app.services.transcript import Transcript
from app.services.transcript_cache import read_cached
from evaluation.common import (
    BLOOM_LEVELS,
    COL_ANSWERABLE,
    COL_BLOOM,
    COL_ERRORS,
    COL_FLAWS,
    COL_GROUNDED,
    FILL_COLUMNS,
    GUIDE_PLACEHOLDER,
    MAX_FLAWS,
    SHEET_FLAWS,
    SHEET_GUIDE,
    SHEET_QUESTIONS,
    TRANSCRIPT_PREFIX,
    VISIBLE_COLUMNS,
    write_json,
)

FLAWS_DOC = Path(__file__).resolve().parents[2] / "docs" / "soru-yazim-hatalari.md"
RATER_FILES = ("degerlendirici-A.xlsx", "degerlendirici-B.xlsx")
KEY_FILE = "anahtar.json"
HEADER_FILL = PatternFill("solid", fgColor="D9E1F2")
FILL_HEADER_FILL = PatternFill("solid", fgColor="FFF2CC")
SECRET_PATTERNS = {
    "API anahtarı": r"sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY",
    "yetki başlığı": r"(?i)\bauthorization\s*:|\bbearer\s+\S{8,}",
    "parola/token": r"(?i)\b(password|parola|token)\s*=",
    ".env": r"\.env\b",
    "e-posta": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "yerel yol": r"[A-Za-z]:[\\/]+Users|/c/Users|/home/\w+",
    "paylaşım kodu": r"[?&]si=",
}


class ExportError(Exception):
    """Girdi dışa aktarmaya uygun değil."""


@dataclass
class Run:
    """Bir video ve koşulun tek çalıştırması."""

    source: str  # dosya adı (#etiket); yerel yol içermez
    video_id: str
    condition: str
    prompt_version: str
    response: dict
    generation: dict


def _run(source: str, response: dict, generation: dict) -> Run:
    return Run(source, response["video_id"], generation["context_mode"], generation["prompt_version"], response, generation)


def read_runs(path: Path) -> list[Run]:
    """Dosyadaki çalıştırmalar. Üç biçim tanınır: çalıştırma kaydı, pilot 1 (`conditions`), pilot 2 (`runs`)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    name = Path(path).name
    if "topic_generation" in data:
        if data.get("outcome", "ok") != "ok" or not data["topic_generation"]:
            raise ExportError(f"{name}: başarılı bir konu tabanlı soru kaydı değil.")
        return [_run(name, data["response"], data["topic_generation"])]
    parts = data.get("runs") or data.get("conditions")
    if parts is None:
        raise ExportError(f"{name}: tanınmayan dosya biçimi.")
    return [_run(f"{name}#{label}", part["response"], part["topic_generation"]) for label, part in parts.items()]


def collect(runs: list[Run], prompt_version: str | None) -> tuple[list[dict], list[dict], str]:
    """Soruları ve üretilemeyen konuları düz listeye çevirir; çift kimliklerini verir.

    Çift: aynı video + konu sırası + hedef düzey için iki koşul. Ana deney tek istem
    sürümüyle yapıldığı için girdide birden çok sürüm varsa `prompt_version` seçilmelidir.
    """
    if prompt_version:
        runs = [r for r in runs if r.prompt_version == prompt_version]
    versions = sorted({r.prompt_version for r in runs})
    if not runs:
        raise ExportError("Seçilen istem sürümüyle çalıştırma bulunamadı.")
    if len(versions) > 1:
        raise ExportError(f"Girdide birden çok istem sürümü var: {', '.join(versions)}. --istem-surumu ile birini seçin.")

    questions, unproduced, seen, topics = [], [], set(), {}
    for run in sorted(runs, key=lambda r: (r.video_id, r.condition)):
        if (run.video_id, run.condition) in seen:
            raise ExportError(f"{run.video_id} / {run.condition} için birden çok çalıştırma var ({run.source}).")
        seen.add((run.video_id, run.condition))
        by_topic = {}
        for q in run.response["questions"]:
            if q["topic"] in by_topic:
                raise ExportError(f"{run.source}: aynı konuda iki soru var.")
            by_topic[q["topic"]] = q
        for index, trace in enumerate(run.generation["per_topic"], 1):
            slot = (run.video_id, index)
            target = trace["bloom_level"]
            if topics.setdefault(slot, (trace["topic"], target)) != (trace["topic"], target):
                raise ExportError(f"{run.video_id} konu {index}: iki koşulda konu ya da hedef düzey farklı.")
            base = {"video_id": run.video_id, "topic_index": index, "topic": trace["topic"], "condition": run.condition,
                    "prompt_version": run.prompt_version, "bloom_target": target, "source": run.source}
            question = by_topic.get(trace["topic"])
            if trace["outcome"] == "ok":
                if question is None:
                    raise ExportError(f"{run.source}: konu {index} sonucu ok ama soru yok.")
                questions.append({**base, "question": question})
            else:
                unproduced.append({**base, "outcome": trace["outcome"]})

    pair_ids = {slot: f"P{i:03d}" for i, slot in enumerate(sorted(topics), 1)}
    for item in questions + unproduced:
        item["pair_id"] = pair_ids[(item["video_id"], item["topic_index"])]
    return questions, unproduced, versions[0]


def assign_ids(questions: list[dict], seed: int) -> list[dict]:
    """Sırayı tohumla karıştırır; kimlikler karıştırılmış sıraya göre verilir (S001, S002, ...).

    Karıştırmadan önce sabit bir sıra alınır: sonuç girdi dosyalarının sırasına bağlı değildir.
    """
    ordered = sorted(questions, key=lambda q: (q["video_id"], q["topic_index"], q["condition"]))
    random.Random(seed).shuffle(ordered)
    width = max(3, len(str(len(ordered))))
    return [{**q, "id": f"S{i:0{width}d}"} for i, q in enumerate(ordered, 1)]


def build_key(questions: list[dict], unproduced: list[dict], seed: int, version: str, inputs: list[str]) -> dict:
    fields = ("video_id", "topic_index", "topic", "condition", "prompt_version", "bloom_target", "pair_id", "source")
    slots = {}
    for item in questions + unproduced:
        slots.setdefault(item["pair_id"], set()).add(item["condition"])
    return {
        "seed": seed,
        "prompt_version": version,
        "inputs": inputs,
        "question_count": len(questions),
        "questions": {q["id"]: {f: q[f] for f in fields} for q in questions},
        "unproduced": [{**{f: u[f] for f in fields}, "outcome": u["outcome"]} for u in unproduced],
        # İki koşuldan yalnızca biri girdide olan çiftler; analize girmez
        "incomplete_pairs": sorted(p for p, conditions in slots.items() if len(conditions) < 2),
    }


def read_flaws(path: Path = FLAWS_DOC) -> list[tuple[int, str, str]]:
    """19 maddelik listenin numarası, adı ve kısa açıklaması (sınıf sütunu otomatik denetime ait, alınmaz)."""
    rows = re.findall(r"^\| (\d+) \| ([^|]+?) \| ([^|]+?) \|", Path(path).read_text(encoding="utf-8"), re.MULTILINE)
    flaws = [(int(n), name, text) for n, name, text in rows]
    if [f[0] for f in flaws] != list(range(1, MAX_FLAWS + 1)):
        raise ExportError(f"{Path(path).name}: {MAX_FLAWS} madde bulunamadı.")
    return flaws


def load_transcripts(video_ids: list[str]) -> dict[str, Transcript]:
    """Temiz transkriptler; yalnızca önbellekten. Eksikse hata verir, YouTube'a gitmez."""
    languages = get_settings().transcript_language_list
    transcripts = {}
    for video_id in video_ids:
        cached = read_cached(video_id, languages)
        if cached is None:
            raise ExportError(f"{video_id}: transkript önbellekte yok.")
        transcripts[video_id] = clean_transcript(cached)
    return transcripts


def mmss(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def _text(cell, value: str) -> None:
    """Metni her zaman metin olarak yazar: "= 10" gibi bir seçenek formüle dönüşmesin."""
    cell.value = ILLEGAL_CHARACTERS_RE.sub("", value)
    cell.data_type = "s"


def _header(sheet, names: list[str], fill_columns: tuple = ()) -> None:
    for column, name in enumerate(names, 1):
        cell = sheet.cell(1, column, name)
        cell.font = Font(bold=True)
        cell.fill = FILL_HEADER_FILL if name in fill_columns else HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "A2"


def _validation(sheet, column: int, last_row: int, values: list[str], title: str) -> None:
    rule = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True,
                          showErrorMessage=True, errorTitle=title, error="Listeden bir değer seçin.")
    letter = get_column_letter(column)
    rule.add(f"{letter}2:{letter}{last_row}")
    sheet.add_data_validation(rule)


def write_rater_workbook(path: Path, questions: list[dict], transcripts: dict[str, Transcript],
                         flaws: list[tuple[int, str, str]]) -> None:
    wb = Workbook()
    wb.properties.creator = ""
    sheet = wb.active
    sheet.title = SHEET_QUESTIONS
    columns = VISIBLE_COLUMNS + FILL_COLUMNS
    _header(sheet, columns, tuple(FILL_COLUMNS))
    for row, item in enumerate(questions, 2):
        q = item["question"]
        letter = "ABCD"[q["correct_index"]]
        values = [item["id"], f"https://youtu.be/{item['video_id']}", f"{TRANSCRIPT_PREFIX}{item['video_id']}", q["question"],
                  *q["options"], f"{letter}) {q['options'][q['correct_index']]}"]
        for column, value in enumerate(values, 1):
            _text(sheet.cell(row, column), value)
            sheet.cell(row, column).alignment = Alignment(wrap_text=True, vertical="top")
        # Metin biçimi: "4,12" gibi bir giriş Excel'de sayıya dönüşmesin
        sheet.cell(row, columns.index(COL_FLAWS) + 1).number_format = "@"
    for column, width in enumerate([8, 28, 18, 60, 30, 30, 30, 30, 30, 15, 10, 14, 11, 15, 30], 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    last = len(questions) + 1
    _validation(sheet, columns.index(COL_BLOOM) + 1, last, BLOOM_LEVELS, COL_BLOOM)
    _validation(sheet, columns.index(COL_ERRORS) + 1, last, [str(i) for i in range(MAX_FLAWS + 1)], COL_ERRORS)
    _validation(sheet, columns.index(COL_GROUNDED) + 1, last, ["evet", "hayır"], COL_GROUNDED)
    _validation(sheet, columns.index(COL_ANSWERABLE) + 1, last, ["1", "2", "3", "4", "5"], COL_ANSWERABLE)

    wb.create_sheet(SHEET_GUIDE).cell(1, 1, GUIDE_PLACEHOLDER)

    flaw_sheet = wb.create_sheet(SHEET_FLAWS)
    _header(flaw_sheet, ["Madde", "Ad", "Kısa açıklama"])
    for row, (number, name, text) in enumerate(flaws, 2):
        flaw_sheet.cell(row, 1, number)
        _text(flaw_sheet.cell(row, 2), name)
        _text(flaw_sheet.cell(row, 3), text)
    flaw_sheet.column_dimensions["B"].width = 34
    flaw_sheet.column_dimensions["C"].width = 80

    for video_id, transcript in sorted(transcripts.items()):
        video_sheet = wb.create_sheet(f"{TRANSCRIPT_PREFIX}{video_id}")
        _header(video_sheet, ["Zaman", "Metin"])
        for row, segment in enumerate(transcript.segments, 2):
            _text(video_sheet.cell(row, 1), mmss(segment.start))
            _text(video_sheet.cell(row, 2), segment.text)
        video_sheet.column_dimensions["B"].width = 100
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def workbook_strings(path: Path) -> list[str]:
    from openpyxl import load_workbook

    wb = load_workbook(path)
    return [str(c.value) for ws in wb for row in ws.iter_rows() for c in row if c.value is not None]


def find_secrets(texts: list[str]) -> list[str]:
    """Eşleşen gizli bilgi türleri (eşleşen metin döndürülmez)."""
    joined = "\n".join(texts)
    return [kind for kind, pattern in SECRET_PATTERNS.items() if re.search(pattern, joined)]


def export(paths: list[Path], seed: int, out_dir: Path, key_dir: Path, prompt_version: str | None = None) -> dict:
    """Dosyaları yazar ve anahtarı döndürür. Gizli bilgi bulunursa dosyalar silinir, hata verilir."""
    runs = [run for path in paths for run in read_runs(path)]
    produced, unproduced, version = collect(runs, prompt_version)
    questions = assign_ids(produced, seed)
    key = build_key(questions, unproduced, seed, version, sorted({Path(p).name for p in paths}))
    transcripts = load_transcripts(sorted({q["video_id"] for q in questions}))
    flaws = read_flaws()

    targets = [Path(out_dir) / name for name in RATER_FILES]
    for target in targets:
        write_rater_workbook(target, questions, transcripts, flaws)
    key_path = Path(key_dir) / KEY_FILE
    write_json(key_path, key)
    secrets = find_secrets(workbook_strings(targets[0]) + [key_path.read_text(encoding="utf-8")])
    if secrets:
        for path in [*targets, key_path]:
            path.unlink()
        raise ExportError(f"Çıktıda gizli bilgi bulundu ({', '.join(secrets)}); dosyalar silindi.")
    return key


def main() -> None:
    parser = argparse.ArgumentParser(description="Kör değerlendirme dosyalarını hazırlar.")
    parser.add_argument("--girdi", nargs="+", required=True, help="Çalıştırma kaydı ya da pilot JSON'u (joker karakter olabilir)")
    parser.add_argument("--tohum", type=int, required=True, help="Sıralama tohumu; anahtara yazılır")
    parser.add_argument("--cikti", type=Path, required=True, help="Değerlendirici dosyalarının klasörü")
    parser.add_argument("--anahtar-cikti", type=Path, required=True, help="Anahtar dosyasının klasörü; değerlendiricilere verilmez")
    parser.add_argument("--istem-surumu", help="Girdide birden çok sürüm varsa seçilecek sürüm (ör. questions-v3)")
    args = parser.parse_args()
    paths = [Path(p) for pattern in args.girdi for p in sorted(glob.glob(pattern))]
    if not paths:
        parser.error("Girdi dosyası bulunamadı.")
    key = export(paths, args.tohum, args.cikti, args.anahtar_cikti, args.istem_surumu)
    print(f"{key['question_count']} soru, {len(key['unproduced'])} üretilemeyen konu, "
          f"{len(key['incomplete_pairs'])} eksik çift, tohum {key['seed']}, sürüm {key['prompt_version']}.")


if __name__ == "__main__":
    main()
