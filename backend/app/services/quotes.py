"""Kaynak alıntısını transkriptte arama ve alıntının video zamanını bulma.

LLM'in verdiği alıntıya ve zamana güvenilmez: alıntı kodda transkript içinde
aranır, zaman da alıntının başladığı segmentten hesaplanır.
"""

import bisect
import unicodedata

from app.services.text_clean import clean_text
from app.services.transcript import Segment

# Bu kadar ya da daha uzun alıntı, transkriptte geçiyorsa doğrulanır
MIN_QUOTE_WORDS = 5
# Daha kısa alıntılar (3-4 kelime) yalnızca transkriptte tam bir kez geçerse
# doğrulanır: tek geçiş alıntının tek bir yeri gösterdiğini garanti eder.
# Bundan kısası (ör. "ve bu") hiçbir zaman kanıt sayılmaz.
MIN_UNIQUE_QUOTE_WORDS = 3


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

        - `MIN_QUOTE_WORDS` ve üzeri kelime: transkriptte geçmesi yeterli (ilk geçiş kullanılır).
        - `MIN_UNIQUE_QUOTE_WORDS` ile `MIN_QUOTE_WORDS` arası: transkriptte tam bir kez geçmeli.
        - Daha kısa ya da bulunamayan alıntı: None.
        """
        normalized = normalize(quote)
        word_count = len(normalized.split())
        if word_count < MIN_UNIQUE_QUOTE_WORDS:
            return None
        needle = " " + normalized + " "
        index = self._text.find(needle)
        if index == -1:
            return None
        # Kısa alıntı ikinci kez geçiyorsa hangi yeri gösterdiği belirsizdir
        if word_count < MIN_QUOTE_WORDS and self._text.find(needle, index + 1) != -1:
            return None
        # index, eşleşmeden önceki boşluğu gösterir; bu da birleşik metindeki
        # (baştaki boşluk hariç) kelime başlangıcına denk gelir
        segment = bisect.bisect_right(self._offsets, index) - 1
        return self._starts[segment]
