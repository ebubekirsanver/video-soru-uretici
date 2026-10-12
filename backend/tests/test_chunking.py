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
