"""Kaynak alıntısını transkriptte arama ve alıntının video zamanını bulma.

LLM'in verdiği alıntıya ve zamana güvenilmez: alıntı kodda transkript içinde
aranır, zaman da alıntının başladığı segmentten hesaplanır.
"""

import bisect
import unicodedata

from app.services.text_clean import clean_text
from app.services.transcript import Segment

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
    """Transkript segmentleri üzerinde alıntı arar; bulunursa alıntının başladığı segmentin zamanını verir.

    Segmentler tek bir metinde birleştirilir, bu yüzden birden çok segmente
    (ya da bloğa) yayılan alıntılar da bulunur.
    """

    def __init__(self, segments: list[Segment]):
        parts: list[str] = []
        self._offsets: list[int] = []  # her segmentin birleşik metindeki başlangıç konumu
        self._starts: list[float] = []
        position = 0
        for segment in segments:
            text = normalize(segment.text)
            if not text:
                continue
            self._offsets.append(position)
            self._starts.append(segment.start)
            parts.append(text)
            position += len(text) + 1  # segmentler arasına bir boşluk konur
        # Baştaki ve sondaki boşluk, yalnızca tam kelime eşleşmesi için
        self._text = " " + " ".join(parts) + " "

    def find(self, quote: str) -> float | None:
        """Alıntı transkriptte tam kelimelerle geçiyorsa başladığı segmentin saniyesini döndürür.

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
        segment = bisect.bisect_right(self._offsets, index) - 1
        return self._starts[segment]
