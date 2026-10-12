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
    # "sıralama" yerine "sıra": kelime parçası eşleşmemeli (ortada olduğu için kırpılamaz)
    assert make_locator().find("merhaba arkadaşlar bugün sıra algoritmalarını konuşacağız") is None


def test_word_fragment_at_edge_is_trimmed_not_matched():
    # Kenardaki kelime parçası ("kadaşlar") birebir eşleşmez; kırpılarak atılır
    m = make_locator().match("kadaşlar bugün sıralama algoritmalarını konuşacağız")
    assert m.match == "trimmed"
    assert m.text == "bugün sıralama algoritmalarını konuşacağız"


def test_find_with_word_changed():
    # Kelimeler birebir aynı olmalı: tek kelime farkı doğrulamayı bozar
    assert make_locator().find("kabarcık sıralaması yakın elemanları karşılaştırır") is None


# --- Kenar kırpma -------------------------------------------------------------


def test_exact_match_is_not_trimmed():
    m = make_locator().match("İlk olarak, kabarcık sıralaması komşu elemanları karşılaştırır.")
    assert m.match == "exact"
    # Metin transkriptteki özgün yazımıyla döner
    assert m.text == "İlk olarak kabarcık sıralaması komşu elemanları karşılaştırır"
    assert m.start_seconds == 30.0


def test_exact_preferred_even_if_trimmed_also_matches():
    # Birebir eşleşen alıntı, kırpılmış hali de eşleşse "exact" kalır ve tamamı döner
    m = make_locator().match("bugün sıralama algoritmalarını konuşacağız")
    assert m.match == "exact" and m.text == "bugün sıralama algoritmalarını konuşacağız"


@pytest.mark.parametrize(
    "quote, expected_text",
    [
        # Başta dolgu sözcüğü
        ("Yani kabarcık sıralaması komşu elemanları karşılaştırır", "kabarcık sıralaması komşu elemanları karşılaştırır"),
        # Sonda dolgu sözcüğü
        ("kabarcık sıralaması komşu elemanları karşılaştırır tamam", "kabarcık sıralaması komşu elemanları karşılaştırır"),
        # Başta iki sözcük
        ("Yani şöyle kabarcık sıralaması komşu elemanları", "kabarcık sıralaması komşu elemanları"),
        # Başta ve sonda birer sözcük
        ("Evet ilk olarak kabarcık sıralaması tamam", "İlk olarak kabarcık sıralaması"),
    ],
)
def test_filler_word_at_edge_is_trimmed(quote, expected_text):
    m = make_locator().match(quote)
    assert m is not None and m.match == "trimmed"
    # Dönen metin transkriptteki özgün yazımdır
    assert m.text == expected_text


def test_trim_more_than_two_words_is_rejected():
    # Başta üç fazladan sözcük: en fazla 2 kırpılabilir
    assert make_locator().match("Yani şöyle ki kabarcık sıralaması komşu elemanları karşılaştırır") is None
    # Başta iki, sonda bir: toplam 3
    assert make_locator().match("Yani şöyle kabarcık sıralaması komşu elemanları karşılaştırır tamam") is None


def test_difference_in_middle_is_rejected():
    # Ortadaki fark kırpılarak giderilemez
    assert make_locator().match("İlk olarak kabarcık sıralaması yakın elemanları karşılaştırır ve") is None


def test_trimmed_part_must_pass_short_quote_rules():
    # Kırpılınca kalan 2 kelime: kural gereği doğrulanmaz
    assert make_locator().match("Yani komşu elemanları") is None
    # Kırpılınca kalan 4 kelime ama transkriptte iki kez geçiyor: doğrulanmaz
    assert repeated_locator().match("Yani sıralama algoritmaları çok önemli") is None


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


REAL_EXCERPT_SORU1 = [
    Segment("besin üretiyorsa biz buna fotosentetik", 214.319, 2.521),
    Segment("canlı demiştik. Kimyasal bir enerjiyi", 216.84, 2.36),
    Segment("kullanarak besin üretimini", 219.2, 1.239),
    Segment("gerçekleştiriyorsa o canlıya da", 220.439, 2.0),
    Segment("kemosentetik canlı adını vermiştik.", 222.439, 2.16),
]


def test_real_example_soru1_leading_filler_is_trimmed():
    # Model alıntının başına transkriptte olmayan "Yani" eklemişti
    quote = (
        "[219] Yani kimyasal bir enerjiyi kullanarak besin üretimini "
        "gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik."
    )
    m = QuoteLocator(REAL_EXCERPT_SORU1).match(quote)
    assert m.match == "trimmed"
    assert m.start_seconds == pytest.approx(216.84)
    assert m.text == (
        "Kimyasal bir enerjiyi kullanarak besin üretimini "
        "gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik."
    )


def test_real_example_soru4_four_word_unique_quote_is_verified():
    # Gerçek testte 4 kelime olduğu için reddedilmişti; transkriptte tek kez geçiyor
    quote = "[806] Kemosentezde oksijen açığa çıkmıyormuş."
    assert QuoteLocator(REAL_EXCERPT_SORU4).find(quote) == pytest.approx(813.279)
