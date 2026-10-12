"""Kaynak alıntısını transkriptte arama ve alıntının video zamanını bulma.

LLM'in verdiği alıntıya ve zamana güvenilmez: alıntı kodda transkript içinde
aranır, zaman da alıntının başladığı segmentten hesaplanır.
"""

import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.services.text_clean import clean_text
from app.services.transcript import Segment

# Bu kadar ya da daha uzun alıntı, transkriptte geçiyorsa doğrulanır
MIN_QUOTE_WORDS = 5
# Daha kısa alıntılar (3-4 kelime) yalnızca transkriptte tam bir kez geçerse
# doğrulanır: tek geçiş alıntının tek bir yeri gösterdiğini garanti eder.
# Bundan kısası (ör. "ve bu") hiçbir zaman kanıt sayılmaz.
MIN_UNIQUE_QUOTE_WORDS = 3
# Birebir bulunamayan alıntının kenarlarından toplamda en fazla bu kadar kelime kırpılır
MAX_TRIM_WORDS = 2

# Denenecek (baştan, sondan) kırpma sayıları; önce hiç kırpmadan, sonra en az kırpmayla
_TRIMS = [
    (front, back)
    for total in range(MAX_TRIM_WORDS + 1)
    for front in range(total + 1)
    for back in [total - front]
]


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


@dataclass
class QuoteMatch:
    start_seconds: float  # alıntının başladığı segmentin başlangıcı
    text: str  # transkriptte bulunan metin, özgün yazımıyla
    match: Literal["exact", "trimmed"]


class QuoteLocator:
    """Transkript segmentleri üzerinde alıntı arar; bulunursa alıntının başladığı segmentin zamanını verir.

    Transkript tek bir kelime dizisine çevrilir, bu yüzden birden çok segmente
    (ya da bloğa) yayılan alıntılar da bulunur. Her kelime, transkriptteki
    özgün sözcüğünü ve segmentinin zamanını hatırlar.
    """

    def __init__(self, segments: list[Segment]):
        self._words: list[str] = []  # normalleştirilmiş kelimeler
        self._word_token: list[int] = []  # her kelimenin geldiği özgün sözcüğün sırası
        self._tokens: list[str] = []  # transkriptteki özgün sözcükler
        self._token_starts: list[float] = []  # her sözcüğün segment başlangıcı
        for segment in segments:
            for token in clean_text(segment.text).split():
                words = normalize(token).split()
                if not words:
                    continue  # yalnızca noktalamadan oluşan sözcük
                self._tokens.append(token)
                self._token_starts.append(segment.start)
                for word in words:
                    self._words.append(word)
                    self._word_token.append(len(self._tokens) - 1)

    def _occurrences(self, words: list[str]) -> list[int]:
        """Kelime dizisinin transkriptte başladığı tüm konumlar (örtüşenler dahil)."""
        n = len(words)
        return [i for i in range(len(self._words) - n + 1) if self._words[i : i + n] == words]

    def _accept(self, words: list[str]) -> int | None:
        """Kelime dizisi doğrulama kurallarını geçiyorsa başladığı konumu döndürür.

        - `MIN_QUOTE_WORDS` ve üzeri kelime: transkriptte geçmesi yeterli (ilk geçiş kullanılır).
        - `MIN_UNIQUE_QUOTE_WORDS` ile `MIN_QUOTE_WORDS` arası: transkriptte tam bir kez geçmeli.
        - Daha kısa ya da bulunamayan dizi: None.
        """
        if len(words) < MIN_UNIQUE_QUOTE_WORDS:
            return None
        found = self._occurrences(words)
        if not found:
            return None
        # Kısa alıntı birden çok kez geçiyorsa hangi yeri gösterdiği belirsizdir
        if len(words) < MIN_QUOTE_WORDS and len(found) != 1:
            return None
        return found[0]

    def match(self, quote: str) -> QuoteMatch | None:
        """Alıntıyı arar; birebir bulunamazsa kenarlarından en fazla `MAX_TRIM_WORDS` kelime kırpar.

        Model bazen alıntının başına ya da sonuna transkriptte olmayan bir dolgu
        sözcüğü ("Yani" gibi) ekliyor. Kırpılan parça da aynı kurallardan geçmek
        zorundadır; ortadaki kelime farkları hiçbir zaman kabul edilmez.
        """
        words = normalize(quote).split()
        for front, back in _TRIMS:
            part = words[front : len(words) - back]
            position = self._accept(part)
            if position is None:
                continue
            first_token = self._word_token[position]
            last_token = self._word_token[position + len(part) - 1]
            return QuoteMatch(
                start_seconds=self._token_starts[first_token],
                text=" ".join(self._tokens[first_token : last_token + 1]),
                match="trimmed" if front + back else "exact",
            )
        return None

    def find(self, quote: str) -> float | None:
        """Alıntı (gerekirse kenarları kırpılarak) bulunursa başladığı segmentin saniyesini döndürür."""
        found = self.match(quote)
        return found.start_seconds if found else None
