import pytest

from app.services.youtube import InvalidYouTubeUrl, extract_video_id

VID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"https://youtube.com/watch?v={VID}&t=42s",
        f"https://www.youtube.com/watch?list=PL123&v={VID}",
        f"https://m.youtube.com/watch?v={VID}",
        f"https://youtu.be/{VID}",
        f"https://youtu.be/{VID}?si=abc",
        f"https://www.youtube.com/embed/{VID}",
        f"https://www.youtube.com/shorts/{VID}",
        f"https://www.youtube.com/live/{VID}",
        f"www.youtube.com/watch?v={VID}",
        f"  https://youtu.be/{VID}  ",
        VID,
    ],
)
def test_extract_video_id_valid(url):
    assert extract_video_id(url) == VID


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "https://example.com/watch?v=" + VID,
        "https://www.youtube.com/watch",
        "https://www.youtube.com/watch?v=kisa",
        "https://www.youtube.com/@kanal",
        "bu bir bağlantı değil",
    ],
)
def test_extract_video_id_invalid(url):
    with pytest.raises(InvalidYouTubeUrl):
        extract_video_id(url)
