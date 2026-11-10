"""Doldurulmuş değerlendirme dosyalarını okur ve denetler.

Eksik ya da geçersiz hücreler sessizce geçilmez: her biri kimlik ve sütunla
`Problem` olarak döner. Geçersiz alan None olur ve o alanın hesabından çıkar.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook

from evaluation.common import (
    ACCEPTABLE_MAX_ERRORS,
    BLOOM_LEVELS,
    COL_ANSWERABLE,
    COL_ASR,
    COL_BLOOM,
    COL_ERRORS,
    COL_FLAWS,
    COL_GROUNDED,
    COL_ID,
    COL_NOTE,
    DESCRIPTION_LABEL,
    FILL_COLUMNS,
    MAX_FLAWS,
    SHEET_QUESTIONS,
)


class LabelError(Exception):
    """Dosya hiç okunamıyor (ör. sayfa ya da sütun yok)."""


@dataclass
class Label:
    bloom: str | None = None
    errors: int | None = None
    flaws: tuple[int, ...] | None = None
    grounded: bool | None = None
    answerable: int | None = None
    asr_error: bool | None = None  # sorunun hatası konuşma tanıma hatasından mı
    note: str = ""

    @property
    def acceptable(self) -> bool | None:
        return None if self.errors is None else self.errors <= ACCEPTABLE_MAX_ERRORS


@dataclass
class Problem:
    file: str
    id: str
    column: str
    value: str
    reason: str

    def as_dict(self) -> dict:
        return {"file": self.file, "id": self.id, "column": self.column, "value": self.value, "reason": self.reason}


def _integer(value, low: int, high: int) -> int | None:
    """Tam sayı ya da tam sayı yazılmış metin; aralık dışıysa None. Excel sayıları float okunabilir."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, str) and re.fullmatch(r"\s*\d+\s*", value):
        value = int(value)
    return value if isinstance(value, int) and low <= value <= high else None


def _grounded(value) -> bool | None:
    text = str(value).strip().replace("I", "ı").replace("İ", "i").lower()
    return {"evet": True, "hayır": False}.get(text)


def _flaws(value) -> tuple[int, ...] | None:
    """"4, 12" biçimindeki madde numaraları; boşsa boş demet, geçersizse None."""
    if value is None or not str(value).strip():
        return ()
    text = str(value).strip()
    if not re.fullmatch(r"\d+(\s*[,;]\s*\d+)*", text):
        return None
    numbers = tuple(int(n) for n in re.findall(r"\d+", text))
    if len(set(numbers)) != len(numbers) or not all(1 <= n <= MAX_FLAWS for n in numbers):
        return None
    return numbers


def read_labels(path: Path, expected_ids: list[str]) -> tuple[dict[str, Label], list[Problem]]:
    """Dosyadaki etiketler ve sorunlar. `expected_ids` anahtardaki kimliklerdir."""
    name = Path(path).name
    wb = load_workbook(path, data_only=True)
    if SHEET_QUESTIONS not in wb.sheetnames:
        raise LabelError(f"{name}: '{SHEET_QUESTIONS}' sayfası yok.")
    rows = wb[SHEET_QUESTIONS].iter_rows(values_only=True)
    header = list(next(rows))
    missing = [c for c in [COL_ID, *FILL_COLUMNS] if c not in header]
    if missing:
        raise LabelError(f"{name}: sütun yok: {', '.join(missing)}.")
    columns = {c: header.index(c) for c in [COL_ID, *FILL_COLUMNS]}

    labels: dict[str, Label] = {}
    problems: list[Problem] = []
    expected = set(expected_ids)

    def report(item_id, column, value, reason):
        problems.append(Problem(name, str(item_id), column, "" if value is None else str(value), reason))

    for row in rows:
        item_id = row[columns[COL_ID]]
        if item_id is None or item_id == DESCRIPTION_LABEL:
            continue
        if item_id not in expected:
            report(item_id, COL_ID, item_id, "kimlik anahtarda yok")
            continue
        if item_id in labels:
            report(item_id, COL_ID, item_id, "kimlik birden çok kez geçiyor")
            continue
        cell = {c: row[i] for c, i in columns.items()}
        label = Label(note=str(cell[COL_NOTE] or ""))

        def parse(column, parser, reason):
            value = cell[column]
            if value is None or not str(value).strip():
                report(item_id, column, None, "boş")
                return None
            parsed = parser(value)
            if parsed is None:
                report(item_id, column, value, reason)
            return parsed

        label.bloom = parse(COL_BLOOM, lambda v: str(v).strip() if str(v).strip() in BLOOM_LEVELS else None, "geçerli Bloom düzeyi değil")
        label.errors = parse(COL_ERRORS, lambda v: _integer(v, 0, MAX_FLAWS), f"0-{MAX_FLAWS} arası tam sayı değil")
        label.grounded = parse(COL_GROUNDED, _grounded, "evet ya da hayır değil")
        label.answerable = parse(COL_ANSWERABLE, lambda v: _integer(v, 1, 5), "1-5 arası tam sayı değil")
        label.asr_error = parse(COL_ASR, _grounded, "evet ya da hayır değil")

        label.flaws = _flaws(cell[COL_FLAWS])
        if label.flaws is None:
            report(item_id, COL_FLAWS, cell[COL_FLAWS], f"1-{MAX_FLAWS} arası, tekrarsız numaralar olmalı (ör. 4, 12)")
        elif label.errors is not None and len(label.flaws) != label.errors:
            report(item_id, COL_FLAWS, cell[COL_FLAWS], f"madde sayısı ({len(label.flaws)}) yazım hatası sayısıyla ({label.errors}) uyuşmuyor")
        labels[item_id] = label

    for item_id in expected_ids:
        if item_id not in labels:
            report(item_id, COL_ID, None, "kimlik dosyada yok")
    return labels, problems
