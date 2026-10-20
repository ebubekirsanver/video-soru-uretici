"""Aşama 9 (b): kodla kontrol edilen soru yazım kuralları (writing-rules-v1).

Model çağrısı yoktur; uç nokta testlerinde sahte LLM kullanılır.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import runs
from app.services.llm import get_llm
from app.services.questions import generate_questions
from app.services.transcript import Segment, Transcript
from app.services.writing_check import RULES_VERSION, check_question

VID = "dQw4w9WgXcQ"
STEM = "Kemosentez yapan canlılar hangi hücre yapısına sahiptir?"
PLAIN = ["Prokaryot", "Ökaryot", "Bitkisel", "Hayvansal"]


def rule_ids(question, options, correct_index=0):
    return [f.rule_id for f in check_question(question, options, correct_index)]


def test_plain_question_has_no_flags():
    assert check_question(STEM, PLAIN, 0) == []


# --- 3 ve 9: hiçbiri / hepsi ------------------------------------------------------


@pytest.mark.parametrize("option", ["Hiçbiri", "Yukarıdakilerin hiçbiri", "Hiçbiri doğru değil"])
def test_none_of_the_above(option):
    assert rule_ids(STEM, PLAIN[:3] + [option]) == [3]


@pytest.mark.parametrize("option", ["Hepsi", "Yukarıdakilerin tümü", "Hepsi doğrudur"])
def test_all_of_the_above(option):
    # "Tümü" tek başına 9. maddedir; 11. madde (kesin ifade) olarak ayrıca sayılmaz
    assert rule_ids(STEM, PLAIN[:3] + [option]) == [9]


def test_none_all_words_inside_normal_option_not_flagged():
    options = ["Hiçbir canlı ışık kullanmaz", "Bitkiler", "Hayvanlar", "Mantarlar"]
    assert 3 not in rule_ids(STEM, options) and 9 not in rule_ids(STEM, options)


# --- 4: en uzun seçenek doğru ------------------------------------------------------


LONG = ["Kimyasal tepkimelerden açığa çıkan enerjiyle", "Işıkla", "Isıyla", "Sesle"]


def test_longest_option_correct():
    flags = check_question("Kemosentezde hangi kaynak kullanılır?", LONG, 0)
    assert [f.rule_id for f in flags] == [4]
    assert "karakter" in flags[0].detail


def test_longest_option_not_correct():
    assert 4 not in rule_ids("Kemosentezde hangi kaynak kullanılır?", LONG, 1)


def test_longest_option_only_slightly_longer_not_flagged():
    # 12 ve 11 karakter: oran 1,3'ün altında
    assert 4 not in rule_ids("Hangisi?", ["Fotosentezle", "Solunumuyla", "Ab", "Cd"], 0)


def test_longest_rule_uses_shuffled_correct_index():
    """Kontrol karıştırmadan sonraki son soru üzerinde: doğru seçenek yeni yerinde aranır."""

    class FakeLLM:
        model = "fake"

        def complete(self, system, user, json_mode=False):
            return json.dumps(
                {
                    "questions": [
                        {
                            "question": "Kemosentezde hangi kaynak kullanılmaktadır?",
                            "options": LONG,
                            "correct_index": 0,
                            "explanation": "açıklama",
                            "source_quote": "kabarcık sıralaması komşu elemanları karşılaştırır",
                        }
                    ]
                },
                ensure_ascii=False,
            )

    t = Transcript(VID, "tr", True, [Segment("kabarcık sıralaması komşu elemanları karşılaştırır", 0.0, 5.0)])
    (q,) = generate_questions(t, t, FakeLLM(), 1)
    assert q.correct_index != 0  # karıştırma doğru seçeneği yerinden oynattı
    assert q.options[q.correct_index] == LONG[0]
    assert [f.rule_id for f in check_question(q.question, q.options, q.correct_index)] == [4]
    # Karıştırmadan önceki sıra (0) artık doğru seçeneği göstermiyor
    assert 4 not in [f.rule_id for f in check_question(q.question, q.options, 0)]


# --- 6: doğru-yanlış --------------------------------------------------------------


def test_true_false_options():
    assert rule_ids("Kemosentezde oksijen açığa çıkar.", ["Doğru", "Yanlış", "Kısmen", "Bilinmiyor"]) == [6]


def test_single_true_word_not_true_false():
    assert 6 not in rule_ids(STEM, ["Doğru", "Prokaryot", "Ökaryot", "Bitkisel"])


# --- 10: boşluk doldurma ------------------------------------------------------------


@pytest.mark.parametrize("stem", ["Kemosentez yapan canlılara ____ denir.", "Kemosentez yapan canlılara ...... denir."])
def test_fill_in_blank(stem):
    assert rule_ids(stem, PLAIN) == [10]


def test_trailing_ellipsis_not_blank():
    assert 10 not in rule_ids("Kemosentez yapan canlılar...?", PLAIN)


# --- 11: kesin ifadeler -----------------------------------------------------------


def test_absolute_terms():
    # Doğru seçenek 1: en uzun seçenek kuralı (4) karışmasın
    flags = check_question(STEM, ["Her zaman prokaryot", "Ökaryot", "Asla bitkisel", "Hayvansal"], 1)
    assert [f.rule_id for f in flags] == [11]
    assert "her zaman" in flags[0].detail and "asla" in flags[0].detail


def test_absolute_term_needs_whole_word():
    # "hiçbir" kesin ifadedir, "hiçbirinde" ek aldığı için bu sürümde sayılmaz
    assert 11 not in rule_ids(STEM, ["Hiçbirinde", "Ökaryot", "Bitkisel", "Hayvansal"])


# --- 12: kelime tekrarı -------------------------------------------------------------


def test_word_repeat_only_in_correct_option():
    stem = "Kemosentez yapan canlılara ne ad verilir?"
    options = ["Kemosentetik canlılar", "Fotosentetik bitkiler", "Heterotrof hayvanlar", "Ayrıştırıcılar"]
    flags = check_question(stem, options, 0)
    assert [f.rule_id for f in flags] == [12]
    assert "kemosentez" in flags[0].detail


def test_word_repeat_also_in_distractor_not_flagged():
    stem = "Kemosentez yapan canlılara ne ad verilir?"
    options = ["Kemosentetik canlılar", "Kemosentetik olmayan bitkiler", "Heterotrof hayvanlar", "Ayrıştırıcılar"]
    # "kemos" ön eki bir çeldiricide de var; "canlı" yalnızca doğru seçenekte
    flags = check_question(stem, options, 0)
    assert [f.rule_id for f in flags] == [12]
    assert "kemosentez" not in flags[0].detail and "canlılara" in flags[0].detail
    options[2] = "Canlılar dışındakiler"
    assert 12 not in rule_ids(stem, options)


# --- 14: birleşik seçenekler --------------------------------------------------------


@pytest.mark.parametrize("option", ["I ve II", "A ve B", "Yalnız I", "I, II ve III"])
def test_k_type(option):
    assert rule_ids(STEM, PLAIN[:3] + [option]) == [14]


def test_k_type_not_triggered_by_words():
    assert 14 not in rule_ids(STEM, ["DNA ile RNA", "Vitamin ve mineral", "Ökaryot", "Bitkisel"])


# --- 16: sayısal sıra -------------------------------------------------------------


def test_lost_sequence():
    assert rule_ids("Cumhuriyet hangi yıl ilan edildi?", ["1923", "1920", "1938", "1919"]) == [16]


def test_sorted_numbers_not_flagged():
    assert 16 not in rule_ids("Cumhuriyet hangi yıl ilan edildi?", ["1919", "1920", "1923", "1938"])
    assert 16 not in rule_ids("Kaç derece?", ["400 °C", "300 °C", "200 °C", "100 °C"])


def test_numbers_with_same_unit_flagged_mixed_text_not():
    assert rule_ids("Kaç derece?", ["300 °C", "100 °C", "400 °C", "200 °C"]) == [16]
    assert 16 not in rule_ids("Kaç derece?", ["300 °C", "100 °C", "400 derece", "200 °C"])


# --- 17: belirsiz ifadeler ----------------------------------------------------------


def test_vague_terms():
    assert rule_ids(STEM, ["Genellikle prokaryot", "Ökaryot", "Bazen bitkisel", "Hayvansal"], 1) == [17]


def test_vague_term_needs_whole_word():
    assert 17 not in rule_ids(STEM, ["Bazı canlılar", "Ökaryot", "Bitkisel", "Hayvansal"])


# --- 19: olumsuz soru kökü ----------------------------------------------------------


@pytest.mark.parametrize(
    "stem",
    [
        "Kemosentezde hangi madde açığa çıkmaz?",
        "Aşağıdakilerden hangisi kemosentetik canlı değildir?",
        "Işık kullanmayan canlılar hangisidir?",
    ],
)
def test_negative_stem(stem):
    assert rule_ids(stem, PLAIN) == [19]


def test_positive_stem_not_negative():
    assert 19 not in rule_ids("Kemosentezde hangi madde açığa çıkar?", PLAIN)


# --- Uç nokta ve kayıt ----------------------------------------------------------------


client = TestClient(app)

QUESTIONS_JSON = json.dumps(
    {
        "questions": [
            {
                "question": "Kemosentezde hangi madde açığa çıkmaz?",
                "options": ["Oksijen", "Su", "Enerji", "Hiçbiri"],
                "correct_index": 0,
                "explanation": "açıklama",
                "source_quote": "kemosentezde oksijen açığa çıkmıyormuş demek ki",
            },
            {
                "question": "Kemosentez yapan canlıların hücre yapısı nedir?",
                "options": ["Prokaryot", "Ökaryot", "Bitkisel", "Hayvansal"],
                "correct_index": 0,
                "explanation": "açıklama",
                "source_quote": "bu canlıların tamamı prokaryot hücre yapısına sahip",
            },
        ]
    },
    ensure_ascii=False,
)


class FakeLLM:
    model = "fake-model"

    def complete(self, system, user, json_mode=False):
        return QUESTIONS_JSON


@pytest.fixture
def setup(monkeypatch, tmp_path):
    d = tmp_path / "runs"
    monkeypatch.setenv("SAVE_RUNS", "true")
    monkeypatch.setenv("RUNS_DIR", str(d))
    get_settings.cache_clear()
    t = Transcript(
        VID,
        "tr",
        True,
        [
            Segment("demek ki kemosentezde oksijen açığa çıkmıyormuş demek ki", 0.0, 5.0),
            Segment("bu canlıların tamamı prokaryot hücre yapısına sahip", 5.0, 5.0),
        ],
    )
    monkeypatch.setattr("app.routers.fetch_transcript", lambda video_id, languages: t)
    app.dependency_overrides[get_llm] = lambda: FakeLLM()
    yield d
    app.dependency_overrides.clear()


def test_flags_only_in_record_not_in_response(setup):
    r = client.post("/api/questions", json={"url": VID})
    assert r.status_code == 200
    body = r.json()
    for q in body["questions"]:
        assert set(q) == {
            "question", "options", "correct_index", "explanation",
            "source_quote", "source_start_seconds", "verified", "quote_match",
        }
    assert "writing" not in r.text and "rule_id" not in r.text

    (path,) = setup.glob("*.json")
    record = runs.load_run(path)
    assert record["record_version"] == 5
    assert record["response"] == body  # yanıt kayıtta değiştirilmeden durur
    wc = record["writing_check"]
    assert wc["rules_version"] == RULES_VERSION == "writing-rules-v1"
    first, second = wc["results"]
    assert first["index"] == 1 and first["question"] == "Kemosentezde hangi madde açığa çıkmaz?"
    assert [f["rule_id"] for f in first["flags"]] == [3, 19]
    assert first["flags"][0]["rule_name"] == "None of the above"
    assert all(set(f) == {"rule_id", "rule_name", "detail"} for f in first["flags"])
    assert second["flags"] == []
    # İşaretlenen soru atılmadı
    assert body["returned_count"] == 2
    assert "writing_check_ms" in record["metrics"]["stages"]


def test_summary_record_has_no_writing_check(setup):
    summary = json.dumps({"summary": "Özet.", "topics": []}, ensure_ascii=False)

    class SummaryLLM:
        model = "fake-model"

        def complete(self, system, user, json_mode=False):
            return summary

    app.dependency_overrides[get_llm] = lambda: SummaryLLM()
    assert client.post("/api/summary", json={"url": VID}).status_code == 200
    (path,) = setup.glob("*.json")
    assert "writing_check" not in json.loads(path.read_text(encoding="utf-8"))
    assert runs.load_run(path)["writing_check"] is None


def test_load_run_v4_record_without_writing_check(tmp_path):
    path = tmp_path / "eski.json"
    path.write_text(
        json.dumps(
            {
                "record_version": 4,
                "saved_at": "2026-10-20T10:00:00+03:00",
                "endpoint": "/api/questions",
                "outcome": "ok",
                "request": {"url": VID},
                "response": {"video_id": VID},
                "metrics": {"stages": {"total_ms": 1.0}, "llm_calls": []},
            }
        ),
        encoding="utf-8",
    )
    record = runs.load_run(path)
    assert record["record_version"] == 4 and record["writing_check"] is None
    assert record["metrics"]["stages"] == {"total_ms": 1.0}
