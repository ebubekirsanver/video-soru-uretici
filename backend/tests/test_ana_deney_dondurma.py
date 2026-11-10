# Ana deney istemi ve ayarları 2026-11-10'da donduruldu (Pilot 2 kararı, Hafta-3 geri bildirimi). Bu test kırılırsa istemi değiştirmeden önce danışmanla konuş; değişiklik yeni bir sürümle yapılır, bu dosyalar değiştirilmez.
"""Ana deney istemlerinin ve ayarlarının dondurulduğunu denetler (git etiketi istem-v3-ana-deney).

Özetler satır sonları LF'ye çevrilerek hesaplanır: Windows'ta git dosyaları CRLF
ile çıkarabiliyor; istem dosyaları da Python'da satır sonları çevrilerek okunuyor.
Böylece özet, depodaki içerikle (c0c68cd) aynıdır ve bilgisayardan bilgisayara değişmez.
"""

import hashlib
import inspect

import pytest

from app.config import Settings
from app.schemas import QuestionsRequest
from app.services.chunking import CHUNKING_VERSION
from app.services.llm import OpenAIClient, get_llm
from app.services.prompts import PROMPT_DIR
from app.services.similarity import SIMILARITY_THRESHOLD
from app.services.topic_questions import PROMPT_FILES, PROMPT_VERSION_V3, generate_topic_questions
from app.services.topics import PROMPT_VERSION as TOPICS_PROMPT_VERSION

FROZEN_SHA256 = {
    "questions_v3_system.txt": "26d2b278157b624ded86e876770cdbe717f28e13f5e1edf94550563eb2b2f200",
    "questions_v3_user.txt": "fb3afd1e683db116fdd39b05eccb9568fa84871eab8ff593ee8f8c2c37dab2f0",
    "bloom_levels.json": "29c6df32b4541d8f3dd0ff59749e1646a539bc9e7f8598588962b6441adbdd95",
    "topics_v1_system.txt": "943ab874bdf9a8786991fff1283797c1438b7efa491fda4dba9a0991ca526660",
    "topics_v1_user.txt": "68969432197ff661ec6a4957b243fc36be24501c7785f9c418a0b0c4962f0f4d",
}


def normalized_sha256(name: str) -> str:
    data = (PROMPT_DIR / name).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("name", sorted(FROZEN_SHA256))
def test_frozen_prompt_files_unchanged(name):
    assert normalized_sha256(name) == FROZEN_SHA256[name]


def test_frozen_prompt_versions():
    assert PROMPT_FILES[PROMPT_VERSION_V3] == ("questions_v3_system.txt", "questions_v3_user.txt")
    assert TOPICS_PROMPT_VERSION == "topics-v1"


def test_default_prompt_version_is_v3():
    assert QuestionsRequest.model_fields["prompt_version"].default == "questions-v3"
    assert inspect.signature(generate_topic_questions).parameters["prompt_version"].default == "questions-v3"


def test_model_and_temperature():
    # Varsayılan değer kodda; .env ile değiştirilebildiği için ortamdan değil alanın kendisinden okunur
    assert Settings.model_fields["openai_model"].default == "gpt-4o-mini"
    assert inspect.signature(OpenAIClient.__init__).parameters["temperature"].default == 0.2
    assert get_llm().temperature == 0.2  # get_llm sıcaklığı değiştirmiyor


def test_retrieval_settings():
    assert QuestionsRequest.model_fields["k"].default == 5
    assert inspect.signature(generate_topic_questions).parameters["k"].default == 5
    assert CHUNKING_VERSION == "fixed-150-30"
    assert Settings.model_fields["embedding_model"].default == "BAAI/bge-m3"


def test_output_limit_and_similarity_threshold():
    assert Settings.model_fields["question_max_tokens"].default == 1000
    assert SIMILARITY_THRESHOLD == 0.80
