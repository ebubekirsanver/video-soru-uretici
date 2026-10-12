import pytest

from app.services.text_clean import clean_text, clean_transcript, prepare_transcript
from app.services.transcript import Segment, Transcript


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("[Müzik] merhaba arkadaşlar", "merhaba arkadaşlar"),
        ("bugün [Alkış] sıralama", "bugün sıralama"),
        ("[ __ ] neyse", "neyse"),
        ("♪ şarkı sözü ♪", "şarkı sözü"),
        ("O(n log n) karmaşıklık", "O(n log n) karmaşıklık"),  # normal parantez kalır
        ("(gülüşmeler) devam edelim", "(gülüşmeler) devam edelim"),
        ("  çok    boşluk  ", "çok boşluk"),
        ("[Müzik]", ""),
        ("dizi[0] elemanı", "dizi elemanı"),  # bilinen sınır: kod içindeki köşeli parantez de silinir
    ],
)
def test_clean_text(raw, expected):
    assert clean_text(raw) == expected


def make_transcript():
    return Transcript(
        video_id="vid",
        language="tr",
        is_generated=True,
        segments=[
            Segment("[Müzik]", 0.0, 3.0),
            Segment("merhaba [Alkış] arkadaşlar", 3.0, 2.0),
            Segment("♪", 5.0, 1.0),
            Segment("bugün sıralama", 6.0, 2.0),
        ],
    )


def test_clean_transcript_drops_empty_and_keeps_timestamps():
    cleaned = clean_transcript(make_transcript())
    assert [(s.text, s.start, s.duration) for s in cleaned.segments] == [
        ("merhaba arkadaşlar", 3.0, 2.0),
        ("bugün sıralama", 6.0, 2.0),
    ]
    assert cleaned.video_id == "vid" and cleaned.language == "tr"


def test_clean_transcript_does_not_modify_raw():
    raw = make_transcript()
    clean_transcript(raw)
    assert [s.text for s in raw.segments] == ["[Müzik]", "merhaba [Alkış] arkadaşlar", "♪", "bugün sıralama"]


def test_prepare_transcript_modes():
    raw = make_transcript()
    assert prepare_transcript(raw, "raw") is raw
    assert len(prepare_transcript(raw, "clean").segments) == 2
