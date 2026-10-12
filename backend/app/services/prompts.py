"""İstem dosyalarını okuma ve transkripti isteme yerleştirme (özet ve soru servisleri ortak kullanır)."""

from functools import lru_cache
from pathlib import Path

from app.services.chunking import format_blocks, group_into_blocks
from app.services.transcript import Transcript

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
BLOCK_SECONDS = 30.0


@lru_cache
def load_prompt(name: str) -> str:
    """`app/prompts` altındaki istem dosyasını okur."""
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def transcript_context(transcript: Transcript, block_seconds: float = BLOCK_SECONDS) -> str:
    """Transkripti `[saniye] metin` satırlarından oluşan zaman damgalı bloklara çevirir."""
    text = format_blocks(group_into_blocks(transcript.segments, block_seconds))
    # Transkript içinde sınır etiketi geçerse veri bölümünün dışına taşmasın
    return text.replace("<transkript>", "").replace("</transkript>", "")


def fill_prompt(template: str, transcript_text: str, **values) -> str:
    """Şablondaki `{ad}` alanlarını doldurur; transkript en son yerleştirilir.

    str.format yerine replace kullanılır: transkriptteki { } karakterleri sorun
    çıkarmaz ve transkript içinde geçen `{ad}` metinleri yeniden işlenmez.
    """
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template.replace("{transcript}", transcript_text)
