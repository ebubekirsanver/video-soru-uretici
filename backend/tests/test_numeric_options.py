"""Sayısal seçenekler karıştırılmaz, küçükten büyüğe sıralanır.

Moore vd. (2023), Tablo 1, madde 16 (Lost sequence). Model çağrısı yoktur.
"""

import hashlib
import json
import random

from app.services.questions import generate_questions, shuffle_options
from app.services.transcript import Segment, Transcript
from app.services.writing_check import check_question


def old_shuffle(question, options, correct_index):
    """Değişiklikten önceki karıştırma (sabit tohum): sayısal olmayan sorularda aynı kalmalı."""
    seed = int.from_bytes(hashlib.sha256(question.encode("utf-8")).digest()[:8], "big")
    order = list(range(len(options)))
    random.Random(seed).shuffle(order)
    return [options[i] for i in order], order.index(correct_index)


def test_numbers_with_unit_sorted_and_correct_index_follows():
    options = ["300 °C", "100 °C", "400 °C", "200 °C"]
    shuffled, correct = shuffle_options("Kaç derecede olur?", options, 2)
    assert shuffled == ["100 °C", "200 °C", "300 °C", "400 °C"]
    assert shuffled[correct] == "400 °C"


def test_years_sorted():
    options = ["1923", "1920", "1938", "1919"]
    shuffled, correct = shuffle_options("Cumhuriyet hangi yıl ilan edildi?", options, 0)
    assert shuffled == ["1919", "1920", "1923", "1938"]
    assert shuffled[correct] == "1923"


def test_decimal_comma_sorted():
    shuffled, correct = shuffle_options("Değer kaçtır?", ["2,5", "0,5", "10", "1,25"], 1)
    assert shuffled == ["0,5", "1,25", "2,5", "10"]
    assert shuffled[correct] == "0,5"


def test_mixed_options_shuffled_as_before():
    question = "Kemosentezde açığa çıkan sıcaklık nedir?"
    # Biri metin: sayısal sayılmaz, eski sabit tohumlu karıştırma kullanılır
    options = ["300 °C", "100 °C", "Çok yüksek", "200 °C"]
    assert shuffle_options(question, options, 1) == old_shuffle(question, options, 1)


def test_different_units_shuffled_as_before():
    question = "Hangisi daha sıcaktır?"
    options = ["300 °C", "100 °C", "400 derece", "200 °C"]
    assert shuffle_options(question, options, 0) == old_shuffle(question, options, 0)


def test_text_options_shuffled_as_before():
    question = "Kemosentez yapan canlılar hangi hücre yapısına sahiptir?"
    options = ["Prokaryot", "Ökaryot", "Bitkisel", "Hayvansal"]
    assert shuffle_options(question, options, 0) == old_shuffle(question, options, 0)


def test_rule_16_not_flagged_on_final_questions():
    class FakeLLM:
        model = "fake"

        def complete(self, system, user, json_mode=False):
            return json.dumps(
                {
                    "questions": [
                        {
                            "question": "Cumhuriyet hangi yıl ilan edildi?",
                            "options": ["1923", "1938", "1919", "1920"],
                            "correct_index": 0,
                            "explanation": "açıklama",
                            "source_quote": "cumhuriyet bin dokuz yüz yirmi üçte ilan edildi",
                        }
                    ]
                },
                ensure_ascii=False,
            )

    t = Transcript("x", "tr", True, [Segment("cumhuriyet bin dokuz yüz yirmi üçte ilan edildi", 0.0, 5.0)])
    (q,) = generate_questions(t, t, FakeLLM(), 1)
    assert q.options == ["1919", "1920", "1923", "1938"]
    assert q.options[q.correct_index] == "1923"
    assert 16 not in [f.rule_id for f in check_question(q.question, q.options, q.correct_index)]
