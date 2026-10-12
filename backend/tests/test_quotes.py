import pytest

from app.services.quotes import QuoteLocator, normalize, turkish_lower
from app.services.transcript import Segment


def test_turkish_lower():
    assert turkish_lower("IŞIK İSTANBUL") == "ışık istanbul"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Merhaba,   ARKADAŞLAR!", "merhaba arkadaşlar"),
        ("[Müzik] İkili   arama", "ikili arama"),
        ("bir,iki.üç", "bir iki üç"),
        ("Python'un listesi", "python un listesi"),
        ("O(n log n)", "o n log n"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


def make_locator():
    return QuoteLocator(
        [
            Segment("Merhaba arkadaşlar bugün sıralama", 0.0, 4.0),
            Segment("algoritmalarını konuşacağız", 4.0, 3.0),
            Segment("İlk olarak kabarcık sıralaması", 30.0, 4.0),
            Segment("komşu elemanları karşılaştırır", 34.0, 4.0),
            Segment("ve yanlış sıradaysa yer değiştirir", 60.0, 4.0),
            Segment("bu işlem tekrarlanır", 64.0, 3.0),
        ]
    )


def test_find_returns_start_of_segment_where_quote_begins():
    assert make_locator().find("kabarcık sıralaması komşu elemanları karşılaştırır") == 30.0
    assert make_locator().find("komşu elemanları karşılaştırır ve yanlış sıradaysa") == 34.0


def test_find_ignores_case_whitespace_and_punctuation():
    quote = "  İLK olarak, Kabarcık   sıralaması komşu elemanları karşılaştırır. "
    assert make_locator().find(quote) == 30.0


def test_find_missing_quote():
    assert make_locator().find("kabarcık sıralaması en hızlı sıralama algoritmasıdır") is None


def test_find_rejects_short_quote():
    # Transkriptte geçse de 5 kelimeden kısa alıntı kanıt sayılmaz
    assert make_locator().find("kabarcık sıralaması komşu") is None


def test_find_requires_whole_words():
    # "arkadaşlar" yerine "kadaşlar": kelime parçası eşleşmemeli
    assert make_locator().find("kadaşlar bugün sıralama algoritmalarını konuşacağız") is None


def test_find_with_word_changed():
    # Kelimeler birebir aynı olmalı: tek kelime farkı doğrulamayı bozar
    assert make_locator().find("kabarcık sıralaması yakın elemanları karşılaştırır") is None


def test_empty_segments():
    assert QuoteLocator([]).find("bir iki üç dört beş") is None


# Gerçek test videosundan (109kCbVtU1U) kesit: 435,4 sn'de başlayan 30 sn'lik blok.
# Aşama 6 ilk gerçek testinde Soru 3'ün alıntısı bu bloktaydı; ayrıntı:
# docs/bulgular/asama-6-ilk-gercek-test.md
REAL_EXCERPT = [
    Segment("yapıyoruz? Enerji üretimini", 435.4, 1.4),
    Segment("gerçekleştirmek için. Niye yapıyoruz", 436.8, 1.959),
    Segment("derken bunu tabii ki de kimler yapıyor?", 438.759, 2.16),
    Segment("Kemosentetik canlılar yapıyor.", 440.919, 1.801),
    Segment("Kemosentetik canlıların tamamının", 442.72, 4.039),
    Segment("prokaryot olduğunu unutma. Bak bu çok", 444.919, 1.84),
    Segment("önemliydi. Ünlemle böyle sağa sola,", 446.759, 2.16),
]


def test_real_example_soru3_uses_segment_start_not_block_start():
    # Model alıntının başına [591] yazmıştı; etiket temizlenir, zaman alıntıdan hesaplanır.
    # Blok düzeyinde sonuç 435,4 idi; cümle 442,72'de başlayan segmentte söyleniyor.
    quote = "[591] Kemosentetik canlıların tamamının prokaryot olduğunu unutma"
    assert QuoteLocator(REAL_EXCERPT).find(quote) == pytest.approx(442.72)
