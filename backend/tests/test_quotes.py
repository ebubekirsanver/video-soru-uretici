import pytest

from app.services.chunking import TimeBlock
from app.services.quotes import QuoteLocator, normalize, turkish_lower


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
            TimeBlock(0.0, 30.0, "Merhaba arkadaşlar bugün sıralama algoritmalarını konuşacağız"),
            TimeBlock(30.0, 60.0, "İlk olarak kabarcık sıralaması komşu elemanları karşılaştırır"),
            TimeBlock(60.0, 90.0, "ve yanlış sıradaysa yer değiştirir bu işlem tekrarlanır"),
        ]
    )


def test_find_exact_quote_returns_block_start():
    assert make_locator().find("kabarcık sıralaması komşu elemanları karşılaştırır") == 30.0


def test_find_ignores_case_whitespace_and_punctuation():
    quote = "  İLK olarak, Kabarcık   sıralaması komşu elemanları karşılaştırır. "
    assert make_locator().find(quote) == 30.0


def test_find_quote_spanning_two_blocks_uses_first_block():
    assert make_locator().find("komşu elemanları karşılaştırır ve yanlış sıradaysa") == 30.0


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


def test_empty_blocks():
    assert QuoteLocator([]).find("bir iki üç dört beş") is None
