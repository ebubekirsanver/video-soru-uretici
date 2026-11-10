"""Paketin ortak sabitleri ve küçük yardımcıları."""

import json
from pathlib import Path

BLOOM_LEVELS = ["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]
CONDITIONS = ("full", "rag")
MAX_FLAWS = 19  # docs/soru-yazim-hatalari.md: 19 madde
ACCEPTABLE_MAX_ERRORS = 1  # AS1 ölçütü: 0-1 yazım hatası kabul edilebilir
DEFAULT_ALPHA = 0.05

SHEET_QUESTIONS = "Sorular"
SHEET_GUIDE = "Yönerge"
SHEET_FLAWS = "Yazım maddeleri"
TRANSCRIPT_PREFIX = "T-"
GUIDE_PLACEHOLDER = "YÖNERGE: kullanıcı tarafından doldurulacak"

COL_ID = "Kimlik"
COL_VIDEO = "Video bağlantısı"
COL_TRANSCRIPT = "Transkript sayfası"
COL_QUESTION = "Soru"
COL_OPTIONS = ["Seçenek A", "Seçenek B", "Seçenek C", "Seçenek D"]
COL_ANSWER = "Modelin işaretlediği doğru seçenek"
COL_BLOOM = "Bloom düzeyi"
COL_ERRORS = "Yazım hatası sayısı"
COL_FLAWS = "Hatalı maddeler"
COL_GROUNDED = "Kaynağa dayalı mı"
COL_ANSWERABLE = "Cevaplanabilirlik"
COL_NOTE = "Not"
VISIBLE_COLUMNS = [COL_ID, COL_VIDEO, COL_TRANSCRIPT, COL_QUESTION, *COL_OPTIONS, COL_ANSWER]
FILL_COLUMNS = [COL_BLOOM, COL_ERRORS, COL_FLAWS, COL_GROUNDED, COL_ANSWERABLE, COL_NOTE]


def load_key(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def num(value, digits: int = 3) -> str:
    """Rapordaki sayı: virgüllü; tanımsız değer için "tanımsız"."""
    if value is None:
        return "tanımsız"
    return f"{value:.{digits}f}".replace(".", ",")


def interval(low, high, digits: int = 3) -> str:
    if low is None or high is None:
        return "tanımsız"
    return f"[{num(low, digits)}; {num(high, digits)}]"


def table(headers: list[str], rows: list[list]) -> list[str]:
    """Markdown tablosu satırları."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |" for row in rows]
    return lines
