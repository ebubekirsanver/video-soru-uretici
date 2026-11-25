"""Doldurulmuş değerlendirme dosyalarını okur ve denetler.

Eksik ya da geçersiz hücreler sessizce geçilmez: her biri kimlik ve sütunla
`Problem` olarak döner. Geçersiz alan None olur ve o alanın hesabından çıkar.

"Anahtar yanlış" kuralı (yönerge, Bölüm 4; 2026-11-25, puanlamadan önce): "Hatalı
maddeler"de 1-19 arası numaralara ek olarak A (büyük ya da küçük harf) yazılabilir.
A yazım hatası sayısına 1 olarak katılır ve soru kabul edilemez sayılır. A işaretli
soruda kaynağa dayalı = hayır ve cevaplanabilirlik = 1 olmalıdır; değilse çelişen
hücre geçersiz sayılır (o ölçütün hesabından çıkar).
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
    KEY_WRONG_MARK,
    MAX_FLAWS,
    SHEET_QUESTIONS,
)


KEY_WRONG_CONFLICT = ("Anahtar yanlış (A) işaretli soruda kaynağa dayalı = hayır ve cevaplanabilirlik = 1 olmalı "
                      "(yönerge, Bölüm 4).")


class LabelError(Exception):
    """Dosya hiç okunamıyor (ör. sayfa ya da sütun yok)."""


@dataclass
class Label:
    bloom: str | None = None
    errors: int | None = None
    flaws: tuple[int, ...] | None = None  # yalnızca 1-19 arası madde numaraları
    grounded: bool | None = None
    answerable: int | None = None
    asr_error: bool | None = None  # sorunun hatası konuşma tanıma hatasından mı
    note: str = ""
    key_wrong: bool | None = None  # "Hatalı maddeler"de A var mı; hücre geçersizse None

    @property
    def acceptable(self) -> bool | None:
        """Birincil: anahtar yanlışsa kabul edilemez; değilse yazım hatası sayısı (A dahil) ≤ 1."""
        if self.key_wrong:
            return False
        return None if self.errors is None else self.errors <= ACCEPTABLE_MAX_ERRORS

    @property
    def acceptable_flaws_only(self) -> bool | None:
        """Ek: anahtar kuralı uygulanmadan, yalnızca 19 maddeye göre (numara sayısı ≤ 1).

        Numara sayısı = yazım hatası sayısı - 1 (A varsa); A yoksa birincil sonuçla aynıdır.
        """
        if self.errors is None:
            return None
        numbers = self.errors - 1 if self.key_wrong else self.errors
        return numbers <= ACCEPTABLE_MAX_ERRORS


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


def _flaws(value) -> tuple[tuple[int, ...], bool] | None:
    """"4, 12" ya da "4, A" biçimi: (madde numaraları, A var mı). Boşsa ((), False), geçersizse None.

    Numaralar 1-19 arası; A büyük ya da küçük harf olabilir. Hiçbiri tekrar edemez.
    """
    if value is None or not str(value).strip():
        return (), False
    text = str(value).strip()
    token = rf"(?:\d+|[{KEY_WRONG_MARK}{KEY_WRONG_MARK.lower()}])"
    if not re.fullmatch(rf"{token}(\s*[,;]\s*{token})*", text):
        return None
    tokens = [t.strip().upper() for t in re.split(r"[,;]", text)]
    marks = [t for t in tokens if t == KEY_WRONG_MARK]
    numbers = tuple(int(t) for t in tokens if t != KEY_WRONG_MARK)
    if len(marks) > 1 or len(set(numbers)) != len(numbers) or not all(1 <= n <= MAX_FLAWS for n in numbers):
        return None
    return numbers, bool(marks)


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

        parsed = _flaws(cell[COL_FLAWS])
        if parsed is None:
            report(item_id, COL_FLAWS, cell[COL_FLAWS],
                   f"1-{MAX_FLAWS} arası, tekrarsız numaralar ve en çok bir {KEY_WRONG_MARK} olmalı (ör. 4, 12 ya da 4, {KEY_WRONG_MARK})")
        else:
            label.flaws, label.key_wrong = parsed
            count = len(label.flaws) + (1 if label.key_wrong else 0)  # A, sayıya 1 olarak katılır
            if label.errors is not None and count != label.errors:
                report(item_id, COL_FLAWS, cell[COL_FLAWS], f"madde sayısı ({count}) yazım hatası sayısıyla ({label.errors}) uyuşmuyor")
            if label.key_wrong:
                # Yönerge, Bölüm 4: A işaretli soruda kaynağa dayalı = hayır, cevaplanabilirlik = 1
                for column, field, bad in ((COL_GROUNDED, "grounded", lambda v: v is True),
                                           (COL_ANSWERABLE, "answerable", lambda v: v is not None and v > 1)):
                    if bad(getattr(label, field)):
                        report(item_id, column, cell[column], KEY_WRONG_CONFLICT)
                        setattr(label, field, None)
        labels[item_id] = label

    for item_id in expected_ids:
        if item_id not in labels:
            report(item_id, COL_ID, None, "kimlik dosyada yok")
    return labels, problems
