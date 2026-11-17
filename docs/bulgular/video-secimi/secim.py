"""Ana deney videolarının seçimi: docs/video-secim-kurali.md, 5. bölüm.

Yalnızca adaylar.csv'deki `durum = aday` satırlarıyla çalışır. Sıra:

1. adaylar.csv git'te izlenmiyorsa ya da commit'lenmemiş değişiklik varsa çalışmaz
   (kural: aday listesi seçimden önce depoda olmalı).
2. Pilot kanalından gelen ve aynı kanaldan ikinci olan aday YouTube'a gidilmeden
   reddedilir (kural, 3. bölüm, 7. ölçüt). Aynı kanal sınırı bütün listede uygulanır;
   adaylar alan sırasıyla (kural, 1. bölüm), alan içinde arama sırasıyla işlenir,
   kanal ilk çıktığı alanda kalır.
3. adaylar.csv'deki süresi (sure_dk_sn, YouTube'da görünen süre) 10-35 dakika
   dışında kalan aday YouTube'a gidilmeden elenir (kural, 3. bölüm, 3. ölçüt).
4. Her adayın Türkçe altyazısı transkript servisi ve önbellek üzerinden bir kez
   alınır (video başına en çok bir YouTube isteği). Dil listesi yalnızca ["tr"]:
   kütüphane önce elle hazırlanmış Türkçe altyazıyı, yoksa otomatik olanı verir;
   gelen altyazının `is_generated` değeri altyazı türünü belirler. Altyazısı
   alınamayan aday gerekçesiyle elenir. Transkriptin son satırından ölçülen süre
   yalnızca bilgi olarak yazılır, elemede kullanılmaz.
5. YouTube engeli gelirse yeniden denenmez; betik durur, kaç adayın işlendiğini
   yazar ve sonuç dosyası yazmaz. Engel eleme gerekçesi değildir. Alınan
   transkriptler önbellekte kaldığı için betik sonra yeniden çalıştırılabilir.
6. Her alanda kalan adaylar arama sırasına (sira) göre dizilir,
   random.Random("20261110-<alan kodu>") ile karıştırılır; ardından elle hazırlanmış
   altyazısı olanlar kendi aralarındaki sıra korunarak öne alınır.
7. Sonuç secim.md ve secim.json dosyalarına yazılır; dosyalar varsa üzerine yazılmaz.

OpenAI'a gidilmez. Kelime ve parça sayısı temiz transkriptten mevcut kodla hesaplanır.

secim.md tablolarında hücre içindeki "|" karakteri "\\|" olarak kaçırılır (yoksa Markdown
onu sütun ayracı sanar). secim-notlar.md varsa içeriği secim.md'nin sonuna olduğu gibi eklenir;
seçimden sonra yazılan notlar bu dosyada tutulur, böylece secim.md yeniden üretilince kaybolmaz.

Çalıştırma (depo kökünden):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\video-secimi\\secim.py
secim.md'yi ağa çıkmadan mevcut secim.json'dan yeniden üretmek (yalnızca secim.md'nin
üzerine yazılır; secim.json ve adaylar.csv'ye dokunulmaz):
    backend\\.venv\\Scripts\\python.exe docs\\bulgular\\video-secimi\\secim.py --md-yeniden
"""

import argparse
import csv
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.chunking import fixed_size_chunks  # noqa: E402
from app.services.text_clean import clean_transcript  # noqa: E402
from app.services.transcript import TranscriptBlocked, TranscriptUnavailable, fetch_transcript  # noqa: E402
from app.services.transcript_cache import load_transcript  # noqa: E402
from app.services.youtube import InvalidYouTubeUrl, extract_video_id  # noqa: E402

HERE = Path(__file__).resolve().parent
CANDIDATES = HERE / "adaylar.csv"
CSV_COLUMNS = ["alan", "arama_ifadesi", "arama_tarihi", "sira", "baslik", "kanal", "url",
               "sure_dk_sn", "durum", "elenme_olcutu", "not"]
# Alan kodları, kural 1. bölümdeki sırayla; adaylar.csv'deki alan değerleri bunlardan biri olmalı.
# Tohumda olduğu gibi kullanılır.
FIELDS = ["biyoloji", "tarih", "matematik", "ingilizce", "edebiyat", "python"]
BILINGUAL_FIELDS = {"ingilizce"}  # kural, 7. bölüm
PILOT_CHANNELS = ["BETÜL BİYOLOJİ", "Ardıç Tarih", "Partikül Matematik", "Ms. Jasmin ELT", "tonguç 10. SINIF", "Fehmi UYAR"]
MIN_SECONDS, MAX_SECONDS = 10 * 60, 35 * 60
LANGUAGES = ["tr"]
SEED_FORMAT = "20261110-{alan}"
ROLES = ["birinci", "ikinci"]


class SelectionError(Exception):
    """Betik çalışmayı reddediyor (girdi kurala uymuyor)."""


class Stopped(Exception):
    """YouTube engeli: betik durdu."""

    def __init__(self, processed: int, total: int, video_id: str):
        super().__init__(f"YouTube engeli ({video_id}); {total} adayın {processed} tanesi işlendi.")
        self.processed, self.total, self.video_id = processed, total, video_id


def check_committed(path: Path, run=subprocess.run) -> None:
    """Dosya git'te izlenmiyorsa ya da commit'lenmemiş değişikliği varsa SelectionError."""
    if not path.exists():
        raise SelectionError(f"{path.name} yok.")
    tracked = run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ROOT, capture_output=True, text=True)
    if tracked.returncode != 0:
        raise SelectionError(f"{path.name} git'te izlenmiyor; önce commit'lenmeli (kural, 4. bölüm).")
    status = run(["git", "status", "--porcelain", "--", str(path)], cwd=ROOT, capture_output=True, text=True)
    if status.stdout.strip():
        raise SelectionError(f"{path.name} dosyasında commit'lenmemiş değişiklik var.")


def parse_duration(text: str) -> int:
    """"12:34" ya da "1:02:03" -> saniye."""
    parts = [int(p) for p in text.strip().split(":")]
    if not 2 <= len(parts) <= 3 or any(p < 0 for p in parts):
        raise ValueError(text)
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def mmss(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def read_candidates(path: Path) -> list[dict]:
    """`durum = aday` satırları; biçim hatası SelectionError verir (uydurma düzeltme yapılmaz)."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != CSV_COLUMNS:
            raise SelectionError(f"{path.name} sütunları kuraldakiyle aynı değil: {reader.fieldnames}")
        rows = list(reader)
    candidates = []
    for line, row in enumerate(rows, 2):
        if row["durum"] not in ("aday", "elendi"):
            raise SelectionError(f"{path.name} satır {line}: durum 'aday' ya da 'elendi' olmalı.")
        if row["durum"] != "aday":
            continue
        if row["alan"] not in FIELDS:
            raise SelectionError(f"{path.name} satır {line}: alan kodu şunlardan biri olmalı: {', '.join(FIELDS)}.")
        try:
            row["sira"] = int(row["sira"])
            row["sure_csv_sn"] = parse_duration(row["sure_dk_sn"])
            row["video_id"] = extract_video_id(row["url"])
        except (ValueError, InvalidYouTubeUrl) as exc:
            raise SelectionError(f"{path.name} satır {line}: sira, sure_dk_sn ya da url geçersiz ({exc}).") from exc
        candidates.append(row)
    return candidates


def _channel_key(name: str) -> str:
    return " ".join(name.replace("I", "ı").replace("İ", "i").lower().split())


def screen(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """Pilot kanalı ve aynı kanaldan ikinci aday reddedilir (kural, 3. bölüm, 7. ölçüt).

    Sıra: alan sırası (kural, 1. bölüm), sonra arama sırası; kanal ilk çıktığı adayda kalır.
    """
    pilot = {_channel_key(c) for c in PILOT_CHANNELS}
    seen, kept, rejected = {}, [], []
    for row in sorted(candidates, key=lambda r: (FIELDS.index(r["alan"]), r["sira"])):
        channel = _channel_key(row["kanal"])
        if channel in pilot:
            rejected.append({**row, "gerekce": "pilot kanalı (kural, 1. bölüm ve 3. bölüm 7. ölçüt)"})
        elif channel in seen:
            first = seen[channel]
            rejected.append({**row, "gerekce": f"aynı kanaldan ikinci aday; kanal {first['alan']} alanında "
                                              f"{first['sira']}. sıradaki aday (kural, 3. bölüm, 7. ölçüt)"})
        else:
            seen[channel] = row
            kept.append(row)
    return kept, rejected


def default_loader(video_id: str):
    """Önbellekte yoksa tek YouTube isteği; (transkript, kaynak) döndürür."""
    return load_transcript(video_id, LANGUAGES, fetch_transcript)


def measure(row: dict, load) -> dict:
    """Süreyi denetler, altyazıyı alır ve ölçer. Sonuçta `elendi` doluysa aday elenmiştir.

    Süre ölçütü adaylar.csv'deki süredir (kural, 3. bölüm, 3. ölçüt); dışındaysa YouTube'a gidilmez.
    Engel TranscriptBlocked olarak yükselir.
    """
    base = {k: row[k] for k in ("alan", "sira", "baslik", "kanal", "video_id", "sure_dk_sn", "sure_csv_sn")}
    if not MIN_SECONDS <= row["sure_csv_sn"] <= MAX_SECONDS:
        return {**base, "elendi": f"süre {row['sure_dk_sn']} (adaylar.csv), 10-35 dakika dışında"}
    try:
        raw, source = load(row["video_id"])
    except TranscriptUnavailable as exc:
        return {**base, "elendi": f"altyazı alınamadı: {exc}"}
    seconds = raw.duration_seconds  # yalnızca bilgi; elemede kullanılmaz
    result = {**base, "url": f"https://youtu.be/{row['video_id']}", "transkript_kaynagi": source, "dil": raw.language,
              "sure_transkript_sn": seconds, "sure_transkript": mmss(seconds), "elendi": None}
    clean = clean_transcript(raw)
    return {**result, "altyazi_turu": "otomatik" if raw.is_generated else "elle",
            "iki_dilli": row["alan"] in BILINGUAL_FIELDS,
            "kelime": sum(len(s.text.split()) for s in clean.segments),
            "parca": len(fixed_size_chunks(clean.segments, row["video_id"]))}


def order(field: str, eligible: list[dict]) -> list[dict]:
    """Arama sırasına göre dizilir, alan tohumuyla karıştırılır, elle altyazılılar öne alınır (sıralı kararlı)."""
    items = sorted(eligible, key=lambda r: r["sira"])
    random.Random(SEED_FORMAT.format(alan=field)).shuffle(items)
    return sorted(items, key=lambda r: r["altyazi_turu"] != "elle")


def select(candidates: list[dict], load=default_loader) -> dict:
    kept, rejected = screen(candidates)
    measured = []
    for done, row in enumerate(kept):
        try:
            measured.append(measure(row, load))
        except TranscriptBlocked as exc:
            raise Stopped(done, len(kept), row["video_id"]) from exc
    fields, videos = {}, {}
    for field in FIELDS:
        rows = [m for m in measured if m["alan"] == field]
        ranked = order(field, [m for m in rows if not m["elendi"]])
        for i, item in enumerate(ranked):
            item["sira_no"] = i + 1
            item["rol"] = ROLES[i] if i < len(ROLES) else "yedek"
            if i < len(ROLES):
                videos[item["video_id"]] = {"alan": field, "altyazi_turu": item["altyazi_turu"], "iki_dilli": item["iki_dilli"]}
        fields[field] = {"tohum": SEED_FORMAT.format(alan=field), "siralama": ranked,
                         "elenen": [m for m in rows if m["elendi"]]}
    return {
        "kural": "docs/video-secim-kurali.md",
        "dil": LANGUAGES,
        "sure_araligi_sn": [MIN_SECONDS, MAX_SECONDS],
        "alanlar": fields,
        "reddedilen": [{k: r[k] for k in ("alan", "sira", "baslik", "kanal", "video_id", "gerekce")} for r in rejected],
        # Değerlendirme paketinin video bilgi dosyası biçimi: birinci ve ikinci videolar
        "videos": videos,
    }


NOTES_FILE = "secim-notlar.md"


def cell(value) -> str:
    """Tablo hücresi: "|" sütun ayracı sanılmasın diye kaçırılır, satır sonu boşluğa çevrilir."""
    return " ".join(str(value).replace("|", "\\|").splitlines())


def render(result: dict, notes: str | None = None) -> str:
    """secim.md metni. `notes` verilirse (secim-notlar.md içeriği) sona olduğu gibi eklenir."""
    lines =["# Ana deney video seçimi", "", "Kural: [docs/video-secim-kurali.md](../../video-secim-kurali.md). "
             "Eleme adaylar.csv'deki süreyle (YouTube'da görünen süre) yapıldı; transkriptin son satırından "
             "ölçülen süre yalnızca bilgi olarak yazıldı.", ""]
    for field, block in result["alanlar"].items():
        lines += [f"## {field}", "", f"Tohum: `{block['tohum']}`", "",
                  "| Sıra | Rol | Başlık | Kanal | Bağlantı | Süre (csv) | Süre (transkript) | Altyazı | İki dilli | Kelime | Parça |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in block["siralama"]:
            values = [r["sira_no"], r["rol"], r["baslik"], r["kanal"], r["url"], r["sure_dk_sn"], r["sure_transkript"],
                      r["altyazi_turu"], "evet" if r["iki_dilli"] else "hayır", r["kelime"], r["parca"]]
            lines.append("| " + " | ".join(cell(v) for v in values) + " |")
        if len(block["siralama"]) < len(ROLES):
            lines.append(f"\nBu alanda {len(block['siralama'])} uygun video kaldı; {len(ROLES)} gerekli.")
        if block["elenen"]:
            lines += ["", "Elenen:", ""] + [f"- {r['baslik']} ({r['kanal']}): {r['elendi']}" for r in block["elenen"]]
        lines.append("")
    if result["reddedilen"]:
        lines += ["## Reddedilen adaylar", ""] + [f"- {r['alan']}, {r['baslik']} ({r['kanal']}): {r['gerekce']}" for r in result["reddedilen"]]
        lines.append("")
    text = "\n".join(lines)
    if notes and notes.strip():
        text = text.rstrip("\n") + "\n\n" + notes.strip("\n") + "\n"
    return text


def read_notes(out_dir: Path) -> str | None:
    path = out_dir / NOTES_FILE
    return path.read_text(encoding="utf-8") if path.exists() else None


def write_outputs(result: dict, out_dir: Path) -> None:
    md = render(result, read_notes(out_dir))
    for name, text in (("secim.json", json.dumps(result, ensure_ascii=False, indent=2)), ("secim.md", md)):
        with (out_dir / name).open("x", encoding="utf-8") as f:
            f.write(text)


def rebuild_md(out_dir: Path) -> Path:
    """Ağa çıkmadan secim.json'dan secim.md'yi yeniden yazar; yalnızca secim.md değişir."""
    source = out_dir / "secim.json"
    if not source.exists():
        raise SelectionError("secim.json yok; secim.md yeniden üretilemez.")
    result = json.loads(source.read_text(encoding="utf-8"))
    target = out_dir / "secim.md"
    with target.open("w", encoding="utf-8") as f:
        f.write(render(result, read_notes(out_dir)))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ana deney video seçimi (docs/video-secim-kurali.md).")
    parser.add_argument("--md-yeniden", action="store_true",
                        help="secim.md'yi mevcut secim.json'dan yeniden üret (ağa çıkmaz, secim.json'a dokunmaz)")
    args = parser.parse_args(argv)
    if args.md_yeniden:
        try:
            path = rebuild_md(HERE)
        except SelectionError as exc:
            print(f"Çalışmayı reddetti: {exc}")
            return 1
        print(f"{path.name} secim.json'dan yeniden yazıldı.")
        return 0
    try:
        check_committed(CANDIDATES)
        candidates = read_candidates(CANDIDATES)
        if not candidates:
            raise SelectionError("adaylar.csv'de aday yok.")
        if (HERE / "secim.json").exists() or (HERE / "secim.md").exists():
            raise SelectionError("secim.json ya da secim.md zaten var; üzerine yazılmaz.")
        result = select(candidates)
    except SelectionError as exc:
        print(f"Çalışmayı reddetti: {exc}")
        return 1
    except Stopped as exc:
        print(f"Durdu: {exc} Sonuç dosyası yazılmadı.")
        return 2
    write_outputs(result, HERE)
    print(f"Seçim yazıldı: {len(result['videos'])} video (birinci ve ikinci).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
