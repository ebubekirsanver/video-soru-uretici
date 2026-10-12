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


@pytest.mark.parametrize(
    "quote, expected",
    [
        ("kabarcık sıralaması komşu", 30.0),  # 3 kelime, tek geçiş: doğrulanır
        ("komşu elemanları karşılaştırır ve", 34.0),  # 4 kelime, tek geçiş: doğrulanır
        ("elemanları karşılaştırır", None),  # 2 kelime: hiçbir zaman doğrulanmaz
        ("sıralama", None),
    ],
)
def test_short_quote_rules(quote, expected):
    assert make_locator().find(quote) == expected


def repeated_locator():
    # "sıralama algoritmaları çok önemli" iki kez geçiyor
    return QuoteLocator(
        [
            Segment("sıralama algoritmaları çok önemli", 0.0, 3.0),
            Segment("bugün bunları göreceğiz", 3.0, 3.0),
            Segment("tekrar ediyorum sıralama algoritmaları çok önemli", 50.0, 4.0),
            Segment("sınavda mutlaka çıkar", 54.0, 3.0),
        ]
    )


def test_short_quote_occurring_twice_is_rejected():
    assert repeated_locator().find("sıralama algoritmaları çok önemli") is None  # 4 kelime, 2 geçiş
    assert repeated_locator().find("algoritmaları çok önemli") is None  # 3 kelime, 2 geçiş


def test_long_quote_occurring_twice_uses_first():
    # 5+ kelimede bugünkü davranış korunur: geçmesi yeterli, ilk geçiş kullanılır
    assert repeated_locator().find("sıralama algoritmaları çok önemli bugün") == 0.0
    assert repeated_locator().find("ediyorum sıralama algoritmaları çok önemli") == 50.0


def test_short_quote_occurring_twice_overlapping():
    # Örtüşen geçişler de sayılır: "bir bir bir" içinde "bir bir" iki kez geçer
    locator = QuoteLocator([Segment("bir bir bir bir", 0.0, 2.0)])
    assert locator.find("bir bir bir") is None


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


# Aynı videodan 806,96 sn'de başlayan bloğun başı (Soru 4'ün alıntısı)
REAL_EXCERPT_SORU4 = [
    Segment("yazmıştık değil mi? Ama fotosentezde", 806.959, 2.281),
    Segment("hemen besinin yanında oksijen", 809.24, 1.52),
    Segment("yazdığımızı da görmüştün ama burada", 810.76, 2.519),
    Segment("görmüyorsun. Demek ki kemosentezde", 813.279, 2.12),
    Segment("oksijen açığa çıkmıyormuş. Bunu da", 815.399, 1.761),
    Segment("anlamış oldun. Bu arada şu inorganik", 817.16, 2.44),
]


def test_real_example_soru4_four_word_unique_quote_is_verified():
    # Gerçek testte 4 kelime olduğu için reddedilmişti; transkriptte tek kez geçiyor
    quote = "[806] Kemosentezde oksijen açığa çıkmıyormuş."
    assert QuoteLocator(REAL_EXCERPT_SORU4).find(quote) == pytest.approx(813.279)
