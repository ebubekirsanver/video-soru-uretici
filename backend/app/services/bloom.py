"""Bloom düzeyleri ve konu–düzey eşlemesi (Aşama 8, istem questions-v3).

Düzeylerin tanımları, örnek bağlam ve örnek sorular tek bir yerden okunur:
`app/prompts/bloom_levels.json`. Bu metinler docs/bloom-istem-protokolu.md'deki
metinlerle birebir aynıdır (tests/test_bloom.py denetler). İsteme yalnızca
hedef düzeyin tanımı ve örneği konur, altı düzeyin hepsi değil (aşırı bilgi
yüklemek başarıyı düşürüyor: Scaria vd., 2024).

Konu–düzey eşlemesi (protokol): 6 konuya 6 düzey, video_id'den türetilen
sabit tohumla karıştırılarak eşlenir. Konular videodaki sırayla geldiği için
bu, aynı düzeyin hep videonun başına ya da sonuna düşmesini önler. Aynı video
her zaman aynı eşlemeyi verir; iki koşulda (full / rag) aynı eşleme kullanılır.
Eşleme istekte elle de verilebilir. Konu sayısı 6 değilse tohumlu eşleme
yapılmaz (kullanıcı kararı: düzeyler elle verilmeli).
"""

import hashlib
import json
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from app.services.prompts import PROMPT_DIR

LEVELS_FILE = "bloom_levels.json"
LEVEL_COUNT = 6

# Yenilenmiş Bloom taksonomisinin altı düzeyi (protokoldeki sırayla)
BloomLevelName = Literal["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]


@dataclass(frozen=True)
class BloomLevel:
    name: str
    key: str
    definition: str
    example: tuple[str, ...]  # örnek sorunun satırları (soru, seçenekler, doğru cevap, gerekçe)


@lru_cache
def _data() -> dict:
    return json.loads((PROMPT_DIR / LEVELS_FILE).read_text(encoding="utf-8"))


def levels() -> list[BloomLevel]:
    return [
        BloomLevel(lv["name"], lv["key"], lv["definition"], tuple(lv["example"]))
        for lv in _data()["levels"]
    ]


def level_names() -> list[str]:
    return [lv.name for lv in levels()]


def get_level(name: str) -> BloomLevel:
    for lv in levels():
        if lv.name == name:
            return lv
    raise ValueError(f"Bilinmeyen Bloom düzeyi: {name!r}")


def example_text(level: BloomLevel) -> str:
    """İsteme konan örnek: ortak örnek bağlam ve o düzeyin örnek sorusu."""
    return "Örnek bağlam: " + _data()["example_context"] + "\n" + "\n".join(level.example)


def seeded_mapping(video_id: str, topic_count: int) -> list[str]:
    """Konuların sırasıyla eşlenecek düzey adları (video_id'den türetilen sabit tohumla karıştırılmış).

    Yalnızca tam 6 konu için tanımlıdır; değilse ValueError.
    """
    if topic_count != LEVEL_COUNT:
        raise ValueError(
            f"Tohumlu Bloom eşlemesi yalnızca {LEVEL_COUNT} konu için yapılır ({topic_count} konu var); "
            "bloom_levels istekte elle verilmeli."
        )
    # Python'un hash() fonksiyonu her çalıştırmada değiştiği için sha256 kullanılır
    seed = int.from_bytes(hashlib.sha256(video_id.encode("utf-8")).digest()[:8], "big")
    order = level_names()
    random.Random(seed).shuffle(order)
    return order
