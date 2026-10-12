"""Kaynak alıntısını transkriptte arama ve alıntının video zamanını bulma.

LLM'in verdiği alıntıya ve zamana güvenilmez: alıntı kodda transkript içinde
aranır, zaman da alıntının bulunduğu bloktan hesaplanır.
"""

import bisect
import unicodedata

from app.services.chunking import TimeBlock
from app.services.text_clean import clean_text

# Bundan kısa alıntılar (ör. "ve bu") her transkriptte geçer, kanıt sayılmaz
MIN_QUOTE_WORDS = 5


def turkish_lower(text: str) -> str:
    """Türkçeye uygun küçük harf: I → ı, İ → i (str.lower() İ'yi bozar)."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def normalize(text: str) -> str:
    """Karşılaştırma için metni sadeleştirir.

    Köşeli parantez etiketleri silinir; büyük/küçük harf, noktalama ve boşluk
    farkları yok sayılır. Kelimeler ise aynen kalır.
    """
    text = unicodedata.normalize("NFC", clean_text(text))
    text = turkish_lower(text)
    # Noktalama işaretleri boşluğa çevrilir ("bir,iki" → "bir iki")
    text = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text)
    return " ".join(text.split())


class QuoteLocator:
    """Bloklar üzerinde alıntı arar; bulunursa alıntının başladığı bloğun zamanını verir."""

    def __init__(self, blocks: list[TimeBlock]):
        parts: list[str] = []
        self._offsets: list[int] = []  # her bloğun birleşik metindeki başlangıç konumu
        self._starts: list[float] = []
        position = 0
        for block in blocks:
            text = normalize(block.text)
            if not text:
                continue
            self._offsets.append(position)
            self._starts.append(block.start)
            parts.append(text)
            position += len(text) + 1  # bloklar arasına bir boşluk konur
        # Baştaki ve sondaki boşluk, yalnızca tam kelime eşleşmesi için
        self._text = " " + " ".join(parts) + " "

    def find(self, quote: str) -> float | None:
        """Alıntı transkriptte tam kelimelerle geçiyorsa başladığı bloğun saniyesini döndürür.

        Alıntı bulunamazsa ya da `MIN_QUOTE_WORDS` kelimeden kısaysa None döner.
        """
        normalized = normalize(quote)
        if len(normalized.split()) < MIN_QUOTE_WORDS:
            return None
        index = self._text.find(" " + normalized + " ")
        if index == -1:
            return None
        # index, eşleşmeden önceki boşluğu gösterir; bu da birleşik metindeki
        # (baştaki boşluk hariç) kelime başlangıcına denk gelir
        block = bisect.bisect_right(self._offsets, index) - 1
        return self._starts[block]
