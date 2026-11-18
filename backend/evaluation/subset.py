"""Alan öğretmeni alt kümesinin seçimi: docs/alt-kume-secim-kurali.md.

Anahtar dosyasından (export.py) 36 soruluk, alan × Bloom düzeyi × koşul × video
dengeli bir alt küme seçer. Rastgelelik için yalnızca kuraldaki tek üreteç
random.Random("20261118-alt-kume") kuraldaki sırayla kullanılır:

1. alan listesinin kopyası karıştırılır (koşul tablosunun satırları),
2. Bloom düzeyi listesinin kopyası karıştırılır (sütunlar),
3. alanlar alfabetik sırayla dolaşılıp her alan için rng.sample(Bloom düzeyleri, 3)
   ile ilk videonun (video_id sıralamasında) düzeyleri seçilir.

Değerlendiricilerin etiketleri seçimde kullanılmaz. Seçim dosyası (alt-kume.json)
koşul bilgisi taşır: depo dışındaki bir klasöre yazılır ve puanlama bitene kadar
depoya konmaz; depoya yalnızca SHA-256 özet değeri girer. Ekrana soru kimliği ve
koşul yazılmaz (çıktı kopyalanıp paylaşılabilir).

Alan öğretmeni dosyası (--ogretmen-dosyasi, --tohum, --girdi): alt kümedeki
sorular değerlendirici dosyasıyla aynı biçimde (export.py'nin yazma kodu) ve
tohumla karıştırılmış sırayla yazılır. Soru metinleri anahtarda olmadığı için
export.py'ye verilen çalıştırma dosyaları --girdi ile yeniden okunur; kimliklerin
anahtardakiyle birebir aynı olduğu denetlenir. Transkriptler yalnızca yerel
önbellekten okunur; YouTube'a ve OpenAI'a gidilmez.

Çalıştırma (backend klasöründen):
    python -m evaluation.subset --anahtar <anahtar.json> --cikti <klasör>
    python -m evaluation.subset --anahtar <anahtar.json> --cikti <klasör> \\
        --ogretmen-dosyasi <xlsx> --tohum <sayı> --girdi <dosya...>
"""

import argparse
import glob
import hashlib
import json
import os
import random
from pathlib import Path

from evaluation.common import BLOOM_LEVELS, load_key
from evaluation.export import (
    ExportError,
    assign_ids,
    collect,
    find_secrets,
    load_transcripts,
    read_flaws,
    read_runs,
    workbook_strings,
    write_rater_workbook,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RULE_FILE = "docs/alt-kume-secim-kurali.md"
RULE_VERSION = "alt-kume-v1 (2026-11-18)"
SEED = "20261118-alt-kume"
SUBSET_FILE = "alt-kume.json"
# Kural: alanlar alfabetik sırayla (alan kodları, docs/video-secim-kurali.md)
FIELDS = ["biyoloji", "edebiyat", "ingilizce", "matematik", "python", "tarih"]
CONDITIONS = ("rag", "full")
PER_VIDEO = 3  # her alanda bir videodan 3, öbür videodan 3 soru
# Hücre durumları
SELECTED, OTHER_VIDEO, EMPTY = "secildi", "oteki_video", "bos"


class SubsetError(Exception):
    """Girdi kurala uymuyor ya da çıktı yeri uygun değil."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside_repo(path: Path) -> bool:
    """Yol depo kökünün altında mı (kökün kendisi dahil). Windows'ta büyük-küçük harf gözetilmez."""
    target = os.path.normcase(str(Path(path).resolve()))
    root = os.path.normcase(str(REPO_ROOT))
    return target == root or target.startswith(root.rstrip("\\/") + os.sep)


def check_outside_repo(path: Path, what: str) -> None:
    if inside_repo(path):
        raise SubsetError(f"{what} depo içinde olamaz: seçim dosyası koşul bilgisi taşır ve puanlama bitene kadar "
                          "depoya girmez. Depo dışında bir klasör verin (ör. anahtar dosyasının klasörü).")


def videos_by_field(key: dict) -> dict[str, list[str]]:
    """Anahtardaki "videos" bölümünden alan -> video_id listesi (sıralı). Kurala uymuyorsa SubsetError."""
    videos = key.get("videos")
    if not isinstance(videos, dict) or not videos:
        raise SubsetError("Anahtarda 'videos' bölümü yok (export.py --video-bilgisi ile üretilmeli).")
    by_field: dict[str, list[str]] = {}
    for video_id, info in videos.items():
        by_field.setdefault(info.get("alan"), []).append(video_id)
    if sorted(by_field) != FIELDS:
        raise SubsetError(f"Anahtardaki alanlar kuraldaki altı alan değil: {', '.join(map(str, sorted(by_field, key=str)))}.")
    for field, ids in by_field.items():
        if len(ids) != 2:
            raise SubsetError(f"{field} alanında {len(ids)} video var; kural her alanda iki video ister.")
    return {field: sorted(by_field[field]) for field in FIELDS}


def question_index(key: dict) -> dict[tuple[str, str, str], str]:
    """(video_id, koşul, hedef düzey) -> soru kimliği. Aynı üçlüde iki soru varsa SubsetError."""
    index: dict[tuple[str, str, str], str] = {}
    for item_id, q in key.get("questions", {}).items():
        slot = (q["video_id"], q["condition"], q["bloom_target"])
        if slot in index:
            raise SubsetError(f"Anahtarda aynı video, koşul ve hedef düzeyde iki soru var ({q['condition']}, {q['bloom_target']}).")
        index[slot] = item_id
    return index


def plan(by_field: dict[str, list[str]]) -> tuple[dict, dict]:
    """Koşul tablosu ve video ataması; kuraldaki tek üreteçle, kuraldaki sırayla."""
    rng = random.Random(SEED)
    rows = list(FIELDS)
    rng.shuffle(rows)
    columns = list(BLOOM_LEVELS)
    rng.shuffle(columns)
    conditions = {field: {} for field in FIELDS}
    for i, field in enumerate(rows):
        for j, level in enumerate(columns):
            conditions[field][level] = "rag" if (i + j) % 2 == 0 else "full"
    # Okunurluk için kuraldaki düzey sırasıyla yaz
    conditions = {field: {level: conditions[field][level] for level in BLOOM_LEVELS} for field in FIELDS}

    assignment = {}
    for field in FIELDS:
        first, second = by_field[field]
        chosen = set(rng.sample(BLOOM_LEVELS, PER_VIDEO))
        assignment[field] = {first: [lv for lv in BLOOM_LEVELS if lv in chosen],
                             second: [lv for lv in BLOOM_LEVELS if lv not in chosen]}
    return conditions, assignment


def select(key: dict, key_sha256: str) -> dict:
    """Seçim dosyasının içeriği."""
    by_field = videos_by_field(key)
    index = question_index(key)
    conditions, assignment = plan(by_field)
    cells = []
    for field in FIELDS:
        video_of = {level: video for video, levels in assignment[field].items() for level in levels}
        for level in BLOOM_LEVELS:
            condition, wanted = conditions[field][level], video_of[level]
            other = next(v for v in by_field[field] if v != wanted)
            if (wanted, condition, level) in index:
                chosen, status = wanted, SELECTED
            elif (other, condition, level) in index:
                chosen, status = other, OTHER_VIDEO
            else:
                chosen, status = None, EMPTY
            cells.append({"alan": field, "bloom_duzeyi": level, "kosul": condition, "istenen_video": wanted,
                          "secilen_video": chosen, "soru_kimligi": index.get((chosen, condition, level)) if chosen else None,
                          "durum": status})
    counts = {status: sum(c["durum"] == status for c in cells) for status in (SELECTED, OTHER_VIDEO, EMPTY)}
    return {
        "kural": RULE_FILE,
        "kural_surumu": RULE_VERSION,
        "tohum": SEED,
        "anahtar_sha256": key_sha256,
        "alanlar": FIELDS,
        "bloom_duzeyleri": BLOOM_LEVELS,
        "kosul_tablosu": conditions,
        "video_atamasi": assignment,
        "hucreler": cells,
        "ozet": {"soru": counts[SELECTED] + counts[OTHER_VIDEO], **counts},
    }


def serialize(result: dict) -> bytes:
    """Sabit bayt dizisi: özet değeri işletim sisteminden bağımsız olsun diye satır sonu her zaman LF."""
    return (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_subset(result: dict, out_dir: Path) -> tuple[Path, bool]:
    """alt-kume.json'u yazar. Dosya varsa ve aynıysa dokunmaz; farklıysa üzerine yazmaz, SubsetError.

    Döner: (yol, yeni yazıldı mı).
    """
    check_outside_repo(out_dir, "Çıktı klasörü")
    path = Path(out_dir) / SUBSET_FILE
    data = serialize(result)
    if path.exists():
        if path.read_bytes() != data:
            raise SubsetError(f"{SUBSET_FILE} zaten var ve bu seçimden farklı; üzerine yazılmaz (özeti commit'lenmiş olabilir).")
        return path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path, True


def teacher_questions(key: dict, subset: dict, input_paths: list[Path], seed: int) -> list[dict]:
    """Alt kümedeki soruların değerlendirici dosyası için kayıtları, tohumla karıştırılmış sırayla.

    Sorular export.py'nin kodu ve anahtardaki tohumla yeniden toplanır; kimlikler ve
    soru bilgileri anahtardakiyle birebir aynı değilse SubsetError (yanlış girdi).
    """
    runs = [run for path in input_paths for run in read_runs(path)]
    produced, _, _ = collect(runs, key["prompt_version"])
    questions = assign_ids(produced, key["seed"])
    fields = ("video_id", "topic_index", "topic", "condition", "bloom_target", "pair_id")
    rebuilt = {q["id"]: {f: q[f] for f in fields} for q in questions}
    expected = {i: {f: q[f] for f in fields} for i, q in key["questions"].items()}
    if rebuilt != expected:
        raise SubsetError("Girdi dosyaları anahtarla uyuşmuyor: aynı tohumla yeniden verilen kimlikler anahtardakilerle "
                          "aynı değil. export.py'ye verilen dosyaların aynısını verin.")
    wanted = {c["soru_kimligi"] for c in subset["hucreler"] if c["soru_kimligi"]}
    chosen = sorted((q for q in questions if q["id"] in wanted), key=lambda q: q["id"])
    random.Random(seed).shuffle(chosen)
    return chosen


def write_teacher_file(path: Path, key: dict, subset: dict, input_paths: list[Path], seed: int) -> int:
    """Alan öğretmeni dosyasını export.py'nin değerlendirici dosyası yazma koduyla yazar; soru sayısını döndürür."""
    chosen = teacher_questions(key, subset, input_paths, seed)
    transcripts = load_transcripts(sorted({q["video_id"] for q in chosen}))
    path = Path(path)
    write_rater_workbook(path, chosen, transcripts, read_flaws())
    secrets = find_secrets(workbook_strings(path))
    if secrets:
        path.unlink()
        raise SubsetError(f"Alan öğretmeni dosyasında gizli bilgi bulundu ({', '.join(secrets)}); dosya silindi.")
    return len(chosen)


def run(key_path: Path, out_dir: Path) -> tuple[dict, Path, bool]:
    check_outside_repo(out_dir, "Çıktı klasörü")
    key = load_key(key_path)
    result = select(key, sha256_file(key_path))
    path, created = write_subset(result, out_dir)
    return result, path, created


def summary_lines(result: dict, path: Path, created: bool) -> list[str]:
    """Ekran özeti: soru kimliği ve koşul yazılmaz."""
    counts = result["ozet"]
    lines = [f"Seçilen soru: {counts['soru']} / {len(result['hucreler'])}",
             f"Öbür videodan alınan hücre: {counts[OTHER_VIDEO]}"]
    lines += [f"  - {c['alan']}, {c['bloom_duzeyi']}" for c in result["hucreler"] if c["durum"] == OTHER_VIDEO]
    lines.append(f"Boş kalan hücre: {counts[EMPTY]}")
    lines += [f"  - {c['alan']}, {c['bloom_duzeyi']}" for c in result["hucreler"] if c["durum"] == EMPTY]
    lines.append(f"{SUBSET_FILE} {'yazıldı' if created else 'zaten vardı, içeriği aynı'}.")
    lines.append(f"{SUBSET_FILE} SHA-256: {sha256_file(path)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Alan öğretmeni alt kümesini seçer (docs/alt-kume-secim-kurali.md).")
    parser.add_argument("--anahtar", type=Path, required=True, help="export.py'nin anahtar dosyası")
    parser.add_argument("--cikti", type=Path, required=True, help="alt-kume.json klasörü; depo dışında olmalı")
    parser.add_argument("--ogretmen-dosyasi", type=Path, help="Alan öğretmeni dosyası (xlsx)")
    parser.add_argument("--tohum", type=int, help="Alan öğretmeni dosyasındaki soru sırasının tohumu")
    parser.add_argument("--girdi", nargs="+", help="export.py'ye verilen çalıştırma dosyaları (joker karakter olabilir)")
    args = parser.parse_args(argv)
    if args.ogretmen_dosyasi and (args.tohum is None or not args.girdi):
        parser.error("--ogretmen-dosyasi ile --tohum ve --girdi de verilmeli.")
    try:
        result, path, created = run(args.anahtar, args.cikti)
        for line in summary_lines(result, path, created):
            print(line)
        if args.ogretmen_dosyasi:
            paths = [Path(p) for pattern in args.girdi for p in sorted(glob.glob(pattern))]
            if not paths:
                raise SubsetError("Girdi dosyası bulunamadı.")
            count = write_teacher_file(args.ogretmen_dosyasi, load_key(args.anahtar), result, paths, args.tohum)
            print(f"Alan öğretmeni dosyası yazıldı: {count} soru, tohum {args.tohum}.")
    except (SubsetError, ExportError) as exc:
        print(f"Hata: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
