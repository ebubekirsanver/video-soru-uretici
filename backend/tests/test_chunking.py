import pytest

from app.services.chunking import TimeBlock, format_blocks, group_into_blocks
from app.services.transcript import Segment


def test_group_into_blocks_about_30_seconds():
    segments = [
        Segment("a", 0.0, 10.0),
        Segment("b", 10.0, 10.0),
        Segment("c", 20.0, 10.0),
        Segment("d", 30.0, 10.0),  # bloğun başından 30 sn sonra: yeni blok
        Segment("e", 45.0, 5.0),
        Segment("f", 61.5, 3.0),
    ]
    blocks = group_into_blocks(segments, block_seconds=30.0)
    assert blocks == [
        TimeBlock(start=0.0, end=30.0, text="a b c"),
        TimeBlock(start=30.0, end=50.0, text="d e"),
        TimeBlock(start=61.5, end=64.5, text="f"),
    ]


def test_long_segment_is_not_split():
    blocks = group_into_blocks([Segment("uzun", 0.0, 90.0), Segment("sonra", 90.0, 2.0)])
    assert [(b.start, b.end, b.text) for b in blocks] == [(0.0, 90.0, "uzun"), (90.0, 92.0, "sonra")]


def test_empty_segments():
    assert group_into_blocks([]) == []


def test_invalid_block_seconds():
    with pytest.raises(ValueError):
        group_into_blocks([Segment("a", 0.0, 1.0)], block_seconds=0)


def test_format_blocks():
    blocks = [TimeBlock(0.0, 30.0, "giriş"), TimeBlock(30.7, 55.0, "sıralama")]
    assert format_blocks(blocks) == "[0] giriş\n[30] sıralama"


# --- Sabit boyutlu parçalar (Aşama 7a) ----------------------------------------------

from app.services.chunking import (  # noqa: E402
    CHUNK_OVERLAP_WORDS,
    CHUNK_WORDS,
    CHUNKING_VERSION,
    Chunk,
    fixed_size_chunks,
)


def words_segment(n_words, start, duration=5.0, word="k"):
    return Segment(" ".join(f"{word}{i}" for i in range(n_words)), start, duration)


def test_fixed_chunks_size_overlap_and_times():
    # 20 segment × 20 kelime = 400 kelime; her segment 5 sn
    segments = [words_segment(20, i * 5.0, word=f"s{i}_") for i in range(20)]
    chunks = fixed_size_chunks(segments, "vid")
    assert [(c.chunk_index, c.start_seconds, c.end_seconds) for c in chunks] == [
        (0, 0.0, 40.0),  # segment 0-7: 160 kelime (150'ye ulaşınca kapanır)
        (1, 30.0, 70.0),  # son iki segment (40 kelime, en az 30) örtüşme olarak tekrar başlar
        (2, 60.0, 100.0),
    ]
    assert all(len(c.text.split()) == 160 for c in chunks)
    # Örtüşme: parça 1, parça 0'ın son iki segmentiyle başlar
    assert chunks[1].text.startswith(segments[6].text + " " + segments[7].text)
    assert all(c.video_id == "vid" and c.chunking == CHUNKING_VERSION == "fixed-150-30" for c in chunks)
    assert (CHUNK_WORDS, CHUNK_OVERLAP_WORDS) == (150, 30)


def test_fixed_chunks_do_not_split_segments():
    sizes = [7, 40, 13, 55, 9, 60, 21, 33, 18]
    segments = [words_segment(n, i * 3.0, word=f"s{i}_") for i, n in enumerate(sizes)]
    for chunk in fixed_size_chunks(segments, "vid"):
        # Parça metni, art arda gelen bütün segmentlerin birleşimidir; hiçbir segment yarım kalmaz
        parts = [s.text for s in segments if s.text in chunk.text]
        assert " ".join(parts) == chunk.text


def test_fixed_chunks_every_segment_covered_and_last_chunk_short():
    segments = [words_segment(20, i * 5.0, word=f"s{i}_") for i in range(9)]  # 180 kelime
    chunks = fixed_size_chunks(segments, "vid")
    assert len(chunks) == 2
    assert len(chunks[1].text.split()) < CHUNK_WORDS  # son parça kısa kalabilir
    assert chunks[-1].end_seconds == 45.0
    covered = " ".join(c.text for c in chunks)
    assert all(s.text in covered for s in segments)


def test_fixed_chunks_empty():
    assert fixed_size_chunks([], "vid") == []


def test_fixed_chunks_single_long_segment():
    long = words_segment(200, 0.0, 60.0, word="uzun")
    assert fixed_size_chunks([long], "vid") == [Chunk("vid", 0, 0.0, 60.0, long.text, CHUNKING_VERSION)]


def test_fixed_chunks_long_segment_then_short_ones():
    long = words_segment(200, 0.0, 60.0, word="uzun")
    short = [words_segment(10, 60.0 + i * 4, 4.0, word=f"k{i}_") for i in range(3)]
    chunks = fixed_size_chunks([long] + short, "vid")
    # Tek segmentlik parçadan örtüşme alınmaz; ikinci parça yeni segmentlerle başlar
    assert [(c.start_seconds, c.end_seconds) for c in chunks] == [(0.0, 60.0), (60.0, 72.0)]
    assert chunks[1].text == " ".join(s.text for s in short)


def test_fixed_chunks_invalid_parameters():
    seg = [words_segment(5, 0.0)]
    with pytest.raises(ValueError):
        fixed_size_chunks(seg, "vid", chunk_words=0)
    with pytest.raises(ValueError):
        fixed_size_chunks(seg, "vid", chunk_words=50, overlap_words=50)


def test_group_into_blocks_unchanged_by_new_chunking():
    # Özet ve soru istemlerinin kullandığı 30 sn'lik bloklar aynı kalır
    segments = [words_segment(20, i * 10.0, 10.0) for i in range(4)]
    assert [b.start for b in group_into_blocks(segments)] == [0.0, 30.0]
