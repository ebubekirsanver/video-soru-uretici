"""Paketin ortak sabitleri ve küçük yardımcıları."""

import json
import os
from pathlib import Path

# Depo kökü: körlemeyi bozabilecek ya da tam transkript içeren dosyalar bunun altına yazılmaz
REPO_ROOT = Path(__file__).resolve().parents[2]

BLOOM_LEVELS = ["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]
CONDITIONS = ("full", "rag")
MAX_FLAWS = 19  # docs/soru-yazim-hatalari.md: 19 madde
ACCEPTABLE_MAX_ERRORS = 1  # AS1 ölçütü: 0-1 yazım hatası kabul edilebilir
DEFAULT_ALPHA = 0.05

# "Anahtar yanlış" kuralı (yönerge, Bölüm 4; 2026-11-25, puanlamadan önce): modelin doğru diye
# işaretlediği seçenek videoya göre yanlışsa "Hatalı maddeler"e A yazılır. A yazım hatası
# sayısına 1 olarak katılır ve soru başka hatası olmasa da kabul edilemez sayılır. Moore vd.
# (2023) listesinin maddesi değildir.
KEY_WRONG_MARK = "A"
KEY_WRONG_NAME = "Anahtar yanlış"
KEY_WRONG_TEXT = ("Modelin işaretlediği cevap videoya göre yanlış (anahtar yanlış). "
                  "Yazım hatası sayısına 1 olarak katılır; soru kabul edilemez sayılır.")

SHEET_QUESTIONS = "Sorular"
SHEET_GUIDE = "Yönerge"
SHEET_FLAWS = "Yazım maddeleri"
TRANSCRIPT_PREFIX = "T-"
# Değerlendirme yönergesi: metni Excel'in Yönerge sayfasına yazılır (export --yonerge)
GUIDE_FILE = REPO_ROOT / "docs" / "degerlendirme-yonergesi-v1.md"

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
COL_ASR = "Tanıma hatası kaynaklı mı"
COL_NOTE = "Not"
VISIBLE_COLUMNS = [COL_ID, COL_VIDEO, COL_TRANSCRIPT, COL_QUESTION, *COL_OPTIONS, COL_ANSWER]
FILL_COLUMNS = [COL_BLOOM, COL_ERRORS, COL_FLAWS, COL_GROUNDED, COL_ANSWERABLE, COL_ASR, COL_NOTE]

# Başlığın altındaki açıklama satırı; sorular bir alttaki satırdan başlar
DESCRIPTION_LABEL = "Açıklama"
DATA_START_ROW = 3
COLUMN_DESCRIPTIONS = {
    COL_ASR: "Sorudaki hata (yanlış bilgi, anlamsız ifade, yanlış doğru cevap) transkriptteki konuşma tanıma "
             "hatasından kaynaklanıyorsa evet. Sorunun hatası yoksa hayır.",
}

# Video bilgi dosyası (Hafta-3): altyazı türü ve iki dilli olma analizde değişkendir
SUBTITLE_TYPES = ("elle", "otomatik")


class InsideRepoError(ValueError):
    """Dosya depo içine yazılmak istendi."""


def inside_repo(path: Path) -> bool:
    """Yol depo kökünün altında mı (kökün kendisi dahil). Windows'ta büyük-küçük harf gözetilmez."""
    target = os.path.normcase(str(Path(path).resolve()))
    root = os.path.normcase(str(REPO_ROOT))
    return target == root or target.startswith(root.rstrip("\\/") + os.sep)


def check_outside_repo(path: Path, what: str, reason: str) -> None:
    """Yol depo içindeyse InsideRepoError. Mesaj: "<what> depo içinde olamaz: <reason>."

    Hiçbir dosya ya da klasör oluşturulmadan önce çağrılmalı.
    """
    if inside_repo(path):
        raise InsideRepoError(f"{what} depo içinde olamaz: {reason}.")


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
