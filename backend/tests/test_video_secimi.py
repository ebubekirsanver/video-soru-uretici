"""Ana deney video seçim betiği (docs/bulgular/video-secimi/secim.py). Sahte transkript servisi; YouTube'a gidilmez."""

import csv
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.transcript import Segment, Transcript, TranscriptBlocked, TranscriptUnavailable

SCRIPT = Path(__file__).resolve().parents[2] / "docs" / "bulgular" / "video-secimi" / "secim.py"
spec = importlib.util.spec_from_file_location("secim", SCRIPT)
secim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(secim)

IDS = [f"vid{i:08d}" for i in range(20)]  # 11 karakterlik sahte video kimlikleri


def row(alan, sira, video_id, kanal=None, sure="20:00", durum="aday"):
    return {"alan": alan, "arama_ifadesi": "x konu anlatımı", "arama_tarihi": "2026-11-11 10:00", "sira": str(sira),
            "baslik": f"Ders {video_id}", "kanal": kanal or f"Kanal {video_id}", "url": f"https://www.youtube.com/watch?v={video_id}",
            "sure_dk_sn": sure, "durum": durum, "elenme_olcutu": "", "not": ""}


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=secim.CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


class FakeLoader:
    """Sahte transkript servisi: video başına süre, elle/otomatik ve hata verilebilir; çağrıları sayar."""

    def __init__(self, minutes=None, manual=(), unavailable=(), blocked=()):
        self.minutes, self.manual = minutes or {}, set(manual)
        self.unavailable, self.blocked = set(unavailable), set(blocked)
        self.calls = []

    def __call__(self, video_id):
        self.calls.append(video_id)
        if video_id in self.blocked:
            raise TranscriptBlocked("engel")
        if video_id in self.unavailable:
            raise TranscriptUnavailable("Bu videoda altyazılar kapalı.")
        end = self.minutes.get(video_id, 20) * 60
        segments = [Segment("merhaba arkadaşlar bugün konu anlatıyoruz", 0.0, 5.0), Segment("son cümle", end - 5, 5.0)]
        return Transcript(video_id, "tr", video_id not in self.manual, segments), "youtube"


def candidates(tmp_path, rows):
    return secim.read_candidates(write_csv(tmp_path / "adaylar.csv", rows))


def five(alan, start=0):
    return [row(alan, i + 1, IDS[start + i]) for i in range(5)]


def order_ids(result, alan):
    return [r["video_id"] for r in result["alanlar"][alan]["siralama"]]


# --- Sıralama --------------------------------------------------------------------------


def test_order_fixed_by_seed_and_matches_rule(tmp_path):
    rows = candidates(tmp_path, five("biyoloji"))
    first = secim.select(rows, FakeLoader())
    second = secim.select(candidates(tmp_path, list(reversed(five("biyoloji")))), FakeLoader())
    assert order_ids(first, "biyoloji") == order_ids(second, "biyoloji")  # csv satır sırası etkilemez
    expected = sorted(IDS[:5])  # sira 1-5 kimlik sırasıyla aynı
    import random
    random.Random("20261110-biyoloji").shuffle(expected)
    assert order_ids(first, "biyoloji") == expected
    assert [r["rol"] for r in first["alanlar"]["biyoloji"]["siralama"]] == ["birinci", "ikinci", "yedek", "yedek", "yedek"]


def test_seed_depends_on_field_name(tmp_path):
    bio = secim.select(candidates(tmp_path, five("biyoloji")), FakeLoader())
    tarih_rows = [{**r, "alan": "tarih"} for r in five("biyoloji")]
    tarih = secim.select(candidates(tmp_path, tarih_rows), FakeLoader())
    assert order_ids(bio, "biyoloji") != order_ids(tarih, "tarih")


def test_manual_subtitles_moved_to_front_keeping_order(tmp_path):
    rows = candidates(tmp_path, five("biyoloji"))
    shuffled = order_ids(secim.select(rows, FakeLoader()), "biyoloji")
    manual = {shuffled[3], shuffled[1]}
    result = secim.select(rows, FakeLoader(manual=manual))
    ranked = order_ids(result, "biyoloji")
    assert ranked[:2] == [shuffled[1], shuffled[3]]  # elle olanlar kendi aralarındaki sırayla önde
    assert ranked[2:] == [v for v in shuffled if v not in manual]
    assert [r["altyazi_turu"] for r in result["alanlar"]["biyoloji"]["siralama"]][:2] == ["elle", "elle"]
    assert set(result["videos"]) == manual


# --- Eleme ve ret ----------------------------------------------------------------------


@pytest.mark.parametrize("sure", ["9:59", "35:01", "1:00:00"])
def test_csv_duration_outside_range_eliminated_without_request(tmp_path, sure):
    rows = five("biyoloji")
    rows[0]["sure_dk_sn"] = sure
    loader = FakeLoader()
    result = secim.select(candidates(tmp_path, rows), loader)
    assert IDS[0] not in order_ids(result, "biyoloji")
    (eliminated,) = result["alanlar"]["biyoloji"]["elenen"]
    assert eliminated["video_id"] == IDS[0] and "10-35 dakika dışında" in eliminated["elendi"]
    assert "adaylar.csv" in eliminated["elendi"]
    assert IDS[0] not in loader.calls  # csv süresiyle elenen için YouTube'a gidilmez


@pytest.mark.parametrize("sure", ["10:00", "35:00"])
def test_csv_duration_boundaries_kept(tmp_path, sure):
    rows = five("biyoloji")
    rows[0]["sure_dk_sn"] = sure
    result = secim.select(candidates(tmp_path, rows), FakeLoader())
    assert IDS[0] in order_ids(result, "biyoloji")


@pytest.mark.parametrize("minutes", [9, 36])
def test_transcript_duration_only_informational(tmp_path, minutes):
    # csv'de 20:00, transkript 9 ya da 36 dakika: elenmez, transkript süresi bilgi olarak yazılır
    result = secim.select(candidates(tmp_path, five("biyoloji")), FakeLoader(minutes={IDS[0]: minutes}))
    assert IDS[0] in order_ids(result, "biyoloji")
    item = next(r for r in result["alanlar"]["biyoloji"]["siralama"] if r["video_id"] == IDS[0])
    assert item["sure_transkript"] == f"{minutes}:00" and item["sure_dk_sn"] == "20:00"
    assert result["alanlar"]["biyoloji"]["elenen"] == []


def test_unavailable_subtitles_eliminated(tmp_path):
    result = secim.select(candidates(tmp_path, five("biyoloji")), FakeLoader(unavailable={IDS[2]}))
    (eliminated,) = result["alanlar"]["biyoloji"]["elenen"]
    assert eliminated["video_id"] == IDS[2] and eliminated["elendi"].startswith("altyazı alınamadı")


def test_second_candidate_from_same_channel_rejected(tmp_path):
    rows = five("biyoloji") + [row("tarih", 1, IDS[10], kanal="kanal ders 1"), row("tarih", 2, IDS[11], kanal=" Kanal  Ders 1 ")]
    loader = FakeLoader()
    rows[1]["kanal"] = "Kanal Ders 1"  # biyolojide aynı kanal, tarihten önce gelir
    result = secim.select(candidates(tmp_path, rows), loader)
    rejected = {r["video_id"]: r["gerekce"] for r in result["reddedilen"]}
    assert set(rejected) == {IDS[10], IDS[11]}
    assert all("aynı kanaldan ikinci aday" in g and "biyoloji alanında 2. sıradaki" in g for g in rejected.values())
    assert IDS[10] not in loader.calls and IDS[11] not in loader.calls  # reddedilen için YouTube'a gidilmez


def test_same_channel_kept_in_first_field_by_rule_order(tmp_path):
    # Kanal csv'de önce tarihte (sira 1), sonra biyolojide (sira 5) yazılı; kural sırasında biyoloji önce gelir
    rows = [row("tarih", 1, IDS[10], kanal="Ortak Kanal")] + five("biyoloji")
    rows[-1]["kanal"] = "Ortak Kanal"
    result = secim.select(candidates(tmp_path, rows), FakeLoader())
    assert IDS[4] in order_ids(result, "biyoloji")
    (rejected,) = result["reddedilen"]
    assert rejected["video_id"] == IDS[10] and rejected["alan"] == "tarih"
    assert "biyoloji alanında 5. sıradaki" in rejected["gerekce"]


def test_same_channel_within_field_keeps_earlier_search_rank(tmp_path):
    rows = five("biyoloji")
    rows[1]["kanal"] = rows[3]["kanal"] = "Tek Kanal"
    result = secim.select(candidates(tmp_path, list(reversed(rows))), FakeLoader())
    assert [r["video_id"] for r in result["reddedilen"]] == [IDS[3]]


@pytest.mark.parametrize("channel", secim.PILOT_CHANNELS + ["Tonguç 10. Sınıf", "betül biyoloji"])
def test_pilot_channels_rejected(tmp_path, channel):
    rows = five("biyoloji")
    rows[0]["kanal"] = channel
    loader = FakeLoader()
    result = secim.select(candidates(tmp_path, rows), loader)
    assert result["reddedilen"][0]["video_id"] == IDS[0] and "pilot kanalı" in result["reddedilen"][0]["gerekce"]
    assert IDS[0] not in loader.calls


def test_eliminated_rows_in_csv_ignored(tmp_path):
    rows = five("biyoloji") + [row("biyoloji", 6, IDS[6], durum="elendi")]
    loader = FakeLoader()
    secim.select(candidates(tmp_path, rows), loader)
    assert IDS[6] not in loader.calls


# --- Engel -----------------------------------------------------------------------------


def test_block_stops_without_retry(tmp_path):
    loader = FakeLoader(blocked={IDS[2]})
    with pytest.raises(secim.Stopped) as exc:
        secim.select(candidates(tmp_path, five("biyoloji")), loader)
    assert (exc.value.processed, exc.value.total) == (2, 5)
    assert loader.calls == IDS[:3]  # engelden sonra istek yok, engelli video bir kez


def test_main_does_not_write_output_on_block(tmp_path, monkeypatch):
    path = write_csv(tmp_path / "adaylar.csv", five("biyoloji"))
    monkeypatch.setattr(secim, "CANDIDATES", path)
    monkeypatch.setattr(secim, "HERE", tmp_path)
    monkeypatch.setattr(secim, "check_committed", lambda p: None)
    monkeypatch.setattr(secim, "default_loader", FakeLoader(blocked={IDS[0]}))
    monkeypatch.setattr(secim.select, "__defaults__", (secim.default_loader,))
    assert secim.main() == 2
    assert not (tmp_path / "secim.json").exists()


# --- Çıktı ve video bilgisi --------------------------------------------------------------


def test_output_fields_and_video_info(tmp_path):
    rows = five("ingilizce") + five("biyoloji", 5)
    result = secim.select(candidates(tmp_path, rows), FakeLoader(minutes={IDS[0]: 12}))
    first = result["alanlar"]["ingilizce"]["siralama"][0]
    assert {"baslik", "kanal", "url", "sure_dk_sn", "sure_transkript", "altyazi_turu", "iki_dilli", "kelime", "parca"} <= set(first)
    assert first["url"] == f"https://youtu.be/{first['video_id']}"
    assert first["kelime"] == 7 and first["parca"] == 1
    assert len(result["videos"]) == 4
    assert {v["iki_dilli"] for k, v in result["videos"].items() if v["alan"] == "ingilizce"} == {True}
    assert {v["iki_dilli"] for k, v in result["videos"].items() if v["alan"] == "biyoloji"} == {False}
    assert result["alanlar"]["ingilizce"]["tohum"] == "20261110-ingilizce"
    secim.write_outputs(result, tmp_path)
    assert "## ingilizce" in (tmp_path / "secim.md").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        secim.write_outputs(result, tmp_path)  # üzerine yazılmaz


def test_video_info_accepted_by_evaluation_export(tmp_path):
    from evaluation.export import read_video_info

    result = secim.select(candidates(tmp_path, five("biyoloji")), FakeLoader())
    secim.write_outputs(result, tmp_path)
    info = read_video_info(tmp_path / "secim.json")
    assert set(info) == set(result["videos"]) and all(v["altyazi_turu"] == "otomatik" for v in info.values())


# --- Girdi denetimi --------------------------------------------------------------------


def git_result(code=0, out=""):
    return SimpleNamespace(returncode=code, stdout=out)


def test_refuses_missing_untracked_or_modified_csv(tmp_path):
    with pytest.raises(secim.SelectionError, match="yok"):
        secim.check_committed(tmp_path / "adaylar.csv")
    path = write_csv(tmp_path / "adaylar.csv", five("biyoloji"))
    with pytest.raises(secim.SelectionError, match="izlenmiyor"):
        secim.check_committed(path, run=lambda *a, **k: git_result(1))
    with pytest.raises(secim.SelectionError, match="commit'lenmemiş"):
        secim.check_committed(path, run=lambda *a, **k: git_result(0, " M adaylar.csv"))
    secim.check_committed(path, run=lambda *a, **k: git_result(0, ""))


def test_real_candidates_file_readable():
    # Gerçek aday listesi (2026-11-17): başlık kuraldaki sütunlar, adaylar biçim hatası olmadan okunur.
    with secim.CANDIDATES.open(encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == secim.CSV_COLUMNS
    rows = secim.read_candidates(secim.CANDIDATES)
    assert {r["alan"] for r in rows} <= set(secim.FIELDS)


@pytest.mark.parametrize(
    "change,message",
    [
        ({"alan": "Biyoloji"}, "alan kodu şunlardan biri"),
        ({"alan": "İngilizce"}, "alan kodu şunlardan biri"),
        ({"alan": "Python programlama"}, "alan kodu şunlardan biri"),
        ({"durum": "belki"}, "durum"),
        ({"sure_dk_sn": "yirmi"}, "geçersiz"),
        ({"url": "https://example.com/x"}, "geçersiz"),
    ],
)
def test_invalid_rows_rejected(tmp_path, change, message):
    with pytest.raises(secim.SelectionError, match=message):
        candidates(tmp_path, [{**row("biyoloji", 1, IDS[0]), **change}])


def test_field_codes_match_rule_text():
    rule = (SCRIPT.parents[2] / "video-secim-kurali.md").read_text(encoding="utf-8")
    line = next(l for l in rule.splitlines() if l.startswith("- Alan kodları"))
    codes = [c.strip(" .") for c in line.split(":", 1)[1].split(",")]
    assert codes == secim.FIELDS  # aynı kodlar, aynı sıra
    assert 'random.Random("20261110-<alan kodu>")' in rule and secim.SEED_FORMAT == "20261110-{alan}"


@pytest.mark.parametrize("alan", secim.FIELDS)
def test_all_field_codes_accepted(tmp_path, alan):
    (item,) = candidates(tmp_path, [row(alan, 1, IDS[0])])
    assert item["alan"] == alan


def test_wrong_columns_rejected(tmp_path):
    path = tmp_path / "adaylar.csv"
    path.write_text("alan,baslik\nbiyoloji,x\n", encoding="utf-8")
    with pytest.raises(secim.SelectionError, match="sütunları"):
        secim.read_candidates(path)


def test_parse_duration():
    assert secim.parse_duration("12:34") == 754
    assert secim.parse_duration("1:02:03") == 3723
    with pytest.raises(ValueError):
        secim.parse_duration("12")
