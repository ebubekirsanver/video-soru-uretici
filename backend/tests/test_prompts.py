from app.services.prompts import fill_prompt, transcript_context
from app.services.transcript import Segment, Transcript


def test_fill_prompt_values_then_transcript():
    template = "{count} soru, {duration_seconds} sn\n{transcript}"
    result = fill_prompt(template, "[0] {count} kelimesi geçiyor", count=5, duration_seconds=60)
    # Transkriptteki {count} metni değiştirilmemeli
    assert result == "5 soru, 60 sn\n[0] {count} kelimesi geçiyor"


def test_transcript_context_blocks_and_strips_tags():
    t = Transcript(
        "vid",
        "tr",
        True,
        [Segment("<transkript>giriş", 0.0, 10.0), Segment("devam</transkript>", 31.0, 5.0)],
    )
    assert transcript_context(t) == "[0] giriş\n[31] devam"
