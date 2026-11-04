"""Aşama 8: Bloom yönlendirmeli istem (questions-v3). Sahte LLM ve sahte gömme; gerçek model yok."""

import hashlib
import json
import math
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.schemas import QuestionOut
from app.services import runs
from app.services.bloom import example_text, get_level, level_names, levels, seeded_mapping
from app.services.embeddings import get_embedder_provider
from app.services.llm import get_llm
from app.services.retrieval import TranscriptIndex, get_index_provider
from app.services.topic_questions import build_topic_user_prompt
from app.services.transcript import Segment, Transcript

VID = "dQw4w9WgXcQ"
PROTOCOL = Path(__file__).resolve().parents[2] / "docs" / "bloom-istem-protokolu.md"
NAMES = ["Hatırlama", "Anlama", "Uygulama", "Çözümleme", "Değerlendirme", "Yaratma"]

# 6 konu, her biri tek uzun segment (>150 kelime): her konu kendi parçası olur
TOPICS = [
    ("fotosentez", "fotosentezde bitkiler klorofil sayesinde ışık enerjisini kullanır", 0.0),
    ("hidrotermal bacalar", "hidrotermal bacalar okyanus tabanında yer alan sıcak su kaynaklarıdır", 100.0),
    ("prokaryot hücre", "kemosentetik canlıların tamamı prokaryot hücre yapısına sahiptir", 200.0),
    ("mitoz bölünme", "mitoz bölünmede kromozom sayısı yavru hücrelerde korunur", 300.0),
    ("enzimler", "enzimler tepkimeleri hızlandıran protein yapılı moleküllerdir", 400.0),
    ("solunum", "oksijenli solunumda glikoz parçalanarak enerji elde edilir", 500.0),
]
TITLES = [t for t, _, _ in TOPICS]


def make_transcript():
    return Transcript(VID, "tr", True, [Segment(f"{s} " + " ".join([t] * 75), start, 90.0) for t, s, start in TOPICS])


class FakeEmbedder:
    model = "fake-embedder"

    def embed(self, texts):
        out = []
        for text in texts:
            v = [0.0] * 64
            for w in text.lower().split():
                v[int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % 64] += 1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


class BloomLLM:
    """Konu ve hedef düzeye göre soru döndürür; istemleri kaydeder. Konu çıkarma istemini de tanır."""

    model = "fake-model"

    def __init__(self, extracted=TITLES):
        self.extracted = extracted
        self.calls = []

    def complete(self, system, user, json_mode=False, max_tokens=None):
        if "konu çıkaran" in system:  # topics_v1_system.txt
            return json.dumps({"topics": [{"title": t, "description": f"{t} anlatılıyor."} for t in self.extracted]},
                              ensure_ascii=False)
        self.calls.append((system, user))
        topic = re.search(r"^Konu: (.+)$", user, re.MULTILINE).group(1).split(": ")[0]
        level = re.search(r"^Hedef Bloom düzeyi: (.+)$", user, re.MULTILINE).group(1)
        sentence = next(s for t, s, _ in TOPICS if t == topic)
        return json.dumps({"questions": [{
            "reasoning": f"{level} düzeyinde çünkü {topic} gerekçesi.",
            "question": f"{topic} hakkında {level} sorusu?",
            "options": ["Doğru", "Yanlış bir", "Yanlış iki", "Yanlış üç"],
            "correct_index": 0, "explanation": "açıklama", "source_quote": sentence,
        }]}, ensure_ascii=False)


client = TestClient(app)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    runs_dir = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(runs_dir))
    get_settings.cache_clear()
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: make_transcript())
    index = TranscriptIndex(FakeEmbedder(), path=tmp_path / "chroma")

    def use(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        app.dependency_overrides[get_index_provider] = lambda: (lambda: index)
        app.dependency_overrides[get_embedder_provider] = lambda: (lambda: index.embedder)
        return llm

    use.runs_dir = runs_dir
    yield use
    app.dependency_overrides.clear()


def last_record(runs_dir):
    return runs.load_run(sorted(runs_dir.glob("*.json"))[-1])


# --- Tanımlar tek kaynaktan ve protokolle birebir aynı ------------------------------


def test_levels_json_matches_protocol_document():
    md = PROTOCOL.read_text(encoding="utf-8")
    assert level_names() == NAMES
    for lv in levels():
        section = md.split(f". {lv.name} (", 1)[1].split("\n### ", 1)[0]
        assert f"- **Tanım:** {lv.definition}\n" in section
        assert len(lv.example) == 7
        for line in lv.example:
            assert f"  - {line}\n" in section
    context = json.loads((Path(__file__).resolve().parents[1] / "app" / "prompts" / "bloom_levels.json")
                         .read_text(encoding="utf-8"))["example_context"]
    assert f"\n{context}\n" in md


# --- İstem -----------------------------------------------------------------------------


def test_prompt_contains_only_target_level():
    user = build_topic_user_prompt("mitoz bölünme", "[300] mitoz", "Uygulama")
    target = get_level("Uygulama")
    assert "Hedef Bloom düzeyi: Uygulama" in user
    assert target.definition in user
    assert all(line in user for line in target.example)
    assert example_text(target) in user
    for other in levels():
        if other.name != "Uygulama":
            assert other.definition not in user
            assert other.example[0] not in user  # başka düzeyin örnek sorusu yok


def test_both_conditions_same_system_prompt_and_same_user_prompt_except_context(setup):
    full_llm = setup(BloomLLM())
    assert client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": TITLES}).status_code == 200
    rag_llm = setup(BloomLLM())
    assert client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": TITLES}).status_code == 200
    assert {s for s, _ in full_llm.calls} == {s for s, _ in rag_llm.calls}
    assert len({s for s, _ in full_llm.calls}) == 1
    strip = lambda u: u.split("<bağlam>\n")[0]  # noqa: E731  (bağlamdan önceki kısım)
    assert [strip(u) for _, u in full_llm.calls] == [strip(u) for _, u in rag_llm.calls]


# --- Eşleme ---------------------------------------------------------------------------


def test_seeded_mapping_is_stable_permutation():
    first = seeded_mapping(VID, 6)
    assert first == seeded_mapping(VID, 6)  # aynı video, aynı eşleme
    assert sorted(first) == sorted(NAMES)  # her düzey bir kez
    others = {tuple(seeded_mapping(f"video{i:07d}", 6)) for i in range(10)}
    assert len(others | {tuple(first)}) > 1  # farklı videolar farklı eşleme verebilir


def test_seeded_mapping_requires_six_topics():
    with pytest.raises(ValueError):
        seeded_mapping(VID, 5)


def test_seeded_mapping_used_and_same_in_both_conditions(setup):
    setup(BloomLLM())
    r_full = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": TITLES})
    full_record = last_record(setup.runs_dir)
    r_rag = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": TITLES})
    rag_record = last_record(setup.runs_dir)
    expected = seeded_mapping(VID, 6)
    for r, record in ((r_full, full_record), (r_rag, rag_record)):
        assert [q["bloom_level"] for q in r.json()["questions"]] == expected
        tg = record["topic_generation"]
        assert tg["bloom_mapping_source"] == "seeded"
        assert tg["bloom_mapping"] == [{"topic": t, "bloom_level": lv} for t, lv in zip(TITLES, expected)]
        assert [t["bloom_level"] for t in tg["per_topic"]] == expected


def test_manual_mapping_used(setup):
    llm = setup(BloomLLM())
    levels_given = ["Yaratma", "Hatırlama", "Hatırlama", "Anlama", "Uygulama", "Çözümleme"]
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": TITLES,
                                            "bloom_levels": levels_given})
    assert r.status_code == 200
    assert [q["bloom_level"] for q in r.json()["questions"]] == levels_given
    assert [re.search(r"^Hedef Bloom düzeyi: (.+)$", u, re.MULTILINE).group(1) for _, u in llm.calls] == levels_given
    assert last_record(setup.runs_dir)["topic_generation"]["bloom_mapping_source"] == "request"


def test_manual_mapping_allows_other_topic_counts(setup):
    setup(BloomLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "rag", "topics": TITLES[:2],
                                            "bloom_levels": ["Anlama", "Değerlendirme"]})
    assert r.status_code == 200 and [q["bloom_level"] for q in r.json()["questions"]] == ["Anlama", "Değerlendirme"]


@pytest.mark.parametrize(
    "extra",
    [
        {"context_mode": "full", "topics": TITLES, "bloom_levels": NAMES[:5]},  # uzunluk uyuşmazlığı
        {"context_mode": "full", "bloom_levels": NAMES},  # topics olmadan
        {"bloom_levels": NAMES},  # context_mode olmadan
        {"context_mode": "full", "topics": TITLES, "bloom_levels": ["Hatırlama"] * 5 + ["Sentez"]},  # geçersiz ad
        {"context_mode": "full", "topics": TITLES[:5]},  # 6 dışı konu, düzey verilmemiş
        {"context_mode": "full", "count": 5},  # konu çıkarma 5 konu, düzey verilemez
    ],
)
def test_invalid_bloom_requests_422(setup, extra):
    llm = setup(BloomLLM())
    assert client.post("/api/questions", json={"url": VID, **extra}).status_code == 422
    assert llm.calls == []


def test_extraction_shortfall_422_with_record(setup):
    # Konu çıkarma adımı 6 yerine 5 konu döndürürse tohumlu eşleme yapılamaz
    llm = setup(BloomLLM(extracted=TITLES[:5]))
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "count": 6})
    assert r.status_code == 422 and "6 konu" in r.json()["detail"]
    record = last_record(setup.runs_dir)
    assert record["outcome"] == "error" and record["error"]["kind"] == "bloom_mapping"
    assert llm.calls == []  # soru çağrısı yapılmadı


# --- reasoning yalnızca kayıtta -------------------------------------------------------


def test_reasoning_in_record_not_in_response(setup):
    setup(BloomLLM())
    r = client.post("/api/questions", json={"url": VID, "context_mode": "full", "topics": TITLES})
    assert "reasoning" not in r.text
    body = r.json()
    assert body["prompt_version"] == "questions-v3"
    record = last_record(setup.runs_dir)
    reasons = record["topic_generation"]["questions_reasoning"]
    assert len(reasons) == 6
    assert reasons[0]["reasoning"].endswith("gerekçesi.") and reasons[0]["topic"] == TITLES[0]
    assert record["topic_generation"]["prompt_version"] == "questions-v3"
    assert record["response"] == body


def test_bloom_level_field_says_target_not_claim():
    description = QuestionOut.model_fields["bloom_level"].description
    assert "Hedef" in description and "iddia edilmez" in description


# --- v1 değişmedi ---------------------------------------------------------------------


def test_v1_unchanged(setup):
    class V1LLM:
        model = "fake-model"

        def __init__(self):
            self.systems = []

        def complete(self, system, user, json_mode=False, max_tokens=None):
            self.systems.append(system)
            return json.dumps({"questions": [{"question": "Mitoz nedir?", "options": ["a", "b", "c", "d"],
                                              "correct_index": 0, "explanation": "x",
                                              "source_quote": TOPICS[3][1]}]}, ensure_ascii=False)

    llm = setup(V1LLM())
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200
    assert r.json()["prompt_version"] == "questions-v1"
    assert all("bloom_level" not in q and "topic" not in q for q in r.json()["questions"])
    assert "Bloom" not in llm.systems[0]
    assert last_record(setup.runs_dir)["topic_generation"] is None
