"""Videodan konu çıkarma (istem topics-v1).

Deneyde (AS1) iki koşula (full / rag) aynı konu listesi verilir. Konular
özet servisinden değil bu ayrı adımdan gelir: istem, birbirinden açıkça farklı
ve videonun farklı bölümlerini kapsayan tam `count` konu ister. Gerekçe: 7b
koşul denemesinde (docs/bulgular/asama-7b-kosul-denemesi-1.md) özetten gelen
konular birbirine yakındı ve sorular tekrar etti; özet servisi de 3-8 arası
konu veriyor, deneyde her videoda 6 konu gerekiyor.

Konuların farklılığı kodla ölçülmez: yalnızca istemle ve başlık eşitliğiyle
(normalleştirilmiş başlığı aynı olan konulardan ilki tutulur) sağlanır.

Soru üretimine ve erişime verilen konu metni "Başlık: açıklama" biçimindedir
(`Topic.text`). Böylece questions-v2 isteminde ({topic}) ve RAG erişim
sorgusunda aynı metin kullanılır; questions-v2 istem dosyaları değişmez.
"""

import json
from dataclasses import dataclass, field

from app.services.llm import LLMClient, LLMError
from app.services.prompts import BLOCK_SECONDS, fill_prompt, load_prompt, transcript_context
from app.services.quotes import normalize
from app.services.transcript import Transcript

# İstem değişirse yeni dosyalar (v2) açılır
PROMPT_VERSION = "topics-v1"
SYSTEM_PROMPT_FILE = "topics_v1_system.txt"
USER_PROMPT_FILE = "topics_v1_user.txt"
DEFAULT_COUNT = 6


@dataclass
class Topic:
    title: str
    description: str

    @property
    def text(self) -> str:
        """Soru üretimine (questions-v2 {topic}) ve erişim sorgusuna verilen metin."""
        return f"{self.title}: {self.description}"


@dataclass
class TopicExtraction:
    topics: list[Topic]
    requested: int
    # Atılan konular: empty (boş başlık ya da açıklama), duplicate (aynı başlık),
    # extra (istenenden fazlası)
    dropped: dict = field(default_factory=lambda: {"empty": 0, "duplicate": 0, "extra": 0})

    @property
    def shortfall(self) -> int:
        """İstenen sayıdan eksik kalan konu sayısı (0: eksik yok)."""
        return max(self.requested - len(self.topics), 0)

    def as_record(self) -> dict:
        """Çalıştırma kaydına yazılacak özet (eksiklik dahil)."""
        return {
            "prompt_version": PROMPT_VERSION,
            "requested_count": self.requested,
            "returned_count": len(self.topics),
            "shortfall": self.shortfall,
            "dropped": dict(self.dropped),
            "topics": [{"title": t.title, "description": t.description} for t in self.topics],
        }


def build_user_prompt(transcript: Transcript, count: int, block_seconds: float = BLOCK_SECONDS) -> str:
    """Tam transkripti (~30 sn'lik `[saniye] metin` blokları) ve konu sayısını isteme yerleştirir."""
    return fill_prompt(load_prompt(USER_PROMPT_FILE), transcript_context(transcript, block_seconds), count=count)


def parse_topics(raw: str, count: int) -> TopicExtraction:
    """Model yanıtını doğrular.

    Yanıtın tamamı JSON değilse ya da `topics` listesi yoksa LLMError
    fırlatılır. Boş başlıklı ya da açıklamalı konu atılır; normalleştirilmiş
    başlığı aynı olan konulardan ilki tutulur; fazlası gelirse ilk `count`
    alınır. Geçerli konu `count`'tan azsa hata verilmez, eldekiler döner.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMError("Konu yanıtı geçerli JSON değil.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("topics"), list):
        raise LLMError("Konu yanıtında 'topics' listesi yok.")

    result = TopicExtraction(topics=[], requested=count)
    seen: set[str] = set()
    for item in data["topics"]:
        title = item.get("title") if isinstance(item, dict) else None
        description = item.get("description") if isinstance(item, dict) else None
        title = title.strip() if isinstance(title, str) else ""
        description = description.strip() if isinstance(description, str) else ""
        if not title or not description:
            result.dropped["empty"] += 1
            continue
        key = normalize(title)
        if key in seen:
            result.dropped["duplicate"] += 1
            continue
        seen.add(key)
        result.topics.append(Topic(title, description))
    if len(result.topics) > count:
        result.dropped["extra"] = len(result.topics) - count
        result.topics = result.topics[:count]
    return result


def extract_topics(transcript: Transcript, llm: LLMClient, count: int = DEFAULT_COUNT) -> TopicExtraction:
    """Temiz transkriptin tamamından en çok `count` konu çıkarır."""
    if not transcript.segments:
        raise ValueError("Konu çıkarılacak transkript boş.")
    raw = llm.complete(
        system=load_prompt(SYSTEM_PROMPT_FILE),
        user=build_user_prompt(transcript, count),
        json_mode=True,
    )
    return parse_topics(raw, count)
